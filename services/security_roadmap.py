# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Any, List
from ._normalize import _briefing_to_dict

def build_security_roadmap(briefing: Dict[str,Any] | Any, scores: Dict[str,Any] | None = None) -> Dict[str,Any]:
    b = _briefing_to_dict(briefing)
    gaps: List[Dict[str,Any]] = []
    steps: List[Dict[str,Any]] = []
    # grobe Heuristik anhand b:
    if not b.get("zweifaktor") and not b.get("mfa_enabled"):
        gaps.append({"item":"2FA für Admin-Logins", "points":3})
        steps.append({"title":"2FA für Admin-Zugänge aktivieren", "impact_points":3, "effort":"< 1 Tag", "cost":"~0–100 €"})
    if not b.get("dpa_avv"):
        gaps.append({"item":"AVV/DPAs für KI-Anbieter", "points":2})
        steps.append({"title":"AVV mit KI-Anbietern abschließen", "impact_points":2, "effort":"1–2 Tage", "cost":"0 €"})
    gaps.append({"item":"Penetrationstest (jährlich)", "points":5})
    steps.append({"title":"Penetrationstest beauftragen", "impact_points":5, "effort":"2 Wochen", "cost":"2.000–5.000 €"})
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
