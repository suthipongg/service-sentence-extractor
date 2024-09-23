import urllib.parse
import requests

from pymongo import MongoClient
from elasticsearch import Elasticsearch
from elasticapm import Client as ApmClient

from configs.environment import ENV
from configs.es_model import ElasticsearchIndexConfigs
from configs.logger import LoggerConfig

class MongoDBConnection:
    mongo_client = None

    def __new__(cls):
        cls.connect_mongodb()
        return super().__new__(cls)

    @classmethod
    def connect_mongodb(cls):
        if cls.mongo_client is None:
            mongodb_uri = f"{ENV.MONGODB_HOST}:{int(ENV.MONGODB_PORT)}/{ENV.MONGODB_DB}"
            use_authentication = ENV.MONGODB_USER and ENV.MONGODB_PASSWORD
            if use_authentication:
                mongodb_uri = f"{urllib.parse.quote_plus(ENV.MONGODB_USER)}:{urllib.parse.quote_plus(ENV.MONGODB_PASSWORD)}@" + mongodb_uri
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

class MGCollection:
    start_collection = None

    def __new__(cls) -> None:
        cls.init_collection()
        return super().__new__(cls)
    
    @classmethod
    def init_collection(cls):
        if cls.start_collection is None:
            mongo_connect = MongoDBConnection()
            mongo_db = mongo_connect.mongo_client[ENV.MONGODB_DB]
            suffix_collection = '_COLLECTION_NAME'
            for variable_name, value in vars(ENV).items():
                is_collection_name_variable = not callable(value) and not variable_name.startswith('__') and suffix_collection in variable_name
                if is_collection_name_variable:
                    variable_name = variable_name.split(suffix_collection)[0]
                    collection = mongo_db[value]
                    setattr(cls, variable_name, collection)
            cls.start_collection = True
        return cls.start_collection


class ElasticsearchConnection:
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
                "host": ENV.ES_HOST,
                "port": int(ENV.ES_PORT),
                "api_version": ENV.ES_VERSION,
                "timeout": 60 * 60,
                "use_ssl": False
            }
            use_authentication = ENV.ES_USER and ENV.ES_PASSWORD
            if use_authentication:
                es_config["http_auth"] = (ENV.ES_USER, ENV.ES_PASSWORD)

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
                'SERVICE_NAME': ENV.APM_SERVICE_NAME,
                'ENVIRONMENT': ENV.APM_ENVIRONMENT,
                'SERVER_URL': ENV.APM_SERVER_URL
            })
            cls.check_apm_connection()
        else:
            LoggerConfig.logger.info("APM client already initialized.")

        return cls.apm_client
    
    @classmethod
    def check_apm_connection(cls):
        try:
            if requests.get(f"{ENV.APM_SERVER_URL}/", timeout=1).status_code == 200:
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


class ESIndex:
    all_index_name = {}
    all_index_config = {}

    def __new__(cls):
        cls.init_index()
        return super().__new__(cls)
    
    @classmethod
    def init_index(cls):
        not_started_index = not cls.all_index_name or not cls.all_index_config
        if not_started_index:
            suffix_index = '_INDEX_NAME'
            for variable_name, value in vars(ENV).items():
                is_index_name_variable = not callable(value) and not variable_name.startswith('__') and suffix_index in variable_name
                if is_index_name_variable:
                    variable_name = variable_name.split(suffix_index)[0]
                    setattr(cls, variable_name, value)
                    cls.all_index_name[variable_name] = value

            suffix_config = '_CONFIG'
            for variable_name, value in vars(ElasticsearchIndexConfigs).items():
                is_config_name_variable = not callable(value) and not variable_name.startswith('__') and suffix_config in variable_name
                if is_config_name_variable:
                    variable_name = variable_name.split(suffix_config)[0]
                    cls.all_index_config[variable_name] = value
        return cls.all_index_name, cls.all_index_config