from unittest.mock import patch, MagicMock

from configs.db import MongoDBConnection, MGCollection


class MockENVConnect:
    MONGODB_DB = 'test_db'
    MONGODB_HOST = 'localhost'
    MONGODB_PORT = 27017
    MONGODB_USER = ''
    MONGODB_PASSWORD = ''
@patch('configs.db.ENV', MockENVConnect)
def test_connect_mongodb(mock_mongo_client):
    MongoDBConnection.mongo_client = None
    mongo_conn = MongoDBConnection.connect_mongodb()
    assert mongo_conn is mock_mongo_client.return_value
    mock_mongo_client.assert_called_once_with('mongodb://localhost:27017/test_db')
    mock_mongo_client.return_value.admin.command.assert_called_once()

class MockENVConnectUser:
    MONGODB_DB = 'test_db'
    MONGODB_HOST = 'localhost'
    MONGODB_PORT = 27017
    MONGODB_USER = 'user'
    MONGODB_PASSWORD = 'pass'
@patch('configs.db.ENV', MockENVConnectUser)
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

def test_mongo_initialization(mock_mongo_client):
    MongoDBConnection.mongo_client = None
    mongo_conn = MongoDBConnection()
    assert mongo_conn.mongo_client is mock_mongo_client.return_value
    mock_mongo_client.assert_called_once()


class MockENV:
    MONGODB_DB = 'test_db'
    USERS_COLLECTION_NAME = 'users_collection'
    ORDERS_COLLECTION_NAME = 'orders_collection'
    __private_var = 'should_not_be_included'
    CALLABLE_COLLECTION_NAME = lambda: 'should_not_be_callable'
@patch('configs.db.MongoDBConnection')
@patch('configs.db.ENV', MockENV)
def test_init_collection(mock_db_connection):
    mock_db_connection.return_value = MagicMock()
    mock_db_connection.return_value.mongo_client = {
        'test_db': {
            'users_collection': MagicMock(name='users_collection'),
            'orders_collection': MagicMock(name='orders_collection')
        }
    }

    mongo_collection = MGCollection()

    assert mongo_collection.USERS == mock_db_connection().mongo_client['test_db']['users_collection']
    assert mongo_collection.ORDERS == mock_db_connection().mongo_client['test_db']['orders_collection']

    assert not hasattr(mongo_collection, '__private_var')
    assert not hasattr(mongo_collection, 'CALLABLE')