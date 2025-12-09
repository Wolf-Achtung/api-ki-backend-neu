# -*- coding: utf-8 -*-
"""
Sprint G21: PLATIN++ Design Enhancement Tests

Tests for G21 PLATIN++ Design Enhancement System:
- Report card CSS classes in templates
- KPI triple block design
- Step cards for starter kit
- Pair cards for tools/funding
- Badge block for branch/risk
- SVG icon library documentation
- G20 prompt updates with design examples
"""
from __future__ import annotations

import pytest
from pathlib import Path


class TestG21CSSClasses:
    """Tests for G21 CSS classes in PDF templates."""

    @pytest.fixture
    def templates_dir(self) -> Path:
        """Get templates directory."""
        return Path(__file__).parent.parent / "templates"

    def test_de_template_has_g21_css_section(self, templates_dir: Path) -> None:
        """Test that German PDF template has G21 CSS section."""
        template_file = templates_dir / "pdf_template.html"
        content = template_file.read_text(encoding="utf-8")

        assert "G21: PLATIN++ DESIGN ENHANCEMENT SYSTEM" in content, \
            "German template should have G21 CSS section marker"

    def test_en_template_has_g21_css_section(self, templates_dir: Path) -> None:
        """Test that English PDF template has G21 CSS section."""
        template_file = templates_dir / "pdf_template_en.html"
        content = template_file.read_text(encoding="utf-8")

        assert "G21: PLATIN++ DESIGN ENHANCEMENT SYSTEM" in content, \
            "English template should have G21 CSS section marker"

    def test_report_card_classes_exist_de(self, templates_dir: Path) -> None:
        """Test that report card CSS classes exist in German template."""
        template_file = templates_dir / "pdf_template.html"
        content = template_file.read_text(encoding="utf-8")

        required_classes = [
            ".report-card",
            ".report-card-header",
            ".report-card-icon",
            ".report-card-title",
            ".report-card-badge",
            ".report-card-body",
        ]

        for css_class in required_classes:
            assert css_class in content, \
                f"German template should have {css_class} CSS class"

    def test_report_card_classes_exist_en(self, templates_dir: Path) -> None:
        """Test that report card CSS classes exist in English template."""
        template_file = templates_dir / "pdf_template_en.html"
        content = template_file.read_text(encoding="utf-8")

        required_classes = [
            ".report-card",
            ".report-card-header",
            ".report-card-icon",
            ".report-card-title",
            ".report-card-badge",
            ".report-card-body",
        ]

        for css_class in required_classes:
            assert css_class in content, \
                f"English template should have {css_class} CSS class"

    def test_kpi_triple_classes_exist_de(self, templates_dir: Path) -> None:
        """Test that KPI triple CSS classes exist in German template."""
        template_file = templates_dir / "pdf_template.html"
        content = template_file.read_text(encoding="utf-8")

        required_classes = [
            ".kpi-triple",
            ".kpi",
            ".kpi-label",
            ".kpi-value",
            ".kpi-sub",
        ]

        for css_class in required_classes:
            assert css_class in content, \
                f"German template should have {css_class} CSS class"

    def test_kpi_triple_classes_exist_en(self, templates_dir: Path) -> None:
        """Test that KPI triple CSS classes exist in English template."""
        template_file = templates_dir / "pdf_template_en.html"
        content = template_file.read_text(encoding="utf-8")

        required_classes = [
            ".kpi-triple",
            ".kpi",
            ".kpi-label",
            ".kpi-value",
            ".kpi-sub",
        ]

        for css_class in required_classes:
            assert css_class in content, \
                f"English template should have {css_class} CSS class"

    def test_step_card_classes_exist_de(self, templates_dir: Path) -> None:
        """Test that step card CSS classes exist in German template."""
        template_file = templates_dir / "pdf_template.html"
        content = template_file.read_text(encoding="utf-8")

        required_classes = [
            ".step-cards",
            ".step-card",
            ".step-card-number",
            ".step-card-title",
            ".step-card-body",
        ]

        for css_class in required_classes:
            assert css_class in content, \
                f"German template should have {css_class} CSS class"

    def test_step_card_classes_exist_en(self, templates_dir: Path) -> None:
        """Test that step card CSS classes exist in English template."""
        template_file = templates_dir / "pdf_template_en.html"
        content = template_file.read_text(encoding="utf-8")

        required_classes = [
            ".step-cards",
            ".step-card",
            ".step-card-number",
            ".step-card-title",
            ".step-card-body",
        ]

        for css_class in required_classes:
            assert css_class in content, \
                f"English template should have {css_class} CSS class"

    def test_pair_card_classes_exist_de(self, templates_dir: Path) -> None:
        """Test that pair card CSS classes exist in German template."""
        template_file = templates_dir / "pdf_template.html"
        content = template_file.read_text(encoding="utf-8")

        required_classes = [
            ".pair-card",
            ".pair-card-icon",
            ".pair-card-content",
            ".pair-card-name",
            ".pair-card-category",
            ".pair-card-description",
        ]

        for css_class in required_classes:
            assert css_class in content, \
                f"German template should have {css_class} CSS class"

    def test_pair_card_classes_exist_en(self, templates_dir: Path) -> None:
        """Test that pair card CSS classes exist in English template."""
        template_file = templates_dir / "pdf_template_en.html"
        content = template_file.read_text(encoding="utf-8")

        required_classes = [
            ".pair-card",
            ".pair-card-icon",
            ".pair-card-content",
            ".pair-card-name",
            ".pair-card-category",
            ".pair-card-description",
        ]

        for css_class in required_classes:
            assert css_class in content, \
                f"English template should have {css_class} CSS class"

    def test_badge_block_classes_exist_de(self, templates_dir: Path) -> None:
        """Test that badge block CSS classes exist in German template."""
        template_file = templates_dir / "pdf_template.html"
        content = template_file.read_text(encoding="utf-8")

        required_classes = [
            ".badge-block",
            ".badge-block-item",
            ".badge-block-label",
            ".badge-block-value",
            ".badge-block-icon",
        ]

        for css_class in required_classes:
            assert css_class in content, \
                f"German template should have {css_class} CSS class"

    def test_badge_block_classes_exist_en(self, templates_dir: Path) -> None:
        """Test that badge block CSS classes exist in English template."""
        template_file = templates_dir / "pdf_template_en.html"
        content = template_file.read_text(encoding="utf-8")

        required_classes = [
            ".badge-block",
            ".badge-block-item",
            ".badge-block-label",
            ".badge-block-value",
            ".badge-block-icon",
        ]

        for css_class in required_classes:
            assert css_class in content, \
                f"English template should have {css_class} CSS class"

    def test_risk_level_classes_exist_de(self, templates_dir: Path) -> None:
        """Test that risk level CSS classes exist in German template."""
        template_file = templates_dir / "pdf_template.html"
        content = template_file.read_text(encoding="utf-8")

        required_classes = [
            ".risk-low",
            ".risk-medium",
            ".risk-high",
        ]

        for css_class in required_classes:
            assert css_class in content, \
                f"German template should have {css_class} CSS class"

    def test_risk_level_classes_exist_en(self, templates_dir: Path) -> None:
        """Test that risk level CSS classes exist in English template."""
        template_file = templates_dir / "pdf_template_en.html"
        content = template_file.read_text(encoding="utf-8")

        required_classes = [
            ".risk-low",
            ".risk-medium",
            ".risk-high",
        ]

        for css_class in required_classes:
            assert css_class in content, \
                f"English template should have {css_class} CSS class"


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
    """Tests for G21 CSS quality and completeness."""

    @pytest.fixture
    def templates_dir(self) -> Path:
        """Get templates directory."""
        return Path(__file__).parent.parent / "templates"

    def test_css_uses_platin_variables(self, templates_dir: Path) -> None:
        """Test that G21 CSS uses PLATIN++ V5.2 CSS variables."""
        template_file = templates_dir / "pdf_template.html"
        content = template_file.read_text(encoding="utf-8")

        # Find G21 section
        g21_start = content.find("G21: PLATIN++ DESIGN ENHANCEMENT SYSTEM")
        assert g21_start > 0, "G21 CSS section should exist"

        g21_section = content[g21_start:g21_start + 10000]

        assert "var(--color-bg-card)" in g21_section, "G21 CSS should use --color-bg-card variable"
        assert "var(--color-border)" in g21_section, "G21 CSS should use --color-border variable"
        assert "var(--color-brand-primary)" in g21_section, "G21 CSS should use --color-brand-primary variable"
        assert "var(--radius-card)" in g21_section, "G21 CSS should use --radius-card variable"

    def test_css_has_break_inside_avoid(self, templates_dir: Path) -> None:
        """Test that G21 CSS uses break-inside: avoid for cards."""
        template_file = templates_dir / "pdf_template.html"
        content = template_file.read_text(encoding="utf-8")

        # Find G21 section
        g21_start = content.find("G21: PLATIN++ DESIGN ENHANCEMENT SYSTEM")
        g21_section = content[g21_start:g21_start + 10000]

        # All card types should have break-inside: avoid for PDF rendering
        assert g21_section.count("break-inside: avoid") >= 5, \
            "G21 CSS should use break-inside: avoid for proper PDF pagination"
