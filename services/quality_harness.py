# -*- coding: utf-8 -*-
"""Simple Quality Harness (Gold-Standard+)
- HTML sanity (no fenced code blocks, presence of basic tags)
- Tone check (no "Wir/Unser/Ich" in Summary)
- Quick-Wins sums consistency (optional; calculated upstream)
"""
from __future__ import annotations
import re
from typing import Dict, List

def _has_fenced_code(s: str) -> bool:
    return "```" in (s or "")

def _needs_basic_tags(s: str) -> bool:
    s = s or ""
    return not any(t in s.lower() for t in ("<p", "<ul", "<table", "<div"))

def run_quality_checks(sections: Dict[str,str]) -> List[str]:
    issues: List[str] = []
    es = sections.get("EXECUTIVE_SUMMARY_HTML","")
    if _has_fenced_code(es): issues.append("Executive Summary enthält Code-Fences")
    if _needs_basic_tags(es): issues.append("Executive Summary ohne Basistags")
    if re.search(r"\b(wir|unser|ich)\b", es, flags=re.IGNORECASE):
        issues.append("Executive Summary nicht neutral (Wir/Ich-Formulierungen)")

    qw = (sections.get("QUICK_WINS_HTML_LEFT","") or "") + (sections.get("QUICK_WINS_HTML_RIGHT","") or "")
    if _has_fenced_code(qw): issues.append("Quick Wins enthalten Code-Fences")
    return issues
