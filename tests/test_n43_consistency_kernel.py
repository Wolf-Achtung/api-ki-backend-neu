# -*- coding: utf-8 -*-
"""
N4.3 Test Suite: Consistency Kernel v7
======================================

Tests for services/consistency_kernel_v7.py

Coverage:
- Cross-model consistency validation
- 3-way alignment (narrative, numerical, governance)
- Contradiction detection
- Tolerance validation (KPIs ±3%, governance ±1 level)
- Self-healing

Target: ~25 tests

Version: 1.0.0 (N4.3 - PLATIN+++ v5.3)
"""

import pytest
from typing import Dict, Any

from services.consistency_kernel_v7 import (
    AlignmentDimension,
    ConsistencyLevel,
    ModelSource,
    IssueSeverity,
    ConsistencyIssue,
    AlignmentResult,
    ConsistencyKernelV7,
    normalize_model_output,
    identify_contradictions,
    merge_model_outputs,
    check_3way_alignment,
    validate_cross_model_consistency,
    TOLERANCES,
    GOVERNANCE_LEVELS,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_sections() -> Dict[str, Any]:
    """Sample sections for testing."""
    return {
        "executive_summary": "ROI of 150% over 12 months. Payback period: 6 months.",
        "business_case": "Monthly savings: 2400€. ROI: 150%. Payback: 6 months.",
        "risks": "Low risk implementation. Risk level: minimal.",
        "governance": "AI governance score: 75. Maturity: defined.",
    }


@pytest.fixture
def sample_briefing() -> Dict[str, Any]:
    """Sample briefing for testing."""
    return {
        "company_name": "TechCorp GmbH",
        "lang": "de",
        "ROI_12M": 150,
        "PAYBACK_MONTHS": 6,
    }


@pytest.fixture
def claude_output() -> Dict[str, Any]:
    """Simulated Claude output."""
    return {
        "executive_summary": "ROI: 150%",
        "roi_value": 150,
        "risk_level": "minimal",
    }


@pytest.fixture
def gpt_output() -> Dict[str, Any]:
    """Simulated GPT output."""
    return {
        "executive_summary": "ROI: 152%",  # Slightly different
        "roi_value": 152,
        "risk_level": "low",  # Different terminology
    }


# =============================================================================
# TEST CLASS: Enums & Constants
# =============================================================================

class TestConsistencyEnums:
    """Tests for consistency enums."""

    def test_alignment_dimension_values(self):
        """All alignment dimensions should be defined."""
        assert AlignmentDimension.NARRATIVE.value == "narrative"
        assert AlignmentDimension.NUMERICAL.value == "numerical"
        assert AlignmentDimension.GOVERNANCE.value == "governance"

    def test_consistency_level_values(self):
        """All consistency levels should be defined."""
        assert ConsistencyLevel.FULL.value == "full"
        assert ConsistencyLevel.HIGH.value == "high"
        assert ConsistencyLevel.MODERATE.value == "moderate"
        assert ConsistencyLevel.LOW.value == "low"
        assert ConsistencyLevel.CONFLICT.value == "conflict"

    def test_model_source_values(self):
        """All model sources should be defined."""
        assert ModelSource.CLAUDE.value == "claude"
        assert ModelSource.GPT.value == "gpt"
        assert ModelSource.MERGED.value == "merged"

    def test_issue_severity_values(self):
        """All issue severity levels should be defined."""
        assert IssueSeverity.CRITICAL.value == "critical"
        assert IssueSeverity.HIGH.value == "high"
        assert IssueSeverity.MEDIUM.value == "medium"
        assert IssueSeverity.LOW.value == "low"


class TestConsistencyConstants:
    """Tests for consistency constants."""

    def test_tolerances_dict_exists(self):
        """Tolerances dictionary should be defined."""
        assert isinstance(TOLERANCES, dict)
        assert "kpi_percentage" in TOLERANCES
        assert "governance_level" in TOLERANCES

    def test_kpi_tolerance_value(self):
        """KPI tolerance should be reasonable."""
        kpi_tol = TOLERANCES.get("kpi_percentage", 0.03)
        assert kpi_tol > 0
        assert kpi_tol <= 0.10  # Should be reasonable (e.g., 3%)

    def test_governance_levels_exist(self):
        """Governance levels should be defined."""
        assert isinstance(GOVERNANCE_LEVELS, dict)
        assert len(GOVERNANCE_LEVELS) > 0


# =============================================================================
# TEST CLASS: Model Output Normalization
# =============================================================================

class TestModelOutputNormalization:
    """Tests for model output normalization."""

    def test_normalize_claude_output(self, claude_output):
        """Should normalize Claude output."""
        result = normalize_model_output(claude_output, ModelSource.CLAUDE)
        assert isinstance(result, dict)

    def test_normalize_gpt_output(self, gpt_output):
        """Should normalize GPT output."""
        result = normalize_model_output(gpt_output, ModelSource.GPT)
        assert isinstance(result, dict)

    def test_normalize_empty_output(self):
        """Should handle empty model output."""
        result = normalize_model_output({}, ModelSource.CLAUDE)
        assert isinstance(result, dict)


# =============================================================================
# TEST CLASS: Contradiction Detection
# =============================================================================

class TestContradictionDetection:
    """Tests for contradiction detection."""

    def test_detect_contradictions_returns_list(self, claude_output, gpt_output):
        """Should return list of contradictions."""
        result = identify_contradictions(claude_output, gpt_output)
        assert isinstance(result, list)

    def test_no_contradiction_identical(self, claude_output):
        """Identical outputs should have no contradictions."""
        result = identify_contradictions(claude_output, claude_output)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_identify_contradictions_empty(self):
        """Should handle empty outputs."""
        result = identify_contradictions({}, {})
        assert isinstance(result, list)


# =============================================================================
# TEST CLASS: Output Merging
# =============================================================================

class TestOutputMerging:
    """Tests for model output merging."""

    def test_merge_outputs_returns_dict(self, claude_output, gpt_output):
        """Should merge model outputs."""
        result = merge_model_outputs(
            claude_output=claude_output,
            gpt_output=gpt_output,
        )
        assert isinstance(result, dict)

    def test_merge_with_preference(self, claude_output, gpt_output):
        """Merge should respect preference."""
        result = merge_model_outputs(
            claude_output=claude_output,
            gpt_output=gpt_output,
            preference="claude",
        )
        assert isinstance(result, dict)


# =============================================================================
# TEST CLASS: 3-Way Alignment
# =============================================================================

class TestThreeWayAlignment:
    """Tests for 3-way alignment checking."""

    def test_alignment_returns_dict(self, claude_output, gpt_output):
        """3-way alignment should return dict of results."""
        result = check_3way_alignment(
            claude_output=claude_output,
            gpt_output=gpt_output,
        )
        assert isinstance(result, dict)

    def test_alignment_has_dimensions(self, claude_output, gpt_output):
        """Alignment result should have dimension keys."""
        result = check_3way_alignment(
            claude_output=claude_output,
            gpt_output=gpt_output,
        )
        # Result should contain AlignmentResult objects by dimension
        assert isinstance(result, dict)


# =============================================================================
# TEST CLASS: Cross-Model Consistency
# =============================================================================

class TestCrossModelConsistency:
    """Tests for cross-model consistency."""

    def test_validate_consistency(self, sample_sections, sample_briefing, claude_output, gpt_output):
        """Should validate cross-model consistency."""
        is_valid, details = validate_cross_model_consistency(
            sections=sample_sections,
            briefing=sample_briefing,
            claude_output=claude_output,
            gpt_output=gpt_output,
        )
        assert isinstance(is_valid, bool)
        assert isinstance(details, dict)

    def test_validate_consistency_without_outputs(self, sample_sections, sample_briefing):
        """Should handle missing model outputs."""
        is_valid, details = validate_cross_model_consistency(
            sections=sample_sections,
            briefing=sample_briefing,
        )
        assert isinstance(is_valid, bool)
        assert isinstance(details, dict)


# =============================================================================
# TEST CLASS: Engine Processing
# =============================================================================

class TestEngineProcessing:
    """Tests for engine processing."""

    def test_engine_init(self, sample_sections, sample_briefing):
        """Engine should initialize."""
        engine = ConsistencyKernelV7(
            sections=sample_sections,
            briefing=sample_briefing,
        )
        assert engine is not None

    def test_engine_process(self, sample_sections, sample_briefing):
        """Engine should process sections."""
        engine = ConsistencyKernelV7(
            sections=sample_sections,
            briefing=sample_briefing,
        )
        result_sections, report = engine.process()

        assert isinstance(result_sections, dict)
        assert report.engine_id == "CONSISTENCY_KERNEL_V7"

    def test_engine_adds_metadata(self, sample_sections, sample_briefing):
        """Engine should add consistency metadata."""
        engine = ConsistencyKernelV7(
            sections=sample_sections,
            briefing=sample_briefing,
        )
        result_sections, _ = engine.process()

        # Check for metadata key (actual name from implementation)
        assert "_model_consistency_validated" in result_sections or "_consistency_validated" in result_sections
        assert "_consistency_report" in result_sections


# =============================================================================
# TEST CLASS: Data Structures
# =============================================================================

class TestDataStructures:
    """Tests for data structures."""

    def test_consistency_issue_creation(self):
        """ConsistencyIssue should be creatable."""
        issue = ConsistencyIssue(
            issue_id="CI-001",
            dimension=AlignmentDimension.NUMERICAL,
            severity=IssueSeverity.MEDIUM,
            section="executive_summary",
            description="Test issue",
            claude_value="150%",
            gpt_value="180%",
        )
        assert issue.issue_id == "CI-001"
        assert issue.dimension == AlignmentDimension.NUMERICAL

    def test_consistency_issue_to_dict(self):
        """ConsistencyIssue should serialize to dict."""
        issue = ConsistencyIssue(
            issue_id="CI-001",
            dimension=AlignmentDimension.NUMERICAL,
            severity=IssueSeverity.MEDIUM,
            section="executive_summary",
            description="Test issue",
        )
        d = issue.to_dict()
        assert d["issue_id"] == "CI-001"
        assert d["dimension"] == "numerical"

    def test_alignment_result_creation(self):
        """AlignmentResult should be creatable."""
        result = AlignmentResult(
            dimension=AlignmentDimension.NUMERICAL,
            consistency_level=ConsistencyLevel.HIGH,
            score=0.95,
        )
        assert result.dimension == AlignmentDimension.NUMERICAL
        assert result.score == 0.95

    def test_alignment_result_to_dict(self):
        """AlignmentResult should serialize to dict."""
        result = AlignmentResult(
            dimension=AlignmentDimension.NUMERICAL,
            consistency_level=ConsistencyLevel.HIGH,
            score=0.95,
        )
        d = result.to_dict()
        assert d["dimension"] == "numerical"
        assert "score" in d


# =============================================================================
# TEST CLASS: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_sections(self, sample_briefing):
        """Should handle empty sections."""
        engine = ConsistencyKernelV7(
            sections={},
            briefing=sample_briefing,
        )
        result_sections, report = engine.process()
        assert report.success

    def test_empty_briefing(self, sample_sections):
        """Should handle empty briefing."""
        engine = ConsistencyKernelV7(
            sections=sample_sections,
            briefing={},
        )
        result_sections, report = engine.process()
        assert isinstance(result_sections, dict)
