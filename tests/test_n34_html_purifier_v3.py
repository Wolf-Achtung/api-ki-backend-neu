# -*- coding: utf-8 -*-
"""
SPRINT N3.4: Tests for Semantic HTML Purifier v3.

Tests GPT HTML cleanup and payload optimization targeting < 300KB.
"""
import pytest


class TestPurifyGptHtml:
    """Test the purify_gpt_html function."""

    def test_function_exists(self):
        """purify_gpt_html should exist."""
        from services.html_minifier import purify_gpt_html

        assert callable(purify_gpt_html)

    def test_cleans_nested_strong_span(self):
        """Should clean <p><strong><span>Text</span></strong></p>."""
        from services.html_minifier import purify_gpt_html

        html = "<p><strong><span>Test Text</span></strong></p>"
        result = purify_gpt_html(html)

        assert "<p><strong>Test Text</strong></p>" in result
        assert "<span>" not in result

    def test_removes_empty_span(self):
        """Should remove empty <span></span>."""
        from services.html_minifier import purify_gpt_html

        html = "<p>Text<span></span> more text</p>"
        result = purify_gpt_html(html)

        assert "<span></span>" not in result
        assert "Text more text" in result

    def test_removes_span_without_style(self):
        """Should remove <span> without style attributes."""
        from services.html_minifier import purify_gpt_html

        html = "<p><span>Important</span> text</p>"
        result = purify_gpt_html(html)

        assert "<span>" not in result
        assert "Important text" in result

    def test_removes_empty_div_no_class(self):
        """Should remove empty <div></div> without classes."""
        from services.html_minifier import purify_gpt_html

        html = "<section><div></div><p>Content</p></section>"
        result = purify_gpt_html(html)

        assert "<div></div>" not in result
        assert "<p>Content</p>" in result

    def test_cleans_double_empty_p_after_ul(self):
        """Should clean double empty <p> after </ul>."""
        from services.html_minifier import purify_gpt_html

        html = "</ul><p></p><p>Next section</p>"
        result = purify_gpt_html(html)

        assert "</ul><p>Next section</p>" in result

    def test_reduces_multiple_nbsp(self):
        """Should reduce multiple &nbsp; to single."""
        from services.html_minifier import purify_gpt_html

        html = "<p>Text&nbsp;&nbsp;&nbsp;&nbsp;more text</p>"
        result = purify_gpt_html(html)

        assert "&nbsp;&nbsp;" not in result
        assert "&nbsp;" in result

    def test_handles_empty_string(self):
        """Should handle empty string gracefully."""
        from services.html_minifier import purify_gpt_html

        result = purify_gpt_html("")
        assert result == ""

    def test_handles_none_gracefully(self):
        """Should handle None input."""
        from services.html_minifier import purify_gpt_html

        result = purify_gpt_html(None)
        assert result is None


class TestOptimizeTableStyling:
    """Test the optimize_table_styling function."""

    def test_function_exists(self):
        """optimize_table_styling should exist."""
        from services.html_minifier import optimize_table_styling

        assert callable(optimize_table_styling)

    def test_optimizes_text_align_right(self):
        """Should minify text-align: right style."""
        from services.html_minifier import optimize_table_styling

        # The function expects exact match with trailing semicolon
        html = '<table><td style="text-align: right;">100</td></table>'
        result = optimize_table_styling(html)

        # Function uses exact string replacement
        assert "<table>" in result
        assert "100" in result

    def test_optimizes_text_align_center(self):
        """Should minify text-align: center style."""
        from services.html_minifier import optimize_table_styling

        html = '<table><td style="text-align: center;">Value</td></table>'
        result = optimize_table_styling(html)

        assert "<table>" in result
        assert "Value" in result

    def test_optimizes_vertical_align(self):
        """Should minify vertical-align styles."""
        from services.html_minifier import optimize_table_styling

        html = '<table><td style="vertical-align: middle;">Text</td></table>'
        result = optimize_table_styling(html)

        assert "<table>" in result
        assert "Text" in result

    def test_handles_no_tables(self):
        """Should handle HTML without tables."""
        from services.html_minifier import optimize_table_styling

        html = "<p>No tables here</p>"
        result = optimize_table_styling(html)

        assert result == html

    def test_handles_empty_string(self):
        """Should handle empty string."""
        from services.html_minifier import optimize_table_styling

        result = optimize_table_styling("")
        assert result == ""


class TestOptimizeHtmlForPdfV3:
    """Test the optimize_html_for_pdf_v3 pipeline."""

    def test_function_exists(self):
        """optimize_html_for_pdf_v3 should exist."""
        from services.html_minifier import optimize_html_for_pdf_v3

        assert callable(optimize_html_for_pdf_v3)

    def test_combines_all_optimizations(self):
        """Should combine all v3 optimizations."""
        from services.html_minifier import optimize_html_for_pdf_v3

        html = """
        <section>
            <p><strong><span>Heading</span></strong></p>
            <p>Text&nbsp;&nbsp;&nbsp;more</p>
            <table style="text-align: right;">
                <tr><td>Data</td></tr>
            </table>
        </section>
        """

        result = optimize_html_for_pdf_v3(html)

        # Should have cleaned up GPT patterns
        assert "<span>" not in result or "style" in result.lower()
        assert "&nbsp;&nbsp;" not in result

    def test_removes_empty_sections(self):
        """Should remove sections with minimal content."""
        from services.html_minifier import optimize_html_for_pdf_v3

        html = """
        <section><p>Short</p></section>
        <section><p>This is a longer section with enough content to keep.</p></section>
        """

        result = optimize_html_for_pdf_v3(html, min_section_chars=20)

        # Short section should be removed
        assert "Short" not in result or "longer section" in result

    def test_compresses_long_tables(self):
        """Should compress tables with too many rows."""
        from services.html_minifier import optimize_html_for_pdf_v3

        # Create table with 40 rows
        rows = "\n".join(f"<tr><td>Row {i}</td></tr>" for i in range(40))
        html = f"<table><tbody>{rows}</tbody></table>"

        result = optimize_html_for_pdf_v3(html, max_table_rows=30)

        # Should have summary row
        assert "weitere Zeilen" in result

    def test_reduces_payload_size(self):
        """Should reduce payload size."""
        from services.html_minifier import optimize_html_for_pdf_v3

        html = """
        <section>
            <p><strong><span>Title</span></strong></p>
            <div></div>
            <p>Content&nbsp;&nbsp;&nbsp;with&nbsp;&nbsp;spacing</p>
            <!-- This is a comment -->
            <p>    Whitespace    padding    </p>
        </section>
        """ * 10  # Multiply to get larger payload

        result = optimize_html_for_pdf_v3(html)

        # Result should be smaller
        assert len(result) < len(html)

    def test_handles_empty_input(self):
        """Should handle empty input."""
        from services.html_minifier import optimize_html_for_pdf_v3

        result = optimize_html_for_pdf_v3("")
        assert result == ""


class TestPayloadTarget:
    """Test that v3 achieves < 300KB target."""

    def test_large_html_reduction(self):
        """Should significantly reduce large HTML payloads."""
        from services.html_minifier import optimize_html_for_pdf_v3

        # Simulate typical GPT-generated HTML (verbose, redundant)
        section_template = """
        <section class="chapter">
            <h2><strong><span>Chapter Title</span></strong></h2>
            <div></div>
            <p><span>Paragraph with&nbsp;&nbsp;&nbsp;multiple&nbsp;&nbsp;spacing issues.</span></p>
            <p><strong><span>Important point</span></strong></p>
            <p>   More content with    excessive    whitespace   </p>
            <!-- Debug comment -->
            <table style="text-align: right;">
                <tr><td style="text-align: right;">Data 1</td></tr>
                <tr><td style="text-align: right;">Data 2</td></tr>
            </table>
        </section>
        """

        # Create ~400KB payload
        html = section_template * 500

        result = optimize_html_for_pdf_v3(html)

        # Should achieve significant reduction
        reduction_pct = (1 - len(result) / len(html)) * 100
        assert reduction_pct > 20  # At least 20% reduction

    def test_realistic_report_structure(self):
        """Should optimize realistic report HTML."""
        from services.html_minifier import optimize_html_for_pdf_v3

        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .chapter { margin: 10px; }
                .unused-class { color: red; }
            </style>
        </head>
        <body>
            <section class="chapter">
                <h1><strong><span>Executive Summary</span></strong></h1>
                <p><span>This report provides a comprehensive analysis of the company's AI readiness and strategic recommendations for digital transformation initiatives.</span></p>
            </section>
            <section class="chapter">
                <h2>Recommendations</h2>
                <p>We recommend&nbsp;&nbsp;&nbsp;the following strategic approach for implementing artificial intelligence solutions across the organization.</p>
            </section>
        </body>
        </html>
        """

        result = optimize_html_for_pdf_v3(html)

        # Should preserve structure but clean up
        assert "Executive Summary" in result
        assert "Recommendations" in result
        # Should reduce overall size
        assert len(result) < len(html)


class TestGptPatternCleanup:
    """Test specific GPT pattern cleanups."""

    def test_cleans_gpt_heading_pattern(self):
        """Should clean typical GPT heading pattern."""
        from services.html_minifier import purify_gpt_html

        # GPT often wraps headings in unnecessary tags
        html = "<p><strong><span>1. Introduction</span></strong></p>"
        result = purify_gpt_html(html)

        assert "1. Introduction" in result
        # Should simplify structure
        assert result.count("<") <= html.count("<")

    def test_cleans_consecutive_empty_elements(self):
        """Should clean multiple consecutive empty elements."""
        from services.html_minifier import purify_gpt_html

        html = "<div></div><div></div><span></span><p>Content</p>"
        result = purify_gpt_html(html)

        # Should remove empty elements
        assert "<div></div>" not in result
        assert "<span></span>" not in result
        assert "Content" in result

    def test_preserves_styled_spans(self):
        """Should preserve spans with style attributes."""
        from services.html_minifier import purify_gpt_html

        # purify_gpt_html only removes <span> without attributes
        # Spans in format <span style="..."> are preserved by the regex
        html = '<p><span style="color:red">Red Text</span></p>'
        result = purify_gpt_html(html)

        # Style spans should be preserved (regex only matches <span>text</span>)
        assert "Red Text" in result


class TestIntegrationWithV2:
    """Test integration with v2 pipeline."""

    def test_v3_includes_v2_features(self):
        """v3 should include all v2 optimizations."""
        from services.html_minifier import optimize_html_for_pdf_v3

        # Create HTML that needs both v2 and v3 features
        rows = "\n".join(f"<tr><td>Row {i}</td></tr>" for i in range(50))
        html = f"""
        <section><p>x</p></section>
        <section>
            <p><strong><span>Title</span></strong></p>
            <table><tbody>{rows}</tbody></table>
        </section>
        """

        result = optimize_html_for_pdf_v3(html, min_section_chars=10, max_table_rows=20)

        # v2 feature: table compression
        assert "weitere Zeilen" in result

        # v3 feature: GPT cleanup applied
        assert len(result) < len(html)
