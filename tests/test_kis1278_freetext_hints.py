# -*- coding: utf-8 -*-
"""KIS-1278: Audit der Freitextfeld-Hinweise (alle Fragebögen, DE/EN).

Abgesichert wird die neue Struktur (keine Flow-Änderungen):

1. FIELD_QUESTIONS_EN — nativer EN-Fragensatz, schlüsselgleich zu
   FIELD_QUESTIONS. Genutzt vom Fast-Mode-Formular (vorher: nacktes
   EN-Label als "Frage") und von den deterministischen EN-Fallbacks in
   routes/chat.py (vorher: generisches "Next up: <label>…").
2. get_template_question_en — gleicher SONNET_REQUIRED_FIELDS-Gate wie
   die DE-Variante: Freitext-Felder liefern None, Sonnet formuliert.
3. Neue FIELD_QUESTIONS-Einträge für die 6 Sonnet-Freitext-Felder
   ändern den Chat-Template-Mode NICHT (is_template_field bleibt False),
   verbessern aber die Fast-Mode-Fragen (vorher Label ohne Hinweis).
4. FIELD_DESCRIPTIONS: medien_sparte ergänzt (Re-Ask-Kontext für die
   Sparten-Frage, KIS-1276/1277) und ki_hemmnisse um Medien-Beispiele
   erweitert (Phase-1-Medien-Fokus).
"""
from __future__ import annotations

from services.field_templates import (
    FIELD_QUESTIONS,
    FIELD_QUESTIONS_EN,
    SONNET_REQUIRED_FIELDS,
    get_template_question,
    get_template_question_en,
    is_template_field,
)

# Die 6 Freitext-Felder, die im Chat weiterhin Sonnet formuliert
FT_SONNET_FIELDS = {
    "hauptleistung", "ki_projekte", "geschaeftsmodell_evolution",
    "vision_3_jahre", "strategische_ziele", "ki_guardrails",
}

# Freitext-Felder, die im Fast-Mode-Formular auftauchen können
# (Block B + C; hauptleistung ist Phase-1-Pflicht und nie offen)
FT_FASTMODE_FIELDS = {
    "ki_projekte", "geschaeftsmodell_evolution", "vision_3_jahre",
    "strategische_ziele", "ki_guardrails",
    "zeitersparnis_prioritaet", "top_zeitfresser",
}


class TestFieldQuestionsEnParity:

    def test_same_keys_as_de(self):
        assert set(FIELD_QUESTIONS_EN) == set(FIELD_QUESTIONS), (
            "FIELD_QUESTIONS_EN muss exakt die Schlüssel von "
            "FIELD_QUESTIONS spiegeln (DE/EN-Parität)."
        )

    def test_en_questions_nonempty_and_question_shaped(self):
        for field, q in FIELD_QUESTIONS_EN.items():
            assert q and q.strip(), f"{field}: leerer EN-Fragetext"
            assert "?" in q, f"{field}: EN-Text ist keine Frage: {q!r}"

    def test_en_questions_contain_no_german_artifacts(self):
        # Grobe Heuristik gegen kopierte DE-Texte (Umlaute/ß und
        # häufige deutsche Funktionswörter als eigenes Wort).
        german_words = {"Sie", "Ihr", "Ihre", "und", "oder", "nicht", "wie"}
        for field, q in FIELD_QUESTIONS_EN.items():
            assert not any(ch in q for ch in "äöüÄÖÜß"), (
                f"{field}: Umlaut im EN-Text: {q!r}"
            )
            words = set(q.replace("—", " ").replace("?", " ").split())
            assert not (words & german_words), (
                f"{field}: deutsches Wort im EN-Text: {q!r}"
            )

    def test_durchschnittshonorar_absent_in_both(self):
        # KIS-1240: Honorar-Frage darf nie wieder gestellt werden
        assert "durchschnittshonorar" not in FIELD_QUESTIONS
        assert "durchschnittshonorar" not in FIELD_QUESTIONS_EN


class TestSonnetGateUnchanged:

    def test_ft_fields_present_for_fast_mode(self):
        for field in FT_SONNET_FIELDS - {"hauptleistung"}:
            assert field in FIELD_QUESTIONS, (
                f"{field}: Fast-Mode braucht einen DE-Fragetext mit Hinweis "
                f"(vorher erschien nur das Label)."
            )
            assert field in FIELD_QUESTIONS_EN

    def test_template_mode_still_gated(self):
        # Chat-Template-Mode bleibt für Sonnet-Felder aus — DE und EN.
        for field in FT_SONNET_FIELDS:
            assert not is_template_field(field)
            assert get_template_question(field) is None
            assert get_template_question_en(field) is None

    def test_template_question_en_serves_qr_fields(self):
        assert get_template_question_en("investitionsbudget")
        assert get_template_question_en("zeitersparnis_prioritaet")
        assert get_template_question_en("top_zeitfresser")

    def test_ja_nein_framing_matches_chips(self):
        # KIS-1264/1268: Chips beginnen mit "Ja, …" / "Eher nein, …" —
        # die Frage muss als Könnte-KI-Frage gestellt sein (DE + EN).
        assert FIELD_QUESTIONS["geschaeftsmodell_evolution"].startswith("Könnte KI")
        assert FIELD_QUESTIONS_EN["geschaeftsmodell_evolution"].startswith("Could AI")


class TestFastModeQuestionCoverage:

    def test_all_fastmode_ft_fields_have_hint_questions(self):
        for field in FT_FASTMODE_FIELDS:
            for reg, name in ((FIELD_QUESTIONS, "DE"), (FIELD_QUESTIONS_EN, "EN")):
                q = reg.get(field, "")
                assert q and "?" in q, (
                    f"{field} ({name}): Fast-Mode-Frage fehlt oder ist "
                    f"keine Frage — Nutzer sähe nur das Label."
                )

    def test_fast_mode_en_uses_field_questions_en(self):
        # Wiring-Pin (Stil wie test_kis1243): EN-Zweig des Fast-Mode
        # bevorzugt FIELD_QUESTIONS_EN vor dem Label-Fallback.
        src = open("routes/chat.py", encoding="utf-8").read()
        idx = src.find("def get_fast_mode_fields")
        assert idx != -1
        block = src[idx:idx + 3500]
        assert "FIELD_QUESTIONS_EN.get(field)" in block
        assert "_QR_LABELS_EN.get(field)" in block

    def test_en_fallbacks_use_template_question_en(self):
        # Leere-Antwort-Guard + Frage-Garantie nutzen die native EN-Frage
        # statt (nur) des generischen "Next up: <label>"-Satzes.
        src = open("routes/chat.py", encoding="utf-8").read()
        assert src.count("get_template_question_en(next_fields[0])") >= 2


class TestFieldDescriptionsMedien:

    def test_medien_sparte_description_present_with_freetext_invite(self):
        from services.chat_conversation import FIELD_DESCRIPTIONS
        desc = FIELD_DESCRIPTIONS.get("medien_sparte", "")
        assert desc, "medien_sparte fehlt in FIELD_DESCRIPTIONS (Re-Ask-Kontext)"
        # Muster der KIS-1277-Sparten-Frage: Freitext explizit einladen
        assert "eigenen Worten" in desc
        assert "Optional" in desc

    def test_ki_hemmnisse_has_medien_examples(self):
        from services.chat_conversation import FIELD_DESCRIPTIONS
        desc = FIELD_DESCRIPTIONS["ki_hemmnisse"]
        assert "Medien:" in desc
        assert "Urheberrecht" in desc
