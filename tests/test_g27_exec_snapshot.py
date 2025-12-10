# -*- coding: utf-8 -*-
"""
Tests for Sprint G27: Executive Snapshot One-Pager

Tests cover:
- ExecSnapshotData dataclass
- generate_exec_snapshot() function
- All 8 building blocks
- HTML structure validation
- Consistency with G22 rules
- Language support (DE/EN)

Target: 30+ tests
"""

import pytest
from typing import Dict, Any

from services.exec_snapshot import (
    generate_exec_snapshot,
    inject_exec_snapshot_into_sections,
    ExecSnapshotData,
    KPIData,
    ToolCard,
    FundingCard,
    _extract_kpi_data,
    _extract_tools,
    _extract_funding,
    _extract_quick_wins,
    _extract_key_risks,
    _extract_roadmap_steps,
    _extract_funding_timeline,
    _generate_kpi_block,
    _generate_tools_block,
    _generate_funding_block,
    _generate_branch_block,
    _generate_quickwins_block,
    _generate_risks_block,
    _generate_roadmap_block,
    _generate_timeline_block,
    EXEC_SNAPSHOT_ENABLED,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_briefing() -> Dict[str, Any]:
    """Create a sample briefing for testing."""
    return {
        "branche": "IT-Beratung",
        "unternehmensgroesse": "team",
        "bundesland": "BY",
        "ROI_12M": 150,
        "PAYBACK_MONTHS": 6,
        "einsparung_stunden_monat": 40,
        "einsparung_monat_eur": 2400,
    }


@pytest.fixture
def sample_sections() -> Dict[str, Any]:
    """Create sample report sections for testing."""
    return {
        "ROI_12M": 150,
        "PAYBACK_MONTHS": 6,
        "EINSPARUNG_STUNDEN_MONAT": 40,
        "EINSPARUNG_MONAT_EUR": 2400,
        "MATURITY_LEVEL": 3,
        "AI_ACT_RISK_LEVEL": "minimal",
        "BRANCH_LABEL": "IT-Beratung",
        "BRANCH_SHORT_LABEL": "IT",
        "SIZE_LABEL": "Team (2-10)",
        "DSGVO_RELEVANT": False,
        "TOOLS_V4_DATA": [
            {"name": "ChatGPT", "category": "LLM", "cost_level": 2, "complexity_level": 1, "eu_hosting": False},
            {"name": "GitHub Copilot", "category": "Code", "cost_level": 3, "complexity_level": 2, "eu_hosting": False},
            {"name": "Notion AI", "category": "Docs", "cost_level": 2, "complexity_level": 1, "eu_hosting": True},
        ],
        "FUNDING_V2_DATA": [
            {"name": "go-digital", "year": 2025, "level": "federal", "funding_rate": "50%", "match_score": 0.85},
            {"name": "Digital Jetzt", "year": 2025, "level": "federal", "funding_rate": "40%", "match_score": 0.75},
        ],
        "QUICK_WINS_DATA": [
            "ChatGPT für Recherche einsetzen",
            "Code-Reviews mit Copilot",
            "Dokumente mit Notion AI",
        ],
        "KEY_RISKS_DATA": [
            "Datenschutz bei Cloud-KI",
            "Abhängigkeit von US-Anbietern",
        ],
        "ROADMAP_STEPS": [
            {"phase": "1", "title": "Setup", "description": "Tools einrichten"},
            {"phase": "2", "title": "Workflow", "description": "Prozesse anpassen"},
            {"phase": "3", "title": "Scale", "description": "Rollout"},
        ],
    }


@pytest.fixture
def sample_kpi_data() -> KPIData:
    """Create sample KPI data."""
    return KPIData(
        roi_12m=150.0,
        payback_months=6.0,
        time_savings_hours=40.0,
        time_savings_eur=2400.0,
        industry_benchmark_roi=120.0,
    )


@pytest.fixture
def sample_tool_cards() -> list:
    """Create sample tool cards."""
    return [
        ToolCard(name="ChatGPT", category="LLM", cost_level=2, complexity_level=1),
        ToolCard(name="GitHub Copilot", category="Code", cost_level=3, complexity_level=2),
    ]


@pytest.fixture
def sample_funding_cards() -> list:
    """Create sample funding cards."""
    return [
        FundingCard(name="go-digital", year=2025, level="federal", funding_rate="50%", match_score=0.85, is_time_critical=True),
        FundingCard(name="Horizon Europe", year=2026, level="eu", funding_rate="70%", match_score=0.7),
    ]


# =============================================================================
# DATACLASS TESTS
# =============================================================================

class TestDataclasses:
    """Tests for dataclasses."""

    def test_kpi_data_creation(self) -> None:
        """Test KPIData creation."""
        kpi = KPIData(roi_12m=150.0, payback_months=6.0)
        assert kpi.roi_12m == 150.0
        assert kpi.payback_months == 6.0

    def test_tool_card_creation(self) -> None:
        """Test ToolCard creation."""
        tool = ToolCard(name="ChatGPT", category="LLM")
        assert tool.name == "ChatGPT"
        assert tool.category == "LLM"
        assert tool.cost_level == 3  # default

    def test_funding_card_creation(self) -> None:
        """Test FundingCard creation."""
        funding = FundingCard(name="go-digital", year=2025, level="federal", funding_rate="50%", match_score=0.85)
        assert funding.name == "go-digital"
        assert funding.year == 2025
        assert funding.is_time_critical is False  # default

    def test_exec_snapshot_data_creation(self) -> None:
        """Test ExecSnapshotData creation."""
        data = ExecSnapshotData(
            branch_label="IT-Beratung",
            ai_act_risk="minimal",
        )
        assert data.branch_label == "IT-Beratung"
        assert data.ai_act_risk == "minimal"
        assert len(data.tools) == 0
        assert len(data.quick_wins) == 0


# =============================================================================
# EXTRACTION TESTS
# =============================================================================

class TestExtraction:
    """Tests for data extraction functions."""

    def test_extract_kpi_data(self, sample_sections: Dict, sample_briefing: Dict) -> None:
        """Test KPI data extraction."""
        kpis = _extract_kpi_data(sample_sections, sample_briefing)
        assert kpis.roi_12m == 150.0
        assert kpis.payback_months == 6.0
        assert kpis.time_savings_hours == 40.0

    def test_extract_kpi_data_fallback(self) -> None:
        """Test KPI data extraction with fallback."""
        kpis = _extract_kpi_data({}, {"ROI_12M": 100})
        assert kpis.roi_12m == 100.0

    def test_extract_tools(self, sample_sections: Dict) -> None:
        """Test tool extraction."""
        tools = _extract_tools(sample_sections)
        assert len(tools) == 3
        assert tools[0].name == "ChatGPT"

    def test_extract_tools_empty(self) -> None:
        """Test tool extraction with no data."""
        tools = _extract_tools({})
        assert len(tools) == 0

    def test_extract_funding(self, sample_sections: Dict) -> None:
        """Test funding extraction."""
        funding = _extract_funding(sample_sections)
        assert len(funding) == 2
        assert funding[0].name == "go-digital"

    def test_extract_funding_time_critical(self, sample_sections: Dict) -> None:
        """Test funding extraction with time-critical flag."""
        funding = _extract_funding(sample_sections)
        assert funding[0].is_time_critical is True  # 2025 is time-critical

    def test_extract_quick_wins(self, sample_sections: Dict, sample_briefing: Dict) -> None:
        """Test quick wins extraction."""
        wins = _extract_quick_wins(sample_sections, sample_briefing)
        assert len(wins) == 3
        assert "ChatGPT" in wins[0]

    def test_extract_quick_wins_fallback(self) -> None:
        """Test quick wins fallback defaults."""
        wins = _extract_quick_wins({}, {"branche": "beratung"})
        assert len(wins) == 3

    def test_extract_key_risks(self, sample_sections: Dict, sample_briefing: Dict) -> None:
        """Test key risks extraction."""
        risks = _extract_key_risks(sample_sections, sample_briefing)
        assert len(risks) >= 2

    def test_extract_roadmap_steps(self, sample_sections: Dict) -> None:
        """Test roadmap steps extraction."""
        steps = _extract_roadmap_steps(sample_sections)
        assert len(steps) == 3
        assert steps[0]["title"] == "Setup"

    def test_extract_roadmap_steps_default(self) -> None:
        """Test roadmap steps default."""
        steps = _extract_roadmap_steps({})
        assert len(steps) == 3

    def test_extract_funding_timeline(self, sample_sections: Dict) -> None:
        """Test funding timeline extraction."""
        timeline = _extract_funding_timeline(sample_sections)
        assert len(timeline) == 3  # 2025, 2026, 2027


# =============================================================================
# BLOCK GENERATION TESTS
# =============================================================================

class TestBlockGeneration:
    """Tests for HTML block generation."""

    def test_generate_kpi_block_de(self, sample_kpi_data: KPIData) -> None:
        """Test German KPI block generation."""
        html = _generate_kpi_block(sample_kpi_data, lang="de")
        assert "KPIs" in html
        assert "ROI 12M" in html
        assert "150%" in html
        assert "kpi-bar-fill" in html

    def test_generate_kpi_block_en(self, sample_kpi_data: KPIData) -> None:
        """Test English KPI block generation."""
        html = _generate_kpi_block(sample_kpi_data, lang="en")
        assert "KPIs" in html
        assert "ROI 12M" in html

    def test_generate_tools_block(self, sample_tool_cards: list) -> None:
        """Test tools block generation."""
        html = _generate_tools_block(sample_tool_cards, lang="de")
        assert "Top Tools" in html
        assert "ChatGPT" in html
        assert "tool-mini-card" in html

    def test_generate_tools_block_empty(self) -> None:
        """Test tools block with no tools."""
        html = _generate_tools_block([], lang="de")
        assert "Keine Tools" in html

    def test_generate_funding_block(self, sample_funding_cards: list) -> None:
        """Test funding block generation."""
        html = _generate_funding_block(sample_funding_cards, lang="de")
        assert "Förderung" in html
        assert "go-digital" in html
        assert "funding-mini-card" in html

    def test_generate_funding_block_flags(self, sample_funding_cards: list) -> None:
        """Test funding block with time-critical flag."""
        html = _generate_funding_block(sample_funding_cards, lang="de")
        assert "time-critical" in html  # 2025 programme

    def test_generate_branch_block(self) -> None:
        """Test branch block generation."""
        data = ExecSnapshotData(
            branch_label="IT-Beratung",
            branch_short="IT",
            ai_act_risk="minimal",
        )
        html = _generate_branch_block(data, lang="de")
        assert "Profil" in html
        assert "IT" in html
        assert "AI Act" in html

    def test_generate_quickwins_block(self) -> None:
        """Test quick wins block generation."""
        wins = ["Win 1", "Win 2", "Win 3"]
        html = _generate_quickwins_block(wins, lang="de")
        assert "Quick Wins" in html
        assert "Win 1" in html
        assert "qw-num" in html

    def test_generate_risks_block(self) -> None:
        """Test risks block generation."""
        risks = ["Risk 1", "Risk 2"]
        html = _generate_risks_block(risks, lang="de")
        assert "Risiken" in html
        assert "Risk 1" in html
        assert "risk-item" in html

    def test_generate_roadmap_block(self) -> None:
        """Test roadmap block generation."""
        steps = [
            {"phase": "1", "title": "Setup", "description": "Start"},
            {"phase": "2", "title": "Workflow", "description": "Process"},
            {"phase": "3", "title": "Scale", "description": "Grow"},
        ]
        html = _generate_roadmap_block(steps, lang="de")
        assert "Roadmap" in html
        assert "Setup" in html
        assert "step-number" in html

    def test_generate_timeline_block(self) -> None:
        """Test timeline block generation."""
        timeline = [
            {"year": 2025, "count": 5, "programmes": ["prog1"]},
            {"year": 2026, "count": 3, "programmes": ["prog2"]},
        ]
        html = _generate_timeline_block(timeline, lang="de")
        assert "Timeline" in html
        assert "2025" in html
        assert "timeline-bar" in html


# =============================================================================
# MAIN FUNCTION TESTS
# =============================================================================

class TestGenerateExecSnapshot:
    """Tests for main generate_exec_snapshot function."""

    def test_generate_returns_html(self, sample_sections: Dict, sample_briefing: Dict) -> None:
        """Test that function returns HTML string."""
        html = generate_exec_snapshot(sample_sections, sample_briefing)
        assert isinstance(html, str)
        assert len(html) > 0

    def test_generate_contains_all_blocks(self, sample_sections: Dict, sample_briefing: Dict) -> None:
        """Test that HTML contains all 8 blocks."""
        html = generate_exec_snapshot(sample_sections, sample_briefing, lang="de")
        assert "kpi-block" in html
        assert "tools-block" in html
        assert "funding-block" in html
        assert "branch-block" in html
        assert "quickwins-block" in html
        assert "risks-block" in html
        assert "roadmap-block" in html
        assert "timeline-block" in html

    def test_generate_contains_header(self, sample_sections: Dict, sample_briefing: Dict) -> None:
        """Test that HTML contains header."""
        html = generate_exec_snapshot(sample_sections, sample_briefing)
        assert "exec-snapshot-header" in html
        assert "Executive Snapshot" in html
        assert "G27" in html

    def test_generate_contains_grid(self, sample_sections: Dict, sample_briefing: Dict) -> None:
        """Test that HTML contains grid structure."""
        html = generate_exec_snapshot(sample_sections, sample_briefing)
        assert "exec-snapshot-grid" in html
        assert "snapshot-row" in html

    def test_generate_de_language(self, sample_sections: Dict, sample_briefing: Dict) -> None:
        """Test German language output."""
        html = generate_exec_snapshot(sample_sections, sample_briefing, lang="de")
        assert "Förderung" in html or "funding" in html.lower()

    def test_generate_en_language(self, sample_sections: Dict, sample_briefing: Dict) -> None:
        """Test English language output."""
        html = generate_exec_snapshot(sample_sections, sample_briefing, lang="en")
        assert "Funding" in html or "funding" in html.lower()


# =============================================================================
# INJECTION TESTS
# =============================================================================

class TestInjection:
    """Tests for inject_exec_snapshot_into_sections function."""

    def test_inject_adds_exec_snapshot_html(self, sample_sections: Dict, sample_briefing: Dict) -> None:
        """Test that injection adds EXEC_SNAPSHOT_HTML."""
        result = inject_exec_snapshot_into_sections(sample_sections, sample_briefing)
        assert "EXEC_SNAPSHOT_HTML" in result

    def test_inject_preserves_existing(self, sample_sections: Dict, sample_briefing: Dict) -> None:
        """Test that injection preserves existing sections."""
        sample_sections["EXISTING_KEY"] = "existing_value"
        result = inject_exec_snapshot_into_sections(sample_sections, sample_briefing)
        assert result["EXISTING_KEY"] == "existing_value"

    def test_inject_html_not_empty(self, sample_sections: Dict, sample_briefing: Dict) -> None:
        """Test that injected HTML is not empty."""
        result = inject_exec_snapshot_into_sections(sample_sections, sample_briefing)
        assert len(result["EXEC_SNAPSHOT_HTML"]) > 100


# =============================================================================
# HTML STRUCTURE TESTS
# =============================================================================

class TestHTMLStructure:
    """Tests for HTML structure validation."""

    def test_html_has_valid_structure(self, sample_sections: Dict, sample_briefing: Dict) -> None:
        """Test that HTML has valid structure."""
        html = generate_exec_snapshot(sample_sections, sample_briefing)
        assert html.count("<div") == html.count("</div") or html.count("<div") == html.count("</div>")

    def test_html_no_forbidden_phrases(self, sample_sections: Dict, sample_briefing: Dict) -> None:
        """Test that HTML contains no forbidden phrases."""
        html = generate_exec_snapshot(sample_sections, sample_briefing)
        forbidden = [
            "Wir empfehlen",
            "Es ist wichtig zu beachten",
            "Zusammenfassend lässt sich sagen",
        ]
        for phrase in forbidden:
            assert phrase not in html

    def test_html_contains_proper_badges(self, sample_sections: Dict, sample_briefing: Dict) -> None:
        """Test that HTML contains proper badge classes."""
        html = generate_exec_snapshot(sample_sections, sample_briefing)
        assert "badge" in html


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_sections(self) -> None:
        """Test with empty sections."""
        html = generate_exec_snapshot({}, {})
        assert isinstance(html, str)

    def test_empty_briefing(self, sample_sections: Dict) -> None:
        """Test with empty briefing."""
        html = generate_exec_snapshot(sample_sections, {})
        assert isinstance(html, str)

    def test_none_values(self) -> None:
        """Test with None values in sections."""
        sections = {
            "ROI_12M": None,
            "PAYBACK_MONTHS": None,
        }
        html = generate_exec_snapshot(sections, {})
        assert isinstance(html, str)

    def test_zero_kpi_values(self) -> None:
        """Test with zero KPI values."""
        sections = {
            "ROI_12M": 0,
            "PAYBACK_MONTHS": 0,
            "EINSPARUNG_MONAT_EUR": 0,
        }
        html = generate_exec_snapshot(sections, {})
        assert isinstance(html, str)
        assert "0%" in html or "0 Mt" in html


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests."""

    def test_full_workflow_de(self, sample_sections: Dict, sample_briefing: Dict) -> None:
        """Test full workflow in German."""
        result = inject_exec_snapshot_into_sections(sample_sections, sample_briefing, lang="de")
        html = result["EXEC_SNAPSHOT_HTML"]

        # Check all major elements
        assert "exec-snapshot-container" in html
        assert "Executive Snapshot" in html
        assert len(html) > 500

    def test_full_workflow_en(self, sample_sections: Dict, sample_briefing: Dict) -> None:
        """Test full workflow in English."""
        result = inject_exec_snapshot_into_sections(sample_sections, sample_briefing, lang="en")
        html = result["EXEC_SNAPSHOT_HTML"]

        # Check all major elements
        assert "exec-snapshot-container" in html
        assert len(html) > 500
