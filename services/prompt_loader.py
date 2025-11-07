# -*- coding: utf-8 -*-
from __future__ import annotations

"""Prompt Loader (Gold‑Standard+)
Exports a single API expected by gpt_analyze.py:

    load_prompt(section: str, lang: str = "de", vars_dict: dict | None = None) -> str | dict

Features
- Looks up prompts under ./prompts/<lang>/... (default lang from env PROMPTS_DEFAULT_LANG=de)
- Supports prompt_manifest.json (global or per language)
- Fallbacks: .md/.txt/.json/.yaml|.yml
- Safe variable interpolation for {{var}} and ${var} in text and structured prompts
- No hard runtime deps beyond stdlib (yaml is optional)
"""

import json
import os
import re
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

__all__ = ["load_prompt"]

log = logging.getLogger(__name__)

DEFAULT_LANG = os.getenv("PROMPTS_DEFAULT_LANG", "de")
BASE_DIR = Path(os.getenv("PROMPTS_BASE_DIR", "prompts")).resolve()
_SUPPORTED_EXT = (".md", ".txt", ".json", ".yaml", ".yml")


def _interpolate_text(s: str, vars_dict: Optional[Dict[str, Any]]) -> str:
    if not isinstance(s, str) or not vars_dict:
        return s
    # {{ key }} style
    def _repl_curly(m: re.Match) -> str:
        key = m.group(1).strip()
        return str(vars_dict.get(key, m.group(0)))
    s = re.sub(r"\{\{\s*([a-zA-Z0-9_.-]+)\s*\}\}", _repl_curly, s)
    # ${ key } style
    s = re.sub(r"\$\{\s*([a-zA-Z0-9_.-]+)\s*\}", _repl_curly, s)
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
def _read_manifest(lang: str) -> Dict[str, Any]:
    # prefer language-specific manifest
    lang_manifest = BASE_DIR / lang / "prompt_manifest.json"
    if lang_manifest.exists():
        try:
            return json.loads(lang_manifest.read_text(encoding="utf-8"))
        except Exception as exc:
            log.warning("Invalid manifest at %s: %s", lang_manifest, exc)
    # fallback to global manifest
    global_manifest = BASE_DIR / "prompt_manifest.json"
    if global_manifest.exists():
        try:
            return json.loads(global_manifest.read_text(encoding="utf-8"))
        except Exception as exc:
            log.warning("Invalid manifest at %s: %s", global_manifest, exc)
    return {}


def _resolve_section_path(section: str, lang: str) -> Tuple[Optional[Path], str]:
    manifest = _read_manifest(lang)
    if isinstance(manifest, dict):
        rel = manifest.get(section)
        if isinstance(rel, str):
            p = (BASE_DIR / lang / rel).resolve()
            if p.exists():
                return p, lang

    # try common extensions
    for ext in _SUPPORTED_EXT:
        p = (BASE_DIR / lang / f"{section}{ext}").resolve()
        if p.exists():
            return p, lang

    # fallback to default lang
    if lang != DEFAULT_LANG:
        return _resolve_section_path(section, DEFAULT_LANG)

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
            raise RuntimeError("YAML support requires PyYAML installed") from exc
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    raise ValueError(f"Unsupported prompt file extension: {ext}")


def load_prompt(section: str, lang: str = "de", vars_dict: Optional[Dict[str, Any]] = None) -> Any:
    if not section or not isinstance(section, str):
        raise ValueError("section must be a non-empty string")

    lang = lang or DEFAULT_LANG
    path, used_lang = _resolve_section_path(section, lang)
    if not path:
        raise FileNotFoundError(f"Prompt section '{section}' not found for lang '{lang}' in {BASE_DIR}")

    payload = _read_file(path)
    return _interpolate(payload, vars_dict)
