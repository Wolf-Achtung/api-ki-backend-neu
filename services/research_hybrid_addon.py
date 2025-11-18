# -*- coding: utf-8 -*-
"""
services/research_hybrid_addon.py
Optional Perplexity "Hybrid"-Addon: augments existing research sections
(TOOLS_HTML / FOERDERPROGRAMME_HTML) with Perplexity API results.
- Safe to import when PERPLEXITY_API_KEY is missing (no effect).
- Gracefully degrades on any error.
"""
from __future__ import annotations
from typing import Dict, Any, List
import os, json, re, html
from datetime import datetime, timezone
import requests

PPLX_API = os.getenv("PERPLEXITY_API_BASE","https://api.perplexity.ai").rstrip("/") + "/chat/completions"
PPLX_MODEL = os.getenv("PERPLEXITY_MODEL","sonar-pro")

def _pplx_chat(prompt: str, temperature: float = 0.0, max_tokens: int = 1200) -> str:
    key = os.getenv("PERPLEXITY_API_KEY","").strip()
    if not key:
        return ""
    try:
        r = requests.post(
            PPLX_API,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": PPLX_MODEL,
                "temperature": float(os.getenv("PERPLEXITY_TEMPERATURE","0.0") or 0.0),
                "messages": [
                    {"role": "system", "content": "You are a precise research assistant. Always output VALID HTML tables only."},
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=int(os.getenv("PERPLEXITY_TIMEOUT","60"))
        )
        r.raise_for_status()
        data = r.json()
        result = (data.get("choices", [{}])[0].get("message", {}) or {}).get("content","")
        return str(result) if result else ""
    except Exception:
        return ""

def _clean_html(s: str) -> str:
    return (s or "").replace("```html","").replace("```","").strip()

def _merge_tables_by_link(html_a: str, html_b: str) -> str:
    """Merge <tr> rows of two simple <table>s; deduplicate by first href."""
    def rows(block: str) -> List[str]:
        return re.findall(r"<tr[^>]*>.*?</tr>", block or "", flags=re.I|re.S)
    def has_href(row: str) -> str:
        m = re.search(r"href=['\"]([^'\"]+)['\"]", row or "", flags=re.I)
        return (m.group(1).strip() if m else "")
    rows_a, rows_b = rows(html_a), rows(html_b)
    seen = set()
    out_rows = []
    for r in rows_a + rows_b:
        href = has_href(r)
        key = href or re.sub(r"\s+"," ", re.sub(r"<[^>]+>"," ", r)).strip().lower()
        if key in seen: 
            continue
        seen.add(key)
        out_rows.append(r)
    if not out_rows:
        return html_a or html_b
    # try to keep original table header from html_a if present, else simple wrap
    head_match = re.search(r"(<thead>.*?</thead>)", html_a or "", flags=re.I|re.S)
    thead = head_match.group(1) if head_match else ""
    return "<table class='table'>" + thead + "<tbody>" + "".join(out_rows) + "</tbody></table>"

def _tools_prompt(ans: Dict[str, Any]) -> str:
    branche = ans.get("BRANCHE_LABEL") or ans.get("branche","")
    groesse = ans.get("UNTERNEHMENSGROESSE_LABEL") or ans.get("unternehmensgroesse","")
    bundesland = ans.get("BUNDESLAND_LABEL") or ans.get("bundesland","")
    return (f"Liste eine kuratierte Auswahl aktueller KI-Tools (max. 10) als HTML <table>"
            f" mit Spalten: Tool/Produkt, Kategorie, Preis, DSGVO/Host, Links. "
            f"Berücksichtige Branche '{branche}', Größe '{groesse}', Standort '{bundesland}'. "
            f"Gib pro Zeile mindestens einen Link an (Produkt oder Trust Center). "
            f"Nur valide <table>-Struktur, keine Prosa.")

def _funding_prompt(ans: Dict[str, Any]) -> str:
    bundesland = ans.get("BUNDESLAND_LABEL") or ans.get("bundesland","")
    groesse = ans.get("UNTERNEHMENSGROESSE_LABEL") or ans.get("unternehmensgroesse","")
    return (f"Liste die wichtigsten Förderprogramme in Deutschland (fokussiere {bundesland}) als HTML <table> "
            f"mit Spalten: Programm, Fördersatz/Max, Zielgruppe, Laufzeit/Status, Link. "
            f"Zielgruppe: {groesse}. Nur valide <table>-Struktur ohne weitere Texte.")

def augment_sections_with_perplexity(sections: Dict[str, str], answers: Dict[str, Any]) -> Dict[str, str]:
    """Augment TOOLS_HTML and FOERDERPROGRAMME_HTML using Perplexity results if API key is set."""
    key = os.getenv("PERPLEXITY_API_KEY","").strip()
    if not key:
        return sections
    tools_html = _clean_html(_pplx_chat(_tools_prompt(answers)))
    funding_html = _clean_html(_pplx_chat(_funding_prompt(answers)))
    if tools_html:
        merged = _merge_tables_by_link(sections.get("TOOLS_HTML",""), tools_html)
        sections["TOOLS_HTML"] = merged
    if funding_html:
        merged = _merge_tables_by_link(sections.get("FOERDERPROGRAMME_HTML",""), funding_html)
        sections["FOERDERPROGRAMME_HTML"] = merged
    # Update "last updated" if present
    sections["research_last_updated"] = sections.get("research_last_updated") or datetime.now().strftime("%d.%m.%Y")
    return sections