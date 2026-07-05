# -*- coding: utf-8 -*-
"""KIS-1248/1249: Restbefunde aus Lauf KIS-1238 + Platin+++-QA-Gate Stufe 1.

Befunde der drei parallelen PDF-Prüfungen (Status 37 S., Strategie 43 S.,
KPA + 2 Briefings): hartkodierte 120-€-OPEX-Box, Dedup-Lücken
(Hauptsystem-Varianten, Vendor-Disclaimer 6×, „KI (künstliche Intelligenz)"
2×), englische Badge-Reste, Briefing-Formatlücken (Bindestrich-Ranges,
s1_budget ohne €, Komma-Spacing), strichlose th-Umbrüche, Score 78 vs. 80.
"""
from __future__ import annotations


def _read(path: str) -> str:
    return open(path, encoding="utf-8").read()


# =========================================================================
# Dedup-Erweiterung (Strategie)
# =========================================================================

class TestDedupExtension:

    def test_hauptsystem_pattern_generalized(self):
        src = _read("services/strategy_renderer.py")
        assert "nicht als Hauptsystem[^<>.!?]{0,200}[.!?]" in src

    def test_ki_explanation_and_vendor_disclaimer_capped(self):
        src = _read("services/strategy_renderer.py")
        idx = src.find("KIS-1248: Weitere Wiederholungs-Klassen")
        assert idx != -1
        block = src[idx:idx + 1600]
        assert "_ki_pat" in block and "_va_pat" in block
        assert "Vendor-Audit-Status" in block
        assert "_va_matches[2:]" in block  # Disclaimer-Cap: 2


# =========================================================================
# Badge-Eindeutschung
# =========================================================================

class TestBadgeLocalization:

    def test_badges_and_slug(self):
        from services.content_quality_enforcer import apply_badge_localization
        s = {"X": "ESSENTIAL · ANALYSIS · AI-ACT RISIKO limited · "
                  "Komplexität: low · KMU/Bau/KI-Anwender"}
        out = apply_badge_localization(s)["X"]
        assert "UNVERZICHTBAR" in out
        assert "ANALYSE" in out
        assert "RISIKO begrenzt" in out
        assert "Komplexität: niedrig" in out
        assert "KMU · Bau · KI-Anwender" in out

    def test_proper_names_untouched(self):
        from services.content_quality_enforcer import apply_badge_localization
        s = {"X": "Der Anbieter DeepL Limited bietet Analysis-Funktionen."}
        assert apply_badge_localization(s)["X"] == s["X"] or "Limited" in apply_badge_localization(s)["X"]


# =========================================================================
# Briefing-Formatter-Lücken
# =========================================================================

class TestBriefingFormatterGaps:

    def test_hyphen_range_gets_unit(self):
        from services.email_templates import _prettify_enum_value
        # Lauf 1238: "51-80" blieb einheitenlos, weil das Enum-Gate
        # Bindestriche ablehnte.
        out = _prettify_enum_value("51-80", "prozesse_papierlos").replace("\u00a0", " ")
        assert out == "51–80 %"
        out2 = _prettify_enum_value("2000-10000", "s1_budget").replace("\u00a0", " ")
        assert out2 == "2000–10000 €"

    def test_hyphen_untouched_without_unit_field(self):
        from services.email_templates import _prettify_enum_value
        assert _prettify_enum_value("2026-07") == "2026-07"

    def test_comma_join_gets_spacing(self):
        from services.email_templates import _prettify_enum_value
        out = _prettify_enum_value("ChatGPT / OpenAI,Claude / Anthropic,Perplexity")
        assert out == "ChatGPT / OpenAI, Claude / Anthropic, Perplexity"

    def test_strategy_rows_pass_field(self):
        src = _read("services/email_templates.py")
        assert "_prettify_enum_value(val, key)" in src
        idx = src.find("KIS-1248: field durchreichen")
        assert idx != -1


# =========================================================================
# OPEX-Box, Score-Sync, th-Umbruch, Trenn-Schwelle
# =========================================================================

class TestRemainingFixes:

    def test_no_hardcoded_120_opex(self):
        src = _read("services/strategy_renderer.py")
        assert "120 €/Monat" not in src
        assert "KI-Status-Report" not in src

    def test_briefing_uses_canonical_overall(self):
        src = _read("gpt_analyze.py")
        idx = src.find("KIS-1248: Das Briefing-Dossier zeigte den Pre-Bonus-Score")
        assert idx != -1
        assert "CANONICAL_OVERALL" in src[idx:idx + 700]

    def test_th_no_mid_word_break(self):
        src = _read("templates/strategy_report.html")
        assert "th { hyphens: none; overflow-wrap: normal; word-break: keep-all; }" in src

    def test_soft_hyphen_threshold_raised(self):
        # "Selbstbetrieb"/"Dienstleister" (13) bekamen falsche Trennstellen —
        # weich getrennt wird erst ab 14 Zeichen.
        from services.style_lint import _LONG_WORD_RE
        assert not _LONG_WORD_RE.search("Selbstbetrieb")
        assert not _LONG_WORD_RE.search("Dienstleister")
        assert _LONG_WORD_RE.search("Rechercheassistent")


# =========================================================================
# Platin+++ Stufe 1: QA-Gate
# =========================================================================

class TestPlatinQaGate:

    def test_clean_report_yields_zero_findings(self):
        from services.platin_qa import scan_sections
        s = {"EXECUTIVE_SUMMARY_HTML": "<p>Ein sauberer Absatz mit Substanz und ROI von 22 %.</p>"}
        assert scan_sections(s, {}) == []

    def test_detects_collapsed_kpi(self):
        from services.platin_qa import scan_sections
        s = {"KI_STACK_SUMMARY_HTML": "<p>ROI8 %nach 12 Monaten Break-Even11,1 Monate</p>"}
        types = {f["type"] for f in scan_sections(s, {})}
        assert "collapsed_kpi" in types

    def test_detects_name_leak(self):
        from services.platin_qa import scan_sections
        s = {"EXECUTIVE_SUMMARY_HTML": "<p>Die Musterbau GmbH plant KI-Einsatz im großen Stil.</p>"}
        types = {f["type"] for f in scan_sections(s, {"unternehmen_name": "Musterbau GmbH"})}
        assert "name_leak" in types

    def test_detects_raw_bool_and_badge_and_snake(self):
        from services.platin_qa import scan_sections
        s = {"A": "<p>Datenschutz: True — Badge ESSENTIAL — Feld projekte_pro_monat sichtbar.</p>"}
        types = {f["type"] for f in scan_sections(s, {})}
        assert {"raw_boolean", "english_badge", "visible_snake_case"} <= types

    def test_detects_truncated_tail_and_dsgvo_cap(self):
        from services.platin_qa import scan_sections
        s = {
            "A": "<p>Format: Executive Summary (max.</p>",
            "B": "<p>x (DSGVO-Vorbehalt 1) y (DSGVO-Vorbehalt 2) z (DSGVO-Vorbehalt 3)</p>",
        }
        types = {f["type"] for f in scan_sections(s, {})}
        assert "truncated_text" in types
        assert "dsgvo_cap" in types

    def test_internal_keys_skipped(self):
        from services.platin_qa import scan_sections
        s = {"_risk_report": "<p>status: True ESSENTIAL projekte_pro_monat</p>"}
        assert scan_sections(s, {}) == []

    def test_run_wrapper_stores_findings_and_never_raises(self):
        from services.platin_qa import run_platin_qa
        s = {"A": "<p>Datenschutz: True</p>"}
        findings = run_platin_qa(s, {}, run_id="test")
        assert s["_PLATIN_QA_FINDINGS"] == findings
        assert findings and findings[0]["type"] == "raw_boolean"

    def test_gate_hooked_at_pipeline_end(self):
        # KIS-1251: Der Scan lief anfangs VOR hard_stop/Quality-Enforcer und
        # meldete Timing-Artefakte (english_badge, die Badge-L10N später
        # heilte). Er misst jetzt den Auslieferungszustand: NACH dem
        # Hard-Stop und dem finalen Quality-Enforcer, direkt vor render().
        src = _read("gpt_analyze.py")
        idx_qa = src.find("run_platin_qa(sections, answers, run_id=run_id)")
        idx_hs = src.find("hard_stop_if_invalid(sections, error_gate, persona=persona, run_id=run_id)")
        idx_qe = src.find("[QUALITY-ENFORCER-RENDER] Applied FINAL quality fixes")
        idx_render = src.find("result = render(")
        assert idx_qa != -1 and idx_hs != -1 and idx_qe != -1 and idx_render != -1
        assert idx_hs < idx_qa, "QA-Scan muss NACH dem Hard-Stop laufen"
        assert idx_qe < idx_qa, "QA-Scan muss NACH dem finalen Quality-Enforcer laufen"
        assert idx_qa < idx_render, "QA-Scan muss VOR render() laufen"
