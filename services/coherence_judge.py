# -*- coding: utf-8 -*-
"""KIS-1252 / Platin++++: Kohärenz-Judge über dem fertigen Report.

Der Platin-QA-Scan (services/platin_qa.py) findet mechanische Befund-Klassen
(snake_case, Satzabbrüche, kollabierte KPIs). Was er nicht sehen kann, sind
INHALTLICHE Inkohärenzen zwischen Sektionen, die unabhängig voneinander
generiert wurden. Genau dafür läuft dieser Judge: ein LLM-Pass mit fünf
FESTEN Fragen über dem Auslieferungszustand des Reports.

Die fünf Fragen (immer dieselben, immer alle):
  vendor_ampel  Widerspricht eine Empfehlung der Vendor-Ampel?
  budget        Wird das Kundenbudget respektiert bzw. eine Überschreitung
                explizit eingeordnet?
  zahlen        Ist jede zentrale Zahl aus dem Business Case herleitbar?
  spiegelung    Werden die wörtlichen Kundenangaben aufgegriffen?
  dubletten     Gibt es inhaltliche Doppel-Aussagen?

Ergebnis: Ampel (gruen/gelb/rot) je Frage + Gesamt-Ampel, abgelegt unter
sections['_COHERENCE_JUDGE'] und als Log-Zeilen ([PLATIN-JUDGE]). NICHT
blockierend — der Judge urteilt, er repariert nicht (chirurgische
Korrekturen macht weiterhin services/coherence_pass.py).

Flag: PLATIN_COHERENCE_JUDGE (default: an). Ohne API-Key: No-op.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")

CHECK_IDS = ["vendor_ampel", "budget", "zahlen", "spiegelung", "dubletten"]

_CHECK_QUESTIONS = {
    "vendor_ampel": (
        "Widerspricht eine Tool-Empfehlung der Vendor-Ampel? (Ein rot/gelb "
        "bewerteter Anbieter, der ohne die genannten Schutzmaßnahmen "
        "uneingeschränkt empfohlen wird, ist ein Widerspruch. Eine Empfehlung "
        "MIT Hinweis auf AVV/Opt-out/EU-Region ist KEIN Widerspruch.)"
    ),
    "budget": (
        "Wird das vom Kunden angegebene Investitionsbudget respektiert? "
        "(KIS-1260-Kalibrierung: Eine Investition INNERHALB des Budgetbands "
        "ist gruen — auch am oberen Rand, sofern der Report die Grenznähe "
        "irgendwo einordnet (z. B. 'Budget-Einordnung', gestufter Einstieg, "
        "Förder-Pfad). Nur eine Investition am oberen Rand OHNE jede "
        "Einordnung = gelb. Rot AUSSCHLIESSLICH bei unkommentierter "
        "ÜBERSCHREITUNG des Bands.)"
    ),
    "zahlen": (
        "Ist jede zentrale Kennzahl in den erzählenden Sektionen aus den "
        "KANONISCHEN WERTEN herleitbar (ROI, Startinvestition, laufende "
        "Kosten, Zeitersparnis, Amortisation)? Frei erfundene oder stark "
        "abweichende Zahlen = rot; gerundete/konservativere Darstellung = gruen."
    ),
    "spiegelung": (
        "Werden die wörtlichen Kundenangaben (größter Zeitfresser, "
        "Zeitspar-Priorität, Hauptleistung) inhaltlich im Report aufgegriffen? "
        "(KIS-1260-Kalibrierung: gruen, wenn die Angabe irgendwo erkennbar "
        "adressiert wird UND der Report-Fokus daran anschließt — auch wenn er "
        "den Begriff fachlich PRÄZISIERT, z. B. 'Dokumentation und Berichte' "
        "→ 'Buchhaltungsbelege', solange die Verbindung sichtbar ist. Gelb "
        "nur, wenn eine Angabe komplett unverbunden bleibt; rot, wenn keine "
        "der Angaben vorkommt.)"
    ),
    "dubletten": (
        "Gibt es inhaltliche Doppel-Aussagen — derselbe Satz NAHEZU "
        "WORTGLEICH (im Wesentlichen identische Formulierung) in mehreren "
        "Sektionen? (KIS-1260-Kalibrierung: Dieselbe Kernbotschaft in "
        "UNTERSCHIEDLICHER Formulierung ist ein zulässiger roter Faden = "
        "gruen. Eine Fokus-/Übersichtsliste und ihr ausführlicher Abschnitt "
        "INNERHALB DERSELBEN Sektion zählen nicht als Dublette. Gelb erst "
        "ab drei nahezu wortgleichen Vorkommen ÜBER Sektionsgrenzen hinweg.)"
    ),
}

JUDGE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "checks": {
            "type": "array",
            "minItems": 5,
            "maxItems": 5,
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "enum": CHECK_IDS},
                    "verdict": {
                        "type": "string",
                        "enum": ["gruen", "gelb", "rot"],
                        "description": "gruen = kohärent, gelb = unscharf/teilweise, rot = belegter Widerspruch",
                    },
                    "begruendung": {
                        "type": "string",
                        "description": "Ein Satz Begründung; bei gelb/rot mit konkretem Beleg (Zitat/Zahl)",
                    },
                },
                "required": ["id", "verdict", "begruendung"],
            },
        },
    },
    "required": ["checks"],
}


def _enabled() -> bool:
    return os.getenv("PLATIN_COHERENCE_JUDGE", "1").strip().lower() not in (
        "0", "false", "no", "off",
    )


def _txt(html: Any, limit: int = 2400) -> str:
    return _TAG_RE.sub(" ", str(html or "")).strip()[:limit]


def build_judge_digest(sections: Dict[str, Any], answers: Dict[str, Any]) -> str:
    """Kompakter Digest: kanonische Fakten + Kundenangaben + Sektionsauszüge."""
    parts: List[str] = []

    facts: List[str] = []
    for label, keys in (
        ("ROI Jahr 1", ("ROI_12M_DISPLAY_DE", "ROI_12M")),
        ("Startinvestition €", ("CANON_CAPEX_EUR",)),
        ("Laufende Kosten €/Monat", ("CANON_OPEX_MONTH_EUR",)),
        ("Zeitersparnis h/Monat", ("CANON_HOURS_MONTH",)),
        ("Stundensatz €", ("CANON_RATE_EUR",)),
        ("Amortisation (Monate)", ("PAYBACK_MONTHS_FMT_DE", "PAYBACK_MONTHS")),
    ):
        for k in keys:
            v = sections.get(k)
            if v not in (None, ""):
                facts.append(f"{label}: {v}")
                break
    if facts:
        parts.append("KANONISCHE WERTE:\n" + "\n".join(facts))

    _va_total = sections.get("VENDOR_AUDIT_TOTAL")
    if _va_total:
        parts.append(
            f"VENDOR-AMPEL: {_va_total} Tools geprüft — "
            f"{sections.get('VENDOR_AUDIT_GREEN', 0)} grün, "
            f"{sections.get('VENDOR_AUDIT_YELLOW', 0)} gelb, "
            f"{sections.get('VENDOR_AUDIT_RED', 0)} rot."
        )

    kunde: List[str] = []
    for label, key in (
        ("Investitionsbudget (Angabe)", "investitionsbudget"),
        ("Größter Zeitfresser (wörtlich)", "top_zeitfresser"),
        ("Zeitspar-Priorität (wörtlich)", "zeitersparnis_prioritaet"),
        ("Hauptleistung", "hauptleistung"),
    ):
        v = str(answers.get(key) or "").strip()
        if v:
            kunde.append(f"{label}: {v[:200]}")
    if kunde:
        parts.append("KUNDENANGABEN:\n" + "\n".join(kunde))

    for title, keys, limit in (
        ("EXECUTIVE SUMMARY", ("EXECUTIVE_SUMMARY_HTML", "executive_summary"), 2400),
        ("BUSINESS CASE", ("BUSINESS_CASE_HTML", "business_case"), 2400),
        ("QUICK WINS", ("QUICK_WINS_HTML",), 1800),
        ("EMPFEHLUNGEN", ("RECOMMENDATIONS_HTML", "recommendations"), 1800),
        ("TOOL-EMPFEHLUNGEN", ("TOOLS_EMPFEHLUNGEN_HTML", "STARTER_KIT_HTML"), 1800),
        ("VENDOR-AUDIT (Auszug)", ("VENDOR_AUDIT_HTML",), 1400),
        ("PERSÖNLICHE EINSCHÄTZUNG", ("ADVISOR_NOTE_HTML", "advisor_note"), 1600),
        ("ROADMAP (Auszug)", ("ROADMAP_12M_HTML", "roadmap_12m"), 1400),
    ):
        for k in keys:
            t = _txt(sections.get(k), limit)
            if len(t) > 40:
                parts.append(f"### {title}:\n{t}")
                break

    return "\n\n".join(parts)


def _overall(checks: List[Dict[str, Any]]) -> str:
    verdicts = {str(c.get("verdict")) for c in checks}
    if "rot" in verdicts:
        return "rot"
    if "gelb" in verdicts:
        return "gelb"
    return "gruen"


_AMPEL_ICON = {"gruen": "🟢", "gelb": "🟡", "rot": "🔴"}


def run_coherence_judge(sections: Dict[str, Any], answers: Dict[str, Any] | None = None,
                        run_id: str = "") -> Optional[Dict[str, Any]]:
    """Stellt die 5 festen Kohärenz-Fragen an den fertigen Report.

    Nicht blockierend, fail-open: jeder Fehler → None + Log-Warnung.
    Ergebnis wird unter sections['_COHERENCE_JUDGE'] abgelegt.
    """
    if not _enabled():
        return None
    answers = answers or {}
    try:
        digest = build_judge_digest(sections, answers)
        if len(digest) < 200:
            log.info("[%s] [PLATIN-JUDGE] Digest zu dünn — Judge übersprungen", run_id)
            return None

        questions = "\n".join(
            f"{i + 1}. [{cid}] {_CHECK_QUESTIONS[cid]}" for i, cid in enumerate(CHECK_IDS)
        )
        prompt = (
            "Du prüfst einen fertigen KI-Beratungsreport auf INNERE KOHÄRENZ. "
            "Unten stehen die kanonischen Werte, die wörtlichen Kundenangaben "
            "und Auszüge der erzählenden Sektionen.\n\n"
            f"{digest}\n\n"
            "Beantworte GENAU diese fünf Fragen — für jede eine Ampel:\n"
            f"{questions}\n\n"
            "Regeln: 'rot' NUR bei konkret belegbarem Widerspruch (Zitat oder "
            "Zahl in der Begründung nennen). 'gelb' bei Unschärfe oder nur "
            "teilweiser Abdeckung. Im Zweifel 'gruen' — du bewertest Kohärenz, "
            "nicht Stil oder Vollständigkeit."
        )
        from services.anthropic_client import call_anthropic_structured
        result = call_anthropic_structured(
            prompt,
            section="coherence_judge",
            schema=JUDGE_SCHEMA,
            tool_name="emit_verdicts",
            system_prompt="Du bist ein strenger, präziser Qualitäts-Auditor für Beratungsreports.",
            max_tokens=1600,
        )
        checks = (result or {}).get("checks") or []
        checks = [c for c in checks if c.get("id") in CHECK_IDS]
        if not checks:
            log.info("[%s] [PLATIN-JUDGE] keine verwertbare Antwort — übersprungen", run_id)
            return None

        overall = _overall(checks)
        verdict_map = {str(c.get("id")): c for c in checks}
        for cid in CHECK_IDS:
            c = verdict_map.get(cid)
            if not c:
                continue
            v = str(c.get("verdict") or "gelb")
            log.log(
                logging.INFO if v == "gruen" else logging.WARNING,
                "[%s] [PLATIN-JUDGE][%s] %s %s",
                run_id, cid, _AMPEL_ICON.get(v, v), str(c.get("begruendung") or "")[:220],
            )
        judge_result = {"ampel": overall, "checks": checks}
        sections["_COHERENCE_JUDGE"] = judge_result
        sections["_COHERENCE_JUDGE_AMPEL"] = overall
        if overall == "gruen":
            log.info("[%s] [PLATIN-JUDGE] ✅ Gesamt-Ampel GRÜN — Platin++++-Kohärenz bestätigt", run_id)
        else:
            log.warning("[%s] [PLATIN-JUDGE] Gesamt-Ampel %s %s", run_id,
                        _AMPEL_ICON.get(overall, ""), overall.upper())
        return judge_result
    except Exception as exc:  # pragma: no cover - Judge darf nie den Report killen
        log.warning("[%s] [PLATIN-JUDGE] übersprungen: %s", run_id, exc)
        return None
