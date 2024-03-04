import asyncio
from typing import Optional
from aio_pika import connect_robust
from aio_pika.exceptions import AMQPException
from aio_pika.abc import AbstractRobustConnection

from fast_rabbit import logger


class ConnectionManager:
    """Manages the connection to RabbitMQ.

    This class is responsible for establishing and maintaining a robust connection
    to RabbitMQ. It provides mechanisms to obtain a connection and to close it when
    it is no longer required.

    Attributes:
        amqp_url (str): The AMQP URL used to connect to RabbitMQ.
        connection (AbstractRobustConnection | None): The connection object to RabbitMQ. Initially None and
            gets assigned upon successful connection.
    """

    def __init__(self, amqp_url: str) -> None:
        """Initialises a new ConnectionManager instance.

        Args:
            amqp_url (str): The AMQP URL to connect to RabbitMQ.
        """
        self.amqp_url: str = amqp_url
        self.connection: Optional[AbstractRobustConnection] = None

    async def get_connection(self) -> AbstractRobustConnection:
        """Obtains a robust connection to RabbitMQ.

        This method attempts to establish a connection to RabbitMQ using the provided
        AMQP URL. If the connection is already established and open, it returns the
        existing connection. Otherwise, it attempts to connect and retries upon failure.

        Returns:
            AbstractRobustConnection: The connection object to RabbitMQ.

        Raises:
            AMQPException: If there is an error connecting to RabbitMQ.
        """
        while True:
            if self.connection is None or self.connection.is_closed:
                try:
                    self.connection = await connect_robust(self.amqp_url)
                    logger.info("Connection to RabbitMQ established successfully.")
                except AMQPException as e:
                    logger.error(
                        f"Failed to connect to RabbitMQ: {e}. Retrying in 1 second..."
                    )
                    await asyncio.sleep(1)
            else:
                break
        return self.connection

    async def close_connection(self) -> None:
        """Closes the connection to RabbitMQ.

        This method checks if the connection is open and, if so, attempts to close it.
        It logs the outcome of the operation.

        Raises:
            AMQPException: If there is an error closing the connection to RabbitMQ.
        """
        if self.connection and not self.connection.is_closed:
            try:
                await self.connection.close()
                logger.info("Connection to RabbitMQ closed successfully.")
            except AMQPException as e:
                logger.error(f"Failed to close connection to RabbitMQ: {e}")
