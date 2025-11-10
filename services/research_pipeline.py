
# -*- coding: utf-8 -*-
"""
services.research_pipeline
Bündelt Recherchen für Tools & Förderprogramme.
- RESEARCH_PROVIDER: "hybrid" (Tavily + Perplexity), "tavily", "perplexity", "disabled"
- RESEARCH_DAYS: Zeitfenster für Aktualität (Default 14)
"""
from __future__ import annotations
import os, html, datetime
from typing import Dict, Any, List

from .research_clients import search_hybrid, search_tavily, search_perplexity, dedup_and_filter

RESEARCH_PROVIDER = os.getenv("RESEARCH_PROVIDER", "hybrid").strip().lower()
RESEARCH_DAYS = int(os.getenv("RESEARCH_DAYS", "14"))

BUNDESLAND_LABELS = {
    "bw": "Baden-Württemberg","by": "Bayern","be": "Berlin","bb": "Brandenburg","hb": "Bremen","hh": "Hamburg",
    "he": "Hessen","mv": "Mecklenburg-Vorpommern","ni": "Niedersachsen","nw": "Nordrhein-Westfalen",
    "rp": "Rheinland-Pfalz","sl": "Saarland","sn": "Sachsen","st": "Sachsen-Anhalt","sh": "Schleswig-Holstein","th": "Thüringen"
}


def _get_provider_fn():
    if RESEARCH_PROVIDER == "tavily":
        return lambda qs: dedup_and_filter(sum([search_tavily(q, days=RESEARCH_DAYS) for q in qs], []))
    if RESEARCH_PROVIDER == "perplexity":
        return lambda qs: dedup_and_filter(sum([search_perplexity(q, days=RESEARCH_DAYS) for q in qs], []))
    if RESEARCH_PROVIDER in ("hybrid", "auto", ""):
        return lambda qs: search_hybrid(qs, days=RESEARCH_DAYS)
    return lambda qs: []


def _qs_tools(branche: str, groesse: str) -> List[str]:
    b = (branche or "").strip()
    g = (groesse or "").strip()
    return [
        f"best KI tools {b} Germany 2025 DSGVO",
        f"SMB AI tools {b} Germany 2025 privacy compliant",
        f"Open‑Source AI stack for SMEs Germany 2025 {b}",
        f"Azure OpenAI EU + Cognitive Search case study {b} 2025",
    ]


def _qs_funding(bundesland_code_or_label: str) -> List[str]:
    code = (bundesland_code_or_label or "").lower()
    label = BUNDESLAND_LABELS.get(code, None) or bundesland_code_or_label
    return [
        f"Förderprogramm KI {label} 2025 site:*.de",
        f"Digitalisierung Zuschuss {label} 2025 site:*.de",
        f"ZIM Förderung {label} 2025",
        f"go-digital Förderprogramm {label} 2025 BMWK",
    ]


def _to_tools_table(items: List[Dict[str,str]]) -> str:
    # Wir haben nicht immer Kategorie/Preis – konservativ auffüllen.
    rows = []
    for it in items[:12]:
        title = html.escape(it.get("title") or it.get("url") or "Quelle")
        url = html.escape(it.get("url",""))
        rows.append(
            "<tr>"
            f"<td><strong>{title}</strong></td>"
            "<td>—</td>"
            "<td>—</td>"
            "<td>—</td>"
            f"<td><a href='{url}' target='_blank' rel='noopener'>Quelle</a></td>"
            "</tr>"
        )
    if not rows:
        rows = ["<tr><td colspan='5'>Keine aktuellen, seriösen Quellen gefunden.</td></tr>"]
    return (
        "<table class='table'>"
        "<thead><tr><th>Tool/Produkt</th><th>Kategorie</th><th>Preis</th><th>DSGVO/Host</th><th>Links</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def _to_funding_list(items: List[Dict[str,str]]) -> str:
    lis = []
    for it in items[:8]:
        title = html.escape(it.get("title") or it.get("url") or "Programm")
        url = html.escape(it.get("url",""))
        lis.append(f"<li><strong>{title}</strong> – Kurzbeschreibung offen – <a href='{url}' target='_blank' rel='noopener'>Offizielle Infos</a></li>")
    if not lis:
        lis = ["<li>Aktuell keine verlässlichen Informationen gefunden (Stand: Recherchefenster).</li>"]
    return "<ul>" + "".join(lis) + "</ul>"


def run_research(answers: Dict[str, Any]) -> Dict[str, Any]:
    if RESEARCH_PROVIDER == "disabled":
        return {"last_updated": datetime.date.today().isoformat()}
    branche = answers.get("BRANCHE_LABEL") or answers.get("branche") or ""
    groesse = answers.get("UNTERNEHMENSGROESSE_LABEL") or answers.get("unternehmensgroesse") or ""
    bundesland = answers.get("BUNDESLAND_LABEL") or answers.get("bundesland") or ""
    provider_fn = _get_provider_fn()

    # Tools
    tools_qs = _qs_tools(branche, groesse)
    tools_items = provider_fn(tools_qs)

    # Funding
    funding_qs = _qs_funding(bundesland)
    funding_items = provider_fn(funding_qs)

    tools_html = _to_tools_table(tools_items)
    funding_html = _to_funding_list(funding_items)

    return {
        "TOOLS_TABLE_HTML": tools_html,
        "FUNDING_TABLE_HTML": funding_html,
        "last_updated": datetime.date.today().isoformat(),
    }
