import pytest


@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown_data(client, valid_auth_token):
    yield
    response_id = client.post(
        "/extractor/getList",
        json={
            "filter": [
                {
                    "field": "created_at", 
                    "operator": {
                        "gte":"1970-01-01T00:00:00", 
                        "lt":"1971-01-01T00:00:00"
                    }, 
                    "type":"datetime"
                }
            ]
        },
        headers={"Authorization": valid_auth_token},
    )
    for item in response_id.json()['data']:
        client.delete(
            f"/extractor/{item['id']}",
            headers={"Authorization": valid_auth_token},
        )


def test_embedded_model(client, valid_auth_token):
    response = client.post(
        "/extractor/model",
        json={"sentences": ["Hello world!"]},
        headers={"Authorization": valid_auth_token},
    )
    assert response.status_code == 200
    assert "vector" in response.json()
    assert len(response.json()["vector"]) == 1
    assert len(response.json()["vector"][0]) == 1024

def test_multiple_sentence_embedding(client, valid_auth_token):
    response = client.post(
        "/extractor/elasticsearch/multiple",
        json={"sentences": ["First sentence.", "Second sentence.", "Hello world!"]},
        headers={"Authorization": valid_auth_token},
    )
    result = response.json()
    assert response.status_code == 200
    assert len(result["result"]) == 3
    assert len(result["result"][0]) == 1024

def test_single_sentence_embedding_sentence_exist(client, valid_auth_token):
    response = client.post(
        "/extractor/elasticsearch/single",
        json={"sentence": "This is a single sentence."},
        headers={"Authorization": valid_auth_token},
    )
    result = response.json()
    assert response.status_code == 200
    assert result["is_exist"] == False

@pytest.mark.parametrize(
    "sentence, created_at", 
    [
        ("Extract this sentence.", "1970-01-02T00:00:01"),
        ("This is another single sentence.", "1970-01-01T00:00:01"),
    ]
)
def test_extractor_sentence(sentence, created_at, client, valid_auth_token):
    body = {
        "sentence": sentence
    }
    if created_at:
        body["created_at"] = created_at
    response = client.post(
        "/extractor",
        json=body,
        headers={"Authorization": valid_auth_token},
    )
    result = response.json()
    assert response.status_code == 200
    assert len(result['sentence_vector']) == 1024
    assert result['counter'] == 1

def test_single_sentence_embedding_sentence_not_exist(client, valid_auth_token):
    response = client.post(
        "/extractor/elasticsearch/single",
        json={"sentence": "Extract this sentence."},
        headers={"Authorization": valid_auth_token},
    )
    result = response.json()
    assert response.status_code == 200
    assert result["is_exist"] == True
    assert result['result']['counter'] == 1

def test_extractor_sentence_exists(client, valid_auth_token):
    response = client.post(
        "/extractor",
        json={"sentence": "Extract this sentence."},
        headers={"Authorization": valid_auth_token},
    )
    result = response.json()
    assert response.status_code == 200
    assert result['counter'] == 2

def test_embedded_model_warmup(client, valid_auth_token):
    response = client.get(
        "/extractor/model/warmup",
        headers={"Authorization": valid_auth_token},
    )
    result = response.json()
    assert response.status_code == 200
    assert result == {"detail": "success"}


@pytest.mark.parametrize(
    "page, page_size, include, exclude, sort, filter, expected_result, expect_pagination", 
    [
        (
            1, 10, [], ["sentence", "created_at", "_id"], {"created_at": -1}, [], 
            [{"counter": 2}, {"counter": 1}],
            {"page": 1,"pageSize": 10,"pageCount": 1,"total": 2}
        ),
        (
            1, 5, ["counter"], [], {"created_at": -1}, [{"field": "counter", "operator":{"eq":1}, "type":"term"}],
            [{"counter": 1}],
            {"page": 1,"pageSize": 5,"pageCount": 1,"total": 1}
        ),
        (
            1, 5, ["counter"], [], {"created_at": -1}, [{"field": "counter", "operator":{"ne":2}, "type":"term"}],
            [{"counter": 1}],
            {"page": 1,"pageSize": 5,"pageCount": 1,"total": 1}
        ),
        (
            1, 5, ["counter"], [], {"created_at": -1}, [{"field": "counter", "operator":{"gt":0, "lte":1}, "type":"range"}],
            [{"counter": 1}],
            {"page": 1,"pageSize": 5,"pageCount": 1,"total": 1}
        ),
        (
            1, 5, ["counter"], [], {"created_at": -1}, [{"field": "counter", "operator":{"gte":1, "lt":2}, "type":"range"}],
            [{"counter": 1}],
            {"page": 1,"pageSize": 5,"pageCount": 1,"total": 1}
        ),
        (
            1, 5, ["counter"], [], {"created_at": -1}, [{"field": "created_at", "operator":{"gt":"1970-01-01T00:00:00", "lte":"1970-01-01T00:00:01"}, "type":"datetime"}],
            [{"counter": 1}],
            {"page": 1,"pageSize": 5,"pageCount": 1,"total": 1}
        ),
        (
            1, 5, ["counter"], [], {"created_at": -1}, [{"field": "created_at", "operator":{"gte":"1970-01-01T00:00:01", "lt":"1970-01-02T00:00:01"}, "type":"datetime"}],
            [{"counter": 1}],
            {"page": 1,"pageSize": 5,"pageCount": 1,"total": 1}
        ),
        (
            1, 5, ["counter"], [], {"created_at": -1}, [{"field": "sentence", "operator":{"like":"single"}, "type":"wildcard"}],
            [{"counter": 1}],
            {"page": 1,"pageSize": 5,"pageCount": 1,"total": 1}
        ),
        (
            1, 5, ["counter"], [], {"created_at": -1}, [{"field": "sentence", "operator":{"like":"another*single"}, "type":"wildcard"}],
            [{"counter": 1}],
            {"page": 1,"pageSize": 5,"pageCount": 1,"total": 1}
        ),
        (
            2, 1, ["counter"], [], {"created_at": 1}, [],
            [{"counter": 2}],
            {"page": 2,"pageSize": 1,"pageCount": 2,"total": 2}
        ),
    ]
)
def test_extractor_get_list(
    page, 
    page_size, 
    include, 
    exclude, 
    sort, 
    filter, 
    expected_result, 
    expect_pagination,
    client, 
    valid_auth_token
):
    body = {
        "page": page,
        "pageSize": page_size,
        "include": include,
        "exclude": exclude,
        "sort": sort,
        "filter": filter
    }
    response = client.post(
        "/extractor/getList",
        json=body,
        headers={"Authorization": valid_auth_token},
    )
    result = response.json()
    assert response.status_code == 200
    assert result['status'] == True
    assert result['data'] == expected_result
    assert len(result['data']) <= expect_pagination['pageSize']
    assert result['meta']['pagination'] == expect_pagination

def test_get_one_extracted(client, valid_auth_token):
    response_id = client.post(
        "/extractor/getList",
        json={"filter":[{"field": "counter", "operator":{"eq":1}, "type":"term"}]},
        headers={"Authorization": valid_auth_token},
    )
    item_id = response_id.json()['data'][0]['id']
    response = client.get(
        f"/extractor/{item_id}",
        headers={"Authorization": valid_auth_token},
    )
    result = response.json()
    assert response.status_code == 200
    assert result['data']['id'] == item_id


def test_delete_extractor(client, valid_auth_token):
    response_id = client.post(
        "/extractor/getList",
        json={},
        headers={"Authorization": valid_auth_token},
    )
    item_id = response_id.json()['data'][0]['id']
    response = client.delete(
        f"/extractor/{item_id}",
        headers={"Authorization": valid_auth_token},
    )
    assert response.status_code == 200
    assert response.json().get("status") is True

    response = client.delete(
        f"/extractor/{item_id}",
        headers={"Authorization": valid_auth_token},
    )
    assert response.status_code == 200
    assert response.json().get("status") is False