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

import hashlib
import inspect
import json
import os
import re
import logging
import contextvars
import threading
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

__all__ = [
    "load_prompt", "clear_prompt_cache", "get_prompt_info", "diagnose_prompt_system",
    "PromptIncludeCycleError", "PromptTemplateNotAllowedError", "check_prompt_cycles",
    "PromptManifest", "flush_usage_to_artifact", "get_used_prompts", "clear_used_prompts",
]

log = logging.getLogger(__name__)

DEFAULT_LANG = os.getenv("PROMPTS_DEFAULT_LANG", "de")

# FIX-505: STRICT_MODE flag - no fallback to simple substitution when enabled
RELEASE_STRICT_MODE = os.getenv("RELEASE_STRICT_MODE", "0") in ("1", "true", "True")

# STATE-AUDIT-517A: Debug trace for section propagation forensics
DEBUG_PROMPT_TRACE = os.getenv("DEBUG_PROMPT_TRACE", "0") in ("1", "true", "TRUE")

# FIX-505: Contextvar for tracking include stack (thread-safe)
# Note: Using a factory function to avoid mutable default issues
_include_stack: contextvars.ContextVar[List[str]] = contextvars.ContextVar('include_stack')


def _get_include_stack() -> List[str]:
    """Get current include stack, initializing if needed."""
    try:
        return _include_stack.get()
    except LookupError:
        _include_stack.set([])
        return []


def _set_include_stack(stack: List[str]) -> None:
    """Set current include stack."""
    _include_stack.set(stack)


# =============================================================================
# PROMPT-MANIFEST: Single Source of Truth for prompt file resolution
# =============================================================================

class PromptManifest:
    """Cached singleton for prompt_manifest.json resolution."""

    _instance: Optional["PromptManifest"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}
        self._loaded = False

    @classmethod
    def load(cls) -> "PromptManifest":
        """Load manifest once (cached singleton)."""
        if cls._instance is not None and cls._instance._loaded:
            return cls._instance
        with cls._lock:
            if cls._instance is not None and cls._instance._loaded:
                return cls._instance
            inst = cls()
            manifest_path = BASE_DIR / "prompt_manifest.json"
            if manifest_path.exists():
                try:
                    data = json.loads(manifest_path.read_text(encoding="utf-8"))
                    inst._data = data if isinstance(data, dict) else {}
                except Exception as exc:
                    log.error("[PROMPT-MANIFEST][ERROR] failed to parse manifest: %s", exc)
                    inst._data = {}
            else:
                log.error("[PROMPT-MANIFEST][ERROR] manifest not found at %s", manifest_path)
                inst._data = {}
            inst._loaded = True
            cls._instance = inst
            return inst

    def resolve(self, section: str, lang: str) -> Optional[str]:
        """
        Resolve section+lang to a relative path (e.g. 'executive_summary.md').
        Returns None if section is not in manifest for the given lang.
        """
        lang_block = self._data.get(lang)
        if not isinstance(lang_block, dict):
            return None
        entry = lang_block.get(section)
        if isinstance(entry, dict):
            path_val = entry.get("path")
            return str(path_val) if path_val is not None else None
        if isinstance(entry, str):
            return entry
        return None

    def has_section(self, section: str, lang: str) -> bool:
        """Check if section exists in manifest for lang."""
        lang_block = self._data.get(lang)
        if not isinstance(lang_block, dict):
            return False
        return section in lang_block

    def get_allowed_includes(self, lang: str) -> Optional[List[str]]:
        """Get allowed_includes list from manifest if defined."""
        lang_block = self._data.get(lang)
        if isinstance(lang_block, dict):
            includes = lang_block.get("_allowed_includes")
            if isinstance(includes, list):
                return includes
        # Global level
        includes = self._data.get("_allowed_includes")
        if isinstance(includes, list):
            return includes
        return None

    @classmethod
    def reset(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None


# =============================================================================
# PROMPT-USAGE: Track what was rendered during this process
# =============================================================================

_usage_lock = threading.Lock()
_used_prompts: List[Dict[str, Any]] = []


def _record_usage(
    section: str, lang: str, path: str, content_bytes: int,
    content: str, includes: List[str]
) -> None:
    """Record a prompt usage entry."""
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
    entry = {
        "section": section,
        "lang": lang,
        "path": path,
        "bytes": content_bytes,
        "sha256": sha,
        "includes": includes,
    }
    with _usage_lock:
        _used_prompts.append(entry)


def flush_usage_to_artifact() -> Optional[str]:
    """
    Write usage data to artifacts/prompt_usage_last.json.
    Returns the path written, or None on error.
    """
    with _usage_lock:
        entries = list(_used_prompts)
    if not entries:
        return None
    artifact_dir = Path(__file__).resolve().parent.parent / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "prompt_usage_last.json"
    try:
        out_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
        log.info("[PROMPT-USAGE] wrote %s entries=%d", out_path, len(entries))
        return str(out_path)
    except Exception as exc:
        log.error("[PROMPT-USAGE] failed to write artifact: %s", exc)
        return None


def get_used_prompts() -> List[Dict[str, Any]]:
    """Get current usage list (for testing/inspection)."""
    with _usage_lock:
        return list(_used_prompts)


def clear_used_prompts() -> None:
    """Clear usage list (for testing)."""
    with _usage_lock:
        _used_prompts.clear()


# =============================================================================
# PROMPT-JINJA: Pre-scan for forbidden Jinja tags
# =============================================================================

_FORBIDDEN_JINJA_TAGS = re.compile(
    r"{%[-\s]*(extends|import|from|macro|call|filter)\b",
    re.IGNORECASE,
)


def _prescan_jinja_tags(template_text: str, section: str) -> None:
    """
    Pre-scan template for forbidden Jinja2 tags.
    Raises RuntimeError in STRICT mode, logs warning otherwise.
    Only {% include %} and {% raw %} are allowed.
    """
    match = _FORBIDDEN_JINJA_TAGS.search(template_text)
    if match:
        tag = match.group(1)
        msg = f"[PROMPT-JINJA][BLOCK] forbidden tag='{tag}' in section={section}"
        log.error(msg)
        if RELEASE_STRICT_MODE:
            raise RuntimeError(msg)


# =============================================================================
# PROMPT-INCLUDE: Path sandbox validation
# =============================================================================

_INCLUDE_PATTERN = re.compile(r'{%[-\s]*include\s+["\']([^"\']+)["\']')


def _validate_include_path(include_target: str, lang: str, section: str) -> bool:
    """
    Validate that an include path is safe:
    - Must be a string literal (already guaranteed by regex)
    - No '..' components
    - No absolute paths
    - No backslashes
    - Must resolve within prompts/<lang>/
    Returns True if valid, raises/logs on invalid.
    """
    if ".." in include_target:
        msg = f"[PROMPT-INCLUDE][BLOCK] illegal include='{include_target}' reason=path_traversal (..) section={section}"
        log.error(msg)
        if RELEASE_STRICT_MODE:
            raise RuntimeError(msg)
        return False
    if include_target.startswith("/") or include_target.startswith("\\"):
        msg = f"[PROMPT-INCLUDE][BLOCK] illegal include='{include_target}' reason=absolute_path section={section}"
        log.error(msg)
        if RELEASE_STRICT_MODE:
            raise RuntimeError(msg)
        return False
    if "\\" in include_target:
        msg = f"[PROMPT-INCLUDE][BLOCK] illegal include='{include_target}' reason=backslash section={section}"
        log.error(msg)
        if RELEASE_STRICT_MODE:
            raise RuntimeError(msg)
        return False

    # Check manifest allowlist if available
    manifest = PromptManifest.load()
    allowed = manifest.get_allowed_includes(lang)
    if allowed is not None and include_target not in allowed:
        msg = f"[PROMPT-INCLUDE][BLOCK] illegal include='{include_target}' reason=not_in_allowlist section={section}"
        log.error(msg)
        if RELEASE_STRICT_MODE:
            raise RuntimeError(msg)
        return False

    log.debug("[PROMPT-INCLUDE] allow include='%s' section=%s", include_target, section)
    return True


def _prescan_includes(template_text: str, lang: str, section: str) -> List[str]:
    """
    Pre-scan all {% include %} targets, validate each, return list of includes.
    """
    includes: List[str] = []
    for match in _INCLUDE_PATTERN.finditer(template_text):
        target = match.group(1)
        _validate_include_path(target, lang, section)
        includes.append(target)
    return includes


class PromptIncludeCycleError(RuntimeError):
    """FIX-505: Raised when a cycle is detected in prompt includes."""

    def __init__(self, chain: List[str], section: str):
        self.chain = chain
        self.section = section
        chain_str = " -> ".join(chain)
        super().__init__(
            f"[FIX-505][PROMPT][CYCLE] Cycle detected in section={section}: {chain_str}"
        )


class PromptTemplateNotAllowedError(RuntimeError):
    """FIX-517: Raised when an include target is not in the allowlist."""

    def __init__(self, template_name: str, section: str, lang: str):
        self.template_name = template_name
        self.section = section
        self.lang = lang
        super().__init__(
            f"[FIX-517][PROMPT][INCLUDE-DENY] template={template_name} "
            f"section={section} lang={lang} (not in allowlist)"
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
    FIX-517: Extended with include-allowlist enforcement.

    This loader wraps the standard ChoiceLoader and tracks the include stack
    using a contextvar to detect cycles before they cause recursion depth errors.

    Cycle detection strategy:
    - Track templates currently being loaded in a stack
    - Push when entering get_source, pop when exiting
    - If a template is already in the stack when trying to load it, it's a cycle

    This allows diamond dependencies (A->B->D, A->C->D) while catching cycles.
    Note: Due to Jinja2's execution model, some cycles may not be caught by
    proactive detection and will fall through to RecursionError, which is
    handled in the calling code.
    """

    def __init__(self, loaders: List[Any], section: str, lang: str = "de"):
        from jinja2 import ChoiceLoader
        self._inner_loader = ChoiceLoader(loaders)
        self._section = section
        self._lang = lang
        # Copy required attributes from BaseLoader for compatibility
        self.has_source_access = getattr(self._inner_loader, 'has_source_access', True)
        # FIX-517: Build include-allowlist for this language
        self._allowed_templates = self._build_allowlist(lang)

    def _build_allowlist(self, lang: str) -> Set[str]:
        """
        FIX-517: Build the set of allowed template names for includes.
        Includes:
        - All filenames referenced in the manifest for this language
        - All underscore partials (_*.md) in prompts/{lang}/
        - All .md files in the inner loaders' search paths (handles test envs)
        """
        allowed: Set[str] = set()
        # Manifest files
        manifest = PromptManifest.load()
        lang_block = manifest._data.get(lang)
        if isinstance(lang_block, dict):
            for key, entry in lang_block.items():
                if key.startswith("_"):
                    continue
                if isinstance(entry, dict):
                    path_val = entry.get("path")
                    if path_val:
                        allowed.add(str(path_val))
                elif isinstance(entry, str):
                    allowed.add(entry)
        # Underscore partials from filesystem
        lang_dir = BASE_DIR / lang
        if lang_dir.exists():
            for partial in lang_dir.glob("_*.md"):
                allowed.add(partial.name)
        # Also include all .md files found in the inner loaders' search paths
        # This handles test environments where BASE_DIR is patched to a temp dir
        # and the manifest doesn't cover the test files
        for loader in getattr(self._inner_loader, 'loaders', []):
            for search_path in getattr(loader, 'searchpath', []):
                sp = Path(search_path)
                if sp.exists():
                    for md_file in sp.glob("*.md"):
                        allowed.add(md_file.name)
        return allowed

    def get_source(self, environment: Any, template_name: str) -> tuple:
        """
        Get template source, checking for cycles, path safety, and allowlist first.

        This is the primary cycle detection point. It's called whenever
        Jinja2 needs to load a template (including via {% include %}).
        """
        # PROMPT-INCLUDE: Runtime path sandbox check
        _validate_include_path(template_name, self._lang, self._section)

        # FIX-517: Include-allowlist enforcement
        if self._allowed_templates and template_name not in self._allowed_templates:
            log.error(
                "[FIX-517][PROMPT][INCLUDE-DENY] template=%s section=%s lang=%s include_stack=%s",
                template_name, self._section, self._lang,
                " -> ".join(_get_include_stack())
            )
            if RELEASE_STRICT_MODE:
                raise PromptTemplateNotAllowedError(template_name, self._section, self._lang)
            else:
                from jinja2.exceptions import TemplateNotFound
                raise TemplateNotFound(template_name)

        # Get current include stack
        stack = _get_include_stack()

        # Check for cycle - template already being loaded in current call chain
        if template_name in stack:
            cycle_chain = list(stack) + [template_name]
            log.error(
                "[FIX-505][PROMPT][CYCLE] section=%s chain=%s",
                self._section,
                " -> ".join(cycle_chain)
            )
            raise PromptIncludeCycleError(cycle_chain, self._section)

        # Push to stack (mark as being loaded)
        new_stack = list(stack) + [template_name]
        _set_include_stack(new_stack)

        try:
            # Get source from inner loader
            source, filename, uptodate = self._inner_loader.get_source(environment, template_name)
            return source, filename, uptodate
        finally:
            # Pop from stack (loading complete for this get_source call)
            _set_include_stack(stack)

    def list_templates(self) -> List[str]:
        """List available templates."""
        return list(self._inner_loader.list_templates())

    def load(self, environment: Any, name: str, globals: Optional[Dict[str, Any]] = None) -> Any:
        """
        Load a template.

        Delegates to Jinja2's standard template loading, which will call
        our get_source() method where cycle detection happens.
        """
        # Get the source (this is where cycle detection happens)
        source, filename, uptodate = self.get_source(environment, name)

        # Compile and return the template
        code = environment.compile(source, name, filename)
        return environment.template_class.from_code(
            environment, code, globals or {}, uptodate
        )


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

    FIX-517: section parameter is now enforced:
    - STRICT: raises ValueError if section is "unknown" or empty
    - Non-STRICT: logs warning
    """
    if not isinstance(s, str):
        return s

    # FIX-517: Enforce section parameter for usage+cycle tracking
    if not section or section == "unknown":
        msg = (
            "[FIX-517][PROMPT][SECTION] section=unknown — "
            "Pass section=<prompt_key> to render_prompt for usage+cycle tracking"
        )
        # STATE-AUDIT-517A: Log caller info for forensics
        if DEBUG_PROMPT_TRACE:
            try:
                _frames = inspect.stack()[:4]  # Limit to 4 frames
                _caller_info = " <- ".join(
                    f"{f.filename.split('/')[-1]}:{f.lineno}:{f.function}"
                    for f in _frames[1:3]  # Skip self, show 2 callers
                )
            except Exception:
                _caller_info = "<unavailable>"
            log.error(
                "[PROMPT-TRACE][ERROR] section=unknown caller=%s "
                "key_hint=<unknown> text_bytes=%d has_jinja=%s",
                _caller_info, len(s), "{%" in s,
            )
        if RELEASE_STRICT_MODE:
            raise ValueError(msg)
        else:
            log.warning(msg)
            section = section or "unknown"

    # Use empty dict if None provided
    if vars_dict is None:
        vars_dict = {}

    # Determine strict mode
    is_strict = strict_mode if strict_mode is not None else RELEASE_STRICT_MODE

    # 🎯 JINJA2-RENDERING: Wenn Jinja2-Tags vorhanden sind, rendere mit Jinja2
    if "{% " in s or "{%" in s:
        log.debug(
            "[FIX-505][PROMPT] render start section=%s lang=%s strict=%d",
            section, lang, int(is_strict)
        )

        # PROMPT-JINJA: Pre-scan for forbidden tags (extends/import/macro/etc.)
        _prescan_jinja_tags(s, section)

        # PROMPT-INCLUDE: Pre-scan and validate include paths
        include_list = _prescan_includes(s, lang, section)

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
            # FIX-517: Pass lang for include-allowlist enforcement
            cycle_loader = CycleDetectingLoader(loaders, section, lang)

            # Reset include stack for this render and add main template
            # This ensures the initial template is tracked for cycle detection
            # when it's included recursively (e.g., a.md -> b.md -> a.md)
            main_template_name = f"{section}.md"
            _set_include_stack([main_template_name])

            # Type ignore needed because CycleDetectingLoader implements BaseLoader
            # interface but doesn't inherit from it (duck typing)
            # FIX-505: Disable template cache to ensure cycle detection works
            # (otherwise cached templates bypass get_source and our detection)
            env = Environment(
                loader=cycle_loader,  # type: ignore[arg-type,unused-ignore]
                autoescape=False,  # nosec B701 — bewusst: rendert Prompt-Markdown, kein User-HTML
                cache_size=0,  # Disable cache to ensure get_source is called each time
            )
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
            # RecursionError indicates a cycle we didn't catch proactively
            # FIX-505: Cycles should ALWAYS fail, even in non-strict mode
            # (fallback is for minor template errors, not infinite recursion)
            log.error(
                "[FIX-505][PROMPT][CYCLE] section=%s recursion_error=%s",
                section, str(e)[:100]
            )
            raise RuntimeError(
                f"[FIX-505][PROMPT] Jinja2 recursion error in section={section}. "
                f"This indicates a template cycle that must be fixed."
            ) from e

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

    # Properly typed result structure
    cycles_list: List[List[str]] = []
    warnings_list: List[str] = []
    graph_dict: Dict[str, Dict[str, List[str]]] = {}
    checked_files_count: int = 0

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
            warnings_list.append(f"Language directory not found: {lang_dir}")
            continue

        # Build dependency graph
        deps: Dict[str, Set[str]] = {}

        for prompt_file in lang_dir.glob("*.md"):
            checked_files_count += 1
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
                warnings_list.append(f"Error reading {prompt_file}: {e}")

        graph_dict[lang] = {k: list(v) for k, v in deps.items()}

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
                    cycles_list.append(cycle)
                    log.error(
                        "[FIX-505][PROMPT][CYCLE-PREFLIGHT] Detected cycle: %s",
                        " -> ".join(cycle)
                    )

    if cycles_list:
        log.error(
            "[FIX-505][PROMPT][CYCLE-PREFLIGHT] Found %d cycle(s) in prompt templates!",
            len(cycles_list)
        )
    else:
        log.info(
            "[FIX-505][PROMPT][CYCLE-PREFLIGHT] No cycles detected in %d prompt files",
            checked_files_count
        )

    return {
        "cycles": cycles_list,
        "warnings": warnings_list,
        "graph": graph_dict,
        "checked_files": checked_files_count,
    }


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

    PROMPT-MANIFEST enforcement:
    - Always resolves via PromptManifest first (Single Source of Truth).
    - In STRICT mode: fail-closed if section not in manifest.
    - Non-strict: falls back to extension scanning with warning.

    Multilingual v1: For lang=en, tries ALIASES_EN mapping before fallback.
    This ensures German-named sections find their English equivalents.
    """
    # --- PROMPT-MANIFEST resolution (primary) ---
    pm = PromptManifest.load()
    rel_path = pm.resolve(section, lang)
    if rel_path:
        p = (BASE_DIR / lang / rel_path).resolve()
        if p.exists():
            log.info(
                "[PROMPT-MANIFEST] ok section=%s lang=%s path=%s",
                section, lang, rel_path
            )
            return p, lang
        else:
            log.error(
                "[PROMPT-MANIFEST][ERROR] missing file path=%s section=%s lang=%s",
                p, section, lang
            )
            if RELEASE_STRICT_MODE:
                raise RuntimeError(
                    f"[PROMPT-MANIFEST][ERROR] missing file path={p} "
                    f"section={section} lang={lang}"
                )
    elif not pm.has_section(section, lang):
        # Section not in manifest at all
        if RELEASE_STRICT_MODE and not _tried_alias:
            # In STRICT: try alias first before failing
            if lang == "en":
                alias = ALIASES_EN.get(section)
                if alias and alias != section:
                    result = _resolve_section_path(alias, lang, _tried_alias=True)
                    if result[0]:
                        return result
            log.error(
                "[PROMPT-MANIFEST][ERROR] unknown section=%s lang=%s",
                section, lang
            )
            raise RuntimeError(
                f"[PROMPT-MANIFEST][ERROR] unknown section={section} lang={lang} "
                f"(not in manifest, STRICT mode)"
            )

    # --- Legacy fallback (non-STRICT only) ---
    # Also used by _read_manifest-based legacy path
    manifest = _read_manifest(lang)
    if isinstance(manifest, dict):
        rel = manifest.get(section)
        if isinstance(rel, str):
            p = (BASE_DIR / lang / rel).resolve()
            if p.exists():
                log.debug("Found prompt via legacy manifest: %s", p)
                return p, lang

    # try common extensions (non-STRICT fallback)
    for ext in _SUPPORTED_EXT:
        p = (BASE_DIR / lang / f"{section}{ext}").resolve()
        if p.exists():
            log.debug("Found prompt via extension scan: %s", p)
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
    result = _interpolate(payload, vars_dict, lang=used_lang, section=section)

    # PROMPT-USAGE: Record what was rendered
    content_str = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
    # Scan raw payload for includes (before rendering expanded them)
    raw_text = payload if isinstance(payload, str) else ""
    includes_found = _INCLUDE_PATTERN.findall(raw_text)
    _record_usage(
        section=section,
        lang=used_lang,
        path=str(path.relative_to(BASE_DIR)) if path.is_relative_to(BASE_DIR) else str(path),
        content_bytes=len(content_str),
        content=content_str,
        includes=includes_found,
    )

    return result


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
