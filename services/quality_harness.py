# -*- coding: utf-8 -*-
from __future__ import annotations
import re
from typing import Dict, List

REQUIRED_SECTIONS = [
    "EXECUTIVE_SUMMARY_HTML","QUICK_WINS_HTML_LEFT","QUICK_WINS_HTML_RIGHT",
    "PILOT_PLAN_HTML","ROADMAP_12M_HTML","ROI_HTML","COSTS_OVERVIEW_HTML",
    "BUSINESS_CASE_HTML","BUSINESS_SENSITIVITY_HTML","DATA_READINESS_HTML",
    "ORG_CHANGE_HTML","RISKS_HTML","GAMECHANGER_HTML","RECOMMENDATIONS_HTML"
]

def _has_fenced_code(s: str) -> bool:
    return "```" in (s or "")

def _needs_basic_tags(s: str) -> bool:
    s = (s or "").lower()
    return not any(t in s for t in ("<p", "<ul", "<table", "<div", "<h4"))

def run_quality_checks(sections: Dict[str,str]) -> List[str]:
    issues: List[str] = []
    # neutral tone check for Exec-Summary
    es = sections.get("EXECUTIVE_SUMMARY_HTML","")
    if _has_fenced_code(es): issues.append("Executive Summary enthält Code-Fences")
    if _needs_basic_tags(es): issues.append("Executive Summary ohne Basistags")
    if re.search(r"\\b(wir|unser|ich)\\b", es, flags=re.IGNORECASE):
        issues.append("Executive Summary nicht neutral (Wir/Ich-Formulierungen)")
    # presence of required sections
    for k in REQUIRED_SECTIONS:
        if not sections.get(k): issues.append(f"Abschnitt fehlt oder leer: {k}")
    # quick wins shouldn't contain fences
    qw = (sections.get("QUICK_WINS_HTML_LEFT","") or "") + (sections.get("QUICK_WINS_HTML_RIGHT","") or "")
    if _has_fenced_code(qw): issues.append("Quick Wins enthalten Code-Fences")
    return issues
