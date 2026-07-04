# -*- coding: utf-8 -*-
"""KIS-1240: Fragebogen-UX-Fixes aus dem abgebrochenen Testlauf (04.07.).

1. BLOCKER: Nach der Honorar-Eingabe ging es nicht weiter (Block A 8/9,
   keine Frage, keine Chips). Zwei Ursachen, zwei Fixes:
   a) projekte_pro_monat/durchschnittshonorar hatten keine _QR_OPTIONS —
      Enum-Felder wurden als Freitext gestellt.
   b) Frage-Garantie: Solange Felder offen sind, muss die Antwort eine
      Frage enthalten — sonst wird die Template-Frage angehängt.
2. Die Honorar-Frage wirkte übergriffig — sie wird NICHT mehr gestellt;
   der Wert wird aus Jahresumsatz × Projekte/Monat abgeleitet.
3. Bereichs-Auswahl am Checkpoint: Empfehlung zuerst (ALL primary),
   Einzelbereiche sekundär.
"""
from __future__ import annotations


# =========================================================================
# 1a. Chips für projekte_pro_monat
# =========================================================================

class TestProjekteQrOptions:

    def test_qr_options_registered(self):
        from routes.chat import _QR_OPTIONS
        opts = {o["value"] for o in _QR_OPTIONS["projekte_pro_monat"]}
        assert opts == {"unter_2", "2_5", "6_10", "ueber_10", "keine_angabe"}

    def test_honorar_has_no_qr_options(self):
        from routes.chat import _QR_OPTIONS
        assert "durchschnittshonorar" not in _QR_OPTIONS


# =========================================================================
# 1b. Frage-Garantie
# =========================================================================

class TestQuestionGuarantee:

    def test_guard_present_with_conditions(self):
        src = open("routes/chat.py", encoding="utf-8").read()
        assert "KIS-1240: Frage-Garantie" in src
        idx = src.find("KIS-1240: Frage-Garantie")
        block = src[idx:idx + 1600]
        assert '"?" not in full_response' in block
        assert "get_template_question(next_fields[0])" in block
        assert "_checkpoint_triggered" in block


# =========================================================================
# 2. Honorar wird abgeleitet statt erhoben
# =========================================================================

class TestHonorarDerivation:

    def test_derived_from_umsatz_and_projekte(self):
        import gpt_analyze
        out = gpt_analyze._resolve_avg_project_value({
            "jahresumsatz": "unter_100k", "projekte_pro_monat": "unter_2",
        })
        # 60.000 / (1,5 × 12) = 3.333 → gerundet 3.500
        assert "3.500" in out
        assert "geschätzt" in out

    def test_explicit_legacy_value_wins(self):
        import gpt_analyze
        out = gpt_analyze._resolve_avg_project_value({
            "durchschnittshonorar": "5k_20k",
            "jahresumsatz": "unter_100k", "projekte_pro_monat": "unter_2",
        })
        assert out == "5.000–20.000 €"

    def test_missing_inputs_yield_empty(self):
        import gpt_analyze
        assert gpt_analyze._resolve_avg_project_value({}) == ""
        assert gpt_analyze._resolve_avg_project_value(
            {"jahresumsatz": "keine_angabe", "projekte_pro_monat": "2_5"}) == ""

    def test_rounding_steps(self):
        import gpt_analyze
        # 6.000.000 / (12 × 12) = 41.667 → 5.000er-Schritt: 40.000
        out = gpt_analyze._resolve_avg_project_value({
            "jahresumsatz": "2m_10m", "projekte_pro_monat": "ueber_10",
        })
        assert "40.000" in out

    def test_question_never_asked_anywhere(self):
        from services.chat_normalizer import SECTIONS
        from services.field_templates import FIELD_QUESTIONS
        from routes.chat import BLOCK_FIELDS
        from services.chat_conversation import FIELD_DESCRIPTIONS
        for sec in SECTIONS:
            assert "durchschnittshonorar" not in sec["fields"]
        assert "durchschnittshonorar" not in FIELD_QUESTIONS
        for fields in BLOCK_FIELDS.values():
            assert "durchschnittshonorar" not in fields
        assert "durchschnittshonorar" not in FIELD_DESCRIPTIONS


# =========================================================================
# 3. Checkpoint-Auswahl: Empfehlung zuerst
# =========================================================================

class TestCheckpointOptions:
    # KIS-1241 (2. Abbruch): genau ZWEI Ein-Klick-Optionen, Single-Select —
    # kein Bestätigen-Schritt, keine Einzelbereichs-Chips, kein Schnellmodus.

    def test_exactly_two_single_select_options(self):
        src = open("routes/chat.py", encoding="utf-8").read()
        idx = src.find('field="__checkpoint__"')
        assert idx != -1
        block = src[idx - 1200:idx + 400]
        assert 'label="Vollständiger Report (empfohlen) · ~10 Min"' in block
        assert 'label="Schnell-Report jetzt erstellen"' in block
        assert "multi_select=False" in block
        assert "max_select" not in block
        # Einzelbereiche und Schnellmodus sind aus dem Checkpoint raus
        assert 'label="Nur:' not in src
        assert "Schnellmodus (alle Fragen auf einmal)" not in src

    def test_checkpoint_text_recommends(self):
        src = open("routes/chat.py", encoding="utf-8").read()
        assert "Meine Empfehlung: der vollständige Report" in src
        assert "Schnell-Report" in src

    def test_handler_accepts_single_values(self):
        src = open("routes/chat.py", encoding="utf-8").read()
        assert '_cp_value == "REPORT"' in src
        assert '_cp_value == "ALL"' in src
