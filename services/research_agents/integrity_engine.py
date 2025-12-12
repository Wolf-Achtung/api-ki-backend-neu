# -*- coding: utf-8 -*-
"""
N4.4: Research Integrity Engine v1
==================================

PLATIN+++ v5.4 - Research Data Integrity Validation

Features:
- Source Authenticity Check
- Bias Detection
- Temporal Decay (older sources get lower weight)
- Anomaly Detection for numbers (min/max/median comparison)

Version: 1.0.0 (N4.4 - PLATIN+++ v5.4)
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import statistics

from services.research_agents.orchestrator import (
    AgentResult,
    AgentSignalType,
    ResearchInsight,
)

log = logging.getLogger(__name__)

__all__ = [
    "SourceTrustLevel",
    "BiasType",
    "AnomalyType",
    "SourceAuthenticity",
    "BiasIndicator",
    "NumericAnomaly",
    "IntegrityReport",
    "ResearchIntegrityEngineV1",
    "verify_source_authenticity",
    "detect_bias",
    "apply_temporal_decay",
    "detect_anomalies",
]


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class SourceTrustLevel(Enum):
    """Trust levels for sources."""
    OFFICIAL = "official"           # Government, regulators
    ACADEMIC = "academic"           # Peer-reviewed research
    ENTERPRISE = "enterprise"       # Major corporations
    INDUSTRY = "industry"           # Industry associations
    NEWS = "news"                   # Major news outlets
    BLOG = "blog"                   # Blogs, opinions
    UNKNOWN = "unknown"             # Unverified


class BiasType(Enum):
    """Types of bias in research."""
    VENDOR_BIAS = "vendor_bias"         # Promotes specific vendor
    SELECTION_BIAS = "selection_bias"   # Cherry-picked data
    CONFIRMATION_BIAS = "confirmation_bias"  # Confirms expectations
    TEMPORAL_BIAS = "temporal_bias"     # Outdated information
    REGIONAL_BIAS = "regional_bias"     # Not applicable to region


class AnomalyType(Enum):
    """Types of numeric anomalies."""
    OUTLIER = "outlier"             # Outside normal range
    IMPLAUSIBLE = "implausible"     # Unrealistic value
    INCONSISTENT = "inconsistent"   # Contradicts other data
    MISSING = "missing"             # Expected value missing


# Trusted source patterns
TRUSTED_SOURCES: Dict[str, SourceTrustLevel] = {
    "eu commission": SourceTrustLevel.OFFICIAL,
    "european commission": SourceTrustLevel.OFFICIAL,
    "bundesregierung": SourceTrustLevel.OFFICIAL,
    "bmwk": SourceTrustLevel.OFFICIAL,
    "bsi": SourceTrustLevel.OFFICIAL,
    "bitkom": SourceTrustLevel.INDUSTRY,
    "gartner": SourceTrustLevel.ENTERPRISE,
    "mckinsey": SourceTrustLevel.ENTERPRISE,
    "harvard": SourceTrustLevel.ACADEMIC,
    "mit": SourceTrustLevel.ACADEMIC,
    "iso": SourceTrustLevel.OFFICIAL,
    "nist": SourceTrustLevel.OFFICIAL,
    "reuters": SourceTrustLevel.NEWS,
    "bloomberg": SourceTrustLevel.NEWS,
}

# Bias indicator patterns
BIAS_PATTERNS: Dict[str, Dict[str, List[str]]] = {
    "vendor_bias": {
        "de": ["nur mit", "exklusiv", "einzig", "beste Lösung", "marktführend"],
        "en": ["only with", "exclusive", "unique", "best solution", "market leading"],
    },
    "promotional": {
        "de": ["garantiert", "revolutionär", "beispiellos", "nie dagewesen"],
        "en": ["guaranteed", "revolutionary", "unprecedented", "never before"],
    },
}

# Temporal decay settings
TEMPORAL_DECAY_RATE = 0.1  # 10% decay per year
MAX_SOURCE_AGE_DAYS = 365 * 3  # 3 years max

# Numeric plausibility ranges
PLAUSIBILITY_RANGES: Dict[str, Tuple[float, float]] = {
    "roi_percent": (5, 500),
    "payback_months": (1, 60),
    "savings_percent": (1, 80),
    "fte_savings": (0.1, 100),
    "cost_reduction": (1, 90),
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class SourceAuthenticity:
    """Source authenticity assessment."""

    source_name: str
    trust_level: SourceTrustLevel
    verified: bool
    verification_method: str = ""
    url_valid: bool = True
    last_verified: str = ""

    def trust_score(self) -> float:
        """Calculate trust score (0-1)."""
        base_scores = {
            SourceTrustLevel.OFFICIAL: 1.0,
            SourceTrustLevel.ACADEMIC: 0.95,
            SourceTrustLevel.ENTERPRISE: 0.85,
            SourceTrustLevel.INDUSTRY: 0.80,
            SourceTrustLevel.NEWS: 0.70,
            SourceTrustLevel.BLOG: 0.40,
            SourceTrustLevel.UNKNOWN: 0.30,
        }
        score = base_scores.get(self.trust_level, 0.30)

        if not self.verified:
            score *= 0.8
        if not self.url_valid:
            score *= 0.9

        return score

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_name": self.source_name,
            "trust_level": self.trust_level.value,
            "verified": self.verified,
            "trust_score": round(self.trust_score(), 3),
            "url_valid": self.url_valid,
        }


@dataclass
class BiasIndicator:
    """Indicator of bias in content."""

    bias_type: BiasType
    severity: float  # 0-1
    evidence: str
    location: str = ""
    mitigation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "bias_type": self.bias_type.value,
            "severity": round(self.severity, 3),
            "evidence": self.evidence[:200],
            "mitigation": self.mitigation,
        }


@dataclass
class NumericAnomaly:
    """Detected numeric anomaly."""

    anomaly_type: AnomalyType
    field_name: str
    value: float
    expected_range: Tuple[float, float]
    severity: float  # 0-1
    context: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "anomaly_type": self.anomaly_type.value,
            "field_name": self.field_name,
            "value": self.value,
            "expected_range": self.expected_range,
            "severity": round(self.severity, 3),
        }


@dataclass
class IntegrityReport:
    """Full integrity assessment report."""

    report_id: str
    timestamp: str = ""
    insights_checked: int = 0
    sources_verified: int = 0
    biases_detected: int = 0
    anomalies_found: int = 0
    overall_integrity_score: float = 1.0
    source_assessments: List[SourceAuthenticity] = field(default_factory=list)
    bias_indicators: List[BiasIndicator] = field(default_factory=list)
    anomalies: List[NumericAnomaly] = field(default_factory=list)
    temporal_adjustments: int = 0
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp,
            "insights_checked": self.insights_checked,
            "sources_verified": self.sources_verified,
            "biases_detected": self.biases_detected,
            "anomalies_found": self.anomalies_found,
            "overall_integrity_score": round(self.overall_integrity_score, 3),
            "source_assessments": [s.to_dict() for s in self.source_assessments],
            "bias_indicators": [b.to_dict() for b in self.bias_indicators],
            "anomalies": [a.to_dict() for a in self.anomalies],
            "temporal_adjustments": self.temporal_adjustments,
            "warnings": self.warnings,
        }


# =============================================================================
# RESEARCH INTEGRITY ENGINE V1
# =============================================================================

class ResearchIntegrityEngineV1:
    """
    Research data integrity validation engine.

    Validates:
    - Source authenticity
    - Bias detection
    - Temporal relevance
    - Numeric plausibility
    """

    def __init__(
        self,
        language: str = "de",
        strict_mode: bool = False,
    ) -> None:
        """
        Initialize Research Integrity Engine.

        Args:
            language: Language code (de/en)
            strict_mode: Apply stricter validation rules
        """
        self.language = language
        self.strict_mode = strict_mode

        self._insights: List[ResearchInsight] = []
        self._report: Optional[IntegrityReport] = None

        log.info("[N4.4-Integrity] Initialized: lang=%s, strict=%s", language, strict_mode)

    def validate(self, insights: List[ResearchInsight]) -> IntegrityReport:
        """
        Validate research insights for integrity.

        Returns IntegrityReport with findings.
        """
        self._insights = insights
        log.info("[N4.4-Integrity] Validating %d insights", len(insights))

        # Initialize report
        self._report = IntegrityReport(
            report_id=f"IR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            insights_checked=len(insights),
        )

        # Step 1: Verify sources
        self._verify_sources()

        # Step 2: Detect bias
        self._detect_bias()

        # Step 3: Apply temporal decay
        self._apply_temporal_decay()

        # Step 4: Detect anomalies
        self._detect_anomalies()

        # Step 5: Calculate overall integrity score
        self._calculate_integrity_score()

        log.info("[N4.4-Integrity] Validation complete: score=%.2f",
                 self._report.overall_integrity_score)

        return self._report

    def _verify_sources(self) -> None:
        """Verify source authenticity."""
        seen_sources: Dict[str, SourceAuthenticity] = {}

        for insight in self._insights:
            source = insight.source.lower()

            if source in seen_sources:
                continue

            # Check against trusted sources
            trust_level = SourceTrustLevel.UNKNOWN
            for pattern, level in TRUSTED_SOURCES.items():
                if pattern in source:
                    trust_level = level
                    break

            assessment = SourceAuthenticity(
                source_name=insight.source,
                trust_level=trust_level,
                verified=trust_level != SourceTrustLevel.UNKNOWN,
                verification_method="pattern_matching",
                url_valid=bool(insight.source_url),
            )

            seen_sources[source] = assessment
            self._report.source_assessments.append(assessment)

            # Add warning for unverified sources
            if not assessment.verified and self.strict_mode:
                self._report.warnings.append(f"Unverified source: {insight.source}")

        self._report.sources_verified = sum(
            1 for s in self._report.source_assessments if s.verified
        )

    def _detect_bias(self) -> None:
        """Detect bias in insight content."""
        patterns = BIAS_PATTERNS

        for insight in self._insights:
            content_lower = insight.content.lower()

            # Check vendor bias
            vendor_patterns = patterns.get("vendor_bias", {}).get(self.language, [])
            for pattern in vendor_patterns:
                if pattern.lower() in content_lower:
                    indicator = BiasIndicator(
                        bias_type=BiasType.VENDOR_BIAS,
                        severity=0.6,
                        evidence=pattern,
                        location=insight.insight_id,
                        mitigation="Cross-reference with neutral sources",
                    )
                    self._report.bias_indicators.append(indicator)
                    break

            # Check promotional bias
            promo_patterns = patterns.get("promotional", {}).get(self.language, [])
            for pattern in promo_patterns:
                if pattern.lower() in content_lower:
                    indicator = BiasIndicator(
                        bias_type=BiasType.CONFIRMATION_BIAS,
                        severity=0.4,
                        evidence=pattern,
                        location=insight.insight_id,
                        mitigation="Verify claims with data",
                    )
                    self._report.bias_indicators.append(indicator)
                    break

        self._report.biases_detected = len(self._report.bias_indicators)

    def _apply_temporal_decay(self) -> None:
        """Apply temporal decay to insights based on age."""
        now = datetime.utcnow()
        adjustments = 0

        for insight in self._insights:
            # Try to parse timestamp
            try:
                if insight.timestamp:
                    insight_date = datetime.fromisoformat(
                        insight.timestamp.replace("Z", "+00:00")
                    ).replace(tzinfo=None)
                    age_days = (now - insight_date).days

                    if age_days > MAX_SOURCE_AGE_DAYS:
                        # Very old source - significant decay
                        decay = 0.5
                        self._report.warnings.append(
                            f"Source older than {MAX_SOURCE_AGE_DAYS} days: {insight.insight_id}"
                        )
                    else:
                        # Calculate decay based on age
                        years = age_days / 365
                        decay = 1 - (years * TEMPORAL_DECAY_RATE)
                        decay = max(0.5, decay)  # Minimum 50%

                    if decay < 1.0:
                        # Store original confidence
                        original = insight.confidence
                        insight.confidence = insight.confidence * decay
                        adjustments += 1
                        log.debug(
                            "[N4.4-Integrity] Temporal decay: %s %.2f -> %.2f",
                            insight.insight_id, original, insight.confidence
                        )

            except (ValueError, TypeError):
                # Can't parse date - no adjustment
                pass

        self._report.temporal_adjustments = adjustments

    def _detect_anomalies(self) -> None:
        """Detect numeric anomalies in insights."""
        # Extract numeric values from content
        numeric_pattern = r"(\d+(?:[.,]\d+)?)\s*(%|EUR|€|\bMonat|\bmonths?)"

        all_values: Dict[str, List[float]] = {}

        for insight in self._insights:
            matches = re.findall(numeric_pattern, insight.content, re.IGNORECASE)

            for value_str, unit in matches:
                # Normalize value
                value = float(value_str.replace(",", "."))

                # Categorize by unit
                if "%" in unit:
                    category = "percentage"
                elif "eur" in unit.lower() or "€" in unit:
                    category = "amount"
                elif "monat" in unit.lower() or "month" in unit.lower():
                    category = "months"
                else:
                    category = "other"

                if category not in all_values:
                    all_values[category] = []
                all_values[category].append(value)

        # Check for outliers and implausible values
        for category, values in all_values.items():
            if len(values) < 2:
                continue

            median = statistics.median(values)
            stdev = statistics.stdev(values) if len(values) > 1 else 0

            for value in values:
                # Check for statistical outliers
                if stdev > 0 and abs(value - median) > 2 * stdev:
                    anomaly = NumericAnomaly(
                        anomaly_type=AnomalyType.OUTLIER,
                        field_name=category,
                        value=value,
                        expected_range=(median - stdev, median + stdev),
                        severity=0.5,
                    )
                    self._report.anomalies.append(anomaly)

                # Check plausibility for known categories
                if category == "percentage":
                    if value > 500 or value < 0:
                        anomaly = NumericAnomaly(
                            anomaly_type=AnomalyType.IMPLAUSIBLE,
                            field_name=category,
                            value=value,
                            expected_range=(0, 500),
                            severity=0.7,
                        )
                        self._report.anomalies.append(anomaly)

        self._report.anomalies_found = len(self._report.anomalies)

    def _calculate_integrity_score(self) -> None:
        """Calculate overall integrity score."""
        if not self._insights:
            self._report.overall_integrity_score = 0.0
            return

        # Start with base score
        score = 1.0

        # Deduct for unverified sources
        verified_ratio = (
            self._report.sources_verified / len(self._report.source_assessments)
            if self._report.source_assessments else 1.0
        )
        score *= (0.7 + 0.3 * verified_ratio)

        # Deduct for bias
        bias_penalty = min(0.3, self._report.biases_detected * 0.05)
        score -= bias_penalty

        # Deduct for anomalies
        anomaly_penalty = min(0.2, self._report.anomalies_found * 0.03)
        score -= anomaly_penalty

        # Stricter penalties in strict mode
        if self.strict_mode:
            score *= 0.95

        self._report.overall_integrity_score = max(0.0, min(1.0, score))


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def verify_source_authenticity(
    source_name: str,
    source_url: str = "",
) -> SourceAuthenticity:
    """
    Verify a single source's authenticity.

    Returns SourceAuthenticity assessment.
    """
    source_lower = source_name.lower()

    # Check against trusted sources
    trust_level = SourceTrustLevel.UNKNOWN
    for pattern, level in TRUSTED_SOURCES.items():
        if pattern in source_lower:
            trust_level = level
            break

    return SourceAuthenticity(
        source_name=source_name,
        trust_level=trust_level,
        verified=trust_level != SourceTrustLevel.UNKNOWN,
        verification_method="pattern_matching",
        url_valid=bool(source_url),
        last_verified=datetime.utcnow().isoformat(),
    )


def detect_bias(
    content: str,
    language: str = "de",
) -> List[BiasIndicator]:
    """
    Detect bias indicators in content.

    Returns list of BiasIndicators.
    """
    indicators: List[BiasIndicator] = []
    content_lower = content.lower()

    for bias_category, lang_patterns in BIAS_PATTERNS.items():
        patterns = lang_patterns.get(language, [])

        for pattern in patterns:
            if pattern.lower() in content_lower:
                bias_type = (
                    BiasType.VENDOR_BIAS if bias_category == "vendor_bias"
                    else BiasType.CONFIRMATION_BIAS
                )

                indicator = BiasIndicator(
                    bias_type=bias_type,
                    severity=0.5,
                    evidence=pattern,
                    mitigation="Cross-reference with neutral sources",
                )
                indicators.append(indicator)

    return indicators


def apply_temporal_decay(
    insights: List[ResearchInsight],
    decay_rate: float = TEMPORAL_DECAY_RATE,
    max_age_days: int = MAX_SOURCE_AGE_DAYS,
) -> List[ResearchInsight]:
    """
    Apply temporal decay to insights.

    Modifies confidence based on age.
    Returns modified insights.
    """
    now = datetime.utcnow()

    for insight in insights:
        try:
            if insight.timestamp:
                insight_date = datetime.fromisoformat(
                    insight.timestamp.replace("Z", "+00:00")
                ).replace(tzinfo=None)
                age_days = (now - insight_date).days

                if age_days > max_age_days:
                    insight.confidence *= 0.5
                else:
                    years = age_days / 365
                    decay = max(0.5, 1 - (years * decay_rate))
                    insight.confidence *= decay

        except (ValueError, TypeError):
            pass

    return insights


def detect_anomalies(
    values: List[float],
    field_name: str = "value",
    expected_range: Optional[Tuple[float, float]] = None,
) -> List[NumericAnomaly]:
    """
    Detect anomalies in a list of numeric values.

    Returns list of NumericAnomalies.
    """
    if not values:
        return []

    anomalies: List[NumericAnomaly] = []

    median = statistics.median(values)
    stdev = statistics.stdev(values) if len(values) > 1 else 0

    # Use expected range or calculate from data
    if expected_range:
        min_val, max_val = expected_range
    else:
        min_val = median - 2 * stdev if stdev > 0 else median * 0.5
        max_val = median + 2 * stdev if stdev > 0 else median * 1.5

    for value in values:
        # Check outliers
        if stdev > 0 and abs(value - median) > 2 * stdev:
            anomaly = NumericAnomaly(
                anomaly_type=AnomalyType.OUTLIER,
                field_name=field_name,
                value=value,
                expected_range=(min_val, max_val),
                severity=0.5,
            )
            anomalies.append(anomaly)

        # Check range violations
        if expected_range and (value < min_val or value > max_val):
            anomaly = NumericAnomaly(
                anomaly_type=AnomalyType.IMPLAUSIBLE,
                field_name=field_name,
                value=value,
                expected_range=expected_range,
                severity=0.7,
            )
            anomalies.append(anomaly)

    return anomalies
