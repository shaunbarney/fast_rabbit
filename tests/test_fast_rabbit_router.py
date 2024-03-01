import pytest
from fast_rabbit.fast_rabbit import FastRabbitEngine


@pytest.mark.asyncio
async def test_consumer_callback():
    engine = FastRabbitEngine(amqp_url="amqp://user:pass@localhost")
    # Define a mock consumer function
    async def mock_consumer(message):
        assert message == "test message"

    # Register the mock consumer
    engine.subscribe("test_queue")(mock_consumer)
    # Simulate receiving a message
    await engine._start_consumer("test_queue", engine.subscriptions["test_queue"])
    # Here you would need to mock the queue.consume method to call the mock_consumer with a test message
