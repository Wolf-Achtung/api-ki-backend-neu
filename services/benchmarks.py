# -*- coding: utf-8 -*-
"""
Benchmarks for 12 industries (DE, KMU). Provides lookup + HTML snippet.
Numbers are based on public reports (2024/25) and approximations for top quartile.
"""
from __future__ import annotations
import json
import os
from typing import Dict, Any

BENCHMARKS_PATH = os.getenv("BENCHMARKS_PATH", "data/benchmarks.json")

CANON = [
    "Marketing & Werbung",
    "Beratung & Dienstleistungen",
    "IT & Software",
    "Finanzen & Versicherungen",
    "Handel & E-Commerce",
    "Bildung",
    "Verwaltung",
    "Gesundheit & Pflege",
    "Bauwesen & Architektur",
    "Medien & Kreativwirtschaft",
    "Industrie & Produktion",
    "Transport & Logistik",
]

# Lowercased keyword mapping → canonical label
SYNONYMS = {
    "marketing": "Marketing & Werbung",
    "werbung": "Marketing & Werbung",
    "beratung": "Beratung & Dienstleistungen",
    "dienstleistung": "Beratung & Dienstleistungen",
    "it": "IT & Software",
    "software": "IT & Software",
    "finanzen": "Finanzen & Versicherungen",
    "versicherung": "Finanzen & Versicherungen",
    "handel": "Handel & E-Commerce",
    "e-commerce": "Handel & E-Commerce",
    "ecommerce": "Handel & E-Commerce",
    "bildung": "Bildung",
    "schule": "Bildung",
    "verwaltung": "Verwaltung",
    "kommune": "Verwaltung",
    "gesundheit": "Gesundheit & Pflege",
    "pflege": "Gesundheit & Pflege",
    "bau": "Bauwesen & Architektur",
    "architektur": "Bauwesen & Architektur",
    "medien": "Medien & Kreativwirtschaft",
    "kreativ": "Medien & Kreativwirtschaft",
    "industrie": "Industrie & Produktion",
    "produktion": "Industrie & Produktion",
    "transport": "Transport & Logistik",
    "logistik": "Transport & Logistik",
}

DEFAULT_BENCHMARKS = {
    "Marketing & Werbung": {
        "avg": 72, "top25": 90,
        "source_title": "ifo Konjunkturumfrage (Juli 2024)",
        "source_url": "https://www.ifo.de/2024-07-18/mehr-unternehmen-nutzen-kuenstliche-intelligenz",
        "year": 2024, "notes": "Anteil KI-Nutzer; Top25 geschätzt."
    },
    "Beratung & Dienstleistungen": {
        "avg": 55, "top25": 80,
        "source_title": "IW Köln Zukunftspanel (2025)",
        "source_url": "https://www.iwd.de/artikel/noch-grosses-ki-potenzial-in-unternehmen-654534/",
        "year": 2025, "notes": "Anteil KI-Nutzer; Top25 geschätzt."
    },
    "IT & Software": {
        "avg": 60, "top25": 85,
        "source_title": "ifo Konjunkturumfrage (Juli 2024)",
        "source_url": "https://www.ifo.de/2024-07-18/mehr-unternehmen-nutzen-kuenstliche-intelligenz",
        "year": 2024, "notes": "Anteil KI-Nutzer; Top25 geschätzt."
    },
    "Finanzen & Versicherungen": {
        "avg": 75, "top25": 90,
        "source_title": "PwC Studie KI im Finanzsektor (2025)",
        "source_url": "https://www.pwc.de/de/finanzdienstleistungen/pwc-studie-ki-im-finanzsektor-2025.pdf",
        "year": 2025, "notes": "Anteil KI-Nutzer; Top25 geschätzt."
    },
    "Handel & E-Commerce": {
        "avg": 22, "top25": 45,
        "source_title": "ifo Konjunkturumfrage (Juli 2024)",
        "source_url": "https://www.ifo.de/2024-07-18/mehr-unternehmen-nutzen-kuenstliche-intelligenz",
        "year": 2024, "notes": "Anteil KI-Nutzer; Top25 geschätzt."
    },
    "Bildung": {
        "avg": 20, "top25": 50,
        "source_title": "IU Lernreport (2024) / Bitkom Lehrer-Umfrage",
        "source_url": "https://www.bildungsspiegel.de/news/weiterbildung-bildungspolitik/7641-iu-lernreport-2024-beleuchtet-einfluss-von-ki-auf-bildung",
        "year": 2024, "notes": "Anteil KI-Nutzer; Top25 geschätzt."
    },
    "Verwaltung": {
        "avg": 13, "top25": 30,
        "source_title": "Zukunftsradar Digitale Kommune (2024)",
        "source_url": "https://www.iit-berlin.de/wp-content/uploads/2025/02/Zukunftsradar-Digitale-Kommune-2024_iit-DStGB_WEB.pdf",
        "year": 2024, "notes": "Anteil KI-Nutzer; Top25 geschätzt."
    },
    "Gesundheit & Pflege": {
        "avg": 15, "top25": 30,
        "source_title": "Bitkom/Hartmannbund (2025)",
        "source_url": "https://www.bitkom.org/Presse/Presseinformation/KI-in-Praxis-und-Kliniken-im-Einsatz",
        "year": 2025, "notes": "Anteil KI-Nutzer; Top25 geschätzt."
    },
    "Bauwesen & Architektur": {
        "avg": 12, "top25": 25,
        "source_title": "ifo Konjunkturumfrage (Juli 2024)",
        "source_url": "https://www.ifo.de/2024-07-18/mehr-unternehmen-nutzen-kuenstliche-intelligenz",
        "year": 2024, "notes": "Anteil KI-Nutzer; Top25 geschätzt."
    },
    "Medien & Kreativwirtschaft": {
        "avg": 96, "top25": 100,
        "source_title": "BDZV/Retresco KI-Reifegrad-Report (2025)",
        "source_url": "https://www.bdzv.de/fileadmin/content/6_Service/6-1_Presse/6-1-2_Pressemitteilungen/2025/PDFs/BDZV_Retresco_KI_Reifegrad_Report_2025.pdf",
        "year": 2025, "notes": "Anteil KI-Nutzer; Top25 geschätzt."
    },
    "Industrie & Produktion": {
        "avg": 40, "top25": 70,
        "source_title": "IW Köln Zukunftspanel (2025)",
        "source_url": "https://www.iwd.de/artikel/noch-grosses-ki-potenzial-in-unternehmen-654534/",
        "year": 2025, "notes": "Anteil KI-Nutzer; Top25 geschätzt."
    },
    "Transport & Logistik": {
        "avg": 20, "top25": 45,
        "source_title": "IW Köln Zukunftspanel (2025)",
        "source_url": "https://www.iwd.de/artikel/noch-grosses-ki-potenzial-in-unternehmen-654534/",
        "year": 2025, "notes": "Anteil KI-Nutzer; Top25 geschätzt."
    },
}

def _load_file(path: str) -> Dict[str, Any]:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else DEFAULT_BENCHMARKS
        except Exception:
            pass
    return DEFAULT_BENCHMARKS

def canonicalize(branche: str) -> str:
    if not branche:
        return "Beratung & Dienstleistungen"
    s = str(branche).strip().lower()
    # direct match
    for label in CANON:
        if s == label.lower():
            return label
    # synonym match
    for key, label in SYNONYMS.items():
        if key in s:
            return label
    # fallback
    return "Beratung & Dienstleistungen"

def lookup(branche: str) -> Dict[str, Any]:
    data = _load_file(BENCHMARKS_PATH)
    canon = canonicalize(branche)
    result = data.get(canon, DEFAULT_BENCHMARKS["Beratung & Dienstleistungen"])
    return result if isinstance(result, dict) else DEFAULT_BENCHMARKS["Beratung & Dienstleistungen"]

def build_html(branche: str) -> str:
    b = lookup(branche)
    avg = int(b.get("avg", 0))
    top25 = int(b.get("top25", 0))
    src = b.get("source_title") or "Quelle"
    url = b.get("source_url") or "#"
    year = b.get("year") or ""
    return (
        "<div>"
        f"<p><strong>Branchen‑Benchmark ({canonicalize(branche)})</strong></p>"
        "<table class='table'>"
        "<thead><tr><th>Messgröße</th><th>Wert</th></tr></thead>"
        f"<tbody><tr><td>Durchschnittlicher KI‑Reifegrad</td><td>{avg}/100</td></tr>"
        f"<tr><td>Top‑Quartil (25 %)</td><td>{top25}/100</td></tr></tbody>"
        "</table>"
        f"<p class='small'>Quelle: <a href='{url}'>{src}</a> ({year}). Werte beruhen auf aktuellen Umfragen/Reports; Top‑Quartil ggf. konservativ geschätzt.</p>"
        "</div>"
    )
