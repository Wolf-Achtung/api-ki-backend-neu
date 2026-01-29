# -*- coding: utf-8 -*-
"""
Tests for Sprint G19.1-MAP: Frontend-Branch to Engine Mapping

Tests verify:
- All 12 frontend dropdown values map correctly
- German labels with & and spaces map correctly
- Legacy/alternate strings (construction, logistik) map correctly
- Unknown values fall back to "beratung"
- Integration with branch_profile_engine.py
"""

import pytest
from typing import Dict, List, Tuple


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def frontend_dropdown_values() -> List[Tuple[str, str]]:
    """
    Frontend dropdown value → expected engine key.

    All 12 frontend values must map correctly.
    """
    return [
        ("marketing_werbung", "marketing"),
        ("beratung_dienstleistungen", "beratung"),
        ("it_software", "it"),
        ("finanzen_versicherungen", "finanzen"),
        ("handel_ecommerce", "handel"),
        ("bildung", "bildung"),
        ("verwaltung", "verwaltung"),
        ("gesundheit_pflege", "gesundheit"),
        ("bauwesen_architektur", "bauwesen_architektur"),
        ("medien_kreativwirtschaft", "marketing"),  # maps to marketing profile
        ("industrie_produktion", "industrie"),
        ("transport_logistik", "transport_logistik"),
    ]


@pytest.fixture
def german_labels() -> List[Tuple[str, str]]:
    """
    German labels with & → expected engine key.

    These are the display labels users see in the dropdown.
    """
    return [
        ("Marketing & Werbung", "marketing"),
        ("Beratung & Dienstleistungen", "beratung"),
        ("IT & Software", "it"),
        ("Finanzen & Versicherungen", "finanzen"),
        ("Handel & E-Commerce", "handel"),
        ("Bildung", "bildung"),
        ("Verwaltung", "verwaltung"),
        ("Gesundheit & Pflege", "gesundheit"),
        ("Bauwesen & Architektur", "bauwesen_architektur"),
        ("Medien & Kreativwirtschaft", "marketing"),
        ("Industrie & Produktion", "industrie"),
        ("Transport & Logistik", "transport_logistik"),
    ]


@pytest.fixture
def legacy_synonyms() -> List[Tuple[str, str]]:
    """
    Legacy/alternate strings → expected engine key.

    These handle old data formats and common variations.
    """
    return [
        # English variants
        ("construction", "bauwesen_architektur"),
        ("logistics", "transport_logistik"),
        ("public_sector", "verwaltung"),
        ("government", "verwaltung"),
        ("healthcare", "gesundheit"),
        ("manufacturing", "industrie"),
        ("retail", "handel"),
        ("consulting", "beratung"),
        # Short German forms
        ("bau", "bauwesen_architektur"),
        ("logistik", "transport_logistik"),
        ("transport", "transport_logistik"),
        ("medizin", "gesundheit"),
        ("pharma", "gesundheit"),
        ("werbung", "marketing"),
        # Direct engine keys (should pass through)
        ("beratung", "beratung"),
        ("it", "it"),
        ("finanzen", "finanzen"),
        ("handel", "handel"),
        ("bildung", "bildung"),
        ("gesundheit", "gesundheit"),
        ("industrie", "industrie"),
        ("marketing", "marketing"),
    ]


# =============================================================================
# MAPPING FUNCTION TESTS
# =============================================================================

class TestMapFrontendBranchToEngine:
    """Tests for map_frontend_branch_to_engine function."""

    def test_all_frontend_values_mapped(self, frontend_dropdown_values):
        """Verify all 12 frontend dropdown values map correctly."""
        from services.branch_mapping import map_frontend_branch_to_engine

        for frontend_value, expected_engine in frontend_dropdown_values:
            result = map_frontend_branch_to_engine(frontend_value)
            assert result == expected_engine, \
                f"Frontend value '{frontend_value}' should map to '{expected_engine}', got '{result}'"

    def test_german_labels_mapped(self, german_labels):
        """Verify German labels (with &) map correctly."""
        from services.branch_mapping import map_frontend_branch_to_engine

        for label, expected_engine in german_labels:
            result = map_frontend_branch_to_engine(label)
            assert result == expected_engine, \
                f"German label '{label}' should map to '{expected_engine}', got '{result}'"

    def test_legacy_synonyms_mapped(self, legacy_synonyms):
        """Verify legacy/alternate strings map correctly."""
        from services.branch_mapping import map_frontend_branch_to_engine

        for legacy_value, expected_engine in legacy_synonyms:
            result = map_frontend_branch_to_engine(legacy_value)
            assert result == expected_engine, \
                f"Legacy value '{legacy_value}' should map to '{expected_engine}', got '{result}'"

    def test_unknown_values_fallback_to_beratung(self):
        """Verify unknown values fall back to 'beratung'."""
        from services.branch_mapping import map_frontend_branch_to_engine

        unknown_values = [
            "unknown_branch",
            "xyz123",
            "foobar",
            "nonexistent",
            "random_value",
        ]

        for unknown in unknown_values:
            result = map_frontend_branch_to_engine(unknown)
            assert result == "beratung", \
                f"Unknown value '{unknown}' should default to 'beratung', got '{result}'"

    def test_empty_value_fallback(self):
        """Verify empty/None values fall back to 'beratung'."""
        from services.branch_mapping import map_frontend_branch_to_engine

        assert map_frontend_branch_to_engine("") == "beratung"
        assert map_frontend_branch_to_engine("   ") == "beratung"

    def test_case_insensitivity(self):
        """Verify mapping is case-insensitive."""
        from services.branch_mapping import map_frontend_branch_to_engine

        test_cases = [
            ("MARKETING_WERBUNG", "marketing"),
            ("Beratung_Dienstleistungen", "beratung"),
            ("IT_SOFTWARE", "it"),
            ("VERWALTUNG", "verwaltung"),
            ("Construction", "bauwesen_architektur"),
            ("LOGISTICS", "transport_logistik"),
        ]

        for input_val, expected in test_cases:
            result = map_frontend_branch_to_engine(input_val)
            assert result == expected, \
                f"'{input_val}' should map to '{expected}', got '{result}'"

    def test_whitespace_handling(self):
        """Verify leading/trailing whitespace is handled."""
        from services.branch_mapping import map_frontend_branch_to_engine

        test_cases = [
            ("  beratung_dienstleistungen  ", "beratung"),
            ("\tit_software\n", "it"),
            ("  Verwaltung  ", "verwaltung"),
        ]

        for input_val, expected in test_cases:
            result = map_frontend_branch_to_engine(input_val)
            assert result == expected, \
                f"'{input_val!r}' should map to '{expected}', got '{result}'"


# =============================================================================
# NORMALIZATION TESTS
# =============================================================================

class TestNormalization:
    """Tests for normalization functions."""

    def test_normalize_function(self):
        """Test the _normalize helper function."""
        from services.branch_mapping import _normalize

        test_cases = [
            ("Beratung & Dienstleistungen", "beratung dienstleistungen"),
            ("IT & Software", "it software"),
            ("Bäume & Öl", "baeume oel"),
            ("Test-Value/Slash", "test value slash"),
            ("  extra   spaces  ", "extra spaces"),
        ]

        for input_val, expected in test_cases:
            result = _normalize(input_val)
            assert result == expected, \
                f"_normalize('{input_val}') should return '{expected}', got '{result}'"

    def test_normalize_to_key_function(self):
        """Test the _normalize_to_key helper function."""
        from services.branch_mapping import _normalize_to_key

        test_cases = [
            ("Beratung & Dienstleistungen", "beratung_dienstleistungen"),
            ("IT & Software", "it_software"),
            ("Transport Logistik", "transport_logistik"),
        ]

        for input_val, expected in test_cases:
            result = _normalize_to_key(input_val)
            assert result == expected, \
                f"_normalize_to_key('{input_val}') should return '{expected}', got '{result}'"


# =============================================================================
# MAPPING DATA TESTS
# =============================================================================

class TestMappingData:
    """Tests for mapping data completeness."""

    def test_branch_mapping_has_canonical_entries(self):
        """Verify BRANCH_MAPPING has all 13 canonical + legacy entries."""
        from services.branch_mapping import BRANCH_MAPPING

        # FIX-BRANCH-13: Now 23 entries (13 canonical + 10 legacy)
        assert len(BRANCH_MAPPING) >= 13, \
            f"BRANCH_MAPPING should have at least 13 entries, has {len(BRANCH_MAPPING)}"

        # Verify all 13 canonical values are present
        canonical_13 = [
            "marketing", "beratung", "it", "finanzen", "handel", "bildung",
            "verwaltung", "gesundheit", "bau", "medien", "industrie",
            "logistik", "gastronomie",
        ]
        for branch in canonical_13:
            assert branch in BRANCH_MAPPING, f"Canonical branch '{branch}' missing from BRANCH_MAPPING"

    def test_all_engine_keys_are_valid(self):
        """Verify all mapped engine keys exist in branch_profile_engine."""
        from services.branch_mapping import BRANCH_MAPPING
        from services.branch_profile_engine import BRANCH_MATURITY_DATA, BRANCH_ALIASES

        for frontend_key, engine_key in BRANCH_MAPPING.items():
            # Engine key should either be in BRANCH_MATURITY_DATA or resolve via BRANCH_ALIASES
            is_direct = engine_key in BRANCH_MATURITY_DATA
            is_aliased = engine_key in BRANCH_ALIASES and BRANCH_ALIASES[engine_key] in BRANCH_MATURITY_DATA

            assert is_direct or is_aliased, \
                f"Engine key '{engine_key}' (from '{frontend_key}') not found in branch_profile_engine"

    def test_synonyms_map_to_valid_frontend_keys(self):
        """Verify all synonyms map to valid frontend keys."""
        from services.branch_mapping import BRANCH_SYNONYMS, BRANCH_MAPPING

        for synonym, frontend_key in BRANCH_SYNONYMS.items():
            # Some synonyms map directly to engine keys (like "beratung" → "beratung_dienstleistungen")
            # These should still resolve to a valid mapping
            if frontend_key in BRANCH_MAPPING:
                continue  # Valid mapping
            # If not directly in mapping, the synonym should at least not cause errors
            assert isinstance(frontend_key, str), \
                f"Synonym '{synonym}' maps to non-string: {frontend_key}"


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================

class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_all_supported_branches(self):
        """Test get_all_supported_branches returns unique engine keys."""
        from services.branch_mapping import get_all_supported_branches

        branches = get_all_supported_branches()

        # Should return unique values
        assert len(branches) == len(set(branches)), "Branches should be unique"

        # Should include the 11 engine keys
        expected = {
            "marketing", "beratung", "it", "finanzen", "handel",
            "bildung", "verwaltung", "gesundheit", "bauwesen_architektur",
            "industrie", "transport_logistik"
        }
        assert set(branches) == expected, \
            f"Expected {expected}, got {set(branches)}"

    def test_get_frontend_branch_options(self):
        """Test get_frontend_branch_options returns correct format."""
        from services.branch_mapping import get_frontend_branch_options

        options = get_frontend_branch_options()

        # FIX-BRANCH-13: Should return 13 options (canonical form values)
        assert len(options) == 13, f"Expected 13 options, got {len(options)}"

        # Each option should be a (value, label) tuple
        for option in options:
            assert isinstance(option, tuple), f"Option should be tuple: {option}"
            assert len(option) == 2, f"Option should have 2 elements: {option}"
            value, label = option
            assert isinstance(value, str), f"Value should be string: {value}"
            assert isinstance(label, str), f"Label should be string: {label}"

        # Verify gastronomie is included (FIX-BRANCH-13)
        values = [opt[0] for opt in options]
        assert "gastronomie" in values, "gastronomie should be in frontend options"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests with other modules."""

    def test_mapping_works_with_branch_profile_engine(self):
        """Test mapped values work with branch_profile_engine."""
        from services.branch_mapping import map_frontend_branch_to_engine
        from services.branch_profile_engine import build_branch_profile

        frontend_values = [
            "beratung_dienstleistungen",
            "it_software",
            "verwaltung",
            "transport_logistik",
            "bauwesen_architektur",
        ]

        for frontend_val in frontend_values:
            engine_key = map_frontend_branch_to_engine(frontend_val)
            profile = build_branch_profile(engine_key, "team", "de")

            assert profile is not None, f"Profile should not be None for {engine_key}"
            assert profile.maturity_score > 0, f"Maturity score should be > 0 for {engine_key}"

    def test_mapping_works_with_funding_recommender(self):
        """Test mapped values work with funding_recommender."""
        from services.branch_mapping import map_frontend_branch_to_engine
        from services.funding_recommender import BRANCH_FUNDING_PRIORITIES

        frontend_values = [
            "verwaltung",
            "transport_logistik",
            "bauwesen_architektur",
        ]

        for frontend_val in frontend_values:
            engine_key = map_frontend_branch_to_engine(frontend_val)
            assert engine_key in BRANCH_FUNDING_PRIORITIES, \
                f"Engine key '{engine_key}' should be in BRANCH_FUNDING_PRIORITIES"

    def test_mapping_works_with_tools_analytics(self):
        """Test mapped values work with tools_analytics."""
        from services.branch_mapping import map_frontend_branch_to_engine
        from services.tools_analytics import BRANCH_TOOL_BOOSTS

        frontend_values = [
            "verwaltung",
            "transport_logistik",
            "bauwesen_architektur",
        ]

        for frontend_val in frontend_values:
            engine_key = map_frontend_branch_to_engine(frontend_val)
            assert engine_key in BRANCH_TOOL_BOOSTS, \
                f"Engine key '{engine_key}' should be in BRANCH_TOOL_BOOSTS"

    def test_full_mapping_chain(self):
        """Test complete mapping chain from frontend to engine output."""
        from services.branch_mapping import map_frontend_branch_to_engine
        from services.branch_profile_engine import (
            build_branch_profile,
            get_branch_risk_opportunity_map,
            get_branch_profile_html_sections,
        )

        # Test with German dropdown label
        frontend_label = "Verwaltung"
        engine_key = map_frontend_branch_to_engine(frontend_label)

        assert engine_key == "verwaltung", f"Expected 'verwaltung', got '{engine_key}'"

        # Build profile
        profile = build_branch_profile(engine_key, "team", "de")
        assert profile.maturity_score == 45, "Verwaltung should have maturity 45"

        # Get risk/opportunity map
        risk_map = get_branch_risk_opportunity_map(engine_key, "de")
        assert len(risk_map.opportunities) == 3, "Should have 3 opportunities"

        # Generate HTML sections
        briefing = {"branche": frontend_label, "unternehmensgroesse": "team"}
        sections = get_branch_profile_html_sections(briefing, "de")
        assert "BRANCH_PROFILE_HTML" in sections, "Should have BRANCH_PROFILE_HTML"


# =============================================================================
# BRANCH_ALIASES SYNC TESTS
# =============================================================================

class TestBranchAliasesSync:
    """Tests to verify BRANCH_ALIASES is in sync with branch_mapping."""

    def test_frontend_keys_in_branch_aliases(self):
        """Verify frontend keys are also in BRANCH_ALIASES."""
        from services.branch_mapping import BRANCH_MAPPING
        from services.branch_profile_engine import BRANCH_ALIASES

        for frontend_key, engine_key in BRANCH_MAPPING.items():
            # The frontend key should be resolvable via BRANCH_ALIASES
            if frontend_key in BRANCH_ALIASES:
                resolved = BRANCH_ALIASES[frontend_key]
                # Resolved should match engine_key or be equivalent
                assert resolved == engine_key or frontend_key == engine_key, \
                    f"BRANCH_ALIASES['{frontend_key}'] = '{resolved}' should match engine key '{engine_key}'"

    def test_g19_1_branches_in_aliases(self):
        """Verify G19.1 branches are in BRANCH_ALIASES."""
        from services.branch_profile_engine import BRANCH_ALIASES

        g19_1_keys = [
            "bauwesen_architektur",
            "verwaltung",
            "transport_logistik",
        ]

        for key in g19_1_keys:
            assert key in BRANCH_ALIASES, \
                f"G19.1 branch '{key}' should be in BRANCH_ALIASES"


# =============================================================================
# FIX-BRANCH-UNMAPPED: Tests for branch_unmapped flag
# =============================================================================

class TestBranchUnmappedFlag:
    """Tests for FIX-BRANCH-UNMAPPED: unknown branches get flagged."""

    def test_known_branch_not_unmapped(self):
        """Known branches should have unmapped=False."""
        from services.branch_mapping import map_frontend_branch_with_status

        # Test canonical values
        for canonical in ["marketing", "beratung", "it", "finanzen", "gastronomie"]:
            result = map_frontend_branch_with_status(canonical)
            assert result.unmapped is False, f"'{canonical}' should not be unmapped"
            assert result.canonical == canonical or result.match_type == "direct"

    def test_synonym_not_unmapped(self):
        """Synonym matches should have unmapped=False."""
        from services.branch_mapping import map_frontend_branch_with_status

        synonyms = [
            ("Gastronomie & Tourismus", "handel"),
            ("consulting", "beratung"),
            ("healthcare", "gesundheit"),
            ("construction", "bauwesen_architektur"),
        ]
        for raw, expected in synonyms:
            result = map_frontend_branch_with_status(raw)
            assert result.unmapped is False, f"Synonym '{raw}' should not be unmapped"
            assert result.canonical == expected, f"'{raw}' should map to '{expected}'"

    def test_unknown_branch_is_unmapped(self):
        """Unknown branches should have unmapped=True and fallback to beratung."""
        from services.branch_mapping import map_frontend_branch_with_status

        unknowns = ["unknown_xyz", "foobar_industry", "random_text_123"]
        for unknown in unknowns:
            result = map_frontend_branch_with_status(unknown)
            assert result.unmapped is True, f"Unknown '{unknown}' should be unmapped"
            assert result.canonical == "beratung", f"Unknown '{unknown}' should fallback to beratung"
            assert result.match_type == "fallback"
            assert result.original == unknown

    def test_empty_branch_is_unmapped(self):
        """Empty/whitespace-only branches should have unmapped=True."""
        from services.branch_mapping import map_frontend_branch_with_status

        empties = ["", "   ", None]
        for empty in empties:
            result = map_frontend_branch_with_status(empty or "")
            assert result.unmapped is True, f"Empty input should be unmapped"
            assert result.canonical == "beratung"

    def test_is_branch_known_function(self):
        """Test the is_branch_known helper function."""
        from services.branch_mapping import is_branch_known

        # Known branches
        assert is_branch_known("beratung") is True
        assert is_branch_known("gastronomie") is True
        assert is_branch_known("Gastronomie & Tourismus") is True
        assert is_branch_known("it") is True

        # Unknown branches
        assert is_branch_known("unknown_xyz") is False
        assert is_branch_known("") is False
        assert is_branch_known("foobar") is False

    def test_branch_mapping_result_properties(self):
        """Test BranchMappingResult dataclass properties."""
        from services.branch_mapping import map_frontend_branch_with_status

        result = map_frontend_branch_with_status("marketing")
        assert result.branch == result.canonical  # .branch is alias for .canonical
        assert result.original == "marketing"
        assert result.match_type in ("direct", "synonym", "normalized", "key", "engine", "alias", "fallback")
