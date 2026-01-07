import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S',
)

logger = logging.getLogger(__name__)

def info(message):
    logger.info(message)

def error(message):
    logger.error(message)

def warn(message):
    logger.warning(message)

def debug(message):
    logger.debug(message)
