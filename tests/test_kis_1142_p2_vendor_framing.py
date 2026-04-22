# -*- coding: utf-8 -*-
"""
KIS-1142 Punkt 2 — Vendor-Audit-Framing-Inkonsistenz.

R1 war imperativ, Strategy S8 bereits relativierend. Ziel: R1 an Strategy
angleichen — konstatieren statt befehlen, plus der Kontextualisierungs-
Satz aus Strategy S8 (dass der Audit-Status die Tools bewertet, nicht
das Unternehmen).

Regression cover:

  1. Summary enthält **nicht** mehr "Sofortiger Handlungsbedarf" /
     "Immediate action required" — stattdessen "Prüfbedarf" / "Review
     required".
  2. Summary schließt mit einem Kontextualisierungs-Satz, der klarmacht
     dass der Status die Tools bewertet, nicht das Unternehmen.
  3. Recommendations schreiben "prüfen und ggf. nachholen" statt
     "abschliessen" und "einordnen" statt "sicherstellen".
  4. Der "Keine kritischen Befunde"-Pfad bleibt intakt (kein Regress
     auf der grünen Seite).
"""

from __future__ import annotations

import pytest

from services.vendor_audit_engine import (
    VendorAuditEntry,
    _generate_summary,
    _generate_recommendations,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_entry(
    name: str,
    overall: str = "green",
    jurisdiction: str = "EU",
    has_dpa: bool = True,
    data_location: str = "EU-only",
    security_posture: str = "strong",
    ai_act_relevance: str = "low",
    has_certifications: bool = True,
) -> VendorAuditEntry:
    # ``is_eu_compliant`` and ``has_certifications`` are computed properties,
    # not dataclass fields — seed the underlying attrs (certifications list,
    # jurisdiction + has_dpa) so the properties evaluate as intended.
    certifications = ["ISO 27001"] if has_certifications else []
    return VendorAuditEntry(
        name=name,
        category="LLM",
        overall_category=overall,
        jurisdiction=jurisdiction,
        has_dpa=has_dpa,
        data_location=data_location,
        security_posture=security_posture,
        ai_act_relevance=ai_act_relevance,
        certifications=certifications,
    )


# ---------------------------------------------------------------------------
# H1 — Summary tonality
# ---------------------------------------------------------------------------

class TestSummaryTonality:
    def test_de_red_vendor_says_pruefbedarf_not_handlungsbedarf(self):
        entries = [_make_entry("X", overall="red", jurisdiction="US", has_dpa=False)]
        summary = _generate_summary(entries, lang="de")
        assert "Sofortiger Handlungsbedarf" not in summary, (
            "Hartes 'Sofortiger Handlungsbedarf' muss durch 'Prüfbedarf' "
            "ersetzt sein (konstatieren statt befehlen)."
        )
        assert "Prüfbedarf" in summary

    def test_en_red_vendor_says_review_required_not_immediate_action(self):
        entries = [_make_entry("X", overall="red", jurisdiction="US", has_dpa=False)]
        summary = _generate_summary(entries, lang="en")
        assert "Immediate action required" not in summary
        assert "Review required" in summary

    def test_de_green_only_keeps_keine_kritischen_befunde(self):
        # Guard the green-path — softening must not erase the no-findings
        # message.
        entries = [_make_entry("X", overall="green")]
        summary = _generate_summary(entries, lang="de")
        assert "Keine kritischen Befunde" in summary

    def test_en_green_only_keeps_no_critical_findings(self):
        entries = [_make_entry("X", overall="green")]
        summary = _generate_summary(entries, lang="en")
        assert "No critical findings" in summary


# ---------------------------------------------------------------------------
# H2 — Contextualising sentence from Strategy S8
# ---------------------------------------------------------------------------

class TestSummaryContextualisation:
    def test_de_summary_ends_with_tool_vs_company_clarification(self):
        entries = [_make_entry("X", overall="red", jurisdiction="US", has_dpa=False)]
        summary = _generate_summary(entries, lang="de")
        # Exakte Formulierung aus strategy_prompts.py L105 (gekürzt).
        assert "bezieht sich auf den Konformitätsstatus der" in summary
        assert "nicht auf den Gesamt-KI-Readiness-Status" in summary
        assert "Ihres Unternehmens" in summary

    def test_en_summary_ends_with_tool_vs_company_clarification(self):
        entries = [_make_entry("X", overall="red", jurisdiction="US", has_dpa=False)]
        summary = _generate_summary(entries, lang="en")
        assert "compliance posture of the listed" in summary
        assert "not the overall AI-readiness status" in summary

    def test_clarification_present_on_green_path_too(self):
        # Context clarification is about what the audit *measures*, so it
        # must be consistent regardless of red count.
        entries = [_make_entry("X", overall="green")]
        de_summary = _generate_summary(entries, lang="de")
        en_summary = _generate_summary(entries, lang="en")
        assert "nicht auf den Gesamt-KI-Readiness-Status" in de_summary
        assert "not the overall AI-readiness status" in en_summary


# ---------------------------------------------------------------------------
# H3 — Recommendations: "abschliessen" → "prüfen und ggf. nachholen"
# ---------------------------------------------------------------------------

class TestRecommendationsTonality:
    def test_us_no_dpa_no_longer_says_abschliessen(self):
        entries = [
            _make_entry("USTool", jurisdiction="US", has_dpa=False,
                        overall="yellow"),
        ]
        recs = _generate_recommendations(entries, size_label="team")
        us_recs = [r for r in recs if "USTool" in r]
        assert us_recs, "Expected a DPA recommendation for US-no-DPA vendor"
        for r in us_recs:
            assert "abschliessen" not in r, (
                f"'abschliessen' lingers in: {r!r}"
            )
            assert "prüfen und ggf. nachholen" in r

    def test_red_vendor_recommendation_no_sicherstellen(self):
        # Keep the entry DPA-complete so the US-no-DPA recommendation path
        # doesn't fire — we want to isolate the "Hochrisiko-Anbieter" path.
        entries = [_make_entry("Red1", overall="red", jurisdiction="EU",
                               has_dpa=True)]
        recs = _generate_recommendations(entries, size_label="team")
        red_recs = [r for r in recs if "Hochrisiko-Anbieter" in r]
        assert red_recs, f"No Hochrisiko recommendation in {recs!r}"
        for r in red_recs:
            # "sicherstellen" was the hard imperative. "einordnen" is the
            # softer constatative replacement.
            assert "sicherstellen" not in r, (
                f"'sicherstellen' lingers in: {r!r}"
            )
            assert "einordnen" in r


# ---------------------------------------------------------------------------
# H4 — No regression on empty inputs
# ---------------------------------------------------------------------------

class TestEmptyInput:
    def test_empty_entries_returns_stable_message_de(self):
        assert _generate_summary([], lang="de") == (
            "Keine Anbieter zur Prüfung vorhanden."
        )

    def test_empty_entries_returns_stable_message_en(self):
        assert _generate_summary([], lang="en") == (
            "No vendors to audit."
        )
