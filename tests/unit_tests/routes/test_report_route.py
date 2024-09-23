import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from fastapi import FastAPI

from routes.report_route import report_route, get_token

def mock_get_token():
    with patch("routes.report_route.get_token") as mock:
        mock.return_value = "mocked_token"
        yield mock

@pytest.fixture(scope="function")
def client():
    app = FastAPI()
    app.include_router(report_route)
    app.dependency_overrides[get_token] = mock_get_token
    return TestClient(app)


@patch("routes.report_route.ESIndex")
@patch("routes.report_route.ESFuncs.aggregate_sentence_total_by_days")
def test_extractor_report_success(mock_group_sentenece, mock_index, client):
    mock_index.EXTRACTED = "mocked_extracted_index"
    mock_group_sentenece.return_value = {"result": "mocked_response"}
    params = {
        "start_date": "2021-01-01T00:00:00",
        "end_date": "2021-01-31T23:59:59",
        "calendar_interval": "day",
    }
    response = client.get("/report/extractor", params=params)
    assert response.status_code == 200
    assert response.json() == {"result": "mocked_response"}
    mock_group_sentenece.assert_called_once_with(
        "mocked_extracted_index",
        {
            "start_date": "2021-01-01T00:00:00",
            "end_date": "2021-01-31T23:59:59",
            "type": "setting",
            "calendar_interval": "day",
        },
    )


@patch("routes.report_route.ESFuncs.check_apm_connection", return_value=True)
@patch("routes.report_route.ESFuncs.check_elasticsearch_connection", return_value=True)
@patch("routes.report_route.MGFuncs.check_mongo_connection", return_value=True)
@patch("routes.report_route.SentenceExtractor._instance", return_value=MagicMock())
def test_check_dependacy(mock_mg_connect, mock_es_connect, mock_apm_connect, mock_request, client):
    response = client.get("/report/dependency")
    assert response.status_code == 200
    assert response.json() == {
        "status": {
            "mongodb": "connected",
            "elasticsearch": "connected",
            "apm": "connected",
            "sentence_extractor": "started",
        }
    }