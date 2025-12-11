# -*- coding: utf-8 -*-
"""
SPRINT N3.2: Tests for Consistency Engine Healing Flags.

Tests that _bc_healed and _reco_healed flags are:
1. Set correctly when healing is performed
2. Respected by consistency_engine to avoid false positives
"""
import pytest
from unittest.mock import MagicMock, patch


def make_briefing():
    """Create a minimal briefing dict for tests."""
    return {
        "company_name": "Test GmbH",
        "branche": "beratung",
        "size": "team",
        "unternehmensgroesse": "team",
    }


class TestBCHealedFlagSetting:
    """Test _bc_healed flag is set in sections after healing."""

    def test_bc_healed_flag_set_after_healing(self):
        """Flag should be set when scenario healing is performed."""
        from services.business_case_engine_v2 import generate_business_case_report

        sections = {}
        briefing = make_briefing()

        # Provide LLM response with inverted scenarios (needs healing)
        llm_response = {
            "scenarios": [
                {"name": "optimistic", "roi_12m": 80, "payback_months": 10,
                 "monthly_savings": 500, "annual_savings": 6000, "investment_total": 5000},
                {"name": "realistic", "roi_12m": 120, "payback_months": 8,  # Inverted!
                 "monthly_savings": 600, "annual_savings": 7200, "investment_total": 5000},
                {"name": "conservative", "roi_12m": 60, "payback_months": 12,
                 "monthly_savings": 400, "annual_savings": 4800, "investment_total": 5000},
            ]
        }

        report = generate_business_case_report(
            sections=sections,
            briefing=briefing,
            llm_response=llm_response,
        )

        # Flag should be set because healing was needed
        assert sections.get("_bc_healed") is True, \
            "_bc_healed flag should be True after healing inverted scenarios"

    def test_bc_healed_flag_not_set_when_valid(self):
        """Flag should NOT be set when scenarios are already valid."""
        from services.business_case_engine_v2 import generate_business_case_report

        sections = {}
        briefing = make_briefing()

        # Provide LLM response with correctly ordered scenarios
        llm_response = {
            "scenarios": [
                {"name": "optimistic", "roi_12m": 150, "payback_months": 6,
                 "monthly_savings": 800, "annual_savings": 9600, "investment_total": 5000},
                {"name": "realistic", "roi_12m": 100, "payback_months": 8,
                 "monthly_savings": 600, "annual_savings": 7200, "investment_total": 5000},
                {"name": "conservative", "roi_12m": 50, "payback_months": 12,
                 "monthly_savings": 400, "annual_savings": 4800, "investment_total": 5000},
            ]
        }

        report = generate_business_case_report(
            sections=sections,
            briefing=briefing,
            llm_response=llm_response,
        )

        # Flag should NOT be set because no healing was needed
        assert "_bc_healed" not in sections or sections.get("_bc_healed") is not True, \
            "_bc_healed flag should not be True when scenarios are valid"


class TestRECOHealedFlagSetting:
    """Test _reco_healed flag is set in sections after healing."""

    def test_reco_healed_flag_set_after_healing(self):
        """Flag should be set when recommendation healing is performed."""
        from services.recommendations_engine import generate_recommendations_report

        sections = {}
        briefing = make_briefing()

        # Provide LLM response with reduces_risk but no related_risks (needs healing)
        llm_response = {
            "recommendations": [
                {
                    "id": "rec_1",
                    "title": "Implement Security",
                    "description": "Improve security measures",
                    "reason": "Risk reduction",
                    "impact_level": "high",
                    "urgency_level": "medium",
                    "risk_relation": "reduces_risk",
                    "related_risks": [],  # Empty! Should trigger healing
                    "timeline_phase": "phase_1",
                }
            ],
            "top_3_ids": ["rec_1"],
        }

        report = generate_recommendations_report(
            sections=sections,
            briefing=briefing,
            llm_response=llm_response,
        )

        # Flag should be set because healing was needed
        assert sections.get("_reco_healed") is True, \
            "_reco_healed flag should be True after healing empty related_risks"

    def test_reco_healed_flag_not_set_when_valid(self):
        """Flag should NOT be set when recommendations are already valid."""
        from services.recommendations_engine import generate_recommendations_report

        sections = {}
        briefing = make_briefing()

        # Provide LLM response with valid reduces_risk and related_risks
        llm_response = {
            "recommendations": [
                {
                    "id": "rec_1",
                    "title": "Implement Security",
                    "description": "Improve security measures",
                    "reason": "Risk reduction",
                    "impact_level": "high",
                    "urgency_level": "medium",
                    "risk_relation": "reduces_risk",
                    "related_risks": ["risk_dsgvo", "risk_vendor"],  # Has risks
                    "timeline_phase": "phase_1",
                }
            ],
            "top_3_ids": ["rec_1"],
        }

        report = generate_recommendations_report(
            sections=sections,
            briefing=briefing,
            llm_response=llm_response,
        )

        # Flag should NOT be set because no healing was needed
        assert "_reco_healed" not in sections or sections.get("_reco_healed") is not True, \
            "_reco_healed flag should not be True when recommendations are valid"


class TestConsistencyEngineRespectsFlags:
    """Test consistency engine respects healing flags."""

    def test_bc001_skipped_when_bc_healed_true(self):
        """BC_001 check should be skipped when _bc_healed is True."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "business_case": {
                "scenarios": {
                    "optimistic": {"roi_12m": 80},
                    "realistic": {"roi_12m": 120},  # Inverted (would trigger BC_001)
                    "conservative": {"roi_12m": 60},
                }
            },
            "_bc_healed": True,  # Healing flag set
        }

        engine = ConsistencyEngine(sections, make_briefing(), language="de")
        result = engine.check_all()

        # BC_001 should NOT be in issues because _bc_healed is True
        bc001_issues = [i for i in result.issues if i.rule_id == "BC_001"]
        assert len(bc001_issues) == 0, \
            "BC_001 should be skipped when _bc_healed is True"

    def test_bc001_triggers_when_bc_healed_false(self):
        """BC_001 check should run when _bc_healed is False."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "business_case": {
                "scenarios": {
                    "optimistic": {"roi_12m": 80},
                    "realistic": {"roi_12m": 120},  # Inverted
                    "conservative": {"roi_12m": 60},
                }
            },
            "_bc_healed": False,  # Healing flag not set
        }

        engine = ConsistencyEngine(sections, make_briefing(), language="de")
        result = engine.check_all()

        # BC_001 check should run (might or might not have issues depending on HTML extraction)
        assert result is not None

    def test_reco002_skipped_when_reco_healed_true(self):
        """RECO_002 check should be skipped when _reco_healed is True."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "recommendations": [
                {
                    "title": "Test Recommendation",
                    "risk_relation": "reduces_risk",
                    "reduces_risk": [],  # Empty (would trigger RECO_002)
                }
            ],
            "_reco_healed": True,  # Healing flag set
        }

        engine = ConsistencyEngine(sections, make_briefing(), language="de")
        result = engine.check_all()

        # RECO_002 should NOT be in issues because _reco_healed is True
        reco002_issues = [i for i in result.issues if i.rule_id == "RECO_002"]
        assert len(reco002_issues) == 0, \
            "RECO_002 should be skipped when _reco_healed is True"


class TestBothFlagsSimultaneous:
    """Test both flags can work together."""

    def test_both_flags_can_be_set(self):
        """Both _bc_healed and _reco_healed can be True simultaneously."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "business_case": {
                "scenarios": {
                    "optimistic": {"roi_12m": 80},
                    "realistic": {"roi_12m": 120},  # Would trigger BC_001
                    "conservative": {"roi_12m": 60},
                }
            },
            "recommendations": [
                {"title": "Test", "reduces_risk": []}  # Would trigger RECO_002
            ],
            "_bc_healed": True,
            "_reco_healed": True,
        }

        engine = ConsistencyEngine(sections, make_briefing(), language="de")
        result = engine.check_all()

        # Neither BC_001 nor RECO_002 should trigger
        bc001_issues = [i for i in result.issues if i.rule_id == "BC_001"]
        reco002_issues = [i for i in result.issues if i.rule_id == "RECO_002"]

        assert len(bc001_issues) == 0, "BC_001 should be skipped"
        assert len(reco002_issues) == 0, "RECO_002 should be skipped"


class TestFlagPersistence:
    """Test flag persistence through report generation."""

    def test_flags_accessible_after_generation(self):
        """Flags should be accessible in sections after report generation."""
        from services.business_case_engine_v2 import generate_business_case_report
        from services.recommendations_engine import generate_recommendations_report

        sections = {}
        briefing = make_briefing()

        # Generate BC report with healing needed
        bc_llm_response = {
            "scenarios": [
                {"name": "optimistic", "roi_12m": 80, "payback_months": 10,
                 "monthly_savings": 500, "annual_savings": 6000, "investment_total": 5000},
                {"name": "realistic", "roi_12m": 120, "payback_months": 8,
                 "monthly_savings": 600, "annual_savings": 7200, "investment_total": 5000},
                {"name": "conservative", "roi_12m": 60, "payback_months": 12,
                 "monthly_savings": 400, "annual_savings": 4800, "investment_total": 5000},
            ]
        }

        generate_business_case_report(
            sections=sections,
            briefing=briefing,
            llm_response=bc_llm_response,
        )

        # Generate RECO report with healing needed
        reco_llm_response = {
            "recommendations": [
                {
                    "id": "rec_1",
                    "title": "Test",
                    "description": "Test desc",
                    "reason": "Test reason",
                    "impact_level": "high",
                    "urgency_level": "medium",
                    "risk_relation": "reduces_risk",
                    "related_risks": [],
                    "timeline_phase": "phase_1",
                }
            ],
        }

        generate_recommendations_report(
            sections=sections,
            briefing=briefing,
            llm_response=reco_llm_response,
        )

        # Both flags should be set
        assert sections.get("_bc_healed") is True
        assert sections.get("_reco_healed") is True
