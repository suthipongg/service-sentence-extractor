from pydantic import BaseModel, Field
from typing import List, Union, Mapping
from datetime import datetime
from enum import Enum

class ExtractorModel(BaseModel):
    sentence: Union[str, list] = ''
    # sentence_vector: List = None
    created_at: str = datetime.now()
    counter: int = 1

    def __init__(self, **data):
        super().__init__(**data)
        self.created_at = datetime.now()

    class Config:
        json_schema_extra = {
            "example": {
                "sentence": "Example Text",
            }
        }
    
class ExtractorListModel(BaseModel):
    sentences: Union[str, list] = ''

    def __init__(self, **data):
        super().__init__(**data)
        if isinstance(self.sentences, str):
            self.sentences = [self.sentences]
            
    class Config:
        json_schema_extra = {
            "example": {
                "sentences": ["Example Text"],
            }
        }


class CalendarInterval(str, Enum):
    # minute = "minute"
    hour = "hour"
    day = "day"
    week = "week"
    month = "month"
    quarter = "quarter"
    year = "year"


# Define Pydantic models for request and response
class TermOperator(BaseModel):
    eq: Union[float, bool, int, str]

class RangeOperator(BaseModel):
    gte: Union[float, int, str, None] = None
    lte: Union[float, int, str, None] = None
    gt: Union[float, int, str, None] = None
    lt: Union[float, int, str, None] = None

class WildcardOperator(BaseModel):
    like: str

class FilterItem(BaseModel):
    type: str
    field: str
    operator: Union[TermOperator, WildcardOperator, RangeOperator, ]

class BodyList(BaseModel):
    include: List[str] = Field(None, description="List of fields to include in response")
    exclude: List[str] = Field(None, description="List of fields to exclude from response")
    page: int = Field(1, ge=1, description="Page number for pagination (default: 1)")
    pageSize: int = Field(12, ge=1, description="Number of items per page (default: 12)")
    sort: Mapping[str, Union[int, float, str]] = Field({}, description="Sort criteria for results")
    filter: List[FilterItem] = Field([], description="List of filtering criteria")
