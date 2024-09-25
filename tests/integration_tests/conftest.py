import pytest
from fastapi.testclient import TestClient

from app import app

from configs.config import SettingsManager
from configs.db import ESIndex
from controllers.elasticsearch_controller import ElasticsearchCRUD
from controllers.mongodb_controller import MongoDBCRUD

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown_database():
    yield
    ElasticsearchCRUD.es_client.indices.delete(index=ESIndex.EXTRACTED)
    MongoDBCRUD.mongo_client.drop_database(SettingsManager.settings.mongodb_db)

@pytest.fixture(scope="session")
def valid_auth_token():
    return "Bearer dev"