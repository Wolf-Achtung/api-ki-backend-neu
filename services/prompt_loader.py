# -*- coding: utf-8 -*-
from __future__ import annotations

"""Prompt Loader (Gold‑Standard+ / FIX-505)
Exports a single API expected by gpt_analyze.py:

    load_prompt(section: str, lang: str = "de", vars_dict: dict | None = None) -> str | dict

Features
- Looks up prompts under ./prompts/<lang>/... (default lang from env PROMPTS_DEFAULT_LANG=de)
- Supports prompt_manifest.json (global or per language)
- Fallbacks: .md/.txt/.json/.yaml|.yml
- Safe variable interpolation for {{var}} and ${var} in text and structured prompts
- No hard runtime deps beyond stdlib (yaml is optional)

FIX-505 Additions:
- Cycle detection for Jinja2 includes (prevents infinite recursion)
- STRICT_MODE support (no fallback to simple substitution when enabled)
- Enhanced logging with [FIX-505] prefix for diagnostics
"""

import json
import os
import re
import logging
import contextvars
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

__all__ = [
    "load_prompt", "clear_prompt_cache", "get_prompt_info", "diagnose_prompt_system",
    "PromptIncludeCycleError", "check_prompt_cycles"
]

log = logging.getLogger(__name__)

DEFAULT_LANG = os.getenv("PROMPTS_DEFAULT_LANG", "de")

# FIX-505: STRICT_MODE flag - no fallback to simple substitution when enabled
RELEASE_STRICT_MODE = os.getenv("RELEASE_STRICT_MODE", "0") in ("1", "true", "True")

# FIX-505: Contextvar for tracking include stack (thread-safe)
_include_stack: contextvars.ContextVar[List[str]] = contextvars.ContextVar('include_stack', default=[])


class PromptIncludeCycleError(RuntimeError):
    """FIX-505: Raised when a cycle is detected in prompt includes."""

    def __init__(self, chain: List[str], section: str):
        self.chain = chain
        self.section = section
        chain_str = " -> ".join(chain)
        super().__init__(
            f"[FIX-505][PROMPT][CYCLE] Cycle detected in section={section}: {chain_str}"
        )

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


class CycleDetectingLoader:
    """
    FIX-505: Jinja2 Loader wrapper that detects include cycles.

    This loader wraps the standard FileSystemLoader and tracks the include stack
    using a contextvar to detect cycles before they cause recursion depth errors.
    """

    def __init__(self, loaders, section: str):
        from jinja2 import ChoiceLoader
        self._inner_loader = ChoiceLoader(loaders)
        self._section = section

    def get_source(self, environment, template_name: str):
        """Get template source, checking for cycles first."""
        # Get current include stack
        stack = _include_stack.get()

        # Check for cycle
        if template_name in stack:
            cycle_chain = stack + [template_name]
            log.error(
                "[FIX-505][PROMPT][CYCLE] section=%s chain=%s",
                self._section,
                " -> ".join(cycle_chain)
            )
            raise PromptIncludeCycleError(cycle_chain, self._section)

        # Push to stack
        new_stack = stack + [template_name]
        _include_stack.set(new_stack)

        try:
            source, filename, uptodate = self._inner_loader.get_source(environment, template_name)
            return source, filename, uptodate
        finally:
            # Pop from stack (restore previous state)
            _include_stack.set(stack)

    def list_templates(self):
        return self._inner_loader.list_templates()


def _interpolate_text(
    s: str,
    vars_dict: Optional[Dict[str, Any]],
    lang: str = "de",
    section: str = "unknown",
    strict_mode: Optional[bool] = None,
) -> str:
    """
    Interpolate variables in text, with Jinja2 support and cycle detection.

    FIX-505 Enhancements:
    - Cycle detection for Jinja2 includes
    - STRICT_MODE: no fallback on Jinja2 errors
    - Enhanced logging with [FIX-505] prefix
    """
    if not isinstance(s, str) or not vars_dict:
        return s

    # Determine strict mode
    is_strict = strict_mode if strict_mode is not None else RELEASE_STRICT_MODE

    # 🎯 JINJA2-RENDERING: Wenn Jinja2-Tags vorhanden sind, rendere mit Jinja2
    if "{% " in s or "{%" in s:
        log.debug(
            "[FIX-505][PROMPT] render start section=%s lang=%s strict=%d",
            section, lang, int(is_strict)
        )

        try:
            from jinja2 import Environment, FileSystemLoader

            # FIX-497: Use FileSystemLoader to support {% include %} statements
            # Load from both language-specific and shared prompt directories
            prompt_dirs = [
                str(BASE_DIR / lang),  # Language-specific prompts first
                str(BASE_DIR / "de"),  # Fallback to German prompts
                str(BASE_DIR),         # Base prompts directory
            ]
            loaders = [FileSystemLoader(d) for d in prompt_dirs if Path(d).exists()]

            # FIX-505: Use cycle-detecting loader
            loader = CycleDetectingLoader(loaders, section)

            # Reset include stack for this render
            _include_stack.set([])

            env = Environment(loader=loader, autoescape=False)
            template = env.from_string(s)
            rendered = template.render(**vars_dict)

            # Count includes for logging
            include_count = s.count("{% include")
            log.info(
                "[FIX-505][PROMPT] render ok section=%s bytes=%d includes=%d",
                section, len(rendered), include_count
            )

            s = rendered

        except PromptIncludeCycleError:
            # Re-raise cycle errors - these should always fail
            raise

        except RecursionError as e:
            # RecursionError indicates a cycle we didn't catch
            log.error(
                "[FIX-505][PROMPT][CYCLE] section=%s recursion_error=%s",
                section, str(e)[:100]
            )
            if is_strict:
                raise RuntimeError(
                    f"[FIX-505][PROMPT] STRICT_MODE: Jinja2 recursion error in section={section}. "
                    f"This indicates a template cycle that must be fixed."
                ) from e
            else:
                log.warning(
                    "[FIX-505][PROMPT][FALLBACK] section=%s reason=RecursionError",
                    section
                )

        except Exception as e:
            error_msg = str(e)[:200]
            log.error(
                "[FIX-505][PROMPT] Jinja2 error section=%s error=%s",
                section, error_msg
            )

            if is_strict:
                raise RuntimeError(
                    f"[FIX-505][PROMPT] STRICT_MODE: Jinja2 rendering failed for section={section}. "
                    f"Error: {error_msg}"
                ) from e
            else:
                log.warning(
                    "[FIX-505][PROMPT][FALLBACK] section=%s reason=%s",
                    section, error_msg
                )

    # {{ key }} style (simple substitution for non-Jinja2 cases or after Jinja2 rendering)
    def _repl_curly(m: re.Match) -> str:
        key = m.group(1).strip()
        return str(vars_dict.get(key, m.group(0)))
    s = re.sub(r"\{\{\s*([a-zA-Z0-9_.-]+)\s*\}\}", _repl_curly, s)
    # ${ key } style
    s = re.sub(r"\$\{\s*([a-zA-Z0-9_.-]+)\s*\}", _repl_curly, s)
    return s


def _interpolate(
    obj: Any,
    vars_dict: Optional[Dict[str, Any]],
    lang: str = "de",
    section: str = "unknown",
    strict_mode: Optional[bool] = None,
) -> Any:
    """
    Recursively interpolate variables in text, dicts, and lists.

    FIX-505: Now passes section and strict_mode for proper error handling.
    """
    if isinstance(obj, str):
        return _interpolate_text(obj, vars_dict, lang=lang, section=section, strict_mode=strict_mode)
    if isinstance(obj, dict):
        return {k: _interpolate(v, vars_dict, lang=lang, section=section, strict_mode=strict_mode) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_interpolate(v, vars_dict, lang=lang, section=section, strict_mode=strict_mode) for v in obj]
    return obj


def check_prompt_cycles(base_dir: Optional[Path] = None, langs: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    FIX-505: Preflight check for prompt template cycles.

    Scans all prompt files for {% include %} statements and builds a dependency graph,
    then checks for cycles without actually rendering templates.

    Args:
        base_dir: Base prompt directory (defaults to BASE_DIR)
        langs: Languages to check (defaults to ["de", "en"])

    Returns:
        Dict with:
        - cycles: List of detected cycles (each is a list of template names)
        - warnings: List of warning messages
        - graph: Dependency graph for debugging
    """
    import re

    base = base_dir or BASE_DIR
    check_langs = langs or ["de", "en"]

    result = {
        "cycles": [],
        "warnings": [],
        "graph": {},
        "checked_files": 0,
    }

    include_pattern = re.compile(r'{%\s*include\s+["\']([^"\']+)["\']')

    # Patterns to strip before searching for includes (documentation/examples)
    strip_patterns = [
        # Remove {% raw %}...{% endraw %} blocks
        re.compile(r'{%\s*raw\s*%}.*?{%\s*endraw\s*%}', re.DOTALL),
        # Remove HTML comments <!-- ... -->
        re.compile(r'<!--.*?-->', re.DOTALL),
        # Remove markdown code blocks ```...```
        re.compile(r'```.*?```', re.DOTALL),
    ]

    for lang in check_langs:
        lang_dir = base / lang
        if not lang_dir.exists():
            result["warnings"].append(f"Language directory not found: {lang_dir}")
            continue

        # Build dependency graph
        deps: Dict[str, Set[str]] = {}

        for prompt_file in lang_dir.glob("*.md"):
            result["checked_files"] += 1
            try:
                content = prompt_file.read_text(encoding="utf-8")

                # Strip documentation blocks before finding includes
                # This prevents false positives from example code in comments
                stripped_content = content
                for strip_pat in strip_patterns:
                    stripped_content = strip_pat.sub('', stripped_content)

                includes = include_pattern.findall(stripped_content)

                file_key = f"{lang}/{prompt_file.name}"
                deps[file_key] = set()

                for inc in includes:
                    # Normalize include path
                    inc_key = f"{lang}/{inc}" if "/" not in inc else inc
                    deps[file_key].add(inc_key)

            except Exception as e:
                result["warnings"].append(f"Error reading {prompt_file}: {e}")

        result["graph"][lang] = {k: list(v) for k, v in deps.items()}

        # Detect cycles using DFS
        def find_cycles(node: str, visited: Set[str], path: List[str]) -> Optional[List[str]]:
            if node in path:
                cycle_start = path.index(node)
                return path[cycle_start:] + [node]

            if node in visited:
                return None

            visited.add(node)
            path.append(node)

            for neighbor in deps.get(node, set()):
                cycle = find_cycles(neighbor, visited, path)
                if cycle:
                    return cycle

            path.pop()
            return None

        visited: Set[str] = set()
        for node in deps:
            if node not in visited:
                cycle = find_cycles(node, visited, [])
                if cycle:
                    result["cycles"].append(cycle)
                    log.error(
                        "[FIX-505][PROMPT][CYCLE-PREFLIGHT] Detected cycle: %s",
                        " -> ".join(cycle)
                    )

    if result["cycles"]:
        log.error(
            "[FIX-505][PROMPT][CYCLE-PREFLIGHT] Found %d cycle(s) in prompt templates!",
            len(result["cycles"])
        )
    else:
        log.info(
            "[FIX-505][PROMPT][CYCLE-PREFLIGHT] No cycles detected in %d prompt files",
            result["checked_files"]
        )

    return result


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
    # FIX-497: Pass lang to _interpolate for proper include resolution
    # FIX-505: Pass section for cycle detection and strict mode handling
    return _interpolate(payload, vars_dict, lang=used_lang, section=section)


# =============================================================================
# CACHE MANAGEMENT & DEBUGGING (Sprint G19: Cache-Clear für Deployments)
# =============================================================================

def clear_prompt_cache() -> Dict[str, Any]:
    """
    Clear the manifest LRU cache to force re-reading from disk.

    Call this after deployment or when prompts are updated to ensure
    fresh content is loaded. Note: The actual prompt files are NOT cached,
    only the manifest.json files are cached via LRU.

    Returns:
        Dict with cache clear status and info
    """
    try:
        cache_info_before = _read_manifest.cache_info()
        _read_manifest.cache_clear()
        cache_info_after = _read_manifest.cache_info()

        log.info("🔄 [prompt_loader] Manifest cache cleared. Before: %s, After: %s",
                 cache_info_before, cache_info_after)

        return {
            "success": True,
            "message": "Manifest cache cleared successfully",
            "cache_before": {
                "hits": cache_info_before.hits,
                "misses": cache_info_before.misses,
                "size": cache_info_before.currsize,
            },
            "cache_after": {
                "hits": cache_info_after.hits,
                "misses": cache_info_after.misses,
                "size": cache_info_after.currsize,
            },
            "note": "Prompt files are read fresh on each request (no LRU cache on file content)"
        }
    except Exception as e:
        log.error("❌ [prompt_loader] Failed to clear cache: %s", e)
        return {
            "success": False,
            "error": str(e)
        }


def get_prompt_info(section: str, lang: str = "de") -> Dict[str, Any]:
    """
    Get debugging info about a prompt without loading its full content.

    Useful for verifying that prompts are being loaded from the correct path
    and that files exist after deployment.

    Args:
        section: Prompt section name (e.g., "quick_wins", "roadmap_90d")
        lang: Language code ("de" or "en")

    Returns:
        Dict with prompt path, existence, size, and modification time
    """
    import os
    from datetime import datetime

    lang_norm = str(lang).lower().strip()
    if lang_norm.startswith("en"):
        lang = "en"
    else:
        lang = "de"

    path, used_lang = _resolve_section_path(section, lang)

    info: Dict[str, Any] = {
        "section": section,
        "requested_lang": lang,
        "used_lang": used_lang,
        "base_dir": str(BASE_DIR),
        "base_dir_exists": BASE_DIR.exists(),
    }

    if path:
        info["path"] = str(path)
        info["exists"] = path.exists()

        if path.exists():
            stat = path.stat()
            info["size_bytes"] = stat.st_size
            info["modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()

            # Read first 200 chars to verify content
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    preview = f.read(200)
                    info["preview"] = preview.replace('\n', ' ')[:150] + "..."

                    # Check for v7.0 marker (Phase 3 hyper-personalization)
                    if "v7.0" in preview or "PHASE 3" in preview:
                        info["version_detected"] = "v7.0 (Phase 3)"
                    elif "v6" in preview:
                        info["version_detected"] = "v6.x"
                    else:
                        info["version_detected"] = "unknown"
            except Exception as e:
                info["preview_error"] = str(e)
    else:
        info["path"] = None
        info["exists"] = False
        info["error"] = f"Prompt '{section}' not found for lang '{lang}'"

    # Cache info
    cache_info = _read_manifest.cache_info()
    info["manifest_cache"] = {
        "hits": cache_info.hits,
        "misses": cache_info.misses,
        "size": cache_info.currsize,
        "maxsize": cache_info.maxsize,
    }

    log.info("[prompt_loader] get_prompt_info: %s", info)
    return info


def diagnose_prompt_system() -> Dict[str, Any]:
    """
    Comprehensive diagnostic check for the prompt system.

    Checks:
    - Environment variables (USE_PROMPT_SYSTEM, ENABLE_LLM_CONTENT)
    - PromptEnhancer initialization status
    - Prompt files existence and versions
    - Potential issues that could cause fallback to legacy prompts

    Returns:
        Dict with full diagnostic report
    """
    import os
    from datetime import datetime

    report: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "status": "OK",
        "issues": [],
        "recommendations": [],
    }

    # 1. Check environment variables
    use_prompt_system = os.getenv("USE_PROMPT_SYSTEM", "1")
    enable_llm = os.getenv("ENABLE_LLM_CONTENT", "1")

    report["environment"] = {
        "USE_PROMPT_SYSTEM": use_prompt_system,
        "USE_PROMPT_SYSTEM_effective": use_prompt_system in ("1", "true", "TRUE", "yes", "YES"),
        "ENABLE_LLM_CONTENT": enable_llm,
        "ENABLE_LLM_CONTENT_effective": enable_llm in ("1", "true", "TRUE", "yes", "YES"),
        "PROMPTS_DEFAULT_LANG": DEFAULT_LANG,
        "PROMPTS_BASE_DIR": os.getenv("PROMPTS_BASE_DIR", "(not set - using default)"),
    }

    if use_prompt_system not in ("1", "true", "TRUE", "yes", "YES"):
        report["issues"].append("USE_PROMPT_SYSTEM is OFF - legacy hardcoded prompts will be used!")
        report["recommendations"].append("Set USE_PROMPT_SYSTEM=1 in Railway environment")
        report["status"] = "CRITICAL"

    # 2. Check PromptEnhancer
    try:
        from services.prompt_enhancer import PromptEnhancer
        test_enhancer = PromptEnhancer(data_dir="data")
        report["prompt_enhancer"] = {
            "can_import": True,
            "can_initialize": True,
        }
    except Exception as e:
        report["prompt_enhancer"] = {
            "can_import": True,
            "can_initialize": False,
            "error": str(e),
        }
        report["issues"].append(f"PromptEnhancer failed to initialize: {e}")
        report["status"] = "ERROR"

    # 3. Check BASE_DIR
    report["base_dir"] = {
        "path": str(BASE_DIR),
        "exists": BASE_DIR.exists(),
    }

    if not BASE_DIR.exists():
        report["issues"].append(f"BASE_DIR does not exist: {BASE_DIR}")
        report["status"] = "CRITICAL"
    else:
        # List language directories
        de_dir = BASE_DIR / "de"
        en_dir = BASE_DIR / "en"
        report["base_dir"]["de_exists"] = de_dir.exists()
        report["base_dir"]["en_exists"] = en_dir.exists()

    # 4. Check critical prompt files
    critical_prompts = [
        ("quick_wins", "de"),
        ("quick_wins", "en"),
        ("roadmap_90d", "de"),
        ("roadmap_90d", "en"),
        ("executive_summary", "de"),
    ]

    prompt_checks = []
    for section, lang in critical_prompts:
        info = get_prompt_info(section, lang)
        check = {
            "section": section,
            "lang": lang,
            "exists": info.get("exists", False),
            "version": info.get("version_detected", "unknown"),
            "size_bytes": info.get("size_bytes", 0),
        }

        if not check["exists"]:
            report["issues"].append(f"Prompt '{section}' for '{lang}' not found!")
            if report["status"] == "OK":
                report["status"] = "WARNING"
        elif check["version"] != "v7.0 (Phase 3)":
            report["issues"].append(f"Prompt '{section}' ({lang}) is not v7.0: {check['version']}")
            if report["status"] == "OK":
                report["status"] = "WARNING"

        prompt_checks.append(check)

    report["prompt_files"] = prompt_checks

    # 5. Check manifest cache
    cache_info = _read_manifest.cache_info()
    report["manifest_cache"] = {
        "hits": cache_info.hits,
        "misses": cache_info.misses,
        "size": cache_info.currsize,
        "maxsize": cache_info.maxsize,
    }

    # 6. Summary
    if not report["issues"]:
        report["summary"] = "✅ Prompt system is correctly configured. v7.0 prompts should be in use."
    else:
        report["summary"] = f"⚠️ {len(report['issues'])} issue(s) found. Check 'issues' and 'recommendations'."

    log.info("[prompt_loader] diagnose_prompt_system: status=%s, issues=%d",
             report["status"], len(report["issues"]))

    return report
