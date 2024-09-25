import pytest
from unittest.mock import patch

from controllers.elasticsearch_controller import ElasticsearchCRUD, ESFuncs


class TestElasticsearchCRUD:
    def test_create_index_es_index_exists(self, mock_es_client_attr):
        mock_es_client_attr.indices.exists.return_value = True
        result = ElasticsearchCRUD.create_index_es('test_index', {"mappings": {}})
        mock_es_client_attr.indices.create.assert_not_called()
        mock_es_client_attr.indices.exists.assert_called_once_with(index='test_index')
        assert result is None

    def test_create_index_es_index_not_exists(self, mock_es_client_attr):
        mock_es_client_attr.indices.exists.return_value = False
        mock_es_client_attr.indices.create.return_value = {"acknowledged": True}

        result = ElasticsearchCRUD.create_index_es('test_index', {'mappings': {}})
        mock_es_client_attr.indices.create.assert_called_once_with(index='test_index', mappings={})
        mock_es_client_attr.indices.exists.assert_called_once_with(index='test_index')
        assert result == {"acknowledged": True}

    @pytest.mark.parametrize(
        "mocked_data, expected_action",
        [
            (
                [{"_id": "1", "field": "value1"}, {"_id": "2", "field": "value2"}],
                [
                    {
                        "_index": "test_index",
                        "_op_type": "index",
                        "_id": "1",
                        "_source": {"_id": "1", "field": "value1"}
                    },
                    {
                        "_index": "test_index",
                        "_op_type": "index",
                        "_id": "2",
                        "_source": {"_id": "2", "field": "value2"}
                    }
                ]
            ),
            (
                [{"_id": "1", "field": "value1"}],
                [
                    {
                        "_index": "test_index",
                        "_op_type": "index",
                        "_id": "1",
                        "_source": {"_id": "1", "field": "value1"}
                    }
                ]
            ),
            (
                [],
                []
            ),
            (
                None,
                []
            ),
            (
                [{"field": "value1"}, {"field": "value2"}],
                [
                    {
                        "_index": "test_index",
                        "_op_type": "index",
                        "_id": None,
                        "_source": {"field": "value1"}
                    },
                    {
                        "_index": "test_index",
                        "_op_type": "index",
                        "_id": None,
                        "_source": {"field": "value2"}
                    }
                ]
            ),
            (
                [{"field": "value1"}],
                [
                    {
                        "_index": "test_index",
                        "_op_type": "index",
                        "_id": None,
                        "_source": {"field": "value1"}
                    }
                ]
            ),
            (
                [{}],
                []
            ),
            (
                [None],
                []
            )
        ]
    )
    def test_cvt_datas_to_bulk(self, mocked_data, expected_action):
        result = ElasticsearchCRUD.cvt_datas_to_bulk("test_index", mocked_data)
        assert result == expected_action

    @patch('controllers.elasticsearch_controller.bulk')
    def test_bulk_es(self, mock_bulk, mock_es_client_attr, mock_logger_info):
        mock_bulk.return_value = (5, 0)

        datas = [{"_id": "1", "field": "value1"}, {"_id": "2", "field": "value2"}]
        success, failed = ElasticsearchCRUD.bulk_es("test_index", datas)

        assert success == 5
        assert failed == 0
        mock_bulk.assert_called_once()
        mock_logger_info.assert_called()

    def test_insert_es(self, mock_es_client_attr):
        mock_es_client_attr.index.return_value = {"_id": "1"}

        result = ElasticsearchCRUD.insert_es("test_index", {"field": "value"}, id="1")
        assert result == {"_id": "1"}
        mock_es_client_attr.index.assert_called_once_with(index="test_index", document={"field": "value"}, id="1")

    def test_update_es(self, mock_es_client_attr):
        mock_es_client_attr.update.return_value = {"_id": "1"}

        result = ElasticsearchCRUD.update_es("test_index", id="1", body={"doc": {"field": "new_value"}})
        assert result == {"_id": "1"}
        mock_es_client_attr.update.assert_called_once_with(index="test_index", id="1", doc={"field": "new_value"})

    def test_delete_es(self, mock_es_client_attr):
        mock_es_client_attr.delete.return_value = {"_id": "1"}

        result = ElasticsearchCRUD.delete_es("test_index", id="1")
        assert result == {"_id": "1"}
        mock_es_client_attr.delete.assert_called_once_with(index="test_index", id="1")

    def test_delete_by_query_es(self, mock_es_client_attr):
        mock_es_client_attr.delete_by_query.return_value = {"deleted": 2}

        result = ElasticsearchCRUD.delete_by_query_es("test_index", {"query": {"match_all": {}}})
        assert result == {"deleted": 2}
        mock_es_client_attr.delete_by_query.assert_called_once_with(index="test_index", body={"query": {"match_all": {}}})

    def test_search_es(self, mock_es_client_attr):
        mock_es_client_attr.search.return_value = {"hits": {"hits": [{"_id": "1"}]}}

        result = ElasticsearchCRUD.search_es("test_index", body={"query": {"match_all": {}}})
        assert result == {"hits": {"hits": [{"_id": "1"}]}}
        mock_es_client_attr.search.assert_called_once_with(index="test_index", body={"query": {"match_all": {}}})


class TestESFuncs:
    @patch('controllers.elasticsearch_controller.ESIndex.init_index')
    @patch('controllers.elasticsearch_controller.ElasticsearchCRUD.create_index_es', autospec=True)
    def test_start_index_es(self, mock_create_ind, mock_index, mock_logger_info):
        mock_index.return_value = (
            {
                'index1': 'index1_value',
                'index2': 'index2_value'
            },
            {
            'index1': {'setting': 'value1'},
            'index2': {'setting': 'value2'}
            }
        )
        mock_create_ind.side_effect = [True, False]
        ESFuncs.start_index_es()

        mock_create_ind.assert_any_call('index1_value', {'setting': 'value1'})
        mock_create_ind.assert_any_call('index2_value', {'setting': 'value2'})

        mock_logger_info.assert_any_call('index1_value \033[96mCreated\033[0m :::')
        mock_logger_info.assert_any_call('index2_value Already Exists :::')


    @patch('controllers.elasticsearch_controller.ElasticsearchCRUD.update_es', autospec=True)
    def test_update_counter(self, mock_update_es, mock_logger_info):
        index_name = 'test_index'
        doc_id = '123'
        mock_update_es.return_value = {'_index': index_name,
            '_id': doc_id,
            'result': 'updated',
            '_shards': {'total': 1, 'successful': 1, 'failed': 0}
        }
        result = ESFuncs.update_counter(index_name, doc_id)

        expected_script = {
            "script": {
                "source": "ctx._source.counter += params.count",
                "lang": "painless",
                "params": {"count": 1}
            }
        }
        mock_update_es.assert_called_once_with(index_name=index_name, id=doc_id, body=expected_script)
        assert result == {'_index': index_name,
            '_id': doc_id,
            'result': 'updated',
            '_shards': {'total': 1, 'successful': 1, 'failed': 0}
        }
        mock_logger_info.assert_called()


    @pytest.mark.parametrize(
        "calendar_interval, start_date, end_date, expected",
        [
            ('day', '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z', ("yyyy-MM-dd", "2024-01-01", "2024-01-02")),
            ('week', '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z', ("yyyy-MM-dd", "2024-01-01", "2024-01-02")),
            ('month', '2024/01/01 00:00:00', '2024/03/01T00:00:00', ("yyyy-MM", "2024-01", "2024-03")),
            ('quarter', '2024/01/01T00:00:00Z', '2024/03/01 00:00:00Z', ("yyyy-MM", "2024-01", "2024-03")),
            ('year', '2024-01-01T00:00:00', '2025-01-01 00:00:00', ("yyyy", "2024", "2025")),
            ('other', '2024-01-01 00:00:00Z', '2024-02-01T00:00:00Z', ("yyyy-MM-dd HH:mm:ss", '2024-01-01 00:00:00', '2024-02-01 00:00:00'))
        ]
    )
    def test_extract_calendar_interval(self, calendar_interval, start_date, end_date, expected):
        result = ESFuncs.extract_calendar_interval(calendar_interval, start_date, end_date)
        assert result == expected


    @patch('controllers.elasticsearch_controller.ElasticsearchCRUD.search_es', autospec=True)
    def test_aggregate_sentence_total_by_days(self, mock_search_es):
        mock_search_es.return_value = {
            'aggregations': {'total_by_day': {'buckets': []}, 'total_count': {'value': 100}}
        }

        data = {
            'calendar_interval': 'day',
            'start_date': '2024-01-01T00:00:00Z',
            'end_date': '2024-01-31T00:00:00Z'
        }

        result = ESFuncs.aggregate_sentence_total_by_days('test_index', data)

        expected_query = {
            "size": 0,
            "query": {
                "bool": {
                    "filter": [
                        {
                            "range": {
                                "created_at": {
                                    "gte": data['start_date'],
                                    "lte": data['end_date']
                                }
                            }
                        }
                    ]
                }
            },
            "aggs": {
                "total_by_day": {
                    "date_histogram": {
                        "field": "created_at",
                        "calendar_interval": data['calendar_interval'],
                        "format": "yyyy-MM-dd",
                        "extended_bounds": {
                            "min": '2024-01-01',
                            "max": '2024-01-31'
                        }
                    }
                },
                "total_count": {
                    "sum": {
                        "field": "counter"
                    }
                }
            }
        }

        mock_search_es.assert_called_once_with(index_name='test_index', **expected_query)
        assert result == {"status": True, "data": {'total_by_day': {'buckets': []}, 'total_count': {'value': 100}}}

    @patch('controllers.elasticsearch_controller.ElasticsearchCRUD.search_es', autospec=True)
    def test_check_sentence_exists(self, mock_search_es):
        mock_search_es.return_value = {
            'hits': {
                'total': {'value': 1},
                'hits': [{'_id': '1', '_source': {'sentence': 'sentence'}}]
            }
        }

        is_exist, result = ESFuncs.check_sentence_exists('test_index', 'sentence')

        expected_query = {"term": {"sentence.keyword": 'sentence'}}

        mock_search_es.assert_called_once_with(index_name='test_index', query=expected_query)
        assert is_exist == True
        assert result == {'sentence': 'sentence'}