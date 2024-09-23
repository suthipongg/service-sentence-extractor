from fastapi import Request

import http
import time
from datetime import datetime

from configs.logger import LoggerConfig

class ANSIColors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'

async def log_all_request_middleware(request: Request, call_next):
    url = f"{request.url.path}?{request.query_params}" if request.query_params else request.url.path
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = "{0:.2f}".format(process_time)
    try:
        status_phrase = http.HTTPStatus(response.status_code).phrase
        if 200 <= response.status_code < 300:
            status_phrase = f'{ANSIColors.GREEN}{status_phrase}{ANSIColors.RESET}'
        else:
            status_phrase = f'{ANSIColors.RED}{status_phrase}{ANSIColors.RESET}'
    except ValueError:
        status_phrase = f"{ANSIColors.YELLOW}Unknown status code{ANSIColors.RESET}"
        LoggerConfig.logger.info(f"Unknown status code: {response.status_code}")

    current_datetime = datetime.now().isoformat()

    # eg. format: 2024-01-01T00:00:00.000000 - "GET /ping" 200 OK 1.00ms
    LoggerConfig.logger.info(f'{current_datetime} - "{request.method} {url}" {response.status_code} {status_phrase} {formatted_process_time}ms')
    return response
