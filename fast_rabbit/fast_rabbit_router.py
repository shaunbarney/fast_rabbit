import inspect
import logging
from pydantic import BaseModel

from typing import Awaitable, Callable, Dict, Any


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FastRabbitRouter:
    """Manages routing for RabbitMQ message handlers.

    This class provides functionality to register message handlers for different RabbitMQ queues
    and publish messages to these queues. It supports automatic deserialisation of messages into
    Pydantic models for the registered handlers.

    Attributes:
        subscriptions (Dict[str, Callable[..., Awaitable[None]]]): A dictionary mapping queue names
            to their message handler functions.
    """

    def __init__(self) -> None:
        """Initialises a new FastRabbitRouter instance with an empty subscriptions dictionary."""
        self.subscriptions: Dict[str, Callable[..., Awaitable[None]]] = {}

    def subscribe(
        self, queue_name: str
    ) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Any]]:
        """Registers a coroutine as a consumer for a specified queue with optional Pydantic model deserialisation.

        This method inspects the coroutine's parameters to determine if a Pydantic model is expected.
        If so, it automatically deserialises incoming messages into that model before passing them
        to the coroutine.

        Args:
            queue_name (str): The name of the queue for which the consumer is being registered.

        Returns:
            Callable[[Callable[..., Awaitable[Any]]], Callable[..., Any]]: A decorator function that
            takes a coroutine, wraps it to include automatic deserialisation of messages, and
            registers the wrapped coroutine as a consumer for the specified queue.
        """

        def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Any]:
            params = inspect.signature(func).parameters
            model_type = None
            for param in params.values():
                if isinstance(param.annotation, type) and issubclass(
                    param.annotation, BaseModel
                ):
                    model_type = param.annotation
                    break

            async def wrapper(message_body: str) -> None:
                """Deserialises message before passing to the consumer if a Pydantic model is expected."""
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

    async def publish(self, queue_name: str, data: Any, priority: int = 0) -> None:
        """Publishes a message to a specified queue with optional priority.

        Utilises the FastRabbitEngine singleton instance to publish messages, supporting both
        Pydantic models and any serialisable data types.

        Args:
            queue_name (str): The name of the queue to which the message will be published.
            data (Any): The message data, which can be a Pydantic model or any serialisable type.
            priority (int, optional): The priority of the message, with 0 as the default.
        """
        from fast_rabbit import FastRabbitEngine

        engine = (
            FastRabbitEngine()
        )  # Assumes FastRabbitEngine manages its singleton instance
        await engine.publish(queue_name, data, priority)
