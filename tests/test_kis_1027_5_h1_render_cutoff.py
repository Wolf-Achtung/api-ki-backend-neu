# -*- coding: utf-8 -*-
"""FIX-KIS-1027.5-H1: Render-Layer-Cutoff bei R1 S.4 Entscheidungsvorlage.

KIS-1199-Validierung zeigte: trotz sauberer post-Healer-Daten (3 vollständige
<li> in gamechanger_decision/EXECUTIVE_DECISION_HTML) rendert das PDF nur
einen mid-sentence-abgeschnittenen Bullet.

Diagnose:
- .exec-decision-box hatte break-inside:avoid !important
- #decision > div hatte zusätzlich break-inside:avoid (höhere Specificity)
- Bei 3 Bullets >1 Seite zwingt Container-Atomarität Chromium zum Clipping
- (Strukturell analog zum 1027.2.2-A-figure-Wrapper, der in 1027.2.3 entfernt
  wurde — die div-Regel war derselbe Bug auf anderer CSS-Ebene)

Fix: Container-Atomarität entfernt, <li>-Atomarität bleibt. Container darf
über Seitengrenze hinweg fließen, einzelne Bullets bleiben mid-sentence-sicher.
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


def test_exec_decision_box_container_allows_pagebreak():
    """Container .exec-decision-box darf umbrechen — Schutz nur auf li-Ebene."""
    tpl = _read_template()
    rule_match = re.search(
        r'\.exec-decision-box\s*\{([^}]*)\}',
        tpl,
        re.DOTALL,
    )
    assert rule_match, ".exec-decision-box CSS-Regel fehlt"
    body = rule_match.group(1)
    # Strip Kommentar-Zeilen vor dem Check
    active_body = re.sub(r'/\*.*?\*/', '', body, flags=re.DOTALL)
    for prop in ("break-inside", "page-break-inside"):
        active_rule = re.search(
            rf'^\s*{re.escape(prop)}\s*:\s*avoid',
            active_body,
            re.MULTILINE,
        )
        assert active_rule is None, (
            f".exec-decision-box hat aktive {prop}: avoid — "
            f"1027.5-H1 hat sie entfernt, Regression."
        )


def _strip_css_comments(body: str) -> str:
    """Entfernt /* ... */-Kommentare, damit auskommentierte Properties nicht
    als aktive Regeln zaehlen."""
    return re.sub(r'/\*.*?\*/', '', body, flags=re.DOTALL)


def test_decision_li_atomicity_removed():
    """KIS-1027.5.3-B: li-Atomaritaet (break-inside:avoid) auf BEIDEN
    Decision-li-Pfaden entfernt — Vertrag gegenueber der Vorgaenger-Version
    (test_decision_li_atomicity_preserved) umgekehrt.

    In der Kette figure (1027.2.3) -> container (1027.5-H1) -> li war die
    <li>-Ebene die letzte verbliebene Clipping-Quelle: break-inside:avoid
    clippte R1 S.4 mid-sentence trotz #decision { break-before: page }
    (KIS-1210/1211; DB-belegt 1064/1065, decision-span vollstaendig). Sowohl
    '#decision li' als auch '.exec-decision-box li' trugen avoid und clippten.

    Dieser Test schuetzt davor, dass avoid auf einem der beiden li-Pfade
    zurueckkehrt (Regression-Guard, vgl. KIS-1199)."""
    tpl = _read_template()
    # Robuste Regex: matcht auch simples "#decision li { ... }" (ohne
    # vorangestellte Selektor-Liste). [^{}]* ueberspringt eine evtl.
    # Komma-Selektor-Liste, ohne in andere Bloecke zu laufen.
    section_rule = re.search(
        r'#decision\s+li\b[^{}]*\{([^}]*)\}',
        tpl,
        re.DOTALL,
    )
    box_li_rule = re.search(
        r'\.exec-decision-box\s+li\s*\{([^}]*)\}',
        tpl,
        re.DOTALL,
    )
    assert section_rule, "'#decision li'-Regel nicht gefunden"
    assert box_li_rule, "'.exec-decision-box li'-Regel nicht gefunden"

    # avoid muss auf BEIDEN li-Pfaden WEG sein (Kommentare vorher strippen).
    for name, match in (
        ("#decision li", section_rule),
        (".exec-decision-box li", box_li_rule),
    ):
        active_body = _strip_css_comments(match.group(1))
        for prop in ("break-inside", "page-break-inside"):
            assert not re.search(rf'{re.escape(prop)}\s*:\s*avoid', active_body), (
                f"'{name}' hat noch aktives {prop}:avoid — KIS-1027.5.3-B "
                f"hat es entfernt (clippte S.4), avoid darf nicht "
                f"zurueckkehren: {active_body!r}"
            )


def test_no_generic_div_atomicity_in_decision_section():
    """Generische '#decision > div' / '#decision .section-body > div'
    Atomaritaets-Regeln sind entfernt — sie haben höhere Specificity als
    .exec-decision-box und re-introduzierten die Container-Atomarität."""
    tpl = _read_template()
    # Suche nach aktiver Regel (nicht Kommentar) — entweder fehlt der
    # Block ganz, oder er enthält kein break-inside:avoid mehr.
    for selector_pattern in (
        r'^\s*#decision\s*>\s*div\s*[,{]',
        r'^\s*#decision\s+\.section-body\s*>\s*div\s*[,{]',
    ):
        match = re.search(selector_pattern, tpl, re.MULTILINE)
        if not match:
            continue
        # Selektor existiert — prüfe ob der Regel-Body break-inside:avoid hat
        # Sucht von der Selektor-Position nach dem nächsten { ... }-Block
        rest = tpl[match.start():]
        block = re.search(r'\{([^}]*)\}', rest, re.DOTALL)
        if not block:
            continue
        body = block.group(1)
        assert not re.search(r'break-inside\s*:\s*avoid', body), (
            f"Generische '{match.group()}'-Regel hat noch break-inside:avoid — "
            f"1027.5-H1 hat sie entfernt, Regression."
        )
