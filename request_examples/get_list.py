from datetime import datetime
import random
import string

getList = {
    "normal": {
        "summary": "A normal example",
        "description": "A **normal** item works correctly.",
        "value": {
            "page": 1,
            "pageSize": 12,
            "sort": {},
            "filter": []
        }

    },
    "term": {
        "summary": "A filter term example",
        "description": "A filter **term** item works correctly.",
        "value": {
            "page": 1,
            "pageSize": 12,
            "sort": {
                "score": 1
            },
            "filter": [
                {
                    "type": "term",
                    "field": "sentence",
                    "operator": {
                        "eq": "test"
                    }
                }
            ]
        }

    },
    "boolean": {
        "summary": "A filter boolean example",
        "description": "A filter **boolean** item works correctly.",
        "value": {
            "page": 1,
            "pageSize": 12,
            "sort": {
                "score": 1
            },
            "filter": [
                {
                    "type": "bool",
                    "field": "active",
                    "operator": {
                        "eq": True
                    }
                }
            ]
        }
    },
    "wildcard": {
        "summary": "A filter wildcard example",
        "description": "A filter **wildcard** item works correctly.",
        "value": {
            "page": 1,
            "pageSize": 12,
            "sort": {
                "score": 1
            },
            "filter": [
                {
                    "type": "wildcard",
                    "field": "sentence",
                    "operator": {
                        "like": "test"
                    }
                }
            ]
        }

    },
    "range": {
        "summary": "A filter range example",
        "description": "A filter **range** item works correctly.",
        "value": {
            "page": 1,
            "pageSize": 12,
            "sort": {
                "score": 1
            },
            "filter": [
                {
                    "type": "range",
                    "field": "score",
                    "operator": {"gte": 0.5, "lte": 0.7}
                }
            ]
        }

    },
    "datetime": {
        "summary": "A filter datetime example",
        "description": "A filter **datetime** item works correctly.",
        "value": {
            "page": 1,
            "pageSize": 12,
            "sort": {
                "score": 1
            },
            "filter": [
                {
                    "type": "datetime",
                    "field": "created_at",
                    "operator": {
                        "gte": "2024-03-27",
                        "lte": "2024-03-28"
                    }
                }
            ]
        }

    },
    "and": {
        "summary": "A filter multiple filed example",
        "description": "A filter **multiple** item works correctly.",
        "value": {
            "page": 1,
            "pageSize": 12,
            "sort": {
                "score": 1
            },
            "filter": [
                {
                    "type": "wildcard",
                    "field": "sentence",
                    "operator": {
                        "like": "test"
                    }
                },
                {
                    "type": "datetime",
                    "field": "created_at",
                    "operator": {
                        "gte": "2024-03-27",
                        "lte": "2024-03-28"
                    }
                }
            ]
        }

    }
}
