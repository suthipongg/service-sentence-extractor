from unittest.mock import patch

from configs.es_model import ElasticSearchConfigs, ElasticsearchIndexConfigs
from configs.config import SettingsManager

def test_elasticsearch_configs():
    expected_settings = {
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
    
    assert ElasticSearchConfigs.Settings == expected_settings

def test_elasticsearch_index_configs(mock_settings_manager):
    mock_settings_manager.sentences_vector_size = 33
    ElasticsearchIndexConfigs()
    expected_index_config = {
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
                    "dims": 33
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

    assert ElasticsearchIndexConfigs.EXTRACTED_CONFIG == expected_index_config