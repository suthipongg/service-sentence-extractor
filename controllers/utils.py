import json
import random
import string
import es_model
from config.db import es_client
from elasticsearch.helpers import bulk
from datetime import datetime, date, timedelta
from config.environment import ENV
env = ENV()


class Utils:
    def __init__(self):
        self.index_extracted = env.NAME_INDEX_EXTRACETED

        print('[START] Create Index EXTRACETED :::')
        self.create_index_es(self.index_extracted, es_model.extractMapping)
        print('[END] Create Index EXTRACETED :::')

        # Get the current date as a string in ISO format with time set to 00:00:00 AM
        self.first_day, self.last_day = self.get_first_last_date_of_month()
        self.date_now_str = datetime.now().strftime('%d%m%Y')

    def create_index_es(self, index_name, mapping):
        isIndex = es_client.indices.exists(index_name)
        if not isIndex:
            data = json.loads(json.dumps(mapping))
            created = es_client.indices.create(index_name, body=data, ignore=[400, 404])
            print(created)

    def get_first_last_date_of_month(self):
        today = datetime.now()
        first_day = today.replace(day=1)
        next_month = first_day.replace(month=first_day.month % 12 + 1)
        last_day = next_month - timedelta(days=1)
        return first_day, last_day
    
    def bulk_extracted(self, datas):
        actions = []
        for data in datas:
            action = {
                "_index": self.index_extracted,
                "_op_type": "index",  # Use "index" for indexing documents
                "_id": data['id'],
                "_source": data  # Your document data
            }
            actions.append(action)
        success, failed = bulk(
                        es_client,
                        actions,
                    )
        print({"success": success, "failed":failed})

    def update_counter_extracted(self, _id):
        return self.update_counter(self.index_extracted, _id)

    def update_counter(self, index_name, _id):
        script = {
            "script": {
                "source": "ctx._source.counter += params.count",
                "lang": "painless",
                "params": {
                "count": 1
                }
            }
        }
        updated = es_client.update(index=index_name, id=_id, body=script)
        print(updated)

    def generate_unique_id(self, length):
        characters = string.ascii_letters + string.digits
        unique_id = ''.join(random.choice(characters) for _ in range(length))
        return unique_id
    
    def delete_extracted(self, _id):
        deleted = es_client.delete(index=self.index_extracted, id=_id, ignore=[400, 404])
        print(deleted)
    

    def get_sentence(self, sentence: str):
        query = {
                "query": {
                        "term": {
                        "sentence.keyword": {
                            "value": sentence
                        }
                    }
                }
            }
        result = es_client.search(index=self.index_extracted, body=query)
        hits_total = result['hits']['total']['value']
        if hits_total == 0:
            return {"is_exist": False}
        return {"is_exist": True, "result": result['hits']['hits'][0]['_source']}
    

    def group_by_sentence(self, data):

        if data['calendar_interval'] == 'day' or data['calendar_interval'] == 'week':
            _format = "yyyy-MM-dd"
            _min = data['start_date'][:10]
            _max = data['end_date'][:10]
        elif data['calendar_interval'] == 'month' or data['calendar_interval'] == 'quarter':
            _format = "yyyy-MM"
            _min = data['start_date'][:7]
            _max = data['end_date'][:7]
        elif data['calendar_interval'] == 'year':
            _format = "yyyy"
            _min = data['start_date'][:4]
            _max = data['end_date'][:4]
        else:
            _format = "yyyy-MM-dd HH:mm:ss"
            _min = data['start_date'].replace('T', ' ')
            _max = data['end_date'].replace('T', ' ')

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

        result = es_client.search(index=self.index_extracted, body=query, ignore=[404, 400])
        return {"status": True, "data": result['aggregations']}

