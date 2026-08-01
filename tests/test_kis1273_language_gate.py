# -*- coding: utf-8 -*-
"""KIS-1273 — Strukturelles EN-Sprachgate (EN-Testlauf 5, KIS-1254).

Lauf 5 zeigte: das LLM generiert einzelne Kapitel komplett deutsch
(Management Summary, Quick-Win-Karten, Förder-Narrative), nachgelagerte
Wort-Ersetzungen machen daraus Denglisch, und von Lauf zu Lauf flippen
andere Sektionen. Diese Tests decken (LLM gemockt, ohne Netzwerk) ab:

  G   gpt_analyze._en_language_sweep_sections — deutsche Blöcke erkannt und
      per Marker-Protokoll übersetzt, englische Blöcke byte-identisch,
      Marker-Mismatch/leere Antwort → Original (fail-open), DE-Lauf → kein
      einziger LLM-Call, Programmnamen-Schutz im Übersetzungs-Prompt,
      Call-Budget, Locale-Token-Nachsanitisierung (Kit-Seiten-Klasse
      "Vier-Augen-Prinzip", Lauf 5 S.14).
  F   funding_recommender/extra_sections — Programmnamen-Shield: BAFA-/
      Games-Namen bleiben durch Map und Tabelle intakt, Relevanz-/Fokus-
      Zellen werden vollständig übersetzt (Lauf-5-Befunde als Fixtures).
  R   risk_engine_v2 — "well manageable" → "manageable" (EN), DE unverändert.
  Q   quickwins_renderer — generisches "siehe X" → "see X" im Hinweis-Feld
      (EN-gated), DE byte-identisch.
"""

import os
import re

os.environ.setdefault("JWT_SECRET", "t")
os.environ.setdefault("DATABASE_URL", "sqlite:///t.db")

import pytest


# =============================================================================
# G — EN-Sprachgate auf Sektionsebene
# =============================================================================

_EN_PARA = "<p>This part is proper English prose and long enough to stay untouched.</p>"
_DE_PARA = ("<p>Das Projekt trägt sich auch ohne externe Zuschüsse und bleibt "
            "wirtschaftlich stabil über die kommenden Monate.</p>")
_DE_PARA_EN = ("<p>The project sustains itself without external grants and remains "
               "economically stable over the coming months.</p>")


class TestLanguageSweep:
    def _briefing(self, lang):
        return {"lang": lang, "branche": "medien"}

    def test_de_run_makes_no_llm_call_and_is_untouched(self, monkeypatch):
        import gpt_analyze as g
        calls = []

        def _boom(**k):
            calls.append(1)
            raise AssertionError("DE-Lauf darf keinen Sprachgate-LLM-Call machen")

        monkeypatch.setattr(g, "_call_llm_for_section", _boom)
        sections = {"MGMT_SUMMARY_HTML": _DE_PARA, "LANG": "de"}
        before = dict(sections)
        out = g._en_language_sweep_sections(sections, self._briefing("de"))
        assert out == before
        assert not calls

    def test_german_block_translated_english_untouched(self, monkeypatch):
        import gpt_analyze as g
        captured = {}

        def fake_llm(section_key, prompt, **kw):
            captured["section"] = section_key
            captured["prompt"] = prompt
            return f"<<<BLOCK 0>>>\n{_DE_PARA_EN}"

        monkeypatch.setattr(g, "_call_llm_for_section", fake_llm)
        sections = {"MGMT_SUMMARY_HTML": _EN_PARA + _DE_PARA}
        out = g._en_language_sweep_sections(sections, self._briefing("en"))
        html = out["MGMT_SUMMARY_HTML"]
        assert _EN_PARA in html                       # englischer Block byte-identisch
        assert _DE_PARA not in html                   # deutscher Block ersetzt
        assert "external grants" in html
        assert captured["section"] == "MGMT_SUMMARY_HTML"
        assert "<<<BLOCK 0>>>" in captured["prompt"]

    def test_multiple_german_blocks_one_llm_call(self, monkeypatch):
        import gpt_analyze as g
        calls = []

        def fake_llm(section_key, prompt, **kw):
            calls.append(prompt)
            return ("<<<BLOCK 0>>>\n<li>Set up the tool within one week.</li>\n"
                    "<<<BLOCK 1>>>\n<li>Document the results for the team.</li>")

        monkeypatch.setattr(g, "_call_llm_for_section", fake_llm)
        sections = {"QUICK_WINS_HTML": (
            "<ul>"
            "<li>Richten Sie das Werkzeug innerhalb einer Woche ein und prüfen Sie die Qualität.</li>"
            "<li>Dokumentieren Sie die Ergebnisse für Ihr Team und für die Planung.</li>"
            "</ul>"
        )}
        out = g._en_language_sweep_sections(sections, self._briefing("en"))
        assert len(calls) == 1                        # EIN Call für beide Blöcke
        assert "<<<BLOCK 0>>>" in calls[0] and "<<<BLOCK 1>>>" in calls[0]
        assert "Set up the tool" in out["QUICK_WINS_HTML"]
        assert "Richten Sie" not in out["QUICK_WINS_HTML"]

    def test_marker_mismatch_keeps_original(self, monkeypatch):
        # KIS-1275 (Aufgabe 7): fail-open-Sektionen behalten das Original,
        # tragen aber jetzt die Fail-open-Markierung am Sektionsanfang.
        import gpt_analyze as g
        monkeypatch.setattr(
            g, "_call_llm_for_section",
            lambda **k: "<<<BLOCK 7>>>\n<p>wrong marker index</p>")
        sections = {"X_HTML": _DE_PARA}
        out = g._en_language_sweep_sections(sections, self._briefing("en"))
        assert out["X_HTML"] == g._LANG_SWEEP_FAILOPEN_MARKER + _DE_PARA  # fail-open

    def test_empty_response_keeps_original(self, monkeypatch):
        import gpt_analyze as g
        monkeypatch.setattr(g, "_call_llm_for_section", lambda **k: "")
        sections = {"X_HTML": _DE_PARA}
        out = g._en_language_sweep_sections(sections, self._briefing("en"))
        assert out["X_HTML"] == g._LANG_SWEEP_FAILOPEN_MARKER + _DE_PARA

    def test_llm_exception_keeps_original(self, monkeypatch):
        import gpt_analyze as g
        monkeypatch.setattr(
            g, "_call_llm_for_section",
            lambda **k: (_ for _ in ()).throw(RuntimeError("timeout")))
        sections = {"X_HTML": _DE_PARA}
        out = g._en_language_sweep_sections(sections, self._briefing("en"))
        assert out["X_HTML"] == g._LANG_SWEEP_FAILOPEN_MARKER + _DE_PARA

    def test_funding_program_names_protected_in_prompt(self, monkeypatch):
        """Der Übersetzungs-Prompt weist deutsche Programm-EIGENNAMEN explizit
        als unantastbar aus (Lauf 5: zerlegte Namen in Empfehlungsbox)."""
        import gpt_analyze as g
        captured = {}

        def fake_llm(section_key, prompt, **kw):
            captured["prompt"] = prompt
            return None  # Original bleibt — hier zählt nur der Prompt-Inhalt

        monkeypatch.setattr(g, "_call_llm_for_section", fake_llm)
        de_funding = ("<p>Für Ihr Vorhaben ist die Games-Förderung des Bundes "
                      "eine geeignete Investition und ein guter Einstieg.</p>")
        sections = {"FOERDER_HTML": de_funding}
        g._en_language_sweep_sections(sections, self._briefing("en"))
        prompt = captured["prompt"]
        for name in ("BAFA – Förderung von Unternehmensberatungen für KMU",
                     "DFFF – Deutscher Filmförderfonds", "ProFIT", "ZIM", "KfW",
                     "Games-Förderung des Bundes", "Medienboard",
                     "Qualifizierungschancengesetz"):
            assert name in prompt, f"Programmname fehlt im Schutz-Hinweis: {name}"
        # KIS-1275: fail-open (fake_llm liefert None) → Original + Markierung
        assert de_funding in sections["FOERDER_HTML"]  # Name im Original unangetastet
        assert sections["FOERDER_HTML"].startswith("<!--ksj-lang-failopen-->")

    def test_short_german_fragment_not_translated(self, monkeypatch):
        """Blöcke unter 25 Zeichen sichtbarem Text lösen keinen Call aus."""
        import gpt_analyze as g
        calls = []

        def _boom(**k):
            calls.append(1)
            raise AssertionError("Kurzer Block darf keinen Call auslösen")

        monkeypatch.setattr(g, "_call_llm_for_section", _boom)
        sections = {"X_HTML": "<h3>Übersicht</h3>"}
        out = g._en_language_sweep_sections(sections, self._briefing("en"))
        assert out["X_HTML"] == "<h3>Übersicht</h3>"
        assert not calls

    def test_underscore_keys_skipped(self, monkeypatch):
        import gpt_analyze as g
        calls = []

        def _boom(**k):
            calls.append(1)
            raise AssertionError("_-Keys dürfen nicht übersetzt werden")

        monkeypatch.setattr(g, "_call_llm_for_section", _boom)
        sections = {"_QUICK_WINS_PRISTINE": _DE_PARA}
        out = g._en_language_sweep_sections(sections, self._briefing("en"))
        assert out["_QUICK_WINS_PRISTINE"] == _DE_PARA
        assert not calls

    def test_llm_budget_max_10_calls(self, monkeypatch):
        # KIS-1275 (6b): inhaltsgleiche Sektionen werden dedupliziert —
        # für den Budget-Test brauchen die 14 Sektionen daher DISTINKTE
        # deutsche Inhalte (vorher 14× identisch = wäre jetzt nur 1 Call).
        import gpt_analyze as g
        calls = []

        def fake_llm(section_key, prompt, **kw):
            calls.append(section_key)
            return None  # fail-open, zählt aber als Call

        monkeypatch.setattr(g, "_call_llm_for_section", fake_llm)
        # KIS-1279: Default-Budget ist jetzt 40 (ENV-konfigurierbar) — der
        # Test pinnt 10, er prüft den Deckel-Mechanismus, nicht den Default.
        monkeypatch.setenv("LANG_SWEEP_MAX_LLM_CALLS", "10")
        sections = {
            f"SEC_{i:02d}_HTML": _DE_PARA.replace("Monate", f"Monate (Variante {i})")
            for i in range(14)
        }
        g._en_language_sweep_sections(sections, self._briefing("en"))
        assert len(calls) == 10

    def test_locale_tokens_resanitized_after_late_heals(self, monkeypatch):
        """Kit-Seiten-Klasse (Lauf 5, S.14): 'Vier-Augen-Prinzip' in einem
        ansonsten englischen Block überlebt Restore-Pässe NACH dem
        Sanitizer-Final-Pass — das Sprachgate wendet die deterministische
        EN-Token-Map erneut an (kein LLM-Call nötig)."""
        import gpt_analyze as g
        calls = []

        def _boom(**k):
            calls.append(1)
            raise AssertionError("EN-Block mit DE-Token braucht keinen LLM-Call")

        monkeypatch.setattr(g, "_call_llm_for_section", _boom)
        sections = {"STARTER_KIT_HTML": (
            "<p>Step 2 (workflow): apply the Vier-Augen-Prinzip before "
            "publishing any AI output.</p>")}
        out = g._en_language_sweep_sections(sections, self._briefing("en"))
        assert "Vier-Augen-Prinzip" not in out["STARTER_KIT_HTML"]
        assert "two-person principle" in out["STARTER_KIT_HTML"]
        assert not calls

    def test_heuristic_core_shared_with_fallback_gate(self):
        """Beide Pfade (KIS-1272-Fallback-Gate, KIS-1273-Sprachgate) nutzen
        dieselbe Kernfunktion _text_looks_german."""
        import inspect
        import gpt_analyze as g
        assert g._text_looks_german("Für Ihr Unternehmen ergeben sich große Potenziale.")
        assert not g._text_looks_german("This is plain English content for your company.")
        assert not g._text_looks_german("Übersicht", min_chars=25)  # zu kurz
        # Stopwörter ohne Umlaute (>=3) reichen
        assert g._text_looks_german("Das Team wird die Planung mit dem Kunden bei Bedarf auch anpassen und testen.")
        src = inspect.getsource(g._fallback_html_looks_german)
        assert "_text_looks_german" in src

    def test_hook_in_analyze_briefing_before_render(self):
        """Source-Contract: Der Sweep hängt in analyze_briefing NACH den
        Enforcern/Heals und VOR render() (und vor dem Platin-QA-Gate)."""
        import inspect
        import gpt_analyze as g
        src = inspect.getsource(g.analyze_briefing)
        sweep_pos = src.find("_en_language_sweep_sections(")
        render_pos = src.find("result = render(")
        qw_restore_pos = src.find("[FIX-QW1] Post-healer QW restore")
        assert sweep_pos != -1, "Sprachgate ist nicht eingehängt"
        assert render_pos != -1
        assert sweep_pos < render_pos, "Sprachgate muss VOR render() laufen"
        assert qw_restore_pos != -1 and qw_restore_pos < sweep_pos, \
            "Sprachgate muss NACH dem Post-Healer-QW-Restore laufen"


# =============================================================================
# F — Programmnamen-Schutz in der Förder-Übersetzung
# =============================================================================

class TestFundingNameShield:
    def test_bafa_name_survives_map(self):
        from services.funding_recommender import _translate_funding_value_en as t
        name = "BAFA – Förderung von Unternehmensberatungen für KMU"
        assert t(name) == name

    def test_games_name_survives_map(self):
        from services.funding_recommender import _translate_funding_value_en as t
        assert t("Games-Förderung des Bundes") == "Games-Förderung des Bundes"
        assert t("Games-Förderung des Bundes (BMFTR)") == "Games-Förderung des Bundes (BMFTR)"

    def test_name_embedded_in_sentence_survives(self):
        from services.funding_recommender import _translate_funding_value_en as t
        out = t("Über die Games-Förderung des Bundes sind KI-gestützte "
                "Produktionstools förderfähig")
        assert "Games-Förderung des Bundes" in out
        assert "Games-Funding" not in out
        assert "AI-supported" in out
        assert "eligible" in out

    def test_run5_kfw_relevance_cell(self):
        from services.funding_recommender import _translate_funding_value_en as t
        assert t("Mittel – KI als Teil von Digitalisierungsinvestitionen förderfähig") == \
            "Medium – AI as part of digitalisation investments eligible"
        # Auch die in Lauf 5 beobachtete Denglisch-Zwischenform wird sauber
        assert t("Mittel – AI als Teil von digitalisation investments eligible") == \
            "Medium – AI as part of digitalisation investments eligible"

    def test_run5_games_focus_cell(self):
        from services.funding_recommender import _translate_funding_value_en as t
        out = t("Entwicklung und Prototyping von Games; KI-gestützte "
                "Produktionstools im Rahmen der Projektkosten")
        assert out == ("Development and prototyping of games; AI-supported "
                       "production tools as part of the project costs")
        assert "im Rahmen of the" not in out
        assert "Projektkosten" not in out

    def test_new_category_terms(self):
        from services.funding_recommender import _translate_funding_value_en as t
        out = t("Verwaltungsdigitalisierung, IT-Sicherheit, Prozessautomatisierung")
        assert out == "administrative digitalisation, IT-Sicherheit, process automation"
        assert t("Digitalisierung, Innovation, Wachstumsfinanzierung") == \
            "digitalisation, Innovation, growth financing"

    def test_prompt_block_keeps_name_translates_relevance(self):
        from services.funding_recommender import format_funding_programs_for_prompt
        programs = [{
            "name": "BAFA – Förderung von Unternehmensberatungen für KMU",
            "provider": "BAFA",
            "funding_rate": "50%",
            "max_funding": "bis 1.750 €",
            "ki_relevance": "Sehr hoch – KI-Projekte explizit förderfähig",
            "url": "",
            "summary": "",
        }]
        block = format_funding_programs_for_prompt(programs, lang="en")
        assert "- BAFA – Förderung von Unternehmensberatungen für KMU (provider: BAFA)" in block
        assert "Funding von Unternehmensberatungen" not in block
        assert "AI relevance: Very high – AI projects explicitly eligible" in block
        assert "Max. funding: up to 1,750 €" in block

    def test_prompt_block_de_unchanged(self):
        from services.funding_recommender import format_funding_programs_for_prompt
        programs = [{
            "name": "BAFA – Förderung von Unternehmensberatungen für KMU",
            "provider": "BAFA",
            "funding_rate": "50%",
            "max_funding": "bis 1.750 €",
            "ki_relevance": "Sehr hoch – KI-Projekte explizit förderfähig",
            "url": "",
            "summary": "",
        }]
        block = format_funding_programs_for_prompt(programs, lang="de")
        assert "Träger: BAFA" in block
        assert "KI-Relevanz: Sehr hoch – KI-Projekte explizit förderfähig" in block

    def test_filtered_programs_en_relevance_translated_name_intact(self):
        from services.funding_recommender import get_filtered_funding_programs
        programs = get_filtered_funding_programs(
            bundesland="Berlin", size="team", branch="medien", country="DE", lang="en")
        assert programs
        for p in programs:
            assert "Funding von Unternehmensberatungen" not in p["name"]
            assert "förderfähig" not in p["ki_relevance"]
            assert "Sehr hoch" not in p["ki_relevance"]

    def test_en_funding_table_names_intact_cells_translated(self):
        from services.extra_sections import build_core_funding_table_html
        briefing = {"BRANCHE_LABEL": "Medien", "BUNDESLAND_LABEL": "Berlin",
                    "UNTERNEHMENSGROESSE_LABEL": "2-10 (Kleines Team)"}
        html = build_core_funding_table_html(briefing, lang="en")
        # Programm-Namen (PROGRAMME-Spalte) bleiben exakt erhalten
        assert "BAFA – Förderung von Unternehmensberatungen für KMU" in html
        assert "Funding von Unternehmensberatungen" not in html
        assert "Games-Funding" not in html
        # Lauf-5-Denglisch darf nicht mehr entstehen
        assert "im Rahmen of the" not in html
        assert "als Teil von" not in html
        assert "Projektkosten" not in html
        assert "förderfähig" not in html

    def test_de_funding_table_unchanged(self):
        from services.extra_sections import build_core_funding_table_html
        briefing = {"BRANCHE_LABEL": "Medien", "BUNDESLAND_LABEL": "Berlin",
                    "UNTERNEHMENSGROESSE_LABEL": "2-10 (Kleines Team)"}
        html = build_core_funding_table_html(briefing, lang="de")
        assert "<th>KI-Relevanz</th>" in html
        assert "BAFA – Förderung von Unternehmensberatungen für KMU" in html
        assert "Sehr hoch" in html


# =============================================================================
# R — Risk-Narrativ-Politur
# =============================================================================

class TestRiskNarrativePolish:
    def _report(self):
        from services.risk_engine_v2 import (
            RiskReport, _generate_default_risk_matrix, _generate_narrative_summary)
        matrix = _generate_default_risk_matrix("limited", "niedrig", 2, {})
        narrative = _generate_narrative_summary("limited", "niedrig", 2, 78.0, "B", {})
        return RiskReport(
            ai_act_class="limited",
            dsgvo_risk_level="niedrig",
            vendor_risk_score=2,
            risk_matrix=matrix,
            consolidated_score=78.0,
            consolidated_grade="B",
            narrative_summary=narrative,
        )

    def test_en_wording_polished(self):
        from services.risk_engine_v2 import risk_report_to_html
        html = risk_report_to_html(self._report(), lang="en")
        assert "well manageable" not in html
        assert "The risk profile is manageable." in html

    def test_de_unchanged(self):
        from services.risk_engine_v2 import risk_report_to_html
        html = risk_report_to_html(self._report(), lang="de")
        assert "Das Risikoprofil ist gut beherrschbar." in html


# =============================================================================
# Q — Quick-Win-Fußnote: generisches "siehe X" → "see X" (nur EN, nur Hinweis)
# =============================================================================

class TestQuickwinFootnoteSiehe:
    def _payload(self, hinweis):
        import json
        return json.dumps([{
            "title": "Transcription workflow",
            "icon": "🎯",
            "problem": "Manual logging eats editing time.",
            "wirkung": "Saves 5-8 hours per month.",
            "umsetzung": "Pilot on one project.",
            "hinweis": hinweis,
        }])

    def test_en_generic_siehe_translated(self):
        from services.quickwins_renderer import render_quickwins_premium_json
        html = render_quickwins_premium_json(
            self._payload("– siehe AI-Projects"), "FULL", lang="en")
        assert html
        assert "siehe" not in html
        assert "– see AI-Projects" in html

    def test_en_capitalized_siehe_translated(self):
        from services.quickwins_renderer import render_quickwins_premium_json
        html = render_quickwins_premium_json(
            self._payload("Siehe Roadmap for details"), "FULL", lang="en")
        assert "Siehe" not in html
        assert "See Roadmap for details" in html

    def test_en_legacy_business_case_mapping_kept(self):
        from services.quickwins_renderer import render_quickwins_premium_json
        html = render_quickwins_premium_json(
            self._payload("siehe Business Case"), "FULL", lang="en")
        assert "siehe Business Case" not in html
        assert "see business case" in html

    def test_de_hinweis_unchanged(self):
        from services.quickwins_renderer import render_quickwins_premium_json
        html = render_quickwins_premium_json(
            self._payload("– siehe KI-Projekte"), "FULL", lang="de")
        assert "– siehe KI-Projekte" in html

    def test_en_body_text_not_globally_replaced(self):
        """Kein globaler Ersatz: 'siehe' außerhalb des Hinweis-Felds bleibt
        (dafür ist das Sprachgate zuständig)."""
        import json
        from services.quickwins_renderer import render_quickwins_premium_json
        payload = json.dumps([{
            "title": "Workflow",
            "icon": "🎯",
            "problem": "Manual work (siehe oben) takes time.",
            "wirkung": "Saves hours.",
            "umsetzung": "Pilot it.",
            "hinweis": "see business case",
        }])
        html = render_quickwins_premium_json(payload, "FULL", lang="en")
        assert "siehe oben" in html


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
