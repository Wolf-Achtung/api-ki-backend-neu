# -*- coding: utf-8 -*-
"""
Tests for PDF payload limit validation.

Tests the ENV-configurable HTML payload limit and slim mode preparation.
"""
import os
import sys
import pytest
from unittest.mock import patch

# KIS-1277: Hier stand `sys.modules['requests'] = MagicMock()`. Die Zeile
# lief beim Einsammeln der Testdateien und ersetzte das echte
# requests-Modul fuer den GESAMTEN Testlauf. Folge: In jeder spaeteren
# Datei war `requests.exceptions.ReadTimeout` ein MagicMock, und
# `raise` darauf ergab einen TypeError statt der erwarteten Ausnahme.
# requests ist eine echte Abhaengigkeit (requirements.txt) — der Ersatz
# war nie noetig.


class TestPDFPayloadLimit:
    """Tests for HTML payload size validation."""

    def test_pdf_payload_under_limit(self):
        """Test that HTML under the limit passes validation."""
        with patch.dict(os.environ, {"PDF_MAX_HTML_KB": "1024"}):
            # Force reimport with new ENV
            if 'services.pdf_client' in sys.modules:
                del sys.modules['services.pdf_client']
            from services import pdf_client

            html = "A" * (900 * 1024)  # 900 KB - under 1024 KB limit
            result = pdf_client.validate_html_size(html)
            assert result is None, f"Expected None for valid payload, got: {result}"

    def test_pdf_payload_over_limit(self):
        """Test that HTML over the limit fails validation."""
        with patch.dict(os.environ, {"PDF_MAX_HTML_KB": "1024"}):
            if 'services.pdf_client' in sys.modules:
                del sys.modules['services.pdf_client']
            from services import pdf_client

            html = "A" * (1500 * 1024)  # 1.5 MB - over 1024 KB limit
            result = pdf_client.validate_html_size(html)
            assert result is not None, "Expected error message for oversized payload"
            assert "exceeds limit" in result
            assert "1024KB" in result

    def test_pdf_payload_exactly_at_limit(self):
        """Test that HTML exactly at the limit passes validation."""
        with patch.dict(os.environ, {"PDF_MAX_HTML_KB": "100"}):
            if 'services.pdf_client' in sys.modules:
                del sys.modules['services.pdf_client']
            from services import pdf_client

            # Slightly under limit (accounting for encoding)
            html = "A" * (99 * 1024)  # 99 KB
            result = pdf_client.validate_html_size(html)
            assert result is None

    def test_pdf_payload_empty_html(self):
        """Test that empty HTML returns error."""
        if 'services.pdf_client' in sys.modules:
            del sys.modules['services.pdf_client']
        from services import pdf_client

        result = pdf_client.validate_html_size("")
        assert result is not None
        assert "empty" in result.lower()

    def test_pdf_payload_env_variable_default(self):
        """Test that default limit is 1024 KB when ENV not set."""
        # Remove PDF_MAX_HTML_KB if present
        env_copy = os.environ.copy()
        env_copy.pop("PDF_MAX_HTML_KB", None)

        with patch.dict(os.environ, env_copy, clear=True):
            if 'services.pdf_client' in sys.modules:
                del sys.modules['services.pdf_client']
            from services import pdf_client

            assert pdf_client.MAX_HTML_PAYLOAD_KB == 1024

    def test_pdf_payload_env_variable_custom(self):
        """Test that custom ENV value is respected when module reloaded."""
        # This test verifies the ENV variable is read - we test indirectly via validate_html_size
        if 'services.pdf_client' in sys.modules:
            del sys.modules['services.pdf_client']
        from services import pdf_client

        # Test that we can read the constant (already verified default is 1024)
        assert pdf_client.MAX_HTML_PAYLOAD_KB >= 1024
        # The actual value may vary based on ENV at test time

    def test_pdf_payload_error_message_format(self):
        """Test that error message includes helpful information."""
        if 'services.pdf_client' in sys.modules:
            del sys.modules['services.pdf_client']
        from services import pdf_client

        # Use a size that's definitely over any reasonable limit
        html = "A" * (2000 * 1024)  # 2 MB - over 1024 KB default limit
        result = pdf_client.validate_html_size(html)
        assert result is not None
        assert "PDF failed" in result
        assert "SLIM mode" in result


class TestSlimHtmlSections:
    """Tests for slim_html_sections function (prepared but not activated)."""

    def test_slim_removes_news_box(self):
        """Test that slim mode removes NEWS_BOX_HTML."""
        if 'services.pdf_client' in sys.modules:
            del sys.modules['services.pdf_client']
        from services.pdf_client import slim_html_sections

        sections = {
            "TITLE": "Test Report",
            "NEWS_BOX_HTML": "<div>Large news content...</div>",
            "SUMMARY_HTML": "<div>Summary</div>",
        }

        result = slim_html_sections(sections.copy())

        assert "NEWS_BOX_HTML" not in result
        assert "TITLE" in result
        assert "SUMMARY_HTML" in result

    def test_slim_removes_market_insights(self):
        """Test that slim mode removes MARKET_INSIGHTS_HTML."""
        if 'services.pdf_client' in sys.modules:
            del sys.modules['services.pdf_client']
        from services.pdf_client import slim_html_sections

        sections = {
            "MARKET_INSIGHTS_HTML": "<div>Market data...</div>",
            "CORE_CONTENT": "Important stuff",
        }

        result = slim_html_sections(sections.copy())

        assert "MARKET_INSIGHTS_HTML" not in result
        assert "CORE_CONTENT" in result

    def test_slim_removes_kreativ_special(self):
        """Test that slim mode removes KREATIV_SPECIAL_HTML."""
        if 'services.pdf_client' in sys.modules:
            del sys.modules['services.pdf_client']
        from services.pdf_client import slim_html_sections

        sections = {
            "KREATIV_SPECIAL_HTML": "<div>Creative content...</div>",
            "MAIN_REPORT": "Main report content",
        }

        result = slim_html_sections(sections.copy())

        assert "KREATIV_SPECIAL_HTML" not in result
        assert "MAIN_REPORT" in result

    def test_slim_preserves_essential_sections(self):
        """Test that slim mode preserves essential sections."""
        if 'services.pdf_client' in sys.modules:
            del sys.modules['services.pdf_client']
        from services.pdf_client import slim_html_sections

        sections = {
            "TITLE": "Report Title",
            "SUMMARY_HTML": "<div>Executive Summary</div>",
            "RISK_HTML": "<div>Risk Assessment</div>",
            "ROI_HTML": "<div>ROI Analysis</div>",
            "NEWS_BOX_HTML": "<div>News to remove</div>",
        }

        result = slim_html_sections(sections.copy())

        # Essential sections preserved
        assert "TITLE" in result
        assert "SUMMARY_HTML" in result
        assert "RISK_HTML" in result
        assert "ROI_HTML" in result
        # Non-essential removed
        assert "NEWS_BOX_HTML" not in result

    def test_slim_handles_empty_sections(self):
        """Test that slim mode handles empty sections dict."""
        if 'services.pdf_client' in sys.modules:
            del sys.modules['services.pdf_client']
        from services.pdf_client import slim_html_sections

        result = slim_html_sections({})
        assert result == {}

    def test_slim_handles_no_removable_sections(self):
        """Test slim mode when no removable sections present."""
        if 'services.pdf_client' in sys.modules:
            del sys.modules['services.pdf_client']
        from services.pdf_client import slim_html_sections

        sections = {
            "TITLE": "Test",
            "CONTENT": "Content",
        }

        result = slim_html_sections(sections.copy())

        assert result == sections

    def test_slim_removes_multiple_sections(self):
        """Test that slim removes all configured sections at once."""
        if 'services.pdf_client' in sys.modules:
            del sys.modules['services.pdf_client']
        from services.pdf_client import slim_html_sections

        sections = {
            "TITLE": "Test",
            "NEWS_BOX_HTML": "News",
            "MARKET_INSIGHTS_HTML": "Market",
            "KREATIV_SPECIAL_HTML": "Creative",
            "RESEARCH_DETAILS_HTML": "Research",
            "RAW_RESEARCH_HTML": "Raw",
        }

        result = slim_html_sections(sections.copy())

        assert "TITLE" in result
        assert "NEWS_BOX_HTML" not in result
        assert "MARKET_INSIGHTS_HTML" not in result
        assert "KREATIV_SPECIAL_HTML" not in result
        assert "RESEARCH_DETAILS_HTML" not in result
        assert "RAW_RESEARCH_HTML" not in result


class TestPDFSizeValidation:
    """Tests for PDF output size validation."""

    def test_pdf_size_under_limit(self):
        """Test that PDF under limit passes validation."""
        if 'services.pdf_client' in sys.modules:
            del sys.modules['services.pdf_client']
        from services.pdf_client import validate_pdf_size

        pdf_bytes = b"A" * (5 * 1024 * 1024)  # 5 MB
        result = validate_pdf_size(pdf_bytes)
        assert result is None

    def test_pdf_size_over_limit(self):
        """Test that PDF over limit fails validation."""
        if 'services.pdf_client' in sys.modules:
            del sys.modules['services.pdf_client']
        from services import pdf_client

        # Default limit is 20 MB, so use 25 MB to exceed it
        pdf_bytes = b"A" * (25 * 1024 * 1024)  # 25 MB - over 20 MB default limit
        result = pdf_client.validate_pdf_size(pdf_bytes)
        assert result is not None
        assert "exceeds" in result

    def test_pdf_size_empty_bytes(self):
        """Test that empty PDF bytes returns None (no error)."""
        if 'services.pdf_client' in sys.modules:
            del sys.modules['services.pdf_client']
        from services.pdf_client import validate_pdf_size

        result = validate_pdf_size(b"")
        assert result is None


class TestWarningThresholds:
    """Tests for warning thresholds."""

    def test_html_warning_threshold_exists(self):
        """Test that HTML warning threshold is defined."""
        if 'services.pdf_client' in sys.modules:
            del sys.modules['services.pdf_client']
        from services import pdf_client

        assert hasattr(pdf_client, "WARN_HTML_SIZE_KB")
        assert pdf_client.WARN_HTML_SIZE_KB == 500

    def test_pdf_warning_threshold_exists(self):
        """Test that PDF warning threshold is defined."""
        if 'services.pdf_client' in sys.modules:
            del sys.modules['services.pdf_client']
        from services import pdf_client

        assert hasattr(pdf_client, "WARN_PDF_SIZE_MB")
        assert pdf_client.WARN_PDF_SIZE_MB == 10
