import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from fastapi import FastAPI

from routes.tokenizer_route import tokenizer_route, get_token

def mock_get_token():
    with patch("routes.tokenizer_route.get_token") as mock:
        mock.return_value = "mocked_token"
        yield mock

@pytest.fixture(scope="function")
def client():
    app = FastAPI()
    app.include_router(tokenizer_route)
    app.dependency_overrides[get_token] = mock_get_token
    return TestClient(app)

@patch("routes.tokenizer_route.SentenceExtractor")
def test_tokenizer_counter_success(sentence_extrator, client):
    sentence_extrator._instance = MagicMock()
    sentence_extrator().compute_token.return_value = 5
    response = client.post(
        "/tokenizer/counter",
        json={"sentences": ["This is a test sentence"]},
    )
    assert response.status_code == 200
    assert response.json() == {"success": True, "token_count": 5}