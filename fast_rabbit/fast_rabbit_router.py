from typing import Awaitable, Callable, Dict


class FastRabbitRouter:
    """A router for RabbitMQ to register and manage message handlers for different queues.

    This class mimics the functionality of a FastAPI router but for RabbitMQ message queues,
    allowing for the organised handling of messages based on the queue they are received from.

    Attributes:
        routes (Dict[str, Callable[..., Awaitable[None]]]): A dictionary mapping queue names to their message handler functions.
    """

    def __init__(self) -> None:
        """Initialises a new instance of FastRabbitRouter with an empty routes dictionary."""
        self.routes: Dict[str, Callable[..., Awaitable[None]]] = {}

    def route(
        self, queue_name: str
    ) -> Callable[[Callable[..., Awaitable[None]]], Callable[..., Awaitable[None]]]:
        """Registers a message handler for a specific queue.

        This method is intended to be used as a decorator, adding the decorated function as a handler
        for messages coming from the specified queue.

        Args:
            queue_name: The name of the queue for which to register the handler.

        Returns:
            A decorator that registers the given handler function for the specified queue.
        """

        def decorator(
            handler: Callable[..., Awaitable[None]]
        ) -> Callable[..., Awaitable[None]]:
            if queue_name in self.routes:
                raise ValueError(
                    f"A handler for queue '{queue_name}' is already registered."
                )
            self.routes[queue_name] = handler
            return handler

        return decorator
