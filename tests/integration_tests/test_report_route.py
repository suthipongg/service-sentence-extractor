import pytest


@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown_data(client, valid_auth_token):
    bodys = [
        {
            "sentence": "sentence 1",
            "created_at": "1970-01-01T00:00:00",
        },
        {
            "sentence": "sentence 2",
            "created_at": "1970-02-01T00:00:00",
        },
        {
            "sentence": "sentence 3",
            "created_at": "1970-04-01T00:00:00",
        },
    ]
    for data in bodys:
        client.post(
            "/extractor",
            json=data,
            headers={"Authorization": valid_auth_token},
        )
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

@pytest.mark.parametrize(
    "custom_start_date, custom_end_date, calendar_interval, expected_bucket, expected_total",
    [
        (
            "1970-01-01T00:00:00", "1970-01-01T01:59:59", "hour",
            [{"key_as_string": "1970-01-01 00:00:00","doc_count": 1}, {"key_as_string": "1970-01-01 01:00:00","doc_count": 0}],
            1
        ),
        (
            "1970-01-01T00:00:00", "1970-01-02T23:59:59", "day",
            [{"key_as_string": "1970-01-01","doc_count": 1}, {"key_as_string": "1970-01-02","doc_count": 0}],
            1
        ),
        (
            "1970-01-01T00:00:00", "1970-01-14T23:59:59", "week",
            [{"key_as_string": "1969-12-29","doc_count": 1}, {"key_as_string": "1970-01-05","doc_count": 0}],
            1
        ),
        (
            "1970-01-01T00:00:00", "1970-02-28T23:59:59", "month",
            [{"key_as_string": "1970-01","doc_count": 1}, {"key_as_string": "1970-02","doc_count": 1}],
            2
        ),
        (
            "1970-01-01T00:00:00", "1970-12-31T23:59:59", "quarter",
            [{"key_as_string": "1970-01","doc_count": 2}, {"key_as_string": "1970-04","doc_count": 1}],
            3
        ),
        (
            "1970-01-01T00:00:00", "1970-12-31T23:59:59", "year",
            [{"key_as_string": "1970","doc_count": 3}],
            3
        ),
    ],
)
def test_extractor_report_custom_dates(
    custom_start_date, 
    custom_end_date, 
    calendar_interval, 
    expected_bucket, 
    expected_total, 
    client, 
    valid_auth_token
):
    response = client.get(
        f"/report/extractor?start_date={custom_start_date}&end_date={custom_end_date}&calendar_interval={calendar_interval}",
        headers={"Authorization": valid_auth_token},
    )
    assert response.status_code == 200
    result = response.json()
    assert result['status'], "The status should be True"
    assert result["data"]["total_count"]["value"] == expected_total
    for data, expected in zip(result['data']['total_by_day']["buckets"], expected_bucket):
        assert data['key_as_string'] == expected['key_as_string']
        assert data['doc_count'] == expected['doc_count']

def test_extractor_report_unauthorized(client):
    response = client.get("/report/extractor")
    assert response.status_code == 401
    assert response.json() == {"detail": "Bearer token missing or unknown"}


def test_check_dependancy(client, valid_auth_token):
    response = client.get(
        "/report/dependency",
        headers={"Authorization": valid_auth_token},
    )
    assert response.status_code == 200
    result = response.json()
    assert result == {
        "status": {
            "mongodb": "connected",
            "elasticsearch": "connected",
            "apm": "connected",
            "sentence_extractor": "started",
        }
    }

def test_check_dependancy_unauthorized(client):
    response = client.get("/report/dependency")
    assert response.status_code == 401
    assert response.json() == {"detail": "Bearer token missing or unknown"}