import asyncio
from aio_pika import Message
from aio_pika.abc import AbstractIncomingMessage, AbstractChannel

from .logger_config import logger

from typing import Any


class ConsumerErrorHandler:
    """Handles errors during message processing."""

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        dead_letter_exchange: str = "dead_letter",
    ):
        """
        Initializes the ErrorHandler.

        Args:
            channel: Channel to use for publishing messages for retry or dead-lettering.
            max_retries: Maximum number of retries for a message before giving up.
            retry_delay: Initial delay between retries, in seconds. This delay increases exponentially.
            dead_letter_exchange: The name of the dead-letter exchange to which messages should be published if processing fails.
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.dead_letter_exchange = dead_letter_exchange

    async def handle_error(
        self, error: Any, message: AbstractIncomingMessage, channel: AbstractChannel
    ) -> None:
        """
        Handles an error that occurred during message processing.

        Args:
            error: The exception that was raised during message processing.
            message: The message that was being processed when the error occurred.
        """
        # Attempt to safely extract the retry count, handling various possible types
        retry_count_value = message.headers.get("x-retry-count", 0)

        # Ensure retry_count is an integer
        if isinstance(retry_count_value, int):
            retry_count = retry_count_value
        elif isinstance(retry_count_value, str):
            try:
                retry_count = int(retry_count_value)
            except ValueError:
                logger.warning(
                    f"Invalid retry count '{retry_count_value}' for message {message.message_id}, defaulting to 0."
                )
                retry_count = 0
        else:
            logger.warning(
                f"Unexpected type for retry count {type(retry_count_value)} for message {message.message_id}, defaulting to 0."
            )
            retry_count = 0

        if retry_count < self.max_retries:
            await self._retry_message(message, retry_count, channel)
        else:
            await self._dead_letter_message(message)
            logger.error(
                f"Message dead-lettered after {self.max_retries} retries: {error}"
            )

    async def _retry_message(
        self,
        message: AbstractIncomingMessage,
        retry_count: int,
        channel: AbstractChannel,
    ) -> None:
        """
        Retries processing a message after a delay, with exponential backoff.

        Args:
            message: The message to retry.
            retry_count: The current retry count for the message.
        """
        delay = self.retry_delay * (2**retry_count)
        await asyncio.sleep(delay)
        message.headers["x-retry-count"] = str(retry_count + 1)
        logger.info(
            f"Retrying message {message.message_id} (Attempt {retry_count + 1}) after {delay} seconds."
        )

        # Ensure a valid routing_key is used
        routing_key = (
            message.routing_key
            if message.routing_key is not None
            else "default_routing_key"
        )

        # Republish the message for retry
        await channel.default_exchange.publish(
            Message(body=message.body, headers=message.headers),
            routing_key=routing_key,
        )

    async def _dead_letter_message(self, message: AbstractIncomingMessage) -> None:
        """
        Moves a message to a dead-letter queue after retries are exhausted.

        Args:
            message: The message to dead-letter.
        """
        logger.info(f"Dead-lettering message {message.message_id}.")
        # Publish the message to the dead-letter exchange
        await self.channel.default_exchange.publish(
            Message(body=message.body, headers=message.headers),
            routing_key=self.dead_letter_exchange,
        )
