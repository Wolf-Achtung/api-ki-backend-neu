# -*- coding: utf-8 -*-
"""KIS-1235: Chat-Fragebogen-Fixes aus dem Frontend-Testlauf.

Drei gemeldete Bugs:
1. Bot-Antwort endet mitten im Wort ("… verpflichtet. Bei K") —
   Satzgrenzen-Trim im Post-Processing + max_tokens 800→1200.
2. Nach Blockwechsel erscheint keine Frage (leerer done-Text) —
   Fallback-Frage im Route-Handler (hier: Template-Question-Kontrakt).
3. Bestätigen-Button im Checkpoint abgeschnitten — Frontend-CSS
   (make-ki-frontend, per Playwright verifiziert).
"""
from __future__ import annotations

from routes.chat import _post_process_response


class TestSentenceFragmentTrim:

    def test_midword_fragment_removed(self):
        text = (
            "Als Einzelunternehmer sind Sie erst ab 20 Personen, die ständig "
            "mit personenbezogenen Daten arbeiten, zur Benennung eines "
            "Datenschutzbeauftragten verpflichtet. Bei K"
        )
        out = _post_process_response(text, None)
        assert out.endswith("verpflichtet.")
        assert "Bei K" not in out

    def test_complete_sentence_untouched(self):
        text = "Haben Sie einen Datenschutzbeauftragten benannt?"
        assert _post_process_response(text, None) == text

    def test_statement_ending_with_period_untouched(self):
        text = "Notiert. Weiter geht es mit dem nächsten Bereich."
        assert _post_process_response(text, None) == text

    def test_no_sentence_boundary_keeps_text(self):
        # Kein früheres Satzende → nichts zu trimmen, Text bleibt erhalten
        text = "Kurzer Fragment-Text ohne Satzende am Anfang der Antwort"
        assert _post_process_response(text, None) == text

    def test_large_tail_not_trimmed(self):
        # Fragment > 40 % der Antwort → kein Trim (Schutz vor Inhaltsverlust)
        text = "Kurz. " + "Dies ist ein sehr langer angefangener Satz ohne Ende " * 4
        out = _post_process_response(text, None)
        assert len(out) > len("Kurz.")

    def test_colon_ending_untouched(self):
        # Doppelpunkt ist legitimes Ende (z. B. vor QR-Buttons)
        text = "Wählen Sie bitte eine der folgenden Optionen:"
        assert _post_process_response(text, None) == text


class TestBlockTransitionFallback:
    """Kontrakt für den Leere-Antwort-Fallback: Für Template-Felder muss
    get_template_question eine Frage liefern, sonst greift das Label."""

    def test_template_question_available_for_template_fields(self):
        from services.field_templates import (
            get_template_question, is_template_field, FIELD_QUESTIONS,
        )
        assert FIELD_QUESTIONS, "Template-Fragen dürfen nicht leer sein"
        _covered = [f for f in FIELD_QUESTIONS if is_template_field(f)]
        assert _covered, "Mindestens ein Template-Feld erwartet"
        for field in _covered[:5]:
            assert get_template_question(field), field

    def test_field_label_fallback_nonempty(self):
        from services.chat_normalizer import get_field_label
        label = get_field_label("ki_ziele", "r1")
        assert isinstance(label, str) and label.strip()
