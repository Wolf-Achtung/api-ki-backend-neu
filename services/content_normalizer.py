# -*- coding: utf-8 -*-
from __future__ import annotations
"""
services.content_normalizer – Gold-Standard+
- Tools- und Fördertabellen: Standardwerte bei fehlenden Live-Daten
- Einheitliche Platzhalter-Nutzung
"""
from typing import Dict, Any
import re

try:
    from .sanitize import ensure_utf8  # type: ignore
except Exception:
    def ensure_utf8(x: str) -> str:
        return (x or "").encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")

EM_DASH = "—"

def _table(headers, rows) -> str:
    parts = []
    parts.append('<table class="table"><thead><tr>')
    for h in headers:
        parts.append(f"<th>{ensure_utf8(h)}</th>")
    parts.append("</tr></thead><tbody>")
    for r in rows:
        parts.append("<tr>")
        for c in r:
            parts.append(f"<td>{ensure_utf8(c)}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)

def _to_eur(v: float) -> str:
    s = f"{v:,.2f} €"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s

def _parse_budget_range(text: str) -> float:
    if not text:
        return 0.0
    t = str(text).strip()
    m = re.match(r"(\d+)[^\d]+(\d+)", t)
    if not m:
        m = re.match(r"(\d+)_?(\d+)?", t)
    if m:
        low = float(m.group(1))
        high = float(m.group(2) or m.group(1))
        return (low + high) / 2.0
    try:
        return float(t)
    except Exception:
        return 0.0

def _branch_defaults(branche: str, size: str) -> Dict[str, Any]:
    b = (branche or "").lower()
    defaults = {
        "beratung": {
            "kpis": [
                ("Durchlaufzeit Angebot", "Zeit von Anfrage bis Angebot", "≤ 24 h"),
                ("Antwortzeit Kundenchat", "Median in Bürozeiten", "≤ 30 min"),
                ("Wiederverwendbare Vorlagen", "Anteil standardisierter Antworten", "≥ 60 %"),
                ("Automatisierungsgrad", "Anteil automatisierter Schritte", "≥ 40 %"),
            ],
            "tools": [
                ("Notion AI (Business)", "Notion", "ab ~20 €/User/Monat", "Wissensbasis & Doku (EU‑Optionen)"),
                ("Typeform (EU API)", "Typeform", "ab ~30–70 €/Monat", "Formulare/Fragebögen mit EU‑Endpunkt"),
                ("Make.com", "Make", "ab ~9–29 €/Monat", "No‑Code Automationen, Webhooks"),
                ("n8n (Self‑Hosted)", "n8n", "Open Source", "Automationsplattform, On‑Prem möglich"),
                ("Claude (Workplaces)", "Anthropic", "Pay‑per‑use", "LLM für Auswertung/Content, DE‑stark"),
            ],
        }
    }
    d = defaults.get(b, defaults["beratung"])
    kpis = list(d["kpis"])
    s = (size or "").lower()
    if s == "solo":
        kpis[0] = (kpis[0][0], kpis[0][1], "≤ 48 h")
        kpis[1] = (kpis[1][0], kpis[1][1], "≤ 60 min")
    elif s == "team_2_10":
        kpis[0] = (kpis[0][0], kpis[0][1], "≤ 36 h")
        kpis[1] = (kpis[1][0], kpis[1][1], "≤ 45 min")
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
    yearly = float(metrics.get("jahresersparnis_eur", 0) or 0)
    monthly = float(metrics.get("monatsersparnis_eur", 0) or 0)
    rate = float(metrics.get("stundensatz_eur", 60) or 60)
    roi_pct = ((yearly - invest) / invest * 100.0) if invest > 0 else 0.0
    payback_months = (invest / monthly) if monthly > 0 else 0.0
    roi_rows = [
        ("Stundensatz (Benchmark)", f"{int(rate)} €"),
        ("Investition", _to_eur(invest)),
        ("Ersparnis (jährlich)", _to_eur(yearly)),
        ("Return on Investment (ROI)", f"{roi_pct:.0f} %" if invest > 0 else EM_DASH),
        ("Payback‑Periode", f"{payback_months:.1f} Monate" if monthly > 0 else EM_DASH),
    ]
    costs_rows = [
        ("Initiale Investition (CapEx)", _to_eur(invest)),
        ("Lizenzen/Hosting (OpEx)", _to_eur(max(180.0, rate * 3.0))),
        ("Schulung/Change", _to_eur(600.0)),
        ("Betrieb (Schätzung)", _to_eur(360.0)),
    ]
    return {
        "ROI_HTML": _table(["Kennzahl", "Wert"], roi_rows),
        "COSTS_OVERVIEW_HTML": _table(["Position", "Betrag"], costs_rows),
        "invest_value": invest,
    }

def _sensitivity_table(invest: float, monthly_base: float, rate: float) -> str:
    if invest <= 0 or monthly_base <= 0:
        return "<p>—</p>"
    rows = []
    for f in (1.0, 0.8, 0.6):
        mon = monthly_base * f
        yr = mon * 12.0
        roi = ((yr - invest) / invest * 100.0) if invest > 0 else 0.0
        pb = (invest / mon) if mon > 0 else 0.0
        rows.append((f"{int(f * 100)} %", f"{_to_eur(yr)} / {_to_eur(mon)}", f"{roi:.0f} %", f"{pb:.1f} Monate"))
    return _table(["Adoption", "Ersparnis Jahr / Monat", "ROI", "Payback"], rows)

def _so_what(scores: Dict[str, int]) -> str:
    g = scores.get("governance", 0)
    s = scores.get("security", 0)
    v = scores.get("value", 0)
    e = scores.get("enablement", 0)
    items = []
    if g < 50:
        items.append("<li><strong>Governance:</strong> Rollen & Leitlinien klären (1–2 Seiten), Freigabepfade definieren.</li>")
    if s < 50:
        items.append("<li><strong>Sicherheit:</strong> Datenschutz-Checkliste + Logging, Prompt‑Richtlinien, Human‑Oversight.</li>")
    if v < 50:
        items.append("<li><strong>Nutzen:</strong> 3 Quick Wins priorisieren, KPI‑Baseline setzen, 30‑Tage‑Review.</li>")
    if e < 50:
        items.append("<li><strong>Befähigung:</strong> Prompt‑Training (3 Sessions), Brown‑Bags, Champions benennen.</li>")
    if not items:
        items.append("<li>Reifegrad solide – Fokus auf Skalierung: wiederverwendbare Bausteine & Automatisierungsgrad erhöhen.</li>")
    return "<ul>" + "".join(items) + "</ul>"

def _default_tools_and_funding(briefing: Dict[str, Any], last_updated: str, report_date: str) -> Dict[str, str]:
    b = (briefing.get("bundesland") or "").lower()
    branche = briefing.get("branche") or "beratung"
    d = _branch_defaults(branche, briefing.get("unternehmensgroesse") or "")
    tools_rows = d.get("tools", [])
    tools_html = _table(["Tool/Produkt", "Anbieter", "Preis‑Hinweis", "Einsatz"], tools_rows)
    funding_rows = []
    if b == "be":
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
    if last_updated or report_date:
        funding_html += f'<p class="small">Stand: {ensure_utf8(report_date)} • Research: {ensure_utf8(last_updated or report_date)}</p>'
    return {"TOOLS_HTML": tools_html, "FOERDERPROGRAMME_HTML": funding_html}

def normalize_and_enrich_sections(briefing: Dict[str, Any] = None,
                                  snippets: Dict[str, str] = None,
                                  metrics: Dict[str, Any] = None,
                                  **kwargs) -> Dict[str, str]:
    snippets = snippets or kwargs.get("sections") or {}
    briefing = briefing or kwargs.get("answers") or {}
    metrics = metrics or kwargs.get("metrics") or {}
    out = dict(snippets or {})

    # KPI
    kpi = _kpi_tables(briefing.get("branche") or "beratung", briefing.get("unternehmensgroesse") or "")
    out.setdefault("KPI_HTML", kpi["KPI_HTML"])
    out.setdefault("KPI_BRANCHE_HTML", kpi["KPI_BRANCHE_HTML"])

    # Governance „So-what?“
    scores = kwargs.get("scores") or {}
    out.setdefault("REIFEGRAD_SOWHAT_HTML", _so_what(scores))

    # ROI & Kosten
    if not out.get("ROI_HTML") or len(out.get("ROI_HTML", "").strip()) < 20:
        out.update(_roi_and_costs(briefing, metrics))

    # Sensitivität
    invest = float(out.get("invest_value", 0) or 0)
    monthly = float(metrics.get("monatsersparnis_eur", 0) or 0)
    rate = float(metrics.get("stundensatz_eur", 60) or 60)
    out.setdefault("BUSINESS_SENSITIVITY_HTML", _sensitivity_table(invest, monthly, rate))

    # Tools/Förderungen
    last_updated = snippets.get("last_updated") or kwargs.get("last_updated") or briefing.get("research_last_updated") or ""
    report_date = briefing.get("report_date", "")
    if not out.get("TOOLS_HTML") or len(out.get("TOOLS_HTML", "").strip()) < 24:
        out.update(_default_tools_and_funding(briefing, last_updated, report_date))
    if not out.get("FOERDERPROGRAMME_HTML") or len(out.get("FOERDERPROGRAMME_HTML", "").strip()) < 20:
        b = (briefing.get("bundesland") or "").lower()
        funding_rows = []
        if b == "be":
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
        if last_updated or report_date:
            funding_html += f'<p class="small">Stand: {ensure_utf8(report_date)} • Research: {ensure_utf8(last_updated or report_date)}</p>'
        out["FOERDERPROGRAMME_HTML"] = funding_html

    # Quellen (Fallback)
    if not out.get("QUELLEN_HTML") or len(out.get("QUELLEN_HTML", "").strip()) < 16:
        out["QUELLEN_HTML"] = _table(
            ["Titel", "Host", "Datum", "Link"],
            [
                ("EU‑KI‑Verordnung (AI Act) – Überblick", "europa.eu", "—", "https://europa.eu"),
                ("INQA‑Coaching", "inqa.de", "—", "https://inqa.de"),
            ],
        )
    return out
