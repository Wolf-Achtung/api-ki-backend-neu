# -*- coding: utf-8 -*-
"""
FIX-BRANCH-13 TASK 2: Company Size Normalizer

Normalizes unternehmensgroesse values from the questionnaire form.
Handles En-Dash (–) vs regular dash (-) robustly.

Form values from formbuilder_de_SINGLE_FULL.js:
  - "1" → solo
  - "2–10" (En-Dash U+2013) → small_team
  - "11–100" (En-Dash U+2013) → kmu

Version: 1.0.0 (FIX-BRANCH-13)
"""
from __future__ import annotations

import logging
import re
from typing import Dict, Optional, Any

log = logging.getLogger(__name__)

# =============================================================================
# COMPANY SIZE BUCKETS
# =============================================================================

# Bucket definitions with employee ranges
# "segment" maps to the canonical key used by healer, validator, and final-pass
SIZE_BUCKETS = {
    "solo": {"min": 1, "max": 1, "label_de": "Einzelunternehmer", "label_en": "Solo", "segment": "solo"},
    "small_team": {"min": 2, "max": 10, "label_de": "Kleines Team", "label_en": "Small Team", "segment": "team"},
    "kmu": {"min": 11, "max": 100, "label_de": "KMU", "label_en": "SME", "segment": "kmu"},
}

# Direct value mappings (normalized - all dashes converted to hyphen)
DIRECT_MAPPINGS = {
    "1": "solo",
    "2-10": "small_team",
    "11-100": "kmu",
}


# =============================================================================
# NORMALIZATION FUNCTION
# =============================================================================

def _normalize_dash(value: str) -> str:
    """
    Normalize all dash variants to regular hyphen.

    Handles:
    - En-dash (–, U+2013)
    - Em-dash (—, U+2014)
    - Minus sign (−, U+2212)
    - Regular hyphen-minus (-, U+002D)
    """
    if not value:
        return ""

    # Replace all dash variants with regular hyphen
    result = value
    result = result.replace("–", "-")  # En-dash
    result = result.replace("—", "-")  # Em-dash
    result = result.replace("−", "-")  # Minus sign

    return result.strip()


def normalize_company_size(value: str) -> Dict[str, Any]:
    """
    Normalize a company size value from the questionnaire.

    Args:
        value: Raw company size value (e.g., "2–10", "2-10", "1", "11–100")

    Returns:
        Dict with:
            - bucket: "solo" | "small_team" | "kmu"
            - min: Minimum employee count
            - max: Maximum employee count
            - label_de: German label
            - label_en: English label
            - raw: Original input value
            - normalized: Dash-normalized value

    Examples:
        >>> normalize_company_size("2–10")
        {"bucket": "small_team", "min": 2, "max": 10, ...}

        >>> normalize_company_size("2-10")
        {"bucket": "small_team", "min": 2, "max": 10, ...}
    """
    if not value:
        log.warning("[FIX-BRANCH-13] Empty company_size, defaulting to 'solo'")
        return {
            "bucket": "solo",
            "segment": "solo",
            "min": 1,
            "max": 1,
            "label_de": "Einzelunternehmer",
            "label_en": "Solo",
            "raw": value,
            "normalized": "",
        }

    # Normalize dashes
    normalized = _normalize_dash(value)

    # 1) Direct mapping lookup
    if normalized in DIRECT_MAPPINGS:
        bucket = DIRECT_MAPPINGS[normalized]
        bucket_data = SIZE_BUCKETS[bucket]
        log.debug("[FIX-BRANCH-13] Direct match: '%s' → '%s'", value, bucket)
        return {
            "bucket": bucket,
            "segment": bucket_data["segment"],
            "min": bucket_data["min"],
            "max": bucket_data["max"],
            "label_de": bucket_data["label_de"],
            "label_en": bucket_data["label_en"],
            "raw": value,
            "normalized": normalized,
        }

    # 2) Try to parse numeric range
    range_match = re.match(r'^(\d+)\s*-\s*(\d+)$', normalized)
    if range_match:
        min_val = int(range_match.group(1))
        max_val = int(range_match.group(2))

        # Determine bucket based on range
        if max_val <= 1:
            bucket = "solo"
        elif max_val <= 10:
            bucket = "small_team"
        else:
            bucket = "kmu"

        bucket_data = SIZE_BUCKETS[bucket]
        log.debug("[FIX-BRANCH-13] Parsed range: '%s' → '%s' (%d-%d)", value, bucket, min_val, max_val)
        return {
            "bucket": bucket,
            "segment": bucket_data["segment"],
            "min": min_val,
            "max": max_val,
            "label_de": bucket_data["label_de"],
            "label_en": bucket_data["label_en"],
            "raw": value,
            "normalized": normalized,
        }

    # 3) Try to parse single number
    single_match = re.match(r'^(\d+)$', normalized)
    if single_match:
        num = int(single_match.group(1))

        # Determine bucket based on single value
        if num <= 1:
            bucket = "solo"
        elif num <= 10:
            bucket = "small_team"
        else:
            bucket = "kmu"

        bucket_data = SIZE_BUCKETS[bucket]
        log.debug("[FIX-BRANCH-13] Parsed single: '%s' → '%s' (count=%d)", value, bucket, num)
        return {
            "bucket": bucket,
            "segment": bucket_data["segment"],
            "min": num,
            "max": num,
            "label_de": bucket_data["label_de"],
            "label_en": bucket_data["label_en"],
            "raw": value,
            "normalized": normalized,
        }

    # 4) Try bucket name matching (for backwards compat with "solo", "team", "kmu")
    lower_val = normalized.lower()
    if "solo" in lower_val or "einzel" in lower_val or "selbst" in lower_val:
        bucket = "solo"
    elif "team" in lower_val or "klein" in lower_val:
        bucket = "small_team"
    elif "kmu" in lower_val or "mittel" in lower_val or "sme" in lower_val:
        bucket = "kmu"
    else:
        # Default fallback
        log.warning("[FIX-BRANCH-13] Unknown company_size '%s', defaulting to 'solo'", value)
        bucket = "solo"

    bucket_data = SIZE_BUCKETS[bucket]
    return {
        "bucket": bucket,
        "segment": bucket_data["segment"],
        "min": bucket_data["min"],
        "max": bucket_data["max"],
        "label_de": bucket_data["label_de"],
        "label_en": bucket_data["label_en"],
        "raw": value,
        "normalized": normalized,
    }


def get_company_size_bucket(value: str) -> str:
    """
    Get just the bucket name for a company size value.

    Convenience function that returns only the bucket string.

    Args:
        value: Raw company size value

    Returns:
        Bucket name: "solo" | "small_team" | "kmu"
    """
    result = normalize_company_size(value)["bucket"]
    return str(result)  # Explicit cast for mypy


def get_segment(value: str) -> str:
    """
    Get the canonical segment key for healer/validator/final-pass.

    Maps small_team → team so downstream code can use 'team' consistently.

    Args:
        value: Raw company size value

    Returns:
        Segment key: "solo" | "team" | "kmu"
    """
    result = normalize_company_size(value)["segment"]
    return str(result)


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[FIX-BRANCH-13] Company Size Normalizer loaded - %d buckets, %d direct mappings",
    len(SIZE_BUCKETS),
    len(DIRECT_MAPPINGS),
)
