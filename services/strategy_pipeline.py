# -*- coding: utf-8 -*-
"""
Strategy Report Pipeline Orchestrator (Report 3).

Coordinates research, budget calculation, and section generation
for the KI-Strategiebericht.

Pipeline order:
1. Research + Budget-Calc (parallel)
2. S1 + S2 (parallel)
3. S3 (needs S2)
4. S4 (needs S3)
5. S5 (needs S3, S4)
6. S6 (needs S3-S5)
7. S7 + S8 (parallel)
8. Executive Summary (needs all sections, via Claude)
"""
from __future__ import annotations

import asyncio
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.live_research import execute_research
from services.strategy_budget import calculate_strategy_budget

logger = logging.getLogger(__name__)


# =============================================================================
# MAIN PIPELINE
# =============================================================================

async def generate_strategy_report(
    briefing_id: int,
    briefing_data: Dict[str, Any],
    strategy_questions: Dict[str, Any],
    report1_data: Dict[str, Any],
    report2_data: Dict[str, Any],
    db_session: Any,
) -> Dict[str, str]:
    """
    Main function: Generates the entire strategy report.

    Args:
        briefing_id: Briefing ID
        briefing_data: Briefing answers dict
        strategy_questions: Strategy questions dict (S1-S10)
        report1_data: Report 1 analysis meta dict
        report2_data: Report 2 / gamechanger data (may be empty)
        db_session: SQLAlchemy session

    Returns:
        Dict of section keys to HTML content
    """
    start_time = time.time()
    sections: Dict[str, str] = {}

    try:
        # === PHASE 1: Research + Budget Calculation (parallel) ===
        _update_status(db_session, briefing_id, "researching")

        handlungsfelder = _derive_handlungsfelder(report1_data, report2_data)
        logger.info("[Strategy %d] Handlungsfelder: %s", briefing_id, handlungsfelder)

        research_task = execute_research(briefing_data, strategy_questions, handlungsfelder)
        budget_task = asyncio.to_thread(
            calculate_strategy_budget,
            briefing_data,
            strategy_questions,
            handlungsfelder,
            report1_data.get("business_case", {}),
        )

        research_context, budget = await asyncio.gather(research_task, budget_task)

        research_duration = time.time() - start_time
        logger.info("[Strategy %d] Research + Budget: %.1fs", briefing_id, research_duration)

        # Cache research + budget in DB
        _save_intermediate(db_session, briefing_id, research_context, budget.to_dict())

        # === PHASE 2: Section Generation ===
        _update_status(db_session, briefing_id, "generating")

        # Shared context for all sections
        report1_sections = report1_data.get("sections", {})
        # FIX-Iv4: Compute score LIVE from dimension scores + quality bonus.
        # meta["sections"] is serialized BEFORE quality bonus in gpt_analyze.py,
        # so stored score_gesamt = pre-bonus. Recalculate to match R1 cover.
        _r1_scores = report1_data.get("scores", {})
        # Match R1 formula exactly: round((gov + sec + val + ena) / 4)
        # Use float() not int(float()) to avoid truncation-induced rounding errors
        _dim_vals = [
            float(_r1_scores.get("governance", 0) or 0),
            float(_r1_scores.get("security", 0) or 0),
            float(_r1_scores.get("value", 0) or 0),
            float(_r1_scores.get("enablement", 0) or 0),
        ]
        # Always divide by 4 (same as R1: scores["overall"] = round(sum/4))
        _base = round(sum(_dim_vals) / 4) if any(_dim_vals) else 0

        _dod_ok = report1_sections.get("N43_DOD_PASSED", False) or report1_sections.get("_n43_dod_passed", False)
        _cg = str(report1_sections.get("_CONSISTENCY_GRADE", "F"))
        _cs = report1_sections.get("_CONSISTENCY_SCORE", 0)
        _qb = 0
        if _dod_ok:
            _qb = 2 if (_cg in ("A", "B") or (isinstance(_cs, (int, float)) and _cs >= 80)) else 1
        _live = min(_base + _qb, 98)

        # Fallback: stored values (for older analyses)
        _stored = []
        for _key, _src in [
            ("sections.score_gesamt", report1_sections.get("score_gesamt", "")),
            ("sections.CANONICAL_OVERALL", report1_sections.get("CANONICAL_OVERALL", "")),
            ("scores.overall", _r1_scores.get("overall", "")),
        ]:
            try:
                _v = int(float(_src)) if _src not in ("", None) else 0
            except (ValueError, TypeError):
                _v = 0
            if _v > 0:
                _stored.append((_key, _v))
        _stored_max = max((v for _, v in _stored), default=0)
        # FIX-Iv4b: Prefer live calculation when dimension data exists.
        # max(live, stored) is wrong: stored score_gesamt can be post-bonus
        # from an older formula (int(float()) rounding), causing stale values
        # to override the correct live calculation.
        if any(_dim_vals):
            _score = _live  # Dimension data present → trust live calc
        else:
            _score = _stored_max  # Legacy data without dimensions → use stored
        logger.info("[Strategy %d] Score: R1-formula dims=%r base=%d bonus=%d live=%d stored_max=%d → using %d (live_preferred=%s)",
                    briefing_id, _dim_vals, _base, _qb, _live, _stored_max, _score, any(_dim_vals))

        # Reifegrad label: fallback to live calculation if not stored
        _reifegrad_label = report1_sections.get("score_rating", "")
        if not _reifegrad_label and _score > 0:
            try:
                from services.extra_sections import get_score_context
                _size_raw = briefing_data.get("unternehmensgroesse", "klein")
                _sc_ctx = get_score_context(_score, _size_raw, lang="de")
                _reifegrad_label = _sc_ctx.get("score_rating", "")
                logger.info("[Strategy %d] reifegrad_label computed on-demand: %s", briefing_id, _reifegrad_label)
            except Exception:
                pass

        base_context = {
            "branche": (briefing_data.get("branche", "") or "").title(),
            "segment": _segment_label(briefing_data.get("unternehmensgroesse", "")),
            "mitarbeiter": briefing_data.get("mitarbeiter", ""),
            "bundesland": briefing_data.get("bundesland", ""),
            "firmenname": briefing_data.get("unternehmen_name", "Ihr Unternehmen"),
            "readiness_score": _score,
            "reifegrad": _reifegrad_label,
            "reifegrad_label": _reifegrad_label,
            # Strategy questions
            "s1_budget": strategy_questions.get("s1_budget", ""),
            "s2_zeitrahmen": strategy_questions.get("s2_zeitrahmen", ""),
            "s3_prioritaeten": ", ".join(strategy_questions.get("s3_prioritaeten", [])),
            "s4_engpass": strategy_questions.get("s4_engpass", ""),
            "s5_software": strategy_questions.get("s5_software", ""),
            "s6_foerderinteresse": strategy_questions.get("s6_foerderinteresse", ""),
            "s7_entscheidung": strategy_questions.get("s7_entscheidung", ""),
            "s8_erfahrung": strategy_questions.get("s8_erfahrung", ""),
            "s9_ansatz": strategy_questions.get("s9_ansatz", ""),
            "s10_datenschutz": strategy_questions.get("s10_datenschutz", ""),
            # Budget values (pre-calculated, German format)
            **budget.to_dict(),
        }

        # S1 + S2 parallel (independent)
        s1_task = _generate_section("S1", base_context, {
            "staerken_top3": str(report1_data.get("staerken", "")),
            "handlungsfelder_top3": str(report1_data.get("handlungsfelder", "")),
            "potenziale_summary": str(report2_data.get("potenziale", "")),
        })
        s2_task = _generate_section("S2", base_context, {
            "research_markt_trends": research_context.get("markt_trends", {}).get("results", ""),
            "research_wettbewerb": research_context.get("wettbewerb_benchmark", {}).get("results", ""),
            "research_branche_stats": research_context.get("branche_stats_en", {}).get("results", ""),
        })

        sections["S1"], sections["S2"] = await asyncio.gather(s1_task, s2_task)
        _heartbeat(db_session, briefing_id)

        # S3 (needs S2)
        sections["S3"] = await _generate_section("S3", base_context, {
            "s2_trends_summary": _extract_summary(sections["S2"]),
            "staerken_top3": str(report1_data.get("staerken", "")),
            "handlungsfelder_top3": str(report1_data.get("handlungsfelder", "")),
            "potenziale_summary": str(report2_data.get("potenziale", "")),
        })

        _heartbeat(db_session, briefing_id)

        # S4 (needs S3)
        sections["S4"] = await _generate_section("S4", base_context, {
            "s3_handlungsfelder": _extract_handlungsfelder(sections["S3"]),
            "research_tool_1": research_context.get("tool_vergleich_1", {}).get("results", ""),
            "research_tool_2": research_context.get("tool_vergleich_2", {}).get("results", ""),
            "research_integration": research_context.get("tool_integration", {}).get("results", ""),
        })

        _heartbeat(db_session, briefing_id)

        # S5 (needs S3, S4 — budget values already in base_context)
        sections["S5"] = await _generate_section("S5", base_context, {})

        _heartbeat(db_session, briefing_id)

        # S6 (needs S3-S5)
        sections["S6"] = await _generate_section("S6", base_context, {
            "s3_handlungsfelder": _extract_handlungsfelder(sections["S3"]),
            "s4_tools_summary": _extract_summary(sections["S4"]),
            "s5_budget_summary": _extract_summary(sections["S5"]),
        })

        # S7 + S8 parallel
        s7_task = _generate_section("S7", base_context, {
            "foerder_matches": str(report1_data.get("foerder_matches", "")),
            "research_foerdermittel": research_context.get("foerdermittel", {}).get("results", ""),
            "research_foerdermittel_eu": research_context.get("foerdermittel_eu", {}).get("results", ""),
        })
        s8_task = _generate_section("S8", base_context, {
            "risiko_score": str(report1_data.get("risiko_score", "")),
            "risiken_report1": str(report1_data.get("risiken", "")),
            "s3_handlungsfelder": _extract_handlungsfelder(sections["S3"]),
            "s4_tools_summary": _extract_summary(sections["S4"]),
        })

        sections["S7"], sections["S8"] = await asyncio.gather(s7_task, s8_task)
        _heartbeat(db_session, briefing_id)

        # Executive Summary LAST (via Claude, not GPT)
        # Log budget values being passed to EXEC for debugging hallucination
        logger.info(
            "[Strategy %d] EXEC context: score=%s, budget=%s, roi=%s/%s/%s, breakeven=%s/%s/%s",
            briefing_id,
            base_context.get("readiness_score", "EMPTY"),
            base_context.get("budget_gesamt_jahr1", "EMPTY"),
            base_context.get("roi_konservativ", "EMPTY"),
            base_context.get("roi_realistisch", "EMPTY"),
            base_context.get("roi_optimistisch", "EMPTY"),
            base_context.get("breakeven_konservativ", "EMPTY"),
            base_context.get("breakeven_realistisch", "EMPTY"),
            base_context.get("breakeven_optimistisch", "EMPTY"),
        )

        sections["exec_summary"] = await _generate_section("EXEC", base_context, {
            "top_handlungsfeld": _extract_top_handlungsfeld(sections["S3"]),
            "anzahl_felder": str(len(handlungsfelder)),
            "quick_win": _extract_quick_win(sections["S3"]),
            "summe_foerder": _extract_foerder_summe(sections["S7"]),
            "s5_investition_summary": _extract_summary(sections["S5"], max_words=150),
        }, use_claude=True)

        # === PHASE 3: Assembly ===
        generation_duration = time.time() - start_time - research_duration
        total_duration = time.time() - start_time

        logger.info(
            "[Strategy %d] Complete: Research %.1fs, Generation %.1fs, Total %.1fs",
            briefing_id, research_duration, generation_duration, total_duration,
        )

        _save_sections(db_session, briefing_id, sections, research_duration, generation_duration, total_duration)
        _update_status(db_session, briefing_id, "completed")

        # === PHASE 4: PDF Generation ===
        await _generate_pdf(db_session, briefing_id)

        return sections

    except Exception as e:
        logger.error("[Strategy %d] Pipeline failed: %s", briefing_id, e, exc_info=True)
        _update_status(db_session, briefing_id, "failed")
        raise


# =============================================================================
# SECTION GENERATION
# =============================================================================

async def _generate_section(
    section_key: str,
    base_context: Dict[str, Any],
    extra_context: Dict[str, Any],
    use_claude: bool = False,
) -> str:
    """
    Generate a single section via LLM.
    Uses existing LLM infrastructure (OpenAI for most sections, Anthropic for exec summary).
    """
    from prompts.strategy_prompts import STRATEGY_PROMPTS, SYSTEM_PROMPT_STRATEGY_REPORT

    prompt_template = STRATEGY_PROMPTS.get(section_key, "")
    if not prompt_template:
        logger.warning("[Strategy] No prompt template for section %s", section_key)
        return ""

    # Build prompt
    context = {**base_context, **extra_context}
    try:
        prompt = prompt_template.format(**{k: str(v or "") for k, v in context.items()})
    except KeyError as e:
        logger.warning("[Strategy] Missing key in prompt template for %s: %s", section_key, e)
        # Fill missing keys with empty strings
        prompt = prompt_template
        for key in re.findall(r"\{(\w+)\}", prompt_template):
            if key not in context:
                context[key] = ""
        prompt = prompt_template.format(**{k: str(v or "") for k, v in context.items()})

    # Call LLM — respect LLM_PROVIDER_DEFAULT (same routing as Report 1+2)
    start = time.time()
    result: Optional[str] = None

    route_to_anthropic = use_claude
    if not route_to_anthropic:
        from services.anthropic_client import should_use_anthropic
        route_to_anthropic = should_use_anthropic(section=f"strategy_{section_key}")

    prompt_len = len(prompt)
    prompt_words = len(prompt.split())
    logger.info(
        "[Strategy] Section %s: routing to %s (use_claude=%s, prompt=%d chars / %d words)",
        section_key, "Anthropic" if route_to_anthropic else "OpenAI",
        use_claude, prompt_len, prompt_words,
    )

    # Longer sections (S8 Risiken, EXEC) get more output tokens
    max_out_tokens = 6000 if section_key in ("S8", "EXEC", "S5") else 5000

    if route_to_anthropic:
        result = await _call_anthropic(prompt, SYSTEM_PROMPT_STRATEGY_REPORT, section_key, max_tokens=max_out_tokens)
    else:
        result = await _call_openai(prompt, SYSTEM_PROMPT_STRATEGY_REPORT, section_key, max_tokens=max_out_tokens)

    duration = time.time() - start
    word_count = len((result or "").split())
    logger.info(
        "[Strategy] Section %s: %d words in %.1fs (anthropic=%s)",
        section_key, word_count, duration, route_to_anthropic,
    )

    return result or f"<p><em>Section {section_key} konnte nicht generiert werden.</em></p>"


async def _call_openai(prompt: str, system_prompt: str, section: str, max_tokens: int = 5000) -> Optional[str]:
    """Call OpenAI using ENV-configured model (same as Report 1+2)."""
    try:
        import os
        import openai

        api_key = os.getenv("OPENAI_API_KEY", "")
        model = os.getenv("OPENAI_MODEL", "gpt-4o")

        if not api_key:
            logger.error("[Strategy] OPENAI_API_KEY not set — cannot call OpenAI for %s", section)
            return None

        logger.info("[Strategy] OpenAI call for %s: model=%s, max_tokens=%d", section, model, max_tokens)

        client = openai.OpenAI(api_key=api_key, timeout=180.0)

        def _openai_call() -> Any:
            return client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_completion_tokens=max_tokens,
            )

        response = await asyncio.to_thread(_openai_call)

        content: Optional[str] = response.choices[0].message.content if response.choices else None

        # Log raw response details for debugging
        finish_reason = response.choices[0].finish_reason if response.choices else "no_choices"
        content_len = len(content) if content else 0
        logger.info(
            "[Strategy] OpenAI raw response for %s: %d chars, finish_reason=%s",
            section, content_len, finish_reason,
        )
        if finish_reason == "length":
            logger.warning("[Strategy] OpenAI response TRUNCATED for %s (hit token limit)", section)

        return content
    except Exception as exc:
        logger.error("[Strategy] OpenAI call failed for %s: %s", section, exc, exc_info=True)
        return None


async def _call_anthropic(prompt: str, system_prompt: str, section: str, max_tokens: int = 5000) -> Optional[str]:
    """Call Anthropic Claude via the existing anthropic_client."""
    try:
        from services.anthropic_client import call_anthropic

        result = await asyncio.to_thread(
            call_anthropic,
            prompt,
            section=f"strategy_{section}",
            system_prompt=system_prompt,
            max_tokens=max_tokens,
        )
        result_len = len(result) if result else 0
        logger.info("[Strategy] Anthropic response for %s: %d chars", section, result_len)
        if result_len == 0:
            logger.warning("[Strategy] Anthropic returned EMPTY for %s — falling back to OpenAI", section)
            return await _call_openai(prompt, system_prompt, section)
        return result
    except Exception as exc:
        logger.error("[Strategy] Anthropic call failed for %s: %s", section, exc, exc_info=True)
        # Fallback to OpenAI
        logger.info("[Strategy] Falling back to OpenAI for %s", section)
        return await _call_openai(prompt, system_prompt, section)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _segment_label(raw: str) -> str:
    """Map raw unternehmensgroesse value to a readable segment label for prompts."""
    _map = {
        "1": "Einzelunternehmer",
        "solo": "Einzelunternehmer",
        "freelancer": "Einzelunternehmer",
        "2-10": "Kleinunternehmen (2\u201310 Mitarbeiter)",
        "2\u201310": "Kleinunternehmen (2\u201310 Mitarbeiter)",
        "team": "Kleinunternehmen (2\u201310 Mitarbeiter)",
        "klein": "Kleinunternehmen (2\u201310 Mitarbeiter)",
        "11-100": "KMU (11\u2013100 Mitarbeiter)",
        "11\u2013100": "KMU (11\u2013100 Mitarbeiter)",
        "kmu": "KMU (11\u2013100 Mitarbeiter)",
        "medium": "KMU (11\u2013100 Mitarbeiter)",
    }
    key = str(raw or "").strip().lower()
    return _map.get(key, str(raw or ""))


def _derive_handlungsfelder(report1_data: Dict[str, Any], report2_data: Dict[str, Any]) -> List[str]:
    """Derive action fields from Report 1+2 data."""
    felder = []

    # From Report 1 sections
    sections = report1_data.get("sections", {})
    if isinstance(sections, dict):
        # Try to get recommendations / handlungsfelder
        for key in ("handlungsfelder", "recommendations", "empfehlungen"):
            val = sections.get(key)
            if val and isinstance(val, list):
                felder.extend(val[:3])
                break
            elif val and isinstance(val, str):
                felder.append(val)

    # From Report 2 potenziale
    potenziale = report2_data.get("potenziale")
    if potenziale and isinstance(potenziale, list):
        felder.extend(potenziale[:2])
    elif potenziale and isinstance(potenziale, str):
        felder.append(potenziale)

    # Defaults if nothing found
    if not felder:
        felder = ["KI-gestützte Prozessautomatisierung", "Datenanalyse & Business Intelligence", "Kundenservice-Optimierung"]

    return felder[:5]  # Max 5 fields


def _extract_summary(section_html: str, max_words: int = 200) -> str:
    """Extract a brief summary from section HTML for follow-up sections."""
    if not section_html:
        return ""
    # Strip HTML tags
    text = re.sub(r"<[^>]+>", " ", section_html)
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split()
    return " ".join(words[:max_words])


def _extract_handlungsfelder(s3_html: str) -> str:
    """Extract action field list from S3 HTML."""
    return _extract_summary(s3_html, max_words=300)


def _extract_top_handlungsfeld(s3_html: str) -> str:
    """Extract the top action field (first heading after S3 content)."""
    if not s3_html:
        return "KI-Automatisierung"
    # Try to find first h3 or strong tag
    match = re.search(r"<h3[^>]*>(.*?)</h3>", s3_html)
    if match:
        return re.sub(r"<[^>]+>", "", match.group(1)).strip()
    match = re.search(r"<strong>(.*?)</strong>", s3_html)
    if match:
        return re.sub(r"<[^>]+>", "", match.group(1)).strip()
    return _extract_summary(s3_html, max_words=10)


def _extract_quick_win(s3_html: str) -> str:
    """Extract the quick win from S3."""
    if not s3_html:
        return ""
    # Look for quick win pattern
    match = re.search(r"(?:Quick.?Win|Sofort|sofort)[^<]*", s3_html, re.IGNORECASE)
    if match:
        return match.group(0).strip()[:200]
    return _extract_summary(s3_html, max_words=30)


def _extract_foerder_summe(s7_html: str) -> str:
    """Extract total funding sum from S7."""
    if not s7_html:
        return "k.A."
    # Look for Euro amounts
    matches = re.findall(r"[\d.,]+\s*(?:€|Euro|EUR)", s7_html)
    if matches:
        return str(matches[0])
    return "k.A."


# =============================================================================
# PDF GENERATION
# =============================================================================

async def _generate_pdf(db_session: Any, briefing_id: int) -> None:
    """Generate PDF after all sections are saved (analog to Report 1)."""
    try:
        from models import StrategyReport
        from services.strategy_renderer import render_strategy_html
        from services.pdf_client import render_pdf_from_html

        sr = db_session.query(StrategyReport).filter(
            StrategyReport.briefing_id == briefing_id
        ).first()
        if not sr or not sr.sections:
            logger.warning("[Strategy %d] Cannot generate PDF — no sections", briefing_id)
            return

        html_content = render_strategy_html(sr, db_session)

        # Embed logos as base64 for PDF service compatibility
        from utils.logo_embedder import embed_logos_in_html
        import os
        _tpl_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        html_content = embed_logos_in_html(html_content, _tpl_dir)

        logger.info("[Strategy %d] Rendering PDF (%d chars HTML)", briefing_id, len(html_content))

        result = await asyncio.to_thread(
            render_pdf_from_html,
            html_content,
            {"report_type": "strategy", "briefing_id": briefing_id},
        )

        if "error" in result:
            logger.error("[Strategy %d] PDF generation failed: %s", briefing_id, result["error"])
            return

        pdf_bytes = result.get("pdf_bytes")
        if pdf_bytes:
            sr.pdf_available = True
            sr.pdf_generated_at = datetime.now(timezone.utc)
            sr.updated_at = datetime.now(timezone.utc)
            db_session.commit()
            logger.info("[Strategy %d] PDF generated (%d bytes)", briefing_id, len(pdf_bytes))

            # FIX-Jv2: Send email with PDF attachment
            logger.info("[Strategy %d] Starting email delivery (%d bytes PDF)...", briefing_id, len(pdf_bytes))
            try:
                _send_strategy_email(briefing_id, pdf_bytes, db_session)
                sr.email_sent = True
                sr.email_sent_at = datetime.now(timezone.utc)
                db_session.commit()
                logger.info("[Strategy %d] email_sent=True committed", briefing_id)
            except Exception as mail_exc:
                logger.error("[Strategy %d] Email sending failed: %s", briefing_id, mail_exc, exc_info=True)
        else:
            logger.warning("[Strategy %d] PDF service returned no bytes", briefing_id)

    except Exception as exc:
        logger.error("[Strategy %d] PDF generation error: %s", briefing_id, exc, exc_info=True)


# =============================================================================
# EMAIL HELPER (FIX-J)
# =============================================================================

def _send_strategy_email(briefing_id: int, pdf_bytes: bytes, db_session: Any) -> None:
    """Send KI-Strategiebericht PDF via email (same pattern as KPA)."""
    import os
    import time as _time

    run_tag = f"STRATEGY-MAIL-{briefing_id}"
    logger.info("[%s] _send_strategy_email called (pdf=%d bytes)", run_tag, len(pdf_bytes))

    if os.getenv("DISABLE_EMAILS", "").lower() in ("1", "true", "yes", "on"):
        logger.info("[%s] Emails disabled via DISABLE_EMAILS. Skipping.", run_tag)
        return

    try:
        from gpt_analyze import (
            _send_email_via_resend,
            _determine_user_email,
            _admin_recipients,
            _mask_email,
        )
        from services.email_templates import render_strategy_email
        from models import Briefing
        logger.info("[%s] Imports OK", run_tag)
    except ImportError as exc:
        logger.error("[%s] Import FAILED, skipping email: %s", run_tag, exc)
        return

    briefing = db_session.query(Briefing).filter(Briefing.id == briefing_id).first()
    if not briefing:
        logger.warning("[%s] Briefing not found, skipping email.", run_tag)
        return

    user_email = _determine_user_email(db_session, briefing, None)
    logger.info("[%s] Resolved user_email=%s", run_tag, _mask_email(user_email) if user_email else "NONE")

    attachment = {
        "filename": f"KI-Strategiebericht-{briefing_id}.pdf",
        "content": pdf_bytes,
        "mimetype": "application/pdf",
    }
    subject = "Ihr KI-Strategiebericht"

    # --- User email ---
    if user_email:
        ok, err = _send_email_via_resend(
            user_email,
            subject,
            render_strategy_email(recipient="user"),
            attachments=[attachment],
        )
        if ok:
            logger.info("[%s] Email sent to user %s", run_tag, _mask_email(user_email))
        else:
            logger.warning("[%s] User email failed: %s", run_tag, err)
    else:
        logger.warning("[%s] No user email found, skipping user email.", run_tag)

    _time.sleep(0.6)  # Resend Rate Limit: max 2 req/sec

    # --- Admin email ---
    if os.getenv("ENABLE_ADMIN_NOTIFY", "1") in ("1", "true", "TRUE", "yes", "YES"):
        for addr in _admin_recipients():
            _time.sleep(0.6)
            ok, err = _send_email_via_resend(
                addr,
                f"Kopie: KI-Strategiebericht — Briefing #{briefing_id}",
                render_strategy_email(recipient="admin"),
                attachments=[attachment],
            )
            if ok:
                logger.info("[%s] Admin email sent to %s", run_tag, _mask_email(addr))
            else:
                logger.warning("[%s] Admin email failed for %s: %s", run_tag, _mask_email(addr), err)


# =============================================================================
# DB HELPERS
# =============================================================================

def _heartbeat(db_session: Any, briefing_id: int) -> None:
    """Touch updated_at to prevent stale-detection during long generations."""
    from models import StrategyReport

    sr = db_session.query(StrategyReport).filter(
        StrategyReport.briefing_id == briefing_id
    ).first()
    if sr:
        sr.updated_at = datetime.now(timezone.utc)
        db_session.commit()


def _update_status(db_session: Any, briefing_id: int, status: str) -> None:
    """Update strategy_reports.status."""
    from models import StrategyReport

    sr = db_session.query(StrategyReport).filter(
        StrategyReport.briefing_id == briefing_id
    ).first()
    if sr:
        sr.status = status
        sr.updated_at = datetime.now(timezone.utc)
        db_session.commit()
        logger.info("[Strategy %d] Status → %s", briefing_id, status)


def _save_intermediate(
    db_session: Any,
    briefing_id: int,
    research_context: Dict[str, Any],
    calculated_values: Dict[str, str],
) -> None:
    """Save research + calculated values as JSON in DB (cache)."""
    from models import StrategyReport

    sr = db_session.query(StrategyReport).filter(
        StrategyReport.briefing_id == briefing_id
    ).first()
    if sr:
        sr.research_context = research_context
        sr.calculated_values = calculated_values
        sr.updated_at = datetime.now(timezone.utc)
        db_session.commit()


def _save_sections(
    db_session: Any,
    briefing_id: int,
    sections: Dict[str, str],
    r_dur: float,
    g_dur: float,
    t_dur: float,
) -> None:
    """Save generated sections + timing in DB."""
    from models import StrategyReport

    sr = db_session.query(StrategyReport).filter(
        StrategyReport.briefing_id == briefing_id
    ).first()
    if sr:
        sr.sections = sections
        sr.research_duration_seconds = r_dur
        sr.generation_duration_seconds = g_dur
        sr.total_duration_seconds = t_dur
        sr.updated_at = datetime.now(timezone.utc)
        db_session.commit()
