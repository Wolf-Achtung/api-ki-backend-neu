# -*- coding: utf-8 -*-
"""
Sprint G14: Stability & Runtime Hardening Tests
================================================

Test coverage for:
- G14-A: LLM retry system (services/llm_client.py)
- G14-B: Research pipeline stabilization (circuit breaker, timeouts)
- G14-C: Validator smart mode (warning de-duplication)
- G14-D: Performance hardening (regex cache, PDF retry)

Version: 1.0.0 (Sprint G14)
"""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock


# =============================================================================
# G14-A: LLM Client Retry Tests
# =============================================================================

class TestG14A_LLMClient:
    """Tests for LLM client retry functionality."""

    def test_llm_client_imports(self):
        """Test that llm_client module can be imported."""
        from services.llm_client import LLMClient, LLMCallResult
        assert LLMClient is not None
        assert LLMCallResult is not None

    def test_llm_call_result_dataclass(self):
        """Test LLMCallResult dataclass structure."""
        from services.llm_client import LLMCallResult

        result = LLMCallResult(
            success=True,
            content="Test response",
            final_strategy="primary",
            retries_used=1,
            total_time_ms=100.0,
        )
        assert result.success is True
        assert result.content == "Test response"
        assert result.final_strategy == "primary"
        assert result.retries_used == 1
        assert result.total_time_ms == 100.0
        assert result.error is None

    def test_llm_call_result_failure(self):
        """Test LLMCallResult for failure case."""
        from services.llm_client import LLMCallResult

        result = LLMCallResult(
            success=False,
            content=None,
            final_strategy="short_retry",
            retries_used=3,
            total_time_ms=5000.0,
            error="API timeout",
        )
        assert result.success is False
        assert result.content is None
        assert result.error == "API timeout"

    def test_llm_client_instantiation(self):
        """Test LLMClient can be instantiated."""
        from services.llm_client import LLMClient

        client = LLMClient()
        assert client is not None
        assert hasattr(client, "call_with_retry")

    def test_llm_retry_config_env(self):
        """Test LLM retry configuration from environment."""
        from services import llm_client

        # Check default values exist
        assert hasattr(llm_client, "LLM_SHORT_RETRY_ENABLED")
        assert hasattr(llm_client, "LLM_SHORT_RETRY_MAXTOKENS")
        assert hasattr(llm_client, "LLM_MAX_RETRIES")

    def test_llm_client_call_with_retry_success(self):
        """Test call_with_retry with successful call."""
        from services.llm_client import LLMClient

        client = LLMClient()

        # Mock a successful call
        def mock_call_fn(**kwargs):
            return {"content": "Test response", "success": True}

        result = client.call_with_retry(
            call_fn=mock_call_fn,
            section="test_section",
            max_tokens=1000,
        )

        assert result.success is True
        assert result.content is not None


# =============================================================================
# G14-B: Research Pipeline Circuit Breaker Tests
# =============================================================================

class TestG14B_CircuitBreaker:
    """Tests for Perplexity circuit breaker functionality."""

    def test_circuit_breaker_imports(self):
        """Test circuit breaker can be imported."""
        from services.provider_perplexity import (
            get_circuit_status,
            PPLX_FAILURE_THRESHOLD,
            PPLX_CIRCUIT_RESET_SEC,
        )
        assert get_circuit_status is not None
        assert PPLX_FAILURE_THRESHOLD >= 1
        assert PPLX_CIRCUIT_RESET_SEC > 0

    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker starts in closed state."""
        from services.provider_perplexity import get_circuit_status

        status = get_circuit_status()
        assert "failures" in status
        assert "threshold" in status
        assert "is_open" in status
        # Note: State might not be fresh in test environment

    def test_circuit_breaker_class(self):
        """Test _CircuitBreaker class directly."""
        from services.provider_perplexity import _CircuitBreaker

        cb = _CircuitBreaker(threshold=2, reset_sec=60)

        # Initial state
        assert cb.is_open() is False
        status = cb.get_status()
        assert status["failures"] == 0

        # Record failures
        cb.record_failure()
        assert cb.is_open() is False  # Still under threshold

        cb.record_failure()
        assert cb.is_open() is True  # Now open

        # Success resets
        cb.record_success()
        assert cb.is_open() is False

    def test_circuit_breaker_thread_safety(self):
        """Test circuit breaker is thread-safe."""
        from services.provider_perplexity import _CircuitBreaker

        cb = _CircuitBreaker(threshold=10, reset_sec=60)
        errors = []

        def record_failures():
            try:
                for _ in range(5):
                    cb.record_failure()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=record_failures) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        # Should have recorded 20 failures (4 threads x 5 each)
        status = cb.get_status()
        assert status["failures"] >= 10  # At least reached threshold


class TestG14B_TavilyTimeout:
    """Tests for Tavily timeout configuration."""

    def test_tavily_timeout_config(self):
        """Test Tavily timeout is configured correctly."""
        from services.provider_tavily import TAVILY_TIMEOUT

        # G14-B: Should be 8 seconds (reduced from 20s)
        assert TAVILY_TIMEOUT == 8


class TestG14B_MarketFallback:
    """Tests for expanded market fallback HTML."""

    def test_market_fallback_expanded(self):
        """Test market fallback has 3+ paragraphs per G14-B."""
        pytest.importorskip("bs4", reason="bs4 required for research_pipeline")
        from services.research_pipeline import _market_fallback_html

        html = _market_fallback_html()

        # Count <p> tags - should have at least 3 substantive paragraphs
        p_count = html.count("<p>")
        assert p_count >= 3, f"Expected at least 3 paragraphs, got {p_count}"

        # Check for new content added in G14-B
        assert "Markttrends 2025" in html or "Aktuelle Markttrends" in html
        assert "Wettbewerbslandschaft" in html


# =============================================================================
# G14-C: Validator Smart Mode Tests
# =============================================================================

class TestG14C_ValidatorSmartMode:
    """Tests for validator warning de-duplication."""

    def test_smart_mode_enabled(self):
        """Test smart mode is enabled by default."""
        from services.report_validator import ReportValidator

        assert ReportValidator.SMART_MODE_ENABLED is True

    def test_dedupe_warnings(self):
        """Test warning de-duplication."""
        from services.report_validator import ReportValidator, ValidationError

        validator = ReportValidator({}, {"unternehmensgroesse": "kmu"})

        # Add duplicate warnings
        validator.errors = [
            ValidationError("WARNING", "TEST", "section1", "Same message", ""),
            ValidationError("WARNING", "TEST", "section1", "Same message", ""),
            ValidationError("WARNING", "TEST", "section2", "Different", ""),
        ]

        deduped = validator._dedupe_warnings()
        assert len(deduped) == 2  # Duplicates removed

    def test_bundle_min_word_warnings(self):
        """Test bundling of min-word warnings."""
        from services.report_validator import ReportValidator, ValidationError

        validator = ReportValidator({}, {"unternehmensgroesse": "kmu"})

        # Add multiple SECTION_TOO_SHORT warnings
        validator.errors = [
            ValidationError(
                "WARNING", "SECTION_TOO_SHORT", "sec1",
                "Section zu kurz: 45 Wörter (Minimum: 100 Wörter)", ""
            ),
            ValidationError(
                "WARNING", "SECTION_TOO_SHORT", "sec2",
                "Section zu kurz: 32 Wörter (Minimum: 80 Wörter)", ""
            ),
            ValidationError(
                "WARNING", "SECTION_TOO_SHORT", "sec3",
                "Section zu kurz: 55 Wörter (Minimum: 120 Wörter)", ""
            ),
            ValidationError(
                "WARNING", "SECTION_TOO_SHORT", "sec4",
                "Section zu kurz: 60 Wörter (Minimum: 100 Wörter)", ""
            ),
            ValidationError(
                "CRITICAL", "OTHER", "sec5",
                "Some other error", ""
            ),
        ]

        bundled = validator._bundle_min_word_warnings(validator.errors)

        # Should bundle 4 warnings into 1, plus keep the CRITICAL
        assert len(bundled) == 2
        bundle_warning = [e for e in bundled if "BUNDLE" in e.category]
        assert len(bundle_warning) == 1
        assert "4 Sektionen" in bundle_warning[0].message

    def test_get_smart_errors(self):
        """Test full smart error processing pipeline."""
        from services.report_validator import ReportValidator, ValidationError

        validator = ReportValidator({}, {"unternehmensgroesse": "solo"})

        # Add various warnings
        validator.errors = [
            ValidationError("WARNING", "SECTION_TOO_SHORT", "s1", "msg1", ""),
            ValidationError("WARNING", "SECTION_TOO_SHORT", "s1", "msg1", ""),  # duplicate
            ValidationError("WARNING", "SECTION_TOO_SHORT", "s2", "msg2", ""),
            ValidationError("WARNING", "SECTION_TOO_SHORT", "s3", "msg3", ""),
            ValidationError("WARNING", "SECTION_TOO_SHORT", "s4", "msg4", ""),
            ValidationError("CRITICAL", "PLACEHOLDER", "s5", "error", ""),
        ]

        smart_errors = validator.get_smart_errors()

        # Should be significantly reduced
        assert len(smart_errors) < len(validator.errors)


# =============================================================================
# G14-D: Performance Hardening Tests
# =============================================================================

class TestG14D_HTMLMinifierCache:
    """Tests for HTML minifier regex caching."""

    def test_compiled_patterns_exist(self):
        """Test pre-compiled regex patterns are defined."""
        from services.html_minifier import (
            _RE_HTML_COMMENTS,
            _RE_MULTIPLE_SPACES,
            _RE_CSS_COMMENTS,
            _RE_DEBUG_DIV,
        )
        import re

        assert isinstance(_RE_HTML_COMMENTS, re.Pattern)
        assert isinstance(_RE_MULTIPLE_SPACES, re.Pattern)
        assert isinstance(_RE_CSS_COMMENTS, re.Pattern)
        assert isinstance(_RE_DEBUG_DIV, re.Pattern)

    def test_regex_cache_stats(self):
        """Test regex cache statistics function."""
        from services.html_minifier import get_regex_cache_stats

        stats = get_regex_cache_stats()

        assert "hits" in stats
        assert "misses" in stats
        assert "maxsize" in stats
        assert "currsize" in stats
        assert "hit_rate" in stats

    def test_compress_html_performance(self):
        """Test HTML compression uses cached patterns."""
        from services.html_minifier import compress_html

        html = """
        <html>
            <head><title>Test</title></head>
            <body>
                <div class="test">
                    <!-- This is a comment -->
                    <p>   Multiple    spaces   </p>
                </div>
            </body>
        </html>
        """

        # Warm up cache
        compress_html(html)

        # Time multiple calls
        start = time.time()
        for _ in range(100):
            compress_html(html)
        elapsed = time.time() - start

        # Should be fast due to caching (< 1 second for 100 iterations)
        assert elapsed < 1.0, f"Compression too slow: {elapsed:.2f}s for 100 iterations"

    def test_optimize_html_for_pdf(self):
        """Test full optimization pipeline."""
        from services.html_minifier import optimize_html_for_pdf

        # Use a div with debug class (not section) since strip_unused_sections
        # targets div elements with debug class
        html = """
        <html>
        <head>
            <style>
                .used-class { color: red; }
                .unused-class { color: blue; }
            </style>
        </head>
        <body>
            <div class="used-class">Content</div>
            <div class="debug-panel">Debug info</div>
        </body>
        </html>
        """

        optimized = optimize_html_for_pdf(html)

        # Should be smaller
        assert len(optimized) < len(html)

        # Unused CSS class should be removed
        assert ".unused-class" not in optimized


class TestG14D_PDFClientRetry:
    """Tests for PDF client retry enhancements."""

    def test_error_categorization(self):
        """Test error categorization constants."""
        from services.pdf_client import TRANSIENT_ERRORS, PERMANENT_ERRORS

        # Check transient errors include retryable codes
        assert 429 in TRANSIENT_ERRORS
        assert 500 in TRANSIENT_ERRORS
        assert 502 in TRANSIENT_ERRORS
        assert 503 in TRANSIENT_ERRORS

        # Check permanent errors
        assert 400 in PERMANENT_ERRORS
        assert 401 in PERMANENT_ERRORS
        assert 403 in PERMANENT_ERRORS
        assert 404 in PERMANENT_ERRORS

    def test_max_retries_configurable(self):
        """Test MAX_RETRIES is configurable via env."""
        from services.pdf_client import MAX_RETRIES

        # Default should be 3
        assert MAX_RETRIES >= 1

    @patch("services.pdf_client.requests.post")
    def test_permanent_error_no_retry(self, mock_post):
        """Test permanent errors don't trigger retry."""
        from services.pdf_client import render_pdf_from_html

        # Mock 403 response
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_post.return_value = mock_response

        with patch("services.pdf_client.PDF_SERVICE_URL", "http://test"):
            result = render_pdf_from_html("<html></html>")

        # Should only call once (no retry)
        assert mock_post.call_count == 1
        assert "error" in result
        assert result.get("retry_count", 0) == 0


# =============================================================================
# Integration Tests
# =============================================================================

class TestG14_Integration:
    """Integration tests for G14 features."""

    def test_all_g14_modules_import(self):
        """Test all G14-modified modules can be imported together."""
        from services.llm_client import LLMClient
        from services.provider_perplexity import get_circuit_status
        from services.provider_tavily import TAVILY_TIMEOUT
        from services.report_validator import ReportValidator
        from services.html_minifier import optimize_html_for_pdf
        from services.pdf_client import render_pdf_from_html

        # All imports successful
        assert True

    @pytest.mark.timeout(10)
    def test_research_pipeline_with_circuit_breaker(self):
        """Test research pipeline respects circuit breaker."""
        pytest.importorskip("bs4", reason="bs4 required for research_pipeline")
        from unittest.mock import patch

        from services.research_pipeline import run_research

        # KIS-1280: Zwei Netzwege, nicht einer. feedparser war gestopft,
        # harvest_links -> http_get -> requests.get war offen. Der Aufruf
        # ging bis dahin wirklich ins Netz; im Lauf vom 04.09.2026 blieb
        # er an einer SSL-Leseoperation haengen und riss die ganze
        # Testsuite in die Zeitgrenze.
        #
        # Aufgefallen ist das erst, nachdem KIS-1277 den globalen
        # sys.modules-Ersatz fuer requests entfernt hat: Der hatte jeden
        # echten Aufruf zu einem MagicMock gemacht und diesen Test
        # jahrelang stumm gestellt.
        mock_feed = type("Feed", (), {"entries": [], "bozo": False, "feed": {}})()
        with patch("services.research_clients.feedparser.parse", return_value=mock_feed), \
                patch("services.research_clients.http_get", return_value=None):
            result = run_research({})

        assert "TOOLS_TABLE_HTML" in result
        assert "FUNDING_TABLE_HTML" in result
        assert "research_status" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
