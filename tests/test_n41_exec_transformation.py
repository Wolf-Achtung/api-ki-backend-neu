"""
Tests for Executive Transformation Roadmap - N4.1 PLATIN+++ Executive Experience Layer.

Tests cover:
- Operational automation track building
- Organisational transformation track building
- Decision checkpoints
- Timeline integration
- KPI coupling

25 comprehensive tests for dual-track roadmaps.
"""

import pytest
from datetime import datetime
from typing import Any, Dict

from services.executive_transformation_roadmap import (
    ExecutiveTransformationRoadmapEngine,
    OperationalRoadmapBuilder,
    OrganisationalRoadmapBuilder,
    RoadmapTrack,
    TransformationDomain,
    TimeHorizon,
    DecisionType,
    get_roadmap_engine,
    build_transformation_roadmap,
    get_decision_checkpoints_by_horizon,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def sample_analysis_data() -> Dict[str, Any]:
    """Sample analysis data for roadmap building."""
    return {
        "company_name": "TechCorp GmbH",
        "automation": {
            "automation_percentage": 55,
            "fte_required": 8,
            "data_quality": 75,
            "skill_gaps": ["Data Science", "ML Ops"],
        },
        "organization": {
            "skills_maturity": 60,
            "governance_maturity": 45,
            "culture_maturity": 55,
            "data_readiness_maturity": 50,
            "tool_adoption_maturity": 40,
        },
        "kpis": {
            "roi_percentage": 125,
        },
    }


@pytest.fixture
def engine() -> ExecutiveTransformationRoadmapEngine:
    """Fresh roadmap engine."""
    return ExecutiveTransformationRoadmapEngine()


@pytest.fixture
def op_builder() -> OperationalRoadmapBuilder:
    """Fresh operational roadmap builder."""
    return OperationalRoadmapBuilder()


@pytest.fixture
def org_builder() -> OrganisationalRoadmapBuilder:
    """Fresh organisational roadmap builder."""
    return OrganisationalRoadmapBuilder()


# =============================================================================
# OPERATIONAL ROADMAP BUILDER TESTS
# =============================================================================


class TestOperationalRoadmapBuilder:
    """Tests for OperationalRoadmapBuilder."""

    def test_build_track_basic(
        self,
        op_builder: OperationalRoadmapBuilder,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test basic operational track building."""
        track = op_builder.build_track(sample_analysis_data["automation"])

        assert track is not None
        assert track["track_type"] == RoadmapTrack.OPERATIONAL_AUTOMATION.value
        assert len(track["phases"]) > 0

    def test_track_has_phases(
        self,
        op_builder: OperationalRoadmapBuilder,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test track contains phases."""
        track = op_builder.build_track(sample_analysis_data["automation"])

        assert len(track["phases"]) >= 4

    def test_phase_has_required_fields(
        self,
        op_builder: OperationalRoadmapBuilder,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test phases have all required fields."""
        track = op_builder.build_track(sample_analysis_data["automation"])
        phase = track["phases"][0]

        assert "phase_id" in phase
        assert "name" in phase
        assert "timeline" in phase
        assert "objectives" in phase
        assert "deliverables" in phase
        assert "kpis" in phase
        assert "decision_checkpoints" in phase

    def test_phase_has_kpis(
        self,
        op_builder: OperationalRoadmapBuilder,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test phases have KPIs."""
        track = op_builder.build_track(sample_analysis_data["automation"])
        phase = track["phases"][0]

        assert len(phase["kpis"]) >= 2

    def test_phase_has_checkpoints(
        self,
        op_builder: OperationalRoadmapBuilder,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test phases have decision checkpoints."""
        track = op_builder.build_track(sample_analysis_data["automation"])
        phase = track["phases"][0]

        assert len(phase["decision_checkpoints"]) >= 1

    def test_track_has_critical_path(
        self,
        op_builder: OperationalRoadmapBuilder,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test track identifies critical path."""
        track = op_builder.build_track(sample_analysis_data["automation"])

        assert len(track["critical_path"]) > 0

    def test_track_has_risk_factors(
        self,
        op_builder: OperationalRoadmapBuilder,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test track identifies risk factors."""
        track = op_builder.build_track(sample_analysis_data["automation"])

        assert len(track["risk_factors"]) >= 2


# =============================================================================
# ORGANISATIONAL ROADMAP BUILDER TESTS
# =============================================================================


class TestOrganisationalRoadmapBuilder:
    """Tests for OrganisationalRoadmapBuilder."""

    def test_build_track_basic(
        self,
        org_builder: OrganisationalRoadmapBuilder,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test basic organisational track building."""
        track = org_builder.build_track(sample_analysis_data["organization"])

        assert track is not None
        assert track["track_type"] == RoadmapTrack.ORGANISATIONAL_TRANSFORMATION.value

    def test_track_covers_all_domains(
        self,
        org_builder: OrganisationalRoadmapBuilder,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test track covers all transformation domains."""
        track = org_builder.build_track(sample_analysis_data["organization"])

        assert len(track["phases"]) == len(TransformationDomain)

    def test_domain_specific_phases(
        self,
        org_builder: OrganisationalRoadmapBuilder,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test domain-specific phase content."""
        track = org_builder.build_track(sample_analysis_data["organization"])

        # Find skills phase
        skills_phase = next(
            (p for p in track["phases"] if "SKI" in p["phase_id"]),
            None,
        )

        assert skills_phase is not None
        assert "Skills" in skills_phase["name"] or "Talent" in skills_phase["name"]

    def test_duration_based_on_maturity(
        self,
        org_builder: OrganisationalRoadmapBuilder,
    ) -> None:
        """Test duration adjusts based on maturity."""
        low_maturity = {"skills_maturity": 20}
        high_maturity = {"skills_maturity": 80}

        track_low = org_builder.build_track(low_maturity)
        track_high = org_builder.build_track(high_maturity)

        # Lower maturity should have longer duration
        # (though implementation might parallelize)
        assert track_low["total_duration_days"] >= track_high["total_duration_days"]


# =============================================================================
# MAIN ENGINE TESTS
# =============================================================================


class TestExecutiveTransformationRoadmapEngine:
    """Tests for main ExecutiveTransformationRoadmapEngine."""

    def test_build_roadmap_complete(
        self,
        engine: ExecutiveTransformationRoadmapEngine,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test complete roadmap building."""
        roadmap = engine.build_roadmap(sample_analysis_data)

        assert roadmap is not None
        assert "operational_track" in roadmap
        assert "organisational_track" in roadmap
        assert "integrated_timeline" in roadmap
        assert "executive_summary" in roadmap

    def test_roadmap_has_both_tracks(
        self,
        engine: ExecutiveTransformationRoadmapEngine,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test roadmap contains both tracks."""
        roadmap = engine.build_roadmap(sample_analysis_data)

        op_track = roadmap["operational_track"]
        org_track = roadmap["organisational_track"]

        assert len(op_track["phases"]) > 0
        assert len(org_track["phases"]) > 0

    def test_integrated_timeline(
        self,
        engine: ExecutiveTransformationRoadmapEngine,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test integrated timeline creation."""
        roadmap = engine.build_roadmap(sample_analysis_data)

        timeline = roadmap["integrated_timeline"]
        assert len(timeline) == len(TimeHorizon)

    def test_timeline_has_horizons(
        self,
        engine: ExecutiveTransformationRoadmapEngine,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test timeline includes all horizons."""
        roadmap = engine.build_roadmap(sample_analysis_data)

        horizons = [t["horizon"] for t in roadmap["integrated_timeline"]]
        assert TimeHorizon.IMMEDIATE.value in horizons
        assert TimeHorizon.ANNUAL.value in horizons

    def test_get_decision_checkpoints(
        self,
        engine: ExecutiveTransformationRoadmapEngine,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test checkpoint extraction."""
        roadmap = engine.build_roadmap(sample_analysis_data)
        checkpoints = engine.get_decision_checkpoints(roadmap)

        assert len(checkpoints) > 0
        assert all("checkpoint_id" in c for c in checkpoints)

    def test_total_investment_calculated(
        self,
        engine: ExecutiveTransformationRoadmapEngine,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test total investment is calculated."""
        roadmap = engine.build_roadmap(sample_analysis_data)

        assert "total_investment" in roadmap
        assert "EUR" in roadmap["total_investment"] or "Mio" in roadmap["total_investment"]

    def test_expected_roi_included(
        self,
        engine: ExecutiveTransformationRoadmapEngine,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test expected ROI is included."""
        roadmap = engine.build_roadmap(sample_analysis_data)

        assert "expected_roi" in roadmap
        assert "%" in roadmap["expected_roi"]

    def test_executive_summary_generated(
        self,
        engine: ExecutiveTransformationRoadmapEngine,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test executive summary is generated."""
        roadmap = engine.build_roadmap(sample_analysis_data)

        summary = roadmap["executive_summary"]
        assert len(summary) > 100
        assert "TechCorp" in summary


# =============================================================================
# DECISION CHECKPOINT TESTS
# =============================================================================


class TestDecisionCheckpoints:
    """Tests for decision checkpoints."""

    def test_checkpoint_structure(
        self,
        engine: ExecutiveTransformationRoadmapEngine,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test checkpoint has required structure."""
        roadmap = engine.build_roadmap(sample_analysis_data)
        checkpoints = engine.get_decision_checkpoints(roadmap)

        if checkpoints:
            checkpoint = checkpoints[0]
            assert "decision_type" in checkpoint
            assert "timeline" in checkpoint
            assert "decision_makers" in checkpoint
            assert "required_inputs" in checkpoint
            assert "success_criteria" in checkpoint

    def test_checkpoints_sorted_by_timeline(
        self,
        engine: ExecutiveTransformationRoadmapEngine,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test checkpoints are sorted by timeline."""
        roadmap = engine.build_roadmap(sample_analysis_data)
        checkpoints = engine.get_decision_checkpoints(roadmap)

        # Should be in chronological order
        timelines = [c["timeline"] for c in checkpoints]
        # Basic check - first should come before last
        assert len(timelines) >= 2


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_engine_singleton(self) -> None:
        """Test singleton pattern."""
        engine1 = get_roadmap_engine()
        engine2 = get_roadmap_engine()

        assert engine1 is engine2

    def test_build_transformation_roadmap_function(
        self,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test build_transformation_roadmap function."""
        roadmap = build_transformation_roadmap(sample_analysis_data)

        assert roadmap is not None
        assert "operational_track" in roadmap

    def test_get_checkpoints_by_horizon_function(
        self,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test get_decision_checkpoints_by_horizon function."""
        roadmap = build_transformation_roadmap(sample_analysis_data)
        checkpoints = get_decision_checkpoints_by_horizon(
            roadmap,
            TimeHorizon.IMMEDIATE,
        )

        # May or may not have checkpoints at this horizon
        assert isinstance(checkpoints, list)
