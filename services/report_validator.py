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
        r'\{[A-Z_]+\}',                    # {SELBSTSTAENDIG_LABEL}
        r'\{\{[a-z_]+\}\}',                 # {{hauptleistung}}
        r'\[Deliverable \d+\]',             # [Deliverable 1]
        r'\[Name\]',                        # [Name]
        r'\[Rollen\]',                      # [Rollen]
        r'\[€\]',                           # [€]
        r'\[Zahlen\]',                      # [Zahlen]
        r'\[KPI \d+',                       # [KPI 1 mit Zahl...]
        r'\[Feature/System \d+',            # [Feature/System 1...]
        r'\[Kompletter Meilenstein',       # [Kompletter Meilenstein...]
        r'\[Konkrete Zahlen\]',            # [Konkrete Zahlen]
        r'\[X\]',                          # [X]
        r'\[Y\]',                          # [Y]
        r'\[Z\]',                          # [Z]
    ]
    
    # Generische Template-Phrasen die NICHT im finalen Report sein dürfen
    TEMPLATE_PHRASES = [
        "Was wird gebaut:",
        "Feature/System 1 - technisch konkret",
        "Messbarer Erfolg:",
        "✅ KPI 1 mit Zahl:",
        "Team: Rolle + Stunden",
        "Budget: €-Betrag oder",
        "Risiken & Mitigation:",
        "Risiko: Potentielles Problem",
        "Abhängigkeiten: Von welchen",
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
            "PMO-Team",
            "Organisationsberater",
        ],
    }

    # Replacement terms for size-inappropriate content
    SIZE_REPLACEMENTS = {
        "solo": {
            "Abteilung": "Bereich",
            "Abteilungen": "Bereiche",
            "die Geschäftsleitung": "Sie",
            "das Management": "Sie",
            "Ihr Team": "Sie",
            "Mitarbeiter": "Freelancer oder Partner",
            "HR-Abteilung": "HR-Prozesse",
            "IT-Abteilung": "IT-Setup",
        },
        "klein": {
            "der Konzern": "das Unternehmen",
            "Vorstand": "Geschäftsführung",
        }
    }
    
    # Minimum Content-Length pro Section (Zeichen)
    MIN_SECTION_LENGTH = {
        "EXECUTIVE_SUMMARY_HTML": 500,
        "QUICK_WINS_HTML": 300,
        "PILOT_PLAN_HTML": 800,  # Roadmap 90d!
        "ROADMAP_12M_HTML": 500,
        "BUSINESS_CASE_HTML": 400,
        "GAMECHANGER_HTML": 600,
        "RECOMMENDATIONS_HTML": 400,
    }
    
    def __init__(self, sections: Dict[str, Any], briefing: Dict[str, Any]):
        """
        Args:
            sections: Report-Sections dict aus gpt_analyze.py
            briefing: Original Briefing-Daten (für Kontext-Checks)
        """
        self.sections = sections
        self.briefing = briefing
        self.errors: List[ValidationError] = []
        
    def validate_all(self) -> Tuple[bool, List[ValidationError]]:
        """
        Führt alle Validierungen durch.
        
        Returns:
            (is_valid, errors) - is_valid=False wenn CRITICAL errors gefunden
        """
        self.errors = []
        
        # Alle Validierungen durchführen
        self._check_placeholders()
        self._check_empty_sections()
        self._check_template_phrases()
        self._check_size_specific_content()
        self._check_duplicate_context_blocks()
        self._check_roadmap_quality()
        
        # Critical errors = Report nicht publishable
        critical_errors = [e for e in self.errors if e.severity == "CRITICAL"]
        is_valid = len(critical_errors) == 0
        
        return is_valid, self.errors
    
    def _check_placeholders(self):
        """Prüft ob noch Placeholder nicht ersetzt wurden"""
        for section_name, content in self.sections.items():
            if not isinstance(content, str):
                continue
                
            for pattern in self.PLACEHOLDER_PATTERNS:
                matches = re.findall(pattern, content)
                if matches:
                    # Deduplicate matches
                    unique_matches = list(set(matches))
                    
                    for match in unique_matches:
                        self.errors.append(ValidationError(
                            severity="CRITICAL",
                            category="PLACEHOLDER_NOT_REPLACED",
                            section=section_name,
                            message=f"Placeholder nicht ersetzt: {match}",
                            details=f"Pattern: {pattern}, Fundstellen: {content.count(match)}×"
                        ))
    
    def _check_empty_sections(self):
        """Prüft ob wichtige Sections zu kurz/leer sind"""
        for section_name, min_length in self.MIN_SECTION_LENGTH.items():
            content = self.sections.get(section_name, "")
            
            if not isinstance(content, str):
                continue
                
            # Strip HTML tags für echte Content-Length
            text_only = re.sub(r'<[^>]+>', '', content)
            actual_length = len(text_only.strip())
            
            if actual_length < min_length:
                self.errors.append(ValidationError(
                    severity="CRITICAL" if actual_length < min_length / 2 else "WARNING",
                    category="SECTION_TOO_SHORT",
                    section=section_name,
                    message=f"Section zu kurz: {actual_length} Zeichen (Minimum: {min_length})",
                    details=f"Content preview: {text_only[:100]}..."
                ))
    
    def _check_template_phrases(self):
        """Prüft ob noch Template-Instruktionen im Report sind"""
        for section_name, content in self.sections.items():
            if not isinstance(content, str):
                continue
                
            for phrase in self.TEMPLATE_PHRASES:
                if phrase in content:
                    self.errors.append(ValidationError(
                        severity="CRITICAL",
                        category="TEMPLATE_PHRASE_FOUND",
                        section=section_name,
                        message=f"Template-Text gefunden: '{phrase}'",
                        details="GPT hat Instruktions-Text nicht durch echten Content ersetzt!"
                    ))
    
    def _check_size_specific_content(self):
        """Prüft ob verbotene Begriffe für Unternehmensgröße verwendet wurden"""
        company_size = self.briefing.get("unternehmensgroesse", "").lower()
        
        if company_size not in self.SIZE_FORBIDDEN:
            return  # Keine spezifischen Regeln für diese Größe
            
        forbidden_terms = self.SIZE_FORBIDDEN[company_size]
        
        for section_name, content in self.sections.items():
            if not isinstance(content, str):
                continue
                
            for term in forbidden_terms:
                # Case-insensitive search
                if re.search(re.escape(term), content, re.IGNORECASE):
                    self.errors.append(ValidationError(
                        severity="WARNING",
                        category="SIZE_INAPPROPRIATE_CONTENT",
                        section=section_name,
                        message=f"Unangemessen für '{company_size}': '{term}'",
                        details=f"Solo-Unternehmen haben kein '{term}'!"
                    ))
    
    def _check_duplicate_context_blocks(self):
        """Prüft ob Context-Blöcke mehrfach im HTML vorkommen"""
        # Suche nach häufigen Context-Block-Markern
        context_markers = [
            "Branchen-Context:",
            "Größen-Context:",
            "Typische Workflows:",
            "Häufigste Pain Points:",
        ]
        
        full_html = ""
        for section_name, content in self.sections.items():
            if isinstance(content, str) and "_HTML" in section_name:
                full_html += content
        
        for marker in context_markers:
            count = full_html.count(marker)
            if count > 2:  # Mehr als 2× = definitiv zu viel
                self.errors.append(ValidationError(
                    severity="WARNING",
                    category="DUPLICATE_CONTEXT_BLOCKS",
                    section="FULL_REPORT",
                    message=f"Context-Block zu oft wiederholt: '{marker}' ({count}×)",
                    details="Context sollte nur 1× auf 'Unternehmensprofil'-Seite sein!"
                ))
    
    def _check_roadmap_quality(self):
        """Spezial-Check für Roadmap 90d - häufigste Fehlerquelle!"""
        roadmap = self.sections.get("PILOT_PLAN_HTML", "")
        
        if not roadmap:
            self.errors.append(ValidationError(
                severity="CRITICAL",
                category="MISSING_ROADMAP",
                section="PILOT_PLAN_HTML",
                message="Roadmap 90 Tage fehlt komplett!",
                details="PILOT_PLAN_HTML ist leer oder nicht vorhanden"
            ))
            return
        
        # Check 1: Enthält Roadmap echte Deliverables?
        has_concrete_deliverables = bool(re.search(r'Woche \d+-\d+: [A-Z]', roadmap))
        
        if not has_concrete_deliverables:
            self.errors.append(ValidationError(
                severity="CRITICAL",
                category="ROADMAP_NO_DELIVERABLES",
                section="PILOT_PLAN_HTML",
                message="Roadmap hat keine konkreten Deliverables!",
                details="Keine 'Woche X-Y: [Deliverable]' Pattern gefunden"
            ))
        
        # Check 2: Enthält Roadmap noch Template-Marker?
        template_markers = ["[Deliverable", "[Name]", "[Rollen]", "[€]"]
        for marker in template_markers:
            if marker in roadmap:
                self.errors.append(ValidationError(
                    severity="CRITICAL",
                    category="ROADMAP_TEMPLATE_CONTENT",
                    section="PILOT_PLAN_HTML",
                    message=f"Roadmap enthält Template-Marker: '{marker}'",
                    details="GPT hat Template-Text nicht ausgefüllt!"
                ))
        
        # Check 3: Hat Roadmap messbare KPIs?
        has_kpis = bool(re.search(r'[+\-]\d+%|€\d|[0-9]+ (neue |User|Partner)', roadmap))
        
        if not has_kpis:
            self.errors.append(ValidationError(
                severity="WARNING",
                category="ROADMAP_NO_KPIS",
                section="PILOT_PLAN_HTML",
                message="Roadmap hat keine messbaren KPIs!",
                details="Keine konkreten Zahlen wie '+200%', '-50%', '100 User' gefunden"
            ))
    
    def print_report(self):
        """Gibt Validation-Report auf Console aus"""
        print("\n" + "="*80)
        print("📋 REPORT VALIDATION RESULTS")
        print("="*80)
        
        if not self.errors:
            print("✅ ALLE CHECKS BESTANDEN! Report ist GOLD STANDARD+")
            return
        
        # Gruppiere nach Severity
        critical = [e for e in self.errors if e.severity == "CRITICAL"]
        warnings = [e for e in self.errors if e.severity == "WARNING"]
        info = [e for e in self.errors if e.severity == "INFO"]
        
        if critical:
            print(f"\n🔴 CRITICAL ERRORS: {len(critical)}")
            print("→ Report kann NICHT published werden!")
            print("-" * 80)
            for err in critical:
                print(f"\n[{err.category}] {err.section}")
                print(f"   {err.message}")
                print(f"   Details: {err.details}")
        
        if warnings:
            print(f"\n⚠️  WARNINGS: {len(warnings)}")
            print("→ Report kann published werden, aber Quality leidet")
            print("-" * 80)
            for err in warnings:
                print(f"\n[{err.category}] {err.section}")
                print(f"   {err.message}")
        
        if info:
            print(f"\nℹ️  INFO: {len(info)}")
            for err in info:
                print(f"   [{err.section}] {err.message}")
        
        print("\n" + "="*80)
        print(f"TOTAL: {len(critical)} Critical | {len(warnings)} Warnings | {len(info)} Info")
        print("="*80 + "\n")


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


def filter_size_inappropriate_content(content: str, unternehmensgroesse: str) -> str:
    """
    Replace size-inappropriate terms with better alternatives.

    Args:
        content: HTML/text content to filter
        unternehmensgroesse: Company size (solo, klein, mittel, gross)

    Returns:
        Filtered content with replacements applied
    """
    import logging
    log = logging.getLogger(__name__)

    size = unternehmensgroesse.lower() if unternehmensgroesse.lower() in ReportValidator.SIZE_REPLACEMENTS else "solo"
    replacements = ReportValidator.SIZE_REPLACEMENTS.get(size, {})

    for inappropriate, replacement in replacements.items():
        if inappropriate in content:
            log.info(f"[CONTENT-FILTER] Replacing '{inappropriate}' with '{replacement}' for {size}")
            content = content.replace(inappropriate, replacement)

    return content


def filter_all_sections(sections: Dict[str, Any], briefing: Dict[str, Any]) -> Dict[str, Any]:
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
    log.info(f"[CONTENT-FILTER] Filtering size-inappropriate content for {unternehmensgroesse}")

    filtered_sections = {}
    for section_key, section_value in sections.items():
        if isinstance(section_value, str):
            filtered_sections[section_key] = filter_size_inappropriate_content(
                section_value,
                unternehmensgroesse
            )
        else:
            filtered_sections[section_key] = section_value

    return filtered_sections


# ============================================================================
# INTEGRATION IN GPT_ANALYZE.PY
# ============================================================================
# 
# In gpt_analyze.py nach Zeile 1849 (nach sections.setdefault(...)):
#
# ```python
# # Validation Gate vor PDF-Generierung
# from services.report_validator import validate_report
# 
# log.info(f"[{rid}] 🔍 Running validation checks...")
# is_valid = validate_report(sections, briefing)
# 
# if not is_valid:
#     log.warning(f"[{rid}] ⚠️ Report has validation errors but continuing...")
#     # Optional: Bei Critical Errors Report nicht generieren:
#     # raise ValueError("Report validation failed - see logs")
# else:
#     log.info(f"[{rid}] ✅ Report passed all validation checks")
# ```
#
# ============================================================================


if __name__ == "__main__":
    # Test mit Mock-Daten
    test_sections = {
        "EXECUTIVE_SUMMARY_HTML": "<p>Test summary mit {PLACEHOLDER_TEST}</p>",
        "PILOT_PLAN_HTML": "Woche 1-2: [Deliverable 1] [Name] macht [Rollen]",
        "BUSINESS_CASE_HTML": "<p>ROI ist +200% nach 12 Monaten</p>",
    }
    
    test_briefing = {
        "unternehmensgroesse": "solo",
        "hauptleistung": "Test",
    }
    
    validator = ReportValidator(test_sections, test_briefing)
    is_valid, errors = validator.validate_all()
    validator.print_report()
    
    print(f"\nValidation Result: {'PASS' if is_valid else 'FAIL'}")
