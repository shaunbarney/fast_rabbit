import inspect
from aio_pika import IncomingMessage, Message
from aio_pika.abc import AbstractIncomingMessage
from pydantic import BaseModel
from aio_pika.exceptions import AMQPException

from fast_rabbit import logger
from .channel_manager import ChannelManager

from typing import Callable, Dict, Awaitable, Type, Any


class ConsumerManager:
    """Manages message consumption from RabbitMQ queues.

    This class is responsible for subscribing to queues, starting consumers,
    and processing incoming messages with registered handlers.

    Attributes:
        channel_manager (ChannelManager): The channel manager used to obtain channels for message consumption.
        subscriptions (Dict[str, Callable[..., Awaitable[None]]]): A dictionary mapping queue names to their
            message handler functions.
    """

    def __init__(self, channel_manager: ChannelManager) -> None:
        """Initialises a new ConsumerManager instance.

        Args:
            channel_manager (ChannelManager): The channel manager for obtaining channels.
        """
        self.channel_manager: ChannelManager = channel_manager
        self.subscriptions: Dict[str, Callable[[Any], Awaitable[None]]] = {}

    def subscribe(
        self, queue_name: str
    ) -> Callable[[Callable[..., Awaitable[None]]], Callable[..., Awaitable[None]]]:
        """Registers a coroutine as a consumer for a specified queue.

        This method decorates a coroutine to be used as a message handler for the specified queue.
        It supports automatic deserialisation of messages into Pydantic models if specified.

        Args:
            queue_name (str): The name of the queue for which the consumer is being registered.

        Returns:
            A decorator that registers the coroutine as a consumer for the specified queue.
        """

        def decorator(
            func: Callable[..., Awaitable[None]]
        ) -> Callable[..., Awaitable[None]]:
            self.subscriptions[queue_name] = func
            return func

        return decorator

    async def _start_consumer(self, queue_name: str) -> None:
        """Starts a message consumer for a specified queue.

        This internal method declares a queue and starts consuming messages from it,
        using the registered handler to process incoming messages.

        Args:
            queue_name (str): The name of the queue to consume messages from.

        Raises:
            AMQPException: If there is an error declaring the queue or starting the consumer.
        """
        channel = await self.channel_manager.get_channel()
        try:
            queue = await channel.declare_queue(queue_name, durable=True)
        except AMQPException as e:
            logger.error(f"Failed to declare queue '{queue_name}': {e}")
            raise

        async def message_handler(message: AbstractIncomingMessage) -> None:
            """Processes incoming messages using the registered handler."""
            async with message.process():
                try:
                    func = self.subscriptions[queue_name]
                    params = inspect.signature(func).parameters
                    model_type: Type[BaseModel] | None = None
                    for param in params.values():
                        if issubclass(param.annotation, BaseModel):
                            model_type = param.annotation
                            break
                    if model_type:
                        data = model_type.parse_raw(message.body.decode())
                    else:
                        data = message.body.decode()
                    await func(data)
                except Exception as e:
                    logger.error(f"Error processing message for '{queue_name}': {e}")

        await queue.consume(message_handler)
        logger.info(f"Consumer started for queue '{queue_name}'.")

    async def start_consumers(self) -> None:
        """Starts all registered message consumers.

        This method iterates through all registered queue names and starts a consumer for each.
        """
        for queue_name in self.subscriptions.keys():
            await self._start_consumer(queue_name)
