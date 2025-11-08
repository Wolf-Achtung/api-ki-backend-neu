# -*- coding: utf-8 -*-
from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Any

from ._normalize import _briefing_to_dict

DEFAULT_TOOLS = [
    {
        "name":"Tally.so", "url":"https://tally.so",
        "category":"Fragebogen / Intake",
        "price":"0–29 €/Monat",
        "gdpr":"✓ EU-Server (optionen)",
        "host":"EU (Option)",
        "best_for_size":["solo","kmu"],
        "best_for_industries":["beratung","dienstleistungen","marketing"]
    },
    {
        "name":"Make (Integromat)", "url":"https://www.make.com",
        "category":"Automation / Workflows",
        "price":"ab 9 €/Monat",
        "gdpr":"✓ EU-Server",
        "host":"EU",
        "best_for_size":["solo","kmu","enterprise"],
        "best_for_industries":["beratung","dienstleistungen","handel","it"]
    },
    {
        "name":"Railway.app", "url":"https://railway.app",
        "category":"Hosting / Deployment",
        "price":"ab ~5 € (Nutzung)",
        "gdpr":"⚠︎ US-Hosting",
        "host":"US",
        "best_for_size":["solo","kmu"],
        "best_for_industries":["it","dienstleistungen","beratung"]
    },
    {
        "name":"Notion", "url":"https://www.notion.so",
        "category":"Wissensmanagement",
        "price":"0–10 €/Monat",
        "gdpr":"✓ EU-Option",
        "host":"EU/US",
        "best_for_size":["solo","kmu","enterprise"],
        "best_for_industries":["beratung","dienstleistungen","marketing"]
    },
    {
        "name":"HubSpot", "url":"https://www.hubspot.de",
        "category":"CRM / Sales",
        "price":"Free / ab 18 €/Monat",
        "gdpr":"✓ AVV verfügbar",
        "host":"EU/US",
        "best_for_size":["kmu","enterprise"],
        "best_for_industries":["beratung","dienstleistungen","handel"]
    },
    {
        "name":"OpenAI API", "url":"https://platform.openai.com",
        "category":"KI-API",
        "price":"Usage-basiert",
        "gdpr":"⚠︎ US (Vendor-Assessment)",
        "host":"US",
        "best_for_size":["solo","kmu","enterprise"],
        "best_for_industries":["it","dienstleistungen","beratung","marketing"]
    },
]

def _load_seed() -> List[Dict[str,Any]]:
    seed_file = Path("data/tools_seed.json")
    if seed_file.exists():
        try:
            return json.loads(seed_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return DEFAULT_TOOLS

def recommend_tools(briefing: Dict[str,Any] | Any) -> List[Dict[str,Any]]:
    tools = _load_seed()
    b = _briefing_to_dict(briefing)
    branche = (b.get("branche") or b.get("branche_label") or "").lower()
    groesse = (b.get("unternehmensgroesse") or b.get("groesse") or "").lower()
    ranked = []
    for t in tools:
        score = 0
        if not branche or any(branche.startswith(bi) for bi in t.get("best_for_industries", [])):
            score += 2
        if not groesse or (groesse in t.get("best_for_size", [])):
            score += 2
        if "automation" in (t.get("category","").lower()):
            score += 1
        if "fragebogen" in (t.get("category","").lower()) or "intake" in (t.get("category","").lower()):
            score += 1
        t["_score"] = score
        ranked.append(t)
    ranked.sort(key=lambda x: x["_score"], reverse=True)
    return ranked[:10]

def to_html(tools: List[Dict[str,Any]]) -> str:
    if not tools:
        return "<p class='muted'>Keine passenden Tools gefunden.</p>"
    rows = []
    rows.append("""<table style="width:100%;border-collapse:collapse">
<thead><tr>
<th style="text-align:left;border-bottom:1px solid #e2e8f0;padding:6px">Tool/Produkt</th>
<th style="text-align:left;border-bottom:1px solid #e2e8f0;padding:6px">Kategorie</th>
<th style="text-align:left;border-bottom:1px solid #e2e8f0;padding:6px">Preis</th>
<th style="text-align:left;border-bottom:1px solid #e2e8f0;padding:6px">DSGVO/Host</th>
<th style="text-align:left;border-bottom:1px solid #e2e8f0;padding:6px">Link</th>
</tr></thead><tbody>""")
    for t in tools:
        rows.append(f"""<tr>
<td style="padding:6px;border-bottom:1px solid #f1f5f9"><strong>{t['name']}</strong></td>
<td style="padding:6px;border-bottom:1px solid #f1f5f9">{t.get('category','')}</td>
<td style="padding:6px;border-bottom:1px solid #f1f5f9">{t.get('price','')}</td>
<td style="padding:6px;border-bottom:1px solid #f1f5f9">{t.get('gdpr','')} – {t.get('host','')}</td>
<td style="padding:6px;border-bottom:1px solid #f1f5f9"><a href="{t.get('url','')}" target="_blank">Quelle</a></td>
</tr>""")
    rows.append("</tbody></table>")
    return "\n".join(rows)
