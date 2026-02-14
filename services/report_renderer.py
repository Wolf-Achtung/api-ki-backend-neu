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
from services.report_validator import GENERIC_LLM_LEAK_PHRASES, remove_leak_phrases_from_html
from services.html_sanitizer import sanitize_en_locale_tokens
from services.lang_utils import normalize_lang
from services.i18n import ui as ui_factory, ui_for_segment
from services.locale_rewriter import apply_locale_v2
from services.debug_503d import build_debug_503d_attachments, build_debug_503d_summary, is_debug_render_enabled

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

    # Mark HTML sections as safe (prevent escaping)
    safe_sections = {}
    for key, value in sections.items():
        if isinstance(value, str) and key.endswith('_HTML') and '<' in value:
            safe_sections[key] = Markup(value)
            log.debug(f"[RENDER] Marked section '{key}' as safe HTML")
        else:
            safe_sections[key] = value
    sections = safe_sections
    
    # [FINAL-SANITIZER] Last-pass fixes after ALL injections
    sections = final_sanitize(sections)
    # Safe defaults with FIXED UTF-8
    # TEIL 3.1.4.x: Force LANG to detected value (no fallback to sections)
    ctx: Dict[str, Any] = {
        "LANG": "en" if is_en else "de",  # FORCED, not from sections
        "OWNER_NAME": sections.get("OWNER_NAME", os.getenv("OWNER_NAME", "KI-Sicherheit.jetzt")),  # ✅ FIXED
        "report_date": sections.get("report_date", ""),
        "report_id": sections.get("report_id", ""),
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

    html = env.get_template(tpl_name).render(**ctx)

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
    # FIX-514: Quick-Wins Non-Empty Gate (pre-PDF, fail-closed in STRICT)
    # Ensures Quick-Wins section is never an empty page in the PDF.
    # =========================================================================
    try:
        release_strict = os.getenv("RELEASE_STRICT_MODE", "0") in ("1", "true", "True")
        qw_cards = html.count('class="quick-win')
        qw_marker = html.count('data-qw-json-rendered="true"')
        qw_indicator = max(qw_cards, qw_marker)
        # Extract Quick-Wins text length from rendered HTML
        import re as _re
        qw_section_match = _re.search(
            r'class="quick-wins-container"[^>]*>(.*?)</div>\s*</div>',
            html, _re.DOTALL
        )
        qw_text_len = len(qw_section_match.group(1)) if qw_section_match else 0
        # Fallback: if no container match, use card count as proxy
        if qw_text_len == 0 and qw_indicator > 0:
            qw_text_len = qw_indicator * 100  # Estimate

        qw_non_empty = qw_indicator >= 3 and qw_text_len > 300
        log.info(
            "[FIX-514][QW] non_empty=%s cards=%d len=%d",
            str(qw_non_empty).lower(), qw_indicator, qw_text_len
        )

        if not qw_non_empty and release_strict:
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
