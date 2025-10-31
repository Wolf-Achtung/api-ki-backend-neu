# -*- coding: utf-8 -*-
"""
Content‑Normalizer & Enricher (v3, Gold‑Standard+)
==================================================
Verbesserungen gegenüber eurer v2-Fassung:
- Robustere HTML-Säuberung (Markdown-Fences, überflüssige Wrapper)
- Quick‑Wins: Stunden‑Parsing mit Dezimalzahlen, Bereichsangaben (z. B. "5–8 h"), "Std"/"Stunden"
- Geld-/Zahlformatierung vereinheitlicht
- Research‑Policy: nutzt ENV‑Zeitfenster (TOOLS_DAYS/FUNDING_DAYS) und ist fehlertolerant
- Tools/Förderungen: nur ergänzt, wenn Sections leer sind (LLM/Fetched-Inhalte werden nicht überschrieben)
- Scores & Transparenztext bleiben konsistent
- Optionale Default‑Logos & Datumsfelder (falls nicht bereits beim Rendern gesetzt)

Kompatibel mit eurem bestehenden Renderer und Template.
"""
from __future__ import annotations

import html
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple

from services.playbooks import build_playbooks_html, normalize_industry
from services.research_policy import ResearchPolicy
from services.kpi_sets import build_kpi_table_html


# ------------------------------- Helpers --------------------------------

LOGO_DEFAULTS = {
    "logo_primary": "templates/ki-sicherheit-logo.webp",
    "logo_tuv": "templates/tuev-logo-transparent.webp",
    "logo_dsgvo": "templates/dsgvo.svg",
    "logo_eu_ai": "templates/eu-ai.svg",
    "logo_ready": "templates/ki-ready-2025.webp",
}


def _clean_html(s: str | None) -> str:
    """Entfernt Markdown-Fences und trimmt Whitespace."""
    s = (s or "").strip()
    if not s:
        return ""
    s = s.replace("```html", "").replace("```", "")
    # häufige Wrapper entfernen (reduziert doppelte <p>)
    s = re.sub(r"<p>\s*(</?)(h\d|ul|ol|table)", r"\\1\\2", s, flags=re.IGNORECASE)
    return s


_H_RANGE = re.compile(
    r"(?P<a>[0-9]+(?:[.,][0-9]+)?)\s*(?:-|–|bis)\s*(?P<b>[0-9]+(?:[.,][0-9]+)?)\s*(?:h|std|stunden)",
    flags=re.IGNORECASE,
)
_H_SINGLE = re.compile(
    r"(?P<hours>[0-9]+(?:[.,][0-9]+)?)\s*(?:h|std|stunden)",
    flags=re.IGNORECASE,
)


def _parse_hours(text: str) -> float:
    """Extrahiert Stundenangaben (inkl. Bereiche/Dezimalzahlen) aus einem Text."""
    if not text:
        return 0.0
    total = 0.0
    # Ranges zuerst (z. B. "5–8 h")
    for m in _H_RANGE.finditer(text):
        a = float(m.group("a").replace(",", "."))
        b = float(m.group("b").replace(",", "."))
        total += (a + b) / 2.0
    # Einzelwerte (z. B. "3,5 h") – vermeide Doppelzählung, indem wir Ranges vorher entfernen
    text_wo_ranges = _H_RANGE.sub(" ", text)
    for m in _H_SINGLE.finditer(text_wo_ranges):
        total += float(m.group("hours").replace(",", "."))
    return total


def _split_quickwins_to_columns(qw_html: str) -> Tuple[str, str, float]:
    """Teilt eine <ul> Liste in zwei Spalten und summiert Stunden (Monat)."""
    items = re.findall(r"<li>(.*?)</li>", qw_html or "", flags=re.IGNORECASE | re.DOTALL)
    hours_total = 0.0
    parsed_items: List[str] = []
    for it in items:
        h = _parse_hours(it)
        hours_total += h
        parsed_items.append(f"<li>{it}</li>")
    if not parsed_items:
        return "", "", 0.0
    half = max(1, (len(parsed_items) + 1) // 2)
    left = "<ul>" + "".join(parsed_items[:half]) + "</ul>"
    right = "<ul>" + "".join(parsed_items[half:]) + "</ul>"
    return left, right, hours_total


def _eur(x: float) -> str:
    try:
        return f"{int(round(float(x))):,}".replace(",", ".")
    except Exception:
        return "0"


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except Exception:
        return default


# --------------------------- Normalizer Core -----------------------------

def normalize_and_enrich_sections(sections: Dict[str, str], answers: Dict[str, Any], scores: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}

    # 1) Basis-HTML
    out["EXECUTIVE_SUMMARY_HTML"] = _clean_html(sections.get("EXECUTIVE_SUMMARY_HTML") or sections.get("EXEC_SUMMARY_HTML"))
    out["PILOT_PLAN_HTML"] = _clean_html(sections.get("PILOT_PLAN_HTML") or sections.get("ROADMAP_HTML"))

    # 2) Business Case – ROI / Kosten trennen (erste/zweite Tabelle)
    business_html = _clean_html(sections.get("ROI_HTML") or sections.get("BUSINESS_CASE_HTML") or "")
    if "<table" in (business_html or "").lower():
        parts = re.split(r"</table>", business_html, flags=re.IGNORECASE)
        roi = (parts[0] + "</table>") if parts and parts[0].strip() else ""
        costs = (parts[1] + "</table>") if len(parts) > 1 and parts[1].strip() else ""
        out["ROI_HTML"] = roi or "<p>—</p>"
        out["COSTS_OVERVIEW_HTML"] = costs or "<p>—</p>"
    else:
        out["ROI_HTML"] = "<p>—</p>"
        out["COSTS_OVERVIEW_HTML"] = "<p>—</p>"

    # 3) Quick Wins – 2 Spalten + Stunden/EUR (Monat/Jahr)
    qw_html = _clean_html(sections.get("QUICK_WINS_HTML") or sections.get("QUICK_WINS"))
    left, right, hpm = _split_quickwins_to_columns(qw_html)
    out["QUICK_WINS_HTML_LEFT"] = left
    out["QUICK_WINS_HTML_RIGHT"] = right

    rate = float(os.getenv("DEFAULT_STUNDENSATZ_EUR", "60") or "60")
    out["monatsersparnis_stunden"] = str(int(round(hpm)))
    out["monatsersparnis_eur"] = _eur(hpm * rate)
    out["jahresersparnis_stunden"] = str(int(round(hpm * 12)))
    out["jahresersparnis_eur"] = _eur(hpm * 12 * rate)
    out["stundensatz_eur"] = str(int(rate))

    # 4) Scores auf Template-Keys
    out["score_governance"] = scores.get("governance", 0)
    out["score_sicherheit"] = scores.get("security", 0)
    out["score_nutzen"] = scores.get("value", 0)
    out["score_befaehigung"] = scores.get("enablement", 0)
    out["score_gesamt"] = scores.get("overall", 0)

    # 5) Transparenz-Text (professionell, ohne Flaps)
    t = (os.getenv("TRANSPARENCY_TEXT", "") or "").replace("ich schwöre", "").replace("ich schwoere", "").strip()
    if not t:
        t = ("Dieser Report wurde teilweise mithilfe von KI‑Systemen erstellt und im europäischen "
             "Rechtsrahmen (EU AI Act, DSGVO) geprüft. Alle Empfehlungen werden redaktionell kuratiert.")
    out["transparency_text"] = html.escape(t)

    # 6) KPI-Dashboard (Überblick) + Branchen-KPIs
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

    # 7) Playbooks
    out["PLAYBOOKS_HTML"] = build_playbooks_html(
        branche=answers.get("branche") or answers.get("branche_name"),
        unternehmensgroesse=answers.get("unternehmensgroesse"),
    )

    # 8) Research-Policy – Tools & Förderungen (Whitelist + Zeitfenster 7/30/60)
    #    Nutzt Defaults aus ENV (TOOLS_DAYS/FUNDING_DAYS), kann im Code/Lauf pro Report überschrieben werden.
    rp = ResearchPolicy()
    branche_norm = normalize_industry(answers.get("branche"))
    tools_days = _int_env("TOOLS_DAYS", 30)
    funding_days = _int_env("FUNDING_DAYS", 30)

    try:
        tools = rp.search_tools(branche=branche_norm, days=tools_days)
        if not sections.get("TOOLS_HTML"):  # LLM/Fetched Inhalt nicht überschreiben
            out["TOOLS_HTML"] = rp.results_to_html(tools, "Aktuell keine qualifizierten Tool‑Ergebnisse.")
        else:
            out["TOOLS_HTML"] = sections.get("TOOLS_HTML")
    except Exception:
        out["TOOLS_HTML"] = sections.get("TOOLS_HTML", "")

    try:
        foerd = rp.search_funding(bundesland=answers.get("bundesland", ""), branche=branche_norm, days=funding_days)
        if not sections.get("FOERDERPROGRAMME_HTML"):
            out["FOERDERPROGRAMME_HTML"] = rp.results_to_html(foerd, "Keine passenden Förderprogramme gefunden.")
        else:
            out["FOERDERPROGRAMME_HTML"] = sections.get("FOERDERPROGRAMME_HTML")
    except Exception:
        out["FOERDERPROGRAMME_HTML"] = sections.get("FOERDERPROGRAMME_HTML", "")

    # 9) Risiken (Fallback), Gamechanger
    out["RISKS_HTML"] = _clean_html(sections.get("RISKS_HTML") or "") or (
        "<table class='table'><thead><tr><th>Risiko</th><th>Eintritt</th><th>Auswirkung</th><th>Mitigation</th></tr></thead>"
        "<tbody>"
        "<tr><td>Datenschutz/DSGVO</td><td>mittel</td><td>Bußgelder/Vertrauen</td><td>DPA/TOMs, Löschkonzept</td></tr>"
        "<tr><td>Halluzinationen</td><td>hoch</td><td>Fehlentscheidungen</td><td>4‑Augen‑Prinzip, Quellenpflicht</td></tr>"
        "<tr><td>Abhängigkeit</td><td>niedrig</td><td>Lock‑in</td><td>Offene Schnittstellen, Export</td></tr>"
        "</tbody></table>"
    )
    out["GAMECHANGER_HTML"] = _clean_html(sections.get("GAMECHANGER_HTML") or "")

    # 10) Logos & Datumsangaben – nur setzen, wenn nicht bereits vorhanden
    for k, v in LOGO_DEFAULTS.items():
        out.setdefault(k, v)
    out.setdefault("report_date", datetime.now().strftime("%d.%m.%Y"))
    out.setdefault("report_year", datetime.now().strftime("%Y"))

    return out
