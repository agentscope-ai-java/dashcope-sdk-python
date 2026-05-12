import logging
import sys

from dashscope.finetune.reinforcement.common.constants import LOGGER_NAME, \
    LOG_LEVEL


def setup_logger():
    """Initialize and configure the logger with value masking."""
    logger = logging.getLogger(LOGGER_NAME)
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    logger.setLevel(level_map.get(LOG_LEVEL, logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = setup_logger()
