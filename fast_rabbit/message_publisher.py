from aio_pika import Message, DeliveryMode
from aio_pika.exceptions import AMQPException

from fast_rabbit import logger
from fast_rabbit.utils import serialise_data
from fast_rabbit.channel_manager import ChannelManager

from typing import Any


class MessagePublisher:
    """Publishes messages to RabbitMQ queues.

    This class handles the serialisation of message data and ensures messages are
    published with the appropriate delivery mode and priority.

    Attributes:
        channel_manager (ChannelManager): The channel manager for obtaining RabbitMQ channels.
    """

    def __init__(self, channel_manager: ChannelManager) -> None:
        """Initialises a new instance of MessagePublisher.

        Args:
            channel_manager (ChannelManager): The channel manager for obtaining RabbitMQ channels.
        """
        self.channel_manager: ChannelManager = channel_manager

    async def publish(self, queue_name: str, data: Any, priority: int = 0) -> None:
        """Publishes a message to a specified RabbitMQ queue.

        Args:
            queue_name (str): The name of the queue to publish the message to.
            data (Any): The message data. This can be a Pydantic model, a dict, or any serialisable data.
            priority (int, optional): The priority of the message. Defaults to 0.

        Raises:
            AMQPException: If declaring the queue or publishing the message fails.
        """
        channel = await self.channel_manager.get_channel()
        try:
            await channel.declare_queue(queue_name, durable=True)
        except AMQPException as e:
            logger.error(f"Failed to declare queue for publishing: {e}")
            raise

        message_body = serialise_data(data).encode()
        message = Message(
            message_body, delivery_mode=DeliveryMode.PERSISTENT, priority=priority
        )
        try:
            await channel.default_exchange.publish(message, routing_key=queue_name)
        except AMQPException as e:
            logger.error(f"Failed to publish message to {queue_name}: {e}")
            raise
