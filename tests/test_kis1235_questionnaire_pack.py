# -*- coding: utf-8 -*-
"""KIS-1235 PR E: Fragebogen & Briefing.

Der Lauf 1235 zeigte, dass die vier "Widersprüche" großteils Frage-Artefakte
sind: 'vorhandene_tools' fragt nur klassische Business-Systeme ab (Antwort
"Keine / andere" wird als "keine" gespeichert), 'interne_ki_kompetenzen' ist
als Team-Frage formuliert (Solo antwortet korrekt "Nein"). Dazu: Briefing-PDF
zeigte rohe Enum-Codes ("freiberufler", "marktfuehrerschaft") und kappte die
Hauptleistung mitten im Wort ("KI-API-basie").
"""
from __future__ import annotations

from services.email_templates import _prettify_enum_value, render_briefing_pdf_html


class TestQuestionWording:

    def test_tools_question_scopes_classic_systems(self):
        from services.field_templates import FIELD_QUESTIONS
        q = FIELD_QUESTIONS["vorhandene_tools"]
        assert "klassisch" in q.lower()
        assert "KI-Tools" in q  # Abgrenzung zur FB2-Frage

    def test_competence_question_is_solo_aware(self):
        from services.field_templates import FIELD_QUESTIONS
        q = FIELD_QUESTIONS["interne_ki_kompetenzen"]
        assert "Solo" in q or "eigene" in q

    def test_tools_none_option_label_disambiguated(self):
        from services.chat_conversation import _ENUM_DISPLAY
        label = _ENUM_DISPLAY["vorhandene_tools"]["keine"]
        assert "klassisch" in label.lower()
        assert label != "Keine / andere"


class TestBriefingLabels:

    def test_enum_value_uses_questionnaire_label(self):
        assert _prettify_enum_value("b2b", "zielgruppen") == "B2B (Geschäftskunden)"
        assert _prettify_enum_value("marktfuehrerschaft", "vision_prioritaet") == (
            "Technologieführerschaft im Markt"
        )

    def test_free_text_untouched(self):
        assert _prettify_enum_value("Berlin, DE", "region") == "Berlin, DE"

    def test_unknown_enum_falls_back_to_generic(self):
        # kein Mapping vorhanden → bisheriges Verhalten (underscores → Spaces)
        assert _prettify_enum_value("unbekannter_wert", "gibt_es_nicht") == "unbekannter wert"


class TestBriefingHauptleistung:

    def _render(self, hauptleistung: str) -> str:
        return render_briefing_pdf_html(
            display_id="KIS-TEST",
            datum="03.07.2026",
            answers={"hauptleistung": hauptleistung, "branche": "beratung"},
            scores={},
            sections={},
        )

    def test_long_hauptleistung_cut_at_word_boundary(self):
        text = ("TÜV-zertifizierte KI-Manager-Beratung zur KI-Einführung in "
                "Unternehmen mit automatisierten KI-gestützten Fragebögen und "
                "LLM-API-Modellen für Analyse und Empfehlungen sowie Entwicklung "
                "von KI-API-basierten Produkten und Readiness-Checks für den "
                "deutschen Mittelstand und weitere Zielgruppen im DACH-Raum")
        html = self._render(text)
        assert "KI-API-basie<" not in html  # kein Mitten-im-Wort-Schnitt
        assert "…" in html

    def test_short_hauptleistung_untouched(self):
        html = self._render("KI-Beratung für KMU")
        assert "KI-Beratung für KMU" in html and "…" not in html.split("Hauptleistung")[1][:80]


class TestCoverProfile:

    def test_renderer_builds_profile_fallback(self):
        src = open("services/strategy_renderer.py", encoding="utf-8").read()
        assert "wird aus Datenschutzgründen bewusst nie" in src
        assert 'briefing_data.get("unternehmen_name")' in src
