# -*- coding: utf-8 -*-
"""KIS-1319 — Testlauf KIS1288 (06.09.2026, Build 1336, Motion-Profil nach
KIS-1317). Kennzahlen unverändert, kein Rückfall, Kernbotschaft aus den
Scores, Entscheidungsblock mit drei Punkten. Restbefunde im Code:

- R1 S. 20: „Für LLM-Anbieter existieren keine gleichwertigen EU-Alternativen"
  — fester Text, während die Liste Aleph Alpha und Mistral führt.
- Strategie S. 15/16: „20.000 € im Monat, bei 1–2 Jahreslizenzen" bei
  „Jahreslizenz ab 50.000 €" — Komma vor „bei", Tabellenzelle ohne „Jahres".
- Strategie S. 19: Wächter-Fehlalarm „Adobe Premiere Pro Umgebung … und
  EU-gehostet ist" — das „es" ist Amberscript.
- Strategie S. 7: „Quellen: KI-Readiness-Analyse 2024".
- Strategie S. 15: „Adobe Premiere Pro (Neural Engine)"; S. 23: „als
  alleinige Entscheiderin".
- R1 S. 27/28: „50 Stunden/Monater Einsparung", „ein Motion Designer nutzen
  Runway", „jedes Teammitglied eigene Standards setzen".
- KPA S. 2: „Anforderungen des EU AI Act werden in den nächsten Monaten
  wirksam" — der gc-Prompt hatte keine Zeitlage.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))


def _cr():
    import compare_reports
    return compare_reports


class TestVendorHinweis:
    def test_hinweis_nennt_eu_anbieter(self):
        from services.vendor_audit_engine import _RECOMMENDATION_HINT_DE, _RECOMMENDATION_HINT_EN
        assert "keine gleichwertigen" not in _RECOMMENDATION_HINT_DE
        assert "Aleph Alpha" in _RECOMMENDATION_HINT_DE and "Mistral" in _RECOMMENDATION_HINT_DE
        assert "no equivalent" not in _RECOMMENDATION_HINT_EN and "Aleph Alpha" in _RECOMMENDATION_HINT_EN

    def test_waechter_schweigt_beim_neuen_hinweis(self):
        from services.vendor_audit_engine import _RECOMMENDATION_HINT_DE, _RECOMMENDATION_HINT_EN
        cr = _cr()
        assert cr._us_werkzeug_als_eu("Hochrisiko-Anbieter prüfen: Runway, ChatGPT (OpenAI). " + _RECOMMENDATION_HINT_DE) is None
        assert cr._us_werkzeug_als_eu(_RECOMMENDATION_HINT_EN) is None

    def test_rote_anbieter_bekommen_den_hinweis(self):
        import inspect
        from services import vendor_audit_engine as v
        src = inspect.getsource(v)
        assert "gleichwertigen EU-Alternativen —" not in src  # das alte Literal
        assert src.count("_RECOMMENDATION_HINT_DE}") == 1


class TestJahreslizenz:
    HTML = (
        '<p><strong>Preismodell:</strong> Jahreslizenz ab 50.000 € mit individuellem Setup. '
        'Alternativ monatliche Lizenz ab 4.500 €.</p>'
        '<p><strong>Umsatzprojektion:</strong> Voraussichtlich 20.000 € im Monat, bei 1–2 Jahreslizenzen, '
        'die das Komplettpaket nutzen.</p>'
        '<table><tr><td>Jahreslizenz ab 50.000 € / Monatlich ab 4.500 €</td><td>20.000 € bei 1–2 Lizenzen</td></tr></table>'
    )

    def test_sanitizer_rechnet_komma_und_tabelle(self):
        from services.strategy_sanitizer import umsatz_jahresabo_korrigieren
        out, n = umsatz_jahresabo_korrigieren(self.HTML)
        assert n == 2
        assert "8.300 € im Monat, bei 1–2 Jahreslizenzen" in out
        assert "8.300 € bei 1–2 Lizenzen" in out
        assert "20.000" not in out

    def test_waechter_kennt_komma(self):
        cr = _cr()
        t = ("Preismodell: Jahreslizenz ab 50.000 € mit individuellem Setup.\n"
             "Umsatzprojektion: Voraussichtlich 20.000 € im Monat, bei 1–2 Jahreslizenzen, die das Komplettpaket nutzen.")
        assert cr._umsatz_jahresabo_rechnung(t)
        assert cr._umsatz_jahresabo_rechnung(t.replace("20.000", "8.300")) is None


class TestWaechterAdobe:
    def test_amberscript_als_subjekt_ist_kein_befund(self):
        cr = _cr()
        assert cr._us_werkzeug_als_eu(
            "Starten Sie mit Amberscript als Quick Win, da es Ihre Adobe Premiere Pro Umgebung "
            "direkt ergänzt und EU-gehostet ist."
        ) is None

    def test_premiere_als_subjekt_bleibt_befund(self):
        cr = _cr()
        assert cr._us_werkzeug_als_eu(
            "Amberscript ist EU-gehostet. Beginnen Sie mit Adobe Premiere Pro (Speech to Text), "
            "da es Ihre Schnittsoftware ergänzt und über eine EU-konforme Hosting-Option verfügt."
        )


class TestQuellenjahr:
    def test_eigener_report_traegt_reportjahr(self):
        from services.strategy_sanitizer import quellen_stand_jahr_korrigieren
        out, n = quellen_stand_jahr_korrigieren(
            '<p><strong>Quellen:</strong> KI-Readiness-Analyse 2024, EU AI Act, DSGVO.</p>', 2026)
        assert n == 1 and "KI-Readiness-Analyse 2026" in out

    def test_fremde_quelle_bleibt(self):
        from services.strategy_sanitizer import quellen_stand_jahr_korrigieren
        html = '<p><strong>Quellen:</strong> Metricool 2024, Bitkom 2025.</p>'
        assert quellen_stand_jahr_korrigieren(html, 2026) == (html, 0)

    def test_waechter_meldet(self):
        cr = _cr()
        assert cr._veraltete_jahreszahl("Report-ID: KIS-1288 • 06.09.2026\nQuellen: KI-Readiness-Analyse 2024, EU AI Act") == "KI-Readiness-Analyse 2024"
        assert cr._veraltete_jahreszahl("Report-ID: KIS-1288 • 06.09.2026\nQuellen: KI-Readiness Report 2026") is None


class TestKleinigkeiten:
    def test_fremde_engine(self):
        from services.strategy_sanitizer import fremde_engine_entfernen
        out, n = fremde_engine_entfernen(
            "Adobe Premiere Pro (Neural Engine) für Schnitt und DaVinci Resolve (Neural Engine) für Grading.")
        assert n == 1
        assert "Adobe Premiere Pro für Schnitt" in out and "DaVinci Resolve (Neural Engine)" in out

    def test_waechter_kennt_fremde_engine(self):
        cr = _cr()
        pruefung = dict((p[0], p[2]) for p in cr.PRUEFUNGEN)["erfundenes_werkzeug"]
        assert pruefung("Adobe Premiere Pro (Neural Engine) für Schnittautomatisierung")
        assert pruefung("DaVinci Resolve (Neural Engine) für Grading") is None

    def test_entscheiderin_neutral(self):
        from services.strategy_sanitizer import entscheider_neutral
        out, n = entscheider_neutral("das Team, das Sie als alleinige Entscheiderin steuern.")
        assert n == 1 and "als alleinige Entscheidungsinstanz steuern" in out
        out, n = entscheider_neutral("the team you run as the sole decision-maker.")
        assert n == 1 and "sole decision-making authority" in out

    def test_sanitizer_laeuft_beide_paesse(self):
        from services.strategy_sanitizer import sanitize_strategy_sections
        secs = {"S3B": "<p>" + "Kombination aus Adobe Premiere Pro (Neural Engine) für Schnitt. " * 6 + "</p>",
                "S6": "<p>" + "Das Team, das Sie als alleinige Entscheiderin steuern. " * 6 + "</p>"}
        out = sanitize_strategy_sections(secs)
        assert "(Neural Engine)" not in out["S3B"]
        assert "Entscheiderin" not in out["S6"] and "Entscheidungsinstanz" in out["S6"]

    @pytest.mark.parametrize("vorher,nachher", [
        ("ein Motion Designer nutzen Runway, das Social-Team schreibt Captions",
         "ein Motion Designer nutzt Runway, das Social-Team schreibt Captions"),
        ("statt dass jedes Teammitglied eigene Standards setzen.",
         "statt dass jedes Teammitglied eigene Standards setzt."),
        ("die 50 Stunden/Monater Einsparung aus den Quick-Wins",
         "die Einsparung von 50 Stunden/Monat aus den Quick-Wins"),
    ])
    def test_grammatik(self, vorher, nachher):
        from services.content_quality_enforcer import apply_grammar_fixes
        out, _ = apply_grammar_fixes("<p>" + vorher + "</p>")
        assert nachher in out

    def test_grammatik_laesst_plural_und_sie(self):
        from services.content_quality_enforcer import apply_grammar_fixes
        html = "<p>Sie nutzen 50 Stunden/Monat. Die Designer nutzen Runway. Alle Teammitglieder setzen Standards.</p>"
        assert apply_grammar_fixes(html)[0] == html


class TestKpaStichtag:
    def test_kontext_traegt_zeitlage(self):
        from services.gamechanger_deep_dive import build_gamechanger_context
        ctx = build_gamechanger_context({"LANG": "de"}, {"lang": "de", "branche": "medien"})
        assert ctx["AI_ACT_STICHTAG"] == "gelten seit dem 2. August 2026"
        ctx_en = build_gamechanger_context({"LANG": "en"}, {"lang": "en", "branche": "medien"})
        assert ctx_en["AI_ACT_STICHTAG"].startswith("have applied since")

    @pytest.mark.parametrize("pfad", [
        "prompts/de/gc_strategic_analysis.md", "prompts/de/gc_risk_assessment.md",
        "prompts/en/gc_strategic_analysis.md", "prompts/en/gc_risk_assessment.md",
    ])
    def test_prompt_nennt_platzhalter(self, pfad):
        text = (ROOT / pfad).read_text(encoding="utf-8")
        assert "{{AI_ACT_STICHTAG}}" in text

    def test_render_setzt_satz_ein(self):
        import inspect
        from services import gamechanger_deep_dive as g
        assert "'AI_ACT_STICHTAG': context.get('AI_ACT_STICHTAG', '')" in inspect.getsource(g)
