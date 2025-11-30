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

Version: 1.3.0-PLATIN-WORDS
Author: Claude + Wolf

PLATIN+ ÄNDERUNG: Validierung basiert jetzt auf WÖRTERN statt Zeichen!
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

    # Phrasen, die klar auf Template- oder Platzhaltertexte hindeuten
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

    # PLATIN+ Standard: Mindestlängen in WÖRTERN (nicht Zeichen!)
    # Umrechnung: ca. 5-6 Zeichen pro Wort im Deutschen
    # HINWEIS: Validator prüft konservativ auf 800 Wörter für roadmap_12m,
    # obwohl Prompt 900+ fordert – so verschwinden False Negatives bei Zähldifferenzen.
    MIN_SECTION_LENGTH_WORDS = {
        "executive_summary": 100,      # ~600 Zeichen
        "business_case": 130,          # ~800 Zeichen
        "quick_wins": 80,              # ~500 Zeichen
        "roadmap_90d": 120,            # ~700 Zeichen
        "roadmap_12m": 800,            # PLATIN+: Prompt fordert 900, Validator prüft 800 (Sicherheitsmarge)
        "strategie_governance": 130,   # ~800 Zeichen
        "org_change": 120,             # ~700 Zeichen
        "tools_empfehlungen": 100,     # ~600 Zeichen
        "foerderpotenzial": 900,       # PLATIN+: 900 Wörter
        "risks": 800,                  # PLATIN+: 800 Wörter
        "recommendations": 800,        # PLATIN+: 800 Wörter
        "gamechanger": 700,            # PLATIN+: 700 Wörter
    }

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
        "risks": "risks",                 # PLATIN+: hinzugefügt
        "recommendations": "recommendations",  # PLATIN+: hinzugefügt
        "gamechanger": "gamechanger",     # PLATIN+: hinzugefügt
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
        """
        PLATIN+ Validierung: Prüft Sections auf Mindest-WORTZAHL (nicht Zeichen!).
        """
        for logical_name, min_words in self.MIN_SECTION_LENGTH_WORDS.items():
            section_key = self.SECTION_KEY_MAP.get(logical_name, logical_name)
            if section_key not in self.sections:
                continue
            content = self.sections.get(section_key)
            if not isinstance(content, str):
                continue
            # HTML-Tags entfernen
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

            # PLATIN+: Wörter zählen statt Zeichen
            # Wörter sind durch Whitespace getrennte Sequenzen
            words = text_only.split()
            actual_word_count = len(words)

            if actual_word_count < min_words:
                self.errors.append(
                    ValidationError(
                        severity="WARNING",
                        category="SECTION_TOO_SHORT",
                        section=section_key,
                        message=(
                            f"Section zu kurz: {actual_word_count} Wörter "
                            f"(Minimum: {min_words} Wörter)"
                        ),
                        details=f"Content preview: {text_only[:150]}...",
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
    """
    PLATIN+ Post-Filter: Ersetzt size-inappropriate Begriffe im Content.

    Für Solo-Profile werden Begriffe wie "Abteilung" durch "Bereich" ersetzt,
    sofern sie sich nicht auf Kunden-Strukturen beziehen.
    """
    if not content or not isinstance(content, str):
        return content

    size_raw = unternehmensgroesse.lower() if unternehmensgroesse else ""

    # Solo-spezifische Ersetzungen
    if "solo" in size_raw or "1" in size_raw or "freiberuf" in size_raw:
        # Ersetze "Abteilung" durch "Bereich" (nur wenn nicht im Kunden-Kontext)
        # Vorsicht: Nicht ersetzen bei "Kundenabteilung", "auf Kundenseite"
        import re

        # Patterns für solo-unpassende Begriffe (nur wenn nicht Kunden-bezogen)
        replacements = [
            # "Abteilung" → "Aufgabenbereich" (wenn nicht Kunden-bezogen)
            (r'(?<![Kk]unden)([Aa])bteilung(?!en\s+(?:auf|bei|der|des)\s+[Kk]unden)', r'\1ufgabenbereich'),
            # "Abteilungen" → "Aufgabenbereiche" (wenn nicht Kunden-bezogen)
            (r'(?<![Kk]unden)([Aa])bteilungen(?!\s+(?:auf|bei|der|des)\s+[Kk]unden)', r'\1ufgabenbereiche'),
        ]

        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)

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
