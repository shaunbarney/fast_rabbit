import asyncio
import inspect
from typing import Callable, Dict, Awaitable, Type, Any, List

from aio_pika import connect, IncomingMessage
from aio_pika.abc import AbstractIncomingMessage, AbstractChannel
from aio_pika.exceptions import AMQPException
from pydantic import BaseModel

from fast_rabbit import logger
from .channel_manager import ChannelManager


class ConsumerManager:
    """Manages message consumption from RabbitMQ queues.

    Responsible for subscribing to queues, starting consumers, and processing incoming messages with registered handlers.

    Attributes:
        channel_manager: The channel manager used to obtain channels for message consumption.
        subscriptions: A dictionary mapping queue names to their message handler functions and configurations.
    """

    def __init__(self, channel_manager: ChannelManager) -> None:
        """Initializes a new ConsumerManager instance.

        Args:
            channel_manager: The channel manager for obtaining channels.
        """
        self.channel_manager: ChannelManager = channel_manager
        self.subscriptions: Dict[str, Dict[str, Any]] = {}

    def subscribe(self, queue_name: str, prefetch_count: int = 1) -> Callable:
        """Registers a coroutine as a consumer for a specified queue with a prefetch count.

        Decorates a coroutine to be used as a message handler for the specified queue, supporting automatic deserialization into Pydantic models if specified.

        Args:
            queue_name: The name of the queue for which the consumer is being registered.
            prefetch_count: The number of messages to prefetch for batch processing.

        Returns:
            A decorator that registers the coroutine as a consumer for the specified queue.
        """

        def decorator(
            func: Callable[..., Awaitable[None]]
        ) -> Callable[..., Awaitable[None]]:
            self.subscriptions[queue_name] = {
                "handler": func,
                "prefetch_count": prefetch_count,
            }
            return func

        return decorator

    async def _start_consumer(self, queue_name: str) -> None:
        """Starts a message consumer for a specified queue.

        Declares a queue and starts consuming messages from it, using the registered handler to process incoming messages.

        Args:
            queue_name: The name of the queue to consume messages from.

        Raises:
            AMQPException: If there is an error declaring the queue or starting the consumer.
        """
        channel: AbstractChannel = await self.channel_manager.get_channel()
        await channel.set_qos(
            prefetch_count=self.subscriptions[queue_name]["prefetch_count"]
        )

        try:
            queue = await channel.declare_queue(queue_name, durable=True)
        except AMQPException as e:
            logger.error(f"Failed to declare queue '{queue_name}': {e}")
            raise

        async def message_handler(message: AbstractIncomingMessage) -> None:
            """Processes incoming messages using the registered handler."""
            try:
                handler = self.subscriptions[queue_name]["handler"]
                params = inspect.signature(handler).parameters
                model_type: Type[BaseModel] | None = None
                for param in params.values():
                    if issubclass(param.annotation, BaseModel):
                        model_type = param.annotation
                        break
                if model_type:
                    data = model_type.parse_raw(message.body.decode())
                else:
                    data = message.body.decode()
                await handler(data)
                await message.ack()
            except Exception as e:
                logger.error(f"Error processing message for '{queue_name}': {e}")
                # Consider requeuing or dead-lettering the message here

        await queue.consume(message_handler)

    async def start_consumers(self) -> None:
        """Starts all registered message consumers.

        Iterates through all registered queue names and starts a consumer for each.
        """
        for queue_name in self.subscriptions:
            await self._start_consumer(queue_name)
