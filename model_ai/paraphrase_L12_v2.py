from sentence_transformers import SentenceTransformer #InputExample
import torch
from model_ai.cvt_arr_type import return_convert_type
from transformers import AutoTokenizer

class EmbeddingModel:
    def __init__(self, model_name='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'):
        self.model_name = model_name
        word_embedding_model = self.model_name.Transformer(model_name_or_path=self.model_name)
        pooling_model = self.model_name.Pooling(word_embedding_model.get_word_embedding_dimension(),pooling_mode='cls') # We use a [CLS] token as representation
        self.model = SentenceTransformer(modules=[word_embedding_model, pooling_model])
        self.model = self.model.to('cuda') if torch.cuda.is_available() else self.model
        self.tokenizer = AutoTokenizer.from_pretrained(pretrained_model_name_or_path=self.model_name)

    def encode(self, list_text, return_type='ls'):
        embeded = self.model.encode(list_text, convert_to_tensor=True)
        return {'dense_vecs': return_convert_type(embeded, return_type=return_type)}