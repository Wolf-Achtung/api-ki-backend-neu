# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Any
import html

"""
coverage_guard
--------------

Einfache Heuristik, um zu prüfen, welche wichtigen Formularfelder im Briefing
befüllt wurden und ob sie im Report (bzw. in Templates/Prompts) tatsächlich
verwendet werden.

Die Coverage dient vor allem intern als Hinweis:
- Welche Felder werden im Formular abgefragt, aber (noch) nicht im Report genutzt?
- Wie hoch ist der Anteil der genutzten Felder an allen befüllten EXPECTED_FIELDS?
"""

# Felder, die typischerweise im Fragebogen vorkommen und wichtig sind
EXPECTED_FIELDS = [
    "BRANCHE_LABEL",
    "UNTERNEHMENSGROESSE_LABEL",
    "BUNDESLAND_LABEL",
    "jahresumsatz",
    "ki_ziele",
    "strategische_ziele",
    "vision_3_jahre",
    "vision_prioritaet",
    "anwendungsfaelle",
    "ki_projekte",
    "pilot_bereich",
    "hauptleistung",
    "governance_richtlinien",
    "datenschutz",
    "datenschutzbeauftragter",
    "folgenabschaetzung",
    "technische_massnahmen",
    "ki_kompetenz",
    "ki_knowhow",
    "trainings_interessen",
    "zeitbudget",
    "change_management",
    "innovationsprozess",
    "investitionsbudget",
    "stundensatz_eur",
    "email",
    "kontakt_email",
    # KIS-AUDIT-A6: 9 scoring-relevant fields previously missing
    "roadmap_vorhanden",          # maturity_level (+8/+4)
    "meldewege",                  # _sec_meldewege_bonus
    "ai_act_kenntnis",            # _gov_ai_act_bonus
    "digitalisierungsgrad",       # Digi-Score Bonus
    "risikofreude",               # direkt mapped
    "bisherige_foerdermittel",    # direkt mapped
    "massnahmen_komplexitaet",    # direkt mapped
    "prozesse_papierlos",         # efficiency.py: digital 25%
    "automatisierungsgrad",       # efficiency.py: auto_potential 30%
]

# Felder, die sicher irgendwo im Report/Template/Prompt-System genutzt werden.
# Diese Liste ist bewusst enger als EXPECTED_FIELDS, damit "missing" wirklich
# auf ungenutzte Potenziale hinweist.
USED_IN_REPORT = {
    "BRANCHE_LABEL",
    "UNTERNEHMENSGROESSE_LABEL",
    "BUNDESLAND_LABEL",
    "jahresumsatz",
    "ki_ziele",
    "strategische_ziele",
    "vision_3_jahre",
    "anwendungsfaelle",
    "ki_projekte",
    "hauptleistung",
    "investitionsbudget",
    "stundensatz_eur",
    "email",
    "kontakt_email",
    # KIS-AUDIT-A6: scoring-relevant fields (flow into report scores indirectly)
    "roadmap_vorhanden",
    "digitalisierungsgrad",
    "risikofreude",
    "prozesse_papierlos",
    "automatisierungsgrad",
    "massnahmen_komplexitaet",
    "bisherige_foerdermittel",
    "meldewege",
    "ai_act_kenntnis",
}


def _is_filled(val: Any) -> bool:
    """Heuristik: Feld gilt als befüllt, wenn nicht leer/None."""
    if val is None:
        return False
    if isinstance(val, str):
        return val.strip() != ""
    if isinstance(val, (list, tuple, set, dict)):
        return len(val) > 0
    return True


def analyze_coverage(answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analysiert, welche EXPECTED_FIELDS im Briefing befüllt wurden und welche
    davon laut USED_IN_REPORT im Report verwendet werden.

    Rückgabe:
        {
            "present": [...],       # befüllte EXPECTED_FIELDS
            "used": [...],          # davon als genutzt markiert
            "missing": [...],       # befüllt, aber (noch) nicht genutzt
            "coverage_pct": 0..100, # used / present
            "present_count": int,
        }
    """
    present = [f for f in EXPECTED_FIELDS if _is_filled(answers.get(f))]
    used = [f for f in present if f in USED_IN_REPORT]
    missing = [f for f in present if f not in USED_IN_REPORT]
    coverage = int(round(100.0 * (len(used) / max(1, len(present)))))

    return {
        "present": present,
        "used": used,
        "missing": missing,
        "coverage_pct": coverage,
        "present_count": len(present),
    }


def build_html_report(result: Dict[str, Any]) -> str:
    """Erzeugt ein kleines HTML-Snippet für die Feedback-Box im Report."""
    if not result:
        return ""
    missing = result.get("missing", [])
    rows = "".join(
        f"<li><code>{html.escape(str(k))}</code></li>" for k in missing
    ) or "<li>—</li>"

    return (
        "<div class='fb-section'>"
        "<div class='fb-head'><span class='fb-step'>Intern</span>"
        "<h3 class='fb-title'>Daten‑Coverage (Formular → Report)</h3></div>"
        f"<p><strong>Abdeckung:</strong> {result.get('coverage_pct', 0)}% · "
        f"Felder befüllt: {result.get('present_count', 0)}</p>"
        "<div class='callout'><strong>Nicht verwertete, aber ausgefüllte Felder:</strong>"
        f"<ul>{rows}</ul>"
        "<p class='small muted'>Hinweis: Heuristik. Einige Felder fließen indirekt "
        "in Scores oder generierte Texte ein.</p>"
        "</div></div>"
    )
