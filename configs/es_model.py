from configs.environment import ENV

class ElasticSearchConfigs:
    Settings = {
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

class ElasticsearchIndexConfigs:
    EXTRACTED_CONFIG = {
        "settings": ElasticSearchConfigs.Settings,
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
                    "dims": ENV.SENTENCES_VECTOR_SIZE
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