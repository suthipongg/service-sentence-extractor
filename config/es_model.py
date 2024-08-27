

autoFieldMapping = {
    "description": "sets the field",
    "processors": [
        {
            "set": {
                "field": "@timestamp",
                "value": "{{{_ingest.timestamp}}}"
            }
        },
        {
            "set": {
                "field": "version",
                "value": "0.0.1"
            }
        }
    ]
}


settingsMapping = {
    # "index.default_pipeline": os.getenv('NAME_AUTO_FIELD'),
    "analysis": {
        "number_of_shards": 1,
        "number_of_replicas": 1,
        "filter": {
            "autocomplete_filter": {
                "type": "edge_ngram",
                "min_gram": 2,
                "max_gram": 50
            },
            "shingle": {
                "type": "shingle",
                "min_shingle_size": 2,
                "max_shingle_size": 3
            },
            "stopwords_filter": {
                "type": "stop",
                "stopwords": [
                    "_english_",
                    "_thai_"
                ]
            }
        },
        "analyzer": {
            "autocomplete": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": [
                    "lowercase",
                    "autocomplete_filter"
                ],
                "char_filter": [
                    "html_strip"
                ]
            },
            "trigram": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": [
                    "lowercase",
                    "shingle"
                ],
                "char_filter": [
                    "html_strip"
                ]
            }
        }
    }
}


extractMapping = {
    "settings": settingsMapping,
    "mappings": {
        "properties": {
            "id": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword"
                    }
                }
            },
            "sentence": {
                "type": "text",
                "fields": {
                    "trigram": {
                        "type": "text",
                        "analyzer": "trigram"
                    },
                    "keyword": {
                        "type": "keyword"
                    },
                    "autocomplete": {
                        "type": "text",
                        "analyzer": "autocomplete",
                        "search_analyzer": "standard",
                    },
                    "completion": {
                        "type": "completion"
                    }
                }
            },
            "sentence_vector": {
                "type": "dense_vector",
                "dims": 1024
            },
            "created_at" : {
                "type" : "date"
            },
            "counter": {
                "type": "long",
                "fields": {
                    "keyword": {
                        "type": "keyword"
                    }
                }
            }
        }
    }
}

tokenizedMapping = {
    "settings": settingsMapping,
    "mappings": {
        "properties": {
            "id": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword"
                    }
                }
            },
            "method": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword"
                    }
                }
            },
            "prompt_id": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword"
                    }
                }
            },
            "active_context": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword"
                    }
                }
            },
            "message": {
                "type": "text",
                "fields": {
                    "trigram": {
                        "type": "text",
                        "analyzer": "trigram"
                    },
                    "keyword": {
                        "type": "keyword"
                    },
                    "autocomplete": {
                        "type": "text",
                        "analyzer": "autocomplete",
                        "search_analyzer": "standard",
                    },
                    "completion": {
                        "type": "completion"
                    }
                }
            },
            "keyword": {
                "type": "text",
                "fields": {
                    "trigram": {
                        "type": "text",
                        "analyzer": "trigram"
                    },
                    "keyword": {
                        "type": "keyword"
                    },
                    "autocomplete": {
                        "type": "text",
                        "analyzer": "autocomplete",
                        "search_analyzer": "standard",
                    },
                    "completion": {
                        "type": "completion"
                    }
                }
            },
            "created_at" : {
                "type" : "date"
            },
            "updated_at" : {
                "type" : "date"
            }
        }
    }
}