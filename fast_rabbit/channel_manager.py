import logging
from aio_pika.abc import AbstractChannel
from aio_pika.exceptions import AMQPException

from .connection_manager import ConnectionManager


logger = logging.getLogger(__name__)


class ChannelManager:
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.channels = {}

    async def get_channel(self, channel_name: str = "default") -> AbstractChannel:
        if channel_name in self.channels and not self.channels[channel_name].is_closed:
            return self.channels[channel_name]
        else:
            connection = await self.connection_manager.get_connection()
            try:
                channel = await connection.channel()
                self.channels[channel_name] = channel
                return channel
            except AMQPException as e:
                logger.error(f"Failed to create channel: {e}")
                raise

    async def close_channels(self):
        for channel_name, channel in self.channels.items():
            if not channel.is_closed:
                try:
                    await channel.close()
                    logger.info(f"Channel '{channel_name}' closed successfully.")
                except AMQPException as e:
                    logger.error(f"Failed to close channel '{channel_name}': {e}")
        self.channels.clear()
