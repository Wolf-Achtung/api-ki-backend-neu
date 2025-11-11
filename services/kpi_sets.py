# -*- coding: utf-8 -*-
"""
Branchen-KPI Sets (Gold-Standard+)
==================================
Für jede Branche werden praxisnahe KPIs inkl. Definition, Formel und Ziel-Hinweis geliefert.
Die Ausgabe erfolgt als valides HTML (Tabelle), damit das PDF-Template es direkt einbetten kann.
"""
from __future__ import annotations
from typing import Dict, List
import html
from services.playbooks import normalize_industry

KPI_SETS: Dict[str, List[dict]] = {
    "beratung": [
        {"name": "Time to Recommendation (TTR)", "definition": "Zeit von Intake bis Erstempfehlung",
         "formula": "Durchschnitt(TTR aller Fälle in Tagen)", "target": "≤ 2 Tage"},
        {"name": "First‑Pass‑Approval‑Rate", "definition": "Anteil der Empfehlungen ohne Nacharbeit",
         "formula": "Freigegeben ohne Revision / Gesamt", "target": "≥ 85 %"},
        {"name": "CSAT/NPS", "definition": "Kundenzufriedenheit/Weiterempfehlung",
         "formula": "Standard‑Survey", "target": "↑ im Trend"},
    ],
    "it": [
        {"name": "Cycle Time", "definition": "Zeit von Commit bis Deploy",
         "formula": "Median Cycle Time (h)", "target": "↓ quartalsweise"},
        {"name": "Defects/PR", "definition": "Fehlerdichte im Code Review",
         "formula": "Anzahl Defekte / Pull Request", "target": "≤ 0,3"},
        {"name": "MTTR", "definition": "Mean Time To Recovery bei Incidents",
         "formula": "Durchschnittliche Wiederherstellungszeit", "target": "≤ 60 min"},
    ],
    "handel": [
        {"name": "Conversion‑Rate (CR)", "definition": "Besucher zu Kauf",
         "formula": "Bestellungen / Sessions", "target": "↑ +0,3–0,7 pp"},
        {"name": "Time‑to‑List", "definition": "Zeit neue Artikel → live",
         "formula": "Median (h)", "target": "≤ 24 h"},
        {"name": "Retouren‑Quote", "definition": "Rücksendungen zu Bestellungen",
         "formula": "Retouren / Bestellungen", "target": "↓ im Trend"},
    ],
    "gesundheit": [
        {"name": "Dokumentationszeit / Fall", "definition": "Zeit für Anamnese/Bericht",
         "formula": "Durchschnitt (min)", "target": "−30–50 %"},
        {"name": "Korrekturquote", "definition": "Anteil korrigierter Dokumente",
         "formula": "Korrekturen / Gesamt", "target": "≤ 5 %"},
        {"name": "Wartezeit", "definition": "Patientenwartezeit",
         "formula": "Median (min)", "target": "↓ im Trend"},
    ],
    "industrie": [
        {"name": "Ausschussquote", "definition": "Fehlerhafte Teile",
         "formula": "Fehlerteile / Gesamtteile", "target": "↓ 20–40 %"},
        {"name": "Stillstandszeit", "definition": "Ungeplante Downtime",
         "formula": "Stunden / Monat", "target": "↓ im Trend"},
        {"name": "MTTR", "definition": "Mean Time To Repair",
         "formula": "Durchschnittliche Reparaturzeit", "target": "≤ 2 h"},
    ],
    "logistik": [
        {"name": "Pünktlichkeit", "definition": "On‑Time Deliveries",
         "formula": "Pünktliche Lieferungen / Gesamt", "target": "≥ 95 %"},
        {"name": "CO₂ / Tonne", "definition": "Emissionen pro transportierter Tonne",
         "formula": "g CO₂ / t·km", "target": "↓ im Trend"},
        {"name": "Picks/Stunde", "definition": "Kommissionier‑Leistung",
         "formula": "Durchschnitt Picks pro Stunde", "target": "↑ im Trend"},
    ],
    "marketing": [
        {"name": "CTR / Conversion", "definition": "Leistung der Kampagnen",
         "formula": "Klicks/Impr., Conversions/Visits", "target": "↑ quartalsweise"},
        {"name": "Content‑Durchlaufzeit", "definition": "Briefing → Publish",
         "formula": "Median (Tage)", "target": "↓ um 30 %"},
        {"name": "Brand Consistency", "definition": "Style/Guideline‑Treue",
         "formula": "Review‑Score 1–5", "target": "≥ 4,5"},
    ],
    "finanzen": [
        {"name": "False‑Positive‑Rate (AML/KYC)", "definition": "Fehlalarme in Prüfungen",
         "formula": "False Positives / Gesamt", "target": "≤ 10 %"},
        {"name": "Durchlaufzeit Onboarding", "definition": "Kundenanlage bis Freigabe",
         "formula": "Median (h)", "target": "↓ im Trend"},
        {"name": "Audit Findings", "definition": "Beanstandungen pro Audit",
         "formula": "Anzahl / Audit", "target": "0–2"},
    ],
    "bildung": [
        {"name": "Lernfortschritt", "definition": "Kompetenzzuwachs",
         "formula": "Score Δ (Pre/Post)", "target": "↑ signifikant"},
        {"name": "Material‑Vorbereitungszeit", "definition": "Erstellung von Materialien",
         "formula": "Stunden / Modul", "target": "−30–50 %"},
        {"name": "Zugänglichkeit", "definition": "Barrierefreiheit",
         "formula": "Anteil mit Unterstützung", "target": "↑ im Trend"},
    ],
    "verwaltung": [
        {"name": "Durchlaufzeit Antrag", "definition": "Antragseingang → Bescheid",
         "formula": "Median (Tage)", "target": "↓ im Trend"},
        {"name": "Rückfragenquote", "definition": "Anträge mit Rückfragen",
         "formula": "Rückfragen / Anträge", "target": "↓ im Trend"},
        {"name": "Fehlerquote Bescheide", "definition": "Korrekturbedarf",
         "formula": "Fehler / Bescheide", "target": "≤ 2 %"},
    ],
    "bau": [
        {"name": "Nachträge", "definition": "Unvorhergesehene Zusatzleistungen",
         "formula": "Nachträge / Projekt", "target": "↓ im Trend"},
        {"name": "Plan‑Abweichungen", "definition": "Abweichungen Baustelle vs. Plan",
         "formula": "Anzahl / Woche", "target": "↓ 20 %"},
        {"name": "Angebotserstellung", "definition": "LV → Angebot",
         "formula": "Median (Tage)", "target": "↓ im Trend"},
    ],
    "medien": [
        {"name": "Produktionstime", "definition": "Rohmaterial → finaler Export",
         "formula": "Median (h)", "target": "↓ um 30 %"},
        {"name": "QC‑Fehler", "definition": "Qualitätsmängel pro Export",
         "formula": "Anzahl / Export", "target": "≤ 1"},
        {"name": "Ausspielungen/Asset", "definition": "Versionen/Varianten pro Asset",
         "formula": "Anzahl", "target": "↑ im Trend"},
    ],
}

def build_kpi_table_html(branche: str | None) -> str:
    key = normalize_industry(branche)
    rows: List[str] = []
    items = KPI_SETS.get(key) or KPI_SETS.get("beratung", [])
    for it in items:
        rows.append(
            "<tr>"
            f"<td>{html.escape(it['name'])}</td>"
            f"<td>{html.escape(it['definition'])}</td>"
            f"<td>{html.escape(it['formula'])}</td>"
            f"<td>{html.escape(it['target'])}</td>"
            "</tr>"
        )
    return (
        "<table class='table'>"
        "<thead><tr><th>KPI</th><th>Definition</th><th>Formel</th><th>Zielwert (Richtwert)</th></tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table>"
    )
