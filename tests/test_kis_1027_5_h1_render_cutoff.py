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


def test_decision_li_atomicity_preserved():
    """<li>-Bullets bleiben atomar — gegen Mid-Sentence-Cuts."""
    tpl = _read_template()
    # Beide Pfade pruefen: #decision-Section-Level und .exec-decision-box-spezifisch
    section_rule = re.search(
        r'#decision\s+(?:[^{]*,\s*)*#decision\s+li[^{]*\{([^}]*)\}',
        tpl,
        re.DOTALL,
    )
    box_li_rule = re.search(
        r'\.exec-decision-box\s+li\s*\{([^}]*)\}',
        tpl,
        re.DOTALL,
    )
    # Mindestens einer der beiden Pfade muss li-Atomaritaet sichern
    li_protected = False
    for match in (section_rule, box_li_rule):
        if match and re.search(r'break-inside\s*:\s*avoid', match.group(1)):
            li_protected = True
            break
    assert li_protected, (
        "Weder '#decision li' noch '.exec-decision-box li' "
        "haben break-inside:avoid — Bullet-Schutz fehlt komplett."
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
