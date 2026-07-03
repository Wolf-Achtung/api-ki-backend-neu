# -*- coding: utf-8 -*-
"""KIS-1235 P2b: Advisor-Kohärenz-Pass.

Der Lauf 1235 zeigte einen fachlichen Selbstwiderspruch im Kernthema
Sicherheit: Die Vendor-Cards trugen das Badge "AVV vorhanden", während die
Persönliche Einschätzung vor "Anbindungen OHNE AV-Vertrag" warnte. Solche
Widersprüche zwischen den erzählenden Sektionen (Executive Summary,
Persönliche Einschätzung) und den deterministischen Fakten-Sektionen
(Vendor-Audit, Business Case, AI-Act, Förderung) entstehen, weil die
Sektionen unabhängig voneinander generiert werden.

Dieser Pass läuft NACH allen Enforcern: Er gibt dem LLM die fertigen
erzählenden Sektionen plus einen kompakten Fakten-Digest und fordert per
Structured Output (Tool-Use) eine Liste CHIRURGISCHER Korrekturen
(find/replace). Angewendet wird nur, was exakt matcht — maximal 5
Korrekturen, Ersatztexte längenbegrenzt. Kein Befund → No-op.

Flag: ADVISOR_COHERENCE_PASS (default: an).
"""
from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

_MAX_CORRECTIONS = 5
_MAX_FIND_LEN = 240
_TAG_RE = re.compile(r"<[^>]+>")

COHERENCE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "corrections": {
            "type": "array",
            "maxItems": _MAX_CORRECTIONS,
            "items": {
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "enum": ["advisor_note", "executive_summary"],
                        "description": "Sektion, in der der Widerspruch steht",
                    },
                    "find": {
                        "type": "string",
                        "description": "EXAKTER Textausschnitt aus der Sektion (ohne HTML-Tags kürzen!), der den Fakten widerspricht",
                    },
                    "replace": {
                        "type": "string",
                        "description": "Faktisch korrekte, minimal geänderte Ersatzformulierung",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Welchem Fakt widersprach die Stelle?",
                    },
                },
                "required": ["section", "find", "replace", "reason"],
            },
        },
    },
    "required": ["corrections"],
}


def _enabled() -> bool:
    return os.getenv("ADVISOR_COHERENCE_PASS", "1").strip().lower() not in (
        "0", "false", "no", "off",
    )


def _txt(html: str, limit: int = 2200) -> str:
    return _TAG_RE.sub(" ", html or "")[:limit].strip()


def build_facts_digest(sections: Dict[str, Any]) -> str:
    """Kompakter Digest der deterministischen Fakten für den Prüf-Prompt."""
    parts: List[str] = []
    _va_total = sections.get("VENDOR_AUDIT_TOTAL")
    if _va_total:
        parts.append(
            f"VENDOR-AUDIT: {_va_total} Tools geprüft — "
            f"{sections.get('VENDOR_AUDIT_GREEN', 0)} grün, "
            f"{sections.get('VENDOR_AUDIT_YELLOW', 0)} gelb, "
            f"{sections.get('VENDOR_AUDIT_RED', 0)} rot. "
            "WICHTIG zur AVV-Semantik: 'AVV verfügbar' heißt, der Anbieter BIETET "
            "einen AV-Vertrag an — ob der Nutzer ihn abgeschlossen hat, ist unbekannt. "
            "Eine Warnung, den AVV-Abschluss zu prüfen, ist daher KEIN Widerspruch."
        )
    for label, keys in (
        ("ROI (12M)", ("ROI_12M_DISPLAY_DE", "ROI_12M")),
        ("Payback (Monate)", ("PAYBACK_MONTHS_FMT_DE", "PAYBACK_MONTHS")),
        ("Zeitersparnis h/Monat", ("CANON_HOURS_MONTH",)),
        ("CAPEX €", ("CANON_CAPEX_EUR",)),
        ("AI-Act-Risikostufe", ("AI_ACT_RISK_LEVEL_DE", "AI_ACT_RISK_LEVEL")),
    ):
        for k in keys:
            v = sections.get(k)
            if v not in (None, ""):
                parts.append(f"{label}: {v}")
                break
    _funding = _txt(sections.get("FOERDERPROGRAMME_HTML", ""), 600)
    if _funding:
        parts.append(f"FÖRDERPROGRAMME (Auszug): {_funding}")
    return "\n".join(parts)


def run_advisor_coherence_pass(sections: Dict[str, Any]) -> Dict[str, Any]:
    """Prüft advisor_note + executive_summary gegen den Fakten-Digest und
    wendet chirurgische Korrekturen an. Fail-open: Fehler → No-op."""
    if not _enabled():
        return sections

    advisor = sections.get("ADVISOR_NOTE_HTML") or sections.get("advisor_note") or ""
    exec_sum = sections.get("EXECUTIVE_SUMMARY_HTML") or sections.get("executive_summary") or ""
    if not (advisor or exec_sum):
        return sections
    facts = build_facts_digest(sections)
    if not facts:
        return sections

    prompt = (
        "Du prüfst zwei erzählende Report-Sektionen auf FAKTISCHE "
        "SELBSTWIDERSPRÜCHE zu den deterministischen Fakten desselben Reports.\n\n"
        f"FAKTEN (verbindlich):\n{facts}\n\n"
        f"SEKTION advisor_note (Persönliche Einschätzung):\n{advisor[:6000]}\n\n"
        f"SEKTION executive_summary:\n{exec_sum[:6000]}\n\n"
        "AUFGABE: Finde NUR Stellen, die den FAKTEN direkt widersprechen "
        "(falsche Zahlen, falsche Statusbehauptungen, falsche Risikostufe). "
        "Stil, Meinung und Zuspitzung sind NICHT dein Thema. "
        "Für jede Stelle: 'find' = exakter zusammenhängender Textausschnitt "
        "aus der Sektion (mit HTML-Tags, falls enthalten), 'replace' = minimal "
        "korrigierte Fassung. Wenn es KEINE Widersprüche gibt: leere Liste. "
        "Lieber null Korrekturen als eine unsichere."
    )

    try:
        from services.anthropic_client import call_anthropic_structured
        result = call_anthropic_structured(
            prompt,
            section="coherence_pass",
            schema=COHERENCE_SCHEMA,
            tool_name="emit_corrections",
            system_prompt="Du bist ein präziser Fakten-Prüfer für Beratungsreports.",
            max_tokens=1500,
        )
    except Exception as exc:  # pragma: no cover
        log.warning("[KIS-1235][COHERENCE] Pass übersprungen: %s", exc)
        return sections

    corrections = (result or {}).get("corrections") or []
    if not corrections:
        log.info("[KIS-1235][COHERENCE] keine Selbstwidersprüche gefunden")
        return sections

    _slot_map = {
        "advisor_note": ("ADVISOR_NOTE_HTML", "advisor_note"),
        "executive_summary": ("EXECUTIVE_SUMMARY_HTML", "executive_summary"),
    }
    applied = 0
    for corr in corrections[:_MAX_CORRECTIONS]:
        find = str(corr.get("find") or "")
        replace = str(corr.get("replace") or "")
        slots = _slot_map.get(str(corr.get("section") or ""))
        if not slots or not find or len(find) > _MAX_FIND_LEN:
            continue
        if not replace or len(replace) > 3 * len(find) + 120:
            continue
        for slot in slots:
            val = sections.get(slot)
            if isinstance(val, str) and find in val:
                sections[slot] = val.replace(find, replace, 1)
                applied += 1
                log.info(
                    "[KIS-1235][COHERENCE] %s korrigiert (%s): %.80s → %.80s",
                    slot, str(corr.get("reason") or "")[:120], find, replace,
                )
    if applied:
        log.info("[KIS-1235][COHERENCE] %d chirurgische Korrektur(en) angewendet", applied)
    else:
        log.info("[KIS-1235][COHERENCE] %d Vorschläge, keiner exakt anwendbar", len(corrections))
    return sections
