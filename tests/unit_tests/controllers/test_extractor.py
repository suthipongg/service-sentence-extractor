import pytest
from unittest.mock import MagicMock, patch

from controllers.extractor import SentenceExtractor


@pytest.fixture(scope='module')
def mock_embedding_model():
    mock_model = MagicMock()
    mock_model.encode.return_value = {'dense_vecs': ['mock_dense_vec']}
    mock_model.count_tokenizer.return_value = 42
    return mock_model

@pytest.fixture(scope='module')
def mock_import_module(mock_embedding_model):
    with patch('controllers.extractor.importlib.import_module') as mock_import:
        mock_module = MagicMock()
        mock_module.EmbeddingModel.return_value = mock_embedding_model
        mock_import.return_value = mock_module
        yield mock_import


def test_toggle_loading():
    SentenceExtractor._loading = False
    assert SentenceExtractor._toggle_loading() == True, "Loading was not toggled"
    assert SentenceExtractor._toggle_loading() == False, "Loading was not toggled"


@patch('controllers.extractor.SentenceExtractor._toggle_loading')
def test_singleton_instance(mock_toggle, mock_import_module, mock_logger_info):
    start_call_count = mock_logger_info.call_count
    
    SentenceExtractor._toggle_loading = MagicMock()
    instance1 = SentenceExtractor()
    assert instance1._toggle_loading.call_count == 2, "_toggle_loading was not called twice"
    
    instance2 = SentenceExtractor()
    assert instance2._toggle_loading.call_count == 2, "_toggle_loading was not called twice"
    assert instance1 is instance2, "SentenceExtractor is not following Singleton pattern"
    assert mock_logger_info.call_count - start_call_count == 2, "Logger was not called twice"
    assert mock_import_module.call_count == 1, "import_module was not called once"

def test_singleton_initialization(mock_import_module, mock_logger_info):
    start_call_count = mock_logger_info.call_count
    instance = SentenceExtractor()
    
    assert hasattr(instance, 'model'), "SentenceExtractor model was not initialized"
    assert instance.model is not None, "SentenceExtractor model is None"
    assert instance.model == mock_import_module.return_value.EmbeddingModel.return_value
    assert mock_logger_info.call_count - start_call_count == 0, "Logger was called during initialization"

def test_singleton_thread_safety(mock_import_module):
    import threading
    
    def create_instance():
        instance = SentenceExtractor()
        return instance
    
    threads = [threading.Thread(target=create_instance) for _ in range(10)]
    
    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join()

    instances = [create_instance() for _ in range(10)]
    assert all(inst == instances[0] for inst in instances), "Singleton pattern is not thread-safe"


def test_extract(mock_embedding_model):
    sentence_extractor = SentenceExtractor()
    list_text = ['Hello, world!']
    expected_output = ['mock_dense_vec']

    result = sentence_extractor.extract(list_text)

    assert result == expected_output
    mock_embedding_model.encode.assert_called_once_with(list_text)


def test_compute_token(mock_embedding_model):
    sentence_extractor = SentenceExtractor()
    sentence = 'Hello, world!'
    expected_token_count = 42

    result = sentence_extractor.compute_token(sentence)
    assert result == expected_token_count

    mock_embedding_model.count_tokenizer.assert_called_once_with(sentence)