# -*- coding: utf-8 -*-
"""
FIX-KIS-1188-ITEM5: kontextloser „Förderprogramme · siehe Kapitel Fördermittel"
snippet on R1 S.11 (Starter-Kit Compact).

inject_starter_kit_into_sections collapses kit.funding to a single
StarterKitFunding(program_id="crossref_foerderprogramme",
                  name="→ siehe Kapitel Fördermittel", …)
when the main FOERDERPROGRAMME_HTML chapter already exists. Previously the
compact renderer just `, ".join(f.name)`-ed that, so the rendered output
read „Förderung: → siehe Kapitel Fördermittel" — a bare fragment without
the explanation.

The compact renderer now detects the crossref-only case and renders a
full-sentence cross-reference instead.
"""
from __future__ import annotations

from services.tools_starter_kits import (
    StarterKit,
    StarterKitTool,
    StarterKitFunding,
    StarterKitChecklist,
    generate_starter_kit_compact_html,
)


def _kit(funding):
    return StarterKit(
        kit_id="solo_starter",
        kit_name="Solo Starter",
        segment_label="Solo / Freelancer",
        description="",
        tools=[
            StarterKitTool(name="ChatGPT", category="LLM",
                           purpose="Schreiben", priority=1),
            StarterKitTool(name="DeepL", category="Übersetzung",
                           purpose="Übersetzen", priority=2),
            StarterKitTool(name="Make", category="Automation",
                           purpose="Automatisierung", priority=2),
        ],
        funding=funding,
        checklist=[
            StarterKitChecklist(step=1, title="A", description="x",
                                category="setup"),
        ],
        estimated_total_days=14,
        estimated_investment="2.000 €",
        potential_funding="",
        quick_win_count=2,
    )


CROSSREF = StarterKitFunding(
    program_id="crossref_foerderprogramme",
    name="→ siehe Kapitel Fördermittel",
    provider="",
    max_amount="",
    fit_reason="Detaillierte Förderprogramme finden Sie im Kapitel Fördermittel.",
    application_complexity="low",
)


REAL_FUNDING = StarterKitFunding(
    program_id="bafa_unternehmensberatung",
    name="BAFA-Förderung Unternehmensberatung",
    provider="BAFA",
    max_amount="3.500 €",
    fit_reason="Passt für Solo-Selbstständige.",
    application_complexity="medium",
)


class TestCrossrefOnlyRendering:
    """When funding is reduced to the crossref placeholder, the compact
    block must NOT show the bare fragment „→ siehe Kapitel Fördermittel"."""

    def test_full_sentence_replaces_truncated_name(self):
        html = generate_starter_kit_compact_html(_kit([CROSSREF]))
        # Bare fragment is gone:
        assert "Förderung: → siehe Kapitel Fördermittel" not in html
        # Full sentence is present:
        assert "Detaillierte Förderprogramme" in html
        assert "Fördermittel" in html

    def test_misleading_one_foerderprogramme_count_dropped(self):
        """„1 Förderprogramme" reads as a wrong count when the entry is a
        cross-reference, not a programme. The count line must omit it."""
        html = generate_starter_kit_compact_html(_kit([CROSSREF]))
        assert "1 Förderprogramme" not in html
        # Tool count is still rendered separately:
        assert "3 Tools" in html

    def test_crossref_does_not_leak_arrow_name(self):
        html = generate_starter_kit_compact_html(_kit([CROSSREF]))
        # The truncated arrow-form must not be the only funding text:
        assert "Förderung: →" not in html


class TestRealFundingStillRendered:
    """The crossref special-case must not affect normal kits."""

    def test_real_funding_name_listed(self):
        html = generate_starter_kit_compact_html(_kit([REAL_FUNDING]))
        assert "BAFA-Förderung Unternehmensberatung" in html

    def test_real_funding_count_shown(self):
        html = generate_starter_kit_compact_html(_kit([REAL_FUNDING]))
        assert "1 Förderprogramme" in html

    def test_mixed_funding_treated_as_real(self):
        """If even one programme is real, render normally."""
        html = generate_starter_kit_compact_html(_kit([CROSSREF, REAL_FUNDING]))
        assert "BAFA-Förderung Unternehmensberatung" in html
        assert "Detaillierte Förderprogramme finden Sie" not in html
