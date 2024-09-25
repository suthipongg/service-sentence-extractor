import pytest
from unittest.mock import patch
from configs.config import SettingsManager, Settings, get_env_file, get_project_enviroment


@patch('os.getenv')
def test_get_project_environment(mock_getenv):
    mock_getenv.return_value = 'test'
    assert get_project_enviroment() == 'test'
    mock_getenv.assert_called_with('ENVIRONMENT', 'dev')

@patch('os.getenv')
def test_get_env_file(mock_getenv):
    mock_getenv.return_value = 'test'
    assert get_env_file() == 'configs/.env.test'

class TestSettingsManager:  
    @patch('configs.config.load_dotenv')
    def test_initialize_settings(self, mock_load_dotenv):
        manager = SettingsManager.initialize()
        assert manager is not None
        assert isinstance(SettingsManager.settings, Settings)
        mock_load_dotenv.assert_called_with('configs/.env.dev')
    
    def test_singleton_behavior(self):
        manager1 = SettingsManager()
        manager2 = SettingsManager()
        assert manager1 is manager2

    @patch('configs.config.set_key')
    @patch('configs.config.load_dotenv')
    def test_update_settings(self, mock_load_dotenv, mock_set_key):
        mock_set_key.return_value = None
        manager = SettingsManager()
        manager.update_setting('host_ip', '127.0.0.1')
        mock_set_key.assert_called_with('configs/.env.dev', 'host_ip', '127.0.0.1')
        mock_load_dotenv.assert_called()

    def test_error_when_not_initialized(self):
        SettingsManager._instance = None
        with pytest.raises(ValueError, match="SettingsManager is not initialized."):
            SettingsManager.update_setting('host_ip', '127.0.0.1')