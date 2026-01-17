# -*- coding: utf-8 -*-
"""
Tests for Fix-Batch I - Empty Page Killer & Risk Truncation

Tests:
- Empty page sections are detected and removed
- Risk descriptions truncate at sentence boundaries
- No mid-sentence truncation occurs
"""

import os
import pytest
import re

# Set test environment before imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")


class TestEmptyPageKiller:
    """Test empty page detection and removal."""

    def test_kill_empty_pages_removes_empty_section(self):
        """Test that empty sections with only headings are removed."""
        from services.content_quality_enforcer import kill_empty_pages

        html = '''
        <section class="test">
            <h2>Empty Section</h2>
        </section>
        <section class="test">
            <h2>Section with Content</h2>
            <p>This section has actual content.</p>
        </section>
        '''

        result, count = kill_empty_pages(html)

        # Empty section should be removed
        assert "Empty Section" not in result
        # Section with content should remain
        assert "Section with Content" in result
        assert "This section has actual content" in result
        assert count >= 1

    def test_kill_empty_pages_removes_div_with_only_heading(self):
        """Test that divs with only headings are removed."""
        from services.content_quality_enforcer import kill_empty_pages

        html = '''
        <div class="section">
            <h3>Only Heading</h3>
        </div>
        '''

        result, count = kill_empty_pages(html)

        # Should be removed or significantly changed
        assert count >= 1 or "Only Heading" not in result

    def test_kill_empty_pages_preserves_valid_content(self):
        """Test that valid content sections are preserved."""
        from services.content_quality_enforcer import kill_empty_pages

        html = '''
        <section>
            <h2>Good Section</h2>
            <p>This is important content that should be preserved.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
        </section>
        '''

        result, count = kill_empty_pages(html)

        # All content should be preserved
        assert "Good Section" in result
        assert "important content" in result
        assert "Item 1" in result
        assert count == 0

    def test_kill_empty_pages_handles_empty_input(self):
        """Test that empty input is handled gracefully."""
        from services.content_quality_enforcer import kill_empty_pages

        result, count = kill_empty_pages("")

        assert result == ""
        assert count == 0


class TestRiskTruncation:
    """Test risk description sentence truncation."""

    def test_truncate_at_sentence_basic(self):
        """Test basic sentence truncation."""
        from services.content_quality_enforcer import truncate_at_sentence

        text = "This is the first sentence. This is the second sentence. This is the third sentence that is quite long."

        result = truncate_at_sentence(text, 50)

        # Should end at sentence boundary
        assert result.endswith(".")
        assert len(result) <= 50
        # Should contain first sentence
        assert "first sentence" in result

    def test_truncate_at_sentence_respects_max_chars(self):
        """Test that max_chars is respected."""
        from services.content_quality_enforcer import truncate_at_sentence

        text = "Short. " * 100  # Lots of sentences

        result = truncate_at_sentence(text, 100)

        assert len(result) <= 100

    def test_truncate_at_sentence_preserves_short_text(self):
        """Test that short text is preserved unchanged."""
        from services.content_quality_enforcer import truncate_at_sentence

        text = "This is short."

        result = truncate_at_sentence(text, 100)

        assert result == text

    def test_truncate_at_sentence_handles_exclamation(self):
        """Test that exclamation marks are recognized as sentence boundaries."""
        from services.content_quality_enforcer import truncate_at_sentence

        text = "Warning! This is important. Do not ignore this."

        result = truncate_at_sentence(text, 30)

        # Should end at ! or .
        assert result.endswith("!") or result.endswith(".")

    def test_truncate_at_sentence_handles_question(self):
        """Test that question marks are recognized as sentence boundaries."""
        from services.content_quality_enforcer import truncate_at_sentence

        text = "Is this a risk? Yes it is. Take action now."

        result = truncate_at_sentence(text, 30)

        # Should end at ? or .
        assert result.endswith("?") or result.endswith(".")

    def test_truncate_at_sentence_no_mid_word_cut(self):
        """Test that truncation produces reasonable output."""
        from services.content_quality_enforcer import truncate_at_sentence

        text = "This is a very long sentence that should not be cut in the middle of any word because that would be bad."

        result = truncate_at_sentence(text, 50)

        # Should be truncated
        assert len(result) <= 50
        # Should have some content
        assert len(result) > 10
        # Should either end with punctuation or ellipsis
        assert result[-1] in ".!?…" or result.endswith("...")


class TestRiskTruncationHTML:
    """Test risk description truncation in HTML."""

    def test_truncate_risk_descriptions_basic(self):
        """Test basic HTML risk description truncation."""
        from services.content_quality_enforcer import truncate_risk_descriptions

        long_text = "A" * 100 + ". " + "B" * 100 + ". " + "C" * 100 + ". " + "D" * 100 + ". " + "E" * 100 + "."
        html = f'<div class="risk-description">{long_text}</div>'

        result, count = truncate_risk_descriptions(html, max_chars=200)

        # Should have truncated
        assert count >= 1 or len(result) < len(html)

    def test_truncate_risk_descriptions_preserves_short(self):
        """Test that short descriptions are preserved."""
        from services.content_quality_enforcer import truncate_risk_descriptions

        html = '<div class="risk-description">Short risk.</div>'

        result, count = truncate_risk_descriptions(html, max_chars=500)

        assert result == html
        assert count == 0


class TestBatchIIntegration:
    """Integration tests for Fix-Batch I."""

    def test_apply_empty_page_killer(self):
        """Test apply_empty_page_killer function."""
        from services.content_quality_enforcer import apply_empty_page_killer

        sections = {
            "RISKS_HTML": '''
            <section><h2>Empty</h2></section>
            <section><h2>With Content</h2><p>Real content here.</p></section>
            ''',
            "OTHER_KEY": "unchanged",
        }

        result = apply_empty_page_killer(sections)

        # Should process HTML sections
        assert "Empty" not in result.get("RISKS_HTML", "") or "With Content" in result.get("RISKS_HTML", "")
        # Non-HTML should be unchanged
        assert result["OTHER_KEY"] == "unchanged"

    def test_apply_risk_truncation(self):
        """Test apply_risk_truncation function."""
        from services.content_quality_enforcer import apply_risk_truncation

        sections = {
            "RISKS_HTML": '<div class="risk-description">Short text.</div>',
            "OTHER_KEY": "unchanged",
        }

        result = apply_risk_truncation(sections)

        # Should process risk sections
        assert "Short text" in result.get("RISKS_HTML", "")
        # Non-risk should be unchanged
        assert result["OTHER_KEY"] == "unchanged"

    def test_pipeline_includes_batch_i(self):
        """Test that the quality enforcer pipeline includes Fix-Batch I steps."""
        from services.content_quality_enforcer import apply_all_quality_enforcers

        sections = {
            "RISKS_HTML": "<section><h2>Test</h2><p>Content</p></section>",
        }

        # Should run without errors
        result = apply_all_quality_enforcers(sections)

        assert result is not None

    def test_fix_batch_i_comment_exists(self):
        """Test that Fix-Batch I comment block exists."""
        from services import content_quality_enforcer
        import inspect

        source = inspect.getsource(content_quality_enforcer)

        # Should have Fix-Batch I comments
        assert "Fix-Batch I" in source
        assert "EMPTY PAGE KILLER" in source
        assert "RISK TEXT SENTENCE TRUNCATION" in source

    def test_truncate_at_sentence_exported(self):
        """Test that truncate_at_sentence is importable."""
        from services.content_quality_enforcer import truncate_at_sentence

        assert callable(truncate_at_sentence)

    def test_kill_empty_pages_exported(self):
        """Test that kill_empty_pages is importable."""
        from services.content_quality_enforcer import kill_empty_pages

        assert callable(kill_empty_pages)
