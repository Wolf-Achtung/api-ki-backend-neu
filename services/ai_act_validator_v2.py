# -*- coding: utf-8 -*-
"""
Sprint G12: AI-Act Validator 2.0

Robust validation layer for AI Act compliance data:
- Risk level consistency validation
- Duty matrix completeness check
- Alerts/gaps idempotency verification
- Reasoning minimum length enforcement
- Persona prohibition in AI-Act sections
- Funding impact presence for high-risk

Version: 2.0.0 (Sprint G12)
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

log = logging.getLogger(__name__)

# =============================================================================
# ENV CONFIGURATION
# =============================================================================

AI_ACT_STRICT_VALIDATION = os.getenv("AI_ACT_STRICT_VALIDATION", "1").lower() in ("1", "true", "yes")
AI_ACT_REQUIRE_FUNDING_IMPACT = os.getenv("AI_ACT_REQUIRE_FUNDING_IMPACT", "1").lower() in ("1", "true", "yes")
AI_ACT_FAIL_ON_INCONSISTENCY = os.getenv("AI_ACT_FAIL_ON_INCONSISTENCY", "0").lower() in ("1", "true", "yes")
MIN_REASONING_WORDS = int(os.getenv("AI_ACT_MIN_REASONING_WORDS", "15"))


# =============================================================================
# VALIDATION RULES DATA
# =============================================================================

# Valid risk levels
VALID_RISK_LEVELS: Set[str] = {"none", "minimal", "limited", "high-risk"}

# Required duty matrix fields by risk level
REQUIRED_DUTIES_BY_RISK: Dict[str, List[str]] = {
    "high-risk": [
        "risk_management_system",
        "technical_documentation",
        "automatic_logging",
        "transparency",
        "human_oversight",
        "accuracy_robustness",
        "ce_conformity",
    ],
    "limited": [
        "transparency",
        "ai_labeling",
    ],
    "minimal": [],
    "none": [],
}

# Branches that typically indicate high-risk
HIGH_RISK_BRANCHES: Set[str] = {
    "finanz", "finance", "versicherung", "insurance", "kredit", "credit",
    "gesundheit", "health", "medizin", "medical", "pharma",
    "recht", "legal", "justiz", "justice",
    "hr", "personal", "recruiting", "bewerbung",
    "bildung", "education", "schule", "school",
    "polizei", "police", "sicherheit", "security", "überwachung", "surveillance",
}

# Use cases that indicate high-risk
HIGH_RISK_USE_CASES: Set[str] = {
    "scoring", "kredit", "credit", "bonitätsprüfung", "kreditwürdigkeit",
    "diagnose", "diagnosis", "behandlung", "treatment",
    "bewerbung", "recruiting", "einstellung", "hiring",
    "überwachung", "surveillance", "biometrie", "biometric",
    "entscheidung", "decision", "automatisiert", "automated",
}

# Persona patterns that should not appear in AI-Act sections
PERSONA_PATTERNS: List[str] = [
    r"\bich\s+(?:bin|war|werde|habe|hatte)\b",
    r"\bals\s+(?:ihr|euer|dein)\s+\w*berater\b",
    r"\bmein(?:e|er|es)?\s+empfehlung\b",
    r"\bwir\s+empfehlen\b",
    r"\bunser(?:e|er|es)?\s+(?:analyse|bewertung)\b",
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ValidationIssue:
    """A single validation issue."""
    code: str
    severity: str  # error, warning, info
    message: str
    field: str = ""
    expected: Any = None
    actual: Any = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
        }
        if self.field:
            result["field"] = self.field
        if self.expected is not None:
            result["expected"] = self.expected
        if self.actual is not None:
            result["actual"] = self.actual
        return result


@dataclass
class ValidationResult:
    """Complete validation result."""
    valid: bool = True
    score: int = 100  # 0-100 validation score
    issues: List[ValidationIssue] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, code: str, message: str, **kwargs: Any) -> None:
        self.issues.append(ValidationIssue(code=code, severity="error", message=message, **kwargs))
        self.valid = False
        self.score = max(0, self.score - 20)

    def add_warning(self, code: str, message: str, **kwargs: Any) -> None:
        self.issues.append(ValidationIssue(code=code, severity="warning", message=message, **kwargs))
        self.warnings.append(message)
        self.score = max(0, self.score - 5)

    def add_info(self, code: str, message: str, **kwargs: Any) -> None:
        self.issues.append(ValidationIssue(code=code, severity="info", message=message, **kwargs))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "score": self.score,
            "error_count": len([i for i in self.issues if i.severity == "error"]),
            "warning_count": len([i for i in self.issues if i.severity == "warning"]),
            "issues": [i.to_dict() for i in self.issues],
        }


# =============================================================================
# VALIDATOR IMPLEMENTATION
# =============================================================================

class AIActValidatorV2:
    """
    Comprehensive AI Act validation with business logic rules.

    Validates:
    1. Risk level consistency with use cases and branch
    2. Duty matrix completeness for risk level
    3. Alerts/gaps idempotency (no duplicates)
    4. Reasoning minimum word count
    5. No persona language in AI-Act sections
    6. Funding impact present for high-risk
    """

    def __init__(self) -> None:
        self._persona_regex = [re.compile(p, re.IGNORECASE) for p in PERSONA_PATTERNS]

    def validate(
        self,
        sections: Dict[str, Any],
        answers: Optional[Dict[str, Any]] = None,
        lang: str = "de",
    ) -> ValidationResult:
        """
        Validate AI Act data in sections.

        Args:
            sections: The report sections dict
            answers: Original user answers (for cross-validation)
            lang: Language code

        Returns:
            ValidationResult with issues and score
        """
        result = ValidationResult()

        if not AI_ACT_STRICT_VALIDATION:
            result.add_info("VALIDATION_DISABLED", "AI Act strict validation is disabled")
            return result

        # Extract AI Act data from sections
        risk_level = sections.get("AI_ACT_RISK_LEVEL", "").lower()
        reasoning = sections.get("AI_ACT_RISK_REASONING", "")
        duty_matrix = sections.get("AI_ACT_DUTY_MATRIX", {})
        alerts = sections.get("AI_ACT_ALERTS", [])
        gaps = sections.get("AI_ACT_GAPS", [])
        summary = sections.get("AI_ACT_SUMMARY", "")
        funding_impact = sections.get("AI_ACT_FUNDING_IMPACT", "")
        branch = sections.get("BRANCH_LABEL", "")
        use_cases = sections.get("USE_CASE_LABELS", [])

        # 1. Validate risk level value
        self._validate_risk_level(result, risk_level)

        # 2. Validate risk level consistency
        self._validate_risk_consistency(result, risk_level, branch, use_cases, sections)

        # 3. Validate duty matrix completeness
        self._validate_duty_matrix(result, risk_level, duty_matrix)

        # 4. Validate alerts/gaps idempotency
        self._validate_alerts_gaps(result, alerts, gaps)

        # 5. Validate reasoning length
        self._validate_reasoning(result, reasoning)

        # 6. Check for persona in AI Act sections
        self._validate_no_persona(result, summary, reasoning)

        # 7. Validate funding impact for high-risk
        self._validate_funding_impact(result, risk_level, funding_impact)

        # Log validation result
        if not result.valid:
            log.warning(
                "[G12-Validator] AI Act validation failed: %d errors, %d warnings",
                len([i for i in result.issues if i.severity == "error"]),
                len([i for i in result.issues if i.severity == "warning"]),
            )

        return result

    def _validate_risk_level(self, result: ValidationResult, risk_level: str) -> None:
        """Validate risk level is a valid value."""
        if not risk_level:
            result.add_error(
                "MISSING_RISK_LEVEL",
                "AI Act risk level is missing",
                field="AI_ACT_RISK_LEVEL",
            )
        elif risk_level not in VALID_RISK_LEVELS:
            result.add_error(
                "INVALID_RISK_LEVEL",
                f"Invalid risk level: {risk_level}",
                field="AI_ACT_RISK_LEVEL",
                expected=list(VALID_RISK_LEVELS),
                actual=risk_level,
            )

    def _validate_risk_consistency(
        self,
        result: ValidationResult,
        risk_level: str,
        branch: str,
        use_cases: List[str],
        sections: Dict[str, Any],
    ) -> None:
        """Validate risk level is consistent with branch and use cases."""
        if not risk_level or risk_level not in VALID_RISK_LEVELS:
            return  # Already reported as error

        branch_lower = branch.lower() if branch else ""
        use_cases_lower = [u.lower() for u in (use_cases or [])]
        all_text = " ".join([branch_lower] + use_cases_lower)

        # Check if high-risk indicators are present
        has_high_risk_branch = any(hrb in branch_lower for hrb in HIGH_RISK_BRANCHES)
        has_high_risk_use_case = any(
            hru in all_text for hru in HIGH_RISK_USE_CASES
        )

        # High-risk indicators but not classified as high-risk
        if (has_high_risk_branch or has_high_risk_use_case) and risk_level == "minimal":
            result.add_warning(
                "RISK_LEVEL_TOO_LOW",
                f"Risk level 'minimal' may be too low for branch '{branch}' with these use cases",
                field="AI_ACT_RISK_LEVEL",
                expected="limited or high-risk",
                actual=risk_level,
            )

        # High-risk classification without clear indicators
        if risk_level == "high-risk" and not has_high_risk_branch and not has_high_risk_use_case:
            result.add_info(
                "HIGH_RISK_WITHOUT_INDICATORS",
                "High-risk classification without typical high-risk indicators",
                field="AI_ACT_RISK_LEVEL",
            )

    def _validate_duty_matrix(
        self,
        result: ValidationResult,
        risk_level: str,
        duty_matrix: Dict[str, Any],
    ) -> None:
        """Validate duty matrix is complete for risk level."""
        if not risk_level or risk_level not in VALID_RISK_LEVELS:
            return

        required = REQUIRED_DUTIES_BY_RISK.get(risk_level, [])
        if not required:
            return  # No required duties for this risk level

        # Check if duty matrix is present
        if not duty_matrix:
            if risk_level in ("high-risk", "limited"):
                result.add_error(
                    "MISSING_DUTY_MATRIX",
                    f"Duty matrix is required for risk level '{risk_level}'",
                    field="AI_ACT_DUTY_MATRIX",
                )
            return

        # Check for missing required fields
        matrix_keys = {k.lower().replace("-", "_").replace(" ", "_") for k in duty_matrix.keys()}
        for duty in required:
            duty_normalized = duty.lower().replace("-", "_").replace(" ", "_")
            if duty_normalized not in matrix_keys:
                result.add_warning(
                    "MISSING_DUTY",
                    f"Required duty '{duty}' not found in duty matrix",
                    field="AI_ACT_DUTY_MATRIX",
                    expected=duty,
                )

    def _validate_alerts_gaps(
        self,
        result: ValidationResult,
        alerts: List[Any],
        gaps: List[Any],
    ) -> None:
        """Validate alerts and gaps are unique (idempotent)."""
        # Check for duplicate alerts
        if alerts:
            alert_texts = []
            for alert in alerts:
                if isinstance(alert, dict):
                    text = alert.get("text", "") or alert.get("message", "") or str(alert)
                else:
                    text = str(alert)
                alert_texts.append(text.strip().lower()[:100])

            if len(alert_texts) != len(set(alert_texts)):
                result.add_warning(
                    "DUPLICATE_ALERTS",
                    "Duplicate alerts detected",
                    field="AI_ACT_ALERTS",
                )

        # Check for duplicate gaps
        if gaps:
            gap_texts = []
            for gap in gaps:
                if isinstance(gap, dict):
                    text = gap.get("text", "") or gap.get("description", "") or str(gap)
                else:
                    text = str(gap)
                gap_texts.append(text.strip().lower()[:100])

            if len(gap_texts) != len(set(gap_texts)):
                result.add_warning(
                    "DUPLICATE_GAPS",
                    "Duplicate gaps detected",
                    field="AI_ACT_GAPS",
                )

    def _validate_reasoning(self, result: ValidationResult, reasoning: str) -> None:
        """Validate reasoning has minimum word count."""
        if not reasoning:
            result.add_error(
                "MISSING_REASONING",
                "AI Act risk reasoning is missing",
                field="AI_ACT_RISK_REASONING",
            )
            return

        word_count = len(reasoning.split())
        if word_count < MIN_REASONING_WORDS:
            result.add_warning(
                "INSUFFICIENT_REASONING",
                f"Risk reasoning too short: {word_count} words (minimum: {MIN_REASONING_WORDS})",
                field="AI_ACT_RISK_REASONING",
                expected=f">= {MIN_REASONING_WORDS} words",
                actual=f"{word_count} words",
            )

    def _validate_no_persona(
        self,
        result: ValidationResult,
        summary: str,
        reasoning: str,
    ) -> None:
        """Validate no persona language in AI Act sections."""
        texts_to_check = [
            ("AI_ACT_SUMMARY", summary),
            ("AI_ACT_RISK_REASONING", reasoning),
        ]

        for field_name, text in texts_to_check:
            if not text:
                continue

            for pattern in self._persona_regex:
                match = pattern.search(text)
                if match:
                    result.add_warning(
                        "PERSONA_IN_AI_ACT",
                        f"Persona language detected in {field_name}: '{match.group()}'",
                        field=field_name,
                        actual=match.group(),
                    )
                    break  # Only report first match per field

    def _validate_funding_impact(
        self,
        result: ValidationResult,
        risk_level: str,
        funding_impact: str,
    ) -> None:
        """Validate funding impact is present for high-risk."""
        if not AI_ACT_REQUIRE_FUNDING_IMPACT:
            return

        if risk_level == "high-risk":
            if not funding_impact or len(funding_impact.strip()) < 10:
                result.add_warning(
                    "MISSING_FUNDING_IMPACT",
                    "Funding impact statement recommended for high-risk classification",
                    field="AI_ACT_FUNDING_IMPACT",
                )


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_validator_instance: Optional[AIActValidatorV2] = None


def get_ai_act_validator() -> AIActValidatorV2:
    """Get singleton validator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = AIActValidatorV2()
    return _validator_instance


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def validate_ai_act_data(
    sections: Dict[str, Any],
    answers: Optional[Dict[str, Any]] = None,
    lang: str = "de",
) -> ValidationResult:
    """
    Convenience function to validate AI Act data.

    Returns ValidationResult with issues and score.
    """
    return get_ai_act_validator().validate(sections, answers, lang)


def check_ai_act_consistency(sections: Dict[str, Any]) -> bool:
    """
    Quick check if AI Act data is consistent.

    Returns True if valid, False if critical issues found.
    """
    result = validate_ai_act_data(sections)
    return result.valid


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[G12] AI Act Validator v2 loaded - strict=%s require_funding=%s fail_on_error=%s min_words=%d",
    AI_ACT_STRICT_VALIDATION,
    AI_ACT_REQUIRE_FUNDING_IMPACT,
    AI_ACT_FAIL_ON_INCONSISTENCY,
    MIN_REASONING_WORDS,
)
