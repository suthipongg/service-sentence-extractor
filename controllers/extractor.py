import os
import importlib
from dotenv import load_dotenv
load_dotenv()

os.environ["TOKENIZERS_PARALLELISM"] = "true"

class SentenceExtractor():
    def __init__(self):
        MODEL_NAME = os.getenv('MODEL_NAME', 'bge_m3')
        EmbeddingModel = importlib.import_module(f"model_ai.{MODEL_NAME}").EmbeddingModel
        self.model = EmbeddingModel()
        self.tokenizer = self.model.tokenizer

    def extract(self, list_text):
        return self.model.encode(list_text)['dense_vecs']

if __name__ == "__main__":

    st = SentenceExtractor()
    text = 'สวัสดีครับ'
    print(st.extract(text))