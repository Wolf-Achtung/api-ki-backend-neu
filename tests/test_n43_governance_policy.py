# -*- coding: utf-8 -*-
"""
N4.3 Test Suite: Governance Policy Engine v2
============================================

Tests for services/governance_policy_engine_v2.py

Coverage:
- AI Act risk classification
- ISO 42001 mapping
- NIST AI RMF integration
- Control derivation
- Policy card generation
- Governance score computation
- Self-healing (conflict resolution)

Target: ~30 tests

Version: 1.0.0 (N4.3 - PLATIN+++ v5.3)
"""

import pytest
from typing import Dict, Any

from services.governance_policy_engine_v2 import (
    AIActRiskClass,
    GovernanceFramework,
    MaturityLevel,
    ControlType,
    DPIAStatus,
    CompanySize,
    PolicyCard,
    GovernanceControl,
    GovernanceMatrix,
    GovernanceScore,
    GovernancePolicyEngineV2,
    generate_governance_matrix,
    derive_controls,
    map_to_iso42001,
    map_to_nist_rmf,
    compute_governance_score,
    get_policy_cards,
    validate_governance_compliance,
    EU_AI_ACT_HIGH_RISK_AREAS,
    ISO_42001_DOMAINS,
    NIST_AI_RMF_FUNCTIONS,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_sections() -> Dict[str, Any]:
    """Sample sections for testing."""
    return {
        "executive_summary": "AI system with ROI 150%",
        "risks": "Low risk implementation with governance controls",
        "governance": "AI policy documented. Risk assessment performed.",
        "recommendations": "Implement monitoring and continuous improvement.",
    }


@pytest.fixture
def sample_briefing() -> Dict[str, Any]:
    """Sample briefing for testing."""
    return {
        "company_name": "TechCorp GmbH",
        "lang": "de",
        "ai_use_cases": ["document_classification", "chatbot"],
        "data_types": ["text", "metadata"],
        "deployment_context": "internal",
        "human_oversight": True,
    }


@pytest.fixture
def high_risk_briefing() -> Dict[str, Any]:
    """High-risk briefing for testing."""
    return {
        "company_name": "HealthCare AG",
        "lang": "de",
        "ai_use_cases": ["patient_diagnosis", "treatment_recommendation"],
        "data_types": ["health", "biometric"],
        "deployment_context": "clinical",
        "human_oversight": True,
    }


# =============================================================================
# TEST CLASS: Enums
# =============================================================================

class TestGovernanceEnums:
    """Tests for governance enums."""

    def test_ai_act_risk_class_values(self):
        """All risk classes should be defined."""
        assert AIActRiskClass.UNACCEPTABLE.value == "unacceptable"
        assert AIActRiskClass.HIGH.value == "high"
        assert AIActRiskClass.LIMITED.value == "limited"
        assert AIActRiskClass.MINIMAL.value == "minimal"

    def test_governance_framework_values(self):
        """All frameworks should be defined."""
        assert GovernanceFramework.EU_AI_ACT.value == "eu_ai_act"
        assert GovernanceFramework.ISO_42001.value == "iso_42001"
        assert GovernanceFramework.NIST_AI_RMF.value == "nist_ai_rmf"
        assert GovernanceFramework.COMBINED.value == "combined"

    def test_maturity_level_values(self):
        """All maturity levels should be defined."""
        assert MaturityLevel.INITIAL.value == "initial"
        assert MaturityLevel.DEVELOPING.value == "developing"
        assert MaturityLevel.DEFINED.value == "defined"
        assert MaturityLevel.MANAGED.value == "managed"
        assert MaturityLevel.OPTIMIZING.value == "optimizing"

    def test_control_type_values(self):
        """All control types should be defined."""
        assert ControlType.PREVENTIVE.value == "preventive"
        assert ControlType.DETECTIVE.value == "detective"
        assert ControlType.CORRECTIVE.value == "corrective"
        assert ControlType.DIRECTIVE.value == "directive"

    def test_dpia_status_values(self):
        """All DPIA statuses should be defined."""
        assert DPIAStatus.NOT_REQUIRED.value == "not_required"
        assert DPIAStatus.REQUIRED_NOT_STARTED.value == "required_not_started"
        assert DPIAStatus.IN_PROGRESS.value == "in_progress"
        assert DPIAStatus.COMPLETED_APPROVED.value == "completed_approved"


# =============================================================================
# TEST CLASS: Constants
# =============================================================================

class TestGovernanceConstants:
    """Tests for governance constants."""

    def test_eu_ai_act_high_risk_areas(self):
        """High-risk areas should be defined."""
        assert "biometric" in EU_AI_ACT_HIGH_RISK_AREAS
        assert "employment" in EU_AI_ACT_HIGH_RISK_AREAS
        assert "critical_infrastructure" in EU_AI_ACT_HIGH_RISK_AREAS
        assert "education" in EU_AI_ACT_HIGH_RISK_AREAS

    def test_iso_42001_domains(self):
        """ISO 42001 domains should be defined."""
        assert "context" in ISO_42001_DOMAINS
        assert "leadership" in ISO_42001_DOMAINS
        assert "planning" in ISO_42001_DOMAINS
        assert "support" in ISO_42001_DOMAINS
        assert "operation" in ISO_42001_DOMAINS
        assert "performance" in ISO_42001_DOMAINS
        assert "improvement" in ISO_42001_DOMAINS

    def test_nist_ai_rmf_functions(self):
        """NIST AI RMF functions should be defined."""
        assert "govern" in NIST_AI_RMF_FUNCTIONS
        assert "map" in NIST_AI_RMF_FUNCTIONS
        assert "measure" in NIST_AI_RMF_FUNCTIONS
        assert "manage" in NIST_AI_RMF_FUNCTIONS


# =============================================================================
# TEST CLASS: Data Structures
# =============================================================================

class TestDataStructures:
    """Tests for data structures."""

    def test_governance_control_to_dict(self):
        """GovernanceControl should serialize to dict."""
        control = GovernanceControl(
            control_id="GOV-001",
            name="Test Control",
            description="Test description",
            control_type=ControlType.PREVENTIVE,
            framework=GovernanceFramework.EU_AI_ACT,
            priority=1,
        )
        d = control.to_dict()
        assert d["control_id"] == "GOV-001"
        assert d["control_type"] == "preventive"
        assert d["framework"] == "eu_ai_act"

    def test_policy_card_to_dict(self):
        """PolicyCard should serialize to dict."""
        card = PolicyCard(
            card_id="PC-001",
            title="Test Card",
            category="test",
            summary="Test summary",
            status="compliant",
            score=85,
        )
        d = card.to_dict()
        assert d["card_id"] == "PC-001"
        assert d["status"] == "compliant"
        assert d["score"] == 85

    def test_governance_matrix_to_dict(self):
        """GovernanceMatrix should serialize to dict."""
        matrix = GovernanceMatrix(
            risk_class=AIActRiskClass.LIMITED,
            maturity_level=MaturityLevel.DEFINED,
            dpia_status=DPIAStatus.NOT_REQUIRED,
            frameworks=[GovernanceFramework.EU_AI_ACT],
        )
        d = matrix.to_dict()
        assert d["risk_class"] == "limited"
        assert d["maturity_level"] == "defined"

    def test_governance_score_to_dict(self):
        """GovernanceScore should serialize to dict."""
        score = GovernanceScore(
            overall_score=75,
            maturity_level=MaturityLevel.MANAGED,
            framework_scores={"eu_ai_act": 80},
        )
        d = score.to_dict()
        assert d["overall_score"] == 75
        assert d["maturity_level"] == "managed"


# =============================================================================
# TEST CLASS: Engine Initialization
# =============================================================================

class TestEngineInitialization:
    """Tests for engine initialization."""

    def test_engine_init_default(self, sample_sections, sample_briefing):
        """Engine should initialize with defaults."""
        engine = GovernancePolicyEngineV2(
            sections=sample_sections,
            briefing=sample_briefing,
        )
        assert engine.branch == "consulting"
        assert engine.size == CompanySize.TEAM

    def test_engine_init_with_branch(self, sample_sections, sample_briefing):
        """Engine should accept branch parameter."""
        engine = GovernancePolicyEngineV2(
            sections=sample_sections,
            briefing=sample_briefing,
            branch="healthcare",
        )
        assert engine.branch == "healthcare"

    def test_engine_init_with_size(self, sample_sections, sample_briefing):
        """Engine should accept size parameter."""
        engine = GovernancePolicyEngineV2(
            sections=sample_sections,
            briefing=sample_briefing,
            size="enterprise",
        )
        assert engine.size == CompanySize.ENTERPRISE

    def test_engine_init_invalid_size_fallback(self, sample_sections, sample_briefing):
        """Engine should fallback for invalid size."""
        engine = GovernancePolicyEngineV2(
            sections=sample_sections,
            briefing=sample_briefing,
            size="invalid",
        )
        assert engine.size == CompanySize.TEAM


# =============================================================================
# TEST CLASS: Risk Classification
# =============================================================================

class TestRiskClassification:
    """Tests for AI Act risk classification."""

    def test_minimal_risk_classification(self, sample_sections, sample_briefing):
        """Standard use case should be minimal risk."""
        engine = GovernancePolicyEngineV2(
            sections=sample_sections,
            briefing=sample_briefing,
            branch="consulting",
        )
        engine._extract_risk_data()
        risk_class = engine._classify_ai_act_risk()
        assert risk_class in (AIActRiskClass.MINIMAL, AIActRiskClass.LIMITED)

    def test_high_risk_healthcare(self, sample_sections, high_risk_briefing):
        """Healthcare with health data should be high risk."""
        engine = GovernancePolicyEngineV2(
            sections=sample_sections,
            briefing=high_risk_briefing,
            branch="healthcare",
        )
        engine._extract_risk_data()
        risk_class = engine._classify_ai_act_risk()
        assert risk_class == AIActRiskClass.HIGH

    def test_high_risk_biometric_data(self, sample_sections, sample_briefing):
        """Biometric data should trigger high risk."""
        briefing = dict(sample_briefing)
        briefing["data_types"] = ["biometric", "facial_recognition"]
        briefing["ai_use_cases"] = ["biometric_identification"]

        engine = GovernancePolicyEngineV2(
            sections=sample_sections,
            briefing=briefing,
        )
        engine._extract_risk_data()
        risk_class = engine._classify_ai_act_risk()
        assert risk_class == AIActRiskClass.HIGH


# =============================================================================
# TEST CLASS: Maturity Assessment
# =============================================================================

class TestMaturityAssessment:
    """Tests for maturity level assessment."""

    def test_initial_maturity_empty_sections(self, sample_briefing):
        """Empty sections should result in initial maturity."""
        engine = GovernancePolicyEngineV2(
            sections={},
            briefing=sample_briefing,
        )
        engine._extract_risk_data()
        maturity = engine._assess_maturity_level()
        assert maturity == MaturityLevel.INITIAL

    def test_developing_maturity_with_policy(self, sample_briefing):
        """Policy mention should increase maturity."""
        sections = {
            "governance": "We have an AI policy and risk assessment process.",
        }
        engine = GovernancePolicyEngineV2(
            sections=sections,
            briefing=sample_briefing,
        )
        engine._extract_risk_data()
        maturity = engine._assess_maturity_level()
        assert maturity in (MaturityLevel.DEVELOPING, MaturityLevel.DEFINED)


# =============================================================================
# TEST CLASS: Control Derivation
# =============================================================================

class TestControlDerivation:
    """Tests for control derivation."""

    def test_derive_controls_minimal_risk(self):
        """Minimal risk should have base controls."""
        controls = derive_controls(
            ai_act_class="minimal",
            risk_level="low",
            maturity="initial",
            dpia_status="not_required",
        )
        assert len(controls) >= 3
        assert any(c.control_id == "GOV-001" for c in controls)

    def test_derive_controls_high_risk(self):
        """High risk should have additional controls."""
        controls = derive_controls(
            ai_act_class="high",
            risk_level="high",
            maturity="developing",
            dpia_status="required_not_started",
        )
        assert len(controls) >= 5
        # Should have high-risk specific controls
        assert any("HIGH" in c.control_id for c in controls)
        # Should have DPIA control
        assert any("DPIA" in c.control_id for c in controls)


# =============================================================================
# TEST CLASS: Framework Mapping
# =============================================================================

class TestFrameworkMapping:
    """Tests for framework mapping."""

    def test_map_to_iso42001(self, sample_sections, sample_briefing):
        """ISO 42001 mapping should cover all domains."""
        mapping = map_to_iso42001(sample_sections, sample_briefing)
        assert len(mapping) == 7  # 7 ISO domains
        assert "context" in mapping
        assert "leadership" in mapping

    def test_map_to_nist_rmf(self, sample_sections, sample_briefing):
        """NIST RMF mapping should cover all functions."""
        mapping = map_to_nist_rmf(sample_sections, sample_briefing)
        assert len(mapping) == 4  # 4 NIST functions
        assert "govern" in mapping
        assert "map" in mapping
        assert "measure" in mapping
        assert "manage" in mapping


# =============================================================================
# TEST CLASS: Score Computation
# =============================================================================

class TestScoreComputation:
    """Tests for governance score computation."""

    def test_compute_score_returns_score(self, sample_sections, sample_briefing):
        """Score computation should return GovernanceScore."""
        score = compute_governance_score(sample_sections, sample_briefing)
        assert isinstance(score, GovernanceScore)
        assert 0 <= score.overall_score <= 100

    def test_compute_score_framework_scores(self, sample_sections, sample_briefing):
        """Score should include framework-specific scores."""
        score = compute_governance_score(sample_sections, sample_briefing)
        assert "eu_ai_act" in score.framework_scores
        assert "iso_42001" in score.framework_scores
        assert "nist_ai_rmf" in score.framework_scores


# =============================================================================
# TEST CLASS: Policy Cards
# =============================================================================

class TestPolicyCards:
    """Tests for policy card generation."""

    def test_get_policy_cards_returns_list(self, sample_sections, sample_briefing):
        """Policy cards should be returned as list."""
        cards = get_policy_cards(sample_sections, sample_briefing)
        assert isinstance(cards, list)
        assert len(cards) >= 3

    def test_policy_cards_have_required_fields(self, sample_sections, sample_briefing):
        """Policy cards should have required fields."""
        cards = get_policy_cards(sample_sections, sample_briefing)
        for card in cards:
            assert "card_id" in card
            assert "title" in card
            assert "status" in card
            assert "score" in card


# =============================================================================
# TEST CLASS: Governance Validation
# =============================================================================

class TestGovernanceValidation:
    """Tests for governance validation."""

    def test_validate_compliance_returns_tuple(self, sample_sections, sample_briefing):
        """Validation should return tuple."""
        is_valid, details = validate_governance_compliance(
            sample_sections, sample_briefing
        )
        assert isinstance(is_valid, bool)
        assert isinstance(details, dict)

    def test_validation_details_structure(self, sample_sections, sample_briefing):
        """Validation details should have expected structure."""
        _, details = validate_governance_compliance(
            sample_sections, sample_briefing
        )
        assert "validated" in details
        assert "score" in details
        assert "risk_class" in details


# =============================================================================
# TEST CLASS: Full Processing
# =============================================================================

class TestFullProcessing:
    """Tests for full engine processing."""

    def test_process_returns_sections_and_report(self, sample_sections, sample_briefing):
        """Process should return sections and report."""
        engine = GovernancePolicyEngineV2(
            sections=sample_sections,
            briefing=sample_briefing,
        )
        result_sections, report = engine.process()

        assert isinstance(result_sections, dict)
        assert "_governance_validated" in result_sections
        assert "_governance_score" in result_sections

    def test_process_adds_metadata(self, sample_sections, sample_briefing):
        """Process should add governance metadata."""
        engine = GovernancePolicyEngineV2(
            sections=sample_sections,
            briefing=sample_briefing,
        )
        result_sections, _ = engine.process()

        assert "_governance_matrix" in result_sections
        assert "_governance_report" in result_sections
        assert "_policy_cards" in result_sections

    def test_process_report_success(self, sample_sections, sample_briefing):
        """Process report should indicate success."""
        engine = GovernancePolicyEngineV2(
            sections=sample_sections,
            briefing=sample_briefing,
        )
        _, report = engine.process()

        assert report.engine_id == "GOVERNANCE_POLICY_V2"
        assert report.controls_derived > 0


# =============================================================================
# TEST CLASS: Self-Healing
# =============================================================================

class TestSelfHealing:
    """Tests for self-healing (conflict resolution)."""

    def test_detect_conflicts_high_risk_no_controls(self, sample_briefing):
        """Should detect insufficient controls for high risk."""
        engine = GovernancePolicyEngineV2(
            sections={},
            briefing=sample_briefing,
            branch="healthcare",
        )
        engine._extract_risk_data()

        # Force high risk classification
        engine._matrix = GovernanceMatrix(
            risk_class=AIActRiskClass.HIGH,
            maturity_level=MaturityLevel.INITIAL,
            dpia_status=DPIAStatus.REQUIRED_NOT_STARTED,
            frameworks=[GovernanceFramework.EU_AI_ACT],
            controls=[],  # No controls
        )

        conflicts = engine._detect_governance_conflicts()
        assert len(conflicts) > 0

    def test_resolve_conflicts_adds_controls(self, sample_briefing):
        """Resolving conflicts should add controls."""
        engine = GovernancePolicyEngineV2(
            sections={},
            briefing=sample_briefing,
        )

        engine._matrix = GovernanceMatrix(
            risk_class=AIActRiskClass.HIGH,
            maturity_level=MaturityLevel.INITIAL,
            dpia_status=DPIAStatus.REQUIRED_NOT_STARTED,
            frameworks=[GovernanceFramework.EU_AI_ACT],
            controls=[],
        )

        conflicts = [{"type": "insufficient_controls", "severity": "high"}]
        resolved = engine._resolve_governance_conflicts(conflicts)

        assert resolved >= 1
        assert len(engine._matrix.controls) > 0
