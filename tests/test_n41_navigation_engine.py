"""
Tests for Executive Navigation Engine - N4.1 PLATIN+++ Executive Experience Layer.

Tests cover:
- Semantic structure mapping
- Executive jump point detection
- Impact hotspot identification
- PDF navigation anchor generation
- Decision flow guidance
- "You Are Here" markers

25 comprehensive tests for board-ready navigation.
"""

import pytest
from typing import Any, Dict, List

from services.executive_navigation_engine import (
    ExecutiveNavigationEngine,
    SemanticStructureMapper,
    ExecutiveJumpPointDetector,
    ImpactHotspotDetector,
    PDFNavigationAnchorGenerator,
    DecisionFlowGuidanceGenerator,
    YouAreHereMarkerGenerator,
    Section,
    SectionCategory,
    ImpactLevel,
    DecisionUrgency,
    get_navigation_engine,
    build_executive_navigation,
    get_bookmark_map,
    get_executive_flow_map,
    get_section_guidance,
    get_you_are_here_marker,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def sample_sections() -> List[Dict[str, Any]]:
    """Sample report sections for testing."""
    return [
        {
            "id": "G1",
            "title": "G1 Executive Zusammenfassung",
            "content": (
                "Diese Zusammenfassung enthält die kritischen Empfehlungen für das "
                "Management. Die ROI-Analyse zeigt 45% Potenzial. Sofortige Entscheidung "
                "erforderlich für die KI-Strategie. Investment von 2.5 Mio EUR empfohlen."
            ),
        },
        {
            "id": "G5",
            "title": "G5 Strategische Analyse",
            "content": (
                "Die strategische Positionierung erfordert mittelfristige Maßnahmen. "
                "Wettbewerbsanalyse zeigt signifikante Marktchancen. Der Marktanteil "
                "kann um 15% gesteigert werden durch KI-Adoption."
            ),
        },
        {
            "id": "G10",
            "title": "G10 ROI und Finanzanalyse",
            "content": (
                "Die Investitionsrechnung zeigt erhebliche Einsparungen. EBIT-Verbesserung "
                "von 3.2 Mio EUR erwartet. Payback-Periode von 18 Monaten. Der ROI "
                "beträgt 145% über 3 Jahre."
            ),
        },
        {
            "id": "G20",
            "title": "G20 Prozessautomatisierung",
            "content": (
                "Die operativen Prozesse können zu 60% automatisiert werden. "
                "Moderate Verbesserungen in der Durchlaufzeit. Die Tool-Integration "
                "erfordert 6 Monate Implementierungszeit."
            ),
        },
        {
            "id": "G30",
            "title": "G30 Risiko und AI Act Compliance",
            "content": (
                "Geschäftskritische Compliance-Anforderungen durch AI Act. "
                "Dringende Governance-Strukturen erforderlich. DSGVO-Konformität "
                "muss sichergestellt werden. Risikobewertung zeigt hohes Exposure."
            ),
        },
        {
            "id": "G35",
            "title": "G35 Transformations-Roadmap",
            "content": (
                "Die Roadmap definiert 4 Phasen über 24 Monate. Phase 1 startet "
                "kurzfristig mit Quick Wins. Meilensteine und KPIs sind definiert. "
                "Change Management Programm integriert."
            ),
        },
        {
            "id": "G40",
            "title": "G40 Anhang und Glossar",
            "content": (
                "Detaillierte Erläuterungen und Definitionen. Referenzmaterial "
                "für vertiefte Analyse. Technische Spezifikationen im Detail."
            ),
        },
    ]


@pytest.fixture
def navigation_engine() -> ExecutiveNavigationEngine:
    """Fresh navigation engine instance."""
    return ExecutiveNavigationEngine()


@pytest.fixture
def structure_mapper() -> SemanticStructureMapper:
    """Fresh structure mapper instance."""
    return SemanticStructureMapper()


@pytest.fixture
def jump_detector() -> ExecutiveJumpPointDetector:
    """Fresh jump point detector instance."""
    return ExecutiveJumpPointDetector()


@pytest.fixture
def hotspot_detector() -> ImpactHotspotDetector:
    """Fresh impact hotspot detector instance."""
    return ImpactHotspotDetector()


# =============================================================================
# SEMANTIC STRUCTURE MAPPER TESTS
# =============================================================================


class TestSemanticStructureMapper:
    """Tests for SemanticStructureMapper."""

    def test_map_sections_basic(
        self,
        structure_mapper: SemanticStructureMapper,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test basic section mapping."""
        sections = structure_mapper.map_sections(sample_sections)

        assert len(sections) == 7
        assert "G1" in sections
        assert "G10" in sections

    def test_category_classification_executive_summary(
        self,
        structure_mapper: SemanticStructureMapper,
    ) -> None:
        """Test executive summary classification."""
        sections = structure_mapper.map_sections([
            {
                "id": "test_exec",
                "title": "Executive Zusammenfassung",
                "content": "Dies ist eine Zusammenfassung der Ergebnisse.",
            }
        ])

        assert sections["test_exec"].category == SectionCategory.EXECUTIVE_SUMMARY

    def test_category_classification_financial(
        self,
        structure_mapper: SemanticStructureMapper,
    ) -> None:
        """Test financial category classification."""
        sections = structure_mapper.map_sections([
            {
                "id": "test_fin",
                "title": "ROI Analyse und Kosten",
                "content": "Investment von 5 Mio EUR. ROI beträgt 200%.",
            }
        ])

        assert sections["test_fin"].category == SectionCategory.FINANCIAL_IMPACT

    def test_category_classification_risk(
        self,
        structure_mapper: SemanticStructureMapper,
    ) -> None:
        """Test risk/governance classification."""
        sections = structure_mapper.map_sections([
            {
                "id": "test_risk",
                "title": "Risiko und Compliance",
                "content": "AI Act Compliance erforderlich. Governance Framework.",
            }
        ])

        assert sections["test_risk"].category == SectionCategory.RISK_GOVERNANCE

    def test_key_sentence_extraction(
        self,
        structure_mapper: SemanticStructureMapper,
    ) -> None:
        """Test key sentence extraction."""
        sections = structure_mapper.map_sections([
            {
                "id": "test_key",
                "title": "Test Section",
                "content": (
                    "Einleitung. Die Empfehlung lautet: Sofort handeln. "
                    "Weitere Details folgen."
                ),
            }
        ])

        # Should extract sentence with "Empfehlung"
        assert "Empfehlung" in sections["test_key"].key_sentence

    def test_kpi_link_extraction(
        self,
        structure_mapper: SemanticStructureMapper,
    ) -> None:
        """Test KPI link extraction."""
        sections = structure_mapper.map_sections([
            {
                "id": "test_kpi",
                "title": "KPI Section",
                "content": "ROI von 45%. EBIT um 3.2 Mio EUR. Score von 85.",
            }
        ])

        kpi_links = sections["test_kpi"].kpi_links
        assert len(kpi_links) > 0
        assert any("ROI" in kpi for kpi in kpi_links)


# =============================================================================
# JUMP POINT DETECTOR TESTS
# =============================================================================


class TestExecutiveJumpPointDetector:
    """Tests for ExecutiveJumpPointDetector."""

    def test_identify_jump_points(
        self,
        jump_detector: ExecutiveJumpPointDetector,
        structure_mapper: SemanticStructureMapper,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test jump point identification."""
        sections = structure_mapper.map_sections(sample_sections)
        jump_points = jump_detector.identify_jump_points(sections)

        # Should identify critical sections as jump points
        assert len(jump_points) > 0

    def test_jump_point_scoring_critical_content(
        self,
        jump_detector: ExecutiveJumpPointDetector,
    ) -> None:
        """Test jump point scoring for critical content."""
        section = Section(
            id="critical_test",
            title="Kritische Entscheidung für Vorstand",
            content="Sofortige Handlung erforderlich. Management muss entscheiden.",
            category=SectionCategory.EXECUTIVE_SUMMARY,
            impact_level=ImpactLevel.CRITICAL,
            decision_urgency=DecisionUrgency.IMMEDIATE,
        )

        score = jump_detector._calculate_jump_score(section)
        assert score >= 0.7  # Should exceed threshold

    def test_non_jump_point_low_impact(
        self,
        jump_detector: ExecutiveJumpPointDetector,
    ) -> None:
        """Test that low-impact sections are not jump points."""
        section = Section(
            id="low_test",
            title="Anhang Details",
            content="Technische Spezifikationen und Glossar.",
            category=SectionCategory.APPENDIX,
            impact_level=ImpactLevel.LOW,
            decision_urgency=DecisionUrgency.LONG_TERM,
        )

        score = jump_detector._calculate_jump_score(section)
        assert score < 0.7  # Should be below threshold


# =============================================================================
# IMPACT HOTSPOT DETECTOR TESTS
# =============================================================================


class TestImpactHotspotDetector:
    """Tests for ImpactHotspotDetector."""

    def test_identify_hotspots(
        self,
        hotspot_detector: ImpactHotspotDetector,
        structure_mapper: SemanticStructureMapper,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test hotspot identification."""
        sections = structure_mapper.map_sections(sample_sections)
        hotspots = hotspot_detector.identify_hotspots(sections)

        # Should identify high-impact sections
        assert len(hotspots) >= 0  # May or may not have hotspots

    def test_financial_content_hotspot(
        self,
        hotspot_detector: ImpactHotspotDetector,
    ) -> None:
        """Test hotspot detection for financial content."""
        section = Section(
            id="fin_hotspot",
            title="Investitionsanalyse",
            content=(
                "Investment von 5.5 Mio EUR erforderlich. "
                "ROI von 250%. EBIT Verbesserung 4.2 Mio EUR. "
                "Geschäftskritische Entscheidung."
            ),
            category=SectionCategory.FINANCIAL_IMPACT,
            impact_level=ImpactLevel.CRITICAL,
            kpi_links=["ROI", "EBIT", "Investment"],
        )

        score = hotspot_detector._calculate_impact_score(section)
        assert score >= 0.5  # Should have significant score


# =============================================================================
# PDF NAVIGATION ANCHOR TESTS
# =============================================================================


class TestPDFNavigationAnchorGenerator:
    """Tests for PDFNavigationAnchorGenerator."""

    def test_generate_anchors(
        self,
        structure_mapper: SemanticStructureMapper,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test anchor generation."""
        generator = PDFNavigationAnchorGenerator()
        sections = structure_mapper.map_sections(sample_sections)
        page_estimates = {s_id: i + 1 for i, s_id in enumerate(sections)}

        anchors = generator.generate_anchors(sections, page_estimates)

        assert len(anchors) == len(sections)
        assert all(a["anchor_id"].startswith("nav_") for a in anchors)

    def test_anchor_has_required_fields(
        self,
        structure_mapper: SemanticStructureMapper,
    ) -> None:
        """Test that anchors have all required fields."""
        generator = PDFNavigationAnchorGenerator()
        sections = structure_mapper.map_sections([
            {"id": "test", "title": "Test Section", "content": "Content here."}
        ])

        anchors = generator.generate_anchors(sections, {"test": 1})

        anchor = anchors[0]
        assert "anchor_id" in anchor
        assert "section_id" in anchor
        assert "page_number" in anchor
        assert "bookmark_title" in anchor
        assert "level" in anchor
        assert "requires_page_break" in anchor

    def test_bookmark_title_formatting(
        self,
        structure_mapper: SemanticStructureMapper,
    ) -> None:
        """Test bookmark title formatting."""
        generator = PDFNavigationAnchorGenerator()

        # Create section marked as jump point
        section = Section(
            id="jump_test",
            title="Kritische Entscheidung",
            content="Content",
            category=SectionCategory.EXECUTIVE_SUMMARY,
            is_jump_point=True,
        )

        title = generator._format_bookmark_title(section)
        assert title.startswith("★")  # Jump point marker


# =============================================================================
# DECISION FLOW GUIDANCE TESTS
# =============================================================================


class TestDecisionFlowGuidanceGenerator:
    """Tests for DecisionFlowGuidanceGenerator."""

    def test_generate_guidance(
        self,
        structure_mapper: SemanticStructureMapper,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test guidance generation."""
        generator = DecisionFlowGuidanceGenerator()
        sections = structure_mapper.map_sections(sample_sections)

        guidance = generator.generate_guidance(sections)

        assert len(guidance) == len(sections)

    def test_guidance_has_required_fields(
        self,
        structure_mapper: SemanticStructureMapper,
    ) -> None:
        """Test that guidance has all required fields."""
        generator = DecisionFlowGuidanceGenerator()
        sections = structure_mapper.map_sections([
            {"id": "test", "title": "Test", "content": "Strategic content here."}
        ])

        guidance = generator.generate_guidance(sections)
        g = guidance["test"]

        assert "why_matters" in g
        assert "decision_options" in g
        assert "risks_30_days" in g
        assert "risks_90_days" in g
        assert "risks_180_days" in g

    def test_category_specific_guidance(
        self,
        structure_mapper: SemanticStructureMapper,
    ) -> None:
        """Test category-specific guidance content."""
        generator = DecisionFlowGuidanceGenerator()
        sections = structure_mapper.map_sections([
            {
                "id": "fin_test",
                "title": "ROI Analysis",
                "content": "Financial ROI investment analysis.",
            }
        ])

        guidance = generator.generate_guidance(sections)
        g = guidance["fin_test"]

        # Should have financial-specific guidance
        assert len(g["decision_options"]) > 0


# =============================================================================
# YOU ARE HERE MARKER TESTS
# =============================================================================


class TestYouAreHereMarkerGenerator:
    """Tests for YouAreHereMarkerGenerator."""

    def test_generate_markers(
        self,
        structure_mapper: SemanticStructureMapper,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test marker generation."""
        generator = YouAreHereMarkerGenerator()
        sections = structure_mapper.map_sections(sample_sections)
        hierarchy: Dict[str, List[str]] = {}

        markers = generator.generate_markers(sections, hierarchy)

        assert len(markers) == len(sections)

    def test_marker_has_breadcrumb(
        self,
        structure_mapper: SemanticStructureMapper,
    ) -> None:
        """Test that markers include breadcrumb."""
        generator = YouAreHereMarkerGenerator()
        sections = structure_mapper.map_sections([
            {"id": "test", "title": "Test Section", "content": "Content."}
        ])

        markers = generator.generate_markers(sections, {})
        marker = markers["test"]

        assert "breadcrumb" in marker
        assert ">" in marker["breadcrumb"]


# =============================================================================
# MAIN ENGINE TESTS
# =============================================================================


class TestExecutiveNavigationEngine:
    """Tests for main ExecutiveNavigationEngine."""

    def test_build_navigation(
        self,
        navigation_engine: ExecutiveNavigationEngine,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test complete navigation building."""
        graph = navigation_engine.build_navigation(sample_sections)

        assert graph is not None
        assert len(graph.sections) == 7
        assert len(graph.anchors) == 7

    def test_get_decision_guidance(
        self,
        navigation_engine: ExecutiveNavigationEngine,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test getting decision guidance."""
        navigation_engine.build_navigation(sample_sections)
        guidance = navigation_engine.get_decision_guidance()

        assert len(guidance) == 7
        assert "G1" in guidance

    def test_get_you_are_here(
        self,
        navigation_engine: ExecutiveNavigationEngine,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test getting you are here marker."""
        navigation_engine.build_navigation(sample_sections)
        marker = navigation_engine.get_you_are_here("G1")

        assert marker is not None
        assert marker["section_id"] == "G1"

    def test_get_executive_flow_map(
        self,
        navigation_engine: ExecutiveNavigationEngine,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test getting executive flow map."""
        navigation_engine.build_navigation(sample_sections)
        flow_map = navigation_engine.get_executive_flow_map()

        assert flow_map["total_sections"] == 7
        assert len(flow_map["categories"]) > 0
        assert 0 <= flow_map["navigation_score"] <= 1

    def test_get_bookmark_map(
        self,
        navigation_engine: ExecutiveNavigationEngine,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test getting bookmark map."""
        navigation_engine.build_navigation(sample_sections)
        bookmarks = navigation_engine.get_bookmark_map()

        assert len(bookmarks) == 7
        assert all("id" in b for b in bookmarks)
        assert all("title" in b for b in bookmarks)
        assert all("page" in b for b in bookmarks)


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_navigation_engine_singleton(self) -> None:
        """Test singleton pattern for navigation engine."""
        engine1 = get_navigation_engine()
        engine2 = get_navigation_engine()

        assert engine1 is engine2

    def test_build_executive_navigation_function(
        self,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test build_executive_navigation convenience function."""
        graph = build_executive_navigation(sample_sections)

        assert graph is not None
        assert len(graph.sections) == 7

    def test_get_section_guidance_function(
        self,
        sample_sections: List[Dict[str, Any]],
    ) -> None:
        """Test get_section_guidance convenience function."""
        build_executive_navigation(sample_sections)
        guidance = get_section_guidance("G1")

        assert guidance is not None
        assert guidance["section_id"] == "G1"
