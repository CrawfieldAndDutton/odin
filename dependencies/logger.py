# Standard library imports
import sys
import logging


logger = logging.getLogger(__name__)

formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

stream_handler = logging.StreamHandler(sys.stdout)

file_handler = logging.FileHandler('logs.log')

stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.handlers = [stream_handler, file_handler]

logger.setLevel(logging.INFO)
