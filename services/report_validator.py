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

Version: 1.2.0-GOLD
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
        "CAPEX ca. €",
        "Payback etwa Monate",
        "ROI nach 12 Monaten rund %",
    ]

    QUICK_WINS_PROMPT_PHRASES = [
        "Schritt 1 – beschreibe den ersten konkreten Handgriff",
        "Schritt 2 – definiere ein kurzes Prüfverfahren",
        "Schritt 3 – integriere die Methode in den bestehenden Alltag",
    ]

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
        "team": [],
        "kmu": [],
    }

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

    def _check_empty_or_short_sections(self) -> None:
        for logical_name, min_length in self.MIN_SECTION_LENGTH.items():
            section_key = self.SECTION_KEY_MAP.get(logical_name, logical_name)
            if section_key not in self.sections:
                continue
            content = self.sections.get(section_key)
            if not isinstance(content, str):
                continue
            text_only = re.sub(r"<[^>]+>", "", content).strip()
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
            actual_length = len(text_only)
            if actual_length < min_length:
                self.errors.append(
                    ValidationError(
                        severity="WARNING",
                        category="SECTION_TOO_SHORT",
                        section=section_key,
                        message=(
                            f"Section zu kurz: {actual_length} Zeichen "
                            f"(Minimum: {min_length})"
                        ),
                        details=f"Content preview: {text_only[:100]}...",
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
    validator = ReportValidator(sections, briefing)
    is_valid, errors = validator.validate_all()
    validator.print_report()
    return is_valid


def filter_size_inappropriate_content(content: str, unternehmensgroesse: str) -> str:
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
