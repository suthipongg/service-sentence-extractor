import urllib.parse
import requests

from pymongo import MongoClient
from elasticsearch import Elasticsearch
from elasticapm import Client as ApmClient

from configs.config import SettingsManager
from configs.es_model import ElasticsearchIndexConfigs
from configs.logger import LoggerConfig

class MongoDBConnection(SettingsManager):
    mongo_client = None

    def __new__(cls):
        cls.connect_mongodb()
        return super().__new__(cls)

    @classmethod
    def connect_mongodb(cls):
        if cls.mongo_client is None:
            mongodb_uri = f"{cls.settings.mongodb_host}:{int(cls.settings.mongodb_port)}/{cls.settings.mongodb_db}"
            use_authentication = cls.settings.mongodb_user and cls.settings.mongodb_password
            if use_authentication:
                mongodb_uri = f"{urllib.parse.quote_plus(cls.settings.mongodb_user)}:{urllib.parse.quote_plus(cls.settings.mongodb_password)}@" + mongodb_uri
            mongodb_uri = "mongodb://" + mongodb_uri

            cls.mongo_client = MongoClient(mongodb_uri)
            cls.check_mongo_connection()
        return cls.mongo_client

    @classmethod
    def check_mongo_connection(cls):
        try:
            cls.mongo_client.admin.command('ping')
            LoggerConfig.logger.info("::: [\033[96mMongoDB\033[0m] connected \033[92msuccessfully\033[0m. :::")
            return True
        except Exception as e:
            LoggerConfig.logger.info(f"\033[91mFailed\033[0m to connect to [\033[96mMongoDB\033[0m]: {e}")
            return False

class MGCollection(SettingsManager):
    start_collection = None

    def __new__(cls) -> None:
        cls.init_collection()
        return super().__new__(cls)
    
    @classmethod
    def init_collection(cls):
        if cls.start_collection is None:
            mongo_client = MongoDBConnection.connect_mongodb()
            mongo_db = mongo_client[cls.settings.mongodb_db]
            suffix_collection = '_collection_name'
            for variable_name, value in cls.settings.model_dump().items():
                is_collection_name_variable = not callable(value) and not variable_name.startswith('__') and suffix_collection in variable_name.lower()
                if is_collection_name_variable:
                    variable_name = variable_name.lower().split(suffix_collection)[0].upper()
                    collection = mongo_db[value]
                    setattr(cls, variable_name, collection)
            cls.start_collection = True
        return cls.start_collection


class ElasticsearchConnection(SettingsManager):
    apm_client = None
    es_client = None

    def __new__(cls):
        cls.connect_elasticsearch()
        cls.connect_apm_service()
        return super().__new__(cls)

    @classmethod
    def connect_elasticsearch(cls):
        if cls.es_client is None:
            es_config = {
                "host": cls.settings.es_host,
                "port": cls.settings.es_port,
                "api_version": cls.settings.es_version,
                "timeout": 60 * 60,
                "use_ssl": False
            }
            use_authentication = cls.settings.es_user and cls.settings.es_password
            if use_authentication:
                es_config["http_auth"] = (cls.settings.es_user, cls.settings.es_password)

            cls.es_client = Elasticsearch(**es_config)
            cls.check_elasticsearch_connection()
        return cls.es_client

    @classmethod
    def check_elasticsearch_connection(cls):
        try:
            if cls.es_client.ping():
                LoggerConfig.logger.info("::: [\033[96mElasticsearch\033[0m] connected \033[92msuccessfully\033[0m. :::")
                return True
            else:
                LoggerConfig.logger.info("\033[91mFailed\033[0m to connect to [\033[96mElasticsearch\033[0m].")
                return False
        except Exception as e:
            LoggerConfig.logger.error(f"\033[91mError\033[0m to connect to [\033[96mElasticsearch\033[0m]: {e}")
            return False


    @classmethod
    def connect_apm_service(cls):
        if cls.apm_client is None:
            LoggerConfig.logger.info("Initializing APM client...")
            cls.apm_client = ApmClient({
                'SERVICE_NAME': cls.settings.apm_service_name,
                'ENVIRONMENT': cls.settings.apm_environment,
                'SERVER_URL': cls.settings.apm_server_url
            })
            cls.check_apm_connection()
        else:
            LoggerConfig.logger.info("APM client already initialized.")

        return cls.apm_client
    
    @classmethod
    def check_apm_connection(cls):
        try:
            if requests.get(f"{cls.settings.apm_server_url}/", timeout=1).status_code == 200:
                LoggerConfig.logger.info("::: [\033[96mAPM\033[0m] connected \033[92msuccessfully\033[0m. :::")
                return True
            else:
                LoggerConfig.logger.info("\033[91mFailed\033[0m to connect to [\033[96mAPM\033[0m].")
                return False
        except Exception as e:
            LoggerConfig.logger.error(f"\033[91mError\033[0m to connect to [\033[96mAPM\033[0m]: {e}")
            return False

    @classmethod
    def get_apm_client(cls):
        if cls.apm_client is None:
            cls.connect_apm_service()
        return cls.apm_client
    
    @classmethod
    def apm_capture_exception(cls):
        cls.get_apm_client().capture_exception()
        LoggerConfig.logger.info("Exception captured in APM client.")


class ESIndex(SettingsManager, ElasticsearchIndexConfigs):
    all_index_name = {}
    all_index_config = {}

    def __new__(cls):
        cls.init_index()
        return super().__new__(cls)
    
    @classmethod
    def init_index(cls):
        not_started_index = not cls.all_index_name or not cls.all_index_config
        if not_started_index:
            suffix_index = '_index_name'
            for variable_name, value in cls.settings.model_dump().items():
                is_index_name_variable = not callable(value) and not variable_name.startswith('__') and suffix_index in variable_name.lower()
                if is_index_name_variable:
                    variable_name = variable_name.lower().split(suffix_index)[0].upper()
                    setattr(cls, variable_name, value)
                    cls.all_index_name[variable_name] = value

            suffix_config = '_config'
            for variable_name, value in vars(ElasticsearchIndexConfigs).items():
                is_config_name_variable = not callable(value) and not variable_name.startswith('__') and suffix_config in variable_name.lower()
                if is_config_name_variable:
                    variable_name = variable_name.lower().split(suffix_config)[0].upper()
                    cls.all_index_config[variable_name] = value
        return cls.all_index_name, cls.all_index_config