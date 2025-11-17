# utils/llm_overrides.py
# Helper to override model/temperature/max_tokens for specific sections (e.g., Executive Summary)
# Safe to import anywhere. No side effects.
from __future__ import annotations
import os
from typing import Dict, Any

def _get_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default

def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default

def exec_summary_llm_config() -> Dict[str, Any]:
    """Return LLM params for the Executive Summary based on env overrides.
    
    Environment variables:
      - OPENAI_MODEL_EXEC_SUMMARY
      - OPENAI_TEMP_EXEC_SUMMARY
      - OPENAI_MAX_TOKENS_EXEC_SUMMARY (optional)
      Fallbacks:
      - OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS
    """
    model = os.getenv("OPENAI_MODEL_EXEC_SUMMARY") or os.getenv("OPENAI_MODEL", "gpt-4o")
    temperature = _get_float("OPENAI_TEMP_EXEC_SUMMARY", _get_float("OPENAI_TEMPERATURE", 0.2))
    max_tokens = _get_int("OPENAI_MAX_TOKENS_EXEC_SUMMARY", _get_int("OPENAI_MAX_TOKENS", 3000))
    # Clamp to sane ranges
    if temperature < 0: temperature = 0.0
    if temperature > 2: temperature = 2.0
    if max_tokens < 256: max_tokens = 256
    return {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

def llm_config_for(section: str) -> Dict[str, Any]:
    """Generic selector for future sections if you want overrides per section."""
    if section.lower() in {"exec_summary", "executive_summary"}:
        return exec_summary_llm_config()
    # default: fall back to global
    return {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
        "temperature": _get_float("OPENAI_TEMPERATURE", 0.2),
        "max_tokens": _get_int("OPENAI_MAX_TOKENS", 3000),
    }
