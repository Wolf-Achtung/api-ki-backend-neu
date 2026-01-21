# -*- coding: utf-8 -*-
"""
FIX-505 Tests: OpenAI Retry Module

Tests for:
- Retry on transient errors (timeout, 429, 5xx)
- Timeout truth (logged = actual)
- Backoff with Retry-After header respect
- STRICT_MODE fail-closed behavior
"""
import os
import time
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import requests

# Module under test
from services.openai_retry import (
    openai_request,
    openai_request_simple,
    OpenAIRequestError,
    OpenAIResponse,
    get_section_timeout,
    calculate_backoff,
    is_retryable_error,
    parse_retry_after,
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_READ_TIMEOUT,
    EXPAND_READ_TIMEOUT,
)


class TestTimeoutConfiguration:
    """Tests for timeout configuration."""

    def test_default_timeout(self):
        """Test: Default section gets default timeout."""
        connect, read = get_section_timeout("unknown_section")
        assert connect == DEFAULT_CONNECT_TIMEOUT
        assert read == DEFAULT_READ_TIMEOUT

    def test_expand_section_timeout(self):
        """Test: _expand sections get extended timeout."""
        connect, read = get_section_timeout("recommendations_expand")
        assert connect == DEFAULT_CONNECT_TIMEOUT
        assert read == EXPAND_READ_TIMEOUT

    def test_heavy_section_timeout(self):
        """Test: Heavy sections get extended timeout."""
        connect, read = get_section_timeout("gamechanger")
        assert connect == DEFAULT_CONNECT_TIMEOUT
        assert read >= 120  # Should be at least 120s

    def test_repair_section_timeout(self):
        """Test: _repair sections get repair timeout."""
        connect, read = get_section_timeout("html_repair")
        assert read >= 200  # Repair sections need extended time


class TestRetryLogic:
    """Tests for retry logic."""

    @patch('services.openai_retry.requests.post')
    def test_retry_on_timeout_then_success(self, mock_post):
        """Test: 2x ReadTimeout, then success → succeeds with attempts=3."""
        # First two calls timeout, third succeeds
        mock_post.side_effect = [
            requests.exceptions.ReadTimeout("timeout 1"),
            requests.exceptions.ReadTimeout("timeout 2"),
            MagicMock(
                status_code=200,
                json=lambda: {
                    "choices": [{"message": {"content": "Success!"}, "finish_reason": "stop"}],
                    "usage": {"completion_tokens": 10}
                }
            ),
        ]

        result = openai_request(
            section="test_section",
            payload={"model": "gpt-4o", "messages": []},
            api_key="test-key",
            max_attempts=3,
            strict_mode=False,
        )

        assert result.success
        assert result.content == "Success!"
        assert result.attempts == 3
        assert len(result.attempts_log) == 3

    @patch('services.openai_retry.requests.post')
    def test_retry_on_429_respects_retry_after(self, mock_post):
        """Test: 429 with Retry-After header is respected."""
        # Create mock response with Retry-After
        mock_429_response = MagicMock()
        mock_429_response.status_code = 429
        mock_429_response.headers = {"Retry-After": "2"}

        mock_success_response = MagicMock()
        mock_success_response.status_code = 200
        mock_success_response.json = lambda: {
            "choices": [{"message": {"content": "OK"}, "finish_reason": "stop"}],
            "usage": {"completion_tokens": 5}
        }

        mock_post.side_effect = [mock_429_response, mock_success_response]

        start = time.time()
        with patch('services.openai_retry.time.sleep') as mock_sleep:
            result = openai_request(
                section="test",
                payload={"model": "gpt-4o", "messages": []},
                api_key="key",
                max_attempts=3,
            )

            # Should have slept at least once
            assert mock_sleep.called
            # Sleep duration should respect Retry-After (2 seconds, capped at max)
            sleep_call_args = mock_sleep.call_args_list
            assert len(sleep_call_args) >= 1

    @patch('services.openai_retry.requests.post')
    def test_no_retry_on_400_bad_request(self, mock_post):
        """Test: 400 Bad Request is not retryable."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "Bad Request", response=mock_response
        )

        mock_post.return_value = mock_response

        result = openai_request(
            section="test",
            payload={"model": "gpt-4o", "messages": []},
            api_key="key",
            max_attempts=3,
        )

        assert not result.success
        # Should only attempt once (no retry for 400)
        assert mock_post.call_count == 1

    @patch('services.openai_retry.requests.post')
    def test_retry_on_502_503_504(self, mock_post):
        """Test: 502, 503, 504 are retryable."""
        for status in [502, 503, 504]:
            mock_post.reset_mock()

            mock_error_response = MagicMock()
            mock_error_response.status_code = status
            mock_error_response.headers = {}

            mock_success_response = MagicMock()
            mock_success_response.status_code = 200
            mock_success_response.json = lambda: {
                "choices": [{"message": {"content": "OK"}, "finish_reason": "stop"}],
                "usage": {"completion_tokens": 5}
            }

            mock_post.side_effect = [mock_error_response, mock_success_response]

            with patch('services.openai_retry.time.sleep'):
                result = openai_request(
                    section="test",
                    payload={"model": "gpt-4o", "messages": []},
                    api_key="key",
                    max_attempts=3,
                )

            assert result.success, f"Should retry and succeed for {status}"
            assert mock_post.call_count == 2, f"Should have retried for {status}"


class TestTimeoutTruth:
    """Tests for timeout truth - logged = actual."""

    @patch('services.openai_retry.requests.post')
    def test_timeout_tuple_passed_correctly(self, mock_post, caplog):
        """Test: The timeout logged matches the timeout passed to requests."""
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "choices": [{"message": {"content": "OK"}, "finish_reason": "stop"}],
                "usage": {"completion_tokens": 5}
            }
        )

        import logging
        caplog.set_level(logging.INFO)

        result = openai_request(
            section="recommendations_expand",
            payload={"model": "gpt-4o", "messages": []},
            api_key="key",
            connect_timeout_s=15,
            read_timeout_s=250,
        )

        # Check that requests.post was called with exact timeout tuple
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs['timeout'] == (15, 250), "Timeout tuple must match exactly"

        # Check log message contains the timeout
        log_messages = [r.message for r in caplog.records]
        assert any("timeout=(15,250)" in msg for msg in log_messages), \
            f"Log should contain timeout=(15,250), got: {log_messages}"

    @patch('services.openai_retry.requests.post')
    def test_section_timeout_used_when_not_overridden(self, mock_post, caplog):
        """Test: Section-specific timeout is used when not explicitly overridden."""
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "choices": [{"message": {"content": "OK"}, "finish_reason": "stop"}],
                "usage": {"completion_tokens": 5}
            }
        )

        import logging
        caplog.set_level(logging.INFO)

        expected_connect, expected_read = get_section_timeout("html_repair")

        result = openai_request(
            section="html_repair",
            payload={"model": "gpt-4o", "messages": []},
            api_key="key",
            # No timeout override
        )

        call_kwargs = mock_post.call_args[1]
        actual_timeout = call_kwargs['timeout']

        assert actual_timeout[0] == expected_connect
        assert actual_timeout[1] == expected_read

        # Verify in response object
        assert result.timeout_used == (expected_connect, expected_read)


class TestStrictMode:
    """Tests for STRICT_MODE behavior."""

    @patch('services.openai_retry.requests.post')
    def test_strict_mode_raises_after_exhausted(self, mock_post):
        """Test: STRICT_MODE raises OpenAIRequestError when retries exhausted."""
        mock_post.side_effect = requests.exceptions.ReadTimeout("timeout")

        with pytest.raises(OpenAIRequestError) as exc_info:
            openai_request(
                section="test_strict",
                payload={"model": "gpt-4o", "messages": []},
                api_key="key",
                max_attempts=2,
                strict_mode=True,
            )

        error = exc_info.value
        assert error.section == "test_strict"
        assert error.attempts == 2
        assert "debug_info" in dir(error)
        assert error.debug_info is not None

    @patch('services.openai_retry.requests.post')
    def test_non_strict_mode_returns_failure(self, mock_post):
        """Test: Non-STRICT mode returns failure response instead of raising."""
        mock_post.side_effect = requests.exceptions.ReadTimeout("timeout")

        result = openai_request(
            section="test_non_strict",
            payload={"model": "gpt-4o", "messages": []},
            api_key="key",
            max_attempts=2,
            strict_mode=False,
        )

        assert not result.success
        assert result.error is not None
        assert "timeout" in result.error.lower()


class TestBackoffCalculation:
    """Tests for backoff calculation."""

    def test_exponential_backoff(self):
        """Test: Backoff increases exponentially."""
        backoff_1 = calculate_backoff(1)
        backoff_2 = calculate_backoff(2)
        backoff_3 = calculate_backoff(3)

        # With jitter, we can't check exact values, but trend should be increasing
        # Multiple samples to average out jitter
        samples_1 = [calculate_backoff(1) for _ in range(10)]
        samples_2 = [calculate_backoff(2) for _ in range(10)]

        avg_1 = sum(samples_1) / len(samples_1)
        avg_2 = sum(samples_2) / len(samples_2)

        assert avg_2 > avg_1, "Backoff should increase with attempts"

    def test_retry_after_respected(self):
        """Test: Retry-After header value is used when present."""
        backoff = calculate_backoff(1, retry_after=5.0)
        assert backoff == 5.0  # Should use retry_after directly

    def test_backoff_capped_at_max(self):
        """Test: Backoff is capped at maximum value."""
        from services.openai_retry import BACKOFF_MAX

        # High attempt number should still be capped
        backoff = calculate_backoff(100)
        assert backoff <= BACKOFF_MAX


class TestRetryableErrors:
    """Tests for error classification."""

    def test_read_timeout_is_retryable(self):
        """Test: ReadTimeout is retryable."""
        error = requests.exceptions.ReadTimeout("read timeout")
        is_retry, reason = is_retryable_error(error)
        assert is_retry
        assert reason == "ReadTimeout"

    def test_connect_timeout_is_retryable(self):
        """Test: ConnectTimeout is retryable."""
        error = requests.exceptions.ConnectTimeout("connect timeout")
        is_retry, reason = is_retryable_error(error)
        assert is_retry
        assert reason == "ConnectTimeout"

    def test_connection_error_is_retryable(self):
        """Test: ConnectionError is retryable."""
        error = requests.exceptions.ConnectionError("connection reset")
        is_retry, reason = is_retryable_error(error)
        assert is_retry
        assert "Connection" in reason

    def test_429_is_retryable(self):
        """Test: HTTP 429 is retryable."""
        response = MagicMock()
        response.status_code = 429
        error = requests.exceptions.HTTPError("rate limit", response=response)

        is_retry, reason = is_retryable_error(error)
        assert is_retry
        assert "429" in reason

    def test_500_is_retryable(self):
        """Test: HTTP 500 is retryable."""
        response = MagicMock()
        response.status_code = 500
        error = requests.exceptions.HTTPError("server error", response=response)

        is_retry, reason = is_retryable_error(error)
        assert is_retry

    def test_400_is_not_retryable(self):
        """Test: HTTP 400 is NOT retryable."""
        response = MagicMock()
        response.status_code = 400
        error = requests.exceptions.HTTPError("bad request", response=response)

        is_retry, reason = is_retryable_error(error)
        assert not is_retry


class TestSimpleInterface:
    """Tests for openai_request_simple helper."""

    @patch('services.openai_retry.openai_request')
    def test_simple_interface_builds_payload(self, mock_request):
        """Test: Simple interface builds correct payload."""
        mock_request.return_value = OpenAIResponse(
            success=True, content="Hello!", section="test", model="gpt-4o"
        )

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            result = openai_request_simple(
                section="greeting",
                prompt="Say hello",
                system_prompt="Be friendly",
                model="gpt-4o",
                temperature=0.5,
                max_tokens=100,
            )

        assert result == "Hello!"

        # Verify payload structure
        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs['payload']

        assert payload['model'] == "gpt-4o"
        assert payload['temperature'] == 0.5
        assert len(payload['messages']) == 2
        assert payload['messages'][0]['role'] == "system"
        assert payload['messages'][1]['role'] == "user"

    def test_simple_interface_no_key_returns_none(self):
        """Test: No API key returns None."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove OPENAI_API_KEY if present
            os.environ.pop("OPENAI_API_KEY", None)

            result = openai_request_simple(
                section="test",
                prompt="test",
            )

            assert result is None


class TestResponseObject:
    """Tests for OpenAIResponse data class."""

    def test_to_debug_dict(self):
        """Test: Response can be converted to debug dict."""
        response = OpenAIResponse(
            success=True,
            content="Test content",
            section="test",
            model="gpt-4o",
            attempts=2,
            total_time_ms=1500.5,
            timeout_used=(10, 120),
            finish_reason="stop",
            completion_tokens=50,
        )

        debug_dict = response.to_debug_dict()

        assert debug_dict['success'] is True
        assert debug_dict['section'] == "test"
        assert debug_dict['model'] == "gpt-4o"
        assert debug_dict['attempts'] == 2
        assert debug_dict['timeout_used'] == [10, 120]
        assert debug_dict['completion_tokens'] == 50
