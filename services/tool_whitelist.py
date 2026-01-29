# -*- coding: utf-8 -*-
"""
FIX-HAUPTLEISTUNG-FIRST: Tool Whitelist Service

Loads and provides access to the tool whitelist configuration.
Used by tools_empfehlungen section to ensure only approved tool
categories are recommended.

Version: 1.0.0
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import yaml

log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG_PATH = Path(__file__).parent.parent / "config" / "tool_whitelist.yaml"

# Cache for loaded config
_config_cache: Optional[Dict[str, Any]] = None


# =============================================================================
# LOADING FUNCTIONS
# =============================================================================

def _load_config() -> Dict[str, Any]:
    """Load and cache the tool whitelist configuration."""
    global _config_cache

    if _config_cache is not None:
        return _config_cache

    if not CONFIG_PATH.exists():
        log.warning(
            "[TOOL-WHITELIST] Config file not found: %s - using defaults",
            CONFIG_PATH
        )
        _config_cache = _get_default_config()
        return _config_cache

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            _config_cache = yaml.safe_load(f) or {}
            log.info(
                "[TOOL-WHITELIST] Loaded config: %d categories, %d size profiles",
                len(_config_cache.get("categories", {})),
                len(_config_cache.get("size_profiles", {})),
            )
            return _config_cache
    except Exception as e:
        log.error("[TOOL-WHITELIST] Failed to load config: %s", e)
        _config_cache = _get_default_config()
        return _config_cache


def _get_default_config() -> Dict[str, Any]:
    """Return minimal default configuration."""
    return {
        "version": "1.0.0-default",
        "categories": {
            "ki_assistent": {
                "id": "ki_assistent",
                "label_de": "KI-Assistent",
                "label_en": "AI Assistant",
            },
            "wissensspeicher": {
                "id": "wissensspeicher",
                "label_de": "Wissensspeicher",
                "label_en": "Knowledge Repository",
            },
            "aufgabenverwaltung": {
                "id": "aufgabenverwaltung",
                "label_de": "Aufgabenverwaltung",
                "label_en": "Task Management",
            },
        },
        "size_profiles": {
            "solo": {"max_tools": 5, "required": ["ki_assistent"], "optional": []},
            "team": {"max_tools": 7, "required": ["ki_assistent"], "optional": []},
            "kmu": {"max_tools": 10, "required": ["ki_assistent"], "optional": []},
        },
        "branch_additions": {},
        "data_classification": {
            "green": {"label_de": "GRÜN", "label_en": "GREEN", "allowed": True},
            "yellow": {"label_de": "GELB", "label_en": "YELLOW", "allowed": "with_conditions"},
            "red": {"label_de": "ROT", "label_en": "RED", "allowed": False},
        },
        "blacklist": [],
    }


def reload_config() -> Dict[str, Any]:
    """Force reload of configuration (for testing)."""
    global _config_cache
    _config_cache = None
    return _load_config()


# =============================================================================
# ACCESS FUNCTIONS
# =============================================================================

def get_categories() -> Dict[str, Dict[str, Any]]:
    """Get all tool categories."""
    config = _load_config()
    return cast(Dict[str, Dict[str, Any]], config.get("categories", {}))


def get_category(category_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific tool category by ID."""
    categories = get_categories()
    return categories.get(category_id)


def get_size_profile(size: str) -> Dict[str, Any]:
    """
    Get the tool profile for a company size.

    Args:
        size: Company size ('solo', 'team', 'kmu')

    Returns:
        Profile with max_tools, required, optional, governance_level
    """
    config = _load_config()
    profiles = config.get("size_profiles", {})

    # Normalize size
    size_lower = str(size).lower().strip()
    if size_lower in ("small_team", "2-10", "2–10"):
        size_lower = "team"
    elif size_lower in ("11-100", "11–100"):
        size_lower = "kmu"
    elif size_lower in ("1", "einzelunternehmer"):
        size_lower = "solo"

    return cast(Dict[str, Any], profiles.get(size_lower, profiles.get("solo", {})))


def get_branch_additions(branch: str) -> Dict[str, Any]:
    """
    Get additional tool categories for a specific branch.

    Args:
        branch: Branch key (e.g., 'beratung', 'finanzen')

    Returns:
        Dict with 'add' (list of category IDs), 'priority', 'compliance_note'
    """
    config = _load_config()
    additions = config.get("branch_additions", {})
    return cast(Dict[str, Any], additions.get(branch.lower(), {}))


def get_recommended_tools(
    size: str,
    branch: Optional[str] = None,
    lang: str = "de"
) -> List[Dict[str, Any]]:
    """
    Get recommended tool categories for a size/branch combination.

    Args:
        size: Company size ('solo', 'team', 'kmu')
        branch: Optional branch key
        lang: Language for labels ('de' or 'en')

    Returns:
        List of tool category dicts with labels
    """
    profile = get_size_profile(size)
    categories = get_categories()

    # Start with required tools
    tool_ids = list(profile.get("required", []))

    # Add optional tools (up to max)
    max_tools = profile.get("max_tools", 5)
    optional = profile.get("optional", [])
    for opt_id in optional:
        if len(tool_ids) < max_tools and opt_id not in tool_ids:
            tool_ids.append(opt_id)

    # Add branch-specific tools
    if branch:
        branch_adds = get_branch_additions(branch)
        for add_id in branch_adds.get("add", []):
            if len(tool_ids) < max_tools and add_id not in tool_ids:
                tool_ids.append(add_id)

    # Build result with labels
    result = []
    label_key = f"label_{lang}" if lang in ("de", "en") else "label_de"

    for tool_id in tool_ids:
        cat = categories.get(tool_id, {})
        if cat:
            result.append({
                "id": tool_id,
                "label": cat.get(label_key, cat.get("label_de", tool_id)),
                "description": cat.get(f"description_{lang}", cat.get("description_de", "")),
                "use_cases": cat.get("use_cases", []),
                "compliance_note": cat.get("compliance_note", ""),
            })

    return result


def get_data_classification(lang: str = "de") -> Dict[str, Dict[str, Any]]:
    """
    Get data classification (green/yellow/red) with labels.

    Args:
        lang: Language for labels

    Returns:
        Dict with green, yellow, red classifications
    """
    config = _load_config()
    classification = config.get("data_classification", {})

    result = {}
    for level, data in classification.items():
        label_key = f"label_{lang}" if lang in ("de", "en") else "label_de"
        result[level] = {
            "label": data.get(label_key, level.upper()),
            "allowed": data.get("allowed", False),
            "conditions": data.get("conditions", []),
            "examples": data.get("examples", []),
        }

    return result


def get_blacklist() -> List[str]:
    """Get list of tools/practices NOT to recommend."""
    config = _load_config()
    return cast(List[str], config.get("blacklist", []))


def is_tool_allowed(tool_name: str, size: str) -> bool:
    """
    Check if a tool/category is allowed for a given size.

    Args:
        tool_name: Tool category ID or name
        size: Company size

    Returns:
        True if allowed, False if forbidden
    """
    profile = get_size_profile(size)
    forbidden = profile.get("forbidden", [])

    tool_lower = tool_name.lower().strip()

    # Check if explicitly forbidden
    if tool_lower in [f.lower() for f in forbidden]:
        return False

    # Check if in required or optional
    allowed = profile.get("required", []) + profile.get("optional", [])
    if tool_lower in [a.lower() for a in allowed]:
        return True

    # Default: allow if not forbidden
    return True


def validate_tool_recommendation(tool_name: str, size: str, branch: Optional[str] = None) -> Dict[str, Any]:
    """
    Validate a tool recommendation and provide feedback.

    Args:
        tool_name: Tool category ID or name
        size: Company size
        branch: Optional branch

    Returns:
        Dict with 'valid', 'message', 'alternative' (if invalid)
    """
    profile = get_size_profile(size)
    categories = get_categories()

    tool_lower = tool_name.lower().strip()

    # Check if it's a known category
    if tool_lower not in categories:
        return {
            "valid": False,
            "message": f"Unknown tool category: {tool_name}",
            "alternative": "KI-Assistent",  # Safe default
        }

    # Check if forbidden for this size
    forbidden = profile.get("forbidden", [])
    if tool_lower in [f.lower() for f in forbidden]:
        return {
            "valid": False,
            "message": f"Tool '{tool_name}' is too complex for {size}",
            "alternative": None,
        }

    return {
        "valid": True,
        "message": "OK",
        "alternative": None,
    }


# =============================================================================
# PROMPT HELPERS
# =============================================================================

def get_whitelist_prompt_block(size: str, branch: Optional[str] = None, lang: str = "de") -> str:
    """
    Generate a prompt block with tool whitelist for injection into prompts.

    Args:
        size: Company size
        branch: Optional branch
        lang: Language

    Returns:
        Formatted string for prompt injection
    """
    tools = get_recommended_tools(size, branch, lang)
    classification = get_data_classification(lang)
    blacklist = get_blacklist()

    if lang == "en":
        header = "## Allowed Tool Categories"
        data_header = "## Data Classification"
        blacklist_header = "## Not Allowed"
    else:
        header = "## Erlaubte Tool-Kategorien"
        data_header = "## Daten-Klassifizierung"
        blacklist_header = "## Nicht erlaubt"

    lines = [header, ""]

    for tool in tools:
        lines.append(f"- **{tool['label']}**: {tool['description']}")
        if tool.get("compliance_note"):
            lines.append(f"  _{tool['compliance_note']}_")

    lines.append("")
    lines.append(data_header)
    for level, data in classification.items():
        allowed_text = "Erlaubt" if data["allowed"] is True else (
            "Mit Bedingungen" if data["allowed"] == "with_conditions" else "Nicht erlaubt"
        )
        if lang == "en":
            allowed_text = "Allowed" if data["allowed"] is True else (
                "With conditions" if data["allowed"] == "with_conditions" else "Not allowed"
            )
        lines.append(f"- **{data['label']}**: {allowed_text}")
        if data.get("examples"):
            lines.append(f"  Beispiele: {', '.join(data['examples'][:3])}")

    lines.append("")
    lines.append(blacklist_header)
    for item in blacklist[:6]:
        lines.append(f"- {item}")

    return "\n".join(lines)


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

# Pre-load config on import
try:
    _load_config()
except Exception as e:
    log.warning("[TOOL-WHITELIST] Failed to pre-load config: %s", e)
