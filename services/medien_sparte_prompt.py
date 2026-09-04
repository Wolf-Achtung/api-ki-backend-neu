# -*- coding: utf-8 -*-
"""KIS-1288: Persona und Sparte fuer System-Prompts, die kein Jinja kennen.

Der Strategiebericht formatiert seinen System-Prompt mit ``str.format``;
eine ``{% if %}``-Bedingung wie in den Markdown-Prompts geht dort nicht.
Deshalb setzt dieser Baustein die beiden Zeilen nachtraeglich:

1. Die erste Zeile („Du bist ein erfahrener KI-Strategieberater fuer den
   deutschen Mittelstand.") wird durch die konfigurierte Persona ersetzt —
   dieselbe, die der Status-Report ueber REPORT_PERSONA_PATH bekommt.
   Ohne Konfiguration bleibt die Zeile, wie sie ist.
2. Ist eine Sparte gesetzt, folgt ein Satz, der sie nennt.

Nur fuer Deutsch. Die englische Persona-Datei gibt es nicht; dort bleibt
die erste Zeile stehen, die Sparte wird trotzdem genannt.
"""
from __future__ import annotations

import os


def _persona_konfiguriert() -> str:
    """Liefert die konfigurierte Persona oder leer, wenn keine gesetzt ist."""
    if not (os.getenv("REPORT_PERSONA_TEXT", "").strip()
            or os.getenv("REPORT_PERSONA_PATH", "").strip()):
        return ""
    try:
        from services.report_system_prompt import _resolve_persona
        return _resolve_persona().strip()
    except Exception:  # pragma: no cover - Schutznetz
        return ""


def persona_und_sparte(system_prompt: str, sparte: str = "", lang: str = "de") -> str:
    """Ersetzt die Persona-Zeile (nur DE, nur bei Konfiguration) und nennt die Sparte."""
    if not system_prompt:
        return system_prompt
    is_en = str(lang or "de").lower().startswith("en")
    text = system_prompt

    if not is_en:
        persona = _persona_konfiguriert()
        if persona:
            erste, _, rest = text.partition("\n")
            if erste.strip().startswith("Du bist"):
                text = persona + "\n" + rest

    s = str(sparte or "").strip()
    if s:
        satz = (
            f"The client works in this segment of the media and creative industries: {s}. "
            "Tailor examples, tools and risks to this segment."
            if is_en else
            f"Der Kunde arbeitet in dieser Sparte der Medien- und Kreativbranche: {s}. "
            "Beispiele, Werkzeuge und Risiken auf diese Sparte zuschneiden."
        )
        erste, _, rest = text.partition("\n")
        text = erste + "\n" + satz + ("\n" + rest if rest else "")
    return text
