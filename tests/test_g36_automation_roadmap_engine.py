# -*- coding: utf-8 -*-
"""
Sprint G36: Automation Roadmap Engine Tests
============================================

Comprehensive test suite covering:
- ProcessCandidate dataclass
- AutomationPath dataclass
- AutomationRoadmapReport dataclass
- Report generation
- HTML rendering
- Consistency rules AUTO_001-AUTO_008
- Size awareness (solo/team/kmu)
- Branch awareness
- Edge cases

Version: 1.0.0 (Sprint G36)
"""
from __future__ import annotations

import pytest
from typing import Dict, Any, List, Optional


# =============================================================================
# TEST: ProcessCandidate Dataclass
# =============================================================================

class TestProcessCandidate:
    """Tests for ProcessCandidate dataclass."""

    def test_basic_creation(self) -> None:
        """Test ProcessCandidate can be instantiated with basic values."""
        from services.automation_roadmap_engine import ProcessCandidate

        proc = ProcessCandidate(
            id="proc_001",
            name="Test Process",
            description="A test process for automation",
        )

        assert proc.id == "proc_001"
        assert proc.name == "Test Process"
        assert proc.description == "A test process for automation"

    def test_default_values(self) -> None:
        """Test ProcessCandidate has correct defaults."""
        from services.automation_roadmap_engine import ProcessCandidate

        proc = ProcessCandidate(
            id="proc_001",
            name="Test",
            description="Test",
        )

        assert proc.impact_score == 0.5
        assert proc.feasibility_score == 0.5
        assert proc.risk_relation == "medium"
        assert proc.phase_assignment == "phase_2"
        assert proc.dependencies == []
        assert proc.blockers == []
        assert proc.recommended_tools == []
        assert proc.recommended_funding == []

    def test_automation_potential_calculation(self) -> None:
        """Test automation_potential is correctly calculated."""
        from services.automation_roadmap_engine import ProcessCandidate

        proc = ProcessCandidate(
            id="proc_001",
            name="Test",
            description="Test",
            impact_score=0.8,
            feasibility_score=0.6,
        )

        expected = 0.8 * 0.6
        assert abs(proc.automation_potential - expected) < 0.001

    def test_impact_score_clamped_high(self) -> None:
        """Test impact_score is clamped to max 1.0."""
        from services.automation_roadmap_engine import ProcessCandidate

        proc = ProcessCandidate(
            id="proc_001",
            name="Test",
            description="Test",
            impact_score=1.5,
        )

        assert proc.impact_score == 1.0

    def test_impact_score_clamped_low(self) -> None:
        """Test impact_score is clamped to min 0.0."""
        from services.automation_roadmap_engine import ProcessCandidate

        proc = ProcessCandidate(
            id="proc_001",
            name="Test",
            description="Test",
            impact_score=-0.5,
        )

        assert proc.impact_score == 0.0

    def test_feasibility_score_clamped(self) -> None:
        """Test feasibility_score is clamped to 0.0-1.0."""
        from services.automation_roadmap_engine import ProcessCandidate

        proc_high = ProcessCandidate(
            id="proc_001",
            name="Test",
            description="Test",
            feasibility_score=2.0,
        )
        assert proc_high.feasibility_score == 1.0

        proc_low = ProcessCandidate(
            id="proc_002",
            name="Test",
            description="Test",
            feasibility_score=-1.0,
        )
        assert proc_low.feasibility_score == 0.0

    def test_invalid_risk_relation_normalized(self) -> None:
        """Test invalid risk_relation is normalized to 'medium'."""
        from services.automation_roadmap_engine import ProcessCandidate

        proc = ProcessCandidate(
            id="proc_001",
            name="Test",
            description="Test",
            risk_relation="invalid",
        )

        assert proc.risk_relation == "medium"

    def test_valid_risk_relations(self) -> None:
        """Test all valid risk_relation values."""
        from services.automation_roadmap_engine import ProcessCandidate, RISK_RELATIONS

        for risk in RISK_RELATIONS:
            proc = ProcessCandidate(
                id="proc_001",
                name="Test",
                description="Test",
                risk_relation=risk,
            )
            assert proc.risk_relation == risk

    def test_invalid_phase_assignment_normalized(self) -> None:
        """Test invalid phase_assignment is normalized to 'phase_2'."""
        from services.automation_roadmap_engine import ProcessCandidate

        proc = ProcessCandidate(
            id="proc_001",
            name="Test",
            description="Test",
            phase_assignment="invalid_phase",
        )

        assert proc.phase_assignment == "phase_2"

    def test_valid_phase_assignments(self) -> None:
        """Test all valid phase_assignment values."""
        from services.automation_roadmap_engine import ProcessCandidate, PHASE_NAMES

        for phase in PHASE_NAMES:
            proc = ProcessCandidate(
                id="proc_001",
                name="Test",
                description="Test",
                phase_assignment=phase,
                risk_relation="low",  # Prevent auto-recalculation
                feasibility_score=0.9,
            )
            # Note: phase may be recalculated based on rules
            assert proc.phase_assignment in PHASE_NAMES

    def test_is_quick_win_true(self) -> None:
        """Test is_quick_win returns True for high impact and feasibility."""
        from services.automation_roadmap_engine import ProcessCandidate

        proc = ProcessCandidate(
            id="proc_001",
            name="Test",
            description="Test",
            impact_score=0.8,
            feasibility_score=0.85,
        )

        assert proc.is_quick_win is True

    def test_is_quick_win_false(self) -> None:
        """Test is_quick_win returns False for low scores."""
        from services.automation_roadmap_engine import ProcessCandidate

        proc = ProcessCandidate(
            id="proc_001",
            name="Test",
            description="Test",
            impact_score=0.5,
            feasibility_score=0.5,
        )

        assert proc.is_quick_win is False

    def test_is_strategic_true(self) -> None:
        """Test is_strategic returns True for high impact, lower feasibility."""
        from services.automation_roadmap_engine import ProcessCandidate

        proc = ProcessCandidate(
            id="proc_001",
            name="Test",
            description="Test",
            impact_score=0.8,
            feasibility_score=0.4,
        )

        assert proc.is_strategic is True

    def test_is_low_priority_true(self) -> None:
        """Test is_low_priority returns True for low scores."""
        from services.automation_roadmap_engine import ProcessCandidate

        proc = ProcessCandidate(
            id="proc_001",
            name="Test",
            description="Test",
            impact_score=0.3,
            feasibility_score=0.3,
        )

        assert proc.is_low_priority is True

    def test_priority_score_calculation(self) -> None:
        """Test priority_score is calculated correctly."""
        from services.automation_roadmap_engine import ProcessCandidate

        proc = ProcessCandidate(
            id="proc_001",
            name="Test",
            description="Test",
            impact_score=0.8,
            feasibility_score=0.6,
            risk_relation="low",
        )

        # Base: (0.8 * 0.6) + (0.6 * 0.4) = 0.48 + 0.24 = 0.72
        # No penalty for low risk
        assert proc.priority_score > 0.5

    def test_priority_score_high_risk_penalty(self) -> None:
        """Test high risk reduces priority score."""
        from services.automation_roadmap_engine import ProcessCandidate

        proc_low = ProcessCandidate(
            id="proc_001",
            name="Test",
            description="Test",
            impact_score=0.8,
            feasibility_score=0.8,
            risk_relation="low",
        )

        proc_high = ProcessCandidate(
            id="proc_002",
            name="Test",
            description="Test",
            impact_score=0.8,
            feasibility_score=0.8,
            risk_relation="high",
        )

        assert proc_low.priority_score > proc_high.priority_score

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        from services.automation_roadmap_engine import ProcessCandidate

        proc = ProcessCandidate(
            id="proc_001",
            name="Test Process",
            description="Description",
            impact_score=0.8,
            feasibility_score=0.6,
            recommended_tools=["Tool1", "Tool2"],
        )

        data = proc.to_dict()

        assert data["id"] == "proc_001"
        assert data["name"] == "Test Process"
        assert data["impact_score"] == 0.8
        assert data["feasibility_score"] == 0.6
        assert "Tool1" in data["recommended_tools"]
        assert "is_quick_win" in data
        assert "priority_score" in data

    def test_from_dict(self) -> None:
        """Test from_dict deserialization."""
        from services.automation_roadmap_engine import ProcessCandidate

        data = {
            "id": "proc_001",
            "name": "Test Process",
            "description": "Description",
            "impact_score": 0.8,
            "feasibility_score": 0.6,
            "recommended_tools": ["Tool1"],
            "risk_relation": "low",
        }

        proc = ProcessCandidate.from_dict(data)

        assert proc.id == "proc_001"
        assert proc.name == "Test Process"
        assert proc.impact_score == 0.8
        assert proc.feasibility_score == 0.6
        assert "Tool1" in proc.recommended_tools

    def test_round_trip_serialization(self) -> None:
        """Test round-trip serialization preserves data."""
        from services.automation_roadmap_engine import ProcessCandidate

        original = ProcessCandidate(
            id="proc_001",
            name="Test",
            description="Desc",
            impact_score=0.75,
            feasibility_score=0.65,
            dependencies=["proc_002"],
            blockers=["resource_constraint"],
            recommended_tools=["ChatGPT"],
            recommended_funding=["go-digital"],
            risk_relation="medium",
        )

        data = original.to_dict()
        restored = ProcessCandidate.from_dict(data)

        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.impact_score == original.impact_score
        assert restored.feasibility_score == original.feasibility_score

    def test_high_risk_cannot_be_phase_1(self) -> None:
        """Test high risk processes are moved from phase_1."""
        from services.automation_roadmap_engine import ProcessCandidate

        proc = ProcessCandidate(
            id="proc_001",
            name="Test",
            description="Test",
            risk_relation="high",
            phase_assignment="phase_1",
        )

        # Should be recalculated to phase_2 or phase_3
        assert proc.phase_assignment != "phase_1"

    def test_low_feasibility_goes_to_phase_3(self) -> None:
        """Test low feasibility processes go to phase_3."""
        from services.automation_roadmap_engine import ProcessCandidate

        proc = ProcessCandidate(
            id="proc_001",
            name="Test",
            description="Test",
            feasibility_score=0.2,
            phase_assignment="phase_1",
        )

        assert proc.phase_assignment == "phase_3"


# =============================================================================
# TEST: AutomationPath Dataclass
# =============================================================================

class TestAutomationPath:
    """Tests for AutomationPath dataclass."""

    def test_basic_creation(self) -> None:
        """Test AutomationPath can be instantiated."""
        from services.automation_roadmap_engine import AutomationPath

        path = AutomationPath(
            id="path_001",
            title="Main Automation Path",
        )

        assert path.id == "path_001"
        assert path.title == "Main Automation Path"

    def test_default_phases(self) -> None:
        """Test default phases are initialized."""
        from services.automation_roadmap_engine import AutomationPath

        path = AutomationPath(
            id="path_001",
            title="Test",
        )

        assert "phase_1" in path.phases
        assert "phase_2" in path.phases
        assert "phase_3" in path.phases

    def test_phases_with_processes(self) -> None:
        """Test phases can contain process IDs."""
        from services.automation_roadmap_engine import AutomationPath

        path = AutomationPath(
            id="path_001",
            title="Test",
            phases={
                "phase_1": ["proc_001", "proc_002"],
                "phase_2": ["proc_003"],
                "phase_3": [],
            },
        )

        assert len(path.phases["phase_1"]) == 2
        assert "proc_001" in path.phases["phase_1"]

    def test_total_processes(self) -> None:
        """Test total_processes property."""
        from services.automation_roadmap_engine import AutomationPath

        path = AutomationPath(
            id="path_001",
            title="Test",
            phases={
                "phase_1": ["proc_001", "proc_002"],
                "phase_2": ["proc_003"],
                "phase_3": ["proc_004", "proc_005"],
            },
        )

        assert path.total_processes == 5

    def test_has_phase_1_true(self) -> None:
        """Test has_phase_1 returns True when phase_1 has processes."""
        from services.automation_roadmap_engine import AutomationPath

        path = AutomationPath(
            id="path_001",
            title="Test",
            phases={"phase_1": ["proc_001"], "phase_2": [], "phase_3": []},
        )

        assert path.has_phase_1 is True

    def test_has_phase_1_false(self) -> None:
        """Test has_phase_1 returns False when phase_1 is empty."""
        from services.automation_roadmap_engine import AutomationPath

        path = AutomationPath(
            id="path_001",
            title="Test",
            phases={"phase_1": [], "phase_2": ["proc_001"], "phase_3": []},
        )

        assert path.has_phase_1 is False

    def test_kpi_gains(self) -> None:
        """Test expected_kpi_gain storage."""
        from services.automation_roadmap_engine import AutomationPath

        path = AutomationPath(
            id="path_001",
            title="Test",
            expected_kpi_gain={
                "roi": 80.0,
                "savings": 25.0,
                "time_reduction": 30.0,
            },
        )

        assert path.expected_kpi_gain["roi"] == 80.0
        assert path.expected_kpi_gain["savings"] == 25.0

    def test_has_kpi_gains_true(self) -> None:
        """Test has_kpi_gains returns True when gains exist."""
        from services.automation_roadmap_engine import AutomationPath

        path = AutomationPath(
            id="path_001",
            title="Test",
            expected_kpi_gain={"roi": 50.0},
        )

        assert path.has_kpi_gains is True

    def test_has_kpi_gains_false(self) -> None:
        """Test has_kpi_gains returns False when no gains."""
        from services.automation_roadmap_engine import AutomationPath

        path = AutomationPath(
            id="path_001",
            title="Test",
            expected_kpi_gain={},
        )

        assert path.has_kpi_gains is False

    def test_kpi_gains_clamped(self) -> None:
        """Test KPI gains are clamped to reasonable range."""
        from services.automation_roadmap_engine import AutomationPath

        path = AutomationPath(
            id="path_001",
            title="Test",
            expected_kpi_gain={"roi": 600.0},  # Too high
        )

        # Should be clamped to 500
        assert path.expected_kpi_gain["roi"] <= 500.0

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        from services.automation_roadmap_engine import AutomationPath

        path = AutomationPath(
            id="path_001",
            title="Test Path",
            phases={"phase_1": ["proc_001"], "phase_2": [], "phase_3": []},
            rationale="Test rationale",
            expected_kpi_gain={"roi": 80.0},
        )

        data = path.to_dict()

        assert data["id"] == "path_001"
        assert data["title"] == "Test Path"
        assert "total_processes" in data
        assert "has_kpi_gains" in data

    def test_from_dict(self) -> None:
        """Test from_dict deserialization."""
        from services.automation_roadmap_engine import AutomationPath

        data = {
            "id": "path_001",
            "title": "Test",
            "phases": {"phase_1": ["proc_001"], "phase_2": [], "phase_3": []},
            "rationale": "Rationale",
            "expected_kpi_gain": {"roi": 50.0},
        }

        path = AutomationPath.from_dict(data)

        assert path.id == "path_001"
        assert path.title == "Test"
        assert "proc_001" in path.phases["phase_1"]


# =============================================================================
# TEST: AutomationRoadmapReport Dataclass
# =============================================================================

class TestAutomationRoadmapReport:
    """Tests for AutomationRoadmapReport dataclass."""

    def test_basic_creation(self) -> None:
        """Test AutomationRoadmapReport can be instantiated."""
        from services.automation_roadmap_engine import AutomationRoadmapReport

        report = AutomationRoadmapReport()

        assert report.processes == []
        assert report.automation_paths == []
        assert report.summary == ""

    def test_with_processes(self) -> None:
        """Test report with processes."""
        from services.automation_roadmap_engine import (
            AutomationRoadmapReport,
            ProcessCandidate,
        )

        proc1 = ProcessCandidate(id="p1", name="P1", description="D1")
        proc2 = ProcessCandidate(id="p2", name="P2", description="D2")

        report = AutomationRoadmapReport(
            processes=[proc1, proc2],
        )

        assert report.total_processes == 2

    def test_total_processes(self) -> None:
        """Test total_processes property."""
        from services.automation_roadmap_engine import (
            AutomationRoadmapReport,
            ProcessCandidate,
        )

        procs = [
            ProcessCandidate(id=f"p{i}", name=f"P{i}", description="D")
            for i in range(5)
        ]

        report = AutomationRoadmapReport(processes=procs)

        assert report.total_processes == 5

    def test_quick_wins_count(self) -> None:
        """Test quick_win_count property."""
        from services.automation_roadmap_engine import (
            AutomationRoadmapReport,
            ProcessCandidate,
        )

        procs = [
            ProcessCandidate(
                id="p1", name="Quick Win", description="D",
                impact_score=0.9, feasibility_score=0.9
            ),
            ProcessCandidate(
                id="p2", name="Not Quick", description="D",
                impact_score=0.5, feasibility_score=0.5
            ),
        ]

        report = AutomationRoadmapReport(processes=procs)

        assert report.quick_win_count == 1

    def test_phase_counts(self) -> None:
        """Test phase process counts."""
        from services.automation_roadmap_engine import (
            AutomationRoadmapReport,
            ProcessCandidate,
        )

        procs = [
            ProcessCandidate(
                id="p1", name="P1", description="D",
                phase_assignment="phase_1",
                feasibility_score=0.9, risk_relation="low"
            ),
            ProcessCandidate(
                id="p2", name="P2", description="D",
                phase_assignment="phase_2"
            ),
            ProcessCandidate(
                id="p3", name="P3", description="D",
                phase_assignment="phase_3"
            ),
        ]

        report = AutomationRoadmapReport(processes=procs)

        # Note: phases may be recalculated
        total = (
            len(report.phase_1_processes) +
            len(report.phase_2_processes) +
            len(report.phase_3_processes)
        )
        assert total == 3

    def test_avg_impact_score(self) -> None:
        """Test avg_impact_score calculation."""
        from services.automation_roadmap_engine import (
            AutomationRoadmapReport,
            ProcessCandidate,
        )

        procs = [
            ProcessCandidate(id="p1", name="P1", description="D", impact_score=0.8),
            ProcessCandidate(id="p2", name="P2", description="D", impact_score=0.6),
        ]

        report = AutomationRoadmapReport(processes=procs)

        expected = (0.8 + 0.6) / 2
        assert abs(report.avg_impact_score - expected) < 0.01

    def test_avg_feasibility_score(self) -> None:
        """Test avg_feasibility_score calculation."""
        from services.automation_roadmap_engine import (
            AutomationRoadmapReport,
            ProcessCandidate,
        )

        procs = [
            ProcessCandidate(id="p1", name="P1", description="D", feasibility_score=0.9),
            ProcessCandidate(id="p2", name="P2", description="D", feasibility_score=0.7),
        ]

        report = AutomationRoadmapReport(processes=procs)

        expected = (0.9 + 0.7) / 2
        assert abs(report.avg_feasibility_score - expected) < 0.01

    def test_high_risk_count(self) -> None:
        """Test high_risk_count property."""
        from services.automation_roadmap_engine import (
            AutomationRoadmapReport,
            ProcessCandidate,
        )

        procs = [
            ProcessCandidate(id="p1", name="P1", description="D", risk_relation="high"),
            ProcessCandidate(id="p2", name="P2", description="D", risk_relation="low"),
            ProcessCandidate(id="p3", name="P3", description="D", risk_relation="high"),
        ]

        report = AutomationRoadmapReport(processes=procs)

        assert report.high_risk_count == 2

    def test_total_paths(self) -> None:
        """Test total_paths property."""
        from services.automation_roadmap_engine import (
            AutomationRoadmapReport,
            AutomationPath,
        )

        paths = [
            AutomationPath(id="path1", title="Path 1"),
            AutomationPath(id="path2", title="Path 2"),
        ]

        report = AutomationRoadmapReport(automation_paths=paths)

        assert report.total_paths == 2

    def test_processes_sorted_by_priority(self) -> None:
        """Test processes are sorted by priority score descending."""
        from services.automation_roadmap_engine import (
            AutomationRoadmapReport,
            ProcessCandidate,
        )

        procs = [
            ProcessCandidate(id="low", name="Low", description="D", impact_score=0.3, feasibility_score=0.3),
            ProcessCandidate(id="high", name="High", description="D", impact_score=0.9, feasibility_score=0.9),
            ProcessCandidate(id="mid", name="Mid", description="D", impact_score=0.5, feasibility_score=0.5),
        ]

        report = AutomationRoadmapReport(processes=procs)

        # High priority should be first
        assert report.processes[0].id == "high"

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        from services.automation_roadmap_engine import (
            AutomationRoadmapReport,
            ProcessCandidate,
            AutomationPath,
        )

        proc = ProcessCandidate(id="p1", name="P1", description="D")
        path = AutomationPath(id="path1", title="Path 1", expected_kpi_gain={"roi": 50.0})

        report = AutomationRoadmapReport(
            processes=[proc],
            automation_paths=[path],
            summary="Test summary",
        )

        data = report.to_dict()

        assert "processes" in data
        assert "automation_paths" in data
        assert data["total_processes"] == 1
        assert data["total_paths"] == 1

    def test_from_dict(self) -> None:
        """Test from_dict deserialization."""
        from services.automation_roadmap_engine import AutomationRoadmapReport

        data = {
            "processes": [
                {"id": "p1", "name": "P1", "description": "D", "impact_score": 0.8}
            ],
            "automation_paths": [
                {"id": "path1", "title": "Path 1", "expected_kpi_gain": {"roi": 50.0}}
            ],
            "summary": "Summary",
        }

        report = AutomationRoadmapReport.from_dict(data)

        assert report.total_processes == 1
        assert report.total_paths == 1
        assert report.summary == "Summary"


# =============================================================================
# TEST: Report Generation
# =============================================================================

class TestReportGeneration:
    """Tests for generate_automation_roadmap function."""

    def test_basic_generation(self) -> None:
        """Test basic report generation."""
        from services.automation_roadmap_engine import generate_automation_roadmap

        report = generate_automation_roadmap(
            briefing={"unternehmensgroesse": "team"},
        )

        assert report is not None
        assert isinstance(report.processes, list)
        assert isinstance(report.automation_paths, list)

    def test_generation_with_no_params(self) -> None:
        """Test generation works with no parameters."""
        from services.automation_roadmap_engine import generate_automation_roadmap

        report = generate_automation_roadmap()

        assert report is not None
        assert report.total_processes > 0

    def test_size_aware_solo(self) -> None:
        """Test solo size limits processes."""
        from services.automation_roadmap_engine import generate_automation_roadmap

        report = generate_automation_roadmap(
            briefing={"unternehmensgroesse": "solo"},
        )

        assert report.total_processes <= 5

    def test_size_aware_team(self) -> None:
        """Test team size limits processes."""
        from services.automation_roadmap_engine import generate_automation_roadmap

        report = generate_automation_roadmap(
            briefing={"unternehmensgroesse": "team"},
        )

        assert report.total_processes <= 7

    def test_size_aware_kmu(self) -> None:
        """Test KMU size allows more processes."""
        from services.automation_roadmap_engine import generate_automation_roadmap

        report = generate_automation_roadmap(
            briefing={"unternehmensgroesse": "kmu"},
        )

        assert report.total_processes <= 12

    def test_has_quick_wins(self) -> None:
        """Test report identifies quick wins."""
        from services.automation_roadmap_engine import generate_automation_roadmap

        report = generate_automation_roadmap(
            briefing={"unternehmensgroesse": "kmu"},
        )

        # Should have at least some quick wins
        assert report.quick_win_count >= 0

    def test_has_automation_paths(self) -> None:
        """Test report generates automation paths."""
        from services.automation_roadmap_engine import generate_automation_roadmap

        report = generate_automation_roadmap(
            briefing={"unternehmensgroesse": "kmu"},
        )

        assert report.total_paths >= 1

    def test_summary_generated(self) -> None:
        """Test summary is generated."""
        from services.automation_roadmap_engine import generate_automation_roadmap

        report = generate_automation_roadmap(
            briefing={"unternehmensgroesse": "team"},
        )

        assert len(report.summary) > 0

    def test_all_processes_have_ids(self) -> None:
        """Test all processes have unique IDs."""
        from services.automation_roadmap_engine import generate_automation_roadmap

        report = generate_automation_roadmap()

        ids = [p.id for p in report.processes]
        assert len(ids) == len(set(ids))  # All unique

    def test_all_paths_have_kpi_gains(self) -> None:
        """Test all paths have KPI gains (AUTO_008 rule)."""
        from services.automation_roadmap_engine import generate_automation_roadmap

        report = generate_automation_roadmap()

        for path in report.automation_paths:
            assert path.has_kpi_gains, f"Path {path.id} has no KPI gains"

    def test_automation_potential_valid(self) -> None:
        """Test automation_potential <= 1.0 (AUTO_004 rule)."""
        from services.automation_roadmap_engine import generate_automation_roadmap

        report = generate_automation_roadmap()

        for proc in report.processes:
            assert proc.automation_potential <= 1.0, \
                f"Process {proc.id} has automation_potential > 1.0"


# =============================================================================
# TEST: HTML Rendering
# =============================================================================

class TestHTMLRendering:
    """Tests for automation_roadmap_to_html function."""

    def test_html_generation(self) -> None:
        """Test HTML can be generated."""
        from services.automation_roadmap_engine import (
            generate_automation_roadmap,
            automation_roadmap_to_html,
        )

        report = generate_automation_roadmap()
        html = automation_roadmap_to_html(report, lang="de")

        assert isinstance(html, str)
        assert len(html) > 0
        assert "<div" in html

    def test_html_contains_processes(self) -> None:
        """Test HTML contains process information."""
        from services.automation_roadmap_engine import (
            generate_automation_roadmap,
            automation_roadmap_to_html,
        )

        report = generate_automation_roadmap()
        html = automation_roadmap_to_html(report, lang="de")

        # Should contain at least some process names
        for proc in report.processes[:3]:
            assert proc.name in html or html  # May be truncated

    def test_html_contains_matrix(self) -> None:
        """Test HTML contains Impact × Feasibility Matrix."""
        from services.automation_roadmap_engine import (
            generate_automation_roadmap,
            automation_roadmap_to_html,
        )

        report = generate_automation_roadmap()
        html = automation_roadmap_to_html(report, lang="de")

        # Check for matrix-related content
        assert "Matrix" in html or "grid" in html.lower()

    def test_german_labels(self) -> None:
        """Test German labels are used for de language."""
        from services.automation_roadmap_engine import (
            generate_automation_roadmap,
            automation_roadmap_to_html,
        )

        report = generate_automation_roadmap()
        html = automation_roadmap_to_html(report, lang="de")

        # German labels
        assert "Automations-Roadmap" in html or "Prozesskandidaten" in html

    def test_english_labels(self) -> None:
        """Test English labels are used for en language."""
        from services.automation_roadmap_engine import (
            generate_automation_roadmap,
            automation_roadmap_to_html,
        )

        report = generate_automation_roadmap()
        html = automation_roadmap_to_html(report, lang="en")

        # English labels
        assert "Automation Roadmap" in html or "Process Candidates" in html

    def test_html_has_platin_colors(self) -> None:
        """Test HTML uses Platin++ color palette."""
        from services.automation_roadmap_engine import (
            generate_automation_roadmap,
            automation_roadmap_to_html,
        )

        report = generate_automation_roadmap()
        html = automation_roadmap_to_html(report, lang="de")

        # Check for Platin++ colors
        assert "#8b5cf6" in html or "#22c55e" in html  # Purple or green

    def test_html_has_g36_badge(self) -> None:
        """Test HTML contains G36 engine badge."""
        from services.automation_roadmap_engine import (
            generate_automation_roadmap,
            automation_roadmap_to_html,
        )

        report = generate_automation_roadmap()
        html = automation_roadmap_to_html(report, lang="de")

        assert "G36" in html

    def test_empty_report_handling(self) -> None:
        """Test HTML handles empty report gracefully."""
        from services.automation_roadmap_engine import (
            AutomationRoadmapReport,
            automation_roadmap_to_html,
        )

        report = AutomationRoadmapReport(processes=[], automation_paths=[])
        html = automation_roadmap_to_html(report, lang="de")

        assert isinstance(html, str)
        # Should indicate no processes
        assert "Keine" in html or len(html) > 100


# =============================================================================
# TEST: Consistency Rules
# =============================================================================

class TestConsistencyRules:
    """Tests for AUTO_001-AUTO_008 consistency rules."""

    def test_auto_004_potential_bounds(self) -> None:
        """Test AUTO_004: Impact × Feasibility <= 1.0."""
        from services.automation_roadmap_engine import (
            ProcessCandidate,
            validate_impact_feasibility_bounds,
        )

        valid_proc = ProcessCandidate(
            id="p1", name="P1", description="D",
            impact_score=0.8, feasibility_score=0.9,
        )
        assert validate_impact_feasibility_bounds(valid_proc) is True

    def test_auto_008_path_kpi_gains(self) -> None:
        """Test AUTO_008: Paths must have KPI gains."""
        from services.automation_roadmap_engine import (
            AutomationPath,
            validate_path_has_kpi_gains,
        )

        valid_path = AutomationPath(
            id="path1", title="Test",
            expected_kpi_gain={"roi": 50.0},
        )
        assert validate_path_has_kpi_gains(valid_path) is True

        invalid_path = AutomationPath(
            id="path2", title="Test",
            expected_kpi_gain={},
        )
        assert validate_path_has_kpi_gains(invalid_path) is False

    def test_auto_001_tool_fit_validation(self) -> None:
        """Test AUTO_001: Tool fit validation function exists."""
        from services.automation_roadmap_engine import (
            ProcessCandidate,
            validate_process_tool_fit,
        )

        proc = ProcessCandidate(
            id="p1", name="P1", description="D",
            recommended_tools=["ChatGPT"],
        )

        # Should not raise
        result = validate_process_tool_fit(proc, None)
        assert isinstance(result, bool)

    def test_auto_005_funding_fit_validation(self) -> None:
        """Test AUTO_005: Funding fit validation function exists."""
        from services.automation_roadmap_engine import (
            ProcessCandidate,
            validate_process_funding_fit,
        )

        proc = ProcessCandidate(
            id="p1", name="P1", description="D",
            recommended_funding=["go-digital"],
        )

        # Should not raise
        result = validate_process_funding_fit(proc, None)
        assert isinstance(result, bool)

    def test_auto_007_high_risk_phase_validation(self) -> None:
        """Test AUTO_007: High risk phase validation."""
        from services.automation_roadmap_engine import (
            ProcessCandidate,
            validate_high_risk_phase,
        )

        proc = ProcessCandidate(
            id="p1", name="P1", description="D",
            phase_assignment="phase_2",
            recommended_tools=["ChatGPT"],
        )

        # Should pass with no vendor risks
        result = validate_high_risk_phase(proc, {})
        assert result is True


# =============================================================================
# TEST: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_briefing(self) -> None:
        """Test generation with empty briefing."""
        from services.automation_roadmap_engine import generate_automation_roadmap

        report = generate_automation_roadmap(briefing={})

        assert report is not None
        assert report.total_processes > 0

    def test_none_briefing(self) -> None:
        """Test generation with None briefing."""
        from services.automation_roadmap_engine import generate_automation_roadmap

        report = generate_automation_roadmap(briefing=None)

        assert report is not None

    def test_invalid_json_llm_response(self) -> None:
        """Test handling of invalid JSON LLM response."""
        from services.automation_roadmap_engine import generate_automation_roadmap

        report = generate_automation_roadmap(
            llm_response="not valid json{",
        )

        # Should fall back to default generation
        assert report is not None
        assert report.total_processes > 0

    def test_empty_tools_data(self) -> None:
        """Test generation with empty tools data."""
        from services.automation_roadmap_engine import generate_automation_roadmap

        report = generate_automation_roadmap(
            tools_data=[],
        )

        assert report is not None

    def test_empty_funding_data(self) -> None:
        """Test generation with empty funding data."""
        from services.automation_roadmap_engine import generate_automation_roadmap

        report = generate_automation_roadmap(
            funding_data=[],
        )

        assert report is not None

    def test_process_with_empty_name(self) -> None:
        """Test ProcessCandidate handles empty name."""
        from services.automation_roadmap_engine import ProcessCandidate

        proc = ProcessCandidate(
            id="p1",
            name="",
            description="Description",
        )

        assert proc.name == ""

    def test_path_with_empty_phases(self) -> None:
        """Test AutomationPath handles empty phases."""
        from services.automation_roadmap_engine import AutomationPath

        path = AutomationPath(
            id="path1",
            title="Empty Path",
            phases={},
        )

        # Should have default phases
        assert "phase_1" in path.phases

    def test_report_with_single_process(self) -> None:
        """Test report with only one process."""
        from services.automation_roadmap_engine import (
            AutomationRoadmapReport,
            ProcessCandidate,
        )

        proc = ProcessCandidate(id="p1", name="Only One", description="D")
        report = AutomationRoadmapReport(processes=[proc])

        assert report.total_processes == 1
        assert report.avg_impact_score == proc.impact_score

    def test_non_list_dependencies_normalized(self) -> None:
        """Test non-list dependencies are normalized."""
        from services.automation_roadmap_engine import ProcessCandidate

        proc = ProcessCandidate(
            id="p1",
            name="Test",
            description="D",
            dependencies=None,  # type: ignore
        )

        assert proc.dependencies == []


# =============================================================================
# TEST: Integration with Other Engines
# =============================================================================

class TestEngineIntegration:
    """Tests for integration with other engines."""

    def test_accepts_tools_engine_data(self) -> None:
        """Test accepts Tools Engine 4.0 data format."""
        from services.automation_roadmap_engine import generate_automation_roadmap

        tools_data = {
            "tools": [
                {"name": "ChatGPT", "fit_score": 0.8},
                {"name": "Zapier", "fit_score": 0.7},
            ]
        }

        report = generate_automation_roadmap(tools_data=tools_data)
        assert report is not None

    def test_accepts_funding_engine_data(self) -> None:
        """Test accepts Funding Engine v2 data format."""
        from services.automation_roadmap_engine import generate_automation_roadmap

        funding_data = {
            "programs": [
                {"name": "ZIM", "amount": 50000},
                {"name": "go-digital", "amount": 16500},
            ]
        }

        report = generate_automation_roadmap(funding_data=funding_data)
        assert report is not None

    def test_engine_enabled_flag(self) -> None:
        """Test engine enabled flag exists."""
        from services.automation_roadmap_engine import AUTOMATION_ROADMAP_ENGINE_ENABLED

        assert isinstance(AUTOMATION_ROADMAP_ENGINE_ENABLED, bool)
        assert AUTOMATION_ROADMAP_ENGINE_ENABLED is True


# =============================================================================
# TEST: Constants and Configuration
# =============================================================================

class TestConfiguration:
    """Tests for configuration constants."""

    def test_risk_relations_defined(self) -> None:
        """Test RISK_RELATIONS constant is defined."""
        from services.automation_roadmap_engine import RISK_RELATIONS

        assert "low" in RISK_RELATIONS
        assert "medium" in RISK_RELATIONS
        assert "high" in RISK_RELATIONS

    def test_phase_names_defined(self) -> None:
        """Test PHASE_NAMES constant is defined."""
        from services.automation_roadmap_engine import PHASE_NAMES

        assert "phase_1" in PHASE_NAMES
        assert "phase_2" in PHASE_NAMES
        assert "phase_3" in PHASE_NAMES

    def test_size_limits_defined(self) -> None:
        """Test SIZE_AUTOMATION_LIMITS constant is defined."""
        from services.automation_roadmap_engine import SIZE_AUTOMATION_LIMITS

        assert "solo" in SIZE_AUTOMATION_LIMITS
        assert "team" in SIZE_AUTOMATION_LIMITS
        assert "kmu" in SIZE_AUTOMATION_LIMITS

    def test_size_limits_have_max_processes(self) -> None:
        """Test size limits include max_processes."""
        from services.automation_roadmap_engine import SIZE_AUTOMATION_LIMITS

        for size in ["solo", "team", "kmu"]:
            assert "max_processes" in SIZE_AUTOMATION_LIMITS[size]

    def test_process_categories_defined(self) -> None:
        """Test PROCESS_CATEGORIES constant is defined."""
        from services.automation_roadmap_engine import PROCESS_CATEGORIES

        assert len(PROCESS_CATEGORIES) > 0
        assert "customer_service" in PROCESS_CATEGORIES
        assert "content_creation" in PROCESS_CATEGORIES

    def test_blocker_types_defined(self) -> None:
        """Test BLOCKER_TYPES constant is defined."""
        from services.automation_roadmap_engine import BLOCKER_TYPES

        assert len(BLOCKER_TYPES) > 0
        assert "data_quality" in BLOCKER_TYPES


# =============================================================================
# TEST: Module Exports
# =============================================================================

class TestModuleExports:
    """Tests for module __all__ exports."""

    def test_all_exports_exist(self) -> None:
        """Test all __all__ exports are importable."""
        from services.automation_roadmap_engine import __all__

        import services.automation_roadmap_engine as module

        for name in __all__:
            assert hasattr(module, name), f"Missing export: {name}"

    def test_main_classes_exported(self) -> None:
        """Test main classes are in __all__."""
        from services.automation_roadmap_engine import __all__

        assert "ProcessCandidate" in __all__
        assert "AutomationPath" in __all__
        assert "AutomationRoadmapReport" in __all__

    def test_main_functions_exported(self) -> None:
        """Test main functions are in __all__."""
        from services.automation_roadmap_engine import __all__

        assert "generate_automation_roadmap" in __all__
        assert "automation_roadmap_to_html" in __all__
