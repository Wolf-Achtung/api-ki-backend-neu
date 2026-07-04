# -*- coding: utf-8 -*-
"""KIS-1243: Tools-Block-Unklarheiten aus Anlauf 4 (04.07.).

Zwei Befunde aus den Screenshots:
  1. Frage/Chips-Mismatch: Die Zeitfresser-Inspiration-Chips („Angebote und
     Proposals schreiben" …) standen unter der vorhandene_tools-Frage —
     Sonnet formulierte frei, die Chips kamen deterministisch für das
     next_field. Frage und Chips liefen auseinander.
  2. Doppel-Frage-Gefühl: zeitersparnis_prioritaet („Welche Aufgabe kostet
     … am meisten Zeit oder Nerven?") und top_zeitfresser („Welche 2-3
     Aufgaben rauben Ihnen am meisten Zeit?") waren fast wortgleich.

Lösung (Kopplungs-Prinzip): Felder mit deterministischen Chips bekommen
auch eine deterministische Frage — beide Felder sind jetzt Template-Felder
mit sprachlich klar abgegrenzten Fragen (Bereich vs. Einzelaufgaben), und
der Template-Mode greift auch nach sauber committeten Freitext-Turns.
"""
from __future__ import annotations


# =========================================================================
# 1. Beide Zeitfresser-Felder sind Template-Felder (Frage+Chips gekoppelt)
# =========================================================================

class TestTemplateCoupling:

    def test_both_fields_are_template_fields(self):
        from services.field_templates import is_template_field
        assert is_template_field("top_zeitfresser")
        assert is_template_field("zeitersparnis_prioritaet")

    def test_template_questions_served(self):
        from services.field_templates import get_template_question
        assert get_template_question("top_zeitfresser")
        assert get_template_question("zeitersparnis_prioritaet")

    def test_chips_still_registered(self):
        # top_zeitfresser: Inspiration-Chips; zeitersparnis_prioritaet:
        # branchenspezifische Chips — beide Kanäle bleiben aktiv.
        from services.field_templates import FIELD_EXAMPLES
        from routes.chat import FREETEXT_SUGGESTIONS
        assert len(FIELD_EXAMPLES["top_zeitfresser"]) == 3
        assert "default" in FREETEXT_SUGGESTIONS["zeitersparnis_prioritaet"]

    def test_gate_covers_freetext_turns(self):
        # Kopplungs-Garantie im Code: Template-Mode feuert auch ohne
        # QR-Klick, wenn das nächste Feld deterministische Chips hat und
        # der Turn sauber committed hat.
        src = open("routes/chat.py", encoding="utf-8").read()
        idx = src.find("KIS-1243: Kopplungs-Garantie")
        assert idx != -1
        block = src[idx:idx + 1400]
        assert "_nf_for_tpl in FIELD_EXAMPLES or _nf_for_tpl in FREETEXT_SUGGESTIONS" in block
        assert "_clean_commit_turn = bool(normalized) and not _draft_new_field" in block
        assert "(_is_qr_click or (_nf_has_deterministic_chips and _clean_commit_turn))" in block


# =========================================================================
# 2. Sprachliche Abgrenzung: Bereich vs. konkrete Einzelaufgaben
# =========================================================================

class TestQuestionDistinction:

    def test_questions_are_clearly_different(self):
        from services.field_templates import FIELD_QUESTIONS
        prio = FIELD_QUESTIONS["zeitersparnis_prioritaet"]
        tasks = FIELD_QUESTIONS["top_zeitfresser"]
        assert prio != tasks
        # Bereichs-Frage: fragt nach dem Bereich, nicht nach Aufgaben
        assert "Bereich" in prio
        assert "Aufgabe" not in prio
        # Aufgaben-Frage: explizit konkret, explizit Einzelaufgaben
        assert "konkret" in tasks
        assert "Einzelaufgaben" in tasks

    def test_field_descriptions_disambiguated(self):
        from services.chat_conversation import FIELD_DESCRIPTIONS
        prio = FIELD_DESCRIPTIONS["zeitersparnis_prioritaet"]
        tasks = FIELD_DESCRIPTIONS["top_zeitfresser"]
        # Die alte, fast wortgleiche Aufgaben-Formulierung ist raus
        assert "Welche Aufgabe kostet" not in prio
        assert "Bereich" in prio
        # Jede Beschreibung verweist auf das jeweils andere Feld
        assert "top_zeitfresser" in prio
        assert "zeitersparnis_prioritaet" in tasks

    def test_chip_bar_label_no_longer_zeitfresser(self):
        # Das Chip-Bar-Label des Prioritäts-Felds hieß wörtlich
        # „Zeitfresser" — Hauptquelle des Doppel-Frage-Gefühls.
        from routes.chat import _QR_LABELS
        assert _QR_LABELS["zeitersparnis_prioritaet"] != "Zeitfresser"
        assert _QR_LABELS["zeitersparnis_prioritaet"] == "Entlastungs-Bereiche"


# =========================================================================
# 3. Block-C-Prompt: Feld-Bindung statt verschmelzender Beispiel-Frage
# =========================================================================

class TestBlockCPrompt:

    def test_feld_bindung_rule_present(self):
        from services.chat_conversation import BLOCK_C_PROMPT
        assert "FELD-BINDUNG (STRIKT)" in BLOCK_C_PROMPT

    def test_fusing_example_removed(self):
        # „Welche Tools nutzen Sie aktuell und wo liegt der größte
        # Zeitfresser?" verschmolz genau die zwei Felder, die im
        # Screenshot kollidierten.
        from services.chat_conversation import BLOCK_C_PROMPT
        assert "wo liegt der größte Zeitfresser" not in BLOCK_C_PROMPT
