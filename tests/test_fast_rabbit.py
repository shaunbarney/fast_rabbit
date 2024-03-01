import pytest
from unittest.mock import AsyncMock  # Import AsyncMock
from fast_rabbit.fast_rabbit import FastRabbitEngine


@pytest.mark.asyncio
async def test_publish():
    engine = FastRabbitEngine(amqp_url="amqp://user:pass@localhost")

    # Use AsyncMock to mock the _get_channel method
    engine._get_channel = AsyncMock()

    # Create a mock channel using AsyncMock
    mock_channel = AsyncMock()
    mock_channel.declare_queue = AsyncMock()

    # Mock the default_exchange.publish method to be an AsyncMock
    mock_channel.default_exchange.publish = AsyncMock()

    engine.channels["default"] = mock_channel

    # Test the publish method
    await engine.publish("test_queue", "Hello, World!")

    # Assert that the publish method was called once
    mock_channel.default_exchange.publish.assert_called_once()
