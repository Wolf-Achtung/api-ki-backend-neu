"""Hotfix 1027.2.2-A: Source-level guard für den figure-Wrapper-Backup
um EXECUTIVE_DECISION_HTML in templates/pdf_template_v7.html.

KIS-1193 (1027.2.1) + KIS-1194 (1027.2.2) zeigten: Chromium honoriert
break-inside:avoid auf generischen <div>-Containern unzuverlässig, wenn
der Box-Content > halbe Seitenhöhe ist. Wrapping in <figure> behebt das
laut Chromium-Verhalten (atomare Layout-Einheit), aber nur wenn beide
Teile zusammen ankommen — der Wrapper im Template UND die CSS-Regeln,
die die Härtung tatsächlich tragen.

Statt eine vollständige Jinja-Rendering-Umgebung mit Asset-Pipeline
aufzusetzen, prüfen die Tests die Template-Quelle direkt — analog zu
TestTemplateSkipHintUsesExpertiseLevel in test_kis_1142_p3_woche_1_skip.py.
"""
from __future__ import annotations

import os
import re

TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "templates",
    "pdf_template_v7.html",
)


def _read_template() -> str:
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        return f.read()


class TestFigureWrapperPresent:
    def test_executive_decision_html_wrapped_in_figure(self) -> None:
        """EXECUTIVE_DECISION_HTML muss in <figure class="exec-decision-figure">
        gewrappt sein — der Wrapper ist der Hebel für Chromium-Atomic-Layout."""
        tpl = _read_template()
        # Suche das exakte Markup im decision-Block
        pattern = re.compile(
            r'<figure\s+class="exec-decision-figure"\s*>'
            r'\s*\{\{\s*EXECUTIVE_DECISION_HTML\s*\|\s*safe\s*\}\}\s*'
            r'</figure>',
        )
        assert pattern.search(tpl), (
            "EXECUTIVE_DECISION_HTML ist nicht in <figure class='exec-decision-figure'> "
            "gewrappt — 1027.2.2-A-Wrapper fehlt."
        )

    def test_figure_wrapper_only_in_decision_section(self) -> None:
        """Der figure-Wrapper darf nicht in eine andere Section gewandert sein
        (Smoke-Test gegen Copy-Paste-Fehler)."""
        tpl = _read_template()
        # Section-Header steht direkt vor dem Wrapper
        match = re.search(
            r'<div class="section" id="decision"[^>]*>'
            r'(.*?)<figure\s+class="exec-decision-figure"',
            tpl,
            re.DOTALL,
        )
        assert match, (
            "figure-Wrapper steht nicht innerhalb der #decision-Section — "
            "1027.2.2-A im falschen Block?"
        )
        # Keine zweite <figure class="exec-decision-figure"> außerhalb #decision
        all_figures = re.findall(r'<figure\s+class="exec-decision-figure"', tpl)
        assert len(all_figures) == 1, (
            f"Erwarte genau einen exec-decision-figure-Wrapper, gefunden: {len(all_figures)}"
        )


class TestCssHardeningOnFigure:
    def test_exec_decision_figure_has_break_inside_avoid(self) -> None:
        """CSS-Regel .exec-decision-figure muss break-inside:avoid (mit !important)
        UND page-break-inside:avoid setzen — beide Properties, weil
        Chromium-Versionen unterschiedlich strikt sind."""
        tpl = _read_template()
        rule_match = re.search(
            r'\.exec-decision-figure\s*\{([^}]*)\}',
            tpl,
            re.DOTALL,
        )
        assert rule_match, ".exec-decision-figure CSS-Regel fehlt"
        body = rule_match.group(1)
        assert re.search(r'break-inside\s*:\s*avoid\s*!important', body), (
            f".exec-decision-figure fehlt break-inside:avoid !important: {body!r}"
        )
        assert re.search(r'page-break-inside\s*:\s*avoid\s*!important', body), (
            f".exec-decision-figure fehlt page-break-inside:avoid !important: {body!r}"
        )

    def test_exec_decision_figure_has_min_height(self) -> None:
        """Wolf-Anweisung 1027.2.2: min-height aus 1027.2.1 von .exec-decision-box
        auf .exec-decision-figure verschieben (Floor zwingt Chromium zur
        Atomic-Behandlung)."""
        tpl = _read_template()
        rule_match = re.search(
            r'\.exec-decision-figure\s*\{([^}]*)\}',
            tpl,
            re.DOTALL,
        )
        assert rule_match, ".exec-decision-figure CSS-Regel fehlt"
        body = rule_match.group(1)
        assert re.search(r'min-height\s*:\s*\d+(?:\.\d+)?(?:em|rem|px|%)', body), (
            f".exec-decision-figure fehlt min-height-Floor: {body!r}"
        )

    def test_decision_section_selector_covers_figure(self) -> None:
        """Section-Level-Regel #decision … figure muss im selben Selector-
        Block stehen wie ul/li/p — sonst greift die Härtung nicht für den
        äußeren Container."""
        tpl = _read_template()
        # Multi-Selector-Block mit #decision-Prefix
        block_match = re.search(
            r'(#decision\s+ul,[^{]*?#decision\s+figure[^{]*)\{',
            tpl,
            re.DOTALL,
        )
        assert block_match, (
            "Section-Level-Regel deckt '#decision figure' nicht ab — "
            "1027.2.2-A-Wrapper bekommt nur Eigen-Regel, nicht den "
            "kombinierten Section-Schutz."
        )
