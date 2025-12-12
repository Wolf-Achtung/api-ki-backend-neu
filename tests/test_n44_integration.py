# -*- coding: utf-8 -*-
"""
N4.4 Test Suite: Integration Module
===================================

Tests for services/research_agents/n44_integration.py

Coverage:
- N44ResearchReport
- N44Status
- process_n44_research main function
- validate_n44_dod
- get_n44_status
- inject_research_into_sections

Target: ~15 tests
Version: 1.0.0 (N4.4 - PLATIN+++ v5.4)
"""

import pytest
from typing import Dict, Any

from services.research_agents.n44_integration import (
    N44ResearchReport,
    N44Status,
    process_n44_research,
    validate_n44_dod,
    get_n44_status,
    inject_research_into_sections,
)
from services.research_agents.knowledge_fusion import (
    InjectionTarget,
    InjectionHook,
    ExecutiveThesis,
)
from services.research_agents.orchestrator import AgentSignalType


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_briefing() -> Dict[str, Any]:
    return {
        "company_name": "TechCorp GmbH",
        "branch": "consulting",
        "lang": "de",
        "region": "Deutschland",
    }


@pytest.fixture
def sample_sections() -> Dict[str, Any]:
    return {
        "executive_summary": "This is the executive summary.",
        "strategy": "Strategy section content.",
        "ki_stack_summary": "KI Stack overview.",
        "risks": "Risk assessment.",
    }


@pytest.fixture
def sample_report() -> N44ResearchReport:
    return N44ResearchReport(
        agents_run=5,
        agents_succeeded=5,
        agents_failed=0,
        total_insights=15,
        fused_signals=5,
        theses_generated=3,
        integrity_score=0.92,
        sources_verified=10,
        hooks_applied=8,
    )


# =============================================================================
# TEST CLASS: N44ResearchReport
# =============================================================================

class TestN44ResearchReport:
    """Tests for N44ResearchReport dataclass."""

    def test_report_creation(self):
        report = N44ResearchReport()
        assert report.success is True
        assert report.report_id.startswith("N44-")

    def test_report_auto_timestamp(self):
        report = N44ResearchReport()
        assert report.timestamp != ""

    def test_report_to_dict(self, sample_report):
        d = sample_report.to_dict()
        assert d["agents_run"] == 5
        assert d["agents_succeeded"] == 5
        assert d["integrity_score"] == 0.92

    def test_report_fields(self, sample_report):
        assert sample_report.total_insights == 15
        assert sample_report.fused_signals == 5
        assert sample_report.theses_generated == 3


# =============================================================================
# TEST CLASS: N44Status
# =============================================================================

class TestN44Status:
    """Tests for N44Status dataclass."""

    def test_status_creation(self):
        status = N44Status()
        assert status.phase == "idle"
        assert status.progress == 0.0

    def test_status_to_dict(self):
        status = N44Status(
            phase="orchestrating",
            progress=0.5,
            current_agent="market_agent",
        )
        d = status.to_dict()
        assert d["phase"] == "orchestrating"
        assert d["progress"] == 0.5

    def test_status_errors(self):
        status = N44Status()
        status.errors.append("Test error")
        assert len(status.errors) == 1


# =============================================================================
# TEST CLASS: Main Processing
# =============================================================================

class TestProcessN44Research:
    """Tests for process_n44_research function."""

    def test_process_mock_mode(self, sample_sections, sample_briefing):
        modified, report = process_n44_research(
            sections=sample_sections,
            briefing=sample_briefing,
            language="de",
            mock_mode=True,
        )
        assert report.success is True
        assert "_n44_research_processed" in modified

    def test_process_returns_report(self, sample_sections, sample_briefing):
        _, report = process_n44_research(
            sections=sample_sections,
            briefing=sample_briefing,
            mock_mode=True,
        )
        assert isinstance(report, N44ResearchReport)
        assert report.agents_run >= 1

    def test_process_english_mode(self, sample_sections):
        briefing = {"company_name": "Test", "lang": "en"}
        _, report = process_n44_research(
            sections=sample_sections,
            briefing=briefing,
            language="en",
            mock_mode=True,
        )
        assert report.success is True

    def test_process_adds_metadata(self, sample_sections, sample_briefing):
        modified, _ = process_n44_research(
            sections=sample_sections,
            briefing=sample_briefing,
            mock_mode=True,
        )
        assert "_n44_report" in modified
        assert "_n44_integrity_score" in modified


# =============================================================================
# TEST CLASS: Validation & Status
# =============================================================================

class TestValidationAndStatus:
    """Tests for validation and status functions."""

    def test_validate_dod_success(self, sample_report):
        is_valid, details = validate_n44_dod(sample_report)
        assert is_valid is True
        assert details["agents_ok"] is True
        assert details["integrity_ok"] is True

    def test_validate_dod_failure(self):
        report = N44ResearchReport(
            agents_succeeded=2,  # Below threshold
            integrity_score=0.5,  # Below threshold
        )
        is_valid, details = validate_n44_dod(report)
        assert is_valid is False

    def test_get_n44_status(self):
        status = get_n44_status()
        assert isinstance(status, dict)
        assert "phase" in status
        assert "progress" in status


# =============================================================================
# TEST CLASS: Section Injection
# =============================================================================

class TestSectionInjection:
    """Tests for inject_research_into_sections function."""

    def test_inject_empty_hooks(self, sample_sections):
        modified = inject_research_into_sections(
            sections=sample_sections,
            hooks={},
            theses=[],
            language="de",
        )
        # Should return copy without changes
        assert "executive_summary" in modified

    def test_inject_with_hooks(self, sample_sections):
        hooks = {
            InjectionTarget.STRATEGY: [
                InjectionHook(
                    hook_id="H1",
                    target=InjectionTarget.STRATEGY,
                    content="Injected strategy insight",
                    priority=1,
                )
            ],
        }
        modified = inject_research_into_sections(
            sections=sample_sections,
            hooks=hooks,
            theses=[],
            language="de",
        )
        # Strategy should have injected content
        assert "Injected strategy insight" in modified["strategy"] or "_research_strategy" in modified

    def test_inject_with_theses(self, sample_sections):
        theses = [
            ExecutiveThesis(
                thesis_id="TH1",
                statement="Test thesis statement",
                supporting_signals=[AgentSignalType.MARKET],
                confidence=0.9,
                priority=1,
            ),
        ]
        hooks = {
            InjectionTarget.EXECUTIVE_SUMMARY: [
                InjectionHook(
                    hook_id="H1",
                    target=InjectionTarget.EXECUTIVE_SUMMARY,
                    content="Test hook",
                    priority=1,
                )
            ],
        }
        modified = inject_research_into_sections(
            sections=sample_sections,
            hooks=hooks,
            theses=theses,
            language="de",
        )
        # Should have some injection content
        assert any(
            "_research_" in k or "Forschungs" in str(v) or "Test thesis" in str(v)
            for k, v in modified.items()
        )
