# -*- coding: utf-8 -*-
"""
SPRINT N3.9 PACKAGE D: Safety & Compliance Auto-Tuner.

Auto-adjusts KI-Act parameters based on context:
- High-risk scenarios: Enhanced reasoning requirements
- Sensitive data: Strict fallback mode
- Consulting reports: Increased governance weight
- DSGVO-Strict Mode: Automatic anonymization

Version: 1.0.0 (N3.9 - PLATIN++ v4.28)
"""
from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Pattern, Set, Tuple

log = logging.getLogger(__name__)

# Type aliases
ConfigDict = Dict[str, Any]


# =============================================================================
# CONFIGURATION
# =============================================================================

class RiskLevel(Enum):
    """AI Act risk classification levels."""
    MINIMAL = "minimal"
    LIMITED = "limited"
    HIGH = "high"
    UNACCEPTABLE = "unacceptable"


class DataSensitivity(Enum):
    """Data sensitivity classification."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PII = "pii"


class ReportType(Enum):
    """Report type classification."""
    STANDARD = "standard"
    CONSULTING = "consulting"
    EXECUTIVE = "executive"
    REGULATORY = "regulatory"
    AUDIT = "audit"


class ComplianceMode(Enum):
    """Compliance mode settings."""
    STANDARD = "standard"
    STRICT = "strict"
    DSGVO_STRICT = "dsgvo_strict"
    KI_ACT_HIGH = "ki_act_high"
    FULL_COMPLIANCE = "full_compliance"


# Base AI Act parameters
BASE_AI_ACT_PARAMS: ConfigDict = {
    "min_reasoning_words": 150,
    "min_explanation_depth": 2,
    "require_fallback_documentation": True,
    "require_model_transparency": True,
    "governance_weight": 1.0,
    "human_oversight_level": 1,
}

# Risk level adjustments
RISK_LEVEL_ADJUSTMENTS: Dict[str, ConfigDict] = {
    "minimal": {
        "reasoning_multiplier": 1.0,
        "governance_weight_bonus": 0.0,
        "require_human_review": False,
        "enhanced_audit": False,
    },
    "limited": {
        "reasoning_multiplier": 1.1,
        "governance_weight_bonus": 0.05,
        "require_human_review": False,
        "enhanced_audit": True,
    },
    "high": {
        "reasoning_multiplier": 1.2,  # +20% reasoning
        "governance_weight_bonus": 0.15,  # +15% governance weight
        "require_human_review": True,
        "enhanced_audit": True,
    },
    "unacceptable": {
        "reasoning_multiplier": 1.5,
        "governance_weight_bonus": 0.30,
        "require_human_review": True,
        "enhanced_audit": True,
    },
}

# Report type adjustments
REPORT_TYPE_ADJUSTMENTS: Dict[str, ConfigDict] = {
    "standard": {
        "governance_weight_bonus": 0.0,
        "formality_level": "standard",
        "require_executive_summary": True,
    },
    "consulting": {
        "governance_weight_bonus": 0.15,  # +15% for consulting
        "formality_level": "formal",
        "require_executive_summary": True,
    },
    "executive": {
        "governance_weight_bonus": 0.10,
        "formality_level": "executive",
        "require_executive_summary": True,
    },
    "regulatory": {
        "governance_weight_bonus": 0.25,
        "formality_level": "formal",
        "require_executive_summary": True,
    },
    "audit": {
        "governance_weight_bonus": 0.20,
        "formality_level": "formal",
        "require_executive_summary": True,
    },
}

# Sensitive data patterns (DSGVO/GDPR)
SENSITIVE_PATTERNS: Dict[str, str] = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone_de": r"(\+49|0049|0)\s*[\d\s/\-]{6,14}\d",
    "iban": r"[A-Z]{2}\d{2}\s*[\dA-Z\s]{12,30}",
    "personal_id": r"\b\d{2}[\.\s]?\d{2}[\.\s]?\d{2}[\.\s\-]?\d{3,5}\b",
    "credit_card": r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b",
    "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    "name_prefix": r"\b(Herr|Frau|Dr\.|Prof\.)\s+[A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+\b",
    "date_of_birth": r"\b\d{1,2}[\.\-/]\d{1,2}[\.\-/]\d{2,4}\b",
}

# Compiled patterns
COMPILED_PATTERNS: Dict[str, Pattern[str]] = {
    name: re.compile(pattern, re.IGNORECASE)
    for name, pattern in SENSITIVE_PATTERNS.items()
}

# Entity masking replacements
ENTITY_MASKS: Dict[str, str] = {
    "email": "[EMAIL REDACTED]",
    "phone_de": "[PHONE REDACTED]",
    "iban": "[IBAN REDACTED]",
    "personal_id": "[ID REDACTED]",
    "credit_card": "[CARD REDACTED]",
    "ip_address": "[IP REDACTED]",
    "name_prefix": "[NAME REDACTED]",
    "date_of_birth": "[DOB REDACTED]",
}

# High-risk industry indicators
HIGH_RISK_INDUSTRIES: Set[str] = {
    "healthcare", "gesundheit", "medizin", "pharma",
    "finance", "finanz", "banking", "bank", "versicherung",
    "legal", "recht", "anwalt", "justiz",
    "government", "regierung", "behörde", "öffentlich",
    "defense", "verteidigung", "military", "militär",
    "education", "bildung", "schule", "universität",
    "critical_infrastructure", "energie", "wasser", "verkehr",
}

# Sensitive data indicators
SENSITIVE_DATA_INDICATORS: Set[str] = {
    "personenbezogen", "personal", "mitarbeiter", "employee",
    "kunde", "customer", "patient", "klient",
    "gehalt", "salary", "lohn", "vergütung",
    "gesundheit", "health", "krankheit", "diagnose",
    "finanzdaten", "financial", "konto", "account",
    "passwort", "password", "zugangsdaten", "credential",
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class SafetyContext:
    """Context for safety tuning decisions."""
    risk_level: RiskLevel = RiskLevel.MINIMAL
    data_sensitivity: DataSensitivity = DataSensitivity.INTERNAL
    report_type: ReportType = ReportType.STANDARD
    compliance_mode: ComplianceMode = ComplianceMode.STANDARD
    industry: str = ""
    contains_pii: bool = False
    requires_anonymization: bool = False
    detected_patterns: List[str] = field(default_factory=list)

    def to_dict(self) -> ConfigDict:
        """Convert to dictionary."""
        return {
            "risk_level": self.risk_level.value,
            "data_sensitivity": self.data_sensitivity.value,
            "report_type": self.report_type.value,
            "compliance_mode": self.compliance_mode.value,
            "industry": self.industry,
            "contains_pii": self.contains_pii,
            "requires_anonymization": self.requires_anonymization,
            "detected_patterns": self.detected_patterns,
        }


@dataclass
class TunedParameters:
    """Tuned safety parameters."""
    min_reasoning_words: int = 150
    reasoning_multiplier: float = 1.0
    governance_weight: float = 1.0
    human_oversight_level: int = 1
    require_human_review: bool = False
    require_fallback_documentation: bool = True
    require_model_transparency: bool = True
    enhanced_audit: bool = False
    fallback_strict_mode: bool = False
    anonymization_enabled: bool = False
    formality_level: str = "standard"
    compliance_mode: str = "standard"

    def to_dict(self) -> ConfigDict:
        """Convert to dictionary."""
        return {
            "min_reasoning_words": self.min_reasoning_words,
            "reasoning_multiplier": self.reasoning_multiplier,
            "governance_weight": round(self.governance_weight, 2),
            "human_oversight_level": self.human_oversight_level,
            "require_human_review": self.require_human_review,
            "require_fallback_documentation": self.require_fallback_documentation,
            "require_model_transparency": self.require_model_transparency,
            "enhanced_audit": self.enhanced_audit,
            "fallback_strict_mode": self.fallback_strict_mode,
            "anonymization_enabled": self.anonymization_enabled,
            "formality_level": self.formality_level,
            "compliance_mode": self.compliance_mode,
        }


@dataclass
class AnonymizationResult:
    """Result of anonymization operation."""
    original_hash: str = ""
    anonymized_text: str = ""
    patterns_found: Dict[str, int] = field(default_factory=dict)
    total_redactions: int = 0
    processing_time_ms: int = 0

    def to_dict(self) -> ConfigDict:
        """Convert to dictionary."""
        return {
            "original_hash": self.original_hash,
            "patterns_found": self.patterns_found,
            "total_redactions": self.total_redactions,
            "processing_time_ms": self.processing_time_ms,
        }


@dataclass
class SafetyTuningReport:
    """Report of safety tuning operations."""
    context: SafetyContext = field(default_factory=SafetyContext)
    parameters: TunedParameters = field(default_factory=TunedParameters)
    adjustments_applied: List[str] = field(default_factory=list)
    anonymization_results: List[AnonymizationResult] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> ConfigDict:
        """Convert to dictionary."""
        return {
            "context": self.context.to_dict(),
            "parameters": self.parameters.to_dict(),
            "adjustments_applied": self.adjustments_applied,
            "anonymization_results": [r.to_dict() for r in self.anonymization_results],
            "warnings": self.warnings,
            "timestamp": self.timestamp,
        }


# =============================================================================
# DETECTION FUNCTIONS
# =============================================================================

def detect_risk_level(briefing: ConfigDict) -> RiskLevel:
    """
    Detect AI Act risk level from briefing.

    Args:
        briefing: Report briefing data

    Returns:
        Detected risk level
    """
    industry = briefing.get("branch", "").lower()
    use_case = briefing.get("use_case", "").lower()
    employees = briefing.get("employees", 0)

    # Check for high-risk industry
    for indicator in HIGH_RISK_INDUSTRIES:
        if indicator in industry:
            log.debug("[N3.9-Safety] High-risk industry detected: %s", indicator)
            return RiskLevel.HIGH

    # Check use case indicators
    high_risk_use_cases = {"entscheidung", "decision", "hiring", "einstellung", "kredit", "credit"}
    for indicator in high_risk_use_cases:
        if indicator in use_case:
            log.debug("[N3.9-Safety] High-risk use case detected: %s", indicator)
            return RiskLevel.HIGH

    # Large enterprises have higher scrutiny
    if employees > 1000:
        return RiskLevel.LIMITED

    return RiskLevel.MINIMAL


def detect_data_sensitivity(briefing: ConfigDict, text_content: str = "") -> DataSensitivity:
    """
    Detect data sensitivity level.

    Args:
        briefing: Report briefing data
        text_content: Optional text content to scan

    Returns:
        Detected sensitivity level
    """
    combined_text = f"{briefing.get('description', '')} {text_content}".lower()

    # Check for PII indicators
    for indicator in SENSITIVE_DATA_INDICATORS:
        if indicator in combined_text:
            log.debug("[N3.9-Safety] Sensitive data indicator found: %s", indicator)
            return DataSensitivity.PII

    # Check for restricted industry data
    industry = briefing.get("branch", "").lower()
    restricted_industries = {"healthcare", "gesundheit", "legal", "recht", "finance", "finanz"}
    for ind in restricted_industries:
        if ind in industry:
            return DataSensitivity.CONFIDENTIAL

    return DataSensitivity.INTERNAL


def detect_report_type(briefing: ConfigDict) -> ReportType:
    """
    Detect report type from briefing.

    Args:
        briefing: Report briefing data

    Returns:
        Detected report type
    """
    report_purpose = briefing.get("report_purpose", "").lower()
    audience = briefing.get("audience", "").lower()

    if any(w in report_purpose for w in ["audit", "prüfung"]):
        return ReportType.AUDIT

    if any(w in report_purpose for w in ["regulatory", "regulierung", "compliance"]):
        return ReportType.REGULATORY

    if any(w in audience for w in ["board", "vorstand", "c-level", "executive"]):
        return ReportType.EXECUTIVE

    if any(w in audience for w in ["consulting", "beratung", "externe"]):
        return ReportType.CONSULTING

    return ReportType.STANDARD


def detect_pii_patterns(text: str) -> Dict[str, List[str]]:
    """
    Detect PII patterns in text.

    Args:
        text: Text to scan

    Returns:
        Dictionary of pattern types to matched strings
    """
    findings: Dict[str, List[str]] = {}

    for pattern_name, pattern in COMPILED_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            findings[pattern_name] = list(set(matches))

    return findings


# =============================================================================
# SAFETY TUNER
# =============================================================================

class SafetyTuner:
    """
    Main Safety & Compliance Auto-Tuner.

    Automatically adjusts KI-Act parameters based on:
    - Risk level detection
    - Data sensitivity classification
    - Report type requirements
    - DSGVO compliance needs
    """

    _instance: Optional["SafetyTuner"] = None

    def __new__(cls) -> "SafetyTuner":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def analyze_context(
        self,
        briefing: ConfigDict,
        sections: Optional[Dict[str, Any]] = None,
    ) -> SafetyContext:
        """
        Analyze briefing and sections to determine safety context.

        Args:
            briefing: Report briefing data
            sections: Optional report sections

        Returns:
            SafetyContext with detected parameters
        """
        # Detect risk level
        risk_level = detect_risk_level(briefing)

        # Detect data sensitivity
        text_content = ""
        if sections:
            for key, value in sections.items():
                if isinstance(value, str):
                    text_content += f" {value}"

        data_sensitivity = detect_data_sensitivity(briefing, text_content)

        # Detect report type
        report_type = detect_report_type(briefing)

        # Determine compliance mode
        if risk_level == RiskLevel.HIGH:
            compliance_mode = ComplianceMode.KI_ACT_HIGH
        elif data_sensitivity in (DataSensitivity.PII, DataSensitivity.RESTRICTED):
            compliance_mode = ComplianceMode.DSGVO_STRICT
        elif report_type in (ReportType.REGULATORY, ReportType.AUDIT):
            compliance_mode = ComplianceMode.FULL_COMPLIANCE
        elif report_type == ReportType.CONSULTING:
            compliance_mode = ComplianceMode.STRICT
        else:
            compliance_mode = ComplianceMode.STANDARD

        # Check for PII
        detected_patterns = []
        if text_content:
            pii_findings = detect_pii_patterns(text_content)
            detected_patterns = list(pii_findings.keys())

        contains_pii = len(detected_patterns) > 0 or data_sensitivity == DataSensitivity.PII
        requires_anonymization = contains_pii and compliance_mode in (
            ComplianceMode.DSGVO_STRICT,
            ComplianceMode.FULL_COMPLIANCE,
        )

        context = SafetyContext(
            risk_level=risk_level,
            data_sensitivity=data_sensitivity,
            report_type=report_type,
            compliance_mode=compliance_mode,
            industry=briefing.get("branch", ""),
            contains_pii=contains_pii,
            requires_anonymization=requires_anonymization,
            detected_patterns=detected_patterns,
        )

        log.info(
            "[N3.9-Safety] Context analyzed: risk=%s, sensitivity=%s, mode=%s",
            risk_level.value,
            data_sensitivity.value,
            compliance_mode.value,
        )

        return context

    def tune_parameters(self, context: SafetyContext) -> TunedParameters:
        """
        Tune safety parameters based on context.

        Args:
            context: Safety context

        Returns:
            Tuned parameters
        """
        params = TunedParameters()
        params.compliance_mode = context.compliance_mode.value

        # Apply risk level adjustments
        risk_adj = RISK_LEVEL_ADJUSTMENTS.get(
            context.risk_level.value,
            RISK_LEVEL_ADJUSTMENTS["minimal"],
        )
        params.reasoning_multiplier = risk_adj["reasoning_multiplier"]
        params.governance_weight += risk_adj["governance_weight_bonus"]
        params.require_human_review = risk_adj["require_human_review"]
        params.enhanced_audit = risk_adj["enhanced_audit"]

        # Apply report type adjustments
        type_adj = REPORT_TYPE_ADJUSTMENTS.get(
            context.report_type.value,
            REPORT_TYPE_ADJUSTMENTS["standard"],
        )
        params.governance_weight += type_adj["governance_weight_bonus"]
        params.formality_level = type_adj["formality_level"]

        # Apply sensitivity adjustments
        if context.data_sensitivity in (DataSensitivity.PII, DataSensitivity.RESTRICTED):
            params.fallback_strict_mode = True
            params.enhanced_audit = True

        # Apply compliance mode adjustments
        if context.compliance_mode == ComplianceMode.DSGVO_STRICT:
            params.anonymization_enabled = True
            params.fallback_strict_mode = True

        if context.compliance_mode == ComplianceMode.KI_ACT_HIGH:
            params.reasoning_multiplier *= 1.2  # Additional +20%
            params.human_oversight_level = 2

        if context.compliance_mode == ComplianceMode.FULL_COMPLIANCE:
            params.anonymization_enabled = True
            params.fallback_strict_mode = True
            params.enhanced_audit = True
            params.require_human_review = True

        # Calculate final reasoning requirement
        params.min_reasoning_words = int(
            BASE_AI_ACT_PARAMS["min_reasoning_words"] * params.reasoning_multiplier
        )

        log.info(
            "[N3.9-Safety] Parameters tuned: reasoning=%d (+%.0f%%), governance=%.2f",
            params.min_reasoning_words,
            (params.reasoning_multiplier - 1) * 100,
            params.governance_weight,
        )

        return params

    def process_safety_tuning(
        self,
        briefing: ConfigDict,
        sections: Optional[Dict[str, Any]] = None,
    ) -> SafetyTuningReport:
        """
        Full safety tuning process.

        Args:
            briefing: Report briefing data
            sections: Optional report sections

        Returns:
            Complete safety tuning report
        """
        report = SafetyTuningReport()

        # Analyze context
        context = self.analyze_context(briefing, sections)
        report.context = context

        # Tune parameters
        params = self.tune_parameters(context)
        report.parameters = params

        # Track adjustments
        if params.reasoning_multiplier > 1.0:
            report.adjustments_applied.append(
                f"Reasoning requirement increased by {int((params.reasoning_multiplier - 1) * 100)}%"
            )

        if params.governance_weight > 1.0:
            report.adjustments_applied.append(
                f"Governance weight increased to {params.governance_weight:.2f}"
            )

        if params.fallback_strict_mode:
            report.adjustments_applied.append("Fallback strict mode enabled")

        if params.anonymization_enabled:
            report.adjustments_applied.append("Anonymization enabled")

        if params.require_human_review:
            report.adjustments_applied.append("Human review required")

        # Add warnings if needed
        if context.risk_level == RiskLevel.HIGH:
            report.warnings.append(
                "High-risk AI application detected - ensure compliance with AI Act Article 6"
            )

        if context.contains_pii and not params.anonymization_enabled:
            report.warnings.append(
                "PII detected but anonymization not enabled - review DSGVO compliance"
            )

        return report


# Singleton instance
_tuner = SafetyTuner()


def get_safety_tuner() -> SafetyTuner:
    """Get the global safety tuner instance."""
    return _tuner


# =============================================================================
# ENTITY MASKING (ANONYMIZATION)
# =============================================================================

def entity_masking(text: str) -> AnonymizationResult:
    """
    Mask/anonymize PII entities in text.

    Args:
        text: Text to anonymize

    Returns:
        AnonymizationResult with anonymized text
    """
    import time
    start_time = time.time()

    result = AnonymizationResult()
    result.original_hash = hashlib.sha256(text.encode()).hexdigest()

    anonymized = text
    total_redactions = 0
    patterns_found: Dict[str, int] = {}

    for pattern_name, pattern in COMPILED_PATTERNS.items():
        matches = pattern.findall(anonymized)
        if matches:
            mask = ENTITY_MASKS.get(pattern_name, "[REDACTED]")
            anonymized = pattern.sub(mask, anonymized)
            patterns_found[pattern_name] = len(matches)
            total_redactions += len(matches)

    result.anonymized_text = anonymized
    result.patterns_found = patterns_found
    result.total_redactions = total_redactions
    result.processing_time_ms = int((time.time() - start_time) * 1000)

    log.info(
        "[N3.9-Safety] Anonymized %d entities across %d pattern types",
        total_redactions,
        len(patterns_found),
    )

    return result


def anonymize_sections(sections: Dict[str, Any]) -> Tuple[Dict[str, Any], List[AnonymizationResult]]:
    """
    Anonymize PII in all text sections.

    Args:
        sections: Report sections

    Returns:
        Tuple of (anonymized sections, list of anonymization results)
    """
    results: List[AnonymizationResult] = []
    anonymized_sections = sections.copy()

    for key, value in sections.items():
        if isinstance(value, str) and len(value) > 10:
            result = entity_masking(value)
            if result.total_redactions > 0:
                anonymized_sections[key] = result.anonymized_text
                results.append(result)

    return anonymized_sections, results


# =============================================================================
# MAIN PROCESSING FUNCTION
# =============================================================================

def process_safety_tuning(
    sections: Dict[str, Any],
    briefing: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Process sections with safety tuning.

    Main entry point for safety-aware processing.

    Args:
        sections: Report sections
        briefing: Report briefing

    Returns:
        Dict with processed sections and safety metadata
    """
    tuner = get_safety_tuner()

    # Get full tuning report
    tuning_report = tuner.process_safety_tuning(briefing, sections)

    # Apply anonymization if required
    processed_sections = sections.copy()
    if tuning_report.parameters.anonymization_enabled:
        processed_sections, anon_results = anonymize_sections(sections)
        tuning_report.anonymization_results = anon_results

    # Build result
    result = {
        "sections": processed_sections,
        "safety_metadata": tuning_report.to_dict(),
        "tuned_parameters": tuning_report.parameters.to_dict(),
    }

    log.info(
        "[N3.9-Safety] Safety tuning complete: mode=%s, adjustments=%d",
        tuning_report.context.compliance_mode.value,
        len(tuning_report.adjustments_applied),
    )

    return result


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "RiskLevel",
    "DataSensitivity",
    "ReportType",
    "ComplianceMode",
    # Data classes
    "SafetyContext",
    "TunedParameters",
    "AnonymizationResult",
    "SafetyTuningReport",
    # Detection functions
    "detect_risk_level",
    "detect_data_sensitivity",
    "detect_report_type",
    "detect_pii_patterns",
    # Main classes
    "SafetyTuner",
    "get_safety_tuner",
    # Anonymization
    "entity_masking",
    "anonymize_sections",
    # Processing function
    "process_safety_tuning",
]
