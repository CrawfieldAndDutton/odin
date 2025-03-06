import time
from fastapi import Request
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
