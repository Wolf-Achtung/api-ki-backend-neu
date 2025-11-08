# -*- coding: utf-8 -*-
from __future__ import annotations
"""Einfache Sicherheits-Gap-Analyse mit next steps (+Punkte)."""
from typing import Dict, Any, List

def build_security_roadmap(briefing: Dict[str,Any], scores: Dict[str,Any]|None=None) -> Dict[str,Any]:
    # Dummy-Heuristik: nimmt vorhandene Felder, erzeugt plausible Gaps
    gaps: List[Dict[str,Any]] = []
    steps: List[Dict[str,Any]] = []
    # Beispiel-Gaps (würde man mit echten Feldern befüllen)
    gaps.append({"item":"Penetrationstest (jährlich)", "points":5})
    gaps.append({"item":"Verschlüsselung at rest", "points":4})
    gaps.append({"item":"2FA für Admin-Logins", "points":3})
    # Schritte
    steps.append({"title":"2FA für Admin-Zugänge aktivieren", "impact_points":3, "effort":"< 1 Tag", "cost":"~0–100 €"})
    steps.append({"title":"Penetrationstest beauftragen", "impact_points":5, "effort":"2 Wochen", "cost":"2.000–5.000 €"})
    steps.append({"title":"DPIA durchführen (falls zutreffend)", "impact_points":4, "effort":"1 Tag", "cost":"0–500 €"})
    return {"gaps":gaps, "steps":steps}

def to_html(roadmap: Dict[str,Any]) -> str:
    if not roadmap:
        return ""
    gaps = roadmap.get("gaps", [])
    steps = roadmap.get("steps", [])
    parts = []
    if gaps:
        parts.append("<h3>Warum nicht 100/100?</h3><ul>")
        for g in gaps:
            parts.append(f"<li>{g['item']} – fehlt (≈ +{g['points']} Punkte)</li>")
        parts.append("</ul>")
    if steps:
        parts.append("<h3>Nächste Schritte</h3><ol>")
        for s in steps:
            parts.append(f"<li><strong>{s['title']}</strong> · Wirkung: +{s['impact_points']} · Aufwand: {s['effort']} · Kosten: {s['cost']}</li>")
        parts.append("</ol>")
    return "\n".join(parts)
