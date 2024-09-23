import pytest
from unittest.mock import patch, MagicMock

from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.testclient import TestClient

import http

from configs.middleware import log_all_request_middleware

app = FastAPI()

@app.middleware("http")
async def custom_middleware(request: Request, call_next):
    return await log_all_request_middleware(request, call_next)

@app.get("/test/ok")
async def route_ok():
    return {"message": "test"}

@app.get("/test/error")
async def route_error():
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

@pytest.fixture(scope='function')
def app_client():
    return TestClient(app)

@pytest.mark.asyncio
async def test_log_request_middleware(mock_logger_info, app_client):
    with patch('time.time', return_value=0):
        response = app_client.get("/test/ok")
    log_message = mock_logger_info.call_args[0][0]

    assert response.status_code == 200
    assert "GET /test" in log_message
    assert "200" in log_message
    assert "0.00ms" in log_message
    assert "test" in log_message

    mock_logger_info.assert_called()

@pytest.mark.asyncio
async def test_logging_status_color(mock_logger_info, app_client):
    app_client.get("/test/error")
    log_message = mock_logger_info.call_args[0][0]
    assert '[91m' in log_message
    
    with patch('http.HTTPStatus', return_value=http.HTTPStatus.OK):
        app_client.get("/test/ok")
    
    log_message = mock_logger_info.call_args[0][0]
    assert '[92m' in log_message

@pytest.mark.asyncio
@patch('configs.middleware.http.HTTPStatus')
async def test_log_request_middleware_error_status(mock_http_status, mock_logger_info):
    mock_request = MagicMock(spec=Request)
    mock_request.method = 'GET'
    mock_request.url.path = '/ping'
    mock_request.query_params = ''
    
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 500
    
    async def mock_call_next(request):
        return mock_response
    
    mock_http_status.side_effect = ValueError
    response = await log_all_request_middleware(mock_request, mock_call_next)
    mock_logger_info.assert_any_call("Unknown status code: 500")
    logged_message = mock_logger_info.call_args[0][0]
    
    assert response == mock_response
    assert 'GET /ping' in logged_message
    assert '500' in logged_message
    assert 'Unknown status code' in logged_message