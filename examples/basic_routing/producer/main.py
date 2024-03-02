import logging
import asyncio
from fast_rabbit import FastRabbitEngine


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

RABBIT_MQ_URL = "amqp://user:password@rabbitmq"


fast_rabbit = FastRabbitEngine(RABBIT_MQ_URL)


async def run_producer():
    for i in range(10):
        await fast_rabbit.publish("test_queue", f"Message {i}")
        await fast_rabbit.publish("example_router_queue", f"Message {i}")
        logger.info(f"Published message {i}")


if __name__ == "__main__":
    asyncio.run(run_producer())
