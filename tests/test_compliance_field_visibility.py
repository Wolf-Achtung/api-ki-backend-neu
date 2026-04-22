# -*- coding: utf-8 -*-
"""
Tests for Section 6 compliance field visibility (KIS-1153).

Background: Pre-fix, technische_massnahmen / folgenabschaetzung / meldewege /
loeschregeln were all hidden for non-regulated branches (show_if: gesundheit,
finanzen, verwaltung). That starved the security scorer for the vast majority
of users and produced the 40/100 Solo Beratung score seen in KIS-1153.

Post-fix: technische_massnahmen / meldewege / loeschregeln (Art. 32 / 33 / 17
DSGVO) are visible for all branches. folgenabschaetzung (Art. 35, reserved for
Hoch-Risiko-Verarbeitungen) remains regulated-only.
"""

import pytest

from services.chat_normalizer import is_field_visible, CONDITIONALS


COMPLIANCE_ALL_BRANCHES = ["technische_massnahmen", "meldewege", "loeschregeln"]
COMPLIANCE_REGULATED_ONLY = ["folgenabschaetzung", "regulierte_branche"]

NON_REGULATED = [
    "beratung", "marketing", "it", "handel", "bildung", "bau",
    "medien", "industrie", "logistik", "gastronomie",
]
REGULATED = ["gesundheit", "finanzen", "verwaltung"]


class TestNonRegulatedBranchesSeeCoreCompliance:
    """Core DSGVO compliance fields must be visible for every branche."""

    @pytest.mark.parametrize("field", COMPLIANCE_ALL_BRANCHES)
    @pytest.mark.parametrize("branche", NON_REGULATED)
    def test_field_visible_in_non_regulated_branche(self, field, branche):
        assert is_field_visible(field, {"branche": branche}) is True, (
            f"{field} must be visible for branche={branche} (KIS-1153)"
        )

    @pytest.mark.parametrize("field", COMPLIANCE_ALL_BRANCHES)
    def test_field_visible_without_branche(self, field):
        # Before the branche is known, compliance fields should not be hidden
        assert is_field_visible(field, {}) is True


class TestFolgenabschaetzungStaysRegulated:
    """DSFA (Art. 35) is only relevant for Hoch-Risiko-Verarbeitungen."""

    @pytest.mark.parametrize("branche", NON_REGULATED)
    def test_dsfa_hidden_for_non_regulated(self, branche):
        assert is_field_visible("folgenabschaetzung", {"branche": branche}) is False

    @pytest.mark.parametrize("branche", REGULATED)
    def test_dsfa_visible_for_regulated(self, branche):
        assert is_field_visible("folgenabschaetzung", {"branche": branche}) is True


class TestConditionalsTable:
    """Guard the CONDITIONALS dict shape so future edits don't silently re-gate fields."""

    @pytest.mark.parametrize("field", COMPLIANCE_ALL_BRANCHES)
    def test_field_has_no_conditional(self, field):
        assert field not in CONDITIONALS, (
            f"{field} must not be conditionally hidden — security scoring depends on it"
        )

    def test_folgenabschaetzung_still_gated(self):
        assert "folgenabschaetzung" in CONDITIONALS
        assert CONDITIONALS["folgenabschaetzung"]["show_if"]["branche"] == [
            "gesundheit", "finanzen", "verwaltung",
        ]
