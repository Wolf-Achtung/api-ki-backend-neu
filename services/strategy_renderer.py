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

from services.answers_normalizer import BRANCHEN_LABELS
from utils.report_display_id import get_report_display_id as _get_display_id

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


# FIX-PROMPT-LEAK: Patterns where LLM references its input data/context.
# These should never appear in customer-facing output.
_PROMPT_LEAK_PATTERNS = [
    (re.compile(r'(?:im|nicht im)\s+bereitgestellten\s+Material\s+(?:nicht\s+)?beziffert', re.IGNORECASE), 'Auf Anfrage'),
    (re.compile(r'(?:aus|in)\s+(?:den\s+)?(?:bereitgestellten|verfügbaren)\s+(?:Quellen|Daten|Unterlagen|Informationen)\s+(?:nicht\s+)?(?:ersichtlich|beziffert|bekannt|genannt|aufgeführt|spezifiziert)', re.IGNORECASE), 'Auf Anfrage'),
    (re.compile(r'(?:im|aus dem)\s+(?:bereitgestellten|verfügbaren|vorliegenden)\s+(?:Material|Kontext)\s+(?:nicht\s+)?(?:genannt|aufgeführt|spezifiziert|beziffert|ersichtlich|bekannt)', re.IGNORECASE), 'Auf Anfrage'),
    (re.compile(r'laut\s+(?:den\s+)?bereitgestellten\s+(?:Daten|Unterlagen|Informationen)', re.IGNORECASE), ''),
    (re.compile(r'(?:die|keine)\s+(?:bereitgestellten|verfügbaren)\s+(?:Daten|Informationen|Quellen)\s+(?:enthalten|zeigen|nennen)', re.IGNORECASE), ''),
]


def _strip_prompt_leaks(html: str) -> str:
    """Remove LLM meta-language about data sources from any section."""
    if not html:
        return html
    result = html
    count = 0
    for pattern, replacement in _PROMPT_LEAK_PATTERNS:
        result, n = pattern.subn(replacement, result)
        count += n
    if count > 0:
        logger.info("[FIX-PROMPT-LEAK] Removed %d prompt-leak pattern(s)", count)
    return result


def _strip_funding_total(s7_html: str) -> str:
    """Remove misleading cross-program funding total from S7 HTML."""
    if not s7_html:
        return s7_html
    cleaned, count = _FUNDING_TOTAL_PATTERN.subn('', s7_html)
    if count > 0:
        logger.info("[B42-FUNDING] Removed %d misleading funding total(s) from S7", count)
    return cleaned


def inject_opex_bridge(s5_html: str, software_monatlich: str) -> str:
    """FIX-KIS-1188-ITEM2: Append the OPEX-methodology bridge to Strategy S5.

    Strategy includes Software + Tool-Lizenzen + anteilige Betriebskosten;
    R1/KPA report only Software-Grundkosten (120 €/Mo). Customers with high
    AI literacy spot the gap without an explicit bridge.

    Returns the S5 HTML with the bridge appended. If either input is empty
    the original HTML is returned unchanged.
    """
    if not s5_html or not software_monatlich:
        return s5_html
    bridge = (
        '\n<div class="methodik-hinweis methodik-hinweis--opex" '
        'style="margin-top:16px;padding:10px 14px;'
        'background:#f0f4f8;border-left:3px solid #3b82f6;'
        'font-size:0.85em;color:#475569;">'
        '<strong>ℹ️ OPEX-Methodik:</strong> '
        f'Die in diesem Strategiebericht ausgewiesenen {software_monatlich} €/Monat '
        'umfassen Software-Lizenzen, Tool-Abos und anteilige Betriebskosten '
        '(Wartung, Support, Backup). '
        'Der KI-Status-Report kalkuliert demgegenüber mit reinen '
        'Software-Grundkosten von 120 €/Monat. '
        'Beide Werte sind methodisch korrekt; sie beschreiben unterschiedliche '
        'Kostenumfänge derselben Investition.'
        '</div>'
    )
    return s5_html + bridge


def _append_contradictions_box(s1_html: str, briefing_data: dict) -> str:
    """KIS-1235: Deterministische Spannungs-Box ans Ende von Kapitel 1.

    Lauf 1235: Der Prompt-Block (P2) führte nur zu 1 von 4 thematisierten
    Angaben-Spannungen — die Box rendert alle erkannten Spannungen als
    beratende Einordnung, unabhängig vom LLM.
    """
    if not s1_html or "Was Ihre Angaben zeigen" in s1_html:
        return s1_html
    try:
        from services.briefing_contradictions import build_contradictions_box_html
        box = build_contradictions_box_html(briefing_data or {})
        if box:
            return s1_html + "\n" + box
    except Exception:
        pass
    return s1_html


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
    # KIS-1235: FB2-Antworten für die Spannungs-Box mitladen (Tools-,
    # Engpass- und Datenreife-Regeln lesen s5_software/s4_engpass etc.).
    try:
        from models import StrategyQuestion as _SQ1235
        _sq_row = db_session.query(_SQ1235).filter(_SQ1235.briefing_id == sr.briefing_id).first()
        if _sq_row is not None and "_strategy_answers" not in briefing_data:
            briefing_data = {**briefing_data, "_strategy_answers": _sq_row.to_dict()}
    except Exception:
        pass

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

    # KIS-1126 / C1 FIX: Always use deterministic absolute label from get_score_label()
    # to ensure cross-report consistency (R1, KPA, Strategy all show same label for same score)
    if readiness_score > 0:
        try:
            from services.extra_sections import get_score_label
            reifegrad_label = get_score_label(readiness_score, lang="de")
            logger.info("[Strategy-Score] reifegrad_label from deterministic lookup: %s (score=%d)",
                        reifegrad_label, readiness_score)
        except Exception:
            if not reifegrad_label:
                reifegrad_label = report1_sections.get("score_rating", "")

    # Branche: use canonical display label (KIS-1116 Fix 1)
    branche_raw = briefing_data.get("branche", "")
    branche_label = BRANCHEN_LABELS.get(branche_raw.lower(), branche_raw.title()) if branche_raw else ""

    # Research date from report1 or generation date (always German DD.MM.YYYY format)
    research_date = report1_meta.get("research_last_updated", "")
    if not research_date:
        research_date = (sr.updated_at or datetime.now()).strftime("%d.%m.%Y")
    else:
        # Convert ISO format (2026-03-23) to German format (23.03.2026)
        try:
            if "-" in research_date and len(research_date) == 10:
                from datetime import datetime as _dt
                research_date = _dt.strptime(research_date, "%Y-%m-%d").strftime("%d.%m.%Y")
        except (ValueError, TypeError):
            pass  # Keep original if parsing fails

    # Segment label — briefing stores "1", "2–10", "11–100" or "solo", "team", "kmu"
    segment_map = {
        # Numeric strings (from briefing form)
        "1": "Einzelunternehmer",
        "2–10": "Kleinunternehmen (2-10 MA)",
        "2-10": "Kleinunternehmen (2-10 MA)",
        "11–100": "KMU (11–100 MA)",
        "11-100": "KMU (11–100 MA)",
        # Canonical keys (from normalization)
        "solo": "Einzelunternehmer",
        "team": "Kleinunternehmen (2-10 MA)",
        "small": "Kleinunternehmen (2-10 MA)",
        "kmu": "KMU (11–100 MA)",
        "medium": "KMU (11–100 MA)",
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

    # FIX-EXEC-METHODIK: Append ROI methodology note to exec_summary so readers
    # understand why Strategy ROI differs from R1/KPA ROI (12-month TCO vs CAPEX-only).
    _exec_body = sections.get("exec_summary", "")
    _strat_budget = calculated_values.get("budget_gesamt_jahr1", "")
    _r1_capex = report1_sections.get("capex", report1_sections.get("bc_capex", report1_meta.get("capex", "")))
    if _exec_body and _strat_budget:
        _r1_label = f" ({_r1_capex} € CAPEX)" if _r1_capex else ""
        _exec_body += (
            '\n<div class="methodik-hinweis" style="margin-top:16px;padding:10px 14px;'
            'background:#f0f4f8;border-left:3px solid #3b82f6;font-size:0.85em;color:#475569;">'
            '<strong>\u2139\uFE0F ROI-Methodik:</strong> '
            f'Dieser Strategiebericht kalkuliert mit der Gesamtinvestition \u00fcber 12 Monate '
            f'({_strat_budget} \u20ac, inkl. Software, Implementierung, Schulung, Koordination). '
            f'Der KI-Readiness Report rechnet mit einer einmaligen Startinvestition{_r1_label}. '
            'Abweichende ROI- und Break-Even-Werte sind methodisch bedingt, nicht widerspr\u00fcchlich.'
            '</div>'
        )

    # KIS-1011-V1a / KIS-1110-P3: Inject "Mit Förderung" box into exec summary
    # for ALL segments when funding potential > 0 (not just low-ROI reports).
    try:
        _roi_real_str = calculated_values.get("roi_realistisch", "0")
        _foerder_str = calculated_values.get("foerder_potenzial", "0")
        _gesamt_str = calculated_values.get("budget_gesamt_jahr1", "0")
        _ersparnis_str = calculated_values.get("jaehrliche_ersparnis", "0")
        _monat_str = calculated_values.get("zeitersparnis_euro", "0")

        # Parse German format "48.000" → 48000
        def _parse_de(s: str) -> int:
            return int(str(s).replace(".", "").replace(",", "").strip() or "0")

        _roi_real = int(_roi_real_str) if _roi_real_str.lstrip("-").isdigit() else 0
        _foerder = _parse_de(_foerder_str)
        _gesamt = _parse_de(_gesamt_str)
        _ersparnis = _parse_de(_ersparnis_str)
        _monat_spar = _parse_de(_monat_str)

        # Plausibility cap: funding may not exceed 70% of total investment
        _foerder_capped = min(_foerder, int(_gesamt * 0.7))

        if _foerder_capped > 0 and _gesamt > _foerder_capped and _monat_spar > 0:
            import math as _math
            _netto_invest = _gesamt - _foerder_capped
            _netto_roi = round((_ersparnis - _netto_invest) / _netto_invest * 100)
            _netto_be = _math.ceil(_netto_invest / _monat_spar)
            # KIS-1232: Anzeige-Cap analog zur 200-%-Philosophie des
            # KI-Readiness-Reports \u2014 "267 %" wirkte neben dem
            # realistischen 38-%-Szenario unglaubw\u00fcrdig aggressiv.
            _netto_roi_display = "\u00fcber 200" if _netto_roi > 200 else str(_netto_roi)

            def _fmt_eur(v: int) -> str:
                return f"{v:,}".replace(",", ".")

            # FIX-KIS-1188-ITEM3: explain the 70%-plausibility cap and reference
            # concrete programmes so the 8.400 \u20ac-style number isn't perceived
            # as arbitrary.
            # FIX-KIS-1027.4-3D: Wolf-Decision "Annahme transparent machen".
            # Headline beh\u00e4lt Wirkung, bekommt aber explizite Zusatz-Zeile,
            # dass die 70\u00a0% nur bei Programm-Kombination erreichbar sind
            # (z.\u00a0B. Bundes- plus Landesf\u00f6rderung). KIS-1237: Solo-Programm aus dem\n            # Beispieltext entfernt \u2014 das Programm richtet sich an Solo-\n            # Selbstst\u00e4ndige und stand in Kapitel 7 des KMU-Laufs 1119 nie drin\n            # (Exec Summary verwies damit auf ein unbelegtes Programm).
            # Verhindert, dass Leser den Headline-ROI als Einzelprogramm-
            # Standardfall interpretieren.
            _foerder_note = (
                f'\n<div style="margin-top:12px;padding:12px 16px;'
                f'background:linear-gradient(135deg,#ecfdf5,#d1fae5);'
                f'border-left:4px solid #10b981;border-radius:6px;'
                f'font-size:0.95em;color:#065f46;">'
                f'<strong>Mit F\u00f6rderung:</strong> '
                f'Unter Ber\u00fccksichtigung eines F\u00f6rderpotenzials von bis zu 70\u00a0% '
                f'der Gesamtinvestition (max. {_fmt_eur(_foerder_capped)}\u00a0\u20ac) '
                f'reduziert sich Ihre Nettoinvestition auf {_fmt_eur(_netto_invest)}\u00a0\u20ac '
                f'\u2014 mit einem Netto-ROI von {_netto_roi_display}\u00a0% '
                f'und Break-Even bereits in Monat\u00a0{_netto_be}. '
                f'<br>'
                f'<span style="font-size:0.85em;color:#047857;">'
                f'<strong>Hinweis zur Annahme:</strong> '
                f'Die 70\u00a0%-Quote ist ein <em>Plausibilit\u00e4ts-Cap</em> bei '
                f'vollst\u00e4ndiger Aussch\u00f6pfung der in Kapitel\u00a07 '
                f'(F\u00f6rdermittel &amp; Finanzierung) beschriebenen Programme \u2014 '
                f'typischerweise durch Kombination einer Bundes- mit einer '
                f'Landesf\u00f6rderung (etwa BAFA plus regionale Digitalpr\u00e4mien). '
                f'Ein einzelnes F\u00f6rderprogramm '
                f'erreicht meist 50\u201360\u00a0%. Pr\u00fcfen Sie die Kombinations'
                f'm\u00f6glichkeiten f\u00fcr Ihre Region.'
                f'</span>'
                f'</div>'
            )
            _exec_body += _foerder_note
            logger.info(
                "[KIS-1110-P3] Injected net-ROI: netto_invest=%d, netto_roi=%d%%, "
                "netto_breakeven=%d mo (gross_roi=%d%%, foerder_raw=%d, foerder_capped=%d)",
                _netto_invest, _netto_roi, _netto_be, _roi_real, _foerder, _foerder_capped,
            )
    except Exception as _e:
        logger.warning("[KIS-1110-P3] Failed to inject net-ROI: %s", _e)

    # FIX-KIS-1188-ITEM2: OPEX-bridge appended to S5 (helper is unit-tested).
    sections["S5"] = inject_opex_bridge(
        sections.get("S5", ""),
        calculated_values.get("budget_software_monatlich", ""),
    )

    # KIS-1235: Der Firmenname wird aus Datenschutzgründen bewusst nie
    # erhoben — statt des Platzhalters "Ihr Unternehmen · Beratung &
    # Dienstleistungen" zeigt das Deckblatt ein sprechendes Profil
    # ("Solo-Beratung · Berlin").
    _firmenname = str(briefing_data.get("unternehmen_name") or "").strip()
    if not _firmenname:
        _seg = (segment_label or "").strip()
        _bl = str(briefing_data.get("bundesland") or "").strip()
        if _bl:
            try:
                from services.chat_normalizer import BUNDESLAND_LABELS
                _bl = BUNDESLAND_LABELS.get(_bl, _bl.title() if _bl == _bl.lower() else _bl)
            except Exception:
                pass
        if _seg and _bl:
            _firmenname = f"{_seg} · {_bl}"
        elif _seg:
            _firmenname = _seg
        else:
            _firmenname = "Ihr Unternehmen"

    context = {
        # Cover metadata
        "firmenname": _firmenname,
        "branche": branche_label,
        "datum": datetime.now().strftime("%d.%m.%Y"),
        "segment": segment_label,
        "mitarbeiter": mitarbeiter,
        "readiness_score": readiness_score,
        "reifegrad_label": reifegrad_label,
        "research_date": research_date,
        "report_id": f"STR-{sr.briefing_id}",
        "build_id": os.getenv("BUILD_ID", ""),
        # Unified customer-facing report number (KIS-XXXX)
        "REPORT_DISPLAY_ID": _get_display_id(sr.briefing_id),
        # Sections
        "exec_summary": _exec_body,
        "section_s1": _append_contradictions_box(
            _strip_prompt_leaks(sections.get("S1", "")), briefing_data,
        ),
        "section_s2": _strip_prompt_leaks(sections.get("S2", "")),
        "section_s3": _strip_prompt_leaks(sections.get("S3", "")),
        "section_s3b": _strip_prompt_leaks(sections.get("S3b", "")),
        "section_s4": _strip_prompt_leaks(sections.get("S4", "")),
        "section_s5": _strip_prompt_leaks(sections.get("S5", "")),
        "section_s6": _strip_prompt_leaks(sections.get("S6", "")),
        "section_s7": _strip_prompt_leaks(_strip_funding_total(sections.get("S7", ""))),
        "section_s8": _strip_prompt_leaks(sections.get("S8", "")),
        "section_s_moat": _strip_prompt_leaks(sections.get("s_moat", "")),
        # KIS-1142 Punkt 5: Persönliche Einschätzung (Strategy-Äquivalent zum
        # R1 advisor_note). Rendered between s_moat and "Nächste Schritte".
        "section_advisor_note": _strip_prompt_leaks(sections.get("advisor_note", "")),
        "naechste_schritte": naechste_schritte,
    }

    # KIS-1128 audit M11: warn on empty required keys (silent-loss detector).
    try:
        from services.coverage_guard import audit_render_context
        audit_render_context("strategy", context, report_id=str(context.get("report_id") or ""))
    except Exception as _e:
        import logging as _logging
        _logging.getLogger(__name__).debug("audit_render_context failed: %s", _e)

    html = str(template.render(**context))

    # Post-process LLM HTML to use CSS design classes (KPI cards, timelines, etc.)
    from services.html_enhancer import enhance_strategy_html
    html = enhance_strategy_html(html)

    # Safety net: enforce canonical budget values in final HTML
    if calculated_values:
        html = _enforce_budget_values(html, calculated_values, sr.briefing_id)

    # KIS-1235: Finaler Textmechanik-Pass (analog report_renderer) — v. a.
    # Soft-Hyphens für die 6-7-spaltigen Tabellen (Prioritätsmatrix,
    # Tool-/Fördertabellen), die Headless-Chromium sonst ohne Trennstrich
    # mitten im Wort umbricht ("HANDLUN GSFELD", Lauf 1235).
    try:
        from services.style_lint import (
            fix_missing_sentence_space as _sf_fss,
            remove_punctuation_only_nodes as _sf_rpn,
            soften_table_long_words as _sf_shy,
            fix_double_periods as _sf_fdp,
            fix_misc_typography as _sf_fmt,
        )
        html, _s1 = _sf_fss(html)
        html, _s2 = _sf_rpn(html)
        html, _s3 = _sf_shy(html)
        html, _s4 = _sf_fdp(html)
        html, _s5 = _sf_fmt(html)
        if _s1 or _s2 or _s3 or _s4 or _s5:
            import logging as _lg
            _lg.getLogger(__name__).info(
                "[KIS-1235][STRATEGY-TEXTMECHANIK] spaces=%d punct_nodes=%d shy_words=%d periods=%d typo=%d",
                _s1, _s2, _s3, _s4, _s5,
            )
    except Exception:  # pragma: no cover
        pass

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
