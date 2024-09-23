from fastapi import Request
from fastapi.responses import JSONResponse

import traceback

from configs.logger import LoggerConfig
from configs.db import ElasticsearchConnection


def log_and_capture_exception(exc: Exception):
    tb_frames  = traceback.extract_tb(exc.__traceback__)
    if tb_frames :
        last_trace = tb_frames [-1]
        fname = last_trace.filename
        lineno = last_trace.lineno
        LoggerConfig.logger.error(f"Error Type: {type(exc)}, File: {fname}, Line: {lineno}")
    else:
        LoggerConfig.logger.error(f"Error Type: {type(exc)}")

    tb_list = traceback.format_exception(type(exc), exc, exc.__traceback__)
    max_traceback_lines = 5
    tb_str = ''.join(tb_list [-max_traceback_lines:])
    LoggerConfig.logger.error(tb_str)
    
    ElasticsearchConnection.apm_capture_exception()

async def custom_exception_handler(request: Request, exc: Exception):
    log_and_capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )