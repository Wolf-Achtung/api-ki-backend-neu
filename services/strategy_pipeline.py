# -*- coding: utf-8 -*-
"""
Strategy Report Pipeline Orchestrator (Report 3).

Coordinates research, budget calculation, and section generation
for the KI-Strategiebericht.

Pipeline order:
1. Research + Budget-Calc (parallel)
2. S1 + S2 (parallel)
3. S3 (needs S2)
4. S3b + S4 (parallel; S3b independent, S4 needs S3)
5. S5 (needs S3, S4)
6. S6 (needs S3-S5)
7. S7 + S8 + s_moat (parallel)
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

        # B41-FIX: Build report1_values from R1 sections (single source of truth).
        # Previously passed report1_data.get("business_case", {}) which is HTML, not
        # a structured dict — causing fallback to segment defaults (Team=30h instead
        # of canonical 36h from R1).
        _r1_sections = report1_data.get("sections", {})
        _r1_bc = report1_data.get("business_case", {})
        _r1_values = _r1_bc if isinstance(_r1_bc, dict) else {}
        # Overlay canonical values from R1 sections (these are the authoritative source)
        _canon_hours = (
            _r1_sections.get("CANON_HOURS_MONTH")
            or _r1_sections.get("TIME_SAVINGS_MONTH_HOURS_CAPPED")
            or _r1_sections.get("EINSPARUNG_STUNDEN_MONAT")
        )
        if _canon_hours:
            _r1_values["zeitersparnis_stunden"] = _canon_hours
        _canon_rate = (
            _r1_sections.get("CANON_RATE_EUR")
            or _r1_sections.get("stundensatz_eur")
        )
        if _canon_rate:
            _r1_values["stundensatz"] = _canon_rate
        logger.info(
            "[Strategy %d] R1 values for budget: zeitersparnis=%s, stundensatz=%s",
            briefing_id, _r1_values.get("zeitersparnis_stunden"), _r1_values.get("stundensatz"),
        )

        budget_task = asyncio.to_thread(
            calculate_strategy_budget,
            briefing_data,
            strategy_questions,
            handlungsfelder,
            _r1_values,
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
        # FIX-Iv4 + FIX-HOTFIX3: Compute score from stored post-quality value or LIVE recalc.
        _r1_scores = report1_data.get("scores", {})
        # Match R1 formula exactly: round((gov + sec + val + ena) / 4)
        _dim_vals = [
            float(_r1_scores.get("governance", 0) or 0),
            float(_r1_scores.get("security", 0) or 0),
            float(_r1_scores.get("value", 0) or 0),
            float(_r1_scores.get("enablement", 0) or 0),
        ]
        _base = round(sum(_dim_vals) / 4) if any(_dim_vals) else 0

        # --- SCORE-DEBUG (temporary, remove after verification) ---
        logger.debug("SCORE-DEBUG-1: [Strategy %d] meta.scores = %r", briefing_id, _r1_scores)
        logger.debug("SCORE-DEBUG-2: [Strategy %d] dimension scores = gov=%s, sec=%s, val=%s, ena=%s",
                        briefing_id, _dim_vals[0], _dim_vals[1], _dim_vals[2], _dim_vals[3])
        logger.debug("SCORE-DEBUG-3: [Strategy %d] calculated = %s, rounded = %d",
                        briefing_id, sum(_dim_vals) / 4 if any(_dim_vals) else 0, _base)
        logger.debug("SCORE-DEBUG-KEYS: [Strategy %d] N43_DOD_PASSED=%r, _n43_dod_passed=%r, "
                        "CONSISTENCY_GRADE=%r, _CONSISTENCY_GRADE=%r, _CONSISTENCY_SCORE=%r, "
                        "QUALITY_BONUS=%r, score_gesamt=%r, CANONICAL_OVERALL=%r, scores.overall=%r",
                        briefing_id,
                        report1_sections.get("N43_DOD_PASSED", "MISSING"),
                        report1_sections.get("_n43_dod_passed", "MISSING"),
                        report1_sections.get("CONSISTENCY_GRADE", "MISSING"),
                        report1_sections.get("_CONSISTENCY_GRADE", "MISSING"),
                        report1_sections.get("_CONSISTENCY_SCORE", "MISSING"),
                        report1_sections.get("QUALITY_BONUS", "MISSING"),
                        report1_sections.get("score_gesamt", "MISSING"),
                        report1_sections.get("CANONICAL_OVERALL", "MISSING"),
                        _r1_scores.get("overall", "MISSING"))

        # FIX-HOTFIX3: Prefer stored QUALITY_BONUS (exact value from gpt_analyze)
        # over re-deriving from N43_DOD_PASSED/_CONSISTENCY_GRADE which may be
        # filtered from serializable_sections (underscore-prefixed keys).
        _qb_stored = report1_sections.get("QUALITY_BONUS", None)
        if isinstance(_qb_stored, (int, float)):
            _qb = int(_qb_stored)
            logger.info("[Strategy %d] Using stored QUALITY_BONUS=%d", briefing_id, _qb)
        else:
            # Fallback: re-derive quality bonus (for older analyses without QUALITY_BONUS)
            _dod_ok = report1_sections.get("N43_DOD_PASSED", False) or report1_sections.get("_n43_dod_passed", False)
            # FIX-HOTFIX3b: Read CONSISTENCY_GRADE (without underscore, survives
            # serialization at gpt_analyze.py:18084) and default to 'F'/0 to match
            # calc_quality_bonus defaults (gpt_analyze.py:2099-2100).
            # Previous code used _CONSISTENCY_GRADE (filtered) with default 'A'/100,
            # which OVER-estimated the bonus vs what calc_quality_bonus actually gave.
            _cg = str(report1_sections.get("CONSISTENCY_GRADE",
                       report1_sections.get("_CONSISTENCY_GRADE", "F")))
            _cs = report1_sections.get("_CONSISTENCY_SCORE", 0)
            _qb = 0
            if _dod_ok:
                _qb = 2 if (_cg in ("A", "B") or (isinstance(_cs, (int, float)) and _cs >= 80)) else 1
            logger.info("[Strategy %d] Re-derived QUALITY_BONUS=%d (dod=%s, grade=%s, score=%s)", briefing_id, _qb, _dod_ok, _cg, _cs)
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
        # FIX-HOTFIX3: Use stored max if it matches scores.overall (post-quality from FIX-HOTFIX3-SCORE).
        # If scores.overall was updated with final score, stored_max will be correct.
        # Prefer live calc when dims exist AND live matches stored (consistency check).
        if any(_dim_vals):
            # If stored_max is available and matches or exceeds live, prefer stored
            # (covers case where scores.overall was synced post-quality-bonus)
            if _stored_max >= _live:
                _score = _stored_max
            else:
                _score = _live
        else:
            _score = _stored_max  # Legacy data without dimensions → use stored
        logger.info("[Strategy %d] Score: R1-formula dims=%r base=%d bonus=%d live=%d stored_max=%d → using %d (live_preferred=%s)",
                    briefing_id, _dim_vals, _base, _qb, _live, _stored_max, _score, any(_dim_vals))
        # --- SCORE-DEBUG (temporary, remove after verification) ---
        logger.debug("SCORE-DEBUG-4: [Strategy %d] score passed to template = %d", briefing_id, _score)
        logger.debug("SCORE-DEBUG-5: [Strategy %d] stored_candidates = %r", briefing_id, _stored)

        # KIS-1126 / C1 FIX: Always use deterministic absolute label from get_score_label()
        # to ensure cross-report consistency (R1, KPA, Strategy all show same label for same score)
        _reifegrad_label = report1_sections.get("score_rating", "")
        if _score > 0:
            try:
                from services.extra_sections import get_score_label
                _reifegrad_label = get_score_label(_score, lang="de")
                logger.info("[Strategy %d] reifegrad_label from deterministic lookup: %s (score=%d)",
                            briefing_id, _reifegrad_label, _score)
            except Exception:
                if not _reifegrad_label:
                    _reifegrad_label = report1_sections.get("score_rating", "")

        # Country code for country-aware prompts (S7 funding, S8 compliance)
        _country_raw = (
            briefing_data.get("country", "")
            or briefing_data.get("land", "")
            or ""
        )
        _country_code = str(_country_raw).strip().upper() if _country_raw else "DE"
        if _country_code not in ("DE", "AT", "CH", "GB"):
            _country_code = "DE"

        # FIX-A3/A2: Canonical BAFA values based on Bundesland
        _bl_label = _bundesland_label(briefing_data.get("bundesland", ""), country=_country_code)
        try:
            from config.bafa import get_bafa_foerderquote, get_bafa_foerderung_max_display
            _bafa_quote = get_bafa_foerderquote(_bl_label)
            _bafa_max = get_bafa_foerderung_max_display(_bl_label)
        except ImportError:
            _bafa_quote = 50
            _bafa_max = "1.750 €"

        # S31-FIX-A: Extract hauptleistung for industry-specific context
        _hauptleistung = (briefing_data.get("hauptleistung", "") or "").strip()

        # S31-FIX-C: Extract R1 ROI values for ROI bridge explanation
        # FIX-911: Format as clean integers/decimals (no "48000.0" or "-28.999999996")
        _r1_roi_12m_raw = _r1_sections.get("ROI_12M", "") or _r1_sections.get("ROI_12M_CAPPED", "")
        _r1_capex_raw = _r1_sections.get("BC_INVESTMENT_TOTAL", "") or _r1_sections.get("CAPEX", "")
        _r1_payback_raw = _r1_sections.get("PAYBACK_MONTHS", "")
        try:
            _r1_roi_12m = f"{float(_r1_roi_12m_raw):.0f}" if _r1_roi_12m_raw else ""
        except (ValueError, TypeError):
            _r1_roi_12m = str(_r1_roi_12m_raw)
        try:
            _r1_capex = f"{int(float(_r1_capex_raw)):,}".replace(",", ".") if _r1_capex_raw else ""
        except (ValueError, TypeError):
            _r1_capex = str(_r1_capex_raw)
        try:
            _r1_payback = f"{float(_r1_payback_raw):.1f}".replace(".", ",") if _r1_payback_raw else ""
        except (ValueError, TypeError):
            _r1_payback = str(_r1_payback_raw)

        # S31-FIX-D: Extract vendor audit results for tool consistency
        _vendor_audit_red = str(_r1_sections.get("VENDOR_AUDIT_RED", 0) or 0)
        _vendor_audit_green = str(_r1_sections.get("VENDOR_AUDIT_GREEN", 0) or 0)
        _vendor_audit_status = str(_r1_sections.get("VENDOR_AUDIT_STATUS", "") or "")

        _COUNTRY_NAME_MAP = {
            "DE": "Deutschland",
            "AT": "Österreich",
            "CH": "Schweiz",
            "GB": "Vereinigtes Königreich",
        }
        _country_name = _COUNTRY_NAME_MAP.get(_country_code, "Deutschland")

        base_context = {
            "branche": (briefing_data.get("branche", "") or "").title(),
            "hauptleistung": _hauptleistung,
            "segment": _segment_label(briefing_data.get("unternehmensgroesse", "")),
            "mitarbeiter": briefing_data.get("mitarbeiter", ""),
            "bundesland": _bl_label,
            "country": _country_code,
            "country_name": _country_name,
            "firmenname": briefing_data.get("unternehmen_name", "Ihr Unternehmen"),
            # FIX-A3: Deterministic BAFA values for S7
            "bafa_foerderquote": str(_bafa_quote),
            "bafa_max_foerderung": _bafa_max,
            "readiness_score": _score,
            "reifegrad": _reifegrad_label,
            "reifegrad_label": _reifegrad_label,
            # KIS-1142 Punkt 5: R1 dimension scores for advisor_note prompt.
            # _dim_vals order matches [_r1_scores.governance, .security, .value, .enablement].
            "r1_score_governance": str(int(_dim_vals[0])) if _dim_vals[0] else "",
            "r1_score_sicherheit": str(int(_dim_vals[1])) if _dim_vals[1] else "",
            "r1_score_nutzen":     str(int(_dim_vals[2])) if _dim_vals[2] else "",
            "r1_score_befaehigung": str(int(_dim_vals[3])) if _dim_vals[3] else "",
            # S31-FIX-C: R1 ROI values for bridge explanation
            "r1_roi_pct": str(_r1_roi_12m),
            "r1_capex": str(_r1_capex),
            "r1_payback_months": str(_r1_payback),
            # S31-FIX-D: Vendor audit results
            "vendor_audit_red_count": _vendor_audit_red,
            "vendor_audit_green_count": _vendor_audit_green,
            "vendor_audit_status": _vendor_audit_status,
            # Strategy questions
            "s1_budget": strategy_questions.get("s1_budget", ""),
            "s2_zeitrahmen": strategy_questions.get("s2_zeitrahmen", ""),
            "s3_prioritaeten": ", ".join(strategy_questions.get("s3_prioritaeten", [])),
            "s4_engpass": strategy_questions.get("s4_engpass", ""),
            # s5_software: comma-separated string, merged in Frontend (strategy.html ~L1179-1184)
            # from s5_tools (checkboxes) + s5_tools_other (freetext). Backend only reads s5_software.
            "s5_software": strategy_questions.get("s5_software", ""),
            "s6_foerderinteresse": strategy_questions.get("s6_foerderinteresse", ""),
            "s7_entscheidung": strategy_questions.get("s7_entscheidung", ""),
            "s8_erfahrung": strategy_questions.get("s8_erfahrung", ""),
            "s9_ansatz": strategy_questions.get("s9_ansatz", ""),
            "s10_datenschutz": strategy_questions.get("s10_datenschutz", ""),
            # Budget values (pre-calculated, German format)
            **budget.to_dict(),
        }

        # FIX-GUARDRAIL-STRATEGY: Pass ki_guardrails into base_context
        base_context["ki_guardrails"] = (
            briefing_data.get("ki_guardrails", "") or ""
        )

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

        # S3b + S4 parallel (S3b is independent, S4 needs S3)
        s3b_extra = {
            "geschaeftsmodell_evolution": briefing_data.get("geschaeftsmodell_evolution", ""),
            "vision_3_jahre": briefing_data.get("vision_3_jahre", ""),
            "strategische_ziele": briefing_data.get("strategische_ziele", ""),
            "ki_ziele_labels": str(report1_sections.get("KI_ZIELE_LABELS", "") or briefing_data.get("ki_ziele", "")),
            "zeitersparnis_prioritaet": briefing_data.get("zeitersparnis_prioritaet", ""),
            "ki_projekte": briefing_data.get("ki_projekte", ""),
            "ki_kompetenz": briefing_data.get("ki_kompetenz", ""),
            "zielgruppen_labels": str(report1_sections.get("ZIELGRUPPEN_LABELS", "") or briefing_data.get("zielgruppen", "")),
            "marktposition_label": str(report1_sections.get("MARKTPOSITION_LABEL", "") or briefing_data.get("marktposition", "")),
            "anwendungsfaelle_labels": str(report1_sections.get("ANWENDUNGSFAELLE_LABELS", "") or briefing_data.get("anwendungsfaelle", "")),
            "vorhandene_tools_labels": str(report1_sections.get("VORHANDENE_TOOLS_LABELS", "") or briefing_data.get("vorhandene_tools", "")),
            "jahresumsatz_label": str(report1_sections.get("JAHRESUMSATZ_LABEL", "") or briefing_data.get("jahresumsatz", "")),
            "canon_hours_month": str(report1_sections.get("CANON_HOURS_MONTH", "") or ""),
            "canon_rate_eur": str(report1_sections.get("CANON_RATE_EUR", "") or ""),
            "canon_capex_eur": str(report1_sections.get("CANON_CAPEX_EUR", "") or ""),
            "s5_vision": strategy_questions.get("s5_vision", ""),
        }
        s3b_task = _generate_section("S3b", base_context, s3b_extra)
        s4_task = _generate_section("S4", base_context, {
            "s3_handlungsfelder": _extract_handlungsfelder(sections["S3"]),
            "research_tool_1": research_context.get("tool_vergleich_1", {}).get("results", ""),
            "research_tool_2": research_context.get("tool_vergleich_2", {}).get("results", ""),
            "research_integration": research_context.get("tool_integration", {}).get("results", ""),
        })

        sections["S3b"], sections["S4"] = await asyncio.gather(s3b_task, s4_task)
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

        # --- S7: KIS-1093-B — Structured JSON funding data for S7 prompt ---
        # Programs are filtered ONCE by region/country/size at the source.
        # No HTML parsing, no regex removal, no re-injection needed.
        _funding_data_block = ""
        try:
            from services.funding_recommender import (
                get_filtered_funding_programs,
                format_funding_programs_for_prompt,
            )
            # KIS-1098: Normalize size before passing — DB stores "11–100" (en-dash)
            # but funding_recommender's inline normalization only checks hyphen "11-".
            from services.business_case_engine_v2 import normalize_company_size as _norm_size
            _funding_size = _norm_size(briefing_data.get("unternehmensgroesse", "team"))
            _filtered_programs = get_filtered_funding_programs(
                bundesland=briefing_data.get("bundesland", ""),
                country=_country_code,
                size=_funding_size,
                branch=briefing_data.get("branche", ""),
                limit=8,
            )
            _funding_data_block = format_funding_programs_for_prompt(_filtered_programs)
            logger.info(
                "[Strategy %d] S7 funding (KIS-1093-B): %d pre-filtered programs for country=%s, bl=%s",
                briefing_id, len(_filtered_programs), _country_code,
                briefing_data.get("bundesland", ""),
            )
        except Exception as _fe:
            logger.warning("[Strategy %d] Funding injection failed: %s", briefing_id, _fe, exc_info=True)

        # KIS-1097: Fallback — if get_filtered_funding_programs returned nothing
        # (e.g. import error, JSON load failure), ensure S7 at least gets BAFA data
        # from the base_context that was already computed deterministically.
        if not _funding_data_block.strip():
            _funding_data_block = (
                f"- BAFA – Förderung von Unternehmensberatungen für KMU (Träger: BAFA)\n"
                f"  Förderquote: {_bafa_quote}%\n"
                f"  Max. Förderung: {_bafa_max}\n"
                f"  KI-Relevanz: high\n"
                f"  Frist: bis 31.12.2026"
            )
            # Also try to merge R1 programme names from report1_sections
            _r1_foerder = str(report1_sections.get("FOERDERPROGRAMME_HTML", "") or "")
            if _r1_foerder and "BAFA" not in _r1_foerder[:50]:
                # R1 has a funding table — mention it so LLM doesn't ignore it
                _funding_data_block += (
                    "\n\nHINWEIS: Weitere Programme wurden im KI-Status-Report identifiziert. "
                    "Verwende die BAFA-Daten oben als Minimum."
                )
            logger.warning(
                "[Strategy %d] S7 funding fallback: primary source empty, using BAFA baseline (%s%%, %s)",
                briefing_id, _bafa_quote, _bafa_max,
            )

        # S7 + S8 + s_moat parallel (s_moat is independent of S7/S8)
        s7_task = _generate_section("S7", base_context, {
            "foerder_matches": str(report1_data.get("foerder_matches", "")),
            "research_foerdermittel": research_context.get("foerdermittel", {}).get("results", ""),
            "research_foerdermittel_eu": research_context.get("foerdermittel_eu", {}).get("results", ""),
            "funding_endpoint_data": _funding_data_block,
        })
        s8_task = _generate_section("S8", base_context, {
            "risiko_score": str(report1_data.get("risiko_score", "")),
            "risiken_report1": str(report1_data.get("risiken", "")),
            "s3_handlungsfelder": _extract_handlungsfelder(sections["S3"]),
            "s4_tools_summary": _extract_summary(sections["S4"]),
        })

        # S-Moat: KI-gestützter Wettbewerbsvorteil
        # Build KPA top use cases from R1 analysis data
        _kpa_top_use_cases = (
            str(report1_sections.get("ANWENDUNGSFAELLE_LABELS", "")
                or briefing_data.get("anwendungsfaelle", ""))
        )
        # Fallback: derive from report2 potenziale if available
        if not _kpa_top_use_cases.strip():
            _r2_potenziale = report2_data.get("potenziale", "")
            _kpa_top_use_cases = str(_r2_potenziale) if _r2_potenziale else "keine Angabe"

        s_moat_task = _generate_section("s_moat", base_context, {
            "groesse": _segment_label(briefing_data.get("unternehmensgroesse", "")),
            "geschaeftsmodell_evolution": briefing_data.get("geschaeftsmodell_evolution", "") or "",
            "vision_3_jahre": briefing_data.get("vision_3_jahre", "") or "",
            "strategische_ziele": briefing_data.get("strategische_ziele", "") or "",
            "ki_projekte": briefing_data.get("ki_projekte", "") or "",
            "r1_readiness_score": str(_score),
            "kpa_top_use_cases": _kpa_top_use_cases,
            "wettbewerber_anzahl": strategy_questions.get("wettbewerber_anzahl") or "keine Angabe",
            "kundenbindung_typ": strategy_questions.get("kundenbindung_typ") or "keine Angabe",
            "datenreife": strategy_questions.get("datenreife") or "keine Angabe",
        })

        sections["S7"], sections["S8"], sections["s_moat"] = await asyncio.gather(
            s7_task, s8_task, s_moat_task,
        )
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

        # KIS-1142 Punkt 5: Executive Summary + advisor_note (Persönliche
        # Einschätzung) run in parallel — both depend on S3/S5/S7 being
        # finished but are otherwise independent. advisor_note uses
        # base_context only (R1 dim scores + Strategy questions are already
        # populated there).
        exec_task = _generate_section("EXEC", base_context, {
            "top_handlungsfeld": _extract_top_handlungsfeld(sections["S3"]),
            "anzahl_felder": str(len(handlungsfelder)),
            "quick_win": _extract_quick_win(sections["S3"]),
            "summe_foerder": _extract_foerder_summe(sections["S7"]),
            "s5_investition_summary": _extract_summary(sections["S5"], max_words=150),
        }, use_claude=True)
        advisor_task = _generate_section("advisor_note", base_context, {},
                                         use_claude=True)

        sections["exec_summary"], sections["advisor_note"] = await asyncio.gather(
            exec_task, advisor_task,
        )

        # === FIX-SF1: Strategy Fact Sanitizer ===
        # Snapshot raw LLM outputs before sanitizer (for re-render / sanitizer iteration)
        import copy
        raw_sections = copy.deepcopy(sections)

        from services.strategy_sanitizer import sanitize_strategy_sections
        sections = sanitize_strategy_sections(sections, report_year=2026)
        _sf1_raw = sections.pop('_strategy_sanitizer_report', None)
        sf1_report: dict = _sf1_raw if isinstance(_sf1_raw, dict) else {}
        if sf1_report.get('patches_applied', 0) > 0:
            logger.warning(
                "[Strategy %d] SF1 patched %d implausible values: %s",
                briefing_id, sf1_report['patches_applied'], sf1_report['warnings']
            )

        # === FIX-NL1: Non-Latin Character Sanitizer ===
        from services.pipeline_sanitizers import sanitize_non_latin_sections
        sections = sanitize_non_latin_sections(sections)

        # === FIX-KIS1034-D3: Funding Blacklist for Strategy ===
        # R1 already filters expired programs via apply_funding_blacklist, but
        # Strategy was missing this step — "Digital Jetzt" / "go-digital" leaked through.
        # FIX-S7: Pass bundesland into sections so _build_funding_blacklist can detect
        # Bavaria and keep Digitalbonus Bayern (same logic as R1 pipeline).
        from b25_enforcer import apply_funding_blacklist
        if "bundesland" not in sections and "BUNDESLAND_LABEL" not in sections:
            sections["bundesland"] = base_context.get("bundesland", "")
        sections = apply_funding_blacklist(sections)

        # KIS-1093-B: FIX-KIS-1091-FUND block removed — S7 now receives
        # pre-filtered funding programs as JSON via get_filtered_funding_programs().
        # No HTML parsing, no regex removal, no re-injection needed.

        # === PHASE 3: Assembly ===
        generation_duration = time.time() - start_time - research_duration
        total_duration = time.time() - start_time

        logger.info(
            "[Strategy %d] Complete: Research %.1fs, Generation %.1fs, Total %.1fs",
            briefing_id, research_duration, generation_duration, total_duration,
        )

        _save_sections(db_session, briefing_id, sections, research_duration, generation_duration, total_duration,
                       raw_sections=raw_sections)
        _update_status(db_session, briefing_id, "completed")

        # === PHASE 4: PDF Generation ===
        await _generate_pdf(db_session, briefing_id)

        return sections

    except Exception as e:
        logger.error("[Strategy %d] Pipeline failed: %s", briefing_id, e, exc_info=True)
        _update_status(db_session, briefing_id, "failed")
        raise


# =============================================================================
# FIX-GUARDRAIL-STRATEGY: Detect local-only / no-cloud guardrails
# =============================================================================

_LOCAL_ONLY_KEYWORDS = [
    "nur lokal", "keine online", "keine cloud", "kein cloud",
    "on-premise", "on premise", "selbst gehostet", "self-hosted",
    "lokal nutzbar", "keine saas", "keine externen ki",
    "no cloud", "local only", "on-prem",
]


def _detect_local_only_guardrail(context: dict) -> tuple:
    """Check if ki_guardrails contains a local-only / no-cloud constraint."""
    guardrails = str(context.get("ki_guardrails", "") or "")
    if not guardrails:
        return False, ""
    gl = guardrails.lower()
    is_local = any(kw in gl for kw in _LOCAL_ONLY_KEYWORDS)
    return is_local, guardrails


_GUARDRAIL_BLOCK_S4 = """
## VERPFLICHTENDE EINSCHRÄNKUNG — KUNDENGUARDRAIL

Der Kunde hat folgende KI-Leitplanken definiert:
"{guardrail_text}"

BINDENDE REGELN für deine Tool-Empfehlungen:
1. Empfehle PRIMÄR lokale/on-premise/self-hosted Tools (z.B. Whisper lokal, \
Ollama, LM Studio, DaVinci Resolve AI, n8n self-hosted, lokale LLMs)
2. Wenn der Kunde BEREITS Cloud-Tools nutzt (siehe "Bestehende Software"), \
weise auf den Widerspruch zu seinem Guardrail hin und empfehle einen \
Migrationspfad zu lokalen Alternativen
3. Cloud-Tools dürfen NUR als "Übergangs-Option mit DSGVO-Vorbehalt" genannt \
werden, NICHT als Hauptempfehlung
4. Stelle IMMER eine lokale Alternative als erste Empfehlung dar
5. Begründe bei jeder Tool-Empfehlung, ob sie das Guardrail erfüllt oder nicht

WICHTIG: Der Kunde vertraut darauf, dass seine Guardrails respektiert werden. \
Ein Strategiebericht, der Cloud-Tools als Hauptempfehlung gibt, obwohl der \
Kunde "keine Online-Tools" gesagt hat, untergräbt das Kundenvertrauen.

"""

_GUARDRAIL_BLOCK_SHORT = """
## KUNDENGUARDRAIL (BINDEND)
Guardrail: "{guardrail_text}"
→ Alle Handlungsempfehlungen und Tool-Referenzen MÜSSEN dieses Guardrail \
respektieren. Bevorzuge lokale/on-premise-Lösungen. Cloud-Tools nur als \
Übergangs-Option mit Vorbehalt.

"""


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

    # FIX-GUARDRAIL-STRATEGY: Inject local-only guardrail into S3/S4/S6 prompts
    if section_key in ("S4", "S3", "S3b", "S6"):
        _is_local, _guardrail_text = _detect_local_only_guardrail(context)
        if _is_local:
            if section_key == "S4":
                _block = _GUARDRAIL_BLOCK_S4.format(guardrail_text=_guardrail_text)
            else:
                _block = _GUARDRAIL_BLOCK_SHORT.format(guardrail_text=_guardrail_text)
            prompt = _block + prompt
            logger.info(
                "[Strategy %s] LOCAL-ONLY guardrail injected: '%s'",
                section_key, _guardrail_text[:80],
            )

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

    # S31: Format system prompt with context (for industry, ROI bridge, vendor audit)
    try:
        system_prompt = SYSTEM_PROMPT_STRATEGY_REPORT.format(
            **{k: str(v or "") for k, v in context.items()}
        )
    except KeyError:
        system_prompt = SYSTEM_PROMPT_STRATEGY_REPORT
        for key in re.findall(r"\{(\w+)\}", SYSTEM_PROMPT_STRATEGY_REPORT):
            if key not in context:
                context[key] = ""
        system_prompt = SYSTEM_PROMPT_STRATEGY_REPORT.format(
            **{k: str(v or "") for k, v in context.items()}
        )

    # Longer sections get more output tokens — S4 (Tool-Landschaft) has large prompts
    # FIX-S9-B2: Increased token budget for S4 to prevent truncation
    max_out_tokens = 8000 if section_key in ("S4", "S8", "EXEC", "S5") else 5000

    if route_to_anthropic:
        result = await _call_anthropic(prompt, system_prompt, section_key, max_tokens=max_out_tokens)
    else:
        result = await _call_openai(prompt, system_prompt, section_key, max_tokens=max_out_tokens)

        # FIX-S9-B2: If OpenAI truncated (returned empty/very short), retry with Claude
        if not result or len(result.split()) < 20:
            logger.warning(
                "[Strategy] Section %s: OpenAI returned empty/truncated (%d words), retrying with Claude",
                section_key, len((result or "").split()),
            )
            result = await _call_anthropic(prompt, system_prompt, section_key, max_tokens=max_out_tokens)

    duration = time.time() - start
    word_count = len((result or "").split())
    logger.info(
        "[Strategy] Section %s: %d words in %.1fs (anthropic=%s)",
        section_key, word_count, duration, route_to_anthropic,
    )

    # FIX-S9-B2: Customer-friendly fallback instead of technical error message
    if not result or len(result.split()) < 10:
        return (
            "<p><em>Die Tool-Landschaft und Empfehlungen werden in einem Update nachgeliefert. "
            "Kontaktieren Sie uns unter kontakt@ki-sicherheit.jetzt für Details.</em></p>"
        )

    return result


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

        from services.llm_client import maybe_openai_temperature
        create_kwargs: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "max_completion_tokens": max_tokens,
            **maybe_openai_temperature(model, 0.3),
        }
        _m = model.lower()
        if any(_m.startswith(p) for p in ("gpt-5", "o1", "o3", "o4")):
            from services.llm_client import get_reasoning_effort
            create_kwargs["reasoning_effort"] = get_reasoning_effort()

        def _openai_call() -> Any:
            return client.chat.completions.create(**create_kwargs)

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
            # FIX-S9-B2: Return None on truncation so retry logic in _generate_section triggers
            return None

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

def _bundesland_label(raw: str, country: str = "DE") -> str:
    """Map raw bundesland/region code to readable label for prompts (country-aware)."""
    from services.answers_normalizer import get_region_label
    return get_region_label(raw, country=country) or str(raw or "")


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
        from utils.logo_embedder import embed_logos_in_html, convert_webp_paths_to_png_base64
        import os
        _tpl_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        html_content = embed_logos_in_html(html_content, _tpl_dir)
        html_content = convert_webp_paths_to_png_base64(html_content, _tpl_dir)

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

            # Fire-and-forget: Admin briefing email with questionnaire data
            try:
                _send_admin_briefing_email(briefing_id, db_session)
            except Exception as admin_exc:
                logger.error("[Strategy %d] Admin briefing email failed: %s", briefing_id, admin_exc, exc_info=True)
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

    from utils.report_display_id import get_report_display_id
    _display = get_report_display_id(briefing_id)
    attachment = {
        "filename": f"KI-Strategiebericht-{_display}.pdf",
        "content": pdf_bytes,
        "mimetype": "application/pdf",
    }
    subject = f"Ihr KI-Strategiebericht ({_display})"

    # --- User email ---
    if user_email:
        ok, err = _send_email_via_resend(
            user_email,
            subject,
            render_strategy_email(recipient="user", briefing_id=briefing_id),
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
# ADMIN BRIEFING EMAIL (Fragebogen-Daten)
# =============================================================================

def _send_admin_briefing_email(briefing_id: int, db_session: Any) -> None:
    """Send admin email with all questionnaire data (R1 + Strategy) after strategy generation.

    Fire-and-forget: errors are logged but never propagated.
    """
    import os
    import time as _time

    run_tag = f"ADMIN-BRIEFING-{briefing_id}"
    logger.info("[%s] _send_admin_briefing_email called", run_tag)

    if os.getenv("DISABLE_EMAILS", "").lower() in ("1", "true", "yes", "on"):
        logger.info("[%s] Emails disabled via DISABLE_EMAILS. Skipping.", run_tag)
        return

    try:
        from gpt_analyze import _send_email_via_resend, _mask_email
        from services.email_templates import render_admin_briefing_email
        from models import Briefing, StrategyQuestion, Analysis
        logger.info("[%s] Imports OK", run_tag)
    except ImportError as exc:
        logger.error("[%s] Import FAILED, skipping: %s", run_tag, exc)
        return

    # --- Load briefing ---
    briefing = db_session.query(Briefing).filter(Briefing.id == briefing_id).first()
    if not briefing:
        logger.warning("[%s] Briefing not found, skipping.", run_tag)
        return

    r1_answers: dict = briefing.answers or {}

    # --- Load strategy questions ---
    sq = db_session.query(StrategyQuestion).filter(
        StrategyQuestion.briefing_id == briefing_id
    ).first()
    strategy_answers: dict = sq.to_dict() if sq else {}

    # --- Load meta data from Analysis (Report 1) ---
    analysis = db_session.query(Analysis).filter(
        Analysis.briefing_id == briefing_id
    ).first()
    analysis_meta = analysis.meta if analysis else {}
    scores = analysis_meta.get("scores", {}) if isinstance(analysis_meta, dict) else {}

    # Derive segment label
    from services.answers_normalizer import (
        BRANCHEN_LABELS, UNTERNEHMENSGROESSEN_LABELS,
        UNTERNEHMENSGROESSE_MAP, get_region_label,
    )
    from utils.report_display_id import get_report_display_id

    size_raw = str(r1_answers.get("unternehmensgroesse", "") or "").strip().lower()
    # Normalize raw questionnaire values (e.g. "1" → "solo") before label lookup
    size_normalized = UNTERNEHMENSGROESSE_MAP.get(size_raw, size_raw)
    segment = UNTERNEHMENSGROESSEN_LABELS.get(
        size_normalized,
        size_normalized if size_normalized else "\u2014",
    )

    # Derive branche label (prefer enriched label, then resolve raw key)
    branche_raw = r1_answers.get("branche", "")
    branche = (
        r1_answers.get("BRANCHE_LABEL")
        or BRANCHEN_LABELS.get(str(branche_raw).lower(), str(branche_raw) if branche_raw else "\u2014")
    )

    # Derive region label (country-aware: CH→Kantone, AT→Bundesländer, GB→Regions)
    country_raw = r1_answers.get("country", r1_answers.get("land", ""))
    country_code = str(country_raw).strip().upper() if country_raw else "DE"
    if country_code not in ("DE", "AT", "CH", "GB"):
        country_code = "DE"

    bundesland_raw = r1_answers.get("bundesland", "")
    region = (
        r1_answers.get("BUNDESLAND_LABEL")
        or get_region_label(bundesland_raw, country=country_code)
        or "\u2014"
    )

    # Country label (show when not DE)
    country_labels = {"AT": "Österreich", "CH": "Schweiz", "GB": "Vereinigtes Königreich"}
    country_label = country_labels.get(country_code, "")
    if country_label:
        region = f"{region} / {country_label}" if region and region != "\u2014" else country_label

    score = scores.get("overall", "\u2014")
    kis_number = get_report_display_id(briefing_id)

    meta = {
        "segment": segment,
        "branche": branche,
        "region": region,
        "score": score,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "kis_number": kis_number,
    }

    # --- Build subject ---
    subject = f"[KIS-Admin] Briefing #{briefing_id} / {kis_number} \u2014 {branche} / {segment} / {region}"

    # --- Render HTML ---
    html_body = render_admin_briefing_email(
        briefing_id=briefing_id,
        meta=meta,
        r1_answers=r1_answers,
        strategy_answers=strategy_answers,
    )

    # --- FIX-KIS-1090: Generate Briefing-PDF attachment ---
    _briefing_attachments = []
    try:
        from services.email_templates import render_briefing_pdf_html
        from services.pdf_client import render_pdf_from_html

        _sections = analysis_meta.get("sections", {}) if isinstance(analysis_meta, dict) else {}
        _created = getattr(briefing, "created_at", None)
        _datum = _created.strftime("%d.%m.%Y %H:%M") if _created else ""

        _briefing_html = render_briefing_pdf_html(
            display_id=kis_number,
            datum=_datum,
            answers=r1_answers,
            scores=scores,
            sections=_sections,
            strategy_answers=strategy_answers,
        )
        _pdf_result = render_pdf_from_html(
            _briefing_html,
            pdf_options={"format": "A4", "margin": {"top": "15mm", "bottom": "15mm", "left": "10mm", "right": "10mm"}},
        )
        _pdf_bytes = _pdf_result.get("pdf_bytes")
        if _pdf_bytes:
            _briefing_attachments.append({
                "filename": f"Briefing-{kis_number}.pdf",
                "content": _pdf_bytes,
                "mimetype": "application/pdf",
            })
            logger.info("[%s] Generated Briefing-PDF attachment (%d bytes)", run_tag, len(_pdf_bytes))
        else:
            logger.warning("[%s] Briefing-PDF: no pdf_bytes from Puppeteer", run_tag)
    except Exception as _bp_err:
        logger.warning("[%s] Briefing-PDF generation failed (continuing): %s", run_tag, str(_bp_err)[:200])

    # --- Send ---
    admin_addr = "bewertung@ki-sicherheit.jetzt"
    _time.sleep(0.6)  # Resend rate limit
    ok, err = _send_email_via_resend(admin_addr, subject, html_body, attachments=_briefing_attachments or None)
    if ok:
        logger.info("[%s] Admin briefing email sent to %s", run_tag, _mask_email(admin_addr))
    else:
        logger.warning("[%s] Admin briefing email failed: %s", run_tag, err)


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
    raw_sections: Optional[Dict[str, str]] = None,
) -> None:
    """Save generated sections + timing in DB."""
    from models import StrategyReport

    sr = db_session.query(StrategyReport).filter(
        StrategyReport.briefing_id == briefing_id
    ).first()
    if sr:
        sr.sections = sections
        if raw_sections is not None:
            sr.raw_sections = raw_sections
        sr.research_duration_seconds = r_dur
        sr.generation_duration_seconds = g_dur
        sr.total_duration_seconds = t_dur
        sr.updated_at = datetime.now(timezone.utc)
        db_session.commit()
