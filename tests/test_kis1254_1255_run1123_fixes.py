# -*- coding: utf-8 -*-
"""KIS-1254/1255: Befunde aus Lauf 1123 (PDF-Review + Platin-QA + Judge)
und Fragebogen-Feedback.

KIS-1254 (Report): (1) ROI-Filter zerriss Sätze („Der ausgewiesene → siehe
Business Case nach 12 Monaten basiert …"); (2) Badge-Eindeutschung griff
nicht über Tag-Grenzen („Komplexität: <span>low</span>"); (3) DSGVO-Cap
lief vor dem Quick-Wins-Pristine-Restore → 4 statt 2 Vorkommen;
(4) 'vision_prioritaet' roh im Leistungsnachweis; (5) Judge-Gelb: derselbe
Satz 3× nahezu wortgleich; (6) Tabellenkopf-Kollisionen + Orphan-Header.

KIS-1255 (Fragebogen): (7) „Projekt"-Sprache branchenneutral;
(8) Doppelter „Auswertung starten"-Button nach Report-Start.
"""
from __future__ import annotations


def _read(path: str) -> str:
    return open(path, encoding="utf-8").read()


# =========================================================================
# 1. ROI-Filter bleibt grammatisch
# =========================================================================

class TestRoiFilterGrammatical:

    def test_mid_sentence_replacement_keeps_noun(self):
        from services.content_quality_enforcer import remove_roi_from_section
        html = ("<p>Der ausgewiesene ROI von 22 % nach 12 Monaten basiert "
                "auf dem vollen Eigenanteil und steigt mit Förderung.</p>")
        out, n = remove_roi_from_section(html, "FOERDERPOTENZIAL_HTML")
        assert n >= 1
        assert "22" not in out
        # Satz bleibt lesbar: Substantiv + Verweis statt Pfeil-Fragment
        assert "Der ausgewiesene ROI (siehe Business Case) nach 12 Monaten basiert" in out
        assert "→ siehe Business Case nach" not in out

    def test_rendite_variant(self):
        from services.content_quality_enforcer import remove_roi_from_section
        out, n = remove_roi_from_section(
            "<p>Das ergibt eine Rendite von 180 % im Modell.</p>", "RISKS_HTML")
        assert n == 1
        assert "Rendite (siehe Business Case)" in out

    def test_business_case_untouched(self):
        from services.content_quality_enforcer import remove_roi_from_section
        html = "<p>ROI von 22 % nach 12 Monaten.</p>"
        assert remove_roi_from_section(html, "BUSINESS_CASE_HTML") == (html, 0)


# =========================================================================
# 2. Badge-Eindeutschung über Tag-Grenzen + Quelle im Starter-Kit
# =========================================================================

class TestBadgeAcrossTags:

    def test_complexity_value_in_own_span(self):
        from services.content_quality_enforcer import apply_badge_localization
        s = {"STARTER_KIT_HTML":
             '<div>Programm | Komplexität: <span style="color:#22c55e;">low</span> und mehr Kontext dazu.</div>'}
        out = apply_badge_localization(s)["STARTER_KIT_HTML"]
        assert ">niedrig<" in out
        assert ">low<" not in out

    def test_starter_kit_renders_german_at_source(self):
        src = _read("services/tools_starter_kits.py")
        assert "complexity_label" in src
        assert '"low": "niedrig"' in src


# =========================================================================
# 3. DSGVO-Cap nach Quick-Wins-Restore
# =========================================================================

class TestDsgvoCapAfterRestore:

    def test_recap_hooked_after_pristine_restore(self):
        src = _read("gpt_analyze.py")
        idx_restore = src.find("[FIX-R3-5B] Restoring pristine QW HTML")
        idx_recap = src.find("[KIS-1254][DSGVO-VORBEHALT-R2]")
        assert idx_restore != -1 and idx_recap != -1
        assert idx_recap > idx_restore
        # und VOR dem Platin-QA-Scan am Pipeline-Ende
        idx_qa = src.find("run_platin_qa(sections, answers, run_id=run_id)")
        assert idx_recap < idx_qa


# =========================================================================
# 4. Coverage-Box zeigt deutsche Labels statt snake_case
# =========================================================================

class TestCoverageLabels:

    def test_known_field_gets_label(self):
        from services.coverage_guard import build_html_report
        out = build_html_report({"missing": ["vision_prioritaet"],
                                 "coverage_pct": 90, "present_count": 40})
        assert "vision_prioritaet" not in out
        assert "<code>" not in out

    def test_unknown_field_fallback_readable(self):
        from services.coverage_guard import _field_label
        assert "_" not in _field_label("irgendein_neues_feld")


# =========================================================================
# 5. Satz-Dubletten-Cap (Judge-Befund)
# =========================================================================

class TestSentenceCap:

    _S = ("Die Automatisierung der Belegerfassung und Kassenabschlüsse "
          "entlastet den größten Zeitfresser in Ihrer Buchhaltung spürbar "
          "und schafft Kapazität für das Kerngeschäft.")

    def _pad(self, text):
        return "<p>" + "Zusätzlicher individueller Kontext dieser Sektion. " * 5 + text + "</p>"

    def test_third_occurrence_removed(self):
        from services.content_quality_enforcer import cap_repeated_sentences
        s = {
            "RECOMMENDATIONS_HTML": self._pad(self._S),
            "ADVISOR_NOTE_HTML": self._pad(self._S),
            "TOOLS_EMPFEHLUNGEN_HTML": self._pad(self._S),
        }
        out = cap_repeated_sentences(s)
        total = sum(v.count("entlastet den größten Zeitfresser") for v in out.values())
        assert total == 2

    def test_two_occurrences_untouched(self):
        from services.content_quality_enforcer import cap_repeated_sentences
        s = {
            "RECOMMENDATIONS_HTML": self._pad(self._S),
            "ADVISOR_NOTE_HTML": self._pad(self._S),
        }
        before = dict(s)
        assert cap_repeated_sentences(s) == before

    def test_shadow_aliases_not_counted(self):
        from services.content_quality_enforcer import cap_repeated_sentences
        # UPPER + lowercase-Zwilling = EIN sichtbares Vorkommen, kein Doppel
        s = {
            "RECOMMENDATIONS_HTML": self._pad(self._S),
            "recommendations": self._pad(self._S),
            "ADVISOR_NOTE_HTML": self._pad(self._S),
        }
        out = cap_repeated_sentences(s)
        assert out["RECOMMENDATIONS_HTML"].count("entlastet den größten") == 1
        assert out["ADVISOR_NOTE_HTML"].count("entlastet den größten") == 1

    def test_short_sentences_ignored(self):
        from services.content_quality_enforcer import cap_repeated_sentences
        short = "<p>" + ("Das ist ein kurzer Satz. " * 10) + "</p>"
        s = {"A_HTML": short * 1, "B_HTML": short, "C_HTML": short}
        before = dict(s)
        assert cap_repeated_sentences(s) == before


# =========================================================================
# 6. Tabellenkopf: <thead>-Wrapping + Soft-Hyphens im th
# =========================================================================

class TestTableHeaders:

    def test_ensure_thead_wraps_first_th_row(self):
        from services.html_enhancer import _ensure_thead
        html = ('<table class="table"><tr><th>Risiko</th><th>Mitigationsstrategie</th></tr>'
                '<tr><td>X</td><td>Y</td></tr></table>')
        out = _ensure_thead(html)
        assert "<thead><tr><th>" in out
        assert out.count("<thead") == 1

    def test_existing_thead_untouched(self):
        from services.html_enhancer import _ensure_thead
        html = "<table><thead><tr><th>A</th></tr></thead><tbody><tr><td>1</td></tr></tbody></table>"
        assert _ensure_thead(html) == html

    def test_th_words_from_run_1123_get_soft_hyphens(self):
        from services.style_lint import soften_table_long_words
        html = ("<table><tr><th>Zielkonflikt</th><th>Mitigationsstrategie</th>"
                "<th>Handlungsfeld</th></tr><tr><td>ok</td><td>ok</td><td>ok</td></tr></table>")
        out, n = soften_table_long_words(html)
        assert n >= 3
        assert "­" in out.split("</tr>")[0]  # Soft-Hyphen im Kopf

    def test_short_th_words_untouched(self):
        from services.style_lint import soften_table_long_words
        html = "<table><tr><th>Risiko</th><th>Impact</th></tr></table>"
        out, _ = soften_table_long_words(html)
        assert "­" not in out

    def test_boxes_keep_together(self):
        assert "break-inside:avoid" in _read("services/vendor_audit_engine.py")
        assert "break-inside: avoid" in _read("templates/pdf_template_v7.html")


# =========================================================================
# 7. KIS-1255: branchenneutrale Fragebogen-Sprache
# =========================================================================

class TestNeutralWording:

    def test_projekte_question_neutral(self):
        from services.field_templates import FIELD_QUESTIONS
        q = FIELD_QUESTIONS["projekte_pro_monat"]
        assert "Aufträge oder Vorgänge" in q
        assert "Bestellungen" in q  # Beispiel statt Voraussetzung

    def test_zeitfresser_chip_neutral(self):
        from services.field_templates import FIELD_EXAMPLES
        chips = FIELD_EXAMPLES["top_zeitfresser"]
        assert not any("Projektabschluss" in c for c in chips)

    def test_labels_neutralized(self):
        from services.email_templates import _R1_LABELS
        assert _R1_LABELS["projekte_pro_monat"] == "Aufträge/Projekte pro Monat"

    def test_branch_language_rule_in_chat_prompt(self):
        src = _read("services/chat_conversation.py")
        assert "BRANCHENGERECHTE SPRACHE" in src
        idx = src.find("BRANCHENGERECHTE SPRACHE")
        block = src[idx:idx + 900]
        assert "Gastronomie" in block
        assert "projektbasiert" in block


# =========================================================================
# 8. KIS-1255: kein Doppel-Button nach Report-Start
# =========================================================================

class TestNoDoubleStartButton:

    def test_backend_suppresses_summary_qrs_after_start(self):
        # Beide Summary-Zweige (r1 + Strategie) tragen den Guard direkt in
        # der Bedingung — nach "Auswertung starten" werden die
        # __summary_action__-Buttons nicht erneut gesendet.
        src = _read("routes/chat.py")
        assert ('elif _final_phase == "summary" and not _report_start_requested'
                in src)
        assert ('elif _strategy_completion_ready and not _report_start_requested'
                in src)
