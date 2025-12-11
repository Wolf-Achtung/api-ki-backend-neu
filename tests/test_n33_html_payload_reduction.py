# -*- coding: utf-8 -*-
"""
SPRINT N3.3: Tests for HTML Payload Reduction Engine Phase 2.

Tests the new remove_empty_sections and compress_long_tables functions.
"""
import pytest


class TestRemoveEmptySections:
    """Test remove_empty_sections function."""

    def test_function_exists(self):
        """remove_empty_sections should exist."""
        from services.html_minifier import remove_empty_sections

        assert callable(remove_empty_sections)

    def test_removes_empty_section(self):
        """Should remove sections with < 50 chars of content."""
        from services.html_minifier import remove_empty_sections

        html = '<div><section><p>Hi</p></section><section><p>This is good content with more than fifty characters here.</p></section></div>'
        result = remove_empty_sections(html, min_chars=50)

        # First section with "Hi" (2 chars) should be removed
        assert "Hi" not in result
        # Second section should remain
        assert "good content" in result

    def test_keeps_section_with_enough_content(self):
        """Should keep sections with >= 50 chars of content."""
        from services.html_minifier import remove_empty_sections

        html = '<section><p>This section has plenty of content that exceeds the minimum character requirement for inclusion.</p></section>'
        result = remove_empty_sections(html, min_chars=50)

        assert "<section>" in result
        assert "plenty of content" in result

    def test_custom_min_chars(self):
        """Should respect custom min_chars parameter."""
        from services.html_minifier import remove_empty_sections

        html = '<section><p>Short text here.</p></section>'

        # With min_chars=10, should keep
        result = remove_empty_sections(html, min_chars=10)
        assert "Short text" in result

        # With min_chars=100, should remove
        result = remove_empty_sections(html, min_chars=100)
        assert "Short text" not in result

    def test_removes_multiple_empty_sections(self):
        """Should remove multiple empty sections."""
        from services.html_minifier import remove_empty_sections

        html = '''
        <section><p>A</p></section>
        <section><p>B</p></section>
        <section><p>This is a section with substantial content that should be kept in the output.</p></section>
        <section><p>C</p></section>
        '''
        result = remove_empty_sections(html, min_chars=50)

        # Single-letter sections should be removed
        assert ">A<" not in result
        assert ">B<" not in result
        assert ">C<" not in result
        # Substantial content should remain
        assert "substantial content" in result

    def test_counts_text_not_html(self):
        """Should count text content, not HTML tags."""
        from services.html_minifier import remove_empty_sections

        # HTML with many tags but little text
        html = '<section><div><span><strong><em>Hi</em></strong></span></div></section>'
        result = remove_empty_sections(html, min_chars=50)

        # Should be removed because text content is just "Hi"
        assert "<section>" not in result

    def test_empty_html(self):
        """Should handle empty HTML safely."""
        from services.html_minifier import remove_empty_sections

        result = remove_empty_sections("", min_chars=50)
        assert result == ""


class TestCompressLongTables:
    """Test compress_long_tables function."""

    def test_function_exists(self):
        """compress_long_tables should exist."""
        from services.html_minifier import compress_long_tables

        assert callable(compress_long_tables)

    def test_keeps_short_table(self):
        """Should keep tables with <= 30 rows unchanged."""
        from services.html_minifier import compress_long_tables

        rows = ''.join([f'<tr><td>Row {i}</td></tr>' for i in range(20)])
        html = f'<table>{rows}</table>'
        result = compress_long_tables(html, max_rows=30)

        # Table should be unchanged
        assert "Row 19" in result
        assert "weitere Zeilen" not in result

    def test_compresses_long_table(self):
        """Should compress tables with > 30 rows."""
        from services.html_minifier import compress_long_tables

        rows = ''.join([f'<tr><td>Row {i}</td></tr>' for i in range(50)])
        html = f'<table>{rows}</table>'
        result = compress_long_tables(html, max_rows=30)

        # Should have summary row
        assert "weitere Zeilen" in result
        # First 10 rows should be visible
        assert "Row 0" in result
        assert "Row 9" in result
        # Last 5 rows should be visible
        assert "Row 45" in result
        assert "Row 49" in result
        # Middle rows should be removed
        assert "Row 20" not in result

    def test_summary_shows_hidden_count(self):
        """Summary row should show correct hidden row count."""
        from services.html_minifier import compress_long_tables

        # 50 rows: first 10 + last 5 = 15 visible, 35 hidden
        rows = ''.join([f'<tr><td>Row {i}</td></tr>' for i in range(50)])
        html = f'<table>{rows}</table>'
        result = compress_long_tables(html, max_rows=30)

        assert "35 weitere Zeilen" in result

    def test_custom_max_rows(self):
        """Should respect custom max_rows parameter."""
        from services.html_minifier import compress_long_tables

        rows = ''.join([f'<tr><td>Row {i}</td></tr>' for i in range(25)])
        html = f'<table>{rows}</table>'

        # With max_rows=30, should not compress
        result = compress_long_tables(html, max_rows=30)
        assert "weitere Zeilen" not in result

        # With max_rows=20, should compress
        result = compress_long_tables(html, max_rows=20)
        assert "weitere Zeilen" in result

    def test_handles_tbody(self):
        """Should work with tables that have tbody."""
        from services.html_minifier import compress_long_tables

        rows = ''.join([f'<tr><td>Row {i}</td></tr>' for i in range(50)])
        html = f'<table><thead><tr><th>Header</th></tr></thead><tbody>{rows}</tbody></table>'
        result = compress_long_tables(html, max_rows=30)

        assert "weitere Zeilen" in result
        assert "Header" in result

    def test_preserves_column_count(self):
        """Summary row should span correct number of columns."""
        from services.html_minifier import compress_long_tables

        rows = ''.join([f'<tr><td>A{i}</td><td>B{i}</td><td>C{i}</td></tr>' for i in range(50)])
        html = f'<table>{rows}</table>'
        result = compress_long_tables(html, max_rows=30)

        assert 'colspan="3"' in result

    def test_empty_html(self):
        """Should handle empty HTML safely."""
        from services.html_minifier import compress_long_tables

        result = compress_long_tables("", max_rows=30)
        assert result == ""


class TestOptimizeHtmlForPdfV2:
    """Test the enhanced optimization pipeline."""

    def test_function_exists(self):
        """optimize_html_for_pdf_v2 should exist."""
        from services.html_minifier import optimize_html_for_pdf_v2

        assert callable(optimize_html_for_pdf_v2)

    def test_combines_all_optimizations(self):
        """Should apply both empty section removal and table compression."""
        from services.html_minifier import optimize_html_for_pdf_v2

        # Create HTML with empty section and long table
        rows = ''.join([f'<tr><td>Row {i}</td></tr>' for i in range(50)])
        html = f'''
        <html>
        <body>
        <section><p>X</p></section>
        <section><p>This is substantial content that should be kept in the final output.</p></section>
        <table>{rows}</table>
        </body>
        </html>
        '''
        result = optimize_html_for_pdf_v2(html, min_section_chars=50, max_table_rows=30)

        # Empty section should be removed
        assert ">X<" not in result
        # Substantial section should remain
        assert "substantial content" in result
        # Table should be compressed
        assert "weitere Zeilen" in result

    def test_reduces_payload_size(self):
        """Optimization should reduce HTML size."""
        from services.html_minifier import optimize_html_for_pdf_v2

        # Create large HTML
        sections = ''.join([f'<section><p>A</p></section>' for _ in range(10)])
        rows = ''.join([f'<tr><td>Row {i}</td></tr>' for i in range(100)])
        html = f'<html><body>{sections}<table>{rows}</table></body></html>'

        original_size = len(html)
        result = optimize_html_for_pdf_v2(html)
        new_size = len(result)

        # Should be smaller
        assert new_size < original_size


class TestPayloadTargets:
    """Test that optimization achieves target payload sizes."""

    def test_significant_reduction_on_large_html(self):
        """Should achieve significant reduction on large HTML."""
        from services.html_minifier import optimize_html_for_pdf_v2

        # Simulate a 400KB HTML payload
        # Many empty sections
        empty_sections = ''.join([
            f'<section class="chapter-{i}"><p>.</p></section>'
            for i in range(100)
        ])
        # Large tables
        large_table_rows = ''.join([
            f'<tr><td>Data {i}</td><td>Value {i}</td><td>Info {i}</td></tr>'
            for i in range(200)
        ])
        # Substantial content
        substantial = '<section><p>' + 'Substantial content. ' * 100 + '</p></section>'

        html = f'''
        <html>
        <head><style>.chapter-1 {{ color: red; }}</style></head>
        <body>
        {empty_sections}
        {substantial}
        <table class="data-table">{large_table_rows}</table>
        </body>
        </html>
        '''

        original_size = len(html)
        result = optimize_html_for_pdf_v2(html)
        new_size = len(result)

        # Should reduce by at least 30%
        reduction_pct = (1 - new_size / original_size) * 100
        assert reduction_pct > 30, f"Expected >30% reduction, got {reduction_pct:.1f}%"
