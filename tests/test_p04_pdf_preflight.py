# -*- coding: utf-8 -*-
"""
Tests for P0.4 - PDF Preflight: Pagebreak Cleanup & Empty Page Prevention

Tests:
- test_pagebreak_cleanup_removes_consecutive_breaks()
- test_pagebreak_cleanup_removes_empty_sections()
- test_css_has_break_inside_avoid()
"""

import pytest
import re
from pathlib import Path


class TestPagebreakCleanup:
    """Test the pagebreak cleanup function from report_renderer."""

    def test_pagebreak_cleanup_removes_consecutive_breaks(self):
        """Test that consecutive pagebreak divs are reduced to one or removed."""
        from services.report_renderer import cleanup_pagebreaks

        # Input with 3 consecutive pagebreaks followed by chapter
        # Note: .chapter has CSS page-break-before:always, so the div pagebreak is redundant
        html = '''<body>
<div class="page-break"></div>
<div class="page-break"></div>
<div class="page-break"></div>
<section class="chapter">Content</section>
</body>'''

        cleaned, count = cleanup_pagebreaks(html, run_id="test")

        # Should have removed at least 2 (consecutive reduction + orphan at body start)
        # All 3 may be removed since .chapter already has page-break-before
        assert count >= 2, f"Expected at least 2 removed, got {count}"

        # Content should be preserved
        assert "Content" in cleaned

    def test_pagebreak_cleanup_removes_empty_sections(self):
        """Test that empty sections are removed."""
        from services.report_renderer import cleanup_pagebreaks

        # Input with empty sections
        html = '''<body>
<section class="chapter"></section>
<section class="empty"><div></div></section>
<section class="content">Real content here</section>
</body>'''

        cleaned, count = cleanup_pagebreaks(html, run_id="test")

        # Should have removed the empty sections
        assert count >= 1, f"Expected at least 1 removed, got {count}"

        # Real content should be preserved
        assert "Real content here" in cleaned

    def test_pagebreak_cleanup_removes_orphaned_at_start(self):
        """Test that pagebreak at body start is removed."""
        from services.report_renderer import cleanup_pagebreaks

        html = '''<body>
<div class="page-break"></div>
<section>Content</section>
</body>'''

        cleaned, count = cleanup_pagebreaks(html, run_id="test")

        # Should not have pagebreak immediately after body
        assert '<body>\n<div class="page-break"' not in cleaned
        # Content should be preserved
        assert "Content" in cleaned

    def test_pagebreak_cleanup_removes_orphaned_at_end(self):
        """Test that pagebreak at body end is removed."""
        from services.report_renderer import cleanup_pagebreaks

        html = '''<body>
<section>Content</section>
<div class="page-break"></div>
</body>'''

        cleaned, count = cleanup_pagebreaks(html, run_id="test")

        # Should not have pagebreak immediately before </body>
        assert '<div class="page-break"></div>\n</body>' not in cleaned
        # Content should be preserved
        assert "Content" in cleaned

    def test_pagebreak_cleanup_preserves_valid_breaks(self):
        """Test that pagebreaks between non-chapter content are preserved."""
        from services.report_renderer import cleanup_pagebreaks

        # Note: pagebreaks before .chapter are removed (redundant with CSS)
        # but pagebreaks before non-chapter content are preserved
        html = '''<body>
<section class="content">Content 1</section>
<div class="page-break"></div>
<section class="content">Content 2</section>
<div class="page-break"></div>
<section class="content">Content 3</section>
</body>'''

        cleaned, count = cleanup_pagebreaks(html, run_id="test")

        # Valid pagebreaks between non-chapter sections should be preserved
        pagebreak_matches = re.findall(r'<div class="page-break"[^>]*>', cleaned)
        assert len(pagebreak_matches) == 2, f"Expected 2 pagebreaks, found {len(pagebreak_matches)}"

    def test_pagebreak_cleanup_removes_before_chapter(self):
        """Test that pagebreaks before .chapter elements are removed (redundant)."""
        from services.report_renderer import cleanup_pagebreaks

        # .chapter has CSS page-break-before:always, so div pagebreak is redundant
        html = '''<body>
<section class="chapter">Chapter 1</section>
<div class="page-break"></div>
<section class="chapter">Chapter 2</section>
</body>'''

        cleaned, count = cleanup_pagebreaks(html, run_id="test")

        # Pagebreak before .chapter should be removed (redundant)
        assert count >= 1, f"Expected at least 1 removed, got {count}"

        # All chapter content should be preserved
        assert "Chapter 1" in cleaned
        assert "Chapter 2" in cleaned


class TestCSSBreakInsideAvoid:
    """Test that CSS has proper break-inside rules for cards/tables."""

    @pytest.fixture
    def template_css(self):
        """Load the PDF template CSS."""
        template_path = Path(__file__).parent.parent / "templates" / "pdf_template_v7.html"
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()

    def test_css_has_page_break_inside_avoid_for_cards(self, template_css):
        """Test that card elements have page-break-inside: avoid."""
        # v7 uses page-break-inside: avoid for card elements
        assert "page-break-inside: avoid" in template_css, \
            "Template should have page-break-inside: avoid for cards"
        # Check specific v7 card classes
        assert ".kpi-card" in template_css, \
            "Template should have .kpi-card class"
        assert ".card-nobreak" in template_css, \
            "Template should have .card-nobreak class"

    def test_css_section_allows_breaks(self, template_css):
        """Test that .section allows breaks (to prevent empty pages)."""
        # .section should have break-inside: auto
        pattern = r'\.section\s*\{[^}]*break-inside:\s*auto'
        match = re.search(pattern, template_css, re.DOTALL)
        assert match is not None, ".section should have break-inside: auto"


class TestP04Integration:
    """Integration tests for P0.4 in the render pipeline."""

    def test_cleanup_integrated_in_render_pipeline(self):
        """Test that cleanup_pagebreaks is called in render pipeline."""
        from services import report_renderer
        import inspect

        # Get the source code of the render function
        source = inspect.getsource(report_renderer.render)

        # Check that cleanup_pagebreaks is called
        assert "cleanup_pagebreaks" in source, "cleanup_pagebreaks should be called in render()"

    def test_cleanup_function_exists(self):
        """Test that cleanup_pagebreaks function is exported."""
        from services.report_renderer import cleanup_pagebreaks

        assert callable(cleanup_pagebreaks), "cleanup_pagebreaks should be callable"

    def test_cleanup_handles_empty_input(self):
        """Test that cleanup handles empty/None input gracefully."""
        from services.report_renderer import cleanup_pagebreaks

        result, count = cleanup_pagebreaks("", run_id="test")
        assert result == ""
        assert count == 0

        result, count = cleanup_pagebreaks(None, run_id="test")
        assert result == ""
        assert count == 0
