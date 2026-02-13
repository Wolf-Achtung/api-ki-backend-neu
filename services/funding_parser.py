# -*- coding: utf-8 -*-
from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Any

from ._normalize import _briefing_to_dict

DEFAULT_PROGRAMS: List[Dict[str, Any]] = [
    # FIX-R2-6B: go-digital removed (Programm eingestellt seit Dez 2024)
    # Replaced with BAFA Unternehmensberatung as active alternative
    {
        "name": "BAFA Unternehmensberatung",
        "region": "DE",
        "target": "Beratungsförderung für KMU",
        "amount": "bis 3.200 € (50-80%)",
        "deadline": "laufend",
        "url": "https://www.bafa.de",
        "notes": "Beratungsförderung für KMU bis 249 MA; ersetzt go-digital",
    },
    {
        "name": "Berlin – Pro FIT (IBB)",
        "region": "BE",
        "target": "FuE/Innovation",
        "amount": "Zuschuss/Darlehen (variabel)",
        "deadline": "rollierend",
        "url": "https://www.ibb.de",
        "notes": "Typisch für technologiegetriebene Vorhaben; Kombination möglich",
    },
]


def _load_seed() -> List[Dict[str, Any]]:
    p = Path("data/funding_programs.json")
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else DEFAULT_PROGRAMS
        except Exception:
            pass
    return DEFAULT_PROGRAMS


def suggest_programs(briefing: Dict[str, Any] | Any) -> List[Dict[str, Any]]:
    progs = _load_seed()
    b = _briefing_to_dict(briefing)
    land = (b.get("bundesland") or b.get("bundesland_label") or "").upper()
    branche = (b.get("branche") or b.get("branche_label") or "").lower()
    groesse = (b.get("unternehmensgroesse") or b.get("groesse") or "").lower()

    ranked: List[Dict[str, Any]] = []
    for f in progs:
        score = 0
        if f.get("region") in ("DE", land):
            score += 2
        if branche.startswith("beratung"):
            score += 1
            if groesse == "solo":
                score += 1
        if groesse in ("solo", "kmu"):
            score += 1
        ranked.append({**f, "_score": score})
    ranked.sort(key=lambda x: x.get("_score", 0), reverse=True)
    return ranked[:5]


def _link(label: str, url: str | None) -> str:
    if not url:
        return ""
    return f'<a href="{url}" target="_blank" rel="noopener">{label}</a>'


def to_html(programs: List[Dict[str, Any]], research_stand: str | None = None) -> str:
    head = ""
    if research_stand:
        head = f'<div class="stand-hint">Stand: {research_stand}</div>'
    if not programs:
        return head + "<p class='muted'>Keine passenden Förderprogramme gefunden.</p>"
    rows = [head]
    rows.append(
        """<table class="table table-modern">
<thead><tr>
<th>Programm</th>
<th>Förderung</th>
<th>Zielgruppe</th>
<th>Deadline</th>
<th>Quelle</th>
</tr></thead><tbody>"""
    )
    for f in programs:
        rows.append(
            f"""<tr>
<td><strong>{f.get('name','')}</strong></td>
<td>{f.get('amount','')}</td>
<td>{f.get('target','')}</td>
<td>{f.get('deadline','')}</td>
<td>{_link('Förderrichtlinie', f.get('url')) or '—'}</td>
</tr>"""
        )
    rows.append("</tbody></table>")
    return "\n".join(rows)
