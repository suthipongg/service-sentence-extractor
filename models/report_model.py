from pydantic import BaseModel, Field
from typing import List, Union, Mapping
from enum import Enum


class CalendarInterval(str, Enum):
    hour = "hour"
    day = "day"
    week = "week"
    month = "month"
    quarter = "quarter"
    year = "year"


class TermOperator(BaseModel):
    eq: Union[float, bool, int, str, None] = None
    ne: Union[float, bool, int, str, None] = None

class RangeOperator(BaseModel):
    gte: Union[float, int, str, None] = None
    lte: Union[float, int, str, None] = None
    gt: Union[float, int, str, None] = None
    lt: Union[float, int, str, None] = None

class WildcardOperator(BaseModel):
    like: str = ""

class FilterItem(BaseModel):
    type: str = ""
    field: str = ""
    operator: Union[TermOperator, WildcardOperator, RangeOperator] = None

    def __init__(cls, **data):
        super().__init__(**data)
        if any(key in data['operator'] for key in ['gte', 'lte', 'gt', 'lt']):
            cls.operator = RangeOperator(**data['operator'])
        elif 'like' in data['operator']:
            cls.operator = WildcardOperator(**data['operator'])
        elif any(key in data['operator'] for key in ['eq', 'ne']):
            cls.operator = TermOperator(**data['operator'])
        else:
            raise ValueError('Invalid keys for operator')

class BodyList(BaseModel):
    include: List[str] = Field([], description="List of fields to include in response")
    exclude: List[str] = Field([], description="List of fields to exclude from response")
    page: int = Field(1, ge=1, description="Page number for pagination (default: 1)")
    pageSize: int = Field(12, ge=1, description="Number of items per page (default: 12)")
    sort: Mapping[str, Union[int, float, str]] = Field({}, description="Sort criteria for results")
    filter: List[FilterItem] = Field([], description="List of filtering criteria")

    def __init__(cls, **data):
        super().__init__(**data)

        if cls.include and cls.exclude:
            raise ValueError('Include and exclude fields cannot be used together')