# utils/llm_overrides.py
# Helper to override model/temperature/max_tokens for specific sections (e.g., Executive Summary)
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
    Env:
      - OPENAI_MODEL_EXEC_SUMMARY
      - OPENAI_TEMP_EXEC_SUMMARY
      - OPENAI_MAX_TOKENS_EXEC_SUMMARY (optional)
    Fallback:
      - OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS
    """
    model = os.getenv("OPENAI_MODEL_EXEC_SUMMARY") or os.getenv("OPENAI_MODEL", "gpt-4o")
    temperature = _get_float("OPENAI_TEMP_EXEC_SUMMARY", _get_float("OPENAI_TEMPERATURE", 0.2))
    max_tokens = _get_int("OPENAI_MAX_TOKENS_EXEC_SUMMARY", _get_int("OPENAI_MAX_TOKENS", 3000))
    # clamp
    temperature = min(max(temperature, 0.0), 2.0)
    max_tokens = max(256, max_tokens)
    return {"model": model, "temperature": temperature, "max_tokens": max_tokens}

def llm_config_for(section: str) -> Dict[str, Any]:
    if (section or "").lower() in {"executive_summary", "exec_summary", "summary"}:
        return exec_summary_llm_config()
    # Gamechanger optional
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    temperature = _get_float("OPENAI_TEMPERATURE", 0.2)
    max_tokens = _get_int("OPENAI_MAX_TOKENS", 3000)
    return {"model": model, "temperature": temperature, "max_tokens": max_tokens}
