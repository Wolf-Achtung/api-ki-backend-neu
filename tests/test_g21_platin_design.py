# -*- coding: utf-8 -*-
"""
Sprint G21: PLATIN++ Design Enhancement Tests

Tests for design system CSS classes in v7 template:
- KPI card design
- Management cards
- Decision cards
- Funding cards
- Badge system
- Section kickers
- SVG icon library documentation
- Prompt updates with design examples
"""
from __future__ import annotations

import pytest
from pathlib import Path


class TestG21CSSClasses:
    """Tests for design CSS classes in v7 PDF template."""

    @pytest.fixture
    def templates_dir(self) -> Path:
        """Get templates directory."""
        return Path(__file__).parent.parent / "templates"

    def test_de_template_has_design_css(self, templates_dir: Path) -> None:
        """Test that PDF template has design system CSS."""
        template_file = templates_dir / "pdf_template_v7.html"
        content = template_file.read_text(encoding="utf-8")

        assert ".kpi-card" in content, \
            "Template should have .kpi-card CSS class"
        assert ".mgmt-card" in content, \
            "Template should have .mgmt-card CSS class"

    def test_kpi_classes_exist(self, templates_dir: Path) -> None:
        """Test that KPI CSS classes exist in template."""
        template_file = templates_dir / "pdf_template_v7.html"
        content = template_file.read_text(encoding="utf-8")

        required_classes = [
            ".kpi-card",
            ".kpi-label",
            ".kpi-value",
        ]

        for css_class in required_classes:
            assert css_class in content, \
                f"Template should have {css_class} CSS class"

    def test_card_classes_exist(self, templates_dir: Path) -> None:
        """Test that card CSS classes exist in template."""
        template_file = templates_dir / "pdf_template_v7.html"
        content = template_file.read_text(encoding="utf-8")

        required_classes = [
            ".mgmt-card",
            ".decision-card",
            ".funding-card",
            ".card-nobreak",
        ]

        for css_class in required_classes:
            assert css_class in content, \
                f"Template should have {css_class} CSS class"

    def test_badge_classes_exist(self, templates_dir: Path) -> None:
        """Test that badge CSS classes exist in template."""
        template_file = templates_dir / "pdf_template_v7.html"
        content = template_file.read_text(encoding="utf-8")

        required_classes = [
            ".badge",
            ".badge-strategy",
            ".badge-action",
            ".badge-risk",
            ".badge-finance",
        ]

        for css_class in required_classes:
            assert css_class in content, \
                f"Template should have {css_class} CSS class"

    def test_section_kicker_exists(self, templates_dir: Path) -> None:
        """Test that section-kicker CSS class exists in template."""
        template_file = templates_dir / "pdf_template_v7.html"
        content = template_file.read_text(encoding="utf-8")

        assert ".section-kicker" in content, \
            "Template should have .section-kicker CSS class"

    def test_css_has_page_break_avoid(self, templates_dir: Path) -> None:
        """Test that card CSS uses page-break-inside: avoid."""
        template_file = templates_dir / "pdf_template_v7.html"
        content = template_file.read_text(encoding="utf-8")

        assert content.count("page-break-inside: avoid") >= 3, \
            "CSS should use page-break-inside: avoid for proper PDF pagination"


class TestG21IconLibrary:
    """Tests for G21 SVG icon library documentation."""

    @pytest.fixture
    def docs_dir(self) -> Path:
        """Get docs directory."""
        return Path(__file__).parent.parent / "docs"

    def test_svg_icon_documentation_exists(self, docs_dir: Path) -> None:
        """Test that SVG icon documentation file exists."""
        icon_doc = docs_dir / "G21_SVG_ICONS.md"
        assert icon_doc.exists(), "G21_SVG_ICONS.md documentation should exist"

    def test_icon_documentation_has_all_icons(self, docs_dir: Path) -> None:
        """Test that icon documentation includes all required icons."""
        icon_doc = docs_dir / "G21_SVG_ICONS.md"
        content = icon_doc.read_text(encoding="utf-8")

        required_icons = [
            "Automation",
            "Analysis",
            "Collaboration",
            "Compliance",
            "Research",
            "Funding",
            "KPI",
            "Risk",
            "Branch",
            "Step",
        ]

        for icon_name in required_icons:
            assert icon_name in content, \
                f"Icon documentation should include {icon_name} icon"

    def test_icon_documentation_has_svg_tags(self, docs_dir: Path) -> None:
        """Test that icon documentation includes actual SVG code."""
        icon_doc = docs_dir / "G21_SVG_ICONS.md"
        content = icon_doc.read_text(encoding="utf-8")

        assert "<svg" in content, "Icon documentation should include SVG tags"
        assert "viewBox=" in content, "SVG icons should have viewBox attribute"
        assert "stroke=" in content, "SVG icons should have stroke attributes"
        assert "currentColor" in content, "SVG icons should use currentColor"


class TestG21PromptUpdates:
    """Tests for G21 prompt updates with design examples."""

    @pytest.fixture
    def prompts_dir(self) -> Path:
        """Get prompts directory."""
        return Path(__file__).parent.parent / "prompts"

    def test_de_ki_stack_summary_has_design_section(self, prompts_dir: Path) -> None:
        """Test that German G20 prompt has design section."""
        prompt_file = prompts_dir / "de" / "ki_stack_summary.md"
        content = prompt_file.read_text(encoding="utf-8")

        assert "G21 PLATIN++" in content, \
            "German G20 prompt should reference G21 PLATIN++ design"
        assert "pair-card" in content, \
            "German G20 prompt should mention pair-card class"
        assert "kpi-triple" in content, \
            "German G20 prompt should mention kpi-triple class"
        assert "step-cards" in content, \
            "German G20 prompt should mention step-cards class"

    def test_en_ki_stack_summary_has_design_section(self, prompts_dir: Path) -> None:
        """Test that English G20 prompt has design section."""
        prompt_file = prompts_dir / "en" / "ki_stack_summary.md"
        content = prompt_file.read_text(encoding="utf-8")

        assert "G21 PLATIN++" in content, \
            "English G20 prompt should reference G21 PLATIN++ design"
        assert "pair-card" in content, \
            "English G20 prompt should mention pair-card class"
        assert "kpi-triple" in content, \
            "English G20 prompt should mention kpi-triple class"
        assert "step-cards" in content, \
            "English G20 prompt should mention step-cards class"

    def test_de_prompt_has_svg_icon_examples(self, prompts_dir: Path) -> None:
        """Test that German G20 prompt has SVG icon examples."""
        prompt_file = prompts_dir / "de" / "ki_stack_summary.md"
        content = prompt_file.read_text(encoding="utf-8")

        assert "<svg viewBox=" in content, "German G20 prompt should have SVG examples"
        assert "Automation:" in content, "German G20 prompt should reference Automation icon"
        assert "Funding:" in content, "German G20 prompt should reference Funding icon"

    def test_en_prompt_has_svg_icon_examples(self, prompts_dir: Path) -> None:
        """Test that English G20 prompt has SVG icon examples."""
        prompt_file = prompts_dir / "en" / "ki_stack_summary.md"
        content = prompt_file.read_text(encoding="utf-8")

        assert "<svg viewBox=" in content, "English G20 prompt should have SVG examples"
        assert "Automation:" in content, "English G20 prompt should reference Automation icon"
        assert "Funding:" in content, "English G20 prompt should reference Funding icon"

    def test_de_prompt_has_html_structure_example(self, prompts_dir: Path) -> None:
        """Test that German G20 prompt has HTML structure example."""
        prompt_file = prompts_dir / "de" / "ki_stack_summary.md"
        content = prompt_file.read_text(encoding="utf-8")

        assert "```html" in content, "German G20 prompt should have HTML code block"
        assert "ki-stack-summary" in content, "German G20 prompt should show ki-stack-summary class"
        assert "stack-section" in content, "German G20 prompt should show stack-section class"

    def test_en_prompt_has_html_structure_example(self, prompts_dir: Path) -> None:
        """Test that English G20 prompt has HTML structure example."""
        prompt_file = prompts_dir / "en" / "ki_stack_summary.md"
        content = prompt_file.read_text(encoding="utf-8")

        assert "```html" in content, "English G20 prompt should have HTML code block"
        assert "ki-stack-summary" in content, "English G20 prompt should show ki-stack-summary class"
        assert "stack-section" in content, "English G20 prompt should show stack-section class"


class TestG21CSSQuality:
    """Tests for CSS quality and completeness."""

    @pytest.fixture
    def templates_dir(self) -> Path:
        """Get templates directory."""
        return Path(__file__).parent.parent / "templates"

    def test_css_uses_css_variables(self, templates_dir: Path) -> None:
        """Test that CSS uses CSS custom properties (variables)."""
        template_file = templates_dir / "pdf_template_v7.html"
        content = template_file.read_text(encoding="utf-8")

        assert "var(--" in content, "CSS should use CSS custom properties"
        assert ":root" in content or "--c-" in content, \
            "CSS should define custom properties"

    def test_css_has_page_break_avoid(self, templates_dir: Path) -> None:
        """Test that CSS uses page-break-inside: avoid for cards."""
        template_file = templates_dir / "pdf_template_v7.html"
        content = template_file.read_text(encoding="utf-8")

        assert content.count("page-break-inside: avoid") >= 3, \
            "CSS should use page-break-inside: avoid for proper PDF pagination"
