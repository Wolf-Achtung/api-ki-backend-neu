# -*- coding: utf-8 -*-
"""Content Normalizer & Enricher (Gold-Standard+)
==================================================
- Füllt leere Platzhalter (KPI, ROI, Kosten, Tools, Förderungen)
- Liefert robuste Defaults abhängig von Branche/Unternehmensgröße
- Bleibt funktionsfähig, wenn externe Recherche (Tavily/Perplexity) ausfällt
"""
from __future__ import annotations

import re
from typing import Dict, Any

from .sanitize import ensure_utf8

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
    """Parse strings like "2000_10000" and return midpoint as float."""
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

def _branch_defaults(branche: str) -> Dict[str, Any]:
    b = (branche or "").lower()
    # Minimal, aber praxistauglich – kann jederzeit erweitert werden
    defaults = {
        "beratung": {
            "kpis": [
                ("Durchlaufzeit Angebot", "Zeit von Anfrage bis Angebot", "≤ 24 h"),
                ("Antwortzeit Kundenchat", "Median in Bürozeiten", "≤ 30 min"),
                ("Wiederverwendbare Vorlagen", "Anteil standardisierter Antworten", "≥ 60 %"),
                ("Automatisierungsgrad", "Anteil automatisierter Schritte", "≥ 40 %"),
            ],
            "tools": [
                ("Notion AI (Business)", "Notion", "ab ~20 €/User/Monat", "Wissensbasis & Doku (EU-Optionen)"),
                ("Typeform (EU API)", "Typeform", "ab ~30–70 €/Monat", "Formulare/Fragebögen mit EU-Endpunkt"),
                ("Make.com", "Make", "ab ~9–29 €/Monat", "No‑Code Automationen, Webhooks"),
                ("n8n (Self‑Hosted)", "n8n", "Open Source", "Automationsplattform, On‑Prem möglich"),
                ("Claude/Anthropic", "Anthropic", "Pay‑per‑use", "LLM für Auswertung/Content, DE‑stark"),
            ],
        },
        "it & software": {
            "kpis": [
                ("MTTR (Support)", "Mean‑Time‑to‑Resolve", "≤ 24 h"),
                ("Deploy‑Frequenz", "Produktionsdeploys/Monat", "≥ 4"),
            ],
            "tools": [
                ("GitHub Copilot Business", "GitHub", "ab ~19 €/User/Monat", "Code‑Assistenz, Policies"),
                ("Sentry", "Sentry", "Staffelpreis", "Error Tracking & APM"),
            ],
        },
    }
    return defaults.get(b, defaults["beratung"])  # Fallback

def _kpi_tables(branche: str) -> Dict[str, str]:
    d = _branch_defaults(branche)
    overview = _table(["KPI", "Definition", "Ziel"], d["kpis"]) if d.get("kpis") else ""
    return {
        "KPI_HTML": overview or f"<p>{ensure_utf8(EM_DASH)}</p>",
        "KPI_BRANCHE_HTML": overview or f"<p>{ensure_utf8(EM_DASH)}</p>",
    }

def _roi_and_costs(briefing: Dict[str, Any], metrics: Dict[str, Any]) -> Dict[str, str]:
    invest_hint = _parse_budget_range(briefing.get("investitionsbudget"))
    invest = invest_hint if invest_hint > 0 else 6000.0
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
        ("Initiale Investition", _to_eur(invest)),
        ("Lizenzen/Hosting", _to_eur(max(180.0, metrics.get("stundensatz_eur", 60) * 3.0))),  # grobe Daumenregel
        ("Schulung/Change", _to_eur(600.0)),
        ("Betrieb (Schätzung)", _to_eur(360.0)),
    ]
    return {
        "ROI_HTML": _table(["Kennzahl", "Wert"], roi_rows),
        "COSTS_OVERVIEW_HTML": _table(["Position", "Betrag"], costs_rows),
    }

def _default_tools_and_funding(briefing: Dict[str, Any]) -> Dict[str, str]:
    """Fallback‑Tabellen, falls keine Recherche/LLM‑Daten vorliegen."""
    b = (briefing.get("bundesland") or "").lower()
    branche = briefing.get("branche") or "beratung"

    tools = _branch_defaults(branche).get("tools", [])
    tools_rows = [(t[0], t[1], t[2], t[3]) for t in tools]
    tools_html = _table(["Tool/Produkt", "Anbieter", "Preis‑Hinweis", "Einsatz"], tools_rows)

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

    return {
        "TOOLS_HTML": tools_html,
        "FOERDERPROGRAMME_HTML": funding_html,
    }

def normalize_and_enrich_sections(briefing: Dict[str, Any], snippets: Dict[str, str], metrics: Dict[str, Any]) -> Dict[str, str]:
    """Return a copy of snippets with all critical placeholders filled."
    """
    out = dict(snippets or {})
    # KPI tables
    kpis = _kpi_tables(briefing.get("branche") or "beratung")
    out.setdefault("KPI_HTML", kpis["KPI_HTML"])
    out.setdefault("KPI_BRANCHE_HTML", kpis["KPI_BRANCHE_HTML"])

    # ROI & Costs
    if not out.get("ROI_HTML") or "Berechnung erforderlich" in out.get("ROI_HTML", ""):
        out.update(_roi_and_costs(briefing, metrics))

    # Tools & Funding fallback
    if not out.get("TOOLS_HTML") or len(out.get("TOOLS_HTML", "").strip()) < 32:
        out.update(_default_tools_and_funding(briefing))

    # Quellenliste – minimaler Fallback, wenn leer
    if not out.get("QUELLEN_HTML") or len(out.get("QUELLEN_HTML", "").strip()) < 16:
        out["QUELLEN_HTML"] = _table(["Titel", "Host", "Datum", "Link"], [
            ("EU‑KI‑Verordnung (AI Act) – Überblick", "europa.eu", "—", "https://europa.eu"),
            ("INQA‑Coaching", "inqa.de", "—", "https://inqa.de"),
        ])

    return out
