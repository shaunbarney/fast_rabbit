import asyncio
from aio_pika.exceptions import AMQPException
from aio_pika.abc import AbstractQueue, AbstractChannel, AbstractConnection
from aio_pika import connect_robust, Message, DeliveryMode

from . import logger
from .fast_rabbit_router import FastRabbitRouter

from typing import Callable, Awaitable, Any, Dict, Optional


class FastRabbitEngine:
    """A class for managing RabbitMQ interactions asynchronously, enhancing robustness and efficiency.

    This class abstracts the complexity of handling RabbitMQ connections, channels, and consumer
    registration, providing an asynchronous API to publish messages and start message consuming
    workers based on registered callbacks.

    Attributes:
        amqp_url (str): The AMQP URL used to establish a connection to the RabbitMQ server.
        subscriptions (Dict[str, Callable[..., Awaitable[Any]]]): Maps queue names to their respective
            consumer coroutine functions, facilitating message processing.
        connection (Optional[AbstractConnection]): Maintains a robust connection instance to the RabbitMQ server,
            automatically reconnecting if necessary.
        channels (Dict[str, AbstractChannel]): Caches channels for reuse, keyed by a descriptive name, with
            'default' being used for the primary channel.
    """

    def __init__(self, amqp_url: str) -> None:
        """Initialises the RabbitMQEngine instance with the given AMQP URL.

        Args:
            amqp_url (str): The AMQP URL to connect to the RabbitMQ server.
        """
        self.amqp_url: str = amqp_url
        self.subscriptions: Dict[str, Callable[..., Awaitable[Any]]] = {}
        self.connection: Optional[AbstractConnection] = None
        self.channels: Dict[str, AbstractChannel] = {}

    async def _get_connection(self) -> AbstractConnection:
        """Obtains a robust connection to the RabbitMQ server, creating a new connection if none exists or the existing one is closed.

        Returns:
            AbstractConnection: An active, robust connection to the RabbitMQ server.
        """
        if self.connection is None or self.connection.is_closed:
            try:
                self.connection = await connect_robust(self.amqp_url)
            except AMQPException as e:
                logger.error(f"Failed to connect to RabbitMQ: {e}")
                raise
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

    async def publish(self, queue_name: str, body: str, priority: int = 0) -> None:
        """Asynchronously publishes a message to a specified queue with optional priority, ensuring message persistence and leveraging the default exchange for routing.

        Args:
            queue_name (str): The name of the queue to publish the message to.
            body (str): The message body as a string.
            priority (int, optional): The priority of the message. Defaults to 0.

        Raises:
            AMQPException: If message publishing fails, an exception raised
        """
        channel = await self._get_channel()
        try:
            queue = await channel.declare_queue(queue_name, durable=True)
        except AMQPException as e:
            logger.error(f"Failed to declare queue for publishing: {e}")
            raise

        message = Message(
            body.encode(), delivery_mode=DeliveryMode.PERSISTENT, priority=priority
        )
        try:
            await channel.default_exchange.publish(message, routing_key=queue_name)
        except AMQPException as e:
            logger.error(f"Failed to publish message to {queue_name}: {e}")
            raise

    def subscribe(
        self, queue_name: str
    ) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Any]]:
        """Decorator for registering a coroutine as a consumer for a specified queue. This registration facilitates asynchronous message consumption by invoking the decorated coroutine with the message body as its argument.

        Args:
            queue_name (str): The name of the queue for which the consumer is registered.

        Returns:
            Callable[[Callable[..., Awaitable[Any]]], Callable[..., Any]]: The original coroutine, allowing for potential further decoration.
        """

        def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Any]:
            self.subscriptions[queue_name] = func
            return func

        return decorator

    async def start_consumers(self) -> None:
        """Asynchronously starts all registered consumer coroutines, each consuming messages from its respective queue. Logs a warning if no subscriptions are registered."""
        if not self.subscriptions:
            return
        for queue_name, consumer in self.subscriptions.items():
            await self._start_consumer(queue_name, consumer)

    async def _start_consumer(
        self, queue_name: str, consumer: Callable[..., Awaitable[Any]]
    ) -> None:
        """Asynchronously declares a durable queue and starts consuming messages from it using the provided consumer coroutine.

        Args:
            queue_name (str): The name of the queue from which to consume messages.
            consumer (Callable[..., Awaitable[Any]]): The coroutine to process each message.

        Raises:
            AMQPException: If declaring the queue or starting the consumer fails, an exception is logged and raised.
        """
        channel = await self._get_channel()
        try:
            queue: AbstractQueue = await channel.declare_queue(queue_name, durable=True)
        except AMQPException:
            logger.error(f"Failed to declare queue for consumer {queue_name}.")
            raise

        async def message_handler(message: AbstractIncomingMessage) -> None:
            async with message.process():
                await consumer(message.body.decode())

        try:
            await queue.consume(message_handler)
        except AMQPException as e:
            logger.error(f"Failed to start consumer for {queue_name}: {e}")
            raise
        else:
            logger.info(f"Started consuming from {queue_name}.")

    def include_subscriptions(self, router: FastRabbitRouter) -> None:
        """Includes the routes from a RabbitMQRouter instance in the current RabbitMQEngine instance.

        Args:
            router (RabbitMQRouter): The router instance containing the routes to include.
        """
        for queue_name, handler in router.routes.items():
            self.subscriptions[queue_name] = handler

    async def run(self) -> None:
        """Initiates the message consuming process for all registered queues and enters an indefinite wait state."""
        await self.start_consumers()
        await asyncio.Event().wait()
