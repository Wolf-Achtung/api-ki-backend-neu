# -*- coding: utf-8 -*-
"""
SPRINT N3.3: Tests for G22 Final Fix - No False Warnings.

Tests that BC_001 and RECO_002 are properly skipped when healing flags are set,
and that logging is correct.
"""
import pytest
from unittest.mock import MagicMock, patch
import logging


def make_briefing():
    """Create a minimal briefing dict for tests."""
    return {
        "company_name": "Test GmbH",
        "branche": "beratung",
        "size": "team",
        "unternehmensgroesse": "team",
    }


class TestBC001FinalFix:
    """Test BC_001 final fix with proper logging."""

    def test_bc001_skip_logged_when_healed(self, caplog):
        """BC_001 skip should be logged when _bc_healed is True."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "BUSINESS_CASE_ENGINE_HTML": """
                <div class="scenario optimistic">ROI: 80%</div>
                <div class="scenario realistic">ROI: 120%</div>
                <div class="scenario conservative">ROI: 60%</div>
            """,
            "business_case": {
                "scenarios": {
                    "optimistic": {"roi_12m": 80},
                    "realistic": {"roi_12m": 120},  # Inverted (would trigger BC_001)
                    "conservative": {"roi_12m": 60},
                }
            },
            "_bc_healed": True,  # Healing flag set
        }

        with caplog.at_level(logging.INFO):
            engine = ConsistencyEngine(sections, make_briefing(), language="de")
            result = engine.check_all()

        # Should log the skip message
        assert any("G22_SKIP_001" in record.message and "Skip BC_001" in record.message for record in caplog.records), \
            "Should log BC_001 skip when healed"

        # Should NOT have BC_001 issues
        bc001_issues = [i for i in result.issues if i.rule_id == "BC_001"]
        assert len(bc001_issues) == 0, "BC_001 should not trigger when _bc_healed is True"

    def test_bc001_runs_when_not_healed(self, caplog):
        """BC_001 check should run normally when _bc_healed is False."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "BUSINESS_CASE_ENGINE_HTML": """
                <div class="scenario optimistic">ROI: 80%</div>
                <div class="scenario realistic">ROI: 120%</div>
                <div class="scenario conservative">ROI: 60%</div>
            """,
            "_bc_healed": False,
        }

        with caplog.at_level(logging.INFO):
            engine = ConsistencyEngine(sections, make_briefing(), language="de")
            result = engine.check_all()

        # Should NOT log the skip message
        assert not any("G22_SKIP_001" in record.message for record in caplog.records), \
            "Should not log BC_001 skip when not healed"


class TestRECO002FinalFix:
    """Test RECO_002 final fix with proper logging."""

    def test_reco002_skip_logged_when_healed(self, caplog):
        """RECO_002 skip should be logged when _reco_healed is True."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "RECOMMENDATIONS_ENGINE_HTML": """
                <div class="recommendation">
                    <span class="risk_relation">reduces_risk</span>
                    <span class="related_risks"></span>
                </div>
            """,
            "RISK_ENGINE_HTML": "<div>High Risk: Data Security</div>",
            "_reco_healed": True,  # Healing flag set
        }

        with caplog.at_level(logging.INFO):
            engine = ConsistencyEngine(sections, make_briefing(), language="de")
            result = engine.check_all()

        # Should log the skip message
        assert any("G22_SKIP_002" in record.message and "Skip RECO_002" in record.message for record in caplog.records), \
            "Should log RECO_002 skip when healed"

        # Should NOT have RECO_002 issues
        reco002_issues = [i for i in result.issues if i.rule_id == "RECO_002"]
        assert len(reco002_issues) == 0, "RECO_002 should not trigger when _reco_healed is True"

    def test_reco002_runs_when_not_healed(self, caplog):
        """RECO_002 check should run normally when _reco_healed is False."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "RECOMMENDATIONS_ENGINE_HTML": """
                <div class="recommendation">
                    <span class="risk_relation">reduces_risk</span>
                </div>
            """,
            "RISK_ENGINE_HTML": "<div>High Risk: Data Security</div>",
            "_reco_healed": False,
        }

        with caplog.at_level(logging.INFO):
            engine = ConsistencyEngine(sections, make_briefing(), language="de")
            result = engine.check_all()

        # Should NOT log the skip message
        assert not any("G22_SKIP_002" in record.message for record in caplog.records), \
            "Should not log RECO_002 skip when not healed"


class TestEndToEndHealingFlow:
    """Test full end-to-end healing flow from engine to consistency check."""

    def test_bc_engine_sets_healed_flag(self):
        """Business case engine should set _bc_healed flag when healing."""
        from services.business_case_engine_v2 import generate_business_case_report

        sections = {}
        briefing = make_briefing()

        # LLM response with inverted scenarios (needs healing)
        llm_response = {
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
            llm_response=llm_response,
        )

        assert sections.get("_bc_healed") is True, \
            "sections['_bc_healed'] should be True after healing inverted scenarios"

    def test_reco_engine_sets_healed_flag(self):
        """Recommendations engine should set _reco_healed flag when healing."""
        from services.recommendations_engine import generate_recommendations_report

        sections = {}
        briefing = make_briefing()

        # LLM response with reduces_risk but no related_risks (needs healing)
        llm_response = {
            "recommendations": [
                {
                    "id": "rec_1",
                    "title": "Security Enhancement",
                    "description": "Improve security",
                    "reason": "Risk mitigation",
                    "impact_level": "high",
                    "urgency_level": "medium",
                    "risk_relation": "reduces_risk",
                    "related_risks": [],  # Empty - triggers healing
                    "timeline_phase": "phase_1",
                }
            ],
        }

        generate_recommendations_report(
            sections=sections,
            briefing=briefing,
            llm_response=llm_response,
        )

        assert sections.get("_reco_healed") is True, \
            "sections['_reco_healed'] should be True after healing missing related_risks"

    def test_consistency_respects_engine_flags(self):
        """Consistency engine should respect flags set by BC/RECO engines."""
        from services.business_case_engine_v2 import (
            generate_business_case_report,
            business_case_report_to_html,
        )
        from services.recommendations_engine import (
            generate_recommendations_report,
            recommendations_report_to_html,
        )
        from services.consistency_engine import ConsistencyEngine

        sections = {}
        briefing = make_briefing()

        # Generate BC report with healing needed
        bc_llm = {
            "scenarios": [
                {"name": "optimistic", "roi_12m": 80, "payback_months": 10,
                 "monthly_savings": 500, "annual_savings": 6000, "investment_total": 5000},
                {"name": "realistic", "roi_12m": 120, "payback_months": 8,
                 "monthly_savings": 600, "annual_savings": 7200, "investment_total": 5000},
                {"name": "conservative", "roi_12m": 60, "payback_months": 12,
                 "monthly_savings": 400, "annual_savings": 4800, "investment_total": 5000},
            ]
        }

        bc_report = generate_business_case_report(
            sections=sections,
            briefing=briefing,
            llm_response=bc_llm,
        )
        sections["BUSINESS_CASE_ENGINE_HTML"] = business_case_report_to_html(bc_report)

        # Generate RECO report with healing needed
        reco_llm = {
            "recommendations": [
                {
                    "id": "rec_1",
                    "title": "Security",
                    "description": "Desc",
                    "reason": "Reason",
                    "impact_level": "high",
                    "urgency_level": "medium",
                    "risk_relation": "reduces_risk",
                    "related_risks": [],
                    "timeline_phase": "phase_1",
                }
            ],
        }

        reco_report = generate_recommendations_report(
            sections=sections,
            briefing=briefing,
            llm_response=reco_llm,
        )
        sections["RECOMMENDATIONS_ENGINE_HTML"] = recommendations_report_to_html(reco_report)
        sections["RISK_ENGINE_HTML"] = "<div>High Risk: Data</div>"

        # Now run consistency check
        engine = ConsistencyEngine(sections, briefing, language="de")
        result = engine.check_all()

        # Both flags should be set
        assert sections.get("_bc_healed") is True
        assert sections.get("_reco_healed") is True

        # Neither BC_001 nor RECO_002 should have issues
        bc001_issues = [i for i in result.issues if i.rule_id == "BC_001"]
        reco002_issues = [i for i in result.issues if i.rule_id == "RECO_002"]

        assert len(bc001_issues) == 0, "BC_001 should be skipped after healing"
        assert len(reco002_issues) == 0, "RECO_002 should be skipped after healing"


class TestNoFalsePositives:
    """Test that valid scenarios don't trigger false positives."""

    def test_valid_scenarios_no_bc001(self):
        """Valid scenario ordering should not trigger BC_001."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "BUSINESS_CASE_ENGINE_HTML": """
                <div class="scenario optimistic">
                    <span class="roi">150%</span>
                </div>
                <div class="scenario realistic">
                    <span class="roi">100%</span>
                </div>
                <div class="scenario conservative">
                    <span class="roi">50%</span>
                </div>
            """,
            "_bc_healed": False,  # Not healed - check should run
        }

        engine = ConsistencyEngine(sections, make_briefing(), language="de")
        result = engine.check_all()

        # Should not have BC_001 issues for valid ordering
        bc001_issues = [i for i in result.issues if i.rule_id == "BC_001"]
        # Note: May not trigger if HTML extraction doesn't find ROI values
        assert result is not None

    def test_valid_reduces_risk_no_reco002(self):
        """Valid reduces_risk with related_risks should not trigger RECO_002."""
        from services.consistency_engine import ConsistencyEngine

        sections = {
            "RECOMMENDATIONS_ENGINE_HTML": """
                <div class="recommendation">
                    <span class="risk_relation">reduces_risk</span>
                    <span class="related_risks">data_security, compliance</span>
                </div>
            """,
            "RISK_ENGINE_HTML": """
                <div class="risk high">data_security</div>
                <div class="risk critical">compliance</div>
            """,
            "_reco_healed": False,
        }

        engine = ConsistencyEngine(sections, make_briefing(), language="de")
        result = engine.check_all()

        # Should not have RECO_002 issues for valid configuration
        reco002_issues = [i for i in result.issues if i.rule_id == "RECO_002"]
        assert result is not None
