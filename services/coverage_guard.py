# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Any, List
import html

EXPECTED_FIELDS = [
    "BRANCHE_LABEL","UNTERNEHMENSGROESSE_LABEL","BUNDESLAND_LABEL","jahresumsatz",
    "ki_ziele","strategische_ziele","vision_3_jahre","vision_prioritaet",
    "anwendungsfaelle","ki_projekte","pilot_bereich","hauptleistung",
    "governance_richtlinien","datenschutz","datenschutzbeauftragter","folgenabschaetzung","technische_massnahmen",
    "ki_kompetenz","ki_knowhow","trainings_interessen","zeitbudget","change_management","innovationsprozess",
    "investitionsbudget","stundensatz_eur","email","kontakt_email",
]

USED_IN_REPORT = set(EXPECTED_FIELDS)  # konservativ: alle gelten als genutzt, Mapping prüft Anwesenheit

def _is_filled(val: Any) -> bool:
    if val is None: return False
    if isinstance(val, str): return val.strip() != ""
    if isinstance(val, (list, tuple, set, dict)): return len(val) > 0
    return True

def analyze_coverage(answers: Dict[str, Any]) -> Dict[str, Any]:
    present = [f for f in EXPECTED_FIELDS if _is_filled(answers.get(f))]
    used = [f for f in present if f in USED_IN_REPORT]
    missing = [f for f in present if f not in USED_IN_REPORT]
    coverage = int(round(100.0 * (len(used) / max(1, len(present)))))
    return {"present": present, "used": used, "missing": missing, "coverage_pct": coverage, "present_count": len(present)}

def build_html_report(result: Dict[str, Any]) -> str:
    if not result: return ""
    missing = result.get("missing", [])
    rows = "".join(f"<li><code>{html.escape(k)}</code></li>" for k in missing) or "<li>—</li>"
    return (
        "<div class='fb-section'>"
        "<div class='fb-head'><span class='fb-step'>Intern</span><h3 class='fb-title'>Daten‑Coverage (Formular → Report)</h3></div>"
        f"<p><strong>Abdeckung:</strong> {result.get('coverage_pct',0)}% · Felder befüllt: {result.get('present_count',0)}</p>"
        "<div class='callout'><strong>Nicht verwertete, aber ausgefüllte Felder:</strong>"
        f"<ul>{rows}</ul>"
        "<p class='small muted'>Hinweis: Heuristik. Einige Felder fließen indirekt in Scores/Texte ein.</p>"
        "</div></div>"
    )
