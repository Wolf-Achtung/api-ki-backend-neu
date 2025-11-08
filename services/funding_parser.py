# -*- coding: utf-8 -*-
from __future__ import annotations
"""Förderprogramm-Parser (statisch + JSON seed, filtert nach Bundesland/Größe)."""
import json
from pathlib import Path
from typing import List, Dict, Any

DEFAULT_PROGRAMS = [
    {
        "name":"Digital Jetzt (BMWK)",
        "region":"DE",
        "target":"KMU (bis 499 MA)",
        "amount":"bis 50.000 € (50%)",
        "deadline":"31.03.2026",
        "url":"https://www.bmwi.de/Redaktion/DE/Dossier/digital-jetzt.html",
        "best_for_size":["solo","kmu"],
        "best_for_industries":["beratung","dienstleistungen","handel","it"],
    },
    {
        "name":"go-digital (BMWK)",
        "region":"DE",
        "target":"Beratungszuschuss",
        "amount":"bis 16.500 € (50%)",
        "deadline":"laufend",
        "url":"https://www.bmwi.de/Redaktion/DE/Dossier/go-digital.html",
        "best_for_size":["kmu"],
        "best_for_industries":["beratung","dienstleistungen","handel","it"],
    },
    {
        "name":"Berlin – Pro FIT",
        "region":"BE",
        "target":"FuE/Innovation",
        "amount":"variabel (Zuschuss/Darlehen)",
        "deadline":"rollierend",
        "url":"https://www.ibb.de/de/foerderprogramme/pro-fit.html",
        "best_for_size":["kmu","enterprise"],
        "best_for_industries":["it","industrie","forschung"],
    }
]

def _load_seed() -> List[Dict[str,Any]]:
    p = Path("data/funding_programs.json")
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return DEFAULT_PROGRAMS

def suggest_programs(briefing: Dict[str,Any]) -> List[Dict[str,Any]]:
    progs = _load_seed()
    land = (briefing.get("bundesland") or "").upper()
    branche = (briefing.get("branche") or "").lower()
    groesse = (briefing.get("unternehmensgroesse") or "").lower()
    ranked = []
    for f in progs:
        score = 0
        if f.get("region") in ("DE", land):
            score += 2
        if not branche or any(branche.startswith(b) for b in f.get("best_for_industries", [])):
            score += 1
        if not groesse or (groesse in f.get("best_for_size", [])):
            score += 1
        f["_score"] = score
        ranked.append(f)
    ranked.sort(key=lambda x: x["_score"], reverse=True)
    return ranked[:5]

def to_html(programs: List[Dict[str,Any]]) -> str:
    if not programs:
        return "<p class='muted'>Keine passenden Förderprogramme gefunden.</p>"
    rows = []
    rows.append("""<table style="width:100%;border-collapse:collapse">
<thead><tr>
<th style="text-align:left;border-bottom:1px solid #e2e8f0;padding:6px">Programm</th>
<th style="text-align:left;border-bottom:1px solid #e2e8f0;padding:6px">Förderung</th>
<th style="text-align:left;border-bottom:1px solid #e2e8f0;padding:6px">Zielgruppe</th>
<th style="text-align:left;border-bottom:1px solid #e2e8f0;padding:6px">Deadline</th>
<th style="text-align:left;border-bottom:1px solid #e2e8f0;padding:6px">Link</th>
</tr></thead><tbody>""")
    for f in programs:
        rows.append(f"""<tr>
<td style="padding:6px;border-bottom:1px solid #f1f5f9"><strong>{f['name']}</strong></td>
<td style="padding:6px;border-bottom:1px solid #f1f5f9">{f.get('amount','')}</td>
<td style="padding:6px;border-bottom:1px solid #f1f5f9">{f.get('target','')}</td>
<td style="padding:6px;border-bottom:1px solid #f1f5f9">{f.get('deadline','')}</td>
<td style="padding:6px;border-bottom:1px solid #f1f5f9"><a href="{f.get('url','')}" target="_blank">Quelle</a></td>
</tr>""")
    rows.append("</tbody></table>")
    return "\n".join(rows)
