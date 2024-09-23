import pytest
from unittest.mock import patch

import torch

from configs.environment import ENV
from model_ai.base_encoder import BaseEncoder


@patch('model_ai.base_encoder.ENV')
def test_base_encoder_init(mock_env):
    mock_env.DEVICE = 'cuda'
    with patch('torch.cuda.is_available', return_value=True):
        encoder = BaseEncoder()
        assert encoder.device == 'cuda'

    mock_env.DEVICE = 'cpu'
    with patch('torch.cuda.is_available', return_value=False):
        encoder = BaseEncoder()
        assert encoder.device == 'cpu'

    with patch('torch.cuda.is_available', return_value=False):
        encoder = BaseEncoder()
        assert encoder.device == 'cpu'

    with patch('torch.cuda.is_available', return_value=True):
        encoder = BaseEncoder()
        assert encoder.device == 'cpu'

def test_encode_raises_not_implemented_error():
    encoder = BaseEncoder()
    with pytest.raises(NotImplementedError):
        encoder.encode("test text")

def test_count_tokenizer_raises_not_implemented_error():
    encoder = BaseEncoder()
    with pytest.raises(NotImplementedError):
        encoder.count_tokenizer("test sentence")

def test_convert_pt_type():
    encoder = BaseEncoder()
    mock_tensor = torch.tensor([1.0, 2.0, 3.0])
    
    result = encoder.convert_pt_type(mock_tensor, 'pt')
    assert torch.equal(result, mock_tensor)
    
    result = encoder.convert_pt_type(mock_tensor, 'np')
    assert (result == mock_tensor.cpu().numpy()).all()
    
    result = encoder.convert_pt_type(mock_tensor, 'ls')
    assert result == mock_tensor.cpu().numpy().tolist()
    
    with pytest.raises(ValueError):
        encoder.convert_pt_type(mock_tensor, 'invalid')

def test_convert_pt_type_empty_tensor():
    encoder = BaseEncoder()
    empty_tensor = torch.tensor([])
    
    result = encoder.convert_pt_type(empty_tensor, 'pt')
    assert torch.equal(result, empty_tensor)
    
    result = encoder.convert_pt_type(empty_tensor, 'np')
    assert (result == empty_tensor.cpu().numpy()).all()
    
    result = encoder.convert_pt_type(empty_tensor, 'ls')
    assert result == empty_tensor.cpu().numpy().tolist()

def test_convert_pt_type_non_tensor():
    encoder = BaseEncoder()
    non_tensor_input = [1, 2, 3]
    
    with pytest.raises(TypeError):
        encoder.convert_pt_type(non_tensor_input, 'pt')

def test_convert_pt_invalid_target_type():
    encoder = BaseEncoder()
    non_tensor_input = torch.tensor([])
    
    with pytest.raises(ValueError):
        encoder.convert_pt_type(non_tensor_input, 'invalid')

def testconvert_pt_type_large_tensor():
    encoder = BaseEncoder()
    large_tensor = torch.randn(10000) 
    
    result = encoder.convert_pt_type(large_tensor, 'pt')
    assert torch.equal(result, large_tensor)
    
    result = encoder.convert_pt_type(large_tensor, 'np')
    assert (result == large_tensor.cpu().numpy()).all()
    
    result = encoder.convert_pt_type(large_tensor, 'ls')
    assert result == large_tensor.cpu().numpy().tolist()