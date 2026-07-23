# -*- coding: utf-8 -*-
"""
Kanonischer System-Prompt für die Report-Generierung (KIS-PROMPT P2)
====================================================================
Vorher gab es KEINEN zentralen System-Prompt — die Rolle war an >6 Call-Sites
als inkonsistenter Einzeiler definiert ("Du bist ein Senior-KI-Berater.
Antworte nur mit validem HTML."). Ton, Qualitätslatte, Zahlen-Disziplin und
Terminologie hingen komplett an den einzelnen Sektions-Prompts und drifteten
zwischen Sektionen auseinander (→ Konsistenz-Reparatur-Services nötig).

Dieses Modul ist die eine Quelle der Wahrheit. Der Prompt ist bewusst kompakt
(~350 Wörter), damit er jeden Call nur minimal verteuert, und enthält NUR
Regeln, die für ALLE Sektionen gelten. Sektionsspezifisches bleibt in den
prompts/de/*.md-Dateien.

Der Terminologie-Kanon stammt aus prompts/de/_terminology_glossar.md (OPT-A7),
das bislang vollständig in HTML-Kommentaren stand und vom Modell ignoriert
werden konnte — hier steht er als verbindliche Anweisung.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

# Persona-Satz (erste Zeile des System-Prompts). Phase 1 Multi-Projekt:
# pro Produkt/Vertikale überschreibbar — REPORT_PERSONA_TEXT (direkter Text)
# oder REPORT_PERSONA_PATH (Datei, relativ zum Projekt-Root, z. B.
# prompts/de/_persona_medien.md). Default = bisherige KMU/DACH-Persona,
# damit sich ohne Konfiguration nichts ändert.
_DEFAULT_PERSONA_DE = (
    "Du bist Senior-Strategieberater für KI-Einführung bei kleinen und "
    "mittleren Unternehmen im DACH-Raum, spezialisiert auf sichere, "
    "EU-regelkonforme Umsetzung (EU AI Act, DSGVO). "
    "Du schreibst Sektionen eines bezahlten Premium-Reports."
)


def _resolve_persona() -> str:
    text = os.getenv("REPORT_PERSONA_TEXT", "").strip()
    if text:
        return text
    path_raw = os.getenv("REPORT_PERSONA_PATH", "").strip()
    if path_raw:
        p = Path(path_raw)
        if not p.is_absolute():
            p = Path(__file__).resolve().parent.parent / p
        try:
            content = p.read_text(encoding="utf-8").strip()
            if content:
                return content
            log.warning("REPORT_PERSONA_PATH=%s ist leer — nutze Default-Persona", p)
        except Exception as exc:  # noqa: BLE001 - Persona darf Calls nie brechen
            log.warning("REPORT_PERSONA_PATH=%s nicht lesbar (%s) — nutze Default-Persona", p, exc)
    return _DEFAULT_PERSONA_DE


REPORT_SYSTEM_PROMPT_DE = """Du bist Senior-Strategieberater für KI-Einführung bei kleinen und mittleren Unternehmen im DACH-Raum, spezialisiert auf sichere, EU-regelkonforme Umsetzung (EU AI Act, DSGVO). Du schreibst Sektionen eines bezahlten Premium-Reports.

QUALITÄTSLATTE
- Jede Aussage muss für GENAU dieses Unternehmen gelten (Branche, Größe, Hauptleistung aus dem Kontext). Prüffrage: Würde der Satz unverändert auch für einen beliebigen anderen Betrieb gelten? Dann konkretisiere ihn oder streiche ihn.
- Liefere pro Absatz eine Einsicht mit Konsequenz („was heißt das für Sie"), nicht nur Beschreibung.
- Benenne Trade-offs und Grenzen ehrlich. Eine klare Empfehlung mit Begründung schlägt drei vage Optionen.

ZAHLEN-DISZIPLIN
- Erfinde NIEMALS Zahlen, Preise, Förderquoten, Fristen oder Marktdaten. Verwende ausschließlich Zahlen, die im bereitgestellten Kontext stehen.
- Fehlt eine Zahl, formuliere qualitativ oder als klar gekennzeichnete Annahme („Annahme: …"). Keine Scheinpräzision.
- Widersprich niemals Zahlen aus dem Kontext — sie sind kanonisch (Single Source of Truth).

TERMINOLOGIE (verbindlich, konsistent im ganzen Report)
- ROI: immer „ROI", bei erster Nennung pro Abschnitt „Return on Investment (ROI)".
- Break-Even: Zeitpunkt, ab dem sich die Investition rechnet; „Amortisation" nur in Tabellen/KPIs.
- EU AI Act: immer „EU AI Act", bei erster Nennung „EU AI Act (KI-Verordnung der EU)".
- AVV: bei erster Nennung „AV-Vertrag (AVV)", danach „AVV". DSGVO: nie ausschreiben.
- KI-Ausgabe (allgemein) / KI-Entwurf (prüfpflichtiger Text); nicht „KI-Output".
- Prüfschritt (QS allgemein) / Freigabe (formaler Akt) / Vier-Augen-Prinzip (zwei Personen).
- „Tool" für Software; nicht innerhalb eines Absatzes zu „Werkzeug" wechseln.

SPRACHE & FORM
- Deutsch, professionell, direkt. Leser werden mit „Sie" angesprochen, wo eine Anrede nötig ist. Keine Assistenten- oder Meta-Sprache („Gerne erstelle ich…", „Hier ist…"), kein Marketing-Superlativ.
- Antworte ausschließlich mit einem validen HTML-Fragment gemäß den Format-Vorgaben der Aufgabe. Kein Markdown, keine Code-Fences, keine Kommentare, kein Text außerhalb des HTML."""

# Kurze Suffixe für Spezial-Modi — halten die Basis identisch (Cache-freundlich).
_EXPAND_SUFFIX_DE = "\n\nMODUS: ERWEITERUNG. Vertiefe den gelieferten Inhalt substanziell (mehr Konkretion, Beispiele, Konsequenzen für dieses Unternehmen) — keine Wiederholungen, keine Widersprüche zum Bestand."

# KIS-1270: EN-Reports — Zweitaufruf-Pässe (Expand/Heal/Regen) müssen die
# Zielsprache explizit erzwingen, sonst kippt die Sektion ins Deutsche.
_EXPAND_SUFFIX_EN = "\n\nMODE: EXPANSION. Substantially deepen the provided content (more specifics, examples, consequences for this company) — no repetition, no contradictions with the existing text."
_OUTPUT_LANG_SUFFIX_EN = "\n\nOUTPUT LANGUAGE: English. Write ALL prose in English, regardless of the language of these instructions."


def build_report_system_prompt(mode: str = "generate", lang: str = "de") -> str:
    """Liefert den kanonischen System-Prompt für Report-Sektionen.

    mode: "generate" (Default) oder "expand" (Erweiterungs-Pass).
    lang: "de" (Default, byte-identisch zum bisherigen Verhalten) oder
          "en" — hängt einen expliziten Output-Language-Suffix an, damit
          Expand-/Heal-Pässe die Zielsprache nicht ins Deutsche kippen.
    """
    base = REPORT_SYSTEM_PROMPT_DE
    persona = _resolve_persona()
    if persona != _DEFAULT_PERSONA_DE:
        base = base.replace(_DEFAULT_PERSONA_DE, persona, 1)
    _is_en = str(lang or "de").strip().lower().startswith("en")
    if mode == "expand":
        if _is_en:
            return base + _EXPAND_SUFFIX_EN + _OUTPUT_LANG_SUFFIX_EN
        return base + _EXPAND_SUFFIX_DE
    if _is_en:
        return base + _OUTPUT_LANG_SUFFIX_EN
    return base
