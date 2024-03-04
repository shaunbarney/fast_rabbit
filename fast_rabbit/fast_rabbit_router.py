import inspect
from pydantic import BaseModel, ValidationError

from fast_rabbit import logger

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
        self.subscriptions: Dict[str, Callable[..., Awaitable[None]]] = {}

    def subscribe(
        self, queue_name: str
    ) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Any]]:
        """Registers a coroutine as a consumer for a specified queue with optional Pydantic model deserialization.

        Args:
            queue_name: The name of the queue for which the consumer is being registered.

        Returns:
            A decorator function that takes a coroutine, wraps it to include automatic
            deserialization of messages, and registers the wrapped coroutine as a consumer
            for the specified queue.
        """

        def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Any]:
            params = inspect.signature(func).parameters
            model_type: Optional[Type[BaseModel]] = None
            for param in params.values():
                if isinstance(param.annotation, type) and issubclass(
                    param.annotation, BaseModel
                ):
                    model_type = param.annotation
                    break

            async def wrapper(message_body: str) -> None:
                """Deserializes message before passing to the consumer if a Pydantic model is expected."""
                data = message_body
                if model_type:
                    try:
                        data = model_type.parse_raw(message_body)
                    except ValidationError as e:
                        logger.error(
                            f"Error parsing message into model {model_type}: {e}"
                        )
                        return

                await func(data)

            self.subscriptions[queue_name] = wrapper
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
