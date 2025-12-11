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
from services.report_validator import GENERIC_LLM_LEAK_PHRASES, remove_leak_phrases_from_html

log = logging.getLogger(__name__)

# N3: Pre-compute a single regex pattern for O(n) leak detection instead of O(n*phrases)
# This matches ANY leak phrase in a single pass through the HTML
_LEAK_PATTERN = re.compile(
    '|'.join(re.escape(p) for p in GENERIC_LLM_LEAK_PHRASES),
    re.IGNORECASE
)


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
            # Remove sentences containing this phrase
            # Use simple pattern to avoid catastrophic backtracking
            pattern = rf'[^.!?]*{re.escape(phrase)}[^.!?]*[.!?]?\s*'
            try:
                matches = len(re.findall(pattern, cleaned, re.IGNORECASE))
                if matches > 0:
                    cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
                    removed_count += matches
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

def _env() -> Environment:
    tpl_dir = Path(os.getenv("REPORT_TEMPLATE_DIR", "templates"))
    env = Environment(
        loader=FileSystemLoader(str(tpl_dir)),
        autoescape=select_autoescape(["html","xml"]),
        undefined=Undefined,  # ✅ Fixed: Use Undefined class instead of None
        trim_blocks=True, lstrip_blocks=True,
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
    """
    # Language-aware template selection
    lang = (generated_sections or {}).get("LANG", "de")
    if lang == "en":
        default_tpl = "templates/pdf_template_en.html"
        log.info(f"🌐 Using English template for report {run_id}")
    else:
        default_tpl = "templates/pdf_template.html"

    tpl_path = os.getenv("REPORT_TEMPLATE_PATH", default_tpl)
    # Allow language-specific override via env
    if lang == "en" and os.getenv("REPORT_TEMPLATE_PATH_EN"):
        tpl_path = os.getenv("REPORT_TEMPLATE_PATH_EN")

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

    # Mark HTML sections as safe (prevent escaping)
    safe_sections = {}
    for key, value in sections.items():
        if isinstance(value, str) and key.endswith('_HTML') and '<' in value:
            safe_sections[key] = Markup(value)
            log.debug(f"[RENDER] Marked section '{key}' as safe HTML")
        else:
            safe_sections[key] = value
    sections = safe_sections

    # Safe defaults with FIXED UTF-8
    ctx = {
        "LANG": sections.get("LANG", "de"),
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

    # Log what we're rendering (for debugging)
    log.info(f"🎨 Rendering report {run_id} with {len(sections)} sections")
    log.debug(f"Sections available: {list(sections.keys())}")

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
            r'\{PAYBACK_MONTHS\}': str(sections.get('PAYBACK_MONTHS', '')),
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
            r'\{\{\s*PAYBACK_MONTHS\s*\}\}': str(sections.get('PAYBACK_MONTHS', '')),
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
    # SPRINT N2.5: Final leak phrase safety check (defensive)
    # =========================================================================
    # This is the LAST line of defense before PDF rendering.
    # N2.5: Using encapsulated function that NEVER blocks PDF dispatch
    log.info(f"[RENDER] Before final leak cleanup: len(html)={len(html)} for run={run_id}")
    html = final_leak_cleanup(html, run_id=run_id)
    log.info(f"[RENDER] After final leak cleanup: len(html)={len(html)} for run={run_id}")

    return {"html": html, "meta": meta or {}}
