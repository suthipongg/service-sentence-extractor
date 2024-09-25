from unittest.mock import patch, MagicMock

from configs.db import MongoDBConnection, MGCollection
from configs.config import SettingsManager

class MockMongoSetting:
    mongodb_db = 'test_db'
    mongodb_host = 'localhost'
    mongodb_port = 27017
    mongodb_user = ''
    mongodb_password = ''
@patch.object(SettingsManager, 'settings', MockMongoSetting)
def test_connect_mongodb(mock_mongo_client):
    MongoDBConnection.mongo_client = None
    mongo_conn = MongoDBConnection.connect_mongodb()
    assert mongo_conn is mock_mongo_client.return_value
    mock_mongo_client.assert_called_once_with('mongodb://localhost:27017/test_db')
    mock_mongo_client.return_value.admin.command.assert_called_once()

class MockMongoUSERSetting:
    mongodb_db = 'test_db'
    mongodb_host = 'localhost'
    mongodb_port = 27017
    mongodb_user = 'user'
    mongodb_password = 'pass'
@patch.object(SettingsManager, 'settings', MockMongoUSERSetting)
def test_connect_mongodb_with_user(mock_mongo_client):
    MongoDBConnection.mongo_client = None
    mongo_conn = MongoDBConnection.connect_mongodb()
    assert mongo_conn is mock_mongo_client.return_value
    mock_mongo_client.assert_called_once_with('mongodb://user:pass@localhost:27017/test_db')
    mock_mongo_client.return_value.admin.command.assert_called_once()


def test_check_mongo_connection_success(mock_mongo_client, mock_logger_info):
    mock_client = mock_mongo_client.return_value
    mock_client.admin.command.return_value = True

    MongoDBConnection.mongo_client = mock_client
    assert MongoDBConnection.check_mongo_connection() is True
    mock_client.admin.command.assert_called_with('ping')
    mock_logger_info.assert_called_with("::: [\033[96mMongoDB\033[0m] connected \033[92msuccessfully\033[0m. :::")

def test_check_mongo_connection_failure(mock_mongo_client, mock_logger_info):
    mock_client = mock_mongo_client.return_value
    mock_client.admin.command.side_effect = Exception("Connection failed")

    MongoDBConnection.mongo_client = mock_client
    assert MongoDBConnection.check_mongo_connection() is False
    mock_logger_info.assert_called()


def test_mongo_already_initialized(mock_mongo_client, mock_logger_info):
    MongoDBConnection.mongo_client = MagicMock()
    assert MongoDBConnection.check_mongo_connection() is True
    mock_logger_info.assert_called_with("::: [\033[96mMongoDB\033[0m] connected \033[92msuccessfully\033[0m. :::")
    mock_mongo_client.assert_not_called()


@patch.object(SettingsManager, 'settings', MockMongoSetting)
def test_mongo_initialization(mock_mongo_client):
    MongoDBConnection.mongo_client = None
    mongo_conn = MongoDBConnection()
    assert mongo_conn.mongo_client is mock_mongo_client.return_value
    mock_mongo_client.assert_called_once()


class MockMongo:
    mongodb_db = 'test_db'
    @classmethod
    def model_dump(cls):
        return {
            'users_collection_name': 'users_collection',
            'orders_collection_name': 'orders_collection',
            '__private_var': 'should_not_be_included',
            'CALLABLE_collection_name': lambda: 'should_not_be_callable'
        }
@patch.object(SettingsManager, 'settings', MockMongo)
@patch('configs.db.MongoDBConnection.connect_mongodb')
def test_init_collection(mock_db_connection):
    mock_db_connection.return_value = {
        'test_db': {
            'users_collection': MagicMock(name='users_collection'),
            'orders_collection': MagicMock(name='orders_collection')
        }
    }

    mongo_collection = MGCollection()

    assert mongo_collection.USERS == mock_db_connection()['test_db']['users_collection']
    assert mongo_collection.ORDERS == mock_db_connection()['test_db']['orders_collection']

    assert not hasattr(mongo_collection, '__private_var')
    assert not hasattr(mongo_collection, 'CALLABLE')