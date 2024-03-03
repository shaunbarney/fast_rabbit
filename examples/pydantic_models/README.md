# Basic Example Documentation

## Overview

This documentation covers the setup and operation of a basic messaging system using RabbitMQ with a producer and consumer model. The system is containerised using Docker, facilitating easy deployment and scalability. The example demonstrates how to send messages from a producer service to a RabbitMQ queue, which are then consumed by a consumer service.

## Prerequisites

- Docker and Docker Compose installed on your machine.
- Basic understanding of Docker, Python, and asynchronous programming.

## Architecture

The system comprises three main components:

1. **RabbitMQ Server**: A RabbitMQ service with management interface enabled.
2. **Producer**: A Python application that publishes messages to a RabbitMQ queue.
3. **Consumer**: A Python application that subscribes to the RabbitMQ queue and processes messages.

## Docker Configuration

The `docker-compose.yml` file defines the services, networks, and volumes for our application:

- **RabbitMQ Service**: Configured with default user credentials and exposes ports for AMQP protocol and management interface. A named volume `rabbitmq_data` is used for data persistence.
- **Producer and Consumer Services**: Both are built from Dockerfiles located in their respective directories. They depend on the RabbitMQ service being available and mount their source code directories into the container for live editing.

### Volumes

- `rabbitmq_data`: Persists RabbitMQ data across container restarts.

## Producer Service

The producer service sends a series of messages to a specified queue in RabbitMQ.

### Key Components

- **FastRabbitEngine**: A custom Python class (assumed) for interacting with RabbitMQ.
- **run_producer**: An asynchronous function that publishes messages to the `test_queue`.

### Operation

The script connects to RabbitMQ using the provided URL, then enters a loop to publish ten messages to `test_queue`, logging each message sent.

## Consumer Service

The consumer service listens for messages on the specified queue and processes them as they arrive.

### Key Components

- **FastRabbitEngine**: Utilised for setting up a subscription to RabbitMQ.
- **test_consumer**: An asynchronous callback function that processes each message received from `test_queue`.

### Operation

Upon starting, the consumer logs its initiation, then runs indefinitely, processing incoming messages and logging each one.

## Running the Example

1. Start the services using Docker Compose:
   ```bash
   docker-compose up --build
   ```
2. Monitor the logs to see the messages being produced and consumed.

## Conclusion

This basic example demonstrates a simple but effective pattern for asynchronous message processing with RabbitMQ in a Dockerised environment. It showcases the power of combining Docker, RabbitMQ, and Python's asynchronous capabilities for building scalable and efficient messaging systems.

