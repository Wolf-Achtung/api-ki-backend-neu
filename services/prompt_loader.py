# -*- coding: utf-8 -*-
from __future__ import annotations

"""Prompt Loader (Gold-Standard+)
Exports:
    - load_prompt(section: str, lang: str = "de", vars_dict: dict | None = None) -> str | dict
      * Loads prompts from ./prompts/<lang>/... with fallback to default language.
      * Supports prompt_manifest.json (global or language-specific) to map sections to files.
      * Performs safe variable interpolation for {{var}} and ${var}.
      * Returns str for .md/.txt; dict for .json (recursively interpolated).
"""

import json
import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

log = logging.getLogger(__name__)

DEFAULT_LANG = os.getenv("PROMPTS_DEFAULT_LANG", "de")
BASE_DIR = Path(os.getenv("PROMPTS_BASE_DIR", "prompts")).resolve()

_SUPPORTED_EXT = (".md", ".txt", ".json", ".yaml", ".yml")


def _interpolate_text(s: str, vars_dict: Optional[Dict[str, Any]]) -> str:
    if not s or not isinstance(s, str) or not vars_dict:
        return s
    def repl_curly(m: re.Match) -> str:
        key = m.group(1).strip()
        return str(vars_dict.get(key, m.group(0)))
    s = re.sub(r"\{\{\s*([a-zA-Z0-9_.-]+)\s*\}\}", repl_curly, s)
    s = re.sub(r"\$\{\s*([a-zA-Z0-9_.-]+)\s*\}", repl_curly, s)
    return s


def _interpolate(obj: Any, vars_dict: Optional[Dict[str, Any]]) -> Any:
    if isinstance(obj, str):
        return _interpolate_text(obj, vars_dict)
    if isinstance(obj, dict):
        return {k: _interpolate(v, vars_dict) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_interpolate(v, vars_dict) for v in obj]
    return obj


@lru_cache(maxsize=64)
def _read_manifest(lang: str) -> Dict[str, str]:
    """Load prompt_manifest.json (lang-specific preferred, else global)."""
    # lang-level manifest
    lang_manifest = BASE_DIR / lang / "prompt_manifest.json"
    if lang_manifest.exists():
        try:
            return json.loads(lang_manifest.read_text(encoding="utf-8"))
        except Exception as exc:
            log.warning("Invalid manifest at %s: %s", lang_manifest, exc)
    # global fallback
    global_manifest = BASE_DIR / "prompt_manifest.json"
    if global_manifest.exists():
        try:
            return json.loads(global_manifest.read_text(encoding="utf-8"))
        except Exception as exc:
            log.warning("Invalid manifest at %s: %s", global_manifest, exc)
    return {}


def _resolve_section_path(section: str, lang: str) -> Tuple[Optional[Path], str]:
    """Resolve a section to a file path using manifest or naming heuristics."""
    manifest = _read_manifest(lang)
    rel = manifest.get(section)
    if rel:
        p = (BASE_DIR / lang / rel).resolve()
        if p.exists():
            return p, lang

    # Heuristics: try known extensions
    for ext in _SUPPORTED_EXT:
        p = (BASE_DIR / lang / f"{section}{ext}").resolve()
        if p.exists():
            return p, lang

    # Fallback to default language
    if lang != DEFAULT_LANG:
        p, used = _resolve_section_path(section, DEFAULT_LANG)
        if p:
            return p, used

    return None, lang


def _read_file(path: Path) -> Any:
    ext = path.suffix.lower()
    if ext in (".md", ".txt"):
        return path.read_text(encoding="utf-8")
    if ext == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if ext in (".yaml", ".yml"):
        try:
            import yaml  # optional
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("YAML prompts require PyYAML installed") from exc
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    raise ValueError(f"Unsupported prompt file extension: {ext}")


def load_prompt(section: str, lang: str = "de", vars_dict: Optional[Dict[str, Any]] = None) -> Any:
    """Public API expected by gpt_analyze.py.

    Returns str for text prompts; dict for structured (JSON/YAML).

    Performs safe interpolation for {{var}} and ${var}.

    """
    if not section or not isinstance(section, str):
        raise ValueError("section must be a non-empty string")

    if not lang:
        lang = DEFAULT_LANG

    p, used_lang = _resolve_section_path(section, lang)
    if not p:
        raise FileNotFoundError(f"Prompt section '{section}' not found for lang '{lang}' in {BASE_DIR}")

    data = _read_file(p)
    return _interpolate(data, vars_dict)
