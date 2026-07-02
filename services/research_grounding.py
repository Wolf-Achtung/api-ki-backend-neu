# -*- coding: utf-8 -*-
"""
Research-Grounding für Content-Sektionen (KIS-PROMPT P1)
========================================================
Vorher lief der Live-Research (Perplexity/Tavily/RSS) erst NACH der
Sektions-Generierung und wurde nur als Quellen-Box angehängt — die
LLM-Analysen (Tools, Förderung, Markt, Wettbewerb) entstanden komplett
aus Trainingswissen. Der teure Research diente allein der Quellen-Optik.

Dieses Modul holt die Research-Ergebnisse VOR der Generierung (ein Aufruf,
fail-open) und liefert pro research-relevanter Sektion einen kompakten,
kuratierten Kontextblock, der an den Sektions-Prompt angehängt wird.

Steuerung:
- RESEARCH_GROUNDING_ENABLED (Default "1") — Kill-Switch.
- RESEARCH_GROUNDING_MAX_CHARS (Default 2000) — Kappung je Sektion, damit
  der Prompt nicht aufbläht.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict

log = logging.getLogger(__name__)

# Welche Sektion bekommt welche Research-Komponenten.
_SECTION_SOURCES: Dict[str, tuple] = {
    "tools_empfehlungen": ("TOOLS_TABLE_HTML", "NEWS_BOX_HTML"),
    "foerderpotenzial": ("FUNDING_TABLE_HTML",),
    "wettbewerb_benchmark": ("MARKET_INSIGHTS_HTML",),
    "unternehmensprofil_markt": ("MARKET_INSIGHTS_HTML", "NEWS_BOX_HTML"),
}

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _html_to_compact_text(html: str, max_chars: int) -> str:
    """HTML-Block → kompakter Klartext (Zeilen je Tabellenzeile/Listenpunkt)."""
    if not html:
        return ""
    # Zeilenstruktur grob erhalten, damit einzelne Einträge erkennbar bleiben.
    text = re.sub(r"</(tr|li|p|h\d)>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"</t[dh]>", " | ", text, flags=re.IGNORECASE)
    text = _TAG_RE.sub(" ", text)
    lines = []
    for raw in text.splitlines():
        line = _WS_RE.sub(" ", raw).strip(" |").strip()
        if len(line) > 3:
            lines.append(f"- {line}")
    out = "\n".join(lines)
    if len(out) > max_chars:
        out = out[:max_chars].rsplit("\n", 1)[0] + "\n- [weitere Einträge gekürzt]"
    return out


def build_research_grounding(answers: Dict[str, Any]) -> Dict[str, str]:
    """Liefert {section_name: kontextblock} für research-relevante Sektionen.

    Fail-open: Liefert bei jedem Fehler ein leeres Dict — die Generierung
    läuft dann wie bisher ohne Grounding weiter.
    """
    if os.getenv("RESEARCH_GROUNDING_ENABLED", "1").strip() != "1":
        log.info("[RESEARCH-GROUNDING] disabled via env")
        return {}

    max_chars = int(os.getenv("RESEARCH_GROUNDING_MAX_CHARS", "2000"))

    try:
        from services.research_pipeline import run_research
        blocks = run_research(answers) or {}
    except Exception as exc:
        log.warning("[RESEARCH-GROUNDING] research unavailable (%s) — continuing ungrounded", exc)
        return {}

    last_updated = str(blocks.get("last_updated") or "")
    grounding: Dict[str, str] = {}

    for section, source_keys in _SECTION_SOURCES.items():
        parts = []
        for key in source_keys:
            snippet = _html_to_compact_text(str(blocks.get(key) or ""), max_chars)
            if snippet:
                parts.append(snippet)
        if not parts:
            continue
        stand = f" (Stand: {last_updated})" if last_updated else ""
        grounding[section] = (
            "\n\n"
            "=== LIVE-RECHERCHE-KONTEXT" + stand + " ===\n"
            "Die folgenden Einträge stammen aus aktueller Live-Recherche "
            "(kuratierte Quellen). VERBINDLICH:\n"
            "- Stütze Aussagen zu aktuellen Tools, Programmen, Preisen oder "
            "Marktentwicklungen AUSSCHLIESSLICH auf diese Einträge oder auf "
            "kanonische Variablen aus dem Kontext.\n"
            "- Steht ein Detail nicht hier, formuliere qualitativ statt es zu "
            "erfinden.\n"
            "- Keine URLs im Fließtext übernehmen; Quellen zeigt die Quellen-Box.\n\n"
            + "\n".join(parts)
            + "\n=== ENDE LIVE-RECHERCHE-KONTEXT ==="
        )

    if grounding:
        log.info(
            "[RESEARCH-GROUNDING] built for %d section(s): %s",
            len(grounding), ", ".join(sorted(grounding)),
        )
    return grounding
