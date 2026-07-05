# -*- coding: utf-8 -*-
"""KIS-1258 / Platin++++: Judge-Feedback-Heal.

Lauf KIS-1240 zeigte die Lücke der letzten Qualitätsstufe: Der Kohärenz-Judge
(services/coherence_judge.py) urteilt GELB (spiegelung: größter Zeitfresser
des Kunden nicht explizit adressiert; dubletten: dieselbe Kernaussage nahezu
wortgleich in drei Sektionen) — aber niemand handelt auf das Urteil.

Dieser Pass schließt die Schleife: Bei GELB/ROT erzeugt EIN strukturierter
LLM-Aufruf chirurgische find/replace-Edits für die geflaggten Sektionen.
Jeder Edit wird hart validiert, bevor er angewendet wird:

  - 'find' muss EXAKT und GENAU EINMAL in der Sektion vorkommen (>= 30 Zeichen)
  - 'replace' darf keine neuen Zahlen einführen (Zahlen-Schutz: Ziffernfolgen
    in replace ⊆ Ziffernfolgen in find ∪ kanonische Werte)
  - 'replace' darf keine neuen Tag-Typen einführen (HTML-Struktur-Schutz)

Danach läuft der Judge GENAU EINMAL erneut (kein Loop, keine Eskalation).
Das Vorher-Urteil bleibt unter sections['_COHERENCE_JUDGE_PRE_HEAL'] erhalten.

Flag: PLATIN_JUDGE_HEAL (default: an). Fail-open — der Heal darf den Report
nie gefährden; im Zweifel wird ein Edit verworfen statt angewendet.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

MAX_EDITS = 6
MIN_FIND_LEN = 30

# Kandidaten-Sektionen (UPPER + Shadow-Zwilling) — deckungsgleich mit dem
# Digest des Judge, damit Edits genau dort landen, wo der Befund entstand.
_HEAL_SECTION_KEYS: Tuple[Tuple[str, ...], ...] = (
    ("EXECUTIVE_SUMMARY_HTML", "executive_summary"),
    ("BUSINESS_CASE_HTML", "business_case"),
    ("QUICK_WINS_HTML",),
    ("RECOMMENDATIONS_HTML", "recommendations"),
    ("TOOLS_EMPFEHLUNGEN_HTML", "tools_empfehlungen"),
    ("STARTER_KIT_HTML",),
    ("ADVISOR_NOTE_HTML", "advisor_note"),
    ("ROADMAP_12M_HTML", "roadmap_12m"),
    ("FOERDERPOTENZIAL_HTML", "foerderpotenzial"),
)

# Kanonische Zahlen-Quellen: Ziffernfolgen aus diesen Keys dürfen in einem
# replace zusätzlich vorkommen (z. B. wenn ein Satz die Amortisation nennt).
_CANON_NUMBER_KEYS = (
    "CANON_CAPEX_EUR", "CANON_OPEX_MONTH_EUR", "CANON_HOURS_MONTH",
    "CANON_RATE_EUR", "ROI_12M_DISPLAY_DE", "PAYBACK_MONTHS_FMT_DE",
    "PAYBACK_MONTHS", "ROI_12M",
)

HEAL_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "edits": {
            "type": "array",
            "maxItems": MAX_EDITS,
            "items": {
                "type": "object",
                "properties": {
                    "section": {"type": "string",
                                "description": "Key der Sektion, aus der 'find' stammt"},
                    "find": {"type": "string",
                             "description": "EXAKTER, einzigartiger Ausschnitt aus dem HTML (>= 30 Zeichen, inkl. Tags falls vorhanden)"},
                    "replace": {"type": "string",
                                "description": "Korrigierte Fassung; gleiche HTML-Struktur, keine neuen Zahlen"},
                    "grund": {"type": "string",
                              "description": "Welchen Judge-Befund dieser Edit behebt"},
                },
                "required": ["section", "find", "replace", "grund"],
            },
        },
    },
    "required": ["edits"],
}


def _enabled() -> bool:
    return os.getenv("PLATIN_JUDGE_HEAL", "1").strip().lower() not in (
        "0", "false", "no", "off",
    )


_NUM_RE = re.compile(r"\d[\d.,]*")
_TAG_NAME_RE = re.compile(r"</?\s*([a-zA-Z][a-zA-Z0-9]*)")


def _numbers(text: str) -> set:
    return set(_NUM_RE.findall(text or ""))


def _tag_names(text: str) -> set:
    return {t.lower() for t in _TAG_NAME_RE.findall(text or "")}


def _canon_numbers(sections: Dict[str, Any]) -> set:
    nums: set = set()
    for k in _CANON_NUMBER_KEYS:
        nums |= _numbers(str(sections.get(k) or ""))
    return nums


def _resolve_heal_keys(sections: Dict[str, Any]) -> List[str]:
    """Alle vorhandenen Kandidaten-Keys (inkl. Shadow-Zwillinge) mit Inhalt."""
    keys: List[str] = []
    for group in _HEAL_SECTION_KEYS:
        for k in group:
            v = sections.get(k)
            if isinstance(v, str) and len(v.strip()) > 40:
                keys.append(k)
    return keys


def validate_edit(edit: Dict[str, Any], sections: Dict[str, Any],
                  canon_nums: set) -> Tuple[Optional[str], str]:
    """Prüft einen Edit. Rückgabe: (Ziel-Key oder None, Grund bei Ablehnung)."""
    find = str(edit.get("find") or "")
    replace = str(edit.get("replace") or "")
    if len(find) < MIN_FIND_LEN:
        return None, f"find zu kurz ({len(find)} < {MIN_FIND_LEN})"
    if replace == find:
        return None, "replace identisch mit find"
    if len(replace) > 2.5 * len(find) + 120:
        return None, "replace unverhältnismäßig lang"
    new_nums = _numbers(replace) - _numbers(find) - canon_nums
    if new_nums:
        return None, f"neue Zahl(en) erfunden: {sorted(new_nums)[:3]}"
    new_tags = _tag_names(replace) - _tag_names(find)
    if new_tags:
        return None, f"neue Tag-Typen: {sorted(new_tags)}"

    # Ziel-Sektion: bevorzugt die vom LLM genannte, sonst jede Kandidatin,
    # in der 'find' genau einmal vorkommt.
    candidates = _resolve_heal_keys(sections)
    named = str(edit.get("section") or "")
    ordered = ([named] if named in candidates else []) + [
        k for k in candidates if k != named
    ]
    for key in ordered:
        value = sections[key]
        if value.count(find) == 1:
            return key, ""
    return None, "find nicht eindeutig in einer Kandidaten-Sektion gefunden"


def apply_edits(edits: List[Dict[str, Any]], sections: Dict[str, Any],
                run_id: str = "") -> int:
    """Wendet validierte Edits an (auch auf den Shadow-Zwilling). Gibt die
    Zahl der angewendeten Edits zurück."""
    canon_nums = _canon_numbers(sections)
    applied = 0
    for edit in edits[:MAX_EDITS]:
        key, reason = validate_edit(edit, sections, canon_nums)
        if not key:
            log.info("[%s] [PLATIN-HEAL] Edit verworfen: %s", run_id, reason)
            continue
        find, replace = str(edit["find"]), str(edit["replace"])
        # Ziel-Key + alle Zwillinge patchen, in denen find exakt 1× steht.
        twins = {key, key.lower(), key.upper(),
                 key.replace("_HTML", "").lower(), key.lower() + "_html"}
        for tk in twins:
            v = sections.get(tk)
            if isinstance(v, str) and v.count(find) == 1:
                sections[tk] = v.replace(find, replace, 1)
        applied += 1
        log.info("[%s] [PLATIN-HEAL] Edit angewendet in '%s' (%s): %.80s…",
                 run_id, key, str(edit.get("grund") or "")[:60], find)
    return applied


def run_judge_heal(sections: Dict[str, Any], answers: Dict[str, Any] | None,
                   judge_result: Dict[str, Any], run_id: str = "") -> Optional[Dict[str, Any]]:
    """Repariert die vom Judge geflaggten Befunde und re-judged EINMAL.

    Fail-open: jeder Fehler → None + Log-Warnung, Report bleibt unangetastet.
    """
    if not _enabled():
        return None
    answers = answers or {}
    try:
        flagged = [c for c in (judge_result.get("checks") or [])
                   if str(c.get("verdict")) in ("gelb", "rot")]
        if not flagged:
            return None

        findings = "\n".join(
            f"- [{c.get('id')}] {str(c.get('verdict')).upper()}: {c.get('begruendung')}"
            for c in flagged
        )
        kunde = "\n".join(
            f"{label}: {str(answers.get(key) or '').strip()[:200]}"
            for label, key in (
                ("Größter Zeitfresser (wörtlich)", "top_zeitfresser"),
                ("Zeitspar-Priorität (wörtlich)", "zeitersparnis_prioritaet"),
                ("Hauptleistung", "hauptleistung"),
            ) if str(answers.get(key) or "").strip()
        )
        section_blobs: List[str] = []
        for key in _resolve_heal_keys(sections):
            section_blobs.append(f"=== SEKTION {key} ===\n{str(sections[key])[:9000]}")
        if not section_blobs:
            return None

        prompt = (
            "Ein Qualitäts-Judge hat in einem fertigen KI-Beratungsreport diese "
            "Kohärenz-Befunde geflaggt:\n\n"
            f"{findings}\n\n"
            + (f"KUNDENANGABEN (wörtlich):\n{kunde}\n\n" if kunde else "")
            + "Unten die betroffenen Sektionen als HTML. Erzeuge MINIMALE "
            f"chirurgische Edits (max. {MAX_EDITS}), die genau diese Befunde "
            "beheben:\n"
            "- Bei DUBLETTEN: Das ERSTE Vorkommen der Aussage bleibt unverändert; "
            "formuliere die späteren Wiederholungen um oder straffe sie, sodass "
            "jede Stelle einen eigenen Aspekt betont.\n"
            "- Bei SPIEGELUNG: Erweitere einen BESTEHENDEN Satz so, dass die "
            "wörtliche Kundenangabe explizit aufgegriffen und mit dem Fokus des "
            "Reports verbunden wird (Brückensatz, keine neue Sektion).\n"
            "- 'find' muss ein EXAKTER, EINZIGARTIGER Ausschnitt aus dem HTML "
            f"sein (mind. {MIN_FIND_LEN} Zeichen, inkl. Tags, falls im Satz).\n"
            "- KEINE neuen Zahlen, KEINE neuen HTML-Tag-Typen, Ton beibehalten "
            "(Sie-Form, beratend, deutsch).\n\n"
            + "\n\n".join(section_blobs)
        )

        from services.anthropic_client import call_anthropic_structured
        result = call_anthropic_structured(
            prompt,
            section="judge_heal",
            schema=HEAL_SCHEMA,
            tool_name="emit_edits",
            system_prompt=(
                "Du bist ein präziser Report-Chirurg: minimale, exakte "
                "find/replace-Edits, niemals Umbau ganzer Sektionen."
            ),
            max_tokens=3000,
        )
        edits = (result or {}).get("edits") or []
        if not edits:
            log.info("[%s] [PLATIN-HEAL] keine Edits vorgeschlagen — übersprungen", run_id)
            return None

        applied = apply_edits(edits, sections, run_id=run_id)
        flagged_ids = [str(c.get("id")) for c in flagged]
        heal_report: Dict[str, Any] = {"proposed": len(edits), "applied": applied,
                                       "flagged": flagged_ids}
        sections["_JUDGE_HEAL"] = heal_report
        log.info("[%s] [PLATIN-HEAL] %d/%d Edit(s) angewendet (Befunde: %s)",
                 run_id, applied, len(edits), ", ".join(flagged_ids))

        if applied:
            # Vorher-Urteil sichern, dann GENAU EIN Re-Judge (kein Loop).
            sections["_COHERENCE_JUDGE_PRE_HEAL"] = judge_result
            from services.coherence_judge import run_coherence_judge
            run_coherence_judge(sections, answers, run_id=run_id)
        return heal_report
    except Exception as exc:  # pragma: no cover - Heal darf nie den Report killen
        log.warning("[%s] [PLATIN-HEAL] übersprungen: %s", run_id, exc)
        return None
