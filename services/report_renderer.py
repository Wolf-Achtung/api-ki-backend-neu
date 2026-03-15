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

# Emoji regex for stripping emojis from backend-generated HTML blocks
_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F300-\U0001F5FF"  # Misc Symbols and Pictographs
    "\U0001F680-\U0001F6FF"  # Transport and Map Symbols
    "\U0001F1E0-\U0001F1FF"  # Flags
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols Extended-A
    "\U00002702-\U000027B0"  # Dingbats
    "\U000024C2-\U0001F251"  # Enclosed characters
    "\U0000FE0F"             # Variation Selector-16
    "\U0000200D"             # Zero Width Joiner
    "\U00002600-\U000026FF"  # Misc Symbols
    "\U00002700-\U000027BF"  # Dingbats
    "\U0000FE00-\U0000FE0F"  # Variation Selectors
    "\U0000231A-\U0000231B"  # Watch, Hourglass
    "\U000023E9-\U000023F3"  # Various symbols
    "\U000023F8-\U000023FA"  # Various symbols
    "\U000025AA-\U000025AB"  # Squares
    "\U000025B6\U000025C0"   # Play/Reverse buttons
    "\U000025FB-\U000025FE"  # Squares
    "\U00002B05-\U00002B07"  # Arrows
    "\U00002B1B-\U00002B1C"  # Squares
    "\U00002B50\U00002B55"   # Star, Circle
    "\U00003030\U0000303D"   # Wavy Dash, Part Alternation Mark
    "\U00003297\U00003299"   # Circled Ideographs
    "]+",
    flags=re.UNICODE
)


def _strip_emojis(text: str) -> str:
    """Remove all emojis from a string. Safe for HTML content."""
    if not text or not isinstance(text, str):
        return text
    return _EMOJI_RE.sub("", text)


def _strip_emojis_from_context(context: dict) -> dict:
    """Strip emojis from all *_HTML template variables in the render context."""
    for key in list(context.keys()):
        if isinstance(context[key], str) and (key.endswith("_HTML") or key.endswith("_html")):
            context[key] = _strip_emojis(context[key])
    return context


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
            sections[_u2_key] = _u2_val[:200].rsplit(' ', 1)[0]
            log.info("[U2] Trimmed sections['%s']: %d→%d chars", _u2_key, len(_u2_val), len(sections[_u2_key]))

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

    _risks_dbg = sections.get("RISKS_HTML", "")
    # B9: Fix residual LLM-generated "Unternehm…" truncation
    import re as _b9re
    for _b9k, _b9v in list(sections.items()):
        if isinstance(_b9v, str) and _b9re.search(r'Unternehm[…\.]{1,3}(?!en|ens)', _b9v):
            sections[_b9k] = _b9re.sub(r'Unternehm[…\.]{1,3}', 'Unternehmen', _b9v)
            log.info("[B9] Fixed Unternehm-ellipsis in %s", _b9k)

    # Mark HTML sections as safe (prevent escaping) — AFTER all sanitization!
    safe_sections = {}
    for key, value in sections.items():
        if isinstance(value, str) and key.endswith('_HTML') and '<' in value:
            safe_sections[key] = Markup(value)
            log.debug(f"[RENDER] Marked section '{key}' as safe HTML (post-sanitize)")
        else:
            safe_sections[key] = value
    sections = safe_sections
    # FIX-v720-COVER-ROI: Ensure ROI_12M_DISPLAY_DE is always set
    # P0.1 in gpt_analyze.py sets this, but if it fails the template falls back to
    # ROI_P50 (Monte Carlo) which can be much lower than ROI_12M (deterministic).
    if not sections.get("ROI_12M_DISPLAY_DE"):
        _roi_12m = sections.get("ROI_12M")
        if _roi_12m is not None:
            try:
                sections["ROI_12M_DISPLAY_DE"] = Markup(f"{int(float(_roi_12m))} %")
                log.info("[FIX-v720-COVER-ROI] Set ROI_12M_DISPLAY_DE=%s from ROI_12M", sections["ROI_12M_DISPLAY_DE"])
            except (ValueError, TypeError):
                pass

    # FIX-v720-F5: Ensure CAPEX_DISPLAY_DE is set for Management Summary
    # Template shows "—" when CAPEX_DISPLAY_DE and TOTAL_CAPEX are both missing.
    if not sections.get("CAPEX_DISPLAY_DE"):
        _capex_raw = sections.get("CANON_CAPEX_EUR") or sections.get("CAPEX_REALISTISCH_EUR")
        if _capex_raw is not None:
            try:
                _capex_val = int(float(_capex_raw))
                sections["CAPEX_DISPLAY_DE"] = Markup(f"{_capex_val:,}€".replace(",", "."))
                log.info("[FIX-v720-F5] Set CAPEX_DISPLAY_DE=%s", sections["CAPEX_DISPLAY_DE"])
            except (ValueError, TypeError):
                pass

    # FIX-v720-N1: Ensure PAYBACK_MONTHS_FMT_DE is set for Management Summary
    # Solo reports show "n/a Mo" when F1 in final_sanitizer doesn't fire.
    # Safety net: derive from PAYBACK_MONTHS, _PAYBACK_BC_V2, or BC_PAYBACK_REALISTIC.
    if not sections.get("PAYBACK_MONTHS_FMT_DE"):
        _pb_raw = (
            sections.get("PAYBACK_MONTHS")
            or sections.get("_PAYBACK_BC_V2")
            or sections.get("BC_PAYBACK_REALISTIC")
        )
        if _pb_raw is not None:
            try:
                _pb_float = float(str(_pb_raw).replace(",", "."))
                if 0 < _pb_float < 120:  # sanity: 0-120 months
                    _pb_fmt = f"{_pb_float:.1f}".replace(".", ",")
                    sections["PAYBACK_MONTHS_FMT_DE"] = Markup(_pb_fmt)
                    # Also ensure PAYBACK_MONTHS is set for template fallback
                    if not sections.get("PAYBACK_MONTHS"):
                        sections["PAYBACK_MONTHS"] = Markup(_pb_fmt)
                    log.info("[FIX-v720-N1] Set PAYBACK_MONTHS_FMT_DE=%s", _pb_fmt)
            except (ValueError, TypeError):
                pass

    # Safe defaults with FIXED UTF-8
    # TEIL 3.1.4.x: Force LANG to detected value (no fallback to sections)
    ctx: Dict[str, Any] = {
        "LANG": "en" if is_en else "de",  # FORCED, not from sections
        "OWNER_NAME": sections.get("OWNER_NAME", os.getenv("OWNER_NAME", "KI-Sicherheit.jetzt")),  # ✅ FIXED
        "report_date": sections.get("report_date", ""),
        "report_id": sections.get("report_id", ""),
        "BUILD_ID": sections.get("BUILD_ID", "B734d"),
        "LOGO_PRIMARY_B64": os.getenv("LOGO_PRIMARY_SRC", "https://make.ki-sicherheit.jetzt/badges/ki-sicherheit-logo-small.png"),
        "TUEV_LOGO_B64": os.getenv("FOOTER_LEFT_LOGO_SRC", "https://make.ki-sicherheit.jetzt/badges/tuev-logo-transparent.png"),
        "report_year": sections.get("report_year", ""),
        "BRANCHE_LABEL": sections.get("BRANCHE_LABEL", ""),
        "UNTERNEHMENSGROESSE_LABEL": sections.get("UNTERNEHMENSGROESSE_LABEL", ""),
        "BUNDESLAND_LABEL": sections.get("BUNDESLAND_LABEL", ""),
        "HAUPTLEISTUNG": sections.get("HAUPTLEISTUNG", ""),
        # dynamic sections - ensure score_gesamt is numeric
        "score_gesamt": sections.get("score_gesamt") or sections.get("score_overall") or sections.get("overall") or 0,
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

    # --- R1-SCORE-DEBUG (temporary, remove after verification) ---
    _r1_gov = sections.get("score_governance", sections.get("CANONICAL_GOVERNANCE", "?"))
    _r1_sec = sections.get("score_sicherheit", sections.get("CANONICAL_SECURITY", "?"))
    _r1_val = sections.get("score_nutzen", sections.get("score_wertschoepfung", "?"))
    _r1_ena = sections.get("score_befaehigung", "?")
    _r1_gesamt = sections.get("score_gesamt", sections.get("CANONICAL_OVERALL", "?"))
    log.debug("R1-SCORE-DEBUG: [%s] gov=%s, sec=%s, val=%s, ena=%s, score_gesamt=%s",
                run_id, _r1_gov, _r1_sec, _r1_val, _r1_ena, _r1_gesamt)

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
    # FIX-Z1C-GESAMT: Skip replacement pairs where the "wrong" value matches
    # score_gesamt. Otherwise "48/100" (correct Gesamtscore) gets replaced
    # with "2/100" (security score), corrupting Management Summary, TOC, etc.
    _cg_pre = int(float(ctx.get('CANONICAL_GOVERNANCE', 0) or 0))
    _cs_pre = int(float(ctx.get('CANONICAL_SECURITY', 0) or 0))
    _gs_pre = int(float(ctx.get('score_gesamt', 0) or 0))
    _z1c_pre = 0
    if _cg_pre > 0 and _cs_pre > 0:
        _z1c_pairs = [(38, _cg_pre), (42, _cs_pre), (32, _cg_pre), (48, _cs_pre)]
        _z1c_pairs = [(_w, _r) for _w, _r in _z1c_pairs if _w != _gs_pre]
        if _gs_pre > 0:
            log.info("[Z+1c-PRE] score_gesamt=%d — skipping pairs where wrong==%d", _gs_pre, _gs_pre)
        for _sk in list(ctx.keys()):
            _sv = ctx.get(_sk, '')
            if not isinstance(_sv, str) or len(_sv) < 50:
                continue
            _changed = False
            for _w, _r in _z1c_pairs:
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

    # V7: Strip emojis from all backend-generated HTML blocks
    _strip_emojis_from_context(ctx)

    # =========================================================================
    # FIX-SCORE-INTERP: Enforce correct Gesamtscore in SCORE_INTERPRETATION_HTML
    # The LLM sometimes confuses the overall score with a dimension sub-score
    # (e.g. Sicherheit=2 shown as "Reifegrad 2/100" instead of overall=48).
    # Also fix "für  analysiert" gap from empty hauptleistung in FINAL_CHECK_INTRO.
    # =========================================================================
    import re as _re_si
    _final_score = int(float(ctx.get('score_gesamt', 0) or 0))
    if _final_score > 0:
        _si_html = ctx.get('SCORE_INTERPRETATION_HTML', '')
        if isinstance(_si_html, str) and _si_html:
            # Replace any wrong "X/100" pattern in the first sentence
            # that doesn't match the actual overall score
            _si_fixed = _re_si.sub(
                r'(\b(?:Score|Gesamtscore|Reifegrad|KI-Score)\s+(?:von\s+)?)\d+(/100)',
                rf'\g<1>{_final_score}\2',
                _si_html
            )
            # Also fix standalone "X/100" at start of sentence context
            _si_fixed = _re_si.sub(
                r'(\()(\d+)(/100\s*[=–—-])',
                lambda m: f'({_final_score}{m.group(3)}' if int(m.group(2)) != _final_score else m.group(0),
                _si_fixed
            )
            if _si_fixed != _si_html:
                ctx['SCORE_INTERPRETATION_HTML'] = _si_fixed
                log.info("[FIX-SCORE-INTERP] Enforced correct score %d in SCORE_INTERPRETATION_HTML", _final_score)

    # FIX-FCI-GAP: Fix "für  analysiert" / "für analysiert" in FINAL_CHECK_INTRO
    _fci = ctx.get('FINAL_CHECK_INTRO', '')
    if isinstance(_fci, str) and _fci:
        _fci_new = _re_si.sub(r'Report\s+für\s+analysiert', 'Report analysiert', _fci)
        _fci_new = _re_si.sub(r'für\s{2,}analysiert', 'analysiert', _fci_new)
        if _fci_new != _fci:
            ctx['FINAL_CHECK_INTRO'] = _fci_new
            log.info("[FIX-FCI-GAP] Fixed empty hauptleistung gap in FINAL_CHECK_INTRO")

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
        # Also remove bare "2." or "3." not in tags (not followed by digits = not EUR thousands)
        _monet = re.sub(r'(?<=>)\s*[23]\.(?!\d)\s*(?=<)', '', _monet)
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
    # X3: Also check NINETY_DAY_PLAN (ROADMAP_90D_HTML excluded per FIX-B22-P4)
    for _x3_key in ('NINETY_DAY_PLAN_HTML',):
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
        'TOOLS_FUNDING_ALIGNMENT_HTML',  # FIX-B43: Hide if only "Keine Daten" placeholder
    ]
    for _y_key in _Y_EMPTY_CHECK_SECTIONS:
        _y_val = ctx.get(_y_key, '')
        if isinstance(_y_val, str) and _y_val:
            _y_text = re.sub(r'<[^>]+>', '', _y_val).strip()
            # FIX-B43: Hide sections with "Keine Daten" placeholder
            if 'Keine Daten' in _y_text:
                ctx[_y_key] = ''
                log.info("[FIX-B43][Y1-4] Hidden placeholder section %s ('Keine Daten')", _y_key)
                continue
            # Remove bare numbers and punctuation to check for real content
            _y_content = re.sub(r'[\d\.\s,;:\-]+', '', _y_text).strip()
            if len(_y_content) < 30:
                ctx[_y_key] = ''
                log.info("[Y1-4] Hidden empty-content section %s (content: %d chars after cleanup)", _y_key, len(_y_content))

    # Y1b: Also fix bare numbered lists in MONETARISIERUNG (keep section but clean items)
    _y_monet = ctx.get('MONETARISIERUNG_HTML', '')
    if isinstance(_y_monet, str) and _y_monet:
        # Remove any <li>, <p>, <div> that contains ONLY a number like "2." or "3."
        # Negative lookahead (?!\d) prevents matching EUR thousands separators like "19.200"
        _y_monet = re.sub(r'<(li|p|div)[^>]*>\s*\d+\.(?!\d)\s*</(li|p|div)>', '', _y_monet, flags=re.I)
        # Remove bare "N." between tags (not followed by digits = not a thousands separator)
        _y_monet = re.sub(r'(?<=>)\s*\d+\.(?!\d)\s*(?=<)', '', _y_monet)
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
    # FIX-Z1C-GESAMT: Skip pairs where "wrong" == score_gesamt (same as PRE fix)
    import re as _re_z1c
    _cg_post = int(float(ctx.get('CANONICAL_GOVERNANCE', 0) or 0))
    _cs_post = int(float(ctx.get('CANONICAL_SECURITY', 0) or 0))
    _gs_post = int(float(ctx.get('score_gesamt', 0) or 0))
    _z1c_post = 0
    if _cg_post > 0 and _cs_post > 0:
        _z1c_post_pairs = [(38, _cg_post, 'Gov'), (42, _cs_post, 'Sec'), (32, _cg_post, 'Gov'), (48, _cs_post, 'Sec')]
        _z1c_post_pairs = [(_w, _r, _l) for _w, _r, _l in _z1c_post_pairs if _w != _gs_post]
        if _gs_post > 0:
            log.info("[Z+1c-POST] score_gesamt=%d — skipping pairs where wrong==%d", _gs_post, _gs_post)
        for _wrong, _right, _label in _z1c_post_pairs:
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
        # FIX-Z1C-GESAMT: Also skip nuclear regex for score_gesamt values
        _z1c_nuke_pairs = [(38, _cg_post), (42, _cs_post)]
        _z1c_nuke_pairs = [(_w, _r) for _w, _r in _z1c_nuke_pairs if _w != _gs_post]
        for _w, _r in _z1c_nuke_pairs:
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
    # FIX-D4: Use project-root-relative path (same pattern as gamechanger_deep_dive.py)
    # to avoid resolving to repo root when env overrides change tpl_path.
    _tpl_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
    html = embed_logos_in_html(html, _tpl_dir)
    # Belt-and-suspenders: catch any remaining relative img src (trust badges, etc.)
    from utils.logo_embedder import embed_all_images_in_html, convert_webp_paths_to_png_base64
    html = embed_all_images_in_html(html, _tpl_dir)
    # Safety net: convert any remaining WebP file path references to PNG base64
    html = convert_webp_paths_to_png_base64(html, _tpl_dir)
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
    # FIX-v715: Brute-force grammar separator before "Schwerpunkte:" in final HTML
    # Three attempts on FINAL_CHECK_INTRO (v7.1.2, v7.1.3, v7.1.4) failed because
    # the text in the PDF does not come (solely) from FINAL_CHECK_INTRO.
    # This regex runs on the FINAL rendered HTML — nothing can undo it.
    # =========================================================================
    _sw_found = 'Schwerpunkte' in html
    log.info("[FIX-v715-GRAMMAR] Reached. HTML length=%d. 'Schwerpunkte' found=%s run=%s",
             len(html), _sw_found, run_id)
    if _sw_found:
        _html_before_sw = html
        html = re.sub(r'(?<![.!?;:,])\s+(Schwerpunkte\s*:)', r'. \1', html)
        if html != _html_before_sw:
            log.info("[FIX-v715-GRAMMAR] Regex applied — period inserted before 'Schwerpunkte:' run=%s", run_id)
        else:
            log.info("[FIX-v715-GRAMMAR] No change needed — punctuation already present before 'Schwerpunkte:' run=%s", run_id)

    # =========================================================================
    # FIX-v7110: LLM-Mathe-Korrektur auf finalem HTML
    # LLMs können nicht rechnen. Wir korrigieren bekannte Fehler deterministisch
    # mit den kanonischen Werten aus dem Business Case (sections dict).
    # Gleicher Mechanismus wie der Schwerpunkte-Fix: Post-Processing auf
    # finalem HTML, direkt vor Puppeteer — nichts kann es rückgängig machen.
    # =========================================================================
    try:
        _canon_opex_m = float(sections.get("CANON_OPEX_MONTH_EUR") or sections.get("OPEX_REALISTISCH_EUR") or 0)
        _canon_capex = float(sections.get("CANON_CAPEX_EUR") or sections.get("CAPEX_REALISTISCH_EUR") or 0)
        _canon_hours = float(sections.get("CANON_HOURS_MONTH") or sections.get("monatsersparnis_stunden") or 0)
        _canon_rate = float(sections.get("CANON_RATE_EUR") or sections.get("stundensatz_eur") or 0)

        if _canon_opex_m > 0 and _canon_hours > 0 and _canon_rate > 0:
            _opex_annual = _canon_opex_m * 12
            _jahresersparnis = _canon_hours * _canon_rate * 12
            _nettonutzen = _jahresersparnis - _canon_capex - _opex_annual
            _netto_ersparnis = _jahresersparnis - _opex_annual  # Brutto minus laufende Kosten

            def _fmt_de_eur(val: float) -> str:
                """Format number with German thousands separator (dot)."""
                return f"{int(val):,}".replace(",", ".")

            _opex_annual_str = _fmt_de_eur(_opex_annual)
            _nettonutzen_str = _fmt_de_eur(_nettonutzen)
            _netto_ersparnis_str = _fmt_de_eur(_netto_ersparnis)
            _opex_m_int = str(int(_canon_opex_m))

            # --- Debug: show HTML context around known wrong values ---
            for _dbg_pat, _dbg_label in [
                (r'.{0,80}4[\.,\s]?110.{0,80}', 'OPEX-4110'),
                (r'.{0,80}36[\.,\s]?840.{0,80}', 'NettoErsparnis-36840'),
                (r'.{0,80}Netto-Ersparnis.{0,120}', 'NettoErsparnis-context'),
            ]:
                for _dbg_i, _dbg_m in enumerate(re.findall(_dbg_pat, html)):
                    log.info("[FIX-v7110-DEBUG] %s[%d]: ...%s...", _dbg_label, _dbg_i, _dbg_m.strip()[:200])

            _html_before_math = html

            # --- FIX 1a: OPEX-Jahreskosten in ROI-Herleitung ---
            # LLM schreibt z.B. "350€/Monat × 12 = 4.110€" → korrigiere auf "4.200€"
            html = re.sub(
                rf'({re.escape(_opex_m_int)}\s*€?\s*/?\s*Monat\s*[×x]\s*12\s*=\s*)[\d.,]+(\s*€)',
                rf'\g<1>{_opex_annual_str}\2',
                html
            )

            # --- FIX 1b: OPEX-Jahreswert als eigenständiger Betrag (Subtraktionskontext) ---
            # "4.110€" oder "4,110€" oder "4110€" → "4.200€"
            # The wrong OPEX annual value appears in multiple places (e.g. step 4 subtraction)
            _wrong_opex_annual = int(_opex_annual) - 90  # LLM typical error: 350*12=4110 instead of 4200
            if _wrong_opex_annual > 0:
                _wrong_opex_fmts = [
                    _fmt_de_eur(_wrong_opex_annual),                    # "4.110"
                    f"{_wrong_opex_annual:,}".replace(",", "."),        # "4.110"
                    f"{_wrong_opex_annual:,}",                          # "4,110"
                    str(_wrong_opex_annual),                            # "4110"
                ]
                for _wf in dict.fromkeys(_wrong_opex_fmts):  # deduplicate, preserve order
                    if _wf in html:
                        html = html.replace(f"{_wf}€", f"{_opex_annual_str}€")
                        html = html.replace(f"{_wf} €", f"{_opex_annual_str} €")

            # --- FIX 2: Netto-Ersparnis in Sofort-Start Zeitersparnis-Box ---
            # HTML structure: <div style="...">VALUE€</div><div ...>Netto-Ersparnis*</div>
            # The value PRECEDES the label (not after), and uses Python :, format (commas)
            # Match: any €-amount in a div immediately before "Netto-Ersparnis"
            _netto_ersparnis_comma = f"{int(_netto_ersparnis):,}".replace(",", ".")  # German thousands separator
            html = re.sub(
                r'(<div[^>]*>)\s*([\d.,]+)\s*€\s*(</div>\s*<div[^>]*>\s*Netto-Ersparnis)',
                rf'\g<1>{_netto_ersparnis_comma}€\3',
                html
            )

            # --- FIX 3: Entscheidungsvorlage "Jährliche Ersparnis" ---
            # Korrigiere auf kanonischen Nettonutzen
            html = re.sub(
                r'(Jährliche Ersparnis:?\s*(?:ca\.?\s*)?)[\d.,]{4,6}(\s*€)',
                rf'\g<1>{_nettonutzen_str}\2',
                html
            )

            # --- FIX 4: Tool-Kosten "400€/Monat" → kanonische OPEX/Monat ---
            # LLM rundet OPEX auf 400€ statt 350€
            html = re.sub(
                r'(?<!\d)400(\s*€\s*/\s*Monat)',
                rf'{_opex_m_int}\1',
                html
            )

            if html != _html_before_math:
                log.info(
                    "[FIX-v7110-MATH] Applied: OPEX/Jahr=%s€, Netto-Ersparnis=%s€, Nettonutzen=%s€ run=%s",
                    _opex_annual_str, _netto_ersparnis_str, _nettonutzen_str, run_id
                )
            else:
                log.info("[FIX-v7110-MATH] No LLM math errors detected in HTML run=%s", run_id)
        else:
            log.info("[FIX-v7110-MATH] Skipped — canonical values incomplete (opex=%.0f, hours=%.0f, rate=%.0f) run=%s",
                     _canon_opex_m, _canon_hours, _canon_rate, run_id)
    except Exception as e:
        log.warning("[FIX-v7110-MATH] Error during math correction (continuing): %s run=%s", str(e)[:200], run_id)

    # =========================================================================
    # FIX-v7110-BC-EUR: Correct EUR values in ROI-Herleitung and Scenario Cards
    # Post-processing on final HTML ensures correct German EUR formatting.
    # The BC engine generates correct values with _eur(), but post-processing
    # steps (sanitizer, healer, budget trimmer) can corrupt German-formatted
    # EUR values (e.g., "19.200€" → "19.80€"). This fix recalculates and
    # re-inserts the correct values using canonical data.
    # Solo-specific: Solo reports are most affected because their lower values
    # (3-4 digit EUR) have fewer thousands separators as checkpoints.
    # =========================================================================
    try:
        _bc_hours = float(sections.get("CANON_HOURS_MONTH") or sections.get("monatsersparnis_stunden") or 0)
        _bc_rate = float(sections.get("CANON_RATE_EUR") or sections.get("stundensatz_eur") or 0)
        _bc_opex_m = float(sections.get("CANON_OPEX_MONTH_EUR") or sections.get("OPEX_REALISTISCH_EUR") or 0)
        _bc_capex = float(sections.get("CANON_CAPEX_EUR") or sections.get("CAPEX_REALISTISCH_EUR") or 0)

        if _bc_hours > 0 and _bc_rate > 0:
            _bc_jahresersparnis = _bc_hours * _bc_rate * 12
            _bc_opex_annual = _bc_opex_m * 12
            _bc_nettonutzen = _bc_jahresersparnis - _bc_capex - _bc_opex_annual

            def _bc_fmt(val: float) -> str:
                return f"{int(val):,}".replace(",", ".")

            _html_before_bc_eur = html

            # FIX 1: Jahresersparnis line — "{hours}h/Monat × {rate}€/h × 12 = {VALUE}€"
            html = re.sub(
                rf'({int(_bc_hours)})h/Monat\s*[×x]\s*({int(_bc_rate)})€/h\s*[×x]\s*12\s*=\s*[\d.,]+€',
                rf'\1h/Monat × \2€/h × 12 = {_bc_fmt(_bc_jahresersparnis)}€',
                html
            )

            # FIX 2: OPEX annual line — structural match for line 3 of ROI-Herleitung
            # "Abzüglich laufende Jahreskosten: {X}€/Monat × 12 = {Y}€"
            # Uses structural pattern (not value-specific) because both X and Y
            # may already be corrupted (e.g., 180→80, 2.160→2.80).
            _j_fmt = _bc_fmt(_bc_jahresersparnis)
            _c_fmt = _bc_fmt(_bc_capex)
            _o_fmt = _bc_fmt(_bc_opex_annual)
            _opex_m_display = _bc_fmt(_bc_opex_m) if _bc_opex_m >= 1000 else str(int(_bc_opex_m))
            if _bc_opex_m > 0:
                html = re.sub(
                    r'(laufende Jahreskosten:\s*)\d[\d.,]*€/Monat\s*[×x]\s*12\s*=\s*[\d.,]+€',
                    rf'\g<1>{_opex_m_display}€/Monat × 12 = {_o_fmt}€',
                    html
                )

            # FIX 2b: OPEX in "So berechne ich" table — correct monthly display
            # "Laufende Kosten (OPEX)</td><td ...>{X} €/Monat"
            if _bc_opex_m > 0:
                html = re.sub(
                    r'(Laufende Kosten \(OPEX\)</td>\s*<td[^>]*>)\s*\d[\d.,]*\s*(€/Monat)',
                    rf'\g<1>{_opex_m_display} \2',
                    html
                )

            # FIX 3: Nettonutzen line — structural match for line 4 of ROI-Herleitung
            # "Nettonutzen: {A}€ - {B}€ - {C}€ = {D}€"
            # All four values may be corrupted, so match any numbers in this structure.
            html = re.sub(
                r'(Nettonutzen:\s*)\d[\d.,]*€\s*-\s*\d[\d.,]*€\s*-\s*\d[\d.,]*€\s*=\s*\d[\d.,]*€',
                rf'\g<1>{_j_fmt}€ - {_c_fmt}€ - {_o_fmt}€ = {_bc_fmt(_bc_nettonutzen)}€',
                html
            )

            # FIX 3b: ROI step 5 — "ROI (berechnet): {nettonutzen}€ / {capex}€ × 100 = {X}%"
            # Ensure numerator matches corrected Nettonutzen
            if _bc_capex > 0:
                _roi_raw = (_bc_nettonutzen / _bc_capex) * 100
                html = re.sub(
                    r'(ROI \(berechnet\):\s*)\d[\d.,]*€\s*/\s*\d[\d.,]*€\s*[×x]\s*100\s*=\s*\d+%',
                    rf'\g<1>{_bc_fmt(_bc_nettonutzen)}€ / {_c_fmt}€ × 100 = {_roi_raw:.0f}%',
                    html
                )

            # FIX 4: Scenario card monthly savings — recalculate from canonical values
            # Cards appear in order: optimistic, realistic, conservative
            _bc_base_savings = _bc_hours * _bc_rate  # Monthly gross savings
            _sc_correct_values = [
                _bc_fmt(_bc_base_savings * 1.3),  # optimistic
                _bc_fmt(_bc_base_savings * 1.0),  # realistic
                _bc_fmt(_bc_base_savings * 0.7),  # conservative
            ]
            _sc_idx = [0]  # mutable counter for closure

            def _fix_sc_savings(m: re.Match) -> str:
                idx = _sc_idx[0]
                _sc_idx[0] += 1
                if idx < len(_sc_correct_values):
                    return f"{m.group(1)}{_sc_correct_values[idx]} {m.group(2)}"
                return str(m.group(0))  # no change if extra matches

            html = re.sub(
                r'(Monatl\.\s*Ersparnis</span>\s*<p[^>]*>)\s*[\d.,]+\s*(€</p>)',
                _fix_sc_savings,
                html
            )

            if html != _html_before_bc_eur:
                log.info("[FIX-v7110-BC-EUR] Corrected EUR values in ROI-Herleitung/Scenario Cards run=%s", run_id)

    except Exception as e:
        log.warning("[FIX-v7110-BC-EUR] Error (continuing): %s run=%s", str(e)[:200], run_id)

    # =========================================================================
    # FIX-v720-F1: Complete truncated ROI derivation sentence
    # LLM sometimes truncates "gedeckelt auf max. 200%)" to "gedeckelt auf max."
    # =========================================================================
    try:
        _html_before_trunc = html
        html = re.sub(
            r'gedeckelt auf max\.(\s*(?:<|"|\'|\)|$))',
            r'gedeckelt auf max. 200%).\1',
            html
        )
        if html != _html_before_trunc:
            log.info("[FIX-v720-F1] Completed truncated ROI sentence run=%s", run_id)
    except Exception as e:
        log.warning("[FIX-v720-F1] Error (continuing): %s run=%s", str(e)[:100], run_id)

    # =========================================================================
    # FIX-v720-F2: Replace hallucinated dates in Förderprogramme section
    # LLM invents dates like "Juni 2025", "Anfang 2025", etc. for
    # "Stand der Einschätzung/Informationen" — replace with actual report date.
    # =========================================================================
    try:
        _report_date_raw = sections.get("report_date", "")
        if _report_date_raw:
            # Convert DD.MM.YYYY to "März 2026" style
            _GERMAN_MONTHS = {
                1: "Januar", 2: "Februar", 3: "März", 4: "April",
                5: "Mai", 6: "Juni", 7: "Juli", 8: "August",
                9: "September", 10: "Oktober", 11: "November", 12: "Dezember"
            }
            try:
                _rd_parts = _report_date_raw.split(".")
                _rd_month = int(_rd_parts[1])
                _rd_year = _rd_parts[2]
                _rd_german = f"{_GERMAN_MONTHS[_rd_month]} {_rd_year}"
            except (IndexError, ValueError, KeyError):
                _rd_german = _report_date_raw  # fallback: use raw date

            _html_before_date = html
            # Match both "Stand der Einschätzung:" and "Stand der Informationen:"
            # with date formats: "Juni 2025", "Anfang 2025", "Ende 2025", "Q2 2025", "März 2026", etc.
            html = re.sub(
                r'(Stand der (?:Einschätzung|Informationen|Daten|Analyse):\s*)(?:Anfang|Mitte|Ende|Q[1-4])?\s*\w*\s*\d{4}',
                rf'\g<1>{_rd_german}',
                html
            )
            if html != _html_before_date:
                log.info("[FIX-v720-F2] Replaced hallucinated date with '%s' run=%s", _rd_german, run_id)
    except Exception as e:
        log.warning("[FIX-v720-F2] Error (continuing): %s run=%s", str(e)[:100], run_id)

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
