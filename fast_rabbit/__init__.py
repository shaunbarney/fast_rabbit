import logging
from .fast_rabbit import FastRabbitEngine
from .fast_rabbit_router import FastRabbitRouter

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
