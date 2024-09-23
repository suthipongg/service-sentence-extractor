import warnings, os
from pathlib import Path
import torch

from configs.environment import ENV


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
        assert hasattr(ENV, attr), f"Attribute '{attr}' does not exist in ENV class"

def test_amount_of_env_class_attributes():
    num_of_attributes = len(expected_attributes)
    num_of_attributes_in_env_class = len(
        [attr for attr in dir(ENV) if not callable(getattr(ENV, attr)) 
         and not attr.startswith("__")])
    assert num_of_attributes == num_of_attributes_in_env_class, f"ENV class should have {num_of_attributes} attributes"


def test_env_class_attributes():
    assert ENV.HOST_IP, f"HOST must be defined"
    if not ENV.PREFIX: warnings.warn(UserWarning(f"Attribute PREFIX not defined from configs/environment.py in ENV class"))
    assert ENV.API_TOKEN, f"API_TOKEN must be defined"

    assert ENV.APM_SERVICE_NAME, f"APM_SERVICE_NAME must be defined"
    assert ENV.APM_ENVIRONMENT, f"APM_ENVIRONMENT must be defined"
    assert ENV.APM_SERVER_URL, f"APM_SERVER_URL must be defined"

    if not ENV.ES_HOST: warnings.warn(UserWarning(f"Attribute ES_HOST not defined from configs/environment.py in ENV class"))
    if not ENV.ES_HOST: warnings.warn(UserWarning(f"Attribute ES_HOST not defined from configs/environment.py in ENV class"))
    
    if not ENV.ES_HOST: warnings.warn(UserWarning(f"Attribute ES_HOST not defined from configs/environment.py in ENV class"))
    if not ENV.ES_PORT: warnings.warn(UserWarning(f"Attribute ES_PORT not defined from configs/environment.py in ENV class"))
    if not ENV.ES_VERSION: warnings.warn(UserWarning(f"Attribute ES_VERSION not defined from configs/environment.py in ENV class"))
    assert ENV.EXTRACTED_INDEX_NAME, f"NAME_INDEX_EXTRACETED must be defined"
    
    assert ENV.MONGODB_DB, f"MONGODB_DB must be defined"
    if not ENV.MONGODB_HOST: warnings.warn(UserWarning(f"Attribute MONGODB_HOST not defined from configs/environment.py in ENV class"))
    if not ENV.MONGODB_PORT: warnings.warn(UserWarning(f"Attribute MONGODB_PORT not defined from configs/environment.py in ENV class"))
    assert ENV.EXTRACTED_COLLECTION_NAME, f"MONGODB_COLLECTION_EXTRACTED must be defined"

    model_info = {
        'bge_m3_onnx': {"model_file_name": "bge_m3_onnx_o2", "sentence_vector_size": 1024},
        'bge_m3': {"model_file_name": None, "sentence_vector_size": 1024}
    }
    assert ENV.MODEL_NAME, f"MODEL_NAME must be defined"
    assert ENV.MODEL_NAME in model_info, f"Invalid MODEL_NAME, should be one of {list(model_info.keys())}"
    if ENV.MODEL_NAME in model_info:
        if model_info[ENV.MODEL_NAME]["model_file_name"]:
            assert ENV.MODEL_FILE_NAME == model_info[ENV.MODEL_NAME]["model_file_name"], f"MODEL_FILE_NAME must be defined for {ENV.MODEL_NAME}"
            assert os.path.exists(f"{str(Path(__file__).parents[3])}/model_ai/models/{ENV.MODEL_FILE_NAME}"), f"MODEL_FILE_NAME does not exist"
        assert ENV.SENTENCES_VECTOR_SIZE, f"SENTENCES_VECTOR_SIZE must be defined"
        assert ENV.SENTENCES_VECTOR_SIZE == model_info[ENV.MODEL_NAME]["sentence_vector_size"], f"SENTENCES_VECTOR_SIZE must be defined for {ENV.MODEL_NAME}"
    assert ENV.DEVICE, f"DEVICE must be defined"
    assert ENV.DEVICE in ['cuda', 'cpu'], f"DEVICE must be either 'cuda' or 'cpu'"
    assert torch.cuda.is_available() or not (ENV.DEVICE == 'cuda'), f"cuda is not available"