import logging

from configs.logger import LoggerConfig


def test_uvicorn_access_logger_state():
    logger = LoggerConfig.uvicorn_access
    assert not logger.disabled

def test_uvicorn_logger_level():
    logger = LoggerConfig.logger
    assert logger.level == logging.DEBUG

def test_uvicorn_logger_disabled_state():
    logger = LoggerConfig.uvicorn_access
    assert not logger.disabled