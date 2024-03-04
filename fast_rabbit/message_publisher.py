from pydantic import BaseModel
from aio_pika import Message, DeliveryMode
from aio_pika.exceptions import AMQPException

from fast_rabbit import logger
from .utils import serialise_data
from .channel_manager import ChannelManager


class MessagePublisher:
    def __init__(self, channel_manager: ChannelManager):
        self.channel_manager = channel_manager

    async def publish(self, queue_name: str, data, priority: int = 0):
        channel = await self.channel_manager.get_channel()
        try:
            queue = await channel.declare_queue(queue_name, durable=True)
            _ = queue  # noqa
        except AMQPException as e:
            logger.error(f"Failed to declare queue for publishing: {e}")
            raise

        if isinstance(data, BaseModel):
            message_body = data.json().encode()
        else:
            message_body = serialise_data(data).encode()

        message = Message(
            message_body, delivery_mode=DeliveryMode.PERSISTENT, priority=priority
        )
        try:
            await channel.default_exchange.publish(message, routing_key=queue_name)
        except AMQPException as e:
            logger.error(f"Failed to publish message to {queue_name}: {e}")
            raise
