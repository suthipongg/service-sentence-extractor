import os
import importlib

from configs.logger import LoggerConfig
from configs.environment import ENV

# Disabling parallelism to avoid deadlocks
os.environ["TOKENIZERS_PARALLELISM"] = "false"

class SentenceExtractor:
    _instance = None
    _loading = False

    def __new__(cls):
        return cls.init_instance()
    
    @classmethod
    def init_instance(cls):
        if cls._instance is None and cls._toggle_loading():
            LoggerConfig.logger.info("Creating SentenceExtractor instance")
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
            LoggerConfig.logger.info("SentenceExtractor instance created")
            cls._toggle_loading()
        return cls._instance

    @classmethod
    def _toggle_loading(cls):
        if cls._loading == False:
            cls._loading = not cls._loading
            return cls._loading
        return False

    def _initialize(self):
        EmbeddingModel = importlib.import_module(f"model_ai.{ENV.MODEL_NAME}").EmbeddingModel
        self.model = EmbeddingModel()

    def extract(self, list_text):
        return self.model.encode(list_text)['dense_vecs']
    
    def compute_token(self, sentence):
        return self.model.count_tokenizer(sentence)