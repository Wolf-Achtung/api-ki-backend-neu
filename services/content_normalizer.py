# -*- coding: utf-8 -*-
"""
Content-Normalizer & Enricher - FIXED VERSION (Gold Standard+)
===============================================================

FIXES:
1. ✅ Score-Rendering: Scores aus Analysis-Meta korrekt ins Template
2. ✅ {{KPI_HTML}} / {{KPI_BRANCHE_HTML}} werden generiert (nicht leer)
3. ✅ UTF-8 konsistent
4. ✅ Tavily/Perplexity nur ergänzt wenn Sections leer
5. ✅ Fallback: ROI & Kosten werden berechnet, wenn das LLM keine Tabellen liefert

Diese Version bereitet alle Content-Sections auf, berechnet Quick‑Win-Zeiten,
erstellt KPI-Dashboards und erzeugt ROI-/Kosten-Tabellen, falls diese nicht
vom LLM geliefert wurden. So werden leere oder inkonsistente Werte im
finalen PDF vermieden.
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
    # häufige Wrapper entfernen
    s = re.sub(r"<p>\s*(</?)(h\d|ul|ol|table)", r"\1\2", s, flags=re.IGNORECASE)
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
    """Extrahiert Stundenangaben aus Text."""
    if not text:
        return 0.0
    total = 0.0
    # Ranges zuerst
    for m in _H_RANGE.finditer(text):
        a = float(m.group("a").replace(",", "."))
        b = float(m.group("b").replace(",", "."))
        total += (a + b) / 2.0
    # Einzelwerte
    text_wo_ranges = _H_RANGE.sub(" ", text)
    for m in _H_SINGLE.finditer(text_wo_ranges):
        total += float(m.group("hours").replace(",", "."))
    return total


def _split_quickwins_to_columns(qw_html: str) -> Tuple[str, str, float]:
    """Teilt Quick Wins Liste in zwei Spalten."""
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

def normalize_and_enrich_sections(
    sections: Dict[str, str],
    answers: Dict[str, Any],
    scores: Dict[str, Any],
    meta: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Normalisiert HTML-Sections und reichert Template-Variablen an.
    
    Args:
        sections: Dict mit HTML-Sections (von LLM generiert)
        answers: Fragebogen-Antworten
        scores: Score-Dict (WICHTIG: muss governance/security/value/enablement/overall enthalten)
        meta: Optional - Analysis-Metadata (falls vorhanden)
        
    Returns:
        Dict mit allen Template-Variablen (UPPERCASE keys)
    """
    out: Dict[str, Any] = {}
    # =====================================================================
    # ✅ FIX 1: SCORES AUS META ODER SCORES-DICT EXTRAHIEREN
    # =====================================================================
    if meta and 'realistic_scores' in meta:
        rs = meta['realistic_scores']
        out["score_governance"] = rs.get("gov", scores.get("governance", 0))
        out["score_sicherheit"] = rs.get("sec", scores.get("security", 0))
        out["score_nutzen"] = rs.get("val", scores.get("value", 0))
        out["score_befaehigung"] = rs.get("ena", scores.get("enablement", 0))
        out["score_gesamt"] = rs.get("overall", scores.get("overall", 0))
    else:
        out["score_governance"] = scores.get("governance", 0)
        out["score_sicherheit"] = scores.get("security", 0)
        out["score_nutzen"] = scores.get("value", 0)
        out["score_befaehigung"] = scores.get("enablement", 0)
        out["score_gesamt"] = scores.get("overall", 0)
    # =====================================================================
    # ✅ FIX 2: KPI_HTML / KPI_BRANCHE_HTML GENERIEREN
    # =====================================================================
    rate = float(os.getenv("DEFAULT_STUNDENSATZ_EUR", "60") or "60")
    # Quick Wins verarbeiten
    qw_html = _clean_html(sections.get("QUICK_WINS_HTML") or sections.get("QUICK_WINS"))
    left, right, hpm = _split_quickwins_to_columns(qw_html)
    out["QUICK_WINS_HTML_LEFT"] = left
    out["QUICK_WINS_HTML_RIGHT"] = right
    out["monatsersparnis_stunden"] = str(int(round(hpm)))
    out["monatsersparnis_eur"] = _eur(hpm * rate)
    out["jahresersparnis_stunden"] = str(int(round(hpm * 12)))
    out["jahresersparnis_eur"] = _eur(hpm * 12 * rate)
    out["stundensatz_eur"] = str(int(rate))
    # KPI-Dashboard (Überblick)
    out["KPI_HTML"] = (
        "<table class='table'>"
        "<tbody>"
        f"<tr><th>Reifegrad gesamt</th><td>{out['score_gesamt']}/100</td></tr>"
        f"<tr><th>Monats-Ersparnis</th><td>{out['monatsersparnis_stunden']} h (≈ {out['monatsersparnis_eur']} €)</td></tr>"
        f"<tr><th>Jahres-Ersparnis</th><td>{out['jahresersparnis_stunden']} h (≈ {out['jahresersparnis_eur']} €)</td></tr>"
        f"<tr><th>Stundensatz</th><td>{out['stundensatz_eur']} €/h</td></tr>"
        "</tbody></table>"
    )
    # KPI Branche-spezifisch
    out["KPI_BRANCHE_HTML"] = build_kpi_table_html(answers.get("branche"))
    # =====================================================================
    # 3. BASIS-HTML SECTIONS
    # =====================================================================
    out["EXECUTIVE_SUMMARY_HTML"] = _clean_html(
        sections.get("EXECUTIVE_SUMMARY_HTML") or sections.get("EXEC_SUMMARY_HTML")
    )
    out["PILOT_PLAN_HTML"] = _clean_html(
        sections.get("PILOT_PLAN_HTML") or sections.get("ROADMAP_HTML")
    )
    # Business Case - ROI / Kosten trennen
    business_html = _clean_html(
        sections.get("ROI_HTML") or sections.get("BUSINESS_CASE_HTML") or ""
    )
    if "<table" in (business_html or "").lower():
        parts = re.split(r"</table>", business_html, flags=re.IGNORECASE)
        roi = (parts[0] + "</table>") if parts and parts[0].strip() else ""
        costs = (parts[1] + "</table>") if len(parts) > 1 and parts[1].strip() else ""
        out["ROI_HTML"] = roi or "<p>—</p>"
        out["COSTS_OVERVIEW_HTML"] = costs or "<p>—</p>"
    else:
        out["ROI_HTML"] = "<p>—</p>"
        out["COSTS_OVERVIEW_HTML"] = "<p>—</p>"
    # =====================================================================
    # 4. TRANSPARENZ-TEXT
    # =====================================================================
    t = (os.getenv("TRANSPARENCY_TEXT", "") or "").strip()
    if not t:
        t = (
            "Dieser Report wurde teilweise mithilfe von KI-Systemen erstellt und im "
            "europäischen Rechtsrahmen (EU AI Act, DSGVO) geprüft. Alle Empfehlungen "
            "werden redaktionell kuratiert."
        )
    out["transparency_text"] = html.escape(t)
    # =====================================================================
    # 5. PLAYBOOKS
    # =====================================================================
    out["PLAYBOOKS_HTML"] = build_playbooks_html(
        branche=answers.get("branche") or answers.get("branche_name"),
        unternehmensgroesse=answers.get("unternehmensgroesse"),
    )
    # =====================================================================
    # 6. RESEARCH-POLICY (Tools & Förderungen)
    # =====================================================================
    rp = ResearchPolicy()
    branche_norm = normalize_industry(answers.get("branche"))
    tools_days = _int_env("TOOLS_DAYS", 30)
    funding_days = _int_env("FUNDING_DAYS", 30)
    # Tools: Nur ergänzen wenn Section leer
    if not sections.get("TOOLS_HTML"):
        try:
            tools = rp.search_tools(branche=branche_norm, days=tools_days)
            out["TOOLS_HTML"] = rp.results_to_html(
                tools, "Aktuell keine qualifizierten Tool-Ergebnisse."
            )
        except Exception:
            out["TOOLS_HTML"] = "<p>Keine Tool-Recherche verfügbar.</p>"
    else:
        out["TOOLS_HTML"] = sections.get("TOOLS_HTML")
    # Förderungen: Nur ergänzen wenn Section leer
    if not sections.get("FOERDERPROGRAMME_HTML"):
        try:
            foerd = rp.search_funding(
                bundesland=answers.get("bundesland", ""),
                branche=branche_norm,
                days=funding_days
            )
            out["FOERDERPROGRAMME_HTML"] = rp.results_to_html(
                foerd, "Keine passenden Förderprogramme gefunden."
            )
        except Exception:
            out["FOERDERPROGRAMME_HTML"] = "<p>Keine Förder-Recherche verfügbar.</p>"
    else:
        out["FOERDERPROGRAMME_HTML"] = sections.get("FOERDERPROGRAMME_HTML")
    # =====================================================================
    # 7. RISIKEN & GAMECHANGER (Fallbacks)
    # =====================================================================
    out["RISKS_HTML"] = _clean_html(sections.get("RISKS_HTML") or "") or (
        "<table class='table'>"
        "<thead><tr><th>Risiko</th><th>Eintritt</th><th>Auswirkung</th><th>Mitigation</th></tr></thead>"
        "<tbody>"
        "<tr><td>Datenschutz/DSGVO</td><td>mittel</td><td>Bußgelder</td><td>DPA/TOMs</td></tr>"
        "<tr><td>Halluzinationen</td><td>hoch</td><td>Fehlentscheidungen</td><td>4-Augen-Prinzip</td></tr>"
        "</tbody></table>"
    )
    out["GAMECHANGER_HTML"] = _clean_html(sections.get("GAMECHANGER_HTML") or "")
    # =====================================================================
    # 8. LOGOS & DATUM
    # =====================================================================
    for k, v in LOGO_DEFAULTS.items():
        out.setdefault(k, v)
    out.setdefault("report_date", datetime.now().strftime("%d.%m.%Y"))
    out.setdefault("report_year", datetime.now().strftime("%Y"))
    # =====================================================================
    # 9. ROI & Kosten Fallback (neu)
    # =====================================================================
    # Wenn LLM keine validen Tabellen geliefert hat, berechne ROI und Kosten
    try:
        if out.get("ROI_HTML") == "<p>—</p>" or out.get("COSTS_OVERVIEW_HTML") == "<p>—</p>":
            size_raw = (answers.get("unternehmensgroesse") or "").lower()
            base_cost = 2000.0
            if any(k in size_raw for k in ["2", "team", "klein"]):
                base_cost = 5000.0
            elif any(k in size_raw for k in ["11", "100", "kmu", "mittel"]):
                base_cost = 8000.0
            ersparnis_jahr = hpm * 12.0 * rate
            profit = ersparnis_jahr - base_cost
            roi_percent = int(round((profit / base_cost) * 100)) if base_cost > 0 else 0
            payback_months = (base_cost / (hpm * rate)) if (hpm > 0 and rate > 0) else 0
            out["ROI_HTML"] = (
                "<table class='table'><tbody>"
                f"<tr><th>Investition (Jahr 1)</th><td>{_eur(base_cost)} €</td></tr>"
                f"<tr><th>Ersparnis (Jahr 1)</th><td>{_eur(ersparnis_jahr)} €</td></tr>"
                f"<tr><th>Netto-ROI</th><td>{roi_percent} %</td></tr>"
                f"<tr><th>Amortisationszeit</th><td>{int(round(payback_months))} Monate</td></tr>"
                "</tbody></table>"
            )
            init = base_cost * 0.5
            lic = base_cost * 0.3
            training = base_cost * 0.1
            op = base_cost * 0.1
            out["COSTS_OVERVIEW_HTML"] = (
                "<table class='table'><tbody>"
                f"<tr><th>Initiale Investition</th><td>{_eur(init)} €</td></tr>"
                f"<tr><th>Lizenzen & Hosting</th><td>{_eur(lic)} €</td></tr>"
                f"<tr><th>Schulung & Change</th><td>{_eur(training)} €</td></tr>"
                f"<tr><th>Betrieb (Jahr 1)</th><td>{_eur(op)} €</td></tr>"
                "</tbody></table>"
            )
    except Exception:
        pass
    return out