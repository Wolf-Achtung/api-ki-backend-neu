# -*- coding: utf-8 -*-
"""
Sprint G33: Risk Engine 3.0 Tests
=================================

Comprehensive test suite for Risk Engine 3.0 with 60+ tests covering:
- Data structures (DPIAEntry, AIActConformity, RiskReportV3)
- DPIA determination logic
- AI Act conformity mapping
- Mitigation plan generation
- Residual risk calculation
- HTML generation
- Consistency Engine integration (RISK3_001-RISK3_008)

Version: 1.0.0 (Sprint G33)
"""
from __future__ import annotations

import pytest
from typing import Dict, Any, List, Optional


# =============================================================================
# TEST: Data Structures - DPIAEntry
# =============================================================================

class TestDPIAEntry:
    """Tests for DPIAEntry dataclass."""

    def test_basic_creation(self) -> None:
        """Test DPIAEntry can be instantiated with basic values."""
        from services.risk_engine_v3 import DPIAEntry

        entry = DPIAEntry(
            id="dpia_001",
            title="DPIA: Customer Service",
            description="DPIA for customer service chatbot",
            legal_basis="legitimate_interest",
            data_categories=["personal_basic", "personal_contact"],
            rights_risks=["Right to access", "Right to erasure"],
            mitigation_measures=["Data minimization", "Pseudonymization"],
            residual_risk="medium",
        )

        assert entry.id == "dpia_001"
        assert entry.title == "DPIA: Customer Service"
        assert entry.legal_basis == "legitimate_interest"
        assert entry.residual_risk == "medium"

    def test_invalid_legal_basis_normalized(self) -> None:
        """Test invalid legal_basis is normalized."""
        from services.risk_engine_v3 import DPIAEntry

        entry = DPIAEntry(
            id="dpia_001",
            title="Test",
            description="Test",
            legal_basis="invalid_basis",
        )

        assert entry.legal_basis == "legitimate_interest"

    def test_invalid_residual_risk_normalized(self) -> None:
        """Test invalid residual_risk is normalized."""
        from services.risk_engine_v3 import DPIAEntry

        entry = DPIAEntry(
            id="dpia_001",
            title="Test",
            description="Test",
            legal_basis="consent",
            residual_risk="extreme",
        )

        assert entry.residual_risk == "medium"

    def test_valid_residual_risks(self) -> None:
        """Test all valid residual_risk values."""
        from services.risk_engine_v3 import DPIAEntry, RESIDUAL_RISK_LEVELS

        for risk_level in RESIDUAL_RISK_LEVELS:
            entry = DPIAEntry(
                id="dpia_001",
                title="Test",
                description="Test",
                legal_basis="consent",
                residual_risk=risk_level,
            )
            assert entry.residual_risk == risk_level

    def test_has_sensitive_data_true(self) -> None:
        """Test has_sensitive_data property returns True for sensitive data."""
        from services.risk_engine_v3 import DPIAEntry

        entry = DPIAEntry(
            id="dpia_001",
            title="Test",
            description="Test",
            legal_basis="consent",
            data_categories=["sensitive_health", "personal_basic"],
        )

        assert entry.has_sensitive_data is True

    def test_has_sensitive_data_false(self) -> None:
        """Test has_sensitive_data property returns False for non-sensitive data."""
        from services.risk_engine_v3 import DPIAEntry

        entry = DPIAEntry(
            id="dpia_001",
            title="Test",
            description="Test",
            legal_basis="contract",
            data_categories=["personal_basic", "personal_contact"],
        )

        assert entry.has_sensitive_data is False

    def test_risk_score_calculation(self) -> None:
        """Test risk_score property calculation."""
        from services.risk_engine_v3 import DPIAEntry

        entry = DPIAEntry(
            id="dpia_001",
            title="Test",
            description="Test",
            legal_basis="consent",
            data_categories=["personal_basic"],
            rights_risks=["Risk 1", "Risk 2", "Risk 3", "Risk 4"],
            residual_risk="high",
        )

        # Base score for high is 3, plus 2 for 4 rights_risks (4//2=2)
        assert entry.risk_score >= 3

    def test_to_dict_serialization(self) -> None:
        """Test DPIAEntry serialization to dict."""
        from services.risk_engine_v3 import DPIAEntry

        entry = DPIAEntry(
            id="dpia_001",
            title="Test",
            description="Description",
            legal_basis="consent",
            data_categories=["personal_basic"],
            rights_risks=["Risk 1"],
            mitigation_measures=["Measure 1"],
            residual_risk="low",
        )

        data = entry.to_dict()

        assert data["id"] == "dpia_001"
        assert data["legal_basis"] == "consent"
        assert data["residual_risk"] == "low"
        assert "has_sensitive_data" in data
        assert "risk_score" in data

    def test_from_dict_deserialization(self) -> None:
        """Test DPIAEntry creation from dict."""
        from services.risk_engine_v3 import DPIAEntry

        data = {
            "id": "dpia_002",
            "title": "From Dict",
            "description": "Description",
            "legal_basis": "contract",
            "data_categories": ["personal_financial"],
            "rights_risks": ["Risk A"],
            "mitigation_measures": ["Measure A"],
            "residual_risk": "high",
        }

        entry = DPIAEntry.from_dict(data)

        assert entry.id == "dpia_002"
        assert entry.legal_basis == "contract"
        assert entry.residual_risk == "high"


# =============================================================================
# TEST: Data Structures - AIActConformity
# =============================================================================

class TestAIActConformity:
    """Tests for AIActConformity dataclass."""

    def test_basic_creation(self) -> None:
        """Test AIActConformity can be instantiated."""
        from services.risk_engine_v3 import AIActConformity

        conformity = AIActConformity(
            required_controls=["transparency_provision", "human_oversight"],
            implemented_controls=["transparency_provision"],
            missing_controls=["human_oversight"],
            conformity_score=0.5,
            risk_implications=["Missing human oversight"],
            remediation_timeline="phase_2",
        )

        assert len(conformity.required_controls) == 2
        assert len(conformity.implemented_controls) == 1
        assert len(conformity.missing_controls) == 1
        assert conformity.conformity_score == 0.5

    def test_conformity_score_clamped(self) -> None:
        """Test conformity_score is clamped to 0-1."""
        from services.risk_engine_v3 import AIActConformity

        conformity_high = AIActConformity(conformity_score=1.5)
        conformity_low = AIActConformity(conformity_score=-0.5)

        assert conformity_high.conformity_score == 1.0
        assert conformity_low.conformity_score == 0.0

    def test_auto_calculate_missing_controls(self) -> None:
        """Test missing_controls is auto-calculated if not provided."""
        from services.risk_engine_v3 import AIActConformity

        conformity = AIActConformity(
            required_controls=["control_a", "control_b", "control_c"],
            implemented_controls=["control_a"],
            missing_controls=[],  # Should be auto-calculated
        )

        assert "control_b" in conformity.missing_controls
        assert "control_c" in conformity.missing_controls
        assert "control_a" not in conformity.missing_controls

    def test_auto_calculate_conformity_score(self) -> None:
        """Test conformity_score is auto-calculated if zero."""
        from services.risk_engine_v3 import AIActConformity

        conformity = AIActConformity(
            required_controls=["control_a", "control_b", "control_c", "control_d"],
            implemented_controls=["control_a", "control_b"],
            conformity_score=0.0,  # Should be auto-calculated
        )

        assert conformity.conformity_score == 0.5  # 2/4

    def test_is_compliant_true(self) -> None:
        """Test is_compliant property returns True when score >= 0.8."""
        from services.risk_engine_v3 import AIActConformity

        conformity = AIActConformity(conformity_score=0.85)

        assert conformity.is_compliant is True

    def test_is_compliant_false(self) -> None:
        """Test is_compliant property returns False when score < 0.8."""
        from services.risk_engine_v3 import AIActConformity

        conformity = AIActConformity(conformity_score=0.7)

        assert conformity.is_compliant is False

    def test_conformity_grade_a(self) -> None:
        """Test conformity_grade returns A for score >= 0.9."""
        from services.risk_engine_v3 import AIActConformity

        conformity = AIActConformity(conformity_score=0.95)

        assert conformity.conformity_grade == "A"

    def test_conformity_grade_f(self) -> None:
        """Test conformity_grade returns F for score < 0.4."""
        from services.risk_engine_v3 import AIActConformity

        conformity = AIActConformity(conformity_score=0.3)

        assert conformity.conformity_grade == "F"

    def test_to_dict_serialization(self) -> None:
        """Test AIActConformity serialization to dict."""
        from services.risk_engine_v3 import AIActConformity

        conformity = AIActConformity(
            required_controls=["ctrl_a", "ctrl_b"],
            implemented_controls=["ctrl_a"],
            conformity_score=0.5,
        )

        data = conformity.to_dict()

        assert "required_controls" in data
        assert "implemented_controls" in data
        assert "missing_controls" in data
        assert "conformity_score" in data
        assert "conformity_grade" in data
        assert "is_compliant" in data

    def test_from_dict_deserialization(self) -> None:
        """Test AIActConformity creation from dict."""
        from services.risk_engine_v3 import AIActConformity

        data = {
            "required_controls": ["ctrl_a", "ctrl_b"],
            "implemented_controls": ["ctrl_a"],
            "missing_controls": ["ctrl_b"],
            "conformity_score": 0.5,
            "risk_implications": ["Risk 1"],
            "remediation_timeline": "phase_1",
        }

        conformity = AIActConformity.from_dict(data)

        assert len(conformity.required_controls) == 2
        assert conformity.conformity_score == 0.5
        assert conformity.remediation_timeline == "phase_1"


# =============================================================================
# TEST: Data Structures - RiskReportV3
# =============================================================================

class TestRiskReportV3:
    """Tests for RiskReportV3 dataclass."""

    def test_basic_creation(self) -> None:
        """Test RiskReportV3 can be instantiated."""
        from services.risk_engine_v3 import RiskReportV3, DPIAEntry, AIActConformity
        from services.risk_engine_v2 import RiskReport

        base = RiskReport(ai_act_class="high_risk")
        conformity = AIActConformity(conformity_score=0.7)
        dpia_entry = DPIAEntry(
            id="dpia_001",
            title="Test",
            description="Test",
            legal_basis="consent",
        )

        report = RiskReportV3(
            base=base,
            dpia_required=True,
            dpia_reason="High Risk AI",
            dpia_entries=[dpia_entry],
            ai_act_conformity=conformity,
            residual_risk_score=65.0,
        )

        assert report.dpia_required is True
        assert len(report.dpia_entries) == 1
        assert report.residual_risk_score == 65.0

    def test_residual_risk_score_clamped(self) -> None:
        """Test residual_risk_score is clamped to 0-100."""
        from services.risk_engine_v3 import RiskReportV3

        report_high = RiskReportV3(residual_risk_score=150.0)
        report_low = RiskReportV3(residual_risk_score=-50.0)

        assert report_high.residual_risk_score == 100.0
        assert report_low.residual_risk_score == 0.0

    def test_grade_auto_calculated(self) -> None:
        """Test residual_risk_grade is auto-calculated when invalid."""
        from services.risk_engine_v3 import RiskReportV3

        # Provide an invalid grade to trigger recalculation
        report = RiskReportV3(residual_risk_score=85.0, residual_risk_grade="X")

        assert report.residual_risk_grade == "A"

    def test_total_dpia_entries_property(self) -> None:
        """Test total_dpia_entries property."""
        from services.risk_engine_v3 import RiskReportV3, DPIAEntry

        entries = [
            DPIAEntry(id=f"dpia_{i}", title=f"Test {i}", description="D", legal_basis="consent")
            for i in range(3)
        ]

        report = RiskReportV3(dpia_entries=entries)

        assert report.total_dpia_entries == 3

    def test_high_risk_dpia_entries_property(self) -> None:
        """Test high_risk_dpia_entries property."""
        from services.risk_engine_v3 import RiskReportV3, DPIAEntry

        entries = [
            DPIAEntry(id="dpia_1", title="Low", description="D", legal_basis="consent", residual_risk="low"),
            DPIAEntry(id="dpia_2", title="High", description="D", legal_basis="consent", residual_risk="high"),
            DPIAEntry(id="dpia_3", title="Critical", description="D", legal_basis="consent", residual_risk="critical"),
        ]

        report = RiskReportV3(dpia_entries=entries)

        high_risk = report.high_risk_dpia_entries
        assert len(high_risk) == 2

    def test_sensitive_data_entries_property(self) -> None:
        """Test sensitive_data_entries property."""
        from services.risk_engine_v3 import RiskReportV3, DPIAEntry

        entries = [
            DPIAEntry(id="dpia_1", title="Normal", description="D", legal_basis="consent",
                     data_categories=["personal_basic"]),
            DPIAEntry(id="dpia_2", title="Sensitive", description="D", legal_basis="consent",
                     data_categories=["sensitive_health"]),
        ]

        report = RiskReportV3(dpia_entries=entries)

        sensitive = report.sensitive_data_entries
        assert len(sensitive) == 1
        assert sensitive[0].id == "dpia_2"

    def test_combined_risk_score_property(self) -> None:
        """Test combined_risk_score property calculation."""
        from services.risk_engine_v3 import RiskReportV3, AIActConformity
        from services.risk_engine_v2 import RiskReport

        base = RiskReport(ai_act_class="minimal", consolidated_score=70.0)
        conformity = AIActConformity(conformity_score=0.8)

        report = RiskReportV3(
            base=base,
            ai_act_conformity=conformity,
            residual_risk_score=60.0,
        )

        # Combined: 70*0.4 + 60*0.4 + 80*0.2 = 28 + 24 + 16 = 68
        assert 65 <= report.combined_risk_score <= 70

    def test_get_dpia_entry(self) -> None:
        """Test get_dpia_entry method."""
        from services.risk_engine_v3 import RiskReportV3, DPIAEntry

        entries = [
            DPIAEntry(id="dpia_1", title="Entry 1", description="D", legal_basis="consent"),
            DPIAEntry(id="dpia_2", title="Entry 2", description="D", legal_basis="contract"),
        ]

        report = RiskReportV3(dpia_entries=entries)

        assert report.get_dpia_entry("dpia_1").title == "Entry 1"
        assert report.get_dpia_entry("dpia_2").title == "Entry 2"
        assert report.get_dpia_entry("dpia_invalid") is None

    def test_to_dict_serialization(self) -> None:
        """Test RiskReportV3 serialization to dict."""
        from services.risk_engine_v3 import RiskReportV3

        report = RiskReportV3(
            dpia_required=True,
            dpia_reason="Test reason",
            residual_risk_score=65.0,
            compliance_status="partial",
        )

        data = report.to_dict()

        assert data["dpia_required"] is True
        assert data["dpia_reason"] == "Test reason"
        assert data["residual_risk_score"] == 65.0
        assert "combined_risk_score" in data
        assert "combined_grade" in data

    def test_from_dict_deserialization(self) -> None:
        """Test RiskReportV3 creation from dict."""
        from services.risk_engine_v3 import RiskReportV3

        data = {
            "base": {"ai_act_class": "high_risk"},
            "dpia_required": True,
            "dpia_reason": "High Risk",
            "dpia_entries": [],
            "ai_act_conformity": {"conformity_score": 0.6},
            "residual_risk_score": 55.0,
            "compliance_status": "partial",
        }

        report = RiskReportV3.from_dict(data)

        assert report.dpia_required is True
        assert report.residual_risk_score == 55.0


# =============================================================================
# TEST: Constants and Configuration
# =============================================================================

class TestConstants:
    """Tests for module constants."""

    def test_ai_act_controls_exist(self) -> None:
        """Test AI_ACT_ANNEX_III_CONTROLS are defined."""
        from services.risk_engine_v3 import AI_ACT_ANNEX_III_CONTROLS

        assert len(AI_ACT_ANNEX_III_CONTROLS) == 7
        assert "human_oversight" in AI_ACT_ANNEX_III_CONTROLS
        assert "transparency_provision" in AI_ACT_ANNEX_III_CONTROLS

    def test_data_categories_exist(self) -> None:
        """Test DSGVO_DATA_CATEGORIES are defined."""
        from services.risk_engine_v3 import DSGVO_DATA_CATEGORIES

        assert "personal_basic" in DSGVO_DATA_CATEGORIES
        assert "sensitive_health" in DSGVO_DATA_CATEGORIES
        assert "children_data" in DSGVO_DATA_CATEGORIES

    def test_legal_basis_options_exist(self) -> None:
        """Test LEGAL_BASIS_OPTIONS are defined."""
        from services.risk_engine_v3 import LEGAL_BASIS_OPTIONS

        assert "consent" in LEGAL_BASIS_OPTIONS
        assert "contract" in LEGAL_BASIS_OPTIONS
        assert "legitimate_interest" in LEGAL_BASIS_OPTIONS

    def test_size_constraints_exist(self) -> None:
        """Test SIZE_DPIA_LIMITS are defined."""
        from services.risk_engine_v3 import SIZE_DPIA_LIMITS

        assert "solo" in SIZE_DPIA_LIMITS
        assert "team" in SIZE_DPIA_LIMITS
        assert "kmu" in SIZE_DPIA_LIMITS

    def test_solo_constraints(self) -> None:
        """Test Solo size constraints."""
        from services.risk_engine_v3 import SIZE_DPIA_LIMITS

        solo = SIZE_DPIA_LIMITS["solo"]
        assert solo["max_dpia_entries"] == 3
        assert solo["max_controls"] == 4


# =============================================================================
# TEST: Report Generation
# =============================================================================

class TestReportGeneration:
    """Tests for report generation function."""

    def test_generate_with_empty_input(self) -> None:
        """Test report generation with minimal input."""
        from services.risk_engine_v3 import generate_risk_report_v3

        report = generate_risk_report_v3(
            briefing={"unternehmensgroesse": "Team", "branche": "IT"}
        )

        assert report is not None
        assert isinstance(report.dpia_required, bool)
        assert isinstance(report.residual_risk_score, float)

    def test_generate_with_high_risk_ai_act(self) -> None:
        """Test report generation with high-risk AI Act classification."""
        from services.risk_engine_v3 import generate_risk_report_v3
        from services.risk_engine_v2 import RiskReport

        base = RiskReport(ai_act_class="high_risk")

        report = generate_risk_report_v3(
            base_risk_report=base,
            briefing={"unternehmensgroesse": "KMU", "branche": "Gesundheit"}
        )

        # High-risk classification should require DPIA
        assert report.dpia_required is True

    def test_generate_with_sensitive_data(self) -> None:
        """Test report generation with sensitive data categories."""
        from services.risk_engine_v3 import generate_risk_report_v3

        report = generate_risk_report_v3(
            briefing={
                "unternehmensgroesse": "Team",
                "branche": "Gesundheitswesen",
                "datentypen": ["Gesundheitsdaten", "Patientenakte"],
            }
        )

        # Sensitive data should trigger DPIA
        assert report.dpia_required is True

    def test_generate_with_automated_decisions(self) -> None:
        """Test report generation with automated decisions."""
        from services.risk_engine_v3 import generate_risk_report_v3

        report = generate_risk_report_v3(
            briefing={
                "unternehmensgroesse": "KMU",
                "branche": "Finanzen",
                "automatisierte_entscheidungen": True,
            }
        )

        # Automated decisions should trigger DPIA
        assert report.dpia_required is True

    def test_generate_respects_size_limits(self) -> None:
        """Test generated DPIA entries respect size limits."""
        from services.risk_engine_v3 import generate_risk_report_v3
        from services.risk_engine_v2 import RiskReport

        base = RiskReport(ai_act_class="high_risk", dsgvo_risk_level="hoch")

        report = generate_risk_report_v3(
            base_risk_report=base,
            briefing={
                "unternehmensgroesse": "Solo/Freelancer",
                "branche": "IT",
                "automatisierte_entscheidungen": True,
            }
        )

        # Solo should have max 3 DPIA entries
        assert len(report.dpia_entries) <= 3

    def test_generate_creates_mitigation_plan(self) -> None:
        """Test mitigation plan is generated."""
        from services.risk_engine_v3 import generate_risk_report_v3
        from services.risk_engine_v2 import RiskReport

        base = RiskReport(ai_act_class="high_risk")

        report = generate_risk_report_v3(
            base_risk_report=base,
            briefing={"unternehmensgroesse": "KMU", "branche": "IT"}
        )

        assert len(report.mitigation_plan) > 0

    def test_generate_calculates_compliance_status(self) -> None:
        """Test compliance status is calculated."""
        from services.risk_engine_v3 import generate_risk_report_v3

        report = generate_risk_report_v3(
            briefing={"unternehmensgroesse": "Team", "branche": "Handel"}
        )

        assert report.compliance_status in ["compliant", "partial", "non_compliant"]


# =============================================================================
# TEST: HTML Generation
# =============================================================================

class TestHTMLGeneration:
    """Tests for HTML rendering function."""

    def test_html_contains_dpia_status(self) -> None:
        """Test HTML includes DPIA status."""
        from services.risk_engine_v3 import RiskReportV3, risk_report_v3_to_html

        report = RiskReportV3(dpia_required=True, dpia_reason="Test reason")
        html = risk_report_v3_to_html(report, lang="de")

        assert "DPIA" in html
        assert "Test reason" in html

    def test_html_contains_conformity_score(self) -> None:
        """Test HTML includes conformity score."""
        from services.risk_engine_v3 import RiskReportV3, AIActConformity, risk_report_v3_to_html

        conformity = AIActConformity(conformity_score=0.75)
        report = RiskReportV3(ai_act_conformity=conformity)
        html = risk_report_v3_to_html(report, lang="de")

        assert "75" in html  # 75%

    def test_html_german_labels(self) -> None:
        """Test HTML uses German labels."""
        from services.risk_engine_v3 import RiskReportV3, risk_report_v3_to_html

        report = RiskReportV3(dpia_required=True)
        html = risk_report_v3_to_html(report, lang="de")

        assert "Konformität" in html or "DPIA" in html

    def test_html_english_labels(self) -> None:
        """Test HTML uses English labels."""
        from services.risk_engine_v3 import RiskReportV3, risk_report_v3_to_html

        report = RiskReportV3(dpia_required=True)
        html = risk_report_v3_to_html(report, lang="en")

        assert "Conformity" in html or "DPIA" in html

    def test_html_includes_dpia_entries(self) -> None:
        """Test HTML includes DPIA entries."""
        from services.risk_engine_v3 import RiskReportV3, DPIAEntry, risk_report_v3_to_html

        entry = DPIAEntry(
            id="dpia_001",
            title="Customer Data Processing",
            description="Processing of customer data",
            legal_basis="consent",
        )
        report = RiskReportV3(dpia_entries=[entry])
        html = risk_report_v3_to_html(report, lang="de")

        assert "Customer Data Processing" in html

    def test_html_includes_missing_controls(self) -> None:
        """Test HTML includes missing controls."""
        from services.risk_engine_v3 import RiskReportV3, AIActConformity, risk_report_v3_to_html

        conformity = AIActConformity(
            required_controls=["human_oversight", "transparency_provision"],
            implemented_controls=[],
            missing_controls=["human_oversight", "transparency_provision"],
        )
        report = RiskReportV3(ai_act_conformity=conformity)
        html = risk_report_v3_to_html(report, lang="de")

        # Should show missing count or controls
        assert "2" in html or "Fehlend" in html or "Missing" in html

    def test_html_includes_compliance_status(self) -> None:
        """Test HTML includes compliance status."""
        from services.risk_engine_v3 import RiskReportV3, risk_report_v3_to_html

        report = RiskReportV3(compliance_status="partial")
        html = risk_report_v3_to_html(report, lang="de")

        assert "Konform" in html or "Compliance" in html

    def test_html_g33_badge(self) -> None:
        """Test HTML includes G33 sprint badge."""
        from services.risk_engine_v3 import RiskReportV3, risk_report_v3_to_html

        report = RiskReportV3()
        html = risk_report_v3_to_html(report, lang="de")

        assert "G33" in html


# =============================================================================
# TEST: Validation Functions
# =============================================================================

class TestValidationFunctions:
    """Tests for validation helper functions."""

    def test_validate_dpia_required_with_strategy(self) -> None:
        """Test DPIA validation passes when strategy has measures."""
        from services.risk_engine_v3 import RiskReportV3, validate_dpia_required

        report = RiskReportV3(dpia_required=True)

        # Mock strategy data with DPIA keywords
        class MockStrategy:
            phases = [type('obj', (object,), {'focus': 'Implement DPIA measures'})()]

        is_valid, errors = validate_dpia_required(report, MockStrategy())

        assert is_valid is True

    def test_validate_dpia_required_without_strategy(self) -> None:
        """Test DPIA validation fails when strategy missing."""
        from services.risk_engine_v3 import RiskReportV3, validate_dpia_required

        report = RiskReportV3(dpia_required=True)

        is_valid, errors = validate_dpia_required(report, None)

        assert is_valid is False
        assert len(errors) >= 1

    def test_validate_ai_act_conformity_with_strategy(self) -> None:
        """Test AI Act conformity validation."""
        from services.risk_engine_v3 import RiskReportV3, AIActConformity, validate_ai_act_conformity

        conformity = AIActConformity(missing_controls=["human_oversight"])
        report = RiskReportV3(ai_act_conformity=conformity)

        # Mock strategy with control implementation
        class MockStrategy:
            phases = [type('obj', (object,), {'focus': 'Implement human oversight'})()]

        is_valid, errors = validate_ai_act_conformity(report, MockStrategy())

        assert is_valid is True


# =============================================================================
# TEST: Consistency Engine Integration
# =============================================================================

class TestConsistencyEngineIntegration:
    """Tests for consistency engine RISK3_001-RISK3_008 rules."""

    def test_risk3_domain_in_consistency_engine(self) -> None:
        """Test 'risk_engine_v3' domain exists in consistency engine."""
        from services.consistency_engine import ConsistencyEngine

        sections = {"RISK_ENGINE_V3_HTML": "<div>test</div>"}
        briefing = {"unternehmensgroesse": "Team"}

        engine = ConsistencyEngine(sections, briefing)
        report = engine.check_all()

        assert "risk_engine_v3" in report.domain_scores

    def test_consistency_skips_without_v3_html(self) -> None:
        """Test consistency check skips when no risk_v3 HTML."""
        from services.consistency_engine import ConsistencyEngine

        sections = {}
        briefing = {"unternehmensgroesse": "Team"}

        engine = ConsistencyEngine(sections, briefing)
        report = engine.check_all()

        # No RISK3 issues when section missing
        risk3_issues = [i for i in report.issues if i.rule_id.startswith("RISK3_")]
        assert len(risk3_issues) == 0


# =============================================================================
# TEST: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_dpia_entries_list(self) -> None:
        """Test report with empty DPIA entries list."""
        from services.risk_engine_v3 import RiskReportV3

        report = RiskReportV3(dpia_entries=[])

        assert report.total_dpia_entries == 0
        assert len(report.high_risk_dpia_entries) == 0

    def test_none_values_in_dpia_entry(self) -> None:
        """Test DPIAEntry handles None values in lists."""
        from services.risk_engine_v3 import DPIAEntry

        entry = DPIAEntry(
            id="dpia_001",
            title="Test",
            description="Test",
            legal_basis="consent",
            data_categories=None,  # type: ignore
            rights_risks=None,  # type: ignore
            mitigation_measures=None,  # type: ignore
        )

        assert entry.data_categories == []
        assert entry.rights_risks == []
        assert entry.mitigation_measures == []

    def test_empty_ai_act_conformity(self) -> None:
        """Test AIActConformity with empty controls."""
        from services.risk_engine_v3 import AIActConformity

        conformity = AIActConformity(
            required_controls=[],
            implemented_controls=[],
        )

        assert conformity.conformity_score == 0.0
        assert len(conformity.missing_controls) == 0

    def test_determine_size_label(self) -> None:
        """Test _determine_size_label function."""
        from services.risk_engine_v3 import _determine_size_label

        assert _determine_size_label({"unternehmensgroesse": "Solo/Freelancer"}) == "solo"
        assert _determine_size_label({"unternehmensgroesse": "Freiberufler"}) == "solo"
        assert _determine_size_label({"unternehmensgroesse": "Team (2-10 MA)"}) == "team"
        assert _determine_size_label({"unternehmensgroesse": "KMU (>10 Mitarbeiter)"}) == "kmu"
        assert _determine_size_label({}) == "team"
        assert _determine_size_label(None) == "team"


# =============================================================================
# TEST: Module Loading
# =============================================================================

class TestModuleLoading:
    """Tests for module loading and exports."""

    def test_module_exports(self) -> None:
        """Test all expected exports are available."""
        from services.risk_engine_v3 import (
            DPIAEntry,
            AIActConformity,
            RiskReportV3,
            generate_risk_report_v3,
            risk_report_v3_to_html,
            RISK_ENGINE_V3_ENABLED,
        )

        assert DPIAEntry is not None
        assert AIActConformity is not None
        assert RiskReportV3 is not None
        assert generate_risk_report_v3 is not None
        assert risk_report_v3_to_html is not None
        assert RISK_ENGINE_V3_ENABLED is True

    def test_imports_from_risk_engine_v2(self) -> None:
        """Test Risk Engine V3 properly imports from V2."""
        from services.risk_engine_v3 import (
            RiskReport,
            RiskMatrixEntry,
        )

        # These should be re-exported from v2
        assert RiskReport is not None
        assert RiskMatrixEntry is not None
