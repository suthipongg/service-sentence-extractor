import json
import requests
import random
import string
import os
import math
import es_model
from config.db import es_client
from elasticsearch.helpers import bulk

from config.environment import ENV
env = ENV()


class Utils:
    def __init__(self):
        self.index_extracted = env.NAME_INDEX_EXTRACETED

        print('[START] Create Index EXTRACETED :::')
        self.create_index_es(self.index_extracted, es_model.extractMapping)
        print('[END] Create Index EXTRACETED :::')

    def create_index_es(self, index_name, mapping):
        isIndex = es_client.indices.exists(index_name)
        if not isIndex:
            data = json.loads(json.dumps(mapping))
            created = es_client.indices.create(index_name, body=data, ignore=[400, 404])
            print(created)
      
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

