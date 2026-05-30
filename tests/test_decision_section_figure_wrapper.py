"""Sprint 1027.2.3: Source-level guard für den Pre-figure-Zustand der
Decision-Section in templates/pdf_template_v7.html.

Hintergrund: Sprint 1027.2.2-A (Commit 3bfbf36e) hatte einen
<figure class="exec-decision-figure">-Wrapper mit min-height:12em um
EXECUTIVE_DECISION_HTML gelegt. KIS-1195 (analysis_id=1053, DB-Diag:
Backend liefert 3 vollständige Bullets, Restplatz 765-784px, Figure-
Bedarf ~280px, Headroom +485-504px) zeigte trotzdem Cutoff nach
"…Standard-Arbeitsablauf (Input". Ursache: figure(min-height:12em) +
nested .exec-decision-box(break-inside:avoid) triggerte Chromium-
Layout-Pass-Bug — figure fixiert auf min-height (176px), Content
~280px wurde geclippt obwohl reichlich Restplatz vorhanden war.

Fix 1027.2.3: figure-Wrapper komplett zurückgenommen. .exec-decision-box
trägt jetzt wieder allein die Atomarität (Pre-1027.2.2-A-Zustand,
äquivalent zu 1027.2.1-F1). Zusätzlich .exec-decision-box li explizit
auf break-inside:avoid + page-break-inside:avoid — verhindert Mid-
Sentence-Cuts innerhalb eines Bullets, ohne den Block als Ganzes mit
unnötig hartem Layout-Floor zu belasten.

Tests prüfen die Template-Quelle direkt (analog
TestTemplateSkipHintUsesExpertiseLevel in test_kis_1142_p3_woche_1_skip.py).
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


class TestDecisionDirectRender:
    def test_executive_decision_html_renders_directly(self) -> None:
        """EXECUTIVE_DECISION_HTML wird DIREKT in #decision gerendert, nicht
        in einen Wrapper geschachtelt. Pre-1027.2.2-A-Zustand."""
        tpl = _read_template()
        # Innerhalb der #decision-Section: EXECUTIVE_DECISION_HTML steht
        # als nackter {{ … |safe }}-Output ohne umschließendes Element.
        decision_block = re.search(
            r'<div class="section" id="decision"[^>]*>(.*?)<!-- ',
            tpl,
            re.DOTALL,
        )
        assert decision_block, "#decision-Section nicht gefunden"
        body = decision_block.group(1)
        direct_render = re.search(
            r'\{\{\s*EXECUTIVE_DECISION_HTML\s*\|\s*safe\s*\}\}',
            body,
        )
        assert direct_render, (
            "EXECUTIVE_DECISION_HTML wird nicht direkt im #decision-Block "
            "gerendert."
        )
        # Direkt davor darf KEIN öffnender Wrapper-Tag stehen (figure / span /
        # zusätzlicher div mit Klasse für diese Variable).
        prefix = body[: direct_render.start()].rstrip()
        assert not prefix.endswith("<figure class=\"exec-decision-figure\">"), (
            "EXECUTIVE_DECISION_HTML ist in <figure class='exec-decision-figure'> "
            "gewrappt — 1027.2.2-A-Wrapper wurde nicht entfernt."
        )

    def test_no_exec_decision_figure_wrapper_in_template(self) -> None:
        """Kein <figure class="exec-decision-figure"> mehr im Template — der
        Wrapper aus 1027.2.2-A ist vollständig entfernt."""
        tpl = _read_template()
        figures = re.findall(r'<figure[^>]*class="[^"]*exec-decision-figure', tpl)
        assert figures == [], (
            f"Erwarte 0 <figure class='exec-decision-figure'>-Wrapper, "
            f"gefunden: {len(figures)}"
        )

    def test_no_exec_decision_figure_css_rule(self) -> None:
        """Die CSS-Regel .exec-decision-figure { … } ist vollständig entfernt —
        kein toter Code, kein Layout-Hebel ohne korrespondierendes Markup."""
        tpl = _read_template()
        rule = re.search(r'\.exec-decision-figure\s*[,{]', tpl)
        assert rule is None, (
            ".exec-decision-figure CSS-Regel/Selektor existiert noch — "
            "1027.2.3 hat den figure-Layer nicht vollständig entfernt."
        )


class TestDecisionBoxAtomicity:
    def test_exec_decision_box_no_container_atomicity(self) -> None:
        """FIX-KIS-1027.5-H1: .exec-decision-box darf KEIN break-inside:avoid
        mehr tragen. Sprint 1027.5-H1 hat die Container-Atomarität entfernt,
        weil sie bei 3-Bullet-Inhalt >1 Seite denselben Chromium-Clipping-Bug
        triggerte wie der 1027.2.2-A-figure-Wrapper. Atomarität bleibt auf
        <li>-Ebene (siehe test_exec_decision_box_li_break_inside_avoid)."""
        tpl = _read_template()
        rule_match = re.search(
            r'\.exec-decision-box\s*\{([^}]*)\}',
            tpl,
            re.DOTALL,
        )
        assert rule_match, ".exec-decision-box CSS-Regel fehlt"
        body = rule_match.group(1)
        # Aktive (nicht-auskommentierte) break-inside / page-break-inside
        # mit "avoid" darf NICHT vorkommen.
        for line in body.splitlines():
            stripped = line.strip()
            if stripped.startswith("/*") or stripped.startswith("*"):
                continue
            assert not re.search(
                r'^\s*(break-inside|page-break-inside)\s*:\s*avoid',
                line,
            ), (
                f".exec-decision-box hat noch aktive Container-Atomarität: "
                f"{line!r}. 1027.5-H1 hat sie entfernt — Regression."
            )

    def test_exec_decision_box_li_break_inside_avoid(self) -> None:
        """Pro-Bullet-Atomarität: .exec-decision-box li trägt
        break-inside:avoid + page-break-inside:avoid — verhindert Mid-Sentence-
        Cuts innerhalb eines einzelnen Bullets."""
        tpl = _read_template()
        rule_match = re.search(
            r'\.exec-decision-box\s+li\s*\{([^}]*)\}',
            tpl,
            re.DOTALL,
        )
        assert rule_match, (
            ".exec-decision-box li CSS-Regel fehlt — Bullet-Atomarität "
            "1027.2.3 nicht gesetzt."
        )
        body = rule_match.group(1)
        assert re.search(r'break-inside\s*:\s*avoid', body), (
            f".exec-decision-box li fehlt break-inside:avoid: {body!r}"
        )
        assert re.search(r'page-break-inside\s*:\s*avoid', body), (
            f".exec-decision-box li fehlt page-break-inside:avoid: {body!r}"
        )

    def test_exec_decision_box_has_no_min_height(self) -> None:
        """Kein min-height auf .exec-decision-box — der Floor war Teil der
        1027.2.2-A-Hypothese und wurde mit dem figure-Wrapper entfernt.
        Content soll seine natürliche Höhe behalten."""
        tpl = _read_template()
        rule_match = re.search(
            r'\.exec-decision-box\s*\{([^}]*)\}',
            tpl,
            re.DOTALL,
        )
        assert rule_match, ".exec-decision-box CSS-Regel fehlt"
        body = rule_match.group(1)
        assert not re.search(r'min-height\s*:', body), (
            f".exec-decision-box hat min-height — 1027.2.3 sollte keinen "
            f"Floor mehr setzen: {body!r}"
        )


class TestDecisionSectionLevelSelector:
    def test_section_level_rule_no_longer_targets_figure(self) -> None:
        """Section-Level-Regel #decision ul/ol/li/p/… darf nicht mehr
        '#decision figure' enthalten — der Selektor wurde mit dem
        figure-Wrapper aus 1027.2.2-A entfernt."""
        tpl = _read_template()
        # Block, der #decision ul / ol / li / p / … gemeinsam härtet.
        block_match = re.search(
            r'(#decision\s+ul,[^{]*?)\{',
            tpl,
            re.DOTALL,
        )
        assert block_match, (
            "Section-Level-Härtungs-Block (#decision ul, …) nicht gefunden"
        )
        selector_list = block_match.group(1)
        assert "figure" not in selector_list, (
            f"Section-Level-Selektor enthält noch 'figure' — 1027.2.3 hat "
            f"den figure-Selektor nicht entfernt: {selector_list!r}"
        )

    def test_decision_div_atomicity_rule_removed(self) -> None:
        """FIX-KIS-1027.5-H1: Der generische "#decision > div /
        #decision .section-body > div { break-inside: avoid }"-Block ist
        komplett entfernt. Diese Regel war spezifischer als
        .exec-decision-box und re-introduzierte die Container-Atomarität,
        die den Clipping-Bug auslöste. Schutz auf <li>-Ebene ist
        ausreichend; generische div-Wrapper duerfen jetzt umbrechen.
        (Pre-1027.5-H1-Variante prüfte zusaetzlich, dass kein 'figure'
        mehr im Selektor steht — beides obsolet durch Entfernung des
        gesamten Blocks.)"""
        tpl = _read_template()
        # Aktive (nicht-kommentar) Regel mit "#decision > div" als
        # Selektor und avoid-Konstraint im Body darf nicht existieren.
        rule = re.search(
            r'^\s*#decision\s*>\s*div[^{]*\{[^}]*break-inside\s*:\s*avoid',
            tpl,
            re.MULTILINE | re.DOTALL,
        )
        assert rule is None, (
            "Aktive '#decision > div { break-inside: avoid }'-Regel gefunden — "
            "1027.5-H1 hat sie entfernt, Regression."
        )
