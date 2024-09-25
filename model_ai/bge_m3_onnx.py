from optimum.onnxruntime import ORTModelForFeatureExtraction
from huggingface_hub import snapshot_download
from transformers import AutoTokenizer
import torch

from collections import defaultdict
from typing import List, Union
import numpy as np
from pathlib import Path
import os

from configs.config import SettingsManager
from configs.logger import LoggerConfig
from model_ai.base_encoder import BaseEncoder


class EmbeddingModel(BaseEncoder):
    def __init__(self, model_name='BAAI/bge-m3', sentence_pooling_method='cls', normlized=True, max_length=8192):
        super().__init__()
        self.model_name = model_name
        self.load_model()
        self.load_pooler()
        self.sentence_pooling_method = sentence_pooling_method
        self.vocab_size = self.model.config.vocab_size
        self.normlized = normlized
        self.max_length = max_length

    def load_model(self):
        model_path_not_exist = not os.path.exists(self.model_name)
        if model_path_not_exist:
            cache_folder = os.getenv('HF_HUB_CACHE')
            self.model_name = snapshot_download(repo_id=self.model_name, cache_dir=cache_folder, ignore_patterns=['flax_model.msgpack', 'rust_model.ot', 'tf_model.h5'])

        self.model = ORTModelForFeatureExtraction.from_pretrained(
            f"{str(Path().resolve())}/model_ai/models/{SettingsManager.settings.model_file_name}",
            use_io_binding=self.device!='cpu'
        ).to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

    def load_pooler(self):
        pooler_colbert_path_exist = os.path.exists(os.path.join(self.model_name, 'colbert_linear.pt'))
        pooler_sparse_path_exist = os.path.exists(os.path.join(self.model_name, 'sparse_linear.pt'))
        if pooler_colbert_path_exist and pooler_sparse_path_exist:
            LoggerConfig.logger.info('loading existing colbert_linear and sparse_linear')

            colbert_state_dict = torch.load(os.path.join(self.model_name, 'colbert_linear.pt'), map_location=self.device, weights_only=True)
            self.colbert_linear = torch.nn.Linear(in_features=self.model.config.hidden_size, out_features=self.model.config.hidden_size).to(self.device)
            self.colbert_linear.load_state_dict(colbert_state_dict)

            sparse_state_dict = torch.load(os.path.join(self.model_name, 'sparse_linear.pt'), map_location=self.device, weights_only=True)
            self.sparse_linear = torch.nn.Linear(in_features=self.model.config.hidden_size, out_features=1).to(self.device)
            self.sparse_linear.load_state_dict(sparse_state_dict)
        else:
            LoggerConfig.logger.error('The parameters of colbert_linear and sparse linear is new initialize. Make sure the model is loaded for training, not inferencing')

    def dense_embedding(self, hidden_state, mask, return_type='ls'):
        if self.sentence_pooling_method == 'cls':
            dense_vecs = hidden_state[:, 0]
        elif self.sentence_pooling_method == 'mean':
            s = torch.sum(hidden_state * mask.unsqueeze(-1).float(), dim=1)
            d = mask.sum(axis=1, keepdim=True).float()
            dense_vecs = s / d
        
        dense_vecs = torch.nn.functional.normalize(dense_vecs, dim=-1) if self.normlized else dense_vecs
        return self.convert_pt_type(dense_vecs.contiguous(), return_type)

    def sparse_embedding(self, hidden_state, input_ids, return_embedding: bool = True, return_type='ls'):
        token_weights = torch.relu(self.sparse_linear(hidden_state)).to(self.device)
        unused_tokens = [self.tokenizer.cls_token_id, self.tokenizer.eos_token_id, self.tokenizer.pad_token_id, self.tokenizer.unk_token_id]
        
        def _process_token_weights(token_weights: np.ndarray, input_ids: list):
            result = defaultdict(int)
            set_unused_tokens = set(unused_tokens)
            for w, idx in zip(token_weights, input_ids):
                idx = idx.item()
                if idx not in set_unused_tokens and w > 0:
                    idx = str(idx)
                    if w > result[idx]:
                        result[idx] = w.item()
            return result
        
        if not return_embedding:
            token_weights = list(map(_process_token_weights, token_weights, input_ids)) 
            return token_weights

        sparse_embedding = torch.zeros(input_ids.size(0), input_ids.size(1), self.vocab_size, dtype=token_weights.dtype, device=self.device)
        sparse_embedding = torch.scatter(sparse_embedding, dim=-1, index=input_ids.unsqueeze(-1), src=token_weights)
        sparse_embedding = torch.max(sparse_embedding, dim=1).values
        sparse_embedding[:, unused_tokens] *= 0.
        return self.convert_pt_type(sparse_embedding.contiguous(), return_type)
    
    def colbert_embedding(self, last_hidden_state, mask, return_type='ls'):
        colbert_vecs = self.colbert_linear(last_hidden_state[:, 1:])
        colbert_vecs = colbert_vecs * mask[:, 1:][:, :, None].float().contiguous()
        def _process_colbert_vecs(colbert_vecs, mask):
            use_token_layer = mask.sum(-1)
            embedded_without_cls_layer = colbert_vecs[:use_token_layer - 1]
            embedded_without_cls_layer = torch.nn.functional.normalize(embedded_without_cls_layer, dim=-1).cpu() if self.normlized else embedded_without_cls_layer.cpu()
            return self.convert_pt_type(embedded_without_cls_layer, return_type)
        return list(map(_process_colbert_vecs, colbert_vecs, mask))
    
    def convert_id_to_token(self, lexical_weights):
        return_type = list
        if isinstance(lexical_weights, dict):
            return_type = dict
            lexical_weights = [lexical_weights]
        new_lexical_weights = []
        for item in lexical_weights:
            new_item = {}
            for id, weight in item.items():
                token = self.tokenizer.decode([int(id)])
                new_item[token] = weight
            new_lexical_weights.append(new_item)

        if return_type is dict:
            new_lexical_weights = new_lexical_weights[0]
        return new_lexical_weights

    def _encode(self, token, return_dense=True, return_sparse=True, return_colbert=True, return_sparse_embedding=True, return_type='ls'):
        if not return_dense and not return_sparse and not return_colbert:
            raise ValueError('At least one of return_dense, return_sparse, return_colbert should be True')
        last_hidden_state = self.model(**token, return_dict=True).last_hidden_state

        dense_vecs, sparse_vecs, colbert_vecs = None, None, None
        if return_dense:
            dense_vecs = self.dense_embedding(last_hidden_state, token['attention_mask'], return_type=return_type)
        if return_sparse:
            sparse_vecs = self.sparse_embedding(last_hidden_state, token['input_ids'], return_embedding=return_sparse_embedding, return_type=return_type)
        if return_colbert:
            colbert_vecs = self.colbert_embedding(last_hidden_state, token['attention_mask'], return_type=return_type)

        return dense_vecs, sparse_vecs, colbert_vecs

    @torch.no_grad()
    def encode(self, sentences:Union[List[str], str], return_dense=True, return_sparse=False, return_colbert=False, return_sparse_embedding=False, return_type='ls', batch_size=12):
        input_was_string = False
        if isinstance(sentences, str):
            sentences = [sentences]
            input_was_string = True
        
        init_res = lambda return_vect: [] if return_vect else None
        all_dense_vecs, all_sparse_vecs, all_colbert_vecs = init_res(return_dense), init_res(return_sparse), init_res(return_colbert)
        for batch in range(0, len(sentences), batch_size):
            sentences_batch = sentences[batch:batch + batch_size]
            batch_token = self.tokenizer(
                sentences_batch,
                max_length=self.max_length, 
                padding=True, 
                return_token_type_ids=False, 
                truncation=True, 
                return_tensors='pt'
            ).to(self.device)

            dense_vecs, sparse_vecs, colbert_vecs = self._encode(
                batch_token, 
                return_dense=return_dense,
                return_sparse=return_sparse,
                return_colbert=return_colbert,
                return_sparse_embedding=return_sparse_embedding,
                return_type=return_type
            )
            if return_dense:
                all_dense_vecs.extend(dense_vecs)
            if return_sparse:
                all_sparse_vecs.extend(sparse_vecs)
            if return_colbert:
                all_colbert_vecs.extend(colbert_vecs)
        
        if input_was_string:
            all_dense_vecs = all_dense_vecs[0] if return_dense else None
            all_sparse_vecs = all_sparse_vecs[0] if return_sparse else None
            all_colbert_vecs = all_colbert_vecs[0] if return_colbert else None
        return {"dense_vecs": all_dense_vecs, "lexical_weights": all_sparse_vecs, "colbert_vecs": all_colbert_vecs}

    def count_tokenizer(self, sentence):
        return list(map(len, self.tokenizer(sentence)['input_ids']))