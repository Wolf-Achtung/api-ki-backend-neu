# -*- coding: utf-8 -*-
"""KIS-1262: Restbefunde aus dem Platin++++-Abnahmelauf KIS-1241.

Der Lauf lieferte erstmals '[PLATIN-JUDGE] ✅ Gesamt-Ampel GRÜN' — mit zwei
verbliebenen Befunden aus dem PDF-Abgleich:

(1) Die Budget-Einordnungs-Box stand in BUSINESS_CASE_HTML (dort las sie
der Judge → budget GRÜN), aber pdf_template_v7 rendert das Business-Case-
Kapitel aus BUSINESS_CASE_ENGINE_HTML — im PDF fehlte die Box. Beide
Budget-Gates injizieren jetzt zusätzlich in die gerenderte Sektion.

(2) Der Healer-Redundanz-Pass (FIX-C) entfernte die Box als
"Cross-Section-Duplikat" aus dem Shadow-Key — deterministisch injizierte
Hinweis-Boxen sind jetzt vor beiden Dedup-Pässen geschützt.

(3) Die TOC-Legende kippte als letztes Element allein auf S. 3 (104
Zeichen) — sie steht jetzt oben im TOC-Kopf.
"""
from __future__ import annotations


def _read(path: str) -> str:
    return open(path, encoding="utf-8").read()


# =========================================================================
# 1. Budget-Box landet auch in der GERENDERTEN Sektion
# =========================================================================

class TestBudgetBoxInRenderedSection:

    def test_both_gates_patch_engine_html(self):
        src = _read("gpt_analyze.py")
        assert src.count("[KIS-1262][BUDGET-BOX-ENGINE]") == 2
        # je einmal hinter Überschreitungs- und Grenznähe-Zweig
        i1 = src.find("[KIS-1244][BUDGET-GATE] CAPEX %s > Budget-Band")
        i2 = src.find("[KIS-1260][BUDGET-GRENZNAEHE]")
        e1 = src.find("[KIS-1262][BUDGET-BOX-ENGINE]")
        e2 = src.find("[KIS-1262][BUDGET-BOX-ENGINE]", e1 + 1)
        assert i1 < e1 < i2 < e2

    def test_engine_section_is_fixc_protected(self):
        src = _read("services/report_healer.py")
        idx = src.find("PROTECTED_SECTION_KEYS = {")
        block = src[idx:idx + 900]
        assert "BUSINESS_CASE_ENGINE_HTML" in block

    def test_template_renders_engine_not_business_case_html(self):
        src = _read("templates/pdf_template_v7.html")
        assert "BUSINESS_CASE_ENGINE_HTML" in src
        # Der Grund für KIS-1262: BUSINESS_CASE_HTML wird NICHT gerendert.
        # Sollte sich das ändern, ist die Doppel-Injektion obsolet — dieser
        # Test macht die Annahme sichtbar.
        assert "BUSINESS_CASE_HTML|safe" not in src


# =========================================================================
# 2. FIX-C lässt kuratierte Hinweis-Boxen in Ruhe
# =========================================================================

class TestFixCProtectsHinweisBoxes:

    _BOX = ('<div class="hinweis-box budget-gate" style="padding:12px;">'
            "<strong>Budget-Einordnung:</strong> Die kalkulierte "
            "Gesamtinvestition liegt innerhalb Ihres angegebenen Rahmens und "
            "nutzt ihn weitgehend aus — gestufter Einstieg und Förderpfad "
            "halten Sie dabei jederzeit flexibel und steuerbar.</div>")

    def test_box_survives_cross_section_dedup(self):
        from services.report_healer import reduce_redundancy
        sections = {
            "AAA_HTML": "<p>Individueller Kontext der ersten Sektion.</p>" + self._BOX,
            "BBB_HTML": "<p>Individueller Kontext der zweiten Sektion.</p>" + self._BOX,
        }
        healed, _stats = reduce_redundancy(dict(sections))
        assert "Budget-Einordnung" in healed["AAA_HTML"]
        assert "Budget-Einordnung" in healed["BBB_HTML"]

    def test_normal_duplicates_still_removed(self):
        from services.report_healer import reduce_redundancy
        dup = ("<p>Dieser völlig gewöhnliche Absatz wiederholt sich wortgleich "
               "über zwei Sektionen hinweg und ist ein klassischer Kandidat "
               "für die Redundanz-Entfernung im Healer-Durchlauf.</p>")
        sections = {
            "AAA_HTML": "<p>Eigener Inhalt A mit ausreichend Länge im Text.</p>" + dup,
            "BBB_HTML": "<p>Eigener Inhalt B mit ausreichend Länge im Text.</p>" + dup,
        }
        healed, stats = reduce_redundancy(dict(sections))
        total = sum(v.count("völlig gewöhnliche Absatz") for v in healed.values())
        assert total == 1

    def test_guard_present_in_both_dedup_passes(self):
        src = _read("services/report_healer.py")
        assert src.count("KIS-1262: Deterministisch injizierte Hinweis-Boxen") == 2


# =========================================================================
# 3. TOC-Legende steht oben — keine Waisen-Seite mehr
# =========================================================================

class TestTocLegendOnTop:

    def test_legend_before_first_level_header(self):
        src = _read("templates/pdf_template_v7.html")
        # Im MARKUP vergleichen (die CSS-Selektoren stehen weit oben im Head)
        toc = src.find('<div class="section" id="toc"')
        assert toc != -1
        idx_legend = src.find('class="toc-legend"', toc)
        idx_first_header = src.find('class="toc-level-header toc-level-header-exec"', toc)
        assert idx_legend != -1 and idx_first_header != -1
        assert idx_legend < idx_first_header

    def test_legend_appears_exactly_once(self):
        src = _read("templates/pdf_template_v7.html")
        assert src.count('class="toc-legend"') == 1
