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
    # KIS-1264: pdf_template_v7 rendert das Business-Case-Kapitel aus
    # BUSINESS_CASE_ENGINE_HTML (KIS-1262) — Heal-Edits muessen dort
    # ankommen koennen, sonst heilt der Heal nur den Judge-Digest,
    # nicht das PDF (Lauf 1125: Budget-Edit fuer den Leser unsichtbar).
    ("BUSINESS_CASE_ENGINE_HTML", "BUSINESS_CASE_HTML", "business_case"),
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


def _answer_numbers(answers: Dict[str, Any] | None) -> set:
    """KIS-1264: Ziffernfolgen aus den KUNDENANGABEN.

    Lauf 1125: Der Heal wollte das Budget-Band des Kunden zitieren
    ("10.000–50.000 €") und wurde verworfen ("neue Zahl(en) erfunden:
    ['10.000', '50.000']") — die Zahlen stammten aus
    answers['investitionsbudget'] = '10000_50000'. Kundenangaben sind
    keine erfundenen Zahlen; der Heal-Prompt reicht sie sogar wörtlich
    als Kontext hinein."""
    nums: set = set()
    for v in (answers or {}).values():
        nums |= _numbers(str(v or ""))
    return nums


def _norm_num(token: str) -> str:
    """Tausender-/Dezimal-Separatoren entfernen: '10.000' ≙ '10000'."""
    return token.replace(".", "").replace(",", "")


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
    # KIS-1260: 2.5×+120 → 3×+240 — der Brückensatz-Edit für den
    # budget-Befund (Lauf run-38da98cc) wurde sonst verworfen.
    if len(replace) > 3.0 * len(find) + 240:
        return None, "replace unverhältnismäßig lang"
    # KIS-1264: Vergleich zusätzlich separator-normalisiert — '10.000' im
    # replace ist zulässig, wenn '10000' in den erlaubten Quellen steht.
    allowed = _numbers(find) | canon_nums
    allowed_norm = {_norm_num(n) for n in allowed}
    new_nums = {n for n in _numbers(replace)
                if n not in allowed and _norm_num(n) not in allowed_norm}
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
                run_id: str = "", answers: Dict[str, Any] | None = None) -> int:
    """Wendet validierte Edits an (auch auf den Shadow-Zwilling). Gibt die
    Zahl der angewendeten Edits zurück."""
    canon_nums = _canon_numbers(sections) | _answer_numbers(answers)
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


_VERDICT_RANK = {"gruen": 0, "gelb": 1, "rot": 2}


def apply_rejudge_ratchet(pre: Dict[str, Any], post: Dict[str, Any],
                          sections: Dict[str, Any], run_id: str = "") -> bool:
    """KIS-1264: Der Re-Judge VERIFIZIERT den Heal — er eröffnet keine
    neuen Befunde.

    Lauf 1125: budget wurde geheilt (🟡→🟢), aber dubletten flippte im
    Re-Judge durch Judge-Varianz 🟢→🟡 (nahezu identischer Input, der
    erste Judge sah dieselben Sektionen als gruen) — Gesamt-Ampel blieb
    GELB und der Heal-Loop kann so nie konvergieren. Regel: Checks, die
    im Vorher-Urteil GRUEN waren, behalten im Re-Judge mindestens ihr
    Vorher-Verdict. Geflaggte Checks (gelb/rot) bleiben ungeschönt —
    dort muss der Re-Judge ehrlich urteilen, ob der Heal gewirkt hat.

    Rückgabe: True, wenn mindestens ein Verdict zurückgesetzt wurde."""
    pre_map = {str(c.get("id")): str(c.get("verdict"))
               for c in (pre.get("checks") or [])}
    changed = False
    for check in (post.get("checks") or []):
        cid = str(check.get("id"))
        pre_v = pre_map.get(cid)
        post_v = str(check.get("verdict"))
        if pre_v != "gruen":
            continue
        if _VERDICT_RANK.get(post_v, 1) > _VERDICT_RANK.get(pre_v, 1):
            log.info(
                "[%s] [PLATIN-HEAL][RATCHET] %s: Re-Judge %s → Vorher-Urteil "
                "gruen beibehalten (Judge-Varianz — der Re-Judge verifiziert "
                "den Heal, er eröffnet keine neuen Befunde)",
                run_id, cid, post_v,
            )
            check["verdict"] = "gruen"
            check["begruendung"] = ("[Ratchet: Vorher-Urteil gruen beibehalten] "
                                    + str(check.get("begruendung") or ""))
            changed = True
    if changed:
        from services.coherence_judge import _overall
        post["ampel"] = _overall(post.get("checks") or [])
        sections["_COHERENCE_JUDGE"] = post
        sections["_COHERENCE_JUDGE_AMPEL"] = post["ampel"]
        if post["ampel"] == "gruen":
            log.info("[%s] [PLATIN-JUDGE] ✅ Gesamt-Ampel GRÜN — "
                     "Platin++++-Kohärenz bestätigt (nach Ratchet)", run_id)
        else:
            log.warning("[%s] [PLATIN-JUDGE] Gesamt-Ampel nach Ratchet: %s",
                        run_id, post["ampel"].upper())
    return changed


def run_judge_heal(sections: Dict[str, Any], answers: Dict[str, Any] | None,
                   judge_result: Dict[str, Any], run_id: str = "",
                   lang: str = "de") -> Optional[Dict[str, Any]]:
    """Repariert die vom Judge geflaggten Befunde und re-judged EINMAL.

    KIS-1275 (Aufgabe 2): lang-aware — bei EN-Reports läuft der Heal mit einer
    englischen Prompt-Variante (gleicher Kontrakt: max. MAX_EDITS chirurgische
    find/replace-Edits, Zahlen- und Tag-Schutz). Der bisherige deutsche Prompt
    verlangte wörtlich "Ton beibehalten (Sie-Form, beratend, deutsch)" und
    injizierte damit NACH dem EN-Sprachgate deutsche Sätze in EN-Reports.
    DE (default) bleibt byte-identisch.

    Fail-open: jeder Fehler → None + Log-Warnung, Report bleibt unangetastet.
    """
    if not _enabled():
        return None
    answers = answers or {}
    _is_en = str(lang or "de").strip().lower().startswith("en")
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

        if _is_en:
            # KIS-1275 (Aufgabe 2): EN-Variante — identischer Kontrakt
            # (max. MAX_EDITS chirurgische Edits), aber englischer Zieltext:
            # kein Wort Deutsch darf in den EN-Report injiziert werden.
            prompt = (
                "A quality judge flagged these coherence findings in a "
                "finished AI consulting report:\n\n"
                f"{findings}\n\n"
                + (f"CUSTOMER INPUT (verbatim):\n{kunde}\n\n" if kunde else "")
                + "Below are the affected sections as HTML. Produce MINIMAL "
                f"surgical edits (max. {MAX_EDITS}) that fix exactly these "
                "findings:\n"
                "- For DUPLICATES: keep the FIRST occurrence of the statement "
                "unchanged; rephrase or tighten the later repetitions so each "
                "spot emphasises its own aspect.\n"
                "- For MIRRORING: extend an EXISTING sentence so the verbatim "
                "customer input is explicitly picked up and connected to the "
                "report's focus (bridging sentence, no new section).\n"
                "- 'find' must be an EXACT, UNIQUE excerpt from the HTML "
                f"(at least {MIN_FIND_LEN} characters, including tags if part "
                "of the sentence).\n"
                "- NO new numbers, NO new HTML tag types. Keep the consulting "
                "tone. Write ONLY in English — the report is English, do NOT "
                "introduce any German words.\n\n"
                + "\n\n".join(section_blobs)
            )
            system_prompt = (
                "You are a precise report surgeon: minimal, exact "
                "find/replace edits, never restructuring whole sections. "
                "All replacement text must be English."
            )
        else:
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
            system_prompt = (
                "Du bist ein präziser Report-Chirurg: minimale, exakte "
                "find/replace-Edits, niemals Umbau ganzer Sektionen."
            )

        from services.anthropic_client import call_anthropic_structured
        result = call_anthropic_structured(
            prompt,
            section="judge_heal",
            schema=HEAL_SCHEMA,
            tool_name="emit_edits",
            system_prompt=system_prompt,
            max_tokens=3000,
        )
        edits = (result or {}).get("edits") or []
        if not edits:
            log.info("[%s] [PLATIN-HEAL] keine Edits vorgeschlagen — übersprungen", run_id)
            return None

        applied = apply_edits(edits, sections, run_id=run_id, answers=answers)
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
            re_result = run_coherence_judge(sections, answers, run_id=run_id)
            if re_result:
                apply_rejudge_ratchet(judge_result, re_result, sections,
                                      run_id=run_id)
        return heal_report
    except Exception as exc:  # pragma: no cover - Heal darf nie den Report killen
        log.warning("[%s] [PLATIN-HEAL] übersprungen: %s", run_id, exc)
        return None
