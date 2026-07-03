# -*- coding: utf-8 -*-
"""KIS-1234-P2: Deterministische Widerspruchs-Erkennung im Briefing.

Der KIS-1234-Lauf zeigte unaufgelöste Spannungen in den Fragebogen-Antworten
("Vorhandene Tools: keine" vs. 5 genutzte Tools in FB2; "Interne
KI-Kompetenzen: Nein" vs. "KI-Kompetenz: hoch"; "Datenreife: keine" vs.
Digitalisierungsgrad 9; Engpass "Kein Budget" vs. Investitionsbudget) —
die Reports glätteten sie stillschweigend. Dieser Pass erkennt die
bekannten Paare regelbasiert (kein LLM-Call) und liefert einen
Prompt-Block, der die LLM-Sektionen anweist, die Spannungen zu
THEMATISIEREN statt zu glätten. Das macht insbesondere die Persönliche
Einschätzung schärfer.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

_NEGATIVES = {"nein", "keine", "kein", "no", "none", "false", ""}
_HIGH = {"hoch", "sehr hoch", "fortgeschritten", "experte", "expert", "high"}


def _norm(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value).strip().lower()
    return str(value or "").strip().lower()


def detect_contradictions(
    briefing: Dict[str, Any],
    strategy_answers: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Liefert menschenlesbare Beschreibungen erkannter Spannungen."""
    b = briefing or {}
    s = strategy_answers or b.get("_strategy_answers") or {}
    findings: List[str] = []

    # 1. "Vorhandene Tools: keine" vs. real genutzte Software (FB2/ki_projekte)
    tools_fb1 = _norm(b.get("vorhandene_tools"))
    tools_fb2 = _norm(s.get("s5_software") or b.get("s5_software"))
    ki_projekte = _norm(b.get("ki_projekte"))
    if tools_fb1 in _NEGATIVES and (tools_fb2 or "api" in ki_projekte):
        _raw = s.get("s5_software") or b.get("s5_software") or b.get("ki_projekte")
        genannt = (", ".join(str(v) for v in _raw) if isinstance(_raw, list)
                   else str(_raw or "")).strip() or tools_fb2 or ki_projekte
        findings.append(
            "Im Readiness-Fragebogen wurde 'Vorhandene Tools: keine' angegeben, "
            f"gleichzeitig werden aber real genutzte Werkzeuge genannt ({genannt[:120]}). "
            "Die Tool-Basis ist also vorhanden — vermutlich wurde 'keine' als "
            "'keine formale Tool-Einführung' gemeint."
        )

    # 2. "Interne KI-Kompetenzen: Nein" vs. hohe persönliche KI-Kompetenz
    interne = _norm(b.get("interne_ki_kompetenzen"))
    kompetenz = _norm(b.get("ki_kompetenz") or b.get("ki_knowhow"))
    erfahrung = _norm(s.get("s9_ki_erfahrung") or b.get("ki_erfahrung"))
    if interne in _NEGATIVES and (kompetenz in _HIGH or erfahrung in _HIGH):
        findings.append(
            "'Interne KI-Kompetenzen: Nein' steht neben hoher persönlicher "
            "KI-Kompetenz/Erfahrung. Bei Solo-/Kleinstbetrieben ist die Frage "
            "nach 'internen' Kompetenzen doppeldeutig — fachlich vorhanden ist "
            "die Kompetenz offensichtlich."
        )

    # 3. "Datenreife: keine" vs. hoher Digitalisierungs-/Automatisierungsgrad
    datenreife = _norm(s.get("datenreife") or b.get("datenreife"))
    try:
        digi = float(str(b.get("digitalisierungsgrad", "0")).replace(",", "."))
    except (ValueError, TypeError):
        digi = 0.0
    if datenreife in _NEGATIVES and digi >= 7:
        findings.append(
            f"'Datenreife: keine' widerspricht dem Digitalisierungsgrad von {digi:g}/10. "
            "Wahrscheinlich fehlt keine Digitalisierung, sondern eine STRUKTURIERTE, "
            "KI-nutzbare Datenbasis — das ist ein anderes (lösbares) Problem."
        )

    # 4. Engpass "Kein Budget" vs. angegebenes Investitionsbudget
    engpass = _norm(s.get("s4_engpass") or b.get("groesster_engpass"))
    budget = _norm(s.get("s1_budget") or b.get("investitionsbudget") or b.get("budget"))
    if "budget" in engpass and budget not in _NEGATIVES and any(ch.isdigit() for ch in budget):
        findings.append(
            f"Der genannte Engpass 'Kein Budget' steht neben einem konkreten "
            f"Investitionsrahmen ({budget}). Vermutlich ist nicht das Budget das "
            "Problem, sondern unklare Priorisierung innerhalb des Rahmens."
        )

    return findings


def build_contradictions_box_html(
    briefing: Dict[str, Any],
    strategy_answers: Optional[Dict[str, Any]] = None,
) -> str:
    """KIS-1235: Sichtbare Beratungs-Box "Was Ihre Angaben zeigen".

    Der P2-Prompt-Block überließ die Thematisierung dem LLM — im Lauf 1235
    wurde nur 1 von 4 Spannungen aufgegriffen. Diese Box rendert die
    erkannten Spannungen DETERMINISTISCH als beratende Einordnung; sie
    entfällt komplett, wenn keine Spannungen erkannt wurden.
    """
    findings = detect_contradictions(briefing, strategy_answers)
    if not findings:
        return ""
    items = "".join(f"<li>{f}</li>" for f in findings)
    return (
        '<div class="callout card-nobreak" style="border-left:4px solid #2563eb;'
        'background:#eff6ff;padding:14px 18px;margin:16px 0;break-inside:avoid;">'
        '<p style="margin:0 0 6px 0;"><strong>Was Ihre Angaben zeigen:</strong> '
        'Einige Antworten stehen in einem produktiven Spannungsverhältnis — '
        'kein Fehler, sondern ein Hinweis, wo die Begriffe im Alltag anders '
        'belegt sind als im Fragebogen:</p>'
        f'<ul style="margin:0;padding-left:18px;">{items}</ul>'
        '</div>'
    )


def build_contradictions_block(
    briefing: Dict[str, Any],
    strategy_answers: Optional[Dict[str, Any]] = None,
) -> str:
    """Prompt-Block für die Injektion — leer, wenn nichts erkannt wurde."""
    findings = detect_contradictions(briefing, strategy_answers)
    if not findings:
        return ""
    lines = "\n".join(f"- {f}" for f in findings)
    return (
        "\n\n-----\n"
        "BEKANNTE SPANNUNGEN IN DEN ANGABEN (deterministisch erkannt):\n"
        f"{lines}\n"
        "UMGANG DAMIT (verbindlich): Diese Spannungen NICHT stillschweigend "
        "glätten. Wo fachlich relevant, kurz und beratend einordnen (1 Satz "
        "genügt) — das erhöht die Glaubwürdigkeit der Analyse. Keine "
        "Meta-Kommentare über den Fragebogen selbst.\n"
    )
