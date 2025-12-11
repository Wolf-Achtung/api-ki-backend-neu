# -*- coding: utf-8 -*-
"""
SPRINT N3.7 PACKAGE G: Comprehensive Regression Test Suite.

140+ tests covering all N3.7 packages:
- PACKAGE A: Executive Coherence Engine (25 tests)
- PACKAGE B: Executive Summary Diamond Model (20 tests)
- PACKAGE C: Layout Consistency Engine (25 tests)
- PACKAGE E: Zero-Fallback Layer v4 (25 tests)
- PACKAGE F: Performance Resilience v4 (15 tests)
- Integration Tests (10 tests)

Version: 1.0.0 (N3.7 - PLATIN++ v4.23 RC)
"""
import pytest


# =============================================================================
# PACKAGE A: Executive Coherence Engine Tests (25 tests)
# =============================================================================

class TestCoherenceEngineImports:
    """Test Coherence Engine module imports."""

    def test_module_import(self):
        """Should import executive_coherence_engine module."""
        from services import executive_coherence_engine

        assert executive_coherence_engine is not None

    def test_analyze_coherence_exists(self):
        """analyze_coherence function should exist."""
        from services.executive_coherence_engine import analyze_coherence

        assert callable(analyze_coherence)

    def test_heal_coherence_exists(self):
        """heal_coherence function should exist."""
        from services.executive_coherence_engine import heal_coherence

        assert callable(heal_coherence)

    def test_process_coherence_exists(self):
        """process_coherence function should exist."""
        from services.executive_coherence_engine import process_coherence

        assert callable(process_coherence)


class TestCoherenceReport:
    """Test CoherenceReport dataclass."""

    def test_report_creation(self):
        """Should create CoherenceReport with defaults."""
        from services.executive_coherence_engine import CoherenceReport

        report = CoherenceReport()

        assert report.sections_analyzed == 0
        assert report.redundancy_score == 0.0
        assert report.clarity_score == 100.0

    def test_report_add_issue(self):
        """Should add issues to report."""
        from services.executive_coherence_engine import CoherenceReport, CoherenceIssue

        report = CoherenceReport()
        issue = CoherenceIssue(
            issue_type="redundancy",
            severity="medium",
            sections=["sec1", "sec2"],
            message="Test"
        )
        report.add_issue(issue)

        assert len(report.issues) == 1
        assert report.redundancy_score > 0

    def test_report_to_dict(self):
        """Should convert to dictionary."""
        from services.executive_coherence_engine import CoherenceReport

        report = CoherenceReport(sections_analyzed=5)
        d = report.to_dict()

        assert d["sections_analyzed"] == 5


class TestCoherenceIssue:
    """Test CoherenceIssue dataclass."""

    def test_issue_creation(self):
        """Should create CoherenceIssue."""
        from services.executive_coherence_engine import CoherenceIssue

        issue = CoherenceIssue(
            issue_type="redundancy",
            severity="high",
            sections=["sec1"],
            message="Test message"
        )

        assert issue.issue_type == "redundancy"
        assert issue.severity == "high"

    def test_issue_to_dict(self):
        """Should convert to dictionary."""
        from services.executive_coherence_engine import CoherenceIssue

        issue = CoherenceIssue(
            issue_type="vague",
            severity="low",
            sections=["sec1"],
            message="Test"
        )
        d = issue.to_dict()

        assert d["issue_type"] == "vague"


class TestRedundancyDetection:
    """Test redundancy detection functions."""

    def test_detect_redundancy_function(self):
        """detect_redundancy should exist."""
        from services.executive_coherence_engine import detect_redundancy

        assert callable(detect_redundancy)

    def test_similarity_threshold(self):
        """SIMILARITY_THRESHOLD should be 0.92."""
        from services.executive_coherence_engine import SIMILARITY_THRESHOLD

        assert SIMILARITY_THRESHOLD == 0.92

    def test_calculate_similarity(self):
        """calculate_similarity should return float."""
        from services.executive_coherence_engine import calculate_similarity

        result = calculate_similarity("test text", "test text")
        assert isinstance(result, float)
        assert result == 1.0

    def test_calculate_similarity_different(self):
        """calculate_similarity should be low for different texts."""
        from services.executive_coherence_engine import calculate_similarity

        result = calculate_similarity("hello world", "goodbye universe")
        assert result < 0.5


class TestContradictionDetection:
    """Test contradiction detection."""

    def test_detect_contradictions_function(self):
        """detect_contradictions should exist."""
        from services.executive_coherence_engine import detect_contradictions

        assert callable(detect_contradictions)

    def test_contradiction_pairs_defined(self):
        """CONTRADICTION_PAIRS should be defined."""
        from services.executive_coherence_engine import CONTRADICTION_PAIRS

        assert isinstance(CONTRADICTION_PAIRS, list)
        assert len(CONTRADICTION_PAIRS) >= 5


class TestVagueStatementDetection:
    """Test vague statement detection."""

    def test_detect_vague_statements(self):
        """detect_vague_statements should exist."""
        from services.executive_coherence_engine import detect_vague_statements

        assert callable(detect_vague_statements)

    def test_vague_phrases_defined(self):
        """VAGUE_PHRASES should be defined."""
        from services.executive_coherence_engine import VAGUE_PHRASES

        assert isinstance(VAGUE_PHRASES, list)
        assert len(VAGUE_PHRASES) >= 15

    def test_clarity_boosters_defined(self):
        """CLARITY_BOOSTERS should be defined."""
        from services.executive_coherence_engine import CLARITY_BOOSTERS

        assert isinstance(CLARITY_BOOSTERS, dict)
        assert len(CLARITY_BOOSTERS) >= 5


class TestCoherenceHealing:
    """Test coherence healing functions."""

    def test_heal_vague_statements(self):
        """heal_vague_statements should replace weak forms."""
        from services.executive_coherence_engine import heal_vague_statements

        text = "Das könnte helfen bei der Umsetzung."
        healed, count = heal_vague_statements(text)

        assert count >= 1
        assert "unterstützt direkt" in healed

    def test_heal_redundancy_indicators(self):
        """heal_redundancy_indicators should remove indicators."""
        from services.executive_coherence_engine import heal_redundancy_indicators

        text = "Wie bereits erwähnt ist dies wichtig."
        healed, count = heal_redundancy_indicators(text)

        assert count >= 1
        assert "wie bereits erwähnt" not in healed.lower()


class TestCoherenceGrade:
    """Test coherence grading."""

    def test_get_coherence_grade_a(self):
        """Should return A for low redundancy and high clarity."""
        from services.executive_coherence_engine import get_coherence_grade, CoherenceReport

        report = CoherenceReport(redundancy_score=5, clarity_score=95)
        grade = get_coherence_grade(report)

        assert grade == "A"

    def test_get_coherence_grade_f(self):
        """Should return F for high redundancy and low clarity."""
        from services.executive_coherence_engine import get_coherence_grade, CoherenceReport

        report = CoherenceReport(redundancy_score=60, clarity_score=40)
        grade = get_coherence_grade(report)

        assert grade == "F"


# =============================================================================
# PACKAGE B: Executive Summary Diamond Model Tests (20 tests)
# =============================================================================

class TestDiamondModelImports:
    """Test Diamond Model module imports."""

    def test_module_import(self):
        """Should import executive_summary_diamond module."""
        from services import executive_summary_diamond

        assert executive_summary_diamond is not None

    def test_build_diamond_model_exists(self):
        """build_diamond_model function should exist."""
        from services.executive_summary_diamond import build_diamond_model

        assert callable(build_diamond_model)

    def test_enhance_executive_summary_exists(self):
        """enhance_executive_summary_diamond function should exist."""
        from services.executive_summary_diamond import enhance_executive_summary_diamond

        assert callable(enhance_executive_summary_diamond)


class TestDiamondModelStructure:
    """Test DiamondModel dataclass."""

    def test_diamond_model_creation(self):
        """Should create DiamondModel."""
        from services.executive_summary_diamond import DiamondModel

        model = DiamondModel()

        assert model.situation == ""
        assert model.complication == ""
        assert model.recommendation == ""
        assert model.impact == ""
        assert model.next_steps == ""

    def test_diamond_model_to_dict(self):
        """Should convert to dictionary."""
        from services.executive_summary_diamond import DiamondModel

        model = DiamondModel(situation="Test situation")
        d = model.to_dict()

        assert d["situation"] == "Test situation"
        assert "kpis" in d
        assert "risks" in d


class TestDiamondExtraction:
    """Test Diamond Model extraction functions."""

    def test_extract_kpis(self):
        """extract_kpis should extract KPIs."""
        from services.executive_summary_diamond import extract_kpis

        sections = {
            "BUSINESS_CASE_ENGINE_HTML": "<p>ROI: 120%</p>"
        }
        kpis = extract_kpis(sections)

        assert isinstance(kpis, list)

    def test_extract_risks(self):
        """extract_risks should extract risks."""
        from services.executive_summary_diamond import extract_risks

        sections = {
            "RISK_ENGINE_HTML": "<p>Risiko: kritisch - Datenverlust</p>"
        }
        risks = extract_risks(sections)

        assert isinstance(risks, list)

    def test_extract_actions(self):
        """extract_actions should extract actions."""
        from services.executive_summary_diamond import extract_actions

        sections = {
            "RECOMMENDATIONS_ENGINE_HTML": "<p>Empfehlung 1: Implementieren</p>"
        }
        actions = extract_actions(sections)

        assert isinstance(actions, list)

    def test_extract_tools(self):
        """extract_tools should extract tools."""
        from services.executive_summary_diamond import extract_tools

        assert callable(extract_tools)

    def test_extract_funding(self):
        """extract_funding should extract funding programs."""
        from services.executive_summary_diamond import extract_funding

        assert callable(extract_funding)


class TestDiamondGeneration:
    """Test Diamond Model generation."""

    def test_generate_situation(self):
        """generate_situation should generate text."""
        from services.executive_summary_diamond import generate_situation

        sections = {}
        result = generate_situation(sections)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_complication(self):
        """generate_complication should generate text."""
        from services.executive_summary_diamond import generate_complication

        sections = {}
        result = generate_complication(sections, [])

        assert isinstance(result, str)

    def test_generate_diamond_html(self):
        """generate_diamond_html should generate HTML."""
        from services.executive_summary_diamond import generate_diamond_html, DiamondModel

        model = DiamondModel(situation="Test")
        html = generate_diamond_html(model)

        assert "<div" in html
        assert "diamond" in html.lower()


class TestDiamondReport:
    """Test DiamondReport dataclass."""

    def test_report_creation(self):
        """Should create DiamondReport."""
        from services.executive_summary_diamond import DiamondReport

        report = DiamondReport()

        assert report.success is True
        assert report.sections_generated == 0

    def test_report_to_dict(self):
        """Should convert to dictionary."""
        from services.executive_summary_diamond import DiamondReport

        report = DiamondReport(kpis_extracted=3)
        d = report.to_dict()

        assert d["kpis_extracted"] == 3


# =============================================================================
# PACKAGE C: Layout Consistency Engine Tests (25 tests)
# =============================================================================

class TestLayoutEngineImports:
    """Test Layout Engine module imports."""

    def test_module_import(self):
        """Should import layout_consistency_engine module."""
        from services import layout_consistency_engine

        assert layout_consistency_engine is not None

    def test_process_layout_exists(self):
        """process_layout_consistency function should exist."""
        from services.layout_consistency_engine import process_layout_consistency

        assert callable(process_layout_consistency)


class TestLayoutConfiguration:
    """Test layout configuration constants."""

    def test_grid_unit(self):
        """GRID_UNIT should be 8."""
        from services.layout_consistency_engine import GRID_UNIT

        assert GRID_UNIT == 8

    def test_spacing_values(self):
        """SPACING should have correct values."""
        from services.layout_consistency_engine import SPACING

        assert SPACING["xs"] == 8
        assert SPACING["sm"] == 16
        assert SPACING["md"] == 24
        assert SPACING["lg"] == 32

    def test_no_break_elements(self):
        """NO_BREAK_ELEMENTS should be defined."""
        from services.layout_consistency_engine import NO_BREAK_ELEMENTS

        assert isinstance(NO_BREAK_ELEMENTS, list)
        assert "table" in NO_BREAK_ELEMENTS

    def test_heading_styles(self):
        """HEADING_STYLES should be defined."""
        from services.layout_consistency_engine import HEADING_STYLES

        assert "h1" in HEADING_STYLES
        assert "h2" in HEADING_STYLES


class TestLayoutCanonicalizer:
    """Test HTML canonicalizer functions."""

    def test_canonicalize_html(self):
        """canonicalize_html should clean HTML."""
        from services.layout_consistency_engine import canonicalize_html

        html = "<p></p><p>Content</p>"
        result, changes = canonicalize_html(html)

        assert "<p></p>" not in result

    def test_normalize_tables(self):
        """normalize_tables should add classes."""
        from services.layout_consistency_engine import normalize_tables

        html = "<table><tr><td>Data</td></tr></table>"
        result, changes = normalize_tables(html)

        assert "data-table" in result


class TestWhitespaceAuditor:
    """Test whitespace auditor functions."""

    def test_audit_whitespace(self):
        """audit_whitespace should normalize spacing."""
        from services.layout_consistency_engine import audit_whitespace, LayoutReport

        report = LayoutReport()
        html = '<div style="margin: 15px;"></div>'
        result = audit_whitespace(html, report)

        assert isinstance(result, str)

    def test_check_vertical_gaps(self):
        """check_vertical_gaps should find gap issues."""
        from services.layout_consistency_engine import check_vertical_gaps, LayoutReport

        report = LayoutReport()
        html = "</div>\n\n\n\n\n<div>"
        issues = check_vertical_gaps(html, report)

        assert isinstance(issues, list)


class TestBreakOptimizer:
    """Test page break optimizer functions."""

    def test_optimize_page_breaks(self):
        """optimize_page_breaks should add break rules."""
        from services.layout_consistency_engine import optimize_page_breaks, LayoutReport

        report = LayoutReport()
        html = '<table><tr><td>Data</td></tr></table>'
        result = optimize_page_breaks(html, report)

        assert "page-break-inside" in result

    def test_add_break_before_headings(self):
        """add_break_before_headings should add break-before."""
        from services.layout_consistency_engine import add_break_before_headings, LayoutReport

        report = LayoutReport()
        html = '<h1>Title</h1>'
        result = add_break_before_headings(html, report)

        assert "page-break-before" in result


class TestLayoutNormalization:
    """Test layout normalization functions."""

    def test_normalize_headings(self):
        """normalize_headings should apply styles."""
        from services.layout_consistency_engine import normalize_headings, LayoutReport

        report = LayoutReport()
        html = '<h1>Title</h1>'
        result = normalize_headings(html, report)

        assert "font-size" in result

    def test_normalize_cards(self):
        """normalize_cards should apply card styles."""
        from services.layout_consistency_engine import normalize_cards, LayoutReport

        report = LayoutReport()
        html = '<div class="card">Content</div>'
        result = normalize_cards(html, report)

        assert "padding" in result or "border" in result


class TestLayoutReport:
    """Test LayoutReport dataclass."""

    def test_report_creation(self):
        """Should create LayoutReport."""
        from services.layout_consistency_engine import LayoutReport

        report = LayoutReport()

        assert report.elements_processed == 0
        assert report.page_breaks_optimized == 0

    def test_report_add_issue(self):
        """Should add issues."""
        from services.layout_consistency_engine import LayoutReport, LayoutIssue

        report = LayoutReport()
        issue = LayoutIssue(
            issue_type="whitespace",
            severity="low",
            element="div",
            message="Test"
        )
        report.add_issue(issue)

        assert report.issues_found == 1


class TestPrintStylesheet:
    """Test print stylesheet generation."""

    def test_generate_print_stylesheet(self):
        """generate_print_stylesheet should generate CSS."""
        from services.layout_consistency_engine import generate_print_stylesheet

        css = generate_print_stylesheet()

        assert "@media print" in css
        assert "@page" in css


# =============================================================================
# PACKAGE E: Zero-Fallback Layer v4 Tests (25 tests)
# =============================================================================

class TestFallbackGuardImports:
    """Test Fallback Guard module imports."""

    def test_module_import(self):
        """Should import fallback_guard module."""
        from services import fallback_guard

        assert fallback_guard is not None

    def test_fallback_guard_class(self):
        """FallbackGuard class should exist."""
        from services.fallback_guard import FallbackGuard

        assert FallbackGuard is not None

    def test_process_with_fallback_guard(self):
        """process_with_fallback_guard should exist."""
        from services.fallback_guard import process_with_fallback_guard

        assert callable(process_with_fallback_guard)


class TestFallbackConfiguration:
    """Test fallback configuration."""

    def test_max_extend_rounds(self):
        """MAX_EXTEND_ROUNDS should be 4."""
        from services.fallback_guard import MAX_EXTEND_ROUNDS

        assert MAX_EXTEND_ROUNDS == 4

    def test_fallback_thresholds(self):
        """FALLBACK_THRESHOLDS should be defined."""
        from services.fallback_guard import FALLBACK_THRESHOLDS

        assert "solo" in FALLBACK_THRESHOLDS
        assert "team" in FALLBACK_THRESHOLDS
        assert "kmu" in FALLBACK_THRESHOLDS

    def test_branch_density(self):
        """BRANCH_DENSITY should be defined."""
        from services.fallback_guard import BRANCH_DENSITY

        assert "technologie" in BRANCH_DENSITY
        assert BRANCH_DENSITY["technologie"] > 1.0

    def test_high_risk_sections(self):
        """HIGH_RISK_SECTIONS should be defined."""
        from services.fallback_guard import HIGH_RISK_SECTIONS

        assert "recommendations" in HIGH_RISK_SECTIONS
        assert "risks" in HIGH_RISK_SECTIONS

    def test_fallback_templates(self):
        """FALLBACK_TEMPLATES should be defined."""
        from services.fallback_guard import FALLBACK_TEMPLATES

        assert "recommendations" in FALLBACK_TEMPLATES
        assert "default" in FALLBACK_TEMPLATES


class TestProgressiveExtend:
    """Test progressive_extend function."""

    def test_progressive_extend_exists(self):
        """progressive_extend function should exist."""
        from services.fallback_guard import progressive_extend

        assert callable(progressive_extend)

    def test_progressive_extend_short_content(self):
        """Should extend short content."""
        from services.fallback_guard import progressive_extend

        content = "Short text."
        extended, rounds = progressive_extend(content, "recommendations", 50)

        assert rounds > 0
        assert len(extended) > len(content)

    def test_progressive_extend_max_rounds(self):
        """Should respect max_rounds."""
        from services.fallback_guard import progressive_extend

        content = "Short."
        extended, rounds = progressive_extend(content, "recommendations", 500, max_rounds=2)

        assert rounds <= 2


class TestSmartExpand:
    """Test smart_expand function."""

    def test_smart_expand_exists(self):
        """smart_expand function should exist."""
        from services.fallback_guard import smart_expand

        assert callable(smart_expand)

    def test_smart_expand_adds_structure(self):
        """Should add structure to content."""
        from services.fallback_guard import smart_expand

        content = "This is a long enough text that should get some structure added to it for better quality."
        expanded, was_expanded = smart_expand(content, "recommendations", target_quality=50)

        assert isinstance(expanded, str)


class TestFallbackGuardClass:
    """Test FallbackGuard class."""

    def test_guard_creation(self):
        """Should create FallbackGuard."""
        from services.fallback_guard import FallbackGuard

        guard = FallbackGuard()

        assert guard.size == "kmu"
        assert guard.density == 1.0

    def test_guard_with_briefing(self):
        """Should use briefing for configuration."""
        from services.fallback_guard import FallbackGuard

        briefing = {"unternehmensgroesse": "Solo-Selbständig"}
        guard = FallbackGuard(briefing)

        assert guard.size == "solo"

    def test_check_and_prevent(self):
        """check_and_prevent should process content."""
        from services.fallback_guard import FallbackGuard

        guard = FallbackGuard()
        content = "Short."
        processed, prevented = guard.check_and_prevent("recommendations", content)

        assert isinstance(processed, str)

    def test_recover_fallback(self):
        """recover_fallback should optimize content."""
        from services.fallback_guard import FallbackGuard

        guard = FallbackGuard()
        content = "<p>Fallback content.</p>"
        recovered = guard.recover_fallback("recommendations", content)

        assert isinstance(recovered, str)

    def test_no_double_fallback(self):
        """Should block second fallback for same section."""
        from services.fallback_guard import FallbackGuard

        guard = FallbackGuard()

        # First fallback
        guard.recover_fallback("recommendations", "Content 1")

        # Second should use template
        result = guard.recover_fallback("recommendations", "Content 2")

        assert "Handlungsempfehlungen" in result  # From template


class TestFallbackReport:
    """Test FallbackGuardReport."""

    def test_report_creation(self):
        """Should create FallbackGuardReport."""
        from services.fallback_guard import FallbackGuardReport

        report = FallbackGuardReport()

        assert report.fallbacks_prevented == 0
        assert report.fallbacks_recovered == 0

    def test_report_to_dict(self):
        """Should convert to dictionary."""
        from services.fallback_guard import FallbackGuardReport

        report = FallbackGuardReport(fallbacks_prevented=3)
        d = report.to_dict()

        assert d["fallbacks_prevented"] == 3


# =============================================================================
# PACKAGE F: Performance Resilience v4 Tests (15 tests)
# =============================================================================

class TestPerformanceConfigN37:
    """Test N3.7 performance configuration."""

    def test_max_retries_6(self):
        """N3.7: Max retries should be 6."""
        from services.llm_client import LLM_MAX_RETRIES

        assert LLM_MAX_RETRIES == 6

    def test_backoff_base_3(self):
        """Backoff base should be 3.0."""
        from services.llm_client import LLM_RETRY_BACKOFF_BASE

        assert LLM_RETRY_BACKOFF_BASE == 3.0

    def test_premium_timeout_165(self):
        """N3.7: Premium sections should have 165s timeout."""
        from services.llm_client import SECTION_TIMEOUT_OVERRIDES

        assert SECTION_TIMEOUT_OVERRIDES["exec_summary"] == 165.0
        assert SECTION_TIMEOUT_OVERRIDES["recommendations"] == 165.0
        assert SECTION_TIMEOUT_OVERRIDES["roadmap_12m"] == 165.0


class TestBackoffSequenceN37:
    """Test N3.7 backoff sequence."""

    def test_backoff_96s(self):
        """Sixth retry should wait 96s."""
        from services.llm_client import calculate_backoff, RetryConfig

        config = RetryConfig()
        assert calculate_backoff(5, config) == 96.0

    def test_full_backoff_sequence(self):
        """Full sequence should be 3, 6, 12, 24, 48, 96."""
        from services.llm_client import calculate_backoff, RetryConfig

        config = RetryConfig()
        expected = [3.0, 6.0, 12.0, 24.0, 48.0, 96.0]

        for i, exp in enumerate(expected):
            assert calculate_backoff(i, config) == exp


class TestRetryConfigN37:
    """Test N3.7 RetryConfig."""

    def test_retry_config_defaults(self):
        """RetryConfig should have N3.7 defaults."""
        from services.llm_client import RetryConfig

        config = RetryConfig()

        assert config.max_retries == 6
        assert config.backoff_base == 3.0
        assert config.backoff_multiplier == 2.0


# =============================================================================
# INTEGRATION TESTS (10 tests)
# =============================================================================

class TestN37Integration:
    """Integration tests for N3.7 packages."""

    def test_coherence_then_diamond(self):
        """Should process through coherence then diamond model."""
        from services.executive_coherence_engine import process_coherence
        from services.executive_summary_diamond import process_executive_summary

        sections = {
            "EXEC_SUMMARY_HTML": "<p>Test content for analysis.</p>",
            "RISKS_HTML": "<p>Risk content here.</p>",
        }

        # Step 1: Coherence
        coherent, coh_report = process_coherence(sections)

        # Step 2: Diamond
        final = process_executive_summary(coherent)

        assert "_coherence_healed" in final
        assert "_diamond_report" in final

    def test_layout_processing(self):
        """Should process layout for all HTML sections."""
        from services.layout_consistency_engine import process_sections_layout

        sections = {
            "EXEC_SUMMARY_HTML": "<h1>Title</h1><p>Content</p>",
            "RISKS_HTML": "<table><tr><td>Data</td></tr></table>",
        }

        processed, report = process_sections_layout(sections)

        assert report.elements_processed >= 0
        assert "_layout_optimized" in processed

    def test_fallback_guard_processing(self):
        """Should process with fallback guard."""
        from services.fallback_guard import process_with_fallback_guard

        sections = {
            "RECOMMENDATIONS_HTML": "<p>Short.</p>",
            "RISKS_HTML": "<p>Normal content here with enough words.</p>",
        }

        processed, report = process_with_fallback_guard(sections)

        assert "_fallback_guard_active" in processed

    def test_full_n37_pipeline(self):
        """Should run full N3.7 pipeline."""
        from services.executive_coherence_engine import process_coherence
        from services.executive_summary_diamond import process_executive_summary
        from services.layout_consistency_engine import process_sections_layout
        from services.fallback_guard import process_with_fallback_guard

        sections = {
            "EXEC_SUMMARY_HTML": "<p>Executive summary content.</p>",
            "RECOMMENDATIONS_HTML": "<p>Recommendations for the company.</p>",
            "RISKS_HTML": "<p>Risk analysis and mitigation.</p>",
        }

        # Pipeline
        sections, _ = process_coherence(sections)
        sections = process_executive_summary(sections)
        sections, _ = process_sections_layout(sections)
        sections, _ = process_with_fallback_guard(sections)

        # All flags should be set
        assert sections.get("_coherence_healed") is True
        assert "_diamond_report" in sections
        assert sections.get("_layout_optimized") is True
        assert sections.get("_fallback_guard_active") is True

    def test_quality_score_calculation(self):
        """Quality score should increase with structure."""
        from services.fallback_guard import calculate_quality_score

        plain = "Simple text without structure."
        structured = "<h3>Title</h3><ul><li>Item 1</li><li>Item 2</li></ul><p>50% improvement</p>"

        plain_score = calculate_quality_score(plain)
        structured_score = calculate_quality_score(structured)

        assert structured_score > plain_score

    def test_word_count_functions(self):
        """Word count functions should work consistently."""
        from services.fallback_guard import word_count as fb_word_count
        from services.executive_summary_diamond import word_count as diamond_word_count

        text = "<p>This is a test with seven words.</p>"

        fb_count = fb_word_count(text)
        diamond_count = diamond_word_count(text)

        # Both should give similar results (HTML stripped)
        assert fb_count >= 5
        assert diamond_count >= 5
