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
import re
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

_NEGATIVES = {"nein", "keine", "kein", "no", "none", "false", ""}
_HIGH = {"hoch", "sehr hoch", "fortgeschritten", "experte", "expert", "high"}


def _tsd(n: str) -> str:
    """1000er-Punkt: '10000' \u2192 '10.000'."""
    return f"{int(n):,}".replace(",", ".")


def _fmt_budget(value: str) -> str:
    """KIS-1237: Budget-Enums lesbar machen, bevor sie in Report-Text
    eingebettet werden. Lauf 1119 zeigte 'Investitionsrahmen (2000_10000)'
    im Strategiebericht \u2014 der Rohwert aus dem Fragebogen."""
    v = value.strip()
    m = re.fullmatch(r"(\d+)_(\d+)", v)
    if m:
        return f"{_tsd(m.group(1))}\u2013{_tsd(m.group(2))} \u20ac"
    m = re.fullmatch(r"(unter|bis)_(\d+)", v)
    if m:
        return f"unter {_tsd(m.group(2))} \u20ac"
    m = re.fullmatch(r"(ueber|ab)_(\d+)", v)
    if m:
        return f"\u00fcber {_tsd(m.group(2))} \u20ac"
    return value


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

    def _explizit_negativ(*keys: str) -> bool:
        """KIS-1267: Nur ein TATSAECHLICH negativ beantwortetes Feld zaehlt.

        _NEGATIVES enthaelt den leeren String — ein unbeantwortetes Feld
        galt damit als "keine". Im Lauf KIS-1262 stand deshalb im
        Status-Report: "'Datenreife: keine' widerspricht dem
        Digitalisierungsgrad von 8/10." Die Frage nach der Datenreife
        stellt der R1-Fragebogen aber gar nicht — sie kommt erst im
        Strategie-Fragebogen. Der Report zitierte also eine Antwort, die
        der Kunde nie gegeben hat. Der Live-Check im Chat macht das ueber
        _answered_negative() schon richtig; hier fehlte das Gegenstueck.
        """
        for key in keys:
            for quelle in (s, b):
                roh = quelle.get(key)
                if roh is None or str(roh).strip() == "":
                    continue
                if _norm(roh) in _NEGATIVES:
                    return True
                break  # Feld ist beantwortet, aber nicht negativ
        return False

    # 1. "Vorhandene Tools: keine" vs. real genutzte Software (FB2/ki_projekte)
    tools_fb2 = _norm(s.get("s5_software") or b.get("s5_software"))
    ki_projekte = _norm(b.get("ki_projekte"))
    if _explizit_negativ("vorhandene_tools") and (tools_fb2 or "api" in ki_projekte):
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
    kompetenz = _norm(b.get("ki_kompetenz") or b.get("ki_knowhow"))
    erfahrung = _norm(s.get("s9_ki_erfahrung") or b.get("ki_erfahrung"))
    if _explizit_negativ("interne_ki_kompetenzen") and (kompetenz in _HIGH or erfahrung in _HIGH):
        findings.append(
            "'Interne KI-Kompetenzen: Nein' steht neben hoher persönlicher "
            "KI-Kompetenz/Erfahrung. Bei Solo-/Kleinstbetrieben ist die Frage "
            "nach 'internen' Kompetenzen doppeldeutig — fachlich vorhanden ist "
            "die Kompetenz offensichtlich."
        )

    # 3. "Datenreife: keine" vs. hoher Digitalisierungs-/Automatisierungsgrad
    try:
        digi = float(str(b.get("digitalisierungsgrad", "0")).replace(",", "."))
    except (ValueError, TypeError):
        digi = 0.0
    if _explizit_negativ("datenreife") and digi >= 7:
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
            f"Investitionsrahmen ({_fmt_budget(budget)}). Vermutlich ist nicht das Budget das "
            "Problem, sondern unklare Priorisierung innerhalb des Rahmens."
        )

    # 5. Zwei Budget-Angaben, die sich unterscheiden (KIS-1267)
    #
    # investitionsbudget (FB1) und s1_budget (FB2) nutzen dieselbe
    # Enum-Skala — es ist dieselbe Frage, zweimal gestellt. Im Lauf
    # KIS-1262 kamen zwei verschiedene Antworten heraus (2000_10000 und
    # 10000_50000). Ergebnis: Der Status-Report schrieb "uebersteigt
    # diesen Rahmen", der Strategiebericht "ist ausreichend" — zur selben
    # Investition. Ungleiche Angaben muessen thematisiert statt geglaettet
    # werden.
    budget_r1 = _norm(b.get("investitionsbudget"))
    budget_fb2 = _norm(s.get("s1_budget") or b.get("s1_budget"))
    if budget_r1 and budget_fb2 and budget_r1 != budget_fb2:
        findings.append(
            f"Zum Budget liegen zwei unterschiedliche Angaben vor: "
            f"{_fmt_budget(budget_r1)} im Readiness-Fragebogen, "
            f"{_fmt_budget(budget_fb2)} im Strategie-Fragebogen. "
            "Für die Bewertung der Investition gilt die spätere Angabe "
            "aus dem Strategie-Fragebogen; die Differenz sollte benannt "
            "und nicht stillschweigend geglättet werden."
        )

    return findings


def detect_contradictions_chat(
    collected: Dict[str, Any],
) -> List[tuple]:
    """KIS-1235-P3: Kurzformen für den Live-Abgleich im Chat.

    Liefert (stabiler_key, kurze_rückfrage) für jede aktuell erkennbare
    Spannung in den gesammelten Antworten. Der Chat stellt die Rückfrage
    genau EINMAL (Ack wird in der Session gespeichert) — der Nutzer kann
    kurz antworten oder einfach weitermachen.
    """
    b = collected or {}
    out: List[tuple] = []

    def _answered_negative(*keys: str) -> bool:
        """True nur, wenn eines der Felder EXPLIZIT mit einem Negativ-Wert
        beantwortet wurde. Ein noch nicht gestelltes Feld (fehlend/leer)
        darf im Live-Check nichts auslösen — sonst käme die Rückfrage,
        bevor die Frage überhaupt dran war."""
        for k in keys:
            raw = b.get(k)
            if raw is None or str(raw).strip() == "":
                continue
            if _norm(raw) in _NEGATIVES:
                return True
        return False

    tools_fb1 = _norm(b.get("vorhandene_tools"))
    tools_real = _norm(b.get("s5_software")) or (
        _norm(b.get("ki_projekte")) if "api" in _norm(b.get("ki_projekte")) else ""
    )
    if _answered_negative("vorhandene_tools") and tools_real:
        out.append((
            "tools",
            "Kurzer Abgleich: Bei den Business-Systemen stand \u201ekeine\u201c \u2014 "
            "gleichzeitig nutzen Sie aber KI-Werkzeuge. Ich werte das als "
            "\u201ekeine klassischen Systeme wie CRM/ERP, aber KI-Tools im "
            "Einsatz\u201c. Passt das?",
        ))

    kompetenz = _norm(b.get("ki_kompetenz"))
    if _answered_negative("interne_ki_kompetenzen") and kompetenz in _HIGH:
        out.append((
            "kompetenz",
            "Kurzer Abgleich: \u201eInternes KI-Know-how: Nein\u201c steht neben "
            "Ihrer als hoch eingestuften KI-Kompetenz \u2014 ich werte Ihre "
            "pers\u00f6nliche Kompetenz als das interne Know-how. Einverstanden?",
        ))

    try:
        digi = float(str(b.get("digitalisierungsgrad", "0")).replace(",", "."))
    except (ValueError, TypeError):
        digi = 0.0
    if _answered_negative("datenreife") and digi >= 7:
        out.append((
            "datenreife",
            f"Kurzer Abgleich: Digitalisierungsgrad {digi:g}/10, aber "
            "\u201eDatenreife: keine\u201c \u2014 gemeint ist vermutlich: digital "
            "ja, aber noch ohne strukturierte, KI-nutzbare Datenbasis. Richtig?",
        ))

    engpass = _norm(b.get("s4_engpass") or b.get("groesster_engpass"))
    budget = _norm(b.get("s1_budget") or b.get("investitionsbudget") or b.get("budget"))
    if "budget" in engpass and budget not in _NEGATIVES and any(ch.isdigit() for ch in budget):
        out.append((
            "budget",
            "Kurzer Abgleich: Als Engpass nennen Sie \u201eKein Budget\u201c, "
            "gleichzeitig ist ein Investitionsrahmen angegeben \u2014 ich lese das "
            "als Priorisierungsfrage, nicht als hartes Null-Budget. Passt das?",
        ))

    return out


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
