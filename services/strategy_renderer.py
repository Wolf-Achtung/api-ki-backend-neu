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
    ).first()
    report1_meta = (analysis.meta if analysis else {}) or {}
    report1_sections = report1_meta.get("sections", {})

    # Extract score + reifegrad from Report 1
    # FIX-Iv2: Collect ALL available score sources and pick the highest (post-bonus).
    # R1 cover uses sections["score_gesamt"] which includes the quality bonus (+2).
    _score_candidates = []
    for _key, _src in [
        ("sections.score_gesamt", report1_sections.get("score_gesamt", "")),
        ("sections.CANONICAL_OVERALL", report1_sections.get("CANONICAL_OVERALL", "")),
        ("scores.overall", report1_meta.get("scores", {}).get("overall", "")),
    ]:
        try:
            _val = int(float(_src)) if _src not in ("", None) else 0
        except (ValueError, TypeError):
            _val = 0
        if _val > 0:
            _score_candidates.append((_key, _val))

    # Use the highest score (post-bonus is always >= pre-bonus)
    if _score_candidates:
        _score_candidates.sort(key=lambda x: x[1], reverse=True)
        readiness_score = _score_candidates[0][1]
    else:
        readiness_score = 0
    logger.info(
        "[Strategy-Score] briefing_id=%s candidates=%r → using %r",
        sr.briefing_id, _score_candidates, readiness_score,
    )
    reifegrad_label = report1_sections.get("score_rating", "")

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
        "section_s7": sections.get("S7", ""),
        "section_s8": sections.get("S8", ""),
        "naechste_schritte": naechste_schritte,
    }

    html = str(template.render(**context))

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
