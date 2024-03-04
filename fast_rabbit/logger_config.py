import logging


def setup_logger(name):
    """
    Configures and returns a logger with the given name.

    Args:
        name (str): The name of the logger to configure.

    Returns:
        logging.Logger: The configured logger instance.
    """
    # Configure the logging format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create a logger and set its level
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create a console handler and set its level and formatter
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(ch)

    return logger


# Create a global logger instance for the application
logger = setup_logger("FastRabbit")
