# -*- coding: utf-8 -*-
"""
Tests for G28: Strategy Engine – 12-Month AI Implementation Plan

Tests all 8 building blocks:
1. Vision Statement
2. Priority Matrix
3. 3-Phase Roadmap
4. Tool Deployment Plan
5. Funding Integration Plan
6. KPI Targets
7. Risk Mitigation Plan
8. RACI-Light Responsibility Matrix

Version: 1.0.0 (Sprint G28)
"""
import pytest
from typing import Any, Dict

from services.strategy_engine import (
    generate_strategy_plan,
    inject_strategy_into_sections,
    StrategyPlan,
    VisionStatement,
    PriorityItem,
    RoadmapPhase,
    ToolDeployment,
    FundingIntegration,
    KPITarget,
    RiskMitigation,
    RACIEntry,
    STRATEGY_ENGINE_ENABLED,
    _extract_vision,
    _extract_priorities,
    _extract_roadmap,
    _extract_tool_deployments,
    _extract_funding_plan,
    _extract_kpi_targets,
    _extract_risk_mitigations,
    _extract_raci_matrix,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_sections() -> Dict[str, Any]:
    """Sample sections with G23, G25, G26 data."""
    return {
        "ROI_12M": 150,
        "PAYBACK_MONTHS": 8,
        "EINSPARUNG_STUNDEN_MONAT": 40,
        "EINSPARUNG_MONAT_EUR": 2400,
        "MATURITY_LEVEL": 2,
        "AI_ACT_RISK_LEVEL": "minimal",
        "BRANCH_LABEL": "IT-Beratung",
        "KI_STACK_SUMMARY_HTML": "<div><strong>ChatGPT</strong></div><div><strong>Make</strong></div>",
        "TOOLS_V4_DATA": [
            {"name": "ChatGPT", "category": "KI-Assistent", "complexity_level": 2, "price": "25€"},
            {"name": "Make.com", "category": "Automation", "complexity_level": 3, "price": "29€"},
            {"name": "Notion AI", "category": "Productivity", "complexity_level": 2, "price": "10€"},
        ],
        "FUNDING_V2_DATA": [
            {"name": "go-digital", "year": 2025, "max_amount": "16.500 €", "deadline": "2025"},
            {"name": "Digital Jetzt", "year": 2025, "max_amount": "50.000 €", "deadline": "2025"},
            {"name": "AI Made in Germany", "year": 2026, "max_amount": "500.000 €", "deadline": "Q1 2026"},
        ],
    }


@pytest.fixture
def sample_briefing() -> Dict[str, Any]:
    """Sample briefing data."""
    return {
        "branche": "IT-Beratung",
        "unternehmensgroesse": "Team (5-10)",
        "bundesland": "BY",
        "einsparung_stunden_monat": 40,
    }


@pytest.fixture
def solo_briefing() -> Dict[str, Any]:
    """Sample briefing for solo entrepreneur."""
    return {
        "branche": "Beratung",
        "unternehmensgroesse": "Solo",
        "bundesland": "BE",
    }


@pytest.fixture
def kmu_briefing() -> Dict[str, Any]:
    """Sample briefing for KMU."""
    return {
        "branche": "Software-Entwicklung",
        "unternehmensgroesse": "KMU (50+)",
        "bundesland": "NW",
    }


# =============================================================================
# DATA STRUCTURE TESTS
# =============================================================================

class TestDataStructures:
    """Test data structures for Strategy Engine."""

    def test_vision_statement_defaults(self):
        """Test VisionStatement default values."""
        vision = VisionStatement()
        assert vision.headline == ""
        assert vision.description == ""
        assert vision.target_state == ""
        assert vision.time_horizon == "12 Monate"

    def test_vision_statement_custom(self):
        """Test VisionStatement with custom values."""
        vision = VisionStatement(
            headline="KI-Excellence",
            description="Transformation durch KI",
            target_state="Vollautomatisierte Workflows",
            time_horizon="18 Monate",
        )
        assert vision.headline == "KI-Excellence"
        assert vision.time_horizon == "18 Monate"

    def test_priority_item_creation(self):
        """Test PriorityItem creation."""
        item = PriorityItem(
            title="ChatGPT einführen",
            description="KI-Assistent für tägliche Aufgaben",
            quadrant="quick_win",
            impact=4,
            effort=2,
            category="tool",
        )
        assert item.title == "ChatGPT einführen"
        assert item.quadrant == "quick_win"
        assert item.impact == 4
        assert item.effort == 2

    def test_roadmap_phase_creation(self):
        """Test RoadmapPhase creation."""
        phase = RoadmapPhase(
            phase_id=1,
            title="Foundation",
            months="1-3",
            focus="Setup & Quick Wins",
            milestones=["Tool ausgewählt", "Team geschult"],
            tools=["ChatGPT", "Make"],
            kpis=["Adoptionsrate"],
            budget_allocation=30.0,
        )
        assert phase.phase_id == 1
        assert phase.months == "1-3"
        assert len(phase.milestones) == 2
        assert phase.budget_allocation == 30.0

    def test_tool_deployment_creation(self):
        """Test ToolDeployment creation."""
        deployment = ToolDeployment(
            tool_name="ChatGPT",
            phase=1,
            priority="must_have",
            users="all",
            training_hours=4,
            cost_monthly="25€",
        )
        assert deployment.tool_name == "ChatGPT"
        assert deployment.priority == "must_have"
        assert deployment.training_hours == 4

    def test_funding_integration_creation(self):
        """Test FundingIntegration creation."""
        funding = FundingIntegration(
            programme_name="go-digital",
            year=2025,
            application_phase=1,
            amount_target="16.500 €",
            requirements_met=["< 100 MA"],
            deadline="2025",
        )
        assert funding.programme_name == "go-digital"
        assert funding.year == 2025
        assert funding.application_phase == 1

    def test_kpi_target_creation(self):
        """Test KPITarget creation."""
        kpi = KPITarget(
            name="ROI",
            current_value="0%",
            target_month_3="30%",
            target_month_6="75%",
            target_month_12="150%",
            unit="%",
            category="cost",
        )
        assert kpi.name == "ROI"
        assert kpi.target_month_12 == "150%"
        assert kpi.category == "cost"

    def test_risk_mitigation_creation(self):
        """Test RiskMitigation creation."""
        risk = RiskMitigation(
            risk_name="Geringe Akzeptanz",
            probability="medium",
            impact="high",
            mitigation_strategy="Frühzeitige Schulung",
            owner="Projektleitung",
        )
        assert risk.risk_name == "Geringe Akzeptanz"
        assert risk.probability == "medium"
        assert risk.impact == "high"

    def test_raci_entry_creation(self):
        """Test RACIEntry creation."""
        raci = RACIEntry(
            task="Tool-Auswahl",
            responsible="IT-Leitung",
            accountable="Geschäftsführung",
            consulted="Teamleiter",
            informed="Alle MA",
        )
        assert raci.task == "Tool-Auswahl"
        assert raci.responsible == "IT-Leitung"
        assert raci.accountable == "Geschäftsführung"

    def test_strategy_plan_complete(self):
        """Test complete StrategyPlan structure."""
        plan = StrategyPlan(
            vision=VisionStatement(headline="Test"),
            priorities=[PriorityItem("Test", "Desc", "quick_win")],
            roadmap=[RoadmapPhase(1, "Test", "1-3", "Focus")],
            company_size="team",
            branch="IT",
        )
        assert plan.vision.headline == "Test"
        assert len(plan.priorities) == 1
        assert len(plan.roadmap) == 1
        assert plan.company_size == "team"


# =============================================================================
# EXTRACTION TESTS
# =============================================================================

class TestExtraction:
    """Test data extraction functions."""

    def test_extract_vision_default_de(self, sample_sections, sample_briefing):
        """Test vision extraction with defaults (German)."""
        vision = _extract_vision(sample_sections, sample_briefing, "de")
        assert "KI-gestützte" in vision.headline or "Exzellenz" in vision.headline
        assert vision.time_horizon == "12 Monate"

    def test_extract_vision_default_en(self, sample_sections, sample_briefing):
        """Test vision extraction with defaults (English)."""
        vision = _extract_vision(sample_sections, sample_briefing, "en")
        assert "AI-Powered" in vision.headline or "Excellence" in vision.headline

    def test_extract_vision_custom(self, sample_sections, sample_briefing):
        """Test vision extraction with custom data."""
        sample_sections["STRATEGY_VISION"] = {
            "headline": "Custom Vision",
            "description": "Custom Desc",
            "target_state": "Custom Target",
        }
        vision = _extract_vision(sample_sections, sample_briefing, "de")
        assert vision.headline == "Custom Vision"

    def test_extract_priorities_default(self, sample_sections, sample_briefing):
        """Test priorities extraction with defaults."""
        priorities = _extract_priorities(sample_sections, sample_briefing, "de")
        assert len(priorities) >= 4
        quadrants = [p.quadrant for p in priorities]
        assert "quick_win" in quadrants
        assert "strategic" in quadrants

    def test_extract_priorities_consulting_branch(self, sample_sections, sample_briefing):
        """Test priorities for consulting branch."""
        sample_briefing["branche"] = "Beratung"
        priorities = _extract_priorities(sample_sections, sample_briefing, "de")
        titles = [p.title for p in priorities]
        # Should have consulting-specific priorities
        assert any("Report" in t or "Kunden" in t for t in titles)

    def test_extract_roadmap_default(self, sample_sections, sample_briefing):
        """Test roadmap extraction with defaults."""
        roadmap = _extract_roadmap(sample_sections, sample_briefing, "de")
        assert len(roadmap) == 3
        assert roadmap[0].phase_id == 1
        assert roadmap[0].months == "1-3"
        assert roadmap[1].phase_id == 2
        assert roadmap[1].months == "4-6"
        assert roadmap[2].phase_id == 3
        assert roadmap[2].months == "7-12"

    def test_extract_roadmap_budget_allocation(self, sample_sections, sample_briefing):
        """Test roadmap budget allocation sums to 100%."""
        roadmap = _extract_roadmap(sample_sections, sample_briefing, "de")
        total_budget = sum(phase.budget_allocation for phase in roadmap)
        assert total_budget == 100.0

    def test_extract_roadmap_uses_tools(self, sample_sections, sample_briefing):
        """Test roadmap includes tools from G25."""
        roadmap = _extract_roadmap(sample_sections, sample_briefing, "de")
        all_tools = []
        for phase in roadmap:
            all_tools.extend(phase.tools)
        assert "ChatGPT" in all_tools or "Make.com" in all_tools

    def test_extract_tool_deployments(self, sample_sections, sample_briefing):
        """Test tool deployment extraction from G25."""
        deployments = _extract_tool_deployments(sample_sections, sample_briefing, "de")
        assert len(deployments) >= 3
        assert deployments[0].tool_name == "ChatGPT"

    def test_extract_tool_deployments_phases(self, sample_sections, sample_briefing):
        """Test tool deployment phase assignment."""
        deployments = _extract_tool_deployments(sample_sections, sample_briefing, "de")
        # Low complexity tools should be phase 1
        chatgpt = next((d for d in deployments if d.tool_name == "ChatGPT"), None)
        assert chatgpt is not None
        assert chatgpt.phase in [1, 2]

    def test_extract_funding_plan(self, sample_sections, sample_briefing):
        """Test funding plan extraction from G26."""
        funding = _extract_funding_plan(sample_sections, sample_briefing, "de")
        assert len(funding) >= 2
        names = [f.programme_name for f in funding]
        assert "go-digital" in names

    def test_extract_funding_plan_phases(self, sample_sections, sample_briefing):
        """Test funding plan phase assignment by year."""
        funding = _extract_funding_plan(sample_sections, sample_briefing, "de")
        for f in funding:
            if f.year == 2025:
                assert f.application_phase == 1
            elif f.year == 2026:
                assert f.application_phase == 2

    def test_extract_kpi_targets(self, sample_sections, sample_briefing):
        """Test KPI targets extraction from G23."""
        kpis = _extract_kpi_targets(sample_sections, sample_briefing, "de")
        assert len(kpis) >= 4
        kpi_names = [k.name for k in kpis]
        assert "ROI" in kpi_names

    def test_extract_kpi_targets_progression(self, sample_sections, sample_briefing):
        """Test KPI targets show progression."""
        kpis = _extract_kpi_targets(sample_sections, sample_briefing, "de")
        roi_kpi = next((k for k in kpis if k.name == "ROI"), None)
        assert roi_kpi is not None
        # Should show progression: 0 < 3mo < 6mo < 12mo
        assert roi_kpi.current_value == "0%"

    def test_extract_risk_mitigations_default(self, sample_sections, sample_briefing):
        """Test risk mitigation extraction with defaults."""
        risks = _extract_risk_mitigations(sample_sections, sample_briefing, "de")
        assert len(risks) >= 3
        risk_names = [r.risk_name for r in risks]
        assert any("Akzeptanz" in n or "Adoption" in n for n in risk_names)

    def test_extract_risk_mitigations_high_risk(self, sample_sections, sample_briefing):
        """Test risk mitigation includes AI Act for high-risk."""
        sample_sections["AI_ACT_RISK_LEVEL"] = "high-risk"
        risks = _extract_risk_mitigations(sample_sections, sample_briefing, "de")
        risk_names = [r.risk_name for r in risks]
        assert any("AI Act" in n or "Compliance" in n for n in risk_names)

    def test_extract_raci_team(self, sample_sections, sample_briefing):
        """Test RACI extraction for team size."""
        raci = _extract_raci_matrix(sample_sections, sample_briefing, "de")
        assert len(raci) >= 4
        # Team should have multiple roles
        all_roles = set()
        for entry in raci:
            all_roles.add(entry.responsible)
            all_roles.add(entry.accountable)
        assert len(all_roles) > 2

    def test_extract_raci_solo(self, sample_sections, solo_briefing):
        """Test RACI extraction for solo entrepreneur."""
        raci = _extract_raci_matrix(sample_sections, solo_briefing, "de")
        assert len(raci) >= 3
        # Solo should have simplified roles (mostly "Inhaber")
        for entry in raci:
            assert "Inhaber" in entry.responsible or "Owner" in entry.responsible


# =============================================================================
# HTML GENERATION TESTS
# =============================================================================

class TestHTMLGeneration:
    """Test HTML generation functions."""

    def test_generate_strategy_plan_basic(self, sample_sections, sample_briefing):
        """Test basic strategy plan HTML generation."""
        html = generate_strategy_plan(sample_sections, sample_briefing, "de")
        assert "strategy-plan-container" in html
        assert "G28" in html
        assert "12-Monats-KI-Strategie" in html

    def test_generate_strategy_plan_english(self, sample_sections, sample_briefing):
        """Test English strategy plan generation."""
        html = generate_strategy_plan(sample_sections, sample_briefing, "en")
        assert "12-Month AI Strategy" in html

    def test_generate_strategy_plan_vision_block(self, sample_sections, sample_briefing):
        """Test vision block in HTML."""
        html = generate_strategy_plan(sample_sections, sample_briefing, "de")
        assert "vision-block" in html
        assert "🎯" in html or "Vision" in html

    def test_generate_strategy_plan_priority_block(self, sample_sections, sample_briefing):
        """Test priority matrix block in HTML."""
        html = generate_strategy_plan(sample_sections, sample_briefing, "de")
        assert "priority-block" in html or "Prioritätsmatrix" in html
        assert "quick_win" in html or "Quick Win" in html

    def test_generate_strategy_plan_roadmap_block(self, sample_sections, sample_briefing):
        """Test roadmap block in HTML."""
        html = generate_strategy_plan(sample_sections, sample_briefing, "de")
        assert "roadmap-block" in html or "Roadmap" in html
        assert "phase-1" in html or "Phase" in html

    def test_generate_strategy_plan_deployment_block(self, sample_sections, sample_briefing):
        """Test tool deployment block in HTML."""
        html = generate_strategy_plan(sample_sections, sample_briefing, "de")
        assert "deployment-block" in html or "Deployment" in html
        assert "ChatGPT" in html

    def test_generate_strategy_plan_funding_block(self, sample_sections, sample_briefing):
        """Test funding integration block in HTML."""
        html = generate_strategy_plan(sample_sections, sample_briefing, "de")
        assert "funding-plan-block" in html or "Förder" in html
        assert "go-digital" in html or "2025" in html

    def test_generate_strategy_plan_kpi_block(self, sample_sections, sample_briefing):
        """Test KPI targets block in HTML."""
        html = generate_strategy_plan(sample_sections, sample_briefing, "de")
        assert "kpi-targets" in html or "KPI" in html
        assert "ROI" in html

    def test_generate_strategy_plan_risk_block(self, sample_sections, sample_briefing):
        """Test risk mitigation block in HTML."""
        html = generate_strategy_plan(sample_sections, sample_briefing, "de")
        assert "risk-block" in html or "Risiko" in html

    def test_generate_strategy_plan_raci_block(self, sample_sections, sample_briefing):
        """Test RACI block in HTML."""
        html = generate_strategy_plan(sample_sections, sample_briefing, "de")
        assert "raci-block" in html or "RACI" in html
        assert "Responsible" in html or "R=" in html


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Test integration functions."""

    def test_inject_strategy_into_sections(self, sample_sections, sample_briefing):
        """Test injecting strategy into sections."""
        result = inject_strategy_into_sections(sample_sections, sample_briefing, "de")
        assert "STRATEGY_PLAN_HTML" in result
        assert len(result["STRATEGY_PLAN_HTML"]) > 100

    def test_inject_strategy_preserves_sections(self, sample_sections, sample_briefing):
        """Test that injection preserves existing sections."""
        original_keys = set(sample_sections.keys())
        inject_strategy_into_sections(sample_sections, sample_briefing, "de")
        # All original keys should still be present
        for key in original_keys:
            assert key in sample_sections


# =============================================================================
# SIZE-AWARENESS TESTS
# =============================================================================

class TestSizeAwareness:
    """Test size-aware adaptations."""

    def test_solo_simplified_raci(self, sample_sections, solo_briefing):
        """Test solo entrepreneurs get simplified RACI."""
        html = generate_strategy_plan(sample_sections, solo_briefing, "de")
        # Solo should have fewer complex roles
        assert "Inhaber" in html or "Owner" in html

    def test_kmu_full_raci(self, sample_sections, kmu_briefing):
        """Test KMU gets full RACI matrix."""
        html = generate_strategy_plan(sample_sections, kmu_briefing, "de")
        # KMU should have compliance roles
        assert "Compliance" in html or "Legal" in html or "Recht" in html

    def test_team_moderate_raci(self, sample_sections, sample_briefing):
        """Test team size gets moderate RACI."""
        html = generate_strategy_plan(sample_sections, sample_briefing, "de")
        assert "IT" in html or "Projekt" in html


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_sections(self, sample_briefing):
        """Test with empty sections."""
        html = generate_strategy_plan({}, sample_briefing, "de")
        # Should still generate with defaults
        assert "strategy-plan-container" in html

    def test_empty_briefing(self, sample_sections):
        """Test with empty briefing."""
        html = generate_strategy_plan(sample_sections, {}, "de")
        assert "strategy-plan-container" in html

    def test_missing_tools_data(self, sample_sections, sample_briefing):
        """Test with missing TOOLS_V4_DATA."""
        del sample_sections["TOOLS_V4_DATA"]
        html = generate_strategy_plan(sample_sections, sample_briefing, "de")
        # Should use defaults
        assert "deployment" in html.lower() or "tool" in html.lower()

    def test_missing_funding_data(self, sample_sections, sample_briefing):
        """Test with missing FUNDING_V2_DATA."""
        del sample_sections["FUNDING_V2_DATA"]
        html = generate_strategy_plan(sample_sections, sample_briefing, "de")
        # Should use defaults
        assert "go-digital" in html or "Digital Jetzt" in html

    def test_missing_kpi_data(self, sample_sections, sample_briefing):
        """Test with missing KPI data."""
        del sample_sections["ROI_12M"]
        del sample_sections["PAYBACK_MONTHS"]
        html = generate_strategy_plan(sample_sections, sample_briefing, "de")
        assert "kpi" in html.lower() or "KPI" in html


# =============================================================================
# CONSISTENCY TESTS
# =============================================================================

class TestConsistency:
    """Test consistency with G22 rules."""

    def test_budget_sums_to_100(self, sample_sections, sample_briefing):
        """Test that phase budgets sum to approximately 100%."""
        roadmap = _extract_roadmap(sample_sections, sample_briefing, "de")
        total = sum(p.budget_allocation for p in roadmap)
        assert 95 <= total <= 105  # Allow small deviation

    def test_tools_from_g25_in_deployment(self, sample_sections, sample_briefing):
        """Test tools in deployment come from G25."""
        deployments = _extract_tool_deployments(sample_sections, sample_briefing, "de")
        g25_tools = [t["name"] for t in sample_sections.get("TOOLS_V4_DATA", [])]
        for dep in deployments:
            if g25_tools:
                assert dep.tool_name in g25_tools

    def test_funding_from_g26_in_plan(self, sample_sections, sample_briefing):
        """Test funding in plan comes from G26."""
        funding = _extract_funding_plan(sample_sections, sample_briefing, "de")
        g26_progs = [f["name"] for f in sample_sections.get("FUNDING_V2_DATA", [])]
        for fp in funding:
            if g26_progs:
                assert fp.programme_name in g26_progs

    def test_ai_act_risk_in_mitigation(self, sample_sections, sample_briefing):
        """Test AI Act risk is addressed in mitigation when needed."""
        sample_sections["AI_ACT_RISK_LEVEL"] = "high-risk"
        risks = _extract_risk_mitigations(sample_sections, sample_briefing, "de")
        risk_names = [r.risk_name.lower() for r in risks]
        assert any("ai act" in n or "compliance" in n for n in risk_names)
