# -*- coding: utf-8 -*-
"""
services/content_normalizer.py
------------------------------
Sorgt dafür, dass die vom LLM gelieferten Inhalte **immer** zu den
Platzhaltern im PDF-Template passen – inkl. Spaltensplitting, Alias-Keys,
Score-Feldern und sinnvollen Defaults (Transparenztext, Ersparniswerte).
"""
from __future__ import annotations

import re
from html import unescape
from typing import Any, Dict, Tuple

# -----------------------------------------------------------------------------
# Regexe
# -----------------------------------------------------------------------------
LI_RE = re.compile(r"<li\b[^>]*>.*?</li>", re.IGNORECASE | re.DOTALL)
HOURS_RE = re.compile(r"(?P<val>\d+(?:[.,]\d+)?)\s*(?:h|std|stunden)\b", re.IGNORECASE)
MIN_RE = re.compile(r"(?P<val>\d+(?:[.,]\d+)?)\s*(?:min|minute[n]?)\b", re.IGNORECASE)

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _to_float(s: str) -> float:
    s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0

def _split_ul_two_columns(ul_html: str) -> Tuple[str, str]:
    """Teilt eine <ul> Liste in zwei annähernd gleich große Spalten."""
    if not ul_html:
        return "<ul></ul>", "<ul></ul>"
    items = LI_RE.findall(ul_html) or []
    if not items:
        # Kein valides <li> – alles links
        return f"<ul>{ul_html}</ul>", "<ul></ul>"
    mid = (len(items) + 1) // 2
    left = "<ul>" + "".join(items[:mid]) + "</ul>"
    right = "<ul>" + "".join(items[mid:]) + "</ul>"
    return left, right

def _split_business_case(html: str) -> Tuple[str, str]:
    """
    Teilt Business-Case-HTML grob in (ROI_HTML, COSTS_OVERVIEW_HTML).
    Erwartet idealerweise zwei <table>-Blöcke. Fällt sonst auf Halbierung zurück.
    """
    if not html:
        return "", ""
    parts = re.split(r"</table>", html, flags=re.IGNORECASE)
    if len(parts) >= 2:
        roi = parts[0] + "</table>"
        costs = "</table>".join(parts[1:]).strip()
        if costs and "<table" not in costs.lower():
            costs = f"<div>{costs}</div>"
        return roi, costs
    # Fallback: Halbieren
    half = len(html) // 2
    return html[:half], html[half:]

def _sanitize_html(value: str) -> str:
    if not isinstance(value, str):
        return ""
    v = value.strip()
    # Fences entfernen
    if v.startswith("```"):
        v = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", v, flags=re.DOTALL).strip()
    # Entities normalisieren
    v = unescape(v)
    return v

def _compute_savings_from_quickwins(html: str, default_hourly: float = 60.0) -> Dict[str, Any]:
    """
    Versucht, aus der Quick-Wins-Liste h/Monat abzuleiten.
    Erlaubt Angaben in Stunden **oder** Minuten.
    """
    if not html:
        return {
            "stundensatz_eur": int(default_hourly),
            "monatsersparnis_stunden": 0,
            "monatsersparnis_eur": 0,
            "jahresersparnis_stunden": 0,
            "jahresersparnis_eur": 0,
        }

    total_hours = 0.0
    # Stunden angaben
    for m in HOURS_RE.finditer(html):
        total_hours += _to_float(m.group("val"))
    # Minuten -> Stunden
    for m in MIN_RE.finditer(html):
        total_hours += _to_float(m.group("val")) / 60.0

    total_hours = round(total_hours, 1)
    monthly_eur = int(round(total_hours * default_hourly))
    yearly_hours = int(round(total_hours * 12))
    yearly_eur = int(round(monthly_eur * 12))

    return {
        "stundensatz_eur": int(default_hourly),
        "monatsersparnis_stunden": total_hours,
        "monatsersparnis_eur": monthly_eur,
        "jahresersparnis_stunden": yearly_hours,
        "jahresersparnis_eur": yearly_eur,
    }

# -----------------------------------------------------------------------------
# Public
# -----------------------------------------------------------------------------

def normalize_and_enrich_sections(
    sections: Dict[str, str] | None,
    answers: Dict[str, Any] | None = None,
    scores: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Vereinheitlicht Keys (Alias), splittet Inhalte, reichert Meta an (Scores, Transparenz, Ersparnis).
    Gibt ein Dict zurück, das direkt als Template-Kontext genutzt werden kann.
    """
    sections = dict(sections or {})
    out: Dict[str, Any] = {}

    # 1) Rohwerte sanitisieren
    for k, v in sections.items():
        out[k] = _sanitize_html(v)

    # 2) Aliasse & Splits
    # Executive Summary
    if "EXECUTIVE_SUMMARY_HTML" not in out and "EXEC_SUMMARY_HTML" in out:
        out["EXECUTIVE_SUMMARY_HTML"] = out["EXEC_SUMMARY_HTML"]

    # Roadmap → Pilot-Plan
    if "PILOT_PLAN_HTML" not in out and "ROADMAP_HTML" in out:
        out["PILOT_PLAN_HTML"] = out["ROADMAP_HTML"]

    # Business Case → ROI/Kosten
    if ("ROI_HTML" not in out or "COSTS_OVERVIEW_HTML" not in out) and "BUSINESS_CASE_HTML" in out:
        roi, costs = _split_business_case(out.get("BUSINESS_CASE_HTML", ""))
        out.setdefault("ROI_HTML", roi)
        out.setdefault("COSTS_OVERVIEW_HTML", costs)

    # Quick Wins zweispaltig
    if ("QUICK_WINS_HTML_LEFT" not in out or "QUICK_WINS_HTML_RIGHT" not in out) and "QUICK_WINS_HTML" in out:
        left, right = _split_ul_two_columns(out.get("QUICK_WINS_HTML", ""))
        out.setdefault("QUICK_WINS_HTML_LEFT", left)
        out.setdefault("QUICK_WINS_HTML_RIGHT", right)

    # Risiken – Alias tolerieren
    if "RISKS_HTML" not in out and "RISK_HTML" in out:
        out["RISKS_HTML"] = out["RISK_HTML"]

    # 3) Transparenztext & Defaults
    default_transparency = (
        "Dieser Report wurde teilweise mithilfe von KI‑Systemen erstellt und nach "
        "Best‑Practice im europäischen Rechtsrahmen (EU AI Act, DSGVO) kuratiert."
    )
    out.setdefault("transparency_text", default_transparency)

    # 4) Scores in Template‑Felder übertragen
    scores = scores or {}
    out.setdefault("score_governance", int(scores.get("governance", 0)))
    out.setdefault("score_sicherheit", int(scores.get("security", 0)))
    out.setdefault("score_nutzen", int(scores.get("value", 0)))
    out.setdefault("score_befaehigung", int(scores.get("enablement", 0)))
    out.setdefault("score_gesamt", int(scores.get("overall", 0)))

    # 5) Ersparnis aus Quick Wins grob schätzen (falls nicht vorhanden)
    if "stundensatz_eur" not in out or "monatsersparnis_stunden" not in out:
        savings = _compute_savings_from_quickwins(out.get("QUICK_WINS_HTML", ""),
                                                  default_hourly=60.0)
        out.update(savings)

    return out
