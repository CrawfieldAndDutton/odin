# Standard library imports
import time

# Third-party library imports
from fastapi import Request

# Local application imports
from dependencies.logger import logger


async def log_middleware(request: Request, call_next):
    start = time.time()

    response = await call_next(request)
    process_time = time.time()-start
    log_dict = {
        "url": request.url,
        "method": request.method,
        "process_time": process_time,
    }
    logger.info(log_dict, extra=log_dict)
    return response
