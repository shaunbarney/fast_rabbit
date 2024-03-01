import logging
import asyncio
from fast_rabbit import FastRabbitEngine


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

RABBIT_MQ_URL = "amqp://user:password@rabbitmq"

fast_rabbit = FastRabbitEngine(RABBIT_MQ_URL)


@fast_rabbit.subscribe("test_queue")
async def test_consumer(message: str):
    logger.info(f"Received message: {message}")


async def main():
    await fast_rabbit.run()


if __name__ == "__main__":
    asyncio.run(main())
