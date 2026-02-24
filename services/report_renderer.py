# -*- coding: utf-8 -*-
"""
Report Renderer for PDF Generation.

Version: 4.18.0 PDF-SLIMDOWN + N2.5 Final Leak Check Fix
- HTML compression and minification
- Unused section stripping
- CSS optimization
- SPRINT N2 (N2-5): Final leak phrase safety check before PDF render
- SPRINT N2.5: Defensive leak cleanup - never blocks PDF dispatch
"""
from __future__ import annotations
import os, logging, re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from jinja2 import Environment, FileSystemLoader, select_autoescape, Undefined
from markupsafe import Markup

from utils.logo_embedder import embed_logos_in_html
from services.html_minifier import optimize_html_for_pdf, strip_unused_sections
from services.final_sanitizer import final_sanitize
from services.pipeline_sanitizers import sanitize_grid_layouts
from services.report_validator import GENERIC_LLM_LEAK_PHRASES, remove_leak_phrases_from_html
from services.html_sanitizer import sanitize_en_locale_tokens
from services.lang_utils import normalize_lang
from services.i18n import ui as ui_factory, ui_for_segment
from services.locale_rewriter import apply_locale_v2
from services.debug_503d import build_debug_503d_attachments, build_debug_503d_summary, is_debug_render_enabled
from services.pipeline_sanitizers import fix_double_encoded_utf8

log = logging.getLogger(__name__)

# N3: Pre-compute a single regex pattern for O(n) leak detection instead of O(n*phrases)
# This matches ANY leak phrase in a single pass through the HTML
_LEAK_PATTERN = re.compile(
    '|'.join(re.escape(p) for p in GENERIC_LLM_LEAK_PHRASES),
    re.IGNORECASE
)


# =============================================================================
# P0.4: Pagebreak Cleanup - Prevent Empty/Low-Value Pages
# =============================================================================
# Patterns for detecting pagebreak elements
_PAGEBREAK_CLASSES = [
    r'class="[^"]*page-break[^"]*"',
    r'class="[^"]*chapter-start[^"]*"',
    r'style="[^"]*page-break-before:\s*always[^"]*"',
    r'style="[^"]*break-before:\s*page[^"]*"',
]

# Compiled pattern for pagebreak detection
_PAGEBREAK_PATTERN = re.compile(
    r'<div\s+(?:' + '|'.join(_PAGEBREAK_CLASSES) + r')[^>]*>\s*</div>',
    re.IGNORECASE | re.DOTALL
)

# Pattern for consecutive pagebreaks (2+ in a row with only whitespace between)
_CONSECUTIVE_PAGEBREAKS = re.compile(
    r'(<div\s+class="[^"]*page-break[^"]*"[^>]*>\s*</div>\s*){2,}',
    re.IGNORECASE | re.DOTALL
)

# Pattern for empty sections that could cause blank pages
_EMPTY_SECTION_PATTERNS = [
    # Empty section with only whitespace
    re.compile(r'<section[^>]*>\s*</section>', re.IGNORECASE | re.DOTALL),
    # Section with only empty divs
    re.compile(r'<section[^>]*>\s*(?:<div[^>]*>\s*</div>\s*)*</section>', re.IGNORECASE | re.DOTALL),
    # Pagebreak followed immediately by another pagebreak element
    re.compile(
        r'(<div\s+class="page-break"[^>]*>\s*</div>)\s*'
        r'(<(?:div|section)[^>]*(?:chapter|page-break)[^>]*>)',
        re.IGNORECASE
    ),
]


def cleanup_pagebreaks(html: str, run_id: str | None = None) -> Tuple[str, int]:
    """
    P0.4: Clean up pagebreak artifacts that cause empty or low-value pages.

    Removes:
    - Consecutive pagebreak divs (keeps only first)
    - Empty sections that would create blank pages
    - Orphaned pagebreaks at document start/end

    Args:
        html: HTML content to clean
        run_id: Optional run ID for logging

    Returns:
        Tuple of (cleaned_html, count_removed)
    """
    if not html or not isinstance(html, str):
        return html or "", 0

    result = html
    removed_count = 0

    try:
        # Step 1: Remove consecutive pagebreaks (keep only first)
        def keep_first_pagebreak(match):
            nonlocal removed_count
            # Count how many pagebreaks were in the match
            pagebreaks = re.findall(r'<div\s+class="[^"]*page-break[^"]*"', match.group(0), re.IGNORECASE)
            if len(pagebreaks) > 1:
                removed_count += len(pagebreaks) - 1
            # Return just one pagebreak
            return '<div class="page-break"></div>'

        result = _CONSECUTIVE_PAGEBREAKS.sub(keep_first_pagebreak, result)

        # Step 2: Remove empty sections
        for pattern in _EMPTY_SECTION_PATTERNS[:2]:  # First two patterns
            matches = pattern.findall(result)
            if matches:
                removed_count += len(matches)
                result = pattern.sub('', result)

        # Step 3: Fix pagebreak immediately before another pagebreak element
        # (removes the first one to avoid double breaks)
        third_pattern = _EMPTY_SECTION_PATTERNS[2]
        while True:
            match = third_pattern.search(result)
            if not match:
                break
            # Keep only the second element (the chapter/section)
            result = result[:match.start()] + match.group(2) + result[match.end():]
            removed_count += 1

        # Step 4: Remove pagebreak at very start of body content
        result = re.sub(
            r'(<body[^>]*>)\s*<div\s+class="page-break"[^>]*>\s*</div>',
            r'\1',
            result,
            flags=re.IGNORECASE
        )

        # Step 5: Remove pagebreak at very end before </body>
        result = re.sub(
            r'<div\s+class="page-break"[^>]*>\s*</div>\s*(</body>)',
            r'\1',
            result,
            flags=re.IGNORECASE
        )

        # Step 6: Normalize whitespace around remaining pagebreaks
        result = re.sub(
            r'\s*(<div\s+class="page-break"[^>]*>\s*</div>)\s*',
            r'\n\1\n',
            result
        )

        if removed_count > 0:
            log.info(f"[P0.4] Pagebreak cleanup removed {removed_count} artifacts for run={run_id}")

    except Exception as e:
        log.error(f"[P0.4] Pagebreak cleanup failed for run={run_id}: {e}", exc_info=True)
        return html, 0

    return result, removed_count


# =============================================================================
# SPRINT N2.5: Defensive Final Leak Cleanup
# =============================================================================
def detect_leak_phrases(html: str) -> List[str]:
    """
    Detect leak phrases in HTML content.

    N2.5: Defensive implementation - never crashes, always returns list.

    Args:
        html: HTML content to check

    Returns:
        List of found leak phrases (empty if none or on error)
    """
    if not html or not isinstance(html, str):
        return []

    try:
        # Use pre-compiled regex for O(n) detection
        found = _LEAK_PATTERN.findall(html)
        # Return unique phrases (case-insensitive dedup)
        return list({p.lower(): p for p in found}.values()) if found else []
    except Exception as e:
        log.error(f"[N2.5] detect_leak_phrases failed: {e}", exc_info=True)
        return []


def apply_leak_replacements(html: str, leaks: List[str]) -> Tuple[str, int]:
    """
    Remove sentences containing leak phrases from HTML.

    N2.5: Defensive implementation - never crashes, always returns valid HTML.

    Args:
        html: HTML content to clean
        leaks: List of leak phrases to remove

    Returns:
        Tuple of (cleaned_html, count_removed)
    """
    if not html or not isinstance(html, str):
        return html or "", 0

    if not leaks:
        return html, 0

    cleaned = html
    removed_count = 0

    try:
        for phrase in leaks:
            if not phrase:
                continue
            # PLATIN+++ v5.4: More precise leak removal
            # OLD (greedy): [^.!?]*{phrase}[^.!?]*[.!?]?\s* - matched across HTML elements
            # NEW: Respect HTML boundaries by excluding < and > from character class
            # This prevents removing content from adjacent HTML elements
            try:
                escaped_phrase = re.escape(phrase)
                # Pattern: match text with phrase, stopping at sentence boundaries AND HTML tags
                # [^<>.!?]* excludes both HTML tag chars and sentence-ending punctuation
                pattern = rf'[^<>.!?]*{escaped_phrase}[^<>.!?]*[.!?]?\s*'
                matches = re.findall(pattern, cleaned, re.IGNORECASE)
                if matches:
                    for match in matches:
                        # Safety: only remove if match is reasonable length (< 500 chars)
                        # Prevents accidental removal of large content blocks
                        if len(match) < 500:
                            cleaned = cleaned.replace(match, '', 1)
                            removed_count += 1
                        else:
                            # Fallback: just remove the phrase itself
                            log.warning(f"[N2.5] Match too long ({len(match)} chars), removing phrase only")
                            cleaned = re.sub(escaped_phrase, '', cleaned, count=1, flags=re.IGNORECASE)
                            removed_count += 1
            except re.error as regex_err:
                log.warning(f"[N2.5] Regex error for phrase '{phrase}': {regex_err}")
                # Fall back to simple string replacement
                if phrase.lower() in cleaned.lower():
                    cleaned = cleaned.replace(phrase, '')
                    removed_count += 1
    except Exception as e:
        log.error(f"[N2.5] apply_leak_replacements failed: {e}", exc_info=True)
        # Return original HTML on error - don't block PDF generation
        return html, 0

    return cleaned, removed_count


def final_leak_cleanup(html: str, run_id: str | None = None) -> str:
    """
    SPRINT N2.5: Final leak phrase cleanup before PDF generation.

    This function is the LAST line of defense before PDF rendering.
    It is designed to:
    - ALWAYS return a valid string (never None)
    - NEVER raise exceptions that block PDF dispatch
    - Log all issues for debugging

    Args:
        html: HTML content to clean
        run_id: Optional run ID for logging

    Returns:
        Cleaned HTML string (original if cleanup fails)
    """
    # Defensive: ensure we always have a string
    if not html:
        log.warning(f"[N2.5] final_leak_cleanup received empty HTML for run={run_id}")
        return html or ""

    if not isinstance(html, str):
        log.error(f"[N2.5] final_leak_cleanup received non-string type: {type(html)} for run={run_id}")
        return str(html) if html else ""

    try:
        # Step 1: Detect leaks
        leaks = detect_leak_phrases(html)

        if not leaks:
            log.debug(f"[N2.5] Leak check passed - no leak phrases found for run={run_id}")
            return html

        # Step 2: Log warning about found leaks
        log.warning(
            f"⚠️ [N2-5] LEAK-CHECK: Found {len(leaks)} leak phrases in final HTML! "
            f"Phrases: {leaks[:3]}{'...' if len(leaks) > 3 else ''} Applying emergency cleanup for run={run_id}"
        )

        # Step 3: Apply replacements
        cleaned_html, removed_count = apply_leak_replacements(html, leaks)
        log.info(f"[N2-5] Emergency cleanup removed {removed_count} leak phrases from final HTML")

        # Step 4: Verify cleanup (soft-fail: log but don't crash)
        remaining = detect_leak_phrases(cleaned_html)
        if remaining:
            log.error(
                f"❌ [N2-5] CRITICAL: {len(remaining)} leak phrases STILL present after cleanup! "
                f"Phrases: {remaining[:3]}... Report {run_id} may contain visible leaks."
            )
        else:
            log.info(f"✅ [N2-5] All leak phrases successfully removed from final HTML for run={run_id}")

        return cleaned_html

    except Exception as e:
        # CRITICAL: Never block PDF generation due to leak cleanup failure
        log.error(
            f"❌ [N2.5] Final leak cleanup FAILED for run={run_id}: {e}",
            exc_info=True
        )
        # Return original HTML - better to have leaks than no PDF
        return html


# =============================================================================
# PLATIN+++ v5.4: Final Development Placeholder Scrub
# =============================================================================
# Root Cause Fix: Development placeholders like DEFAULT_STUNDENSATZ_EUR
# can leak into final HTML if not caught by source fixes.

# Patterns to scrub from final HTML (development/debug tokens)
_DEV_PLACEHOLDER_PATTERNS = [
    r"DEFAULT_STUNDENSATZ_EUR",
    r"DEFAULT_[A-Z_]+_EUR",  # Any DEFAULT_*_EUR pattern
    r"\{\{[A-Z_]+\}\}",  # Unreplaced {{PLACEHOLDER}} patterns
]

# =============================================================================
# FIX-BATCH-497: Code Fence Removal (Zero-Tolerance for Markdown in PDF)
# =============================================================================
# Pattern to match markdown code fences that leak into HTML output
# Matches: ```html, ```json, ```python, ``` (standalone), etc.
_CODE_FENCE_PATTERN = re.compile(
    r'```+(?:[a-zA-Z0-9_-]*)?[\s\n]*',  # Opening fence with optional language
    re.MULTILINE
)

# Also catch HTML-escaped backticks that might appear
_ESCAPED_FENCE_PATTERN = re.compile(
    r'(?:&#96;){3,}|(?:&#x60;){3,}|(?:`){3,}',  # HTML entities or raw backticks
    re.MULTILINE
)


def strip_code_fences_final(html: str, run_id: str | None = None) -> Tuple[str, int]:
    """
    FIX-BATCH-497: Strip all markdown code fences from final HTML.

    This is a hard requirement for premium quality PDFs - no markdown
    artifacts should ever appear in the final output.

    Args:
        html: HTML content to clean
        run_id: Optional run ID for logging

    Returns:
        Tuple of (cleaned_html, count_removed)
    """
    if not html or not isinstance(html, str):
        return html or "", 0

    result = html
    removed_count = 0

    try:
        # Step 1: Remove standard code fences
        matches = _CODE_FENCE_PATTERN.findall(result)
        if matches:
            removed_count += len(matches)
            result = _CODE_FENCE_PATTERN.sub("", result)

        # Step 2: Remove HTML-escaped fences
        escaped_matches = _ESCAPED_FENCE_PATTERN.findall(result)
        if escaped_matches:
            removed_count += len(escaped_matches)
            result = _ESCAPED_FENCE_PATTERN.sub("", result)

        # Step 3: Clean up any resulting empty lines or double-newlines
        result = re.sub(r'\n\s*\n\s*\n', '\n\n', result)

        if removed_count > 0:
            log.warning(
                "[FIX-497] Stripped %d code fence artifacts from final HTML (run=%s)",
                removed_count, run_id
            )

    except Exception as e:
        log.error(f"[FIX-497] Code fence removal failed for run={run_id}: {e}")
        # Return original on error - don't block PDF
        return html, 0

    return result, removed_count


def scrub_development_placeholders(html: str, run_id: str | None = None) -> str:
    """
    PLATIN+++ v5.4: Final scrub for development placeholders before PDF rendering.

    This is a last-line-of-defense that removes any development tokens
    that leaked into the final HTML.

    Args:
        html: HTML content to scrub
        run_id: Optional run ID for logging

    Returns:
        Scrubbed HTML string
    """
    if not html or not isinstance(html, str):
        return html or ""

    result = html
    scrubbed_count = 0

    try:
        for pattern in _DEV_PLACEHOLDER_PATTERNS:
            matches = re.findall(pattern, result)
            if matches:
                scrubbed_count += len(matches)
                result = re.sub(pattern, "", result)

        # Normalize whitespace (double spaces -> single)
        result = re.sub(r"  +", " ", result)

        if scrubbed_count > 0:
            log.warning(
                "[PLATIN-SCRUB] Removed %d development placeholders from final HTML (run=%s)",
                scrubbed_count, run_id
            )

    except Exception as e:
        log.error(f"[PLATIN-SCRUB] Scrub failed for run={run_id}: {e}")
        # Return original on error - don't block PDF
        return html

    return result


def _env() -> Environment:
    tpl_dir = Path(os.getenv("REPORT_TEMPLATE_DIR", "templates"))
    env = Environment(
        loader=FileSystemLoader(str(tpl_dir)),
        autoescape=select_autoescape(["html","xml"]),
        undefined=Undefined,  # ✅ Fixed: Use Undefined class instead of None
        trim_blocks=True, lstrip_blocks=True,
        auto_reload=True,  # ✅ Reload templates on file change (no rebuild needed)
    )
    # Backwards-compat filter for old templates using {{LANG|de}}
    env.filters["de"] = lambda v=None: (v or "de")
    return env

def _self_check(env: Environment, template_name: str) -> None:
    """Validate template at startup to avoid runtime surprises."""
    try:
        src = env.loader.get_source(env, template_name)[0]
        if "{{LANG|de}}" in src or "{{ LANG|de }}" in src:
            log.warning("⚠️ Template uses deprecated '|de' filter. Please switch to '|default(\"de\")'.")
        # Try compile (will raise if invalid)
        env.get_template(template_name)
        log.info("✔ Template validated: %s", template_name)
    except Exception as exc:
        log.error("❌ Template validation failed: %s", exc)
        raise

def render(briefing_obj: Any,
           run_id: str,
           generated_sections: Dict[str, Any],
           use_fetchers: bool = False,
           scores: Optional[Dict[str, Any]] = None,
           meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Render report HTML from sections.

    GOLD STANDARD+ v4.14.1:
    - Fixed UTF-8 encoding issues
    - Clean variable replacement
    - Consistent score handling

    v4.15.0: Language-aware template selection (EN/DE)
    v4.15.1 (TEIL 3.1.4.x): Robust language detection with multiple fallbacks
    """
    # =========================================================================
    # TEIL 3.1.4.x: ROBUST LANGUAGE DETECTION
    # Priority: LANG → lang → meta.lang → briefing_obj.lang → "de"
    # =========================================================================
    lang_raw = None
    sections_dict = generated_sections or {}

    # 1. Check generated_sections["LANG"] (uppercase)
    if sections_dict.get("LANG"):
        lang_raw = sections_dict["LANG"]
        log.debug(f"[LANG] Found LANG in sections: {lang_raw}")

    # 2. Check generated_sections["lang"] (lowercase)
    if not lang_raw and sections_dict.get("lang"):
        lang_raw = sections_dict["lang"]
        log.debug(f"[LANG] Found lang in sections: {lang_raw}")

    # 3. Check meta["lang"] if provided
    if not lang_raw and meta and isinstance(meta, dict) and meta.get("lang"):
        lang_raw = meta["lang"]
        log.debug(f"[LANG] Found lang in meta: {lang_raw}")

    # 4. Check briefing_obj.lang (attribute or dict key)
    if not lang_raw and briefing_obj:
        if hasattr(briefing_obj, "lang") and getattr(briefing_obj, "lang", None):
            lang_raw = briefing_obj.lang
            log.debug(f"[LANG] Found lang in briefing_obj attribute: {lang_raw}")
        elif isinstance(briefing_obj, dict) and briefing_obj.get("lang"):
            lang_raw = briefing_obj["lang"]
            log.debug(f"[LANG] Found lang in briefing_obj dict: {lang_raw}")

    # 5. Fallback to "de"
    if not lang_raw:
        lang_raw = "de"
        log.debug("[LANG] No language found, defaulting to: de")

    # Multilingual v1: Normalize to supported language codes (de/en/fr/es/it)
    lang = normalize_lang(lang_raw, default="de")
    is_en = (lang == "en")

    log.info(f"[LANG] Detected language: '{lang}' (is_en={is_en}) for report {run_id}")

    # =========================================================================
    # TEIL 3.1.4.x: TEMPLATE SELECTION (EN cannot fall back to DE)
    # =========================================================================
    if is_en:
        # EN: Use REPORT_TEMPLATE_PATH_EN or hardcoded EN template
        default_tpl = "templates/pdf_template_en.html"
        env_override = os.getenv("REPORT_TEMPLATE_PATH_EN")
        if env_override:
            tpl_path = env_override
            log.info(f"🌐 Using English template (env override): {tpl_path}")
        else:
            tpl_path = default_tpl
            log.info(f"🌐 Using English template (default): {tpl_path}")
    else:
        # DE: Use REPORT_TEMPLATE_PATH_DE or REPORT_TEMPLATE_PATH (legacy) or default
        default_tpl = "templates/pdf_template.html"
        env_override_de = os.getenv("REPORT_TEMPLATE_PATH_DE")
        env_override_legacy = os.getenv("REPORT_TEMPLATE_PATH")
        if env_override_de:
            tpl_path = env_override_de
            log.info(f"🇩🇪 Using German template (env DE): {tpl_path}")
        elif env_override_legacy:
            tpl_path = env_override_legacy
            log.info(f"🇩🇪 Using German template (env legacy): {tpl_path}")
        else:
            tpl_path = default_tpl
            log.info(f"🇩🇪 Using German template (default): {tpl_path}")

    tpl_dir = Path(tpl_path).parent
    tpl_name = Path(tpl_path).name

    env = _env()
    _self_check(env, tpl_name)

    # Context
    sections = dict(generated_sections or {})

    # Alias FUNDING if necessary
    if not sections.get("FUNDING_HTML") and sections.get("FOERDERPROGRAMME_HTML"):
        sections["FUNDING_HTML"] = sections["FOERDERPROGRAMME_HTML"]

    # Ensure qw_hours_total has a fallback value if not set
    if not sections.get('qw_hours_total'):
        # Fallback: 10 + 8 + 18 = 36 hours (DEFAULT_QW1_H + DEFAULT_QW2_H + FALLBACK_QW_MONTHLY_H)
        sections['qw_hours_total'] = 36

    # FINAL GO FIX: Server-side hygiene for placeholder strings
    # Clean up placeholder artifacts before template rendering - ALL string values, not just _HTML
    PLACEHOLDER_ARTIFACTS = {'?', '??', '???', '—', '-', '–', '...', '…', 'n/a', 'N/A', 'TBD', ''}
    for key, value in list(sections.items()):
        if isinstance(value, str):
            stripped = value.strip()
            # If the entire value is just a placeholder, set to empty string
            if stripped in PLACEHOLDER_ARTIFACTS:
                sections[key] = ''
                log.debug("[RENDER-HYGIENE] Cleared placeholder value: %s", key)
            # Also clean "?" embedded in HTML content (safety net)
            elif key.endswith('_HTML') and '>' in stripped:
                import re
                # Remove standalone "?" between tags or at line boundaries
                cleaned = re.sub(r'>\s*\?\s*<', '><', stripped)
                cleaned = re.sub(r'<p>\s*\?\s*</p>', '', cleaned)
                cleaned = re.sub(r'<li>\s*\?\s*</li>', '', cleaned)
                cleaned = re.sub(r'<div>\s*\?\s*</div>', '', cleaned)
                if cleaned != stripped:
                    sections[key] = cleaned
                    log.debug("[RENDER-HYGIENE] Cleaned '?' from HTML: %s", key)

    # FINAL GO FIX v3: Fail-closed for executive sections with assistant text
    # Suppress section entirely if it contains assistant-like text
    ASSISTANT_POISON_PHRASES = [
        "beschreibe dein anliegen",
        "schreib mir, wobei ich dir helfen",
        "dann antworte ich",
        "wobei ich dir helfen soll",
        "ich sehe keine konkrete frage",
        "du hast noch keine frage",
        "wie kann ich dir helfen",
        "describe your request",
        "tell me what you need",
        "I don't see a question",
        # FINAL GO v3: Additional fragment patterns
        "oder aufgabe in deiner nachricht",
        "in deiner nachricht",
        "aufgabe in deiner",
        "frage in deiner",
    ]
    # Check BRANCH_DEEP_DIVE_HTML
    if sections.get("BRANCH_DEEP_DIVE_HTML"):
        content_lower = sections["BRANCH_DEEP_DIVE_HTML"].lower()
        for phrase in ASSISTANT_POISON_PHRASES:
            if phrase.lower() in content_lower:
                log.warning("[RENDER-HYGIENE] BRANCH_DEEP_DIVE_HTML contains assistant text '%s' - suppressing section", phrase)
                sections["BRANCH_DEEP_DIVE_HTML"] = ""
                sections["branch_deep_dive"] = ""
                break
    # Check KI_STACK_SUMMARY_HTML (FINAL GO v3)
    if sections.get("KI_STACK_SUMMARY_HTML"):
        content_lower = sections["KI_STACK_SUMMARY_HTML"].lower()
        for phrase in ASSISTANT_POISON_PHRASES:
            if phrase.lower() in content_lower:
                log.warning("[RENDER-HYGIENE] KI_STACK_SUMMARY_HTML contains assistant text '%s' - suppressing section", phrase)
                sections["KI_STACK_SUMMARY_HTML"] = ""
                sections["ki_stack_summary"] = ""
                break

    # FIX-R5-6: Filter effectively empty _HTML sections to prevent blank pages.
    # Sections that are only whitespace / empty tags still render page-break containers.
    _EMPTY_HTML_PATTERNS = {'', '<div></div>', '<p></p>', '<section></section>'}
    for key in list(sections.keys()):
        if key.endswith('_HTML') and isinstance(sections.get(key), str):
            _stripped = sections[key].strip()
            if len(_stripped) < 50 or _stripped in _EMPTY_HTML_PATTERNS:
                if _stripped:  # only log non-empty being cleared
                    log.debug("[FIX-R5-6] Cleared near-empty section: %s (%d chars)", key, len(_stripped))
                sections[key] = ''

    # [FINAL-SANITIZER] Last-pass fixes BEFORE Markup wrapping
    # CRITICAL FIX-B1B2: final_sanitize() must run BEFORE Markup() wrapping,
    # because string operations in sanitizer destroy Markup objects → HTML gets escaped
    # -- O2+N3: Deduplicate hauptleistung + Kl→KI fix --
    for _n3_key in ("hauptleistung", "HAUPTLEISTUNG"):
        _n3_val = sections.get(_n3_key, "")
        if _n3_val and isinstance(_n3_val, str):
            # O2a: Fix "Kl" (lowercase L) → "KI" (common input error)
            _n3_val = re.sub(r'\bKl-', 'KI-', _n3_val)
            _n3_val = re.sub(r'\bKl\b', 'KI', _n3_val)
            if len(_n3_val) > 80:
                # O2b: Case-insensitive dedup check
                _n3_half = len(_n3_val) // 2
                _n3_first = _n3_val[:_n3_half].strip().rstrip(".,; ")
                _n3_lower = _n3_val.lower()
                _n3_first_lower = _n3_first.lower()
                if len(_n3_first) > 30 and _n3_first_lower in _n3_lower[_n3_half - 15:]:
                    _n3_val = _n3_first
                    log.warning("[FIX-O2] Deduplicated %s: case-insensitive match", _n3_key)
            sections[_n3_key] = _n3_val

    # W2: Also save a case-insensitive regex pattern for hauptleistung
    # GPT sometimes changes casing (Chatgpt→ChatGPT, etc) so html.replace() misses them
    _hl_ci_replace = True  # Flag: use case-insensitive replace in U1b

    # W1: Save ORIGINAL hauptleistung from BRIEFING (not sections — O2 dedup cuts to ~42 chars)
    # GPT prompts use briefing.get('hauptleistung') → full text lands in GPT-generated HTML
    _hl_original = ''
    if briefing_obj:
        if isinstance(briefing_obj, dict):
            _hl_original = briefing_obj.get('hauptleistung') or briefing_obj.get('HAUPTLEISTUNG') or ''
        elif hasattr(briefing_obj, 'answers'):
            _answers = briefing_obj.answers if isinstance(briefing_obj.answers, dict) else {}
            _hl_original = _answers.get('hauptleistung') or _answers.get('HAUPTLEISTUNG') or ''
        elif hasattr(briefing_obj, 'hauptleistung'):
            _hl_original = getattr(briefing_obj, 'hauptleistung', '') or ''
    if not _hl_original:
        _hl_original = sections.get('hauptleistung') or sections.get('HAUPTLEISTUNG') or ''
    if not isinstance(_hl_original, str):
        _hl_original = str(_hl_original)
    log.info("[W1] Saved original hauptleistung from briefing (%d chars) for final-HTML replace", len(_hl_original))

    # U2: Truncate hauptleistung in sections for template rendering
    for _u2_key in ("hauptleistung", "HAUPTLEISTUNG"):
        _u2_val = sections.get(_u2_key, "")
        if isinstance(_u2_val, str) and len(_u2_val) > 80:
            sections[_u2_key] = _u2_val[:77].rsplit(' ', 1)[0] + '…'
            log.info("[U2] Truncated sections['%s']: %d→%d chars", _u2_key, len(_u2_val), len(sections[_u2_key]))

    # -- M8: Content gate — hide sections with <30 words --
    _M8_GATE_SECTIONS = [
        'KICKOFF_VORLAGE_HTML',
        'NINETY_DAY_PLAN_HTML',
    ]
    for _m8_key in _M8_GATE_SECTIONS:
        _m8_val = sections.get(_m8_key, '')
        if _m8_val and isinstance(_m8_val, str):
            import re as _m8_re
            _m8_text = _m8_re.sub(r'<[^>]+>', '', _m8_val)
            _m8_wc = len(_m8_text.split())
            if _m8_wc < 30:
                log.warning("[FIX-M8] Section %s has only %d words — hidden", _m8_key, _m8_wc)
                sections[_m8_key] = ''

    sections = final_sanitize(sections)

    # Mark HTML sections as safe (prevent escaping) — AFTER all sanitization!
    safe_sections = {}
    for key, value in sections.items():
        if isinstance(value, str) and key.endswith('_HTML') and '<' in value:
            safe_sections[key] = Markup(value)
            log.debug(f"[RENDER] Marked section '{key}' as safe HTML (post-sanitize)")
        else:
            safe_sections[key] = value
    sections = safe_sections
    # Safe defaults with FIXED UTF-8
    # TEIL 3.1.4.x: Force LANG to detected value (no fallback to sections)
    ctx: Dict[str, Any] = {
        "LANG": "en" if is_en else "de",  # FORCED, not from sections
        "OWNER_NAME": sections.get("OWNER_NAME", os.getenv("OWNER_NAME", "KI-Sicherheit.jetzt")),  # ✅ FIXED
        "report_date": sections.get("report_date", ""),
        "report_id": sections.get("report_id", ""),
        "BUILD_ID": sections.get("BUILD_ID", "B734d"),
        "TUEV_LOGO_B64": "data:image/webp;base64,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M8cWWmeizEd/9+F/2bsZbXLunTbtYLVJKLqhnWGVyfY6vuJ/W1P6xYLKXVRGmiBqAFVEDbouB1+5Xe190P6eTRaTcIqm3qFsUJFEun2t72pXey/bs4QiLbuEhY4olHgUgVDB0/4f7ervM8epmMrbgqgARYgSjwYxay5cBfZxZw+5ixUxaimIBoMSRCApX75d/f3m1MA1haRcDVcJlqCoiSS1+gNtxn3z/2M6kt7rZNKilZk4c6hEFRIJkhJX7m9XgX86hSU9ajQrVC0WLTUhiiWp0ltmkzefRTe0m9tJ213NYh9uuqycOrtv1w7lLzoGMsmduRMJElQjKolV9PJl23T43r/5y7/+i776pS997cOvfPjhl7/8wZe/9sUPvvzhF7/45R/8/i/+4Je/+IMffumL3//FL33fF7701Q8+/ODDDz742he+9OUPv/LBl7/+1S99+JWvfPiVr3/1ww++/sEXv/CVD778wVe/9uGXv/7lH/zwK1/5wS997Wtf+/rXvvLBV7/+4Ze+9MEXv/ilD7/+9a999SsffPj1r3/1w69+9cOv/eK77rj1tttvv/3uO//7mbfd9j+3PfOeu++8/fbb77j34Qfv+uz26Bftd1686867b7vls7/wuVs/e8ttd95+2223fOG2+++68647//vWZ9599+333H3X/ffd/W83DuLpt91z++233nrvLbfccutnP3PLHbfdduttX7jlti/ec/edd912621f/MIdd9158QvPvIJ//Jd++OXv/eL3fvf3fP/3/5ff/V993/d+8ANf/P4vffd3f/dt997/P//xN3//t/9+x933Peve1x7IIyWq5R6FFNcKQUAxorLA6ue2+fDHH53qbDtnO3VWnXPu9z3O62OPc855rNXZWTtqs0d0zuNR55yd2c7aao+zczrnfjrbzn12dvY42+mcETpJkWAsQlWSw8GfvITW7k8xkkpVBiRKJQlArEql1+nJIN7hXJUi9DHm3keNIjU0xCTOffbxV/DvOkHlmkpSParEfvCfB3IvEYrSUlErj60EjIIiiOmrf98mxN/u/nh5e399ub/e7y+P19f7y+v97f1+f70+7vf76+vrt15eXu/319e3j8djr6+P1/vj/njcH/f7/XHur68v9/vj8fp6f/t6fzzur4+39/v9cb/fX14fj/vr6+vb19f7y/1+f3t/vb/e74+X++M8qnrvVeu6rGd93fZ9X5daH+ajH91RW/Z5LuZ5nmrqfe59GvMYfV32S1/Xde37ta+9/q4N8ls8maZVr2nuU5979Wk6maa5V++ruc9ZjdWl47G8gt+mj966Px7n9X4/5zwer4/7/ZzT1/1+XZeqtfe++Jhh/HO7Ri1CEouksgUlHgXVWmppM+J/f3s8OvftbG3Oztrpscfp8dh5nO3cd3am2dky21lb55yznZ3HWVInY+e01tljZ+dsa862x9lpkECkehWQ6kVS+zNe5tEt2uOtFCMJKaoCgUpFoOhV6dW/aBSfd9QcMioAqepj1CCURsdcx6svtit8/2X31x22Q05bwAQTqndWv3gUL7UwJiJ7SCRicGKUbETxsPcJU8L3buucc2+19diqnXPKds622s42U49ZbYu6bGt7nFlbjdZK65y1OmvSzjm0VVENSYwVIpF+evDZH11rb5CkSJRkJMGkSJKehISq5Y1HcVwJKUqAIhUqFVWSSu+r8YNXcvvPZjQYYwS3FTHV61mDOEwGkpTl/UjQhgxEStyii5/fpsRfkZ0eOyZnZ5lH2xlns50e21YmxVwytuaxc1ZOp8mjk1KnlkdnYbbKNreRlFoxBit1tt51cil/11ERwJ4EMSYh9iQIPXX65EGcpcSREGOSFGUlisa6OPcT/2A7+Bh/sVecUFo4DooGQ7nsfewYfpK5omJOslLJFWlmIqIiRqj1j9uU+JMebYdtwR6djbWz6WyPLTs7G1tr7GzFnjt1sdXGWWuc7TR2mthZGztENEpQsURg3/+8Xeon7EIVMamEiCaJCUmV9v4fbZDflBpRi4BuCCahUO2jVnlOu9Kfec48jdl2WEg0qdDNwS8bwm9xLhUhFJUWlkYddzkmFhqe1ebEXwdCwRpVxGau0SLPV64lKrlOrnm+iDLPc83HRQVRpaiHl4++pHvHjFEFXA+CGo1CgN8bxd+IUggiKIJg1EKqxjwOruj2xZfXNikRJEo8DvG/RnCjFaCIkXZIzPNFEkTFDsW6r2efEt67/cmYRHnanjCEEGsJQ5TneVKued5gI4hJEUUejYKJCGf9JS/l/Dw6KugG3IiPiMnq54/iFwiKRgyquI6be6b6Yrvyv8qrMzvkGhJVNAkmXDeAiwISBSvhIjoYK0riFtaqxW9sk8I/ZQlLujCM6njXUmVsNGxEYa5ByiSR5GneEVMFo4oWaqBO9xcu5Sn2oSiiYJINsCFY1XmpQRzMiBEMKmquCHqt/K9X8TMe962wyEoQgwiY6Huet0X7FyaoETXd7LDcFVIgQU3ZF25ts+IvWhEqdLFgKOQaSUSaoEyuRTHXkosydnma53gcjxLA/j/tUt/oKigaVTTKmtsASeXaQTxKUVRjQBEQohW1Mvsr2uKKbr/48ZCjDuSKUVRQpd913tqzJWIQ14ogz4UwoqhCUety87Twep/nx4VQSSlB5JrBXDMiwlyLjTytSA2NpVCqaNyyMejy45f0r5xiiFHKEkBRBDFx4cE2yDcTFRSUaIzgZjSj+9h2lf9L99ck6OPgoz7rN5+zRUdHRBWdK21tKSqh3JjYIb5sO5kUfo7X82RRKk9TzEpoqhDz7qaii6hcC7GRa6ESKRSNtQFQgdT7td0l3E7HoKJJqYCgChE4+Huj+FeWaopSJUaUXCapMbK4mt9w2104rumiAiiih3zWOft+U2ZDUEZE2klCBi21VGMtv9amxT/BR7U8SIRiJHLJUOwS0/XJNptZnkYUlqBihEoYkBBAAqJCXrxd6vFUDIu1aECRgBZIQfkpo/jpEYKCJiIhiiQBpVbjrnbV33q81hALkqASMBoP+7vP168zxkoSsWChOpWVUHoaqCBL3dHmxf+ntzuQEjKhCpscyoxqDlVGmZCJTrm2DHMMa65ZYzOiRiwVyxj6+myX8kTmESglKiBqCKiEEHzpUdw7E1EjUYlRBRAdjCnf0RZX83/yeF2erhUVZhMIUn3PY8/TabUgQgRJF2mCMlaFo0S1yueeGL7qdTDBEPJxJyby7iKCaJdrhBREQ4lQoTxHFLeoCf5bu9Q3C6IiG9SoqKhI9aXaIC/YUXEzaNQgrsf0S/yqduXv3W6/37mvPUuIImrEbd/7fufpIwKuR0QVKUKaK8jWFU1dzFu3ifF+7prkaQhKPRFERSSSEHma8nEv1VKmIO98B6KGjUZT/uQl/TcHGAU3o2iQTag65P9G8SzHmmwAFTdGRXGefMpVXM/9qIjkOaJAjqzeem6W7Q0WikYKvMxdTOQ5j6TAnv6zbWL8Cd1PiC4hkVwXUmRVrjEo0iXv7NKT61xzKUbsCaLKBgFS+fBL+iJFQSmCrOHlIUkd/KNR/DonFC8fQUhUI8h0MrUtfn+PsJTsmSlFRHRdeMx5addpKSaqGEty3M2XTF2x0r29zYy/o9d7zLV3pCAl0/J0nhaiXCNEQcrThS5PSz5+8HhUTMjqS19ST1EqgigGN6Maqs788FF8gBmuILpmubkAV/2ubfxRHllcNKaigkajrHzUuVi01u6onoBRxaiMKXHo2tXcUcHSZ58a/mt7e59vdyg2g9RlJIKIiiPiQQ4jZaIMlbDSZU8ULI+XwlJ186WcJxgCosGNaFQ2oVZeaBT3jV64MaIoyhqqyMX84DZ+nI7nwQAQRdgE6+7Wdv//LVv7Uw5FI4oqmkjCUk1MCQJ236VNjf9FLw9k9axikKcFKYRjWDHVpBTybTdPKyZ5WlBRIoJbWP3fdqlPZVAV0IgIisoRxM0NgzjlKq4HVZA1MWRDcZ+/fRu3XzYqXRZ5FLcEtfa5uZ3LJ4mlCklUCD4exjlRFAmD2P31Njf+8Lce92mmClLE1kXhZMm0PO3IY9nJIiTKRpfUO5LoyZ6IahCBjot/dkm/niocgCpKJaIGBVNUnbZBvthVF1WQaOJGVFDkpJ6+hTe3/64dqcxTihgQUbH64ie1k3NwMOyZBRSkAIol1SoyIkiponPW5sYf83g5L5Rr3mE0E7YFtQ2V1JowNdeEJJwn1hak4OFpx16oMaIWQcuvvaTvsgc1wXUAUYwiVb1W/3QUf8JpWCBCiRoQBYIK83yuLbfw69sKIgKgQsRokbPlYjuPP5JJaxCMGiRi1VQTcpTmWAQVnzA53GglXjkKSBSvFhWMl83zvDu5Zp4joiKiIqLiRowbicQkw2df1S8/FIq8s3IbTXr3u0awaK2931JR3BykRHb08itu39nbKBVQRVGOkDB192u/+bR9xYef8RySYkpMWKNcHDHH2s98zzY1LttbnFG4DG7GzVwmipdFZQ0l197xsUPW1hHFDetxYxTXQVG6FU9dzZs7jHzbgCray9dpu/O3bIt2XyZVlCuS0FCP//A79M8caCJupDzdPDGOf+j2Kf/KD19jERaRxyBP57pgLGDJr7S5cdH+i8Po5S5LRPGyqAYVVVBxYzGICAnJetiwroIQ1WgMqtEEZZDRc9yu9tdp6EkKPckjUPbuc7cBLlo7bScoKKRnmndvf8936El2EFRMkAixPJ1f8Wn78OFfRQ1JmC3ikBjypDrKDsv/nUwOrX3BUnEjXA5cZ5OKGxH0it6Zd+djY1SDipuuPIBXWpQ9H7qCN7fb7c3tz1Wap7nW8bGh6tAG+QSHCq7nnUGXk/htvkNt9Bgxgut7Bxk1Hb/xp+3XYN5eTSIWLt/uzB5rPV+bHkkiXkY1GhEUJCpq1BIuZzRUUpc96UmBqOVGsFRQRFHUNURLJZn9bVfw/P+2Q5ZZi6SoR+ipun0My/YmRxE3X4ojxVzn/uO+Ux+0G1WEtWu0cTLs+D98yr7VyYhgKG+uBdE7Jjrzndr0eJ1hfZOiCl4WjBjXARWBGGSDJ8jT6FlwPdlgZE2D67gZAwoa0n3RVX19U0zBzLV8xGT158fQ2r+xx43EayPXE5we/dDtO/3WtSiqbNgFyXqyx6fs73qNeohTuUoKoqAImuOX2vz4GqsIigWgRk1URBEUNVFAQBVEkpa0KCMIEaOighAFN6IgGlxHQwXOX82bl3tBKxmFDaJi5eCHjOK2nBAV0Soyo1Advvc7do6UCnGdsspCatbj+G0+Vb/RChYkFaSKNrKd7TJh57xt0+Oi/R1XEEEFS9Q4iJLEuF6uQ0DRwvVyXJenBZkhI64jCBYoCUZBjRriehw1qtrV/rpeHYeeus5wxKhmXXziII7m0VFEwQzJtWbZ+e9/x9rtiSqI62UFw3qcw8O//Gn6bp9TJi3RHEVOECtqHWSG336GuI9Qo6JEgopEISRqCLgpqogIRDTMtSKY56BgoorEtaSMYlBAC5KQXn3y59viKn43d5in7UIxVdRlf3Y4GcKyPdu4EdQwzDUTe/Q7fef+gqigIoZJhTCc3n6KvuZFQUiikCkyIVuI7eE8/Pm3+fHoujgTCWhFA6gUQKQIREBJiCSKGjQyNgp5VgoGBYkxJQGRRAWIUFJFSSp0/1G72r/Fq+Z5KHkacdsX/r0N8ai90c4arn3cnpRa50d/xxaPUlTRqI4IhtpKx29ze/Np+UPjbFdpEjsIeZrnucbyH9w+B7l4nvNqNfd5VPUa1auPUVWjxjxGH6Pm3sc8Ro0a6WOu6n3MI5YKFEKUdGGcnVFz72O99z4u3/s8eh+jj5ExRvXq1edRffQxLvmadngV/5nXoCeVp8kjJqs/OoaD9vcdUYSoYRhhys751bfvXLtkqYgVrWSX5lrTzr98+7T+AGspJEjSclViIkqZ++OHb5+LeKfzmKlRjJGkSAoZxRiV9EofVYxQVTAqY1RhWPNjpiAfO1T1PqgqRiXpnd6LjGJUJcFRShV9VLAcuald7bf2MHPt8CQfvx98j1F8xl5rxvVElELm4Qe+cwftfzlYM643kUIt13Peflq+ZThEMYxmVLI8DSHInZ9zu72ZH07/6Ut9zCdjGr3P1ftcvdeomqpXH2NMfZ7nMfepT/M8TX30nhp67FpMz+Tj1Kh8a+onU5/73EdPJY4xz9PovY/e597HqvqoKqrG6HPv82qq4/NX81O93B9FHGM5soFo8HDwSWNYHPYMAVV0nsez2V78D79zrX15CtZUFEJLENVbv/XtvU/FP3MyE8tgw2pBMtdheGRv/fW3z0UeHbXTF85dc82566699sJ11164cMPDbrj++muvOzp/7pprrr1wzYVrr7v+IdeeP3/q3IXzZ8+ePb88PHv+3Omzp37dsJsihDwtz5PT6889OnvuwrnTZ84cnjl/zfnz588dnT53/szZ0+eOTp8+e+7M6fOnzp49e+7c6bOnzpw9d+6aa85fuO78Qx7Zrvy922/ro9NKdYom14lbPOvL9WNo1ztKXEdxrXlaR5c/5JNYHFdcg2jGyFxGdXyz//z2qfzzXiULTZhlzBwZWSrP41v7j26fp1y0vV601tp3Z0AlU/YkQgztMd932+6i7Xp5Fbfb3++b9xRZWHgwCG5P93e2QX6NBBE00OXahTr26tf6JNr705OoIh1VCnWh9fLSp+Lx7pTzesVkZaSktgMnmSKp3b9x+5zkcrFsV75orS0OrmS5abFcHLS22NAWi3bm/kqiZQvqYhL06Bz/5G25tmxtsbZobdEWrS1bW1zZYrFYW6wt2hb/0/PRq4R1EjYFyIaz5ffabgz/gFEJIAhNCBGnc+/x/idw0F7PQBAJtShriGE7d3/I7bs+ueMatk7JfdxzlKYNYyM4UT/r8xIP2FOsC/k2c43a/cV/+/aL4zfPOXnSXAsKVNHTeqs2yNscocCrTUTsPH7w9oksagoaFReZkILk9e35wu2T/1Eh5G15DsnzwcSc2fFb3z7XumzPJKUGekeXj1lnb/12nw0/ea+nYgoSRToi7uspg1jMWVdl055cg3L3j30Sbdl+0iGW651QBC2K8/rqp35i73UMJbKkrQx2oQumy9O7f+n2eddfCUENKl1G9GR1f+snfha8d/s93M3TSjWrJs+Rw+HCIB7mGAnxClNKqzY7b/25n8CitfYmhxIFSSJECOfx8Cd/UtcPyztBHleXergGCc4e843b517/F5UYuXhantYl3c/b22fhm9vf7YGa50EIbJR+Vxvkqx2p8oqbp+W67g+/8SfQ2rKdHRERcAV52lwSj/sXPqk7LEAeG0EEiVaQCEo/8fMvd4/EtSD2jlChl8cHnwm327/e/exACW2enguK8suj+LsWkeRKoBkpzuv5UZ/I4qB9jhFFERW7RF2y7WXvfzJ/WaNEuauuSrBayPOxR/w+tzefdzkzBiRurlZBF3G6v/p/fEb84vM4p1wTxi7JLen10aP4BXtRRAXxaQltLn7l7ZNdtD/O5EZy8XyoVOv0ePhTPpFHCdGjruAopqI67myXMQ/zr90+//oUE1XIaBG9w2Vv/amfDT/xcX/do2RKRJUzikp42VGcjGlcRkH1bFg1x3/wiSyWi/ZELwUR3IEax+bj7mX/5Sdyb3VLg9aGurIYtdmzSDp3v/L2uddF+60KUWFRDZrpUve3fq3Pht/RR91H0DLkFFKyqWcbxLnMYyAlrqc5SMHMi7/y9t4nsPHSIKBSSstOmnUpvvXix38CP8CM1JCQhJm7WB6ulUWOn/T5l9b+raWKgXl3gpj7y3n/s+C929/nMUIEy9MhKsY72yCfHjAoCmpIljbm8eo3vr35pD7eE43JDMXBVFK1c/z937m3BEQsJnaFgiIF4VjqPPxWt8/D3iopMDDpHfLOHL/s9ln4/u0/8XZoqmyOkD4OvzWGRfsVFpYqIpvenXDm/U/uDVqKibkm17HINj2+/h1bdKOCokQQojxISRTk7759LnYGk1LQEhqiy9z9y58Jt9sPuedpxJJDISVAPnUMrX2rrDEEQSk1atrO6/nG7ZNfllWAKkmVsBVrPc7xM67ucMNPiwCuV4REM3eTqWitnY6v3D4Xe70VA+oUl83HOrv76z4T3vy49pCqI9o8vwAi4cVHcYchuJ7gZSOV5OE/+xS0j5q4XgbhCcNoO/7qtriaje8xbkYVKnKvB7lzLbWTH/X5mBc6BzemkkljULbjN/9MuP2azmMajNHlUCiJK/2mQZwaXePlWatyTTq7+9s/Dd9wmZDyfE80pXr1q9pVL1prD9WKChgMYmScTFm6VGIv/pDb52P/mmNEFKYx5VoXtLP3Pxv+JI/TYJzNNfM0DXSftRvE4xyK0SgChyRR5OF3+jScHUQp8848HUE2j0fXX1VbtHaPxZq4ucSUwqEoi7zz9C/dPif7E67KCuqS1VFKxmr3ffP22fgPe/FYKcmkiiAQu3/ZBvneYNZKQYqgipTdj5/4aWift5DQULUiHZmahz38iatr7Z/ZpTACC6ZSbVnPaOfSOnntV98+L3tMpypGFIwgx/V43b/zGfG187qWCjqF2aIIRfyWMSzatxVJlCiqWEGJ7PXxzdun8k/YC0lZZATbkLbc3beFL3UUMaCihbV5LEhb61jF0X1+wudjFm2ZKgDViASi4CPjsvqJY/jKs0/bjM5FbXBBqva+yhhut7elQliugCoGral+cD/OZoyCpK5ZJEmopF/v23nvx9x3X3SMkpphMmToQFkC6ctF377Nso+14jpBARVRUTjSyyeP4Vv3uXUk834pXcTevWUQP9YZVBER1zGoMLq/az/abcaqiBDlsUpB9T/7GG8utx9wb7NcZygxNT0JPdvGrP5Im2IXbdF+k0NFBA1gVEAU1KxFG+P3+XheW1HEZjKnLCVLnbVB/kYersskukyJiswrn7Inv825RFOieexgucvLD32Mp3+2YUmJUugp2ipjlcYgh+WuNskuWvshBlTAjURFQNyiHvpDg/hlHxf0IB2Rgkgt+cdR/KUeaXBqQkEVRXWUp/djcX2qY1VTyrBownbd/QYf732Psy2dMtFEtaJMtZ0woSyrr885y7TWLlbvXjZiiJEY7Bv01N8bxF/53LZVLDMbR0i0zvyaMby5/Wu9HOpwcEEFFCTxhPvavt7DJEZCZQxGi9U3/cO3N+96c/uww2IdSrFYSxxciCFGKd+ozbNHGWOwBuAWY1SCUfHUTxvE5/OazvHciFbuAll87RG8ud1uv+J+gqXSeqKIYuTYH2uLPfkvjFCCarSKrDy2t3u9vfu9219P2AR5YolJiu3JioqWP9wm2qd5kmy4fCKKUQQCp3mZthvB4nl9nhXSYizLMtp7+dgR3G63H/U4p55ESUSNICCc+Hvack+ebxU0mZWkwgxZvX7kN3jX7ed4rKhktrOZqcXSkZWZNqL02reZ9pfbiURNoSgYUWKCmnW5dgzP8j+vF+coqIXZoLJmrWqD/K29vQ+x5ToQFaKaVF7QDvakJcM0o5KktSTROt/aP/Yxfuh+31ynldZcZ6Q5RetUykD0hSaaRXu/c0RAPYKPSFQKPXtmG+Ob01Ye8xjClsp6yB2j+As9HpFvN4hqEKe60Pb225i1JtkWIuMh3O+Pb77r/8VJJdsi04U0uQ4TWiUHfP021V7MHDVilBgJoEQloP1P224IP7SzWRKMZF2JxcEfG8W/5i2ppCugQVHQzHe2fV20F+paHuexKIjS5rd89ls5IyRUrEhIhUoxlLD4vW2qPcMYGlGNbgwiiltMfVYb4x8zCMVCmbcFZ77tKH5FZyGXlShuBI3pP7Y3rR0MVdloKdJVqtC9f+rZD1siJFxInoZKITKd8n/bTLtoT7OPqABqIB5FVBEDLzmGOlXIypeskNW7z9d2Q3jvfso7wzPZpAr+lv1ZtB83pnzhEmqee+zt7fbe7faPe5ws15Jr5WmSawSFGG+YbH6pfSqiBEUVjQjCJri/YQy34KBlns+7O4p1XdogfyOvZ3vWgT3ZiCLEZ+/PYftGozzWFMGSlF47D7/m7Xb7A1gzKIMYBKMJmUj0vW/cJtvvcK7gOgiKJqogisIDbYyv4xK1rkjSLkey5t5R/Lnuj/UkXQTZsDmp8/uzaGeVvEGe8pit6fhXbrebZeoiXeaaa06DeEbV+b7WWtvNNHdmjFpjLaoEFEtBTfznIVTyA1ZlRChoLSOV1V8ZxT/i7U66ZLKIikiwMi62vb7VsWPXZqSM1kQdfcM3brf/qLZ1mmyVNCdJc10b2kqc0+9r0+00d+aIUUxQjYgSN9q/dAgif6BnQmYPp0g6Vsnet2sXxvCV+8uOJ5KDIVGTiGb81D4t2+921ghz1+nAk60OP/ovdzZMYVTIcV0qjZpSynIy3TzO3kNUUFEIweMY7OVLjKECKnmsiJWgrJaLPqaN8P3b7a0IIsgVMCWhir+6T609xnGENpUJWUPmyM7/+ReVa6GQwjwTXTH22MnjZU9v0+2bnBJQEoOIoImCsk1de+6qHVfT5LF5m6hI9UNPG+J33X6qs2d7shSDRo1Uhq/Yr3ZSh4gg1rU2waY+SiIW4hAJmafLJjlND//1Nt/+E2uUa6AoBEo1wiZr9m2ML6TmcSgGy7is9nX7GN7cfisLRaI8j0YgMDizZ//KZIrI+0oJW4UgZXm+wpjQIJlyXn3hNuHe6hwQN5J4FPF4wup/n79qxz9hjjxfb/MYvfvDY3j/9ve7IyTxDlAFQ6oWe/Yk50S1IrIWCqNYpdDkMsq7y0IxRMfjuz6Pk4yhRHGdyBEVLYCDX3f+dv1ty1lFKI7sKITl1Lcdw+32nzoxGCkLrmOEdG9t+15r7ow8X2EoylEtkUMhQnlekDNz+K1ub+abR9oTqyICokpUoyUmOfj6g0jZplYG6UA5hnW28MRRfORhSjktKBDBgHT/+Z4t24+URKMSilBMwgiXmZJyXSUyeTrHzj98+7ztorX2S3JSpopCS4BHwpRa1urzjuFaJq1IaxRK69acLYdrBvETOptFqJoOAUWJDr95z1r7ynMopKKZWNBca0K7kKVsnaRZHdil9bj3C26fy/1nNQ+1xHUSUQBVIqSztDE+ws4ETe7TKVpzb7/c3Qb5O3idB7nWoBFUw1DLp+3d0V4tzQarWlYJJqxBxyFqScc8baSpgz3O+fGfz7ndGBAVLx8QQDXLWn8/iH8dxUlBjcIoVHu4fnYU/12vJ09jTHmKWqT31XHb/z/d/7BWScUmyWPKO4s4s7gImcx1joftW/3Ot8/npkoUxY0pQaVUVOrg1w/iD7wL5TEViZjU7PPeo/iP3beePM01xSiVqimfeQD8qE9n7ryNGKmkZFWkJVh5HiE6d2ntf3z7fO51FBkhriMaUY3bhM2bDaJzj9SVVGPSQmnfHzeKb+5xMiKyC41gDWqc+G8fAF/rc6NiXVOCymQpNORjritbUEdrJ8eXb5/T/QqqQGVtHfA4buN65uPHsN8VrnlasBCyynrxwiDe7P4YxmBQlKj2kTHnNQ+AD/+yLQkmd6WEFkWjxWKNRN69tB2d8eM/r/OnB6LB9WCJbI2Anb6shzbG5zPBghjpijFSO/xjG+RPcz+tBfFAiOuYVB17zQPhF3w608jYFfJYsTmkSQhRshrTHFIe/tTb53U/xEAJKGqBaAliQlJr7h7E/8di8HYRBXU8buv3juKP8nhwzrpctQoFtcbo80l7IH6Hc3aCFIZIhMw1z6tBPmbzNJP5R2+f2701AywQNZhN2GhBpQ7+yiB+MaZmeyplagonkfrAUfx33c+qedoq66rReR7HdesD4Ss+dGrbTI+UiulM1ObaxpOe1BNGVtNr37z9f+nxDXBhVSlUFNQAUdmq9N73vs0gLiZT6+ZUMIRs4VUvNop/5/F6Ym2oCQE3Zh4n+VsPjN/xiaOG60hLsT1hOyNmkKmyM6QWtdeHn/T/rb3431x+d1kh5J2IurFqOfgCYzjFKPBcki+51fbPMYpvGTRCIaCCVfS973sebrffwcvDtQtDiJENKcpzCqKoqIhF1r1v3iadN29ufz8NQ+0JKkiOUX3djWDRnmUvfGxs6CFhWXuoDfKnPTYa8jz0RCWmfFzbnYf3Xu6NlJIn5TJBqowlzKIACIEI2Nf1e9rE+90mo+KCKooq0l25vY1w2X65Y2hducfIEsn6x1H8vsYyShIxFdWi92rn9Ms7ZOY6ma4o8lyRL5goHg0GOfS72sz7rUMllCuCx6NaS351CAftP9oTyF0es4UqO35iFP+3eeT5QhDKESjuPC9/vqU6SJIiwzqURGEpWUVkgxhD6saZ58d7xUiuUVEtj/c6+L5DaO3zzFWOyHzRxixnve8ovn4asdC34Tas/NJ5+S7bhHgHYhrpVqZiqRGoogEt4mu2mfe3de+p5wuoQRSDVatPGcNyZBjynISgpHT2QqN4FaZQPSkVamLovsd5uf3iHqEn1BO13uEeJdlEl8oGIel+Z5t6/w5vT+UgCUSNBo3WcujXjuHR9ozCfWgxlIqVM889iF87B+VpEQZurCyLTzwn793+Gm9nl2yCVkoTZazZVcqsiCoatHNvm3v/871tjWqpBokKqpjs6/42xrc5V1UQtjx2Fp119e+7Qfx1TGhz3RYMQU2W3ts5fXP76e4PFCOjUiqPrRXLGpXUNIUileiFyecbXkdFXHIb3SAuZ/Vrg/iYfQwN0cE2d5jtvPxdG+S/soMiLM8LKtH1bP/Aebndbr+ic3Sxklxb6KJUhmTmRi0N9H7wDdrM++Z26zwy754RPIpHs/hBgzimJ0l2EURlWeqzPx7FN886lKQ2FIhb6pA/OB9vLv9Lo4hwKbLeI4eCJCJGBdz7TW3y/dl2qTQL0wgJbpN18QXGcGivkuGqKKpRenj57SG8uf08RwtR01hIeQQ/83w8/Q1cC3Yy2hNqI4uVaT01CcbQWfu/t9n3D3RGCRKh4JaQuKy5MIYnOY+qSEEMyqiUj35lCLfbf9MdzbVjFAaKHHmpc3T7htkhiO1SYqMiKY9DFTQKrmudTD//O/dHUhmRAIolbk773W2Mv8KRUWHYk2KiHOajnx7ER3s8QhlJB0WM29O+Xnc+3txut/du/2vImIhKq6SpxWpF8lxU0cPBV2nT71fPy0HsuNZAAaMacpHfH8T/dKpkWCFNlkEk++j7R/Dm9sd6WHRJbY5YlSDxYj3YzvNv6lCyHGvRBZVCI6WUnOUx9n5Dm3/ffuv1Xp42oWiMRDSVs/rYdmEIP5lVJUlJdjJSse3UfPazI7jdfvV5Pcs6SJrOqFART9c/PTdv3ry53V4dus48JONsMM6xVg3NalqJCFlva/PvT3t8tFeJUiUJohijZKkXbCdDuL+vOjp2aauQOZhtHb97MoK/8/H6WNtom5BVjIias/qyc/P0n3dW1LakLI5uWQdnrZI2DCilTtv0+/7tD3NXtDhyPI8RFXW/v6EN8ewQUUNRisLyuPl8/blZXObN7aeyhFISgjxF3fPC5+t3POceCyvXaVCUZJQIQkzlcOZj5p/b7f/hdauiRGoDYFBxuaeN8SZSuDERW+5U0nJ827m73T40HzOokOyJyrK/Zneubr0+QhVZhTQug1hKrVzE2vv5bQb++h4OzRqHTAENaiTL7wziVSEAm7pqCklr1LzhvFz+/e/XdLBFMGUKeYRntnP+K/fiImqbtANVs2YRSVOSZF39uzYFf+scYkOepm4EA8rHD+J3aSWqFlTL40pqEXfdeL6u+YKd9UDC8jQEJKD+6Hn7S5zp6WGmDDU4SMMQMoTytE3BP2n3u5KNsyciBI1iMC86iH85koCORKSa56zOHHLnzedm2drXdZVriANx5Dlq5C3O24/dHjUpMVRSoSiW7Jqr6PEF2zUz0B/ifh7KtasCigiJYt3SdkP4bgrdhJgsKyyDWZbaf8B5aV/xaU86KyvPRuRpTY3g+hzn7fYLe93y9HgeMrUlVYRkRKu+ts3B/4vOWpXBaBkVVbTHh9sgfyYUAVZ5aV2rcBhryfrg4j+/2nk4+45bdHXSY5inQVO0SyCGPNjO/V/hpdXRFGtWzX1Mts6KKTEe/Os2Cf/Ay4vHCsppNDZahtLUfwxieV8F1aqG86BaYVbEWg9L/I+vfcz/X9e85kdnp5ov1dbMYxOWp7ViM6rU752/n+RxWOvApuS0q70600o4kVRyTdvNQG9ujz0IJdFWahSRVMofHsSpeyNGIRE6EEXsFBUU+sO/9Q6Pu+bYSWttt2tt11pbbuFxf/b2ORHQpEIqvON5xIRaeLPzd/vFr48ki2BNhZhWyJC28zorT2yT8E93RgmlUIIbo6b7loM4uJtEjet4zBfMw1s29kI93Pmrn/CGL/XkWy60/6fnH/bcN/75f3EX6uipiMhcI9fSUIaArMk1A/ivuc9IGyMihqaaRXIOnfywtpuEfjeP9i4jAi2UgKm1bhnE0f2AEUMJIlIFI/Fo1f7QE9TUevrgP/7Fr/3cj/3kD/3gv//3//F7f/QjH/upL3zxvjmuJ2NUBRGBMQjV5GkUOllyexvgr+v+oMhE0HWPYYqcs3M6/qxNw3+nt1ukXLc8DSqqlaUN8vTFmIgyjzkQ5TE3ihgChL6u++puo4oW65W59xqjRk8AMWoIMc+75HlS4eCHjeDNDz1mXJ4mpTQaiqSzenntdTIP/UdezzKoC4eImx7g4B3DuK+rBAcldwbxghFFsEjVqj1JrcnS94f1sGY1TdM8TWMac1UqSTShRNQVPbkWjHOJkvTVG0dw++c6dcQuZTMJRzRCTPbJd7Z5+Bu7MxMyBzkKCYHF7xrFuXsqqohYCROxupRHQ0wUMbItNNVTgSoUpRJV4mVxrTzNE+lZnXKpv2oDfP/2uzvbKPI0xNznQUezOZ/6iQ/z8I+7P+ZYiyEBoEQNrL7jGBbt6N4oooOqoahMNRqNFpoe1SSKCWCSFLFSGSAQQQGzJrEg5LpLrhRZfNUR3G5v7qdt6IrVZpxGtHJgO5/6kw//H/Hv4fXQQ57W4GFZSgQqPn0MrS3uLUBS5l4VVqG15q5ENSUKVYgKomZdSQIKDqKJJRsGncrlijXDWHPgtA3yP3VsE4lIsKMaaaH26fjw/xP/bchGLKH52FXrsrZh3q5iiFgMKWjK0yXL20okMok28hy13FGehzAzDDXJ0n2rMby5/R7OYJSyAxAjgEaFotv7WZ42Ff1zLeMJY56yIfZee+4exbJ90l4qmueF0TDPg0Sth01M5V5UiCl3rWvsyfNSkIykFve7Mdxut04jUugaUQmgQVGS8qPaVPxRj9mkmtK6GMSQ6qf+wiha+wdWseF5VJDyfEErdyG1Gpsqy5o8t0ErlWtt0hq6TJLu6ke1YX4VzYXNgojBLWgh0aX+qk3F798fFUZBNeBxsO/94HG80RFFYq4JYmII0kMhMqiQKURX3jfx9DSiS+pSiGfXjOL921+kSBEmUEEBNSpIPG1z8c98rOoyjo5cUUQj/cwXHscjBt0ETxGDYlESy4yRiMSyaBfGtah06eFIcaSYXEdiXf3Q1tpuAG9ub24/hSnkGiEYjRIUUROfMRn9gXtIYypFF3GLVO+0cS5vpwfgEHNQmbAwQjJRqJAgTxZi5a6CIijPyzVM2ftQG+Ob25vb7fZNEXk2GhBExGhh8KvaZPw/OFsdVpwxVIiCVaz10EDa33cl4opDsGoxKsaMtGKGbEVWWjJd0ZI7UjFDekopmXVfcRDXN7f/g7rMZqWggkcLj4YH2mz8X5xjrrmuLiKohrj3T0fyUgdKqlAHWWsyCVWQhU4VVsLKiLknsfWgJ5xqlERtouOvt6H8ZtpFtmIiIhSoiST69Nnou351bJLnU/NOtNIPflrbjaNN1TGBXMu3H4nytpDnIqKgecydeRv52JH0eLi/DfabWy5FIKKKEEWXw8EXbLPxTz8ItVgUJGoUKZ8xlL9hVRkLXa3K3tETUVAe524Rgrxt8pz3wXpHUM5sXng0/6wHTppr4BYRNysHP7dNxm9uvzeWiTgKkmI0YYkXhnIuVW4sRZWg8s6QRGRdCSWoIINK6k1F8C7KHluP459qo/1N2klhNTCaeJRYa6+/avPRP2AIJs/nKYhWdR5uI122f2WXTXmap8nzkKEUxMWuLzmIYL5gni/J8x1nfultvPcTQxjicTaSnrM2If9X5xQjKYaAuCWrfzWU1q6fLXNweZAxKdKTQ+JIPS2i4byZ50G+4KQyz3eJY3dvf9pn0L/vKFbeySaK6NniS81I33wsakKCKBTZdD9tLMv2Z0xAUDCFMmieJ6gHlCJ7mDtvl66Sa3nax9ju/Da3z+DfxcEhE2wS1aiWX9sm5J/ay8hBOAgDkWhV94XH0lq7FGobwXKylkPFQlQTQYyJkmhJ6gpNV4VFkjxNd/7A22fyfVk50hBxixiSf2wz8u/tI4VThFpoAVFqWb0wmMN2o26ynGAGxcRsUMe9Fqzj3s5gFqRcCvI8G4zBevgzb5/N/9V5qNNyjRg1oJqlTcl/txcu8aQihIJ6uHi2tPH+FsddPWbBiBCezF2h3KW5c7cLzR1ERpfK87aH4tz/kNtn9J/upOPpUkXplKnujXPSd1/eOYSGCIL2pf51QO1f+HjcO1AkT/MO5LGIjGgMOchDaJAdyLeZdeo+L7/97bP6x0ykCyEbk9AXv7vNyT90HunZNXOtqUZI9/tH1D7gPHqszaCe2AV7KoioJY8FKYmgUsjdO5Jqu9+Pb/yM22f3LzPECsVtL1hye5uTf9y5P453l2u5IqWaxbcc0uG/4uWcs8q3XSKSx1Aa5PjCkSCPeSxPR7DtHB/89Ntn+N/r4RpPBNUkWW+Zkt7cfkMv93o2CfNOPHq2+uxDard/3XnoRH2MmRjFFYmJGIxTlF3YEHk+EPSOO//47TP91ywKlsSjJOWrtJM56c/30Z4UBfUkKY5c7Esb9X/Xed1yHT1ziTw/ILq65Lnqyoi+wNMyaN3z8vvebm8+y26/2nmSuUaxrPqtNiv/+3v7sstJFjyT2+jD6x1tN57F2u2v3u73VU5FhuxjjBZNFquQVIIolQq9CRJsx//j9pn/j5iZGNyiC3e2afmHH29fMFSGqWGUKp7VL7Zx/8xf0ssjIW1YuYZoLg5Fa4U1d+sya5QJXUlnh84v+PVun/Xv334rZ8GAgBrObpmXvvm4P1yT51Vkaihy5jsO7Hb7r7k/PjqP1/vjYafTXHIt4qFJnhuLaiiGTFOddjx0t4/u95f5od/v9iPiR/czBkUlrKsv3Kbln+Z1metErkPEYLGvpw3t9rN+icfrR+f+kjPEBnkOuXMXRUEkjyE7h8gJvvV2PvoLbj9C/ivuWJ7SY+Kntnn5d3GvpTKyKtlQRHI4nIztdvs9f6Hz9lsvm3OYMvIcST0kiJ4VQtJVYY+ds865+1V/xe1HzN9ZUCeV6lj+bZuY/xZ3KddImHmOat3aBv/e7fbbfJ3Xx8v9fjphC3vQnKE0JIiCVZ6DNOo8Hi+PO//p73b7EfT9+6IgqWSxdjPTP+Wc5ppTkZM0UY32Hxzd7btut9tv/O+cdr/fH6dHcw3GIAYhlGkr70fhVWfbeXl9zev/42fffiR97/af7IwpSrL6om1m/mV7fRyottAVdkAR1/cf3vMf/Sd/6fB4+3YdqQY9GUGjSGapq8mdz6+dzx8/jf6j3/H2I+yb25/nJbKB9MWPajPzj9r99XHO47EeZzvn9NLW1rFOwppaX+wycbvdfvyf+q/+atqZc45G1nWUcapkKXdItUn5/OnjJ/zjP/xb3H4k/lleTtbOsBb/q03Nv5uPdrYjtIXa43Fohqjsb758XH/+X/OF16KzzVin0AatPM7msaFzGpud15/+4Dd8+JH6Vz20MLImbW4ezabLxXq9ztJFWndtVVZpUW+3XdfVTdc2ZZWv8jqfhPt77YM/+JXWSEDVStranrZdTqmomllJWnJRzank3BXLbbvdbnc5l7YQljd++f87LP89H+/qKs3Sui7L/b4YfjidOgmPYXPd0z/w7b+2mkqYuZVSVEvJWZO17bRtuzanNqVUzA3uJMzO/+K/ffPhiexa/fcrCYcOktADvfrY89/3Tz/xK186c3Fa3N0ANzNzL6ZeStk6/Zuf/Kd/8UXHr6sn8ifN66qW3vXCvmsOHj35tOec/KoXvOjFL3ruVx8+cN3VK+NKZl71v/4Phk31J/2e9P+T/t+1mln1J+ae9P+T/n/S/0/6/0n////+/7+P7i4XywfKNQ9/wvNvftXrv+zG6w83HS52tHwALZcPjMWeLFpbXsXygbebR3atnT+1XJ4/c/rCqcNTiz07e9DaYtEWrbXlsh3u6NTRmdOHR4vD1paPeOi11+/FY//nPeWVTl/4gd/7uGXb+dHRcrk8WC4PDxdHy2Vri8PF4fKgLZYHi4OjRVssD5fL04uDw+XB8vDM6aPTp48ODs+fPTq1uPbatuWjg+VysTw4dXp5eOrU4eLw4ODgsB20xWX2+Mz5c8vW2rK1durUuYfu2003Xv8ctzzXs99y84033XD99c/92JM2lf6AjjnqpdXqYh9j/qa9edhn7Jcu3XNputjHMO7or+VkqupDOL403/v4nT3mf6w0NWqsRmoevXfU8bnf9ejdnLpDqoqhUmOuqIFCTSWoc1UvBxQptZfqnzjcytFdYgFuBFWSMQwXb3nfb3/swZ4s2ruO5z6qR+mDO49aO9yjp148LEKqVtX19NenkmcTqoeQsge4d2/OfMHhDJnTe7mrv6dUTX3UyDzNT93R03/O0WvMlUDZ6Y7Ra54GevLXbtjBDWOee6rGmEdPZR4hVOaaa6QzUSSVqQ/G6LXKqJ6R6vVb23YdkBpzOmQeU1WlRs0ZRUq59D9fc3YfWvsVZXqqMsq5+lHb659kgZXes1qp9ZBrZpJvNYxRAOVISm/cl/bzdX9lcjCPUWNXf0lGqmKYp3l60k5u+Kx9jD6jCtQYos5qH4Pwk4/f2rVTn62qoqpGL8OAQeHmiJBOCi2KxNI5793SqBGsQKj0glCpKsI0Rq+h9/ypo3342hqjl1o1r2bbfvcqrFBdEs/O+OS2m0dWUtE1AXF8y958IrMWmcrorv5AzYkq9HHx4lN28diVRaULKCWqRUJRZDpZxc9+2ZYeU1qJKiSqGOJlUcB14kYUmfml21k4VBOQCgjg5lGlST/O+B07W7SvqVFRkxpj9P16ObtAUNQsh/6/bR59STNCTMUyEqfe2mIvlh8eo5KyLDOyoz9hL4xler80fekOXsJYaY1ehQqoERwFYs80n+g/385N8zyGqGwsIUElEFXKlLK+Jold3rydNk+jwHUSY4xlCRk95ai6eGni00c7au3r5pOUcUiNk36wV39o11DBUsl6Wq8xj3yvaxIwEEtl5dvbnn6MuSuCSWWxi4P22+0xJWGeTvrN23uMFWoeYoqgcZ2yHGVSVatpTKunbuVLppPqKCpQQRVUFNxIFa5TrpMu795S7yMqCoIKkKiOUJpMdelSv/SwXX1NHyQBcTVPZ/dqYTHSkY379dS/nkfsaxlRVEM8zi17Y0cAISNtt7/L2cvSu4/b2vlhqYSAErGgoIyKJqki9x5t5cZOsQmiQhCNoooRVayoSIY1um/cUhVGiSZRiENBCxFLJVpP2dE3MokbazWvFvv0+ABRFFF7rfH6WeST7KooSBDN7CP25IMO1aQg1I5+j1NgQ6rnyVv7fM0RVFAKkARKGKVGGcaPt60+c8QoRiQqURElrKkoKRQVqfTJt2wtGkVRAUtKVEEVVPB4R29JT1ASMqa2z58i2WhtSCoHP2AWeQA2EkVMMCf8+3a4Fx93VsQAZke/g1kFdaSPx23r6xzlRqIxVThqUJQQVHuF2T+/nWeQKJrSpBIVFSLIWpCAECKWZPKbDrbTU0pEjDFzmQSMEhU3d//jbr6xD5MAVo2TfTqjolGjMfake98UsmsvbpUgugEDjExtPz/qHBTQSg5289udVEHN6I/d1hczBmpAJSY15ilj7swWSTDFmL15O093GAOK4mVRUQ2oGBUkiiEZfl3bUhklEskYNaaaqyopRFxnxPULO3kDA1DFPi7tx3LDnxWlQDGiYuELzCCt/bX4iBjVoA5fvx8fsSuWao+L3fxeO6jRpI9tfbNJLMEKZcVoQlWNPsCgwzC4ZjvPt3dq9F690sfoGUUJoDHRpM/zGFMf0zxPY/Sq1ZiGb9mSRIWoWMWIQew1CjciBhnfvZM3MUq0tHo/XuzF5ksV1ahRSxMpfmMKucAGNm3EDFb+wn58MF0S1pLRdvsHnMSopsbWPp8hcWOkopnv+Kkf/8kvXlRHp6qMEtO2+xKl1HjFcSOoQimqxI1BxV+zpWwQJfrpH//sz/zsJz5/+x33R0eKywokfXW4i7dmFlB0zCeH+/MiCcTjJVBoVk9mkI+w1GhUEg2F6cMb9uJH7SIijrCTZfuDTHEjjrk/bjs3ZGhGKSJz/P7nn2obTz3iFf/y1mO1MyrpXtzSM2/59I//+I//+Cc/+IEP/siHP/zhT33ogx/4wMe+UMUGRPJz73//B77/e77nu37wfd/1/vd923d81wd+9GM/97Gf+eyLtyRJWNMxvqRd/txjf81dooJEpbKqr2mL7b3FGVGQ0VfL/flpAm5JgcaEcvXdZ5C76oAhgFYlqli18p/tC1oECH0nrf1Rj41Zqz7lKdt5jwMT1zSZn99aa8u1zU/5t7NWp8qPbqkdLtoWX2eVIWJCflvb8rnFdgIlrKX3s60t2qItWlu21n4nYFAEk1X9j7bDt3tiXK+M6eRwb64x0UStnoAka0LqngnkpVzXVElMXN3dR4FF2dPb0e4OfoxJUaWq5sVu/pCTgiaZ5/GY7fwLu0YgUI7ntW2+6fPWdHKf/2Vb272OipePb9vWthmoazDVTe0qv5yhihtc1b2LHbyBWQ1qTXM/2ps/5ChApeJZFhFRy8fMHz9nxeN0/9avcCRiQP36tvvDH7W7DpCMHf1hT8B1eu/9ydt5v6VoIg5O2pYf+Tfnfpy9eihBlE1v3S8H4Hqc8viraf/O2hBRxrw6u4M32Ykb6cmZvTnJUNzIP/8oa6kbUr85fexKFCuJ+oSbHCMlYpU/sweLj2RGBQJJ2+0fyhwVcYyaH7+dz9tRjSJ+vi2309oTfwT/dTu1Pw9hJKqYlG/fL4LrQY99zFXd6ECjRF2N/ogdvDlBAJ17zUf78izLNRB826ev+65RAA+72eMtXQsKI5VLbXFHZuKIkOH1uzv8mLPrqZjMR7v5I86GqNDn6Ynb+YxDLhfvbTt8w8+/oe3xQ6nAA8UBSlRW48arWLTFPUatoDomH7ODtzsIrtNrtTcfcUQVt8/T/o/0cmP0DVvbTR23WSrG9T/f2t+0W1ACs397d+1jqTUIjtRyN3/QrmC097lv6TZLMCLE48dvWGylPfxgnx7iwCCI3XfvWQpVAsf1qKtorf24KKJiX+UpO3ibA0WUMaZTe3LGoVEw4YHWvsZFla2Hf2tz5832lRRBgIe29kilStQx23e3+GiCqEaqH+xi0f4YM6IGxzSevJ1POiOuA/SfXaz9IngdAXDj5Dv3iypRJay46eo+mIgb4xj9qbtIByFrNR/tya+REChJ8XutPfdSXdziWX/83PE5vRIRVG5prbXbLaoqaJ991c6WP0YJVIReYyet/WlPjIhkrOanbeff2alAlNKpf+eFXxyuIXEzDt+9d4gaWNWjr+4nmS3W0Pl4eugO3sJMRUVHzYd7cr8lFCaEV2ut/U2t5IieLb8yd1ysQwKW2H1zW7b2OkdGaWLKT+/s8MMZKIDiWO5qRQCVeerP2c7vtRfBgAqXTu7/owdbWrbFPl2gQHHzW/drVI+ghtknXt1tFIjrmad7Fjt4t7NJlNin6fR+PMYRgwmah09aa2/hWdJFYd2fTR3PNSBGGLMHrS1aO+4TUcWhT9vV8uOsiWLKtts/5qwaseY5j9vO19tLFUXUxPE9T1xbLK5iz69Jobhx+Ob9qqFRy7J8amuLK/sqA4Xr5Yp/07a+aG91Qi0wU++L/fhPPY4qR2rln2zr9/fgOjD5ax6csdjwMY0b48yPto3/3a6IaPyWtmjLXRx90OE66Bh9R3/cLm4cNeep2zl/bMTLR0fQO/7O9e2BfYOXJWtv2S+ChUqYfXo7assr6lYKw1oNX7O91t6d2RLFVOb9+NFFwcqoXL/hXzlU1sbw4oMzNp5SAhF7Jp+56QlmzVSw09pB2+XBx5hhrUKxqz/JjJLIqJ4nb6f9GF0DoBiookb0rt/58AfStQmgqJRv3zOjRtRpPLYdHB0t1hZrt5uyVMFYve3yrTWQijrGOGl7+ZdqmZFk+COttXaqXefGmFQNn/Lgjd+mqCI15ouLTe0uo1gqM7+q7fbwIwxFDY5kuZs/bwcFNdN46laW7WmOISqiVikmfZ70lt96/oEDhRtj9137ZdygOM2PbIt2hc+fjQAGLPVf7oahEsUxpv344XNKIKOP57VFW//5tajG7nc+eOOeTUR751+0jcv2l+xoMDiPe9tiJ+2D6aKxNrTd/jlHRJVRo2+ntfY9DgxkgyVocFRXb/u91z0wLlgRQXX4zn1DDAZHv/nUNeevu+bg1NmHveAPf1yHIUqiEM7v5B0MVJHR55ODffiZxjbAyP3t4GDDy4Rg1Bq9Tj1Y42aHYBSn4ePWFq21x9qLEYkEn9Z2evDBDIGoVO3qL2UOqmDm/qRtne+WqBgTE5UMTZ8vdfzplz4QroGERCXDX75nRFEM5cnqZJz0eU5pRhKARILDv9t2+t6aNwQdfdqL/46jtUaq+69ba4u2aK1FABUTf9uDNT7sZEUl9tUX2hXe4gqDhfPF/kO7WfxICpWIfWd/LicgG8Y8nryt9mixIiYkbgyUFKv55Fjv+F37d66CUKju3xiCGNFpNfo8z5em4zHmCgoQTeL9y10s2js8MW7u8+pwH36ohyNLMrypbV60b6FENGTK3W0xZZx2VBJQsvIPX8k7nJAo0i/2w3awg4MPU2qJYWTe0V9xRSgkjqmesrX2ciVxnYhKah6MjDGfTLXCu5+1b2cMKoLgW/crFWME7WNe9TFXP5kqNTBGGErUr2i7/eWeEKLBuU/78Hu4VCWrsWpX+PykolAyho9rU+YfdlCJhlj94Eoac1WImHnyz7edfsIZw8akdvS7nRVUx2qVm7bXbtbqxio0VEUFAStY6N9ctOU+XdikouWb9iyIMSpqESIiQCSaafSsnt92/DZ6UMSsxmh7+FWVKzX5m6+k3VYdsBCG739wxl2mIGqg3teu+MMrS0UKct9OFh91mEhiKn1Hf9CZiGL6tJN27h6du1ViEAUiIaikyk+2ttyja/UKmH3zftUYuI4SkKBGghgNq37iyavbrt+emUIC9DGWu/v57p2V9MTDK/odriHEhIfMGI91VNQhMOrZV/YiCg1h6OzzdtE+ygSIBezsD9shIo4x12N20dovL2vMjkpF1ywRNyYZfqzt83krokEdvnG/EhSQqEXAGGPcmKTrbY9sO3/z3FGJ1uir3by5/MN7SFPM/GS74gupUa5XCv/yjPHtzhgNGi+2q7xkqVZ6OepHdvJx+5oRrF39OSc1qOlzv3E3bflXZq0amkgQFZGoBd3v3KcLVKEazewv2a8qxQgaUhGRCIoijvz3o9aWu3prdYiojn7pcCdPH+fQgOFXt9aWl2sfoyeCKUPNGBOjsCqhwr++mn+cQsAaFPM1u/goXTGpOJId/WV7VMExer9pR621X32nWrUGKBBRoUq7v3qPTluIRqX75v0SFCMhOGJMIioS1eN3tX18V81BFKv68XJnf65XwZj61K7yZmsEARzxGfPFe+yKoQzlo6/mYakQQhni39jFRxgGYpGqHOxi0f6GBSiaMfdH72Zx1Jat3fCPjlVMQNYFEnWM6l7Yn7MGEzd237JfpMSoMdBrDCtUEqJiyv95ah/eWytjRKi+OtzZL3l9ObGV7g9cTbtkxSiU5Z/NF591tkyFkZ5725UvWvuiQxAjfRzv4qMOEyspMsbRLlr7185DYyn9ZH7kbq7wCX/9PkzFJGSUEUl6Medb9+eMKBoNk9+0Z4MUIsFKAEZVgZUyEsP/2Id3ZwWyNvrqZGc/08vb7TBMvvCq/ogjJHFYxOtmi0c7VVEYAH/DVbTWXm2PpnDQu0/bwQcdKJZIxrW7+X4noBCYVnty0FprT//Dd1SSCAkoCGWfONib01ZUTGJ8035VjSSgmrGa7rvjzrvvvnuqQKGFhuHL9+DtHANR6fN0cmZX/4fHS0tn2binXfVDCBQJxuGnzRafUoZBSMyNX/Lk57zo5he+5BVPe9ozn/3s5z79Ya+6aCEopPhUW2ztp+glKcHEm3ZyZlSpYiTTvNiLy9/4np/vps9SYlQhw2/emwuCG4H4S/ZrjIgSKtN4dFscHbTDU+0/WBVF1KS80Ja7WbR3ZUIpNWPMbddv95hMlf/mYU999pe//LXPfc6XP//5L3rZK57xpKf9gsaNaL84W1igIonpt65Smfuqd7XmS3drkJRGqjhqW/+YVaqJOPKVO3mBxZoae93d9v2Gv32f3RJQQ3TkO/fmGr2MUL5pvxyIuD6tbmiX/6JjgGhhlT/cdrxo72KOcWPV8cGO/gD35LrSir3q5KQPMvU5M6QwsLbyenPFa5MIGGOqJHMfNSqZMo+uJIiKWPzB7X2bpYqhiP9xJ39P1AhSI5/Zu9YO/1RZJIqWWH5+j7IBMd037xluBDyuh7W2bMu1p81zaUhiMH7Fjlp7W5WASKqmUzv6gXeUyoykV9WYxhgjCVY0isLZevdmN018UUUVUtEQyyTKyAgJCEGi0Lf3t5w2KcC0k/sNakAp3r+tg7bYXmvXTSSoBDUcL/aHWlPDvi2MohiZxqPa+qK1RfvLgVKM2ifuPdjVO+gxqjjGydFufoYt4iiQniKJocgYhhA1Kuvi87VpctkeZalGFdCYQlFKU4AxqAQLn7W1r3EOMUYTeMoOnmdpQNFprj+yrV2/0bgOYuF07b6clwJFtPuWvVo6orLmVF/SFpc7HBXcmLJm/9xuFu2dGShGa4yTg938XR5ZW4mUICZBQNQSRdH9qd8zT7T23xyWqBAZVEAFVCxiAEQ0Vv/I1m5wlATRVMZHd/DTFgKsZdRztvVrf+vRTs7drkE2UKmH7ss1Um4wDt+0V4cCstGTeny70ncKqRJxMIbX7mTZ3l0zCEbGWO3oV+3urEPzsDmiEohRC9xceDZTzKmoSCI4MGpFBSEUMZEYSFb93LbaqkoxRked5LltuaU3SCKqgd5PDrezbLflc8/YRfsWi+hAsVIX9uUCRkSC5dfv1YGjiojGqT+mLTYtWmu3Jm6c06d0f2gnrb2L45QBpM/T4U5+j3NeHe3AGoisgRXVAJUSARPfdZ74tc4WIloxRhIUEBWqkkgQEsdxft/WftguSlRYjbtbW27l6GR0CLFUT/otbUuH961mf+S6HfzHAqJWImN1dm8kKmosv2avmlSkADP1J11u/WEjQYwwJ7PP3cWivYMT4kamvjpoyx38q6+vnROPDpZES4kkMFIDHJpCUzldb50n7rTrmlFlTaxoQiqVXlqKGoQ+n7S23M7rnYIoGlL+RGuLLTxBQcWIw5W/akvtXMYw+VdnW2sH2zh/RyooolbuW+xPBVSR+Jb9IrgeihU3tiv/DudQFcQAdx+15dZaexNDg2LNfSzaLsmcKFMwgUIgY2SMDGoELYOke9Ms8QinWG7GkApVEayqGoyqMeImFTL5zLbls70DBhVT8e5r2tW/NERFq9Q4c7it55pKj/O/ekzb6quREi2Iye1tX6+XuB5N+aY9AwEUT8Zjr+J0daNRxJS/bydvzjAoQk8/3MUf0IHspHNOalQyMqqKjIyRABgU1g5+6QyxbK39AwPCWgQd1DyPCvbeR69R0zTPUcsAOq3m922rfSulRFAl6t8/2rC4zBM+qaUxBgNYf7Vt+88YA/Mwv/A7H351L9eYNYax/IG9uUBqDVl7434JFlHwJDdeRfvzdkGICCuvbYfb+6bqgIhVNR3s4qskdh7n9HjU57mPXunTPKpG5nk1B1SBsjS5OEMctNa6gleIRlLxyueahyqiqMX5bT0mozAaxZJovf9l59rmG375z2lFVCFGo2e29iGHampeqbd/x2940unD1tqytXbTb71FBkFFkfK9e3MtNdaEEN+0X4miUZzqMVfT7nB2nQKd65Nth29KBTFqr5Nd/EyyizrOyzFxnaqojrlGjJbrqKy+/QTRWvtah+uIDj9245Of/5Rn3/ySV776ta/+6te86mu/9vWv++qveu3NN3/p0578F8TLjiJ/blvtI1VGQR2qidpv/dB/+xv/8ZaVWoUGVOPGf9W2/kXRcpI5q6Gak5/51If/07d+/BY0JRETwREv7M1Zh4pRHfsmGnH9hIdf1ZebmIDr6X5VW2ztDcylGqT6Tv4nDok4/tjf5nd+6nOf//wXvfTFL33uzS964Qte9KKbX/DlL3z+S17x9F8vQrA04X/miJ8CZS1QPqPt8HAqUdFiymprNxhLMDpACSfH81DF0eMQ10s0lmlbf2RFq7DQWJf6PKqGSlJzhusDQMo72t5eZwUim966ZxYiGlY86qraj40ZARTIuGfZ2mJLbx1TMErMmJY7eO2uNKfHvnD7JO80aIyrlE+eIR5vJQY1Vo5bW25aLlpri8XBsrVFWy4P20H7DlmT2HPi49piO+2vOAZqoFcwVNWYq4956jUkFioYlfi123ueAwflUBOm3k8y99V88fgSIwUWwxDj8Pn7cw1rluvlm/eLMULEVFZ55NUs2hlqVOJGxqr/pbb1NzuRNeOYpqPt/ZHOmWunF7//7f2PtWiL1tpisWjL1tpbjEZYxPIHZ4h/1FdDDVHwr7edPnMklJoao+b3b619IRFUStGQbjdVhlQpgipVlP+lbf+9djQMDKVjrgEjYxrDoY4MINKNd7T9vcFCxUpSfuN+mQFFqXYfdjVt2X6Pc0woJbWa6szW3ukKjDCY576DX9zpsYvur483tzcf62rPnYzSlLXqsu5niDB6UjFJ6cN3046tCCIE2/YvjiT2tSplREEERYw4iDXG8fhc2+E3WqN6jOsYTawgRkhKSKaMTP26PTq0YiRADd+wX1YiSBJ0TuOmQSKy3RaMYsroj26pkTdFCgSDZJRizcxe7TySpCQ1jf/WdvsTtCBNUcqvfvDDV5tUJAjlz7bW2mIHf9cOBEvFX7u95YkjYFl9aLBYAzdiVHGM7hfbLj8wElCTTQiqYCEmCaaS7je1PT5ngiiS7lv3KwwMBD08ujKT59GMm6vovn47lbyHGhHBIENtDj/RZyFoZXQft6NDDA8HKWH46Qc/fNpCTdR0f/naLq9NryIRS/zc9trZldM8D5NBNKQMIIpaxvXj2Z9vO/0F55JuKcN13IwoxUCV1eTva/t81lFrwaT7tv2iBYNORnBabpyF/J6FBJGi4m3bEXkzFQF6BEvOZTyrh9bQGGJyadzfdr1OMwOEQcyj2sGDGx7qGKUSY4aHu2p3jIEYCeJTttfaj9hrpQUqKop4hSSAf63t9rpvNRkoBkUJbChUy/U6qfqVbc8yVIhh9l17VdEBBhGM6PTgTPbTUAoyRoa/YXsRjCACptPFWf01YolopftX2uGO/gqVDCrROP52e5Djn3BEcSDOfr7tdtHab3YuDDi0/Ge7aF99v46AUkZirgSTjPK+L2s7f8g/VCuDaBCQiJsBTeGnH9n2+8ARiQScfc++eRiBQDDr9TOR77VKjQXWKC5so5K3EwiCEXR4Hs9ocQeJUUzZ69q262tIh2O5fnzPgx3ud0BBpYrJ372j1to1VYNKikivk4MdLFr7u1qjUkTiBgWjUqq/+agd7GixaO38Hz7RyqgRgoiWRmOEgfUHlm3fHZVACQ7fuVdCMwcDEWDyG2ZRSTOPURF7Qnr3fduo5YMwA4PwgLouzOjZVo8VIIN+R9v1SB4LdRAYVTmeX/vghjf3PuaqSs+oGl7YXfvpmhk16DWc8Xk7aMvWzvyB0kGqCkgiiknG0Pt/e9vfp38KrR4qxBpWQYjzQC/9pjNt/9PjqFG9itnfuGeqxdQ8zMxwcBYi8i570UdqqlEZ8ZlbEPmrVDNHGBCaysqM3ueYe81zRs1F/eqdiTxMU5tHBjUyXfrxdvBghjumvppTNY3qKT/ddr1o7b1zr/RVjSocfqotttfasrXT33BrH2YgATQFOsbxtz+xtbZY7GzRWlu21trh6358SGVU1JIEiXX/H76hPSAd6hhjJBn+ib2q3N18J+FJjw2o9mjHqyRjqmlUpffcsZWvQ2seBkR46abXSzOL5R01Ru+jqkjV3HY+EmndutSoQE3Hq2e2BzEeveoFL37+lz3ry5735c9/4fNe8eqvv3FnrbXTz33+U5/znOd+xUte8PwXvuxVr/vNF9oeXv/iP/Hdt913//2XetVquvvuWz70t951rj0gr/vqP/NDP3PrPffPnbE6vnjHrR/8E19+rj1AD775q1928ytf8aIXvPRlr3z5O97+6L2Sr37Vi5/77Be98IXPe8mDr3j1m68a0PNxL3/Jlz3vxS954QteePMLXv1V3/DWN1yzjUPvfP3Tn/Gs++979nPuf8HzX/PqSmb66Je+7CUvf8nzXvLyl7zoBa96xcuesDuR+o7Xve6RV7zkxS9+0Ytf/LJXvfqtT3www/+2Hp298LhH3/ikh59dtgf6qese94QnPvYpjzh/1P5v1Mv2i/Xif5vq/xoWD/pri03LX3T+f0JW/9tlN5086f8n/f+k/5/0/5P+f9L//+fJ6k9gVP91VVL9j8Zl6NUlU10ydb9aRKS6xOoBtYhUs6jrur60mlqqalbVpVZdCk11SVWX//w3tdrRuxKRWhr5r7mS2VfyX2c1izmOhlU7Lteta5k049FkcXFhSZp6PJ7UTd00k+WlpUUZNZOFpdF4Ydxrad/KaGl5+Yrl5ZXx8uLy8sryynh5afmK5cUVaSb96rqRZjxumno8Gi2M6mpmKzKqJ4sLC4uyMFlcWlpYWFjet3LFyvLSaHFlZXl5siCLC0uLK0vjPjfsv2L/ykpTLY0Gjce1yGgyGk0WRk01Hi8sLC0ujCfjpX1L9ajf0riqRCqZVAP2718YN814cbK4OFmsmqoZjaq6Go1Hi8uLk3o0Ho3HzVK/lcXRuB4v1EuTYZMlGY3HC4uT0cLS4uK+leWlcTNe2Lc0GY/qZjJgcaVaWh4tyKgejZu6kXpm+69aWBotL44WFheXlhfHo8WlffuWliaT5cXF5cXF5fF4PFpanDSXUVSy9Lm102c3Vs+snj597tzpxx974sypx1afeOLx06efOHVudfXM6dWzZ0+ff89eldy2sXXx/Obm5sXz57c31jfWNjc2NjfOrW2sra+tnd1Ym/T6wc31s5sbmxtrmxvrG+vr6xsXNs9++Ve/46FrBv3U+Y3Vs2dPnTpz9tSZc+dOr65tnN88f3Fz8/yZ1bNrZ0+dOrO+tnZ+e3vzS5O9rvzDbvPUY2e/9Pj6W6XqN/6Ndu3UE6dPn15dPX1q9Ykzq2vrZ89unN88f2F7a+NLvcZP5M2tx06f20h/tNCjruSb84Uzf3zm9BOrq6dOn3vi1JcfP/OlrzyxunrmzLmz5zZXz3353NlzF39gYa9a5PGt7c1zq5ur3R80Q449tra2vnH+/Mbaxtra+vrG2tr62XNr59ZOr547v3nhsav7fX/O2xfXV9fX186trq6uXTi/uXbmtz//tbcPGv3yubWtjdXN1bPr6xvn1i5srq9tbq6dW19bP3f23Jmza2fOPHHmzJnTZ079yv2XS4hMfqdtO+1KKdlS2u5SSdpqV9SLl9yl4ubWHthL5B7tOu1y1lZL6UrKXelKm7vS5jzdShOp9qrOWs5d7kqxrMWL5txldaf//cV+4ycsl2xdTqUr2VJOuctJu5JSVzpttevanEqhX7VHdR0jstn25tbbZODimmaFZs2atFguxXJOaZo6zZZ7SUZbvJ12Flf0aEQ+iqxeUs7alZKm3bR0pdOuZM0l59TlcH6X9E45F09th7Q85C60lkvWoiV3OWvSLnc5paxlen7LDze9fp1ZS6gVVSS1kkpxI7uNb72+n3ReQrWUtqin0mlKxUsuJaekWXNqu05LKVsbT7t8Qn59uj3N065NOeU0zdOu7do8TW2Xu2mZdtOsWf8v6fssn14sKSfVomkrpdSlrkxzKjml0m030vTYTKXrcsld6lLJJbfddDqdtkm1++6qT71eUpdSziW1qeu60uYuT3PJuW1zmzTl3HXT7Fr273UD89Q6y9Ppm2Tcb+UxnXYpt22bcupyl7tSUtI2t6WUad0r5bZNeXuqeV8PkfqHPWXN26ntupzaadd2Xdd209SmlLrUtlP11aZfW7rUTacX7Hw95GSe5i51OaeUupxKTilNU5dT13UXtuxAPe7zc5wWLVpSSTnnlNvUpi6nbivrj/Zq1plLSl3pNJecU+pyqzl1qUtt1rxLLqnTx45KdblE8ylXN2cQpDo8AgBJOGCu8MRfl963aslBOhnwgLkjEPRAUM2kZyWbJCMiEKABDgsGAubB04s9RmcUBGDuRrqDIIFgWEDD3JVUC27t20MOQi3I6TTeKQObbSvhHoSHwsEIhJcgLPhHsnclE4MRZupc6fe9YQ6LQCDcyTCnB+kRdJqa2VOk/7YVAKGIQc9kDjIYQfOABwAShEdqkY9X0vfTTO4I0oNmoJMMeiCc7bU9VtbphhzmIIJOIgAEDQE4QAYCyHr35RPyy+hKuCMYNFNYgKQxaOG0SOSV/Y5qMY8AGDBwp4cjyAC0l8gFepABggaFBxkkEXRne41ItYs84bBARLgjSDIAMkAEAIKgISLOr+x1fbiRtCneN2TcqjnhiOTucARJd4tw8PEeIhMHyDArHPVqftCKGtwDJGkaTjgZIEE3D35Y+letqzNoRhn6DGZEkHTCPTzc4EYnYerl5mbc5yPMFgCgtHDQg2QE3a2QN+911TlVI03NPcLAIEkQ4chRPIBgILQ7VtWXS1R/ADOFu7nCXa2oGuARAInwwrdJ/yNaCmgBhKmbqauquRngaux3PgAEAXcrWVPxCCCCQYCrC7LnKTcrZp5hbl5IhAUCEeHubqZQmPH8wl43hDnJ3OGDQxZad4bTXTXnokXVUUoUD/cv96hkwggCAeOkl/woUoGaqblbmDoVHjtJhhl/RwahOBhWht0dhWQE6OZq6ihm5uquyYodkN6f2hEBupVpKlYcoDvDQWNa2WNyjkUJU1PNqua7RhhLLkmTw93MrXS3S3NZRF1X8vPamappTsVSsZKtOIPBcDJC+ZgMPKxZg3QyoMVSKsWseDHdGWORqo+DwSAdJbmXouYIRMBg8Xf2Wi85dzmXopqLqjF20qNYzsW0lIKSkncrPUwtGGUb7xoySW5BRjA8Fy1erFgpqsmKr+9VjWQhAAahOqD5Ed125uQlF9VULGVTZxBghMJ5m1T9ZFsNpJsOu3+HeyBQcsk5F7XsWbtiJWe7td8nmCIQhgiUkiKimIWTdA/jL+9RrWtbUnYtJWsxA0hGEOaldJ2V4jnnYrZ9UqrLJOTqcyQJkoyAc1eAEQiau/P2fpUct84cwUAuZBDsHVyuR1LtseFBECAvWlFDEKSDBAlo3muVewZIBui0oINUJcliMO68dq/rzJ3B1OKdQxZaLw6nM7wouGdwZ+xViyyQRmOYDRh/nmBPMALcCdIjLMX/J4NbSwC9lBj0dCYHww3gcPc43O/jzDDCCetSztPipAULSZgCh3dbOeVksGfQGQ6SDgMA7jk9fJmESDX6s3/nA+94+FUPPPTAS5/7gpc//OirH33NC5998FsiEE5z5adl6NHSugO0+JUXPvelL335y7/mhS952UOPPPzAK170kle+/X3SexVGMsiN26+84cYDB+9+5f/1cx1p7nQCfMsulXztu9/zhne9+a2Pvv41r3vje97ypx6wQJAB/uaLHnnk0YceeOXLXvk1r3nota999Xiva9SVwdL6u4ZMMtQCrvzssXue8bwXvOyFL3r581/2zFc+9OhDj77mDXuJyEKEkqA56x51Iw/9y6//0FseefjRRx95+KUvfskrHnjFS5/79BecB4IEEtdkcDP1DiTNOcxLeASdH3vWQ4+89pGHX/7KB172yoceeOD5L3/41V/3tU2/H0XyQHhsX3v1TVfffOj401/7HzMMAYab2z/bTR746+957Z963eu/5pFXverBh1/8kpdbOOB0/Ppznvn8lzz08ocfffUjr/6ahz/wzkW5fHIkM32MgEVo5trioBNtLgwn+a2NzLUSORtAEIgz0vPa/8QwJZRd/PYuIpUMXCBIEsBHZOY3FAMjSpvfMWQhWQHckv87mfNCwIJwc0r/SmZ5QB2AeSgOD5OuZGN4tmHPZEeAYfyrMv8fQQoQyR+Xntdt0J1BC2x/ZY/hSS2c0dq3y+Wbk3E9g38Q4UAAhQ/J4OOWi5sD/C3pX9Ui47qRag8ROR8WIOGbCz1EvhTZnBam23uISL1Lvct+whkk4+f6Vb2eYmqEe+vDplbU3DK/u9qjmtEEDICuGNJMxpMFEamkEqkqkVqu2IQ5SYDfJDPcNgU9isegZ/sUhDPin+yoeo0WmyEf9dbgnnBWpNlDrtQAnQHr2v27jaWqqqZH7XDC0foPSFX1aSaXUwxsdjnoJBmMDfv3Mvw2L8lJK/z8gJluMhiMwPlJr2fQGPTw4L4eAztGBDz4C/3632wKkqXFu4ZMOiuIrMm+WeZcu7mDYe6jfjOs5OcDdKAo1mWG421XBKHKZsjTogvSI/Prdsz5sywRgWk+Lz0r+VYECBKdH91t8CLgDMe0/Ge5TLSqdjzOCHqA3XmZ4RFTDYclfuQSiAiQHhcWeq3kCEcAjhtm1ZJEhPNnZ3dI3Uh6h/cNWShmpHnn/2lelcHIAIzVfCp5Iclwhhvvn0mrGYhwpQy9HyWIQOHfuAQ+Qo0Iqm72aeQ+WhABJn/WjJZhHgCTftPlIrs+SgCEw/yOmRQtQVjHn5zfGjzgBC40vWQtQBLhuH1WWwEwHPG52d2s2UmW1j84qDMw1Fr8+3k1iAiSaqznUYnIBtXDacrPyCwXkxWAMOVoyF3IwSAKv+ES+AlmkOzSRp9KrqciiOA0HpzRosGCjKl/5+UkS3QPBGH8CZnlUU0pCE/8wfltIOBBcLpHtWN0OiIAhMULZjUND2eAPz27W1QRpLbx3iHjZEbCW/vP8xqZg2QUd5lrLf+FThJqGkszqGQydUMwVCFD7/YcgQjjN14CPxgZDOZ8sY/IlXQEGEzxmhlNHMoAW/+uy0l+jqkEDMpUzeQO6xLonvnj81uziKAjthZ223Vl6vAAXfm0mVmAEcafnd2hkj3InH2YuoMFbfr386rCDQhmcC6V3MqwsIA63yczXcqWPQgzH3QvEggi8esvBSqAaPNmv5sNjiC4xWfPaBSwALiFb7mM5BUMOOEWvENmety6EjDP8WPzW3UPEo5upUctR6geHoTZoVltOQKMgp+Z3VPVnKBmfd+QxeJqUXzq/3pu0OyMMJ+PyO/CHeFwrslsl1vPiHA3Dqjk3tJFODzzL10CPxzKAFo93+897iAATOO2GS06nAFs4zsuI0lezAN0fkZme5eXHG5W+JH5nQKIcGO33EPkO2lwRqipzPqCB4IB/tzsDpghQO3ye4csqBeE6zT+zqBqSA1VI90xp0fpBkTAedeMxqkUjzCNISL3escAUPgXLoEfi0IQ09ynEvkjBxzh2O6umNEC3AnEZSX/hcUDhgiOZnQHcgbMjF8UkbppmlFdiVRVU0s95AyMQUakfX1OMrJb7PzMzJIjnAR+cXaHXJ0Ia+0DQxaTa7h5F9/cTJoddV1LJVKP6gGVqjoQKVjNJXkKDbjx+2TGk9ayEyg+7D6bws3c+U9EpBpNJvWOuq6kGvajyBHwpBs9RP4d3cNJqv6czHgMGAnv7LsuE6nlgIdRzbXjG2XG91jJJIngFgPq7sXCws2nLx2y5iCcjM2r9lr8GyBCQSs5bp9V1RVJCT+4vZvpIJk6f8+QhRxKBOHTL506u762sX7x3PpGu/b44+f/Rq9aRuYEqUVjPI9/TIMRWdOGzHo0NXWnl2L1kOf5lAy4BwwRHggyXE3z9OWDPsnsASjOilTNbj/OXQ0R+fZZXb+yGry4fNskIvKbtAjAjadl1ve6AiB20tXCHeGuBo+XS9Vvk46IMGwdvu6pd5x45vP+9KemNAdcPbL9ocx8GwsYu3iquwapyT8wZNncwHD3iAAJxK7e+b9cqHtINQacEa4KmePhcDeCavGMmU06V4a7FcrQ52tCeAQAAg73AN3N1PmGQT/JEkGW2D64tLS075obX/zvMwEGA/D4A5n1tUsvKffrd8wi76Y53cOUR2d2v2lhRCAcgKvBNRwOmD5PBm4gAATBtqRCBkkgEBrhhTfNbioRRr5zB3Qnmdvy4SFLGsZwR7hrMXMv7uaWu/K144UelSwSTg8Um8vvE0TQM35aqlktJHc41DIGPV27YOwOhAMGONygNuzjUYIMkjot0yl3hgGMYBiPzq5n7ZHTmkUWE51gmPHbRaoZ3WNFg2GIiCA9IhikBhzPHbLlAUcEwNRlKx6uFgyqe+G/ldm3YmH4ru09BY4gU2sfGjJWd9KD8LBAwCwQ8NjOf2O56SEyYZBBJLVmdu+nIYIRGisiUs2oMw8wVMugZ1smgQgHAZBkBBVhxlcN+ig7DwYYGpoBtZzhO4yJn5OZXzjkkMTT+va2m0L+HR1kMBeTWY/kbk3FgwQiNIxA0IMID750yEUPgCCLmWZTWAARpGuxL8scU6Gm877tHVDAwdTqe4Y0BQ56uMM9nAFYkIyif2tZei/QNTw8qdczqmVEC9dgYbxbZr9SvACBbDroOeiCIJ1EwMPJYEQQgVfOoAAgGQVqauoIgAC08A9l9ruiIzzUv6VNoQv0EgBofKlUMxK5z9pSPAB4OAJwhBkMcL5iUABBIsINCAPgEUSkwq+M5tFWCXS+d3tPgXs4S2vvHzK2UKfTI9wQcJg7UXJnX78w6jUOFA9GAWXmv0w6Pdz4mEg1s+XWkge8mA366pLMEBGgIwIRgQDc1PxBqQf8JBVEGGChaiA9GEF48CujOVxYq4fKg/nmOeRnUNzCw/kpmeN9yAkORtBNzeHwMAMcfLRXJXKRYBAkzACLnSDCM/+LzL4S2TKQMfI927upuAOR2/yhIROlEuEBgoQp3OHUaWv/ZSK9F6gWdMvOelYvo8EtQOJGmeNyzupESe6Dnh8tgaAjAg54IIiAwfGoDP14FALBMIa6RgBEmIL8kUbms9CTi/3b2skE8k6GuZLmkHneg5JhEWRYUS1mmjSZmqP8+V4iMoXRyUC4a7gDRnN3j1fJfHMQqfG+7R1Qc4Zra+8e0hSYAxaBom1RVcAT1HL7/69UvZowN3dk58KsGMUDO14s85x0qqBGdgx6ibdAOAFogrmbukEDWvxNgz4VCXAj4E7zUHiEK8mvlrnuuj2VfrG+ve1mj1pGYJBQNb5mPqHFI+D8xboaVSJSSz2q63ppebkasmUEIxg+7bZKlELSw8L53Pk00wpi+b3bO+bFPZhbvHHIeGoOksrfmFx39TVXL6+sLO/fv7zvimsP7ZO+tYzNgCDcWc/o8zT3sJL8KzLfVs0CbkA15DnWOsOj8O8341FTVU3TjEajuhnVjQxjiSAsyjRpLsUdDprxl2XOsBJ4ePmmNoH+DIMwmPI3Za530iwQ3vGLMveL4SAJsoQ6QToQ4QG/ei5ysUZVKL99e091LSSt47sHZVWQSPxZmXMDgPDQQpntfVSjAZq5bz7N1EtEwC1k6DM1ebib8XUy9+rHogRJFi+mEaYI0qIUfsN8drDGePHwtZNHJSL3EXSHFedkPvdCDRE+5RcuiaARxvNlY+3UBmkBd/eCr8xnO1Ck8i3be4qpRUTpynuHTDp4hIbz0/Ma00FEFJ/VOjw8hRf+LZnvuHOFM4pGNeTpJXvQXfmX5ic/yewMmHLrj37mp39RWYoGULLzGmnm0CqHCBdrBlEGgxHg35H53oliEUB3KWyRDg/A9smo2de8+PfoYYhQ8PXzKRIY/q/t3eDZQVrydwypszsZyPzk3NQiGFGM9Uz+fxhh7sFVmdcFdUegmNVDnpk7D8Ml8lFmINjqOdn1AWoxD6PqKZlrZS304uGLJw8R+W4i6ECJCzLXSu73lD2AjEvBEeFAuOy+ouEBD8Db/XMipPi2HVjxIHOytw4ZF1eno/Cj81okDM7ITpnlzXBTA9R4y7wm25bgO1wGlc4D9MSvuwQ+wuwIdtxRicg/Z3GjAx3fNZesvVI8sM4fB+jUCHfnifmI3O1tcSAyPz+/C2aMgCNdtZv8ZboGzKPlF+cFDr97eze5GRCW/e1DJsVNw5HsJ+Zn6hFQzGbVrWiYZX6/zG1LO0XAdEgtz04d4EDiN14CP8GCQGzlbdlzzVMBqEYbz2GXqrJ4cP3y6WODCoTD+U0y7/ssF4d54RfmtxFO0JV6hVQidSXS0hRwy1OenMOFFKHid2zvoLuBzJ2+Z8hi8eKhNsV3zGuBWpzhGjN5o5Xs6si6Vc1vmovTTSMGiDwrTwHAL42PRQoEtvTCbrX8NSQv0FQKv2sOrfcKlYeWr589/h+2cDcqTeZ+F3IOh2b+3PwuOkASNl2RPd9O9YB5voBzc9jeYMZ37wBq5ubJ3zlkUtzMIlr/tnlNqFbokX0W1bRVc4cVf0DmPr6Yi8IiIaohzy/bQBid/98l8Cl07rCLurmbiJyHOsxUM++ZRzpV/WJ9w+RxgBGM8ELePL9noBQSVvA71dy2PNwDxnTFXnImPByIAN8vUs+oi6lYfuf2bmeOYLStv3fIKFmJUM/xY/NqXC0CWnQWvxgMmJP5V2T+o6mpI8KKy9BnWxeBcOffvgQ+yeIOb3W1x1NpmSDg/MP5WPDQ8vWTx1eoBAOJn5TZjsZ97vFiQHjx36mHVf0qOR/u4QTK/j1quZkwBhHBaGTWLalg/O7t3UpVkLnVdw5ZyG4gkPjD86rhTsC1xIBK5OUMDwQYvPoSGCe1CMB1SCXP0hymDuVfGVaJ1AN+MhIQKHauh3yKykCEG79/dmsdEnh4+YZJo9rtbtLh4aDLJXhPqCFghb8rc78YCMAi0r7dKmnkMzQLkub8OalmtK2JVP2P7R2CWhCpK+8fVBCkoeP3zKuhgSBUOaAR6UoE3Q3+QbkEJ1k1zGE5Bog8rWR3hzv/8rAZfhzZEMw4s1cl+8LoDgdKuWJmhxzWTi7W5NEyuGt3j1Tjpql3G0nV1NKMJ/XCdXtUIvdFMSDU8IX9UolI1Ujd1NLUC9XyVVcNYDAAwlZ2E6mrBXcHCQC8X2Za70Kp/317NyADZG71vUMmxY10dPyueS3QnCRL8QEiPx5OIkD8S9m7EamlEal27JvcuFslIuO2ABEozkH3aY4AYPz6aq9RJVJPqqV9i1fU/X4iOgdZfH0vEfnndLVwRNgfz2zNUgmn69e3kylj92+lBRkMbp+yre0L082t3E2LFcsld+rq5TdHu0kt9yMXB+DBSNq26sWLlez0SCwLvc4rwmHO3EMq+TssMPcw4/psRLaCUOW3be8mL+Zgbu1dswi6d/FN8xoRCmdkYMhXsTVzWLi3GxfXzm6e32y7nDrVbDmXtnjO37TbzsWkOXZYDHpaSR4OmNvFnKY5tUglJ2dQ3c8f7PdRL0BEZ6t9Krno2Bns+NJZHWpJiofWr2kT50kag84IFuaUupJKyaWUrJqyaVHNj1d7iNzHTo1Owj3lVCznklMqpeSynbkoVY8NBwkoyv4eIrIOJ0k4+HdntD0qkZnv2d4B1QKP1Pl7h4wL1Alv+Z/mNaYrEFDnkK3cFVNEEHQrmkrXmaqbFsuatORSfrzPvmQZCJhhQCVPTxmBiDBYSabaFbWiueSiKZWr+n0EBe6Y4my/pxNwEJjahfFsdktfUsWD/Wtnjgtu4M4gcs6qGl3bptylVLpULKWSTo97PBMpAwZYRO66rG3O2uViOZU2aS19zzqAgEW+qt/zaHCHOjpeJdUstkg0I+/b3vU76GVa3j9kYsiga4v/OK8RtYAoiiFfy86zOxnQyG3b+TR1mlPWlHKaTrN1Kf1An8WSEzy0IAaIPDO3cATgUVJbrM1ZUyqWctHtqV3b7+NWAkBrA2SLJdxI7ezvzuaata9W8vAyc/wl5uwgSLhr6cyKQa24lhKK4l4Mf9Dn6UwFRgvCwq0YTMPg7mowW+p10TSCNNOr+8mXASDCdeq/LTOdVhEzahdePFwt6zuGNMkUMG39v8yrDjODeR6yP3dqCnWPgFvxAisdzQtgZmrZUNKP9plkVQu14hz0vNzBIhAOqBVYUXoUhCkspSv7fRqdA168l4gcpoERrknj4ExOllpI1Wn/xnmjtiDd3dXczMzVYApzd6jB3UHLf3jTbrXIUXbJ3N0sTN2sKFRhWpRWUOqqR3XR4eYBXLxiwMmWXsyQsvLOWSzmUDUP6vu3dwymINpsr+tXVQtdSg5LWX9M6nlU0riXUixcOWr2quR3oK5mAXeHq5upQotpUYW5mxWL8nerPUYybi1rVwzZ62bAcWQzU5irailFrahbyWqaS5cPVH0mvxkWDs1+aoB8isUA5FL089LM4PpwSF/Xi/W9bTdrfJ6q7kVVzV1TyqUULTtN1axkNTf90nVS75CR3M5spkWLmqnmUtQ051yKmgUpUu8lbZiawW06GSDfTC9JrXjiZ0WkGlLl9NXUR83fubX6zq6YB135Gmn61LIcWUtYtOljItUcRGp4ClO3xLraS94eVszCS9HibjnlnEouJaUulWKlpFzMyj+WnlVOKTTnpCZDT7CYlmJm2qWu63LOpeSSVRXBclPTZ/xbkQo9DGel6nc9vLVsnkvK+2WG13SyBs/yDe1kzqier1BD7nIuWrRrU1c0l9SmLucupZS7olnbx66TapdKjrKUtDOnkrrcppxz23ZdLjlP1SayZyWSrVhWK3phcUgd7EpOljrjrTK0FtHVPK1G5vEtW5OTVJj51ra/VnpXcr0VNStJ9fukbuYycc85JUzdpGdzWtuiRbsud6nk0rbdtEtdbqddm0rKqes605z+0V6NrBRNJV8sbe4GVHISJe/UYm3bTlNKqWvTdspdsa7gOpFqL/l9Gixrl9ekfyX/glY05W0m/p40wxrrvtLrwf5jbc5cuPIz4MDg7ojgTgRJtn90hYhUUonIV0WwdwTJCO4alnuIyAXu+fjKoD83nQbJVtvy20vjST8R2VRc/8dba+53JcnS+pv71dWNmoJkuH1amrnUS5m7W97X42tp7B/h3BkR3BkBkOQ3SbVHtVJI0mlM+1d6iTwtODzoCO6M7TurSvZeeIwWJL1sDGjq8WPOoKacAm+W4TedVlD3h+9vuylDZOWq6++94+Sx204cO3b7ybuOH7/jjuNHjxw9fuLk8TuOH7/9yO0nTtx+/MSx666QnqPjJ07cefzEyTtOnLjjyLETJ24/fvzE4UNHbzt67NgdN155vfQ+fvDQLbfefOjmw8+XoZVced3BW669/eanLC/fKMOr40964tOe8LibvuRJN25Nqpuuvu7I4UOHrj007iciJ4/cevvx4wdvvOVamfdNB2+77fjRw3feekx6rjzl5NGj9913/7333nfXPXfd9fTjx0/efeeJe77qxIm7Tt514o47jh0/fuzY7ceO3Sp9b7nhwK3XH7j6lhM3S9WvWrrr/uMnT5w4efT2Ow4eO3LzbYdvOXrktltvPnzLzbfeePX114pIs5ccPHjdNTcdeOqRA9cNkEbqw7ccPHroqYeuuebQSjOsPeG5nv35HveUxz/lGc/b5sx6IpXMtapk96aPiNRy6da17FoNqeVSXWytEhGpK5GqlsGNSCUijVyizaSWqs9/vfW4lkYuyUp2b2RoJbvWdT2gkp2ViEgtItUMWtu1o7tZo5JmJKOmGlbtJpVIJSKV9G6a8Y5qR1UNGEkzoBrVUotUMvNqRzUaVMmiHbRlW7SDre3aiDS1DK8rqapm1FTVJdDIREQq6V3NphpQVdWwpqqrqq4GVVJXUolI1WfXSurRkKqWRpqRVDJk92qnNDLL3a61dnKhXXPhQttNGY38t7auZGfVQ2Zd7TH/3VR1JVKJVEOkEZGqruVSrKUSEamqPv/V1vJffSVzraSRmZ+0Rzln8D//8z//8z//8z//8z//8z//8z//8z//8z//8z//8z//8z//8z//8z//8z//8z//8z//8z//8z//8z//8z//8z//8z//8z//8z//8z//8z//8z//8/+fjLH3x//8z//8z/+oGnt//M///M///M///M///M///M///M///M//70VWUDggzlQAALArAp0BKgAEAAQ+MRiLRCIhoRDpnGggAwSzt33m1EKNtkYOQ/0WztZ47HYvW7cZkDfMf7T3u/pv/e/xnGufjls3uxeZet/OfoB+s18XSh+I/G/wmEG/wP69/3f/yf7H6COG+Ep90/Svx3fr+Gv/defnzD/nPtf+bv/H/6/s/+8P3BP1X/YLrlfu36if6T/nf9p/p/3/+Y//p/7r2U/279t/6b/bvkA/jH9i/7froexd/ev+r7AX8j/yP/r9dD9ovhG/qv+j/9/+K/f////Yx/RP8b//v3f+AD/0eoB/4usf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",
        "report_year": sections.get("report_year", ""),
        "BRANCHE_LABEL": sections.get("BRANCHE_LABEL", ""),
        "UNTERNEHMENSGROESSE_LABEL": sections.get("UNTERNEHMENSGROESSE_LABEL", ""),
        "BUNDESLAND_LABEL": sections.get("BUNDESLAND_LABEL", ""),
        "HAUPTLEISTUNG": sections.get("HAUPTLEISTUNG", ""),
        # dynamic sections
        **sections,
    }

    # =========================================================================
    # Multilingual v1 Step 4: Inject ui() into template context
    # TASK C: Use segment-aware ui_for_segment() for SOLO label localization
    # =========================================================================
    segment = sections.get("COMPANY_SIZE", "team")
    # Normalize segment to canonical form (SOLO, TEAM, KMU)
    segment_map = {"solo": "SOLO", "team": "TEAM", "klein": "TEAM", "kmu": "KMU"}
    segment_canonical = segment_map.get(str(segment).lower(), "TEAM")
    ctx["ui"] = ui_for_segment(lang, segment=segment_canonical)
    ctx["report_lang"] = lang
    ctx["report_segment"] = segment_canonical
    log.debug("[RENDER] Using segment-aware labels: segment=%s, lang=%s", segment_canonical, lang)

    # Log what we're rendering (for debugging)
    log.info(f"🎨 Rendering report {run_id} with {len(sections)} sections (lang={lang})")
    log.debug(f"Sections available: {list(sections.keys())}")

    # FIX-503C: Debug logging for QUICK_WINS_HTML to trace rendering issues
    qw_html = sections.get("QUICK_WINS_HTML", "")
    qw_html_left = sections.get("QUICK_WINS_HTML_LEFT", "")
    qw_html_right = sections.get("QUICK_WINS_HTML_RIGHT", "")
    log.info(f"[FIX-503C] QUICK_WINS_HTML: len={len(qw_html) if qw_html else 0}, "
             f"has_content={bool(qw_html and '<' in str(qw_html))}, "
             f"preview={str(qw_html)[:150] if qw_html else 'EMPTY'}...")
    if qw_html_left or qw_html_right:
        log.info(f"[FIX-503C] QUICK_WINS_HTML_LEFT: len={len(qw_html_left) if qw_html_left else 0}, "
                 f"QUICK_WINS_HTML_RIGHT: len={len(qw_html_right) if qw_html_right else 0}")

    # FIX-F2: UTF-8 Doppel-Encoding in ALLEN ctx-Values reparieren
    # Mojibake kommt aus Questionnaire-Daten die direkt ins Jinja2-Template gehen
    for _k, _v in list(ctx.items()):
        if isinstance(_v, str) and len(_v) > 2:
            _fixed = fix_double_encoded_utf8(_v)
            if _fixed != _v:
                ctx[_k] = _fixed
    # FIX-B734b: Sanitize grid layouts in LLM-generated HTML sections
    _grid_sections = [
        'AI_POLICY_MINI_HTML', 'TEMPLATES_START_HTML', 'MONETARISIERUNG_HTML',
        'KI_SKILLPLAN_HTML', 'KICKOFF_VORLAGE_HTML', 'GLOSSAR_HTML',
        'SOFORT_START_HTML', 'STARTER_KIT_HTML',
    ]
    for _gs in _grid_sections:
        _gv = ctx.get(_gs, '')
        if isinstance(_gv, str) and len(_gv) > 100:
            _gv_new = sanitize_grid_layouts(_gv, _gs)
            if _gv_new != _gv:
                ctx[_gs] = _gv_new

    # Z+1c-PRE: NUCLEAR score fix on ALL ctx sections BEFORE Jinja
    _cg_pre = int(float(ctx.get('CANONICAL_GOVERNANCE', 0) or 0))
    _cs_pre = int(float(ctx.get('CANONICAL_SECURITY', 0) or 0))
    _z1c_pre = 0
    if _cg_pre > 0 and _cs_pre > 0:
        for _sk in list(ctx.keys()):
            _sv = ctx.get(_sk, '')
            if not isinstance(_sv, str) or len(_sv) < 50:
                continue
            _changed = False
            for _w, _r in [(38, _cg_pre), (42, _cs_pre), (32, _cg_pre), (48, _cs_pre)]:
                for _pat in [f'{_w}/100', f'{_w} / 100', f'{_w} von 100']:
                    if _pat in _sv:
                        _sv = _sv.replace(_pat, _pat.replace(str(_w), str(_r)))
                        _changed = True
                        _z1c_pre += 1
                        log.info("[Z+1c-PRE] %s: %d->%d ('%s')", _sk, _w, _r, _pat[:30])
                for _t in ['strong', 'b', 'span', 'em']:
                    for _sep in ['', ' ']:
                        _tp = f'<{_t}>{_w}</{_t}>{_sep}/100'
                        if _tp in _sv:
                            _sv = _sv.replace(_tp, f'<{_t}>{_r}</{_t}>{_sep}/100')
                            _changed = True
                            _z1c_pre += 1
                            log.info("[Z+1c-PRE] %s <%s>: %d->%d", _sk, _t, _w, _r)
            if _changed:
                ctx[_sk] = _sv
    log.info("[Z+1c-PRE] PRE-RENDER: %d fixes (Gov=%d, Sec=%d)", _z1c_pre, _cg_pre, _cs_pre)
    # A2: Strip template phrases from LLM-generated sections
    _TEMPLATE_STRIP_PHRASES = [
        'Template-Text', 'Platzhalter für', 'Beispieltext:', 'Beispieltext',
        'Lorem ipsum', 'TODO:', 'Mustertext', 'Dummy-Text', 'Platzhaltertext',
    ]
    _TEMPLATE_CHECK_SECTIONS = [
        'TECHNOLOGIE_PROZESSE_HTML', 'NEXT_ACTIONS_HTML', 'RECOMMENDATIONS_HTML',
        'BUSINESS_CASE_HTML', 'EXEC_SUMMARY_HTML', 'ROADMAP_HTML',
    ]
    _a2_fixes = 0
    for _a2_sk in _TEMPLATE_CHECK_SECTIONS:
        _a2_sv = ctx.get(_a2_sk, '')
        if not isinstance(_a2_sv, str):
            continue
        for _a2_phrase in _TEMPLATE_STRIP_PHRASES:
            if _a2_phrase in _a2_sv:
                # Remove the sentence containing the template phrase
                _a2_sv = _a2_sv.replace(_a2_phrase, '')
                _a2_fixes += 1
                log.info("[A2] Stripped '%s' from %s", _a2_phrase, _a2_sk)
        if _a2_fixes > 0:
            ctx[_a2_sk] = _a2_sv
    if _a2_fixes > 0:
        log.info("[A2] Total template phrases stripped: %d", _a2_fixes)


    # A2: Strip template phrases from LLM-generated sections
    _TEMPLATE_STRIP_PHRASES = [
        'Template-Text', 'Platzhalter für', 'Beispieltext:', 'Beispieltext',
        'Lorem ipsum', 'TODO:', 'Mustertext', 'Dummy-Text', 'Platzhaltertext',
    ]
    _TEMPLATE_CHECK_SECTIONS = [
        'TECHNOLOGIE_PROZESSE_HTML', 'NEXT_ACTIONS_HTML', 'RECOMMENDATIONS_HTML',
        'BUSINESS_CASE_HTML', 'EXEC_SUMMARY_HTML', 'ROADMAP_HTML',
    ]
    _a2_fixes = 0
    for _a2_sk in _TEMPLATE_CHECK_SECTIONS:
        _a2_sv = ctx.get(_a2_sk, '')
        if not isinstance(_a2_sv, str):
            continue
        for _a2_phrase in _TEMPLATE_STRIP_PHRASES:
            if _a2_phrase in _a2_sv:
                # Remove the sentence containing the template phrase
                _a2_sv = _a2_sv.replace(_a2_phrase, '')
                _a2_fixes += 1
                log.info("[A2] Stripped '%s' from %s", _a2_phrase, _a2_sk)
        if _a2_fixes > 0:
            ctx[_a2_sk] = _a2_sv
    if _a2_fixes > 0:
        log.info("[A2] Total template phrases stripped: %d", _a2_fixes)



    html = env.get_template(tpl_name).render(**ctx)

    # Q3: Fix Kl→KI globally in final HTML (common OCR/input error)
    html = re.sub(r'\bKl-Readiness', 'KI-Readiness', html)
    html = re.sub(r'\bKl-Ready', 'KI-Ready', html)
    html = re.sub(r'Automatisierte Kl-', 'Automatisierte KI-', html)
    log.info("[Q3] Kl→KI fix applied on final HTML")

    # S2: Fix persona leaks for team/kmu size (Einzelperson → Team)
    _company_size = ctx.get("COMPANY_SIZE", "") or ctx.get("size_label", "") or ""
    if _company_size and "solo" not in str(_company_size).lower():
        _persona_fixes = [
            (r'als Einzelperson', 'als Team'),
            (r'Ihre Agilität als Einzelperson', 'Ihre Agilität als kleines Team'),
            (r'Solo-Selbstständige[rn]?', 'kleine Unternehmen'),
            (r'Einzelunternehmer(?:in)?', 'Ihr Unternehmen'),
        ]
        for _pat, _repl in _persona_fixes:
            html = re.sub(_pat, _repl, html)
        log.info("[S2] Persona-leak fix applied for size=%s", _company_size)

    # V4 (was U6): Förder-Alignment-Tabelle — leere Tabellen durch Hinweis ersetzen
    # Improved: Match ANY table, then check if it has only header rows
    def _fix_empty_tables_v4(html_text):
        def _check_table(match):
            t = match.group(0)
            # FIX-B732-VENDOR: Preserve vendor audit tables from empty-table killer
            if "data-preserve" in t:
                return t
            all_rows = re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.DOTALL | re.IGNORECASE)
            if len(all_rows) <= 1:
                # Only 0 or 1 row (header only) → empty
                return '<div style="padding:12px;color:#64748b;font-style:italic;">Keine Daten für diese Darstellung verfügbar.</div>'
            # Check if rows after first have any <td> with actual text content
            data_rows = all_rows[1:]  # skip header
            has_content = False
            for row in data_rows:
                # Strip tags, check for non-whitespace
                text = re.sub(r'<[^>]+>', '', row).strip()
                if len(text) > 5:
                    has_content = True
                    break
            if not has_content:
                return '<div style="padding:12px;color:#64748b;font-style:italic;">Keine Daten für diese Darstellung verfügbar.</div>'
            return t
        return re.sub(r'<table[^>]*>.*?</table>', _check_table, html_text, flags=re.DOTALL | re.IGNORECASE)
    html = _fix_empty_tables_v4(html)

    # U5: Remove TBD placeholders from final HTML
    html = re.sub(r'\bTBD\b', '', html)
    html = re.sub(r'\b[Tt]o [Bb]e [Dd]etermined\b', '', html)
    html = re.sub(r'\b[Pp]latzhalter\b', '', html)

    # W6: Monetarisierung — fix numbered list with missing items
    _monet = ctx.get('MONETARISIERUNG_HTML', '')
    if isinstance(_monet, str) and _monet:
        # Check for "2." or "3." without content (just number + whitespace)
        _monet = re.sub(r'<(?:li|p|div)[^>]*>\s*2\.\s*</(?:li|p|div)>', '', _monet, flags=re.I)
        _monet = re.sub(r'<(?:li|p|div)[^>]*>\s*3\.\s*</(?:li|p|div)>', '', _monet, flags=re.I)
        # Also remove bare "2." or "3." not in tags
        _monet = re.sub(r'(?<=>)\s*[23]\.\s*(?=<)', '', _monet)
        ctx['MONETARISIERUNG_HTML'] = _monet
        log.info("[W6] Cleaned empty pricing model numbers from MONETARISIERUNG")

    # W5: Gamechanger-Dopplung — wenn identischer Text, lösche KI_STACK_SUMMARY
    _gc_text = re.sub(r'<[^>]+>', '', str(ctx.get('GAMECHANGER_HTML', ''))).strip()
    _ks_text = re.sub(r'<[^>]+>', '', str(ctx.get('KI_STACK_SUMMARY_HTML', ''))).strip()
    if _gc_text and _ks_text and (_gc_text == _ks_text or len(_gc_text) < 100):
        ctx['KI_STACK_SUMMARY_HTML'] = ''
        log.info("[W5] Removed duplicate KI_STACK_SUMMARY_HTML (identical to GAMECHANGER)")

    # Y6 (was W4): Label-Disambiguierung — Compliance-Scores in Risiko-Matrix
    # The risk matrix section has its own "Sicherheits-Score" that means something different
    # from the Cover's "Sicherheits-Score". Rename to avoid confusion.
    # Target: inside risk-block/matrix-block divs, rename the label
    def _y6_disambiguate(match):
        block = match.group(0)
        block = block.replace('Sicherheits-Score', 'Compliance-Sicherheits-Score')
        return block
    html = re.sub(
        r'<div[^>]*class="[^"]*risk-block[^"]*"[^>]*>.*?</div>\s*</div>',
        _y6_disambiguate, html, flags=re.DOTALL | re.I
    )
    # Also catch the Gesamtbewertung label near "87 / Sicherheits-Score"
    html = re.sub(
        r'(\d{2,3}\s*/\s*)Sicherheits-Score(\s*/\s*Note)',
        r'\1Compliance-Sicherheits-Score\2', html
    )

    # W3: Hide thin sections — replace sections with <50 words with empty string
    # This removes near-empty placeholder pages from the PDF
    _W3_THIN_SECTIONS = [
        ('ninety-day-plan', 'NINETY_DAY_PLAN_HTML'),
        ('gamechanger-analysis', 'GAMECHANGER_HTML'),
        ('ki-systemlandschaft', 'KI_STACK_SUMMARY_HTML'),
        ('gamechanger-decision', 'GAMECHANGER_DECISION_HTML'),
        ('roadmap-90d-decision', 'ROADMAP_90D_DECISION_HTML'),
        ('ki-stack-summary', 'ki_stack_summary'),
    ]
    for _w3_class, _w3_key in _W3_THIN_SECTIONS:
        _w3_val = ctx.get(_w3_key, '')
        if isinstance(_w3_val, str) and _w3_val:
            _w3_text = re.sub(r'<[^>]+>', '', _w3_val)
            _w3_words = len(_w3_text.split())
            _is_placeholder = any(p in _w3_text.lower() for p in [
                'konkrete empfehlungen richten sich',
                'richten sich nach ihren individuellen',
                'bietet potenziale in prozessautomatisierung',
                'dokumentenverarbeitung und entscheidungsunterst',
                'vorhandenen ressourcen',
            ])
            # Z4: Also check if section is mostly placeholder (>50% generic text)
            _z4_generic = sum(1 for p in [
                'prozessautomatisierung', 'dokumentenverarbeitung',
                'entscheidungsunterst', 'individuellen priorit',
                'vorhandenen ressourcen', 'konkrete empfehlungen',
            ] if p in _w3_text.lower())
            if _z4_generic >= 3:
                _is_placeholder = True
            if _w3_words < 50 or _is_placeholder:
                ctx[_w3_key] = ''
                log.info("[W3+X3] Hidden thin/placeholder section %s (%d words, placeholder=%s)", _w3_key, _w3_words, _is_placeholder)
    # X3: Also check NINETY_DAY_PLAN and redundant roadmap
    for _x3_key in ('NINETY_DAY_PLAN_HTML', 'ROADMAP_90D_HTML'):
        _x3_val = ctx.get(_x3_key, '')
        if isinstance(_x3_val, str) and _x3_val:
            _x3_text = re.sub(r'<[^>]+>', '', _x3_val)
            _x3_words = len(_x3_text.split())
            if _x3_words < 50:
                ctx[_x3_key] = ''
                log.info("[X3] Hidden thin section %s (%d words < 50)", _x3_key, _x3_words)

    # Y7: Roadmap Redundanz — dedup ROADMAP_90D vs ROADMAP
    _y7_road = re.sub(r'<[^>]+>', '', str(ctx.get('ROADMAP_HTML', ''))).strip()
    _y7_90d = re.sub(r'<[^>]+>', '', str(ctx.get('ROADMAP_90D_HTML', ''))).strip()
    if _y7_road and _y7_90d:
        # If 90D is subset of ROADMAP or >60% similar, drop 90D
        _y7_shorter = min(len(_y7_road), len(_y7_90d))
        _y7_overlap = sum(1 for a, b in zip(_y7_road[:_y7_shorter], _y7_90d[:_y7_shorter]) if a == b)
        if _y7_shorter > 50 and _y7_overlap / _y7_shorter > 0.6:
            ctx['ROADMAP_90D_HTML'] = ''
            log.info("[Y7] Removed redundant ROADMAP_90D_HTML (%.0f%% overlap)", 100 * _y7_overlap / _y7_shorter)

    # Y5: Vendor-Tabelle CSS fix — force readable column widths
    _y5_vendor = ctx.get('VENDOR_DETAIL_HTML', '') or ctx.get('VENDOR_AUDIT_HTML', '')
    if isinstance(_y5_vendor, str) and _y5_vendor and '<table' in _y5_vendor.lower():
        # Inject CSS override for vendor tables
        _y5_css = '<style>.vendor-table table, .vendor-detail table {table-layout:fixed;width:100%} .vendor-table td, .vendor-detail td {word-wrap:break-word;overflow-wrap:break-word;padding:6px 8px;vertical-align:top;white-space:normal}</style>'
        for _y5_key in ('VENDOR_DETAIL_HTML', 'VENDOR_AUDIT_HTML'):
            _y5_v = ctx.get(_y5_key, '')
            if _y5_v and '<table' in _y5_v.lower():
                ctx[_y5_key] = _y5_css + _y5_v
                log.info("[Y5] Injected table CSS into %s", _y5_key)

    # Y1-Y4: Generic empty-content hider
    # Sections where GPT produced only bare numbered lists ("1." "2.") or <30 chars text
    _Y_EMPTY_CHECK_SECTIONS = [
        'RECOMMENDATIONS_ENGINE_HTML',
        'STARTER_KIT_HTML',
        'STARTER_KIT_COMPACT_HTML',
        'ROI_TRACKING_HTML',
        'PROMPT_FRAMEWORK_HTML',
    ]
    for _y_key in _Y_EMPTY_CHECK_SECTIONS:
        _y_val = ctx.get(_y_key, '')
        if isinstance(_y_val, str) and _y_val:
            _y_text = re.sub(r'<[^>]+>', '', _y_val).strip()
            # Remove bare numbers and punctuation to check for real content
            _y_content = re.sub(r'[\d\.\s,;:\-]+', '', _y_text).strip()
            if len(_y_content) < 30:
                ctx[_y_key] = ''
                log.info("[Y1-4] Hidden empty-content section %s (content: %d chars after cleanup)", _y_key, len(_y_content))

    # Y1b: Also fix bare numbered lists in MONETARISIERUNG (keep section but clean items)
    _y_monet = ctx.get('MONETARISIERUNG_HTML', '')
    if isinstance(_y_monet, str) and _y_monet:
        # Remove any <li>, <p>, <div> that contains ONLY a number like "2." or "3."
        _y_monet = re.sub(r'<(li|p|div)[^>]*>\s*\d+\.\s*</(li|p|div)>', '', _y_monet, flags=re.I)
        # Remove bare "N." between tags
        _y_monet = re.sub(r'(?<=>)\s*\d+\.\s*(?=<)', '', _y_monet)
        # If after cleanup less than 30 chars of text remain, hide entirely
        _y_monet_text = re.sub(r'<[^>]+>', '', _y_monet).strip()
        _y_monet_content = re.sub(r'[\d\.\s,;:\-]+', '', _y_monet_text).strip()
        if len(_y_monet_content) < 30:
            ctx['MONETARISIERUNG_HTML'] = ''
            log.info("[Y1b] Hidden empty MONETARISIERUNG_HTML")
        else:
            ctx['MONETARISIERUNG_HTML'] = _y_monet
            log.info("[Y1b] Cleaned bare numbers from MONETARISIERUNG_HTML")

    # Z+1c-POST: NUCLEAR score fix on final HTML
    import re as _re_z1c
    _cg_post = int(float(ctx.get('CANONICAL_GOVERNANCE', 0) or 0))
    _cs_post = int(float(ctx.get('CANONICAL_SECURITY', 0) or 0))
    _z1c_post = 0
    if _cg_post > 0 and _cs_post > 0:
        for _wrong, _right, _label in [(38, _cg_post, 'Gov'), (42, _cs_post, 'Sec'), (32, _cg_post, 'Gov'), (48, _cs_post, 'Sec')]:
            for _pat, _rep in [
                (f'{_wrong}/100', f'{_right}/100'),
                (f'{_wrong} / 100', f'{_right} / 100'),
                (f'{_wrong} von 100', f'{_right} von 100'),
            ]:
                _c = html.count(_pat)
                if _c > 0:
                    html = html.replace(_pat, _rep)
                    _z1c_post += _c
                    log.info("[Z+1c-POST] %s: '%s' -> '%s' (%dx)", _label, _pat, _rep, _c)
            for _t in ['strong', 'b', 'span', 'em']:
                for _sep in ['', ' ']:
                    _old_t = f'<{_t}>{_wrong}</{_t}>{_sep}/100'
                    _new_t = f'<{_t}>{_right}</{_t}>{_sep}/100'
                    _c = html.count(_old_t)
                    if _c > 0:
                        html = html.replace(_old_t, _new_t)
                        _z1c_post += _c
                        log.info("[Z+1c-POST] %s <%s>: %d->%d (%dx)", _label, _t, _wrong, _right, _c)
        # NUCLEAR REGEX: >38</tag>/100 or >38< /100 etc
        for _w, _r in [(38, _cg_post), (42, _cs_post)]:
            _nuke = _re_z1c.compile(r'(?<=>)' + str(_w) + r'(?=(?:</[^>]+>)*\s*/\s*100)')
            _nc = len(_nuke.findall(html))
            if _nc > 0:
                html = _nuke.sub(str(_r), html)
                _z1c_post += _nc
                log.info("[Z+1c-POST] NUCLEAR regex: >%d< (%dx)", _w, _nc)
    # FIX-B734a: Prose-Score-Halluzination fixen
    # Fängt "Sicherheits-Score von 38" / "Governance-Score von 42" im Fließtext
    if _cg_post > 0 and _cs_post > 0:
        _prose_patterns = [
            # (regex_pattern, replacement, label)
            (r'(Sicherheits[- ]?Score\s+von\s+)\d{1,3}', rf'\g<1>{_cs_post}', 'Sec-Prose'),
            (r'(Governance[- ]?Score\s+von\s+)\d{1,3}', rf'\g<1>{_cg_post}', 'Gov-Prose'),
            (r'(Sicherheits[- ]?Score\s+unter\s+)\d{1,3}', rf'\g<1>{_cs_post}', 'Sec-unter'),
            (r'(Governance[- ]?Score\s+unter\s+)\d{1,3}', rf'\g<1>{_cg_post}', 'Gov-unter'),
            (r'(Sicherheits[- ]?Score:\s*)\d{1,3}', rf'\g<1>{_cs_post}', 'Sec-colon'),
            (r'(Governance[- ]?Score:\s*)\d{1,3}', rf'\g<1>{_cg_post}', 'Gov-colon'),
        ]
        for _pp, _pr, _pl in _prose_patterns:
            _pm = _re_z1c.findall(_pp, html)
            if _pm:
                html, _pc = _re_z1c.subn(_pp, _pr, html)
                if _pc > 0:
                    _z1c_post += _pc
                    log.info("[Z+1c-POST][FIX-B734a] %s: %d fixes", _pl, _pc)

    if _z1c_post == 0 and _cg_post > 0:
        for _dw in [38, 42, 32, 48]:
            _dp = html.find(str(_dw))
            _da = 0
            while _dp != -1 and _da < 5:
                _dc = html[max(0,_dp-80):_dp+40]
                if any(x in _dc.lower() for x in ['score', 'governance', 'sicherheit', '/100', 'von 100']):
                    log.warning("[Z+1c-DEBUG] '%d' at pos %d: ...%s...", _dw, _dp, repr(_dc[:120]))
                _dp = html.find(str(_dw), _dp + 1)
                _da += 1
    log.info("[Z+1c-POST] Total post-render: %d", _z1c_post)

    # U1b (V1): Global hauptleistung replace using ORIGINAL saved before U2
    if _hl_original and len(_hl_original) > 80:
        _hl_trunc = _hl_original[:77].rsplit(' ', 1)[0] + '…'
        _before = len(re.findall(re.escape(_hl_original), html, re.IGNORECASE))
        # W2: Case-insensitive replace to catch GPT casing variants
        html = re.sub(re.escape(_hl_original), _hl_trunc, html, flags=re.IGNORECASE)
        _after = len(re.findall(re.escape(_hl_original), html, re.IGNORECASE))
        log.info("[U1b+W2] hauptleistung replaced (case-insensitive): %d→%d chars, %d→%d occurrences",
                 len(_hl_original), len(_hl_trunc), _before, _after)
        # W2b: Also catch partial fragments (broken repeats starting mid-sentence)
        # e.g. "einführen wollen, Automatisierte KI-Readiness..."
        if len(_hl_original) > 40:
            _frag = _hl_original[len(_hl_original)//3:]  # last 2/3 of text
            if _frag and len(_frag) > 40:
                _frag_count = len(re.findall(re.escape(_frag), html, re.IGNORECASE))
                if _frag_count > 0:
                    html = re.sub(re.escape(_frag), '', html, flags=re.IGNORECASE)
                    log.info("[W2b] Removed %d fragment occurrences (%d chars)", _frag_count, len(_frag))

    # R2-FIX: Remove go-digital / ZIM from final HTML
    # Blacklist in gpt_analyze runs BEFORE engine sections are generated
    _gd_before = html.count('go-digital') + html.count('go_digital')
    if _gd_before > 0:
        html = re.sub(r'<tr[^>]*>(?:(?!</tr>).)*go[-_]digital(?:(?!</tr>).)*</tr>\s*', '', html, flags=re.I|re.DOTALL)
        html = re.sub(r'<li[^>]*>[^<]*go[-_]digital[^<]*</li>\s*', '', html, flags=re.I)
        html = re.sub(r'<div[^>]*>[^<]*go[-_]digital(?:\s*/\s*ZIM)?[^<]*</div>\s*', '', html, flags=re.I)
        html = re.sub(r'go[-_]digital\s*(?:/\s*ZIM)?\s*(?:\((?:eingestellt|Programm eingestellt)\))?\s*[–—-]?\s*(?:Eignung:[^<]*)?', '', html, flags=re.I)
        _gd_after = html.count('go-digital') + html.count('go_digital')
        log.info("[R2-FIX] go-digital removed from final HTML: %d → %d occurrences", _gd_before, _gd_after)

    # Save debug HTML for troubleshooting
    report_id = sections.get('report_id', run_id)
    debug_path = f'/tmp/report_debug_{report_id}.html'
    try:
        with open(debug_path, 'w', encoding='utf-8') as f:
            f.write(html)
        log.info(f"[RENDER] Debug HTML saved: {debug_path}")
    except Exception as e:
        log.warning(f"[RENDER] Failed to save debug HTML: {e}")

    # Post-processing: Replace unevaluated Jinja2 math expressions with pre-calculated values
    # This handles cases where Jinja2 fails to evaluate expressions like {{ EINSPARUNG_MONAT_EUR * 0.8 }}
    # Also handles single-brace placeholders that GPT may generate incorrectly
    if "{{" in html or "{" in html:
        import re

        # Map of common unevaluated expressions to their pre-calculated section keys
        expr_replacements = {
            r'\{\{\s*EINSPARUNG_MONAT_EUR\s*\*\s*0\.8\s*\}\}': str(sections.get('EINSPARUNG_MONAT_EUR_LOW', '')),
            r'\{\{\s*EINSPARUNG_MONAT_EUR\s*\*\s*1\.2\s*\}\}': str(sections.get('EINSPARUNG_MONAT_EUR_HIGH', '')),
            r'\{\{\s*ROI_12M\s*\*\s*0\.8\s*\}\}': str(sections.get('ROI_12M_LOW', '')),
            r'\{\{\s*ROI_12M\s*\*\s*1\.2\s*\}\}': str(sections.get('ROI_12M_HIGH', '')),
            r'\{\{\s*ROI_12M\s*\*\s*0\.8\s*\*\s*100\s*\}\}': str(sections.get('ROI_12M_LOW', '')),
            r'\{\{\s*ROI_12M\s*\*\s*1\.2\s*\*\s*100\s*\}\}': str(sections.get('ROI_12M_HIGH', '')),
            # ROI percentage expression
            r'\{\{\s*\(ROI_12M\s*\*\s*100\)\s*\|\s*round\s*\(\s*1\s*\)\s*\}\}': str(round(float(sections.get('ROI_12M', 0) or 0) * 100, 1)),
            # OPEX calculations - various multipliers GPT might generate
            r'\{\{\s*OPEX_REALISTISCH_EUR\s*\*\s*1\.2\s*\}\}': str(sections.get('OPEX_REALISTISCH_EUR_HIGH', '')),
            r'\{\{\s*OPEX_REALISTISCH_EUR\s*\*\s*0\.8\s*\}\}': str(sections.get('OPEX_REALISTISCH_EUR_LOW', '')),
            r'\{\{\s*OPEX_REALISTISCH_EUR\s*\*\s*0\.5\s*\}\}': str(int(float(sections.get('OPEX_REALISTISCH_EUR', 0) or 0) * 0.5)),
            r'\{\{\s*OPEX_REALISTISCH_EUR\s*\*\s*0\.2\s*\}\}': str(int(float(sections.get('OPEX_REALISTISCH_EUR', 0) or 0) * 0.2)),
            r'\{\{\s*OPEX_REALISTISCH_EUR\s*\*\s*0\.4\s*\}\}': str(int(float(sections.get('OPEX_REALISTISCH_EUR', 0) or 0) * 0.4)),
            r'\{\{\s*OPEX_REALISTISCH_EUR\s*\*\s*2\.4\s*\}\}': str(int(float(sections.get('OPEX_REALISTISCH_EUR', 0) or 0) * 2.4)),
            r'\{\{\s*OPEX_REALISTISCH_EUR\s*\*\s*12\s*\}\}': str(int(float(sections.get('OPEX_REALISTISCH_EUR', 0) or 0) * 12)),
            # Payback calculations
            r'\{\{\s*CAPEX_REALISTISCH_EUR\s*/\s*\(\s*EINSPARUNG_MONAT_EUR\s*\*\s*0\.8\s*-\s*OPEX_REALISTISCH_EUR\s*\)\s*\}\}': str(sections.get('PAYBACK_MONTHS_PESSIMISTIC', '')),
            r'\{\{\s*CAPEX_REALISTISCH_EUR\s*/\s*\(\s*EINSPARUNG_MONAT_EUR\s*-\s*OPEX_REALISTISCH_EUR\s*\*\s*1\.2\s*\)\s*\}\}': str(sections.get('PAYBACK_MONTHS_PESSIMISTIC', '')),
            r'\{\{\s*CAPEX_REALISTISCH_EUR\s*/\s*\(\s*EINSPARUNG_MONAT_EUR\s*\*\s*1\.2\s*-\s*OPEX_REALISTISCH_EUR\s*\)\s*\}\}': str(sections.get('PAYBACK_MONTHS_OPTIMISTIC', '')),
        }

        # Also replace single-brace placeholders (GPT sometimes generates these incorrectly)
        single_brace_replacements = {
            r'\{CAPEX_REALISTISCH_EUR\}': str(sections.get('CAPEX_REALISTISCH_EUR', '')),
            r'\{OPEX_REALISTISCH_EUR\}': str(sections.get('OPEX_REALISTISCH_EUR', '')),
            r'\{EINSPARUNG_MONAT_EUR\}': str(sections.get('EINSPARUNG_MONAT_EUR', '')),
            # FIX-R4-1: Format payback as German decimal, not raw float
            r'\{PAYBACK_MONTHS\}': str(sections.get('PAYBACK_MONTHS_FMT_DE', '') or sections.get('PAYBACK_MONTHS', '')),
            r'\{ROI_12M\}': str(sections.get('ROI_12M', '')),
        }
        expr_replacements.update(single_brace_replacements)

        # Strip braces from numeric literals that GPT erroneously wrapped
        # Pattern: {number} or {number.decimal} -> just the number
        numeric_brace_pattern = r'\{(\d+(?:\.\d+)?)\}'
        html = re.sub(numeric_brace_pattern, r'\1', html)
        log.debug(f"[RENDER] Stripped braces from numeric literals")

        # Replace simple variable placeholders
        simple_replacements = {
            r'\{\{\s*qw_hours_total\s*\}\}': str(sections.get('qw_hours_total', '')),
            r'\{\{\s*CAPEX_REALISTISCH_EUR\s*\}\}': str(sections.get('CAPEX_REALISTISCH_EUR', '')),
            r'\{\{\s*OPEX_REALISTISCH_EUR\s*\}\}': str(sections.get('OPEX_REALISTISCH_EUR', '')),
            r'\{\{\s*EINSPARUNG_MONAT_EUR\s*\}\}': str(sections.get('EINSPARUNG_MONAT_EUR', '')),
            # FIX-R4-1: Format payback as German decimal, not raw float
            r'\{\{\s*PAYBACK_MONTHS\s*\}\}': str(sections.get('PAYBACK_MONTHS_FMT_DE', '') or sections.get('PAYBACK_MONTHS', '')),
            r'\{\{\s*ROI_12M\s*\}\}': str(sections.get('ROI_12M', '')),
        }
        expr_replacements.update(simple_replacements)

        for pattern, replacement in expr_replacements.items():
            if replacement:  # Only replace if we have a value
                html = re.sub(pattern, replacement, html)

        log.info(f"🔧 Applied {len(expr_replacements)} expression replacements for report {run_id}")

    # Quick validation check - find which variables are missing
    if "{{" in html:
        import re
        missing = re.findall(r'\{\{\s*([^}]+)\s*\}\}', html)
        if missing:
            unique_missing = list(set(m.strip() for m in missing))[:5]  # Show max 5
            log.warning(f"⚠️ Template still contains unreplaced variables in report {run_id}: {unique_missing}")
        else:
            log.warning(f"⚠️ Template still contains unreplaced variables in report {run_id}")

    # Embed logos as base64 for PDF service compatibility
    tpl_dir_str = str(Path(tpl_path).parent)
    html = embed_logos_in_html(html, tpl_dir_str)
    log.info(f"[RENDER] Embedded logos in HTML for report {run_id}")

    # PDF-SLIMDOWN: Optimize HTML for smaller PDF file size
    # 1. Strip unused sections (empty divs, debug elements)
    # 2. Compress HTML (whitespace collapse, comment removal)
    # 3. Minify inline CSS
    original_size = len(html)
    html = optimize_html_for_pdf(html)
    new_size = len(html)
    if original_size > 0:
        savings_pct = (1 - new_size / original_size) * 100
        log.info(f"[RENDER] PDF-SLIMDOWN: {original_size}→{new_size} bytes ({savings_pct:.1f}% saved)")

    # =========================================================================
    # P0.4: Pagebreak cleanup - prevent empty/low-value pages
    # =========================================================================
    html, pagebreak_removed = cleanup_pagebreaks(html, run_id=run_id)
    if pagebreak_removed > 0:
        log.info(f"[P0.4] Pagebreak cleanup: removed {pagebreak_removed} artifacts for run={run_id}")

    # =========================================================================
    # FIX-BATCH-497: Code fence removal (hard requirement for premium PDF)
    # =========================================================================
    html, fences_removed = strip_code_fences_final(html, run_id=run_id)
    if fences_removed > 0:
        log.info(f"[FIX-497] Code fence cleanup: removed {fences_removed} artifacts for run={run_id}")

    # =========================================================================
    # SPRINT N2.5: Final leak phrase safety check (defensive)
    # =========================================================================
    # This is the LAST line of defense before PDF rendering.
    # N2.5: Using encapsulated function that NEVER blocks PDF dispatch
    log.info(f"[RENDER] Before final leak cleanup: len(html)={len(html)} for run={run_id}")
    html = final_leak_cleanup(html, run_id=run_id)
    log.info(f"[RENDER] After final leak cleanup: len(html)={len(html)} for run={run_id}")

    # =========================================================================
    # PLATIN+++ v5.4: Final development placeholder scrub
    # =========================================================================
    html = scrub_development_placeholders(html, run_id=run_id)

    # =========================================================================
    # 3.1.4.18: FINAL EN locale sanitize on full HTML (global hook)
    # Fix-Batch C: Only applies to EN reports, skipped for DE
    # =========================================================================
    html_before_locale = html
    html = sanitize_en_locale_tokens(html, lang=lang)
    if html != html_before_locale:
        log.info(f"[RENDER] Applied EN locale sanitizer (lang={lang}) for run={run_id}")
    else:
        log.debug(f"[RENDER] EN locale sanitizer skipped (lang={lang}) for run={run_id}")

    # =========================================================================
    # Multilingual v2: Locale budget enforcement + section-aware rewrite
    # =========================================================================
    html, locale_v2_meta = apply_locale_v2(html, lang)
    if locale_v2_meta.get("locale_v2", {}).get("sections_rewritten"):
        log.info(
            f"[locale-v2] score_before={locale_v2_meta['locale_v2']['score_before']} "
            f"score_after={locale_v2_meta['locale_v2']['score_after']} "
            f"sections_rewritten={locale_v2_meta['locale_v2']['sections_rewritten']}"
        )
    if meta is None:
        meta = {}
    meta.update(locale_v2_meta)

    # Add report metadata for PDF footer
    meta["report_id"] = ctx.get("report_id", "")
    meta["report_date"] = ctx.get("report_date", "")

    # =========================================================================
    # FIX-I10: Final UTF-8 double-encoding repair on complete HTML
    # =========================================================================
    html_before_utf8 = html
    html = fix_double_encoded_utf8(html)
    if html != html_before_utf8:
        log.info("[FIX-I10] Repaired UTF-8 double-encoding in final HTML for run=%s", run_id)

    # =========================================================================
    # FIX-514: Quick-Wins Non-Empty Gate (pre-PDF, fail-closed in STRICT)
    # Ensures Quick-Wins section is never an empty page in the PDF.
    # =========================================================================
    try:
        release_strict = os.getenv("RELEASE_STRICT_MODE", "0") in ("1", "true", "True")
        qw_cards = html.count('class="quick-win')
        qw_marker = html.count('data-qw-json-rendered="true"')
        # FIX-H4: LLM-HTML hat keine quick-win Klassen - auch h4 Tags zaehlen
        import re as _re
        _qw_section = _re.search(r'Quick\s*Wins</h2>.*?(?=<section\s+class="section\s+chapter"|$)', html, _re.DOTALL | _re.IGNORECASE)
        _qw_area = _qw_section.group(0) if _qw_section else html
        qw_h4_count = len(_re.findall(r'<h4[^>]*>', _qw_area, _re.IGNORECASE))
        qw_indicator = max(qw_cards, qw_marker, qw_h4_count)
        # Extract Quick-Wins text length from rendered HTML
        qw_section_match = _re.search(
            r'class="quick-wins-container"[^>]*>(.*?)</div>\s*</div>',
            html, _re.DOTALL
        )
        qw_text_len = len(qw_section_match.group(1)) if qw_section_match else 0
        # FIX-H4: Fallback - suche QW section via heading
        if qw_text_len == 0:
            _qw_body = _re.search(r'Quick\s*Wins</h2>.*?<div[^>]*class="section-body"[^>]*>(.*?)</section>', html, _re.DOTALL | _re.IGNORECASE)
            if _qw_body:
                qw_text_len = len(_qw_body.group(1))
        # Fallback: if no container match, use card count as proxy
        if qw_text_len == 0 and qw_indicator > 0:
            qw_text_len = qw_indicator * 100  # Estimate

        # FIX-J6: Also pass if substantial text exists (LLM HTML has no quick-win classes)
        qw_non_empty = (qw_indicator >= 3 and qw_text_len > 300) or qw_text_len > 2000
        log.info(
            "[FIX-H4] QW gate: cards=%d marker=%d h4=%d indicator=%d text_len=%d",
            qw_cards, qw_marker, qw_h4_count, qw_indicator, qw_text_len
        )

        if not qw_non_empty and release_strict:
            # FIX-B732-QW-TABLE: Accept table-format Quick Wins as valid
            import re as _re_qw
            _qw_html = sections.get("QUICK_WINS_HTML", "") or ""
            _qw_has_table = bool(_re_qw.search(r"<table[^>]*>.*?<t[dh]", _qw_html, _re_qw.DOTALL | _re_qw.IGNORECASE))
            _qw_has_rows = len(_re_qw.findall(r"<tr[^>]*>", _qw_html, _re_qw.IGNORECASE)) >= 2  # header + 1 data row
            if _qw_has_table and _qw_has_rows:
                log.info("[FIX-B732-QW-TABLE] Quick Wins in table format accepted (rows=%d, len=%d)", len(_re_qw.findall(r"<tr[^>]*>", _qw_html, _re_qw.IGNORECASE)), len(_qw_html))
            else:
                raise RuntimeError(
                f"[FIX-514] QuickWinsEmptyError: cards={qw_indicator} len={qw_text_len}"
            )
    except RuntimeError:
        raise
    except Exception as e:
        log.warning("[FIX-514][QW] Gate check error (continuing): %s", str(e)[:100])

    # =========================================================================
    # FIX-505: HTML Contract Validation (STRICT_MODE aware)
    # Validates final HTML against quality contract before PDF generation.
    # In STRICT_MODE: fails hard on violations. Otherwise: logs and continues.
    # =========================================================================
    try:
        from services.html_contract import (
            html_contract_validate,
            ContractViolationError,
        )

        # Get sections list for validation
        section_keys = [k.replace("_HTML", "").lower() for k in sections.keys() if k.endswith("_HTML")]

        contract_result = html_contract_validate(
            html=html,
            sections=section_keys,
            allow_repair=True,  # Allow one repair attempt
        )

        if contract_result.passed:
            log.info(
                "[FIX-505][HTML-CONTRACT] PASS violations=0 warnings=%d bytes=%d run=%s",
                contract_result.warning_count, len(html), run_id
            )
        else:
            # Non-STRICT mode: log but continue
            log.warning(
                "[FIX-505][HTML-CONTRACT] FAIL violations=%d critical=%d run=%s "
                "(continuing in non-strict mode)",
                len(contract_result.violations),
                contract_result.critical_count,
                run_id
            )

        # Store contract result in meta for debugging
        if meta is None:
            meta = {}
        meta["html_contract_result"] = {
            "passed": contract_result.passed,
            "critical_count": contract_result.critical_count,
            "warning_count": contract_result.warning_count,
            "repair_attempted": contract_result.repair_attempted,
            "repair_successful": contract_result.repair_successful,
        }

        # FIX-517C: One-line Strict Summary with unified warning count
        if contract_result.passed:
            _qw_cards_515 = html.count('class="quick-win')
            _qw_nonempty_515 = 1 if _qw_cards_515 >= 3 else 0
            _repair_llm_515 = 1 if getattr(contract_result, 'repair_llm_used', False) else 0
            # FIX-517C: Use unified total (pipeline + validator) not just contract warnings
            _pipeline_warnings = int(sections.get("PIPELINE_WARNINGS_COUNT", 0) or 0)
            _validator_warnings = int(sections.get("VALIDATOR_WARNINGS_COUNT", 0) or 0)
            _total_warnings = _pipeline_warnings + _validator_warnings + contract_result.warning_count
            _grade = sections.get("PIPELINE_GRADE", "?")
            log.info(
                "[FIX-515][STRICT-READY] contract_pass=1 repair_llm_used=%d "
                "quickwins_nonempty=%d pipeline_warnings=%d validator_warnings=%d "
                "warnings_total=%d grade=%s",
                _repair_llm_515, _qw_nonempty_515,
                _pipeline_warnings, _validator_warnings,
                _total_warnings, _grade
            )

    except ContractViolationError as e:
        # STRICT_MODE violation - re-raise to abort PDF generation
        log.error(
            "[FIX-505][HTML-CONTRACT] FAIL-CLOSED strict=1 violations=%d run=%s",
            e.result.critical_count, run_id
        )
        # Add debug attachments from contract error
        if meta is None:
            meta = {}
        meta["html_contract_error"] = {
            "violations": [v.to_dict() for v in e.result.violations[:10]],
            "critical_count": e.result.critical_count,
        }
        # FIX-512 CHANGE 3: Store debug attachments for admin email
        if e.debug_attachments:
            meta["html_contract_debug_attachments"] = e.debug_attachments
            log.info(
                "[FIX-512][HTML-CONTRACT] debug_attachments stored: keys=%s",
                list(e.debug_attachments.keys())
            )
        raise
    except ImportError:
        log.debug("[FIX-505][HTML-CONTRACT] Module not available, skipping validation")
    except Exception as e:
        # Never block PDF on contract check errors (defensive)
        log.warning("[FIX-505][HTML-CONTRACT] Validation error (continuing): %s", str(e)[:100])

    # =========================================================================
    # DEBUG-503D: Build debug attachments when DEBUG_RENDER=1
    # Collect right before return, after all post-processing, when FINAL HTML is ready.
    # IMPORTANT: Raw bytes are returned separately - they must NEVER be stored in meta
    # (Postgres JSONB can't serialize bytes objects).
    # =========================================================================
    debug_attachments_for_email = None  # Will hold bytes for email, NOT persisted to DB

    if is_debug_render_enabled():
        # Build canonical KPIs dict for payback mentions
        canonical_kpis = {
            "PAYBACK_MONTHS": sections.get("PAYBACK_MONTHS"),
            "CAPEX_REALISTISCH_EUR": sections.get("CAPEX_REALISTISCH_EUR"),
            "OPEX_REALISTISCH_EUR": sections.get("OPEX_REALISTISCH_EUR"),
            "EINSPARUNG_MONAT_EUR": sections.get("EINSPARUNG_MONAT_EUR"),
        }

        debug_attachments = build_debug_503d_attachments(
            final_html=html,
            sections=sections,
            canonical_kpis=canonical_kpis
        )

        if debug_attachments:
            # Store ONLY JSON-safe summary in meta (for DB persistence)
            # Contains: filenames, sizes, sha256 hashes, previews - NO raw bytes
            meta["debug_503d_summary"] = build_debug_503d_summary(debug_attachments)

            # Return raw bytes separately for email attachments (NOT stored in DB)
            debug_attachments_for_email = debug_attachments

            log.info(f"[DEBUG-503D] Collected {len(debug_attachments)} debug artifacts for admin email")

    return {"html": html, "meta": meta or {}, "debug_attachments": debug_attachments_for_email}
