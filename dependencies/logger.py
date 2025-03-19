import logging
import sys

logger = logging.getLogger('KYCFabricLogger')
# iteratively removing default lambda log handlers
for h in logger.handlers:
    logger.removeHandler(h)

FORMAT = '[%(levelname)s] %(message)s'
h = logging.StreamHandler(sys.stdout)
h.setFormatter(logging.Formatter(FORMAT))

logger = logging.getLogger(__name__)
logger.addHandler(h)
logger.setLevel(logging.INFO)
logger.propagate = False
