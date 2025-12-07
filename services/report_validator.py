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

Version: 1.5.0-SPRINT-G7 (AI Act Compliance Validation + Persona Leak Elimination)
Author: Claude + Wolf

PLATIN+ ÄNDERUNG: Validierung basiert jetzt auf WÖRTERN statt Zeichen!

SPRINT N CHANGES:
- Extended SIZE_FORBIDDEN list for Solo personas
- Updated MIN_SECTION_LENGTH_BY_SIZE with new minimums
- Added HARD_STOP_ON_SIZE_MISMATCH option
- Critical sections now enforce minimum word counts strictly
"""

import re
import logging
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

# G8.2: Import centralized validation config
try:
    from services.config_validation import (
        ValidationConfig,
        get_min_words,
        SECTION_MIN_WORDS,
    )
    _HAS_CONFIG_VALIDATION = True
except ImportError:
    _HAS_CONFIG_VALIDATION = False
    ValidationConfig = None
    get_min_words = None
    SECTION_MIN_WORDS = None

log = logging.getLogger(__name__)

__all__ = [
    "ValidationError",
    "ReportValidator",
    "validate_report",
    "filter_size_inappropriate_content",
    "filter_all_sections",
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
            "Bereichsleiter",
            "bereichsübergreifend",
            # English equivalents
            "team building",
            "team members",
            "hire employees",
            "department",
            "departments",
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

    # SPRINT N / G8.2: Hard-Stop Configuration (now ENV-controlled via ValidationConfig)
    # Can be overridden via HARD_STOP_ON_SIZE_MISMATCH env var
    HARD_STOP_ON_SIZE_MISMATCH = (
        ValidationConfig.HARD_STOP_ON_SIZE_MISMATCH
        if _HAS_CONFIG_VALIDATION and ValidationConfig
        else True
    )

    # PLATIN+ Standard: Mindestlängen in WÖRTERN (nicht Zeichen!)
    # SIZE-AWARE: Unterschiedliche Mindestlängen je Unternehmensgröße
    # Solo = kürzere Reports, KMU = ausführlichere Reports
    # SPRINT N: Updated minimums for length stabilization
    MIN_SECTION_LENGTH_WORDS = {
        "executive_summary": 150,      # SPRINT N: erhöht von 100
        "business_case": 130,          # ~800 Zeichen
        "quick_wins": 60,              # Base (wird size-aware überschrieben)
        "roadmap_90d": 250,            # Base (wird size-aware überschrieben)
        "roadmap_12m": 500,            # SPRINT N: erhöht von 400
        "strategie_governance": 130,   # ~800 Zeichen
        "org_change": 120,             # ~700 Zeichen
        "tools_empfehlungen": 120,     # SPRINT N: erhöht von 100
        "foerderpotenzial": 600,       # Reduziert für bessere Compliance
        "risks": 500,                  # Reduziert für bessere Compliance
        "recommendations": 500,        # Reduziert für bessere Compliance
        "gamechanger": 750,            # SPRINT N: erhöht von 400 (Mindestlänge fix)
        "unternehmensprofil_markt": 300,  # Reduziert für bessere Compliance
        "transparency_box": 150,       # Base (wird size-aware überschrieben)
        "technologie_prozesse": 200,   # Base (wird size-aware überschrieben)
    }

    # SPRINT N: SIZE-AWARE Überschreibungen - Updated minimums
    MIN_SECTION_LENGTH_BY_SIZE = {
        "solo": {
            # SPRINT N: Updated minimums
            "executive_summary": 150,   # SPRINT N requirement
            "quick_wins": 60,
            "roadmap_90d": 250,
            "roadmap_12m": 500,         # SPRINT N: erhöht von 400
            "org_change": 80,
            "tools_empfehlungen": 120,  # SPRINT N requirement
            "gamechanger": 750,         # SPRINT N: Mindestlänge fix
            "transparency_box": 100,
            "technologie_prozesse": 150,
        },
        "team": {
            # SPRINT N: Updated minimums
            # SPRINT G6: tools_empfehlungen erhöht, strategie_governance hinzugefügt
            "executive_summary": 180,   # SPRINT N requirement
            "quick_wins": 90,
            "roadmap_90d": 300,
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
            "executive_summary": 200,   # SPRINT N requirement
            "quick_wins": 120,
            "roadmap_90d": 350,
            "roadmap_12m": 700,         # SPRINT N: erhöht von 600
            "org_change": 120,
            "tools_empfehlungen": 220,  # SPRINT G6: erhöht von 200
            "strategie_governance": 220,  # SPRINT G6: konsistent mit anderen
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

    # Legacy-Alias für Abwärtskompatibilität
    MIN_SECTION_LENGTH = MIN_SECTION_LENGTH_WORDS

    SECTION_KEY_MAP: Dict[str, str] = {
        "executive_summary": "EXECUTIVE_SUMMARY_HTML",
        "business_case": "BUSINESS_CASE_HTML",
        "quick_wins": "quick_wins",
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

    def __init__(self, sections: Dict[str, Any], meta: Dict[str, Any]) -> None:
        self.sections = sections or {}
        self.meta = meta or {}
        self.errors: List[ValidationError] = []
        self.company_size: str = self.meta.get("unternehmensgroesse", "unbekannt")

    # ------------------------------------------------------------------

    def validate_all(self) -> Tuple[bool, List[ValidationError]]:
        print("DEBUG ReportValidator – sections keys:", list(self.sections.keys()))

        self._check_placeholders()
        self._check_empty_or_short_sections()
        self._check_template_phrases()
        self._check_quick_wins_prompt_leaks()
        self._check_size_specific_issues()
        self._check_redundancy()  # Sprint G2.4
        self._check_ai_act_sections()  # Sprint G7

        is_valid = not any(e.severity == "CRITICAL" for e in self.errors)
        return is_valid, self.errors

    def print_report(self) -> None:
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

        critical_count = sum(1 for e in self.errors if e.severity == "CRITICAL")
        warning_count = sum(1 for e in self.errors if e.severity == "WARNING")
        info_count = sum(1 for e in self.errors if e.severity == "INFO")

        print("")
        print("=" * 78)
        print("📋 REPORT VALIDATION RESULTS")
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

        for err in self.errors:
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
        for section_name, content in self.sections.items():
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

    def _check_size_specific_issues(self) -> None:
        """
        SPRINT N: Enhanced size-specific validation with HARD_STOP support.
        Checks for forbidden terms and triggers CRITICAL errors when configured.
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

        for section_name, content in self.sections.items():
            if not isinstance(content, str):
                continue
            lower = content.lower()
            for term in forbidden_terms:
                if term.lower() in lower:
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

    # SPRINT G3.3/G4.4: Extended whitelist for standard phrases that may repeat intentionally
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
    ]

    def _check_redundancy(self) -> None:
        """
        Sprint G2.4/G3.3: Check for redundant long sentences across sections.

        Warns when:
        - A sentence >20 words appears identically or 85% similar in ≥2 sections
        - Long branch/offering descriptions appear after strategic_context_block

        Sprint G3.3 tuning:
        - Increased threshold from 15 to 20 words
        - Added whitelist for standard phrases (ROI, AI Act, etc.)

        This is informational only (WARNING, not CRITICAL).
        """
        # Collect all sentences from all sections
        sentence_occurrences: Dict[str, List[str]] = {}  # normalized → list of sections

        for section_name, content in self.sections.items():
            if not isinstance(content, str) or not content:
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
    """
    import logging
    import re

    log = logging.getLogger(__name__)

    if not content or not isinstance(content, str):
        return content

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
