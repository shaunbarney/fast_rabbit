import logging
from fast_rabbit import FastRabbitRouter

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = FastRabbitRouter()


@router.subscribe("example_router_queue")
async def example_router_queue(message: str):
    logging.info(f"Router received message: {message}")
