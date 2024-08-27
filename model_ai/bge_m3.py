import numpy as np
import os
import torch
from collections import defaultdict
from typing import List, Union
from transformers import AutoTokenizer, AutoModel
from huggingface_hub import snapshot_download
from config.logger import logger
from model_ai.cvt_arr_type import return_convert_type

class EmbeddingModel:
    def __init__(self, model_name='BAAI/bge-m3', device='cuda', sentence_pooling_method='cls', normlized=True, temperature=1.0, enable_sub_batch=False, use_fp16=False, max_length=8192):
        self.device = device if torch.cuda.is_available() else 'cpu'
        self.model_name = model_name
        if not os.path.exists(self.model_name):
            cache_folder = os.getenv('HF_HUB_CACHE')
            self.model_name = snapshot_download(repo_id=self.model_name, cache_dir=cache_folder, ignore_patterns=['flax_model.msgpack', 'rust_model.ot', 'tf_model.h5'])
        self.load_model()
        if os.path.exists(os.path.join(self.model_name, 'colbert_linear.pt')) and os.path.exists(
                os.path.join(self.model_name, 'sparse_linear.pt')):
            logger.info('loading existing colbert_linear and sparse_linear---------')
            self.load_pooler()
        else:
            logger.info('The parameters of colbert_linear and sparse linear is new initialize. Make sure the model is loaded for training, not inferencing')
        if use_fp16: self.model.half()
        self.model.eval()
        self.sentence_pooling_method = sentence_pooling_method
        self.vocab_size = self.model.config.vocab_size
        self.normlized = normlized
        self.temperature = 1.0 if not normlized else temperature
        self.enable_sub_batch = enable_sub_batch
        self.max_length = max_length

    def load_model(self):
        self.model = AutoModel.from_pretrained(self.model_name).to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

        self.colbert_linear = torch.nn.Linear(in_features=self.model.config.hidden_size, out_features=self.model.config.hidden_size).to(self.device)
        self.sparse_linear = torch.nn.Linear(in_features=self.model.config.hidden_size, out_features=1).to(self.device)

    def load_pooler(self):
        colbert_state_dict = torch.load(os.path.join(self.model_name, 'colbert_linear.pt'), map_location=self.device, weights_only=True)
        sparse_state_dict = torch.load(os.path.join(self.model_name, 'sparse_linear.pt'), map_location=self.device, weights_only=True)
        self.colbert_linear.load_state_dict(colbert_state_dict)
        self.sparse_linear.load_state_dict(sparse_state_dict)

    def dense_embedding(self, hidden_state, mask, return_type='ls'):
        if self.sentence_pooling_method == 'cls':
            dense_vecs = hidden_state[:, 0]
        elif self.sentence_pooling_method == 'mean':
            s = torch.sum(hidden_state * mask.unsqueeze(-1).float(), dim=1)
            d = mask.sum(axis=1, keepdim=True).float()
            dense_vecs = s / d
        
        dense_vecs = torch.nn.functional.normalize(dense_vecs, dim=-1) if self.normlized else dense_vecs
        return return_convert_type(dense_vecs.contiguous(), return_type)

    def sparse_embedding(self, hidden_state, input_ids, return_embedding: bool = True, return_type='ls'):
        token_weights = torch.relu(self.sparse_linear(hidden_state)).contiguous()
        unused_tokens = [self.tokenizer.cls_token_id, self.tokenizer.eos_token_id, self.tokenizer.pad_token_id, self.tokenizer.unk_token_id]
        
        def _process_token_weights(token_weights: np.ndarray, input_ids: list):
            # convert to dict
            result = defaultdict(int)
            # token_weights = np.ceil(token_weights * 100)
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
        return return_convert_type(sparse_embedding, return_type)
    
    def colbert_embedding(self, last_hidden_state, mask, return_type='ls'):
        colbert_vecs = self.colbert_linear(last_hidden_state[:, 1:])
        colbert_vecs = colbert_vecs * mask[:, 1:][:, :, None].float().contiguous()
        def _process_colbert_vecs(colbert_vecs, mask):
            # delete the vectors of padding tokens
            tokens_num = mask.sum(-1)
            result = colbert_vecs[:tokens_num - 1]  # we don't use the embedding of cls, so select tokens_num-1
            result = torch.nn.functional.normalize(result, dim=-1).cpu() if self.normlized else result.cpu()
            return return_convert_type(result, return_type)
        return list(map(_process_colbert_vecs, colbert_vecs, mask))
    
    def convert_id_to_token(self, lexical_weights):
        if isinstance(lexical_weights, dict):
            lexical_weights = [lexical_weights]
        new_lexical_weights = []
        for item in lexical_weights:
            new_item = {}
            for id, weight in item.items():
                token = self.tokenizer.decode([int(id)])
                new_item[token] = weight
            new_lexical_weights.append(new_item)

        if len(new_lexical_weights) == 1:
            new_lexical_weights = new_lexical_weights[0]
        return new_lexical_weights

    def _encode(self, token, return_dense=True, return_sparse=True, return_colbert=True, return_sparse_embedding=True, return_type='ls'):
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
    def encode(self, text:Union[List[str], str], return_dense=True, return_sparse=False, return_colbert=False, return_sparse_embedding=False, return_type='ls'):
        input_was_string = False
        if isinstance(text, str):
            text = [text]
            input_was_string = True
        
        token = self.tokenizer(text, max_length=self.max_length, padding=True, return_token_type_ids=False, truncation=True, return_tensors='pt').to(self.device)
        params = {'return_dense': return_dense, 'return_sparse': return_sparse, 'return_colbert': return_colbert, 'return_sparse_embedding': return_sparse_embedding, 'return_type':return_type}
        
        if self.enable_sub_batch:
            sub_batch_size=self.compute_sub_batch_size(token)
            all_dense_vecs, all_sparse_vecs, all_colbert_vecs = [], [], []
            for i in range(0, len(token['attention_mask']), sub_batch_size):
                end_inx = min(i + sub_batch_size, len(token['attention_mask']))
                sub_token = {}
                for k, v in token.items():
                    sub_token[k] = v[i:end_inx]

                dense_vecs, sparse_vecs, colbert_vecs = self._encode(sub_token, **params)
                all_dense_vecs.append(dense_vecs)
                all_sparse_vecs.extend(sparse_vecs)
                all_colbert_vecs.extend(colbert_vecs)

            dense_vecs, sparse_vecs, colbert_vecs = torch.cat(all_dense_vecs, 0), torch.cat(all_sparse_vecs, 0), torch.cat(all_colbert_vecs, 0)
        else:
            dense_vecs, sparse_vecs, colbert_vecs = self._encode(token, **params)
        
        if input_was_string:
            dense_vecs = dense_vecs[0] if dense_vecs is not None else dense_vecs
            sparse_vecs = sparse_vecs[0] if sparse_vecs is not None else sparse_vecs
            colbert_vecs = colbert_vecs[0] if colbert_vecs is not None else colbert_vecs
        return {"dense_vecs": dense_vecs, "lexical_weights": sparse_vecs, "colbert_vecs": colbert_vecs}

    def compute_sub_batch_size(self, features):
        mapping = [(6000, 1), (5000, 2), (4000, 3), (3000, 3), (2000, 5), (1000, 9), (512, 16), (0, 32)]
        cur_l = features['input_ids'].size(-1)
        for l, b in mapping:
            if cur_l >= l:
                return b