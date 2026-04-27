# -*- coding: utf-8 -*-
"""
Sprint G17.3-A/B: LLM Fine-Tuning Signal Extractor

Extracts fine-tuning signals from generated reports for LLM improvement:
- Captures prompt/response pairs with quality metadata
- Normalizes signals for training data format
- Applies safety filters to remove PII

Version: 1.0.0 (Sprint G17.3)
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
import json

log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

FT_SIGNAL_EXTRACTION_ENABLED = os.environ.get("FT_SIGNAL_EXTRACTION_ENABLED", "1") == "1"
FT_BUILD_DATASET_ON_REPORT = os.environ.get("FT_BUILD_DATASET_ON_REPORT", "0") == "1"
FT_DATASET_DAYS = int(os.environ.get("FT_DATASET_DAYS", "30"))
FT_MIN_CONFIDENCE_THRESHOLD = float(os.environ.get("FT_MIN_CONFIDENCE_THRESHOLD", "0.35"))
FT_MAX_SIGNALS_PER_REPORT = int(os.environ.get("FT_MAX_SIGNALS_PER_REPORT", "12"))
FT_PRIVACY_STRICT_MODE = os.environ.get("FT_PRIVACY_STRICT_MODE", "1") == "1"
FT_SIGNAL_DEBUG_LOGGING = os.environ.get("FT_SIGNAL_DEBUG_LOGGING", "0") == "1"
FT_ALLOW_WEAK_SEGMENTS = os.environ.get("FT_ALLOW_WEAK_SEGMENTS", "0") == "1"
FT_SIGNAL_STORAGE_PATH = os.environ.get("FT_SIGNAL_STORAGE_PATH", "/app/ft_signals")

# Derived from FT_PRIVACY_STRICT_MODE for backward compatibility
FT_SIGNAL_ANONYMIZE_EMAILS = FT_PRIVACY_STRICT_MODE
FT_SIGNAL_ANONYMIZE_NAMES = FT_PRIVACY_STRICT_MODE
FT_SIGNAL_ANONYMIZE_COMPANIES = FT_PRIVACY_STRICT_MODE
FT_SIGNAL_MAX_AGE_DAYS = FT_DATASET_DAYS  # Alias for dataset days

# Signal type weights for quality aggregation
SIGNAL_WEIGHT_MAP: Dict[str, float] = {
    "persona_fix": 1.0,
    "size_aware_length": 0.8,
    "redundancy_compression": 0.7,
    "html_repair": 0.5,
    "business_case_align": 1.2,
    "ai_act_reasoning": 1.3,
    "insight_quality": 1.1,
    "predictive_drift": 0.9,
    "smart_default_corrections": 0.8,
    "funding_misclassifications": 0.6,
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class SegmentInfo:
    """Segment metadata for normalized signals."""
    size: str = "team"  # solo|team|kmu
    branch: str = "other"  # consulting|finance|industry|health|education|...
    risk: str = "minimal"  # minimal|limited|high-risk
    funding_scope: str = "NONE"  # DE|EU_CORE|NONE
    stability: str = "medium"  # strong|medium|weak


@dataclass
class FTSignal:
    """Fine-tuning signal representing a prompt/completion pair with metadata."""
    signal_id: str
    signal_type: str  # One of 10 signal types
    source_section: str  # Which section produced this signal
    timestamp: str

    # Core training data
    prompt_input: str  # Original prompt/input
    ideal_output: str  # Corrected/ideal output
    original_output: str  # What was originally generated

    # Quality metadata
    quality_score: float  # 0.0 - 1.0
    confidence: float  # 0.0 - 1.0
    human_validated: bool = False

    # Context fields
    segment_key: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    lang: str = "de"
    risk_level: str = "minimal"
    funding_scope: str = "NONE"
    stability: str = "medium"

    # Signal-specific metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Normalization status
    is_normalized: bool = False
    is_anonymized: bool = False


@dataclass
class NormalizedSignal:
    """Normalized signal structure for dataset building (G17.3-B)."""
    signal_type: str  # persona|logic|html|business_case|ai_act|insight|predictive|funding
    language: str  # de|en
    input_pattern: str
    output_target: str
    confidence: float
    segment: SegmentInfo = field(default_factory=SegmentInfo)


@dataclass
class FTSignalBatch:
    """Batch of signals for a single report."""
    report_id: str
    extraction_timestamp: str
    signals: List[FTSignal] = field(default_factory=list)
    total_quality_score: float = 0.0
    signal_counts: Dict[str, int] = field(default_factory=dict)


# =============================================================================
# PII DETECTION AND REMOVAL (G17.3-B Safety Guard)
# =============================================================================

# Email pattern
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

# German phone patterns
PHONE_PATTERN = re.compile(
    r'\b(?:\+49|0049|0)[\s.-]?\d{2,4}[\s.-]?\d{4,8}\b'
)

# Company name patterns (common German legal forms)
COMPANY_PATTERNS = [
    re.compile(r'\b[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*\s+(?:GmbH|AG|UG|KG|OHG|e\.K\.|GbR|mbH)\b'),
    re.compile(r'\b[A-ZÄÖÜ][A-Za-zäöüßÄÖÜ]+\s+(?:GmbH|AG|UG|KG|OHG|e\.K\.|GbR|mbH)\b'),
]

# Person name patterns (titles followed by names)
NAME_PATTERNS = [
    re.compile(r'\b(?:Herr|Frau|Dr\.|Prof\.)\s+[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*\b'),
    re.compile(r'\b(?:Hr\.|Fr\.)\s+[A-ZÄÖÜ][a-zäöüß]+\b'),
]

# Address patterns
ADDRESS_PATTERN = re.compile(
    r'\b(?:Straße|Str\.|Weg|Platz|Allee|Ring)\s*\d+[a-zA-Z]?\b',
    re.IGNORECASE
)

# IBAN pattern - matches DE89 3704 0044 0532 0130 00 or similar
IBAN_PATTERN = re.compile(r'\b[A-Z]{2}\d{2}[\s]?(?:\d{4}[\s]?){4,6}\d{0,2}\b')

# Tax ID patterns - matches "USt-IdNr.: DE123456789" capturing the full ID
TAX_ID_PATTERN = re.compile(r'(?:USt-?IdNr\.?|Steuernummer|St-?Nr\.?)\s*:?\s*[A-Z]{0,2}[\d\s/]+', re.IGNORECASE)


def remove_pii(text: str) -> str:
    """
    Remove PII from text while preserving structure.

    Replaces sensitive data with generic placeholders to maintain
    text structure for training purposes.
    """
    if not text:
        return text

    result = text

    # Remove emails
    if FT_SIGNAL_ANONYMIZE_EMAILS:
        result = EMAIL_PATTERN.sub("[EMAIL]", result)

    # Remove phone numbers
    result = PHONE_PATTERN.sub("[TELEFON]", result)

    # Remove company names
    if FT_SIGNAL_ANONYMIZE_COMPANIES:
        for pattern in COMPANY_PATTERNS:
            result = pattern.sub("[FIRMA]", result)

    # Remove person names
    if FT_SIGNAL_ANONYMIZE_NAMES:
        for pattern in NAME_PATTERNS:
            result = pattern.sub("[PERSON]", result)

    # Remove addresses
    result = ADDRESS_PATTERN.sub("[ADRESSE]", result)

    # Remove IBANs
    result = IBAN_PATTERN.sub("[IBAN]", result)

    # Remove tax IDs
    result = TAX_ID_PATTERN.sub("[STEUER-ID]", result)

    return result


def anonymize_signal(signal: FTSignal) -> FTSignal:
    """Apply PII removal to all text fields in a signal."""
    signal.prompt_input = remove_pii(signal.prompt_input)
    signal.ideal_output = remove_pii(signal.ideal_output)
    signal.original_output = remove_pii(signal.original_output)
    signal.is_anonymized = True

    # Also clean metadata if it contains text
    if signal.metadata:
        for key, value in signal.metadata.items():
            if isinstance(value, str):
                signal.metadata[key] = remove_pii(value)

    return signal


# =============================================================================
# SIGNAL NORMALIZATION (G17.3-B)
# =============================================================================

def normalize_signal(signal: FTSignal) -> FTSignal:
    """
    Normalize signal fields for consistent training data format.

    - Strips whitespace
    - Normalizes newlines
    - Limits text lengths
    - Validates quality scores
    """
    # Normalize text fields
    signal.prompt_input = _normalize_text(signal.prompt_input, max_length=8000)
    signal.ideal_output = _normalize_text(signal.ideal_output, max_length=16000)
    signal.original_output = _normalize_text(signal.original_output, max_length=16000)

    # Clamp scores to valid range
    signal.quality_score = max(0.0, min(1.0, signal.quality_score))
    signal.confidence = max(0.0, min(1.0, signal.confidence))

    # Normalize segment key
    if signal.segment_key:
        signal.segment_key = signal.segment_key.lower().strip()

    # Normalize company size
    if signal.company_size:
        signal.company_size = _normalize_company_size(signal.company_size)

    signal.is_normalized = True
    return signal


def _normalize_text(text: str, max_length: int = 10000) -> str:
    """Normalize text content."""
    if not text:
        return ""

    # Strip and normalize whitespace
    text = text.strip()

    # Normalize newlines
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Remove excessive spaces
    text = re.sub(r' {2,}', ' ', text)

    # Truncate if needed
    if len(text) > max_length:
        text = text[:max_length] + "..."

    return text


def _normalize_company_size(size: str) -> str:
    """Normalize company size values."""
    size_lower = size.lower().strip()

    size_map = {
        "solo": "solo",
        "selbstständig": "solo",
        "einzelunternehmer": "solo",
        "freelancer": "solo",
        "1": "solo",
        "team": "team",
        "klein": "team",
        "small": "team",
        "small_team": "team",
        "2-10": "team",
        "kmu": "kmu",
        "mittel": "kmu",
        "medium": "kmu",
        "11-50": "kmu",
        "51-250": "kmu",
        "enterprise": "enterprise",
        "gross": "enterprise",
        "large": "enterprise",
        "250+": "enterprise",
    }

    return size_map.get(size_lower, size_lower)


# =============================================================================
# SIGNAL GENERATION HELPERS
# =============================================================================

def _generate_signal_id(signal_type: str, source_section: str, content_hash: str) -> str:
    """Generate unique signal ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    hash_suffix = hashlib.md5(
        f"{signal_type}:{source_section}:{content_hash}:{timestamp}".encode(),
        usedforsecurity=False,
    ).hexdigest()[:8]
    return f"ft_{signal_type}_{hash_suffix}"


def _calculate_quality_score(
    original: str,
    corrected: str,
    correction_type: str,
    additional_factors: Optional[Dict[str, float]] = None,
) -> float:
    """
    Calculate quality score for a signal based on correction significance.

    Higher scores indicate more valuable training signals.
    """
    if not original or not corrected:
        return 0.0

    # Base score from correction significance
    original_len = len(original)
    corrected_len = len(corrected)

    # Calculate edit distance ratio (simplified)
    if original == corrected:
        return 0.0  # No change, no signal value

    # Length-based change magnitude
    len_diff = abs(corrected_len - original_len)
    len_ratio = len_diff / max(original_len, 1)

    # Base score: higher for more significant changes
    base_score = min(1.0, len_ratio * 2)

    # Apply type weight
    type_weight = SIGNAL_WEIGHT_MAP.get(correction_type, 1.0)
    weighted_score = base_score * type_weight

    # Apply additional factors
    if additional_factors:
        for factor_name, factor_value in additional_factors.items():
            if factor_name == "human_validated" and factor_value > 0:
                weighted_score *= 1.3  # Boost for human validation
            elif factor_name == "segment_sample_size" and factor_value > 10:
                weighted_score *= 1.1  # More reliable with larger samples
            elif factor_name == "consistency_score":
                weighted_score *= (0.8 + 0.2 * factor_value)

    return min(1.0, max(0.0, weighted_score))


# =============================================================================
# SIGNAL EXTRACTORS (10 Signal Types)
# =============================================================================

def _extract_persona_fix_signals(
    report_data: Dict[str, Any],
    lang: str = "de",
) -> List[FTSignal]:
    """
    Extract persona fix signals.

    Captures cases where persona-inappropriate terms were corrected
    (e.g., "Team" removed for solo users).
    """
    signals: List[FTSignal] = []

    persona_corrections = report_data.get("_persona_corrections", [])
    company_size_raw = report_data.get("unternehmensgroesse") or ""
    company_size = company_size_raw.lower() if company_size_raw else ""

    for correction in persona_corrections:
        if not isinstance(correction, dict):
            continue

        original = correction.get("original_text", "")
        corrected = correction.get("corrected_text", "")
        section = correction.get("section", "unknown")

        if not original or not corrected or original == corrected:
            continue

        quality_score = _calculate_quality_score(
            original, corrected, "persona_fix",
            {"segment_sample_size": correction.get("frequency", 1)}
        )

        if quality_score < FT_MIN_CONFIDENCE_THRESHOLD:
            continue

        signal = FTSignal(
            signal_id=_generate_signal_id("persona_fix", section, original),
            signal_type="persona_fix",
            source_section=section,
            timestamp=datetime.utcnow().isoformat(),
            prompt_input=f"Korrigiere für {company_size}-Persona: {original}",
            ideal_output=corrected,
            original_output=original,
            quality_score=quality_score,
            confidence=correction.get("confidence", 0.7),
            company_size=company_size,
            lang=lang,
            metadata={
                "removed_terms": correction.get("removed_terms", []),
                "persona_type": company_size,
            }
        )
        signals.append(signal)

    return signals


def _extract_size_aware_length_signals(
    report_data: Dict[str, Any],
    lang: str = "de",
) -> List[FTSignal]:
    """
    Extract size-aware length adjustment signals.

    Captures when section lengths were adjusted based on company size.
    """
    signals: List[FTSignal] = []

    length_adjustments = report_data.get("_length_adjustments", [])
    company_size = report_data.get("unternehmensgroesse", "")

    for adjustment in length_adjustments:
        if not isinstance(adjustment, dict):
            continue

        original = adjustment.get("original_text", "")
        adjusted = adjustment.get("adjusted_text", "")
        section = adjustment.get("section", "unknown")
        target_words = adjustment.get("target_word_count", 0)

        if not original or not adjusted:
            continue

        quality_score = _calculate_quality_score(
            original, adjusted, "size_aware_length"
        )

        if quality_score < FT_MIN_CONFIDENCE_THRESHOLD:
            continue

        signal = FTSignal(
            signal_id=_generate_signal_id("size_aware_length", section, original[:100]),
            signal_type="size_aware_length",
            source_section=section,
            timestamp=datetime.utcnow().isoformat(),
            prompt_input=f"Passe Länge für {company_size} an (Ziel: {target_words} Wörter): {original[:500]}...",
            ideal_output=adjusted,
            original_output=original,
            quality_score=quality_score,
            confidence=0.75,
            company_size=company_size,
            lang=lang,
            metadata={
                "original_word_count": len(original.split()),
                "adjusted_word_count": len(adjusted.split()),
                "target_word_count": target_words,
            }
        )
        signals.append(signal)

    return signals


def _extract_redundancy_compression_signals(
    report_data: Dict[str, Any],
    lang: str = "de",
) -> List[FTSignal]:
    """
    Extract redundancy compression signals.

    Captures when redundant content was removed or compressed.
    """
    signals: List[FTSignal] = []

    compressions = report_data.get("_redundancy_compressions", [])

    for compression in compressions:
        if not isinstance(compression, dict):
            continue

        original = compression.get("original_text", "")
        compressed = compression.get("compressed_text", "")
        section = compression.get("section", "unknown")

        if not original or not compressed:
            continue

        # Only track significant compressions
        compression_ratio = len(compressed) / max(len(original), 1)
        if compression_ratio > 0.95:  # Less than 5% reduction
            continue

        quality_score = _calculate_quality_score(
            original, compressed, "redundancy_compression"
        )

        signal = FTSignal(
            signal_id=_generate_signal_id("redundancy_compression", section, original[:100]),
            signal_type="redundancy_compression",
            source_section=section,
            timestamp=datetime.utcnow().isoformat(),
            prompt_input=f"Entferne Redundanzen: {original[:500]}...",
            ideal_output=compressed,
            original_output=original,
            quality_score=quality_score,
            confidence=0.7,
            lang=lang,
            metadata={
                "compression_ratio": compression_ratio,
                "removed_patterns": compression.get("removed_patterns", []),
            }
        )
        signals.append(signal)

    return signals


def _extract_html_repair_signals(
    report_data: Dict[str, Any],
    lang: str = "de",
) -> List[FTSignal]:
    """
    Extract HTML repair signals.

    Captures when malformed HTML was corrected.
    """
    signals: List[FTSignal] = []

    html_repairs = report_data.get("_html_repairs", [])

    for repair in html_repairs:
        if not isinstance(repair, dict):
            continue

        original = repair.get("original_html", "")
        repaired = repair.get("repaired_html", "")
        section = repair.get("section", "unknown")

        if not original or not repaired or original == repaired:
            continue

        quality_score = _calculate_quality_score(
            original, repaired, "html_repair"
        )

        signal = FTSignal(
            signal_id=_generate_signal_id("html_repair", section, original[:100]),
            signal_type="html_repair",
            source_section=section,
            timestamp=datetime.utcnow().isoformat(),
            prompt_input=f"Repariere HTML: {original[:1000]}",
            ideal_output=repaired,
            original_output=original,
            quality_score=quality_score,
            confidence=0.9,  # High confidence for deterministic repairs
            lang=lang,
            metadata={
                "repair_type": repair.get("repair_type", "general"),
                "error_count": repair.get("error_count", 0),
            }
        )
        signals.append(signal)

    return signals


def _extract_business_case_align_signals(
    report_data: Dict[str, Any],
    lang: str = "de",
) -> List[FTSignal]:
    """
    Extract business case alignment signals.

    Captures when business case values were adjusted for consistency.
    """
    signals: List[FTSignal] = []

    bc_alignments = report_data.get("_business_case_alignments", [])
    industry = report_data.get("branche", "")
    company_size = report_data.get("unternehmensgroesse", "")

    for alignment in bc_alignments:
        if not isinstance(alignment, dict):
            continue

        original_values = alignment.get("original_values", {})
        aligned_values = alignment.get("aligned_values", {})

        if not original_values or original_values == aligned_values:
            continue

        original_str = json.dumps(original_values, ensure_ascii=False)
        aligned_str = json.dumps(aligned_values, ensure_ascii=False)

        quality_score = _calculate_quality_score(
            original_str, aligned_str, "business_case_align",
            {"consistency_score": alignment.get("consistency_score", 0.5)}
        )

        signal = FTSignal(
            signal_id=_generate_signal_id("business_case_align", "business_case", original_str[:100]),
            signal_type="business_case_align",
            source_section="business_case",
            timestamp=datetime.utcnow().isoformat(),
            prompt_input=f"Korrigiere Business Case für {industry}/{company_size}: {original_str}",
            ideal_output=aligned_str,
            original_output=original_str,
            quality_score=quality_score,
            confidence=alignment.get("confidence", 0.7),
            company_size=company_size,
            industry=industry,
            lang=lang,
            metadata={
                "adjustment_reason": alignment.get("reason", ""),
                "adjusted_fields": list(aligned_values.keys()),
            }
        )
        signals.append(signal)

    return signals


def _extract_ai_act_reasoning_signals(
    report_data: Dict[str, Any],
    lang: str = "de",
) -> List[FTSignal]:
    """
    Extract AI Act reasoning signals.

    Captures AI Act compliance reasoning and risk level justifications.
    """
    signals: List[FTSignal] = []

    ai_act_reasoning = report_data.get("_ai_act_reasoning", [])

    for reasoning in ai_act_reasoning:
        if not isinstance(reasoning, dict):
            continue

        input_context = reasoning.get("input_context", "")
        reasoning_output = reasoning.get("reasoning_text", "")
        risk_level = reasoning.get("risk_level", "minimal")

        if not input_context or not reasoning_output:
            continue

        # AI Act reasoning is high-value for training
        quality_score = min(1.0, 0.7 + reasoning.get("completeness_score", 0) * 0.3)

        signal = FTSignal(
            signal_id=_generate_signal_id("ai_act_reasoning", "ai_act", input_context[:100]),
            signal_type="ai_act_reasoning",
            source_section="ai_act",
            timestamp=datetime.utcnow().isoformat(),
            prompt_input=f"Begründe AI Act Risikostufe für: {input_context}",
            ideal_output=reasoning_output,
            original_output=reasoning.get("original_reasoning", reasoning_output),
            quality_score=quality_score,
            confidence=reasoning.get("confidence", 0.8),
            industry=report_data.get("branche", ""),
            lang=lang,
            metadata={
                "risk_level": risk_level,
                "use_cases": reasoning.get("use_cases", []),
                "compliance_gaps": reasoning.get("gaps", []),
            }
        )
        signals.append(signal)

    return signals


def _extract_insight_quality_signals(
    report_data: Dict[str, Any],
    lang: str = "de",
) -> List[FTSignal]:
    """
    Extract insight quality signals.

    Captures when insights were enhanced or corrected for quality.
    """
    signals: List[FTSignal] = []

    insight_improvements = report_data.get("_insight_improvements", [])
    segment_key = report_data.get("_segment_key", "")

    for improvement in insight_improvements:
        if not isinstance(improvement, dict):
            continue

        original = improvement.get("original_insight", "")
        improved = improvement.get("improved_insight", "")
        section = improvement.get("section", "unknown")

        if not original or not improved or original == improved:
            continue

        quality_score = _calculate_quality_score(
            original, improved, "insight_quality",
            {"human_validated": 1.0 if improvement.get("human_validated") else 0.0}
        )

        signal = FTSignal(
            signal_id=_generate_signal_id("insight_quality", section, original[:100]),
            signal_type="insight_quality",
            source_section=section,
            timestamp=datetime.utcnow().isoformat(),
            prompt_input=f"Verbessere Insight für {section}: {original}",
            ideal_output=improved,
            original_output=original,
            quality_score=quality_score,
            confidence=improvement.get("confidence", 0.7),
            segment_key=segment_key,
            lang=lang,
            metadata={
                "improvement_type": improvement.get("type", "general"),
                "added_specificity": improvement.get("added_specificity", False),
            }
        )
        signals.append(signal)

    return signals


def _extract_predictive_drift_signals(
    report_data: Dict[str, Any],
    lang: str = "de",
) -> List[FTSignal]:
    """
    Extract predictive drift signals.

    Captures when predictions were corrected based on actual outcomes.
    """
    signals: List[FTSignal] = []

    drift_corrections = report_data.get("_predictive_drift_corrections", [])

    for correction in drift_corrections:
        if not isinstance(correction, dict):
            continue

        predicted = correction.get("predicted_value", "")
        actual = correction.get("actual_value", "")
        prediction_type = correction.get("prediction_type", "unknown")

        if not predicted or not actual:
            continue

        # Drift signals are valuable for improving predictions
        quality_score = 0.8  # Base high value for outcome-based learning

        signal = FTSignal(
            signal_id=_generate_signal_id("predictive_drift", prediction_type, str(predicted)),
            signal_type="predictive_drift",
            source_section=prediction_type,
            timestamp=datetime.utcnow().isoformat(),
            prompt_input=f"Vorhersage-Korrektur für {prediction_type}: Vorhergesagt={predicted}",
            ideal_output=str(actual),
            original_output=str(predicted),
            quality_score=quality_score,
            confidence=correction.get("confidence", 0.85),
            segment_key=correction.get("segment_key", ""),
            lang=lang,
            metadata={
                "drift_magnitude": correction.get("drift_magnitude", 0),
                "time_to_outcome_days": correction.get("days_to_outcome", 0),
            }
        )
        signals.append(signal)

    return signals


def _extract_smart_default_corrections_signals(
    report_data: Dict[str, Any],
    lang: str = "de",
) -> List[FTSignal]:
    """
    Extract smart default correction signals.

    Captures when smart defaults were overridden by user preferences.
    """
    signals: List[FTSignal] = []

    default_corrections = report_data.get("_smart_default_corrections", [])
    segment_key = report_data.get("_segment_key", "")

    for correction in default_corrections:
        if not isinstance(correction, dict):
            continue

        default_value = correction.get("default_value", "")
        user_value = correction.get("user_preferred_value", "")
        field_name = correction.get("field_name", "unknown")

        if not default_value or not user_value or default_value == user_value:
            continue

        quality_score = _calculate_quality_score(
            str(default_value), str(user_value), "smart_default_corrections"
        )

        signal = FTSignal(
            signal_id=_generate_signal_id("smart_default_corrections", field_name, str(default_value)),
            signal_type="smart_default_corrections",
            source_section=field_name,
            timestamp=datetime.utcnow().isoformat(),
            prompt_input=f"Smart Default Korrektur für {field_name} im Segment {segment_key}",
            ideal_output=str(user_value),
            original_output=str(default_value),
            quality_score=quality_score,
            confidence=0.9,  # High confidence - direct user feedback
            segment_key=segment_key,
            lang=lang,
            metadata={
                "correction_count": correction.get("frequency", 1),
                "field_type": correction.get("field_type", "unknown"),
            }
        )
        signals.append(signal)

    return signals


def _extract_funding_misclassification_signals(
    report_data: Dict[str, Any],
    lang: str = "de",
) -> List[FTSignal]:
    """
    Extract funding misclassification signals.

    Captures when funding recommendations were incorrectly matched.
    """
    signals: List[FTSignal] = []

    misclassifications = report_data.get("_funding_misclassifications", [])
    company_size = report_data.get("unternehmensgroesse", "")
    industry = report_data.get("branche", "")

    for misclass in misclassifications:
        if not isinstance(misclass, dict):
            continue

        wrong_match = misclass.get("incorrect_funding", "")
        correct_match = misclass.get("correct_funding", "")
        reason = misclass.get("reason", "")

        if not wrong_match or not correct_match:
            continue

        quality_score = 0.75  # Moderate value for classification corrections

        signal = FTSignal(
            signal_id=_generate_signal_id("funding_misclassifications", "funding", wrong_match[:50]),
            signal_type="funding_misclassifications",
            source_section="funding_recommendations",
            timestamp=datetime.utcnow().isoformat(),
            prompt_input=f"Förderungs-Klassifikation für {industry}/{company_size}: {wrong_match}",
            ideal_output=correct_match,
            original_output=wrong_match,
            quality_score=quality_score,
            confidence=misclass.get("confidence", 0.7),
            company_size=company_size,
            industry=industry,
            lang=lang,
            metadata={
                "misclassification_reason": reason,
                "eligibility_criteria": misclass.get("criteria", []),
            }
        )
        signals.append(signal)

    return signals


# =============================================================================
# MAIN EXTRACTION FUNCTION
# =============================================================================

def extract_llm_signals(
    report_sections: Dict[str, Any],
    validation_result: Optional[Dict[str, Any]] = None,
    predictive_output: Optional[Dict[str, Any]] = None,
    segment_stats: Optional[Any] = None,
    include_types: Optional[List[str]] = None,
) -> List[FTSignal]:
    """
    Extract fine-tuning signals from a generated report (G17.3-A).

    Processes report data to extract training signals for LLM fine-tuning.
    Signals are normalized and anonymized before return.

    Args:
        report_sections: Complete report sections dictionary
        validation_result: Validation results with warnings/errors
        predictive_output: Predictive engine output (G17.2)
        segment_stats: Segment statistics from feedback analyzer
        include_types: Optional list of signal types to extract (None = all)

    Returns:
        List of FTSignal objects ready for dataset building
    """
    if not FT_SIGNAL_EXTRACTION_ENABLED:
        if FT_SIGNAL_DEBUG_LOGGING:
            log.debug("FT Signal extraction disabled")
        return []

    if not report_sections:
        log.warning("Empty report_sections provided for signal extraction")
        return []

    # Merge all data sources into report_data
    report_data = dict(report_sections)
    if validation_result:
        report_data["_validation_result"] = validation_result
    if predictive_output:
        report_data["_predictive_output"] = predictive_output

    # Extract segment info
    stability = "medium"
    risk_level = "minimal"
    funding_scope = "NONE"
    if segment_stats:
        stability = getattr(segment_stats, "stability", None) or "medium"
        risk_level = getattr(segment_stats, "risk_level", None) or "minimal"
        funding_scope = getattr(segment_stats, "funding_scope", None) or "NONE"
        report_data["_segment_stability"] = stability
        report_data["_risk_level"] = risk_level
        report_data["_funding_scope"] = funding_scope

    # Skip weak segments unless allowed
    if stability == "weak" and not FT_ALLOW_WEAK_SEGMENTS:
        if FT_SIGNAL_DEBUG_LOGGING:
            log.debug("Skipping signal extraction for weak segment")
        return []

    lang = report_data.get("LANG", report_data.get("lang", "de"))

    # Define all extractors
    extractors = {
        "persona_fix": _extract_persona_fix_signals,
        "size_aware_length": _extract_size_aware_length_signals,
        "redundancy_compression": _extract_redundancy_compression_signals,
        "html_repair": _extract_html_repair_signals,
        "business_case_align": _extract_business_case_align_signals,
        "ai_act_reasoning": _extract_ai_act_reasoning_signals,
        "insight_quality": _extract_insight_quality_signals,
        "predictive_drift": _extract_predictive_drift_signals,
        "smart_default_corrections": _extract_smart_default_corrections_signals,
        "funding_misclassifications": _extract_funding_misclassification_signals,
    }

    # Filter extractors if specific types requested
    if include_types:
        extractors = {k: v for k, v in extractors.items() if k in include_types}

    all_signals: List[FTSignal] = []

    for signal_type, extractor in extractors.items():
        try:
            signals = extractor(report_data, lang)
            # Enrich signals with segment info
            for signal in signals:
                signal.stability = stability
                signal.risk_level = risk_level
                signal.funding_scope = funding_scope
            if FT_SIGNAL_DEBUG_LOGGING:
                log.debug(f"Extracted {len(signals)} signals of type {signal_type}")
            all_signals.extend(signals)
        except Exception as e:
            log.error(f"Error extracting {signal_type} signals: {e}")
            continue

    # Filter by confidence threshold
    all_signals = [s for s in all_signals if s.confidence >= FT_MIN_CONFIDENCE_THRESHOLD]

    # Apply normalization and anonymization via add_safety_filters
    processed_signals: List[FTSignal] = []
    for signal in all_signals:
        try:
            normalized = normalize_signal(signal)
            safe_signal = add_safety_filters(normalized)
            if safe_signal:  # May be None if filtered out
                processed_signals.append(safe_signal)
        except Exception as e:
            log.error(f"Error processing signal {signal.signal_id}: {e}")
            continue

    # Limit signals per report
    if len(processed_signals) > FT_MAX_SIGNALS_PER_REPORT:
        # Sort by quality score and take top signals
        processed_signals = sorted(
            processed_signals, key=lambda s: s.quality_score, reverse=True
        )[:FT_MAX_SIGNALS_PER_REPORT]

    log.info(f"Extracted {len(processed_signals)} FT signals from report")
    return processed_signals


def add_safety_filters(signal: FTSignal) -> Optional[FTSignal]:
    """
    Apply safety filters to a signal (G17.3-B).

    - Removes PII
    - Removes freetext references
    - Suppresses signals from weak segments in strict mode
    """
    if not signal:
        return None

    # Check privacy strict mode for weak segments
    if FT_PRIVACY_STRICT_MODE and signal.stability == "weak":
        if FT_SIGNAL_DEBUG_LOGGING:
            log.debug(f"Signal {signal.signal_id} suppressed due to weak segment in strict mode")
        return None

    # Apply PII anonymization
    signal = anonymize_signal(signal)

    return signal


def to_normalized_signal(signal: FTSignal) -> NormalizedSignal:
    """
    Convert FTSignal to NormalizedSignal format for dataset building.

    Returns the standardized JSON structure per G17.3-B spec.
    """
    # Map signal types to normalized categories
    type_map = {
        "persona_fix": "persona",
        "size_aware_length": "logic",
        "redundancy_compression": "logic",
        "html_repair": "html",
        "business_case_align": "business_case",
        "ai_act_reasoning": "ai_act",
        "insight_quality": "insight",
        "predictive_drift": "predictive",
        "smart_default_corrections": "logic",
        "funding_misclassifications": "funding",
    }

    normalized_type = type_map.get(signal.signal_type, signal.signal_type)

    segment = SegmentInfo(
        size=_normalize_company_size(signal.company_size or "team"),
        branch=signal.industry or "other",
        risk=signal.risk_level,
        funding_scope=signal.funding_scope,
        stability=signal.stability,
    )

    return NormalizedSignal(
        signal_type=normalized_type,
        language=signal.lang,
        input_pattern=signal.prompt_input,
        output_target=signal.ideal_output,
        confidence=signal.confidence,
        segment=segment,
    )


def create_signal_batch(
    report_id: str,
    signals: List[FTSignal],
) -> FTSignalBatch:
    """
    Create a batch from extracted signals.

    Args:
        report_id: Unique report identifier
        signals: List of extracted signals

    Returns:
        FTSignalBatch with aggregated metadata
    """
    signal_counts: Dict[str, int] = {}
    total_quality = 0.0

    for signal in signals:
        signal_counts[signal.signal_type] = signal_counts.get(signal.signal_type, 0) + 1
        total_quality += signal.quality_score

    avg_quality = total_quality / len(signals) if signals else 0.0

    return FTSignalBatch(
        report_id=report_id,
        extraction_timestamp=datetime.utcnow().isoformat(),
        signals=signals,
        total_quality_score=avg_quality,
        signal_counts=signal_counts,
    )


def signal_to_training_format(signal: FTSignal) -> Dict[str, Any]:
    """
    Convert a signal to training data format.

    Returns format suitable for OpenAI fine-tuning JSONL.
    """
    return {
        "messages": [
            {"role": "system", "content": f"Du bist ein {signal.signal_type}-Spezialist."},
            {"role": "user", "content": signal.prompt_input},
            {"role": "assistant", "content": signal.ideal_output},
        ],
        "metadata": {
            "signal_id": signal.signal_id,
            "signal_type": signal.signal_type,
            "quality_score": signal.quality_score,
            "confidence": signal.confidence,
            "source_section": signal.source_section,
            "segment_key": signal.segment_key,
            "company_size": signal.company_size,
            "industry": signal.industry,
            "lang": signal.lang,
        }
    }


def batch_to_jsonl(batch: FTSignalBatch) -> str:
    """
    Convert a signal batch to JSONL format for fine-tuning.

    Returns newline-delimited JSON strings.
    """
    lines = []
    for signal in batch.signals:
        training_entry = signal_to_training_format(signal)
        lines.append(json.dumps(training_entry, ensure_ascii=False))
    return "\n".join(lines)


# =============================================================================
# SIGNAL STATISTICS
# =============================================================================

def get_signal_statistics(signals: List[FTSignal]) -> Dict[str, Any]:
    """
    Calculate statistics for a collection of signals.
    """
    if not signals:
        return {
            "total_signals": 0,
            "by_type": {},
            "avg_quality_score": 0.0,
            "avg_confidence": 0.0,
            "anonymized_count": 0,
            "human_validated_count": 0,
        }

    by_type: Dict[str, int] = {}
    total_quality = 0.0
    total_confidence = 0.0
    anonymized = 0
    human_validated = 0

    for signal in signals:
        by_type[signal.signal_type] = by_type.get(signal.signal_type, 0) + 1
        total_quality += signal.quality_score
        total_confidence += signal.confidence
        if signal.is_anonymized:
            anonymized += 1
        if signal.human_validated:
            human_validated += 1

    return {
        "total_signals": len(signals),
        "by_type": by_type,
        "avg_quality_score": total_quality / len(signals),
        "avg_confidence": total_confidence / len(signals),
        "anonymized_count": anonymized,
        "human_validated_count": human_validated,
    }
