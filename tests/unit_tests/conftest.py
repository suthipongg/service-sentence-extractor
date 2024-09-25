import pytest
from unittest.mock import patch

from configs.logger import LoggerConfig
from configs.db import ElasticsearchConnection
from configs.config import SettingsManager

@pytest.fixture(scope='function')
def mock_settings_manager():
    with patch.object(SettingsManager, 'settings') as mock:
        yield mock

@pytest.fixture(scope="function")
def mock_logger_info():
    with patch.object(LoggerConfig.logger, "info") as mock:
        yield mock

@pytest.fixture(scope="function")
def mock_logger_error():
    with patch.object(LoggerConfig.logger, "error") as mock:
        yield mock

@pytest.fixture(scope='function')
def mock_mongo_client():
    with patch('configs.db.MongoClient') as mock:
        yield mock

@pytest.fixture(scope='function')
def mock_es_client():
    with patch('configs.db.Elasticsearch') as mock:
        yield mock

@pytest.fixture(scope='function')
def mock_es_client_attr():
    with patch.object(ElasticsearchConnection, 'es_client') as mock:
        yield mock

@pytest.fixture(scope='function')
def mock_apm_client():
    with patch('configs.db.ApmClient') as mock:
        yield mock

@pytest.fixture(scope="function")
def mock_apm_capture_exp():
    with patch.object(ElasticsearchConnection, 'apm_capture_exception') as mock:
        yield mock