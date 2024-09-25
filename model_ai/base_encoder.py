import torch
from typing import List, Union
from configs.config import SettingsManager

class BaseEncoder:
    def __init__(self):
        self.device = SettingsManager.settings.device if torch.cuda.is_available() else 'cpu'
        self.model_name = None
        self.model = None
        self.tokenizer = None

    def encode(self, text:Union[List[str], str], return_type='ls'):
        raise NotImplementedError

    def count_tokenizer(self, sentence):
        raise NotImplementedError
    
    def convert_pt_type(self, result, return_type):
        if not isinstance(result, torch.Tensor):
            raise TypeError(f"result should be a torch.Tensor, but got {type(result)}")
        if return_type == 'pt':
            return result
        elif return_type == 'np':
            return result.cpu().detach().numpy()
        elif return_type == 'ls':
            return result.cpu().detach().numpy().tolist()
        else:
            raise ValueError(f"return_type should be 'pt', 'np' or 'ls', but got {return_type}")