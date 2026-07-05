# -*- coding: utf-8 -*-
"""KIS-1235 P3: Neue Fragebogen-Inhalte + Live-Widerspruchs-Check.

1. Neue Felder: projekte_pro_monat + durchschnittshonorar (QR, Block A)
   und top_zeitfresser (Freitext mit Inspiration-Chips, Block C).
2. Quick-Wins-Prompt nutzt die benannten Zeitfresser als primäre Anker.
3. Live-Widerspruchs-Check: kurze, einmalige Rückfrage im Chat, sobald
   eine bekannte Spannung in den gesammelten Antworten auftaucht.
"""
from __future__ import annotations

from services.briefing_contradictions import detect_contradictions_chat


# =========================================================================
# 1. Feld-Registrierung
# =========================================================================

class TestNewFieldRegistration:

    def test_registry_entries(self):
        from services.chat_normalizer import FIELD_REGISTRY
        assert FIELD_REGISTRY["projekte_pro_monat"]["type"] == "enum"
        assert FIELD_REGISTRY["durchschnittshonorar"]["type"] == "enum"
        assert FIELD_REGISTRY["top_zeitfresser"]["type"] == "text"
        assert FIELD_REGISTRY["top_zeitfresser"]["chat_mode"] == "FT"
        for f in ("projekte_pro_monat", "durchschnittshonorar", "top_zeitfresser"):
            assert FIELD_REGISTRY[f]["required"] is False, f

    def test_sections_contain_new_fields(self):
        from services.chat_normalizer import SECTIONS
        s0 = SECTIONS[0]["fields"]
        assert "projekte_pro_monat" in s0
        # KIS-1240: Honorar wird nicht mehr gefragt (abgeleitet statt erhoben)
        assert "durchschnittshonorar" not in s0
        assert "top_zeitfresser" in SECTIONS[3]["fields"]

    def test_block_assignment(self):
        from routes.chat import BLOCK_FIELDS
        assert "projekte_pro_monat" in BLOCK_FIELDS["A"]
        # KIS-1240: Honorar-Frage entfernt
        assert "durchschnittshonorar" not in BLOCK_FIELDS["A"]
        assert "top_zeitfresser" in BLOCK_FIELDS["C"]

    def test_enum_options_and_labels(self):
        from services.chat_conversation import _ENUM_DISPLAY
        assert _ENUM_DISPLAY["projekte_pro_monat"]["2_5"] == "2–5"
        assert _ENUM_DISPLAY["durchschnittshonorar"]["1k_5k"] == "1.000–5.000 €"

    def test_questions_and_examples(self):
        from services.field_templates import (
            FIELD_QUESTIONS, FIELD_EXAMPLES, SONNET_REQUIRED_FIELDS,
        )
        assert "Projekte" in FIELD_QUESTIONS["projekte_pro_monat"]
        # KIS-1240: Honorar-Frage entfernt — darf nie wieder gestellt werden
        assert "durchschnittshonorar" not in FIELD_QUESTIONS
        assert "Zeit" in FIELD_QUESTIONS["top_zeitfresser"]
        assert len(FIELD_EXAMPLES["top_zeitfresser"]) == 3
        # KIS-1243: top_zeitfresser ist jetzt Template-Feld — die Frage
        # muss deterministisch mit den Inspiration-Chips gekoppelt sein.
        assert "top_zeitfresser" not in SONNET_REQUIRED_FIELDS

    def test_briefing_labels(self):
        from services.email_templates import _R1_LABELS
        assert _R1_LABELS["projekte_pro_monat"] == "Aufträge/Projekte pro Monat"
        assert _R1_LABELS["top_zeitfresser"] == "Top-Zeitfresser"

    def test_prompt_vars_expose_new_fields(self):
        import gpt_analyze
        vars_ = gpt_analyze._build_prompt_vars(
            {"branche": "beratung", "unternehmensgroesse": "solo",
             "hauptleistung": "KI-Beratung",
             "top_zeitfresser": "Angebote schreiben; E-Mails",
             "projekte_pro_monat": "2_5", "durchschnittshonorar": "5k_20k"},
            {"overall": 70},
        )
        assert vars_["top_zeitfresser"] == "Angebote schreiben; E-Mails"
        assert vars_["PROJEKTE_PRO_MONAT"] == "2_5"
        # KIS-1240: expliziter Alt-Wert wird als Label durchgereicht
        assert vars_["DURCHSCHNITTSHONORAR"] == "5.000\u201320.000 \u20ac"

    def test_quick_wins_prompt_anchors_on_zeitfresser(self):
        with open("prompts/de/quick_wins.md", encoding="utf-8") as f:
            src = f.read()
        assert "TOP-ZEITFRESSER" in src
        assert "{{top_zeitfresser}}" in src


# =========================================================================
# 2. Live-Widerspruchs-Check (Chat-Kurzformen)
# =========================================================================

class TestLiveContradictionCheck:

    def test_tools_check_fires(self):
        out = detect_contradictions_chat({
            "vorhandene_tools": "keine", "s5_software": "ChatGPT, Claude",
        })
        keys = [k for k, _ in out]
        assert keys == ["tools"]
        assert "Kurzer Abgleich" in out[0][1]

    def test_kompetenz_check_fires(self):
        out = detect_contradictions_chat({
            "interne_ki_kompetenzen": "nein", "ki_kompetenz": "hoch",
        })
        assert [k for k, _ in out] == ["kompetenz"]

    def test_datenreife_and_budget(self):
        out = detect_contradictions_chat({
            "datenreife": "keine", "digitalisierungsgrad": "9",
            "groesster_engpass": "Kein Budget", "investitionsbudget": "2.000–10.000",
        })
        assert [k for k, _ in out] == ["datenreife", "budget"]
        assert all("?" in t for _, t in out)

    def test_clean_answers_no_findings(self):
        assert detect_contradictions_chat({
            "vorhandene_tools": "crm", "ki_kompetenz": "hoch",
            "digitalisierungsgrad": "9", "datenreife": "strukturiert",
        }) == []

    def test_route_hook_present_with_flag_and_ack(self):
        src = open("routes/chat.py", encoding="utf-8").read()
        assert "CHAT_LIVE_CONTRADICTION_CHECK" in src
        assert "contradiction_acks" in src
        assert "detect_contradictions_chat" in src
