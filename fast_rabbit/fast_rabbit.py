import inspect
import asyncio
import logging
from pydantic import BaseModel
from aio_pika.exceptions import AMQPException
from aio_pika import connect_robust, Message, DeliveryMode
from aio_pika.abc import (
    AbstractIncomingMessage,
    AbstractQueue,
    AbstractChannel,
    AbstractConnection,
)

from fast_rabbit.utils import serialise_data
from fast_rabbit.fast_rabbit_router import FastRabbitRouter

from typing import Callable, Awaitable, Any, Dict, Optional

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FastRabbitEngine:
    """Manages RabbitMQ interactions asynchronously, enhancing robustness and efficiency.

    This class implements the Singleton pattern to ensure only one instance manages
    the RabbitMQ connections, channels, and consumer registration. It provides an
    asynchronous API to publish messages and start message consuming workers based
    on registered callbacks.

    Attributes:
        amqp_url (str): The AMQP URL used to establish a connection to the RabbitMQ server.
        subscriptions (Dict[str, Callable[..., Awaitable[Any]]]): Maps queue names to their
            respective consumer coroutine functions, facilitating message processing.
        connection (Optional[AbstractConnection]): Maintains a robust connection instance to
            the RabbitMQ server, automatically reconnecting if necessary.
        channels (Dict[str, AbstractChannel]): Caches channels for reuse, keyed by a descriptive
            name, with 'default' being used for the primary channel.
    """

    _instance = None

    def __new__(cls, amqp_url: Optional[str] = None):
        """Ensures only one instance of FastRabbitEngine is created.

        Args:
            amqp_url (str): The AMQP URL to connect to the RabbitMQ server. Required for the
                first instantiation of the class.

        Returns:
            The singleton instance of FastRabbitEngine.
        """
        if cls._instance is None:
            instance = super(FastRabbitEngine, cls).__new__(cls)
            instance._initialised = False
            cls._instance = instance
        return cls._instance

    def __init__(self, amqp_url: Optional[str] = None):
        """Initialises the FastRabbitEngine instance, if not already initialised.

        Args:
            amqp_url (str, optional): The AMQP URL to connect to the RabbitMQ server. Required
                for the first instantiation of the class. Defaults to None.
        """
        if not self._initialised:
            if amqp_url is None:
                raise ValueError("AMQP URL must be provided for initialisation.")
            self.amqp_url = amqp_url
            self.subscriptions: Dict[str, Callable[..., Awaitable[Any]]] = {}
            self.connection: Optional[AbstractConnection] = None
            self.channels: Dict[str, AbstractChannel] = {}
            self._initialised = True

    async def _get_connection(self) -> AbstractConnection:
        """Obtains a robust connection to the RabbitMQ server, creating a new connection if none exists or the existing one is closed.

        Returns:
            AbstractConnection: An active, robust connection to the RabbitMQ server.
        """
        while True:
            if self.connection is None or self.connection.is_closed:
                try:
                    self.connection = await connect_robust(self.amqp_url)
                except AMQPException as e:
                    logger.error(
                        f"Failed to connect to RabbitMQ: {e}. Retrying in 1 second..."
                    )
                    await asyncio.sleep(1)
            else:
                break
        return self.connection

    async def _get_channel(self) -> AbstractChannel:
        """Retrieves or creates a default channel on the current RabbitMQ connection, caching it for future use to optimise resource usage.

        Returns:
            AbstractChannel: An active channel for communication with the RabbitMQ server.
        """
        if "default" in self.channels and not self.channels["default"].is_closed:
            return self.channels["default"]
        else:
            connection = await self._get_connection()
            try:
                channel = await connection.channel()
            except AMQPException as e:
                logger.error(f"Failed to create channel: {e}")
                raise
            else:
                self.channels["default"] = channel
                return channel

    async def publish(self, queue_name: str, data: Any, priority: int = 0) -> None:
        """Publishes a message to a specified queue with optional priority.

        Args:
            queue_name (str): The name of the queue to publish the message to.
            data (Any): The message data, supporting Pydantic models or any serialisable type.
            priority (int, optional): The priority of the message. Defaults to 0.
        """
        channel = await self._get_channel()
        try:
            queue = await channel.declare_queue(queue_name, durable=True)
            _ = queue  # Suppresses unused variable warning
        except AMQPException as e:
            logger.error(f"Failed to declare queue for publishing: {e}")
            raise

        # Serialise data based on its type
        message_body = serialise_data(data).encode()
        message = Message(
            message_body, delivery_mode=DeliveryMode.PERSISTENT, priority=priority
        )
        try:
            await channel.default_exchange.publish(message, routing_key=queue_name)
        except AMQPException as e:
            logger.error(f"Failed to publish message to {queue_name}: {e}")
            raise

    def subscribe(self, queue_name: str):
        """
        A decorator for registering a coroutine as a consumer for a specified queue. This method
        inspects the coroutine's parameters to determine if a Pydantic model is expected. If so,
        it automatically deserialises incoming messages into that model before passing them to the
        coroutine.

        Args:
            queue_name (str): The name of the queue for which the consumer is registered.

        Returns:
            Callable: A decorator function that takes a coroutine, wraps it to include automatic
            deserialisation of messages, and registers the wrapped coroutine as a consumer for the
            specified queue.
        """

        def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Any]:
            params = inspect.signature(func).parameters
            model_type = None
            for param in params.values():
                if issubclass(param.annotation, BaseModel):
                    model_type = param.annotation
                    break

            async def wrapper(message_body: str):
                """Internal wrapper function to deserialise message before passing to the consumer."""
                if model_type:
                    try:
                        data = model_type.parse_raw(message_body)
                    except Exception as e:
                        logger.error(
                            f"Error parsing message into model {model_type}: {e}"
                        )
                        return
                else:
                    data = message_body

                await func(data)

            self.subscriptions[queue_name] = wrapper
            return func

        return decorator

    async def _start_consumer(
        self, queue_name: str, consumer: Callable[..., Awaitable[Any]]
    ):
        """
        Starts a message consumer coroutine for a specified queue. This method declares a durable
        queue and begins consuming messages from it, using the provided consumer coroutine for
        message processing. It automatically handles message deserialisation based on the consumer
        function's parameter annotations, supporting dynamic data types including Pydantic models.

        Args:
            queue_name (str): The name of the queue from which to consume messages.
            consumer (Callable[..., Awaitable[Any]]): A coroutine that processes each message.

        Raises:
            AMQPException: If an error occurs during queue declaration or message consumption.
        """
        channel = await self._get_channel()
        try:
            queue: AbstractQueue = await channel.declare_queue(queue_name, durable=True)
        except AMQPException as e:
            logger.error(f"Failed to declare queue '{queue_name}': {e}")
            raise

        params = inspect.signature(consumer).parameters
        model_type = None
        for param in params.values():
            if issubclass(param.annotation, BaseModel):
                model_type = param.annotation
                break

        async def message_handler(message: AbstractIncomingMessage):
            """
            Processes incoming messages, deserialising them as needed before passing to the consumer.

            Args:
                message (AbstractIncomingMessage): The incoming message from the queue.
            """
            async with message.process():
                try:
                    if model_type:
                        data = model_type.parse_raw(message.body.decode())
                    else:
                        data = message.body.decode()
                except Exception as e:
                    logger.error(f"Error deserialising message for '{queue_name}': {e}")
                    return

                try:
                    await consumer(data)
                except Exception as e:
                    logger.error(f"Error processing message for '{queue_name}': {e}")
                    # Handle or log the error as needed

        try:
            await queue.consume(message_handler)
        except AMQPException as e:
            logger.error(f"Failed to start consumer for '{queue_name}': {e}")
            raise
        else:
            logger.info(f"Consumer started for queue '{queue_name}'.")

    def include_subscriptions(self, router: FastRabbitRouter) -> None:
        """Includes the routes from a RabbitMQRouter instance in the current RabbitMQEngine instance.

        Args:
            router (RabbitMQRouter): The router instance containing the routes to include.
        """
        for queue_name, handler in router.subscriptions.items():
            self.subscriptions[queue_name] = handler

    async def _start_consumers(self) -> None:
        """Starts message consumers for all registered queues."""
        for queue_name, consumer in self.subscriptions.items():
            await self._start_consumer(queue_name, consumer)

    async def run(self) -> None:
        """Initiates the message consuming process for all registered queues and enters an indefinite wait state."""
        await self._start_consumers()
        await asyncio.Event().wait()
