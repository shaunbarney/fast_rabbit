# Advanced Messaging with Pydantic Models and Fast RabbitMQ

## Overview

This documentation details an advanced messaging system that leverages Pydantic models for data validation and type safety in a producer-consumer setup using Fast RabbitMQ. The system demonstrates how Pydantic models defined in the producer can be seamlessly used in the consumer's function signature, allowing for dynamic casting of message data to usable Python objects. This approach ensures that data passed through RabbitMQ queues is strongly typed and conforms to the expected structure, enhancing the robustness and reliability of the application.

## System Components

### Pydantic Models

Pydantic models play a central role in this system by defining the data schema for messages. These models ensure that data conforms to a specified format, providing automatic data validation and error handling for messages in transit.

#### User Model

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int
```

- **Description**: Defines a user with a name and age.
- **Usage**: Used by both the producer and consumer to ensure consistent data structure and validation.

### Producer

The producer is responsible for creating and sending messages that conform to the Pydantic model.

#### Key Features

- **Random User Generation**: Dynamically creates instances of the `User` model with random data.
- **Message Publishing**: Sends instances of the `User` model to a specified RabbitMQ queue.

#### Implementation Highlights

```python
async def run_producer():
    for i in range(10):
        user = create_random_user()
        await fast_rabbit.publish("user", user)) 
        logger.info(f"Published user {user.name} with age {user.age}")
```

- **Dynamic Casting**: The `User` instance is converted to JSON for transmission. The consumer will receive this JSON and dynamically cast it back to a `User` object.

### Consumer

The consumer subscribes to the RabbitMQ queue, receives messages, and processes them using the Pydantic model directly in the function signature.

#### Key Features

- **Dynamic Message Casting**: Automatically converts incoming messages to Pydantic model instances.
- **Data Processing**: Implements business logic on the validated and typed data.

#### Implementation Highlights

```python
@fast_rabbit.subscribe("user")
async def user_consumer(user: User):
    logger.info(f"Received user {user.name} with age {user.age}")
```

- **Automatic Conversion**: The `fast_rabbit.subscribe` decorator and Fast RabbitMQ engine handle the dynamic casting of JSON messages to the `User` model, allowing the function to directly use the `User` instance.

### Operation

Upon starting, the consumer logs its initiation, then runs indefinitely, processing incoming messages and logging each one.

## Running the Example

1. Start the services using Docker Compose:
   ```bash
   docker-compose up --build
   ```
2. Monitor the logs to see the messages being produced and consumed.

## Benefits and Considerations

- **Type Safety**: Ensures that all messages conform to the defined data model, reducing runtime errors.
- **Data Validation**: Leverages Pydantic's validation mechanisms to ensure data integrity.
- **Ease of Use**: Simplifies the producer and consumer code by abstracting data serialisation and deserialisation.
- **Flexibility**: Supports complex data structures and validations through Pydantic's extensive features.

## Conclusion

Utilising Pydantic models in conjunction with Fast RabbitMQ provides a powerful pattern for building reliable and scalable messaging systems in Python. This approach not only enforces data integrity and type safety but also simplifies the development process by automating data conversion and validation tasks.


