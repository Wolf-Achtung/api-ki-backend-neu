# -*- coding: utf-8 -*-
"""
Section Key Canonical Mapping
==============================

Single source of truth for mapping logical section names to their canonical
*_HTML keys in the sections dict. Used by validator, truncation, and healing.

Every content section has:
- A logical name (e.g., "gamechanger")
- A canonical key (e.g., "GAMECHANGER_HTML") — the rendered/expanded version

The validator, truncation engine, and healing loop all use canonical_key()
to resolve the correct key for content operations.

Version: 1.0.0 (FIX-TEAM-KMU)
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional

log = logging.getLogger(__name__)


# =============================================================================
# CANONICAL MAP: logical name → HTML section key
# =============================================================================

CANONICAL_MAP: Dict[str, str] = {
    "executive_summary": "EXECUTIVE_SUMMARY_HTML",
    "quick_wins": "QUICK_WINS_HTML",
    "business_case": "BUSINESS_CASE_HTML",
    "roadmap_90d": "ROADMAP_90D_HTML",
    "roadmap_12m": "ROADMAP_12M_HTML",
    "risks": "RISKS_HTML",
    "recommendations": "RECOMMENDATIONS_HTML",
    "gamechanger": "GAMECHANGER_HTML",
    "tools_empfehlungen": "TOOLS_EMPFEHLUNGEN_HTML",
    "foerderpotenzial": "FOERDERPOTENZIAL_HTML",
    "org_change": "ORG_CHANGE_HTML",
    "pilot_plan": "PILOT_PLAN_HTML",
    "data_readiness": "DATA_READINESS_HTML",
    "strategie_governance": "STRATEGIE_GOVERNANCE_HTML",
    "unternehmensprofil_markt": "UNTERNEHMENSPROFIL_MARKT_HTML",
    "monetarisierung": "MONETARISIERUNG_HTML",
    "ki_skillplan": "KI_SKILLPLAN_HTML",
    "transparency_box": "TRANSPARENCY_BOX_HTML",
    "technologie_prozesse": "TECHNOLOGIE_PROZESSE_HTML",
    "next_actions": "NEXT_ACTIONS_HTML",
    "ki_stack_summary": "KI_STACK_SUMMARY_HTML",
}

# Reverse mapping: HTML key → logical name
_REVERSE_MAP: Dict[str, str] = {v: k for k, v in CANONICAL_MAP.items()}


# =============================================================================
# FUNCTIONS
# =============================================================================

def canonical_key(logical_name: str) -> str:
    """
    Get the canonical *_HTML key for a logical section name.

    Returns the *_HTML variant if mapped, otherwise returns the input unchanged.

    Examples:
        >>> canonical_key("gamechanger")
        'GAMECHANGER_HTML'
        >>> canonical_key("GAMECHANGER_HTML")
        'GAMECHANGER_HTML'
    """
    if logical_name in CANONICAL_MAP:
        return CANONICAL_MAP[logical_name]
    # Already a canonical key
    if logical_name in _REVERSE_MAP:
        return logical_name
    return logical_name


def logical_name(html_key: str) -> str:
    """
    Get the logical name for a canonical *_HTML key.

    Returns the lowercase logical name if mapped, otherwise returns the input unchanged.

    Examples:
        >>> logical_name("GAMECHANGER_HTML")
        'gamechanger'
        >>> logical_name("gamechanger")
        'gamechanger'
    """
    if html_key in _REVERSE_MAP:
        return _REVERSE_MAP[html_key]
    if html_key in CANONICAL_MAP:
        return html_key
    return html_key


def resolve_key(sections: Dict[str, Any], name: str) -> Optional[str]:
    """
    Resolve which key actually exists in the sections dict.

    Tries canonical *_HTML key first, then logical name.
    Returns the actual key found, or None if neither exists.
    """
    # Try canonical key first
    html_key = CANONICAL_MAP.get(name)
    if html_key and html_key in sections:
        return html_key

    # Try name as-is (could be either logical or HTML)
    if name in sections:
        return name

    # Try reverse mapping (if given an HTML key, try the logical name)
    logical = _REVERSE_MAP.get(name)
    if logical and logical in sections:
        return logical

    return None


def get_canonical_value(
    sections: Dict[str, Any],
    name: str,
    default: Any = None,
) -> Any:
    """
    Get a section's content by trying canonical key first, then logical name.

    Args:
        sections: The sections dict
        name: Logical name or HTML key
        default: Default value if not found

    Returns:
        The section content, preferring the canonical *_HTML version.
    """
    key = resolve_key(sections, name)
    if key is not None:
        return sections[key]
    return default


def html_word_count(html_content: str) -> int:
    """
    Count words in HTML content after stripping tags.

    Utility used by truncation guard and healing loop.
    """
    if not html_content:
        return 0
    text = re.sub(r'<[^>]+>', '', html_content).strip()
    return len(text.split()) if text else 0


log.info(
    "[SECTION-KEYS] Loaded %d canonical mappings",
    len(CANONICAL_MAP),
)
