# -*- coding: utf-8 -*-
"""
Tests for FIX-BRANCH-13: 13-Branch Catalog and Company Size Normalizer.

These tests verify:
1. All 13 canonical branch values map correctly (no default-to-beratung)
2. Gastronomie is properly supported
3. Company size normalizer handles En-Dash correctly
4. get_frontend_branch_options() returns exactly 13 entries
"""

import pytest
from services.branch_mapping import (
    map_frontend_branch_to_engine,
    get_frontend_branch_options,
    BRANCH_MAPPING,
    BRANCH_SYNONYMS,
)
from services.company_size_normalizer import (
    normalize_company_size,
    get_company_size_bucket,
)


# =============================================================================
# TEST: 13 Canonical Branch Values
# =============================================================================

class TestCanonical13Branches:
    """Tests for the 13 canonical branch values."""

    # The 13 canonical form values from formbuilder_de_SINGLE_FULL.js
    CANONICAL_13 = [
        "marketing",
        "beratung",
        "it",
        "finanzen",
        "handel",
        "bildung",
        "verwaltung",
        "gesundheit",
        "bau",
        "medien",
        "industrie",
        "logistik",
        "gastronomie",
    ]

    def test_all_13_canonical_values_map_without_default_fallback(self):
        """
        All 13 canonical form values should map to a specific engine key,
        NOT fall back to 'beratung' as default.
        """
        for branch in self.CANONICAL_13:
            engine_key = map_frontend_branch_to_engine(branch)
            # The only branches that should map to 'beratung' are:
            # - 'beratung' itself
            # - Empty/unknown values (which we're not testing here)
            if branch != "beratung":
                assert engine_key != "beratung" or branch == "beratung", (
                    f"Branch '{branch}' should NOT default to 'beratung', "
                    f"but got engine_key='{engine_key}'"
                )

    def test_get_frontend_branch_options_returns_exactly_13(self):
        """get_frontend_branch_options() should return exactly 13 entries."""
        options = get_frontend_branch_options()
        assert len(options) == 13, f"Expected 13 options, got {len(options)}"

    def test_get_frontend_branch_options_includes_gastronomie(self):
        """get_frontend_branch_options() should include gastronomie."""
        options = get_frontend_branch_options()
        values = [opt[0] for opt in options]
        assert "gastronomie" in values, (
            f"'gastronomie' not found in options: {values}"
        )

    def test_all_13_canonical_values_in_frontend_options(self):
        """All 13 canonical values should be in get_frontend_branch_options()."""
        options = get_frontend_branch_options()
        option_values = [opt[0] for opt in options]

        for branch in self.CANONICAL_13:
            assert branch in option_values, (
                f"Canonical branch '{branch}' not found in frontend options"
            )

    def test_all_13_canonical_values_in_branch_mapping(self):
        """All 13 canonical values should have entries in BRANCH_MAPPING."""
        for branch in self.CANONICAL_13:
            assert branch in BRANCH_MAPPING, (
                f"Canonical branch '{branch}' not found in BRANCH_MAPPING"
            )


# =============================================================================
# TEST: Gastronomie Branch Support
# =============================================================================

class TestGastronomieBranch:
    """Tests for Gastronomie & Tourismus branch support."""

    def test_gastronomie_maps_to_handel(self):
        """Gastronomie should map to 'handel' engine profile."""
        engine_key = map_frontend_branch_to_engine("gastronomie")
        assert engine_key == "handel", (
            f"'gastronomie' should map to 'handel', got '{engine_key}'"
        )

    def test_gastronomie_synonyms_map_correctly(self):
        """All Gastronomie synonyms should map to the gastronomie canonical value."""
        synonyms = [
            "gastronomie",
            "Gastronomie & Tourismus",
            "gastronomie und tourismus",
            "tourismus",
            "hotel",
            "hotellerie",
            "restaurant",
            "gastgewerbe",
            "gastro",
            "hospitality",
        ]
        for synonym in synonyms:
            engine_key = map_frontend_branch_to_engine(synonym)
            # All should map to 'handel' (via gastronomie canonical)
            assert engine_key == "handel", (
                f"Synonym '{synonym}' should map to 'handel' via gastronomie, "
                f"got '{engine_key}'"
            )

    def test_gastronomie_does_not_default_to_beratung(self):
        """Gastronomie must NEVER default to 'beratung'."""
        engine_key = map_frontend_branch_to_engine("gastronomie")
        assert engine_key != "beratung", (
            "CRITICAL: 'gastronomie' defaulted to 'beratung'! "
            "This is the bug FIX-BRANCH-13 was created to fix."
        )


# =============================================================================
# TEST: Company Size Normalizer (En-Dash Robust)
# =============================================================================

class TestCompanySizeNormalizer:
    """Tests for the company size normalizer."""

    def test_en_dash_equals_hyphen_2_10(self):
        """'2–10' (En-Dash) should equal '2-10' (hyphen)."""
        result_en = normalize_company_size("2–10")  # En-Dash U+2013
        result_hy = normalize_company_size("2-10")  # Regular hyphen

        assert result_en["bucket"] == result_hy["bucket"], (
            f"En-Dash and hyphen should produce same bucket: "
            f"'{result_en['bucket']}' vs '{result_hy['bucket']}'"
        )
        assert result_en["min"] == result_hy["min"]
        assert result_en["max"] == result_hy["max"]

    def test_en_dash_equals_hyphen_11_100(self):
        """'11–100' (En-Dash) should equal '11-100' (hyphen)."""
        result_en = normalize_company_size("11–100")  # En-Dash U+2013
        result_hy = normalize_company_size("11-100")  # Regular hyphen

        assert result_en["bucket"] == result_hy["bucket"]
        assert result_en["min"] == result_hy["min"]
        assert result_en["max"] == result_hy["max"]

    def test_solo_size_value(self):
        """'1' should map to 'solo' bucket."""
        result = normalize_company_size("1")
        assert result["bucket"] == "solo"
        assert result["min"] == 1
        assert result["max"] == 1

    def test_small_team_size_value(self):
        """'2–10' should map to 'small_team' bucket."""
        result = normalize_company_size("2–10")
        assert result["bucket"] == "small_team"
        assert result["min"] == 2
        assert result["max"] == 10

    def test_kmu_size_value(self):
        """'11–100' should map to 'kmu' bucket."""
        result = normalize_company_size("11–100")
        assert result["bucket"] == "kmu"
        assert result["min"] == 11
        assert result["max"] == 100

    def test_legacy_bucket_names(self):
        """Legacy bucket names should be recognized."""
        assert get_company_size_bucket("solo") == "solo"
        assert get_company_size_bucket("team") == "small_team"
        assert get_company_size_bucket("kmu") == "kmu"

    def test_empty_value_defaults_to_solo(self):
        """Empty value should default to 'solo'."""
        result = normalize_company_size("")
        assert result["bucket"] == "solo"


# =============================================================================
# TEST: Legacy Branch Values (Backwards Compatibility)
# =============================================================================

class TestLegacyBranchValues:
    """Tests for backwards compatibility with legacy branch values."""

    LEGACY_TO_ENGINE = {
        "marketing_werbung": "marketing",
        "beratung_dienstleistungen": "beratung",
        "it_software": "it",
        "finanzen_versicherungen": "finanzen",
        "handel_ecommerce": "handel",
        "gesundheit_pflege": "gesundheit",
        "bauwesen_architektur": "bauwesen_architektur",
        "medien_kreativwirtschaft": "medien",
        "industrie_produktion": "industrie",
        "transport_logistik": "transport_logistik",
    }

    def test_legacy_values_still_work(self):
        """Legacy underscore-format values should still map correctly."""
        for legacy_value, expected_engine in self.LEGACY_TO_ENGINE.items():
            engine_key = map_frontend_branch_to_engine(legacy_value)
            assert engine_key == expected_engine, (
                f"Legacy value '{legacy_value}' should map to '{expected_engine}', "
                f"got '{engine_key}'"
            )


# =============================================================================
# TEST: STRICT Mode Compatibility
# =============================================================================

class TestStrictModeCompatibility:
    """Tests to ensure STRICT mode won't have Unknown-Branch-Fallbacks."""

    def test_no_unknown_branch_for_canonical_values(self):
        """
        In STRICT mode, there should be no "Unknown branch ... defaulting to 'beratung'"
        for any of the 13 canonical values.
        """
        import logging

        # Capture log output
        log_capture = []
        handler = logging.Handler()
        handler.emit = lambda record: log_capture.append(record.getMessage())
        logging.getLogger("services.branch_mapping").addHandler(handler)

        canonical_13 = [
            "marketing", "beratung", "it", "finanzen", "handel", "bildung",
            "verwaltung", "gesundheit", "bau", "medien", "industrie",
            "logistik", "gastronomie",
        ]

        for branch in canonical_13:
            map_frontend_branch_to_engine(branch)

        # Check no "Unknown branch" warnings for canonical values
        unknown_warnings = [
            msg for msg in log_capture
            if "Unknown branch" in msg and any(b in msg for b in canonical_13)
        ]
        assert len(unknown_warnings) == 0, (
            f"Found 'Unknown branch' warnings for canonical values: {unknown_warnings}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
