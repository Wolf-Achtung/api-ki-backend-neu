# -*- coding: utf-8 -*-
"""
Solo-Simplifier Service

Automatically replaces Enterprise terminology with Solo-friendly alternatives
in report content. This ensures Solo reports use accessible language without
corporate jargon.

FIX-SOLO-VEREINFACHUNG: Post-processor for Solo reports.

Version: 1.0.0
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast

log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG_PATH = Path(__file__).parent.parent / "config" / "solo_terms.json"

# Cache for loaded config
_config_cache: Optional[Dict[str, Any]] = None


# =============================================================================
# LOADING
# =============================================================================

def _load_config() -> Dict[str, Any]:
    """Load and cache the solo terms configuration."""
    global _config_cache

    if _config_cache is not None:
        return _config_cache

    if not CONFIG_PATH.exists():
        log.warning(
            "[SOLO-SIMPLIFIER] Config file not found: %s - using empty config",
            CONFIG_PATH
        )
        _config_cache = {"replacements": {}, "blacklist_headlines": [], "whitelist_preferred": []}
        return _config_cache

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            _config_cache = json.load(f)
            log.info(
                "[SOLO-SIMPLIFIER] Loaded config: %d replacements, %d blacklist terms",
                len(_config_cache.get("replacements", {})),
                len(_config_cache.get("blacklist_headlines", [])),
            )
            return _config_cache
    except Exception as e:
        log.error("[SOLO-SIMPLIFIER] Failed to load config: %s", e)
        _config_cache = {"replacements": {}, "blacklist_headlines": [], "whitelist_preferred": []}
        return _config_cache


def reload_config() -> Dict[str, Any]:
    """Force reload of configuration (for testing)."""
    global _config_cache
    _config_cache = None
    return _load_config()


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def get_replacements() -> Dict[str, str]:
    """Get the term replacement mapping."""
    config = _load_config()
    return cast(Dict[str, str], config.get("replacements", {}))


def get_blacklist_headlines() -> List[str]:
    """Get terms that should NEVER appear in headlines for Solo."""
    config = _load_config()
    return cast(List[str], config.get("blacklist_headlines", []))


def get_whitelist_preferred() -> List[str]:
    """Get preferred terms for Solo reports."""
    config = _load_config()
    return cast(List[str], config.get("whitelist_preferred", []))


def simplify_text(text: str, preserve_case: bool = True) -> str:
    """
    Replace Enterprise terminology with Solo-friendly alternatives.

    Args:
        text: The text to simplify
        preserve_case: If True, attempt to preserve original case

    Returns:
        Simplified text with replacements applied
    """
    if not text:
        return text

    replacements = get_replacements()
    result = text

    for old_term, new_term in replacements.items():
        # Use word boundaries to avoid partial replacements
        # e.g., "Team" should not match "Teamwork" partially
        pattern = r'\b' + re.escape(old_term) + r'\b'

        if preserve_case:
            # Preserve case of first character
            def replace_with_case(match: re.Match[str]) -> str:
                matched = match.group(0)
                if matched[0].isupper() and new_term[0].islower():
                    return new_term[0].upper() + new_term[1:]
                elif matched[0].islower() and new_term[0].isupper():
                    return new_term[0].lower() + new_term[1:]
                return new_term

            result = re.sub(pattern, replace_with_case, result)
        else:
            result = re.sub(pattern, new_term, result)

    return result


def simplify_html(html: str) -> str:
    """
    Simplify HTML content for Solo reports.

    Applies term replacements while preserving HTML structure.

    Args:
        html: HTML content to simplify

    Returns:
        Simplified HTML
    """
    if not html:
        return html

    # Don't replace inside HTML tags (attributes, etc.)
    # Split by tags and only replace in text content
    parts = re.split(r'(<[^>]+>)', html)
    result_parts = []

    for part in parts:
        if part.startswith('<') and part.endswith('>'):
            # This is an HTML tag, keep as-is
            result_parts.append(part)
        else:
            # This is text content, apply simplification
            result_parts.append(simplify_text(part))

    return ''.join(result_parts)


def check_blacklist_violations(
    text: str,
    check_headlines_only: bool = False
) -> List[Dict[str, Any]]:
    """
    Check for blacklist term violations in text.

    Args:
        text: Text to check
        check_headlines_only: If True, only check headlines (h1-h6 tags)

    Returns:
        List of violations with term, position, context
    """
    violations: List[Dict[str, Any]] = []
    blacklist = get_blacklist_headlines()

    if check_headlines_only:
        # Extract headline content
        headline_pattern = r'<h[1-6][^>]*>(.*?)</h[1-6]>'
        headlines = re.findall(headline_pattern, text, re.IGNORECASE | re.DOTALL)
        text_to_check = ' '.join(headlines)
    else:
        text_to_check = text

    for term in blacklist:
        pattern = r'\b' + re.escape(term) + r'\b'
        matches = list(re.finditer(pattern, text_to_check, re.IGNORECASE))

        for match in matches:
            # Get context (surrounding text)
            start = max(0, match.start() - 30)
            end = min(len(text_to_check), match.end() + 30)
            context = text_to_check[start:end]

            violations.append({
                "term": term,
                "matched": match.group(0),
                "position": match.start(),
                "context": f"...{context}...",
                "severity": "error" if check_headlines_only else "warning",
            })

    return violations


def validate_solo_content(
    content: str,
    section_name: Optional[str] = None
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validate that Solo content doesn't contain blacklist terms.

    Args:
        content: Content to validate
        section_name: Optional section name for better error messages

    Returns:
        Tuple of (is_valid, list of violations)
    """
    # Check headlines for hard errors
    headline_violations = check_blacklist_violations(content, check_headlines_only=True)

    # Check body for warnings
    body_violations = check_blacklist_violations(content, check_headlines_only=False)

    # Filter out headline violations from body violations (avoid duplicates)
    headline_terms = {v["matched"].lower() for v in headline_violations}
    body_only_violations = [
        v for v in body_violations
        if v["matched"].lower() not in headline_terms
    ]

    all_violations = headline_violations + body_only_violations

    # Add section info
    for v in all_violations:
        v["section"] = section_name or "unknown"

    # Is valid if no headline violations (body warnings are acceptable)
    is_valid = len(headline_violations) == 0

    return is_valid, all_violations


def auto_fix_solo_content(content: str, max_iterations: int = 3) -> Tuple[str, int]:
    """
    Automatically fix Solo content by applying replacements.

    Args:
        content: Content to fix
        max_iterations: Maximum number of replacement passes

    Returns:
        Tuple of (fixed content, number of replacements made)
    """
    total_replacements = 0
    current = content

    for _ in range(max_iterations):
        previous = current
        current = simplify_html(current)

        # Count changes
        if current == previous:
            break

        # Rough count of changes
        total_replacements += 1

    return current, total_replacements


# =============================================================================
# HIGH-LEVEL API
# =============================================================================

def process_solo_section(
    content: str,
    section_name: str,
    auto_fix: bool = True,
    strict: bool = False
) -> Dict[str, Any]:
    """
    Process a section for Solo reports.

    Args:
        content: Section content (HTML)
        section_name: Name of the section
        auto_fix: If True, automatically apply replacements
        strict: If True, raise exception on headline violations

    Returns:
        Dict with processed content, validation results, and fixes applied
    """
    result: Dict[str, Any] = {
        "section": section_name,
        "original_length": len(content),
        "processed_content": content,
        "is_valid": True,
        "violations": [],
        "fixes_applied": 0,
        "auto_fixed": False,
    }

    # Step 1: Validate original content
    is_valid, violations = validate_solo_content(content, section_name)
    result["violations"] = violations

    # Step 2: Auto-fix if enabled
    if auto_fix and violations:
        fixed_content, fix_count = auto_fix_solo_content(content)
        result["processed_content"] = fixed_content
        result["fixes_applied"] = fix_count
        result["auto_fixed"] = True

        # Re-validate after fixes
        is_valid_after, violations_after = validate_solo_content(fixed_content, section_name)
        result["is_valid"] = is_valid_after
        result["violations_after_fix"] = violations_after

        if violations_after:
            log.warning(
                "[SOLO-SIMPLIFIER] Section '%s': %d violations remain after auto-fix",
                section_name,
                len(violations_after)
            )
    else:
        result["is_valid"] = is_valid

    # Step 3: Strict mode - raise on errors
    if strict and not result["is_valid"]:
        headline_errors = [v for v in result.get("violations_after_fix", violations) if v["severity"] == "error"]
        if headline_errors:
            raise ValueError(
                f"Solo section '{section_name}' contains forbidden terms in headlines: "
                f"{[v['term'] for v in headline_errors]}"
            )

    result["processed_length"] = len(result["processed_content"])

    return result


def is_solo_size(size: str) -> bool:
    """Check if the company size is Solo."""
    size_lower = str(size).lower().strip()
    return size_lower in ("solo", "1", "einzelunternehmer", "selbstständig", "freiberufler")


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

# Pre-load config on import
try:
    _load_config()
except Exception as e:
    log.warning("[SOLO-SIMPLIFIER] Failed to pre-load config: %s", e)
