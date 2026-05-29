# -*- coding: utf-8 -*-
"""FIX-KIS-1027.4.1-H2: Encoding-Sweep für PDF-Display-Strings.

Sprint-1027.4-Item-3F war Punkt-Korrektur einer Stelle.
KIS-1198 zeigte mehrere weitere "Uebersicht"/"Foerder"-Artefakte:
- R1 S.13: "Monitoring-Uebersicht aufsetzen" (Dashboard->Uebersicht
  Lexikon-Replacement)
- Strategy: "Foerderquote"/"Ueber Branchenmedian" in benchmark prompt

Dieser Test sichert, dass kundensichtbare Strings durchgaengig echte
UTF-8-Umlaute nutzen. Test scannt:
  - data/lexicon/*.json replacement values (Pipeline-Output)
  - prompts/de/*.md (LLM-emittierter Content)
  - hardcoded Display-Strings in services/benchmark_engine.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Bekannte False-Positives (z.B. URL-Slugs, ASCII-Variable-Namen, Mausklick,
# Beraterumfeld, Tausend, ausbauen). Liste klein halten — eher
# Bad-Pattern-Wortliste zaehlen als False-Positives auflisten.
_GOOD_ALLOWLIST = {
    "Mausklick", "Tausend", "Tausende", "ausbauen", "Beraterumfeld",
    "Aushilfe", "ueber",  # eng. "over"
}

# Bad strings (ASCII-Fallback statt Umlaut) die in Display-Strings NICHT vorkommen duerfen.
# Format: ASCII-form -> erwartete Umlaut-form (nur fuer Reporting)
_BAD_TOKENS = {
    "Uebersicht": "Übersicht",
    "Foerder": "Förder",
    "Foerd": "Förd",
    "Ueber Branchen": "Über Branchen",
    "ueber Branchen": "über Branchen",
    "ueber Median": "über Median",
    "ueber Durchschnitt": "über Durchschnitt",
    "gegenueber": "gegenüber",
    "Rueckstand": "Rückstand",
    "Ausschoepfung": "Ausschöpfung",
    "Verknuepfe": "Verknüpfe",
    "Uebersetzung": "Übersetzung",
    "Pruefpfad": "Prüfpfad",
    "Aenderungssteuerung": "Änderungssteuerung",
    "Fuehrungsebene": "Führungsebene",
    "Ablaeufe": "Abläufe",
    "Arbeitsablaeufe": "Arbeitsabläufe",
    "Regelkonformitaet": "Regelkonformität",
}


def _scan_text(text: str, source: str) -> list:
    """Return list of (token, expected, source) tuples for hits."""
    hits = []
    for bad, good in _BAD_TOKENS.items():
        if bad in text:
            hits.append((bad, good, source))
    return hits


def test_lexicon_replacements_use_real_umlauts():
    """Lexicon JSON replacement values flow directly into PDF HTML."""
    hits = []
    for lex_path in [
        ROOT / "data" / "lexicon" / "solo_replacements.json",
        ROOT / "data" / "lexicon" / "team_replacements.json",
    ]:
        if not lex_path.exists():
            continue
        data = json.loads(lex_path.read_text(encoding="utf-8"))
        # data is a list of dicts with "replacement" key
        if isinstance(data, list):
            entries = data
        elif isinstance(data, dict):
            entries = data.get("rules") or data.get("replacements") or []
        else:
            entries = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            repl = entry.get("replacement", "")
            if not isinstance(repl, str):
                continue
            hits.extend(_scan_text(repl, f"{lex_path.name}:replacement={repl!r}"))
    assert not hits, (
        "Lexicon replacement values contain ASCII-fallback umlauts:\n"
        + "\n".join(f"  {bad!r} -> {good!r} in {src}" for bad, good, src in hits)
    )


def test_prompt_files_use_real_umlauts():
    """Prompts/de/*.md tell the LLM what to emit; LLM mirrors encoding."""
    hits = []
    prompts_dir = ROOT / "prompts" / "de"
    if not prompts_dir.exists():
        return
    for md in prompts_dir.glob("*.md"):
        try:
            text = md.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        hits.extend(_scan_text(text, str(md.relative_to(ROOT))))
    assert not hits, (
        f"Prompt files contain ASCII-fallback umlauts ({len(hits)} hits):\n"
        + "\n".join(f"  {bad!r} -> {good!r} in {src}" for bad, good, src in hits[:20])
    )


def test_benchmark_engine_display_string_uses_real_umlaut():
    """services/benchmark_engine.py position label 'Above'/'Ueber' -> 'Über'."""
    src = (ROOT / "services" / "benchmark_engine.py").read_text(encoding="utf-8")
    assert '"Über"' in src or "'Über'" in src, (
        "benchmark_engine.py muss 'Über' (mit Umlaut) als DE-Label nutzen"
    )
    assert '"Ueber"' not in src, "benchmark_engine.py: 'Ueber' (ASCII) regrediert"
