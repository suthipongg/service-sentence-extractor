import pytest

from models.report_model import CalendarInterval, FilterItem, TermOperator, RangeOperator, WildcardOperator, BodyList


def test_calendar_interval():
    assert CalendarInterval.hour == "hour"
    assert CalendarInterval.day == "day"
    assert CalendarInterval.week == "week"
    assert CalendarInterval.month == "month"
    assert CalendarInterval.quarter == "quarter"
    assert CalendarInterval.year == "year"

class TestFilterItem:
    def test_term_operator(self):
        data = {
            "type": "term",
            "field": "age",
            "operator": {"eq": 30}
        }
        filter_item = FilterItem(**data)
        assert isinstance(filter_item.operator, TermOperator)
        assert filter_item.operator.eq == 30

    def test_range_operator(self):
        data = {
            "type": "range",
            "field": "price",
            "operator": {"gte": 10, "lte": 50}
        }
        filter_item = FilterItem(**data)
        assert isinstance(filter_item.operator, RangeOperator)
        assert filter_item.operator.gte == 10
        assert filter_item.operator.lte == 50

    def test_wildcard_operator(self):
        data = {
            "type": "wildcard",
            "field": "name",
            "operator": {"like": "John*"}
        }
        filter_item = FilterItem(**data)
        assert isinstance(filter_item.operator, WildcardOperator)
        assert filter_item.operator.like == "John*"

    def test_invalid_operator(self):
        data = {
            "type": "invalid",
            "field": "unknown",
            "operator": {"unknown_key": "value"}
        }
        with pytest.raises(ValueError):
            FilterItem(**data)

class TestBodyList:
    def test_include_exclude_conflict(self):
        data = {
            "include": ["name"],
            "exclude": ["age"],
            "page": 1,
            "pageSize": 12,
            "sort": {},
            "filter": []
        }
        with pytest.raises(ValueError):
            BodyList(**data)

    def test_valid_body_list(self):
        data = {
            "include": ["name"],
            "page": 1,
            "pageSize": 12,
            "sort": {"name": "asc"},
            "filter": []
        }
        body_list = BodyList(**data)
        assert body_list.page == 1
        assert body_list.pageSize == 12
        assert body_list.include == ["name"]
        assert body_list.sort == {"name": "asc"}
