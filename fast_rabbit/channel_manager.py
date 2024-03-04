from aio_pika.abc import AbstractChannel
from aio_pika.exceptions import AMQPException

from fast_rabbit import logger
from fast_rabbit.connection_manager import ConnectionManager


class ChannelManager:
    """Manages AMQP channels for RabbitMQ communication.

    This class handles the creation, caching, and closing of channels to optimize
    resource usage and simplify channel management throughout the application.

    Attributes:
        connection_manager (ConnectionManager): The connection manager instance used
            to obtain a connection for creating channels.
        channels (dict): A dictionary storing channel instances keyed by a custom
            channel name.
    """

    def __init__(self, connection_manager: ConnectionManager):
        """Initializes a new ChannelManager instance.

        Args:
            connection_manager: An instance of ConnectionManager for managing AMQP connections.
        """
        self.connection_manager = connection_manager
        self.channels = {}

    async def get_channel(self, channel_name: str = "default") -> AbstractChannel:
        """Retrieves or creates an AMQP channel.

        This method checks if a channel with the given name already exists and is open.
        If so, it returns the existing channel. Otherwise, it creates a new channel,
        caches it, and returns it.

        Args:
            channel_name: The name of the channel to retrieve or create. Defaults to "default".

        Returns:
            An instance of AbstractChannel representing the AMQP channel.

        Raises:
            AMQPException: If there is an error creating the channel.
        """
        if channel_name in self.channels and not self.channels[channel_name].is_closed:
            return self.channels[channel_name]

        connection = await self.connection_manager.get_connection()
        try:
            channel = await connection.channel()
            self.channels[channel_name] = channel
            return channel
        except AMQPException as e:
            logger.error(f"Failed to create channel '{channel_name}': {e}")
            raise

    async def close_channels(self):
        """Closes all open channels managed by this ChannelManager.

        This method iterates through all cached channels, closes them if they are not
        already closed, and then clears the cache.

        Raises:
            AMQPException: If there is an error closing any of the channels.
        """
        for channel_name, channel in self.channels.items():
            if not channel.is_closed:
                try:
                    await channel.close()
                    logger.info(f"Channel '{channel_name}' closed successfully.")
                except AMQPException as e:
                    logger.error(f"Failed to close channel '{channel_name}': {e}")
        self.channels.clear()
