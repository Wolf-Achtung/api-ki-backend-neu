# -*- coding: utf-8 -*-
"""Content Normalizer & Enricher (Gold-Standard+)
==================================================
- Füllt leere Platzhalter (KPI, ROI, Kosten, Tools, Förderungen, Quellen)
- Größen-/branchenabhängige Defaults
- Akzeptiert **kwargs + alias 'sections' (Kompatibilität zu Renderer)
"""
from __future__ import annotations

import re
from typing import Dict, Any

try:
    from .sanitize import ensure_utf8  # type: ignore
except Exception:  # Fallback, falls Modul nicht existiert
    def ensure_utf8(x: str) -> str:
        return (x or "").encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")

EM_DASH = "—"

def _table(headers, rows) -> str:
    th = "".join(f"<th>{ensure_utf8(h)}</th>" for h in headers)
    trs = []
    for r in rows:
        tds = "".join(f"<td>{ensure_utf8(c)}</td>" for c in r)
        trs.append(f"<tr>{tds}</tr>")
    return f"<table class=\"table\"><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table>"

def _to_eur(v: float) -> str:
    return f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

def _parse_budget_range(text: str) -> float:
    """Parse strings like '2000_10000' and return midpoint as float."""
    if not text:
        return 0.0
    m = re.match(r"(\d+)[^\d]+(\d+)", str(text))
    if not m:
        m = re.match(r"(\d+)_?(\d+)?", str(text))
    if m:
        low = float(m.group(1))
        high = float(m.group(2) or m.group(1))
        return (low + high) / 2.0
    try:
        return float(text)
    except Exception:
        return 0.0

def _branch_defaults(branche: str, size: str) -> Dict[str, Any]:
    b = (branche or "").lower()
    size = (size or "").lower()
    # KPIs baseline für Beratung – wird unten je Größe justiert
    defaults = {
        "beratung": {
            "kpis": [
                ["Durchlaufzeit Angebot", "Zeit von Anfrage bis Angebot", "≤ 24 h"],
                ["Antwortzeit Kundenchat", "Median in Bürozeiten", "≤ 30 min"],
                ["Wiederverwendbare Vorlagen", "Anteil standardisierter Antworten", "≥ 60 %"],
                ["Automatisierungsgrad", "Anteil automatisierter Schritte", "≥ 40 %"],
            ],
            "tools": [
                ["Notion AI (Business)", "Notion", "ab ~20 €/User/Monat", "Wissensbasis & Doku (EU‑Optionen)"],
                ["Typeform (EU API)", "Typeform", "ab ~30–70 €/Monat", "Formulare/Fragebögen mit EU‑Endpunkt"],
                ["Make.com", "Make", "ab ~9–29 €/Monat", "No‑Code Automationen, Webhooks"],
                ["n8n (Self‑Hosted)", "n8n", "Open Source", "Automationsplattform, On‑Prem möglich"],
                ["Claude (Workplaces)", "Anthropic", "Pay‑per‑use", "LLM für Auswertung/Content, DE‑stark"],
            ],
        }
    }
    d = defaults.get(b, defaults["beratung"])

    # Größen‑Tuning
    kpis = list(d["kpis"])
    if size == "solo":
        kpis[0][2] = "≤ 48 h"
        kpis[1][2] = "≤ 60 min"
    elif size == "team_2_10":
        kpis[0][2] = "≤ 36 h"
        kpis[1][2] = "≤ 45 min"
    # kmu_11_100 bleibt baseline

    return {"kpis": kpis, "tools": d.get("tools", [])}

def _kpi_tables(branche: str, size: str) -> Dict[str, str]:
    d = _branch_defaults(branche, size)
    overview = _table(["KPI", "Definition", "Ziel"], d["kpis"]) if d.get("kpis") else ""
    return {
        "KPI_HTML": overview or f"<p>{ensure_utf8(EM_DASH)}</p>",
        "KPI_BRANCHE_HTML": overview or f"<p>{ensure_utf8(EM_DASH)}</p>",
    }

def _roi_and_costs(briefing: Dict[str, Any], metrics: Dict[str, Any]) -> Dict[str, str]:
    invest_hint = _parse_budget_range(briefing.get("investitionsbudget"))
    invest = invest_hint if invest_hint > 0 else 6000.0
    # Quick‑Wins Kennzahlen (von gpt_analyze gesetzt)
    yearly = float(metrics.get("jahresersparnis_eur", 0))
    monthly = float(metrics.get("monatsersparnis_eur", 0))
    roi_pct = ((yearly - invest) / invest * 100.0) if invest > 0 else 0.0
    payback_months = (invest / monthly) if monthly > 0 else 0.0

    roi_rows = [
        ("Stundensatz", f"{metrics.get('stundensatz_eur', 60)} €"),
        ("Investition", _to_eur(invest)),
        ("Ersparnis (jährlich)", _to_eur(yearly)),
        ("Return on Investment (ROI)", f"{roi_pct:.0f} %" if invest > 0 else EM_DASH),
        ("Payback‑Periode", f"{payback_months:.1f} Monate" if monthly > 0 else EM_DASH),
    ]
    costs_rows = [
        ("Initiale Investition (CapEx)", _to_eur(invest)),
        ("Lizenzen/Hosting (OpEx)", _to_eur(max(180.0, metrics.get("stundensatz_eur", 60) * 3.0))),
        ("Schulung/Change", _to_eur(600.0)),
        ("Betrieb (Schätzung)", _to_eur(360.0)),
    ]
    return {
        "ROI_HTML": _table(["Kennzahl", "Wert"], roi_rows),
        "COSTS_OVERVIEW_HTML": _table(["Position", "Betrag"], costs_rows),
    }

def _default_tools_and_funding(briefing: Dict[str, Any], last_updated: str) -> Dict[str, str]:
    b = (briefing.get("bundesland") or "").lower()
    branche = briefing.get("branche") or "beratung"

    tools = _branch_defaults(branche, briefing.get("unternehmensgroesse") or "").get("tools", [])
    tools_html = _table(["Tool/Produkt", "Anbieter", "Preis‑Hinweis", "Einsatz"], tools)

    funding_rows = []
    if b == "be":  # Berlin
        funding_rows.extend([
            ("KOMPASS (Solo‑Selbständige)", "ESF+/BA", "bis 29.02.2028", "Qualifizierung/Coaching bis 4.500 €"),
            ("INQA‑Coaching (KMU)", "BMAS/ESF+", "laufend", "80 % Zuschuss bis 12 Tage"),
            ("Transfer BONUS", "IBB", "laufend", "bis 45.000 € (70 %)"),
            ("Pro FIT", "IBB", "laufend", "Zuschuss + Darlehen für F&E"),
        ])
    else:
        funding_rows.extend([
            ("INQA‑Coaching (KMU)", "BMAS/ESF+", "laufend", "80 % Zuschuss bis 12 Tage"),
            ("Förderdatenbank (Bund/Land)", "BMWK", "—", "Filter: Digitalisierung/KI"),
        ])
    funding_html = _table(["Programm", "Träger", "Deadline/Datum", "Kurzbeschreibung"], funding_rows)
    funding_html += f'<p class="small">Stand Research: {ensure_utf8(last_updated or briefing.get("report_date") or "—")}</p>'
    return {
        "TOOLS_HTML": tools_html,
        "FOERDERPROGRAMME_HTML": funding_html,
    }

def normalize_and_enrich_sections(briefing: Dict[str, Any] = None,
                                  snippets: Dict[str, str] = None,
                                  metrics: Dict[str, Any] = None,
                                  **kwargs) -> Dict[str, str]:
    """Mergt Snippets mit robusten Defaults. Kompatibel zu call mit sections=..., answers=..., metrics=..."""
    snippets = snippets or kwargs.get("sections") or {}
    briefing = briefing or kwargs.get("answers") or {}
    metrics  = metrics  or kwargs.get("metrics") or {}
    out = dict(snippets or {})

    # KPI tables
    kpi = _kpi_tables(briefing.get("branche") or "beratung", briefing.get("unternehmensgroesse") or "")
    out.setdefault("KPI_HTML", kpi["KPI_HTML"])
    out.setdefault("KPI_BRANCHE_HTML", kpi["KPI_BRANCHE_HTML"])

    # ROI & Costs
    if not out.get("ROI_HTML") or len(out.get("ROI_HTML","").strip()) < 20:
        out.update(_roi_and_costs(briefing, metrics))

    # Tools & Funding fallback (mit Stand)
    last_updated = snippets.get("last_updated") or kwargs.get("last_updated") or briefing.get("research_last_updated") or ""
    if not out.get("TOOLS_HTML") or len(out.get("TOOLS_HTML","").strip()) < 24:
        out.update(_default_tools_and_funding(briefing, last_updated))

    # Quellenliste – minimaler Fallback, wenn leer
    if not out.get("QUELLEN_HTML") or len(out.get("QUELLEN_HTML", "").strip()) < 16:
        out["QUELLEN_HTML"] = _table(["Titel", "Host", "Datum", "Link"], [
            ("EU‑KI‑Verordnung (AI Act) – Überblick", "europa.eu", "—", "https://europa.eu"),
            ("INQA‑Coaching", "inqa.de", "—", "https://inqa.de"),
        ])

    return out
