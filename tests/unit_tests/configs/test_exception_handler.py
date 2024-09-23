import pytest
from fastapi import Request
from unittest.mock import MagicMock, patch
from configs.exception_handler import log_and_capture_exception, custom_exception_handler


class TestExceptionHandling:
    def test_log_and_capture_exception(self, mock_apm_capture_exp, mock_logger_error):
        exc = Exception("This is a test exception")
        log_and_capture_exception(exc)

        mock_logger_error.assert_any_call(f"Error Type: {type(exc)}")
        mock_apm_capture_exp.assert_called_once()

    @pytest.mark.asyncio
    @patch('traceback.extract_tb')
    @patch('traceback.format_exception')
    async def test_custom_exception_handler(self, mock_format_exception, mock_extract_tb, mock_apm_capture_exp, mock_logger_error):
        request = MagicMock(spec=Request)
        exc = Exception("This is a test exception")
        mock_extract_tb.return_value = [
            MagicMock(filename='test_file.py', lineno=10),
            MagicMock(filename='test_file.py', lineno=20)
        ]
        mock_format_exception.return_value = ["Traceback (most recent call last):", "    ..."]

        response = await custom_exception_handler(request, exc)
        mock_logger_error.assert_any_call(f"Error Type: {type(exc)}, File: test_file.py, Line: 20")
        
        assert response.status_code == 500
        assert response.body.decode() == '{"detail":"Internal Server Error"}'
        
        mock_apm_capture_exp.assert_called_once()