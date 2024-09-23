import logging

class LoggerConfig:
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.disabled = False

    logger = logging.getLogger("uvicorn")
    logger.setLevel(logging.getLevelName(logging.DEBUG))