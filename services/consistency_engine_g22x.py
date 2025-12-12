# -*- coding: utf-8 -*-
"""
N4.2: Consistency Engine G22-X (Cross-Language)
================================================

PLATIN+++ v5.2 - Multi-Language Intelligence Layer

Extension to the G22 Consistency Engine with cross-language rules:
- G22-X001: KPI consistency between languages
- G22-X002: Executive Summary semantic drift ≤ 0.08
- G22-X003: Roadmap action drift ≤ 0.05
- G22-X004: Terminology coherence (glossary mapping)

Integrates with existing ConsistencyEngine from consistency_engine.py.

Version: 1.0.0 (N4.2 - PLATIN+++ v5.2)
Author: Claude + Wolf
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from services.types import SectionDict, BriefingDict, EngineReport
from services.language_strategy_engine import (
    SupportedLanguage,
    CONSULTING_GLOSSARY,
    get_language_profile,
)

log = logging.getLogger(__name__)

__all__ = [
    "G22XRule",
    "G22XIssueSeverity",
    "G22XIssue",
    "G22XReport",
    "CrossLanguageConsistencyEngine",
    "check_cross_language_consistency",
    "validate_kpi_cross_language",
    "validate_executive_summary_drift",
    "validate_roadmap_drift",
    "validate_terminology_coherence",
]


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class G22XRule(Enum):
    """G22-X consistency rules for cross-language validation."""
    X001_KPI_CONSISTENCY = "G22-X001"
    X002_EXEC_SUMMARY_DRIFT = "G22-X002"
    X003_ROADMAP_DRIFT = "G22-X003"
    X004_TERMINOLOGY_COHERENCE = "G22-X004"


class G22XIssueSeverity(Enum):
    """Issue severity levels."""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


# Thresholds for drift detection
MAX_EXEC_SUMMARY_DRIFT = 0.08  # 8% semantic drift allowed
MAX_ROADMAP_DRIFT = 0.05  # 5% semantic drift for roadmap actions
MAX_KPI_VARIANCE = 0.001  # 0.1% variance for KPI values (should be exact)

# Critical KPI fields that must be identical across languages
CRITICAL_KPI_FIELDS = [
    "roi_percentage",
    "roi",
    "payback_months",
    "payback",
    "time_savings_hours",
    "time_savings",
    "risk_score",
    "readiness_score",
    "npv",
    "irr",
    "cost_savings",
]

# Sections requiring executive summary drift check
EXECUTIVE_SECTIONS = [
    "executive_summary",
    "investment_thesis",
    "gamechanger",
    "strategic_summary",
]

# Sections requiring roadmap drift check
ROADMAP_SECTIONS = [
    "roadmap_90d",
    "roadmap_12m",
    "recommendations",
    "starter_kit",
    "automation_roadmap",
]

# Terminology categories requiring coherence
TERMINOLOGY_CATEGORIES = [
    "risk_levels",
    "ai_act_terms",
    "compliance_terms",
    "kpi_terms",
    "action_verbs",
    "time_frames",
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class G22XIssue:
    """Single G22-X cross-language consistency issue."""

    rule_id: G22XRule
    severity: G22XIssueSeverity
    source_language: SupportedLanguage
    target_language: SupportedLanguage
    section: str
    message: str
    expected: Any = None
    actual: Any = None
    drift_value: Optional[float] = None
    suggestion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_id": self.rule_id.value,
            "severity": self.severity.value,
            "source_language": self.source_language.value,
            "target_language": self.target_language.value,
            "section": self.section,
            "message": self.message,
            "expected": str(self.expected) if self.expected is not None else None,
            "actual": str(self.actual) if self.actual is not None else None,
            "drift_value": round(self.drift_value, 4) if self.drift_value is not None else None,
            "suggestion": self.suggestion,
        }


@dataclass
class TerminologyMapping:
    """Mapping of a term across languages."""

    term_key: str
    category: str
    source_term: str
    target_term: str
    source_language: SupportedLanguage
    target_language: SupportedLanguage
    found_in_source: bool = False
    found_in_target: bool = False
    correctly_mapped: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "term_key": self.term_key,
            "category": self.category,
            "source_term": self.source_term,
            "target_term": self.target_term,
            "source_language": self.source_language.value,
            "target_language": self.target_language.value,
            "found_in_source": self.found_in_source,
            "found_in_target": self.found_in_target,
            "correctly_mapped": self.correctly_mapped,
        }


@dataclass
class KPIDriftResult:
    """Result of KPI drift analysis between languages."""

    kpi_name: str
    source_value: Optional[float]
    target_value: Optional[float]
    source_language: SupportedLanguage
    target_language: SupportedLanguage
    drift_absolute: float = 0.0
    drift_percentage: float = 0.0
    is_consistent: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "kpi_name": self.kpi_name,
            "source_value": self.source_value,
            "target_value": self.target_value,
            "source_language": self.source_language.value,
            "target_language": self.target_language.value,
            "drift_absolute": round(self.drift_absolute, 4),
            "drift_percentage": round(self.drift_percentage, 4),
            "is_consistent": self.is_consistent,
        }


@dataclass
class SemanticDriftResult:
    """Result of semantic drift analysis."""

    section: str
    source_language: SupportedLanguage
    target_language: SupportedLanguage
    similarity_score: float
    drift_value: float
    threshold: float
    is_within_threshold: bool
    key_phrases_preserved: int = 0
    key_phrases_total: int = 0
    issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "section": self.section,
            "source_language": self.source_language.value,
            "target_language": self.target_language.value,
            "similarity_score": round(self.similarity_score, 4),
            "drift_value": round(self.drift_value, 4),
            "threshold": self.threshold,
            "is_within_threshold": self.is_within_threshold,
            "key_phrases_preserved": self.key_phrases_preserved,
            "key_phrases_total": self.key_phrases_total,
            "issues": self.issues,
        }


@dataclass
class G22XReport:
    """Complete G22-X cross-language consistency report."""

    engine_id: str = "G22X_CROSS_LANGUAGE"
    success: bool = True
    status: str = "PASS"
    grade: str = "A"
    score: float = 100.0
    source_language: Optional[str] = None
    target_language: Optional[str] = None
    rules_checked: int = 0
    rules_passed: int = 0
    rules_failed: int = 0
    issues: List[G22XIssue] = field(default_factory=list)
    kpi_drift_results: List[KPIDriftResult] = field(default_factory=list)
    semantic_drift_results: List[SemanticDriftResult] = field(default_factory=list)
    terminology_mappings: List[TerminologyMapping] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def add_issue(self, issue: G22XIssue) -> None:
        """Add an issue and recalculate scores."""
        self.issues.append(issue)
        self._recalculate()

    def add_warning(self, warning: str) -> None:
        """Add a warning."""
        self.warnings.append(warning)

    def _recalculate(self) -> None:
        """Recalculate status, grade, and score."""
        errors = sum(1 for i in self.issues if i.severity == G22XIssueSeverity.ERROR)
        warnings = sum(1 for i in self.issues if i.severity == G22XIssueSeverity.WARNING)

        # Score: -15 per error, -5 per warning
        self.score = max(0.0, min(100.0, 100.0 - (errors * 15) - (warnings * 5)))
        self.rules_failed = errors + warnings
        self.rules_passed = self.rules_checked - self.rules_failed

        # Grade
        if self.score >= 95:
            self.grade = "A"
        elif self.score >= 85:
            self.grade = "B"
        elif self.score >= 70:
            self.grade = "C"
        elif self.score >= 50:
            self.grade = "D"
        else:
            self.grade = "F"

        # Status
        if errors > 0:
            self.status = "FAIL"
            self.success = False
        elif warnings > 0:
            self.status = "WARN"
        else:
            self.status = "PASS"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "engine_id": self.engine_id,
            "success": self.success,
            "status": self.status,
            "grade": self.grade,
            "score": round(self.score, 1),
            "source_language": self.source_language,
            "target_language": self.target_language,
            "rules_checked": self.rules_checked,
            "rules_passed": self.rules_passed,
            "rules_failed": self.rules_failed,
            "issues": [i.to_dict() for i in self.issues],
            "kpi_drift_results": [r.to_dict() for r in self.kpi_drift_results],
            "semantic_drift_results": [r.to_dict() for r in self.semantic_drift_results],
            "terminology_mappings_checked": len(self.terminology_mappings),
            "warnings": self.warnings,
            "timestamp": self.timestamp,
        }


# =============================================================================
# CROSS-LANGUAGE CONSISTENCY ENGINE
# =============================================================================

class CrossLanguageConsistencyEngine:
    """
    N4.2: Cross-Language Consistency Engine (G22-X).

    Validates consistency between translated versions of reports:
    - KPI values must be identical
    - Executive summaries must have minimal semantic drift
    - Roadmap actions must maintain meaning
    - Terminology must be coherently mapped
    """

    def __init__(
        self,
        source_sections: SectionDict,
        target_sections: SectionDict,
        briefing: BriefingDict,
        source_language: str = "de",
        target_language: str = "en",
    ) -> None:
        """
        Initialize Cross-Language Consistency Engine.

        Args:
            source_sections: Original language sections
            target_sections: Translated language sections
            briefing: Briefing data
            source_language: Source language code
            target_language: Target language code
        """
        self.source_sections = source_sections
        self.target_sections = target_sections
        self.briefing = briefing

        try:
            self._source_lang = SupportedLanguage(source_language.lower())
        except ValueError:
            self._source_lang = SupportedLanguage.DE

        try:
            self._target_lang = SupportedLanguage(target_language.lower())
        except ValueError:
            self._target_lang = SupportedLanguage.EN

        self._report = G22XReport(
            source_language=self._source_lang.value,
            target_language=self._target_lang.value,
        )

        # Load glossaries
        self._source_glossary = CONSULTING_GLOSSARY.get(
            self._source_lang, CONSULTING_GLOSSARY[SupportedLanguage.DE]
        )
        self._target_glossary = CONSULTING_GLOSSARY.get(
            self._target_lang, CONSULTING_GLOSSARY[SupportedLanguage.EN]
        )

        log.info(
            "[G22-X] Engine initialized: %s → %s",
            self._source_lang.value,
            self._target_lang.value,
        )

    def check_all(self) -> G22XReport:
        """
        Run all G22-X cross-language consistency checks.

        Returns:
            G22XReport with all findings
        """
        log.info("[G22-X] Starting cross-language consistency check...")

        # Skip if same language
        if self._source_lang == self._target_lang:
            log.info("[G22-X] Same language, skipping cross-language checks")
            return self._report

        # G22-X001: KPI Consistency
        self._check_kpi_consistency()

        # G22-X002: Executive Summary Drift
        self._check_executive_summary_drift()

        # G22-X003: Roadmap Drift
        self._check_roadmap_drift()

        # G22-X004: Terminology Coherence
        self._check_terminology_coherence()

        log.info(
            "[G22-X] Check complete: status=%s, grade=%s, score=%.1f",
            self._report.status,
            self._report.grade,
            self._report.score,
        )

        return self._report

    def _check_kpi_consistency(self) -> None:
        """
        G22-X001: Check KPI values are identical across languages.

        KPIs (numbers) should never change in translation.
        """
        self._report.rules_checked += 1
        log.debug("[G22-X001] Checking KPI consistency...")

        for kpi_field in CRITICAL_KPI_FIELDS:
            # Check briefing-level KPIs
            source_value = self._extract_kpi_from_briefing(kpi_field, self.source_sections)
            target_value = self._extract_kpi_from_briefing(kpi_field, self.target_sections)

            if source_value is None and target_value is None:
                continue

            result = KPIDriftResult(
                kpi_name=kpi_field,
                source_value=source_value,
                target_value=target_value,
                source_language=self._source_lang,
                target_language=self._target_lang,
            )

            if source_value is not None and target_value is not None:
                # Calculate drift
                if source_value != 0:
                    drift_pct = abs(target_value - source_value) / abs(source_value)
                else:
                    drift_pct = 0.0 if target_value == 0 else 1.0

                result.drift_absolute = abs(target_value - source_value)
                result.drift_percentage = drift_pct

                if drift_pct > MAX_KPI_VARIANCE:
                    result.is_consistent = False
                    self._report.add_issue(G22XIssue(
                        rule_id=G22XRule.X001_KPI_CONSISTENCY,
                        severity=G22XIssueSeverity.ERROR,
                        source_language=self._source_lang,
                        target_language=self._target_lang,
                        section="kpis",
                        message=f"KPI '{kpi_field}' changed during translation",
                        expected=source_value,
                        actual=target_value,
                        drift_value=drift_pct,
                        suggestion="KPI values must be identical in all languages",
                    ))
            elif source_value is not None:
                # Missing in target
                result.is_consistent = False
                self._report.add_issue(G22XIssue(
                    rule_id=G22XRule.X001_KPI_CONSISTENCY,
                    severity=G22XIssueSeverity.WARNING,
                    source_language=self._source_lang,
                    target_language=self._target_lang,
                    section="kpis",
                    message=f"KPI '{kpi_field}' missing in translated version",
                    expected=source_value,
                    actual=None,
                    suggestion="Ensure all KPIs are preserved in translation",
                ))

            self._report.kpi_drift_results.append(result)

        # Also check KPIs in section content
        self._check_kpis_in_sections()

    def _check_kpis_in_sections(self) -> None:
        """Check KPIs within section content."""
        kpi_sections = ["executive_summary", "business_case", "ki_stack_summary"]

        for section_key in kpi_sections:
            source_content = self._get_section_content(section_key, self.source_sections)
            target_content = self._get_section_content(section_key, self.target_sections)

            if not source_content or not target_content:
                continue

            # Extract numbers from both
            source_numbers = self._extract_numbers(source_content)
            target_numbers = self._extract_numbers(target_content)

            # Check for missing numbers
            missing = set(source_numbers) - set(target_numbers)
            if missing:
                self._report.add_issue(G22XIssue(
                    rule_id=G22XRule.X001_KPI_CONSISTENCY,
                    severity=G22XIssueSeverity.WARNING,
                    source_language=self._source_lang,
                    target_language=self._target_lang,
                    section=section_key,
                    message=f"Numbers missing in translation: {', '.join(list(missing)[:3])}",
                    expected=f"{len(source_numbers)} numbers",
                    actual=f"{len(target_numbers)} numbers",
                    suggestion="Ensure all numeric values are preserved",
                ))

    def _check_executive_summary_drift(self) -> None:
        """
        G22-X002: Check Executive Summary semantic drift ≤ 0.08.

        Executive content must maintain meaning within 8% drift.
        """
        self._report.rules_checked += 1
        log.debug("[G22-X002] Checking Executive Summary drift...")

        for section_key in EXECUTIVE_SECTIONS:
            source_content = self._get_section_content(section_key, self.source_sections)
            target_content = self._get_section_content(section_key, self.target_sections)

            if not source_content or not target_content:
                continue

            drift_result = self._calculate_semantic_drift(
                section_key,
                source_content,
                target_content,
                MAX_EXEC_SUMMARY_DRIFT,
            )

            self._report.semantic_drift_results.append(drift_result)

            if not drift_result.is_within_threshold:
                self._report.add_issue(G22XIssue(
                    rule_id=G22XRule.X002_EXEC_SUMMARY_DRIFT,
                    severity=G22XIssueSeverity.ERROR,
                    source_language=self._source_lang,
                    target_language=self._target_lang,
                    section=section_key,
                    message=f"Executive Summary drift {drift_result.drift_value:.2%} exceeds threshold {MAX_EXEC_SUMMARY_DRIFT:.2%}",
                    expected=f"≤ {MAX_EXEC_SUMMARY_DRIFT:.2%} drift",
                    actual=f"{drift_result.drift_value:.2%} drift",
                    drift_value=drift_result.drift_value,
                    suggestion="Review translation for meaning preservation",
                ))

    def _check_roadmap_drift(self) -> None:
        """
        G22-X003: Check Roadmap action drift ≤ 0.05.

        Roadmap actions must maintain meaning within 5% drift.
        """
        self._report.rules_checked += 1
        log.debug("[G22-X003] Checking Roadmap drift...")

        for section_key in ROADMAP_SECTIONS:
            source_content = self._get_section_content(section_key, self.source_sections)
            target_content = self._get_section_content(section_key, self.target_sections)

            if not source_content or not target_content:
                continue

            drift_result = self._calculate_semantic_drift(
                section_key,
                source_content,
                target_content,
                MAX_ROADMAP_DRIFT,
            )

            self._report.semantic_drift_results.append(drift_result)

            if not drift_result.is_within_threshold:
                self._report.add_issue(G22XIssue(
                    rule_id=G22XRule.X003_ROADMAP_DRIFT,
                    severity=G22XIssueSeverity.ERROR,
                    source_language=self._source_lang,
                    target_language=self._target_lang,
                    section=section_key,
                    message=f"Roadmap drift {drift_result.drift_value:.2%} exceeds threshold {MAX_ROADMAP_DRIFT:.2%}",
                    expected=f"≤ {MAX_ROADMAP_DRIFT:.2%} drift",
                    actual=f"{drift_result.drift_value:.2%} drift",
                    drift_value=drift_result.drift_value,
                    suggestion="Review roadmap actions for action verb preservation",
                ))

    def _check_terminology_coherence(self) -> None:
        """
        G22-X004: Check terminology coherence via glossary mapping.

        All glossary terms must be consistently translated.
        """
        self._report.rules_checked += 1
        log.debug("[G22-X004] Checking terminology coherence...")

        # Build term mappings
        for term_key in self._source_glossary:
            source_term = self._source_glossary.get(term_key, term_key)
            target_term = self._target_glossary.get(term_key, term_key)

            mapping = TerminologyMapping(
                term_key=term_key,
                category="consulting",
                source_term=source_term,
                target_term=target_term,
                source_language=self._source_lang,
                target_language=self._target_lang,
            )

            # Check if terms appear in content
            source_found = False
            target_found = False

            for section_key in self.source_sections:
                if section_key.startswith("_"):
                    continue

                source_content = self._get_section_content(section_key, self.source_sections)
                target_content = self._get_section_content(section_key, self.target_sections)

                if source_content and source_term.lower() in source_content.lower():
                    source_found = True
                    mapping.found_in_source = True

                if target_content and target_term.lower() in target_content.lower():
                    target_found = True
                    mapping.found_in_target = True

            # Check coherence
            if source_found:
                if target_found:
                    mapping.correctly_mapped = True
                else:
                    # Term found in source but not properly translated
                    self._report.add_issue(G22XIssue(
                        rule_id=G22XRule.X004_TERMINOLOGY_COHERENCE,
                        severity=G22XIssueSeverity.WARNING,
                        source_language=self._source_lang,
                        target_language=self._target_lang,
                        section="terminology",
                        message=f"Term '{source_term}' not found as '{target_term}' in translation",
                        expected=target_term,
                        actual="not found",
                        suggestion=f"Use consistent terminology: '{source_term}' → '{target_term}'",
                    ))

            self._report.terminology_mappings.append(mapping)

    def _get_section_content(
        self,
        section_key: str,
        sections: SectionDict,
    ) -> Optional[str]:
        """Get section content with fallback key variants."""
        # Try exact key
        content = sections.get(section_key)
        if content and isinstance(content, str):
            return content

        # Try HTML key variant
        html_key = f"{section_key.upper()}_HTML"
        content = sections.get(html_key)
        if content and isinstance(content, str):
            return content

        # Try lowercase
        content = sections.get(section_key.lower())
        if content and isinstance(content, str):
            return content

        return None

    def _extract_kpi_from_briefing(
        self,
        kpi_field: str,
        sections: SectionDict,
    ) -> Optional[float]:
        """Extract KPI value from sections or briefing."""
        # Check in _kpis dict
        kpis = sections.get("_kpis", {})
        if isinstance(kpis, dict) and kpi_field in kpis:
            val = kpis[kpi_field]
            try:
                return float(val)
            except (ValueError, TypeError):
                pass

        # Check in briefing
        val = self.briefing.get(kpi_field) or self.briefing.get(kpi_field.upper())
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                pass

        return None

    def _extract_numbers(self, text: str) -> List[str]:
        """Extract numeric values from text."""
        # Pattern for various number formats
        patterns = [
            r"(\d+(?:[.,]\d+)?)\s*%",  # Percentages
            r"(\d+(?:[.,]\d+)?)\s*(?:€|EUR|USD|\$)",  # Currency
            r"(\d+(?:[.,]\d+)?)\s*(?:Monate?|months?)",  # Months
            r"(\d+(?:[.,]\d+)?)\s*(?:Stunden?|hours?)",  # Hours
        ]

        numbers: List[str] = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            numbers.extend(matches)

        return numbers

    def _calculate_semantic_drift(
        self,
        section_key: str,
        source_text: str,
        target_text: str,
        threshold: float,
    ) -> SemanticDriftResult:
        """
        Calculate semantic drift between source and target text.

        Uses multiple heuristics:
        - Word overlap (Jaccard similarity)
        - Number preservation
        - Key phrase preservation
        """
        # Clean HTML if present
        source_clean = self._strip_html(source_text)
        target_clean = self._strip_html(target_text)

        # Calculate word-based similarity
        source_words = set(source_clean.lower().split())
        target_words = set(target_clean.lower().split())

        if not source_words or not target_words:
            return SemanticDriftResult(
                section=section_key,
                source_language=self._source_lang,
                target_language=self._target_lang,
                similarity_score=0.0,
                drift_value=1.0,
                threshold=threshold,
                is_within_threshold=False,
            )

        # Jaccard similarity for common vocabulary
        common = source_words & target_words
        total = source_words | target_words
        word_similarity = len(common) / len(total) if total else 0.0

        # Number preservation score
        source_numbers = set(self._extract_numbers(source_text))
        target_numbers = set(self._extract_numbers(target_text))

        if source_numbers:
            number_preservation = len(source_numbers & target_numbers) / len(source_numbers)
        else:
            number_preservation = 1.0

        # Key phrase preservation (glossary terms)
        source_terms_found = 0
        target_terms_found = 0

        for term_key, source_term in self._source_glossary.items():
            target_term = self._target_glossary.get(term_key, source_term)

            if source_term.lower() in source_clean.lower():
                source_terms_found += 1
                if target_term.lower() in target_clean.lower():
                    target_terms_found += 1

        term_preservation = (
            target_terms_found / source_terms_found
            if source_terms_found > 0
            else 1.0
        )

        # Combined similarity score
        similarity = (
            word_similarity * 0.3 +
            number_preservation * 0.4 +
            term_preservation * 0.3
        )

        drift = 1.0 - similarity
        issues: List[str] = []

        if number_preservation < 1.0:
            issues.append("Numbers not fully preserved")
        if term_preservation < 0.8:
            issues.append("Terminology mapping incomplete")

        return SemanticDriftResult(
            section=section_key,
            source_language=self._source_lang,
            target_language=self._target_lang,
            similarity_score=similarity,
            drift_value=drift,
            threshold=threshold,
            is_within_threshold=drift <= threshold,
            key_phrases_preserved=target_terms_found,
            key_phrases_total=source_terms_found,
            issues=issues,
        )

    def _strip_html(self, html: str) -> str:
        """Remove HTML tags from text."""
        if not html:
            return ""
        clean = re.sub(r"<[^>]+>", " ", html)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def check_cross_language_consistency(
    source_sections: SectionDict,
    target_sections: SectionDict,
    briefing: BriefingDict,
    source_language: str = "de",
    target_language: str = "en",
) -> G22XReport:
    """
    Check cross-language consistency between source and translated sections.

    Args:
        source_sections: Original language sections
        target_sections: Translated language sections
        briefing: Briefing data
        source_language: Source language code
        target_language: Target language code

    Returns:
        G22XReport with all findings
    """
    engine = CrossLanguageConsistencyEngine(
        source_sections=source_sections,
        target_sections=target_sections,
        briefing=briefing,
        source_language=source_language,
        target_language=target_language,
    )

    return engine.check_all()


def validate_kpi_cross_language(
    source_kpis: Dict[str, Any],
    target_kpis: Dict[str, Any],
    source_language: str = "de",
    target_language: str = "en",
) -> List[KPIDriftResult]:
    """
    Validate KPI consistency between languages.

    Args:
        source_kpis: Source language KPIs
        target_kpis: Target language KPIs
        source_language: Source language code
        target_language: Target language code

    Returns:
        List of KPI drift results
    """
    try:
        src_lang = SupportedLanguage(source_language.lower())
        tgt_lang = SupportedLanguage(target_language.lower())
    except ValueError:
        return []

    results: List[KPIDriftResult] = []

    for kpi_field in CRITICAL_KPI_FIELDS:
        source_val = source_kpis.get(kpi_field)
        target_val = target_kpis.get(kpi_field)

        if source_val is None and target_val is None:
            continue

        try:
            src_float = float(source_val) if source_val is not None else None
            tgt_float = float(target_val) if target_val is not None else None
        except (ValueError, TypeError):
            continue

        result = KPIDriftResult(
            kpi_name=kpi_field,
            source_value=src_float,
            target_value=tgt_float,
            source_language=src_lang,
            target_language=tgt_lang,
        )

        if src_float is not None and tgt_float is not None:
            result.drift_absolute = abs(tgt_float - src_float)
            if src_float != 0:
                result.drift_percentage = result.drift_absolute / abs(src_float)
            result.is_consistent = result.drift_percentage <= MAX_KPI_VARIANCE

        results.append(result)

    return results


def validate_executive_summary_drift(
    source_content: str,
    target_content: str,
    source_language: str = "de",
    target_language: str = "en",
) -> SemanticDriftResult:
    """
    Validate executive summary semantic drift.

    Args:
        source_content: Source language content
        target_content: Target language content
        source_language: Source language code
        target_language: Target language code

    Returns:
        SemanticDriftResult
    """
    engine = CrossLanguageConsistencyEngine(
        source_sections={"executive_summary": source_content},
        target_sections={"executive_summary": target_content},
        briefing={},
        source_language=source_language,
        target_language=target_language,
    )

    return engine._calculate_semantic_drift(
        "executive_summary",
        source_content,
        target_content,
        MAX_EXEC_SUMMARY_DRIFT,
    )


def validate_roadmap_drift(
    source_content: str,
    target_content: str,
    source_language: str = "de",
    target_language: str = "en",
) -> SemanticDriftResult:
    """
    Validate roadmap semantic drift.

    Args:
        source_content: Source language content
        target_content: Target language content
        source_language: Source language code
        target_language: Target language code

    Returns:
        SemanticDriftResult
    """
    engine = CrossLanguageConsistencyEngine(
        source_sections={"roadmap": source_content},
        target_sections={"roadmap": target_content},
        briefing={},
        source_language=source_language,
        target_language=target_language,
    )

    return engine._calculate_semantic_drift(
        "roadmap",
        source_content,
        target_content,
        MAX_ROADMAP_DRIFT,
    )


def validate_terminology_coherence(
    source_sections: SectionDict,
    target_sections: SectionDict,
    source_language: str = "de",
    target_language: str = "en",
) -> List[TerminologyMapping]:
    """
    Validate terminology coherence across languages.

    Args:
        source_sections: Source language sections
        target_sections: Target language sections
        source_language: Source language code
        target_language: Target language code

    Returns:
        List of terminology mappings
    """
    engine = CrossLanguageConsistencyEngine(
        source_sections=source_sections,
        target_sections=target_sections,
        briefing={},
        source_language=source_language,
        target_language=target_language,
    )

    engine._check_terminology_coherence()
    return engine._report.terminology_mappings
