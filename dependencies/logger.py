# Standard library imports
import sys
import logging


logger = logging.getLogger(__name__)

formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
stream_handler.stream.reconfigure(encoding='utf-8')

file_handler = logging.FileHandler('logs.log', encoding='utf-8')

stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.handlers = [stream_handler, file_handler]

logger.setLevel(logging.INFO)
