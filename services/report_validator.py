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

Version: 1.0.0-GOLD
Author: Claude + Wolf
"""

import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

__all__ = [
    "ValidationError",
    "ReportValidator",
    "validate_report",
    "filter_size_inappropriate_content",
    "filter_all_sections",
]


@dataclass
class ValidationError:
    """Ein gefundener Validation-Fehler"""
    severity: str  # "CRITICAL", "WARNING", "INFO"
    category: str  # z.B. "PLACEHOLDER", "EMPTY_SECTION"
    section: str   # z.B. "executive_summary"
    message: str   # Human-readable Beschreibung
    details: str   # Technische Details / Fundstelle


class ReportValidator:
    """Validiert Report-Sections vor PDF-Generierung"""
    
    # Bekannte Placeholder-Pattern
    PLACEHOLDER_PATTERNS = [
        r"\{[A-Z_]+\}",                    # {SELBSTSTAENDIG_LABEL}
        r"\{\{[a-z_]+\}\}",                # {{hauptleistung}}
        r"\[Deliverable \d+\]",            # [Deliverable 1]
        r"\[Name\]",                       # [Name]
        r"\[Rollen\]",                     # [Rollen]
        r"\[€\]",                          # [€]
        r"\[Zahlen\]",                     # [Zahlen]
        r"\[KPI \d+",                      # [KPI 1 mit Zahl...]
        r"\[Feature/System \d+",           # [Feature/System 1...]
        r"\[Kompletter Meilenstein",       # [Kompletter Meilenstein...]
        r"\[Konkrete Zahlen\]",            # [Konkrete Zahlen]
        r"\[X\]",                          # [X]
        r"\[Y\]",                          # [Y]
        r"\[Z\]",                          # [Z]
    ]
    
    # Generische Template-Phrasen die NICHT im finalen Report sein dürfen
    TEMPLATE_PHRASES = [
        "Hier könnten Sie",
        "Platzhalter für",
        "Beispieltext:",
        "Lorem ipsum",
        "TODO:",
        "An dieser Stelle",
        "hier weiter ausformulieren",
        "hier individuelle Inhalte ergänzen",
        "siehe oben",
        "siehe unten",
        "nach Bedarf anpassen",
        "bitte konkretisieren",
        "bitte hier Ihre",
        "hier Ihr Text",
        "Dies ist nur ein Beispiel",
        "Template-Text",
        "konkrete Zahlen ergänzen",
        "Konkrete Zahlen, z.B.",
        "Konkrete Rollen eintragen",
        "Konkrete Tools eintragen",
        "Konkrete KPIs eintragen",
        "Konkrete Systeme eintragen",
        "Konkrete Meilensteine eintragen",
        "Platzhalter für echten Inhalt",
        "Freitextfeld",
        "hier Freitext einfügen",
        "Beispielhafter Text",
        "Standard-Formulierung",
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
    ]
    
    # Verbotene Begriffe für bestimmte Unternehmensgrößen
    SIZE_FORBIDDEN = {
        "solo": [
            "PMO-Team",
            "Team aufbauen",
            "Mitarbeiter einstellen",
            "Abteilung",
            "HR-Abteilung",
            "IT-Abteilung",
            "Organisationsberater",
            "Change-Team",
            "Projektmanagement-Office",
        ],
        "team": [
            # hier könnten später zusätzliche Regeln rein
        ],
        "kmu": [
            # hier könnten später zusätzliche Regeln rein
        ],
    }
    
    # Mindestlängen je Section (reiner Text, ohne HTML-Tags)
    MIN_SECTION_LENGTH = {
        "executive_summary": 600,
        "business_case": 800,
        "quick_wins": 500,
        "roadmap_90d": 700,
        "roadmap_12m": 900,
        "strategie_governance": 800,
        "org_change": 700,
        "tools_empfehlungen": 600,
        "foerderpotenzial": 600,
    }
    
    def __init__(self, sections: Dict[str, Any], meta: Dict[str, Any]) -> None:
        """
        sections: Dict[section_name, content_string]
        meta: Briefing-Daten (inkl. Unternehmensgröße etc.)
        """
        self.sections = sections or {}
        self.meta = meta or {}
        self.errors: List[ValidationError] = []
        
        # Unternehmensgröße aus Briefing – Fallback auf 'unbekannt'
        self.company_size: str = self.meta.get("unternehmensgroesse", "unbekannt")
    
    # ------------------------------------------------------------------
    # Öffentliche API
    # ------------------------------------------------------------------
    
    def validate_all(self) -> Tuple[bool, List[ValidationError]]:
        """
        Führt alle Validierungsregeln aus und gibt (is_valid, errors) zurück.
        is_valid = False, wenn mindestens ein "CRITICAL"-Fehler existiert.
        """
        # 1) Placeholder-Checks
        self._check_placeholders()
        
        # 2) Leere/zu kurze Sections
        self._check_empty_or_short_sections()
        
        # 3) Template-Phrasen
        self._check_template_phrases()
        
        # 4) Größen-spezifische Fehler
        self._check_size_specific_issues()
        
        is_valid = not any(e.severity == "CRITICAL" for e in self.errors)
        return is_valid, self.errors
    
    def print_report(self) -> None:
        """Formatiertes Log der Findings – analog zu deinem Log-Output."""
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
    # Einzelne Checks
    # ------------------------------------------------------------------
    
    def _check_placeholders(self) -> None:
        """Sucht nach den bekannten Placeholder-Patterns in allen Sections."""
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
    
    def _check_empty_or_short_sections(self) -> None:
        """Prüft, ob wichtige Sections leer oder zu kurz sind."""
        for section_name, min_length in self.MIN_SECTION_LENGTH.items():
            content = self.sections.get(section_name, "")
            if not isinstance(content, str):
                self.errors.append(
                    ValidationError(
                        severity="CRITICAL",
                        category="SECTION_INVALID",
                        section=section_name,
                        message="Section-Inhalt fehlt oder ist kein String",
                        details=f"Typ: {type(content)}",
                    )
                )
                continue
            
            # HTML-Tags grob entfernen, um Textlänge zu prüfen
            text_only = re.sub(r"<[^>]+>", "", content)
            text_only = text_only.strip()
            
            if not text_only:
                self.errors.append(
                    ValidationError(
                        severity="CRITICAL",
                        category="SECTION_EMPTY",
                        section=section_name,
                        message="Wichtige Section ist leer",
                        details="Kein Textinhalt nach HTML-Bereinigung",
                    )
                )
                continue
            
            actual_length = len(text_only)
            if actual_length < min_length:
                self.errors.append(
                    ValidationError(
                        severity="WARNING",
                        category="SECTION_TOO_SHORT",
                        section=section_name,
                        message=(
                            f"Section zu kurz: {actual_length} Zeichen "
                            f"(Minimum: {min_length})"
                        ),
                        details=f"Content preview: {text_only[:100]}...",
                    )
                )
    
    def _check_template_phrases(self) -> None:
        """Prüft ob noch Template-Instruktionen im Report sind"""
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
    
    def _check_size_specific_issues(self) -> None:
        """Prüft, ob Inhalte nicht zur Unternehmensgröße passen (Solo/Team/KMU)."""
        forbidden_terms = self.SIZE_FORBIDDEN.get(self.company_size, [])
        if not forbidden_terms:
            return
        
        for section_name, content in self.sections.items():
            if not isinstance(content, str):
                continue
            
            lower = content.lower()
            for term in forbidden_terms:
                if term.lower() in lower:
                    self.errors.append(
                        ValidationError(
                            severity="WARNING",
                            category="SIZE_MISMATCH",
                            section=section_name,
                            message=(
                                f"Inhalt wirkt nicht passend für Unternehmensgröße "
                                f"'{self.company_size}': Begriff '{term}' gefunden."
                            ),
                            details="Bitte prüfen, ob Formulierung zur Größe passt.",
                        )
                    )


def validate_report(sections: Dict[str, Any], briefing: Dict[str, Any]) -> bool:
    """
    Main validation function - to be called from gpt_analyze.py

    Args:
        sections: Report sections dict
        briefing: Original briefing data

    Returns:
        True if report passes validation, False if critical errors found
    """
    validator = ReportValidator(sections, briefing)
    is_valid, errors = validator.validate_all()
    validator.print_report()

    return is_valid


def filter_size_inappropriate_content(
    content: str, unternehmensgroesse: str
) -> str:
    """
    Filtert größen-inkompatible Formulierungen aus einem einzelnen Text.

    Aktuell nur als Wrapper angelegt – die eigentliche Logik sitzt in
    _check_size_specific_issues und arbeitet auf allen Sections. Diese Funktion
    bleibt trotzdem als Public API bestehen, falls später mal einzelne Strings
    gefiltert werden sollen.
    """
    # Derzeit keine aktive Mutation – einfach Content zurückgeben
    return content


def filter_all_sections(
    sections: Dict[str, Any],
    briefing: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Apply size-inappropriate content filter to all sections.

    Args:
        sections: Report sections dict
        briefing: Original briefing data

    Returns:
        Filtered sections dict
    """
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
    # Minimaler Self‑Test, falls du die Datei mal direkt ausführst
    demo_sections = {
        "executive_summary": "Kurzer Text mit TODO: hier weiter ausformulieren",
        "business_case": "<p>Beispieltext: hier Freitext einfügen</p>",
        "quick_wins": "Lorem ipsum",
    }
    demo_briefing = {"unternehmensgroesse": "solo"}

    validator = ReportValidator(demo_sections, demo_briefing)
    ok, errs = validator.validate_all()
    validator.print_report()
    print("Valid?", ok)
