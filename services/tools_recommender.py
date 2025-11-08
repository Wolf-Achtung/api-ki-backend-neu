# -*- coding: utf-8 -*-
from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Any

from ._normalize import _briefing_to_dict

# Kuratierter Seed; kann per data/tools_seed.json überschrieben/ergänzt werden.
DEFAULT_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "Tally.so",
        "url": "https://tally.so",
        "trust_url": "https://tally.so/help/privacy",
        "category": "Fragebogen / Intake",
        "price": "0–29 €/Monat",
        "gdpr": "EU-Option",
        "host": "EU (Option)",
        "best_for_size": ["solo","kmu"],
        "best_for_industries": ["beratung","dienstleistungen","marketing"]
    },
    {
        "name": "Make (Integromat)",
        "url": "https://www.make.com",
        "trust_url": "https://www.make.com/en/privacy-notice",
        "category": "Automation / Workflows",
        "price": "ab 9 €/Monat",
        "gdpr": "EU-Server",
        "host": "EU",
        "best_for_size": ["solo","kmu","enterprise"],
        "best_for_industries": ["beratung","dienstleistungen","handel","it"]
    },
    {
        "name": "Railway.app",
        "url": "https://railway.app",
        "trust_url": "https://railway.app/legal/privacy",
        "category": "Hosting / Deployment",
        "price": "ab ~5 € (Nutzung)",
        "gdpr": "US (AVV prüfen)",
        "host": "US",
        "best_for_size": ["solo","kmu"],
        "best_for_industries": ["it","dienstleistungen","beratung"]
    },
    {
        "name": "Notion",
        "url": "https://www.notion.so",
        "trust_url": "https://www.notion.so/privacy",
        "category": "Wissensmanagement",
        "price": "0–10 €/Monat",
        "gdpr": "EU-Option",
        "host": "EU/US",
        "best_for_size": ["solo","kmu","enterprise"],
        "best_for_industries": ["beratung","dienstleistungen","marketing"]
    },
    {
        "name": "HubSpot",
        "url": "https://www.hubspot.de",
        "trust_url": "https://legal.hubspot.com/privacy-policy",
        "category": "CRM / Sales",
        "price": "Free / ab 18 €/Monat",
        "gdpr": "AVV verfügbar",
        "host": "EU/US",
        "best_for_size": ["kmu","enterprise"],
        "best_for_industries": ["beratung","dienstleistungen","handel"]
    },
    {
        "name": "OpenAI API",
        "url": "https://platform.openai.com",
        "trust_url": "https://openai.com/policies/privacy-policy",
        "category": "KI-API",
        "price": "Usage-basiert",
        "gdpr": "US (Vendor-Assessment)",
        "host": "US",
        "best_for_size": ["solo","kmu","enterprise"],
        "best_for_industries": ["it","dienstleistungen","beratung","marketing"]
    },
    {
        "name": "Mistral AI",
        "url": "https://mistral.ai",
        "trust_url": "https://mistral.ai/legal/privacy/",
        "category": "KI-API (EU)",
        "price": "Usage-basiert",
        "gdpr": "EU-Anbieter",
        "host": "EU",
        "best_for_size": ["solo","kmu","enterprise"],
        "best_for_industries": ["it","dienstleistungen","beratung"]
    },
    {
        "name": "Perplexity API",
        "url": "https://www.perplexity.ai",
        "trust_url": "https://www.perplexity.ai/privacy",
        "category": "Antwort-/Recherche-API",
        "price": "Usage/Pro",
        "gdpr": "US (Vendor-Assessment)",
        "host": "US",
        "best_for_size": ["solo","kmu"],
        "best_for_industries": ["beratung","dienstleistungen","marketing","it"]
    },
    {
        "name": "Tavily",
        "url": "https://www.tavily.com",
        "trust_url": "https://www.tavily.com/privacy",
        "category": "Web-Recherche (API)",
        "price": "Usage",
        "gdpr": "US (Vendor-Assessment)",
        "host": "US",
        "best_for_size": ["solo","kmu","enterprise"],
        "best_for_industries": ["it","dienstleistungen","beratung"]
    },
    {
        "name": "Cloudflare Turnstile",
        "url": "https://www.cloudflare.com/products/turnstile/",
        "trust_url": "https://www.cloudflare.com/privacypolicy/",
        "category": "Formular-Schutz",
        "price": "Kostenlos",
        "gdpr": "EU/US (AVV)",
        "host": "EU/US",
        "best_for_size": ["solo","kmu","enterprise"],
        "best_for_industries": ["alle"]
    }
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

    ranked: List[Dict[str,Any]] = []
    for t in tools:
        score = 0
        industries = [x.lower() for x in t.get("best_for_industries", [])]
        sizes = [x.lower() for x in t.get("best_for_size", [])]
        if not branche or any(branche.startswith(bi) or bi == "alle" for bi in industries):
            score += 2
        if not groesse or (groesse in sizes or "alle" in sizes):
            score += 2
        # leichte Bevorzugung Intake/Automation bei Beratungen
        cat = (t.get("category","") or "").lower()
        if "fragebogen" in cat or "intake" in cat or "automation" in cat:
            score += 1
        t = dict(t)
        t["_score"] = score
        ranked.append(t)
    ranked.sort(key=lambda x: x.get("_score", 0), reverse=True)
    return ranked[:10]

def _link(label: str, url: str | None) -> str:
    if not url:
        return ""
    return f'<a href="{url}" target="_blank" rel="noopener">{label}</a>'

def to_html(tools: List[Dict[str,Any]]) -> str:
    if not tools:
        return "<p class='muted'>Keine passenden Tools gefunden.</p>"
    rows = []
    rows.append("""<table class="table">
<thead><tr>
<th>Tool/Produkt</th>
<th>Kategorie</th>
<th>Preis</th>
<th>DSGVO/Host</th>
<th>Links</th>
</tr></thead><tbody>""")
    for t in tools:
        links = []
        if t.get("url"):
            links.append(_link("Quelle", t["url"]))
        if t.get("trust_url"):
            links.append(_link("Trust&nbsp;Center", t["trust_url"]))
        link_html = " · ".join(links) if links else "—"
        rows.append(f"""<tr>
<td><strong>{t.get('name','')}</strong></td>
<td>{t.get('category','')}</td>
<td>{t.get('price','')}</td>
<td>{t.get('gdpr','')} – {t.get('host','')}</td>
<td>{link_html}</td>
</tr>""")
    rows.append("</tbody></table>")
    return "\n".join(rows)
