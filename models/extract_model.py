from pydantic import BaseModel, ConfigDict
from typing import Union

from datetime import datetime


class ExtractorModel(BaseModel):
    sentence: str
    created_at: datetime = None
    counter: int = 1

    model_config = ConfigDict(json_schema_extra=
    {
        'examples': 
        [
            {
                "sentence": "Example Text"
            }
        ]
    })

    def __init__(self, **data):
        super().__init__(**data)
        if not self.created_at:
            self.created_at = datetime.now()

        self.sentence = self.sentence.strip()
        if not self.sentence:
            raise ValueError("Sentence can't be empty")

class ExtractorListModel(BaseModel):
    sentences: Union[str, list]
    
    def __init__(self, **data):
        super().__init__(**data)
        if isinstance(self.sentences, str):
            self.sentences = [self.sentences]

    model_config = ConfigDict(json_schema_extra=
        {
            'examples': 
            [
                {
                    "sentences": ["Example Text"]
                }
            ]
        }
    )