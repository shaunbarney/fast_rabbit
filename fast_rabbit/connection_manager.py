import asyncio
import logging
from aio_pika import connect_robust
from aio_pika.exceptions import AMQPException

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self, amqp_url: str):
        self.amqp_url = amqp_url
        self.connection = None

    async def get_connection(self):
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

    async def close_connection(self):
        if self.connection and not self.connection.is_closed:
            try:
                await self.connection.close()
                logger.info("Connection to RabbitMQ closed successfully.")
            except AMQPException as e:
                logger.error(f"Failed to close connection to RabbitMQ: {e}")
