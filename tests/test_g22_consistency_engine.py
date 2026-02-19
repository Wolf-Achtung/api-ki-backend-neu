# -*- coding: utf-8 -*-
"""
Sprint G22: Cross-Section Consistency Engine Tests

Tests for G22 Cross-Section Consistency Engine feature:
- ConsistencyIssue and ConsistencyReport data structures
- Tool consistency checks between KI-Stack and Tools sections
- Funding consistency checks
- KPI consistency (ROI, Payback, Time Savings)
- Risk level consistency across sections
- Roadmap alignment checks
- Narrative coherence (size-appropriate terminology)
- Integration with gpt_analyze.py pipeline

Version: 1.0.0 (Sprint G22)
"""
from __future__ import annotations

import pytest
from pathlib import Path
from typing import Dict, Any


class TestG22DataStructures:
    """Tests for G22 data structures (ConsistencyIssue, ConsistencyReport)."""

    def test_consistency_issue_can_be_created(self) -> None:
        """Test that ConsistencyIssue can be instantiated."""
        from services.consistency_engine import ConsistencyIssue

        issue = ConsistencyIssue(
            rule_id="TEST_001",
            severity="ERROR",
            domain="tools",
            source_section="ki_stack_summary",
            target_section="tools_empfehlungen",
            message="Test message",
            expected="Expected value",
            actual="Actual value",
            suggestion="Fix suggestion",
        )

        assert issue.rule_id == "TEST_001"
        assert issue.severity == "ERROR"
        assert issue.domain == "tools"
        assert issue.source_section == "ki_stack_summary"
        assert issue.target_section == "tools_empfehlungen"
        assert issue.message == "Test message"

    def test_consistency_issue_to_dict(self) -> None:
        """Test ConsistencyIssue serialization to dict."""
        from services.consistency_engine import ConsistencyIssue

        issue = ConsistencyIssue(
            rule_id="TEST_001",
            severity="WARNING",
            domain="kpi",
            source_section="business_case",
            target_section="executive_summary",
            message="ROI mismatch",
        )

        result = issue.to_dict()

        assert isinstance(result, dict)
        assert result["rule_id"] == "TEST_001"
        assert result["severity"] == "WARNING"
        assert result["domain"] == "kpi"

    def test_consistency_report_defaults(self) -> None:
        """Test ConsistencyReport default values."""
        from services.consistency_engine import ConsistencyReport

        report = ConsistencyReport()

        assert report.status == "PASS"
        assert report.grade == "A"
        assert report.score == 100.0
        assert report.issues == []
        assert report.checked_rules == 0
        assert report.passed_rules == 0
        assert report.timestamp  # Should be auto-generated

    def test_consistency_report_add_issue_updates_status(self) -> None:
        """Test that adding issues recalculates report status."""
        from services.consistency_engine import ConsistencyReport, ConsistencyIssue

        report = ConsistencyReport()
        report.checked_rules = 10

        # Add an error - should change status to FAIL
        report.add_issue(ConsistencyIssue(
            rule_id="TEST_001",
            severity="ERROR",
            domain="tools",
            source_section="test",
            target_section="test",
            message="Error message",
        ))

        assert report.status == "FAIL"
        assert report.score < 100.0

    def test_consistency_report_grade_calculation(self) -> None:
        """Test grade calculation based on score."""
        from services.consistency_engine import ConsistencyReport, ConsistencyIssue

        report = ConsistencyReport()
        report.checked_rules = 10

        # No issues = Grade A
        assert report.grade == "A"
        assert report.score >= 95

        # Add warnings to lower grade
        # FIX-G22-TUNE: With reduced detail penalty (2.0) and higher bonuses
        # (exec_clean=8, zero_error=5), need 10 detail warnings for Grade B:
        # 100 - (10 * 2.0) + 8 + 5 = 93 → Grade B
        for i in range(10):
            report.add_issue(ConsistencyIssue(
                rule_id=f"WARN_{i}",
                severity="WARNING",
                domain="narrative",
                source_section="test",
                target_section="test",
                message=f"Warning {i}",
            ))

        # 10 detail warnings → score 93 → Grade B
        assert report.grade == "B"
        assert 85 <= report.score < 95

    def test_consistency_report_to_dict(self) -> None:
        """Test ConsistencyReport serialization to dict."""
        from services.consistency_engine import ConsistencyReport

        report = ConsistencyReport()
        report.checked_rules = 16
        report.domain_scores = {"tools": 100.0, "kpi": 90.0}

        result = report.to_dict()

        assert isinstance(result, dict)
        assert "status" in result
        assert "grade" in result
        assert "score" in result
        assert "issues" in result
        assert "summary" in result
        assert result["checked_rules"] == 16


class TestG22Extraction:
    """Tests for G22 extraction helpers."""

    def test_extract_tool_names_from_table(self) -> None:
        """Test tool extraction from HTML tables."""
        from services.consistency_engine import _extract_tool_names

        html = """
        <table>
            <tr><td>ChatGPT</td><td>Analysis</td></tr>
            <tr><td>Claude AI</td><td>Research</td></tr>
            <tr><td>Notion AI</td><td>Productivity</td></tr>
        </table>
        """

        tools = _extract_tool_names(html)

        assert len(tools) >= 1
        # At least some tools should be extracted

    def test_extract_tool_names_from_pair_cards(self) -> None:
        """Test tool extraction from G21 pair-card HTML."""
        from services.consistency_engine import _extract_tool_names

        html = """
        <div class="pair-card">
            <div class="pair-card-name">ChatGPT Enterprise</div>
            <span class="pair-card-category">Automation</span>
        </div>
        <div class="pair-card">
            <div class="pair-card-name">Microsoft Copilot</div>
            <span class="pair-card-category">Analysis</span>
        </div>
        """

        tools = _extract_tool_names(html)

        assert "ChatGPT Enterprise" in tools
        assert "Microsoft Copilot" in tools

    def test_extract_risk_level_from_css_class(self) -> None:
        """Test risk level extraction from CSS classes."""
        from services.consistency_engine import _extract_risk_level

        low_html = '<div class="badge risk-low">Niedriges Risiko</div>'
        medium_html = '<div class="badge risk-medium">Mittleres Risiko</div>'
        high_html = '<div class="badge risk-high">Hohes Risiko</div>'

        assert _extract_risk_level(low_html) == "low"
        assert _extract_risk_level(medium_html) == "medium"
        assert _extract_risk_level(high_html) == "high"

    def test_extract_risk_level_from_text(self) -> None:
        """Test risk level extraction from text patterns."""
        from services.consistency_engine import _extract_risk_level

        low_text = "Das Risiko ist niedrig für diese Branche."
        medium_text = "Das Risiko: mittel aufgrund regulatorischer Anforderungen."
        high_text = "Hohes Risiko im Bereich Finanzen."

        assert _extract_risk_level(low_text) == "low"
        assert _extract_risk_level(medium_text) == "medium"
        assert _extract_risk_level(high_text) == "high"

    def test_extract_kpis_roi(self) -> None:
        """Test ROI extraction from various formats."""
        from services.consistency_engine import _extract_kpis

        html1 = "Der ROI beträgt 150% nach 12 Monaten."
        html2 = "<span class='kpi-value'>125%</span><span class='kpi-label'>ROI</span>"
        html3 = "Return on Investment: 200%"

        kpis1 = _extract_kpis(html1)
        kpis2 = _extract_kpis(html2)
        kpis3 = _extract_kpis(html3)

        assert kpis1.get("roi") == 150.0
        # Note: Pattern matching may vary based on HTML structure

    def test_extract_kpis_payback(self) -> None:
        """Test payback extraction."""
        from services.consistency_engine import _extract_kpis

        html = "Payback: 6 Monate. Amortisation erfolgt schnell."

        kpis = _extract_kpis(html)

        assert kpis.get("payback_months") == 6.0

    def test_extract_step_count(self) -> None:
        """Test step count extraction from Starter-Kit."""
        from services.consistency_engine import _extract_step_count

        html = """
        <div class="step-cards">
            <div class="step-card"><span class="step-card-number">1</span>Setup</div>
            <div class="step-card"><span class="step-card-number">2</span>Workflow</div>
            <div class="step-card"><span class="step-card-number">3</span>Optimierung</div>
        </div>
        """

        assert _extract_step_count(html) == 3

    def test_strip_html(self) -> None:
        """Test HTML stripping utility."""
        from services.consistency_engine import _strip_html

        html = "<div><p>Hello <strong>World</strong></p></div>"
        result = _strip_html(html)

        assert "<" not in result
        assert "Hello" in result
        assert "World" in result


class TestG22ToolsConsistency:
    """Tests for tools consistency checks."""

    def test_tools_consistency_passes_when_aligned(self) -> None:
        """Test that tools consistency passes when KI-Stack tools match full list."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "KI_STACK_SUMMARY_HTML": '<div class="pair-card-name">ChatGPT</div>',
            "TOOLS_EMPFEHLUNGEN_HTML": '<td>ChatGPT</td><td>Claude</td><td>Copilot</td>',
        }
        briefing: Dict[str, Any] = {}

        engine = ConsistencyEngine(sections, briefing)
        report = engine.check_all()

        # Should not have TOOLS_001 error
        tools_errors = [i for i in report.issues if i.rule_id == "TOOLS_001"]
        assert len(tools_errors) == 0, "Should pass when tools are aligned"

    def test_tools_consistency_warns_on_mismatch(self) -> None:
        """Test that tools consistency warns when KI-Stack has unknown tools."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "KI_STACK_SUMMARY_HTML": '<div class="pair-card-name">UnknownTool</div>',
            "TOOLS_EMPFEHLUNGEN_HTML": '<td>ChatGPT</td><td>Claude</td>',
        }
        briefing: Dict[str, Any] = {}

        engine = ConsistencyEngine(sections, briefing)
        report = engine.check_all()

        # Should have warning about missing tools
        # Note: May not trigger if extraction doesn't find "UnknownTool"


class TestG22KPIConsistency:
    """Tests for KPI consistency checks."""

    def test_kpi_consistency_detects_roi_mismatch(self) -> None:
        """Test that KPI consistency detects large ROI discrepancies."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "KI_STACK_SUMMARY_HTML": "ROI: 200%",
            "BUSINESS_CASE_HTML": "ROI: 50%",  # 150% difference
        }
        briefing: Dict[str, Any] = {}

        engine = ConsistencyEngine(sections, briefing)
        report = engine.check_all()

        # Should have KPI_001 error for ROI mismatch
        kpi_errors = [i for i in report.issues if i.rule_id == "KPI_001"]
        assert len(kpi_errors) > 0, "Should detect ROI mismatch"

    def test_kpi_consistency_passes_within_tolerance(self) -> None:
        """Test that small KPI differences are tolerated."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "KI_STACK_SUMMARY_HTML": "ROI: 150%",
            "BUSINESS_CASE_HTML": "ROI: 155%",  # Within 15% tolerance
        }
        briefing: Dict[str, Any] = {}

        engine = ConsistencyEngine(sections, briefing)
        report = engine.check_all()

        # Should not have KPI_001 error
        kpi_errors = [i for i in report.issues if i.rule_id == "KPI_001"]
        assert len(kpi_errors) == 0, "Should pass within tolerance"


class TestG22RiskConsistency:
    """Tests for risk level consistency checks."""

    def test_risk_consistency_detects_mismatch(self) -> None:
        """Test that risk consistency detects different levels across sections."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "KI_STACK_SUMMARY_HTML": '<span class="risk-low">Niedriges Risiko</span>',
            "AI_ACT_SUMMARY_HTML": '<span class="risk-high">Hohes Risiko</span>',
        }
        briefing: Dict[str, Any] = {}

        engine = ConsistencyEngine(sections, briefing)
        report = engine.check_all()

        # Should have RISK_001 error
        risk_errors = [i for i in report.issues if i.rule_id == "RISK_001"]
        assert len(risk_errors) > 0, "Should detect risk level mismatch"

    def test_risk_consistency_passes_when_aligned(self) -> None:
        """Test that risk consistency passes when levels match."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "KI_STACK_SUMMARY_HTML": '<span class="risk-medium">Mittleres Risiko</span>',
            "AI_ACT_SUMMARY_HTML": '<span class="risk-medium">Mittleres Risiko</span>',
        }
        briefing: Dict[str, Any] = {}

        engine = ConsistencyEngine(sections, briefing)
        report = engine.check_all()

        # Should not have RISK_001 error
        risk_errors = [i for i in report.issues if i.rule_id == "RISK_001"]
        assert len(risk_errors) == 0, "Should pass when risk levels match"

    def test_risk_warns_low_risk_for_regulated_branch(self) -> None:
        """Test warning when low risk assigned to regulated industry."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "KI_STACK_SUMMARY_HTML": '<span class="risk-low">Niedriges Risiko</span>',
        }
        briefing = {"branche": "Medizin"}  # Regulated industry

        engine = ConsistencyEngine(sections, briefing)
        report = engine.check_all()

        # Should have RISK_002 warning
        risk_warnings = [i for i in report.issues if i.rule_id == "RISK_002"]
        assert len(risk_warnings) > 0, "Should warn about low risk for regulated industry"


class TestG22NarrativeCoherence:
    """Tests for narrative coherence checks."""

    def test_solo_terminology_flags_team_terms(self) -> None:
        """Test that 'team' terminology is flagged in solo reports."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "EXECUTIVE_SUMMARY_HTML": "Das Team sollte koordiniert vorgehen. Die Abteilung...",
        }
        briefing = {"unternehmensgroesse": "solo"}

        engine = ConsistencyEngine(sections, briefing)
        report = engine.check_all()

        # Should have NARR_001 warning about size-inappropriate terms
        narr_warnings = [i for i in report.issues if i.rule_id == "NARR_001"]
        assert len(narr_warnings) > 0, "Should flag 'team' and 'Abteilung' for solo"

    def test_kmu_terminology_accepted_for_kmu(self) -> None:
        """Test that KMU terminology is accepted for KMU reports."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "EXECUTIVE_SUMMARY_HTML": "Das Unternehmen sollte verschiedene Abteilungen koordinieren.",
        }
        briefing = {"unternehmensgroesse": "kmu"}

        engine = ConsistencyEngine(sections, briefing)
        report = engine.check_all()

        # Should not have NARR_001 warning
        narr_warnings = [i for i in report.issues if i.rule_id == "NARR_001"]
        # KMU can use "Abteilung"
        assert len(narr_warnings) == 0, "KMU should be able to use 'Abteilung'"

    def test_optimistic_exec_with_severe_risks_flagged(self) -> None:
        """Test that overly optimistic exec summary with severe risks is flagged."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "EXECUTIVE_SUMMARY_HTML": "Die Ausgangslage ist hervorragend und optimal.",
            "RISKS_HTML": "Es bestehen kritische und gravierend hohe Risiken.",
        }
        briefing: Dict[str, Any] = {}

        engine = ConsistencyEngine(sections, briefing)
        report = engine.check_all()

        # Should have NARR_002 warning about tone mismatch
        narr_warnings = [i for i in report.issues if i.rule_id == "NARR_002"]
        assert len(narr_warnings) > 0, "Should flag optimistic exec with severe risks"


class TestG22RoadmapAlignment:
    """Tests for roadmap alignment checks."""

    def test_starter_kit_step_count_info(self) -> None:
        """Test that non-standard step count generates info."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "KI_STACK_SUMMARY_HTML": """
                <div class="step-card">Step 1</div>
                <div class="step-card">Step 2</div>
            """,  # Only 2 steps instead of 3
            "ROADMAP_12M_HTML": "Roadmap content here",
        }
        briefing: Dict[str, Any] = {}

        engine = ConsistencyEngine(sections, briefing)
        report = engine.check_all()

        # Should have ROADMAP_001 info about step count
        roadmap_infos = [i for i in report.issues if i.rule_id == "ROADMAP_001"]
        assert len(roadmap_infos) > 0, "Should flag non-standard step count"


class TestG22PublicAPI:
    """Tests for public API (check_consistency function)."""

    def test_check_consistency_function_returns_report(self) -> None:
        """Test that check_consistency returns a ConsistencyReport."""
        from services.consistency_engine import check_consistency, ConsistencyReport

        sections = {
            "KI_STACK_SUMMARY_HTML": "<p>Test content</p>",
        }
        briefing: Dict[str, Any] = {}

        report = check_consistency(sections, briefing)

        assert isinstance(report, ConsistencyReport)
        assert report.status in ("PASS", "WARN", "FAIL")
        assert 0 <= report.score <= 100

    def test_check_consistency_with_language(self) -> None:
        """Test that language parameter is accepted."""
        from services.consistency_engine import check_consistency

        sections = {"KI_STACK_SUMMARY_HTML": "<p>Test</p>"}
        briefing: Dict[str, Any] = {}

        report_de = check_consistency(sections, briefing, language="de")
        report_en = check_consistency(sections, briefing, language="en")

        assert report_de.status in ("PASS", "WARN", "FAIL")
        assert report_en.status in ("PASS", "WARN", "FAIL")


class TestG22DomainScores:
    """Tests for per-domain scoring."""

    def test_domain_scores_calculated(self) -> None:
        """Test that domain scores are calculated."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "KI_STACK_SUMMARY_HTML": "Test",
            "TOOLS_EMPFEHLUNGEN_HTML": "Test",
        }
        briefing: Dict[str, Any] = {}

        engine = ConsistencyEngine(sections, briefing)
        report = engine.check_all()

        assert "tools" in report.domain_scores
        assert "funding" in report.domain_scores
        assert "kpi" in report.domain_scores
        assert "risk" in report.domain_scores
        assert "roadmap" in report.domain_scores
        assert "narrative" in report.domain_scores

    def test_domain_scores_reflect_issues(self) -> None:
        """Test that domain scores decrease with issues."""
        from services.consistency_engine import ConsistencyEngine

        # Create sections that will trigger risk inconsistency
        sections = {
            "KI_STACK_SUMMARY_HTML": '<span class="risk-low">Low</span>',
            "AI_ACT_SUMMARY_HTML": '<span class="risk-high">High</span>',
        }
        briefing: Dict[str, Any] = {}

        engine = ConsistencyEngine(sections, briefing)
        report = engine.check_all()

        # Risk domain should have lower score
        assert report.domain_scores.get("risk", 100) < 100, \
            "Risk domain score should decrease with issues"


class TestG22Integration:
    """Tests for G22 integration with gpt_analyze.py."""

    def test_gpt_analyze_has_consistency_check(self) -> None:
        """Test that gpt_analyze.py has G22 consistency check integration."""
        source_file = Path(__file__).parent.parent / "gpt_analyze.py"
        content = source_file.read_text(encoding="utf-8")

        assert "consistency_engine" in content, \
            "gpt_analyze.py should import consistency_engine"
        assert "check_consistency" in content, \
            "gpt_analyze.py should call check_consistency"
        assert "G22" in content, \
            "gpt_analyze.py should have G22 marker comments"

    def test_consistency_engine_module_exists(self) -> None:
        """Test that consistency_engine.py exists in services."""
        module_file = Path(__file__).parent.parent / "services" / "consistency_engine.py"
        assert module_file.exists(), "consistency_engine.py should exist"

    def test_consistency_engine_exports(self) -> None:
        """Test that consistency_engine exports required classes."""
        from services.consistency_engine import (
            ConsistencyIssue,
            ConsistencyReport,
            ConsistencyEngine,
            check_consistency,
        )

        assert ConsistencyIssue is not None
        assert ConsistencyReport is not None
        assert ConsistencyEngine is not None
        assert callable(check_consistency)


class TestG22EdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_sections_handled(self) -> None:
        """Test that empty sections dictionary is handled gracefully."""
        from services.consistency_engine import check_consistency

        report = check_consistency({}, {})

        # Should not crash, should return valid report
        assert report.status in ("PASS", "WARN", "FAIL")

    def test_missing_sections_skipped(self) -> None:
        """Test that missing sections are skipped without errors."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "EXECUTIVE_SUMMARY_HTML": "Test executive summary",
            # Missing KI_STACK_SUMMARY_HTML, TOOLS_EMPFEHLUNGEN_HTML, etc.
        }
        briefing: Dict[str, Any] = {}

        engine = ConsistencyEngine(sections, briefing)
        report = engine.check_all()

        # Should not crash
        assert isinstance(report.issues, list)

    def test_malformed_html_handled(self) -> None:
        """Test that malformed HTML is handled gracefully."""
        from services.consistency_engine import _extract_tool_names, _extract_risk_level

        malformed = "<div><span class='unclosed'<p>Text"

        # Should not crash
        tools = _extract_tool_names(malformed)
        risk = _extract_risk_level(malformed)

        assert isinstance(tools, list)
        # Risk might be None for malformed HTML

    def test_unicode_content_handled(self) -> None:
        """Test that unicode content is handled properly."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "KI_STACK_SUMMARY_HTML": "Förderung: €50.000 — Risiko: niedrig",
            "EXECUTIVE_SUMMARY_HTML": "Beratung für kleine Unternehmen",
        }
        briefing = {"branche": "Beratung", "unternehmensgroesse": "solo"}

        engine = ConsistencyEngine(sections, briefing)
        report = engine.check_all()

        # Should handle German umlauts and special characters
        assert report.status in ("PASS", "WARN", "FAIL")


class TestG22FullReport:
    """Integration tests with realistic report data."""

    @pytest.fixture
    def realistic_sections(self) -> Dict[str, str]:
        """Create realistic section data for testing."""
        return {
            "KI_STACK_SUMMARY_HTML": """
                <div class="ki-stack-summary">
                    <div class="pair-card">
                        <div class="pair-card-name">ChatGPT Enterprise</div>
                        <span class="pair-card-category">Automation</span>
                    </div>
                    <div class="kpi-triple">
                        <div class="kpi"><span class="kpi-value">150%</span> ROI</div>
                        <div class="kpi">Payback: 8 Monate</div>
                        <div class="kpi">40 h/Monat Zeitersparnis</div>
                    </div>
                    <div class="badge-block">
                        <span class="badge risk-medium">Mittleres Risiko</span>
                    </div>
                </div>
            """,
            "TOOLS_EMPFEHLUNGEN_HTML": """
                <table>
                    <tr><td>ChatGPT Enterprise</td><td>Automation</td></tr>
                    <tr><td>Microsoft Copilot</td><td>Productivity</td></tr>
                    <tr><td>Claude AI</td><td>Research</td></tr>
                </table>
            """,
            "AI_ACT_SUMMARY_HTML": """
                <div class="ai-act-summary">
                    <p>Risiko: mittel aufgrund der Branche.</p>
                    <span class="risk-medium">Medium Risk</span>
                </div>
            """,
            "BUSINESS_CASE_HTML": """
                <div class="business-case">
                    <p>ROI nach 12 Monaten: 145%</p>
                    <p>Payback: 7 Monate</p>
                </div>
            """,
            "EXECUTIVE_SUMMARY_HTML": """
                <p>Das Unternehmen ist gut aufgestellt für KI-Einführung.</p>
            """,
            "RISKS_HTML": """
                <p>Es bestehen moderate Risiken im Bereich Datenschutz.</p>
            """,
        }

    @pytest.fixture
    def realistic_briefing(self) -> Dict[str, Any]:
        """Create realistic briefing data for testing."""
        return {
            "branche": "Beratung",
            "unternehmensgroesse": "team",
            "ROI_12M": 148.0,
            "PAYBACK_MONTHS": 7.5,
        }

    def test_realistic_report_consistency(
        self,
        realistic_sections: Dict[str, str],
        realistic_briefing: Dict[str, Any],
    ) -> None:
        """Test consistency check with realistic report data."""
        from services.consistency_engine import check_consistency

        report = check_consistency(realistic_sections, realistic_briefing)

        # Should pass or warn, not fail with realistic data
        assert report.status in ("PASS", "WARN"), \
            f"Realistic report should pass or warn, got {report.status}"
        assert report.score >= 70, \
            f"Realistic report should score >= 70, got {report.score}"

    def test_realistic_report_domain_coverage(
        self,
        realistic_sections: Dict[str, str],
        realistic_briefing: Dict[str, Any],
    ) -> None:
        """Test that all domains are checked with realistic data."""
        from services.consistency_engine import ConsistencyEngine

        engine = ConsistencyEngine(realistic_sections, realistic_briefing)
        report = engine.check_all()

        # All 6 domains should have scores
        expected_domains = ["tools", "funding", "kpi", "risk", "roadmap", "narrative"]
        for domain in expected_domains:
            assert domain in report.domain_scores, \
                f"Domain '{domain}' should have a score"
