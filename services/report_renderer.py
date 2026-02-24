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
        "BUILD_ID": sections.get("BUILD_ID", "B734e"),
        "TUEV_LOGO_B64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAABAAAAAQACAYAAAB/HSuDAAEAAElEQVR4nOz9edAk530feH5/z5NZVe/RJ9AHunESJC6eECkRJHVQ1mUdtrSivB5Ztne9u7Ez9kx4wmOPd9cTO471zkxs7MixjnWsLznGO9QRO56wR7ZkyZIlUrxvEuABAiQAEuhuHI2++70qM5/fb//IfKqeet6s9+1uoNnoru+no+KtqryzMrPz93uOlL/xN/4GiIiIiIiIiOjW5m70ChARERERERHR9ccEABEREREREdECYAKAiIiIiIiIaAEwAUBERERERES0AJgAICIiIiIiIloATAAQERERERERLQAmAIiIiIiIiIgWQGFmN3odiIiIiIiIiOg6Yw0AIiIiIiIiogXABAARERERERHRAmACgIiIiIiIiGgBMAFAREREREREtACYACAiIiIiIiJaAEwAEBERERERES0AJgCIiIiIiIiIFkBhZjd6HYiIiIiIiIjoOmMNACIiIiIiIqIFwAQAERERERER0QJgAoCIiIiIiIhoATABQERERERERLQAmAAgIiIiIiIiWgBMABAREREREREtACYAiIiIiIiIiBZA4RxzAERERERERES3Okb/RERERERERAuACQAiIiIiIiKiBcAEABEREREREdECYAKAiIiIiIiIaAEwAUBERERERES0AJgAICIiIiIiIloATAAQERERERERLYDCzG70OhARERERERHRdcYaAEREREREREQLgAkAIiIiIiIiogXABAARERERERHRAmACgIiIiIiIiGgBMAFAREREREREtACYACAiIiIiIiJaAEwAEBERERERES0AJgCIiIiIiIiIFgATAEREREREREQLgAkAIiIiIiIiogXABAARERERERHRAmACgIiIiIiIiGgBMAFAREREREREtACYACAiIiIiIiJaAEwAEBERERERES0AJgCIiIiIiIiIFgATAEREREREREQLgAkAIiIiIiIiogXABAARERERERHRAmACgIiIiIiIiGgBMAFAREREREREtACYACAiIiIiIiJaAEwAEBERERERES2AQkRu9DoQERERERER0XXGGgBEREREREREC4AJACIiIiIiIqIFwAQAERERERER0QJgAoCIiIiIiIhoATABQERERERERLQAmAAgIiIiIiIiWgBMABAREREREREtgMLMbvQ6EBEREREREdF1xhoARERERERERAuACQAiIiIiIiKiBcAEABEREREREdECYAKAiIiIiIiIaAEwAUBERERERES0AJgAICIiIiIiIloATAAQERERERERLYBCxN/odSAiIiIiIiKi64w1AIiIiIiIiIgWABMARERERERERAuACQAiIiIiIiKiBcAEABEREREREdECYAKAiIiIiIiIaAEwAUBERERERES0AJgAICIiIiIiIloABaA3eh2IiIiIiIiI6Dq7ggTAbpUEmEAgIiIiIiIieqNjEwAiIiIiIiKiBcAEABEREREREdECYAKAiIiIiIiIaAEwAUBERERERES0AJgAICIiIiIiIloATAAQERERERERLYDitecAmEMgIiIiIiIieqNj9E5ERERERES0AJgAICIiIiIiIloATAAQERERERERLQAmAIiIiIiIiIgWABMARERERERERAuACQAiIiIiIiKiBcAEABEREREREdECKDzkRq8DERERERER0XWnu4S/Zva9WZEbhDUAiIiIiIiIiBYAEwBEREREREREC4AJACIiIiIiIqIFwAQAERERERER0QJgAoCIiIiIiIhoATABQERERERERItqoR6LxwQAERERERERLapb+7l/mWK35yASERERERERLQKRWztAZg0AIiIiIiIiogXABAARERERERHRAmACgIiIiIiIiGgBMAFAREREREREtACYACAiIiIiIiJaAEwAEBERERERES0AJgCIiIiIiIiIFgATAEREREREREQLgAkAIiIiIiIiogXABAARERERERHRAmACgIiIiIiIiGgBMAFAREREREREtACYACAiIiIiIiJaAEwAEBERERERES0AJgCIiIiIiIiIFkAhIjd6HYiIiIiIiIjoOmMNACIiIiIiIqIFwAQAERERERER0QJgAoCIiIiIiIhoATABQERERERERLQAmAAgIiIiIiIiWgBMABAREREREREtACYAiIiIiIiIiBYAEwBEREREREREC4AJACIiIiIiIqIFwAQAERERERER0QJgAoCIiIiIiIhoATABQERERERERLQAmAAgIiIiIiIiWgBMABAREREREREtACYAiIiIiIiIiBZAcaNXgIhunNFotONwM/serQkREREREV1vrAFAREREREREtACYACAiIiIiIiJaAEwAEBERERERES0AJgCIiIiIiIiIFgATAEREREREREQLgAkAIkrJjV4BIiIiIiK6PpgAIKIUn/tHRERERHSLKkRY4Ee0qMbj8Y1eBSIiIiIi+h5hDQAiIiIiIiKiBcAEABEREREREdECYAKAiIiIiIiIaAEwAUBERERERES0AJgAICIiIiIiIloATAAQERERERERLQAmAIiIiIiIiIgWABMARERERERERAuACQAiIiIiIiKiBcAEABEREREREdECYAKAiIiIiIiIaAEwAUBERERERES0AJgAICIiIiIiIloATAAQERERERERLQAmAIiIiIiIiIgWABMARERERERERAuACQAiIiIiIiKiBcAEABEREREREdECYAKAiIiIiIiIaAEwAUBERERERES0AJgAICIiIiIiIloATAAQERERERERLQAmAIiIiIiIiIgWABMARERERERERAuACQAiIiIiIiKiBcAEABEREREREdECYAKAiIiIiIiIaAEwAUBERERERES0AJgAICIiIiIiIloATAAQERERERERLQAmAIiIiIiIiIgWQOFR3Oh1ICIiIiIiIqLrjDUAiIiIiIiIiBYAEwBEREREREREC4AJACIiIiIiIqIFwAQAERERERER0QJgAoCIiIiIiIhoATABQERERERERLQAmAAgIiIiIiIiWgCFOb3R60BERERERERE1xlrABAREREREREtACYAiIiIiIiIiBYAEwBEREREREREC4AJACIiIiIiIqIFwAQAERERERER0QJgAoCIiIiIiIhoATABQERERERERLQACrEbvQpEREREREREdL2xBgARERERERHRAmACgIiIiIiIiGgBMAFAREREREREtACYACAiIiIiIiJaAEwAEBERERERES0AJgCIiIiIiIiIFgATAEREREREREQLoDC50atARERERERERNcbawAQERERERERLQAmAIiIiIiIiIgWABMARERERERERAuACQAiIiIiIiKiBcAEABEREREREdECYAKAiIiIiIiIaAEwAUBERERERES0AJgAICIiIiIiIloATAAQERERERERLQAmAIiIiIiIiIgWABMARERERERERAuACQAiIiIiIiKiBcAEABEREREREdECYAKAiIiIiIiIaAEwAUBERERERES0AAox3XEEk51nILbzcE7P6Tk9p+f0nJ7Tc3pOz+k5Pafn9Jye09/46VkDgIiIiIiIiGgBMAFAREREREREtACYACAiIiIiIiJaAEwAEBERERERES0AJgCIiIiIiIiIFgATAEREREREREQLgAkAIiIiIiIiogVQwPkdR9jlMYK7jsDpOT2n5/ScntNzek7P6Tk9p+f0nJ7Tc/obPz1rABAREREREREtACYAiIiIiIiIiBYAEwBEREREREREC4AJACIiIiIiIqIFwAQAERERERER0QJgAoCIiIiIiIhoATABQERERERERLQACgvhRq8DEREREREREV1nrAFAREREREREtACYACAiIiIiIiJaAEwAEBERERERES0AJgCIiIiIiIiIFgATAEREREREREQLgAkAIiIiIiIiogXABAARERERERHRAijgmAMgIiIiIiIiutUx+iciIiIiIiJaAEwAEBERERERES0AJgCIiIiIiIiIFgATAEREREREREQLgAkAIiIiIiIiogXABAARERERERHRAmACgIiIiIiIiGgBFA5yo9eBiIiIiIiIiK4z1gAgIiIiIiIiWgBMABAREREREREtACYAiIiIiIiIiBYAEwBEREREREREC4AJACIiIiIiIqIFwAQAERERERER0QJgAoCIiIiIiIhoARQKu9HrQERERERERETXGWsAEBERERERES0AJgCIiIiIiIiIFgATAEREREREREQLgAkAIiIiIiIiogXABAARERERERHRAmACgIiIiIiIiGgBMAFAREREREREtAAKsRu9CkRERERERER0vbEGABEREREREdECYAKAiIiIiIiIaAEwAUBERERERES0AJgAICIiIiIiIloATAAQERERERERLQAmAIiIiIiIiIgWABMARERERERERAuACQAiIiIiIiKiBcAEABEREREREdECYAKAiIiIiIiIaAEwAUBERERERES0AJgAICIiIiIiIloATAAQERERERERLQAmAIiIiIiIiIgWABMARERERERERAugMNEbvQ5EREREREREdJ2xBgARERERERHRAmACgIiIiIiIiGgBMAFAREREREREtACYACAiIiIiIiJaAEwAEBERERERES0AJgCIiIiIiIiIFgATAEREREREREQLoIDe6FUgIiIiIiIiouuNNQCIiIiIiIiIFgATAEREREREREQLgAkAIiIiIiIiogXABAARERERERHRAmACgIiIiIiIiGgBMAFAREREREREtACYACAiIiIi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obFa9qUCqXpdqjkTgEJRtM69cy3Xr9z3zWIsZnqd45cC1vD9CbuwY4PqfAhAq+c/Otj48436gZgKF3wCFxUAJvt4Q5RX9X9ZKWSyDWWp1bHQHrLjx+O1rzkQXNnH2j7xvAwVWEuJFBR0vOmY2AgxNB7ChI3bM9neScbHsSAXed4UAMM+0NE19VwI7GXVDaZV99gwkSwTmMKS3CNUgPGg4rEIA1ANJXSv8bxrampeXgwMw6+usjM229kNg6Zqamq+Y8kjg8fOXYBZtQAaF0w2W8CtP4Nce/mn5528s+bCeGPGazlv+Mmbcn6TguFwZYnR/F0InltmxxawWiSHmqSq0Bl+loBjly6v24qrWxhPCsAvPBtl8pbpras+L2Aw89gr653rkUuLN9y+1bw0FACT3jHrMdk1304rhqsZwpufz7XNh5tyw7fM2kqm9ee5yXE2UWrzeb6gE05kN6YAuImDrfQSet4VANfw+zH2/Q3eG9/PS8nXpqam5qWIJ8BZM1Q+rkXtAVBT8zLFE8PbejHxncRmXggvt1jRG/XKeLn1V01NTU1NTc13PrUCoKampuY7hFpgvTrqfqqpqampqal5uVIrAGpqampqviOpBf2ampqampqamnFq/9+ampqampqampqampqampcBtQKgpqampqampqampqampuZlQK0AqKmpqampqampqampqal5GVArAGpqampqampqampqampqXgbUCoCampqampqampqampqampcBtQKgpqampqampqampqampuZlQK0AqKmpqampqampqampqal5GVArAGpqampqampqampqampqXgbYF7sBNTU1NS8UpOPPlV6cdtTU1Lz8+Haff260/d/u519TU1PznULtAVBTU1NTU1NTU1NTU1NT8zKgVgDU1NTU1NTU1NTU1NTU1LwMqBUANTU1NTU1NTU1NTU1NTUvAyxEN/9UTU1NzUuQyRjSyRjTVZ/f9IWXGzLxfBOdsE68T5Pfr6l5+fDtPv/caPsnn3+7nf+LTz3/1tTUvDjUHgA1NTU1NTU1NTU1NTU1NS8DagVATU1NTU1NTU1NTU1NTc3LgFoBUFNTU1NTU1NTU1NTU1PzMsC+2A2oqampeaHgiZhTqetQ19TUvEB8p80/m8X8T/Kddv41NTU1367UHgA1NTU1NTU1NTU1NTU1NS8Dag+Ampqampqa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WrduXXryySd/sSiKPb7whS/4Og291+e9CdPgsiliSUVczjnnNRRqJ4D3ZQBgDREZGughHqOrA2nP24PacIiGSvN9bQSbaKhvlQZAtd8GRETGkJh+nrut6ofJoCo9qYUjS6oXV5al6XQ60ul0uF5Qp0/H19DuTJmpqXEaH1/r1657WqampjA11X5+mqZyw/U3bGlINxr7MSuj914IQQjCzFKWHq97/euMc3a96/eZko20cPqZZ55+3XXXHz42NuatNbUegXhUmRACwD7yyCNur7324Fe96lVHlaWHiOCGG258NpxFURQyXgvN8qEYje8Xww9d/1uwjQR1Fgb6gnr1S88ZJO32lGm3p9BuT3G7PSXx/51OG51OW8bHx2l8fJzq5xZNTE7QxMQkJiYm7MTEBAEg62wWfMC11167tR4/h+mdE/Fn0eHomBn1YmqVRKK+s4kavwtUx7mcmJzAgw89aEWEzj77Jd9717vetffnPvdZ3xR53I4OgObzjhkgBkL9CgCWCByzh44/4XjDgWGsQZ7n653/LX1+KoqibC/URakoyjYjhIAkcdh99z1+8/vf//7SRYsWSZZlJs9zWOsEVUqoRR3hmjNnDj/22OOnERFckqAsParazwLGbJsa41qfDz74XmS/UYcNNKI48XMREWbuT0wrw4O5qgWHBGEAIUnSaBA4AIHFV5NqY2EJBYDnbe44RQT//d//LUni6hIAtiDDEtXYhJmELGpDKGYbVLvYSw1uTribKd0OfRGruM9Ys2Zt+oY3vP6V11133feCD+iUHqOjo/Cl36gQY5xwxyoFs5kT8Isuuqhf9G9M2hhnr667Mf5nq792U+SuGUnluvY/GnwbFdTbBPHYN+ulSUSE+s4PyvOc0Y/+lt12J57PuI6eACCActasEfI+oCjKzPsyGGMLInq8LMtkyRFLYgr55hKj2/F8NNPcDapyElhrQERJnufP5HhMS+lLfPWrX72EOciuu+7KviwpMBvYaj9arRZWrVqFJEnwjne84/TvfeeiJ5LEwfuAqlpnuxKj2XHeVHmLWAIZSjCohv9MiMY/MBhdj6n9vdKD2jEVADTvJdSfifehmRXgmYOrMik4lKWXsigsM7fIVHXrW0mzdKcZKY/HKm4/1PowCapjGe/tKGzZzGZgALJq1aqk2+1i0cJFeOc733n8eV/56jX33nvPwN+G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",
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
    # FIX-B734e: Apply grid sanitizer to ALL _HTML sections globally.
    # Previously only 8 sections were listed — many sections with 3+ column
    # grids were missed, causing Buchstabensalat in Puppeteer PDF output.
    _grid_fix_count = 0
    for _gs in list(ctx.keys()):
        if not _gs.endswith('_HTML'):
            continue
        _gv = ctx.get(_gs, '')
        if isinstance(_gv, str) and len(_gv) > 100:
            _gv_new = sanitize_grid_layouts(_gv, _gs)
            if _gv_new != _gv:
                ctx[_gs] = _gv_new
                _grid_fix_count += 1
    if _grid_fix_count > 0:
        log.info("[GRID-SANITIZER] Fixed %d sections with multi-column grids", _grid_fix_count)

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
