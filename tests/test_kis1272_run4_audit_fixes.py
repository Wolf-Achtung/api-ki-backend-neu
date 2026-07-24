# -*- coding: utf-8 -*-
"""KIS-1272 — Audit-Fixes für den vierten EN-Testlauf (KIS-1253, R1).

Kompakte Unit-Tests ohne Netzwerk/LLM (LLM-Calls werden gemockt):

  T1  gpt_analyze._get_fallback_content     — kuratierte DE-Fallbacks werden im
      EN-Pfad per (gemocktem) LLM übersetzt; DE bleibt byte-identisch; bei
      Übersetzungsfehler bleibt das deutsche Original (nie leer).
  T2  quickwins_renderer                    — EN-Labels (Impact/Implementation),
      Listen/Listen-Literale nie roh, "siehe Business Case" → EN.
  T3  risk_engine_v2                        — EN-Narrativ statt Denglisch,
      Matrix-Zeilenlabel "Implementation risk", DE unverändert.
  T4  funding_recommender/extra_sections    — Phrasen-Map: Förder-Zellwerte
      komplett englisch, "KI-Sicherheit.jetzt" geschützt.
  T5  tools_starter_kits                    — EN-Kit-Untertitel ohne internen
      Slug, Branchenlabel englisch.
  T6  LANG-Gate                             — sections["LANG"] wird in
      _generate_content_sections VOR den Quality-Enforcern gesetzt
      (Root-Cause von "begrenzt" im EN-Text).
  T11 sofort_start_generator                — Review-Labels nach Woche-1-Drop
      neu nummeriert (Off-by-one, DE und EN).
"""

import os
import re

os.environ.setdefault("JWT_SECRET", "t")
os.environ.setdefault("DATABASE_URL", "sqlite:///t.db")

import pytest


# =============================================================================
# T1 — Fallback-Übersetzung im EN-Pfad
# =============================================================================

class TestFallbackTranslationEN:
    def _briefing(self, lang):
        return {"lang": lang, "branche": "medien", "BRANCHE_LABEL": "Medien",
                "unternehmensgroesse": "2-10 (Kleines Team)"}

    def test_de_fallback_unchanged_and_no_llm_call(self, monkeypatch):
        import gpt_analyze
        calls = []

        def _boom(*a, **k):
            calls.append(1)
            raise AssertionError("LLM darf im DE-Pfad nicht aufgerufen werden")

        monkeypatch.setattr(gpt_analyze, "_call_llm_for_section", _boom)
        de = gpt_analyze._get_fallback_content(
            "executive_decision", self._briefing("de"), {"overall": 70})
        assert de
        assert "Strategische Empfehlungen" in de
        assert not calls
        # byte-identisch zur Implementierung (Wrapper = reiner Durchgriff)
        impl = gpt_analyze._get_fallback_content_impl(
            "executive_decision", self._briefing("de"), {"overall": 70})
        assert de == impl

    def test_en_fallback_gets_translated(self, monkeypatch):
        import gpt_analyze
        translated = '<div class="executive-decision-fallback"><h3>Strategic recommendations</h3></div>'
        monkeypatch.setattr(
            gpt_analyze, "_call_llm_for_section", lambda **k: translated)
        out = gpt_analyze._get_fallback_content(
            "executive_decision", self._briefing("en"), {"overall": 70})
        assert out == translated

    def test_en_translation_failure_keeps_german_original(self, monkeypatch):
        import gpt_analyze
        monkeypatch.setattr(
            gpt_analyze, "_call_llm_for_section",
            lambda **k: (_ for _ in ()).throw(RuntimeError("timeout")))
        out = gpt_analyze._get_fallback_content(
            "executive_decision", self._briefing("en"), {"overall": 70})
        assert out  # niemals leer
        assert "Strategische Empfehlungen" in out

    def test_en_translation_empty_response_keeps_german(self, monkeypatch):
        import gpt_analyze
        monkeypatch.setattr(gpt_analyze, "_call_llm_for_section", lambda **k: "")
        out = gpt_analyze._get_fallback_content(
            "executive_decision", self._briefing("en"), {"overall": 70})
        assert out
        assert "Strategische Empfehlungen" in out

    def test_en_fallback_already_english_not_retranslated(self, monkeypatch):
        """foerderpotenzial hat einen eigenen EN-Zweig — kein LLM-Call nötig."""
        import gpt_analyze

        def _boom(**k):
            raise AssertionError("Bereits englischer Fallback darf nicht übersetzt werden")

        monkeypatch.setattr(gpt_analyze, "_call_llm_for_section", _boom)
        out = gpt_analyze._get_fallback_content(
            "foerderpotenzial", self._briefing("en"), {"overall": 70})
        assert "Funding Potential" in out

    def test_german_detection_heuristic(self):
        from gpt_analyze import _fallback_html_looks_german
        assert _fallback_html_looks_german(
            "<p>Für Ihr Unternehmen ergeben sich große Potenziale.</p>")
        assert not _fallback_html_looks_german(
            "<p>This section describes funding options for your company.</p>")
        assert not _fallback_html_looks_german("")


# =============================================================================
# T2 — Quick-Wins-Renderer
# =============================================================================

class TestQuickwinsRendererEN:
    def _payload(self, umsetzung):
        import json
        return json.dumps([{
            "title": "Transcription workflow",
            "icon": "🎯",
            "problem": "Manual logging eats editing time.",
            "wirkung": "Saves 5-8 hours per month.",
            "umsetzung": umsetzung,
            "hinweis": "siehe Business Case",
        }])

    def test_en_labels_impact_and_implementation(self):
        from services.quickwins_renderer import render_quickwins_premium_json
        html = render_quickwins_premium_json(
            self._payload("Pilot on one project."), "FULL", lang="en")
        assert html
        assert "Impact:" in html
        assert "Implementation:" in html
        assert "Wirkung:" not in html
        assert "Umsetzung:" not in html

    def test_de_labels_unchanged(self):
        from services.quickwins_renderer import render_quickwins_premium_json
        html = render_quickwins_premium_json(
            self._payload("Pilot in einem Projekt."), "FULL", lang="de")
        assert html
        assert "Wirkung:" in html
        assert "Umsetzung:" in html
        assert "siehe Business Case" in html

    def test_list_value_rendered_as_ul(self):
        from services.quickwins_renderer import render_quickwins_premium_json
        html = render_quickwins_premium_json(
            self._payload(["Select an AVV-covered tool", "Pilot on one project"]),
            "FULL", lang="en")
        assert html
        assert "['" not in html and '["' not in html
        assert "<ul" in html and "<li>Select an AVV-covered tool</li>" in html

    def test_python_list_literal_string_parsed(self):
        from services.quickwins_renderer import qw_field_value_to_html
        out = qw_field_value_to_html(
            "['Select an AVV-covered transcription tool', 'Pilot on one project']")
        assert out.startswith("<ul")
        assert "<li>Select an AVV-covered transcription tool</li>" in out
        assert "['" not in out

    def test_invalid_list_literal_kept_escaped(self):
        from services.quickwins_renderer import qw_field_value_to_html
        out = qw_field_value_to_html("['broken literal")
        assert "broken literal" in out
        assert "<ul" not in out

    def test_plain_string_unchanged(self):
        from services.quickwins_renderer import qw_field_value_to_html
        assert qw_field_value_to_html("Just a sentence.") == "Just a sentence."

    def test_en_hinweis_translated(self):
        from services.quickwins_renderer import render_quickwins_premium_json
        html = render_quickwins_premium_json(
            self._payload("Pilot on one project."), "FULL", lang="en")
        assert "siehe Business Case" not in html
        assert "see business case" in html


# =============================================================================
# T3 — Risk-Engine v2
# =============================================================================

class TestRiskEngineEN:
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

    def test_en_narrative_fully_english(self):
        from services.risk_engine_v2 import risk_report_to_html
        html = risk_report_to_html(self._report(), lang="en")
        assert "gut beherrschbar" not in html
        assert "Transparenzpflichten" not in html
        assert "überschaubar" not in html
        assert "The risk profile is well manageable." in html
        assert "Transparency obligations under the AI Act apply" in html
        assert "The data protection requirements are manageable." in html

    def test_en_matrix_row_label(self):
        from services.risk_engine_v2 import risk_report_to_html
        html = risk_report_to_html(self._report(), lang="en")
        assert "Implementierungsrisiko" not in html
        assert "Implementation risk" in html
        assert "Data protection (GDPR)" in html

    def test_de_output_unchanged(self):
        from services.risk_engine_v2 import risk_report_to_html
        html = risk_report_to_html(self._report(), lang="de")
        assert "Implementierungsrisiko" in html
        assert "Das Risikoprofil ist gut beherrschbar." in html
        assert ">Risiko</td>" in html

    def test_narrative_translator_maps_all_bricks(self):
        from services.risk_engine_v2 import _translate_narrative_summary_en
        out = _translate_narrative_summary_en(
            "Das Risikoprofil erfordert gezielte Maßnahmen. "
            "Standard-Datenschutzmaßnahmen sind erforderlich.")
        assert out == ("The risk profile requires targeted measures. "
                       "Standard data protection measures are required.")


# =============================================================================
# T4 — Förder-Tabellen-Zellwerte EN
# =============================================================================

class TestFundingTermsEN:
    def test_observed_run4_cells(self):
        from services.funding_recommender import _translate_funding_value_en as t
        assert t("Sehr hoch – KI-Projekte explizit förderfähig") == \
            "Very high – AI projects explicitly eligible"
        assert t("Hoch – ideal für initiale KI-Strategieberatung") == \
            "high – ideal for initial AI strategy consulting"
        assert t("Mittel bis hoch – KI oft Teil von Digitalisierungsprojekten") == \
            "Medium to high – AI often part of digitalisation projects"
        assert t("Kinofilmproduktion; KI-gestützte Produktionsschritte sind "
                 "förderfähige Herstellungskosten") == \
            ("Theatrical film production; AI-supported production steps are "
             "eligible production costs")
        assert t("KI-gestützte Projekte werden explizit gefördert") == \
            "AI-supported projects are explicitly funded"
        assert t("Entwicklung und Prototyping von Games") == \
            "Development and prototyping of games"

    def test_ki_sicherheit_domain_protected(self):
        from services.funding_recommender import _translate_funding_value_en as t
        assert t("KI-Sicherheit.jetzt") == "KI-Sicherheit.jetzt"
        assert "KI-Sicherheit" in t("Mehr auf KI-Sicherheit.jetzt zu KI-Projekten")

    def test_generic_ki_word_boundary(self):
        from services.funding_recommender import _translate_funding_value_en as t
        assert t("KI, Cloud, Automation") == "AI, Cloud, Automation"

    def test_en_funding_table_cells_english(self):
        from services.extra_sections import build_core_funding_table_html
        briefing = {"BRANCHE_LABEL": "Medien", "BUNDESLAND_LABEL": "Berlin",
                    "UNTERNEHMENSGROESSE_LABEL": "2-10 (Kleines Team)"}
        html = build_core_funding_table_html(briefing, lang="en")
        assert "<th>AI relevance</th>" in html
        for german in ("förderfähig", "Sehr hoch", "Mittel bis hoch",
                       "KI-Projekte", "explizit gefördert"):
            assert german not in html, f"deutscher Rest in EN-Tabelle: {german}"
        assert "Very high" in html

    def test_de_funding_table_unchanged(self):
        from services.extra_sections import build_core_funding_table_html
        briefing = {"BRANCHE_LABEL": "Medien", "BUNDESLAND_LABEL": "Berlin",
                    "UNTERNEHMENSGROESSE_LABEL": "2-10 (Kleines Team)"}
        html = build_core_funding_table_html(briefing, lang="de")
        assert "<th>KI-Relevanz</th>" in html
        assert "Sehr hoch" in html  # deutsche Rohwerte bleiben


# =============================================================================
# T5 — Kit-Untertitel ohne Slug-Leak
# =============================================================================

class TestStarterKitSubtitleEN:
    def _ctx(self):
        return {"branche": "medien",
                "unternehmensgroesse": "team",
                "expertise_level": "intermediate",
                "maturity_level": 3}

    def test_en_kit_name_and_segment_label(self):
        from services.tools_starter_kits import generate_starter_kit
        kit = generate_starter_kit(self._ctx(), lang="en")
        assert "Medien" not in kit.kit_name
        assert "Media" in kit.kit_name
        assert kit.segment_label == "Team · Media · AI practitioner"
        assert "TEAM/" not in kit.segment_label

    def test_de_kit_unchanged(self):
        from services.tools_starter_kits import generate_starter_kit
        kit = generate_starter_kit(self._ctx(), lang="de")
        assert kit.kit_name == "Team-Boost Kit für Medien"
        assert kit.segment_label == "TEAM/Medien/KI-Anwender"


# =============================================================================
# T6 — LANG-Gate: sections["LANG"] vor den Quality-Enforcern
# =============================================================================

class TestLangGateForBadgeLocalization:
    def test_badge_localization_gated_for_en(self):
        from services.content_quality_enforcer import apply_badge_localization
        sections = {"LANG": "en",
                    "X_HTML": "applications fall under the limited-risk category"}
        out = apply_badge_localization(dict(sections))
        assert "limited-risk" in out["X_HTML"]
        assert "begrenzt" not in out["X_HTML"]

    def test_badge_localization_translates_without_lang_key(self):
        """Dokumentiert die Root-Cause: ohne LANG greift der DE-Default."""
        from services.content_quality_enforcer import apply_badge_localization
        out = apply_badge_localization(
            {"X_HTML": "test on a limited scale"})
        assert "begrenzt" in out["X_HTML"]

    def test_generate_content_sections_sets_lang_before_enforcers(self):
        """Source-Contract: LANG wird am Funktionsanfang gesetzt, VOR jedem
        apply_all_quality_enforcers-Aufruf innerhalb der Funktion."""
        import inspect
        import gpt_analyze
        src = inspect.getsource(gpt_analyze._generate_content_sections)
        set_pos = src.find('sections["LANG"]')
        enforcer_pos = src.find("apply_all_quality_enforcers(")
        assert set_pos != -1, "sections['LANG'] wird nicht gesetzt"
        assert enforcer_pos != -1
        assert set_pos < enforcer_pos


# =============================================================================
# T11 — Challenge-Review-Labels nach Woche-1-Drop
# =============================================================================

class TestChallengeReviewRenumbering:
    def _challenge(self):
        return {
            "woche_1": {"titel": "Erste Schritte", "tage": [
                {"tag": i, "aufgabe": f"Aufgabe {i}", "dauer": "10 Min"}
                for i in range(1, 7)
            ] + [{"tag": 7, "aufgabe": "Woche 1 Review: Was hat Zeit gespart?",
                  "dauer": "15 Min"}]},
            "woche_2": {"titel": "Anwenden", "tage": [
                {"tag": i, "aufgabe": f"Aufgabe {i}", "dauer": "10 Min"}
                for i in range(8, 14)
            ] + [{"tag": 14, "aufgabe": "Woche 2 Review: Zeitersparnis dokumentieren",
                  "dauer": "15 Min"}]},
            "woche_3": {"titel": "Vertiefen", "tage": [
                {"tag": i, "aufgabe": f"Task {i}", "dauer": "10 min"}
                for i in range(15, 21)
            ] + [{"tag": 21, "aufgabe": "Week 3 review: identify best use cases",
                  "dauer": "20 min"}]},
        }

    def test_review_labels_renumbered_after_drop(self):
        from services.sofort_start_generator import _drop_first_week_and_renumber
        out = _drop_first_week_and_renumber(self._challenge())
        assert "woche_1" not in out
        w2_tasks = {t["tag"]: t["aufgabe"] for t in out["woche_2"]["tage"]}
        w3_tasks = {t["tag"]: t["aufgabe"] for t in out["woche_3"]["tage"]}
        # Tag 7 (Ende der ersten verbleibenden Woche) → "Woche 1 Review"
        assert w2_tasks[7].startswith("Woche 1 Review")
        # Tag 14 → "Week 2 review" (EN-Label ebenfalls neu nummeriert)
        assert w3_tasks[14].startswith("Week 2 review")

    def test_day_renumbering_still_intact(self):
        from services.sofort_start_generator import _drop_first_week_and_renumber
        out = _drop_first_week_and_renumber(self._challenge())
        all_days = [t["tag"] for w in out.values() for t in w["tage"]]
        assert all_days == list(range(1, 15))

    def test_source_dict_untouched(self):
        from services.sofort_start_generator import _drop_first_week_and_renumber
        src = self._challenge()
        _drop_first_week_and_renumber(src)
        assert src["woche_2"]["tage"][-1]["aufgabe"].startswith("Woche 2 Review")
        assert src["woche_2"]["tage"][-1]["tag"] == 14


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
