# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Any, Iterable, List
import html
import logging

log = logging.getLogger(__name__)

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


# ---------------------------------------------------------------------------
# KIS-1128 audit M11: Render-Context Coverage
#
# Detects silent content loss at template render time. If a generator returns
# an empty / whitespace-only string for a required key, the corresponding
# section is suppressed by the template's {% if X and X|trim %} guard. Without
# logging, these losses are invisible in production. This audit emits a
# WARNING per missing/empty required key — output is unchanged.
# ---------------------------------------------------------------------------

# Minimum required top-level context keys per report. Each key lists field names
# that — if missing or empty — likely represent a silent content loss. Cover
# only Pflicht-keys (LLM-generated narrative blocks, deterministic engines).
# Score / metadata keys are excluded (they have their own validators).
RENDER_REQUIRED_KEYS: Dict[str, List[str]] = {
    "r1": [
        "SOFORT_START_HTML",
        "QUICK_WINS_HTML",
        "ROADMAP_90D_DECISION_HTML",
        "BUSINESS_CASE_ENGINE_HTML",
        "KI_STACK_SUMMARY_HTML",
        "PROMPT_VORLAGEN_HTML",
        "CHALLENGE_30_TAGE_HTML",
        "VENDOR_AUDIT_HTML",
        "RISK_ENGINE_HTML",
        "ROADMAP_12M_HTML",
        "GAMECHANGER_DECISION_HTML",
        "ADVISOR_NOTE_HTML",
    ],
    "strategy": [
        "exec_summary",
        "section_s1",
        "section_s2",
        "section_s3",
        "section_s4",
        "section_s5",
        "section_s6",
        "section_s7",
        "naechste_schritte",
    ],
    "kpa": [
        "GC_BRUCHPUNKT_HTML",
        "GC_IMPL_PLAN_HTML",
        "BC_DEEP_DIVE_HTML",
        "GC_RISK_HTML",
        "GC_NEXT_STEPS_HTML",
    ],
}


def audit_render_context(
    report_type: str,
    context: Dict[str, Any],
    *,
    extra_required: Iterable[str] = (),
    report_id: str | None = None,
) -> List[str]:
    """
    Audit a Jinja render context for empty required keys.

    Emits one WARNING per missing/empty key. Returns the list of missing keys
    (caller may forward to telemetry). Output of the renderer is NOT modified.

    Args:
        report_type: "r1" | "strategy" | "kpa" — selects the required-key list.
        context: the dict passed to template.render(**context).
        extra_required: optional caller-specific keys to also check.
        report_id: optional id to include in log messages for traceability.
    """
    base = RENDER_REQUIRED_KEYS.get(report_type, [])
    required = list(base) + [k for k in extra_required if k not in base]
    missing: List[str] = [k for k in required if not _is_filled(context.get(k))]

    if missing:
        prefix = f"[{report_type}"
        if report_id:
            prefix += f"/{report_id}"
        prefix += "]"
        log.warning(
            "%s render-context audit: %d/%d required keys empty: %s",
            prefix,
            len(missing),
            len(required),
            ", ".join(missing),
        )
    return missing


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
