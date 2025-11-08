# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Any, List

from ._normalize import _briefing_to_dict

MAP = {
    "beratung": [
        {"name":"KI-Check.de", "model":"Online-KI-Assessment (Freemium)", "price":"0–99 €", "weakness":"oberflächliche Tiefe"},
        {"name":"HollandAI", "model":"manuelle KI-Audits", "price":"~2.500 €", "weakness":"keine Automatisierung"},
    ],
    "dienstleistungen": [
        {"name":"Generic AI Consultancy", "model":"Projekt-basiert", "price":"Tagessatz 1.200 €", "weakness":"lange Durchlaufzeit"},
    ],
}

def build_insights(briefing: Dict[str,Any] | Any) -> Dict[str,Any]:
    b = _briefing_to_dict(briefing)
    branche = (b.get("branche") or b.get("branche_label") or "").lower()
    lst = MAP.get(branche, MAP.get("beratung", []))
    usp = [
        "Vollautomatisierte Pipeline (kein manueller Aufwand)",
        "GPT‑gestützte Tiefenanalyse statt Checklisten",
        "Aktualität durch Web‑Recherche (Tavily/Perplexity)",
        "Individuelle PDF‑Reports statt generischer PDFs",
    ]
    return {"competitors": lst, "usp": usp}

def to_html(ins: Dict[str,Any]) -> str:
    if not ins:
        return ""
    rows = ["<h3>Wettbewerber (Auswahl)</h3><table class='table'>",
            "<thead><tr><th>Anbieter</th><th>Modell</th><th>Preis</th><th>Schwäche</th></tr></thead><tbody>"]
    for c in ins.get("competitors", []):
        rows.append(f"""<tr>
<td>{c['name']}</td>
<td>{c['model']}</td>
<td>{c['price']}</td>
<td>{c['weakness']}</td>
</tr>""")
    rows.append("</tbody></table>")
    rows.append("<h3>Ihr Vorteil</h3><ul>")
    for u in ins.get("usp", []):
        rows.append(f"<li>{u}</li>")
    rows.append("</ul>")
    return "\n".join(rows)
