from elasticsearch.helpers import bulk

from dateutil.parser import parse as date_parse

from configs.db import ElasticsearchConnection, ESIndex
from configs.logger import LoggerConfig


class ElasticsearchCRUD(ElasticsearchConnection):
    @classmethod
    def create_index_es(cls, index_name, mapping):
        index_exist = cls.es_client.indices.exists(index=index_name)
        if not index_exist:
            created = cls.es_client.indices.create(index=index_name, ignore=[400, 404], **mapping)
            return created
        return None

    @staticmethod
    def cvt_datas_to_bulk(index_name, datas):
        actions = []
        if not datas: return actions
        for data in datas:
            if not data: continue
            action = {
                "_index": index_name,
                "_op_type": "index",
                "_id": data.get("_id", None),
                "_source": data
            }
            actions.append(action)
        return actions

    @classmethod
    def bulk_es(cls, index_name, datas):
        actions = cls.cvt_datas_to_bulk(index_name, datas)
        success, failed = bulk(cls.es_client, actions)
        LoggerConfig.logger.info({"success": success, "failed":failed})
        return success, failed
    
    @classmethod
    def insert_es(cls, index_name, body, id=None):
        inserted = cls.es_client.index(index=index_name, document=body, id=id)
        return inserted

    @classmethod
    def update_es(cls, index_name, id, body):
        updated = cls.es_client.update(index=index_name, id=id, **body)
        return updated
    
    @classmethod
    def delete_es(cls, index_name, id):
        deleted = cls.es_client.delete(index=index_name, id=id, ignore=[400, 404])
        return deleted
    
    @classmethod
    def delete_by_query_es(cls, index_name, body):
        deleted = cls.es_client.delete_by_query(index=index_name, body=body)
        return deleted

    @classmethod
    def search_es(cls, index_name, **kwargs):
        cls.es_client.indices.refresh(index=index_name)
        search = cls.es_client.search(index=index_name, **kwargs)
        return search
    

class ESFuncs(ElasticsearchCRUD):
    @classmethod
    def start_index_es(cls):
        index = ESIndex()
        for index_name in index.all_index_name.keys():
            LoggerConfig.logger.info(f'[\033[96mSTART\033[0m] Create Index {index.all_index_name[index_name]} :::')
            created = cls.create_index_es(index.all_index_name[index_name], index.all_index_config[index_name])
            if created:
                LoggerConfig.logger.info(f'{index.all_index_name[index_name]} \033[96mCreated\033[0m :::')
            else:
                LoggerConfig.logger.info(f'{index.all_index_name[index_name]} Already Exists :::')
            LoggerConfig.logger.info(f'[\033[96mEND\033[0m] Create Index {index.all_index_name[index_name]} :::')

    @classmethod
    def update_counter(cls, index_name, id):
        script = {
            "script": {
                "source": "ctx._source.counter += params.count",
                "lang": "painless",
                "params": {"count": 1}
            }
        }
        updated = cls.update_es(index_name=index_name, id=id, body=script)
        LoggerConfig.logger.info(updated)
        return updated
    
    @staticmethod
    def extract_calendar_interval(calendar_interval, start_date, end_date):
        start_date = date_parse(start_date)
        end_date = date_parse(end_date)
        if calendar_interval == 'day' or calendar_interval == 'week':
            _format = "yyyy-MM-dd"
            _min = start_date.strftime('%Y-%m-%d')
            _max = end_date.strftime('%Y-%m-%d')
        elif calendar_interval == 'month' or calendar_interval == 'quarter':
            _format = "yyyy-MM"
            _min = start_date.strftime('%Y-%m')
            _max = end_date.strftime('%Y-%m')
        elif calendar_interval == 'year':
            _format = "yyyy"
            _min = start_date.strftime('%Y')
            _max = end_date.strftime('%Y')
        else:
            _format = "yyyy-MM-dd HH:mm:ss"
            _min = start_date.strftime('%Y-%m-%d %H:%M:%S')
            _max = end_date.strftime('%Y-%m-%d %H:%M:%S')
        return _format, _min, _max

    @classmethod
    def aggregate_sentence_total_by_days(cls, index_name, data):
        _format, _min, _max = cls.extract_calendar_interval(data['calendar_interval'], data['start_date'], data['end_date'])
        query = {
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
                        "format": _format,
                        "extended_bounds": {
                            "min": _min,
                            "max": _max
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
        result = cls.search_es(index_name=index_name, **query, ignore=[404, 400])
        return {"status": True, "data": result['aggregations']}
    
    @classmethod
    def check_sentence_exists(cls, index_name, sentence):
        query = {"term": {"sentence.keyword": sentence}}
        result = cls.search_es(index_name=index_name, query=query)['hits']
        is_exist = result['total']['value'] != 0
        return is_exist, result['hits'][0]['_source'] if is_exist else None