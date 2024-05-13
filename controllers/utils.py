import json
import random
import string
import es_model
from config.db import es_client
from elasticsearch.helpers import bulk
from datetime import datetime, date, timedelta
from config.environment import ENV
from dateutil.parser import parse as date_parse
from pythainlp.corpus import thai_stopwords
from pythainlp.tokenize import word_tokenize
import nltk

env = ENV()


class Utils:
    def __init__(self):
        self.index_extracted = env.NAME_INDEX_EXTRACETED
        self.intex_trainnlu = env.NAME_INDEX_TRAIN_NLU
        self.index_trainnlu_tokenized = env.NAME_INDEX_TRAIN_NLU_TOKENIZED
        self.index_tokenized = env.NAME_INDEX_TOKENIZED

        print('[START] Create Index EXTRACETED :::')
        self.create_index_es(self.index_extracted, es_model.extractMapping)
        print('[END] Create Index EXTRACETED :::')
        print('[START] Create Index tokenized :::')
        self.create_index_es(self.index_trainnlu_tokenized, es_model.tokenizedMapping)
        print('[END] Create Index tokenized :::')

        # Get the current date as a string in ISO format with time set to 00:00:00 AM
        self.first_day, self.last_day = self.get_first_last_date_of_month()
        self.date_now_str = datetime.now().strftime('%d%m%Y')
        self.stopwords = list(thai_stopwords())
        

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
    
    def remove_stop_word(self, text):
        list_word = word_tokenize(text)
        list_word_not_stopwords = [i for i in list_word if i not in self.stopwords]
        return ''.join(list_word_not_stopwords)
    
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
    

    def convert_to_boolean(self, value):
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            # Convert string representations of boolean values to boolean
            if value.lower() in ['true', 't', 'yes', 'y', '1']:
                return True
            elif value.lower() in ['false', 'f', 'no', 'n', '0']:
                return False
        # Return False for other types or unrecognized string values
        return False

    async def filter_collection(self, body, collection) -> tuple:
        query = {}
        projection = {}
        sort = []
        or_query = []
        
        # Include fields
        if body.include:
            for field in body.include:
                projection[field] = 1
        
        # Exclude fields
        if body.exclude:
            for field in body.exclude:
                projection[field] = 0
        
        for filter_item in body.filter:
            field = filter_item.field
            filter_type = filter_item.type
            operator = filter_item.operator
            if filter_type == "term":
                # query[field] = operator.eq
                or_query.append({field: operator.eq})
            elif filter_type == "bool":
                # query[field] = operator.eq
                or_query.append({field: self.convert_to_boolean(operator.eq)})
            elif filter_type == "range":
                range_query = {}
                if operator.gte is not None:
                    range_query["$gte"] = operator.gte
                if operator.lte is not None:
                    range_query["$lte"] = operator.lte
                if operator.gt is not None:
                    range_query["$gt"] = operator.gt
                if operator.lt is not None:
                    range_query["$lt"] = operator.lt
                # query[field] = range_query
                or_query.append({field: range_query})
            elif filter_type == "wildcard":
                wildcard_regex = ".*" + operator.like.replace("*", ".*") + ".*"
                # query[field] = {"$regex": wildcard_regex}
                or_query.append({field: {"$regex": wildcard_regex}})
            elif filter_type == "datetime":
                range_query = {}
                if operator.gte is not None:
                    range_query["$gte"] = date_parse(operator.gte)
                if operator.lte is not None:
                    range_query["$lte"] = date_parse(operator.lte)
                if operator.gt is not None:
                    range_query["$gt"] = date_parse(operator.gt)
                if operator.lt is not None:
                    range_query["$lt"] = date_parse(operator.lt)
                or_query.append({field: range_query})

        # Combine wildcard queries with $or operator
        if or_query:
            query["$and"] = or_query

        # Sort criteria
        for field, value in body.sort.items():
            sort.append((field, value))

        # Calculate pagination metadata
        page_start = (body.page - 1) * body.pageSize
        page_size = body.pageSize
        total_hits = collection.count_documents(query)
        page_count = (total_hits + page_size - 1) // page_size
        # Fetch items from MongoDB based on the query and pagination
        if sort:
            items = collection.find(query, projection).sort(sort).skip(page_start).limit(page_size)
        else:
            items = collection.find(query, projection).skip(page_start).limit(page_size)
          
        pagination = {
            "page": body.page,
            "pageSize": body.pageSize,
            "pageCount": page_count,
            "total": total_hits
        }

        return items, pagination 
    

    def bulk_trainnlu_tokenized(self, datas):
        actions = []
        for data in datas:
            action = {
                "_index": self.index_trainnlu_tokenized,
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
        return {"success": success, "failed":failed}
    
    async def get_trainnlu_datas(self):
        query = {
            "_source": [
            "id",
            "message",
            "method",
            "action_send",
            "prompt_id",
            "keywords"
            ],
            "size": 10000,
            "query": {
                "bool": {
                    "must": [
                    {
                        "term": {
                        "active.keyword": {
                            "value": "1"
                        }
                        }
                    },
                    {
                        "term": {
                        "level.keyword": {
                            "value": "2"
                        }
                        }
                    }
                    ]
                }
            }
        }

        result = es_client.search(index=self.intex_trainnlu, body=query, ignore=[404, 400])

        datas = []
        for hit in result['hits']['hits']:
            _source = hit['_source']
            _keywords = ''
            keywords:str = _source['keywords']
            for keyword in keywords.split(','):
                text = keyword.strip()
                new_keyword = await self.ngrams(text)
                new_keyword_list = new_keyword.split(' ')
                _keywords += ','.join([r.strip() for r in new_keyword_list if r != ''])
            _source['keywords'] = ','.join(list(set(_keywords.split(','))))
            datas.append(_source)

        await self.delete_all_document(self.index_trainnlu_tokenized)
        return self.bulk_trainnlu_tokenized(datas)
      

    async def ngrams(self, text):
        # Tokenize the input text
        tokens = word_tokenize(text)

        # Generate bigrams
        bigrams = list(nltk.ngrams(tokens, 2))

        # Append bigrams to the tokens list
        tokens += [''.join(bigram) for bigram in bigrams]

        return ' '.join(tokens)


    async def delete_all_document(self, index_name):
        query = {"query" : { 
                "match_all" : {}
            }}
        result = es_client.delete_by_query(index_name, body=query)
        print('delete_all_document ::: >>> ', result)