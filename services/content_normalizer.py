# -*- coding: utf-8 -*-
"""
Content‑Normalizer & Enricher (v2 mit Branchen‑KPIs)
====================================================
Zusatz zu v1: branchenspezifisches KPI‑Set als eigener HTML‑Block.
"""
from __future__ import annotations

import html
import os
import re
from typing import Any, Dict, List, Tuple

from services.playbooks import build_playbooks_html, normalize_industry
from services.research_policy import ResearchPolicy
from services.kpi_sets import build_kpi_table_html


def _clean_html(s: str | None) -> str:
    s = (s or "").strip()
    s = s.replace("```html", "").replace("```", "")
    return s


def _split_quickwins_to_columns(qw_html: str) -> Tuple[str, str, int]:
    items = re.findall(r"<li>(.*?)</li>", qw_html, flags=re.IGNORECASE | re.DOTALL)
    hours_total = 0
    parsed_items: List[str] = []
    for it in items:
        m = re.search(r"ersparnis[:\s]*([0-9]+)\s*h", it, flags=re.IGNORECASE)
        h = int(m.group(1)) if m else 0
        hours_total += h
        parsed_items.append(f"<li>{it}</li>")
    half = (len(parsed_items) + 1) // 2
    left = "<ul>" + "".join(parsed_items[:half]) + "</ul>"
    right = "<ul>" + "".join(parsed_items[half:]) + "</ul>"
    return left, right, hours_total


def _eur(x: float) -> str:
    return f"{int(round(x, 0)):,}".replace(",", ".")


def normalize_and_enrich_sections(sections: Dict[str, str], answers: Dict[str, Any], scores: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}

    out["EXECUTIVE_SUMMARY_HTML"] = _clean_html(sections.get("EXECUTIVE_SUMMARY_HTML") or sections.get("EXEC_SUMMARY_HTML"))
    out["PILOT_PLAN_HTML"] = _clean_html(sections.get("PILOT_PLAN_HTML") or sections.get("ROADMAP_HTML"))

    business_html = _clean_html(sections.get("ROI_HTML") or sections.get("BUSINESS_CASE_HTML") or "")
    if "<table" in business_html:
        parts = re.split(r"</table>", business_html, flags=re.IGNORECASE)
        roi = parts[0] + "</table>" if parts else ""
        costs = parts[1] + "</table>" if len(parts) > 1 else ""
        out["ROI_HTML"] = roi
        out["COSTS_OVERVIEW_HTML"] = costs or "<p>—</p>"
    else:
        out["ROI_HTML"] = "<p>—</p>"
        out["COSTS_OVERVIEW_HTML"] = "<p>—</p>"

    qw_html = _clean_html(sections.get("QUICK_WINS_HTML") or sections.get("QUICK_WINS"))
    left, right, hpm = _split_quickwins_to_columns(qw_html)
    out["QUICK_WINS_HTML_LEFT"] = left
    out["QUICK_WINS_HTML_RIGHT"] = right

    stundensatz = float(os.getenv("DEFAULT_STUNDENSATZ_EUR", "60") or "60")
    out["monatsersparnis_stunden"] = str(hpm)
    out["monatsersparnis_eur"] = _eur(hpm * stundensatz)
    out["jahresersparnis_stunden"] = str(hpm * 12)
    out["jahresersparnis_eur"] = _eur(hpm * 12 * stundensatz)
    out["stundensatz_eur"] = str(int(stundensatz))

    out["score_governance"] = scores.get("governance", 0)
    out["score_sicherheit"] = scores.get("security", 0)
    out["score_nutzen"] = scores.get("value", 0)
    out["score_befaehigung"] = scores.get("enablement", 0)
    out["score_gesamt"] = scores.get("overall", 0)

    t = os.getenv("TRANSPARENCY_TEXT", "")\
        .replace("ich schwöre", "").replace("ich schwoere", "").strip()
    if not t:
        t = ("Dieser Report wurde teilweise mithilfe von KI‑Systemen erstellt und im europäischen "
             "Rechtsrahmen (EU AI Act, DSGVO) geprüft. Alle Empfehlungen werden künftig redaktionell kuratiert.")
    out["transparency_text"] = html.escape(t)

    # KPI‑Dashboard (kompakt) + Branchen‑KPIs
    out["KPI_HTML"] = (
        "<table class='table'>"
        "<tbody>"
        f"<tr><th>Reifegrad gesamt</th><td>{out['score_gesamt']}/100</td></tr>"
        f"<tr><th>Monats‑Ersparnis</th><td>{out['monatsersparnis_stunden']} h (≈ {out['monatsersparnis_eur']} €)</td></tr>"
        f"<tr><th>Jahres‑Ersparnis</th><td>{out['jahresersparnis_stunden']} h (≈ {out['jahresersparnis_eur']} €)</td></tr>"
        f"<tr><th>Stundensatz</th><td>{out['stundensatz_eur']} €/h</td></tr>"
        "</tbody></table>"
    )
    out["KPI_BRANCHE_HTML"] = build_kpi_table_html(answers.get("branche"))

    # Playbooks
    out["PLAYBOOKS_HTML"] = build_playbooks_html(
        branche=answers.get("branche") or answers.get("branche_name"),
        unternehmensgroesse=answers.get("unternehmensgroesse"),
    )

    rp = ResearchPolicy()
    branche = normalize_industry(answers.get("branche"))
    tools = rp.search_tools(branche=branche, days=None)
    out["TOOLS_HTML"] = rp.results_to_html(tools, "Aktuell keine qualifizierten Tool‑Ergebnisse.")

    foerd = rp.search_funding(
        bundesland=answers.get("bundesland", ""),
        branche=branche,
        days=None,
    )
    out["FOERDERPROGRAMME_HTML"] = rp.results_to_html(foerd, "Keine passenden Förderprogramme gefunden.")

    out["RISKS_HTML"] = _clean_html(sections.get("RISKS_HTML") or "") or (
        "<table class='table'><thead><tr><th>Risiko</th><th>Eintritt</th><th>Auswirkung</th><th>Mitigation</th></tr></thead>"
        "<tbody>"
        "<tr><td>Datenschutz/DSGVO</td><td>mittel</td><td>Bußgelder/Vertrauen</td><td>DPA/TOMs, Löschkonzept</td></tr>"
        "<tr><td>Halluzinationen</td><td>hoch</td><td>Fehlentscheidungen</td><td>4‑Augen‑Prinzip, Quellenpflicht</td></tr>"
        "<tr><td>Abhängigkeit</td><td>niedrig</td><td>Lock‑in</td><td>Offene Schnittstellen, Export</td></tr>"
        "</tbody></table>"
    )

    out["GAMECHANGER_HTML"] = _clean_html(sections.get("GAMECHANGER_HTML") or "")

    return out
