# -*- coding: utf-8 -*-
"""KIS-1318 — Feedback-Mail lesbar. Wolfs erstes Formular-Feedback (06.09.2026,
KIS-1287) kam als Textwand mit Codes („yes_interested", „quick_wins", „kmu")
und ohne die Felder `tools_adopted` und `funding_applied` aus KIS-1281.
Jetzt: Labels wie im Formular, Balken für Bewertungen, HTML-Fassung, Betreff
mit Note und Report-Nummer."""
from __future__ import annotations

import re

from services.feedback import (
    _LABELS,
    _build_notification_body,
    build_feedback_subject,
    build_notification_html,
)

PAYLOAD = {
    "email": "wolf@hohl.rocks", "briefing_id": 1170, "type": "form_feedback",
    "overall_helpfulness_score": 6, "report_relevance_rating": 3, "ux_clarity_rating": 4,
    "ux_effort_rating": 2, "ux_required_fields": "ok",
    "report_helpful_sections": ["quick_wins", "funding"], "report_goals_visible": "3",
    "report_guardrails_used": "yes", "branch_feedback": "medien", "company_size_feedback": "kmu",
    "tools_adopted": "Amberscript, DaVinci", "funding_applied": "",
    "payment_willingness": "yes_interested", "training_interest": "interested", "contact_permission": "yes",
    "report_comment": "", "ux_comment": "", "final_comment": "Sehr gut <3",
    "test_reference": "Motion-Profil", "report_version": "v14",
}
TS = "2026-09-06T13:10:40.897628+00:00"


class TestBetreff:
    def test_note_und_kis(self):
        assert build_feedback_subject(PAYLOAD, "form_feedback") == "[KI-Sicherheit] Feedback · 6/10 · KIS-1287 · wolf@hohl.rocks"

    def test_ohne_note(self):
        assert build_feedback_subject({"email": "a@b.de"}, "form_feedback") == "[KI-Sicherheit] Feedback · a@b.de"
        assert build_feedback_subject({"email": "a@b.de"}, "waitlist_training") == "[KI-Sicherheit] Schulungs-Warteliste: a@b.de"


class TestText:
    def test_labels_statt_codes(self):
        t = _build_notification_body(PAYLOAD, "form_feedback", TS)
        assert "Ja, grundsätzlich interessant" in t and "yes_interested" not in t
        assert "Quick Wins, Fördermöglichkeiten" in t and "quick_wins" not in t
        assert "KMU (11–100)" in t and "Medien & Kreativwirtschaft" in t
        assert "KIS-1287 (Briefing 1170)" in t and "06.09.2026, 13:10 Uhr UTC" in t

    def test_neue_felder_und_balken(self):
        t = _build_notification_body(PAYLOAD, "form_feedback", TS)
        assert "Werkzeuge übernommen:" in t and "Amberscript, DaVinci" in t
        assert "Förderung beantragt:" in t and "—" in t
        assert "6/10  ●●●●●●○○○○" in t and "2/5  ●●○○○" in t
        assert "Testreferenz:" in t and "Motion-Profil" in t
        assert "=====" not in t

    def test_freitext_nur_wenn_vorhanden(self):
        t = _build_notification_body(PAYLOAD, "form_feedback", TS)
        assert "Abschluss: Sehr gut <3" in t and "Zum Report:" not in t
        leer = {**PAYLOAD, "final_comment": " "}
        assert "Keine Freitexte." in _build_notification_body(leer, "form_feedback", TS)

    def test_warteliste(self):
        t = _build_notification_body({"email": "a@b.de"}, "waitlist_training", TS)
        assert t.startswith("Neue Anmeldung zur Schulungs-Warteliste") and "a@b.de" in t


class TestHtml:
    def test_struktur(self):
        h = build_notification_html(PAYLOAD, "form_feedback", TS)
        assert "<h3" in h and h.count("<table") == 4
        assert "Kontakt erlaubt" in h and "●●●●●●○○○○" in h
        assert "Sehr gut &lt;3" in h  # escaped
        assert "Werkzeuge übernommen" in h and "Amberscript, DaVinci" in h
        assert "http" not in h  # keine externen Ressourcen

    def test_ohne_kontakt_kein_banner(self):
        h = build_notification_html({**PAYLOAD, "contact_permission": "no"}, "form_feedback", TS)
        assert "Kontakt erlaubt —" not in h and "Nein, danke" in h

    def test_unbekannter_code_bleibt_sichtbar(self):
        h = build_notification_html({**PAYLOAD, "payment_willingness": "neu_xyz"}, "form_feedback", TS)
        assert "neu_xyz" in h


class TestLabelsWieImFormular:
    def test_alle_optionen_des_formulars(self):
        # Spiegel von make-ki-frontend/feedback/feedback.html — wer dort eine
        # Option ergänzt, ergänzt sie hier.
        assert set(_LABELS["payment_willingness"]) == {"yes_interested", "yes_if_deductible", "not_really", "need_info"}
        assert set(_LABELS["training_interest"]) == {"urgent", "interested", "need_info", "no"}
        assert set(_LABELS["report_helpful_sections"]) == {"quick_wins", "roadmap", "compliance", "funding", "summary", "other"}
        assert set(_LABELS["branch_feedback"]) == {"beratung", "it", "medien", "handel", "industrie", "sonstige"}
        assert set(_LABELS["company_size_feedback"]) == {"solo", "small_team", "kmu", "larger"}
        assert set(_LABELS["report_guardrails_used"]) == {"yes", "no", "not_used"}
        assert set(_LABELS["ux_required_fields"]) == {"ok", "too_many", "too_few", "unsure"}
        for mapping in _LABELS.values():
            for v in mapping.values():
                assert v and not re.search(r"_", v)
