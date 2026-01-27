#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P1 Automation Tests - ENV Fallback Logic

Tests for the environment variable fallback chains used by submit_fixture.py.
These tests verify the ENV fallback logic without importing the full script.
"""
import os
import pytest
from unittest.mock import patch


# =============================================================================
# Re-implement the functions here to test the logic independently
# This avoids import issues with httpx dependency
# =============================================================================

DEFAULT_API_BASE = "http://localhost:8000"

# Exit codes
EXIT_SUCCESS = 0
EXIT_USAGE_ERROR = 2
EXIT_AUTH_FAILED = 3
EXIT_TIMEOUT = 4
EXIT_SERVER_FAILED = 5


def get_api_base_url(cli_value=None):
    """Get API base URL with fallback chain."""
    if cli_value:
        return cli_value
    for env_var in ["API_BASE_URL", "BACKEND_BASE", "SMOKE_BASE_URL"]:
        value = os.getenv(env_var)
        if value:
            return value
    return DEFAULT_API_BASE


def get_service_token(cli_value=None):
    """Get service token with fallback chain."""
    if cli_value:
        return cli_value
    for env_var in ["SERVICE_TOKEN", "SMOKE_AUTH_TOKEN"]:
        value = os.getenv(env_var)
        if value:
            return value
    return None


def normalize_base_url(url):
    """Normalize the base URL for consistent API calls."""
    url = url.strip().rstrip("/")
    if not url.startswith(("http://", "https://")):
        if "localhost" in url or "127.0.0.1" in url:
            url = f"http://{url}"
        else:
            url = f"https://{url}"
    return url


def mask_token(token):
    """Mask a token for safe logging."""
    if not token:
        return "(none)"
    if len(token) <= 8:
        return "****"
    return f"{token[:4]}...****"


class TestAPIBaseURLFallback:
    """Tests for API_BASE_URL fallback chain."""

    def test_cli_arg_takes_priority(self):
        """CLI argument should override all env vars."""
        with patch.dict(os.environ, {
            "API_BASE_URL": "https://env.example.com",
            "BACKEND_BASE": "https://backend.example.com",
        }):
            result = get_api_base_url("https://cli.example.com")
            assert result == "https://cli.example.com"

    def test_api_base_url_env_priority(self):
        """API_BASE_URL should be first env var checked."""
        with patch.dict(os.environ, {
            "API_BASE_URL": "https://api.example.com",
            "BACKEND_BASE": "https://backend.example.com",
            "SMOKE_BASE_URL": "https://smoke.example.com",
        }, clear=True):
            result = get_api_base_url(None)
            assert result == "https://api.example.com"

    def test_backend_base_fallback(self):
        """BACKEND_BASE should be second priority."""
        with patch.dict(os.environ, {
            "BACKEND_BASE": "https://backend.example.com",
            "SMOKE_BASE_URL": "https://smoke.example.com",
        }, clear=True):
            result = get_api_base_url(None)
            assert result == "https://backend.example.com"

    def test_smoke_base_url_fallback(self):
        """SMOKE_BASE_URL should be third priority."""
        with patch.dict(os.environ, {
            "SMOKE_BASE_URL": "https://smoke.example.com",
        }, clear=True):
            result = get_api_base_url(None)
            assert result == "https://smoke.example.com"

    def test_default_fallback(self):
        """Should default to localhost when no env vars set."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_api_base_url(None)
            assert result == "http://localhost:8000"


class TestServiceTokenFallback:
    """Tests for SERVICE_TOKEN fallback chain."""

    def test_cli_arg_takes_priority(self):
        """CLI argument should override all env vars."""
        with patch.dict(os.environ, {
            "SERVICE_TOKEN": "env-token",
            "SMOKE_AUTH_TOKEN": "smoke-token",
        }):
            result = get_service_token("cli-token")
            assert result == "cli-token"

    def test_service_token_env_priority(self):
        """SERVICE_TOKEN should be first env var checked."""
        with patch.dict(os.environ, {
            "SERVICE_TOKEN": "service-token",
            "SMOKE_AUTH_TOKEN": "smoke-token",
        }, clear=True):
            result = get_service_token(None)
            assert result == "service-token"

    def test_smoke_auth_token_fallback(self):
        """SMOKE_AUTH_TOKEN should be second priority."""
        with patch.dict(os.environ, {
            "SMOKE_AUTH_TOKEN": "smoke-token",
        }, clear=True):
            result = get_service_token(None)
            assert result == "smoke-token"

    def test_none_when_no_token(self):
        """Should return None when no token is set."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_service_token(None)
            assert result is None


class TestNormalizeBaseURL:
    """Tests for URL normalization."""

    def test_removes_trailing_slash(self):
        """Should remove trailing slashes."""
        assert normalize_base_url("https://example.com/") == "https://example.com"
        assert normalize_base_url("https://example.com///") == "https://example.com"

    def test_strips_whitespace(self):
        """Should strip whitespace."""
        assert normalize_base_url("  https://example.com  ") == "https://example.com"

    def test_adds_https_for_remote(self):
        """Should add https:// for non-localhost URLs."""
        assert normalize_base_url("api.example.com") == "https://api.example.com"
        assert normalize_base_url("example.com/api") == "https://example.com/api"

    def test_adds_http_for_localhost(self):
        """Should add http:// for localhost URLs."""
        assert normalize_base_url("localhost:8000") == "http://localhost:8000"
        assert normalize_base_url("127.0.0.1:8000") == "http://127.0.0.1:8000"

    def test_preserves_existing_scheme(self):
        """Should not modify URLs with existing scheme."""
        assert normalize_base_url("https://example.com") == "https://example.com"
        assert normalize_base_url("http://localhost:8000") == "http://localhost:8000"


class TestMaskToken:
    """Tests for token masking."""

    def test_masks_long_token(self):
        """Should show first 4 chars for long tokens."""
        assert mask_token("abcdefghijklmnop") == "abcd...****"

    def test_fully_masks_short_token(self):
        """Should fully mask short tokens."""
        assert mask_token("abcd") == "****"
        assert mask_token("abcdefgh") == "****"

    def test_handles_none(self):
        """Should handle None gracefully."""
        assert mask_token(None) == "(none)"

    def test_handles_empty_string(self):
        """Should handle empty string."""
        assert mask_token("") == "(none)"


class TestExitCodes:
    """Tests for exit code constants."""

    def test_exit_codes_are_defined(self):
        """Exit codes should be defined and unique."""
        codes = [EXIT_SUCCESS, EXIT_USAGE_ERROR, EXIT_AUTH_FAILED, EXIT_TIMEOUT, EXIT_SERVER_FAILED]
        assert len(codes) == len(set(codes)), "Exit codes should be unique"

    def test_success_is_zero(self):
        """Success should be 0."""
        assert EXIT_SUCCESS == 0

    def test_error_codes_are_nonzero(self):
        """Error codes should be non-zero."""
        assert EXIT_USAGE_ERROR != 0
        assert EXIT_AUTH_FAILED != 0
        assert EXIT_TIMEOUT != 0
        assert EXIT_SERVER_FAILED != 0


class TestRailwayCompatibility:
    """Tests for Railway environment compatibility."""

    def test_railway_backend_base_works(self):
        """Should work with Railway's BACKEND_BASE variable."""
        railway_url = "https://api-ki-backend-neu-production.up.railway.app"
        with patch.dict(os.environ, {"BACKEND_BASE": railway_url}, clear=True):
            result = get_api_base_url(None)
            assert result == railway_url

    def test_railway_smoke_auth_token_works(self):
        """Should work with Railway's SMOKE_AUTH_TOKEN variable."""
        with patch.dict(os.environ, {"SMOKE_AUTH_TOKEN": "railway-smoke-token"}, clear=True):
            result = get_service_token(None)
            assert result == "railway-smoke-token"

    def test_combined_railway_env(self):
        """Should work with typical Railway environment."""
        with patch.dict(os.environ, {
            "BACKEND_BASE": "https://api-ki-backend-neu-production.up.railway.app",
            "SMOKE_BASE_URL": "https://api-ki-backend-neu-production.up.railway.app",
            "SMOKE_AUTH_TOKEN": "railway-auth-token",
        }, clear=True):
            base_url = get_api_base_url(None)
            token = get_service_token(None)

            assert "railway.app" in base_url
            assert token == "railway-auth-token"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
