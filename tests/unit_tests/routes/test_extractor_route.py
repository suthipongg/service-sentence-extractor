import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from fastapi import FastAPI

from bson import ObjectId
import datetime

from routes.extractor_route import extractor_route, get_token

def mock_get_token():
    with patch("routes.extractor_route.get_token") as mock:
        mock.return_value = "mocked_token"
        yield mock

@pytest.fixture(scope="function")
def mock_collection_extracted():
    with patch('routes.extractor_route.MGCollection') as mock:
        mock.EXTRACTED = MagicMock()
        yield mock.EXTRACTED

@pytest.fixture(scope="function")
def mock_search_es():
    with patch('routes.extractor_route.ESFuncs.search_es') as mock:
        yield mock

@pytest.fixture(scope="function")
def mock_extract():
    with patch('routes.extractor_route.SentenceExtractor') as mock:
        yield mock.return_value.extract

@pytest.fixture(scope="function")
def mock_es_index():
    with patch('routes.extractor_route.ESIndex') as mock:
        mock.EXTRACTED = "mocked_extracted_index"
        yield mock

@pytest.fixture(scope="function")
def client():
    app = FastAPI()
    app.include_router(extractor_route)
    app.dependency_overrides[get_token] = mock_get_token
    return TestClient(app)


def test_embedding_model_success(mock_extract, client):
    mock_extract.return_value = [[4, 5, 6]]
    body = {"sentences": "This is a test sentence"}
    response = client.post(
        "/extractor/model",
        json=body,
    )

    assert response.status_code == 200
    assert response.json() == {"vector": [[4, 5, 6]]}
    mock_extract.assert_called_once_with(["This is a test sentence"])

def test_embedding_model_list_success(mock_extract, client):
    mock_extract.return_value = [[4, 5, 6], [7, 8, 9]]
    body = {"sentences": ["This is a test sentence", "This is another test sentence"]}
    response = client.post(
        "/extractor/model",
        json=body,
    )

    assert response.status_code == 200
    assert response.json() == {"vector": [[4, 5, 6], [7, 8, 9]]}
    mock_extract.assert_called_once_with(["This is a test sentence", "This is another test sentence"])


def test_multiple_sentence_embedding_sentences(mock_search_es, mock_extract, mock_es_index, client):
    mock_search_es.side_effect = [
        {'hits': {'total': {'value': 1}, 
                  'hits': [{'_source': {'sentence_vector': [0.1, 0.2, 0.3]}}]}},  # Existing
        {'hits': {'total': {'value': 0}}},  # Non-existing
        {'hits': {'total': {'value': 0}}},  # Non-existing
        {'hits': {'total': {'value': 1}, 
                  'hits': [{'_source': {'sentence_vector': [0.4, 0.5, 0.6]}}]}},  # Existing
    ]
    mock_extract.return_value = [[1, 2, 3], [4, 5, 6]]

    body = {
        "sentences": ["Existing sentence 1", "New sentence 1", "New sentence 2", "Existing sentence 2"]
    }
    response = client.post("/extractor/elasticsearch/multiple", json=body)

    assert response.status_code == 200
    data = response.json()
    assert len(data['result']) == 4
    assert data['result'] == [[0.1, 0.2, 0.3], [1, 2, 3], [4, 5, 6], [0.4, 0.5, 0.6]]


def test_single_sentence_embedding_success(mock_search_es, mock_extract, mock_es_index, client):
    mock_search_es.return_value = {
        "hits": {
            "total": {"value": 1},
            "hits": [
                {
                    "_source": {
                        "sentence_vector": [1, 2, 3],
                        "id": 1,
                        'counter': 1
                    }
                }
            ]
        }
    }
    body = {"sentence": "This is a test sentence"}
    response = client.post(
        "/extractor/elasticsearch/single",
        json=body,
    )

    assert response.status_code == 200
    assert response.json() == {"is_exist": True, "result": {
        "sentence_vector": [1, 2, 3],
        "id": 1,
        'counter': 1
    }}

    mock_search_es.assert_called_once()
    mock_extract.assert_not_called()

def test_single_sentence_embedding_not_exist(mock_search_es, mock_extract, mock_es_index, client):
    mock_search_es.return_value = {
        "hits": {"total": {"value": 0}, "hits": []}
    }
    mock_extract.return_value = [[4, 5, 6]]

    body = {"sentence": "New sentence"}
    response = client.post(
        "/extractor/elasticsearch/single",
        json=body,
    )

    assert response.status_code == 200
    assert response.json() == {"is_exist": False, "result": [4, 5, 6]}  # New sentence extracted

    mock_search_es.assert_called_once()
    mock_extract.assert_called_once_with(["New sentence"])
    

@patch('routes.extractor_route.ESFuncs.update_counter')
@patch('routes.extractor_route.single_sentence_embedding')
def test_extractor_sentence_exists(mock_sentence_embedding, mock_es_funcs, mock_collection_extracted, mock_es_index, client):
    mock_collection_extracted.update_one = MagicMock()
    mock_sentence_embedding.return_value = {
        "is_exist": True, 
        "result": {
            "sentence_vector": [1, 2, 3],
            "id": '605c72f1537f2a001ddae54f',
            'counter': 1
        }
    }
    body = {"sentence": "This is a test sentence"}
    response = client.post("/extractor", json=body)

    assert response.status_code == 200
    data = response.json()
    assert data == {
        "sentence_vector": [1, 2, 3],
        "id": '605c72f1537f2a001ddae54f',
        'counter': 2
    }
    mock_collection_extracted.update_one.assert_called_once_with(
        filter = {"_id": ObjectId('605c72f1537f2a001ddae54f')},
        update = {"$set": {"counter": 2}}
    )
    mock_es_funcs.assert_called_once_with(
        index_name = 'mocked_extracted_index', 
        id = '605c72f1537f2a001ddae54f'
    )

@patch('routes.extractor_route.ESFuncs.insert_es')
@patch('routes.extractor_route.single_sentence_embedding')
def test_extractor_sentence_not_exists(mock_sentence_embedding, mock_es_funcs, mock_collection_extracted, mock_es_index, client):
    mock_collection_extracted.insert_one.return_value = MagicMock(inserted_id=ObjectId('605c72f1537f2a001ddae54f'))
    mock_sentence_embedding.return_value = {
        "is_exist": False, 
        "result": [1, 2, 3]
    }
    body = {"sentence": "This is a new sentence", 'created_at': '2024-09-17T13:47:04.031272'}
    response = client.post("/extractor", json=body)

    assert response.status_code == 200
    data = response.json()
    assert data == {
        "sentence": "This is a new sentence",
        "sentence_vector": [1, 2, 3],
        'created_at': '2024-09-17T13:47:04.031272', 
        "id": '605c72f1537f2a001ddae54f',
        'counter': 1
    }
    mock_collection_extracted.insert_one.assert_called_once_with(
        {
            'sentence': 'This is a new sentence', 
            'created_at': datetime.datetime(2024, 9, 17, 13, 47, 4, 31272), 
            'counter': 1, 
        }
    )
    mock_es_funcs.assert_called_once_with(
        'mocked_extracted_index', 
        {
            'sentence': 'This is a new sentence', 
            'created_at': datetime.datetime(2024, 9, 17, 13, 47, 4, 31272), 
            "id": '605c72f1537f2a001ddae54f',
            'counter': 1, 
            'sentence_vector': [1, 2, 3], 
        },
        id = '605c72f1537f2a001ddae54f'
    )


def test_embedded_model_warmup_success(mock_extract, client):
    mock_extract.return_value = None
    response = client.get("/extractor/model/warmup")
    assert response.status_code == 200
    assert response.json() == {"detail": "success"}
    mock_extract.assert_called_once_with('สวัสดีครับ')


@patch('routes.extractor_route.MGFuncs.query_collection')
@patch('routes.extractor_route.extract_serializer_list')
def test_extractor_get_list_success(mock_serializer, mock_query, mock_collection_extracted, client):
    mock_items = [
        {"id": "id1", "sentence": "test sentence 1"},
        {"id": "id2", "sentence": "test sentence 2"}
    ]
    mock_pagination = {"page": 1, "pageSize": 10, "pageCount":1, "total": 2}
    mock_serializer.return_value = mock_items
    mock_query.return_value = (MagicMock(), mock_pagination)

    response = client.post("/extractor/getList", json={})
    assert response.status_code == 200
    assert response.json() == {
        "status": True,
        "data": mock_items,
        "meta": {"pagination": mock_pagination}
    }
    mock_serializer.assert_called_once()

@patch('routes.extractor_route.MGFuncs.query_collection')
@patch('routes.extractor_route.extract_serializer_list')
def test_extractor_get_list_no_data(mock_serializer, mock_query, mock_collection_extracted, client):
    mock_items = []
    mock_serializer.return_value = mock_items
    mock_pagination = {"page": 1, "size": 10, "total": 0}
    mock_query.return_value = (MagicMock(), mock_pagination)
    
    response = client.post("/extractor/getList", json={})
    assert response.status_code == 200
    assert response.json() == {
        "status": True,
        "data": [],
        "meta": {"pagination": mock_pagination}
    }

def test_get_one_extracted_success(mock_collection_extracted, client):
    mock_collection_extracted.find_one.return_value = {
        "_id": ObjectId('605c72f1537f2a001ddae54f'), 
        "sentence": "test sentence",
        "counter": 1,
        "created_at": "2023-09-05",
        "extra_field": "this should be ignored"
    }
    response = client.get("/extractor/605c72f1537f2a001ddae54f")
    assert response.status_code == 200
    assert response.json() == {
        "status": True,
        "data": {
            "id": '605c72f1537f2a001ddae54f', 
            "sentence": "test sentence",
            "counter": 1,
            "created_at": "2023-09-05",
        }
    }

def test_get_one_extracted_not_found(mock_collection_extracted, client):
    mock_collection_extracted.find_one.return_value = {}
    response = client.get("/extractor/605c72f1537f2a001ddae54f")
    assert response.status_code == 200
    assert response.json() == {"status": False, "detail": "Item not found."}


@patch('routes.extractor_route.ESFuncs.delete_es')
def test_delete_extractor_success(mock_delete_es, mock_es_index, mock_collection_extracted, client):
    mock_collection_extracted.find_one.return_value = {
        "_id": ObjectId('605c72f1537f2a001ddae54f'), 
        "sentence": "test sentence", 
        "counter": 1, 
        "created_at": "2023-09-05", 
        "extra_field": "this should be ignored"
    }
    mock_collection_extracted.delete_one = MagicMock()
    response = client.delete("/extractor/605c72f1537f2a001ddae54f")
    assert response.status_code == 200
    assert response.json() == {
        "status": True,
        "data": {
            "id": '605c72f1537f2a001ddae54f',
            "sentence": "test sentence", 
            "counter": 1, 
            "created_at": "2023-09-05"
        }
    }
    mock_collection_extracted.find_one.assert_called_once_with(
        {"_id": ObjectId('605c72f1537f2a001ddae54f')})
    mock_collection_extracted.delete_one.assert_called_once_with(
        filter={"_id": ObjectId('605c72f1537f2a001ddae54f')})
    mock_delete_es.assert_called_once_with(
        index_name="mocked_extracted_index", id="605c72f1537f2a001ddae54f")

def test_delete_extractor_not_found(mock_collection_extracted, client):
    mock_collection_extracted.find_one.return_value = None
    response = client.delete("/extractor/605c72f1537f2a001ddae54f")

    assert response.status_code == 200
    assert response.json() == {"status": False, "detail": "Item not found."}