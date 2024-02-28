# Fast Rabbit: Asynchronous RabbitMQ Client for Python

Fast Rabbit is an advanced, asynchronous RabbitMQ client designed to simplify the integration and management of RabbitMQ interactions within your Python applications. Leveraging the power of `asyncio` and `aio_pika`, Fast Rabbit provides a robust framework for message publishing and consuming, with an emphasis on simplicity, efficiency, and reliability.

## Features

- **Asynchronous API**: Built on top of `asyncio`, allowing for non-blocking message operations.
- **Easy Consumer Registration**: Utilize decorators to effortlessly register message consumer coroutines.
- **Automatic Connection Management**: Handles connection and channel lifecycle, including reconnections.
- **Flexible Routing**: Incorporate a router similar to FastAPI for organised message handling based on queue names.

## Installation

Install Fast Rabbit using pip:

```bash
pip install fast_rabbit
```

## Quick Start

### Publishing Messages

```python
from fast_rabbit import FastRabbitEngine

engine = FastRabbitEngine(amqp_url="amqp://user:password@localhost/")

await engine.publish("queue_name", "Hello, RabbitMQ!")
```

### Consuming Messages

Define your message handlers and register them as consumers for specific queues:

```python
from fast_rabbit import FastRabbitEngine, FastRabbitRouter

engine = FastRabbitEngine(amqp_url="amqp://user:password@localhost/")

@router.route("queue_name")
async def handle_message(body: str):
    print(f"Received message: {body}")

await engine.run()
```

## Documentation

For more detailed documentation, including API reference and advanced usage, please refer to the [Fast Rabbit Documentation](./documentation/DOCUMENTATION.md).

## Contributing

Contributions are welcome! Please read our [Contributing Guide](./documentation/CONTRIBUTING.md) for details on how to submit pull requests, report issues, and suggest improvements.

## License

Fast Rabbit is released under the MIT License. See the [LICENSE](LICENSE) file for more details.

---

Fast Rabbit aims to provide a high-quality, easy-to-use asynchronous RabbitMQ client for the Python community. Whether you're building microservices, distributed systems, or just need a reliable way to handle message queues, Fast Rabbit is designed to meet your needs with minimal overhead and maximum efficiency.
