from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv, set_key
import os

def get_project_enviroment():
    return os.getenv("ENVIRONMENT", "dev")

def get_env_file():
    return f'configs/.env.{get_project_enviroment()}'

class Settings(BaseSettings):
    host_ip: str
    prefix: str
    api_token: str

    mongodb_host: str
    mongodb_port: int
    mongodb_db: str
    mongodb_user: str
    mongodb_password: str
    extracted_collection_name: str

    es_host: str
    es_port: int
    es_version: str
    es_user: str
    es_password: str
    extracted_index_name: str

    apm_server_url: str
    apm_service_name: str
    apm_environment: str = get_project_enviroment()

    model_file_name: str
    model_name: str
    sentences_vector_size: int
    device: str

    model_config = SettingsConfigDict(
        env_file=get_env_file(),
        env_file_encoding='utf-8',
        protected_namespaces=('settings_',)
    )

class SettingsManager:
    _instance = None
    settings = None

    def __new__(cls):
        return cls.initialize()

    @classmethod
    def initialize(cls):
        if cls._instance is None:
            cls.settings = Settings()
            load_dotenv(get_env_file())
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def update_setting(cls, key: str, value: str):
        if cls._instance is None:
            raise ValueError("SettingsManager is not initialized.")
        set_key(get_env_file(), key, value)
        load_dotenv(get_env_file(), override=True)
        cls.settings = Settings()