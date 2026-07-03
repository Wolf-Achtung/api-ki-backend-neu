# -*- coding: utf-8 -*-
"""KIS-1235 PR C: Render & Verlässlichkeit.

Befunde aus dem Validierungslauf 1235 (Solo/Beratung/Berlin):
1. Vendor-Audit prüfte nur 2 von 4 Tools (Fragebogen-Pfad lief nur als
   Fallback) + "AVV vorhanden"-Badge widersprach der Einschätzung.
2. KPI-Block kollabierte erneut ("ROI8 %nach 12 Monaten").
3. Tabellen brachen ohne Trennstrich mitten im Wort ("HANDLUN GSFELD").
4. final_sanitizer F4 machte aus dem ZEITBUDGET ("Über 10 Stunden/Woche")
   eine Ersparnis ("Über 15 Stunden/Monat").
5. Diverse Textmechanik (Doppelpunkt, ●hoch, UmsetzungsKomplexität,
   Regelkonformität-Score, Badge im Fließtext, halbgefärbte Zellen).
"""
from __future__ import annotations

from datetime import date

import pytest

from services.style_lint import (
    _soften_word,
    soften_table_long_words,
    fix_double_periods,
    fix_misc_typography,
)


# =========================================================================
# 1. Soft-Hyphens für Tabellen
# =========================================================================

class TestSoftHyphens:

    @pytest.mark.parametrize("word,expected_break", [
        ("Handlungsfeld", "Handlungs­feld"),
        ("Antragsfrist", "Antrags­frist"),
        ("Geschäftsmodell", "Geschäfts­modell"),
        ("HANDLUNGSFELD", "HANDLUNGS­FELD"),
    ])
    def test_fugen_s_breaks(self, word, expected_break):
        assert _soften_word(word) == expected_break

    def test_sch_never_split(self):
        # "Vers-chlüsselung" wäre falsch — nie vor "ch" trennen
        assert "s­ch" not in _soften_word("Verschlüsselung")
        assert "s­ch" not in _soften_word("Datenschutzbeauftragter")

    def test_short_words_untouched(self):
        for w in ("Priorität", "PROGRAMM", "Impact"):
            assert _soften_word(w) == w

    def test_only_table_cells_processed(self):
        html = ('<p>Datenschutzbeauftragter bleibt im Fließtext unangetastet</p>'
                '<table><tr><td>Datenschutzbeauftragter</td></tr></table>')
        out, n = soften_table_long_words(html)
        assert n == 1
        p_part = out.split("<table>")[0]
        assert "­" not in p_part
        assert "­" in out.split("<table>")[1]

    def test_urls_in_cells_untouched(self):
        html = '<table><tr><td>https://foerderdatenbank.bundesregierung.de</td></tr></table>'
        out, n = soften_table_long_words(html)
        assert n == 0 and "­" not in out


# =========================================================================
# 2. Textmechanik-Kleinkram
# =========================================================================

class TestTypographyFixes:

    def test_double_period_fixed(self):
        out, n = fix_double_periods("<p>Beratung &amp; Dienstleistungen..</p>")
        assert n == 1 and out == "<p>Beratung &amp; Dienstleistungen.</p>"

    def test_ellipsis_untouched(self):
        out, n = fix_double_periods("<p>und so weiter...</p>")
        assert n == 0

    def test_ampel_dot_gets_space(self):
        out, n = fix_misc_typography("<td>●hoch</td>")
        assert out == "<td>● hoch</td>" and n == 1

    def test_camel_compound_fixed(self):
        out, n = fix_misc_typography("<p>UmsetzungsKomplexität: ● niedrig</p>")
        assert "Umsetzungskomplexität" in out

    def test_tags_untouched(self):
        html = '<img src="a..b.png"><p>ok.</p>'
        out, _ = fix_double_periods(html)
        assert 'a..b.png' in out


# =========================================================================
# 3. Vendor-Audit: Fragebogen-Tools additiv + AVV-Wortlaut
# =========================================================================

class TestVendorAuditAdditive:

    def test_questionnaire_tools_merged_with_tools_data(self):
        from services.vendor_audit_engine import generate_vendor_audit_report
        report = generate_vendor_audit_report(
            context=None,
            tools_data=[{
                "name": "ChatGPT (OpenAI)", "category": "LLM",
                "vendor_risk": 4, "compliance_score": 3,
                "eu_hosting": False, "host": "US", "gdpr": "Limited",
            }],
            risk_report_v2=None, risk_report_v3=None,
            briefing={"ki_projekte": "API-Integration (OpenAI, Anthropic, etc.)"},
            llm_response=None, sections=None,
            strategy_answers={"s5_software": "ChatGPT / OpenAI,Claude / Anthropic,Perplexity,GitHub / GitLab"},
        )
        names = " | ".join(e.name for e in report.entries)
        assert "Perplexity" in names, names
        assert "Anthropic" in names or "Claude" in names, names
        # GitHub bleibt bewusst draußen (Wolf-Decision 1027.4-2D)
        assert "GitHub" not in names

    def test_no_duplicate_openai(self):
        from services.vendor_audit_engine import generate_vendor_audit_report
        report = generate_vendor_audit_report(
            context=None,
            tools_data=[{
                "name": "ChatGPT (OpenAI)", "category": "LLM",
                "vendor_risk": 4, "compliance_score": 3,
                "eu_hosting": False, "host": "US", "gdpr": "Limited",
            }],
            risk_report_v2=None, risk_report_v3=None,
            briefing={"ki_projekte": "OpenAI"},
            llm_response=None, sections=None,
            strategy_answers=None,
        )
        openai_entries = [e for e in report.entries if "OpenAI" in e.name]
        assert len(openai_entries) == 1

    def test_dpa_label_says_verfuegbar(self):
        """'AVV vorhanden' las sich wie 'abgeschlossen' und widersprach der
        Persönlichen Einschätzung — Wortlaut muss 'verfügbar' sein."""
        import inspect
        from services import vendor_audit_engine as vae
        src = inspect.getsource(vae)
        assert "AVV verfügbar" in src
        assert '"dpa_yes": "AVV vorhanden"' not in src


# =========================================================================
# 4. final_sanitizer: Zeitbudget-Schutz
# =========================================================================

class TestZeitbudgetShield:

    def test_zeitbudget_not_rewritten(self):
        from services.final_sanitizer import final_sanitize
        box = ('<!--NO-SANITIZE-ZEITBUDGET--><div>Ihr Zeitbudget: '
               'Über 10 Stunden/Woche ≈ 90 Minuten pro Tag</div><!--/NO-SANITIZE-ZEITBUDGET-->')
        sections = {
            "CANON_HOURS_MONTH": "15",
            "CHALLENGE_30_TAGE_HTML": box + "<p>Zusatztext damit die 50-Zeichen-Schwelle überschritten wird.</p>",
        }
        out = final_sanitize(sections)
        assert "Über 10 Stunden/Woche" in out["CHALLENGE_30_TAGE_HTML"]
        assert "15 Stunden/Monat" not in out["CHALLENGE_30_TAGE_HTML"]

    def test_unprotected_week_hours_still_normalized(self):
        from services.final_sanitizer import final_sanitize
        sections = {
            "CANON_HOURS_MONTH": "15",
            "EXECUTIVE_SUMMARY_HTML": "<p>Sie sparen künftig rund 9 Stunden/Woche durch Automatisierung im Alltag.</p>",
        }
        out = final_sanitize(sections)
        assert "15 Stunden/Monat" in out["EXECUTIVE_SUMMARY_HTML"]

    def test_fallstudie_shield_still_works(self):
        from services.final_sanitizer import final_sanitize
        block = ('<!--NO-SANITIZE-FALLSTUDIE--><p>Fallstudie: 25 Stunden/Woche '
                 'Ersparnis im Team.</p><!--/NO-SANITIZE-FALLSTUDIE-->')
        sections = {
            "CANON_HOURS_MONTH": "15",
            "GAMECHANGER_HTML": block + "<p>Rahmentext für die Mindestlänge dieses Abschnitts hier.</p>",
        }
        out = final_sanitize(sections)
        assert "25 Stunden/Woche" in out["GAMECHANGER_HTML"]


# =========================================================================
# 5. Lexikon: Compliance-Komposita mit Fugen-s
# =========================================================================

class TestComplianceCompound:

    def test_compound_gets_fugen_s(self):
        from services.content_quality_enforcer import apply_solo_language_normalizer
        sections = {"EXECUTIVE_SUMMARY_HTML": "<p>Compliance-Score: 0%. Der Compliance-Schaden ist real.</p>"}
        out = apply_solo_language_normalizer(sections, "solo")
        assert "Regelkonformitäts-Score" in out["EXECUTIVE_SUMMARY_HTML"]
        assert "Regelkonformität-Score" not in out["EXECUTIVE_SUMMARY_HTML"]
        assert "Regelkonformitäts-Schaden" in out["EXECUTIVE_SUMMARY_HTML"]

    def test_plain_compliance_still_replaced(self):
        from services.content_quality_enforcer import apply_solo_language_normalizer
        sections = {"EXECUTIVE_SUMMARY_HTML": "<p>Compliance ist wichtig.</p>"}
        out = apply_solo_language_normalizer(sections, "solo")
        assert "Regelkonformität ist wichtig" in out["EXECUTIVE_SUMMARY_HTML"]


# =========================================================================
# 6. html_enhancer: Zellen-Badges + Quick-Win-Badge
# =========================================================================

class TestEnhancerBadges:

    def test_full_cell_value_badged(self):
        from services.html_enhancer import enhance_strategy_html
        html = "<table><tr><td>hoch</td></tr></table>"
        out = enhance_strategy_html(html)
        assert ">Hoch</span>" in out

    def test_range_value_not_half_badged(self):
        from services.html_enhancer import enhance_strategy_html
        html = "<table><tr><td>Mittel bis hoch</td></tr></table>"
        out = enhance_strategy_html(html)
        assert ">Mittel</span>" not in out
        assert "Mittel bis hoch" in out

    def test_quick_win_badge_only_element_initial(self):
        from services.html_enhancer import enhance_strategy_html
        html = ("<td>Quick Win</td>"
                "<p>Der Quick Win liegt in der Automatisierung.</p>")
        out = enhance_strategy_html(html)
        assert out.count("Quick Win</span>") == 1
        assert "Der Quick Win liegt" in out


# =========================================================================
# 7. Dynamischer Quartalsbezug
# =========================================================================

class TestQuarterGoal:

    def test_july_targets_q3_herbst(self):
        from services.sofort_start_generator import _resolve_quarter_goal
        goal = _resolve_quarter_goal(date(2026, 7, 3))
        assert "Q3" in goal and "Herbst" in goal

    def test_last_month_of_quarter_rolls_over(self):
        from services.sofort_start_generator import _resolve_quarter_goal
        goal = _resolve_quarter_goal(date(2026, 9, 15))
        assert "Q4" in goal and "Jahresende" in goal

    def test_december_rolls_to_q1(self):
        from services.sofort_start_generator import _resolve_quarter_goal
        goal = _resolve_quarter_goal(date(2026, 12, 5))
        assert "Q1" in goal and "Frühjahr" in goal

    def test_no_placeholder_leaks(self):
        from services.sofort_start_generator import generate_30_tage_challenge_html_v2
        html = generate_30_tage_challenge_html_v2(
            company_size="solo", zeitbudget="ueber_10",
            expertise_level="expert", hauptleistung="KI-Beratung",
        )
        assert "__QUARTAL_ZIEL__" not in html
        assert "NO-SANITIZE-ZEITBUDGET" in html


# =========================================================================
# 8. Deutscher Vendor-Audit-Status im Strategie-Kontext
# =========================================================================

class TestVendorStatusGerman:

    def test_status_mapping_present(self):
        import inspect
        from services import strategy_pipeline as sp
        src = inspect.getsource(sp)
        assert '"fail": "nicht bestanden"' in src


# =========================================================================
# 9. Hinweis-Card-Garantie (Renderer-Kontrakt)
# =========================================================================

class TestFundingCardGuarantee:

    def test_renderer_contains_guarantee(self):
        import inspect
        from services import report_renderer as rr
        src = inspect.getsource(rr)
        assert "FOERDER-CARD" in src
        assert "Kernprogramme für Ihr Profil" in src
