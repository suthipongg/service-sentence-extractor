from sentence_transformers import SentenceTransformer #InputExample
from sentence_transformers import models #losses
# from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator
# from torch.utils.data import DataLoader
import numpy as np
import os

from transformers import AutoTokenizer

os.environ["TOKENIZERS_PARALLELISM"] = "true"


class SentenceExtractor:
    def __init__(self):
        # MODEL_NAME = 'mrp/simcse-model-roberta-base-thai'
        # MODEL_NAME = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
        MODEL_NAME = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
        MODEL_PATH = './model_ai'
        word_embedding_model = models.Transformer(model_name_or_path=MODEL_NAME)
        pooling_model = models.Pooling(word_embedding_model.get_word_embedding_dimension(),pooling_mode='cls') # We use a [CLS] token as representation
        self.model = SentenceTransformer(modules=[word_embedding_model, pooling_model])
        # self.model.save('/Users/nawaphongyoochum/Learn-Python/chatbot-deployment/model')

        self.tokenizer = AutoTokenizer.from_pretrained(pretrained_model_name_or_path=MODEL_PATH)


    def extract(self, list_text):
        return self.model.encode(list_text ,normalize_embeddings=True)

    


if __name__ == "__main__":

    st = SentenceExtractor()
    text = 'สวัสดีครับ'
    print(st.extract(text))