import asyncio
import pytest
from fast_rabbit.fast_rabbit import FastRabbitEngine


@pytest.mark.asyncio
async def test_publish_and_consume_multiple_messages():
    amqp_url = "amqp://user:password@localhost"
    test_queue = "multi_msg_test_queue"
    test_messages = ["Hello, RabbitMQ!", "Goodbye, RabbitMQ!"]
    received_messages = []

    engine = FastRabbitEngine(amqp_url)
    test_complete = asyncio.Event()

    async def multi_message_consumer(message: str):
        received_messages.append(message)
        # Check if all messages have been received
        if set(received_messages) == set(test_messages):
            test_complete.set()

    engine.subscribe(test_queue)(multi_message_consumer)
    consumer_task = asyncio.create_task(engine.run())

    # Publish all test messages
    for msg in test_messages:
        await engine.publish(test_queue, msg)

    await asyncio.wait_for(test_complete.wait(), timeout=10)

    # Use the shutdown method for cleanup
    await engine.shutdown()

    # Cancel the consumer task after shutting down the engine
    consumer_task.cancel()
    await asyncio.gather(consumer_task, return_exceptions=True)

    # Assert that all messages were received
    assert set(received_messages) == set(
        test_messages
    ), "Not all messages were received"


@pytest.fixture(autouse=True)
async def cleanup():
    yield
    # Assuming log_pending_tasks is implemented as suggested
    await log_pending_tasks()  # Log pending tasks for debugging
    # Cancel and await all remaining tasks
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


async def log_pending_tasks():
    for task in asyncio.all_tasks():
        if not task.done():
            print(f"Pending task detected: {task}, {task.get_coro()}")
