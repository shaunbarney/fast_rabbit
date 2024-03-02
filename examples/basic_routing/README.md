# Basic Routing Example Documentation

## Overview

This example demonstrates a basic message routing setup using Docker, RabbitMQ, and a Python application with `fast_rabbit`. It includes a RabbitMQ service as the message broker, a producer service that sends messages, and a consumer service that receives messages through specific queues.

## Services

### RabbitMQ

- **Image**: `rabbitmq:3-management`
- **Description**: RabbitMQ service with management plugin enabled.
- **Environment Variables**:
  - `RABBITMQ_DEFAULT_USER`: Username for RabbitMQ access (default: `user`).
  - `RABBITMQ_DEFAULT_PASS`: Password for RabbitMQ access (default: `password`).
- **Ports**:
  - `5672`: Port for AMQP protocol.
  - `15672`: Port for RabbitMQ management interface.
- **Volumes**:
  - `rabbitmq_data`: Persistent volume for RabbitMQ data.

### Producer

- **Build Context**: `./producer`
- **Description**: Python application that publishes messages to RabbitMQ queues.
- **Dependencies**: Depends on the `rabbitmq` service being available.

### Consumer

- **Build Context**: `./consumer`
- **Description**: Python application that subscribes to RabbitMQ queues and processes incoming messages.
- **Dependencies**: Depends on the `rabbitmq` service being available.

## Consumer Application (`consumer/main.py`)

### Overview

The consumer application uses `FastRabbitEngine` to subscribe to queues and process messages asynchronously.

### Environment

- **RabbitMQ URL**: `amqp://user:password@rabbitmq` - Connection URL for RabbitMQ.

### Main Functionality

- Subscribes to the `test_queue` and processes messages by logging them.
- Utilises an asynchronous event loop to run the message processing engine.

## Consumer Router (`consumer/router/router.py`)

### Overview

Defines routing logic for messages using `FastRabbitRouter`.

### Routes

- `example_router_queue`: Subscribes to this queue and logs messages received.

## Producer Application (`producer/main.py`)

### Overview

Publishes messages to the `test_queue` and `example_router_queue` asynchronously.

### Environment

- **RabbitMQ URL**: `amqp://user:password@rabbitmq` - Connection URL for RabbitMQ.

### Main Functionality

- Publishes a series of messages to both `test_queue` and `example_router_queue`, demonstrating basic publishing functionality.

## Running the Example

1. Ensure Docker and Docker Compose are installed.
2. Navigate to the root directory of this example.
3. Run `docker-compose up --build` to start the services.
4. Observe the logs for message publishing and consumption.

## Conclusion

This example provides a basic framework for implementing message routing with RabbitMQ and Python using `fast_rabbit`. It demonstrates asynchronous message publishing and consumption, showcasing the power of event-driven architectures.

