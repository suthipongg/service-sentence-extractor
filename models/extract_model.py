from pydantic import BaseModel, Field
from typing import List, Union, Mapping
from datetime import datetime
from enum import Enum

class ExtractorModel(BaseModel):
    sentence: str = ''
    # sentence_vector: List = None
    created_at: str = datetime.now().isoformat()
    counter: int = 1

    class Config:
        json_schema_extra = {
            "example": {
                "sentence": "Example Text",
            }
        }
    