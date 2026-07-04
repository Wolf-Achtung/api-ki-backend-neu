# -*- coding: utf-8 -*-
"""KIS-1244: Report-Fixes aus Validierungslauf 4 (04.07., Briefing KIS-1237).

Befunde aus 3 parallelen PDF-Prüfungen (Status 24 S., Strategie 31 S., KPA):
Budget-Widerspruch unkommentiert, alte ROI-Erklärung in der Executive
Summary, Entscheidungsvorlage ohne Finanzzahl, Vendor-Ampel widerspricht
der Empfehlung, kollabierte Kennzahlen-Kacheln, DSGVO-Vorbehalt 3× im R1,
invertierte Ampelfarben, interner Template-Name im Impressum, falsche
Silbentrennung, Wiederholungs-Formeln, fehlendes Bundesland auf dem
R1-Deckblatt, veraltete Jahresangabe in der Förder-Überschrift.
"""
from __future__ import annotations


def _read(path: str) -> str:
    return open(path, encoding="utf-8").read()


# =========================================================================
# 1. Budget-Gate (R1)
# =========================================================================

class TestBudgetGate:

    def test_gate_present_with_band_parsing(self):
        src = _read("gpt_analyze.py")
        assert "[KIS-1244][BUDGET-GATE]" in src
        idx = src.find("KIS-1244 (1): Budget-Gate")
        block = src[idx:idx + 3000]
        assert "investitionsbudget" in block
        assert "Budget-Einordnung" in block
        assert "gestufter Einstieg" in block
        # Band-Parsing für "2000_10000" UND "unter_2000"
        assert r"(\d+)_(\d+)" in block
        assert "unter_" in block


# =========================================================================
# 2. ROI-Methodik-Box: OPEX-Abzug statt „andere Investitionssumme"
# =========================================================================

class TestRoiMethodikBox:

    def test_opex_explanation(self):
        src = _read("services/strategy_renderer.py")
        assert "zieht zus\\u00e4tzlich die laufenden Tool-Kosten (OPEX)" in src
        assert "konservativere Netto-Rendite" in src

    def test_old_claim_removed(self):
        # Die untersagte Behauptung: Differenz käme aus einer anderen
        # (einmaligen) Investitionssumme — beide Summen sind identisch.
        src = _read("services/strategy_renderer.py")
        assert "rechnet mit einer einmaligen Startinvestition" not in src


# =========================================================================
# 3. Entscheidungsvorlage bekommt eine Investitions-Zeile
# =========================================================================

class TestDecisionInvestLine:

    def test_deterministic_injection_present(self):
        src = _read("gpt_analyze.py")
        assert "[KIS-1244][DECISION-INVEST]" in src
        idx = src.find("KIS-1244 (3): Entscheidungsvorlage")
        block = src[idx:idx + 2500]
        assert "EXECUTIVE_DECISION_HTML" in block
        assert "Startinvestition" in block
        assert "CANON_CAPEX_EUR" in block
        assert "'</ul>'" in block  # Einfügung in die bestehende Bullet-Liste


# =========================================================================
# 4. Vendor-Ampel: Lesart-Box (Rohzustand vs. mit Maßnahmen)
# =========================================================================

class TestVendorReadingGuide:

    def test_einordnung_box_present(self):
        src = _read("services/vendor_audit_engine.py")
        assert "Wichtig zur Lesart" in src
        assert "im Rohzustand" in src
        assert "nur mit diesen Ma\\u00dfnahmen nutzen" in src


# =========================================================================
# 5./6. KPI-Kollaps: Rebuild greift auch bei nackten Textzeilen
# =========================================================================

class TestKpiPlainlineRebuild:

    def test_trigger_and_pattern(self):
        src = _read("gpt_analyze.py")
        assert "_kpi_plainline" in src
        idx = src.find("_kpi_plainline = _re_c1.compile(")
        pattern_block = src[idx:idx + 300]
        assert "ROI|Break-Even|Zeitersparnis" in pattern_block

    def test_plainline_regex_matches_collapsed_lines(self):
        import re
        pat = re.compile(
            r'<(?:p|div)[^>]*>\s*(?:ROI|Break-Even|Zeitersparnis)[\d][^<]{0,90}</(?:p|div)>'
        )
        # Exakt die kollabierte Form aus Lauf 4, S. 15
        assert pat.search("<p>ROI8 %nach 12 Monaten</p>")
        assert pat.search("<p>Break-Even11,1 MonateAmortisation der Einführungskosten</p>")
        assert pat.search("<p>Zeitersparnis15 Std./Monatvorrangig Projektkoordination</p>")
        # Normale Prosa (Leerzeichen nach dem Begriff) bleibt unangetastet
        assert not pat.search("<p>ROI von 20 % bedeutet eine solide Rendite.</p>")


# =========================================================================
# 7. DSGVO-Vorbehalt-Cap auch im R1
# =========================================================================

class TestDsgvoCapR1:

    def test_cap_present(self):
        src = _read("gpt_analyze.py")
        assert "[KIS-1244][DSGVO-VORBEHALT-R1]" in src
        idx = src.find("KIS-1244 (7): DSGVO-Vorbehalt-Cap")
        block = src[idx:idx + 2500]
        assert "_dv_keep_left = 2" in block
        assert "(?:DSGVO|Datenschutz)-Vorbehalt" in block


# =========================================================================
# 8. Ampel-Semantik je Spaltentyp (funktional)
# =========================================================================

class TestAmpelSemantics:

    def _table(self, header: str, cell: str) -> str:
        return (
            f"<table><tr><th>Maßnahme</th><th>{header}</th></tr>"
            f"<tr><td>X</td><td>{cell}</td></tr></table>"
        )

    def test_risk_high_becomes_red(self):
        from services.strategy_renderer import _fix_ampel_semantics
        html = self._table("Eintritt", '<span class="ampel-green">●</span> Hoch')
        out = _fix_ampel_semantics(html)
        assert "ampel-red" in out and "ampel-green" not in out

    def test_complexity_low_becomes_green(self):
        from services.strategy_renderer import _fix_ampel_semantics
        html = self._table("Komplexität", '<span class="ampel-red">●</span> Niedrig')
        out = _fix_ampel_semantics(html)
        assert "ampel-green" in out and "ampel-red" not in out

    def test_benefit_high_stays_green(self):
        from services.strategy_renderer import _fix_ampel_semantics
        html = self._table("Impact", '<span class="ampel-green">●</span> Hoch')
        assert _fix_ampel_semantics(html) == html

    def test_cell_without_ampel_class_untouched(self):
        from services.strategy_renderer import _fix_ampel_semantics
        html = self._table("Risiko", "Hoch")
        assert _fix_ampel_semantics(html) == html

    def test_table_without_semantic_headers_untouched(self):
        from services.strategy_renderer import _fix_ampel_semantics
        html = self._table("Status", '<span class="ampel-red">●</span> Hoch')
        assert _fix_ampel_semantics(html) == html


# =========================================================================
# 9./10./12. Template-Fixes
# =========================================================================

class TestTemplateFixes:

    def test_no_internal_template_name(self):
        src = _read("templates/strategy_report.html")
        assert "Strategy Blue" not in src

    def test_hyphens_manual_in_strategy_tables(self):
        src = _read("templates/strategy_report.html")
        assert "hyphens: manual" in src
        assert "th { hyphens: none; }" in src
        assert "hyphens: auto" not in src

    def test_thead_keeps_first_row(self):
        src = _read("templates/strategy_report.html")
        assert "tbody tr:first-child { break-before: avoid-page" in src

    def test_banner_sticks_to_content(self):
        src = _read("templates/strategy_report.html")
        import re
        banner = re.search(r"\.chapter-banner \{(.*?)\}", src, re.DOTALL).group(1)
        assert "break-after: avoid" in banner

    def test_orphan_widow_control(self):
        assert "orphans: 3" in _read("templates/strategy_report.html")
        assert "orphans: 3" in _read("templates/pdf_template_v7.html")

    def test_bundesland_on_r1_cover(self):
        src = _read("templates/pdf_template_v7.html")
        assert "{{ UNTERNEHMENSGROESSE_LABEL }}{% if BUNDESLAND_LABEL %}" in src


# =========================================================================
# 11. Wiederholungs-Dedup (funktional)
# =========================================================================

class TestRepetitionDedup:

    def test_dedup_pass_present(self):
        src = _read("services/strategy_renderer.py")
        assert "[KIS-1244][DEDUP]" in src
        assert "EU AI Act" in src
        assert "nicht als Hauptsystem" in src


# =========================================================================
# 13. Förder-Überschrift ohne fest verdrahtete Jahresangabe
# =========================================================================

class TestFundingHeading:

    def test_no_hardcoded_year(self):
        src = _read("gpt_analyze.py")
        assert "Kernprogramme für Ihr Profil (2025/2026)" not in src
        assert "Kernprogramme für Ihr Profil" in src
