# -*- coding: utf-8 -*-
"""
KIS-1132: Expertise-Level Detection for R1 Report Sections
===========================================================
Derives an expertise level (beginner/intermediate/expert) from questionnaire
answers so that section prompts can calibrate content accordingly.

An expert user who builds LLM pipelines must never see "Tag 1: ChatGPT Account
erstellen"; a beginner must not be overwhelmed with API-level advice.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, Tuple

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXPERT_API_KEYWORDS = [
    "api", "llm", "pipeline", "fine-tuning", "finetuning", "fine tuning",
    "embedding", "rag", "sdk", "langchain", "llamaindex", "vector",
    "anthropic", "openai api", "gpt-4 api", "claude api",
    "prompt engineering", "token", "transformer",
]

EXPERT_HAUPTLEISTUNG_KEYWORDS = [
    "llm", "api", "pipeline", "prompt engineering", "ki-manager",
    "ki-beratung", "ki beratung", "machine learning", "neural",
    "transformer", "deep learning", "nlp", "natural language",
    "artificial intelligence", "künstliche intelligenz",
    "ki-strategie", "ki strategie", "data science",
]

INTERMEDIATE_TOOL_KEYWORDS = [
    "chatgpt", "claude", "copilot", "midjourney", "dall-e", "dalle",
    "perplexity", "notion ai", "jasper", "copy.ai",
    "make", "zapier", "n8n", "power automate",
]

# Labels used in prompt context blocks
EXPERTISE_LABELS: Dict[str, str] = {
    "beginner": "KI-Einsteiger",
    "intermediate": "KI-Anwender",
    "expert": "KI-Experte/Entwickler",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_expertise_level(answers: Dict[str, Any]) -> str:
    """Derive expertise level from questionnaire answers.

    Returns one of: ``'beginner'``, ``'intermediate'``, ``'expert'``.

    Scoring logic:
    - ki_kompetenz 'hoch'  → +3
    - ki_kompetenz 'mittel' → +1
    - API/dev keywords in ki_projekte → +3
    - Expert keywords in hauptleistung → +2
    - digitalisierungsgrad >= 7 → +1
    - automatisierungsgrad high → +1
    - Known AI tool names in ki_einsatz/vorhandene_tools → +1

    Thresholds: >=5 expert, >=2 intermediate, else beginner.
    """
    score = 0

    ki_kompetenz = str(answers.get("ki_kompetenz", "") or "").lower().strip()
    ki_projekte = str(answers.get("ki_projekte", "") or "").lower()
    hauptleistung = str(answers.get("hauptleistung", "") or "").lower()
    ki_einsatz = answers.get("ki_einsatz", [])
    if isinstance(ki_einsatz, str):
        ki_einsatz = [ki_einsatz]
    ki_einsatz_str = " ".join(str(x) for x in ki_einsatz).lower()
    vorhandene_tools = str(answers.get("vorhandene_tools", "") or "").lower()
    combined_tools = ki_einsatz_str + " " + vorhandene_tools

    # --- Hard signal: self-reported competence ---
    if ki_kompetenz == "hoch":
        score += 3
    elif ki_kompetenz == "mittel":
        score += 1

    # --- API / developer keywords in ki_projekte ---
    if any(kw in ki_projekte for kw in EXPERT_API_KEYWORDS):
        score += 3

    # --- Expert keywords in hauptleistung ---
    if any(kw in hauptleistung for kw in EXPERT_HAUPTLEISTUNG_KEYWORDS):
        score += 2

    # --- digitalisierungsgrad >= 7 ---
    try:
        digi = int(answers.get("digitalisierungsgrad", 0) or 0)
    except (ValueError, TypeError):
        digi = 0
    if digi >= 7:
        score += 1

    # --- automatisierungsgrad high ---
    auto = str(answers.get("automatisierungsgrad", "") or "").lower()
    if auto in ("eher_hoch", "sehr_hoch", "hoch"):
        score += 1

    # --- Known AI tool usage (at least intermediate signal) ---
    if any(kw in combined_tools for kw in INTERMEDIATE_TOOL_KEYWORDS):
        score += 1

    # --- Thresholds ---
    if score >= 5:
        level = "expert"
    elif score >= 2:
        level = "intermediate"
    else:
        level = "beginner"

    log.info(
        "[KIS-1132] Expertise detection: score=%d → %s "
        "(ki_kompetenz=%s, ki_projekte_len=%d, hauptleistung_len=%d)",
        score, level, ki_kompetenz, len(ki_projekte), len(hauptleistung),
    )
    return level


def get_expertise_label(level: str) -> str:
    """Return the German label for a given expertise level."""
    return EXPERTISE_LABELS.get(level, EXPERTISE_LABELS["beginner"])


def build_expertise_context_block(
    answers: Dict[str, Any],
    expertise_level: str | None = None,
) -> str:
    """Build a prompt context block that calibrates LLM output to the user's
    expertise level.

    This block should be injected into every content-generating section prompt
    so the LLM can adjust its recommendations accordingly.
    """
    if expertise_level is None:
        expertise_level = detect_expertise_level(answers)

    label = get_expertise_label(expertise_level)
    ki_kompetenz = str(answers.get("ki_kompetenz", "") or "")
    ki_projekte = str(answers.get("ki_projekte", "") or "")
    hauptleistung = str(answers.get("hauptleistung", "") or "")
    digitalisierungsgrad = str(answers.get("digitalisierungsgrad", "") or "")
    vorhandene_tools = str(answers.get("vorhandene_tools", "") or "")

    block = f"""
## Kompetenz-Profil des Nutzers
- KI-Kompetenz: {ki_kompetenz} ({expertise_level})
- KI-Projekte: {ki_projekte or 'Keine'}
- Hauptleistung: {hauptleistung or 'Nicht angegeben'}
- Digitalisierungsgrad: {digitalisierungsgrad or 'Nicht angegeben'}/10
- Vorhandene Tools: {vorhandene_tools or 'Keine'}

## WICHTIGE ANWEISUNG zur Content-Kalibrierung
Der Nutzer ist ein {label}."""

    if expertise_level == "expert":
        block += """

KRITISCH: Dieser Nutzer arbeitet BEREITS mit KI-APIs und baut eigene Systeme.
KEINE Einsteiger-Tipps wie 'ChatGPT Account erstellen', 'Testen Sie KI mit
einer einfachen Aufgabe' oder generische Prompts. Empfehlungen muessen auf dem
BESTEHENDEN Niveau aufbauen und den naechsten strategischen Schritt zeigen.
Fokus auf: Pipeline-Optimierung, Governance, Monitoring, Cost-per-Output,
Prompt-Versionierung, Evaluierung, Skalierung."""

    elif expertise_level == "intermediate":
        block += """

Dieser Nutzer kennt KI-Grundlagen und nutzt Tools aktiv. Keine Grundlagen-
Erklaerungen, aber strukturierte Vertiefung und Workflow-Optimierung.
Keine Account-Erstellung, kein 'Was ist ChatGPT'. Stattdessen: Workflow-
Integration, Automatisierung, spezialisierte Branchentools."""

    block += f"""

Die Hauptleistung des Nutzers ist: {hauptleistung or 'Nicht angegeben'}
ALLE Empfehlungen muessen sich auf diese Hauptleistung beziehen.
"""
    return block
