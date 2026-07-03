#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sprint G8.4 & G8.5: AI Act Persona Leak Protection & Regression Tests

Test Suite for:
- Persona leak detection in AI Act sections
- Size-specific content validation (Solo/Team/KMU)
- AI Act consistency checks
- End-to-End regression testing

Version: 1.0.0 (Sprint G8)
"""

import pytest
from typing import Any, Dict, List

# Import AI Act module functions
from services.ai_act_module import (
    determine_risk_level,
    generate_risk_reasoning,
    generate_duty_matrix_html,
    generate_noncompliance_alerts,
    generate_data_gaps,
    generate_next_steps_html,
    generate_usecase_risk_html,
    build_ai_act_sections,
    build_ai_act_sections_optimized,
    validate_ai_act_sections,
    ai_act_harmonize,
    validate_ai_act_persona_compliance,
    apply_ai_act_persona_filter,
    get_ai_act_exec_summary_injection,
    get_ai_act_business_case_injection,
    get_ai_act_roadmap_injection,
    EXTENDED_SOLO_FORBIDDEN,
    EXTENDED_TEAM_FORBIDDEN,
    EXTENDED_KMU_FORBIDDEN,
    VALID_RISK_LEVELS,
)


# =============================================================================
# G8.4: HELPER FUNCTIONS FOR PERSONA LEAK DETECTION
# =============================================================================

def extract_ai_act_sections(report: Dict[str, Any]) -> Dict[str, str]:
    """Extract all AI Act related sections from a report."""
    ai_act_keys = [
        "AI_ACT_RISK_LEVEL",
        "AI_ACT_RISK_REASONING",
        "AI_ACT_DUTY_MATRIX_HTML",
        "AI_ACT_NONCOMPLIANCE_ALERTS_HTML",
        "AI_ACT_DATA_GAPS_HTML",
        "AI_ACT_RECOMMENDED_NEXT_STEPS_HTML",
        "AI_ACT_RELATED_USECASES_HTML",
        "AI_ACT_EXEC_INJECTION",
        "AI_ACT_GOVERNANCE_INJECTION",
        "AI_ACT_RISKS_INJECTION",
        "AI_ACT_TOOLS_INJECTION",
    ]
    return {key: report.get(key, "") for key in ai_act_keys}


def no_team_terms_in_ai_act(ai_sections: Dict[str, str]) -> bool:
    """Check that no team/organization terms appear in AI Act sections."""
    for key, content in ai_sections.items():
        if not isinstance(content, str):
            continue
        content_lower = content.lower()
        for term in EXTENDED_SOLO_FORBIDDEN:
            if term.lower() in content_lower:
                return False
    return True


def no_solo_terms_in_ai_act(ai_sections: Dict[str, str]) -> bool:
    """Check that no solo-specific terms appear in AI Act sections."""
    forbidden = EXTENDED_TEAM_FORBIDDEN + EXTENDED_KMU_FORBIDDEN
    for key, content in ai_sections.items():
        if not isinstance(content, str):
            continue
        content_lower = content.lower()
        for term in set(forbidden):  # Remove duplicates
            if term.lower() in content_lower:
                return False
    return True


def no_kmu_terms_in_ai_act(ai_sections: Dict[str, str]) -> bool:
    """Check that no KMU-specific terms appear in Solo AI Act sections."""
    # For Solo reports, we also check KMU-specific terms
    kmu_only = ["governance board", "compliance-officer", "abteilungsleiter"]
    for key, content in ai_sections.items():
        if not isinstance(content, str):
            continue
        content_lower = content.lower()
        for term in kmu_only:
            if term in content_lower:
                return False
    return True


def assert_no_size_leaks_in_ai_act(report: Dict[str, Any], size: str) -> None:
    """
    G8.4: Main assertion function for persona leak detection.

    Validates that AI Act sections contain no size-inappropriate terms.

    Args:
        report: Report sections dictionary
        size: Size category ("solo", "team", or "kmu")

    Raises:
        AssertionError: If persona leaks are found
    """
    ai_sections = extract_ai_act_sections(report)
    size_lower = size.lower()

    if "solo" in size_lower or "freiberuf" in size_lower:
        assert no_team_terms_in_ai_act(ai_sections), \
            f"Team terms found in Solo AI Act sections"
        assert no_kmu_terms_in_ai_act(ai_sections), \
            f"KMU terms found in Solo AI Act sections"

    elif "team" in size_lower or "klein" in size_lower:
        assert no_solo_terms_in_ai_act(ai_sections), \
            f"Solo terms found in Team AI Act sections"

    else:  # KMU
        assert no_solo_terms_in_ai_act(ai_sections), \
            f"Solo terms found in KMU AI Act sections"


# =============================================================================
# G8.5: REGRESSION CHECK HELPERS
# =============================================================================

def assert_risk_level_is_consistent(report: Dict[str, Any]) -> None:
    """G8.5: Assert that risk level is valid and consistent."""
    risk_level = report.get("AI_ACT_RISK_LEVEL", "")
    assert risk_level in VALID_RISK_LEVELS, \
        f"Invalid risk level: {risk_level}, expected one of {VALID_RISK_LEVELS}"


def assert_duty_matrix_valid(report: Dict[str, Any]) -> None:
    """G8.5: Assert that duty matrix contains valid table structure."""
    matrix = report.get("AI_ACT_DUTY_MATRIX_HTML", "")
    assert "<table" in matrix.lower(), "Duty matrix missing <table> tag"
    assert "</table>" in matrix.lower(), "Duty matrix missing </table> tag"

    # Check minimum row count
    row_count = matrix.lower().count("<tr>") - 1  # Subtract header
    assert row_count >= 3, f"Duty matrix has only {row_count} rows (min 3)"


def assert_mandatory_reasoning_present(report: Dict[str, Any], min_words: int = 60) -> None:
    """G8.5: Assert that risk reasoning meets minimum word count."""
    reasoning = report.get("AI_ACT_RISK_REASONING", "")
    import re
    text_only = re.sub(r"<[^>]+>", "", reasoning).strip()
    word_count = len(text_only.split())
    assert word_count >= min_words, \
        f"Risk reasoning too short: {word_count} words (min {min_words})"


def assert_alerts_and_gaps_count(report: Dict[str, Any], max_alerts: int = 10, max_gaps: int = 8) -> None:
    """G8.5: Assert that alerts and gaps are within expected range."""
    alerts = report.get("AI_ACT_NONCOMPLIANCE_ALERTS", [])
    gaps = report.get("AI_ACT_DATA_GAPS", [])

    assert len(alerts) >= 2, f"Too few alerts: {len(alerts)} (min 2)"
    assert len(alerts) <= max_alerts, f"Too many alerts: {len(alerts)} (max {max_alerts})"

    assert len(gaps) >= 2, f"Too few gaps: {len(gaps)} (min 2)"
    assert len(gaps) <= max_gaps, f"Too many gaps: {len(gaps)} (max {max_gaps})"


def assert_ai_act_html_valid(report: Dict[str, Any]) -> None:
    """G8.5: Assert that AI Act HTML sections are well-formed."""
    html_keys = [
        "AI_ACT_DUTY_MATRIX_HTML",
        "AI_ACT_RECOMMENDED_NEXT_STEPS_HTML",
        "AI_ACT_RELATED_USECASES_HTML",
    ]

    for key in html_keys:
        html = report.get(key, "")
        if html:
            # Check for balanced tags (basic check)
            assert html.count("<") == html.count(">"), \
                f"{key} has unbalanced angle brackets"


def assert_no_hardguard_violations(report: Dict[str, Any], size: str) -> None:
    """G8.5: Assert no hard-guard violations in AI Act content."""
    violations = validate_ai_act_persona_compliance(report, size)
    assert len(violations) == 0, \
        f"Hard-guard violations found: {violations[:3]}"


# =============================================================================
# G8.4: PERSONA LEAK TESTS
# =============================================================================

class TestAIActPersonaLeaks:
    """Test suite for AI Act persona leak detection."""

    def test_solo_no_team_terms(self):
        """Solo reports should not contain team terminology."""
        briefing = {
            "branche": "Beratung",
            "unternehmensgroesse": "Solo-Selbstständig",
            "ki_einsatzbereiche": ["Content-Erstellung"],
            "lang": "de",
        }
        sections = build_ai_act_sections_optimized(briefing, lang="de")
        sections = ai_act_harmonize(sections, briefing)

        assert_no_size_leaks_in_ai_act(sections, "solo")

    def test_team_no_solo_terms(self):
        """Team reports should not contain solo terminology."""
        briefing = {
            "branche": "IT-Dienstleister",
            "unternehmensgroesse": "Team (2-10 MA)",
            "ki_einsatzbereiche": ["Softwareentwicklung"],
            "lang": "de",
        }
        sections = build_ai_act_sections_optimized(briefing, lang="de")
        sections = ai_act_harmonize(sections, briefing)

        assert_no_size_leaks_in_ai_act(sections, "team")

    def test_kmu_no_solo_terms(self):
        """KMU reports should not contain solo terminology."""
        briefing = {
            "branche": "Finanzdienstleister",
            "unternehmensgroesse": "KMU (11-50 MA)",
            "ki_einsatzbereiche": ["Kreditscoring", "Kundenservice"],
            "lang": "de",
        }
        sections = build_ai_act_sections_optimized(briefing, lang="de")
        sections = ai_act_harmonize(sections, briefing)

        assert_no_size_leaks_in_ai_act(sections, "kmu")

    def test_exec_summary_injection_solo(self):
        """Exec summary injection for Solo should not contain team terms."""
        injection = get_ai_act_exec_summary_injection("high-risk", "Solo", "Beratung", "de")

        for term in EXTENDED_SOLO_FORBIDDEN:
            assert term.lower() not in injection.lower(), \
                f"Forbidden term '{term}' found in Solo exec summary injection"

    def test_exec_summary_injection_team(self):
        """Exec summary injection for Team should not contain solo terms."""
        injection = get_ai_act_exec_summary_injection("limited", "Team", "IT", "de")

        for term in EXTENDED_TEAM_FORBIDDEN:
            assert term.lower() not in injection.lower(), \
                f"Forbidden term '{term}' found in Team exec summary injection"

    def test_persona_filter_removes_forbidden_terms(self):
        """Persona filter should replace size-inappropriate terms."""
        # Test Solo filter
        text_with_team = "Ihr Team sollte die Mitarbeiter schulen."
        filtered = apply_ai_act_persona_filter(text_with_team, "Solo")
        assert "ihr team" not in filtered.lower()

        # Test Team filter
        text_with_solo = "Als Einzelperson sollten Sie..."
        filtered = apply_ai_act_persona_filter(text_with_solo, "Team")
        assert "als einzelperson" not in filtered.lower()


# =============================================================================
# G8.5: REGRESSION TESTS
# =============================================================================

class TestAIActRegression:
    """End-to-end regression tests for AI Act module."""

    @pytest.fixture
    def solo_report(self):
        """Generate a Solo report for testing."""
        briefing = {
            "branche": "Beratung",
            "unternehmensgroesse": "Solo-Selbstständig",
            "ki_einsatzbereiche": ["Content-Erstellung", "Recherche"],
            "lang": "de",
        }
        sections = build_ai_act_sections_optimized(briefing, lang="de")
        return ai_act_harmonize(sections, briefing)

    @pytest.fixture
    def team_report(self):
        """Generate a Team report for testing."""
        briefing = {
            "branche": "IT-Dienstleister",
            "unternehmensgroesse": "Team (2-10 MA)",
            "ki_einsatzbereiche": ["Softwareentwicklung", "Testing"],
            "lang": "de",
        }
        sections = build_ai_act_sections_optimized(briefing, lang="de")
        return ai_act_harmonize(sections, briefing)

    @pytest.fixture
    def kmu_report(self):
        """Generate a KMU report for testing."""
        briefing = {
            "branche": "Finanzdienstleister",
            "unternehmensgroesse": "KMU (11-50 MA)",
            "ki_einsatzbereiche": ["Kreditscoring", "Kundenservice"],
            "lang": "de",
        }
        sections = build_ai_act_sections_optimized(briefing, lang="de")
        return ai_act_harmonize(sections, briefing)

    def test_solo_regression(self, solo_report):
        """Full regression test for Solo profile."""
        assert_risk_level_is_consistent(solo_report)
        assert_duty_matrix_valid(solo_report)
        assert_mandatory_reasoning_present(solo_report)
        assert_alerts_and_gaps_count(solo_report)
        assert_ai_act_html_valid(solo_report)
        assert_no_size_leaks_in_ai_act(solo_report, "solo")
        assert_no_hardguard_violations(solo_report, "Solo-Selbstständig")

    def test_team_regression(self, team_report):
        """Full regression test for Team profile."""
        assert_risk_level_is_consistent(team_report)
        assert_duty_matrix_valid(team_report)
        assert_mandatory_reasoning_present(team_report)
        assert_alerts_and_gaps_count(team_report)
        assert_ai_act_html_valid(team_report)
        assert_no_size_leaks_in_ai_act(team_report, "team")
        assert_no_hardguard_violations(team_report, "Team (2-10 MA)")

    def test_kmu_regression(self, kmu_report):
        """Full regression test for KMU profile."""
        assert_risk_level_is_consistent(kmu_report)
        assert_duty_matrix_valid(kmu_report)
        assert_mandatory_reasoning_present(kmu_report)
        assert_alerts_and_gaps_count(kmu_report)
        assert_ai_act_html_valid(kmu_report)
        assert_no_size_leaks_in_ai_act(kmu_report, "kmu")
        assert_no_hardguard_violations(kmu_report, "KMU (11-50 MA)")

    def test_high_risk_finance(self):
        """Test high-risk classification for finance sector."""
        briefing = {
            "branche": "Finanzdienstleister",
            "unternehmensgroesse": "KMU (50-100 MA)",
            "ki_einsatzbereiche": ["Kreditscoring", "Risikobewertung"],
            "lang": "de",
        }
        sections = build_ai_act_sections_optimized(briefing, lang="de")

        assert sections["AI_ACT_RISK_LEVEL"] == "high-risk"
        assert_mandatory_reasoning_present(sections, min_words=60)

    def test_high_risk_healthcare(self):
        """Test high-risk classification for healthcare sector."""
        briefing = {
            "branche": "Gesundheitswesen",
            "unternehmensgroesse": "Team",
            "ki_einsatzbereiche": ["Diagnoseunterstützung"],
            "lang": "de",
        }
        sections = build_ai_act_sections_optimized(briefing, lang="de")

        assert sections["AI_ACT_RISK_LEVEL"] == "high-risk"

    def test_limited_risk_legal(self):
        """Test limited risk classification for legal sector."""
        briefing = {
            "branche": "Rechtsanwaltskanzlei",
            "unternehmensgroesse": "Solo",
            "ki_einsatzbereiche": ["Rechtsrecherche"],
            "lang": "de",
        }
        sections = build_ai_act_sections_optimized(briefing, lang="de")

        assert sections["AI_ACT_RISK_LEVEL"] == "limited"

    def test_minimal_risk_general(self):
        """Test minimal risk classification for general business.

        KIS-1234: "Content-Erstellung" ist seit der Art.-50-Regel bewusst
        "limited" (Kennzeichnungspflicht für KI-generierte Inhalte ab
        02.08.2026) — der Minimal-Fall braucht einen Usecase OHNE
        Kundeninteraktion/Content-Generierung.
        """
        briefing = {
            "branche": "Allgemeine Beratung",
            "unternehmensgroesse": "Solo-Freiberufler",
            "ki_einsatzbereiche": ["Datenanalyse intern"],
            "lang": "de",
        }
        sections = build_ai_act_sections_optimized(briefing, lang="de")

        assert sections["AI_ACT_RISK_LEVEL"] == "minimal"

    def test_content_creation_is_limited_art50(self):
        """KIS-1234: KI-generierte Inhalte → Art. 50 Transparenzpflichten."""
        briefing = {
            "branche": "Allgemeine Beratung",
            "unternehmensgroesse": "Solo-Freiberufler",
            "ki_einsatzbereiche": ["Content-Erstellung"],
            "lang": "de",
        }
        sections = build_ai_act_sections_optimized(briefing, lang="de")

        assert sections["AI_ACT_RISK_LEVEL"] == "limited"


class TestAIActHarmonization:
    """Tests for the harmonization engine."""

    def test_harmonization_adds_injections(self):
        """Harmonization should add all injection fields."""
        briefing = {
            "branche": "IT",
            "unternehmensgroesse": "Team",
            "lang": "de",
        }
        sections = build_ai_act_sections_optimized(briefing, lang="de")
        harmonized = ai_act_harmonize(sections, briefing)

        assert "AI_ACT_EXEC_INJECTION" in harmonized
        assert "AI_ACT_GOVERNANCE_INJECTION" in harmonized
        assert "AI_ACT_RISKS_INJECTION" in harmonized
        assert "AI_ACT_TOOLS_INJECTION" in harmonized
        assert "AI_ACT_ROADMAP_90D_INJECTION" in harmonized
        assert "AI_ACT_ROADMAP_12M_INJECTION" in harmonized

    def test_harmonization_tracks_warnings(self):
        """Harmonization should track consistency warnings."""
        briefing = {
            "branche": "Finanzdienstleister",
            "unternehmensgroesse": "KMU",
            "lang": "de",
        }
        sections = build_ai_act_sections_optimized(briefing, lang="de")
        harmonized = ai_act_harmonize(sections, briefing)

        assert "AI_ACT_CONSISTENCY_WARNINGS" in harmonized
        assert isinstance(harmonized["AI_ACT_CONSISTENCY_WARNINGS"], list)


class TestAIActBusinessCase:
    """Tests for business case injection."""

    def test_high_risk_capex_modifier(self):
        """High-risk should have higher CAPEX modifier."""
        bc = get_ai_act_business_case_injection("high-risk", "KMU", "de")
        assert bc["CAPEX_MODIFIER"] > 1.0
        assert bc["OPEX_MODIFIER"] > 1.0

    def test_minimal_risk_no_modifier(self):
        """Minimal risk should have no cost modifier."""
        bc = get_ai_act_business_case_injection("minimal", "Solo", "de")
        assert bc["CAPEX_MODIFIER"] == 1.0
        assert bc["OPEX_MODIFIER"] == 1.0


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
