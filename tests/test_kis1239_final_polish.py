# -*- coding: utf-8 -*-
"""KIS-1239: Letzte Korrekturen vor dem finalen Testlauf.

1. FIX-G-Sentence-Trim schneidet nicht mehr an Abkürzungen
   ("Format: Executive Summary (max." — Lauf 1119, S. 8).
2. PROMPT_VORLAGEN_HTML aus den Coverage-Pflichtkeys entfernt
   (kein Builder erzeugt den Key; Warnung feuerte in jedem Lauf).
3. Zeitbudget-vs-Zeitersparnis-Guard in den Strategy-Prompts
   (50h Ersparnis wurde als "eingeplantes Zeitbudget" bezeichnet).
4. KPA-Kapitel fließen statt erzwungener Umbrüche (3 von 12 Seiten
   waren zu 75-85 % leer); Kapitel-Banner kleben am Folgeinhalt.
"""
from __future__ import annotations


# =========================================================================
# 1. Abkürzungssicherer Sentence-Trim
# =========================================================================

class TestSentenceBoundaryTrim:

    def test_skips_abbreviation(self):
        from services.report_healer import _rfind_sentence_boundary
        text = "Erster Satz endet hier. Format: Executive Summary (max. 500 Wörter)"
        # Suche endet mitten im Abkürzungsbereich — "max. " darf NICHT
        # als Satzende gelten, der echte Punkt davor gewinnt.
        pos = _rfind_sentence_boundary(text, ". ", len(text))
        assert text[pos - 4:pos] != " max"
        assert text[:pos + 1].endswith("hier.")

    def test_skips_enumeration_digit(self):
        from services.report_healer import _rfind_sentence_boundary
        text = "Alles klar soweit. Schritt 1. Danach folgt mehr Text"
        pos = _rfind_sentence_boundary(text, ". ", len(text))
        assert text[:pos + 1].endswith("soweit.")

    def test_regular_sentence_found(self):
        from services.report_healer import _rfind_sentence_boundary
        text = "Ein normaler Satz. Und noch einer folgt"
        pos = _rfind_sentence_boundary(text, ". ", len(text))
        assert pos == text.index(". ")

    def test_non_dot_markers_unaffected(self):
        from services.report_healer import _rfind_sentence_boundary
        text = "Wirklich? Ja, mit max. Aufwand"
        assert _rfind_sentence_boundary(text, "? ", len(text)) == text.index("? ")

    def test_fix_g_uses_helper(self):
        src = open("services/report_healer.py", encoding="utf-8").read()
        assert "_rfind_sentence_boundary(processed, end_marker, text_budget)" in src


# =========================================================================
# 2. Coverage-Guard
# =========================================================================

class TestCoverageGuardKeys:

    def test_prompt_vorlagen_not_required(self):
        from services.coverage_guard import RENDER_REQUIRED_KEYS
        assert "PROMPT_VORLAGEN_HTML" not in RENDER_REQUIRED_KEYS["r1"]

    def test_other_required_keys_intact(self):
        from services.coverage_guard import RENDER_REQUIRED_KEYS
        r1 = RENDER_REQUIRED_KEYS["r1"]
        assert "QUICK_WINS_HTML" in r1
        assert "VENDOR_AUDIT_HTML" in r1
        assert len(r1) >= 10


# =========================================================================
# 3. Zeitbudget-Guard
# =========================================================================

class TestZeitbudgetGuard:

    def test_prompt_rule_present(self):
        src = open("prompts/strategy_prompts.py", encoding="utf-8").read()
        assert "ZEITBUDGET vs. ZEITERSPARNIS" in src
        assert "NICHT das Zeitbudget" in src


# =========================================================================
# 4. KPA-Seitenfluss
# =========================================================================

class TestKpaPageFlow:

    def test_no_forced_chapter_breaks(self):
        src = open("templates/gamechanger_deep_dive_v1.html", encoding="utf-8").read()
        import re
        block = re.search(
            r"#dd-implementation,.*?\{(.*?)\}", src, re.DOTALL).group(1)
        assert "break-before: auto" in block
        assert "break-before: page" not in block

    def test_banner_sticks_to_content(self):
        src = open("templates/gamechanger_deep_dive_v1.html", encoding="utf-8").read()
        import re
        banner = re.search(r"\.chapter-banner \{(.*?)\}", src, re.DOTALL).group(1)
        assert "break-after: avoid" in banner

    def test_impressum_still_own_page(self):
        src = open("templates/gamechanger_deep_dive_v1.html", encoding="utf-8").read()
        assert 'id="dd-impressum" style="break-before: page;"' in src
