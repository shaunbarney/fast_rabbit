import asyncio
import pytest
from pydantic import BaseModel
from fast_rabbit.fast_rabbit import FastRabbitEngine


class User(BaseModel):
    name: str
    age: int


@pytest.mark.asyncio
async def test_publish_and_consume_simple_str():
    amqp_url = "amqp://user:password@localhost"
    test_queue = "pydantic_model_test_queue"
    test_message = User(name="John", age=30)

    engine = FastRabbitEngine(amqp_url)
    test_complete = asyncio.Event()

    async def simple_consumer(message: User):
        assert message.age == test_message.age
        assert message.name == test_message.name
        test_complete.set()

    engine.subscribe(test_queue)(simple_consumer)
    consumer_task = asyncio.create_task(engine.run())
    await engine.publish(test_queue, test_message)
    await asyncio.wait_for(test_complete.wait(), timeout=10)

    # Use the shutdown method for cleanup
    await engine.shutdown()

    # Cancel the consumer task after shutting down the engine
    consumer_task.cancel()
    await asyncio.gather(consumer_task, return_exceptions=True)


@pytest.fixture(autouse=True)
async def cleanup():
    yield
    # Log pending tasks for debugging
    await log_pending_tasks()  # Assuming log_pending_tasks is implemented as suggested
    # Cancel and await all remaining tasks
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


async def log_pending_tasks():
    for task in asyncio.all_tasks():
        if not task.done():
            print(f"Pending task detected: {task}, {task.get_coro()}")
