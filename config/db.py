import os
from pymongo import MongoClient
from elasticsearch import Elasticsearch
import urllib.parse
from config.environment import ENV

env = ENV()

mongodb_db = env.MONGODB_DB
def get_mongo_connection():
    # Load MongoDB connection details from environment variables
    mongodb_user = env.MONGODB_USER
    mongodb_password = env.MONGODB_PASSWORD
    mongodb_host = env.MONGODB_HOST
    mongodb_port = int(env.MONGODB_PORT)
    mongodb_db = env.MONGODB_DB

    # Create a MongoDB URI with authentication
    if mongodb_user and mongodb_password:
        mongodb_uri = f"mongodb://{urllib.parse.quote_plus(mongodb_user)}:{urllib.parse.quote_plus(mongodb_password)}@{mongodb_host}:{mongodb_port}/{mongodb_db}"
    else:
        mongodb_uri = f"mongodb://{mongodb_host}:{mongodb_port}/{mongodb_db}"

    return MongoClient(mongodb_uri)

# Establish a connection to the MongoDB server
db_connection = get_mongo_connection()

# Access your MongoDB collections
db = db_connection[mongodb_db]
extracted_collection = db[env.MONGODB_COLLECTION_EXTRACTED]


# Define Elasticsearch configuration
es_config = {
    "host": env.ES_HOST,
    "port": int(env.ES_PORT),  # Convert port to integer
    "api_version": env.ES_VERSION,
    "timeout": 60 * 60,
    "use_ssl": False
}

# Check if authentication variables are defined in .env
es_user = env.ES_USER
es_password = env.ES_PASSWORD

# Add HTTP authentication to the configuration if username and password are provided
if es_user and es_password:
    es_config["http_auth"] = (es_user, es_password)

# Create an Elasticsearch client instance
es_client = Elasticsearch(**es_config)

def check_elasticsearch_connection():
    try:
        if es_client.ping():
            print("::: [\033[96mElasticsearch\033[0m] connected \033[92msuccessfully\033[0m. :::")
        else:
            print("\033[91mFailed\033[0m to connect to [\033[96mElasticsearch\033[0m].")
    except Exception as e:
        print(f"\033[91mFailed\033[0m to connect to [\033[96mElasticsearch\033[0m]: {e}")

def check_mongo_connection():
    try:
        # Establish a connection to the MongoDB server
        db_connection = get_mongo_connection()

        # Attempt to list the databases
        db_connection.admin.command('ping')
        print("::: [\033[96mMongoDB\033[0m] connected \033[92msuccessfully\033[0m. :::")
        return True
    except Exception as e:
        print(f"\033[91mFailed\033[0m to connect to [\033[96mMongoDB\033[0m]: {e}")
        return False