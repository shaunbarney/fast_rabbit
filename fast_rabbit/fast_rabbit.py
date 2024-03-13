"""Module for managing Fast RabbitMQ interactions.

This module provides a singleton class for managing connections, channels,
publishing messages, and consuming messages from RabbitMQ using the fast_rabbit
library components.

Example:
    engine = FastRabbitEngine(amqp_url="amqp://user:pass@host/vhost")
    await engine.run()
"""

import asyncio

from fast_rabbit.fast_rabbit_router import FastRabbitRouter
from fast_rabbit.connection_manager import ConnectionManager
from fast_rabbit.channel_manager import ChannelManager
from fast_rabbit.message_publisher import MessagePublisher
from fast_rabbit.consumer_manager import ConsumerManager

from typing import Optional, Any


class FastRabbitEngine:
    """A singleton class for managing Fast RabbitMQ interactions.

    Attributes:
        connection_manager (ConnectionManager): Manages RabbitMQ connections.
        channel_manager (ChannelManager): Manages RabbitMQ channels.
        message_publisher (MessagePublisher): Publishes messages to RabbitMQ.
        consumer_manager (ConsumerManager): Manages message consumption from RabbitMQ.

    Args:
        amqp_url (Optional[str]): The AMQP URL for RabbitMQ connection.
    """

    _instance = None

    def __new__(cls, amqp_url: Optional[str] = None) -> "FastRabbitEngine":
        """Ensures that only one instance of the class is created."""
        if cls._instance is None:
            cls._instance = super(FastRabbitEngine, cls).__new__(cls)
            cls._instance._initialised = False
        return cls._instance

    def __init__(self, amqp_url: Optional[str] = None) -> None:
        """Initialises the FastRabbitEngine instance."""
        if not self._initialised:
            if amqp_url is None:
                raise ValueError("AMQP URL must be provided for initialisation.")
            self.connection_manager: ConnectionManager = ConnectionManager(amqp_url)
            self.channel_manager: ChannelManager = ChannelManager(
                self.connection_manager
            )
            self.message_publisher: MessagePublisher = MessagePublisher(
                self.channel_manager
            )
            self.consumer_manager: ConsumerManager = ConsumerManager(
                self.channel_manager
            )
            self._initialised = True

    async def run(self) -> None:
        """Starts the consumer manager and waits indefinitely."""
        await self.consumer_manager.start_consumers()
        await asyncio.Event().wait()

    async def shutdown(self) -> None:
        """Shuts down the channel and connection managers."""
        await self.channel_manager.close_channels()
        await self.connection_manager.close_connection()

    def subscribe(self, queue_name: str, prefetch_count: int = 1) -> Any:
        """Registers a consumer function for a specific queue.

        Args:
            queue_name (str): The name of the queue for which to register the consumer.

        Returns:
            A decorator function for registering the consumer handler.
        """
        return self.consumer_manager.subscribe(queue_name, prefetch_count)

    async def publish(self, queue_name: str, data: Any, priority: int = 0) -> None:
        """Publishes a message to a specified queue.

        Args:
            queue_name (str): The name of the queue to publish the message to.
            data (Any): The message data. This can be a Pydantic model, a dict, or any serializable data.
            priority (int, optional): The priority of the message. Defaults to 0.
        """
        await self.message_publisher.publish(queue_name, data, priority)

    def include_subscriptions(self, router: FastRabbitRouter) -> None:
        """Includes subscriptions from a FastRabbitRouter instance.

        Args:
            router (FastRabbitRouter): The router containing subscriptions to include.
        """
        for queue_name, handler in router.subscriptions.items():
            self.subscribe(queue_name)(handler)
