# -*- coding: utf-8 -*-
"""KIS-1306 — Befunde aus Testlauf KIS1278 (05.09.2026, Build 1822, nach KIS-1305).

R1: „Format: Executive Summary (max." (S. 8) und „… prüfen und ggf." (Vendor-
Audit S. 21) — der Fragment-Stripper hielt Abkürzungspunkte für Satzenden;
„Ein verfrühter Einführung" (S. 29) nach Rollout→Einführung. Strategie: S1
nannte „Adobe Sensei" (S. 5), S7 die Medienboard-Frist „14.07.2026" und
„Einreichfrist im Juli 2026" (S. 27/29) — beide vor dem Reportdatum; die
Risikotabelle nannte Microsoft 365 Copilot „EU-konform" (S. 32). Der Wächter
„Satzabbruch vor Block" meldete einen umgebrochenen Satz („zwischen" /
„Monat 8 und 17.").
"""
from __future__ import annotations

import importlib.util
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _lade_compare_reports():
    spec = importlib.util.spec_from_file_location("compare_reports", ROOT / "scripts" / "compare_reports.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ---------------------------------------------------------------------------
# 1. Abkürzungspunkte sind keine Satzenden
# ---------------------------------------------------------------------------

class TestAbkuerzungImFragmentStripper:
    def test_max_bleibt(self):
        from services.content_quality_enforcer import strip_trailing_sentence_fragments
        html = "<p>Anforderungen: 1. Aktuelle Entwicklungen (letzte 12 Monate) 2. Relevanz bewerten. Format: Executive Summary (max. 500 Wörter) + Detail-Anhang</p>"
        out = strip_trailing_sentence_fragments({"SOFORT_START_HTML": html})["SOFORT_START_HTML"]
        assert "(max. 500 Wörter) + Detail-Anhang" in out

    def test_ggf_bleibt(self):
        from services.content_quality_enforcer import strip_trailing_sentence_fragments
        html = "<li>Die Prüfung ist Pflicht. DPA (Data Processing Agreement) mit US-Anbietern prüfen und ggf. nachholen: Perplexity AI</li>"
        out = strip_trailing_sentence_fragments({"VENDOR_AUDIT_HTML": html})["VENDOR_AUDIT_HTML"]
        assert "nachholen: Perplexity AI" in out

    def test_echtes_fragment_faellt_weiter(self):
        from services.content_quality_enforcer import strip_trailing_sentence_fragments
        html = "<p>Der erste Satz ist vollständig und lang genug für die Prüfung. Und dann noch</p>"
        out = strip_trailing_sentence_fragments({"X": html})["X"]
        assert "Und dann noch" not in out and out.endswith("Prüfung.</p>")


# ---------------------------------------------------------------------------
# 2. Genus nach Rollout → Einführung
# ---------------------------------------------------------------------------

class TestEinfuehrungGenus:
    @pytest.mark.parametrize("vorher,nachher", [
        ("Ein verfrühter Rollout auf zusätzliche Projekte", "Eine verfrühte Einführung auf zusätzliche Projekte"),
        ("als ein verzögerter Rollout.", "als eine verzögerte Einführung."),
        ("einen schnellen Rollout planen", "eine schnelle Einführung planen"),
        ("den Rollout stoppen", "die Einführung stoppen"),
        ("nach dem Rollout", "nach der Einführung"),
        ("kein überstürzter Rollout", "keine überstürzte Einführung"),
    ])
    def test_artikel_und_adjektiv(self, vorher, nachher):
        from services.content_quality_enforcer import apply_grammar_fixes, apply_solo_terms_final  # noqa: F401
        import re
        # Der Anglizismus-Pass ersetzt Rollout→Einführung; hier nur der Grammatik-Fixer.
        text = re.sub(r"\bRollout\b", "Einführung", vorher)
        out, _ = apply_grammar_fixes(text)
        assert out == nachher

    def test_korrekte_formen_unveraendert(self):
        from services.content_quality_enforcer import apply_grammar_fixes
        for t in ("eine schrittweise Einführung", "der Einführung folgt die Schulung", "bei der Einführung"):
            assert apply_grammar_fixes(t)[0] == t


# ---------------------------------------------------------------------------
# 3. Prompts: Werkzeugregel in S1/S3, Fristen in S7, Copilot in S8
# ---------------------------------------------------------------------------

class TestPrompts:
    def test_s1_s3_kennen_die_werkzeugliste(self):
        from prompts.strategy_prompts import STRATEGY_PROMPTS as DE
        from prompts.strategy_prompts_en import STRATEGY_PROMPTS_EN as EN
        for p in (DE, EN):
            for s in ("S1", "S3"):
                assert "{kuratierte_tools_namen}" in p[s]
                assert "Adobe Sensei" in p[s]

    def test_s7_fristregel(self):
        from prompts.strategy_prompts import STRATEGY_PROMPTS as DE
        from prompts.strategy_prompts_en import STRATEGY_PROMPTS_EN as EN
        assert "FRISTEN (KIS-1306)" in DE["S7"] and "Aktuell prüfen" in DE["S7"]
        assert "DEADLINES (KIS-1306)" in EN["S7"]

    def test_s8_copilot_nie_eu_konform(self):
        from prompts.strategy_prompts import STRATEGY_PROMPTS as DE
        from prompts.strategy_prompts_en import STRATEGY_PROMPTS_EN as EN
        assert "Microsoft 365 Copilot hat keine Zeile" in DE["S8"]
        assert "Microsoft 365 Copilot has no row" in EN["S8"]

    def test_advisor_erwaehnt_altes_budget_nicht(self):
        de = (ROOT / "prompts/de/advisor_note.md").read_text(encoding="utf-8")
        en = (ROOT / "prompts/en/advisor_note.md").read_text(encoding="utf-8")
        assert "erwähne sie gar nicht" in de
        assert "do not mention it at all" in en


# ---------------------------------------------------------------------------
# 4. Sanitizer: abgelaufene Fristen im Förderkapitel
# ---------------------------------------------------------------------------

class TestAbgelaufeneFristen:
    HEUTE = date(2026, 9, 5)

    def test_datum_vor_reportdatum_wird_ersetzt(self):
        from services.strategy_sanitizer import abgelaufene_fristen_korrigieren
        html = "<td>14.07.2026 (Einreichfrist Filmförderung 2026)</td><td>Bis 31.12.2026</td>"
        out, n = abgelaufene_fristen_korrigieren(html, self.HEUTE)
        assert n == 1
        assert "14.07.2026" not in out and "<td>Aktuell prüfen</td>" in out
        assert "Bis 31.12.2026" in out

    def test_monatsangabe_im_praxistipp(self):
        from services.strategy_sanitizer import abgelaufene_fristen_korrigieren
        html = "<p>Prüfen Sie die Antragsfristen frühzeitig, insbesondere beim Medienboard mit der Einreichfrist im Juli 2026.</p>"
        out, n = abgelaufene_fristen_korrigieren(html, self.HEUTE)
        assert n == 1 and "Juli 2026" not in out and "nächsten Einreichtermin" in out

    def test_zukunft_bleibt(self):
        from services.strategy_sanitizer import abgelaufene_fristen_korrigieren
        html = "<p>Einreichfrist im November 2026, Termin 15.10.2026.</p>"
        assert abgelaufene_fristen_korrigieren(html, self.HEUTE) == (html, 0)

    def test_nur_s7_im_gesamtlauf(self):
        from services.strategy_sanitizer import sanitize_strategy_sections
        alt = "<p>" + "Ein ordentlicher Satz ohne Auffälligkeit. " * 5 + "Termin am 14.07.2026 (Einreichfrist).</p>"
        out = sanitize_strategy_sections({"S7": alt, "S6": alt}, report_date=self.HEUTE)
        assert "14.07.2026" not in out["S7"]
        assert "14.07.2026" in out["S6"]


# ---------------------------------------------------------------------------
# 5. Wächter
# ---------------------------------------------------------------------------

class TestWaechter:
    @pytest.fixture(scope="class")
    def cr(self):
        return _lade_compare_reports()

    def test_satzabbruch_ignoriert_umgebrochenen_satz(self, cr):
        text = ("Die jährliche Zeitersparnis von 25 Stunden führt zu einer Einsparung von 28.500 €.\n"
                "Je nach Umsetzung ergeben sich drei ROI-Szenarien mit Break-Even-Zeiten zwischen\n"
                "Monat 8 und 17.\n")
        assert cr._satzabbruch_vor_block(text) is None

    def test_satzabbruch_erkennt_echten_block(self, cr):
        text = ("Die Prüfung der Rechtekette ist bei jedem Projekt Pflicht und dauert im Schnitt zwei Tage, weil\n"
                "das Team jedem Rechteinhaber vor der Auswertung überhaupt weiter Material zur Verfügung\n"
                "Q1 (Monate 1–3): Fundament\n")
        assert cr._satzabbruch_vor_block(text)

    def test_abgelaufene_frist(self, cr):
        text = ("Medienboard\n14.07.2026\n(Einreichfrist\nFilmförderung\n2026)\nHoch\n"
                "Seite 27 / 40\nReport-ID: KIS-1278 • 05.09.2026\n")
        assert cr._abgelaufene_frist(text)
        text2 = ("Einreichfrist im November 2026.\nBis 31.12.2026\n"
                 "Report-ID: KIS-1278 • 05.09.2026\n")
        assert cr._abgelaufene_frist(text2) is None
        text3 = "Tipp: Einreichfrist im Juli 2026.\nReport-ID: KIS-1278 • 05.09.2026\n"
        assert cr._abgelaufene_frist(text3)

    def test_registriert(self, cr):
        assert "abgelaufene_frist" in {p[0] for p in cr.PRUEFUNGEN}
