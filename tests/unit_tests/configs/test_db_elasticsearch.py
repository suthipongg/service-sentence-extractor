from unittest.mock import patch, MagicMock

from configs.db import ElasticsearchConnection, ESIndex
from configs.config import SettingsManager


class MockESSetting:
    es_host = 'localhost'
    es_port = 9200
    es_version = '7.10.2'
    es_user = ''
    es_password = ''
@patch.object(SettingsManager, 'settings', MockESSetting)
def test_connect_elasticsearch(mock_es_client):
    ElasticsearchConnection.es_client = None
    es_client = ElasticsearchConnection.connect_elasticsearch()
    assert es_client is mock_es_client.return_value
    assert es_client is ElasticsearchConnection.es_client
    mock_es_client.assert_called_once_with(
        host='localhost',
        port=9200,
        api_version='7.10.2',
        timeout=60*60,
        use_ssl=False,
    )
    mock_es_client.return_value.ping.assert_called_once()


class MockESSetting:
    es_host = 'localhost'
    es_port = 9200
    es_version = '7.10.2'
    es_user = 'user'
    es_password = 'pass'
@patch.object(SettingsManager, 'settings', MockESSetting)
def test_connect_elasticsearch_with_user(mock_es_client):
    ElasticsearchConnection.es_client = None
    es_client = ElasticsearchConnection.connect_elasticsearch()
    assert es_client is mock_es_client.return_value
    assert es_client is ElasticsearchConnection.es_client
    mock_es_client.assert_called_once_with(
        host='localhost',
        port=9200,
        api_version='7.10.2',
        timeout=60*60,
        use_ssl=False,
        http_auth=('user', 'pass')
    )
    mock_es_client.return_value.ping.assert_called_once()


def test_check_elasticsearch_connection_success(mock_es_client, mock_logger_info):
    mock_es_instance = mock_es_client.return_value
    mock_es_instance.ping.return_value = True

    ElasticsearchConnection.es_client = mock_es_instance
    assert ElasticsearchConnection.check_elasticsearch_connection() is True

    mock_es_instance.ping.assert_called_once()
    mock_logger_info.assert_called_with("::: [\033[96mElasticsearch\033[0m] connected \033[92msuccessfully\033[0m. :::")

def test_check_elasticsearch_connection_failure(mock_es_client, mock_logger_info, mock_logger_error):
    mock_es_instance = mock_es_client.return_value
    mock_es_instance.ping.return_value = False

    ElasticsearchConnection.es_client = mock_es_instance
    assert ElasticsearchConnection.check_elasticsearch_connection() is False

    mock_logger_error.assert_not_called()
    mock_logger_info.assert_called_with("\033[91mFailed\033[0m to connect to [\033[96mElasticsearch\033[0m].")
    mock_es_instance.ping.assert_called_once()

def test_check_elasticsearch_connection_exception(mock_es_client, mock_logger_info, mock_logger_error):
    mock_es_instance = mock_es_client.return_value
    mock_es_instance.ping.side_effect = Exception("Connection error")

    ElasticsearchConnection.es_client = mock_es_instance
    assert ElasticsearchConnection.check_elasticsearch_connection() is False

    mock_logger_info.assert_not_called()
    mock_logger_error.assert_called_with("\033[91mError\033[0m to connect to [\033[96mElasticsearch\033[0m]: Connection error")
    mock_es_instance.ping.assert_called_once()


class MockAPMSetting:
    apm_service_name = 'test_service'
    apm_environment = 'test_env'
    apm_server_url = 'http://localhost'
@patch('requests.get', MagicMock())
@patch.object(SettingsManager, 'settings', MockAPMSetting)
def test_connect_apm_service_initializes_client(mock_apm_client, mock_logger_info):
    ElasticsearchConnection.apm_client = None
    result = ElasticsearchConnection.connect_apm_service()
    # Check that APM client is initialized
    mock_apm_client.assert_called_once_with({
        'SERVICE_NAME': 'test_service',
        'ENVIRONMENT': 'test_env',
        'SERVER_URL': 'http://localhost'
    })
    assert result == mock_apm_client.return_value
    mock_logger_info.assert_any_call("Initializing APM client...")

def test_connect_apm_service_already_initialized(mock_logger_info):
    ElasticsearchConnection.apm_client = MagicMock()
    result = ElasticsearchConnection.connect_apm_service()
    assert result == ElasticsearchConnection.apm_client
    mock_logger_info.assert_called_with("APM client already initialized.")

def test_get_apm_client_initialized():
    ElasticsearchConnection.apm_client = MagicMock()
    result = ElasticsearchConnection.get_apm_client()
    assert result == ElasticsearchConnection.apm_client


@patch.object(SettingsManager, 'settings', MockAPMSetting)
@patch('requests.get')
def test_check_apm_connection_success(mock_request, mock_logger_info):
    mock_request.return_value.status_code = 200  # Simulate successful connection
    assert ElasticsearchConnection.check_apm_connection() is True
    mock_logger_info.assert_called_with("::: [\033[96mAPM\033[0m] connected \033[92msuccessfully\033[0m. :::")

@patch.object(SettingsManager, 'settings', MockAPMSetting)
@patch('requests.get')
def test_check_apm_connection_failure(mock_request, mock_logger_info, mock_logger_error):
    mock_request.return_value.status_code = 500
    assert ElasticsearchConnection.check_apm_connection() is False
    mock_logger_info.assert_called_with("\033[91mFailed\033[0m to connect to [\033[96mAPM\033[0m].")
    mock_logger_error.assert_not_called()

@patch.object(SettingsManager, 'settings', MockAPMSetting)
@patch('requests.get')
def test_check_apm_connection_exception(mock_request, mock_logger_info, mock_logger_error):
    mock_request.side_effect = Exception("Connection error")
    assert ElasticsearchConnection.check_apm_connection() is False
    mock_logger_info.assert_not_called()
    mock_logger_error.assert_called_with("\033[91mError\033[0m to connect to [\033[96mAPM\033[0m]: Connection error")


@patch('requests.get', MagicMock())
@patch.object(ElasticsearchConnection, 'connect_apm_service')
def test_get_apm_client_not_initialized(mock_connect_apm_service):
    ElasticsearchConnection.apm_client = None
    ElasticsearchConnection.get_apm_client()
    mock_connect_apm_service.assert_called_once()

def test_apm_capture_exception(mock_logger_info):
    ElasticsearchConnection.apm_client = MagicMock()
    ElasticsearchConnection.apm_capture_exception()
    ElasticsearchConnection.apm_client.capture_exception.assert_called_once()
    mock_logger_info.assert_called_once_with("Exception captured in APM client.")


class MockESESAPMSetting:
    es_host = 'localhost'
    es_port = 9200
    es_version = '7.10.2'
    es_user = ''
    es_password = ''
    apm_service_name = 'test_service'
    apm_environment = 'test_env'
    apm_server_url = 'http://localhost'
@patch.object(SettingsManager, 'settings', MockESESAPMSetting)
@patch('requests.get', MagicMock())
def test_elasticsearch_connection_initialization(mock_es_client, mock_apm_client, mock_logger_info):
    ElasticsearchConnection.es_client = None
    ElasticsearchConnection.apm_client = None
    es_conn = ElasticsearchConnection()
    assert es_conn.es_client is mock_es_client.return_value
    assert es_conn.apm_client is mock_apm_client.return_value
    mock_es_client.assert_called_once()
    mock_apm_client.assert_called_once()
    mock_logger_info.assert_called()

@patch('requests.get')
def test_elasticsearch_connection_already_initialized(mock_request, mock_es_client, mock_logger_info):
    mock_request.return_value.status_code = 200
    ElasticsearchConnection.es_client = MagicMock()
    ElasticsearchConnection.apm_client = MagicMock()
    es_conn = ElasticsearchConnection()
    assert es_conn.check_elasticsearch_connection() is True
    assert ElasticsearchConnection.check_apm_connection() is True
    mock_logger_info.assert_any_call("::: [\033[96mElasticsearch\033[0m] connected \033[92msuccessfully\033[0m. :::")
    mock_logger_info.assert_any_call("::: [\033[96mAPM\033[0m] connected \033[92msuccessfully\033[0m. :::")
    mock_es_client.assert_not_called()


class MockESIndexSetting:
    sentences_vector_size = 512
    @classmethod
    def model_dump(cls):
        return {
            'example_index_name': 'example_index',
            'other_index_name': 'other_index',
            '__private_var': 'should_not_be_included',
            'callable_index_name': lambda: 'should_not_be_callable'
        }
class MockConfigs:
    EXAMPLE_CONFIG = {'setting': 'value'}
    OTHER_CONFIG = {'setting': 'other_value'}
    __private_var = 'should_not_be_included'
    CALLABLE_CONFIG = lambda: 'should_not_be_callable'
@patch.object(SettingsManager, 'settings', MockESIndexSetting)
@patch('configs.db.ElasticsearchIndexConfigs', MockConfigs)
def test_elasticsearch_index_initialization():
    es_index = ESIndex()
    expected_all_index = {
        'EXAMPLE': 'example_index',
        'OTHER': 'other_index',
    }
    assert es_index.all_index_name == expected_all_index

    assert es_index.EXAMPLE == 'example_index'
    assert es_index.OTHER == 'other_index'

    expected_all_config = {
        'EXAMPLE': {'setting': 'value'},
        'OTHER': {'setting': 'other_value'},
    }
    assert es_index.all_index_config == expected_all_config

    assert not hasattr(es_index, '__private_var')
    assert not hasattr(es_index, 'CALLABLE')

    for key in expected_all_index.keys():
        assert getattr(es_index, key) == expected_all_index[key]