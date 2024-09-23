from dateutil.parser import parse as date_parse

from configs.db import MongoDBConnection


class MongoDBCRUD(MongoDBConnection):
    def __init__(self):
        super().__init__()


class MGFuncs(MongoDBCRUD):
    @staticmethod
    def compute_pagination(collection, query, page, page_size):
        skip_count = (page - 1) * page_size
        total_hits = collection.count_documents(query)
        page_count = (total_hits + page_size - 1) // page_size
        return skip_count, {
            "page": page,
            "pageSize": page_size,
            "pageCount": page_count,
            "total": total_hits
        }

    @staticmethod
    def query_action(collection, query, projection, sort, skip_count, page_size):
        items = collection.find(query, projection)
        items = items.sort(sort) if sort else items
        items = items.skip(skip_count).limit(page_size)
        return items

    @staticmethod
    def convert_string_to_boolean(value):
        if any(isinstance(value, t) for t in [bool, int]):
            return bool(value)
        elif isinstance(value, str):
            if value.lower() in ['true', 't', 'yes', 'y', '1']:
                return True
            elif value.lower() in ['false', 'f', 'no', 'n', '0']:
                return False
        return False
    
    @staticmethod
    def convert_filter_to_mongo_query(filter_item):
        filter_type = filter_item['type']
        operator = filter_item['operator']

        if filter_type == "term":
            value = {f"${k}":v for k, v in operator.items() if v is not None}
        elif filter_type == "bool":
            value = {f"${k}":MGFuncs.convert_string_to_boolean(v) for k, v in operator.items() if v is not None}
        elif filter_type == "range":
            value = {f"${op}": val for op, val in operator.items() if val is not None}
        elif filter_type == "wildcard":
            wildcard_regex = ".*" + operator.get('like', '').replace("*", ".*") + ".*"
            value = {"$regex": wildcard_regex}
        elif filter_type == "datetime":
            value = {f"${op}": date_parse(val) for op, val in operator.items() if val is not None}
        return value

    @classmethod
    def query_collection(cls, body, collection) -> tuple:
        body = body.model_dump()

        or_query = list(map(lambda x: {x['field']: cls.convert_filter_to_mongo_query(x)}, body['filter']))
        query = {"$and": or_query} if or_query else {}

        if body['include']:
            projection = dict(map(lambda x: (x, 1), body['include']))
            if '_id' not in body['include']:
                projection.update({"_id": 0})
        else:
            projection = dict(map(lambda x: (x, 0), body['exclude']))
        sort = list(body['sort'].items())

        skip_count, pagination = cls.compute_pagination(collection, query, body['page'], body['pageSize'])
        items = cls.query_action(collection, query, projection, sort, skip_count, body['pageSize'])
        return items, pagination 