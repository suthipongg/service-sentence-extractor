import pytest
from unittest.mock import patch

from fastapi import Depends
from fastapi.testclient import TestClient

from configs.security import get_token

MOCK_API_TOKEN = "test_token"

@pytest.fixture(scope="function")
def client():
    from fastapi import FastAPI
    app = FastAPI()

    @app.get("/test")
    async def test_route(token: str = Depends(get_token)):
        return {"token": token}

    return TestClient(app)

def test_get_token_valid_token(client):
    with patch("configs.environment.ENV.API_TOKEN", MOCK_API_TOKEN):
        response = client.get("/test", headers={"Authorization": f"Bearer {MOCK_API_TOKEN}"})
        assert response.status_code == 200
        assert response.json() == {"token": MOCK_API_TOKEN}

def test_get_token_missing_token(client):
    with patch("configs.environment.ENV.API_TOKEN", MOCK_API_TOKEN):
        response = client.get("/test")
        assert response.status_code == 401
        assert response.json() == {"detail": "Bearer token missing or unknown"}

def test_get_token_invalid_token(client):
    with patch("configs.environment.ENV.API_TOKEN", MOCK_API_TOKEN):
        response = client.get("/test", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == 401
        assert response.json() == {"detail": "Bearer token missing or unknown"}