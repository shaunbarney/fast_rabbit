<p align="center">
  <img src="./assets/logo.png" alt="Fast Rabbit Logo" width="400"/>
</p>

<h1 align="center">Fast Rabbit: Asynchronous RabbitMQ Client for Python</h1>

<p align="center">
  <a href="https://github.com/shaunbarney/fast_rabbit/releases">
    <img src="https://img.shields.io/github/v/release/shaunbarney/fast_rabbit?include_prereleases&style=flat-square" alt="GitHub release (latest by date including pre-releases)">
  </a>
  <a href="https://github.com/shaunbarney/fast_rabbit/commits/main">
    <img src="https://img.shields.io/github/last-commit/shaunbarney/fast_rabbit?style=flat-square" alt="GitHub last commit">
  </a>
  <a href="https://github.com/shaunbarney/fast_rabbit/issues">
    <img src="https://img.shields.io/github/issues-raw/shaunbarney/fast_rabbit?style=flat-square" alt="GitHub open issues">
  </a>
  <a href="https://github.com/shaunbarney/fast_rabbit/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/shaunbarney/fast_rabbit?style=flat-square" alt="License">
  </a>
</p>

# Fast Rabbit: Asynchronous RabbitMQ Client for Python

Fast Rabbit is an advanced, asynchronous RabbitMQ client designed to simplify the integration and management of RabbitMQ interactions within your Python applications. Leveraging the power of `asyncio` and `aio_pika`, Fast Rabbit provides a robust framework for message publishing and consuming, with an emphasis on simplicity, efficiency, and reliability.

## Features

- **Asynchronous API**: Built on top of `asyncio`, allowing for non-blocking message operations.
- **Easy Consumer Registration**: Utilize decorators to effortlessly register message consumer coroutines.
- **Automatic Connection Management**: Handles connection and channel lifecycle, including reconnections.
- **Flexible Routing**: Incorporate a router similar to FastAPI for organised message handling based on queue names.
- **Prefetch Control**: Easily configure the prefetch count for consumers to optimize message throughput and consumer workload.
- **Message Prioritisation**: Supports prioritising messages to ensure that critical messages are processed before others, enhancing the responsiveness and efficiency of applications.
- **Custom Error Handling**: Offers sophisticated error handling capabilities, including automatic retries with exponential backoff and dead-letter routing for messages that fail processing.

## Installation

Install Fast Rabbit using pip:

```bash
pip install fast_rabbit
```

## Quick Start

### Publishing Messages

```python
import asyncio
from fast_rabbit import FastRabbitEngine


RABBIT_MQ_URL = "amqp://user:password@localhost"
fast_rabbit = FastRabbitEngine(RABBIT_MQ_URL)

async def run_producer():
    for i in range(10):
        await fast_rabbit.publish("test_queue", f"Message {i}")
        print(f"Published message {i}")


if __name__ == "__main__":
    asyncio.run(run_producer())
```

### Consuming Messages

Define your message handlers and register them as consumers for specific queues:

```python
import asyncio
from fast_rabbit import FastRabbitEngine


RABBIT_MQ_URL = "amqp://user:password@localhost"
fast_rabbit = FastRabbitEngine(RABBIT_MQ_URL)

@fast_rabbit.subscribe("test_queue")
async def test_consumer(message: str):
    print(f"Received message: {message}")


if __name__ == "__main__":
    asyncio.run(fast_rabbit.run())
```

## Example Upgrade

In this example, we showcase how message prioritisation, prefetch count, and Pydantic modelling can streamline message handling in Fast Rabbit. Prioritisation ensures urgent messages are processed first, enhancing system responsiveness. The prefetch count optimises workload by controlling how many messages are processed concurrently. Pydantic models validate and structure message data, improving code quality and maintainability. Together, these features form a robust framework for efficient, reliable messaging tailored to specific application needs.

### Publish Message

```python
import asyncio
from pydantic import BaseModel
from fast_rabbit import FastRabbitEngine

class Message(BaseModel):
    name: str
    price: int
    is_offer: Optional[bool] = None

async def run_producer():
    fast_rabbit = FastRabbitEngine(amqp_url="amqp://user:password@localhost")
    
    high_priority_message = Message(name="Urgent", price=100, is_offer=True)
    low_priority_message = Message(name="Regular", price=50, is_offer=False)
    
    # Publish a high priority message
    await fast_rabbit.publish("test_queue", high_priority_message, priority=5)
    print("Published high priority message")
    
    # Publish a low priority message
    await fast_rabbit.publish("test_queue", low_priority_message, priority=1)
    print("Published low priority message")

if __name__ == "__main__":
    asyncio.run(run_producer())
```

### Consuming Messages

```python
import asyncio
from pydantic import BaseModel
from fast_rabbit import FastRabbitEngine

class Message(BaseModel):
    name: str
    price: int
    is_offer: Optional[bool] = None

fast_rabbit = FastRabbitEngine(amqp_url="amqp://user:password@localhost")

@fast_rabbit.subscribe("test_queue", prefetch_count=10)
async def test_consumer(message: Message):
    print(f"Message name: {message.name}")
    print(f"Message price: {message.price}")
    if message.is_offer:
        print("Message is an offer")

if __name__ == "__main__":
    asyncio.run(fast_rabbit.run())
```
## Documentation

For more detailed documentation, including API reference and advanced usage, please refer to the [Fast Rabbit Documentation](./documentation/DOCUMENTATION.md).

## Contributing

Contributions are welcome! Please read our [Contributing Guide](./documentation/CONTRIBUTING.md) for details on how to submit pull requests, report issues, and suggest improvements.

## License

Fast Rabbit is released under the MIT License. See the [LICENSE](LICENSE) file for more details.

---

Fast Rabbit aims to provide a high-quality, easy-to-use asynchronous RabbitMQ client for the Python community. Whether you're building microservices, distributed systems, or just need a reliable way to handle message queues, Fast Rabbit is designed to meet your needs with minimal overhead and maximum efficiency.
