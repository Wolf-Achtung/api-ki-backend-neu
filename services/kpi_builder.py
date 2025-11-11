# -*- coding: utf-8 -*-
"""
services/kpi_builder.py
----------------------
Erzeugt ein kompaktes KPI-Set je Branche/Unternehmensgröße.

Public:
    build_kpis(answers: dict) -> str  # returns KPIS_HTML
"""
from __future__ import annotations
from typing import Dict, List

BRANCH_KPIS = {
    "beratung": [
        ("Lead-zu-Termin-Rate", "Leads → Erstgespräche (%)"),
        ("Angebots-Gewinnquote", "Gewonnene Angebote / Angebote (%)"),
        ("Durchlaufzeit Angebot", "Anfrage → Angebot (Std.)"),
        ("Utilization", "Beratungsstunden / verfügbare Stunden (%)"),
        ("NPS", "Kundenzufriedenheit (–100..+100)"),
    ],
    "marketing": [
        ("MQL→SQL", "Marketing-Qualifiziert → Sales-Qualifiziert (%)"),
        ("CAC", "Customer Acquisition Cost (€)"),
        ("CTR", "Click-Through-Rate (%)"),
        ("ROAS", "Return on Ad Spend (x)"),
        ("Lead-Zykluszeit", "Erstkontakt → Demo (Tage)"),
    ],
    "it_software": [
        ("Cycle Time", "Commit → Deploy (Tage)"),
        ("Lead Time", "Ticket erstellt → Done (Tage)"),
        ("Change Failure Rate", "Fehlgeschlagene Deploys (%)"),
        ("MTTR", "Mean Time To Recovery (Std.)"),
        ("CSAT", "Support-Zufriedenheit (1–5)"),
    ],
    "finanzen": [
        ("Durchlaufzeit Vorgang", "Eingang → Abschluss (Std.)"),
        ("First Pass Yield", "Fehlerfrei im Erstlauf (%)"),
        ("DPO/DSO", "Zahlungsziele (Tage)"),
        ("Automatisierungsquote", "Automatisiert verarbeitete Fälle (%)"),
        ("Audit-Feststellungen", "Abweichungen je Prüfung (#)"),
    ],
    "handel": [
        ("Warenkorbabbruch", "Abbruchrate (%)"),
        ("Retourenquote", "Rücksendungen (%)"),
        ("Pick-Pack-Zeit", "Fulfillment (Min.)"),
        ("Conversion", "Besuch → Kauf (%)"),
        ("AOV", "Average Order Value (€)"),
    ],
}

DEFAULT_KPIS = [
    ("Automatisierungsquote", "Automatisiert verarbeitete Arbeitseinheiten (%)"),
    ("Durchlaufzeit", "Start → Abschluss (Std./Tage)"),
    ("Qualitätsquote", "Fehlerfrei im Erstlauf (%)"),
    ("Kundenzufriedenheit", "NPS/CSAT"),
    ("Produktivität", "Aufwände je Vorgang (Std.)"),
]

SIZE_HINTS = {
    "solo": "Wähle 3–4 Kennzahlen, die du monatlich nachhältst. Keine komplexen Dashboards – einfache Tabellen reichen.",
    "team_2_10": "Definiere 5–7 Kennzahlen, die in einem leichten Dashboard (Notion/Sheets) wöchentlich aktualisiert werden.",
    "kmu_11_100": "Führe ein KPI-Board (Monat/Quartal) mit Verantwortlichen und Zielwerten (OKRs) ein.",
}

def _table(rows: List[List[str]], header: List[str]) -> str:
    head = "<thead><tr>" + "".join(f"<th>{h}</th>" for h in header) + "</tr></thead>"
    body = "<tbody>" + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows) + "</tbody>"
    return f'<table class="table">{head}{body}</table>'

def build_kpis(answers: Dict) -> str:
    branche = (answers or {}).get("branche", "")
    size = (answers or {}).get("unternehmensgroesse", "")
    kpis = BRANCH_KPIS.get(branche) or DEFAULT_KPIS
    rows = [[name, desc] for (name, desc) in kpis]
    hint = SIZE_HINTS.get(size, "")
    html = _table(rows, ["KPI", "Beschreibung"])
    if hint:
        html = f"<p class='small'>{hint}</p>" + html
    return html
