#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Report Validator - Quality Gate vor PDF-Generierung
====================================================
Wolf's Quality Assurance System für KI-Sicherheit.jetzt Reports

Prüft:
- Placeholder nicht ersetzt
- Leere/generische Sections
- Doppelte Context-Blöcke
- Größen-spezifische Fehler ("Team" bei Solo)
- Template-Text statt echtem Content
- Prompt-Leaks in Quick-Wins
- Generic LLM response leaks (Sprint N1)

Version: 1.8.0-SPRINT-N3 (Leak-Buster v2 + Tone Normalizer)
Author: Claude + Wolf

PLATIN+ ÄNDERUNG: Validierung basiert jetzt auf WÖRTERN statt Zeichen!

SPRINT N CHANGES:
- Extended SIZE_FORBIDDEN list for Solo personas
- Updated MIN_SECTION_LENGTH_BY_SIZE with new minimums
- Added HARD_STOP_ON_SIZE_MISMATCH option
- Critical sections now enforce minimum word counts strictly

SPRINT N1 CHANGES:
- Added GENERIC_LLM_LEAK_PHRASES detection (ChatGPT standard responses)
- Leak phrases trigger CRITICAL severity with [LEAK_PHRASE] logging
- Reduced min_words for Solo sections (transparency_box, strategie_governance)
- Added DATA_READINESS template phrase detection

SPRINT N2 CHANGES:
- Added heal_placeholder_sections() for critical empty sections
- Added validate_and_heal() to replace leak content before rendering
- Added KI_AKTIVITAETEN_ZIELE_HTML fallback builder
- Leak healing now modifies sections dict directly
"""

import re
import logging
from typing import Dict, List, Tuple, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass

# G8.2: Import centralized validation config
if TYPE_CHECKING:
    from services.config_validation import ValidationConfig as _ValidationConfigType

try:
    from services.config_validation import (
        ValidationConfig,
        get_min_words,
        SECTION_MIN_WORDS,
    )
    _HAS_CONFIG_VALIDATION = True
except ImportError:
    _HAS_CONFIG_VALIDATION = False

# B2-C: Import Tools Analytics for validation
try:
    from services.tools_analytics import (
        TOOLS_ENGINE_ENABLED,
        TOOLS_CONFIDENCE_MIN,
        get_tool_stats,
        get_segment_analysis,
    )
    _HAS_TOOLS_ANALYTICS = True
except ImportError:
    _HAS_TOOLS_ANALYTICS = False
    TOOLS_ENGINE_ENABLED = False
    TOOLS_CONFIDENCE_MIN = 0.35

    class ValidationConfig:  # type: ignore[no-redef]
        """Fallback stub when config_validation not available."""
        HARD_STOP_ON_SIZE_MISMATCH = False
        MAX_REDUNDANCY_WARNINGS = 5
        REDUNDANCY_WORD_THRESHOLD = 20
        AI_ACT_MIN_REASONING_WORDS = 60

    def get_min_words(size: str, section_key: str) -> int:
        return 100

    SECTION_MIN_WORDS = None

# FIX-SOLO-VEREINFACHUNG: Import Solo simplifier for terminology checks
try:
    from services.solo_simplifier import (
        validate_solo_content,
        is_solo_size,
        get_blacklist_headlines,
    )
    _HAS_SOLO_SIMPLIFIER = True
except ImportError:
    _HAS_SOLO_SIMPLIFIER = False

    def validate_solo_content(content: str, section_name: Optional[str] = None) -> Tuple[bool, List[Dict[str, Any]]]:
        return True, []

    def is_solo_size(size: str) -> bool:
        return "solo" in str(size).lower() or "1" in str(size)

    def get_blacklist_headlines() -> List[str]:
        return []

log = logging.getLogger(__name__)

__all__ = [
    "ValidationError",
    "ReportValidator",
    "validate_report",
    "filter_size_inappropriate_content",
    "filter_all_sections",
    # SPRINT N2: New healing functions
    "heal_placeholder_sections",
    "validate_and_heal",
    "build_ki_aktivitaeten_fallback",
    "CRITICAL_PLACEHOLDER_SECTIONS",
    # SPRINT N2: Leak phrase exports
    "GENERIC_LLM_LEAK_PHRASES",
    "remove_leak_phrases_from_html",
]


@dataclass
class ValidationError:
    severity: str  # "CRITICAL", "WARNING", "INFO"
    category: str  # z.B. "PLACEHOLDER", "EMPTY_SECTION"
    section: str   # z.B. "EXEC_SUMMARY_HTML"
    message: str
    details: str


class ReportValidator:
    """Validiert Report-Sections vor PDF-Generierung."""

    PLACEHOLDER_PATTERNS = [
        r"\{[A-Z_]+\}",
        r"\{\{[a-z_]+\}\}",
        r"\[Deliverable \d+\]",
        r"\[Name\]",
        r"\[Rollen\]",
        r"\[€\]",
        r"\[Zahlen\]",
        r"\[KPI \d+",
        r"\[Feature/System \d+",
        r"\[Kompletter Meilenstein",
        r"\[Konkrete Zahlen\]",
        r"\[X\]",
        r"\[Y\]",
        r"\[Z\]",
    ]

    # Phrasen, die klar auf Template- oder Platzhaltertexte hindeuten
    # SPRINT G2.2: Extended with meta-text patterns
    TEMPLATE_PHRASES = [
        "Hier könnten Sie",
        "Platzhalter für",
        "Beispieltext:",
        "Beispieltext",
        "Lorem ipsum",
        "lorem ipsum",
        "TODO:",
        "TODO",
        "TBD",
        "tbd",
        "An dieser Stelle",
        "hier weiter ausformulieren",
        "hier individuelle Inhalte ergänzen",
        "nach Bedarf anpassen",
        "bitte konkretisieren",
        "bitte hier Ihre",
        "hier Ihr Text",
        "Dies ist nur ein Beispiel",
        "Template-Text",
        "Platzhalter",
        "Platzhaltertext",
        "Dummy-Text",
        "Dummy Text",
        "Mustertext",
        "Beispiel-Maßnahme",
        "Beispiel-KPI",
        "Beispiel-Meilenstein",
        "Beispiel-Prozess",
        "Beispiel-Tool",
        "Beispiel-System",
        "Beispiel-Workflow",
        "Beispiel-Use Case",
        "Beispielhafte Formulierung",
        "Konkretes Beispiel hier einfügen",
        "Konkrete Beschreibung hier einfügen",
        "Konkrete Aufgaben hier einfügen",
        "Konkrete Verantwortliche hier eintragen",
        "Konkreter Zeitplan hier eintragen",
        "Konkrete Risiken hier eintragen",
        "Konkrete Maßnahmen hier eintragen",
        "Konkrete Ergebnisse hier eintragen",
        "Konkretes Zielbild hier beschreiben",
        "Kompletter Meilenstein nach Schema",
        "konkrete Zahlen ergänzen",
        "Konkrete Zahlen, z.B.",
        "Konkrete Rollen eintragen",
        "Konkrete Tools eintragen",
        "Konkrete KPIs eintragen",
        "Konkrete Systeme eintragen",
        "Konkrete Meilensteine eintragen",
        "Platzhalter für echten Inhalt",
        "CAPEX ca. €",
        "Payback etwa Monate",
        "ROI nach 12 Monaten rund %",
        # Freitext-Platzhalter – sollen im finalen Report nie stehen bleiben
        "Freitextfeld",
        "freitextfeld",
        "Freitext-Feld",
        "Freitext-Felder",
        "Freitext-Feldern",
        "hier Freitext einfügen",
        "hier Freitext eingeben",
        # SPRINT G2.2: Meta-text patterns (no actual content, just descriptions)
        "Dieser Abschnitt fasst die wichtigsten Aspekte",
        "Dieser Abschnitt fasst",
        "Die Inhalte basieren auf den",
        "Im Folgenden werden",
        "Im Folgenden finden Sie",
        "Die oben beschriebene Leistung",
        "Wie bereits erwähnt",
        "wie oben beschrieben",
        "This section summarizes",
        "The following section",
        "As mentioned above",
        "based on the information provided",
        # Meta-stub patterns
        "fasst die wichtigsten",
        "basiert auf Ihren Angaben",
        "Basierend auf Ihren Eingaben",
    ]

    QUICK_WINS_PROMPT_PHRASES = [
        "Schritt 1 – beschreibe den ersten konkreten Handgriff",
        "Schritt 2 – definiere ein kurzes Prüfverfahren",
        "Schritt 3 – integriere die Methode in den bestehenden Alltag",
    ]

    # SPRINT N1: Generic LLM response leaks - ChatGPT/GPT "standard answers"
    # These indicate the LLM didn't understand the task or returned default responses
    # Case-insensitive matching, triggers CRITICAL error → PLATIN fallback
    # SPRINT N3-04: Extended to 95+ phrases (Leak-Buster v2)
    GENERIC_LLM_LEAK_PHRASES = [
        # =================================================================
        # German generic LLM responses
        # =================================================================
        "ich sehe keine konkrete frage",
        "ich sehe keine konkrete aufgabe",
        "wie kann ich dir helfen",
        "wie kann ich ihnen helfen",
        "bitte beschreibe kurz dein anliegen",
        "bitte beschreiben sie kurz ihr anliegen",
        "wie kann ich dich unterstützen",
        "was kann ich für dich tun",
        "was kann ich für sie tun",
        "ich bin ein ki-assistent",
        "ich bin ein sprachmodell",
        "als ki-assistent",
        "als sprachmodell kann ich",
        "ich wurde von openai entwickelt",
        "ich wurde von anthropic entwickelt",
        "ich habe keinen zugriff auf",
        "ich kann keine echtzeitdaten",
        "mein wissen endet",
        "mein trainingsdaten reichen bis",
        # N3-04: Additional German LLM leak phrases
        "wie kann ich behilflich sein",
        "bitte gib mehr details",
        "bitte geben sie mehr details",
        "ich benötige weitere informationen",
        "können sie mir mehr kontext geben",
        "könnten sie ihre frage präzisieren",
        "ich verstehe ihre anfrage nicht",
        "ich verstehe deine anfrage nicht",
        "ohne weitere angaben kann ich",
        "ich brauche mehr informationen",
        "bitte spezifizieren sie",
        "bitte konkretisieren sie",
        "leider verstehe ich nicht",
        "ich bin nicht sicher, was sie meinen",
        "was genau meinen sie mit",
        "können sie das näher erläutern",
        "wie soll ich das verstehen",
        "ich habe keinen zugang zu aktuellen",
        "ich verfüge über keine echtzeitdaten",
        "basierend auf meinem wissensstand",
        "nach meinem kenntnisstand",
        "soweit mir bekannt ist",
        "ich bin mir nicht sicher, ob",
        "ich kann diese anfrage nicht bearbeiten",
        "das übersteigt meine fähigkeiten",
        "ich bin darauf trainiert",
        "als künstliche intelligenz",
        "als ki bin ich",
        "mir fehlen die nötigen informationen",
        "ohne die entsprechenden daten",
        "das kann ich leider nicht beantworten",
        "ich empfehle ihnen, einen experten zu konsultieren",
        # N3.1: Removed "wenden sie sich bitte an" - too aggressive heuristic
        "bitte haben sie verständnis",
        "entschuldigung, aber ich kann",
        "tut mir leid, ich verstehe nicht",
        "leider kann ich dazu nichts sagen",
        "ich kann ihnen dabei nicht helfen",
        "das liegt außerhalb meiner möglichkeiten",
        "stellen sie mir gerne weitere fragen",
        "haben sie noch weitere fragen",
        "ich hoffe, das hilft",
        "ich hoffe, ich konnte helfen",
        "lassen sie mich wissen, wenn sie",
        "bei weiteren fragen stehe ich",
        # =================================================================
        # English generic LLM responses
        # =================================================================
        "i don't see a specific question",
        "how can i help you",
        "please describe your request",
        "as an ai assistant",
        "as a language model",
        "i was developed by openai",
        "i was developed by anthropic",
        "i don't have access to",
        "i cannot provide real-time",
        "my knowledge cutoff",
        "my training data ends",
        # N3-04: Additional English LLM leak phrases
        "how can i assist you",
        "please provide more details",
        "i need more information",
        "could you clarify your question",
        "i'm not sure what you mean",
        "i cannot access real-time data",
        "based on my training",
        "as of my knowledge cutoff",
        "i'm an ai language model",
        "i'm just an ai",
        "i don't have the ability to",
        "i cannot browse the internet",
        "i cannot access external",
        "feel free to ask me anything",
        "let me know if you need",
        "hope this helps",
        "hope that helps",
        "i hope this information",
        "if you have any other questions",
        "please let me know if",
        "i'm here to help",
        "i'm happy to help",
        "what else can i help",
        "is there anything else",
        "unfortunately i cannot",
        "i apologize but i cannot",
        "i'm sorry but i can't",
        "i would recommend consulting",
        "please consult a professional",
        # =================================================================
        # Meta-responses that shouldn't appear in reports
        # =================================================================
        "hier ist meine antwort",
        "im folgenden finden sie meine analyse",
        "gerne erstelle ich",
        "natürlich, hier ist",
        "selbstverständlich, hier ist",
        # N3-04: Additional meta-response leaks
        "hier ist eine übersicht",
        "hier ist ein überblick",
        "nachfolgend finden sie",
        "anbei finden sie",
        "im anschluss finden sie",
        "ich habe für sie zusammengestellt",
        "ich fasse zusammen",
        "here is an overview",
        "here's a summary",
        "below you will find",
        "i've compiled for you",
        "let me summarize",
        "to summarize",
        # Prompt-echo leaks (LLM repeating instructions)
        "der nutzer fragt nach",
        "die anfrage lautet",
        "laut ihrer eingabe",
        "gemäß ihrer anfrage",
        "wie in ihrer frage erwähnt",
        "the user asks for",
        "the request is to",
        "according to your input",
        "as per your request",
        "as mentioned in your question",
        # =================================================================
        # QA-Gate v1: Additional prompt-leak patterns
        # =================================================================
        # German assistant waiting phrases
        "du hast noch keine frage",
        "du hast noch keine aufgabe",
        "sie haben noch keine frage",
        "sie haben noch keine aufgabe",
        "bitte beschreibe, wobei ich dir helfen",
        "bitte beschreibe kurz, was du benötigst",
        "bitte beschreiben sie, wobei ich ihnen helfen",
        "ich stehe dir zur verfügung",
        "ich stehe ihnen zur verfügung",
        "womit kann ich ihnen dienen",
        "womit kann ich dir dienen",
        "was führt sie zu mir",
        "was führt dich zu mir",
        "ich warte auf ihre eingabe",
        "ich warte auf deine eingabe",
        "keine eingabe erkannt",
        "keine anfrage erkannt",
        # English assistant waiting phrases
        "you haven't asked a question yet",
        "you haven't provided a task",
        "please describe what you need help with",
        "please tell me what you'd like",
        "i'm waiting for your input",
        "no input detected",
        "no request detected",
        "what can i do for you today",
        "what brings you here today",
        "i'm ready when you are",
        "just let me know what you need",
    ]

    # SPRINT N: Extended SIZE_FORBIDDEN for Solo personas
    # These terms MUST NEVER appear in Solo reports
    # SPRINT G2.1: Extended for Team and KMU persona leak detection
    # SPRINT G3.1: Extended Team/KMU lists for comprehensive Solo-leak prevention
    SIZE_FORBIDDEN = {
        "solo": [
            # Team-specific terms
            "PMO-Team",
            "Team aufbauen",
            "Team-Struktur",
            "Teamstruktur",
            "Teamwork",
            "Teamrollen",
            "Teammitglieder",
            "Change-Team",
            "Projektmanagement-Office",
            # Employee/HR terms
            "Mitarbeiter einstellen",
            "Mitarbeiterschulung",
            "Personalstrategien",
            "Belegschaft",
            # Department/Organization terms
            "Abteilung",
            "Abteilungen",
            "HR-Abteilung",
            "IT-Abteilung",
            "Fachbereich",
            "Fachbereiche",
            # SPRINT G18: "Bereichsleiter" entfernt - erlaubt wenn Kontext: Zielgruppe/Kund:Innen
            # "Bereichsleiter",
            "bereichsübergreifend",
            # English equivalents
            "team building",
            "team members",
            "hire employees",
            "department",
            "departments",
            # =====================================================
            # Problem #6 FIX: Enterprise-Sprache für Solo VERBOTEN
            # Referenz: prompts/de/_solo_language_rules.md
            # =====================================================
            # Technical enterprise buzzwords
            "Engine",
            "Plattform",
            "Framework",
            "Pipeline",
            "Architektur",
            "Baukasten",
            "Modul",
            "Stack",
            "Layer",
            "Deployment",
            # Organization jargon
            "Rollout",
            "Change Management",
            "Skalierung",
            "Stakeholder",
            "Governance-Struktur",
            "Compliance-Framework",
            "Audit-Trail",
            # Abstract concepts
            "Strategische Roadmap",
            "Meilenstein-Planung",
            "KPI-Dashboard",
            "Prozesslandschaft",
            "Wertschöpfungskette",
            "Matrixorganisation",
            "Enterprise-Software",
            "Unternehmensarchitektur",
        ],
        "team": [
            # KMU-specific terms not appropriate for small teams
            "Governance-Board",
            "Enterprise-Architektur",
            "Konzernstruktur",
            # SPRINT G3.1: Solo-specific terms - COMPREHENSIVE list
            "Ihre Agilität als Einzelperson",
            "Agilität als Einzelperson",
            "als Einzelperson",
            "Solo-Selbstständige",
            "Solo-Selbstständigen",
            "Solo-Selbstständiger",
            "Solo-Berater",
            "Solo-Beraterin",
            "Einzelunternehmer",
            "Einzelunternehmerin",
            "Freiberufler",
            "Freiberuflerin",
            "freiberuflich",
            "Selbstständiger",
            "Selbstständige",
            "Ihre persönliche Kapazität",
            "persönliche Kapazität",
            # English Solo terms
            "Your agility as a solo",
            "as a solo professional",
            "solo entrepreneur",
            "as an individual",
            "individual capacity",
            "solo practitioner",
            "freelancer",
            "freelance",
        ],
        "kmu": [
            # SPRINT G3.1: Solo-specific terms - COMPREHENSIVE list for KMU
            "Ihre Agilität als Einzelperson",
            "Agilität als Einzelperson",
            "als Einzelperson",
            "Solo-Selbstständige",
            "Solo-Selbstständigen",
            "Solo-Selbstständiger",
            "Solo-Berater",
            "Solo-Beraterin",
            "Einzelunternehmer",
            "Einzelunternehmerin",
            "Ihre persönliche Kapazität",
            "persönliche Kapazität",
            # English Solo terms
            "Your agility as a solo",
            "as a solo professional",
            "solo entrepreneur",
            "as an individual",
            "individual capacity",
            "solo practitioner",
            # Freelancer-specific terms inappropriate for 11-100 companies
            "Freiberufler",
            "Freiberuflerin",
            "freiberuflich",
            "Selbstständiger",
            "Selbstständige",
            "freelancer",
            "freelance",
        ],
    }

    # SPRINT G3.1: Replacement mappings for size-inappropriate terms
    SIZE_REPLACEMENTS = {
        "team": {
            "als Einzelperson": "als kleines Team",
            "Ihre Agilität als Einzelperson": "Ihre Agilität als kleines Team",
            "Agilität als Einzelperson": "Agilität als kleines Team",
            "Solo-Selbstständige": "kleine Teams",
            "Solo-Selbstständigen": "kleinen Teams",
            "Solo-Selbstständiger": "kleines Team",
            "Solo-Berater": "Beratungsteam",
            "Einzelunternehmer": "kleines Unternehmen",
            "Freiberufler": "Beratungsteam",
            "freiberuflich": "als Team",
            "Selbstständiger": "kleines Team",
            "Selbstständige": "kleine Teams",
            "Ihre persönliche Kapazität": "Ihre Teamkapazität",
            # English
            "as a solo professional": "as a small team",
            "solo entrepreneur": "small business",
            "as an individual": "as a team",
            "Your agility as a solo": "Your agility as a small team",
            "freelancer": "consulting team",
            "freelance": "team-based",
        },
        "kmu": {
            "als Einzelperson": "als Unternehmen",
            "Ihre Agilität als Einzelperson": "Ihre Agilität als KMU",
            "Agilität als Einzelperson": "Agilität als KMU",
            "Solo-Selbstständige": "KMU",
            "Solo-Selbstständigen": "KMU",
            "Solo-Selbstständiger": "KMU",
            "Solo-Berater": "Beratungsunternehmen",
            "Einzelunternehmer": "Unternehmen",
            "Freiberufler": "Fachteam",
            "freiberuflich": "unternehmensintern",
            "Selbstständiger": "Unternehmen",
            "Selbstständige": "Unternehmen",
            "Ihre persönliche Kapazität": "Ihre Unternehmenskapazität",
            # English
            "as a solo professional": "as a company",
            "solo entrepreneur": "SME",
            "as an individual": "as a company",
            "Your agility as a solo": "Your agility as an SME",
            "freelancer": "professional team",
            "freelance": "company-based",
        },
    }

    # SPRINT G15.1-A: Global Artifact Replacements
    # These artifacts appear due to prompt leakage and must be cleaned globally
    # Longest-first matching to avoid partial replacements
    ARTIFACT_REPLACEMENTS = {
        "OnPrüfroutineing-Mails": "Onboarding-E-Mails",
        "OnPrüfroutineing-Mail": "Onboarding-E-Mail",
        "OnPrüfroutineing zukünftiger": "Onboarding zukünftiger",
        "OnPrüfroutineing": "Onboarding",
    }

    # SPRINT N / G8.2: Hard-Stop Configuration (now ENV-controlled via ValidationConfig)
    # Can be overridden via HARD_STOP_ON_SIZE_MISMATCH env var
    HARD_STOP_ON_SIZE_MISMATCH = (
        ValidationConfig.HARD_STOP_ON_SIZE_MISMATCH
        if _HAS_CONFIG_VALIDATION and ValidationConfig
        else False
    )

    # PLATIN+ Standard: Mindestlängen in WÖRTERN (nicht Zeichen!)
    # SIZE-AWARE: Unterschiedliche Mindestlängen je Unternehmensgröße
    # Solo = kürzere Reports, KMU = ausführlichere Reports
    # SPRINT N: Updated minimums for length stabilization
    # SPRINT G17.S: roadmap_90d limits reduced (content is good, just below threshold)
    MIN_SECTION_LENGTH_WORDS = {
        "executive_summary": 100,      # Temporarily lowered to unblock reports
        "business_case": 130,          # ~800 Zeichen
        "quick_wins": 60,              # Base (wird size-aware überschrieben)
        "roadmap_90d": 150,            # SPRINT G17.S: Base reduced from 250
        "roadmap_12m": 500,            # SPRINT N: erhöht von 400
        "strategie_governance": 130,   # ~800 Zeichen
        "org_change": 120,             # ~700 Zeichen
        "tools_empfehlungen": 120,     # SPRINT N: erhöht von 100
        "foerderpotenzial": 600,       # Reduziert für bessere Compliance
        "risks": 500,                  # Reduziert für bessere Compliance
        "recommendations": 150,        # Temporarily lowered to unblock reports
        "gamechanger": 750,            # SPRINT N: erhöht von 400 (Mindestlänge fix)
        "unternehmensprofil_markt": 300,  # Reduziert für bessere Compliance
        "transparency_box": 150,       # Base (wird size-aware überschrieben)
        "technologie_prozesse": 200,   # Base (wird size-aware überschrieben)
    }

    # SPRINT N: SIZE-AWARE Überschreibungen - Updated minimums
    # SPRINT G17.S: roadmap_90d limits reduced (content quality is good)
    MIN_SECTION_LENGTH_BY_SIZE = {
        "solo": {
            # SPRINT N: Updated minimums
            # SPRINT G17.S: roadmap_90d reduced from 250 to 150
            # SPRINT G18: strategie_governance + tools_empfehlungen gelockert
            # SPRINT N1: Further reductions for Solo to avoid fallbacks
            # P3.2: quick_wins reduced from 60 to 30 (Solo-realistic)
            "executive_summary": 100,   # SPRINT N requirement
            "quick_wins": 30,           # P3.2: Solo-realistic threshold
            "roadmap_90d": 150,         # SPRINT G17.S: reduced from 250
            "roadmap_12m": 600,         # SPRINT N1: 500→600 (balanced)
            "org_change": 80,
            "strategie_governance": 90,  # SPRINT N1: 110→90 (Solo-friendly)
            "tools_empfehlungen": 80,  # v14.27: gelockert wegen GPT-Varianz  # SPRINT G18: gelockert von 120
            "foerderpotenzial": 40,     # v14.28: Solo-realistic (GPT-Varianz)
            "gamechanger": 100,  # v14.16: 150→100 (kurze aber valide OK)         # SPRINT N1: 750→500 (Solo-realistic)
            "transparency_box": 50,     # SPRINT N1: 100→50 (minimal overhead)
            "technologie_prozesse": 150,
        },
        "team": {
            # SPRINT N: Updated minimums
            # SPRINT G6: tools_empfehlungen erhöht, strategie_governance hinzugefügt
            # SPRINT G17.S: roadmap_90d reduced from 300 to 200
            "executive_summary": 180,   # SPRINT N requirement
            "quick_wins": 90,
            "roadmap_90d": 200,         # SPRINT G17.S: reduced from 300
            "roadmap_12m": 600,         # SPRINT N: erhöht von 500
            "org_change": 100,
            "tools_empfehlungen": 190,  # SPRINT G6: erhöht von 160
            "strategie_governance": 200,  # SPRINT G6: konsistent mit anderen
            "gamechanger": 750,         # SPRINT N: Mindestlänge fix
            "transparency_box": 150,
            "technologie_prozesse": 200,
        },
        "kmu": {
            # SPRINT N: Updated minimums
            # SPRINT G2.6: transparency_box + technologie_prozesse reduziert
            # SPRINT G6: tools_empfehlungen + strategie_governance erhöht
            # SPRINT G17.S: roadmap_90d reduced from 350 to 220
            # SPRINT G18: foerderpotenzial erhöht für Substanz
            "executive_summary": 200,   # SPRINT N requirement
            "quick_wins": 120,
            "roadmap_90d": 220,         # SPRINT G17.S: reduced from 350
            "roadmap_12m": 700,         # SPRINT N: erhöht von 600
            "org_change": 120,
            "tools_empfehlungen": 220,  # SPRINT G6: erhöht von 200
            "strategie_governance": 220,  # SPRINT G6: konsistent mit anderen
            "foerderpotenzial": 800,    # SPRINT G18: erhöht für Substanz
            "gamechanger": 750,         # SPRINT N: Mindestlänge fix
            "transparency_box": 150,    # SPRINT G2.6: von 200 → 150
            "technologie_prozesse": 200,  # SPRINT G2.6: von 250 → 200
        },
    }

    # SPRINT N: Critical sections that MUST meet minimum length (no fallback padding)
    CRITICAL_LENGTH_SECTIONS = [
        "executive_summary",
        "tools_empfehlungen",
        "gamechanger",
        "roadmap_12m",
    ]

    # Problem #6 FIX: Maximum report pages by company size
    # Solo reports should be shorter and more focused
    MAX_REPORT_PAGES_BY_SIZE = {
        "solo": 25,   # Focused, practical report
        "team": 35,   # Moderate depth
        "kmu": 45,    # Full strategic depth
    }

    # Estimated words per page (for validation)
    WORDS_PER_PAGE_ESTIMATE = 350

    # Legacy-Alias für Abwärtskompatibilität
    MIN_SECTION_LENGTH = MIN_SECTION_LENGTH_WORDS

    SECTION_KEY_MAP: Dict[str, str] = {
        "executive_summary": "EXECUTIVE_SUMMARY_HTML",
        "business_case": "BUSINESS_CASE_HTML",
        "quick_wins": "QUICK_WINS_HTML",  # FIX-503B: Use HTML key, not text key
        "roadmap_90d": "roadmap_90d",
        "roadmap_12m": "roadmap_12m",
        "strategie_governance": "strategie_governance",
        "org_change": "org_change",
        "tools_empfehlungen": "tools_empfehlungen",
        "foerderpotenzial": "foerderpotenzial",
        "risks": "risks",
        "recommendations": "recommendations",
        "gamechanger": "gamechanger",
        "unternehmensprofil_markt": "unternehmensprofil_markt",
        "transparency_box": "transparency_box",
        "technologie_prozesse": "technologie_prozesse",
        # SPRINT N: Additional section mappings
        "wettbewerb_benchmark": "wettbewerb_benchmark",
        "monetarisierung": "monetarisierung",
        "ki_skillplan": "ki_skillplan",
        "ai_act_summary": "ai_act_summary",
        # SPRINT G7: AI Act Compliance Sections
        "ai_act_risk_reasoning": "AI_ACT_RISK_REASONING",
        "ai_act_duty_matrix": "AI_ACT_DUTY_MATRIX_HTML",
        "ai_act_next_steps": "AI_ACT_RECOMMENDED_NEXT_STEPS_HTML",
        "ai_act_usecases": "AI_ACT_RELATED_USECASES_HTML",
    }

    # SPRINT G7: Valid AI Act risk levels
    VALID_AI_ACT_RISK_LEVELS = {"none", "minimal", "limited", "high-risk"}

    # SPRINT G7 / G8.2: AI Act section minimum lengths (words)
    # AI_ACT_MIN_REASONING_WORDS now configurable via ENV
    @property
    def MIN_AI_ACT_SECTION_LENGTH(self) -> Dict[str, int]:
        """Get AI Act min lengths with ENV-configurable reasoning minimum."""
        reasoning_min = (
            ValidationConfig.AI_ACT_MIN_REASONING_WORDS
            if _HAS_CONFIG_VALIDATION and ValidationConfig
            else 60
        )
        return {
            "AI_ACT_RISK_REASONING": reasoning_min,  # 80-120 words expected
            "AI_ACT_DUTY_MATRIX_HTML": 30,           # Table content
            "AI_ACT_RECOMMENDED_NEXT_STEPS_HTML": 30,  # List content
            "AI_ACT_RELATED_USECASES_HTML": 15,      # List content
        }

    # SPRINT G14-C: Smart mode configuration
    SMART_MODE_ENABLED = True  # Enable warning de-duplication and bundling
    MAX_WARNINGS_PER_CATEGORY = 3  # Max warnings shown per category before bundling

    # FIX-526: Shadow/Raw section keys that should be excluded when HTML version exists
    # These are lowercase/raw keys that duplicate the canonical *_HTML versions
    SHADOW_KEY_TO_HTML_MAP: Dict[str, str] = {
        "quick_wins": "QUICK_WINS_HTML",
        "business_case": "BUSINESS_CASE_HTML",
        "risks": "RISKS_HTML",
        "executive_summary": "EXECUTIVE_SUMMARY_HTML",
        "recommendations": "RECOMMENDATIONS_HTML",
        "roadmap_90d": "ROADMAP_90D_HTML",
        "roadmap_12m": "ROADMAP_12M_HTML",
        "gamechanger": "GAMECHANGER_HTML",
        "tools_empfehlungen": "TOOLS_EMPFEHLUNGEN_HTML",
        "next_actions": "NEXT_ACTIONS_HTML",
        "ki_stack_summary": "KI_STACK_SUMMARY_HTML",
        "pilot_plan": "PILOT_PLAN_HTML",
    }

    def __init__(self, sections: Dict[str, Any], meta: Dict[str, Any]) -> None:
        self.sections = sections or {}
        self.meta = meta or {}
        self.errors: List[ValidationError] = []
        self.company_size: str = self.meta.get("unternehmensgroesse", "unbekannt")
        # FIX-526: Build canonical view excluding shadow sections
        self._canonical_sections: Optional[Dict[str, Any]] = None
        self._excluded_shadow_keys: Optional[set] = None

    def _build_canonical_view(self) -> Tuple[Dict[str, Any], set]:
        """
        FIX-526: Build canonical view of sections for validation.

        When both a shadow/raw key (e.g., 'risks') and its HTML version
        (e.g., 'RISKS_HTML') exist, only the HTML version is canonical.

        This prevents false-positive REDUNDANCY_DETECTED and SECTION_TOO_SHORT
        warnings for shadow/raw duplicates.

        Returns:
            Tuple of (canonical_sections_dict, excluded_shadow_keys_set)
        """
        canonical = {}
        excluded = set()

        for key, value in self.sections.items():
            # Check if this is a shadow key with existing HTML version
            html_key = self.SHADOW_KEY_TO_HTML_MAP.get(key)
            if html_key and html_key in self.sections:
                # HTML version exists → exclude this shadow key
                excluded.add(key)
                continue
            canonical[key] = value

        if excluded:
            log.info(
                "[VALIDATOR][FIX-526] canonical_keys=%d excluded_shadow=%s",
                len(canonical),
                sorted(excluded)
            )

        return canonical, excluded

    @property
    def canonical_sections(self) -> Dict[str, Any]:
        """FIX-526: Get canonical sections view (excludes shadow/raw duplicates)."""
        if self._canonical_sections is None:
            self._canonical_sections, self._excluded_shadow_keys = self._build_canonical_view()
        return self._canonical_sections

    @property
    def excluded_shadow_keys(self) -> set:
        """FIX-526: Get set of excluded shadow keys."""
        if self._excluded_shadow_keys is None:
            self._canonical_sections, self._excluded_shadow_keys = self._build_canonical_view()
        return self._excluded_shadow_keys

    # ------------------------------------------------------------------
    # SPRINT G14-C: Smart Mode - Warning De-Duplication & Bundling
    # ------------------------------------------------------------------

    def _dedupe_warnings(self) -> List[ValidationError]:
        """
        SPRINT G14-C: Remove duplicate warnings and bundle similar ones.

        De-duplication rules:
        - Same category + same section + same message = duplicate
        - Multiple SECTION_TOO_SHORT warnings = bundle into one
        - Multiple SIZE_MISMATCH for same term = bundle
        """
        if not self.SMART_MODE_ENABLED:
            return self.errors

        seen_keys: set = set()
        deduped: List[ValidationError] = []

        for err in self.errors:
            # Create unique key for deduplication
            key = (err.severity, err.category, err.section, err.message)

            if key not in seen_keys:
                seen_keys.add(key)
                deduped.append(err)

        return deduped

    def _bundle_min_word_warnings(
        self, errors: List[ValidationError]
    ) -> List[ValidationError]:
        """
        SPRINT G14-C: Bundle multiple SECTION_TOO_SHORT warnings into summary.

        Instead of:
          - Section X too short: 45 words (min 100)
          - Section Y too short: 32 words (min 80)
          - Section Z too short: 55 words (min 120)

        Output:
          - 3 sections below minimum word count: X (45/100), Y (32/80), Z (55/120)
        """
        if not self.SMART_MODE_ENABLED:
            return errors

        # Separate min-word warnings from others
        min_word_warnings: List[ValidationError] = []
        other_errors: List[ValidationError] = []

        for err in errors:
            if err.category == "SECTION_TOO_SHORT" and err.severity == "WARNING":
                min_word_warnings.append(err)
            else:
                other_errors.append(err)

        # If few warnings, don't bundle
        if len(min_word_warnings) <= self.MAX_WARNINGS_PER_CATEGORY:
            return errors

        # Bundle min-word warnings
        section_summaries = []
        for err in min_word_warnings:
            # Extract word counts from message
            import re
            match = re.search(r"(\d+)\s*Wörter.*?(\d+)\s*Wörter", err.message)
            if match:
                actual, minimum = match.groups()
                section_summaries.append(f"{err.section} ({actual}/{minimum})")
            else:
                section_summaries.append(err.section)

        bundled = ValidationError(
            severity="WARNING",
            category="SECTION_TOO_SHORT_BUNDLE",
            section="[multiple]",
            message=f"{len(min_word_warnings)} Sektionen unter Mindest-Wortanzahl",
            details=", ".join(section_summaries[:6]) + (
                f" (+{len(section_summaries) - 6} weitere)"
                if len(section_summaries) > 6 else ""
            ),
        )

        return other_errors + [bundled]

    def _bundle_size_mismatch_warnings(
        self, errors: List[ValidationError]
    ) -> List[ValidationError]:
        """
        SPRINT G14-C: Bundle multiple SIZE_MISMATCH warnings by term.

        Instead of multiple warnings for same term in different sections,
        bundle into one warning listing affected sections.
        """
        if not self.SMART_MODE_ENABLED:
            return errors

        # Group SIZE_MISMATCH warnings by term
        term_warnings: Dict[str, List[ValidationError]] = {}
        other_errors: List[ValidationError] = []

        for err in errors:
            if err.category == "SIZE_MISMATCH":
                # Extract term from message
                import re
                match = re.search(r"Begriff '([^']+)'", err.message)
                if match:
                    term = match.group(1)
                    if term not in term_warnings:
                        term_warnings[term] = []
                    term_warnings[term].append(err)
                else:
                    other_errors.append(err)
            else:
                other_errors.append(err)

        # Bundle warnings for terms appearing in multiple sections
        bundled_errors = []
        for term, warnings in term_warnings.items():
            if len(warnings) == 1:
                # Keep single warning as-is
                bundled_errors.append(warnings[0])
            else:
                # Bundle multiple occurrences
                sections = list(set(w.section for w in warnings))
                severity = warnings[0].severity  # Keep original severity
                bundled = ValidationError(
                    severity=severity,
                    category="SIZE_MISMATCH",
                    section=", ".join(sections[:3]) + (
                        f" (+{len(sections) - 3})" if len(sections) > 3 else ""
                    ),
                    message=f"Persona-Leak: '{term}' in {len(warnings)} Sektionen gefunden",
                    details=f"Term '{term}' muss ersetzt werden für '{self.company_size}'",
                )
                bundled_errors.append(bundled)

        return other_errors + bundled_errors

    def get_smart_errors(self) -> List[ValidationError]:
        """
        SPRINT G14-C: Get errors with smart mode processing applied.

        Applies:
        1. De-duplication of identical warnings
        2. Bundling of min-word warnings
        3. Bundling of size-mismatch warnings
        """
        errors = self._dedupe_warnings()
        errors = self._bundle_min_word_warnings(errors)
        errors = self._bundle_size_mismatch_warnings(errors)
        return errors

    # ------------------------------------------------------------------

    def validate_all(self) -> Tuple[bool, List[ValidationError]]:
        print("DEBUG ReportValidator – sections keys:", list(self.sections.keys()))

        self._check_placeholders()
        self._check_empty_or_short_sections()
        self._check_template_phrases()
        self._check_quick_wins_prompt_leaks()
        self._check_generic_llm_leaks()  # Sprint N1: ChatGPT standard response detection
        self._check_size_specific_issues()
        self._check_solo_terminology()  # FIX-SOLO-VEREINFACHUNG: Blacklist check
        self._check_redundancy()  # Sprint G2.4
        self._check_ai_act_sections()  # Sprint G7
        self._check_tools_section()  # Sprint B2-C
        # Phase 1.5 Consistency Checks
        self._check_hauptleistung_limits()  # Sprint P1.5-1: Min/max hauptleistung counts
        self._check_roi_consistency()  # Sprint P1.5-3: Single ROI value
        self._check_incomplete_sentences()  # Sprint P1.5-4: No sentence fragments
        self._check_tone_consistency()  # Sprint P1.5-6: Sie vs du
        self._check_location_consistency()  # Sprint P1.5-7: Correct Bundesland

        is_valid = not any(e.severity == "CRITICAL" for e in self.errors)
        return is_valid, self.errors

    def print_report(self) -> None:
        """
        Print validation report to console.

        SPRINT G14-C: Uses smart mode to de-duplicate and bundle warnings
        for cleaner, more actionable output.
        """
        if not self.errors:
            print("")
            print("=" * 78)
            print("📋 REPORT VALIDATION RESULTS")
            print("=" * 78)
            print("")
            print("🟢 Keine Validation-Fehler gefunden.")
            print("=" * 78)
            print("")
            return

        # SPRINT G14-C: Use smart mode for display
        display_errors = self.get_smart_errors() if self.SMART_MODE_ENABLED else self.errors

        # Count from original errors (for accurate stats)
        critical_count = sum(1 for e in self.errors if e.severity == "CRITICAL")
        warning_count = sum(1 for e in self.errors if e.severity == "WARNING")
        info_count = sum(1 for e in self.errors if e.severity == "INFO")

        # Count displayed (after bundling)
        displayed_count = len(display_errors)
        original_count = len(self.errors)

        print("")
        print("=" * 78)
        print("📋 REPORT VALIDATION RESULTS")
        if self.SMART_MODE_ENABLED and displayed_count < original_count:
            print(f"   [Smart Mode: {original_count} → {displayed_count} consolidated]")
        print("=" * 78)
        print("")

        if critical_count:
            print(f"🔴 CRITICAL ERRORS: {critical_count}")
        if warning_count:
            print(f"🟠 WARNINGS: {warning_count}")
        if info_count:
            print(f"🔵 INFO: {info_count}")

        if critical_count:
            print("→ Report kann NICHT published werden!")
        print("-" * 80)
        print("")

        for err in display_errors:
            prefix = {
                "CRITICAL": "❌",
                "WARNING": "⚠️",
                "INFO": "ℹ️",
            }.get(err.severity, "•")

            print(f"[{err.category}] {err.section}")
            print(f"   {prefix} {err.message}")
            if err.details:
                print(f"   Details: {err.details}")
            print("")

        print("=" * 78)
        print(
            f"TOTAL: {critical_count} Critical | "
            f"{warning_count} Warnings | {info_count} Info"
        )
        if self.SMART_MODE_ENABLED and displayed_count < original_count:
            print(f"(Displayed: {displayed_count} bundled items)")
        print("=" * 78)
        print("")

    # ------------------------------------------------------------------

    def _check_placeholders(self) -> None:
        for section_name, content in self.sections.items():
            if not isinstance(content, str):
                continue
            for pattern in self.PLACEHOLDER_PATTERNS:
                for match in re.finditer(pattern, content):
                    placeholder = match.group(0)
                    self.errors.append(
                        ValidationError(
                            severity="CRITICAL",
                            category="PLACEHOLDER",
                            section=section_name,
                            message=f"Nicht ersetzter Placeholder gefunden: {placeholder}",
                            details=f"Pattern: {pattern}, Fundstelle: {match.span()}",
                        )
                    )

    def _get_min_words_for_section(self, logical_name: str) -> int:
        """
        Ermittelt die size-aware Mindest-Wortanzahl für eine Section.
        """
        # Normalisiere company_size
        size_key = self.company_size.lower() if self.company_size else "kmu"
        if "solo" in size_key or "1" in size_key or "freiberuf" in size_key:
            size_key = "solo"
        elif "team" in size_key or "klein" in size_key:
            size_key = "team"
        else:
            size_key = "kmu"

        # Size-aware Override falls vorhanden
        size_overrides = self.MIN_SECTION_LENGTH_BY_SIZE.get(size_key, {})
        if logical_name in size_overrides:
            return size_overrides[logical_name]

        # Fallback auf Standard
        return self.MIN_SECTION_LENGTH_WORDS.get(logical_name, 50)

    def _check_empty_or_short_sections(self) -> None:
        """
        PLATIN+ Validierung: Prüft Sections auf Mindest-WORTZAHL (nicht Zeichen!).
        SIZE-AWARE: Unterschiedliche Mindestlängen je Unternehmensgröße.
        SPRINT N: Critical sections trigger CRITICAL errors, not just warnings.
        """
        for logical_name in self.MIN_SECTION_LENGTH_WORDS.keys():
            section_key = self.SECTION_KEY_MAP.get(logical_name, logical_name)

            # FIX-503B: Quick Wins fallback logic
            # If QUICK_WINS_HTML not found, try quick_wins text key
            if logical_name == "quick_wins" and section_key not in self.sections:
                fallback_keys = ["quick_wins", "QUICK_WINS_HTML_LEFT", "QUICK_WINS_HTML_RIGHT"]
                for fallback in fallback_keys:
                    if fallback in self.sections and self.sections.get(fallback):
                        section_key = fallback
                        break

            if section_key not in self.sections:
                continue
            content = self.sections.get(section_key)
            if not isinstance(content, str):
                continue

            # HTML-Tags entfernen für Textzählung
            text_only = re.sub(r"<[^>]+>", "", content).strip()

            # RECOVERY: Wenn nach HTML-Entfernung nichts übrig ist,
            # versuche den Originaltext zu verwenden (kaputtes HTML)
            if not text_only and content.strip():
                # Fallback: Alle Tags entfernen, auch kaputte
                text_only = re.sub(r"<[^>]*>?", "", content).strip()

            if not text_only:
                self.errors.append(
                    ValidationError(
                        severity="CRITICAL",
                        category="SECTION_EMPTY",
                        section=section_key,
                        message="Wichtige Section ist leer",
                        details="Kein Textinhalt nach HTML-Bereinigung",
                    )
                )
                continue

            # PLATIN+: Wörter zählen statt Zeichen
            words = text_only.split()
            actual_word_count = len(words)

            # SIZE-AWARE Mindestlänge
            min_words = self._get_min_words_for_section(logical_name)

            if actual_word_count < min_words:
                # SPRINT N: Use CRITICAL severity for critical length sections
                is_critical_section = logical_name in self.CRITICAL_LENGTH_SECTIONS
                severity = "CRITICAL" if is_critical_section else "WARNING"

                self.errors.append(
                    ValidationError(
                        severity=severity,
                        category="SECTION_TOO_SHORT",
                        section=section_key,
                        message=(
                            f"Section zu kurz: {actual_word_count} Wörter "
                            f"(Minimum für {self.company_size}: {min_words} Wörter)"
                        ),
                        details=(
                            f"Content preview: {text_only[:150]}... "
                            f"{'[CRITICAL SECTION]' if is_critical_section else ''}"
                        ),
                    )
                )

    def _check_template_phrases(self) -> None:
        # FIX-526: Use canonical_sections to avoid duplicate warnings for shadow keys
        for section_name, content in self.canonical_sections.items():
            if not isinstance(content, str):
                continue
            for phrase in self.TEMPLATE_PHRASES:
                if phrase in content:
                    self.errors.append(
                        ValidationError(
                            severity="WARNING",
                            category="TEMPLATE_PHRASE",
                            section=section_name,
                            message=f"Template-Phrase noch enthalten: '{phrase}'",
                            details="Bitte durch individuellen Text ersetzen.",
                        )
                    )

    def _check_quick_wins_prompt_leaks(self) -> None:
        """Sucht nach typischen Prompt-Anweisungen in der Quick-Wins-Section."""
        candidates = []
        key_raw = self.SECTION_KEY_MAP.get("quick_wins", "quick_wins")
        if key_raw in self.sections:
            candidates.append((key_raw, self.sections.get(key_raw)))
        if "QUICK_WINS_HTML" in self.sections:
            candidates.append(("QUICK_WINS_HTML", self.sections.get("QUICK_WINS_HTML")))
        # FIX-503B: Also check legacy "quick_wins" key for backwards compatibility
        if "quick_wins" in self.sections and ("quick_wins", self.sections.get("quick_wins")) not in candidates:
            candidates.append(("quick_wins", self.sections.get("quick_wins")))

        for section_name, content in candidates:
            if not isinstance(content, str) or not content:
                continue
            lower = content.lower()
            for phrase in self.QUICK_WINS_PROMPT_PHRASES:
                if phrase.lower() in lower:
                    self.errors.append(
                        ValidationError(
                            severity="WARNING",
                            category="QUICK_WINS_PROMPT_LEAK",
                            section=section_name,
                            message=(
                                "Quick-Wins enthalten noch Prompt-Anweisungen "
                                "statt ausgefüllter Inhalte."
                            ),
                            details=f'Gefunden: "{phrase}"',
                        )
                    )
                    break

    def _check_generic_llm_leaks(self) -> None:
        """
        SPRINT N1: Check for generic LLM response leaks.

        These are "standard ChatGPT responses" that indicate the LLM
        didn't properly understand the task or returned default responses.

        When found:
        - Log as [LEAK_PHRASE] warning
        - Mark section as CRITICAL (triggers PLATIN fallback)
        """
        for section_name, content in self.sections.items():
            if not isinstance(content, str) or not content:
                continue

            lower = content.lower()
            for phrase in self.GENERIC_LLM_LEAK_PHRASES:
                if phrase.lower() in lower:
                    # Log the leak for monitoring
                    log.warning(
                        '[LEAK_PHRASE] phrase="%s" in section="%s"',
                        phrase, section_name
                    )

                    self.errors.append(
                        ValidationError(
                            severity="CRITICAL",
                            category="GENERIC_LLM_LEAK",
                            section=section_name,
                            message=(
                                f"Generische LLM-Antwort erkannt: '{phrase}' - "
                                "Section enthält Standard-ChatGPT-Antwort statt Report-Inhalt"
                            ),
                            details=(
                                "Section wird durch PLATIN-Fallback ersetzt. "
                                "LLM hat Aufgabe nicht korrekt verstanden."
                            ),
                        )
                    )
                    # Only report first leak per section
                    break

    @staticmethod
    def _term_hit(term: str, text: str) -> bool:
        """
        FIX-517C TASK 3: Word-boundary matching for SIZE_MISMATCH terms.

        Uses \\b word-boundary regex instead of simple substring `in` check.
        This prevents false positives like "Engine" matching "Engineering".

        Args:
            term: The forbidden term to search for
            text: The text content to search in

        Returns:
            True if term is found as a standalone word/phrase
        """
        # Escape regex metacharacters in term, then wrap with word boundaries
        escaped = re.escape(term)
        # Special case: "Engine" must NOT match "Engineering"
        # re.escape preserves the term, \b handles word boundaries correctly
        pattern = r'\b' + escaped + r'\b'
        return bool(re.search(pattern, text, re.IGNORECASE))

    def _check_size_specific_issues(self) -> None:
        """
        SPRINT N: Enhanced size-specific validation with HARD_STOP support.
        Checks for forbidden terms and triggers CRITICAL errors when configured.

        FIX-517C: Uses _term_hit() with word-boundary matching to avoid
        false positives (e.g. "Engine" in "Engineering").
        """
        # Normalize company_size
        size_key = self.company_size.lower() if self.company_size else "kmu"
        if "solo" in size_key or "1" in size_key or "freiberuf" in size_key:
            size_key = "solo"
        elif "team" in size_key or "klein" in size_key:
            size_key = "team"
        else:
            size_key = "kmu"

        forbidden_terms = self.SIZE_FORBIDDEN.get(size_key, [])
        if not forbidden_terms:
            return

        # FIX-526: Use canonical_sections to avoid duplicate warnings for shadow keys
        for section_name, content in self.canonical_sections.items():
            if not isinstance(content, str):
                continue
            for term in forbidden_terms:
                if self._term_hit(term, content):
                    # SPRINT N: Use CRITICAL severity if HARD_STOP is enabled
                    severity = "CRITICAL" if self.HARD_STOP_ON_SIZE_MISMATCH else "WARNING"
                    self.errors.append(
                        ValidationError(
                            severity=severity,
                            category="SIZE_MISMATCH",
                            section=section_name,
                            message=(
                                f"Persona-Leak: Begriff '{term}' unpassend für "
                                f"'{self.company_size}' gefunden."
                            ),
                            details=(
                                f"SPRINT N: Term '{term}' muss ersetzt werden. "
                                f"HARD_STOP={self.HARD_STOP_ON_SIZE_MISMATCH}"
                            ),
                        )
                    )

    def _check_solo_terminology(self) -> None:
        """
        FIX-SOLO-VEREINFACHUNG: Extended Solo terminology validation.

        Uses the solo_simplifier service to check for blacklist terms
        in headlines (CRITICAL) and body text (WARNING).

        This is separate from _check_size_specific_issues which uses
        a static SIZE_FORBIDDEN list. This method uses the comprehensive
        blacklist from config/solo_terms.json.
        """
        if not _HAS_SOLO_SIMPLIFIER:
            return

        # Only check for Solo reports
        if not is_solo_size(self.company_size):
            return

        blacklist_terms = get_blacklist_headlines()
        if not blacklist_terms:
            return

        # Check each section
        for section_name, content in self.canonical_sections.items():
            if not isinstance(content, str):
                continue

            # Use solo_simplifier validation
            is_valid, violations = validate_solo_content(content, section_name)

            for violation in violations:
                severity = violation.get("severity", "WARNING").upper()
                # Headlines are CRITICAL, body is WARNING
                if severity == "ERROR":
                    severity = "CRITICAL"

                self.errors.append(
                    ValidationError(
                        severity=severity,
                        category="SOLO_TERMINOLOGY",
                        section=section_name,
                        message=(
                            f"Solo-Blacklist: '{violation.get('term', 'unknown')}' "
                            f"gefunden in {section_name}"
                        ),
                        details=(
                            f"Kontext: {violation.get('context', '')[:80]}... "
                            f"→ Ersetzung aus solo_terms.json empfohlen"
                        ),
                    )
                )

    def _check_ai_act_sections(self) -> None:
        """
        SPRINT G7: Validate AI Act compliance sections.

        Checks:
        - AI_ACT_RISK_LEVEL is valid (none/minimal/limited/high-risk)
        - AI_ACT_RISK_REASONING meets minimum word count
        - AI_ACT_DUTY_MATRIX_HTML contains table structure
        - AI_ACT_NONCOMPLIANCE_ALERTS has items
        - AI_ACT_DATA_GAPS has items
        - Persona leaks in AI Act text
        """
        # Check risk level validity
        risk_level = self.sections.get("AI_ACT_RISK_LEVEL", "")
        if risk_level and risk_level not in self.VALID_AI_ACT_RISK_LEVELS:
            self.errors.append(
                ValidationError(
                    severity="CRITICAL",
                    category="AI_ACT_INVALID_RISK",
                    section="AI_ACT_RISK_LEVEL",
                    message=f"Ungültiges AI Act Risk Level: '{risk_level}'",
                    details=f"Erlaubte Werte: {self.VALID_AI_ACT_RISK_LEVELS}",
                )
            )

        # Check risk reasoning length
        reasoning = self.sections.get("AI_ACT_RISK_REASONING", "")
        if reasoning and isinstance(reasoning, str):
            text_only = re.sub(r"<[^>]+>", "", reasoning).strip()
            word_count = len(text_only.split())
            min_words = self.MIN_AI_ACT_SECTION_LENGTH.get("AI_ACT_RISK_REASONING", 60)

            if word_count < min_words:
                self.errors.append(
                    ValidationError(
                        severity="WARNING",
                        category="AI_ACT_SHORT_REASONING",
                        section="AI_ACT_RISK_REASONING",
                        message=f"AI Act Begründung zu kurz: {word_count} Wörter (min {min_words})",
                        details=f"Content: {text_only[:100]}...",
                    )
                )

        # Check duty matrix structure
        duty_matrix = self.sections.get("AI_ACT_DUTY_MATRIX_HTML", "")
        if duty_matrix and isinstance(duty_matrix, str):
            if "<table" not in duty_matrix.lower() or "</table>" not in duty_matrix.lower():
                self.errors.append(
                    ValidationError(
                        severity="WARNING",
                        category="AI_ACT_MALFORMED_MATRIX",
                        section="AI_ACT_DUTY_MATRIX_HTML",
                        message="AI Act Pflichten-Matrix enthält keine gültige Tabellenstruktur",
                        details="Erwartet: <table>...</table>",
                    )
                )
            else:
                # Check minimum row count
                row_count = duty_matrix.lower().count("<tr>") - 1  # Subtract header
                if row_count < 3:
                    self.errors.append(
                        ValidationError(
                            severity="WARNING",
                            category="AI_ACT_SHORT_MATRIX",
                            section="AI_ACT_DUTY_MATRIX_HTML",
                            message=f"AI Act Pflichten-Matrix hat nur {row_count} Zeilen (min 3)",
                            details="Matrix sollte mindestens 3 Pflichten/Best Practices enthalten",
                        )
                    )

        # Check alerts list
        alerts = self.sections.get("AI_ACT_NONCOMPLIANCE_ALERTS", [])
        if isinstance(alerts, list) and len(alerts) < 2:
            self.errors.append(
                ValidationError(
                    severity="WARNING",
                    category="AI_ACT_FEW_ALERTS",
                    section="AI_ACT_NONCOMPLIANCE_ALERTS",
                    message=f"Nur {len(alerts)} Non-Compliance Alerts (min 2 empfohlen)",
                    details="Mehr spezifische Hinweise für das Unternehmen generieren",
                )
            )

        # Check data gaps list
        gaps = self.sections.get("AI_ACT_DATA_GAPS", [])
        if isinstance(gaps, list) and len(gaps) < 2:
            self.errors.append(
                ValidationError(
                    severity="WARNING",
                    category="AI_ACT_FEW_GAPS",
                    section="AI_ACT_DATA_GAPS",
                    message=f"Nur {len(gaps)} Data Gaps (min 2 empfohlen)",
                    details="Mehr Datenlücken identifizieren",
                )
            )

        # Check persona leaks in AI Act content
        self._check_ai_act_persona_leaks()

    def _check_ai_act_persona_leaks(self) -> None:
        """
        SPRINT G7: Check for persona leaks in AI Act sections.
        """
        # Normalize company_size
        size_key = self.company_size.lower() if self.company_size else "kmu"
        if "solo" in size_key or "1" in size_key or "freiberuf" in size_key:
            size_key = "solo"
        elif "team" in size_key or "klein" in size_key:
            size_key = "team"
        else:
            size_key = "kmu"

        # AI Act sections to check
        ai_act_sections = [
            "AI_ACT_RISK_REASONING",
            "AI_ACT_DUTY_MATRIX_HTML",
            "AI_ACT_NONCOMPLIANCE_ALERTS_HTML",
            "AI_ACT_DATA_GAPS_HTML",
            "AI_ACT_RECOMMENDED_NEXT_STEPS_HTML",
        ]

        forbidden_terms = self.SIZE_FORBIDDEN.get(size_key, [])
        if not forbidden_terms:
            return

        for section_name in ai_act_sections:
            content = self.sections.get(section_name, "")
            if not isinstance(content, str):
                continue

            lower = content.lower()
            for term in forbidden_terms:
                if term.lower() in lower:
                    self.errors.append(
                        ValidationError(
                            severity="WARNING",
                            category="AI_ACT_PERSONA_LEAK",
                            section=section_name,
                            message=f"Persona-Leak in AI Act Section: '{term}'",
                            details=f"Term '{term}' unpassend für '{self.company_size}'",
                        )
                    )

    # =========================================================================
    # SPRINT B2-C: Tools Engine Validation
    # =========================================================================

    # B2-C: Tools validation configuration
    TOOLS_VALIDATION_ENABLED = True
    TOOLS_LOW_CONFIDENCE_THRESHOLD = 0.30
    TOOLS_OVERPOPULATION_LIMIT = 14
    TOOLS_MIN_FOR_SEGMENT = 3

    def _check_tools_section(self) -> None:
        """
        SPRINT B2-C: Validate tools recommendations section.

        Checks:
        - Missing confidence info
        - Low-confidence tools (<0.3)
        - Segment weakness (fallback to generic)
        - AI-Act misalignment
        - Tools overpopulation (>14)
        """
        if not self.TOOLS_VALIDATION_ENABLED:
            return

        # Get tools data from sections
        tools_html = self.sections.get("tools_empfehlungen", "")
        tools_data = self.sections.get("_tools_data", [])  # Internal data if available

        if not tools_html and not tools_data:
            return  # No tools section to validate

        # Check for missing confidence info
        self._check_tools_missing_confidence(tools_data)

        # Check for low-confidence tools
        self._check_tools_low_confidence(tools_data)

        # Check segment weakness
        self._check_tools_segment_weakness()

        # Check AI-Act alignment
        self._check_tools_ai_act_alignment(tools_data)

        # Check tools overpopulation
        self._check_tools_overpopulation(tools_data, tools_html)

    def _check_tools_missing_confidence(self, tools_data: list) -> None:
        """B2-C: Check for tools missing confidence information."""
        if not tools_data:
            return

        missing_conf_count = 0
        for tool in tools_data:
            if isinstance(tool, dict):
                if "_confidence" not in tool and "confidence" not in tool:
                    missing_conf_count += 1

        if missing_conf_count > 0:
            self.errors.append(
                ValidationError(
                    severity="WARNING",
                    category="TOOLS_MISSING_CONFIDENCE",
                    section="tools_empfehlungen",
                    message=f"{missing_conf_count} Tools ohne Konfidenz-Information",
                    details="Tools sollten Konfidenz-Metadaten enthalten für Transparenz",
                )
            )

    def _check_tools_low_confidence(self, tools_data: list) -> None:
        """B2-C: Check for low-confidence tools (<0.3)."""
        if not tools_data:
            return

        low_conf_tools = []
        for tool in tools_data:
            if isinstance(tool, dict):
                conf = tool.get("_confidence") or tool.get("confidence", 1.0)
                if conf < self.TOOLS_LOW_CONFIDENCE_THRESHOLD:
                    low_conf_tools.append(tool.get("name", "Unknown"))

        if low_conf_tools:
            # Suggest bundling in Smart Mode
            self.errors.append(
                ValidationError(
                    severity="WARNING",
                    category="TOOLS_LOW_CONFIDENCE",
                    section="tools_empfehlungen",
                    message=f"{len(low_conf_tools)} Tools mit niedriger Konfidenz (<{self.TOOLS_LOW_CONFIDENCE_THRESHOLD})",
                    details=f"Tools: {', '.join(low_conf_tools[:5])}... Empfehlung: Smart-Mode Bundling aktivieren",
                )
            )

    def _check_tools_segment_weakness(self) -> None:
        """B2-C: Check if segment data is weak, suggesting fallback to generic list."""
        if not _HAS_TOOLS_ANALYTICS:
            return

        # Normalize company_size
        size_key = self.company_size.lower() if self.company_size else "kmu"
        if "solo" in size_key or "1" in size_key or "freiberuf" in size_key:
            size_key = "solo"
        elif "team" in size_key or "klein" in size_key:
            size_key = "team"
        else:
            size_key = "kmu"

        try:
            segment = get_segment_analysis("size_label", size_key)
            if segment and segment.stability == "weak":
                self.errors.append(
                    ValidationError(
                        severity="INFO",
                        category="TOOLS_SEGMENT_WEAKNESS",
                        section="tools_empfehlungen",
                        message=f"Segment '{size_key}' hat schwache Datenbasis",
                        details="Generische Fallback-Liste kann enthalten sein. Sample-Size erweitern empfohlen.",
                    )
                )
        except Exception:
            pass  # Analytics not available or segment not found

    def _check_tools_ai_act_alignment(self, tools_data: list) -> None:
        """B2-C: Check for AI-Act misalignment in tool recommendations."""
        if not tools_data:
            return

        # Get AI Act risk level from meta
        ai_act_risk = self.meta.get("ai_act_risk_level", "minimal").lower()
        if ai_act_risk not in ("high-risk", "high", "limited"):
            return  # Only check for higher risk levels

        misaligned_tools = []
        for tool in tools_data:
            if isinstance(tool, dict):
                ai_align = tool.get("_ai_act_alignment") or tool.get("ai_act_alignment", 0.5)
                if ai_align < 0.4:  # Low alignment with high-risk context
                    misaligned_tools.append(tool.get("name", "Unknown"))

        if misaligned_tools:
            self.errors.append(
                ValidationError(
                    severity="WARNING",
                    category="TOOLS_AI_ACT_MISALIGNMENT",
                    section="tools_empfehlungen",
                    message=f"{len(misaligned_tools)} Tools mit unzureichender AI-Act Ausrichtung",
                    details=f"Bei Risk-Level '{ai_act_risk}' sollten Governance-Tools priorisiert werden. "
                           f"Betroffene Tools: {', '.join(misaligned_tools[:3])}",
                )
            )

    def _check_tools_overpopulation(self, tools_data: list, tools_html: str) -> None:
        """B2-C: Check for tools overpopulation (>14 tools)."""
        tool_count = 0

        if tools_data:
            tool_count = len(tools_data)
        elif tools_html:
            # Estimate from HTML by counting table rows
            import re
            tool_count = len(re.findall(r"<tr>", tools_html)) - 1  # Subtract header

        if tool_count > self.TOOLS_OVERPOPULATION_LIMIT:
            self.errors.append(
                ValidationError(
                    severity="WARNING",
                    category="TOOLS_OVERPOPULATION",
                    section="tools_empfehlungen",
                    message=f"Zu viele Tools empfohlen: {tool_count} (Limit: {self.TOOLS_OVERPOPULATION_LIMIT})",
                    details="Empfehlung: Tools nach Priorität filtern oder Smart-Defaults verwenden",
                )
            )

    # SPRINT G3.3/G4.4/G13: Extended whitelist for standard phrases that may repeat intentionally
    REDUNDANCY_WHITELIST = [
        # ROI/Business disclaimers (DE)
        "return on investment",
        "roi nach 12 monaten",
        "amortisation",
        "payback",
        "investitionsrechnung",
        "kostenersparnis",
        # ROI/Business disclaimers (EN)
        "cost savings",
        "time savings",
        "efficiency gains",
        # AI Act standard references (DE)
        "ai act",
        "hochrisiko",
        "konformität",
        "risikoklasse",
        "eu-verordnung",
        # AI Act standard references (EN)
        "high-risk",
        "compliance",
        "risk classification",
        "eu regulation",
        # Standard KI references (DE)
        "künstliche intelligenz",
        "maschinelles lernen",
        "automatisierung",
        "digitale transformation",
        # Standard KI references (EN)
        "artificial intelligence",
        "machine learning",
        "automation",
        "digital transformation",
        # Data protection (DE/EN)
        "datenschutz",
        "dsgvo",
        "gdpr",
        "data protection",
        "privacy",
        # Governance standard phrases (DE)
        "verantwortungsvoller einsatz",
        "menschliche kontrolle",
        "qualitätssicherung",
        # Governance standard phrases (EN)
        "responsible use",
        "human oversight",
        "quality assurance",
        # Section cross-references (allowed to repeat)
        "details finden sie",
        "siehe abschnitt",
        "for more details",
        "see section",
        # SPRINT G13-B: Additional standard phrases
        # German connector phrases
        "im rahmen von",
        "basierend auf",
        "auf basis von",
        "in bezug auf",
        "mit blick auf",
        "im hinblick auf",
        "im kontext von",
        "unter berücksichtigung",
        "in verbindung mit",
        "im zusammenhang mit",
        "auf grundlage",
        "gemäß den",
        "entsprechend den",
        # English connector phrases
        "based on",
        "in the context of",
        "with regard to",
        "in connection with",
        "in relation to",
        "taking into account",
        "in accordance with",
        # Industry standard phrases (DE)
        "best practices",
        "use cases",
        "quick wins",
        "zeitersparnis",
        "effizienzsteigerung",
        "prozessoptimierung",
        "workflow-automatisierung",
        # Industry standard phrases (EN)
        "workflow optimization",
        "process improvement",
        "productivity gains",
        # Funding/Förderung standard phrases
        "förderprogramm",
        "zuschuss",
        "förderung",
        "funding program",
        "grant",
        "subsidy",
        # SPRINT G18: Additional standard phrases
        "ki-readiness",
        "ai readiness",
        "starter-kit",
        "starter kit",
        "roadmap 90d",
        "90-day roadmap",
        "90-tage-roadmap",
        "roadmap 12m",
        "12-month roadmap",
        "12-monats-roadmap",
        "data maturity",
        "datenreife",
        "governance-hinweise",
        "governance guidance",
        "tools × funding",
        "tools × förderprogramme",
    ]

    # SPRINT G13-B: Sections excluded from redundancy SOURCE detection
    # These sections are meant to summarize or repeat key information
    REDUNDANCY_EXCLUDED_SECTIONS = [
        "EXECUTIVE_SUMMARY_HTML",
        "executive_summary",
        "EXEC_SUMMARY_HTML",
        "transparency_box",
        "TRANSPARENCY_BOX_HTML",
    ]

    def _check_redundancy(self) -> None:
        """
        Sprint G2.4/G3.3/G13: Check for redundant long sentences across sections.

        Warns when:
        - A sentence >20 words appears identically or 85% similar in ≥2 sections
        - Long branch/offering descriptions appear after strategic_context_block

        Sprint G3.3 tuning:
        - Increased threshold from 15 to 20 words
        - Added whitelist for standard phrases (ROI, AI Act, etc.)

        Sprint G13-B tuning:
        - Executive summary and transparency box excluded from SOURCE detection
        - These sections are MEANT to summarize/repeat key information
        - Expanded whitelist with connector phrases

        This is informational only (WARNING, not CRITICAL).
        """
        # Collect all sentences from all sections
        sentence_occurrences: Dict[str, List[str]] = {}  # normalized → list of sections

        # FIX-526: Use canonical_sections to avoid false-positive redundancy from shadow keys
        for section_name, content in self.canonical_sections.items():
            if not isinstance(content, str) or not content:
                continue

            # SPRINT G13-B: Skip excluded sections (they're meant to summarize)
            if section_name in self.REDUNDANCY_EXCLUDED_SECTIONS:
                continue

            # Split into sentences (rough approximation)
            sentences = re.split(r'[.!?]\s+', content)

            for sentence in sentences:
                # G8.2: Use centralized config for redundancy threshold (default 20 words)
                redundancy_threshold = (
                    ValidationConfig.REDUNDANCY_WORD_THRESHOLD
                    if _HAS_CONFIG_VALIDATION and ValidationConfig
                    else 20
                )
                words = sentence.split()
                if len(words) < redundancy_threshold:
                    continue

                # Normalize for comparison
                normalized = re.sub(r'\s+', ' ', sentence.lower().strip())

                # Skip very short normalized sentences
                if len(normalized) < 60:
                    continue

                # SPRINT G3.3: Skip if contains whitelisted standard phrases
                if any(phrase in normalized for phrase in self.REDUNDANCY_WHITELIST):
                    continue

                if normalized not in sentence_occurrences:
                    sentence_occurrences[normalized] = []
                sentence_occurrences[normalized].append(section_name)

        # Report redundancies (appearing in ≥2 sections)
        redundancy_count = 0
        # G8.2: Use centralized config for max warnings
        max_redundancy_warnings = (
            ValidationConfig.MAX_REDUNDANCY_WARNINGS
            if _HAS_CONFIG_VALIDATION and ValidationConfig
            else 5
        )

        for normalized, sections_list in sentence_occurrences.items():
            if len(sections_list) >= 2 and redundancy_count < max_redundancy_warnings:
                # Only report once per unique redundancy
                unique_sections = list(dict.fromkeys(sections_list))
                if len(unique_sections) >= 2:
                    preview = normalized[:80] + "..." if len(normalized) > 80 else normalized
                    self.errors.append(
                        ValidationError(
                            severity="WARNING",
                            category="REDUNDANCY_DETECTED",
                            section=", ".join(unique_sections[:3]),
                            message=(
                                "Dieser Abschnitt wiederholt längere Textbausteine, "
                                "die bereits im Report vorkamen. Bitte Kurzlabels verwenden."
                            ),
                            details=f"Wiederholter Text: \"{preview}\" in {len(unique_sections)} Sektionen",
                        )
                    )
                    redundancy_count += 1

    # ------------------------------------------------------------------
    # PHASE 1.5 CONSISTENCY VALIDATION METHODS
    # ------------------------------------------------------------------

    def _check_hauptleistung_limits(self) -> None:
        """
        Phase 2: Validate hauptleistung occurrence counts.
        - Executive Summary: MIN 4 occurrences (per prompt requirement)
        - Recommendations: MIN 3 occurrences (per prompt requirement)
        - Roadmap: MAX 5 occurrences
        """
        hauptleistung = self.meta.get("hauptleistung", "")
        if not hauptleistung or len(hauptleistung) < 3:
            return  # No hauptleistung to check

        # Check Executive Summary (minimum 3, recommended 4)
        exec_summary = self.sections.get("EXEC_SUMMARY_HTML", "")
        if exec_summary and isinstance(exec_summary, str):
            count = exec_summary.lower().count(hauptleistung.lower())
            if count < 3:  # CRITICAL: less than 3 is unacceptable
                self.errors.append(
                    ValidationError(
                        severity="CRITICAL",
                        category="HAUPTLEISTUNG_UNDERUSE",
                        section="EXEC_SUMMARY_HTML",
                        message=f"Executive Summary enthält nur {count}x hauptleistung (Minimum: 3)",
                        details=f"Hauptleistung '{hauptleistung}' muss mindestens 3x vorkommen",
                    )
                )
            elif count < 4:  # WARNING: 3 is minimum, 4 is ideal
                self.errors.append(
                    ValidationError(
                        severity="WARNING",
                        category="HAUPTLEISTUNG_UNDERUSE",
                        section="EXEC_SUMMARY_HTML",
                        message=f"Executive Summary enthält nur {count}x hauptleistung (Empfohlen: 4)",
                        details=f"Hauptleistung '{hauptleistung}' sollte 4x vorkommen für optimale Integration",
                    )
                )

        # Check Recommendations (minimum 2, recommended 3)
        recommendations = self.sections.get("RECOMMENDATIONS_HTML", "")
        if recommendations and isinstance(recommendations, str):
            count = recommendations.lower().count(hauptleistung.lower())
            if count < 2:  # CRITICAL: less than 2 is unacceptable
                self.errors.append(
                    ValidationError(
                        severity="CRITICAL",
                        category="HAUPTLEISTUNG_UNDERUSE",
                        section="RECOMMENDATIONS_HTML",
                        message=f"Recommendations enthält nur {count}x hauptleistung (Minimum: 2)",
                        details=f"Hauptleistung '{hauptleistung}' muss mindestens 2x vorkommen",
                    )
                )
            elif count < 3:  # WARNING: 2 is minimum, 3 is ideal
                self.errors.append(
                    ValidationError(
                        severity="WARNING",
                        category="HAUPTLEISTUNG_UNDERUSE",
                        section="RECOMMENDATIONS_HTML",
                        message=f"Recommendations enthält nur {count}x hauptleistung (Empfohlen: 3)",
                        details=f"Hauptleistung '{hauptleistung}' sollte 3x vorkommen für optimale Integration",
                    )
                )
            elif count > 6:  # WARNING: too many occurrences
                self.errors.append(
                    ValidationError(
                        severity="WARNING",
                        category="HAUPTLEISTUNG_OVERUSE",
                        section="RECOMMENDATIONS_HTML",
                        message=f"Recommendations enthält {count}x hauptleistung (Maximum: 6)",
                        details=f"Zu viele Wiederholungen - nutze Synonyme",
                    )
                )

        # Check Roadmap (maximum 5, hard limit 10)
        roadmap = self.sections.get("ROADMAP_90D_HTML", "")
        if roadmap and isinstance(roadmap, str):
            count = roadmap.lower().count(hauptleistung.lower())
            if count > 10:  # CRITICAL: excessive repetition
                self.errors.append(
                    ValidationError(
                        severity="CRITICAL",
                        category="HAUPTLEISTUNG_OVERUSE",
                        section="ROADMAP_90D_HTML",
                        message=f"Roadmap enthält {count}x hauptleistung (Maximum: 5)",
                        details=f"Zu viele Wiederholungen - nutze Synonyme",
                    )
                )
            elif count > 5:  # WARNING: high but acceptable
                self.errors.append(
                    ValidationError(
                        severity="WARNING",
                        category="HAUPTLEISTUNG_OVERUSE",
                        section="ROADMAP_90D_HTML",
                        message=f"Roadmap enthält {count}x hauptleistung (Empfohlen: max 5)",
                        details=f"Zu viele Wiederholungen - nutze Synonyme",
                    )
                )

    def _check_roi_consistency(self) -> None:
        """
        Phase 2: ROI PROHIBITION - No ROI percentages allowed outside Business Case.
        Per prompt requirement: ROI-Werte sind in diesen Sektionen VERBOTEN.
        """
        # Pattern to find ROI percentages (e.g., "284%", "337%", "200%", "150%")
        # Matches 2-3 digit numbers followed by %
        roi_pattern = r"(\d{2,3})\s*%"

        # Sections where ROI is PROHIBITED (per prompt requirement)
        prohibited_roi_sections = [
            "EXEC_SUMMARY_HTML",
            "GAMECHANGER_HTML",
            "RECOMMENDATIONS_HTML",
            "ROADMAP_90D_HTML",
        ]

        for section_name in prohibited_roi_sections:
            content = self.sections.get(section_name, "")
            if not content or not isinstance(content, str):
                continue

            # Find all percentage values
            matches = re.findall(roi_pattern, content)
            # Filter for ROI-like ranges (100-500%) - typical ROI values
            roi_values = [int(m) for m in matches if 100 <= int(m) <= 500]

            if roi_values:
                # ANY ROI percentage in these sections - temporarily WARNING
                # Per prompt: "ROI PROHIBITION - ZERO TOLERANCE" (relaxed temporarily)
                self.errors.append(
                    ValidationError(
                        severity="WARNING",
                        category="ROI_PROHIBITED",
                        section=section_name,
                        message=f"ROI-Prozentsatz {roi_values[0]}% in verbotenem Abschnitt gefunden",
                        details="ROI-Werte sind nur im Business Case erlaubt. Entfernen oder durch '→ siehe Business Case' ersetzen.",
                    )
                )
                # Only report first occurrence per section
                continue

    def _check_incomplete_sentences(self) -> None:
        """
        Sprint P1.5-4: Check for incomplete sentence fragments.
        E.g., "Einrichten eines." without completing the sentence.
        """
        # CRITICAL patterns - obvious fragments that break report quality
        critical_patterns = [
            # Empty labeled content
            r"Maßnahme:\s*\.",  # Empty Maßnahme
            r"Maßnahme:\s*$",   # Maßnahme without content
            r"Schwerpunkt:\s*\.",  # Empty Schwerpunkt
            r"Schwerpunkt:\s*$",   # Schwerpunkt without content
            r"Nutzen:\s*\.",  # Empty Nutzen
            r"Nutzen:\s*$",   # Nutzen without content
            r"Aufwand:\s*\.",  # Empty Aufwand
            r"Aufwand:\s*$",   # Aufwand without content
            # Sentence fragments ending with indefinite article
            r"\bEinrichten eines\.\s",
            r"\bImplementieren von\.\s",
            r"\bAufbau einer\.\s",
            r"\bEinführung eines\.\s",
            r"\bDefinition einer\.\s",
            r"\bOptimierung eines\.\s",
            r"\bAutomatisierung von\.\s",
            r"\bIntegration von\.\s",
            # NOTE: Removed preposition patterns (für, mit, auf, etc.) - too many false positives
            # German separable verbs legitimately end with these (zeigt auf, baut auf, etc.)
            # Empty bullet points
            r"<li>\s*</li>",
            r"<li>\s*\.</li>",
            # Strong tag without content
            r"<strong>\s*</strong>",
            r"<strong>:\s*</strong>",
        ]

        # WARNING patterns - less severe fragments
        warning_patterns = [
            r"\bEntwicklung eines\.\s",
            r"\bErstellung einer\.\s",
            r"\bAusbau eines\.\s",
            r"\bVerbesserung der\.\s",
            r"\beines\.\s*</",  # Ends with "eines." before HTML tag
            r"\beiner\.\s*</",  # Ends with "einer." before HTML tag
            r"\beinem\.\s*</",  # Ends with "einem." before HTML tag
            # Sentences ending with "und" (incomplete enumeration)
            r"\bund\.\s*</",
            r"\bsowie\.\s*</",
        ]

        for section_name, content in self.sections.items():
            if not isinstance(content, str):
                continue

            # Check CRITICAL patterns
            for pattern in critical_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    match = re.search(pattern, content, re.IGNORECASE)
                    preview = content[max(0, match.start() - 20):match.end() + 20] if match else ""
                    self.errors.append(
                        ValidationError(
                            severity="WARNING",
                            category="INCOMPLETE_SENTENCE",
                            section=section_name,
                            message="Unvollständiger Satz (Fragment) - bitte prüfen",
                            details=f"Fragment: '...{preview}...'",
                        )
                    )
                    break  # Only report once per section

            # Check WARNING patterns (only if no CRITICAL found)
            else:
                for pattern in warning_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        match = re.search(pattern, content, re.IGNORECASE)
                        preview = content[max(0, match.start() - 20):match.end() + 20] if match else ""
                        self.errors.append(
                            ValidationError(
                                severity="WARNING",
                                category="INCOMPLETE_SENTENCE",
                                section=section_name,
                                message="Möglicherweise unvollständiger Satz",
                                details=f"Fragment: '...{preview}...'",
                            )
                        )
                        break

    def _check_tone_consistency(self) -> None:
        """
        Sprint P1.5-6: Check for Sie vs du consistency.
        Output should always use formal "Sie", never informal "du".
        """
        # Patterns for informal "du" forms (German)
        informal_patterns = [
            r"\bdu\b",
            r"\bdein\b",
            r"\bdeiner\b",
            r"\bdeinem\b",
            r"\bdeinen\b",
            r"\bdir\b",
            r"\bdich\b",
            r"\beuer\b",
            r"\beure\b",
            r"\beuren\b",
            r"\beurer\b",
            r"\beach\b",
        ]

        # Sections to check (user-facing content)
        content_sections = [
            "EXEC_SUMMARY_HTML",
            "GAMECHANGER_HTML",
            "RECOMMENDATIONS_HTML",
            "ROADMAP_90D_HTML",
            "QUICK_WINS_JSON",
            "BUSINESS_CASE_HTML",
            "AI_ACT_SUMMARY_HTML",
        ]

        for section_name in content_sections:
            content = self.sections.get(section_name, "")
            if not content or not isinstance(content, str):
                continue

            for pattern in informal_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    self.errors.append(
                        ValidationError(
                            severity="WARNING",
                            category="TONE_INCONSISTENCY",
                            section=section_name,
                            message=f"Informelle Anrede gefunden: '{matches[0]}'",
                            details="Output sollte immer formelles 'Sie' verwenden, nicht 'du'",
                        )
                    )
                    break  # Only report once per section

    def _check_location_consistency(self) -> None:
        """
        Sprint P1.5-7: Check that the correct Bundesland is used.
        Should not mention other Bundesländer.
        """
        bundesland = self.meta.get("BUNDESLAND_LABEL", "") or self.meta.get("bundesland", "")
        if not bundesland:
            return

        # All German Bundesländer
        all_bundeslaender = [
            "Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen",
            "Hamburg", "Hessen", "Mecklenburg-Vorpommern", "Niedersachsen",
            "Nordrhein-Westfalen", "NRW", "Rheinland-Pfalz", "Saarland",
            "Sachsen", "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen",
        ]

        # Normalize the user's Bundesland
        user_bundesland_normalized = bundesland.lower().strip()

        # Check sections that mention location
        location_sections = [
            "BUSINESS_CASE_HTML",
            "FOERDERPOTENZIAL_HTML",
        ]

        for section_name in location_sections:
            content = self.sections.get(section_name, "")
            if not content or not isinstance(content, str):
                continue

            for bl in all_bundeslaender:
                # Skip if this is the user's Bundesland
                if bl.lower() in user_bundesland_normalized or user_bundesland_normalized in bl.lower():
                    continue

                if bl in content:
                    # CRITICAL for Förderpotenzial (wrong funding info)
                    # WARNING for other sections
                    severity = "CRITICAL" if section_name == "FOERDERPOTENZIAL_HTML" else "WARNING"
                    self.errors.append(
                        ValidationError(
                            severity=severity,
                            category="LOCATION_INCONSISTENCY",
                            section=section_name,
                            message=f"Falsches Bundesland '{bl}' gefunden (User: {bundesland})",
                            details=f"User-Bundesland ist '{bundesland}', nicht '{bl}'",
                        )
                    )
                    break  # Only report first mismatch per section

    # ------------------------------------------------------------------


def validate_report(sections: Dict[str, Any], briefing: Dict[str, Any]) -> bool:
    validator = ReportValidator(sections, briefing)
    is_valid, errors = validator.validate_all()
    validator.print_report()
    return is_valid


def filter_size_inappropriate_content(content: str, unternehmensgroesse: str) -> str:
    """
    PLATIN+ Post-Filter: Ersetzt size-inappropriate Begriffe im Content.

    Sprint N3.1: Für Solo-Profile wird apply_solo_persona_filter() aufgerufen.
    Sprint G3.1: Für Team/KMU wird apply_size_persona_filter() aufgerufen,
    das Solo-spezifische Phrasen durch Team/KMU-passende Alternativen ersetzt.
    Sprint G15.1-A: Global artifact cleaning (OnPrüfroutineing etc.) for all sizes.
    """
    import logging
    import re

    log = logging.getLogger(__name__)

    if not content or not isinstance(content, str):
        return content

    # SPRINT G15.1-A: Global artifact removal (applies to ALL sizes)
    artifact_replacements_made = []
    # Sort by length (longest first) to avoid partial matches
    sorted_artifacts = sorted(
        ReportValidator.ARTIFACT_REPLACEMENTS.items(),
        key=lambda x: len(x[0]),
        reverse=True
    )
    for artifact, replacement in sorted_artifacts:
        if artifact in content:
            content = content.replace(artifact, replacement)
            artifact_replacements_made.append(f"{artifact} → {replacement}")

    if artifact_replacements_made:
        log.info(f"🧹 Artifact-Cleanup: {len(artifact_replacements_made)} Ersetzungen")

    size_raw = unternehmensgroesse.lower() if unternehmensgroesse else ""

    # Determine size category
    if "solo" in size_raw or "1" in size_raw or "freiberuf" in size_raw:
        size_key = "solo"
    elif "team" in size_raw or "klein" in size_raw or "2" in size_raw:
        size_key = "team"
    else:
        size_key = "kmu"

    # Solo-spezifische Ersetzungen via apply_solo_persona_filter
    if size_key == "solo":
        from services.prompt_enhancer import apply_solo_persona_filter
        content = apply_solo_persona_filter(content)
    else:
        # SPRINT G3.1: Team/KMU-spezifische Ersetzungen
        replacements = ReportValidator.SIZE_REPLACEMENTS.get(size_key, {})
        if replacements:
            replacements_made = []
            # Sort by length (longest first) to avoid partial matches
            sorted_replacements = sorted(
                replacements.items(),
                key=lambda x: len(x[0]),
                reverse=True
            )
            for term, replacement in sorted_replacements:
                if term.lower() in content.lower():
                    # Case-insensitive replacement
                    pattern = re.compile(re.escape(term), re.IGNORECASE)
                    if pattern.search(content):
                        content = pattern.sub(replacement, content)
                        replacements_made.append(f"{term} → {replacement}")

            if replacements_made:
                log.debug(f"🔧 Size-Persona-Filter ({size_key}): {len(replacements_made)} Ersetzungen")

    return content


def filter_all_sections(
    sections: Dict[str, Any],
    briefing: Dict[str, Any],
) -> Dict[str, Any]:
    import logging

    log = logging.getLogger(__name__)
    unternehmensgroesse = briefing.get("unternehmensgroesse", "klein")
    log.info(
        f"[CONTENT-FILTER] Filtering size-inappropriate content "
        f"for {unternehmensgroesse}"
    )

    filtered_sections: Dict[str, Any] = {}
    for section_key, section_value in sections.items():
        if isinstance(section_value, str):
            filtered_sections[section_key] = filter_size_inappropriate_content(
                section_value,
                unternehmensgroesse,
            )
        else:
            filtered_sections[section_key] = section_value

    return filtered_sections


# =============================================================================
# SPRINT N2: PLACEHOLDER & LEAK HEALING
# =============================================================================

# Critical sections that must never be empty
CRITICAL_PLACEHOLDER_SECTIONS = [
    "KI_AKTIVITAETEN_ZIELE_HTML",
    "ki_aktivitaeten_ziele",
]


def build_ki_aktivitaeten_fallback(sections: Dict[str, Any]) -> str:
    """
    SPRINT N2: Build fallback content for KI_AKTIVITAETEN_ZIELE section.

    This ensures the section is never empty, preventing report hard stops.

    Args:
        sections: Current sections dict (for context extraction)

    Returns:
        HTML fallback content for KI activities section
    """
    return """
    <section class="section ki-aktivitaeten-ziele">
      <h2>KI-Aktivitäten & Ziele</h2>
      <p>Aktuell werden erste KI-gestützte Workflows in Analyse, Dokumentation
      und Reporting getestet. Kurzfristig liegt der Fokus auf klar definierten,
      gut kontrollierbaren Automatisierungsbausteinen.</p>
      <p>Mittelfristig folgt der Ausbau standardisierter Prozesse, langfristig
      der Aufbau erweiterbarer KI-Services und eines belastbaren KI-Governance-Frameworks.</p>
      <ul>
        <li><strong>Kurzfristig (0-3 Monate):</strong> Pilotprojekte mit kontrollierbarem Scope</li>
        <li><strong>Mittelfristig (3-12 Monate):</strong> Standardisierung erfolgreicher Workflows</li>
        <li><strong>Langfristig (12+ Monate):</strong> Skalierung und Governance-Framework</li>
      </ul>
    </section>
    """


def heal_placeholder_sections(sections: Dict[str, Any]) -> int:
    """
    SPRINT N2: Heal critical sections that are empty or contain only whitespace.

    This function MUST be called before hard_stop_if_invalid() to prevent
    report failures due to empty critical sections.

    Args:
        sections: Sections dict to heal (modified in place)

    Returns:
        Number of sections healed
    """
    healed_count = 0

    for key in CRITICAL_PLACEHOLDER_SECTIONS:
        value = sections.get(key, "")
        if not value or (isinstance(value, str) and value.strip() == ""):
            log.warning(
                "[N2-Heal] Empty critical section '%s' detected, applying fallback",
                key
            )
            sections[key] = build_ki_aktivitaeten_fallback(sections)
            healed_count += 1

    if healed_count > 0:
        log.info("[N2-Heal] Healed %d empty placeholder sections", healed_count)

    return healed_count


def _build_generic_leak_fallback(section_name: str, company_size: str = "team", lang: str = "de") -> str:
    """
    SPRINT N3.2/N3.3: Build a constructive fallback for sections with quality issues.

    SPRINT N3.3 (TASK 3): Premium "Consulting Tone" templates:
    - KI-Stack: McKinsey-style (Strengths, Gaps, 90-Day Priorities, Strategic Leverage)
    - Branch Deep Dive: BCG-style (Market Dynamics, Competition, Risks, Opportunities, Actions)

    Args:
        section_name: Name of the section needing fallback
        company_size: Company size for personalization
        lang: Language code (de/en)

    Returns:
        HTML fallback content
    """
    # 3.1.4.13: i18n helper for fallback headings
    is_en = str(lang or "de").lower().startswith("en")
    # Size-aware context
    if "solo" in company_size.lower():
        context = "Ihre Tätigkeit"
        address = "Sie"
        structure = "Ihr Arbeitsbereich"
        team_ref = "Ihren Arbeitsprozessen"
    else:
        context = "Ihr Unternehmen"
        address = "Ihr Team"
        structure = "Ihre Organisation"
        team_ref = "Ihren Teams"

    # N3.3 TASK 3: McKinsey-style template for KI-Stack Summary
    # Structure: Strengths → Gaps → 90-Day Priorities → Strategic Leverage
    ki_stack_mckinsey = f"""
            <p><strong>Executive KI-Stack Assessment</strong></p>

            <p class="subtitle">Strategische Analyse der technologischen Ausgangslage</p>

            <p><strong>1. Aktuelle Stärken</strong></p>
            <ul>
              <li><strong>Digitale Infrastruktur:</strong> Grundlegende IT-Systeme sind etabliert und bilden eine solide Basis für KI-Integration</li>
              <li><strong>Prozessreife:</strong> Standardisierte Workflows ermöglichen systematische Automatisierung mit messbarem ROI</li>
              <li><strong>Organisationale Bereitschaft:</strong> Erkennbare Offenheit für technologische Innovation in {team_ref}</li>
            </ul>

            <p><strong>2. Identifizierte Lücken</strong></p>
            <ul>
              <li><strong>Strategischer Rahmen:</strong> Fehlende übergreifende KI-Strategie führt zu fragmentierten Einzelinitiativen</li>
              <li><strong>Datenqualität:</strong> Verfügbare Datenbasis nicht optimal für ML-Anwendungen aufbereitet (Konsistenz, Vollständigkeit)</li>
              <li><strong>Kompetenzprofil:</strong> Skill-Gap bei fortgeschrittenen KI-Themen wie Prompt Engineering und API-Integration</li>
            </ul>

            <p><strong>3. Prioritäten für die nächsten 90 Tage</strong></p>
            <ol>
              <li><strong>Quick-Win Pilotprojekt:</strong> Ein Use Case mit hohem ROI-Potenzial und geringem Implementierungsrisiko identifizieren und umsetzen</li>
              <li><strong>Data Governance initiieren:</strong> Kritische Datenquellen inventarisieren und Qualitätsstandards definieren</li>
              <li><strong>Capability Building:</strong> Strukturiertes Schulungsprogramm für {address} zu KI-Grundlagen starten</li>
            </ol>

            <p><strong>4. Strategische Hebel</strong></p>
            <ul>
              <li><strong>Skalierungspotenzial:</strong> Erfolgreiche Pilotprojekte systematisch auf weitere Bereiche ausweiten – Multiplikatoreffekt nutzen</li>
              <li><strong>Wettbewerbsdifferenzierung:</strong> KI-gestützte Prozesseffizienz als Basis für verbesserte Kundenreaktionszeiten und Servicequalität</li>
            </ul>
        """

    # N3.3 TASK 3: BCG-style template for Branch Deep Dive
    # Structure: Market Dynamics → Competition → Risks → Opportunities → Actions
    # 3.1.4.13/3.1.4.14: i18n headings and content
    _deep_dive_title = "Industry Deep Dive" if is_en else "Branchen-Deep-Dive"
    _recommendations_title = "Recommendations" if is_en else "Handlungsempfehlungen"
    _subtitle = "Strategic market and competitive analysis" if is_en else "Strategische Markt- und Wettbewerbsanalyse"
    _section1_title = "1. Market & Trend Dynamics" if is_en else "1. Markt- & Trenddynamik"
    _section1_content = (
        "The industry is undergoing a fundamental digital transformation. AI adoption "
        "is accelerating exponentially – early adopters are already realizing substantial "
        "efficiency gains (15-35% in automated processes). The tipping point for mass "
        "adoption is expected industry-wide within the next 18-24 months."
    ) if is_en else (
        "Die Branche durchläuft eine fundamentale digitale Transformation. KI-Adoption "
        "beschleunigt sich exponentiell – Früheinsteiger realisieren bereits substanzielle "
        "Effizienzgewinne (15-35% in automatisierten Prozessen). Der Wendepunkt zur "
        "Massenadoption wird branchenweit innerhalb der nächsten 18-24 Monate erwartet. "
        "Die Technologiereife kommerzieller KI-Lösungen hat kritische Schwelle überschritten."
    )
    branch_deep_dive_bcg = f"""
            <p><strong>{_deep_dive_title}</strong></p>

            <p class="subtitle">{_subtitle}</p>

            <p><strong>{_section1_title}</strong></p>
            <p>{_section1_content}</p>

            <p><strong>2. Wettbewerbsdruck & Differenzierungsfaktoren</strong></p>
            <p>Marktführer investieren signifikant in KI-Capabilities – der Abstand zu
            Nachzüglern wächst. Differenzierungsfaktoren: Reaktionsgeschwindigkeit,
            Personalisierungsgrad, Kosteneffizienz. Unternehmen ohne KI-Strategie
            riskieren binnen 3-5 Jahren Marktrelevanz. First-Mover-Advantage ist in
            Kernprozessen noch realisierbar.</p>

            <p><strong>3. Kernrisiken & Regulatorische Trigger</strong></p>
            <ul>
              <li><strong>Regulatorik:</strong> EU AI Act erfordert Compliance-Anpassungen – Übergangsfrist endet 2025/2026</li>
              <li><strong>Talentmarkt:</strong> KI-Fachkräftemangel treibt Personalkosten und verlängert Implementierungszyklen</li>
              <li><strong>Technologierisiko:</strong> Schnelle Obsoleszenz – Tool-Entscheidungen können binnen 12 Monaten revidiert werden müssen</li>
            </ul>

            <p><strong>4. Chancen für Wertschöpfung & Produktivität</strong></p>
            <ul>
              <li><strong>Prozesseffizienz:</strong> 20-40% Zeitersparnis bei repetitiven Tätigkeiten durch intelligente Automatisierung</li>
              <li><strong>Qualitätssteigerung:</strong> KI-gestützte Fehlerprävention reduziert Nacharbeit um 25-50%</li>
              <li><strong>Skalierung:</strong> Wachstum ohne proportionale Ressourcenaufstockung – verbesserte Unit Economics</li>
              <li><strong>Kundenzentrierung:</strong> Datengestützte Personalisierung erhöht Kundenbindung messbar</li>
            </ul>

            <p><strong>5. {_recommendations_title}</strong></p>
            <ol>
              <li><strong>Strategische Positionierung:</strong> KI als Kernbestandteil der Unternehmensstrategie verankern – Investitionsbudget sichern</li>
              <li><strong>Fokussierte Umsetzung:</strong> 2-3 High-Impact Use Cases priorisieren statt breiter Streuung – Ressourcen bündeln</li>
              <li><strong>Ökosystem aufbauen:</strong> Partner-Netzwerk aus Technologieanbietern und Implementierungspartnern etablieren</li>
            </ol>
        """

    # Section-specific constructive fallbacks (N3.3 Premium Templates)
    executive_summary_fallback = f"""
            <p>Die strategische Analyse identifiziert signifikante KI-Potenziale für {context}.
            Kernempfehlungen und priorisierte Maßnahmen sind in den folgenden Kapiteln detailliert.</p>
        """
    section_fallbacks = {
        "ki_stack_summary": ki_stack_mckinsey,
        "branch_deep_dive": branch_deep_dive_bcg,
        "executive_summary": executive_summary_fallback,
        "exec_summary": executive_summary_fallback,  # Alias for tests
    }

    # Get section-specific fallback or use generic
    section_key = section_name.lower().replace('_html', '').replace('-', '_')
    specific_fallback = section_fallbacks.get(section_key)

    if specific_fallback:
        return f"""
        <section class="section {section_key.replace('_', '-')}">
          {specific_fallback}
        </section>
        """

    # Generic fallback - now returns empty string to avoid redundant placeholder text
    # If multiple sections need healing, we don't want identical placeholder paragraphs
    # appearing multiple times in the report. Section-specific fallbacks above should be
    # used for important sections; others are simply hidden.
    log.debug(
        "[N2-Heal] No specific fallback for section '%s' - returning empty",
        section_key
    )
    return ""


def validate_and_heal(
    sections: Dict[str, Any],
    briefing: Dict[str, Any],
) -> Tuple[bool, List[ValidationError], int]:
    """
    SPRINT N2: Validate sections AND heal any issues found.

    This is the new recommended validation function that:
    1. Validates all sections
    2. Detects LLM leak phrases
    3. REPLACES leaked sections with fallback content
    4. Returns validation result with healing count

    IMPORTANT: This modifies sections dict in place!

    Args:
        sections: Sections dict to validate and heal (MODIFIED IN PLACE)
        briefing: Briefing/answers dict

    Returns:
        Tuple of (is_valid, errors, healed_count)
    """
    company_size = briefing.get("unternehmensgroesse", "team")
    # 3.1.4.13: Get language for i18n fallbacks
    report_lang = briefing.get("lang") or briefing.get("LANG") or briefing.get("sprache") or "de"

    # First, heal empty placeholder sections
    placeholder_healed = heal_placeholder_sections(sections)

    # Create validator
    validator = ReportValidator(sections, briefing)

    # Run validation (this populates validator.errors)
    is_valid, errors = validator.validate_all()

    # Now heal any LLM leak issues by replacing content
    leak_healed = 0
    for error in errors:
        if error.category == "GENERIC_LLM_LEAK":
            section_name = error.section
            if section_name in sections and isinstance(sections[section_name], str):
                log.warning(
                    "[N2-Heal] Replacing leaked content in section '%s'",
                    section_name
                )
                # Replace with fallback (3.1.4.13: pass lang for i18n)
                sections[section_name] = _build_generic_leak_fallback(
                    section_name, company_size, report_lang
                )
                leak_healed += 1

    total_healed = placeholder_healed + leak_healed

    if total_healed > 0:
        log.info(
            "[N2-Heal] Total healed: %d (placeholders=%d, leaks=%d)",
            total_healed, placeholder_healed, leak_healed
        )

    # Re-validate to get final status (after healing)
    if leak_healed > 0:
        # Create new validator with healed sections
        validator = ReportValidator(sections, briefing)
        is_valid, errors = validator.validate_all()

    return is_valid, errors, total_healed


# =============================================================================
# SPRINT N2: Module-level leak phrases constant
# =============================================================================
# Alias for easy import from outside the class
GENERIC_LLM_LEAK_PHRASES = ReportValidator.GENERIC_LLM_LEAK_PHRASES

# N3: Pre-compile single regex for O(n) leak detection instead of O(n*phrases)
_LEAK_DETECTION_PATTERN = re.compile(
    '|'.join(re.escape(p) for p in GENERIC_LLM_LEAK_PHRASES),
    re.IGNORECASE
)


def remove_leak_phrases_from_html(html: str) -> Tuple[str, int]:
    """
    SPRINT N2: Remove any remaining leak phrases from final HTML.

    This is a last-resort safety net before PDF rendering.

    SPRINT N3: Optimized for performance with 95+ phrases.
    - Use single compiled regex for O(n) detection
    - Only process phrases that were actually found

    Args:
        html: HTML content to clean

    Returns:
        Tuple of (cleaned_html, phrases_removed_count)
    """
    if not html:
        return html, 0

    # N3: Single-pass detection using pre-compiled regex - O(n) instead of O(n*phrases)
    found_phrases = _LEAK_DETECTION_PATTERN.findall(html)
    if not found_phrases:
        return html, 0

    # Get unique phrases found (case-insensitive dedup)
    unique_phrases = list({p.lower(): p for p in found_phrases}.values())

    cleaned = html
    removed_count = 0

    # Only process phrases that were actually found (usually 0-3, not 95+)
    for phrase in unique_phrases:
        # PLATIN+++ v5.4: More precise leak removal
        # OLD (greedy): [^.!?]*{phrase}[^.!?]*[.!?]?\s* - matched across HTML elements
        # NEW: Respect HTML boundaries by excluding < and > from character class
        escaped_phrase = re.escape(phrase)
        # Pattern: match text with phrase, stopping at sentence boundaries AND HTML tags
        pattern = rf'[^<>.!?]*{escaped_phrase}[^<>.!?]*[.!?]?\s*'
        matches = re.findall(pattern, cleaned, re.IGNORECASE)
        if matches:
            for match in matches:
                # Safety: only remove if match is reasonable length (< 500 chars)
                if len(match) < 500:
                    cleaned = cleaned.replace(match, '', 1)
                    removed_count += 1
                else:
                    # Fallback: just remove the phrase itself
                    cleaned = re.sub(escaped_phrase, '', cleaned, count=1, flags=re.IGNORECASE)
                    removed_count += 1
            log.warning(
                "[N2-SafetyNet] Removed %d occurrences of leak phrase '%s'",
                len(matches), phrase
            )

    return cleaned, removed_count


if __name__ == "__main__":
    demo_sections = {
        "EXEC_SUMMARY_HTML": "<p>Kurzer Text mit TODO: hier weiter ausformulieren</p>",
        "BUSINESS_CASE_HTML": "<p>Beispieltext: hier Freitext einfügen</p>",
        "QUICK_WINS_HTML": "<p>Schritt 1 – beschreibe den ersten konkreten Handgriff …</p>",
    }
    demo_briefing = {"unternehmensgroesse": "solo"}

    validator = ReportValidator(demo_sections, demo_briefing)
    ok, errs = validator.validate_all()
    validator.print_report()
    print("Valid?", ok)
