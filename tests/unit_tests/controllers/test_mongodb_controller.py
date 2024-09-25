import pytest
from unittest.mock import MagicMock, patch

from dateutil.parser import parse as date_parse

from controllers.mongodb_controller import MongoDBCRUD, MGFuncs


@pytest.fixture(scope='function')
def mock_collection_items():
    mock_collection = MagicMock()
    mock_items = MagicMock()
    mock_collection.find.return_value = mock_items
    mock_items.sort.return_value = mock_items
    mock_items.skip.return_value = mock_items
    mock_items.limit.return_value = mock_items
    return mock_collection, mock_items


class TestMongoDBCRUD:
    @patch('controllers.mongodb_controller.MongoDBConnection.mongo_client')
    def test_mongo_crud(self, mock_mongo_client):
        instance = MongoDBCRUD()
        assert MongoDBCRUD.mongo_client is mock_mongo_client
        assert instance.mongo_client is mock_mongo_client


class TestMGFuncs:
    def test_compute_pagination(self):
        mock_collection = MagicMock()
        mock_collection.count_documents.return_value = 50

        page, page_size = 2, 10
        skip_count, pagination = MGFuncs.compute_pagination(mock_collection, {}, page, page_size)

        assert skip_count == 10
        assert pagination == {
            "page": page,
            "pageSize": page_size,
            "pageCount": 5,
            "total": 50
        }


    @pytest.mark.parametrize(
        "sort, expected_sort_called",
        [
            ([], False),
            ([{'field': 1}], True)
        ]
    )
    def test_query_action(self, sort, expected_sort_called, mock_collection_items):
        mock_collection, mock_items = mock_collection_items

        result = MGFuncs.query_action(mock_collection, {}, {}, sort, 0, 10)

        mock_collection.find.assert_called_once_with({}, {})
        
        if expected_sort_called:
            mock_items.sort.assert_called_once_with(sort)
        else:
            mock_items.sort.assert_not_called()

        mock_items.skip.assert_called_once_with(0)
        mock_items.limit.assert_called_once_with(10)
        assert result == mock_items


    @pytest.mark.parametrize(
        "value, expected_boolean",
        [
            (True, True), (False, False),
            ("true", True), ("t", True), ("yes", True), ("y", True), ("1", True),
            ("false", False), ("f", False), ("no", False), ("n", False), ("0", False),
            ("other", False), (1, True), (0, False)
        ]
    )
    def test_convert_to_boolean(self, value, expected_boolean):
        assert MGFuncs.convert_string_to_boolean(value) is expected_boolean


    @pytest.mark.parametrize(
        "filter_item, expected_output",
        [
            ({"type": "term", "operator": {"eq": "value1", "ne": None}}, {"$eq": "value1"}),
            ({"type": "term", "operator": {"eq": "value1", "ne": 2}}, {"$eq": "value1", "$ne": 2}),
            ({"type": "bool", "operator": {"eq": "true", "ne": "false"}}, {"$eq": True, "$ne": False}),
            ({"type": "range", "operator": {"gte": 10, "lte": 20}}, {"$gte": 10, "$lte": 20}),
            ({"type": "range", "operator": {"gt": 10, "lte": 20, "gte": 15}}, {"$gt": 10, "$lte": 20, "$gte": 15}),
            ({"type": "wildcard", "operator": {"like": "value"}}, {"$regex": ".*value.*"}),
            ({"type": "wildcard", "operator": {"like": "val*ue"}}, {"$regex": ".*val.*ue.*"}),
            ({"type": "datetime", "operator": {"gte": "2024-01-01T00:00:00Z"}}, {"$gte": date_parse("2024-01-01T00:00:00Z")}),
        ]
    )
    def test_convert_filter_to_mongo_query(self, filter_item, expected_output):
        result = MGFuncs.convert_filter_to_mongo_query(filter_item)
        assert result == expected_output


    @pytest.mark.parametrize(
        "body, expected_query, expected_projection, expected_sort, expected_skip_count, expected_pagination",
        [
            (
                MagicMock(model_dump=lambda: {
                    "filter": [{"type": "term", "field": "field1", "operator": {"eq": "value1"}}],
                    "include": ["field1"],
                    "exclude": [],
                    "sort": {"field1": 1},
                    "page": 1,
                    "pageSize": 10
                }),
                {"$and": [{"field1": {"$eq": "value1"}}]},
                {"field1": 1, "_id": 0},
                [("field1", 1)],
                0, 
                {
                    "page": 1, 
                    "pageSize": 10, 
                    "pageCount": 1, 
                    "total": 10
                }
            ),
            (
                MagicMock(model_dump=lambda: {
                    "filter": [{"type": "term", "field": "field2", "operator": {"eq": "value2"}}],
                    "include": [],
                    "exclude": ["field1"],
                    "sort": {},
                    "page": 2,
                    "pageSize": 5
                }),
                {"$and": [{"field2": {"$eq": "value2"}}]},
                {"field1": 0},
                [],
                5, 
                {
                    "page": 2, 
                    "pageSize": 5, 
                    "pageCount": 2, 
                    "total": 10
                }
            ),
            (
                MagicMock(model_dump=lambda: {
                    "filter": [],
                    "include": [],
                    "exclude": [],
                    "sort": {"field1": 1},
                    "page": 3,
                    "pageSize": 10
                }),
                {},
                {},
                [("field1", 1)],
                20, 
                {
                    "page": 3, 
                    "pageSize": 10, 
                    "pageCount": 4, 
                    "total": 35
                }
            ),
        ]
    )
    def test_query_collection(
        self, 
        body, 
        expected_query, 
        expected_projection, 
        expected_sort, 
        expected_skip_count, 
        expected_pagination,
        mock_collection_items
    ):
        mock_collection, mock_items = mock_collection_items
        
        MGFuncs.compute_pagination = MagicMock(return_value=(expected_skip_count, expected_pagination))
        MGFuncs.query_action = MagicMock(return_value=mock_items)
        
        result_items, result_pagination = MGFuncs.query_collection(body, mock_collection)
        
        MGFuncs.compute_pagination.assert_called_once_with(
            mock_collection,
            expected_query, 
            expected_pagination['page'], 
            expected_pagination['pageSize'], 
        )
        MGFuncs.query_action.assert_called_once_with(
            mock_collection,
            expected_query, 
            expected_projection, 
            expected_sort, 
            expected_skip_count, 
            expected_pagination['pageSize']
        )

        assert result_items == mock_items
        assert result_pagination == expected_pagination