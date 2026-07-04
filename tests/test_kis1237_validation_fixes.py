# -*- coding: utf-8 -*-
"""KIS-1237: Befunde aus der KIS-1236-PDF-Validierung (Lauf 1119, Bildung/KMU).

1. Chat: contradiction_acks überlebten Draft-Resets nicht — der Live-Abgleich
   („Kurzer Abgleich: …") wurde nach jedem QR-Klick erneut angehängt.
2. R1: Spannungs-Box + AI-Act-Fristen-Box gingen an Sektionen, die
   pdf_template_v7 nie rendert (UNTERNEHMENSPROFIL_MARKT_HTML /
   AI_ACT_SUMMARY_HTML) — Injektion umgezogen auf gerenderte Slots.
3. Spannungs-Box zeigte rohen Budget-Enum „(2000_10000)".
4. Vendor-Karten zeigten rohe englische Werte (US/RED/Medium/high).
5. Briefing-PDF: rohe FB2-Keys, „True" statt „Ja", Kommas ohne Leerzeichen,
   „50.0h/Monat" statt „50 h/Monat".
6. Exec-Förder-Box nannte KOMPASS (Solo-Programm) im KMU-Lauf — Programm
   stand nie in Kapitel 7.
7. Doppelte „Kernprogramme…"-Überschrift ohne Inhalt im Final-HTML.
"""
from __future__ import annotations

import re


# =========================================================================
# 1. Chat: Acks überleben Draft-Resets
# =========================================================================

class TestClearedDraftPreservesAcks:

    def test_acks_preserved_pending_cleared(self):
        from routes.chat import _cleared_draft
        out = _cleared_draft({
            "pending_field": "branche", "pending_value": "it",
            "dialog_mode": True, "contradiction_acks": ["budget", "tools"],
        })
        assert out["pending_field"] is None
        assert out["pending_value"] is None
        assert out["dialog_mode"] is False
        assert out["contradiction_acks"] == ["budget", "tools"]

    def test_none_and_empty_input(self):
        from routes.chat import _cleared_draft
        assert _cleared_draft(None) == {
            "pending_field": None, "pending_value": None, "dialog_mode": False,
        }
        assert "contradiction_acks" not in _cleared_draft({})

    def test_no_bare_reset_literals_left(self):
        """Jeder Draft-Reset muss über _cleared_draft laufen — ein nacktes
        Reset-Literal würde die Acks wieder löschen. Erlaubt ist genau das
        eine Literal im Helper selbst."""
        src = open("routes/chat.py", encoding="utf-8").read()
        literal = '{"pending_field": None, "pending_value": None, "dialog_mode": False}'
        assert src.count(literal) == 1

    def test_raw_sql_write_never_writes_empty_dict(self):
        src = open("routes/chat.py", encoding="utf-8").read()
        assert '"ds": _draft_for_sql or json.dumps({})' not in src
        assert '"ds": _draft_for_sql,' in src


# =========================================================================
# 2. R1-Injektionen auf gerenderte Template-Slots
# =========================================================================

class TestRenderedSlotInjection:

    def test_spannungsbox_targets_score_interpretation_first(self):
        src = open("gpt_analyze.py", encoding="utf-8").read()
        idx = src.find('for _sp_slot in ("SCORE_INTERPRETATION_HTML",')
        assert idx != -1, "Spannungs-Box muss SCORE_INTERPRETATION_HTML priorisieren"

    def test_deadline_box_targets_duty_matrix(self):
        src = open("gpt_analyze.py", encoding="utf-8").read()
        assert 'sections.get("AI_ACT_DUTY_MATRIX_HTML")' in src
        assert "AI-Act-Fristen-Box in AI_ACT_DUTY_MATRIX_HTML injiziert" in src

    def test_template_renders_target_slots(self):
        tpl = open("templates/pdf_template_v7.html", encoding="utf-8").read()
        assert "SCORE_INTERPRETATION_HTML" in tpl
        assert "AI_ACT_DUTY_MATRIX_HTML" in tpl
        # Die alten Ziele rendert das Template nicht — deshalb der Umzug.
        assert "UNTERNEHMENSPROFIL_MARKT_HTML" not in tpl
        assert "AI_ACT_SUMMARY_HTML" not in tpl


# =========================================================================
# 3. Budget-Enum in der Spannungs-Box
# =========================================================================

class TestBudgetEnumFormatting:

    def test_fmt_budget_range(self):
        from services.briefing_contradictions import _fmt_budget
        assert _fmt_budget("2000_10000") == "2.000–10.000 €"
        assert _fmt_budget("10000_50000") == "10.000–50.000 €"

    def test_fmt_budget_open_ranges_and_passthrough(self):
        from services.briefing_contradictions import _fmt_budget
        assert _fmt_budget("unter_2000") == "unter 2.000 €"
        assert _fmt_budget("ueber_50000") == "über 50.000 €"
        assert _fmt_budget("2.000–10.000 €") == "2.000–10.000 €"

    def test_box_uses_formatted_budget(self):
        from services.briefing_contradictions import build_contradictions_box_html
        html = build_contradictions_box_html({
            "groesster_engpass": "Kein Budget",
            "investitionsbudget": "2000_10000",
        })
        assert "2.000–10.000 €" in html
        assert "2000_10000" not in html


# =========================================================================
# 4. Vendor-Karten: deutsche Statuswerte
# =========================================================================

class TestVendorGermanLabels:

    def _entry_html(self):
        from services.vendor_audit_engine import (
            VendorAuditEntry, VendorAuditReport, vendor_audit_report_to_html,
        )
        entry = VendorAuditEntry(
            name="Claude (Anthropic)", category="LLM",
            jurisdiction="US", data_location="US", has_dpa=True,
            security_posture="medium", ai_act_relevance="high",
            vendor_risk_score=4,
        )
        report = VendorAuditReport(entries=[entry], summary="Test")
        return vendor_audit_report_to_html(report, lang="de")

    def test_no_raw_english_badges(self):
        html = self._entry_html()
        assert "USA" in html
        assert ">RED<" not in html and "RED —" not in html
        assert "ROT — hohes Risiko" in html
        assert "AI Act Relevanz: hoch" in html or "AI-Act-Relevanz: hoch" in html
        assert re.search(r"🔒\s*Mittel", html)


# =========================================================================
# 5. Briefing-PDF: Labels + Werte-Formatierung
# =========================================================================

class TestBriefingPdfFormatting:

    def test_smoat_labels_registered(self):
        from services.email_templates import _STRATEGY_LABELS
        assert _STRATEGY_LABELS["wettbewerber_anzahl"] == "Wettbewerber (Anzahl)"
        assert _STRATEGY_LABELS["kundenbindung_typ"] == "Kundenbindung"
        assert _STRATEGY_LABELS["datenreife"] == "Datenreife"

    def test_format_value_string_booleans(self):
        from services.email_templates import _format_value
        assert _format_value("True") == "Ja"
        assert _format_value("false") == "Nein"
        assert _format_value(True) == "Ja"

    def test_format_value_comma_spacing(self):
        from services.email_templates import _format_value
        out = _format_value("ChatGPT / OpenAI,Claude / Anthropic,Perplexity")
        assert "OpenAI, Claude" in out
        assert "Anthropic, Perplexity" in out

    def test_briefing_pdf_german_numbers(self):
        from services.email_templates import render_briefing_pdf_html
        html = render_briefing_pdf_html(
            display_id="KIS-9999",
            datum="04.07.2026 10:00",
            answers={"branche": "bildung", "unternehmensgroesse": "kmu"},
            scores={"overall": 87},
            sections={
                "CANON_HOURS_MONTH": "50.0", "CANON_RATE_EUR": "110",
                "ROI_12M": "22.5", "PAYBACK_MONTHS": "9,8",
            },
        )
        assert "50.0" not in html
        assert "22,5%" in html
        assert "22.5" not in html


# =========================================================================
# 6. KOMPASS raus aus der Exec-Förder-Box
# =========================================================================

class TestExecFundingBoxNeutral:

    def test_no_kompass_in_strategy_renderer(self):
        import inspect
        from services import strategy_renderer
        src = inspect.getsource(strategy_renderer)
        assert "KOMPASS" not in src


# =========================================================================
# 7. Verwaiste Kernprogramme-Zweitüberschrift
# =========================================================================

class TestOrphanFundingHeading:

    def test_final_pass_removes_orphan_heading(self):
        src = open("services/report_renderer.py", encoding="utf-8").read()
        assert "KIS-1237][FOERDER-HEADING" in src
        # Regel: Zweitüberschrift ohne Tabelle in Reichweite wird entfernt
        assert '"<table" not in _lookahead' in src

    def test_orphan_heading_regex_behaviour(self):
        """Repliziert die Finalpass-Logik auf einem Mini-Dokument."""
        _kp_pat = re.compile(
            r'<h3[^>]*>(?:(?!</h3>).)*?Kernprogramme\s+für\s+Ihr\s+Profil(?:(?!</h3>).)*?</h3>\s*',
            re.DOTALL,
        )
        html = (
            '<h3>Kernprogramme für Ihr Profil (2025/2026)</h3>'
            '<table><tr><td>BAFA</td></tr></table>'
            '<div><strong>Hinweis:</strong> …</div>'
            '<h3>Kernprogramme für Ihr Profil (2025/2026)</h3>'
            '<p>Weiterer Text ohne Tabelle</p>'
        )
        matches = list(_kp_pat.finditer(html))
        assert len(matches) == 2
        for m in reversed(matches[1:]):
            if "<table" not in html[m.end():m.end() + 800]:
                html = html[:m.start()] + html[m.end():]
        assert html.count("Kernprogramme") == 1
        assert "<table" in html
