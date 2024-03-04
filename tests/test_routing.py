import asyncio
import pytest
from pydantic import BaseModel

from fast_rabbit.fast_rabbit import FastRabbitEngine, FastRabbitRouter


class User(BaseModel):
    name: str
    age: int


# Define a second test message for the FastRabbitRouter
class Admin(BaseModel):
    username: str
    level: int


@pytest.mark.asyncio
async def test_publish_and_consume_messages():
    amqp_url = "amqp://user:password@localhost"
    user_queue = "user_queue"
    admin_queue = "admin_queue"
    user_message = User(name="John", age=30)
    admin_message = Admin(username="admin", level=5)

    engine = FastRabbitEngine(amqp_url)
    test_complete_user = asyncio.Event()
    test_complete_admin = asyncio.Event()

    async def user_consumer(message: User):
        assert message.age == user_message.age
        assert message.name == user_message.name
        test_complete_user.set()

    async def admin_consumer(message: Admin):
        assert message.username == admin_message.username
        assert message.level == admin_message.level
        test_complete_admin.set()

    # Subscribe the base engine consumer
    engine.subscribe(user_queue)(user_consumer)

    # Setup FastRabbitRouter and subscribe the second consumer
    router = FastRabbitRouter()
    router.subscribe(admin_queue)(admin_consumer)
    engine.include_subscriptions(router)

    # Start consuming messages
    consumer_task = asyncio.create_task(engine.run())

    # Publish messages to both queues
    await engine.publish(user_queue, user_message)
    await engine.publish(admin_queue, admin_message)

    # Wait for both messages to be consumed
    await asyncio.wait_for(test_complete_user.wait(), timeout=10)
    await asyncio.wait_for(test_complete_admin.wait(), timeout=10)

    # Cleanup
    await engine.shutdown()
    consumer_task.cancel()
    await asyncio.gather(consumer_task, return_exceptions=True)


@pytest.fixture(autouse=True)
async def cleanup():
    yield
    await log_pending_tasks()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


async def log_pending_tasks():
    for task in asyncio.all_tasks():
        if not task.done():
            print(f"Pending task detected: {task}, {task.get_coro()}")
