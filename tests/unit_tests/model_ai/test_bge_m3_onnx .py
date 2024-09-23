import pytest
from unittest.mock import patch, MagicMock

import torch
import numpy as np

from model_ai.bge_m3_onnx import EmbeddingModel

@pytest.fixture(scope='module')
def embedding_model_path_exist():
    with patch('model_ai.bge_m3_onnx.snapshot_download') as MockSnapshotDownload, \
        patch('optimum.onnxruntime.ORTModelForFeatureExtraction.from_pretrained') as MockAutoModel, \
        patch('transformers.AutoTokenizer.from_pretrained') as MockAutoTokenizer, \
        patch('os.path.exists') as MockPathExists, \
        patch('torch.load') as MockTorchLoad, \
        patch('torch.nn.Linear') as MockLinear:
        
        MockPathExists.return_value = True
        MockTorchLoad.return_value = MagicMock()
        MockSnapshotDownload = MagicMock()
        MockSnapshotDownload.return_value = 'mocked_model_path'
        MockAutoModel.return_value = MagicMock()
        MockAutoTokenizer.return_value = MagicMock()
        yield 

@pytest.fixture(scope='module')
def embedding_model_path_not_exist():
    with patch('model_ai.bge_m3_onnx.snapshot_download') as MockSnapshotDownload, \
        patch('optimum.onnxruntime.ORTModelForFeatureExtraction.from_pretrained') as MockAutoModel, \
        patch('transformers.AutoTokenizer.from_pretrained') as MockAutoTokenizer, \
        patch('os.path.exists') as MockPathExists, \
        patch('torch.load') as MockTorchLoad, \
        patch('torch.nn.Linear') as MockLinear:
        
        MockPathExists.return_value = False
        MockTorchLoad.return_value = MagicMock()
        MockSnapshotDownload = MagicMock()
        MockSnapshotDownload.return_value = 'mocked_model_path'
        MockAutoModel.return_value = MagicMock()
        MockAutoTokenizer.return_value = MagicMock()
        yield 

class TestEmbeddingModel:
    def test_initialization(self, embedding_model_path_exist, mock_logger_info):
        model = EmbeddingModel()
        assert model.model is not None
        assert model.tokenizer is not None
        mock_logger_info.assert_called_with('loading existing colbert_linear and sparse_linear')
    
    def test_initialization_path_not_exist(self, embedding_model_path_not_exist, mock_logger_error):
        model = EmbeddingModel()
        assert model.model is not None
        assert model.tokenizer is not None
        mock_logger_error.assert_called_once_with('The parameters of colbert_linear and sparse linear is new initialize. Make sure the model is loaded for training, not inferencing')
    
    @pytest.mark.parametrize(
        "sentence_pooling_method, normlized, return_type",
        [
            ('cls', True, 'ls'),
            ('mean', False, 'np'),
            ('cls', False, 'pt')
        ]
    )
    def test_dense_embedding(self, sentence_pooling_method, normlized, return_type, embedding_model_path_exist):
        model = EmbeddingModel()
        model.sentence_pooling_method = sentence_pooling_method
        model.normlized = normlized

        mock_hidden_state = torch.randn(2, 5, 1024) 
        mock_mask = torch.ones(2, 5, dtype=torch.bool)
    
        result = model.dense_embedding(mock_hidden_state, mock_mask, return_type=return_type)
        
        if return_type == 'ls':
            assert isinstance(result, list)
        elif return_type == 'np':
            assert isinstance(result, np.ndarray)
        elif return_type == 'pt':
            assert isinstance(result, torch.Tensor)
        for r in result:
            assert len(r) == 1024

    @pytest.mark.parametrize(
        "return_embedding",
        [
            (True),
            (False)
        ]
    )
    @patch('os.path.exists', return_value=True)
    def test_sparse_embedding(self, mock_path_exists, return_embedding, embedding_model_path_exist):
        model = EmbeddingModel()
        mock_hidden_state = torch.randn(2, 5, 1024).to(model.device)
        mock_input_ids = torch.tensor([[0, 1, 2, 10, 12], [3, 4, 5, 50, 3]]).to(model.device)
        
        with patch('torch.relu') as mock_torch_relu:
            mock_torch_relu.return_value = torch.randn(2, 5, 1)
            model.vocab_size = 100
            model.tokenizer.cls_token_id = 0
            model.tokenizer.eos_token_id = 1
            model.tokenizer.pad_token_id = 2
            model.tokenizer.unk_token_id = 3
            result = model.sparse_embedding(mock_hidden_state, mock_input_ids, return_embedding=return_embedding, return_type='pt')
        
        if return_embedding:
            assert isinstance(result, torch.Tensor)
            assert result.size() == (2, 100)
        else:
            assert isinstance(result, list)
            assert len(result) == 2

    def test_colbert_embedding(self, embedding_model_path_exist):
        model = EmbeddingModel()
        mock_last_hidden_state = torch.randn(2, 5, 1024) 
        mock_mask = torch.ones(2, 5, dtype=torch.bool)
        mock_mask[0, 3:] = 0
        model.colbert_linear = MagicMock()
        model.colbert_linear.return_value = torch.randn(2, 4, 1024)
        result = model.colbert_embedding(mock_last_hidden_state, mock_mask, return_type='pt')
        
        assert isinstance(result, list)
        assert len(result) == 2
        for r in result:
            assert isinstance(r, torch.Tensor)
            assert r.size()[1] == 1024

    @pytest.mark.parametrize(
        "lexical_weights, expected_output",
        [
            (
                {'1': 0.5, '2': 1.0},
                {'token_1': 0.5, 'token_2': 1.0}
            ),
            (
                [{'1': 0.5, '2': 1.0}],
                [{'token_1': 0.5, 'token_2': 1.0}]
            ),
            (
                [],
                []
            ),
            (
                [{}],
                [{}]
            ),
            (
                [{'1': 0.5}, {'2': 1.0}],
                [{'token_1': 0.5}, {'token_2': 1.0}]
            ),
            (
                {},
                {}
            )
        ]
    )
    def test_convert_id_to_token(self, lexical_weights, expected_output, embedding_model_path_exist):
        model = EmbeddingModel()
        model.tokenizer.decode = MagicMock()
        model.tokenizer.decode.side_effect = lambda x: f"token_{x[0]}"
        result = model.convert_id_to_token(lexical_weights)
        assert result == expected_output

    @pytest.mark.parametrize(
        "return_dense, return_sparse, return_colbert, expect_dense, expect_sparse, expect_colbert",
        [
            (
                True, True, True, 
                list, list, list
            ), 
            (
                True, False, True,
                list, type(None), list
            ),
            (
                False, True, False,
                type(None), list, type(None)
            ),
            (
                False, False, True,
                type(None), type(None), list
            ),
            (
                False, False, False,
                type(None), type(None), type(None)
            ),
        ]
    )
    def test__encode(self, return_dense, return_sparse, return_colbert, expect_dense, expect_sparse, expect_colbert, embedding_model_path_exist):
        model = EmbeddingModel()
        model.dense_embedding = MagicMock()
        model.sparse_embedding = MagicMock()
        model.colbert_embedding = MagicMock()
        model.model.return_value = MagicMock()
        model.model.return_value.last_hidden_state = torch.randn(2, 5, 1024) 
        mock_token = {
            'input_ids': torch.zeros(2, 5, dtype=torch.long),
            'attention_mask': torch.ones(2, 5, dtype=torch.bool)
        }
        model.dense_embedding.return_value = [torch.randn(2, 1024)]
        model.sparse_embedding.return_value = [torch.randn(2, 1024)]
        model.colbert_embedding.return_value = [torch.randn(2, 1024)]

        if not return_dense and not return_sparse and not return_colbert:
            assert pytest.raises(ValueError, model._encode, mock_token, return_dense=return_dense, return_sparse=return_sparse, return_colbert=return_colbert, return_type='ls')
        else:
            dense_vecs, sparse_vecs, colbert_vecs = model._encode(mock_token, return_dense=return_dense, return_sparse=return_sparse, return_colbert=return_colbert, return_type='ls')
            assert type(dense_vecs) is expect_dense
            assert type(sparse_vecs) is expect_sparse
            assert type(colbert_vecs) is expect_colbert

    @pytest.mark.parametrize(
        "sentences, mock_tokenizer, mock_dense",
        [
            (
                ["fs", "asdd"],
                [
                    MagicMock(return_value={
                        'input_ids': torch.zeros(2, 5, dtype=torch.long),
                        'attention_mask': torch.ones(2, 5, dtype=torch.bool)
                    })
                ],
                [torch.randn(2, 1024)]
            ), 
            (
                ["fs", "asdd", "asd"],
                [
                    MagicMock(return_value={
                        'input_ids': torch.zeros(2, 5, dtype=torch.long),
                        'attention_mask': torch.ones(2, 5, dtype=torch.bool)
                    }),
                    MagicMock(return_value={
                        'input_ids': torch.zeros(1, 5, dtype=torch.long),
                        'attention_mask': torch.ones(1, 5, dtype=torch.bool)
                    })
                ],
                [torch.randn(2, 1024), torch.randn(1, 1024)]
            ), 
            (
                "asd",
                [
                    MagicMock(return_value={
                        'input_ids': torch.zeros(1, 5, dtype=torch.long),
                        'attention_mask': torch.ones(1, 5, dtype=torch.bool)
                    })
                ],
                [torch.randn(1, 1024)]
            )
        ]
    )
    def test_encode(self, sentences, mock_tokenizer, mock_dense, embedding_model_path_exist):
        model = EmbeddingModel()
        model.tokenizer.side_effect = mock_tokenizer
        model._encode = MagicMock()
        model._encode.side_effect = [(dense, dense, dense) for dense in mock_dense]
        result = model.encode(
            sentences, 
            return_dense=True, 
            return_sparse=True, 
            return_colbert=True, 
            return_type='pt',
            batch_size=2
        )
        if isinstance(sentences, str):
            assert type(result['dense_vecs']) is torch.Tensor
        else:
            assert type(result['dense_vecs']) is list
        if isinstance(sentences, str):
            assert type(result['lexical_weights']) is torch.Tensor
        else:
            assert type(result['lexical_weights']) is list
        if isinstance(sentences, str):
            assert type(result['colbert_vecs']) is torch.Tensor
        else:
            assert type(result['colbert_vecs']) is list

    def test_count_tokenizer(self, embedding_model_path_exist):
        model = EmbeddingModel()
        model.tokenizer = MagicMock()
        model.tokenizer.return_value = {
            'input_ids': torch.tensor([[1, 2, 3], [4, 5, 6]])
        }
        
        result = model.count_tokenizer(['sentence1', 'sentence2'])
        
        assert isinstance(result, list)
        assert result == [3,3]
