import asyncio
import logging
from typing import Optional

from fast_rabbit import logger
from fast_rabbit.fast_rabbit_router import FastRabbitRouter
from fast_rabbit.connection_manager import ConnectionManager
from fast_rabbit.channel_manager import ChannelManager
from fast_rabbit.message_publisher import MessagePublisher
from fast_rabbit.consumer_manager import ConsumerManager


class FastRabbitEngine:
    _instance = None

    def __new__(cls, amqp_url: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super(FastRabbitEngine, cls).__new__(cls)
            cls._instance._initialised = False
        return cls._instance

    def __init__(self, amqp_url: Optional[str] = None):
        if not self._initialised:
            if amqp_url is None:
                raise ValueError("AMQP URL must be provided for initialisation.")
            self.connection_manager = ConnectionManager(amqp_url)
            self.channel_manager = ChannelManager(self.connection_manager)
            self.message_publisher = MessagePublisher(self.channel_manager)
            self.consumer_manager = ConsumerManager(self.channel_manager)
            self._initialised = True

    async def run(self):
        await self.consumer_manager.start_consumers()
        await asyncio.Event().wait()

    async def shutdown(self):
        await self.channel_manager.close_channels()
        await self.connection_manager.close_connection()

    def subscribe(self, queue_name: str):
        """
        Registers a consumer function for a specific queue.
        """
        return self.consumer_manager.subscribe(queue_name)

    async def publish(self, queue_name: str, data, priority: int = 0):
        """
        Publishes a message to a specified queue.

        Args:
            queue_name (str): The name of the queue to publish the message to.
            data: The message data. This can be a Pydantic model, a dict, or any serializable data.
            priority (int, optional): The priority of the message. Defaults to 0.
        """
        await self.message_publisher.publish(queue_name, data, priority)

    def include_subscriptions(self, router: FastRabbitRouter):
        for queue_name, handler in router.subscriptions.items():
            self.subscribe(queue_name)(handler)
