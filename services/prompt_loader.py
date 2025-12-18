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

# =============================================================================
# Multilingual v1: EN alias mapping (German section names → English filenames)
# =============================================================================
# When lang=en and a German-named section is requested, try the English equivalent.
# This prevents EN profiles from falling back to prompts/de/*.md
ALIASES_EN: Dict[str, str] = {
    # German section name → English filename (without .md)
    "strategie_governance": "strategy_governance",
    "wettbewerb_benchmark": "competition_benchmark",
    "technologie_prozesse": "technology_processes",
    "tools_empfehlungen": "tools_recommendations",
    "foerderpotenzial": "funding_potential",
    "ki_aktivitaeten_ziele": "ai_activities_goals",
    "monetarisierung": "monetization",
    "kickoff_vorlage": "kickoff_template",
    # foerderprogramme has its own EN file (with EU-core preference)
    "foerderprogramme": "foerderprogramme",
    # Additional common mappings
    "zusammenfassung": "executive_summary",
    "kurzfazit": "exec_snapshot",
    "naechste_schritte": "next_actions",
    "schnellgewinne": "quick_wins",
    "datenreife": "data_readiness",
    "kosten_uebersicht": "costs_overview",
    "geschaeftsfall": "business_case",
    "org_veraenderung": "org_change",
}

# FIX: Use absolute path based on this file's location
# __file__ = /app/services/prompt_loader.py
# .parent = /app/services/
# .parent.parent = /app/
# / "prompts" = /app/prompts/
if os.getenv("PROMPTS_BASE_DIR"):
    # Allow override via environment variable
    BASE_DIR = Path(os.getenv("PROMPTS_BASE_DIR")).resolve()
else:
    # Default: Calculate from this file's location (works everywhere)
    BASE_DIR = Path(__file__).resolve().parent.parent / "prompts"

log.info(f"🔍 Prompt loader initialized: BASE_DIR={BASE_DIR} (exists: {BASE_DIR.exists()})")

_SUPPORTED_EXT = (".md", ".txt", ".json", ".yaml", ".yml")


def _interpolate_text(s: str, vars_dict: Optional[Dict[str, Any]]) -> str:
    if not isinstance(s, str) or not vars_dict:
        return s

    # 🎯 JINJA2-RENDERING: Wenn Jinja2-Tags vorhanden sind, rendere mit Jinja2
    if "{% " in s or "{%" in s:
        try:
            from jinja2 import Environment, BaseLoader
            env = Environment(loader=BaseLoader(), autoescape=False)
            template = env.from_string(s)
            s = template.render(**vars_dict)
        except Exception as e:
            log.warning(f"⚠️ Jinja2 rendering failed, falling back to simple substitution: {e}")

    # {{ key }} style (simple substitution for non-Jinja2 cases or after Jinja2 rendering)
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
            data = json.loads(lang_manifest.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            log.warning("Invalid manifest at %s: %s", lang_manifest, exc)
    # fallback to global manifest
    global_manifest = BASE_DIR / "prompt_manifest.json"
    if global_manifest.exists():
        try:
            data = json.loads(global_manifest.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            log.warning("Invalid manifest at %s: %s", global_manifest, exc)
    return {}


def _resolve_section_path(section: str, lang: str, _tried_alias: bool = False) -> Tuple[Optional[Path], str]:
    """
    Resolve section name to file path.

    Multilingual v1: For lang=en, tries ALIASES_EN mapping before fallback.
    This ensures German-named sections find their English equivalents.
    """
    manifest = _read_manifest(lang)
    if isinstance(manifest, dict):
        rel = manifest.get(section)
        if isinstance(rel, str):
            p = (BASE_DIR / lang / rel).resolve()
            if p.exists():
                log.debug(f"✅ Found prompt via manifest: {p}")
                return p, lang

    # try common extensions
    for ext in _SUPPORTED_EXT:
        p = (BASE_DIR / lang / f"{section}{ext}").resolve()
        if p.exists():
            log.debug(f"✅ Found prompt: {p}")
            return p, lang

    # =========================================================================
    # Multilingual v1: Try EN alias before falling back to DE
    # =========================================================================
    if lang == "en" and not _tried_alias:
        alias = ALIASES_EN.get(section)
        if alias and alias != section:
            log.debug(f"🔄 Trying EN alias: {section} → {alias}")
            result = _resolve_section_path(alias, lang, _tried_alias=True)
            if result[0]:
                return result

    # =========================================================================
    # HARD BLOCK: EN must NEVER fall back to DE
    # =========================================================================
    if lang == "en":
        log.warning(f"❌ EN prompt '{section}' not found (no DE fallback allowed)")
        return None, lang

    # fallback to default lang (only for non-EN)
    if lang != DEFAULT_LANG:
        log.debug(f"⚠️ Prompt '{section}' not found for lang '{lang}', trying default lang '{DEFAULT_LANG}'")
        return _resolve_section_path(section, DEFAULT_LANG)

    log.warning(f"❌ Prompt '{section}' not found in {BASE_DIR / lang}/ (tried extensions: {_SUPPORTED_EXT})")
    return None, lang


def _read_file(path: Path) -> Any:
    ext = path.suffix.lower()
    if ext in (".md", ".txt"):
        return path.read_text(encoding="utf-8")
    if ext == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    if ext in (".yaml", ".yml"):
        try:
            import yaml
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("YAML support requires PyYAML installed") from exc
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    raise ValueError(f"Unsupported prompt file extension: {ext}")


def load_prompt(section: str, lang: str = "de", vars_dict: Optional[Dict[str, Any]] = None) -> Any:
    if not section or not isinstance(section, str):
        raise ValueError("section must be a non-empty string")

    lang = lang or DEFAULT_LANG

    # 3.1.4.11: Normalize language variants (en-US, EN, en_GB → en)
    lang_norm = str(lang).lower().strip()
    if lang_norm.startswith("en"):
        lang = "en"
    else:
        lang = "de"  # Only de/en supported

    requested_lang = lang  # Store original request for guardrail check
    path, used_lang = _resolve_section_path(section, lang)
    
    if not path:
        # More detailed error message for debugging
        error_msg = (
            f"Prompt section '{section}' not found for lang '{lang}'\n"
            f"  BASE_DIR: {BASE_DIR}\n"
            f"  Expected path: {BASE_DIR / lang / section}_de.md\n"
            f"  BASE_DIR exists: {BASE_DIR.exists()}\n"
        )
        if BASE_DIR.exists():
            lang_dir = BASE_DIR / lang
            if lang_dir.exists():
                files = list(lang_dir.glob("*.md"))
                error_msg += f"  Files in {lang_dir}: {[f.name for f in files[:5]]}\n"
            else:
                error_msg += f"  Language directory {lang_dir} does not exist!\n"
        log.error(error_msg)
        raise FileNotFoundError(error_msg)

    # 3.1.4.11: HARD GUARDRAIL - EN requests must NEVER resolve to DE prompts
    # This prevents silent fallback from prompts/en/* to prompts/de/*
    path_str = str(path).replace("\\", "/")  # Normalize for Windows compatibility
    if requested_lang == "en" and "/prompts/de/" in path_str:
        raise RuntimeError(
            f"EN prompt routing violation: section={section} "
            f"requested_lang={requested_lang} resolved_path={path} "
            f"(DE fallback is forbidden for EN profiles)"
        )

    # 3.1.4.9/3.1.4.11: Debug trace for prompt routing verification
    log.info("[prompt_loader] section=%s requested_lang=%s used_lang=%s path=%s",
             section, requested_lang, used_lang, path)
    payload = _read_file(path)
    return _interpolate(payload, vars_dict)
