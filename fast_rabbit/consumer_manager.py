import inspect
from pydantic import BaseModel
from aio_pika.exceptions import AMQPException

from fast_rabbit import logger
from .channel_manager import ChannelManager


class ConsumerManager:
    def __init__(self, channel_manager: ChannelManager):
        self.channel_manager = channel_manager
        self.subscriptions = {}

    def subscribe(self, queue_name: str):
        def decorator(func):
            self.subscriptions[queue_name] = func
            return func

        return decorator

    async def _start_consumer(self, queue_name: str):
        channel = await self.channel_manager.get_channel()
        try:
            queue = await channel.declare_queue(queue_name, durable=True)
        except AMQPException as e:
            logger.error(f"Failed to declare queue '{queue_name}': {e}")
            raise

        async def message_handler(message):
            async with message.process():
                try:
                    func = self.subscriptions[queue_name]
                    params = inspect.signature(func).parameters
                    model_type = None
                    for param in params.values():
                        if issubclass(param.annotation, BaseModel):
                            model_type = param.annotation
                            break
                    if model_type:
                        data = model_type.parse_raw(message.body.decode())
                    else:
                        data = message.body.decode()
                    await func(data)
                except Exception as e:
                    logger.error(f"Error processing message for '{queue_name}': {e}")

        await queue.consume(message_handler)
        logger.info(f"Consumer started for queue '{queue_name}'.")

    async def start_consumers(self):
        for queue_name in self.subscriptions.keys():
            await self._start_consumer(queue_name)
