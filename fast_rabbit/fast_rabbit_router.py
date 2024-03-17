import inspect
from pydantic import BaseModel, ValidationError

from fast_rabbit import logger
from fast_rabbit.consumer_error_handler import ConsumerErrorHandler

from typing import Awaitable, Callable, Dict, Any, Optional, Type


class FastRabbitRouter:
    """Manages routing for RabbitMQ message handlers.

    This router allows for the registration of message handlers for different RabbitMQ queues
    and supports publishing messages to these queues. It facilitates automatic deserialization
    of messages into Pydantic models for the registered handlers.

    Attributes:
        subscriptions (Dict[str, Callable[..., Awaitable[None]]]): Maps queue names to their
            message handler functions.
    """

    def __init__(self) -> None:
        """Initializes a new FastRabbitRouter instance with an empty subscriptions dictionary."""
        self.subscriptions: Dict[str, Dict[str, Any]] = {}

    def subscribe(
        self,
        queue_name: str,
        prefetch_count: int = 1,
        consumer_error_handler: Optional[ConsumerErrorHandler] = None,
    ) -> Callable:
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
                "consumer_error_handler": consumer_error_handler,
            }
            return func

        return decorator

    async def publish(self, queue_name: str, data: Any, priority: int = 0) -> None:
        """Publishes a message to a specified queue with optional priority.

        Utilizes the FastRabbitEngine singleton instance to publish messages, supporting both
        Pydantic models and any serializable data types.

        Args:
            queue_name: The name of the queue to which the message will be published.
            data: The message data, which can be a Pydantic model or any serializable type.
            priority: The priority of the message, with 0 as the default.
        """
        from .fast_rabbit import FastRabbitEngine

        try:
            engine = FastRabbitEngine()
            await engine.publish(queue_name, data, priority)
        except Exception as e:
            logger.error(f"Failed to publish message to {queue_name}: {e}")
