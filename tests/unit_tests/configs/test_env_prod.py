import warnings, os
from pathlib import Path
import torch
from dotenv import dotenv_values

config = dotenv_values("configs/.env.prod")

expected_attributes = [
    'HOST_IP',
    'PREFIX', 
    'API_TOKEN', 

    'APM_SERVICE_NAME', 
    'APM_ENVIRONMENT',
    'APM_SERVER_URL', 

    'ES_HOST', 
    'ES_PORT', 
    'ES_VERSION', 
    'ES_USER', 
    'ES_PASSWORD',
    'EXTRACTED_INDEX_NAME',

    'MONGODB_DB', 
    'MONGODB_USER', 
    'MONGODB_PASSWORD',
    'MONGODB_HOST', 
    'MONGODB_PORT', 
    'EXTRACTED_COLLECTION_NAME',

    'MODEL_FILE_NAME',
    'MODEL_NAME',
    'SENTENCES_VECTOR_SIZE',
    'DEVICE'
]


def test_env_class_attributes_exist():
    for attr in expected_attributes:
        assert attr in config, f"Attribute '{attr}' does not exist in ENV class"


def test_amount_of_env_class_attributes():
    num_of_attributes = len(expected_attributes)
    num_of_attributes_in_env_class = len(config)
    assert num_of_attributes == num_of_attributes_in_env_class, f"ENV class should have {num_of_attributes} attributes"


def test_env_class_attributes():
    assert config['HOST_IP'], f"HOST must be defined"
    if not config['PREFIX']: warnings.warn(UserWarning(f"Attribute PREFIX not defined from configs/environment.py in ENV class"))
    assert config['API_TOKEN'], f"API_TOKEN must be defined"

    assert config['APM_SERVICE_NAME'], f"APM_SERVICE_NAME must be defined"
    assert config['APM_ENVIRONMENT'], f"APM_ENVIRONMENT must be defined"
    assert config['APM_SERVER_URL'], f"APM_SERVER_URL must be defined"

    if not config['ES_HOST']: warnings.warn(UserWarning(f"Attribute ES_HOST not defined from configs/environment.py in ENV class"))
    if not config['ES_HOST']: warnings.warn(UserWarning(f"Attribute ES_HOST not defined from configs/environment.py in ENV class"))
    
    if not config['ES_HOST']: warnings.warn(UserWarning(f"Attribute ES_HOST not defined from configs/environment.py in ENV class"))
    if not config['ES_PORT']: warnings.warn(UserWarning(f"Attribute ES_PORT not defined from configs/environment.py in ENV class"))
    if not config['ES_VERSION']: warnings.warn(UserWarning(f"Attribute ES_VERSION not defined from configs/environment.py in ENV class"))
    assert config['EXTRACTED_INDEX_NAME'], f"NAME_INDEX_EXTRACETED must be defined"
    
    assert config['MONGODB_DB'], f"MONGODB_DB must be defined"
    if not config['MONGODB_HOST']: warnings.warn(UserWarning(f"Attribute MONGODB_HOST not defined from configs/environment.py in ENV class"))
    if not config['MONGODB_PORT']: warnings.warn(UserWarning(f"Attribute MONGODB_PORT not defined from configs/environment.py in ENV class"))
    assert config['EXTRACTED_COLLECTION_NAME'], f"MONGODB_COLLECTION_EXTRACTED must be defined"

    model_info = {
        'bge_m3_onnx': {"model_file_name": "bge_m3_onnx_o2", "sentence_vector_size": '1024'},
        'bge_m3': {"model_file_name": None, "sentence_vector_size": '1024'}
    }
    assert config['MODEL_NAME'], f"MODEL_NAME must be defined"
    assert config['MODEL_NAME'] in model_info, f"Invalid MODEL_NAME, should be one of {list(model_info.keys())}"
    if config['MODEL_NAME'] in model_info:
        if model_info[config['MODEL_NAME']]["model_file_name"]:
            assert config['MODEL_FILE_NAME'] == model_info[config['MODEL_NAME']]["model_file_name"], f"MODEL_FILE_NAME must be defined for {config['MODEL_NAME']}"
            assert os.path.exists(f"{str(Path(__file__).parents[3])}/model_ai/models/{config['MODEL_FILE_NAME']}"), f"MODEL_FILE_NAME does not exist"
        assert config['SENTENCES_VECTOR_SIZE'], f"SENTENCES_VECTOR_SIZE must be defined"
        assert config['SENTENCES_VECTOR_SIZE'] == model_info[config['MODEL_NAME']]["sentence_vector_size"], f"SENTENCES_VECTOR_SIZE must be defined for {config['MODEL_NAME']}"
    assert config['DEVICE'], f"DEVICE must be defined"
    assert config['DEVICE'] in ['cuda', 'cpu'], f"DEVICE must be either 'cuda' or 'cpu'"
    assert torch.cuda.is_available() or not (config['DEVICE'] == 'cuda'), f"cuda is not available"