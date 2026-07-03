# -*- coding: utf-8 -*-
"""KIS-1232: Report-Politur nach dem KMU-Validierungslauf.

Der KIS-1232-Lauf (drei PDFs) bestätigte alle KIS-1231-Fixes, zeigte aber
eine Reihe von Text-/Layout-Mängeln:
- zusammengeklebte Sätze ("KMU.Das", "Governance?Definieren", "…).Die")
- Dezimalpunkt statt -komma vor Zeiteinheiten ("5.8 h", "12.6 Mon.")
- Genus-Fehler nach Stack→Systemlandschaft ("Ihren bestehenden KI-Systemlandschaft")
- Akronym-Splitter zerlegte "DIGITALisierte" → "DIGITA - Lisierte"
- Label-Doppelpunkte wurden zu Punkten ("Risikofaktoren.")
- einsame Satzzeichen-Absätze ("<p>.</p>")
- 4 Quick-Win-Karten unter der Überschrift "Top 3"
- Quick-Win-Chip mit haengendem Doppelpunkt ("«Chip» :")
- Förder-Hinweis mit rohem Enum ("(11–100 (kmu))")
"""
from __future__ import annotations

import pytest

from services.style_lint import (
    fix_missing_sentence_space,
    fix_decimal_comma_units,
    remove_punctuation_only_nodes,
)
from services.content_quality_enforcer import (
    apply_grammar_fixes,
    strip_trailing_sentence_fragments,
)


# =========================================================================
# 1. Fehlende Leerzeichen nach Satzzeichen
# =========================================================================

class TestSentenceSpace:

    def test_user_input_glued_sentences(self):
        out, n = fix_missing_sentence_space("<p>Finanzberatung für KMU.Das Unternehmen bietet Leistungen an.</p>")
        assert n == 1
        assert "KMU. Das Unternehmen" in out

    def test_question_mark_glued(self):
        out, n = fix_missing_sentence_space("<p>Kosten, Output-Qualität oder Governance?Definieren Sie ein Ziel.</p>")
        assert n == 1
        assert "Governance? Definieren" in out

    def test_paren_period_glued(self):
        out, n = fix_missing_sentence_space("<p>(Ramp-up der Wochenleistung).Die volle Zeitersparnis folgt.</p>")
        assert n == 1
        assert "). Die volle" in out

    def test_abbreviations_untouched(self):
        for text in ("<p>z.B. ein Beispiel</p>", "<p>i.d.R. gilt das</p>", "<p>u.U. anders</p>"):
            out, n = fix_missing_sentence_space(text)
            assert n == 0, text
            assert out == text

    def test_urls_in_attributes_untouched(self):
        html = '<a href="https://x.de/pfad?Query=1&amp;b=2">Link</a>'
        out, n = fix_missing_sentence_space(html)
        assert out == html
        assert n == 0

    def test_lowercase_domains_untouched(self):
        html = "<p>Mehr unter ki-sicherheit.jetzt im Web.</p>"
        out, n = fix_missing_sentence_space(html)
        assert out == html

    def test_decimal_numbers_untouched(self):
        html = "<p>Version 2.5 und 10.000 € bleiben.</p>"
        out, n = fix_missing_sentence_space(html)
        assert out == html


# =========================================================================
# 2. Dezimalkomma vor Zeiteinheiten
# =========================================================================

class TestDecimalCommaUnits:

    @pytest.mark.parametrize("src,expected", [
        ("~5.8 h", "~5,8 h"),
        ("~37.4 Stunden", "~37,4 Stunden"),
        ("12.6 Mon.", "12,6 Mon."),
        ("11.0 Mon.", "11,0 Mon."),
        ("nach 9.8 Monaten", "nach 9,8 Monaten"),
    ])
    def test_converts_time_units(self, src, expected):
        out, n = fix_decimal_comma_units(f"<td>{src}</td>")
        assert expected in out
        assert n == 1

    def test_thousand_separators_untouched(self):
        html = "<td>10.000 € und 48.000 €</td>"
        out, n = fix_decimal_comma_units(html)
        assert out == html
        assert n == 0

    def test_version_numbers_untouched(self):
        html = "<p>Template v7.1 bleibt unangetastet.</p>"
        out, _ = fix_decimal_comma_units(html)
        assert out == html


# =========================================================================
# 3. Satzzeichen-Waisen-Absätze
# =========================================================================

class TestPunctuationOnlyNodes:

    def test_lone_period_paragraph_removed(self):
        out, n = remove_punctuation_only_nodes("<ul><li>Echt</li></ul><p>.</p><h4>Weiter</h4>")
        assert n == 1
        assert "<p>.</p>" not in out
        assert "<li>Echt</li>" in out

    def test_dash_only_li_removed(self):
        out, n = remove_punctuation_only_nodes("<ul><li>–</li><li>Inhalt</li></ul>")
        assert n == 1
        assert "<li>Inhalt</li>" in out

    def test_normal_content_kept(self):
        html = "<p>Ein normaler Satz.</p>"
        out, n = remove_punctuation_only_nodes(html)
        assert out == html
        assert n == 0


# =========================================================================
# 4. Genus-Reparatur + Akronym-Splitter
# =========================================================================

class TestGrammarFixes:

    def test_accusative_with_adjective(self):
        out, n = apply_grammar_fixes("Analysieren Sie Ihren bestehenden KI-Systemlandschaft auf Engpässe.")
        assert "Ihre bestehende KI-Systemlandschaft" in out
        assert n >= 1

    def test_accusative_without_adjective(self):
        out, _ = apply_grammar_fixes("Prüfen Sie Ihren KI-Systemlandschaft regelmäßig.")
        assert "Ihre KI-Systemlandschaft" in out

    def test_indefinite_article(self):
        out, _ = apply_grammar_fixes("Wir bauen einen skalierbaren Systemlandschaft auf.")
        # Hinweis: eine weitere Regel ersetzt "skalierbar"→"erweiterbar" — Genus zählt hier
        assert "eine erweiterbare Systemlandschaft" in out

    def test_nominative_stays(self):
        out, _ = apply_grammar_fixes("Ihre KI-Systemlandschaft ist solide.")
        assert "Ihre KI-Systemlandschaft ist solide." in out

    def test_digitalisierte_not_split(self):
        """Die Header-Trenn-Regel zerlegte 'DIGITALisierte' zu 'DIGITA - Lisierte'
        (Fördertabelle, Status-Report S. 21)."""
        out, _ = apply_grammar_fixes("DIGITALisierte Verwaltung & IT-Sicherheit")
        assert "DIGITALisierte" in out
        assert "DIGITA - " not in out

    def test_glued_header_still_split(self):
        out, _ = apply_grammar_fixes("ROADMAPPhase eins beginnt.")
        assert "ROADMAP - Phase" in out


# =========================================================================
# 5. Trailing-Fragment-Enforcer: Leerzeichen + Label-Doppelpunkte
# =========================================================================

class TestTrailingFragmentEnforcer:

    def test_sentence_join_preserves_spaces(self):
        """''.join() fraß die Leerzeichen zwischen Sätzen beim Fragment-Strip."""
        sections = {
            "test": "<p>" + ("Diese Programme sind vorausgewählt für Sie. "
                             "Weitere Programme können verfügbar sein. "
                             "Der Stand ist aktuell dokumentiert. kurzes Fragment ohne Ende") + "</p>"
        }
        out = strip_trailing_sentence_fragments(sections)
        text = out["test"]
        assert "Sie. Weitere" in text
        assert "sein. Der Stand" in text
        assert "Fragment ohne Ende" not in text

    def test_short_label_colon_survives(self):
        """'Risikofaktoren:' ist eine Listen-Einleitung — der Doppelpunkt darf
        nicht zu einem Punkt umgeschrieben werden (Status-Report S. 17)."""
        sections = {"risk": '<p style="font-weight:500;">Risikofaktoren:</p><ul><li>Eins</li></ul>'}
        out = strip_trailing_sentence_fragments(sections)
        assert "Risikofaktoren:" in out["risk"]
        assert "Risikofaktoren." not in out["risk"]

    def test_long_prose_dangling_colon_still_fixed(self):
        sections = {"t": "<p>" + ("Dieser deutlich längere Absatz beschreibt einen "
                                  "vollständigen Sachverhalt und endet versehentlich mit einem Doppelpunkt:") + "</p>"}
        out = strip_trailing_sentence_fragments(sections)
        assert out["t"].rstrip().endswith(".</p>")


# =========================================================================
# 6. Quick Wins: Kappung auf Top 3
# =========================================================================

class TestQuickWinsCap:

    def _four_wins_json(self):
        import json
        qw = {
            "title": "T", "icon": "◎", "problem": "P" * 40,
            "wirkung": "W" * 40, "umsetzung": "U" * 40, "hinweis": "siehe Business Case",
        }
        return json.dumps([dict(qw, title=f"Win {i}") for i in range(1, 5)], ensure_ascii=False)

    def test_premium_renderer_caps_at_three(self, monkeypatch):
        monkeypatch.delenv("QUICK_WINS_MAX_CARDS", raising=False)
        from services.quickwins_renderer import render_quickwins_premium_json
        html = render_quickwins_premium_json(self._four_wins_json(), "FULL")
        assert html is not None
        assert "Win 1" in html and "Win 3" in html
        assert "Win 4" not in html

    def test_cap_env_override(self, monkeypatch):
        monkeypatch.setenv("QUICK_WINS_MAX_CARDS", "4")
        from services.quickwins_renderer import render_quickwins_premium_json
        html = render_quickwins_premium_json(self._four_wins_json(), "FULL")
        assert html is not None
        assert "Win 4" in html


# =========================================================================
# 7. Quick-Win-Chip: Doppelpunkt wird mitkonsumiert
# =========================================================================

class TestQuickWinBadge:

    def test_colon_consumed(self):
        from services.html_enhancer import _transform_content_boxes
        html = "<p>Quick Win: Markieren Sie die Muster.</p>"
        out = _transform_content_boxes(html)
        assert "</span> Markieren" in out
        assert "</span> :" not in out and "</span>:" not in out

    def test_badge_not_double_wrapped(self):
        # KIS-1235: Fließtext bleibt Text (0 Badges); elementinitial genau 1.
        from services.html_enhancer import _transform_content_boxes
        out = _transform_content_boxes("<p>Als Quick Win empfiehlt sich der Einstieg.</p>")
        assert out.count("Quick Win</span>") == 0
        out2 = _transform_content_boxes("<td>Quick Win: Fragebogen-Auswertung</td>")
        assert out2.count("Quick Win</span>") == 1


# =========================================================================
# 8. Förder-Hinweis: sauberes Größen-Label
# =========================================================================

class TestFundingHint:

    def test_no_raw_enum_in_hint(self):
        from services.extra_sections import build_core_funding_table_html
        html = build_core_funding_table_html({
            "BRANCHE_LABEL": "Finanzen & Versicherungen",
            "BUNDESLAND_LABEL": "Bayern",
            "UNTERNEHMENSGROESSE_LABEL": "11–100 (kmu)",
        })
        assert "(kmu)" not in html
        assert "11–100 Mitarbeitende" in html


# =========================================================================
# 9. Template-Kontrakt: G21-Klassen sind im CSS definiert
# =========================================================================

class TestTemplateContract:

    @pytest.fixture(scope="class")
    def template_html(self):
        import os
        path = os.path.join(os.path.dirname(__file__), "..", "templates", "pdf_template_v7.html")
        with open(path, encoding="utf-8") as f:
            return f.read()

    @pytest.mark.parametrize("css_class", [
        ".ki-stack-summary", ".stack-section-title", ".pair-card",
        ".pair-card-name", ".pair-card-category", ".step-cards",
        ".step-card-number", ".kpi-triple", ".badge-block",
        ".risk-medium",
    ])
    def test_g21_classes_defined(self, template_html, css_class):
        """Der ki_stack_summary-Prompt verspricht diese Klassen — fehlen sie
        im Template, kollabiert die Sektion zu unformatiertem Text."""
        assert css_class in template_html, f"{css_class} fehlt im pdf_template_v7.html"

    def test_ai_act_display_uses_german_label(self, template_html):
        assert "AI_ACT_RISK_LEVEL_DE" in template_html


# =========================================================================
# 10. KIS-1233: Nachzügler aus dem Validierungslauf
# =========================================================================

class TestKis1233Followups:

    def test_bare_dot_after_list_removed(self):
        """Der Waisen-Punkt stand als nackter Textknoten nach </ul>
        (AI-Act-Kapitel S. 20) — nicht als <p>.</p>."""
        out, n = remove_punctuation_only_nodes("<ul><li>Lücke</li></ul>\n.\n<h4>Nächste Schritte</h4>")
        assert n == 1
        assert ">\n<h4>" in out or "</ul><h4>" in out.replace("\n", "")
        assert "." not in out.split("</ul>")[1].split("<h4>")[0]

    def test_sentence_period_before_tag_survives(self):
        html = "<p>Ein echter Satz endet hier.</p><h4>Weiter</h4>"
        out, n = remove_punctuation_only_nodes(html)
        assert out == html

    def test_grammar_pass_after_lexicon(self):
        """Das Lexikon (Stack→Systemlandschaft) läuft NACH dem ersten
        Grammar-Pass — der zweite Pass muss den Genus-Bruch fangen."""
        from services.content_quality_enforcer import apply_all_quality_enforcers
        sections = {"SOFORT_START_HTML": "<p>Analysieren Sie Ihren bestehenden KI-Stack auf den größten Engpass.</p>"}
        out = apply_all_quality_enforcers(dict(sections), company_size="kmu")
        text = out["SOFORT_START_HTML"]
        assert "Ihren bestehenden KI-Systemlandschaft" not in text
        # entweder blieb Stack (kein Lexikon-Hit) oder Genus wurde repariert
        if "Systemlandschaft" in text:
            assert "Ihre bestehende KI-Systemlandschaft" in text

    def test_funding_reinject_is_idempotent(self):
        """Zweifache Anwendung der 1104-Strips darf keine Waisen-Wrapper,
        Doppel-Hinweise oder Doppel-Überschriften hinterlassen."""
        import re as _re
        from services.extra_sections import build_core_funding_table_html
        core = build_core_funding_table_html({
            "BRANCHE_LABEL": "Bildung",
            "BUNDESLAND_LABEL": "Bayern",
            "UNTERNEHMENSGROESSE_LABEL": "11–100 (kmu)",
        })
        heading = '<h3>Kernprogramme für Ihr Profil (2025/2026)</h3>\n'
        prose = "<h4>Einordnung</h4><p>Die geplante API-Integration trägt sich auch ohne Zuschüsse:</p><ul><li>A</li></ul>"
        assembled = f"{heading}{core}\n\n{prose}"
        # Simuliere die (neuen) 1104-Strips auf dem BEREITS assemblierten HTML
        fp = _re.sub(r'<table[^>]*>.*?</table>', '', assembled, flags=_re.DOTALL)
        fp = _re.sub(
            r'<div class="card-nobreak">\s*<p class="small muted"[^>]*>\s*<strong>Hinweis:</strong>.*?</p>\s*</div>',
            '', fp, flags=_re.DOTALL,
        )
        fp = _re.sub(r'<div class="funding-matrix">\s*</div>', '', fp)
        fp = _re.sub(
            r'<h3[^>]*>(?:(?!</h3>).)*?(?:Kernprogramme|Förder(?:programm|mittel)|Programmüberblick)(?:(?!</h3>).)*?</h3>\s*',
            '', fp, flags=_re.IGNORECASE | _re.DOTALL,
        )
        fp = fp.strip()
        rebuilt = f"{heading}{core}\n\n{fp}"
        assert rebuilt.count("Kernprogramme für Ihr Profil") == 1
        assert rebuilt.count("<strong>Hinweis:</strong>") == 1
        assert "Die geplante API-Integration" in rebuilt
