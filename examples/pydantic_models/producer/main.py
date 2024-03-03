import random
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


def create_random_user() -> User:
    names = ["Alice", "Bob", "Charlie", "David", "Eve"]
    return User(name=random.choice(names), age=random.randint(18, 100))


async def run_producer():
    for i in range(10):
        user = create_random_user()
        await fast_rabbit.publish("user", user)
        logger.info(f"Published user {user.name} with age {user.age} - {i}")


if __name__ == "__main__":
    asyncio.run(run_producer())
