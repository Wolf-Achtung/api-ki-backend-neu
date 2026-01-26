#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX-529: Business Case Validation - Prevent Empty Numbers

This module validates business case figures (ROI, Payback, Break-Even) and
replaces invalid/empty values with proper markers instead of showing "0" or "N/A".

Rules:
- ROI/Payback/Break-Even should NEVER show "0" or "N/A" when inputs are missing
- Instead: Insert [INPUT:...] marker and placeholder text
- Log which inputs are missing for debugging

Version: 1.0.0 (FIX-529)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from services.open_inputs_marker import create_marker

log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Patterns that indicate invalid/placeholder values
INVALID_VALUE_PATTERNS = [
    r'^0\s*%?$',           # "0" or "0%"
    r'^0[,.]0+\s*%?$',     # "0.00" or "0,00%"
    r'^N/?A$',             # "N/A" or "NA"
    r'^-$',                # Just a dash
    r'^--$',               # Double dash
    r'^\s*$',              # Empty or whitespace
    r'^nicht verfuegbar$', # "nicht verfuegbar" (i)
    r'^nicht vorhanden$',  # "nicht vorhanden" (i)
    r'^keine angabe$',     # "keine angabe" (i)
    r'^k\.a\.$',           # "k.A." (i)
]

INVALID_PATTERN = re.compile(
    '|'.join(INVALID_VALUE_PATTERNS),
    re.IGNORECASE
)

# Fields that require validation in business case
BC_REQUIRED_FIELDS = {
    "roi_12m": {
        "label": "ROI (12 Monate)",
        "hint": "Wird nach Eingabe von Umsatz und Kosten berechnet",
        "placeholder": "[wird nach Eingabe berechnet]",
    },
    "roi_percent": {
        "label": "ROI Prozent",
        "hint": "Eingabe von Investition und Einsparung erforderlich",
        "placeholder": "[wird nach Eingabe berechnet]",
    },
    "payback_months": {
        "label": "Amortisationszeit",
        "hint": "Abhaengig von Investition und monatlicher Einsparung",
        "placeholder": "[wird nach Eingabe berechnet]",
    },
    "break_even": {
        "label": "Break-Even",
        "hint": "Benoetigt Umsatz- und Kostendaten",
        "placeholder": "[wird nach Eingabe berechnet]",
    },
    "investment": {
        "label": "Investitionssumme",
        "hint": "Bitte Budget im Briefing angeben",
        "placeholder": "[bitte angeben]",
    },
    "yearly_savings": {
        "label": "Jaehrliche Einsparung",
        "hint": "Benoetigt Mitarbeiterzahl und Stundensaetze",
        "placeholder": "[wird nach Eingabe berechnet]",
    },
}

# Input fields that are required for calculations
REQUIRED_INPUTS = {
    "umsatz": {
        "label": "Jahresumsatz",
        "hint": "EUR-Betrag fuer ROI-Berechnung erforderlich",
    },
    "mitarbeiter": {
        "label": "Mitarbeiterzahl",
        "hint": "Anzahl MA fuer Einsparungsberechnung",
    },
    "budget": {
        "label": "KI-Budget",
        "hint": "Geplantes Investitionsbudget in EUR",
    },
    "stundensatz": {
        "label": "Durchschnittlicher Stundensatz",
        "hint": "EUR/Stunde fuer Kostenberechnung",
    },
}


@dataclass
class BCValidationResult:
    """Result of business case validation."""
    is_valid: bool
    missing_inputs: List[str] = field(default_factory=list)
    invalid_fields: List[str] = field(default_factory=list)
    markers_added: List[str] = field(default_factory=list)


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def is_invalid_value(value: Any) -> bool:
    """
    Check if a value is invalid (empty, zero, N/A, etc.).

    Args:
        value: Value to check

    Returns:
        True if the value is invalid
    """
    if value is None:
        return True

    str_value = str(value).strip()

    if not str_value:
        return True

    if INVALID_PATTERN.match(str_value):
        return True

    # Check for zero numeric values
    try:
        num = float(str_value.replace(',', '.').replace('%', '').replace(' ', ''))
        if num == 0:
            return True
    except (ValueError, TypeError):
        pass

    return False


def validate_bc_field(
    field_name: str,
    value: Any,
) -> Tuple[bool, Optional[str]]:
    """
    Validate a single business case field.

    Args:
        field_name: Name of the field
        value: Value to validate

    Returns:
        Tuple of (is_valid, marker_string_if_invalid)
    """
    if not is_invalid_value(value):
        return True, None

    # Get field config
    field_config = BC_REQUIRED_FIELDS.get(field_name)
    if not field_config:
        # Unknown field - use generic marker
        return False, create_marker(
            f"bc_{field_name}",
            field_name.replace("_", " ").title(),
            "Wert fehlt",
        )

    # Create marker for this field
    marker = create_marker(
        f"bc_{field_name}",
        field_config["label"],
        field_config["hint"],
    )

    return False, marker


def validate_business_case_data(
    data: Dict[str, Any],
) -> Tuple[Dict[str, Any], BCValidationResult]:
    """
    Validate business case data and replace invalid values with markers.

    Args:
        data: Business case data dict

    Returns:
        Tuple of (validated_data, BCValidationResult)
    """
    result = BCValidationResult(is_valid=True)
    validated = dict(data)

    # Check each required field
    for field_name, field_config in BC_REQUIRED_FIELDS.items():
        value = data.get(field_name)

        is_valid, marker = validate_bc_field(field_name, value)

        if not is_valid:
            result.is_valid = False
            result.invalid_fields.append(field_name)
            result.markers_added.append(marker or field_name)

            # Replace with placeholder
            validated[field_name] = field_config["placeholder"]

            log.info(
                "[FIX-529][BC-VALIDATE] Invalid value for %s: '%s' -> marker",
                field_name, value
            )

    # Check required input dependencies
    for input_name, input_config in REQUIRED_INPUTS.items():
        if input_name not in data or is_invalid_value(data.get(input_name)):
            result.missing_inputs.append(input_name)

    if result.invalid_fields:
        log.warning(
            "[FIX-529][BC-VALIDATE] Validation failed: %d invalid fields, %d missing inputs",
            len(result.invalid_fields),
            len(result.missing_inputs),
        )

    return validated, result


# =============================================================================
# HTML CONTENT VALIDATION
# =============================================================================

def validate_bc_html_content(
    html: str,
    section_name: str = "",
) -> Tuple[str, List[str]]:
    """
    Validate business case HTML content and replace invalid values.

    Looks for patterns like:
    - ROI: 0%
    - Payback: N/A
    - Break-Even: --

    And replaces them with marker placeholders.

    Args:
        html: HTML content to validate
        section_name: Section name for logging

    Returns:
        Tuple of (validated_html, list_of_markers_added)
    """
    if not html:
        return html, []

    markers_added = []
    result = html

    # Pattern replacements for common invalid presentations
    replacements = [
        # ROI patterns
        (
            r'(ROI[:\s]*)(0\s*%|N/?A|--)',
            lambda m: m.group(1) + create_marker("bc_roi", "ROI", "Wird nach Eingabe berechnet"),
        ),
        # Payback patterns
        (
            r'(Payback|Amortisation)[:\s]*(0\s*(Monate?)?|N/?A|--)',
            lambda m: m.group(1) + ": " + create_marker("bc_payback", "Amortisationszeit", "Benoetigt Investition und Einsparung"),
        ),
        # Break-Even patterns
        (
            r'(Break-?Even)[:\s]*(0|N/?A|--)',
            lambda m: m.group(1) + ": " + create_marker("bc_breakeven", "Break-Even", "Benoetigt Umsatzdaten"),
        ),
        # Investment patterns
        (
            r'(Investition|Investment)[:\s]*(0\s*(EUR|€)?|N/?A|--)',
            lambda m: m.group(1) + ": " + create_marker("bc_investment", "Investition", "Bitte Budget angeben"),
        ),
        # Savings patterns
        (
            r'(Einsparung|Savings?)[:\s]*(0\s*(EUR|€)?|N/?A|--)',
            lambda m: m.group(1) + ": " + create_marker("bc_savings", "Einsparung", "Wird nach Eingabe berechnet"),
        ),
    ]

    for pattern, replacement in replacements:
        matches = list(re.finditer(pattern, result, re.IGNORECASE))
        if matches:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
            markers_added.extend([m.group(0) for m in matches])

    if markers_added:
        log.info(
            "[FIX-529][BC-HTML] Replaced %d invalid values in %s",
            len(markers_added),
            section_name or "content",
        )

    return result, markers_added


def validate_bc_sections(
    sections: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """
    Validate all business case related sections.

    Args:
        sections: Dict of section_key -> content

    Returns:
        Tuple of (validated_sections, stats)
    """
    # Sections that contain business case data
    bc_section_patterns = [
        "BUSINESS_CASE",
        "ROI",
        "INVESTMENT",
        "BC_",
        "PAYBACK",
    ]

    validated = dict(sections)
    stats = {"sections_checked": 0, "markers_added": 0}

    for key, content in sections.items():
        if not isinstance(content, str):
            continue

        # Check if this is a BC-related section
        is_bc_section = any(
            pattern in key.upper() for pattern in bc_section_patterns
        )

        if is_bc_section:
            validated_content, markers = validate_bc_html_content(content, key)
            validated[key] = validated_content
            stats["sections_checked"] += 1
            stats["markers_added"] += len(markers)

    if stats["markers_added"] > 0:
        log.info(
            "[FIX-529][BC-SECTIONS] Validated %d sections, added %d markers",
            stats["sections_checked"],
            stats["markers_added"],
        )

    return validated, stats


# =============================================================================
# INITIALIZATION
# =============================================================================

log.info(
    "[FIX-529] bc_validation loaded: validate_business_case_data, "
    "validate_bc_html_content, validate_bc_sections"
)
