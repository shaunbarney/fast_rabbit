# Fast Rabbit Documentation

Fast Rabbit is an advanced, asynchronous RabbitMQ client for Python, designed to simplify the integration and management of RabbitMQ interactions. It provides a robust and efficient way to publish and consume messages asynchronously, leveraging the power of `asyncio` and `aio_pika`.

## Table of Contents

- [Installation](#installation)
- [Getting Started](#getting-started)
  - [Setting Up the Engine](#setting-up-the-engine)
  - [Publishing Messages](#publishing-messages)
  - [Consuming Messages](#consuming-messages)
- [Advanced Usage](#advanced-usage)
  - [Routing with FastRabbitRouter](#routing-with-fastrabbitrouter)
  - [Error Handling](#error-handling)
- [Contributing](#contributing)
- [License](#license)

## Installation

To install Fast Rabbit, run the following command in your terminal:

```bash
pip install fast_rabbit
```

Ensure you have Python 3.7 or newer, as Fast Rabbit leverages the latest features of `asyncio`.

## Getting Started

### Setting Up the Engine

First, initialize the `FastRabbitEngine` with your RabbitMQ server's AMQP URL:

```python
from fast_rabbit import FastRabbitEngine

engine = FastRabbitEngine(amqp_url="amqp://user:password@localhost/")
```

### Publishing Messages

To publish messages to a queue, use the `publish` method:

```python
await engine.publish("queue_name", "Hello, RabbitMQ!")
```

### Consuming Messages

To consume messages, you first define a handler function and then register it for a specific queue:

```python
async def message_handler(body: str):
    print(f"Received message: {body}")

engine.subscribe("queue_name")(message_handler)

await engine.run()
```

## Advanced Usage

### Routing with FastRabbitRouter

`FastRabbitRouter` allows you to organize your message handlers similarly to routing in web frameworks like FastAPI. This is particularly useful for larger applications with multiple message types and queues.

#### Defining Routes

Create a `FastRabbitRouter` instance and use the `route` decorator to register message handlers:

```python
from fast_rabbit import FastRabbitRouter

router = FastRabbitRouter()

@router.route("queue_name")
async def handle_message(body: str):
    print(f"Received message: {body}")
```

#### Including Routes in the Engine

Once your routes are defined, include them in the `FastRabbitEngine` instance:

```python
engine.include_subscriptions(router)
```

#### Running the Engine

Start the engine to begin consuming messages:

```python
await engine.run()
```

### Error Handling

Fast Rabbit is designed to robustly handle connection and channel errors. However, you should implement your own error handling within message handlers to manage application-specific errors gracefully.

## Contributing

Contributions to Fast Rabbit are welcome! Please refer to the project's issues page to report bugs or suggest features. For pull requests, kindly follow the project's coding standards and include tests for new functionality.

## License

Fast Rabbit is released under the MIT License. See the LICENSE file in the project repository for more details.

