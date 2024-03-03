import logging
import asyncio
from pydantic import BaseModel
from fast_rabbit import FastRabbitEngine


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

RABBIT_MQ_URL = "amqp://user:password@rabbitmq"


fast_rabbit = FastRabbitEngine(RABBIT_MQ_URL)


class User(BaseModel):
    name: str
    age: int


@fast_rabbit.subscribe("user")
async def user_consumer(user: User):
    logger.info(f"Received user")
    logger.info(f"Name: {user.name}")
    logger.info(f"Age: {user.age}")


async def main():
    logger.info("Starting consumer")
    await fast_rabbit.run()


if __name__ == "__main__":
    asyncio.run(main())
