# -*- coding: utf-8 -*-
"""
Strategy Report HTML Renderer.

Renders the Jinja2 template with section content and cover metadata.
Shared between routes/strategy.py (HTML/PDF endpoints) and
services/strategy_pipeline.py (post-generation PDF).
"""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)


# B42: Regex to remove misleading cross-program funding totals from S7.
# LLMs sometimes sum up individual programme maximums into an absurd total
# (e.g. "Gesamtförderung: 1.583.250€") that destroys report credibility.
_FUNDING_TOTAL_PATTERN = re.compile(
    r'<(?:p|tr|div)[^>]*>[^<]*'
    r'(?:[Pp]otenzielle\s+)?[Gg]esamt(?:förderung|summe|potenzial)[^<]*'
    r'[\d.,]+\s*(?:€|Euro|EUR)'
    r'[^<]*</(?:p|tr|div)>',
    re.DOTALL,
)


def _strip_funding_total(s7_html: str) -> str:
    """Remove misleading cross-program funding total from S7 HTML."""
    if not s7_html:
        return s7_html
    cleaned, count = _FUNDING_TOTAL_PATTERN.subn('', s7_html)
    if count > 0:
        logger.info("[B42-FUNDING] Removed %d misleading funding total(s) from S7", count)
    return cleaned


def render_strategy_html(sr: Any, db_session: Any) -> str:
    """
    Render strategy report HTML from Jinja2 template.

    Args:
        sr: StrategyReport ORM object (must have .sections, .briefing_id, .updated_at)
        db_session: SQLAlchemy session for loading Briefing + Analysis
    """
    from models import Briefing, Analysis

    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=False)
    template = env.get_template("strategy_report.html")

    briefing = db_session.query(Briefing).filter(Briefing.id == sr.briefing_id).first()
    briefing_data = (briefing.answers if briefing else {}) or {}

    # Load Report 1 data for scores and metadata
    analysis = db_session.query(Analysis).filter(
        Analysis.briefing_id == sr.briefing_id
    ).order_by(Analysis.id.desc()).first()
    report1_meta = (analysis.meta if analysis else {}) or {}
    report1_sections = report1_meta.get("sections", {})

    # Extract score + reifegrad from Report 1
    # FIX-Iv4 + FIX-HOTFIX3: Compute score from stored post-quality value or LIVE recalc.
    _scores = report1_meta.get("scores", {})
    _dim_scores = [
        float(_scores.get("governance", 0) or 0),
        float(_scores.get("security", 0) or 0),
        float(_scores.get("value", 0) or 0),
        float(_scores.get("enablement", 0) or 0),
    ]
    _base_score = round(sum(_dim_scores) / 4) if any(_dim_scores) else 0

    # --- SCORE-DEBUG (temporary, remove after verification) ---
    logger.debug("SCORE-DEBUG-1: [Renderer %s] meta.scores = %r", sr.briefing_id, _scores)
    logger.debug("SCORE-DEBUG-2: [Renderer %s] dimension scores = gov=%s, sec=%s, val=%s, ena=%s",
                    sr.briefing_id, _dim_scores[0], _dim_scores[1], _dim_scores[2], _dim_scores[3])
    logger.debug("SCORE-DEBUG-3: [Renderer %s] calculated = %s, rounded = %d",
                    sr.briefing_id, sum(_dim_scores) / 4 if any(_dim_scores) else 0, _base_score)
    logger.debug("SCORE-DEBUG-KEYS: [Renderer %s] N43_DOD_PASSED=%r, _n43_dod_passed=%r, "
                    "CONSISTENCY_GRADE=%r, _CONSISTENCY_GRADE=%r, _CONSISTENCY_SCORE=%r, "
                    "QUALITY_BONUS=%r, score_gesamt=%r, CANONICAL_OVERALL=%r, scores.overall=%r",
                    sr.briefing_id,
                    report1_sections.get("N43_DOD_PASSED", "MISSING"),
                    report1_sections.get("_n43_dod_passed", "MISSING"),
                    report1_sections.get("CONSISTENCY_GRADE", "MISSING"),
                    report1_sections.get("_CONSISTENCY_GRADE", "MISSING"),
                    report1_sections.get("_CONSISTENCY_SCORE", "MISSING"),
                    report1_sections.get("QUALITY_BONUS", "MISSING"),
                    report1_sections.get("score_gesamt", "MISSING"),
                    report1_sections.get("CANONICAL_OVERALL", "MISSING"),
                    _scores.get("overall", "MISSING"))

    # FIX-HOTFIX3: Prefer stored QUALITY_BONUS (exact value from gpt_analyze)
    # over re-deriving from N43_DOD_PASSED/_CONSISTENCY_GRADE which may be
    # filtered from serializable_sections (underscore-prefixed keys).
    _qb_stored = report1_sections.get("QUALITY_BONUS", None)
    if isinstance(_qb_stored, (int, float)):
        _quality_bonus = int(_qb_stored)
        logger.info("[Strategy-Score] Using stored QUALITY_BONUS=%d", _quality_bonus)
    else:
        # Fallback: re-derive quality bonus (for older analyses without QUALITY_BONUS)
        _dod_passed = report1_sections.get("N43_DOD_PASSED", False) or report1_sections.get("_n43_dod_passed", False)
        # FIX-HOTFIX3b: Read CONSISTENCY_GRADE (without underscore, survives
        # serialization at gpt_analyze.py:18084) and default to 'F'/0 to match
        # calc_quality_bonus defaults (gpt_analyze.py:2099-2100).
        _consistency_grade = str(report1_sections.get("CONSISTENCY_GRADE",
                                  report1_sections.get("_CONSISTENCY_GRADE", "F")))
        _consistency_score = report1_sections.get("_CONSISTENCY_SCORE", 0)
        _quality_bonus = 0
        if _dod_passed:
            if _consistency_grade in ("A", "B") or (isinstance(_consistency_score, (int, float)) and _consistency_score >= 80):
                _quality_bonus = 2
            else:
                _quality_bonus = 1
        logger.info("[Strategy-Score] Re-derived QUALITY_BONUS=%d (dod=%s, grade=%s, score=%s)", _quality_bonus, _dod_passed, _consistency_grade, _consistency_score)
    _live_score = min(_base_score + _quality_bonus, 98)

    # Fallback: also check stored values (for older analyses without dimension scores)
    _stored_candidates = []
    for _key, _src in [
        ("sections.score_gesamt", report1_sections.get("score_gesamt", "")),
        ("sections.CANONICAL_OVERALL", report1_sections.get("CANONICAL_OVERALL", "")),
        ("scores.overall", _scores.get("overall", "")),
    ]:
        try:
            _val = int(float(_src)) if _src not in ("", None) else 0
        except (ValueError, TypeError):
            _val = 0
        if _val > 0:
            _stored_candidates.append((_key, _val))

    _stored_max = max((v for _, v in _stored_candidates), default=0)

    # FIX-HOTFIX3: Use stored max if it matches or exceeds live (covers case where
    # scores.overall was synced post-quality-bonus by FIX-HOTFIX3-SCORE).
    if any(_dim_scores):
        if _stored_max >= _live_score:
            readiness_score = _stored_max
        else:
            readiness_score = _live_score
    else:
        readiness_score = _stored_max  # Legacy data without dimensions → use stored
    logger.info(
        "[Strategy-Score] briefing_id=%s R1-formula dims=%r base=%d bonus=%d live=%d stored_max=%d → using %d (live_preferred=%s)",
        sr.briefing_id, _dim_scores, _base_score, _quality_bonus, _live_score, _stored_max, readiness_score, any(_dim_scores),
    )
    reifegrad_label = report1_sections.get("score_rating", "")
    # --- SCORE-DEBUG (temporary, remove after verification) ---
    logger.debug("SCORE-DEBUG-4: [Renderer %s] score passed to template = %d", sr.briefing_id, readiness_score)
    logger.debug("SCORE-DEBUG-5: [Renderer %s] score_label = %s", sr.briefing_id, reifegrad_label)

    # Reifegrad label: fallback to live calculation if not stored
    if not reifegrad_label and readiness_score > 0:
        try:
            from services.extra_sections import get_score_context
            _size_raw = briefing_data.get("unternehmensgroesse", "klein")
            _sc_ctx = get_score_context(readiness_score, _size_raw, lang="de")
            reifegrad_label = _sc_ctx.get("score_rating", "")
            logger.info("[Strategy-Score] reifegrad_label computed on-demand: %s", reifegrad_label)
        except Exception:
            pass

    # Branche: capitalize for display
    branche_raw = briefing_data.get("branche", "")
    branche_label = branche_raw.title() if branche_raw else ""

    # Research date from report1 or generation date
    research_date = report1_meta.get("research_last_updated", "")
    if not research_date:
        research_date = (sr.updated_at or datetime.now()).strftime("%d.%m.%Y")

    # Segment label — briefing stores "1", "2–10", "11–100" or "solo", "team", "kmu"
    segment_map = {
        # Numeric strings (from briefing form)
        "1": "Einzelunternehmer",
        "2–10": "Kleinunternehmen (2-10 MA)",
        "2-10": "Kleinunternehmen (2-10 MA)",
        "11–100": "KMU (11-250 MA)",
        "11-100": "KMU (11-250 MA)",
        # Canonical keys (from normalization)
        "solo": "Einzelunternehmer",
        "team": "Kleinunternehmen (2-10 MA)",
        "small": "Kleinunternehmen (2-10 MA)",
        "kmu": "KMU (11-250 MA)",
        "medium": "KMU (11-250 MA)",
    }
    # Mitarbeiter count mapping
    mitarbeiter_map = {
        "1": "1",
        "2–10": "2–10",
        "2-10": "2–10",
        "11–100": "11–100",
        "11-100": "11–100",
        "solo": "1",
        "team": "2–10",
        "small": "2–10",
        "kmu": "11–100",
        "medium": "11–100",
    }
    segment_raw = briefing_data.get("unternehmensgroesse", "")
    segment_key = str(segment_raw).strip().lower() if segment_raw else ""
    # Try exact match, then lowercase match, then readable fallback
    segment_label = segment_map.get(str(segment_raw).strip(), "")
    if not segment_label:
        segment_label = segment_map.get(segment_key, "")
    if not segment_label and segment_raw:
        # Readable fallback for unknown values
        segment_label = f"Unternehmen ({segment_raw} Mitarbeiter)"

    # Mitarbeiter: explicit field or derived from unternehmensgroesse
    mitarbeiter = briefing_data.get("mitarbeiter", "")
    if not mitarbeiter and segment_raw:
        mitarbeiter = mitarbeiter_map.get(str(segment_raw).strip(), "")
        if not mitarbeiter:
            mitarbeiter = mitarbeiter_map.get(segment_key, str(segment_raw))

    logger.info(
        "[Strategy-Cover] briefing_id=%s segment_raw=%r → label=%r, mitarbeiter=%r, branche=%r",
        sr.briefing_id, segment_raw, segment_label, mitarbeiter, branche_label,
    )

    # Nächste Schritte: use segment-aware static template if not generated by LLM
    sections = sr.sections or {}
    naechste_schritte = sections.get("naechste_schritte", "")
    if not naechste_schritte:
        from prompts.strategy_prompts import (
            SECTION_TEMPLATE_NAECHSTE_SCHRITTE_SOLO,
            SECTION_TEMPLATE_NAECHSTE_SCHRITTE_TEAM,
        )
        # Solo gets language without "Team" references
        is_solo = segment_raw in ("1", "solo", "freelancer")
        naechste_schritte = (
            SECTION_TEMPLATE_NAECHSTE_SCHRITTE_SOLO if is_solo
            else SECTION_TEMPLATE_NAECHSTE_SCHRITTE_TEAM
        )

    # Load canonical budget values from DB (saved by pipeline after calculation)
    calculated_values = getattr(sr, "calculated_values", None) or {}

    context = {
        # Cover metadata
        "firmenname": briefing_data.get("unternehmen_name", "Ihr Unternehmen"),
        "branche": branche_label,
        "datum": datetime.now().strftime("%d.%m.%Y"),
        "segment": segment_label,
        "mitarbeiter": mitarbeiter,
        "readiness_score": readiness_score,
        "reifegrad_label": reifegrad_label,
        "research_date": research_date,
        "report_id": f"STR-{sr.briefing_id}",
        "build_id": os.getenv("BUILD_ID", ""),
        # Sections
        "exec_summary": sections.get("exec_summary", ""),
        "section_s1": sections.get("S1", ""),
        "section_s2": sections.get("S2", ""),
        "section_s3": sections.get("S3", ""),
        "section_s4": sections.get("S4", ""),
        "section_s5": sections.get("S5", ""),
        "section_s6": sections.get("S6", ""),
        "section_s7": _strip_funding_total(sections.get("S7", "")),
        "section_s8": sections.get("S8", ""),
        "naechste_schritte": naechste_schritte,
    }

    html = str(template.render(**context))

    # Post-process LLM HTML to use CSS design classes (KPI cards, timelines, etc.)
    from services.html_enhancer import enhance_strategy_html
    html = enhance_strategy_html(html)

    # Safety net: enforce canonical budget values in final HTML
    if calculated_values:
        html = _enforce_budget_values(html, calculated_values, sr.briefing_id)

    return html


# =============================================================================
# SAFETY NET: Enforce canonical budget values in HTML
# =============================================================================

def _enforce_budget_values(html: str, cv: Dict[str, str], briefing_id: int) -> str:
    """
    Safety net: Replace LLM-hallucinated budget/ROI/phase values with
    canonical values from the calculator.

    Targets three table patterns commonly generated by the LLM:
    1. ROI scenario table rows (Konservativ/Realistisch/Optimistisch)
    2. Phase budget table rows (Phase 1/2/3)
    3. Gesamtinvestition in table cells
    """
    fixes = 0

    # --- ROI scenario rows ---
    # Pattern: table row containing scenario keyword + a percentage + months
    roi_map = {
        "onservativ": ("roi_konservativ", "breakeven_konservativ"),
        "ealistisch": ("roi_realistisch", "breakeven_realistisch"),
        "ptimistisch": ("roi_optimistisch", "breakeven_optimistisch"),
    }
    for keyword, (roi_key, be_key) in roi_map.items():
        roi_val = cv.get(roi_key, "")
        be_val = cv.get(be_key, "")
        if not roi_val or not be_val:
            continue

        # Find <tr> containing the keyword and replace % value + month value
        def _fix_roi_row(m: re.Match, _roi=roi_val, _be=be_val) -> str:
            row = m.group(0)
            original = row
            # Replace percentage: any number followed by optional space + %
            row = re.sub(
                r'(?<=>)\s*-?[\d.,]+\s*%',
                f'{_roi}\u202f%',
                row,
                count=1,
            )
            # Replace break-even month: "Monat X" or just a number in a later <td>
            row = re.sub(
                r'(Monat\s*)\d+',
                rf'\g<1>{_be}',
                row,
            )
            return row

        html, n = re.subn(
            rf'<tr[^>]*>(?:(?!</tr>).)*{keyword}(?:(?!</tr>).)*</tr>',
            _fix_roi_row,
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )
        fixes += n

    # --- Phase budget rows ---
    phase_map = {
        r"Phase\s*1": "budget_phase_1",
        r"Phase\s*2": "budget_phase_2",
        r"Phase\s*3": "budget_phase_3",
    }
    for pattern, key in phase_map.items():
        val = cv.get(key, "")
        if not val:
            continue

        def _fix_phase_row(m: re.Match, _val=val) -> str:
            row = m.group(0)
            # Replace Euro amount: digits with optional dots/commas + optional space + €
            row = re.sub(
                r'[\d]+(?:[.,]\d{3})*(?:[.,]\d+)?\s*€',
                f'{_val}\u202f€',
                row,
                count=1,
            )
            return row

        html, n = re.subn(
            rf'<tr[^>]*>(?:(?!</tr>).)*{pattern}(?:(?!</tr>).)*</tr>',
            _fix_phase_row,
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )
        fixes += n

    # --- Gesamtinvestition in table rows ---
    gesamt_val = cv.get("budget_gesamt_jahr1", "")
    if gesamt_val:
        def _fix_gesamt_row(m: re.Match) -> str:
            row = m.group(0)
            row = re.sub(
                r'[\d]+(?:[.,]\d{3})*(?:[.,]\d+)?\s*€',
                f'{gesamt_val}\u202f€',
                row,
                count=1,
            )
            return row

        html, n = re.subn(
            r'<tr[^>]*>(?:(?!</tr>).)*[Gg]esamt(?:investition|budget|kosten)?(?:(?!</tr>).)*</tr>',
            _fix_gesamt_row,
            html,
            flags=re.DOTALL,
        )
        fixes += n

    if fixes > 0:
        logger.info(
            "[Strategy %s] Safety net: enforced %d canonical value replacements",
            briefing_id, fixes,
        )

    return html
