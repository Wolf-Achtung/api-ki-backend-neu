# -*- coding: utf-8 -*-
"""
KIS-1142 Punkt 4 — KPA-Prompt auf einfachere Sprache tunen (Variante A).

Ziel: der KPA-Output (gc_strategic_analysis) liest sich für einen
KMU-Geschäftsführer ohne Beratungs-Hintergrund. Der Prompt bekommt
einen neuen SPRACHREGELN-Block mit fünf harten Regeln + entschlackten
Pflichtstruktur-Headern.

Regression cover (source-level):

  1. Die fünf Richtlinien aus Wolf's Batch-Go sind im Prompt verankert:
     Satz-Länge, Konjunktiv-Limit, Fachbegriff-Erklärungen, Beispiele,
     Jargon-Verbotsliste.
  2. Compliance-Begriffe (DSGVO, AVV, EU AI Act) werden **nicht** als
     erklärungsbedürftig markiert — die bleiben unverändert (Wolf).
  3. Die Pflichtstruktur-Header wurden von Beraterton (Strategischer
     Wendepunkt, Paradigmenwechsel) auf Alltagssprache umgestellt.
  4. Der TONALITÄT-Block und die BEGRIFFSKONSISTENZ-Regeln bleiben
     intakt — die Sprach-Richtlinien ergänzen, ersetzen nicht.
"""

from __future__ import annotations

from pathlib import Path

import pytest


PROMPT_PATH = Path("prompts/de/gc_strategic_analysis.md")


@pytest.fixture(scope="module")
def prompt_src() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# H1 — New SPRACHREGELN block anchors the five rules
# ---------------------------------------------------------------------------

class TestSprachregelnBlockPresent:
    def test_section_header_exists(self, prompt_src):
        assert "SPRACHREGELN FÜR VERSTÄNDLICHKEIT" in prompt_src, (
            "Missing the new SPRACHREGELN block — KIS-1142 P4 is the "
            "entire point of this file change."
        )

    def test_max_sentence_length_rule(self, prompt_src):
        assert "20-25 Wörter pro Satz" in prompt_src

    def test_konjunktiv_rule(self, prompt_src):
        assert "Konjunktive nur bei echten Prognosen" in prompt_src

    def test_fachbegriff_explanation_rule(self, prompt_src):
        # Rule 3 header + at least one worked example from Wolf's list.
        assert "Fachbegriffe bei Erstnennung" in prompt_src
        # The three examples Wolf explicitly named must appear so a future
        # edit doesn't drop them.
        assert "PII" in prompt_src
        assert "Vier-Augen-Prinzip" in prompt_src
        assert "Red-Flag-Liste" in prompt_src

    def test_example_over_abstraction_rule(self, prompt_src):
        assert "Beispiele statt Abstraktion" in prompt_src

    def test_jargon_blacklist_present(self, prompt_src):
        # Spot-check two terms from Wolf's verbots-liste.
        assert "fundamental" in prompt_src
        assert "Paradigmenwechsel" in prompt_src  # as a banned term
        assert "Disruption" in prompt_src


# ---------------------------------------------------------------------------
# H2 — Compliance terms stay exempt (Wolf's explicit exception)
# ---------------------------------------------------------------------------

class TestComplianceTermsExempt:
    def test_dsgvo_not_listed_as_needing_parenthesis(self, prompt_src):
        # DSGVO must be called out as an etabliert/no-parenthesis term
        # in the same rule block — otherwise a future edit might wrap it
        # in a parenthesis and contradict the BEGRIFFSKONSISTENZ guard
        # ("DSGVO = nie ausschreiben").
        assert "Keine Klammer nötig bei etablierten Begriffen: DSGVO" in prompt_src

    def test_compliance_terms_in_exempt_list(self, prompt_src):
        exempt_section = prompt_src.split(
            "Keine Klammer nötig bei etablierten Begriffen:"
        )[-1].split("**4.")[0]
        for term in ("DSGVO", "CRM", "ERP", "ISO 27001", "KPI", "ROI"):
            assert term in exempt_section, (
                f"{term!r} must remain in the exempt list"
            )

    def test_existing_begriffskonsistenz_block_untouched(self, prompt_src):
        # Guard the existing BEGRIFFSKONSISTENZ section — we only add rules,
        # we do not rewrite the established terminology contract.
        assert "BEGRIFFSKONSISTENZ (VERBINDLICH — OPT-A7)" in prompt_src
        assert '„EU AI Act" = immer, bei erster Nennung „EU AI Act (KI-Verordnung der EU)"' in prompt_src
        assert '„AVV" = bei erster Nennung „AV-Vertrag (AVV)"' in prompt_src


# ---------------------------------------------------------------------------
# H3 — Pflichtstruktur headers moved off consultant-speak
# ---------------------------------------------------------------------------

class TestPflichtstrukturHeadersSimplified:
    @pytest.mark.parametrize("old_header", [
        "Strategischer Wendepunkt",
        "Die neue Logik",
        "Konsequenz bei Nicht-Handeln",
    ])
    def test_old_header_gone(self, prompt_src, old_header):
        # Headers on the list lines (1./2./4.) — these bubble into the
        # output's <strong> headers. Keep "Warum jetzt handeln" and
        # "Erster konkreter Schritt" because they are already plain.
        assert f"**{old_header}**" not in prompt_src, (
            f"Old jargon header {old_header!r} still present — should be "
            "replaced with an alltagssprache equivalent."
        )

    @pytest.mark.parametrize("new_header", [
        "Was sich am Markt verändert",
        "Was das für Ihr Geschäft heißt",
        "Was passiert, wenn nichts passiert",
    ])
    def test_new_header_present(self, prompt_src, new_header):
        assert f"**{new_header}**" in prompt_src, (
            f"Expected plain-language header {new_header!r} in the "
            "PFLICHTSTRUKTUR block."
        )

    def test_paradigmenwechsel_gone_from_structure_description(self, prompt_src):
        # The old "Welcher Paradigmenwechsel stattfindet" bullet directly
        # fed the LLM with a jargon seed. It's gone now; the banned-terms
        # reference in the SPRACHREGELN block is the only remaining
        # occurrence.
        paradigmenwechsel_count = prompt_src.count("Paradigmenwechsel")
        assert paradigmenwechsel_count == 1, (
            f"'Paradigmenwechsel' appears {paradigmenwechsel_count}x — "
            "should be exactly once (inside the banned-terms list)."
        )

    def test_fundamental_gone_from_structure_description(self, prompt_src):
        # Same logic for "fundamental" — the old Pflichtstruktur told the
        # LLM to describe "fundamentale" changes, which primed jargon.
        # After the rewrite, it should only appear once (banned-terms).
        fundamental_count = prompt_src.count("fundamental")
        assert fundamental_count == 1, (
            f"'fundamental' appears {fundamental_count}x — expected exactly "
            "once (inside the banned-terms list)."
        )


# ---------------------------------------------------------------------------
# H4 — Tonalität block untouched + HTML format contract intact
# ---------------------------------------------------------------------------

class TestAdjacentBlocksUntouched:
    def test_tonalitaet_block_intact(self, prompt_src):
        assert "## TONALITÄT" in prompt_src
        assert "Analytisch, sachlich, strategisch" in prompt_src
        assert 'Formelle Anrede "Sie"' in prompt_src

    def test_html_format_contract_intact(self, prompt_src):
        assert "`<p>`, `<ul>`, `<li>`, `<strong>`, `<em>`" in prompt_src
        assert "KEIN `<html>`, `<head>`, `<body>`" in prompt_src

    def test_persona_anpassung_intact(self, prompt_src):
        assert "## PERSONA-ANPASSUNG" in prompt_src
        assert '{% if COMPANY_SIZE == "solo" %}' in prompt_src
        assert '{% elif COMPANY_SIZE == "team" %}' in prompt_src

    def test_length_limit_still_500_words(self, prompt_src):
        assert "Maximal 500 Wörter / 4.500 Zeichen HTML gesamt" in prompt_src
