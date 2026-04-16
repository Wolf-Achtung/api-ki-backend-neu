# -*- coding: utf-8 -*-
"""
routes/chat.py — Conversational AI Questionnaire

Endpoints:
  POST /api/chat/start        — Start new chat session
  POST /api/chat/message       — Process user message + stream AI response (SSE)
  GET  /api/chat/session/{id}  — Get session state (for resume / frontend init)
  POST /api/chat/complete      — Finalize session and submit to report pipeline
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text as _sa_text

from models import Briefing, ChatSession, User
from routes._bootstrap import get_db
from schemas.chat import (
    ChatCompleteRequest,
    ChatCompleteResponse,
    ChatMessage,
    ChatMessageRequest,
    ChatSessionResponse,
    ChatSessionState,
    ChatSessionSummary,
    ChatStartRequest,
    ChatStartResponse,
    ConfirmFieldRequest,
    QuickReply,
    QuickReplyOption,
)
from services.chat_normalizer import (
    BUNDESLAND_LABELS,
    BUNDESLAND_VALUES,
    ENUM_VALUES,
    FIELD_REGISTRY,
    SECTIONS,
    STRATEGY_ENUM_VALUES,
    STRATEGY_FIELD_REGISTRY,
    STRATEGY_SECTIONS,
    calculate_progress,
    compute_user_profile,
    get_enum_values_for_report,
    get_field_label,
    get_missing_fields,
    get_next_fields,
    get_registry_for_report,
    get_sections_for_report,
    is_field_visible,
    is_section_complete,
    normalize_field,
)
from services.field_templates import FIELD_QUESTIONS, get_confirmation, get_template_question, is_template_field

router = APIRouter(prefix="/chat", tags=["chat"])
log = logging.getLogger(__name__)

# Feature flag: Draft-Pattern (Sprint 1 infra — default off)
DRAFT_MODE_ENABLED = os.getenv("DRAFT_MODE_ENABLED", "false").lower() == "true"

# KIS-1131: Canonical summary marker — used for both emission and detection.
SUMMARY_MARKER = "**Zusammenfassung Ihrer Angaben:**"

# ---------------------------------------------------------------------------
# KIS-1124 Sprint 2: Hybrid Conversation Model — Phase & Block Definitions
# ---------------------------------------------------------------------------

# Phase 1 required fields — must be collected before checkpoint
PHASE_1_FIELDS: list[str] = [
    "branche", "unternehmensgroesse", "country", "bundesland",
    "hauptleistung", "ki_kompetenz", "digitalisierungsgrad",
    "ki_ziele", "investitionsbudget",
]

# Phase 1a: QR fields collected sequentially (ordered)
PHASE_1A_QR_FIELDS: list[str] = [
    "branche", "unternehmensgroesse", "selbststaendig",
    "country", "bundesland",
    "investitionsbudget",
]

# Phase 1b: Open conversation fields (extracted via multi-field Haiku)
PHASE_1B_OPEN_FIELDS: list[str] = [
    "hauptleistung", "ki_kompetenz", "digitalisierungsgrad", "ki_ziele",
]

# Fields that need QR buttons in Phase 1 (not extractable from free text)
PHASE_1_QR_FIELDS: set[str] = set(PHASE_1A_QR_FIELDS)

# Fields that Haiku can extract from free conversation in Phase 1
PHASE_1_EXTRACTABLE_FIELDS: set[str] = {
    "hauptleistung", "ki_kompetenz", "digitalisierungsgrad",
    "ki_ziele", "zielgruppen", "jahresumsatz", "ki_einsatz",
}


def _get_datenschutz_block_fields(branche: str) -> list[str]:
    """Return Block D fields based on branche (Beratung → reduced set)."""
    if branche == "beratung":
        return ["datenschutz", "datenschutzbeauftragter", "ai_act_kenntnis",
                "ki_hemmnisse", "governance_richtlinien"]
    return [
        "datenschutz", "datenschutzbeauftragter", "technische_massnahmen",
        "folgenabschaetzung", "meldewege", "loeschregeln",
        "ai_act_kenntnis", "regulierte_branche", "ki_hemmnisse",
        "governance_richtlinien",
    ]


# Phase 2 thematic blocks
# Every R1 field must be in exactly ONE location:
#   Phase 1a (QR), Phase 1b (open), or one Block (A/B/C/D).
BLOCK_FIELDS: dict[str, list[str]] = {
    "A": [
        "bisherige_foerdermittel", "interesse_foerderung",
        "erfahrung_beratung", "marktposition",
        "benchmark_wettbewerb", "risikofreude", "jahresumsatz",
    ],
    "B": [
        "vision_3_jahre", "strategische_ziele", "ki_guardrails",
        "geschaeftsmodell_evolution", "roadmap_vorhanden",
        "change_management", "massnahmen_komplexitaet",
        "vision_prioritaet", "innovationsprozess",
        "zielgruppen",          # S3-BE-1: was orphan (Section 1)
    ],
    "C": [
        "automatisierungsgrad", "ki_einsatz", "anwendungsfaelle",
        "ki_projekte", "pilot_bereich", "zeitersparnis_prioritaet",
        "vorhandene_tools", "trainings_interessen", "zeitbudget",
        "prozesse_papierlos",
        "it_infrastruktur",     # S3-BE-1: was orphan (Section 1)
        "interne_ki_kompetenzen",  # S3-BE-1: was orphan (Section 1)
        "datenquellen",         # S3-BE-1: was orphan (Section 1)
    ],
    # Block D is dynamic — see _get_datenschutz_block_fields()
}

BLOCK_LABELS: dict[str, str] = {
    "A": "Fördermittel & Budget",
    "B": "KI-Strategie & Roadmap",
    "C": "Tools & Automatisierung",
    "D": "Recht & Datenschutz",
}


# KIS-1124 Testrun 6 Fix 2: Conservative defaults for fields that couldn't
# be extracted after 2 attempts. Better to move on than loop.
_FIELD_DEFAULTS: dict[str, object] = {
    "marktposition": "unsicher",
    "benchmark_wettbewerb": "selten",
    "risikofreude": 3,  # Midpoint of 1-5
    "bisherige_foerdermittel": "nein",
    "interesse_foerderung": "unklar",
    "erfahrung_beratung": "unklar",
    "roadmap_vorhanden": "nein",
    "governance_richtlinien": "nein",
    "massnahmen_komplexitaet": "unklar",
    "change_management": "mittel",
    "datenschutzbeauftragter": "nein",
    "technische_massnahmen": "teilweise",
    "folgenabschaetzung": "nein",
    "meldewege": "nein",
    "loeschregeln": "nein",
    "ai_act_kenntnis": "unbekannt",
    "automatisierungsgrad": "mittel",
    "it_infrastruktur": "unklar",
    "interne_ki_kompetenzen": "nein",
}


# KIS-1124 Sprint 4 S4-BE-2: Conservative defaults for fields in blocks that
# the user chose NOT to survey.  These are injected at _complete_r1 time so
# the report pipeline receives plausible, non-hallucinated values.
# Fields set to None are intentionally omitted → pipeline produces shorter /
# "recommend deepening" sections.
_REPORT_BLOCK_DEFAULTS: dict[str, dict[str, object]] = {
    "A": {
        "bisherige_foerdermittel": "nein",
        "interesse_foerderung": "unklar",
        "erfahrung_beratung": "unklar",
        "marktposition": "unsicher",
        "benchmark_wettbewerb": "selten",
        "risikofreude": 3,
        "jahresumsatz": None,   # omit — no guessing revenue
    },
    "B": {
        "vision_3_jahre": None,              # omit — pipeline skips section
        "strategische_ziele": None,          # omit
        "ki_guardrails": None,               # omit
        "geschaeftsmodell_evolution": None,   # omit
        "roadmap_vorhanden": "nein",
        "change_management": "mittel",
        "massnahmen_komplexitaet": "unklar",
        "vision_prioritaet": None,           # omit
        "innovationsprozess": None,          # omit
        "zielgruppen": None,                 # omit
    },
    "C": {
        "automatisierungsgrad": "mittel",
        "ki_einsatz": "nein",
        "anwendungsfaelle": None,            # omit
        "ki_projekte": None,                 # omit
        "pilot_bereich": None,               # omit
        "zeitersparnis_prioritaet": None,    # omit
        "vorhandene_tools": None,            # omit
        "trainings_interessen": None,        # omit
        "zeitbudget": None,                  # omit
        "prozesse_papierlos": None,          # omit
        "it_infrastruktur": "unklar",
        "interne_ki_kompetenzen": "nein",
        "datenquellen": None,               # omit
    },
    "D": {
        "datenschutzbeauftragter": None,     # omit
        "technische_massnahmen": None,       # omit
        "folgenabschaetzung": None,          # omit
        "meldewege": None,                   # omit
        "loeschregeln": None,                # omit
        "ai_act_kenntnis": "nein",
        "regulierte_branche": None,          # omit
        "ki_hemmnisse": None,                # omit
        "governance_richtlinien": "nein",
    },
}


def _get_block_fields(block_id: str, collected_fields: dict) -> list[str]:
    """Get remaining (uncollected) fields for a block."""
    if block_id == "D":
        branche = collected_fields.get("branche", "")
        all_fields = _get_datenschutz_block_fields(branche)
    else:
        all_fields = BLOCK_FIELDS.get(block_id, [])
    return [f for f in all_fields if f not in collected_fields]


# ---------------------------------------------------------------------------
# KIS-1128C V6-BE-1: Smart Skip — derive answers for redundant Block C fields
# ---------------------------------------------------------------------------

# Mapping: single anwendungsfall → obvious pilot_bereich
_ANWENDUNG_TO_PILOT: dict[str, str] = {
    "chatbot": "kundenservice",
    "content_generation": "marketing",
    "datenanalyse": "verwaltung",
    "prozess_automation": "verwaltung",
    "dokumentenanalyse": "verwaltung",
    "qualitaetskontrolle": "produktion",
}


def _smart_skip_field(field: str, collected: dict) -> str | None:
    """Return a derived default if *field* can be inferred, else None (= ask).

    Only called for Phase 2 block fields. Every derived value must be
    report-quality — never "keine_angabe".
    """
    digi = collected.get("digitalisierungsgrad")
    ki_komp = collected.get("ki_kompetenz", "")
    groesse = collected.get("unternehmensgroesse", "")
    anwendungen = collected.get("anwendungsfaelle")

    # High digitisation → paperless is nearly 100%
    if field == "prozesse_papierlos" and digi is not None:
        try:
            if int(digi) >= 8:
                return "81-100"
        except (ValueError, TypeError):
            pass

    # Solo entrepreneur → no internal KI team
    if field == "interne_ki_kompetenzen" and groesse == "1":
        return "nein"

    # Single use-case → obvious pilot area
    if field == "pilot_bereich" and isinstance(anwendungen, list) and len(anwendungen) == 1:
        mapped = _ANWENDUNG_TO_PILOT.get(anwendungen[0])
        if mapped:
            return mapped

    # High KI competence → high expansion potential (trivially derivable)
    if field == "ki_ausbau_potenzial" and ki_komp == "hoch":
        return "hoch"

    return None


def _init_phase_state() -> dict:
    """Create initial phase_state for a new R1 session."""
    return {
        "conversation_phase": "phase_1",
        "phase_1_qr_complete": False,
        "selected_blocks": [],
        "completed_blocks": [],
        "current_block": None,
        "block_stale_turns": 0,
        "phase_1b_asked_fields": [],   # KIS-1124 Testrun-Fix Bug 7
        "block_asked_fields": [],      # KIS-1124 Testrun-Fix Bug 8
        "phase_1b_turn_count": 0,      # KIS-1124 Testrun 5 safeguard
        "field_ask_counts": {},        # KIS-1124 Testrun 6 per-field safeguard
    }


def _get_phase_state(session) -> dict:
    """Read phase_state from session, with safe defaults."""
    ps = getattr(session, "phase_state", None) or {}
    return {
        "conversation_phase": ps.get("conversation_phase", "phase_1"),
        "phase_1_qr_complete": ps.get("phase_1_qr_complete", False),
        "selected_blocks": ps.get("selected_blocks", []),
        "completed_blocks": ps.get("completed_blocks", []),
        "current_block": ps.get("current_block"),
        "block_stale_turns": ps.get("block_stale_turns", 0),
        "phase_1b_asked_fields": ps.get("phase_1b_asked_fields", []),
        "block_asked_fields": ps.get("block_asked_fields", []),
        "phase_1b_turn_count": ps.get("phase_1b_turn_count", 0),
        "field_ask_counts": ps.get("field_ask_counts", {}),
    }


def _should_skip_qr_field(field: str, collected: dict) -> bool:
    """Check if a Phase 1a QR field should be skipped due to conditionals."""
    if field == "bundesland" and collected.get("country") not in ("DE", "AT"):
        return True
    if field == "selbststaendig" and collected.get("unternehmensgroesse") != "1":
        return True
    return False


def _is_phase_1a(phase_state: dict, collected: dict) -> bool:
    """Check if we're in Phase 1a (QR fields still missing)."""
    if phase_state.get("conversation_phase") != "phase_1":
        return False
    if phase_state.get("phase_1_qr_complete"):
        return False
    # Check if any QR fields are still missing (skip conditional fields)
    return any(f not in collected for f in PHASE_1A_QR_FIELDS
               if not _should_skip_qr_field(f, collected))


def _is_phase_1b(phase_state: dict, collected: dict) -> bool:
    """Check if we're in Phase 1b (open conversation, QR done)."""
    if phase_state.get("conversation_phase") != "phase_1":
        return False
    return not _is_phase_1a(phase_state, collected)


def _get_next_phase_1a_field(collected: dict) -> str | None:
    """Get the next QR field in Phase 1a sequence."""
    for f in PHASE_1A_QR_FIELDS:
        if _should_skip_qr_field(f, collected):
            continue
        if f not in collected:
            return f
    return None

R1_WELCOME = (
    "Willkommen bei ki-sicherheit.jetzt! Ich führe Sie durch eine "
    "kurze Bestandsaufnahme — in ca. 10–15 Minuten. Am Ende erhalten "
    "Sie einen individuellen KI-Report mit konkreten Empfehlungen "
    "für Ihr Unternehmen. Ihre Angaben werden ausschließlich für "
    "die Analyse verwendet.\n\n"
    "In welcher Branche ist Ihr Unternehmen tätig? "
    "Falls Sie unsicher sind, beschreiben Sie einfach, was Sie tun "
    "— ich helfe bei der Zuordnung."
)

STRATEGY_WELCOME = (
    "Willkommen zurück! Auf Basis Ihrer KI-Readiness-Analyse erstelle ich "
    "jetzt Ihren individuellen KI-Strategiebericht.\n\n"
    "Dafür benötige ich noch einige Angaben zu Ihrer konkreten Umsetzungsplanung. "
    "Das dauert ca. 3 Minuten. Falls Sie bei einer Frage unsicher sind, "
    "fragen Sie einfach nach — ich erkläre gern.\n\n"
    "Beginnen wir: Wie hoch ist Ihr geplantes Budget speziell für die "
    "KI-Implementierung der nächsten 12 Monate?"
)


def _get_welcome(report_type: str) -> str:
    if report_type == "strategy":
        return STRATEGY_WELCOME
    return R1_WELCOME


def _get_first_qr_fields(report_type: str) -> list[str]:
    if report_type == "strategy":
        return ["s1_budget"]
    return ["branche"]


# ===========================================================================
# POST /api/chat/start
# ===========================================================================

@router.post("/start", response_model=ChatStartResponse)
async def chat_start(
    req: ChatStartRequest, request: Request, db: Session = Depends(get_db),
):
    """Start a new chat conversation."""
    if not req.consent_report:
        raise HTTPException(status_code=400, detail="consent_report must be true")

    # Strategy requires a briefing_id
    if req.report_type == "strategy":
        if not req.briefing_id:
            raise HTTPException(status_code=400, detail="briefing_id erforderlich für Strategy-Report")
        briefing = db.query(Briefing).filter(Briefing.id == req.briefing_id).first()
        if not briefing:
            raise HTTPException(status_code=404, detail="Briefing nicht gefunden")

    # Extract user from JWT (optional — unauthenticated sessions work too)
    user_id, user_email = _resolve_user(request, db)

    now = datetime.now(timezone.utc)

    # Initialize phase_state for R1 sessions (hybrid conversation model)
    phase_state = _init_phase_state() if req.report_type == "r1" else {}

    session = ChatSession(
        report_type=req.report_type,
        lang=req.lang,
        consent_report=True,
        consent_at=now,
        collected_fields=req.prefill or {},
        field_meta={},
        current_section=0,
        status="active",
        messages=[],
        turn_count=0,
        briefing_id=req.briefing_id,
        user_id=user_id,
        phase_state=phase_state,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Build initial state
    state = _build_session_state(session)

    # Build welcome quick replies (first field for this report type)
    first_fields = _get_first_qr_fields(req.report_type)
    welcome_qr = _build_quick_replies(first_fields, req.report_type)
    state.quick_replies = welcome_qr

    # Save welcome message
    welcome = _get_welcome(req.report_type)
    welcome_msg = {
        "role": "assistant",
        "content": welcome,
        "timestamp": now.isoformat(),
        "turn": 0,
        "fields_extracted": None,
        "section_index": 0,
        "quick_replies": [qr.model_dump() for qr in welcome_qr] if welcome_qr else None,
    }
    session.messages = [welcome_msg]
    db.commit()

    log.info("[CHAT] Session started: %s (report_type=%s)", session.id, session.report_type)

    return ChatStartResponse(
        session_id=session.id,
        state=state,
        welcome_message=welcome,
    )


# ===========================================================================
# POST /api/chat/message
# ===========================================================================

@router.post("/message")
async def chat_message(req: ChatMessageRequest, db: Session = Depends(get_db)):
    """Process user message, extract fields, stream AI response via SSE."""
    session = db.query(ChatSession).filter(ChatSession.id == req.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session nicht gefunden")
    if session.status != "active":
        raise HTTPException(status_code=400, detail="Session ist nicht aktiv")

    now = datetime.now(timezone.utc)
    session.turn_count += 1
    turn = session.turn_count

    # Save user message
    user_msg = {
        "role": "user",
        "content": req.message,
        "timestamp": now.isoformat(),
        "turn": turn,
    }
    messages = list(session.messages or [])
    messages.append(user_msg)
    session.messages = messages
    session.last_activity_at = now
    session.updated_at = now
    db.commit()

    # Capture values needed inside the stream; actual extraction runs
    # inside event_stream() so the SSE connection starts immediately and
    # heartbeats keep the connection alive during the Haiku call.
    rt = session.report_type
    from services.chat_conversation import (
        generate_response, FIELD_DESCRIPTIONS, build_help_context,
        EDIT_MODE_SONNET_PROMPT, build_edit_extraction_context,
    )

    _HB_INTERVAL = 12  # seconds between keepalive heartbeats

    async def event_stream():
        yield f"event: heartbeat\ndata: {{}}\n\n"

        # ------------------------------------------------------------------
        # Phase 1: Extract fields (inside the stream so heartbeats flow)
        # ------------------------------------------------------------------
        registry = get_registry_for_report(rt)
        normalized = {}

        # Raw SQL read — bypasses ORM stale/expired attribute problem.
        # After db.commit() at l.202 the closure `session` object is
        # unreliable inside this async generator.
        _row = db.execute(
            _sa_text("SELECT collected_fields, field_meta, current_section, draft_state, phase_state "
                     "FROM chat_sessions WHERE id = :sid"),
            {"sid": str(session.id)}
        ).fetchone()
        collected = dict(_row[0] or {})
        field_meta = dict(_row[1] or {})
        _current_section = _row[2]
        _draft_state_snapshot = dict(_row[3] or {})
        _phase_state = dict(_row[4] or {})
        log.info("[CHAT] Turn %d init: collected_keys=%s", turn, list(collected.keys()))

        # Draft-mode tracking variables (only meaningful when DRAFT_MODE_ENABLED)
        _signal = None
        _draft_new_field = None
        _draft_new_value = None
        _draft_confirmed_field = None
        _draft_confirmed_value = None
        _pending_after_turn = False  # True when a pending draft exists AFTER this turn's processing
        _no_extraction = False  # True when free-text yielded no field extraction (user asked a question)
        _asked_field = ""  # The field that was being asked when the user sent this message
        _report_start_requested = False  # True when user clicked "Auswertung starten"

        _is_qr_click = bool(req.quick_reply_field and req.quick_reply_value)
        _is_help_request = "__HELP_REQUEST__" in req.message

        # Edit-mode detection: check if user wants to change a field after summary
        _is_in_edit_mode = bool(_draft_state_snapshot.get("edit_mode"))
        _edit_words = {"ändern", "etwas ändern", "korrigieren", "anpassen", "nein, etwas ändern", "nein ändern"}
        _is_edit_request = (
            not _is_qr_click
            and not _is_help_request
            and _has_summary_been_sent(session)
            and req.message.strip().lower() in _edit_words
        )
        _edit_applied = False  # True when an edit was successfully applied this turn

        if _is_qr_click:
            # Quick reply: direct write, no Draft — user click is explicit confirmation.
            # This applies to both QR (single-select) and MS (multi-select) fields,
            # regardless of DRAFT_MODE_ENABLED. Only free-text goes through Draft.
            qr_field = req.quick_reply_field

            # --- Checkpoint QR handling (Phase 1 → Phase 2 transition) ---
            if qr_field == "__checkpoint__":
                _cp_value = req.quick_reply_value
                if _cp_value == "REPORT":
                    # User wants report now → skip to summary
                    _phase_state["conversation_phase"] = "summary"
                    log.info("[CHAT] Checkpoint: user chose REPORT NOW")
                elif _cp_value == "ALL":
                    _phase_state["conversation_phase"] = "phase_2"
                    _phase_state["selected_blocks"] = ["A", "B", "C", "D"]
                    _phase_state["current_block"] = "A"
                    log.info("[CHAT] Checkpoint: user chose ALL blocks")
                else:
                    # Individual block(s) selected — may be comma-separated
                    _selected = [b.strip() for b in _cp_value.split(",") if b.strip() in BLOCK_LABELS]
                    if _selected:
                        _phase_state["conversation_phase"] = "phase_2"
                        _phase_state["selected_blocks"] = _selected
                        _phase_state["current_block"] = _selected[0]
                        log.info("[CHAT] Checkpoint: user chose blocks %s", _selected)
                    else:
                        log.warning("[CHAT] Checkpoint: invalid selection %r", _cp_value)
                # KIS-1124 Sprint 4 Fix B: Auto-set interesse_foerderung when
                # user chose Block A (Fördermittel & Budget) — interest is obvious.
                _sel = _phase_state.get("selected_blocks", [])
                if "A" in _sel and "interesse_foerderung" not in collected:
                    collected["interesse_foerderung"] = "ja"
                    log.info("[CHAT] Checkpoint: auto-set interesse_foerderung=ja (Block A selected)")

                # Skip normal QR processing for checkpoint
                _no_extraction = True

            # --- Block transition QR handling (Phase 2 inter-block) ---
            elif qr_field == "__block_transition__":
                _bt_value = req.quick_reply_value
                if _bt_value == "report":
                    # User wants report now → skip to summary
                    _phase_state["conversation_phase"] = "summary"
                    log.info("[CHAT] Block transition: user chose REPORT")
                elif _bt_value == "continue":
                    # Continue with next block (current_block already set)
                    _phase_state["block_stale_turns"] = 0
                    _phase_state["block_asked_fields"] = []  # Reset for new block
                    log.info("[CHAT] Block transition: user chose CONTINUE → block %s",
                             _phase_state.get("current_block"))
                _no_extraction = True

            # --- Summary action QR handling (Summary → Report or Edit) ---
            elif qr_field == "__summary_action__":
                _sa_value = req.quick_reply_value
                if _sa_value == "__start_report__":
                    # KIS-1125-HOTFIX: Trigger report completion directly
                    _report_start_requested = True
                    log.info("[CHAT] Summary action: user chose START REPORT")
                elif _sa_value == "__edit_summary__":
                    # User wants to edit → activate edit mode
                    session.draft_state = {
                        **(session.draft_state or {}),
                        "edit_mode": True,
                    }
                    _is_edit_request = True
                    log.info("[CHAT] Summary action: user chose EDIT")
                _no_extraction = True

            # --- Draft housekeeping (pre-step, only when DRAFT_MODE_ENABLED) ---
            # Clears any pending draft. Does NOT affect the QR value write below.
            if DRAFT_MODE_ENABLED:
                _qr_draft = dict(_draft_state_snapshot)
                _qr_pending = _qr_draft.get("pending_field")

                if qr_field == "_draft_action":
                    # Handle confirm/edit QR buttons for pending draft value
                    if _qr_pending and req.quick_reply_value == "confirm":
                        _cf = _qr_draft["pending_field"]
                        _cv = _qr_draft["pending_value"]
                        collected[_cf] = _cv
                        normalized[_cf] = _cv
                        field_meta[_cf] = {
                            "confidence": "high",
                            "source_turn": turn,
                            "raw_input": "confirmed_via_qr",
                            "normalized": True,
                            "confirmed": True,
                        }
                        _draft_confirmed_field = _cf
                        _draft_confirmed_value = _cv
                        log.info("[CHAT] Draft QR confirm: %s=%r", _cf, _cv)
                    else:
                        log.info("[CHAT] Draft QR edit/discard: clearing pending %s", _qr_pending)
                elif _qr_pending:
                    # Regular QR click while draft pending → auto-confirm the pending
                    # value (user explicitly moved on by clicking a different field).
                    _cf = _qr_draft["pending_field"]
                    _cv = _qr_draft["pending_value"]
                    collected[_cf] = _cv
                    normalized[_cf] = _cv
                    field_meta[_cf] = {
                        "confidence": "high",
                        "source_turn": turn,
                        "raw_input": "auto_confirmed_via_qr",
                        "normalized": True,
                        "confirmed": True,
                    }
                    _draft_confirmed_field = _cf
                    _draft_confirmed_value = _cv
                    log.info("[CHAT] Draft auto-confirm (QR click on %s): %s=%r", qr_field, _cf, _cv)
                # Always clear draft state after any QR click
                session.draft_state = {"pending_field": None, "pending_value": None, "dialog_mode": False}

            # --- QR value write (single code path, draft-agnostic) ---
            # KIS-1131 FX-3: Skip meta-fields (__*__) — they are control signals,
            # not data fields, and would produce "Unknown field" warnings in normalize_field.
            if qr_field != "_draft_action" and not qr_field.startswith("__"):
                qr_result = normalize_field(qr_field, req.quick_reply_value, collected, report_type=rt)
                if qr_result.confidence != "low":
                    collected[qr_field] = qr_result.value
                    normalized[qr_field] = qr_result.value
                    field_meta[qr_field] = {
                        "confidence": qr_result.confidence,
                        "source_turn": turn,
                        "raw_input": req.quick_reply_value,
                        "normalized": True,
                        "confirmed": True,  # User clicked explicitly
                    }
                log.info("[CHAT] Quick reply: %s=%s → %s", qr_field, req.quick_reply_value, qr_result.value)
        else:
            # Free text: call LLM extractor (Claude Haiku)
            # Run in background task so we can yield heartbeats while waiting.
            from services.chat_extractor import extract_fields

            # Phase 1 mode: determine fields differently
            _conv_phase = _phase_state.get("conversation_phase", "phase_1") if rt == "r1" else None
            _in_phase_1a = (rt == "r1" and _is_phase_1a(_phase_state, collected))
            _in_phase_1b = (rt == "r1" and _is_phase_1b(_phase_state, collected))

            if _in_phase_1a:
                # Phase 1a: QR sequential — single-field extraction like legacy
                _next_qr = _get_next_phase_1a_field(collected)
                _all_missing = [f for f in PHASE_1_FIELDS if f not in collected]
                asked_fields = [_next_qr] if _next_qr else []
                cur_field = _next_qr or ""
                cur_desc = FIELD_DESCRIPTIONS.get(cur_field, "")
                _asked_field = cur_field
            elif _in_phase_1b:
                # Phase 1b: open conversation — multi-field extraction
                _missing_p1 = [f for f in PHASE_1B_OPEN_FIELDS if f not in collected]
                _all_missing = _missing_p1
                asked_fields = _missing_p1[:1]
                cur_field = asked_fields[0] if asked_fields else ""
                cur_desc = FIELD_DESCRIPTIONS.get(cur_field, "")
                _asked_field = cur_field
            elif _conv_phase == "phase_2" and rt == "r1":
                # Phase 2: block-scoped — determine block fields for Sonnet,
                # but ONLY pass current field to extractor to prevent hallucination.
                # Haiku was inferring values for all block fields from a single "Nein".
                _cur_block = _phase_state.get("current_block")
                _block_remaining = _get_block_fields(_cur_block, collected) if _cur_block else []
                asked_fields = _block_remaining[:1]
                cur_field = asked_fields[0] if asked_fields else ""
                cur_desc = FIELD_DESCRIPTIONS.get(cur_field, "")
                _asked_field = cur_field
                # KIS-1124-HOTFIX: Only extract the field Sonnet actually asked about
                _all_missing = [cur_field] if cur_field else []
                log.info("[CHAT] Phase 2 block %s: cur_field=%s, block_remaining=%d, extraction_target=%s",
                         _cur_block, cur_field, len(_block_remaining), _all_missing)
            else:
                missing_req, missing_opt = get_missing_fields(collected, _current_section, rt)
                _all_missing = missing_req + missing_opt
                asked_fields = get_next_fields(collected, _current_section, report_type=rt)
                cur_field = asked_fields[0] if asked_fields else ""
                cur_desc = FIELD_DESCRIPTIONS.get(cur_field, "")
                _asked_field = cur_field

            # Help-request: skip extraction entirely, stay on current field
            if _is_help_request:
                _no_extraction = True
                log.info("[CHAT] Help request detected for field %s, skipping extraction", cur_field)

            # Edit-request: user wants to change a field after summary
            if _is_edit_request:
                _no_extraction = True
                # Activate edit_mode in draft_state
                session.draft_state = {
                    **(session.draft_state or {}),
                    "edit_mode": True,
                }
                log.info("[CHAT] Edit request detected, activating edit_mode")

            # Edit-mode: try to parse field change from user message
            if _is_in_edit_mode and not _is_edit_request:
                _no_extraction = True  # Skip normal extraction
                _edit_field, _edit_value = _parse_edit_from_message(
                    req.message, collected, registry, rt,
                )
                if _edit_field and _edit_value is not None:
                    # Apply the edit
                    result = normalize_field(_edit_field, _edit_value, collected, report_type=rt)
                    if result.confidence != "low":
                        collected[_edit_field] = result.value
                        normalized[_edit_field] = result.value
                        field_meta[_edit_field] = {
                            "confidence": result.confidence,
                            "source_turn": turn,
                            "raw_input": str(_edit_value),
                            "normalized": True,
                            "confirmed": True,
                        }
                        _edit_applied = True
                        # Deactivate edit_mode
                        session.draft_state = {
                            **(session.draft_state or {}),
                            "edit_mode": False,
                        }
                        log.info("[CHAT] Edit applied: %s=%r", _edit_field, result.value)
                    else:
                        log.info("[CHAT] Edit: low confidence for %s=%r, asking again", _edit_field, _edit_value)
                else:
                    log.info("[CHAT] Edit: could not parse field change from message")

            # Draft-mode: read pending state for extractor context
            _draft = dict(_draft_state_snapshot)
            _pf = _draft.get("pending_field") if DRAFT_MODE_ENABLED else None
            _pv = _draft.get("pending_value") if DRAFT_MODE_ENABLED else None

            if _is_help_request:
                # Help request: skip extraction entirely
                raw_extracted = {"signal": "question", "fields": {}} if DRAFT_MODE_ENABLED else {}
            elif _in_phase_1b and not _is_in_edit_mode and not _is_edit_request:
                # --- Phase 1: Multi-field extraction ---
                from services.chat_extractor import extract_fields_multi
                from services.chat_normalizer import ENUM_VALUES

                # Build target fields for multi-field extractor
                # KIS-1124 Testrun 3: Fields where the extractor should use
                # user's own words instead of mapping to predefined categories
                _FREETEXT_EXTRACTION_FIELDS = {"ki_ziele"}

                _target_fields = []
                for _fname in PHASE_1_FIELDS:
                    if _fname in collected:
                        continue
                    _freg = registry.get(_fname, {})
                    _fdesc = FIELD_DESCRIPTIONS.get(_fname, _fname)
                    _ftype = _freg.get("type", "text")
                    _field_def: dict = {"name": _fname, "type": _ftype, "description": _fdesc}
                    # Add enum options (but skip for freetext extraction fields)
                    if _ftype in ("enum", "multi") and _fname not in _FREETEXT_EXTRACTION_FIELDS:
                        _opts = ENUM_VALUES.get(_fname)
                        if _opts:
                            _field_def["options"] = _opts
                    _target_fields.append(_field_def)

                # Also try to extract bonus fields (zielgruppen, jahresumsatz, etc.)
                for _bname in PHASE_1_EXTRACTABLE_FIELDS:
                    if _bname in collected or _bname in [f["name"] for f in _target_fields]:
                        continue
                    _breg = registry.get(_bname, {})
                    _bdesc = FIELD_DESCRIPTIONS.get(_bname, _bname)
                    _btype = _breg.get("type", "text")
                    _bfield_def: dict = {"name": _bname, "type": _btype, "description": _bdesc}
                    if _btype in ("enum", "multi") and _bname not in _FREETEXT_EXTRACTION_FIELDS:
                        _bopts = ENUM_VALUES.get(_bname)
                        if _bopts:
                            _bfield_def["options"] = _bopts
                    _target_fields.append(_bfield_def)

                async def _run_multi_extraction() -> dict:
                    try:
                        return await asyncio.wait_for(
                            extract_fields_multi(
                                req.message,
                                messages[-6:],
                                _target_fields,
                                collected,
                            ),
                            timeout=30,
                        )
                    except asyncio.TimeoutError:
                        log.warning("[CHAT] Phase 1 multi-extraction timeout, retrying...")
                        try:
                            return await asyncio.wait_for(
                                extract_fields_multi(
                                    req.message,
                                    messages[-6:],
                                    _target_fields,
                                    collected,
                                ),
                                timeout=30,
                            )
                        except asyncio.TimeoutError:
                            log.error("[CHAT] Phase 1 multi-extraction timeout on retry")
                            return {}

                extract_task = asyncio.create_task(_run_multi_extraction())
                while not extract_task.done():
                    try:
                        await asyncio.wait_for(asyncio.shield(extract_task), timeout=_HB_INTERVAL)
                    except asyncio.TimeoutError:
                        yield f"event: heartbeat\ndata: {{}}\n\n"
                    except Exception:
                        break

                _multi_raw = extract_task.result() if not extract_task.cancelled() else {}
                _skip = _multi_raw.pop("__skip_signal", False)

                # Normalize and write all extracted fields
                for _mf_name, _mf_val in _multi_raw.items():
                    if _mf_name not in registry:
                        continue
                    if not is_field_visible(_mf_name, collected):
                        continue
                    if _mf_name in collected:
                        continue
                    result = normalize_field(_mf_name, _mf_val, collected, report_type=rt)
                    if result.confidence == "low":
                        log.info("[CHAT] Phase 1: field %s low confidence, skipping", _mf_name)
                        continue
                    collected[_mf_name] = result.value
                    normalized[_mf_name] = result.value
                    field_meta[_mf_name] = {
                        "confidence": result.confidence,
                        "source_turn": turn,
                        "raw_input": str(_mf_val),
                        "normalized": True,
                        "confirmed": True,
                    }
                    log.info("[CHAT] Phase 1: extracted %s=%r", _mf_name, result.value)

                if not normalized and not _skip:
                    _no_extraction = True
                    log.info("[CHAT] Phase 1: no extraction from free text")

                # Wrap as raw_extracted for compatibility with downstream code
                raw_extracted = {}
            else:
                # KIS-1124: Increased extraction timeout from 30s to 45s.
                # Under load, Haiku can take >30s especially with long prompts.
                _EXTRACT_TIMEOUT = 45

                async def _run_extraction() -> dict:
                    try:
                        return await asyncio.wait_for(
                            extract_fields(
                                req.message,
                                messages[-6:],
                                _all_missing,
                                collected,
                                report_type=rt,
                                current_field=cur_field,
                                current_field_description=cur_desc,
                                draft_mode=DRAFT_MODE_ENABLED,
                                pending_field=_pf,
                                pending_value=_pv,
                            ),
                            timeout=_EXTRACT_TIMEOUT,
                        )
                    except asyncio.TimeoutError:
                        log.warning("[CHAT] Extraction timeout (%ds), retrying once...", _EXTRACT_TIMEOUT)
                        try:
                            return await asyncio.wait_for(
                                extract_fields(
                                    req.message,
                                    messages[-6:],
                                    _all_missing,
                                    collected,
                                    report_type=rt,
                                    current_field=cur_field,
                                    current_field_description=cur_desc,
                                    draft_mode=DRAFT_MODE_ENABLED,
                                    pending_field=_pf,
                                    pending_value=_pv,
                                ),
                                timeout=_EXTRACT_TIMEOUT,
                            )
                        except asyncio.TimeoutError:
                            log.error("[CHAT] Extraction timeout on retry")
                            return {"signal": None, "fields": {}} if DRAFT_MODE_ENABLED else {}

                extract_task = asyncio.create_task(_run_extraction())
                while not extract_task.done():
                    try:
                        await asyncio.wait_for(asyncio.shield(extract_task), timeout=_HB_INTERVAL)
                    except asyncio.TimeoutError:
                        yield f"event: heartbeat\ndata: {{}}\n\n"
                    except Exception:
                        break  # task raised — handled below

                raw_extracted = extract_task.result() if not extract_task.cancelled() else (
                    {"signal": None, "fields": {}} if DRAFT_MODE_ENABLED else {}
                )

            if not DRAFT_MODE_ENABLED:
                # ----- Legacy flow: normalize + direct write to collected_fields -----
                for field_name, raw_value in raw_extracted.items():
                    if field_name not in registry:
                        continue
                    if not is_field_visible(field_name, collected):
                        continue
                    if field_name in collected:
                        log.info("[CHAT] Legacy: field %s already collected, skipping re-extraction", field_name)
                        continue

                    result = normalize_field(field_name, raw_value, collected, report_type=rt)

                    if result.confidence == "low":
                        log.info("[CHAT] Field %s: low confidence, skipping", field_name)
                        continue

                    collected[field_name] = result.value
                    normalized[field_name] = result.value

                    field_meta[field_name] = {
                        "confidence": result.confidence,
                        "source_turn": turn,
                        "raw_input": str(raw_value),
                        "normalized": True,
                        "confirmed": False,
                    }
                # No fields extracted from free text → user likely asked a question
                if not normalized:
                    _no_extraction = True
                    log.info("[CHAT] Legacy: no extraction from free text, staying on field %s", _asked_field)
            else:
                # ----- Draft flow: extract → pending, not collected -----
                _signal = raw_extracted.get("signal")
                _ext_fields = raw_extracted.get("fields", {})
                draft_state = dict(_draft_state_snapshot)

                if _signal == "question":
                    draft_state["dialog_mode"] = True
                    # No write, no pending change
                    log.info("[CHAT] Draft: user question detected")

                elif _signal == "confirm":
                    if draft_state.get("pending_field"):
                        # Pending → Collected
                        _cf = draft_state["pending_field"]
                        _cv = draft_state["pending_value"]
                        collected[_cf] = _cv
                        normalized[_cf] = _cv
                        field_meta[_cf] = {
                            "confidence": "high",
                            "source_turn": turn,
                            "raw_input": "confirmed",
                            "normalized": True,
                            "confirmed": True,
                        }
                        draft_state = {"pending_field": None, "pending_value": None, "dialog_mode": False}
                        _draft_confirmed_field = _cf
                        _draft_confirmed_value = _cv
                        log.info("[CHAT] Draft: confirmed %s=%r", _cf, _cv)
                    else:
                        # No pending → treat like skip
                        log.info("[CHAT] Draft: confirm without pending, treating as skip")

                else:
                    # Normal extraction or correction — process extracted fields
                    for field_name, raw_value in _ext_fields.items():
                        if field_name not in registry:
                            continue
                        if not is_field_visible(field_name, collected):
                            continue
                        if field_name in collected:
                            log.info("[CHAT] Draft: field %s already collected, skipping re-extraction", field_name)
                            continue

                        result = normalize_field(field_name, raw_value, collected, report_type=rt)
                        if result.confidence == "low":
                            log.info("[CHAT] Draft: field %s low confidence, skipping", field_name)
                            continue

                        # Warn if overwriting a different pending field
                        if draft_state.get("pending_field") and draft_state["pending_field"] != field_name:
                            log.warning(
                                "[CHAT] Draft: overwriting pending %s with new field %s",
                                draft_state["pending_field"], field_name,
                            )

                        draft_state["pending_field"] = field_name
                        draft_state["pending_value"] = result.value
                        draft_state["dialog_mode"] = False
                        _draft_new_field = field_name
                        _draft_new_value = result.value
                        log.info("[CHAT] Draft: pending %s=%r (signal=%s)", field_name, result.value, _signal)
                        break  # Only one field at a time in draft mode

                session.draft_state = draft_state
                _pending_after_turn = bool(draft_state.get("pending_field"))

        # KIS-1124-S3-BE-4: Block-level skip detection (Phase 2 only)
        # These phrases end the ENTIRE block, not just one field.
        _BLOCK_SKIP_PATTERNS = [
            "reicht", "genug", "nächster bereich", "nächster block",
            "weitermachen", "das reicht", "können wir weiter",
            "nächstes thema", "thema wechseln", "report erstellen",
            "report reicht", "das genügt", "fertig mit dem bereich",
            "mir reicht das", "reicht mir",
        ]
        _conv_phase_for_skip = _phase_state.get("conversation_phase", "phase_1") if rt == "r1" else None
        _msg_lower_pre = req.message.strip().lower()
        _is_block_skip = (
            _conv_phase_for_skip == "phase_2"
            and not _is_qr_click
            and not _is_help_request
            and any(p in _msg_lower_pre for p in _BLOCK_SKIP_PATTERNS)
        )
        if _is_block_skip:
            # Force block_stale_turns to 2 → triggers block completion in the phase_2 branch
            _phase_state["block_stale_turns"] = 2
            _no_extraction = True
            log.info("[CHAT] Block-level skip detected: '%s' → force-closing current block", _msg_lower_pre)

        # Handle "weiter" / skip for optional fields
        # KIS-1124-S0-BE-2: Extended skip detection with decline phrases
        skip_words = {"weiter", "skip", "überspringen", "nächste", "weiter bitte", "nächste frage"}
        _DECLINE_PATTERNS = [
            "weiß nicht", "weiss nicht", "keine ahnung", "kann ich nicht",
            "überspring", "überspringen", "skip", "egal", "später",
            "das kann ich jetzt nicht", "schwer zu sagen", "müsste ich nachschauen",
            "ist mir nicht wichtig", "spielt keine rolle", "unwichtig",
            "nächste frage", "weiter", "kann ich nicht entscheiden",
            "kann ich nicht sagen", "keine angabe", "k.a.", "kein kommentar",
            "keine meinung", "weiß ich nicht", "weiss ich nicht",
            "kann ich nicht beantworten", "keine idee", "noch keine idee",
            # KIS-1124 Testrun-Fix Bug 4: additional skip-signal phrases
            "weiß nicht genau", "weiss nicht genau", "keine vorstellung",
            "passe", "überspring das", "kein plan", "wüsste ich nicht",
            "da bin ich überfragt", "keine präferenz", "mir egal",
        ]
        _msg_lower = req.message.strip().lower()
        _is_skip_word = _msg_lower in skip_words
        _is_decline = (not normalized and not _is_qr_click and not _is_help_request
                       and any(p in _msg_lower for p in _DECLINE_PATTERNS))
        _skip_confirmed_draft = False

        if (_is_skip_word or _is_decline) and not normalized:
            # In draft mode with pending: "weiter" confirms the pending value
            # but does NOT also skip the next field (confirm only).
            if DRAFT_MODE_ENABLED and _is_skip_word:
                draft_state = dict(_draft_state_snapshot)
                if draft_state.get("pending_field"):
                    _cf = draft_state["pending_field"]
                    _cv = draft_state["pending_value"]
                    collected[_cf] = _cv
                    normalized[_cf] = _cv
                    field_meta[_cf] = {
                        "confidence": "high",
                        "source_turn": turn,
                        "raw_input": "confirmed_via_skip",
                        "normalized": True,
                        "confirmed": True,
                    }
                    session.draft_state = {"pending_field": None, "pending_value": None, "dialog_mode": False}
                    _draft_confirmed_field = _cf
                    _draft_confirmed_value = _cv
                    _skip_confirmed_draft = True
                    _pending_after_turn = False
                    log.info("[CHAT] Draft: 'weiter' confirmed pending %s=%r", _cf, _cv)

            # Only skip the next optional field if we didn't just confirm a draft.
            # "weiter" + pending draft = confirm only; "weiter" + no draft = skip.
            if not _skip_confirmed_draft:
                asked = get_next_fields(collected, _current_section, report_type=rt)
                if asked:
                    skip_field = asked[0]
                    skip_reg = registry.get(skip_field, {})
                    # Count how many times this field has been declined
                    _field_meta_entry = field_meta.get(skip_field, {})
                    _skip_attempts = _field_meta_entry.get("skip_attempts", 0) + 1
                    if not skip_reg.get("required"):
                        # Optional field → skip immediately
                        collected[skip_field] = "" if skip_reg.get("type") == "text" else None
                        field_meta[skip_field] = {
                            "confidence": "high", "source_turn": turn,
                            "raw_input": "skipped", "normalized": True, "confirmed": True,
                        }
                        log.info("[CHAT] User skipped optional field: %s", skip_field)
                    elif _skip_attempts >= 2:
                        # Required field declined 2+ times → force-skip with keine_angabe
                        collected[skip_field] = "keine_angabe"
                        field_meta[skip_field] = {
                            "confidence": "medium", "source_turn": turn,
                            "raw_input": "declined_twice", "normalized": True, "confirmed": True,
                        }
                        log.info("[CHAT] User declined required field %s twice, setting keine_angabe", skip_field)
                    else:
                        # Required field, first decline → track attempt, stay on field
                        # Sonnet will offer QR buttons as fallback
                        field_meta[skip_field] = {
                            **_field_meta_entry,
                            "skip_attempts": _skip_attempts,
                        }
                        _no_extraction = True
                        log.info("[CHAT] User declined required field %s (attempt %d), staying on field", skip_field, _skip_attempts)

        # Evaluate conditionals: remove hidden fields BEFORE writing
        for cond_field in ["selbststaendig", "bundesland"]:
            if cond_field in collected and not is_field_visible(cond_field, collected):
                del collected[cond_field]
                if cond_field in field_meta:
                    del field_meta[cond_field]

        # Raw SQL write — direct SET, no ORM involvement.
        # `collected` was read fresh at turn start and contains the full
        # desired state (previous fields + this turn's additions/deletions).
        # draft_state MUST be included here — ORM assignments to
        # session.draft_state are not reliably flushed after raw SQL commits.
        now = datetime.now(timezone.utc)
        _draft_for_sql = None
        if DRAFT_MODE_ENABLED or _is_edit_request or _is_in_edit_mode:
            _draft_for_sql = json.dumps(
                getattr(session, 'draft_state', None)
                or {"pending_field": None, "pending_value": None, "dialog_mode": False}
            )

        db.execute(
            _sa_text("""
                UPDATE chat_sessions
                SET collected_fields = CAST(:cf AS jsonb),
                    field_meta = CAST(:fm AS jsonb),
                    draft_state = CAST(:ds AS jsonb),
                    phase_state = CAST(:ps AS jsonb),
                    updated_at = :ts
                WHERE id = :sid
            """),
            {
                "sid": str(session.id),
                "cf": json.dumps(collected),
                "fm": json.dumps(field_meta),
                "ds": _draft_for_sql or json.dumps({}),
                "ps": json.dumps(_phase_state),
                "ts": now,
            }
        )
        db.commit()

        # Check section transition (raw SQL inside, commits internally)
        # Skip for Phase 1 — sections aren't used until Phase 2/legacy
        _cur_conv_phase = _phase_state.get("conversation_phase", "phase_1") if rt == "r1" else None
        if _cur_conv_phase not in ("phase_1", "checkpoint"):
            section_advanced = _check_section_transition(session, collected, db, rt)
            if section_advanced:
                _current_section = session.current_section

        # Determine next fields
        sections = get_sections_for_report(rt)

        # Re-evaluate sub-phase after extraction (collected may have changed)
        _post_phase_1a = (rt == "r1" and _is_phase_1a(_phase_state, collected))
        _post_phase_1b = (rt == "r1" and _is_phase_1b(_phase_state, collected))

        # Auto-transition Phase 1a → 1b when all QR fields are collected
        if _cur_conv_phase == "phase_1" and rt == "r1" and not _post_phase_1a and not _phase_state.get("phase_1_qr_complete"):
            _phase_state["phase_1_qr_complete"] = True
            db.execute(
                _sa_text("UPDATE chat_sessions SET phase_state = CAST(:ps AS jsonb) WHERE id = :sid"),
                {"ps": json.dumps(_phase_state), "sid": str(session.id)},
            )
            db.commit()
            log.info("[CHAT] Phase 1a → 1b transition: all QR fields collected")

        # --- Phase 1: Completion check + checkpoint trigger ---
        _checkpoint_triggered = False
        _block_just_completed = False
        if _cur_conv_phase == "phase_1" and rt == "r1":
            _missing_p1_after = [f for f in PHASE_1_FIELDS if f not in collected
                                 and not _should_skip_qr_field(f, collected)]
            all_missing = _missing_p1_after

            # KIS-1124 Testrun-Fix Bug 7: Track which Phase 1b fields
            # Sonnet has asked about. A field extracted via multi-field
            # extraction is only considered "covered" if Sonnet asked
            # about it (it appeared in next_fields) at least once.
            _p1b_asked = _phase_state.get("phase_1b_asked_fields", [])
            if not _post_phase_1a and _asked_field and _asked_field in PHASE_1B_OPEN_FIELDS:
                if _asked_field not in _p1b_asked:
                    _p1b_asked.append(_asked_field)
                    _phase_state["phase_1b_asked_fields"] = _p1b_asked

            # KIS-1124 Testrun 5: Phase 1b turn counter safeguard
            if not _post_phase_1a:
                _p1b_turns = _phase_state.get("phase_1b_turn_count", 0) + 1
                _phase_state["phase_1b_turn_count"] = _p1b_turns
            else:
                _p1b_turns = 0

            if not _missing_p1_after:
                # All Phase 1 fields are in collected → trigger checkpoint.
                # KIS-1124 Testrun 5 Fix: Previously we force-asked about
                # collected-but-unasked fields, causing an infinite loop when
                # _p1b_asked state was lost between turns. New logic: if the
                # field is collected, it's done — no need to re-ask.
                _unasked_p1b = [f for f in PHASE_1B_OPEN_FIELDS
                                if f not in _p1b_asked and f not in collected]
                if _unasked_p1b:
                    # Fields neither collected nor asked — should be rare since
                    # _missing_p1_after is empty. Ask about them.
                    next_fields = [_unasked_p1b[0]]
                    _p1b_asked.append(_unasked_p1b[0])
                    _phase_state["phase_1b_asked_fields"] = _p1b_asked
                    log.info("[CHAT] Phase 1b: field %s uncollected+unasked — forcing question before checkpoint", _unasked_p1b[0])
                    # Persist phase_state
                    db.execute(
                        _sa_text("UPDATE chat_sessions SET phase_state = CAST(:ps AS jsonb) WHERE id = :sid"),
                        {"ps": json.dumps(_phase_state), "sid": str(session.id)},
                    )
                    db.commit()
                else:
                    # All Phase 1b fields covered (collected or asked) → checkpoint
                    _phase_state["conversation_phase"] = "checkpoint"
                    _checkpoint_triggered = True
                    next_fields = []
                    log.info("[CHAT] Phase 1 COMPLETE — triggering checkpoint (p1b_asked=%s, p1b_turns=%d)",
                             _p1b_asked, _p1b_turns)

                    # Persist phase_state change immediately
                    db.execute(
                        _sa_text("UPDATE chat_sessions SET phase_state = CAST(:ps AS jsonb) WHERE id = :sid"),
                        {"ps": json.dumps(_phase_state), "sid": str(session.id)},
                    )
                    db.commit()
            elif _p1b_turns >= 6 and not _post_phase_1a:
                # KIS-1124 Testrun 5: Safeguard — force checkpoint after 6
                # Phase 1b turns to prevent infinite loops. Missing fields
                # can be collected in Phase 2 blocks or skipped entirely.
                log.warning(
                    "[CHAT] Phase 1b SAFEGUARD: forcing checkpoint after %d turns "
                    "(missing: %s, p1b_asked: %s)",
                    _p1b_turns, _missing_p1_after, _p1b_asked,
                )
                _phase_state["conversation_phase"] = "checkpoint"
                _checkpoint_triggered = True
                next_fields = []
                db.execute(
                    _sa_text("UPDATE chat_sessions SET phase_state = CAST(:ps AS jsonb) WHERE id = :sid"),
                    {"ps": json.dumps(_phase_state), "sid": str(session.id)},
                )
                db.commit()
            elif _no_extraction and _asked_field and _asked_field not in collected:
                next_fields = [_asked_field]
                log.info("[CHAT] Phase 1 QR-Sync: keeping next_fields=[%s]", _asked_field)
            elif _post_phase_1a:
                # Phase 1a: next QR field in sequence
                _next_qr = _get_next_phase_1a_field(collected)
                next_fields = [_next_qr] if _next_qr else []
            else:
                # Phase 1b: next open-conversation field (no QR)
                _p1b_missing = [f for f in PHASE_1B_OPEN_FIELDS if f not in collected]
                next_fields = _p1b_missing[:1]
                # Persist phase_1b_asked_fields
                db.execute(
                    _sa_text("UPDATE chat_sessions SET phase_state = CAST(:ps AS jsonb) WHERE id = :sid"),
                    {"ps": json.dumps(_phase_state), "sid": str(session.id)},
                )
                db.commit()

        elif _cur_conv_phase == "checkpoint" and rt == "r1":
            # Checkpoint phase — next_fields is empty, QR handles navigation
            all_missing = []
            next_fields = []

        elif _cur_conv_phase == "summary" and rt == "r1":
            # Summary phase — triggered by checkpoint "Report jetzt erstellen"
            all_missing = []
            next_fields = []

        elif _cur_conv_phase == "phase_2" and rt == "r1":
            # Phase 2: block-scoped fields ONLY — no orphan leakage
            _cur_block = _phase_state.get("current_block")
            if _cur_block:
                _block_remaining = _get_block_fields(_cur_block, collected)

                # KIS-1124 Testrun-Fix Bug 8: Track which fields in the
                # current block Sonnet has asked about.
                _block_asked = _phase_state.get("block_asked_fields", [])
                if _asked_field and _asked_field not in _block_asked:
                    _block_asked.append(_asked_field)
                    _phase_state["block_asked_fields"] = _block_asked

                # KIS-1124 Testrun 6 Fix 2: Per-field ask count tracking.
                # If the same field was asked 2× without extraction → force-default.
                _field_ask_counts: dict = _phase_state.get("field_ask_counts", {})
                if _asked_field and _asked_field not in collected:
                    _field_ask_counts[_asked_field] = _field_ask_counts.get(_asked_field, 0) + 1
                    _phase_state["field_ask_counts"] = _field_ask_counts
                elif _asked_field and _asked_field in collected:
                    # Field was just collected → reset its count
                    _field_ask_counts.pop(_asked_field, None)

                # Force-default for fields asked ≥2× without success
                _force_defaulted = False
                for _fd_field, _fd_count in list(_field_ask_counts.items()):
                    if _fd_count >= 2 and _fd_field not in collected:
                        _default = _FIELD_DEFAULTS.get(_fd_field, "keine_angabe")
                        collected[_fd_field] = _default
                        log.warning(
                            "[CHAT] Phase 2 field safeguard: %s asked %d× without "
                            "extraction — defaulting to '%s'",
                            _fd_field, _fd_count, _default,
                        )
                        _force_defaulted = True
                        _field_ask_counts.pop(_fd_field, None)
                if _force_defaulted:
                    _phase_state["field_ask_counts"] = _field_ask_counts
                    # Persist force-defaulted collected fields
                    db.execute(
                        _sa_text("UPDATE chat_sessions SET collected_fields = CAST(:cf AS jsonb) WHERE id = :sid"),
                        {"cf": json.dumps(collected), "sid": str(session.id)},
                    )
                    # Re-compute remaining after force-defaults
                    _block_remaining = _get_block_fields(_cur_block, collected)

                # KIS-1128C V6-BE-1: Smart Skip — auto-fill derivable fields
                _smart_skipped = False
                for _ss_field in list(_block_remaining):
                    _ss_value = _smart_skip_field(_ss_field, collected)
                    if _ss_value is not None:
                        collected[_ss_field] = _ss_value
                        _smart_skipped = True
                        log.info("[CHAT] SMART SKIP: %s=%s (derived)", _ss_field, _ss_value)
                if _smart_skipped:
                    db.execute(
                        _sa_text("UPDATE chat_sessions SET collected_fields = CAST(:cf AS jsonb) WHERE id = :sid"),
                        {"cf": json.dumps(collected), "sid": str(session.id)},
                    )
                    _block_remaining = _get_block_fields(_cur_block, collected)

                # Stale turn tracking: increment on no extraction, reset on extraction
                if normalized and not _no_extraction:
                    _phase_state["block_stale_turns"] = 0
                elif not _is_qr_click or (req.quick_reply_field == "__block_transition__"):
                    _phase_state["block_stale_turns"] = _phase_state.get("block_stale_turns", 0) + 1

                _stale = _phase_state.get("block_stale_turns", 0)

                # KIS-1124 Testrun-Fix Bug 8: Check if there are remaining
                # fields that Sonnet has never asked about. If so, the block
                # should NOT auto-close — instead redirect Sonnet to ask about
                # those unasked fields first.
                _unasked_remaining = [f for f in _block_remaining if f not in _block_asked]

                # Block completion: no remaining fields OR stale >= 2
                # BUT: don't auto-close if there are unasked remaining fields
                # KIS-1124 Testrun 2 Bug 12: Hard limit raised to 6 to give
                # unasked fields (like jahresumsatz) a chance to be asked.
                _should_close = (
                    not _block_remaining
                    or (_stale >= 2 and not _unasked_remaining)
                    or _stale >= 6  # Hard limit: force-close after 6 stale turns
                )
                if _should_close:
                    if not _block_remaining:
                        log.info("[CHAT] Phase 2: block %s complete (all fields collected)", _cur_block)
                    else:
                        log.info("[CHAT] Phase 2: block %s auto-close (stale_turns=%d, unasked=%d)", _cur_block, _stale, len(_unasked_remaining))

                    # Mark block as completed
                    completed = _phase_state.get("completed_blocks", [])
                    if _cur_block not in completed:
                        completed.append(_cur_block)
                    _phase_state["completed_blocks"] = completed
                    _phase_state["block_stale_turns"] = 0
                    _phase_state["block_asked_fields"] = []  # Reset for next block
                    _phase_state["field_ask_counts"] = {}    # Reset for next block

                    # Determine next block
                    remaining_blocks = [b for b in _phase_state.get("selected_blocks", [])
                                        if b not in completed]
                    if remaining_blocks:
                        _phase_state["current_block"] = remaining_blocks[0]
                        log.info("[CHAT] Phase 2: next block → %s", remaining_blocks[0])
                    else:
                        _phase_state["current_block"] = None
                        log.info("[CHAT] Phase 2: all blocks done → summary")

                    _block_just_completed = True
                    all_missing = []
                    next_fields = []
                elif _stale >= 2 and _unasked_remaining:
                    # Stale threshold hit but there are unasked fields — redirect
                    # Sonnet to ask about the first unasked field instead of closing.
                    all_missing = _block_remaining
                    next_fields = [_unasked_remaining[0]]
                    _phase_state["block_stale_turns"] = 0  # Reset to give the field a chance
                    log.info("[CHAT] Phase 2 block %s: stale but %d unasked fields remain — redirecting to %s",
                             _cur_block, len(_unasked_remaining), _unasked_remaining[0])
                else:
                    all_missing = _block_remaining
                    if _no_extraction and _asked_field and _asked_field not in collected:
                        next_fields = [_asked_field]
                        log.info("[CHAT] Phase 2 block %s: no extraction, keeping next_fields=[%s]", _cur_block, _asked_field)
                    else:
                        next_fields = _block_remaining[:1]
            else:
                all_missing = []
                next_fields = []

            # Persist stale_turns update
            if _cur_conv_phase == "phase_2":
                db.execute(
                    _sa_text("UPDATE chat_sessions SET phase_state = CAST(:ps AS jsonb) WHERE id = :sid"),
                    {"ps": json.dumps(_phase_state), "sid": str(session.id)},
                )
                db.commit()

        else:
            # Legacy / Strategy: section-based next fields
            missing_req, missing_opt = get_missing_fields(collected, _current_section, rt)
            all_missing = missing_req + missing_opt

            if _no_extraction and _asked_field and _asked_field not in collected:
                next_fields = [_asked_field]
                log.info("[CHAT] QR-Sync: no extraction, keeping next_fields=[%s]", _asked_field)
            else:
                next_fields = get_next_fields(collected, _current_section, max_fields=1, report_type=rt)

        current_section = sections[min(_current_section, len(sections) - 1)]

        log.info("[CHAT] Turn %d: normalized=%s, next=%s, no_extraction=%s", turn, list(normalized.keys()), next_fields, _no_extraction)

        # Pre-compute next-field QR context so Sonnet can create
        # coherent transitions (KIS-1123 Fix 1).
        _next_field_qr_context = None
        if next_fields:
            _preview_qrs = _build_quick_replies(next_fields, rt, collected)
            _nf = next_fields[0]
            if _preview_qrs:
                _qr = _preview_qrs[0]
                _opt_labels = ", ".join(o.label for o in _qr.options[:10])
                _next_field_qr_context = (
                    f"Feldname: {_qr.field}\n"
                    f"Label: {_qr.label}\n"
                    f"Hat Quick-Reply-Buttons: ja\n"
                    f"Optionen: {_opt_labels}\n"
                    f"Mehrfachauswahl: {'ja' if _qr.multi_select else 'nein'}"
                )
            else:
                _nf_desc = FIELD_DESCRIPTIONS.get(_nf, _nf)
                _next_field_qr_context = (
                    f"Feldname: {_nf}\n"
                    f"Beschreibung: {_nf_desc}\n"
                    f"Hat Quick-Reply-Buttons: nein\n"
                    f"Der Nutzer gibt Freitext ein."
                )

        # Build user profile summary for Sonnet context (KIS-1123 Fix 2).
        _PROFILE_FIELDS = [
            ("branche", "Branche"),
            ("unternehmensgroesse", "Unternehmensgröße"),
            ("hauptleistung", "Hauptleistung"),
            ("ki_kompetenz", "KI-Kompetenz"),
            ("ki_einsatz", "KI-Einsatzbereiche"),
            ("digitalisierungsgrad", "Digitalisierungsgrad"),
            ("ki_projekte", "Bestehende KI-Projekte"),
            ("zielgruppen", "Zielgruppen"),
        ]
        _profile_parts = []
        for _pf_key, _pf_label in _PROFILE_FIELDS:
            _pf_val = collected.get(_pf_key)
            if _pf_val:
                _profile_parts.append(f"- {_pf_label}: {_pf_val}")
        _user_profile_summary = "\n".join(_profile_parts) if len(_profile_parts) >= 2 else None

        # Extract last 3 bot messages for anti-repetition (KIS-1123 Fix 3).
        _recent_bot_msgs = [
            m["content"] for m in session.messages
            if m.get("role") == "assistant" and m.get("content")
        ][-3:]

        # KIS-1124 Testrun-Fix Bug 2: Track used confirmation phrases
        # across the entire conversation so Sonnet can avoid repeating them.
        _CONFIRMATION_WORDS = {
            "notiert.", "danke.", "klar.", "verstehe.", "gut.",
            "passt.", "erfasst.", "alles klar.", "in ordnung.",
            "verstanden.", "weiter.", "okay.", "gut erfasst.",
        }
        _used_confirmations: list[str] = []
        for _bot_msg in (m["content"] for m in session.messages
                         if m.get("role") == "assistant" and m.get("content")):
            _first_sentence = _bot_msg.strip().split("\n")[0].split(".")[0] + "." if _bot_msg.strip() else ""
            _first_word_lower = _first_sentence.strip().lower()
            for _cw in _CONFIRMATION_WORDS:
                if _first_word_lower.startswith(_cw):
                    _canon = _cw.capitalize()
                    if _canon not in _used_confirmations:
                        _used_confirmations.append(_canon)
                    break

        # ------------------------------------------------------------------
        # Phase 2: Stream Sonnet response with heartbeat keepalive
        # ------------------------------------------------------------------
        _SENTINEL = object()
        queue: asyncio.Queue = asyncio.Queue()

        # Draft context for Sonnet — must reflect THIS turn's state,
        # not the snapshot from turn start.
        if DRAFT_MODE_ENABLED and _draft_new_field:
            # New draft created this turn → tell Sonnet to confirm
            _sonnet_pending_field = _draft_new_field
            _sonnet_pending_value = _draft_new_value
            _sonnet_dialog_mode = False
        elif DRAFT_MODE_ENABLED and _signal == "question":
            # User asked a question → dialog mode, keep existing draft
            _sonnet_pending_field = _draft_state_snapshot.get("pending_field")
            _sonnet_pending_value = _draft_state_snapshot.get("pending_value")
            _sonnet_dialog_mode = True
        elif DRAFT_MODE_ENABLED and _draft_confirmed_field:
            # Draft was just confirmed → no pending, ask next question
            _sonnet_pending_field = None
            _sonnet_pending_value = None
            _sonnet_dialog_mode = False
        elif _is_edit_request or (_is_in_edit_mode and not _edit_applied):
            # Edit mode: Sonnet asks what to change or clarifies
            _sonnet_pending_field = None
            _sonnet_pending_value = None
            _sonnet_dialog_mode = True
        elif _no_extraction and not DRAFT_MODE_ENABLED:
            # Legacy mode: no extraction → dialog mode so Sonnet answers
            # the user's question instead of advancing to next field
            _sonnet_pending_field = None
            _sonnet_pending_value = None
            _sonnet_dialog_mode = True
        else:
            # No change → use snapshot (covers: no draft mode, or
            # existing pending draft carried over from previous turn)
            _ds = dict(_draft_state_snapshot)
            _sonnet_pending_field = _ds.get("pending_field")
            _sonnet_pending_value = _ds.get("pending_value")
            _sonnet_dialog_mode = _ds.get("dialog_mode", False)

        # Build help context if this is a help request
        _help_ctx = None
        if _is_help_request and _asked_field:
            _help_ctx = build_help_context(_asked_field, collected, rt)
        elif _is_edit_request:
            # KIS-1125-HOTFIX: Include field list in initial edit prompt.
            # Previously, Sonnet only got EDIT_MODE_SONNET_PROMPT (no data),
            # so it asked "Was möchten Sie ändern?" without showing fields.
            _edit_field_list = build_edit_extraction_context(collected, rt)
            _help_ctx = (
                f"{EDIT_MODE_SONNET_PROMPT}\n"
                f"Aktuelle Felder und Werte:\n{_edit_field_list}\n\n"
                f"Fragen Sie kurz, welches Feld geändert werden soll."
            )
        elif _edit_applied:
            # Edit was applied — Sonnet confirms the change
            edit_field_label = FIELD_DESCRIPTIONS.get(list(normalized.keys())[0], "").split("(")[0].strip() if normalized else "Feld"
            edit_new_val = list(normalized.values())[0] if normalized else ""
            _help_ctx = (
                f"\n\nAKTUELLER MODUS: ÄNDERUNG BESTÄTIGT\n"
                f"Die Angabe wurde geändert: {edit_field_label} = \"{edit_new_val}\".\n"
                f"Bestätigen Sie die Änderung in EINEM kurzen Satz.\n"
                f"Danach folgt automatisch die aktualisierte Zusammenfassung."
            )
        elif _is_in_edit_mode and not _edit_applied:
            # Still in edit mode but couldn't parse the change — ask for clarification
            field_list = build_edit_extraction_context(collected, rt)
            _help_ctx = (
                f"\n\nAKTUELLER MODUS: ÄNDERUNG\n"
                f"Der Nutzer möchte eine Angabe ändern, aber die Angabe war nicht eindeutig.\n"
                f"Aktuelle Felder:\n{field_list}\n\n"
                f"Fragen Sie den Nutzer, welches Feld geändert werden soll und auf welchen Wert."
            )

        # KIS-1124-S0-BE-2: When user declines a field, tell Sonnet
        # to acknowledge gracefully.
        if _is_decline and not _help_ctx:
            _decline_field = _asked_field
            _decline_reg = registry.get(_decline_field, {})
            if _decline_reg.get("required"):
                _decline_meta = field_meta.get(_decline_field, {})
                _decline_attempts = _decline_meta.get("skip_attempts", 0)
                if _decline_attempts == 1:
                    _help_ctx = (
                        f"\n\nAKTUELLER MODUS: NUTZER KANN NICHT ANTWORTEN\n"
                        f"Der Nutzer hat signalisiert, dass er das Feld \"{_decline_field}\" "
                        f"gerade nicht beantworten kann.\n"
                        f"REAGIERE SO:\n"
                        f"- Verstehe und akzeptiere das (1 kurzer Satz, z.B. 'Verstehe.').\n"
                        f"- Weise darauf hin, dass es unten Buttons zur Auswahl gibt, "
                        f"die die Antwort erleichtern.\n"
                        f"- Maximal 2 Sätze total. NICHT insistieren."
                    )
            else:
                # KIS-1124 Testrun-Fix Bug 4: Skip-friendly message for optional fields
                _help_ctx = (
                    f"\n\nAKTUELLER MODUS: FELD ÜBERSPRUNGEN\n"
                    f"Der Nutzer hat das optionale Feld \"{_decline_field}\" übersprungen.\n"
                    f"REAGIERE SO:\n"
                    f"- Kurze freundliche Bestätigung (z.B. 'Kein Problem, das lassen wir offen.').\n"
                    f"- Dann SOFORT zur nächsten Frage weiter.\n"
                    f"- NICHT 'Notiert.' sagen — das klingt so, als wäre die Ablehnung ein Wert.\n"
                    f"- Maximal 1 Satz, dann die nächste Frage."
                )

        # Compute Phase 1 missing fields for Sonnet prompt
        _missing_p1_for_sonnet = None
        # Phase 2 block context for Sonnet
        _sonnet_block_id = None
        _sonnet_block_remaining = None
        # Determine effective sub-phase for Sonnet prompt routing
        _sonnet_conv_phase = _cur_conv_phase
        if _cur_conv_phase == "phase_1" and rt == "r1":
            if _post_phase_1a:
                _sonnet_conv_phase = "phase_1a"
            else:
                _sonnet_conv_phase = "phase_1b"
                _missing_p1_for_sonnet = [f for f in PHASE_1B_OPEN_FIELDS if f not in collected]
        elif _cur_conv_phase == "phase_2" and rt == "r1":
            _sonnet_conv_phase = "phase_2"
            _sonnet_block_id = _phase_state.get("current_block")
            if _sonnet_block_id:
                _sonnet_block_remaining = _get_block_fields(_sonnet_block_id, collected)

        # Checkpoint: inject checkpoint text instead of streaming Sonnet
        _checkpoint_text = None
        if _checkpoint_triggered:
            _checkpoint_text = (
                "Ich habe jetzt ein gutes Bild von Ihrem Unternehmen. "
                "Damit kann ich bereits einen soliden KI-Report erstellen.\n\n"
                "Am Ende können Sie alle Angaben nochmal prüfen und bei Bedarf korrigieren.\n\n"
                "Sie können die Analyse aber gezielt vertiefen — "
                "welche Bereiche interessieren Sie besonders?"
            )

        # Block completion: inject inter-block transition text
        _block_transition_text = None
        if _cur_conv_phase == "phase_2" and rt == "r1" and _block_just_completed:
            _completed_label = BLOCK_LABELS.get(_cur_block, _cur_block)
            _remaining_blocks_after = [b for b in _phase_state.get("selected_blocks", [])
                                       if b not in _phase_state.get("completed_blocks", [])]
            if _remaining_blocks_after:
                _next_label = BLOCK_LABELS.get(_remaining_blocks_after[0], "")
                _block_transition_text = (
                    f'Bereich \u201e{_completed_label}\u201c abgeschlossen. '
                    f'Sollen wir mit \u201e{_next_label}\u201c weitermachen, '
                    f'oder reicht das f\u00fcr den Report?'
                )
            else:
                # All blocks done → transition to summary
                _phase_state["conversation_phase"] = "summary"
                db.execute(
                    _sa_text("UPDATE chat_sessions SET phase_state = CAST(:ps AS jsonb) WHERE id = :sid"),
                    {"ps": json.dumps(_phase_state), "sid": str(session.id)},
                )
                db.commit()
                _block_transition_text = (
                    f'Bereich \u201e{_completed_label}\u201c abgeschlossen \u2014 '
                    f'damit haben wir alle gew\u00e4hlten Bereiche behandelt. '
                    f'Ich erstelle jetzt Ihre Zusammenfassung.'
                )

        # KIS-1128B V1-BE-2: Template mode — bypass Sonnet for QR-to-QR turns.
        # When user clicked a QR button AND the next field has a deterministic
        # template, serve the response without calling Sonnet (~200ms vs ~3300ms).
        _template_text = None
        if (
            _is_qr_click
            and next_fields
            and is_template_field(next_fields[0])
            and not _checkpoint_triggered
            and not _block_just_completed
            and not _report_start_requested
            and not _is_help_request
            and not _is_edit_request
            and not (_is_in_edit_mode and not _edit_applied)
            and not _no_extraction  # e.g. __checkpoint__, __block_transition__
        ):
            _tpl_field = next_fields[0]
            _tpl_question = get_template_question(_tpl_field)
            if _tpl_question:
                # KIS-1128B V1-BE-3: Prepend varied confirmation sentence
                _last_conf = _used_confirmations[-1] if _used_confirmations else None
                _conf = get_confirmation(_tpl_field, _last_conf)
                _template_text = f"{_conf} {_tpl_question}"
                log.info(
                    "[CHAT] TEMPLATE MODE: next_field=%s, confirm=%r (no Sonnet, ~200ms)",
                    _tpl_field, _conf,
                )

        async def _token_producer():
            try:
                if _checkpoint_text:
                    # Checkpoint: send static text, no Sonnet call
                    await queue.put(_checkpoint_text)
                    return

                if _block_transition_text:
                    # Block transition: send static text, no Sonnet call
                    await queue.put(_block_transition_text)
                    return

                if _report_start_requested:
                    # KIS-1125: Skip Sonnet — send confirmation, trigger completion below
                    await queue.put("Ihre Auswertung wird jetzt erstellt. Sie erhalten den Report in Kürze.")
                    return

                if _template_text:
                    # KIS-1128B: Template mode — deterministic text, no Sonnet call
                    await queue.put(_template_text)
                    return

                async for token in generate_response(
                    session_messages=list(session.messages),
                    collected_fields=collected,
                    missing_fields=all_missing,
                    next_fields=next_fields,
                    section=current_section,
                    report_type=rt,
                    draft_mode=DRAFT_MODE_ENABLED,
                    pending_field=_sonnet_pending_field,
                    pending_value=_sonnet_pending_value,
                    dialog_mode=_sonnet_dialog_mode,
                    help_context=_help_ctx,
                    next_field_qr_context=_next_field_qr_context,
                    user_profile_summary=_user_profile_summary,
                    recent_bot_messages=_recent_bot_msgs,
                    conversation_phase=_sonnet_conv_phase,
                    missing_phase_1_fields=_missing_p1_for_sonnet,
                    current_block=_sonnet_block_id,
                    remaining_block_fields=_sonnet_block_remaining,
                    used_confirmations=_used_confirmations,
                ):
                    await queue.put(token)
            except Exception as exc:
                await queue.put(exc)
            finally:
                await queue.put(_SENTINEL)

        # KIS-1128A V4-BE: Send typing event before Sonnet call.
        # Skip for template turns (checkpoint, block transition, report start,
        # KIS-1128B template mode) which are fast enough (<200ms) that a
        # typing indicator would flicker.
        _is_sonnet_turn = not (_checkpoint_text or _block_transition_text or _report_start_requested or _template_text)
        if _is_sonnet_turn:
            yield f'event: typing\ndata: {json.dumps({"status": "thinking"})}\n\n'

            # KIS-1128C V5-BE: Optimistic QR preview — send preview of QR buttons
            # before Sonnet responds, so the frontend can render them early.
            # Only for freetext→QR transitions (template mode already bypasses Sonnet).
            # Hotfix: initialise _profile_ctx early to avoid UnboundLocalError
            _profile_ctx = None
            if rt == "strategy":
                _profile_ctx = _load_r1_profile_for_strategy(session, db)
            if next_fields and is_template_field(next_fields[0]):
                _pqr = _build_quick_replies(next_fields[:1], rt, collected, _profile_ctx)
                if _pqr:
                    _pqr_data = [qr.model_dump() for qr in _pqr]
                    yield f'event: preview_qr\ndata: {json.dumps(_pqr_data)}\n\n'

        producer = asyncio.create_task(_token_producer())
        full_response = ""
        try:
            while True:
                try:
                    item = await asyncio.wait_for(
                        queue.get(), timeout=_HB_INTERVAL,
                    )
                except asyncio.TimeoutError:
                    yield f"event: heartbeat\ndata: {{}}\n\n"
                    continue
                if item is _SENTINEL:
                    break
                if isinstance(item, Exception):
                    raise item
                full_response += item
                yield f"event: token\ndata: {json.dumps({'text': item})}\n\n"
        except Exception as exc:
            log.error("[CHAT] Streaming error: %s", exc, exc_info=True)
            error_msg = "Entschuldigung, es gab einen Fehler. Bitte versuchen Sie es nochmal."
            yield f"event: error\ndata: {json.dumps({'code': 'stream_error', 'message': error_msg})}\n\n"
            return
        finally:
            if not producer.done():
                producer.cancel()

        # ------------------------------------------------------------------
        # Phase 3: Draft SSE events, QR generation, state update, done
        # ------------------------------------------------------------------

        # Emit draft SSE events (before state_update, after token stream)
        if DRAFT_MODE_ENABLED:
            if _draft_confirmed_field:
                yield _sse_field_confirmed(
                    field=_draft_confirmed_field,
                    value=_draft_confirmed_value,
                )
                yield _sse_dialog_mode(active=False)
            if _draft_new_field:
                yield _sse_draft_value(
                    field=_draft_new_field,
                    value=_draft_new_value,
                    label=get_field_label(_draft_new_field, rt),
                )
                yield _sse_dialog_mode(active=False)
            if _signal == "question":
                yield _sse_dialog_mode(active=True)

        # QR generation — phase-aware
        # Fix 4: For strategy sessions, load R1 profile for context-aware QR
        _profile_ctx = None
        if rt == "strategy":
            _profile_ctx = _load_r1_profile_for_strategy(session, db)

        # Determine qr_next based on conversation phase
        _final_phase = _phase_state.get("conversation_phase") if rt == "r1" else None

        if _checkpoint_triggered or _final_phase == "checkpoint":
            # Checkpoint: show topic selection buttons
            _cp_options = [
                QuickReplyOption(value="A", label="Fördermittel & Budget"),
                QuickReplyOption(value="B", label="KI-Strategie & Roadmap"),
                QuickReplyOption(value="C", label="Tools & Automatisierung"),
                QuickReplyOption(value="D", label="Recht & Datenschutz"),
                QuickReplyOption(value="ALL", label="Alle Bereiche vertiefen"),
                QuickReplyOption(value="REPORT", label="Report jetzt erstellen"),
            ]
            # KIS-1128C V9-BE-1: Schnellmodus for expert users
            _cp_ki = collected.get("ki_kompetenz", "")
            _cp_digi = 0
            try:
                _cp_digi = int(collected.get("digitalisierungsgrad", 0))
            except (ValueError, TypeError):
                pass
            if _cp_ki == "hoch" and _cp_digi >= 7:
                _cp_options.append(QuickReplyOption(
                    value="__fast_mode__",
                    label="Schnellmodus (alle Fragen auf einmal)",
                    style="secondary",
                ))
            quick_replies = [QuickReply(
                field="__checkpoint__",
                label="Bereiche vertiefen",
                options=_cp_options,
                multi_select=True,
                max_select=4,
            )]
        elif _final_phase == "summary" and not _is_edit_request and (not _is_in_edit_mode or _edit_applied):
            # KIS-1124-HOTFIX: Summary phase needs action buttons so user can
            # start the report or request edits. Previously was [] → user had
            # to type manually, which is not discoverable.
            # KIS-1131 FX-2: Suppress during edit-mode (but show again after edit applied).
            quick_replies = [QuickReply(
                field="__summary_action__",
                label="Nächster Schritt",
                options=[
                    QuickReplyOption(value="__start_report__", label="Auswertung starten", style="primary"),
                    QuickReplyOption(value="__edit_summary__", label="Angaben korrigieren", style="secondary"),
                ],
                multi_select=False,
            )]
        elif _final_phase == "phase_1" and _post_phase_1a:
            # Phase 1a: show QR for next sequential QR field
            if _no_extraction and _asked_field and _asked_field not in collected:
                qr_next = [_asked_field]
            else:
                _next_qr = _get_next_phase_1a_field(collected)
                qr_next = [_next_qr] if _next_qr else []
            quick_replies = _build_quick_replies(qr_next, rt, collected, _profile_ctx)
        elif _final_phase == "phase_1":
            # Phase 1b: open conversation — show QR for structured fields
            # KIS-1124 Testrun 3 Bugs 16+17: Show QR buttons for fields that
            # need structured input (digitalisierungsgrad, ki_kompetenz) to
            # prevent Doppelfrage and unclear free text answers.
            _p1b_qr_fields = [f for f in next_fields
                              if f in ("digitalisierungsgrad", "ki_kompetenz")]
            quick_replies = _build_quick_replies(
                _p1b_qr_fields, rt, collected, _profile_ctx,
            ) if _p1b_qr_fields else []
        elif _final_phase == "phase_2" and rt == "r1":
            if _block_just_completed:
                # Block just completed — show inter-block transition QR
                _remaining_blocks_qr = [b for b in _phase_state.get("selected_blocks", [])
                                        if b not in _phase_state.get("completed_blocks", [])]
                if _remaining_blocks_qr:
                    _next_b = _remaining_blocks_qr[0]
                    quick_replies = [QuickReply(
                        field="__block_transition__",
                        label="Nächster Schritt",
                        options=[
                            QuickReplyOption(value="continue",
                                             label=f"Weiter: {BLOCK_LABELS.get(_next_b, _next_b)}"),
                            QuickReplyOption(value="report", label="Report erstellen"),
                        ],
                        multi_select=False,
                    )]
                else:
                    # All blocks done → summary, no QR needed
                    quick_replies = []
            else:
                # Phase 2: block-scoped QR only
                _cur_block = _phase_state.get("current_block")
                _block_remaining = _get_block_fields(_cur_block, collected) if _cur_block else []
                if _no_extraction and _asked_field and _asked_field not in collected:
                    qr_next = [_asked_field]
                else:
                    qr_next = _block_remaining[:1]
                quick_replies = _build_quick_replies(qr_next, rt, collected, _profile_ctx)
        else:
            # Legacy / Strategy: section-based QR
            if _no_extraction and _asked_field and _asked_field not in collected:
                qr_next = [_asked_field]
            else:
                qr_next = get_next_fields(collected, _current_section, max_fields=1, report_type=rt)

            if _is_qr_click and not (req.quick_reply_field == "__checkpoint__"):
                quick_replies = _build_quick_replies(qr_next, rt, collected, _profile_ctx)
            elif DRAFT_MODE_ENABLED and _pending_after_turn:
                quick_replies = [QuickReply(
                    field="_draft_action",
                    label="Angabe bestätigen",
                    options=[
                        QuickReplyOption(value="confirm", label="✓ Übernehmen"),
                        QuickReplyOption(value="edit", label="✏️ Ändern"),
                    ],
                    multi_select=False,
                )]
            elif DRAFT_MODE_ENABLED and _signal == "question":
                quick_replies = []
            elif _is_edit_request or (_is_in_edit_mode and not _edit_applied):
                quick_replies = []
            else:
                quick_replies = _build_quick_replies(qr_next, rt, collected, _profile_ctx)

        # ------------------------------------------------------------------
        # Post-process response text (KIS-1124 Testrun 3: Bugs 13, 14, 9)
        # ------------------------------------------------------------------
        _qr_labels = []
        if quick_replies:
            for qr in quick_replies:
                _qr_labels.extend(opt.label for opt in (qr.options or []))
        full_response = _post_process_response(full_response, _qr_labels or None)
        # Send cleaned text as replacement so frontend can swap out streamed version
        yield f"event: text_replace\ndata: {json.dumps({'text': full_response})}\n\n"

        assistant_msg = {
            "role": "assistant",
            "content": full_response,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "turn": turn,
            "fields_extracted": normalized if normalized else None,
            "section_index": _current_section,
            "quick_replies": [qr.model_dump() for qr in quick_replies] if quick_replies else None,
        }
        msgs = list(session.messages)
        msgs.append(assistant_msg)
        session.messages = msgs
        session.updated_at = datetime.now(timezone.utc)
        db.commit()

        # Check if all fields are done → send summary
        # Also regenerate summary after an edit was applied
        # KIS-1124: Also trigger summary when user selects "Report jetzt erstellen"
        # from the checkpoint (conversation_phase == "summary").
        _phase_summary_requested = (_final_phase == "summary" and not _has_summary_been_sent(session))

        # KIS-1124-S0-BE-1: Check ALL sections, not just current, to prevent
        # premature summary when earlier-section fields (e.g. ki_hemmnisse) are missing.
        last_section = _current_section >= len(sections) - 1
        _globally_complete = False
        if last_section and not next_fields:
            _globally_complete = True
            for _si in range(len(sections)):
                _mr, _mo = get_missing_fields(collected, _si, rt)
                if _mr or _mo:
                    _globally_complete = False
                    break
        all_fields_done = last_section and _globally_complete
        _should_send_summary = (
            (all_fields_done and not _has_summary_been_sent(session))
            or _edit_applied
            or (_phase_summary_requested and not _is_edit_request)  # KIS-1131 FX-2
        )
        if _should_send_summary:
            from services.chat_conversation import build_summary
            summary_text = build_summary(collected, rt)
            yield f"event: token\ndata: {json.dumps({'text': summary_text})}\n\n"
            summary_msg = {
                "role": "assistant",
                "content": summary_text,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "turn": turn,
                "section_index": _current_section,
            }
            msgs2 = list(session.messages)
            msgs2.append(summary_msg)
            session.messages = msgs2
            db.commit()

        # KIS-1125-HOTFIX: Report completion — trigger directly when user clicks
        # "Auswertung starten". Skips Sonnet (confirmation text already streamed
        # via _token_producer), creates Briefing, sends report_started event.
        _briefing_id = None
        _redirect_url = None
        if _report_start_requested:
            try:
                now = datetime.now(timezone.utc)
                _briefing_id = _complete_r1(session, collected, db, now)
                _redirect_url = _complete_redirect(rt, _briefing_id)
                log.info("[CHAT] Report triggered: briefing_id=%s, session=%s", _briefing_id, session.id)
                yield f"event: report_started\ndata: {json.dumps({'briefing_id': _briefing_id, 'redirect_url': _redirect_url})}\n\n"
            except Exception as exc:
                log.error("[CHAT] Report completion failed: %s", exc, exc_info=True)
                yield f"event: error\ndata: {json.dumps({'code': 'completion_error', 'message': 'Report-Erstellung fehlgeschlagen. Bitte versuchen Sie es erneut.'})}\n\n"
            # No QR buttons after report start
            quick_replies = []

        state = _build_session_state(session, collected_override=collected, section_override=_current_section)
        state.quick_replies = quick_replies
        # Draft fields only included when DRAFT_MODE_ENABLED — otherwise identical to pre-draft output
        _draft_exclude = None if DRAFT_MODE_ENABLED else {"pending_field", "pending_value", "dialog_mode"}
        yield f"event: state_update\ndata: {state.model_dump_json(exclude=_draft_exclude)}\n\n"

        if quick_replies:
            qr_data = [qr.model_dump() for qr in quick_replies]
            yield f"event: quick_replies\ndata: {json.dumps(qr_data)}\n\n"

        # KIS-1125-HOTFIX: Include post-processed text in done event.
        # The token stream sends raw Sonnet output; text_replace sends the
        # cleaned version but the frontend doesn't handle that event yet.
        # By including the final text in done (which the frontend already
        # processes), the frontend can replace the streamed tokens.
        _done_data: dict = {'turn': turn, 'text': full_response}
        if _briefing_id is not None:
            _done_data['briefing_id'] = _briefing_id
            _done_data['redirect_url'] = _redirect_url
        yield f"event: done\ndata: {json.dumps(_done_data)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ===========================================================================
# POST /api/chat/confirm  (Draft-Pattern — Sprint 1 skeleton only)
# ===========================================================================

@router.post("/confirm")
async def confirm_field(req: ConfirmFieldRequest, db: Session = Depends(get_db)):
    """Confirm or discard a draft value via explicit endpoint."""
    if not DRAFT_MODE_ENABLED:
        raise HTTPException(status_code=404, detail="Draft mode not enabled")

    session = db.query(ChatSession).filter(ChatSession.id == req.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session nicht gefunden")
    if session.status != "active":
        raise HTTPException(status_code=400, detail="Session ist nicht aktiv")

    pending = dict(getattr(session, 'draft_state', None) or {})
    if not pending.get("pending_field"):
        raise HTTPException(status_code=400, detail="Kein offener Entwurf vorhanden")

    rt = session.report_type
    now = datetime.now(timezone.utc)

    if req.action == "confirm":
        field = pending["pending_field"]
        value = req.value if req.value is not None else pending["pending_value"]

        collected = dict(session.collected_fields or {})
        collected[field] = value
        session.collected_fields = collected

        field_meta = dict(session.field_meta or {})
        field_meta[field] = {
            "confidence": "high",
            "source_turn": session.turn_count,
            "raw_input": "confirmed_via_endpoint",
            "normalized": True,
            "confirmed": True,
        }
        session.field_meta = field_meta
        session.draft_state = {"pending_field": None, "pending_value": None, "dialog_mode": False}
        session.updated_at = now

        # Section transition check (raw SQL inside, commits internally)
        _check_section_transition(session, collected, db, rt)
        db.commit()  # for remaining ORM fields (collected_fields, draft_state, etc.)

        next_fields = get_next_fields(collected, session.current_section, report_type=rt)
        log.info("[CHAT] Confirm endpoint: %s=%r confirmed", field, value)

        return {
            "status": "confirmed",
            "field": field,
            "value": value,
            "next_fields": next_fields,
            "progress_percent": calculate_progress(collected, rt),
        }

    elif req.action == "edit":
        cleared_field = pending["pending_field"]
        session.draft_state = {"pending_field": None, "pending_value": None, "dialog_mode": False}
        session.updated_at = now
        db.commit()

        log.info("[CHAT] Confirm endpoint: draft for %s cleared (edit)", cleared_field)

        return {
            "status": "cleared",
            "field": cleared_field,
            "message": "Entwurf verworfen, bitte erneut antworten",
        }

    else:
        raise HTTPException(status_code=400, detail=f"Ungültige Aktion: {req.action}")


# ===========================================================================
# GET /api/chat/session/{session_id}
# ===========================================================================

@router.get("/session/{session_id}", response_model=ChatSessionResponse)
async def chat_session_get(session_id: UUID, db: Session = Depends(get_db)):
    """Get session state and recent messages (for resume / frontend init)."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session nicht gefunden")

    rt = session.report_type
    state = _build_session_state(session)
    # Use state.next_fields (already computed with correct max_fields logic)
    # instead of calling get_next_fields again with default max_fields=1
    _profile_ctx = _load_r1_profile_for_strategy(session, db) if rt == "strategy" else None
    state.quick_replies = _build_quick_replies(state.next_fields, rt, session.collected_fields, _profile_ctx)

    # Last 10 messages
    all_msgs = session.messages or []
    recent_msgs = all_msgs[-10:]
    chat_messages = []
    for m in recent_msgs:
        chat_messages.append(ChatMessage(
            role=m["role"],
            content=m["content"],
            timestamp=m.get("timestamp", session.created_at.isoformat()),
            turn=m.get("turn", 0),
            fields_extracted=m.get("fields_extracted"),
            section_index=m.get("section_index"),
            quick_replies=m.get("quick_replies"),
        ))

    resumable = session.status == "active"

    return ChatSessionResponse(
        state=state,
        messages=chat_messages,
        resumable=resumable,
        last_activity=session.last_activity_at,
    )


# ===========================================================================
# GET /api/chat/session/{session_id}/fields — export collected fields for form pre-fill
# KIS-1124 Sprint 4 S4-BE-3: Formular-Wechsel mit Feld-Übernahme
# ===========================================================================

@router.get("/session/{session_id}/fields")
async def chat_session_fields(session_id: UUID, db: Session = Depends(get_db)):
    """Export all collected fields as JSON for form pre-fill.

    Used when the user clicks "Zum Formular wechseln" — the frontend
    fetches this endpoint and pre-fills the static form with already
    collected chat values.
    """
    from schemas.chat import ChatFieldsExportResponse

    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session nicht gefunden")

    collected = dict(session.collected_fields or {})
    ps = session.phase_state or {}

    return ChatFieldsExportResponse(
        fields=collected,
        conversation_phase=ps.get("conversation_phase", "phase_1"),
        selected_blocks=ps.get("selected_blocks", []),
        completed_blocks=ps.get("completed_blocks", []),
        current_block=ps.get("current_block"),
        collected_count=len(collected),
        report_type=session.report_type,
    )


# ===========================================================================
# KIS-1128C V9-BE-2: Schnellmodus — fast-mode endpoints
# ===========================================================================

@router.get("/session/{session_id}/fast-mode")
async def get_fast_mode_fields(session_id: UUID, db: Session = Depends(get_db)):
    """Return all remaining fields grouped by block for the fast-mode form.

    Only returns fields for selected blocks that haven't been collected yet.
    Each field includes its question text, input type, and QR options (if any).
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session nicht gefunden")

    collected = dict(session.collected_fields or {})
    ps = session.phase_state or {}
    selected = ps.get("selected_blocks", ["A", "B", "C", "D"])
    rt = session.report_type

    registry = get_registry_for_report(rt)
    result = []
    for block_id in selected:
        if block_id == "D":
            all_fields = _get_datenschutz_block_fields(collected.get("branche", ""))
        else:
            all_fields = BLOCK_FIELDS.get(block_id, [])

        block_fields = []
        for field in all_fields:
            if field in collected:
                continue
            reg = registry.get(field, {})
            qr_options = _QR_OPTIONS.get(field)
            question = FIELD_QUESTIONS.get(field, get_field_label(field))
            block_fields.append({
                "field": field,
                "question": question,
                "type": "select" if qr_options else reg.get("type", "text"),
                "multi_select": reg.get("type") == "multi",
                "options": qr_options,
            })

        if block_fields:
            result.append({
                "block": block_id,
                "label": BLOCK_LABELS.get(block_id, block_id),
                "fields": block_fields,
            })

    return {"blocks": result}


@router.post("/session/{session_id}/fast-mode/submit")
async def submit_fast_mode(session_id: UUID, data: dict, db: Session = Depends(get_db)):
    """Bulk-submit all fast-mode field values, then redirect to summary.

    Expects: {"fields": {"field_name": "value", ...}}
    Each value is normalized via the standard normalize_field pipeline.
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session nicht gefunden")

    collected = dict(session.collected_fields or {})
    rt = session.report_type
    now = datetime.now(timezone.utc)

    submitted = data.get("fields", {})
    accepted = 0
    for field, value in submitted.items():
        if value is None or value == "":
            continue
        result = normalize_field(field, value, collected, report_type=rt)
        if result.value is not None and result.confidence != "low":
            collected[field] = result.value
            accepted += 1
            log.info("[CHAT] FAST-MODE: %s=%s (confidence=%s)", field, result.value, result.confidence)

    # Persist collected fields + move to summary phase
    ps = dict(session.phase_state or {})
    ps["conversation_phase"] = "summary"
    ps["current_block"] = None

    db.execute(
        _sa_text("""
            UPDATE chat_sessions
            SET collected_fields = CAST(:cf AS jsonb),
                phase_state = CAST(:ps AS jsonb),
                updated_at = :ts
            WHERE id = :sid
        """),
        {
            "cf": json.dumps(collected),
            "ps": json.dumps(ps),
            "ts": now.isoformat(),
            "sid": str(session.id),
        },
    )
    db.commit()

    log.info("[CHAT] FAST-MODE submit: session=%s, accepted=%d/%d fields",
             session_id, accepted, len(submitted))

    return {
        "status": "ok",
        "collected_count": len(collected),
        "accepted": accepted,
        "redirect": "summary",
    }


# ===========================================================================
# GET /api/chat/sessions — list open sessions for authenticated user
# ===========================================================================

@router.get("/sessions", response_model=list[ChatSessionSummary])
async def chat_sessions_list(
    request: Request,
    db: Session = Depends(get_db),
    status: str = "active",
):
    """List chat sessions for the authenticated user, filtered by status."""
    user_id, _ = _resolve_user(request, db)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentifizierung erforderlich")

    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id, ChatSession.status == status)
        .order_by(ChatSession.last_activity_at.desc())
        .limit(10)
        .all()
    )

    result = []
    for s in sessions:
        rt = s.report_type
        registry = get_registry_for_report(rt)
        collected = s.collected_fields or {}
        result.append(ChatSessionSummary(
            session_id=s.id,
            report_type=rt,
            status=s.status,
            current_section=s.current_section,
            collected_count=len(collected),
            total_fields=len(registry),
            progress_percent=calculate_progress(collected, rt),
            created_at=s.created_at,
            last_activity=s.last_activity_at,
            resumable=s.status == "active",
        ))

    return result


# ===========================================================================
# POST /api/chat/complete
# ===========================================================================

@router.post("/complete", response_model=ChatCompleteResponse)
async def chat_complete(
    req: ChatCompleteRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Finalize chat session and submit collected data to report pipeline."""
    session = db.query(ChatSession).filter(ChatSession.id == req.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session nicht gefunden")

    # KIS-1131 Fix 3: Idempotency check BEFORE status guard — the SSE stream
    # may have already completed the session via _complete_r1(), so a
    # subsequent /complete call should return the existing briefing_id
    # instead of 400.
    rt = session.report_type
    if session.status == "completed" and session.briefing_id:
        redirect = _complete_redirect(rt, session.briefing_id)
        return ChatCompleteResponse(
            success=True,
            briefing_id=session.briefing_id,
            report_type=rt,
            redirect_url=redirect,
        )

    if session.status != "active":
        raise HTTPException(status_code=400, detail="Session ist nicht aktiv")
    if not req.confirmed:
        raise HTTPException(status_code=400, detail="Bestätigung erforderlich")

    sections = get_sections_for_report(rt)

    # Check all required fields (across all sections)
    collected = dict(session.collected_fields or {})
    missing_all: list[str] = []
    for section in sections:
        sec_idx: int = section["index"]
        missing_req, _ = get_missing_fields(collected, sec_idx, rt)
        missing_all.extend(missing_req)
    if missing_all:
        raise HTTPException(
            status_code=400,
            detail=f"Pflichtfelder fehlen: {', '.join(missing_all)}",
        )

    now = datetime.now(timezone.utc)

    if rt == "strategy":
        briefing_id = await _complete_strategy(session, collected, db, now)
    else:
        briefing_id = _complete_r1(session, collected, db, now, request)

    redirect = _complete_redirect(rt, briefing_id)

    log.info(
        "[CHAT] Session %s completed -> briefing_id=%s (report_type=%s, fields=%d)",
        session.id, briefing_id, rt, len(collected),
    )

    return ChatCompleteResponse(
        success=True,
        briefing_id=briefing_id,
        report_type=rt,
        redirect_url=redirect,
    )


# ===========================================================================
# Response Post-Processing (KIS-1124 Testrun 3)
# ===========================================================================

# Regex to strip <quick_reply_buttons>...</quick_reply_buttons> tags
_QR_TAG_RE = re.compile(
    r'\s*<quick_reply_buttons>.*?</quick_reply_buttons>\s*',
    re.DOTALL,
)

# English exclamations that Sonnet sometimes outputs despite German-only rule
_ENGLISH_EXCLAMATIONS = [
    "Excellent", "Great", "Amazing", "Perfect", "Wonderful",
    "Awesome", "Brilliant", "Fantastic",
]

# German flattery words forbidden as sentence starters
_FORBIDDEN_STARTERS = [
    "Ausgezeichnet", "Exzellent", "Hervorragend", "Wunderbar",
    "Beeindruckend", "Fantastisch", "Großartig", "Spannend",
    "Interessant",
    # KIS-1124 Testrun 4 R5: eingedeutschte Varianten
    "Brillant", "Prima", "Klasse", "Super", "Toll",
    # KIS-1128C P2: "Sehr + Adjektiv" Testrun-9
    "Sehr interessant", "Sehr gut", "Sehr spannend",
]

# KIS-1124 Testrun 4 R3: Context reference patterns that Sonnet over-uses
_CONTEXT_REF_PATTERNS = [
    r'Da Sie bereits\b',
    r'Bei Ihrer (?:hohen|aktuellen|starken|bisherigen|umfangreichen)\b',
    r'Mit Ihren? (?:umfangreichen|hohen|breiten|starken|bisherigen)\b',
]

# KIS-1128A V2-BE: Preamble patterns to strip (Danke/Lob/Rückbezug)
_PREAMBLE_PATTERNS = [
    re.compile(r'^Danke\b', re.IGNORECASE),
    re.compile(r'^Vielen Dank\b', re.IGNORECASE),
    re.compile(r'^Da Sie\b', re.IGNORECASE),
    re.compile(r'^Mit Ihrer\b', re.IGNORECASE),
    re.compile(r'^Bei Ihrer\b', re.IGNORECASE),
    re.compile(r'^Bei Ihrem\b', re.IGNORECASE),
    re.compile(r'^Ihre\b.*zeig', re.IGNORECASE),
    re.compile(r'^Spannend\b', re.IGNORECASE),
    re.compile(r'^Interessant\b', re.IGNORECASE),
    re.compile(r'^Sehr gut\b', re.IGNORECASE),
    re.compile(r'^Sehr\s+(interessant|spannend|gut)\b', re.IGNORECASE),  # P2: "Sehr interessant!" etc.
    re.compile(r'^Perfekt\b', re.IGNORECASE),
    re.compile(r'^Verstanden\b.*,\s', re.IGNORECASE),
    re.compile(r'^Notiert\b.*,\s', re.IGNORECASE),
]


def _strip_context_preamble(text: str) -> str:
    """Strip Danke/context preamble sentences, keep only the question.

    KIS-1128A V2-BE: Phase 2 answers should be ≤15 words. This safety net
    strips known preamble patterns (Danke, Rückbezug, Lob) when the last
    sentence is a question.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= 1:
        return text

    # Only strip if last sentence is a question
    if not sentences[-1].strip().endswith('?'):
        return text

    cleaned = [s for s in sentences
               if not any(p.search(s) for p in _PREAMBLE_PATTERNS)]
    if cleaned:
        return ' '.join(cleaned)
    return text


def _post_process_response(
    text: str,
    qr_labels: list[str] | None = None,
) -> str:
    """Clean Sonnet response before sending to frontend.

    1. Strip <quick_reply_buttons> XML tags (Bug 13)
    2. Remove QR-label blocks duplicated in prose (Bug 14, R1)
    3. Remove English exclamations (Bug 9 reopen)
    4. Remove forbidden flattery starters (Schmeichelei, R5)
    5. Remove context repetition patterns (R3)
    6. Double-question guard (KIS-1124-HOTFIX)
    """
    if not text:
        return text

    log.info("[POST-PROCESS] Input (first 120 chars): %s | qr_labels=%s",
             text[:120].replace('\n', '\\n'), qr_labels)

    # 1. Strip <quick_reply_buttons> tags
    text = _QR_TAG_RE.sub('', text)

    # 2. Strip other XML-like tags Sonnet might generate
    text = re.sub(r'</?quick_reply[^>]*>', '', text)

    # 2a-bis. KIS-1131 Fix 1: Strip [Quick-Reply Buttons:] header (new Sonnet format)
    text = re.sub(r'\[Quick-Reply Buttons?:\]\s*', '', text, flags=re.IGNORECASE)

    # 2b. KIS-1128C P1: Strip <button>...</button> tags (Sonnet generates HTML buttons)
    text = re.sub(r'\s*<button>[^<]*</button>\s*', '', text, flags=re.DOTALL)

    # 2c. KIS-1128C P3: Strip **Option** | **Option** pipe-separated QR format
    text = re.sub(r'\n*(?:\*\*[^*]+\*\*\s*\|\s*)+\*\*[^*]+\*\*\s*', '', text)

    # 3. Remove QR-labels duplicated in prose (Bug 14 + R1)
    if qr_labels and len(qr_labels) >= 2:
        # R1 Format A/C: Markdown list items matching QR labels ("- Ja\n- Nein")
        for label in qr_labels:
            text = re.sub(
                rf'(?:^|\n)\s*[-*]\s*{re.escape(label)}\s*(?=\n|$)',
                '', text, flags=re.IGNORECASE,
            )

        # R1 Format B: Emoji radio buttons ("🔘 Option")
        text = re.sub(r'(?:^|\n)\s*🔘\s*.+', '', text)

        # R1 Format C: Bold label headers + subsequent list items
        # Matches "**Marktposition:**\n- Option1\n- Option2\n- Option3"
        text = re.sub(
            r'\*\*[^*]{3,40}:\*\*\s*\n(?:\s*[-*]\s*.+\n?)+',
            '', text,
        )
        # Standalone bold headers without list (fallback)
        text = re.sub(r'\*\*[^*]{3,40}:\*\*\s*\n?', '', text)

        # KIS-1124 Sprint 4 Fix C: Non-bold header + markdown list of QR labels
        # Catches e.g. "Risikofreude (1–5):\n- 1 (sehr vorsichtig)\n- 2\n..."
        # Header is any line ending with ":" where subsequent list items match QR labels
        escaped_labels = [re.escape(lbl) for lbl in qr_labels]
        label_alt = "|".join(escaped_labels)
        text = re.sub(
            rf'(?:^|\n)[^\n]{{3,50}}:\s*\n(?:\s*[-*]\s*(?:{label_alt})\s*\n?)+',
            '', text, flags=re.IGNORECASE,
        )

        # Original Bug 14: contiguous block of labels (slash/comma/pipe separated)
        if len(qr_labels) >= 3:
            escaped = [re.escape(lbl) for lbl in qr_labels]
            label_pattern = r'[\s/,\|]+'.join(escaped[:6])
            text = re.sub(
                rf'\*{{0,2}}{label_pattern}\*{{0,2}}',
                '', text, flags=re.IGNORECASE,
            )

        # KIS-1124: Catch-all — remove any line whose content (after stripping
        # list markers "- ", "* ", "🔘 ", digits) exactly matches a QR label.
        label_set = {lbl.lower().strip() for lbl in qr_labels}
        cleaned_lines = []
        for line in text.split('\n'):
            stripped = line.strip().lstrip('-*🔘 ').strip()
            # Also strip leading digits + optional parenthesized text
            stripped_no_num = re.sub(r'^\d+\s*(?:\([^)]*\))?\s*', '', stripped).strip()
            if stripped.lower() in label_set or stripped_no_num.lower() in label_set:
                continue  # drop this line — it's a bare QR label
            cleaned_lines.append(line)
        text = '\n'.join(cleaned_lines)

        # KIS-1124: Numbered scale labels like "1 (sehr vorsichtig)", "2", "3 (ausgewogen)"
        text = re.sub(
            r'(?:^|\n)\s*[-*]?\s*\d+\s*(?:\([^)]*\))?\s*$',
            '', text, flags=re.MULTILINE,
        )

    # 4. English exclamations (Bug 9 reopen)
    for word in _ENGLISH_EXCLAMATIONS:
        text = re.sub(
            rf'\b{word}[!.,]?\s*', '', text, flags=re.IGNORECASE,
        )

    # 5. Forbidden flattery at sentence start (R5: +Exzellent, Brillant, etc.)
    # KIS-1124-HOTFIX: Previous regex only matched at absolute string start (^)
    # or after ". " — missed "Hervorragend!" after newlines. Now matches at
    # line starts (re.MULTILINE) and after common sentence boundaries.
    for word in _FORBIDDEN_STARTERS:
        text = re.sub(
            rf'(?:^|(?<=\. )|(?<=\.\n)|(?<=\n)){word}[!.,;:\u2014\u2013]?\s*(?:[\u2014\u2013]\s*)?',
            '', text, flags=re.IGNORECASE | re.MULTILINE,
        )

    # 6. Context repetition filter (R3: "Da Sie bereits..." etc.)
    for pattern in _CONTEXT_REF_PATTERNS:
        # Remove entire sentence starting with the pattern
        text = re.sub(
            rf'(?:^|\.\s+){pattern}[^.!?]*[.!?]',
            '.', text, flags=re.IGNORECASE,
        )

    # 6b. KIS-1128A V2-BE: Strip Danke/context preambles, keep only the question.
    text = _strip_context_preamble(text)

    # 7. Double-question guard: when QR buttons are present and text contains
    # 2+ questions, truncate after the first question mark to prevent
    # Sonnet from asking about two fields in one turn.
    if qr_labels and text.count('?') >= 2:
        first_q = text.index('?')
        rest = text[first_q + 1:].strip()
        # Only truncate if the second question starts a new sentence
        if rest and rest[0].isupper():
            text = text[:first_q + 1].strip()

    # Clean up artifacts
    text = re.sub(r'^[\s.]+', '', text)  # Leading dots/spaces
    text = re.sub(r'  +', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    result = text.strip()

    log.info("[POST-PROCESS] Output (first 120 chars): %s", result[:120].replace('\n', '\\n'))
    return result


# ===========================================================================
# SSE Event Helpers — Draft-Pattern (Sprint 1: defined, not yet called)
# ===========================================================================

def _sse_draft_value(field: str, value, label: str) -> str:
    """SSE event: draft value extracted, awaiting user confirmation."""
    data = json.dumps({"field": field, "value": value, "label": label})
    return f"event: draft_value\ndata: {data}\n\n"


def _sse_field_confirmed(field: str, value) -> str:
    """SSE event: draft confirmed, value written to collected_fields."""
    data = json.dumps({"field": field, "value": value})
    return f"event: field_confirmed\ndata: {data}\n\n"


def _sse_dialog_mode(active: bool) -> str:
    """SSE event: dialog mode toggled (follow-up question vs. progression)."""
    data = json.dumps({"active": active})
    return f"event: dialog_mode\ndata: {data}\n\n"


# ===========================================================================
# Helpers
# ===========================================================================

def _check_section_transition(
    session: ChatSession, collected: dict, db: Session, report_type: str = "r1",
) -> bool:
    """
    Check if all fields (required + optional) of the current section are
    collected. If so, advance current_section via raw SQL (same pattern as
    collected_fields) to avoid expired-ORM-object issues. Returns True if
    advanced.
    """
    sections = get_sections_for_report(report_type)
    if session.current_section >= len(sections) - 1:
        return False

    missing_req, missing_opt = get_missing_fields(collected, session.current_section, report_type)
    if missing_req or missing_opt:
        return False

    new_section = session.current_section + 1
    log.info(
        "[CHAT] Section transition: %d -> %d (%s)",
        session.current_section,
        new_section,
        sections[new_section]["name"],
    )

    # Persist via raw SQL — ORM object may be expired after prior raw SQL commit
    db.execute(
        _sa_text(
            "UPDATE chat_sessions SET current_section = :idx, updated_at = :ts WHERE id = :sid"
        ),
        {"idx": new_section, "sid": str(session.id), "ts": datetime.now(timezone.utc)},
    )
    db.commit()
    session.current_section = new_section  # keep local object in sync
    return True


def _complete_r1(
    session: ChatSession, collected: dict, db: Session, now: datetime,
    request: Request | None = None,
) -> int:
    """Complete R1 chat: create a Briefing for the report pipeline."""
    answers = dict(collected)
    answers["datenschutz"] = True  # consent given at chat start

    # KIS-1124 Sprint 4 S4-BE-2: Apply conservative defaults for blocks
    # that the user chose not to survey.  Only non-None defaults are written;
    # None means "intentionally omit → pipeline produces shorter section".
    ps = session.phase_state or {}
    surveyed_blocks = ps.get("selected_blocks", [])
    all_blocks = ["A", "B", "C", "D"]
    unsurveyed = [b for b in all_blocks if b not in surveyed_blocks]
    for block_id in unsurveyed:
        defaults = _REPORT_BLOCK_DEFAULTS.get(block_id, {})
        for field, default_val in defaults.items():
            if field not in answers and default_val is not None:
                answers[field] = default_val
    # Pass metadata so the report pipeline knows which areas were surveyed
    if unsurveyed:
        answers["_chat_unsurveyed_blocks"] = unsurveyed
        answers["_chat_surveyed_blocks"] = surveyed_blocks
        log.info("[CHAT] Complete R1: unsurveyed blocks %s → defaults applied", unsurveyed)

    # Extract user from JWT — user_id may already be set from /start
    user_id, user_email = _resolve_user(request, db)
    if not user_id:
        user_id = session.user_id  # fallback to session's user_id
    if user_email:
        answers["email"] = user_email
    log.info("[CHAT] Complete R1: user_email=%s, user_id=%s", user_email, user_id)

    briefing = Briefing(
        user_id=user_id,
        lang=session.lang,
        answers=answers,
        status="accepted",
        accepted_at=now,
    )
    db.add(briefing)
    db.flush()

    session.status = "completed"
    session.completed_at = now
    session.briefing_id = briefing.id
    session.updated_at = now
    db.commit()
    return briefing.id


async def _complete_strategy(
    session: ChatSession, collected: dict, db: Session, now: datetime,
) -> int:
    """Complete strategy chat: save questions, create report entry, trigger generation."""
    from models import Analysis, StrategyQuestion, StrategyReport

    briefing_id = session.briefing_id
    if not briefing_id:
        raise HTTPException(status_code=400, detail="Keine briefing_id in der Session")

    # Verify briefing exists
    briefing = db.query(Briefing).filter(Briefing.id == briefing_id).first()
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing nicht gefunden")

    # Upsert strategy questions (same logic as routes/strategy.py)
    existing = db.query(StrategyQuestion).filter(
        StrategyQuestion.briefing_id == briefing_id
    ).first()

    fields = {
        "s1_budget": collected.get("s1_budget", ""),
        "s2_zeitrahmen": collected.get("s2_zeitrahmen", ""),
        "s3_prioritaeten": collected.get("s3_prioritaeten", []),
        "s4_engpass": collected.get("s4_engpass", ""),
        "s5_software": collected.get("s5_software", ""),
        "s6_foerderinteresse": collected.get("s6_foerderinteresse", ""),
        "s7_entscheidung": collected.get("s7_entscheidung", ""),
        "s8_erfahrung": collected.get("s8_erfahrung"),
        "s9_ansatz": collected.get("s9_ansatz"),
        "s10_datenschutz": collected.get("s10_datenschutz"),
        "wettbewerber_anzahl": collected.get("wettbewerber_anzahl"),
        "kundenbindung_typ": collected.get("kundenbindung_typ"),
        "datenreife": collected.get("datenreife"),
    }

    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
        sq = existing
    else:
        sq = StrategyQuestion(briefing_id=briefing_id, **fields)
        db.add(sq)

    # Ensure strategy_reports entry exists
    sr = db.query(StrategyReport).filter(
        StrategyReport.briefing_id == briefing_id
    ).first()
    if not sr:
        sr = StrategyReport(briefing_id=briefing_id, status="pending")
        db.add(sr)

    session.status = "completed"
    session.completed_at = now
    session.updated_at = now

    # Set status to generating BEFORE commit so pipeline picks it up
    sr.status = "generating"
    sr.updated_at = now
    db.commit()
    db.refresh(sq)

    # Trigger strategy pipeline in background (same as POST /api/strategy/generate)
    analysis = db.query(Analysis).filter(
        Analysis.briefing_id == briefing_id
    ).order_by(Analysis.id.desc()).first()

    import asyncio
    asyncio.create_task(_run_strategy_pipeline_bg(
        briefing_id=briefing_id,
        briefing_data=briefing.answers or {},
        strategy_questions=sq.to_dict(),
        report1_data=(analysis.meta if analysis else {}) or {},
    ))
    log.info("[CHAT] Strategy pipeline triggered for briefing_id=%d", briefing_id)

    return briefing_id


async def _run_strategy_pipeline_bg(
    briefing_id: int,
    briefing_data: dict,
    strategy_questions: dict,
    report1_data: dict,
) -> None:
    """Background task: run the strategy report pipeline (same as routes/strategy.py)."""
    from core.db import SessionLocal
    from models import StrategyReport

    db = SessionLocal()
    try:
        from services.strategy_pipeline import generate_strategy_report
        await generate_strategy_report(
            briefing_id=briefing_id,
            briefing_data=briefing_data,
            strategy_questions=strategy_questions,
            report1_data=report1_data,
            report2_data={},
            db_session=db,
        )
    except Exception as exc:
        log.error("[CHAT] Strategy pipeline failed for briefing_id=%d: %s", briefing_id, exc)
        sr = db.query(StrategyReport).filter(
            StrategyReport.briefing_id == briefing_id
        ).first()
        if sr:
            sr.status = "failed"
            sr.updated_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


def _resolve_user(request: Request | None, db: Session) -> tuple[int | None, str | None]:
    """Extract user_id and email from JWT cookie/header. Non-throwing.

    Returns (user_id, email). Both may be None for unauthenticated sessions.
    """
    if not request:
        return None, None
    try:
        from core.security import verify_access_token
        token = request.cookies.get("auth_token")
        if not token:
            auth_header = request.headers.get("authorization", "")
            scheme, _, header_token = auth_header.partition(" ")
            if scheme.lower() == "bearer" and header_token:
                token = header_token
        if not token:
            return None, None
        payload = verify_access_token(token)
        email = payload.email if payload else None
        if not email:
            return None, None
        # Look up or create user (same pattern as routes/briefings.py)
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email)
            db.add(user)
            db.flush()
        return user.id, email
    except Exception:
        return None, None


def _complete_redirect(report_type: str, briefing_id: int) -> str:
    """Build the redirect URL after completion."""
    if report_type == "strategy":
        return f"/strategy.html?briefing_id={briefing_id}&status=generating"
    return f"/formular/status.html?id={briefing_id}"


def _build_session_state(
    session: ChatSession,
    collected_override: dict | None = None,
    section_override: int | None = None,
) -> ChatSessionState:
    """Build ChatSessionState from a ChatSession DB model.

    Args:
        collected_override: If provided, use this instead of session.collected_fields.
            Needed inside streaming callbacks where session attributes may be expired
            after db.commit().
        section_override: If provided, use this instead of session.current_section.
    """
    rt = session.report_type
    sections = get_sections_for_report(rt)
    registry = get_registry_for_report(rt)
    collected = collected_override if collected_override is not None else (session.collected_fields or {})
    section_idx = section_override if section_override is not None else session.current_section
    section = sections[section_idx]

    missing_req, missing_opt = get_missing_fields(collected, section_idx, rt)
    # Always 1 field at a time (Smart Grouping disabled, KIS-1122)
    next_fields = get_next_fields(collected, section_idx, max_fields=1, report_type=rt)

    total = len(registry)
    collected_count = len(collected)

    # Build per-field metadata for next_fields (optional flag, type)
    nf_meta = {}
    for nf in next_fields:
        nf_reg = registry.get(nf, {})
        nf_meta[nf] = {
            "optional": not nf_reg.get("required", False),
            "type": nf_reg.get("type", "text"),
            "chat_mode": nf_reg.get("chat_mode", "FT"),
        }

    section_name: str = section["name"]

    # Draft-Pattern state (backward-compatible: old sessions without column → {})
    draft = getattr(session, 'draft_state', None) or {}

    # Phase tracking (hybrid conversation model, KIS-1124)
    ps = _get_phase_state(session)

    # is_completable: after summary has been sent.
    # KIS-1124-HOTFIX: In the hybrid Phase 2 model, unsurveyed blocks have
    # empty fields that get defaults at /complete time. So we can't require
    # all_done when conversation_phase == "summary" — the summary phase
    # itself means the user is ready to complete.
    last_section = section_idx >= len(sections) - 1
    all_done = len(missing_req) == 0 and len(missing_opt) == 0
    summary_sent = _has_summary_been_sent(session)
    _in_summary_phase = ps["conversation_phase"] == "summary"
    # KIS-1131 FX-4: Not completable while user is editing fields.
    _editing = bool(draft.get("edit_mode"))
    completable = summary_sent and (all_done or _in_summary_phase) and not _editing

    # KIS-1124: Unsurveyed note — only in summary phase when blocks were skipped
    unsurveyed_note: str | None = None
    if ps["conversation_phase"] == "summary":
        _all_blocks = ["A", "B", "C", "D"]
        _unsurveyed = [b for b in _all_blocks if b not in ps["selected_blocks"]]
        if _unsurveyed:
            _block_labels = {
                "A": "Fördermittel & Budget",
                "B": "KI-Strategie & Roadmap",
                "C": "Tools & Automatisierung",
                "D": "Recht & Datenschutz",
            }
            _names = [_block_labels.get(b, b) for b in _unsurveyed]
            unsurveyed_note = (
                f"Nicht vertiefte Bereiche: {', '.join(_names)}. "
                "Diese werden im Report mit branchenüblichen Standardwerten ergänzt."
            )

    # KIS-1128C V7-BE: Block progress metadata
    _cur_blk = ps.get("current_block")
    _blk_label: str | None = None
    _blk_progress = 0
    _blk_total = 0
    if _cur_blk:
        _blk_label = BLOCK_LABELS.get(_cur_blk, "")
        if _cur_blk == "D":
            _blk_all = _get_datenschutz_block_fields(collected.get("branche", ""))
        else:
            _blk_all = BLOCK_FIELDS.get(_cur_blk, [])
        # KIS-1131 Fix 2: Exclude smart-skipped fields from progress count
        _skip_count = sum(1 for f in _blk_all
                         if f in collected and _smart_skip_field(f, collected) is not None)
        _blk_total = len(_blk_all) - _skip_count
        _blk_progress = len([f for f in _blk_all if f in collected]) - _skip_count

    return ChatSessionState(
        session_id=session.id,
        report_type=session.report_type,
        status=session.status,
        current_section=section_idx,
        current_section_name=section_name,
        total_sections=len(sections),
        progress_percent=calculate_progress(collected, rt),
        collected_fields=collected,
        collected_count=collected_count,
        missing_required=missing_req,
        missing_optional=missing_opt,
        total_fields=total,
        next_fields=next_fields,
        next_fields_meta=nf_meta,
        is_completable=completable,
        pending_field=draft.get("pending_field"),
        pending_value=draft.get("pending_value"),
        dialog_mode=draft.get("dialog_mode", False),
        conversation_phase=ps["conversation_phase"],
        selected_blocks=ps["selected_blocks"],
        completed_blocks=ps["completed_blocks"],
        current_block=ps["current_block"],
        unsurveyed_note=unsurveyed_note,
        block_label=_blk_label,
        block_progress=_blk_progress,
        block_total=_blk_total,
    )


def _has_summary_been_sent(session: ChatSession) -> bool:
    """Check if the summary message has already been sent in this session.

    KIS-1131 FX-1: Scans ALL assistant messages, not just the last one.
    Previously, the function broke after the first (most recent) assistant
    message, so any subsequent Sonnet reply would mask an earlier summary.
    """
    messages = session.messages or []
    for msg in messages:
        if msg.get("role") == "assistant":
            content = msg.get("content", "")
            if SUMMARY_MARKER in content:
                return True
    return False


def _parse_edit_from_message(
    message: str,
    collected: dict,
    registry: dict,
    report_type: str = "r1",
) -> tuple[str | None, object]:
    """Parse a field edit from a user message. Returns (field_name, new_value) or (None, None).

    Tries deterministic matching first:
    - Match field labels or technical names in the message
    - Extract the value from common patterns like "X soll Y sein" or "X auf Y"
    """
    from services.chat_conversation import FIELD_DESCRIPTIONS
    msg_lower = message.strip().lower()

    # Build lookup: label fragments → field_name
    label_map: dict[str, str] = {}
    for field_name in collected:
        if field_name not in registry:
            continue
        desc = FIELD_DESCRIPTIONS.get(field_name, "")
        label = desc.split("(")[0].strip().lower() if desc else ""
        if label:
            label_map[label] = field_name
        # Also map the technical name
        label_map[field_name.lower()] = field_name

    # Try to find which field the user is referring to
    matched_field = None
    for label, field_name in sorted(label_map.items(), key=lambda x: -len(x[0])):
        if label in msg_lower:
            matched_field = field_name
            break

    if not matched_field:
        return None, None

    # Try to extract the new value from common patterns
    # Patterns: "X soll Y sein", "X auf Y", "X: Y", "X = Y", "X ändern auf Y"
    import re
    patterns = [
        rf"(?:soll|auf|=|:|ändern auf|ändern zu|wird|wäre)\s+(.+)",
        rf"{re.escape(matched_field)}\s+(.+)",
    ]
    new_value = None
    for pattern in patterns:
        m = re.search(pattern, message, re.IGNORECASE)
        if m:
            new_value = m.group(1).strip().rstrip(".")
            break

    # If no pattern matched but field was found, the message might just be the value
    # e.g., user says "Bayern" after being asked what to change
    if not new_value and matched_field:
        # Check if the whole message (minus the field reference) could be a value
        remainder = msg_lower
        for label, fn in label_map.items():
            if fn == matched_field:
                remainder = remainder.replace(label, "").strip()
        if remainder and remainder != msg_lower:
            new_value = remainder.strip().rstrip(".")

    if not new_value:
        return matched_field, None

    return matched_field, new_value


# ---------------------------------------------------------------------------
# Quick Reply Builder
# ---------------------------------------------------------------------------

# Maps field → quick reply options (labels from formbuilder_de_SINGLE_FULL.js)
_QR_OPTIONS: dict[str, list[dict]] = {
    # --- Sektion 0 ---
    "branche": [
        {"value": "marketing", "label": "Marketing & Werbung"},
        {"value": "beratung", "label": "Beratung & Dienstleistungen"},
        {"value": "it", "label": "IT & Software"},
        {"value": "finanzen", "label": "Finanzen & Versicherungen"},
        {"value": "handel", "label": "Handel & E-Commerce"},
        {"value": "bildung", "label": "Bildung"},
        {"value": "verwaltung", "label": "Verwaltung"},
        {"value": "gesundheit", "label": "Gesundheit & Pflege"},
        {"value": "bau", "label": "Bauwesen & Architektur"},
        {"value": "medien", "label": "Medien & Kreativwirtschaft"},
        {"value": "industrie", "label": "Industrie & Produktion"},
        {"value": "logistik", "label": "Transport & Logistik"},
        {"value": "gastronomie", "label": "Gastronomie & Tourismus"},
    ],
    "unternehmensgroesse": [
        {"value": "1", "label": "1 (Solo/Freiberuflich)"},
        {"value": "2–10", "label": "2–10 (Kleines Team)"},
        {"value": "11–100", "label": "11–100 (KMU)"},
    ],
    "selbststaendig": [
        {"value": "freiberufler", "label": "Freiberuflich/Selbstständig"},
        {"value": "kapitalgesellschaft", "label": "1-Personen-GmbH/UG"},
        {"value": "einzelunternehmer", "label": "Einzelunternehmer (Gewerbe)"},
        {"value": "sonstiges", "label": "Sonstiges"},
    ],
    "country": [
        {"value": "DE", "label": "Deutschland"},
        {"value": "AT", "label": "Österreich"},
        {"value": "CH", "label": "Schweiz"},
        {"value": "GB", "label": "Vereinigtes Königreich"},
    ],
    "jahresumsatz": [
        {"value": "unter_100k", "label": "Bis 100.000 €"},
        {"value": "100k_500k", "label": "100.000–500.000 €"},
        {"value": "500k_2m", "label": "500.000–2 Mio. €"},
        {"value": "2m_10m", "label": "2–10 Mio. €"},
        {"value": "ueber_10m", "label": "Über 10 Mio. €"},
        {"value": "keine_angabe", "label": "Keine Angabe"},
    ],
    # --- Sektion 1 ---
    "zielgruppen": [
        {"value": "b2b", "label": "B2B (Geschäftskunden)"},
        {"value": "b2c", "label": "B2C (Endverbraucher)"},
        {"value": "kmu", "label": "KMU"},
        {"value": "grossunternehmen", "label": "Großunternehmen"},
        {"value": "selbststaendige", "label": "Selbstständige/Freiberufler"},
        {"value": "oeffentliche_hand", "label": "Öffentliche Hand"},
        {"value": "privatpersonen", "label": "Privatpersonen"},
        {"value": "startups", "label": "Startups"},
        {"value": "andere", "label": "Andere"},
    ],
    "it_infrastruktur": [
        {"value": "cloud", "label": "Cloud-basiert (z.\u00A0B. Microsoft 365)"},
        {"value": "on_premise", "label": "Eigenes Rechenzentrum"},
        {"value": "hybrid", "label": "Hybrid (Cloud + eigene Server)"},
        {"value": "unklar", "label": "Unklar / noch offen"},
    ],
    "interne_ki_kompetenzen": [
        {"value": "ja", "label": "Ja"},
        {"value": "nein", "label": "Nein"},
        {"value": "in_planung", "label": "In Planung"},
    ],
    "datenquellen": [
        {"value": "kundendaten", "label": "Kundendaten (CRM, Service)"},
        {"value": "verkaufsdaten", "label": "Verkaufs-/Bestelldaten"},
        {"value": "produktionsdaten", "label": "Produktions-/Betriebsdaten"},
        {"value": "personaldaten", "label": "Personal-/HR-Daten"},
        {"value": "marketingdaten", "label": "Marketing-/Kampagnendaten"},
        {"value": "sonstige", "label": "Sonstige Datenquellen"},
    ],
    # --- Sektion 2 ---
    # KIS-1124 Testrun 3 Bugs 16+17: Grouped scale instead of 10 individual buttons
    # Prevents Doppelfrage ("sehr hoch" → numeric re-ask) and unclear free text
    "digitalisierungsgrad": [
        {"value": "2", "label": "Niedrig (1–3)"},
        {"value": "5", "label": "Mittel (4–5)"},
        {"value": "7", "label": "Fortgeschritten (6–7)"},
        {"value": "8", "label": "Hoch (8–9)"},
        {"value": "9", "label": "Voll digital (10)"},
    ],
    "prozesse_papierlos": [
        {"value": "0-20", "label": "0–20 %"},
        {"value": "21-50", "label": "21–50 %"},
        {"value": "51-80", "label": "51–80 %"},
        {"value": "81-100", "label": "81–100 %"},
    ],
    "automatisierungsgrad": [
        {"value": "sehr_niedrig", "label": "Sehr niedrig"},
        {"value": "eher_niedrig", "label": "Eher niedrig"},
        {"value": "mittel", "label": "Mittel"},
        {"value": "eher_hoch", "label": "Eher hoch"},
        {"value": "sehr_hoch", "label": "Sehr hoch"},
    ],
    "ki_einsatz": [
        {"value": "chatbots", "label": "Chatbots / Kundenservice"},
        {"value": "marketing", "label": "Marketing & Content"},
        {"value": "vertrieb", "label": "Vertrieb & CRM"},
        {"value": "datenanalyse", "label": "Datenanalyse"},
        {"value": "produktion", "label": "Produktion / Logistik"},
        {"value": "hr", "label": "Personalmanagement"},
        {"value": "andere", "label": "Andere Bereiche"},
        {"value": "noch_keine", "label": "Noch keine Nutzung"},
    ],
    "ki_kompetenz": [
        {"value": "hoch", "label": "Hoch"},
        {"value": "mittel", "label": "Mittel"},
        {"value": "niedrig", "label": "Niedrig"},
        {"value": "keine", "label": "Keine"},
    ],
    # --- Sektion 3 ---
    "ki_ziele": [
        {"value": "effizienz", "label": "Effizienz steigern"},
        {"value": "automatisierung", "label": "Automatisierung"},
        {"value": "neue_produkte", "label": "Neue Produkte/Services"},
        {"value": "kundenservice", "label": "Kundenservice verbessern"},
        {"value": "datenauswertung", "label": "Daten besser nutzen"},
        {"value": "kosten_senken", "label": "Kosten senken"},
        {"value": "wettbewerbsfaehigkeit", "label": "Wettbewerbsfähigkeit"},
        {"value": "keine_angabe", "label": "Noch unklar"},
    ],
    "anwendungsfaelle": [
        {"value": "chatbots", "label": "Chatbots / FAQ-Automatisierung"},
        {"value": "content_generation", "label": "Content-Generierung"},
        {"value": "datenanalyse", "label": "Datenanalyse & Reporting"},
        {"value": "dokumentation", "label": "Dokumentation & Wissen"},
        {"value": "prozess_automation", "label": "Prozessautomation"},
        {"value": "personalisierung", "label": "Personalisierung"},
        {"value": "andere", "label": "Andere"},
        {"value": "keine_angabe", "label": "Noch unklar"},
    ],
    "pilot_bereich": [
        {"value": "kundenservice", "label": "Kundenservice"},
        {"value": "marketing", "label": "Marketing / Content"},
        {"value": "vertrieb", "label": "Vertrieb"},
        {"value": "verwaltung", "label": "Verwaltung / Backoffice"},
        {"value": "produktion", "label": "Produktion / Logistik"},
        {"value": "andere", "label": "Andere"},
    ],
    # --- Sektion 4 ---
    "massnahmen_komplexitaet": [
        {"value": "niedrig", "label": "Niedrig"},
        {"value": "mittel", "label": "Mittel"},
        {"value": "hoch", "label": "Hoch"},
        {"value": "unklar", "label": "Unklar"},
    ],
    "roadmap_vorhanden": [
        {"value": "ja", "label": "Ja"},
        {"value": "teilweise", "label": "Teilweise"},
        {"value": "nein", "label": "Nein"},
    ],
    "governance_richtlinien": [
        {"value": "ja", "label": "Ja"},
        {"value": "teilweise", "label": "Teilweise"},
        {"value": "nein", "label": "Nein"},
    ],
    "change_management": [
        {"value": "sehr_hoch", "label": "Sehr hoch"},
        {"value": "hoch", "label": "Hoch"},
        {"value": "mittel", "label": "Mittel"},
        {"value": "niedrig", "label": "Niedrig"},
        {"value": "sehr_niedrig", "label": "Sehr niedrig"},
    ],
    # --- Sektion 5 ---
    "zeitbudget": [
        {"value": "unter_2", "label": "Unter 2 Stunden"},
        {"value": "2_5", "label": "2–5 Stunden"},
        {"value": "5_10", "label": "5–10 Stunden"},
        {"value": "ueber_10", "label": "Über 10 Stunden"},
    ],
    "vorhandene_tools": [
        {"value": "crm", "label": "CRM (HubSpot, Salesforce)"},
        {"value": "erp", "label": "ERP (SAP, Odoo)"},
        {"value": "projektmanagement", "label": "Projektmanagement (Asana, Trello)"},
        {"value": "marketing_automation", "label": "Marketing Automation"},
        {"value": "buchhaltung", "label": "Buchhaltungssoftware"},
        {"value": "keine", "label": "Keine / andere"},
    ],
    "trainings_interessen": [
        {"value": "prompt_engineering", "label": "Prompt Engineering"},
        {"value": "llm_basics", "label": "LLM-Grundlagen"},
        {"value": "datenqualitaet_governance", "label": "Datenqualität & Governance"},
        {"value": "automatisierung", "label": "Automatisierung & Skripte"},
        {"value": "ethik_recht", "label": "Ethische & rechtliche Grundlagen"},
        {"value": "keine", "label": "Keine / noch unklar"},
    ],
    "vision_prioritaet": [
        {"value": "gpt_services", "label": "KI-gestützte Services und Produkte"},
        {"value": "kundenservice", "label": "Optimierung Kundenservice"},
        {"value": "datenprodukte", "label": "Datenbasierte Angebote"},
        {"value": "prozessautomation", "label": "Automatisierung interner Prozesse"},
        {"value": "marktfuehrerschaft", "label": "Technologieführerschaft"},
        {"value": "keine_angabe", "label": "Noch unklar"},
    ],
    "innovationsprozess": [
        {"value": "innovationsteam", "label": "Innovationsteam"},
        {"value": "mitarbeitende", "label": "Durch Mitarbeitende"},
        {"value": "kunden", "label": "Mit Kunden"},
        {"value": "berater", "label": "Externe Berater"},
        {"value": "zufall", "label": "Zufällig"},
        {"value": "unbekannt", "label": "Keine klare Strategie"},
    ],
    "regulierte_branche": [
        {"value": "gesundheit", "label": "Gesundheit & Medizin"},
        {"value": "finanzen", "label": "Finanzen & Versicherungen"},
        {"value": "oeffentlich", "label": "Öffentlicher Sektor"},
        {"value": "recht", "label": "Rechtliche Dienstleistungen"},
        {"value": "vertraulich_nda", "label": "Vertrauliche Kundendaten / NDA"},
        {"value": "keine", "label": "Keine dieser Branchen"},
    ],
    # --- Sektion 6 ---
    "datenschutzbeauftragter": [
        {"value": "ja", "label": "Ja"},
        {"value": "nein", "label": "Nein"},
        {"value": "teilweise", "label": "Teilweise (extern/Planung)"},
    ],
    "technische_massnahmen": [
        {"value": "alle", "label": "Alle relevanten Maßnahmen"},
        {"value": "teilweise", "label": "Teilweise vorhanden"},
        {"value": "keine", "label": "Noch keine"},
    ],
    "folgenabschaetzung": [
        {"value": "ja", "label": "Ja, durchgeführt"},
        {"value": "nein", "label": "Nein, noch nicht"},
        {"value": "teilweise", "label": "In Planung"},
    ],
    "meldewege": [
        {"value": "ja", "label": "Ja, klar definiert"},
        {"value": "teilweise", "label": "Teilweise vorhanden"},
        {"value": "nein", "label": "Nein, noch nicht geregelt"},
    ],
    "loeschregeln": [
        {"value": "ja", "label": "Ja, dokumentiert"},
        {"value": "teilweise", "label": "Teilweise vorhanden"},
        {"value": "nein", "label": "Nein, noch nicht definiert"},
    ],
    "ai_act_kenntnis": [
        {"value": "sehr_gut", "label": "Sehr gut"},
        {"value": "gut", "label": "Gut"},
        {"value": "gehoert", "label": "Schon mal gehört"},
        {"value": "unbekannt", "label": "Noch nicht bekannt"},
    ],
    "ki_hemmnisse": [
        {"value": "rechtsunsicherheit", "label": "Rechtsunsicherheit"},
        {"value": "datenschutz", "label": "Datenschutz"},
        {"value": "knowhow", "label": "Fehlendes Know-how"},
        {"value": "budget", "label": "Begrenztes Budget"},
        {"value": "teamakzeptanz", "label": "Teamakzeptanz"},
        {"value": "zeitmangel", "label": "Zeitmangel"},
        {"value": "it_integration", "label": "IT-Integration"},
        {"value": "keine", "label": "Keine Hemmnisse"},
        {"value": "andere", "label": "Andere"},
    ],
    # --- Sektion 7 ---
    "bisherige_foerdermittel": [
        {"value": "ja", "label": "Ja"},
        {"value": "nein", "label": "Nein"},
    ],
    "interesse_foerderung": [
        {"value": "ja", "label": "Ja, Programme vorschlagen"},
        {"value": "nein", "label": "Kein Bedarf"},
        {"value": "unklar", "label": "Unklar, bitte beraten"},
    ],
    "erfahrung_beratung": [
        {"value": "ja", "label": "Ja"},
        {"value": "nein", "label": "Nein"},
        {"value": "unklar", "label": "Unklar"},
    ],
    "investitionsbudget": [
        {"value": "unter_2000", "label": "Unter 2.000 €"},
        {"value": "2000_10000", "label": "2.000–10.000 €"},
        {"value": "10000_50000", "label": "10.000–50.000 €"},
        {"value": "ueber_50000", "label": "Über 50.000 €"},
        {"value": "unklar", "label": "Noch unklar"},
    ],
    "marktposition": [
        {"value": "marktfuehrer", "label": "Marktführer"},
        {"value": "oberes_drittel", "label": "Oberes Drittel"},
        {"value": "mittelfeld", "label": "Mittelfeld"},
        {"value": "nachzuegler", "label": "Nachzügler"},
        {"value": "unsicher", "label": "Schwer einzuschätzen"},
    ],
    "benchmark_wettbewerb": [
        {"value": "ja", "label": "Ja, regelmäßig"},
        {"value": "nein", "label": "Nein"},
        {"value": "selten", "label": "Selten"},
    ],
    "risikofreude": [
        {"value": "1", "label": "1 (sehr vorsichtig)"},
        {"value": "2", "label": "2"},
        {"value": "3", "label": "3 (ausgewogen)"},
        {"value": "4", "label": "4"},
        {"value": "5", "label": "5 (experimentierfreudig)"},
    ],
    # --- Strategy Fields ---
    "s1_budget": [
        {"value": "unter_2000", "label": "Unter 2.000 €"},
        {"value": "2000_10000", "label": "2.000 – 10.000 €"},
        {"value": "10000_50000", "label": "10.000 – 50.000 €"},
        {"value": "ueber_50000", "label": "Über 50.000 €"},
        {"value": "unklar", "label": "Noch unklar"},
    ],
    "s2_zeitrahmen": [
        {"value": "Sofort (1-3 Monate)", "label": "Sofort (1–3 Monate)"},
        {"value": "Kurzfristig (3-6 Monate)", "label": "Kurzfristig (3–6 Monate)"},
        {"value": "Mittelfristig (6-12 Monate)", "label": "Mittelfristig (6–12 Monate)"},
        {"value": "Langfristig (12-18 Monate)", "label": "Langfristig (12–18 Monate)"},
    ],
    "s3_prioritaeten": [
        {"value": "Kosten senken", "label": "Kosten senken"},
        {"value": "Umsatz steigern", "label": "Umsatz steigern"},
        {"value": "Qualität verbessern", "label": "Qualität verbessern"},
        {"value": "Geschwindigkeit erhöhen", "label": "Geschwindigkeit erhöhen"},
        {"value": "Compliance sichern", "label": "Compliance sichern"},
        {"value": "Neue Geschäftsfelder", "label": "Neue Geschäftsfelder"},
        {"value": "Fachkräftemangel kompensieren", "label": "Fachkräftemangel kompensieren"},
        {"value": "Kundenerlebnis verbessern", "label": "Kundenerlebnis verbessern"},
    ],
    "s4_engpass": [
        {"value": "Zu wenig Know-how", "label": "Zu wenig Know-how"},
        {"value": "Kein Budget", "label": "Kein Budget"},
        {"value": "Fehlende Daten", "label": "Fehlende Daten"},
        {"value": "Widerstand im Team", "label": "Widerstand im Team"},
        {"value": "Regulatorische Unsicherheit", "label": "Regulatorische Unsicherheit"},
        {"value": "Kein klarer Use Case", "label": "Kein klarer Use Case"},
        {"value": "Andere", "label": "Andere"},
    ],
    "s5_software": [
        {"value": "Microsoft 365", "label": "Microsoft 365"},
        {"value": "Google Workspace", "label": "Google Workspace"},
        {"value": "Notion", "label": "Notion"},
        {"value": "Asana / Monday / Trello", "label": "Asana / Monday / Trello"},
        {"value": "Slack", "label": "Slack"},
        {"value": "Jira / Confluence", "label": "Jira / Confluence"},
        {"value": "ChatGPT / OpenAI", "label": "ChatGPT / OpenAI"},
        {"value": "Claude / Anthropic", "label": "Claude / Anthropic"},
        {"value": "Perplexity", "label": "Perplexity"},
        {"value": "Microsoft Copilot", "label": "Microsoft Copilot"},
        {"value": "GitHub / GitLab", "label": "GitHub / GitLab"},
        {"value": "AWS / Azure / Google Cloud", "label": "AWS / Azure / GCP"},
        {"value": "Salesforce / HubSpot", "label": "Salesforce / HubSpot"},
        {"value": "Mailchimp / Brevo", "label": "Mailchimp / Brevo"},
    ],
    "s6_foerderinteresse": [
        {"value": "Ja, dringend", "label": "Ja, dringend"},
        {"value": "Ja, wenn passend", "label": "Ja, wenn passend"},
        {"value": "Nein, eigenes Budget", "label": "Nein, eigenes Budget"},
        {"value": "Weiß nicht", "label": "Weiß nicht"},
    ],
    "s7_entscheidung": [
        {"value": "Entscheide allein", "label": "Entscheide allein"},
        {"value": "Brauche Vorlage für Geschäftsleitung", "label": "Vorlage für Geschäftsleitung"},
        {"value": "Muss Gesellschafter überzeugen", "label": "Gesellschafter überzeugen"},
        {"value": "Muss Aufsichtsrat/Beirat informieren", "label": "Aufsichtsrat/Beirat informieren"},
    ],
    "s8_erfahrung": [
        {"value": "Noch keine", "label": "Noch keine"},
        {"value": "Experimentiert", "label": "Experimentiert"},
        {"value": "Erste Tools im Einsatz", "label": "Erste Tools im Einsatz"},
        {"value": "Fortgeschritten", "label": "Fortgeschritten"},
    ],
    "s9_ansatz": [
        {"value": "Cloud-SaaS", "label": "Cloud-SaaS"},
        {"value": "On-Premise", "label": "On-Premise"},
        {"value": "Hybrid", "label": "Hybrid"},
        {"value": "Egal", "label": "Noch unklar / Egal"},
    ],
    "s10_datenschutz": [
        {"value": "Hoch", "label": "Hoch"},
        {"value": "Mittel", "label": "Mittel"},
        {"value": "Niedrig", "label": "Niedrig"},
    ],
    "wettbewerber_anzahl": [
        {"value": "wenige", "label": "Wenige (1–3)"},
        {"value": "mehrere", "label": "Mehrere (4–10)"},
        {"value": "viele", "label": "Viele (mehr als 10)"},
        {"value": "unklar", "label": "Schwer einzuschätzen"},
    ],
    "kundenbindung_typ": [
        {"value": "einmalig", "label": "Überwiegend Einmalkunden"},
        {"value": "wiederkehrend", "label": "Wiederkehrende Kunden / Verträge"},
        {"value": "gemischt", "label": "Mischung aus beidem"},
    ],
    "datenreife": [
        {"value": "keine", "label": "Kaum / keine strukturierten Daten"},
        {"value": "basis", "label": "Grundlegende Daten (CRM, Buchhaltung)"},
        {"value": "umfangreich", "label": "Umfangreiche eigene Datenbestände"},
        {"value": "unklar", "label": "Bin mir nicht sicher"},
    ],
}

# Field labels for quick replies
_QR_LABELS: dict[str, str] = {
    # Sektion 0
    "branche": "Branche", "unternehmensgroesse": "Unternehmensgröße",
    "selbststaendig": "Unternehmensform", "country": "Land",
    "bundesland": "Bundesland / Region", "hauptleistung": "Hauptleistung",
    "jahresumsatz": "Jahresumsatz",
    # Sektion 1
    "zielgruppen": "Zielgruppen", "it_infrastruktur": "IT-Infrastruktur",
    "interne_ki_kompetenzen": "Internes KI-Team", "datenquellen": "Verfügbare Daten",
    # Sektion 2
    "digitalisierungsgrad": "Digitalisierungsgrad (1–10)",
    "prozesse_papierlos": "Papierlose Prozesse", "automatisierungsgrad": "Automatisierungsgrad",
    "ki_einsatz": "Aktueller KI-Einsatz", "ki_kompetenz": "KI-Kompetenz",
    # Sektion 3
    "ki_ziele": "KI-Ziele", "anwendungsfaelle": "Anwendungsfälle",
    "ki_projekte": "Bestehende KI-Projekte", "pilot_bereich": "Pilotbereich",
    "zeitersparnis_prioritaet": "Zeitfresser", "geschaeftsmodell_evolution": "Geschäftsmodell-Ideen",
    "vision_3_jahre": "3-Jahres-Vision",
    # Sektion 4
    "strategische_ziele": "Strategische Ziele", "ki_guardrails": "KI-Leitplanken",
    "massnahmen_komplexitaet": "Einführungsaufwand", "roadmap_vorhanden": "KI-Roadmap",
    "governance_richtlinien": "Governance-Richtlinien", "change_management": "Veränderungsbereitschaft",
    # Sektion 5
    "zeitbudget": "Zeitbudget pro Woche", "vorhandene_tools": "Genutzte Systeme",
    "trainings_interessen": "Trainingsthemen", "vision_prioritaet": "Strategischer Hebel",
    "innovationsprozess": "Innovationsprozess", "regulierte_branche": "Regulierte Branche",
    # Sektion 6
    "datenschutzbeauftragter": "Datenschutzbeauftragter", "technische_massnahmen": "Schutzmaßnahmen",
    "folgenabschaetzung": "Datenschutz-Folgenabschätzung", "meldewege": "Meldewege",
    "loeschregeln": "Löschrichtlinien", "ai_act_kenntnis": "EU AI Act Kenntnis",
    "ki_hemmnisse": "KI-Hemmnisse",
    # Sektion 7
    "bisherige_foerdermittel": "Bisherige Fördermittel", "interesse_foerderung": "Förderinteresse",
    "erfahrung_beratung": "Beratungserfahrung", "investitionsbudget": "Investitionsbudget",
    "marktposition": "Marktposition", "benchmark_wettbewerb": "Wettbewerber-Vergleich",
    "risikofreude": "Risikofreude (1–5)",
    # Strategy
    "s1_budget": "KI-Implementierungsbudget", "s2_zeitrahmen": "Umsetzungszeitraum",
    "s3_prioritaeten": "Top-Prioritäten (max. 3)", "s4_engpass": "Größter Engpass",
    "s5_software": "Genutzte Software", "s5_vision": "KI-Vision",
    "s6_foerderinteresse": "Förderinteresse", "s7_entscheidung": "Entscheidungsstruktur",
    "s8_erfahrung": "KI-Erfahrung", "s9_ansatz": "Infrastruktur-Ansatz",
    "s10_datenschutz": "Datenschutz-Priorität",
    "wettbewerber_anzahl": "Wettbewerber", "kundenbindung_typ": "Kundenbeziehungen",
    "datenreife": "Datenreife",
}


# ---------------------------------------------------------------------------
# Freetext field suggestions (branche-specific + profile-aware)
# Fix 2: All 13 branches covered for zeitersparnis_prioritaet
# ---------------------------------------------------------------------------

FREETEXT_SUGGESTIONS: dict[str, dict[str, list[str]]] = {
    "zeitersparnis_prioritaet": {
        "beratung": ["Angebotserstellung", "Kundendokumentation", "Recherche", "Administration"],
        "it": ["Bug-Tracking", "Dokumentation", "Meetings", "Deployment"],
        "bau": ["Aufmaß & Kalkulation", "Baustellendokumentation", "Behördenkommunikation"],
        "handel": ["Bestellabwicklung", "Inventur", "Kundenkommunikation"],
        "marketing": ["Content-Erstellung", "Reporting", "Kampagnenplanung", "Kundenbriefings"],
        "finanzen": ["Compliance-Prüfung", "Reporting", "Kundenkommunikation"],
        "gesundheit": ["Dokumentation", "Terminverwaltung", "Abrechnung"],
        "gastronomie": ["Bestellmanagement", "Personalplanung", "Buchhaltung"],
        "bildung": ["Unterrichtsvorbereitung", "Teilnehmerverwaltung", "Zertifikatserstellung", "Evaluationen"],
        "verwaltung": ["Antragsbearbeitung", "Berichtswesen", "Bürgerkommunikation", "Dokumentation"],
        "medien": ["Briefings & Konzepte", "Rechtemanagement", "Postproduktion", "Projektkoordination"],
        "industrie": ["Qualitätsdokumentation", "Wartungsplanung", "Lieferanten-Kommunikation", "Reporting"],
        "logistik": ["Tourenplanung", "Sendungsverfolgung", "Zolldokumentation", "Kundenkommunikation"],
        "default": ["E-Mails & Kommunikation", "Dokumentation", "Recherche", "Administration"],
    },
    "ki_projekte": {
        "default": ["ChatGPT im Team genutzt", "Automatisierungs-Tests", "Noch keine Projekte"],
    },
}

# Expert-override: when is_expert=True, use these instead
_EXPERT_FREETEXT_SUGGESTIONS: dict[str, list[str]] = {
    "ki_projekte": ["API-Integration (OpenAI, Anthropic, etc.)", "Eigene KI-Workflows", "RAG / Retrieval-Systeme"],
}

# Solo-override: when is_solo=True, use these instead
_SOLO_FREETEXT_SUGGESTIONS: dict[str, list[str]] = {
    "ki_projekte": ["KI-Tools im Einsatz", "Automatisierungs-Tests", "Noch keine Projekte"],
}


# ---------------------------------------------------------------------------
# Profile-aware QR label overrides
# ---------------------------------------------------------------------------

# Solo: replace team-centric labels
_SOLO_QR_LABELS: dict[str, str] = {
    "ki_kompetenz": "KI-Kompetenz",
    "change_management": "Veränderungsbereitschaft",
    "interne_ki_kompetenzen": "KI-/Digitalisierungskompetenz",
    "innovationsprozess": "Innovationsansatz",
}

# Small team (2–10): slightly adapted labels
_SMALL_TEAM_QR_LABELS: dict[str, str] = {
    "innovationsprozess": "Innovationsansatz",
}

# Expert: replace beginner-centric labels
_EXPERT_QR_LABELS: dict[str, str] = {
    "pilot_bereich": "KI-Ausbau-Potenzial",
    "ki_projekte": "Aktive KI-Projekte",
}

# Intermediate (1 expert signal): softer expert labels
_INTERMEDIATE_QR_LABELS: dict[str, str] = {
    "pilot_bereich": "Nächstes KI-Projekt",
}


# ---------------------------------------------------------------------------
# Profile-aware QR option filters
# ---------------------------------------------------------------------------

# Fix 1: change_management removed — all options stay, only label adapted
# Solo: QR option values to REMOVE per field
_SOLO_QR_REMOVE: dict[str, set[str]] = {
    "innovationsprozess": {"innovationsteam", "mitarbeitende"},
    "ki_hemmnisse": {"teamakzeptanz"},
}

# KIS-1124 Testrun 3 Bug 15: Solo-specific option REPLACEMENTS
# (completely overrides _QR_OPTIONS for these fields when is_solo=True)
_SOLO_QR_OVERRIDE: dict[str, list[dict]] = {
    "interne_ki_kompetenzen": [
        {"value": "ja", "label": "Ja, mit externen Partnern"},
        {"value": "nein", "label": "Nein, alles selbst"},
        {"value": "in_planung", "label": "Geplant"},
    ],
}

# Fix 3: Small team (2–10): remove enterprise-only options
_SMALL_TEAM_QR_REMOVE: dict[str, set[str]] = {
    "innovationsprozess": {"innovationsteam"},
    "s7_entscheidung": {"Muss Aufsichtsrat/Beirat informieren"},
}

# Expert: QR option values to REMOVE per field
_EXPERT_QR_REMOVE: dict[str, set[str]] = {
    "ki_einsatz": {"noch_keine"},
    "ki_kompetenz": {"keine"},
    "anwendungsfaelle": {"keine_angabe"},
    "ki_ziele": {"keine_angabe"},
}

# Intermediate: lighter expert filter (only remove most obvious)
_INTERMEDIATE_QR_REMOVE: dict[str, set[str]] = {
    "ki_einsatz": {"noch_keine"},
}


def _build_quick_replies(
    next_fields: list[str],
    report_type: str = "r1",
    collected_fields: dict | None = None,
    profile_context: dict | None = None,
) -> list[QuickReply]:
    """Build quick reply buttons for enum fields and freetext suggestions.

    Profile-aware: adapts labels and filters options based on
    Solo/Team/Expert/Intermediate detection from collected_fields.

    Args:
        profile_context: Optional pre-computed profile dict. Used by
            Strategy sessions to pass R1-derived profile data that
            isn't in the Strategy collected_fields.
    """
    registry = get_registry_for_report(report_type)
    collected = collected_fields or {}
    profile = profile_context or compute_user_profile(collected)
    replies = []

    for field_name in next_fields:
        if field_name in collected:
            continue  # Already collected — no buttons

        reg = registry.get(field_name, {})

        # Freetext suggestions (for selected text fields)
        if reg.get("type") == "text" and field_name in FREETEXT_SUGGESTIONS:
            suggestions = _get_freetext_suggestions(field_name, collected, profile)
            if suggestions:
                options = [QuickReplyOption(value=s, label=s) for s in suggestions]
                label = _get_context_label(field_name, profile)
                is_optional = not reg.get("required", False)
                replies.append(QuickReply(
                    field=field_name, label=f"{label} (Vorschläge)", options=options,
                    optional=is_optional,
                ))
            continue

        # Only build QR for enum/multi fields with known options
        if reg.get("chat_mode") not in ("QR", "qr"):
            continue

        # Solo QR overrides (Bug 15: interne_ki_kompetenzen for solo)
        if profile.get("is_solo") and field_name in _SOLO_QR_OVERRIDE:
            options_data = _SOLO_QR_OVERRIDE[field_name]
        # Dynamic bundesland options based on collected country
        elif field_name == "bundesland":
            options_data = _build_bundesland_options(collected.get("country", "DE"))
        else:
            options_data = _QR_OPTIONS.get(field_name)

        if not options_data:
            continue

        # Profile-aware option filtering
        options_data = _filter_options_by_profile(field_name, options_data, profile)

        options = [
            QuickReplyOption(value=o["value"], label=o["label"], description=o.get("description"))
            for o in options_data
        ]
        label = _get_context_label(field_name, profile)
        is_multi = reg.get("type") == "multi"
        max_sel = reg.get("max_select") if is_multi else None
        is_optional = not reg.get("required", False)
        replies.append(QuickReply(
            field=field_name, label=label, options=options,
            multi_select=is_multi, max_select=max_sel,
            optional=is_optional,
        ))

    return replies


def _get_context_label(field_name: str, profile: dict) -> str:
    """Get profile-aware QR label. Priority: expert > intermediate > solo > small_team > default."""
    if profile.get("is_expert"):
        label = _EXPERT_QR_LABELS.get(field_name)
        if label:
            return label
    if profile.get("is_intermediate"):
        label = _INTERMEDIATE_QR_LABELS.get(field_name)
        if label:
            return label
    if profile.get("is_solo"):
        label = _SOLO_QR_LABELS.get(field_name)
        if label:
            return label
    if profile.get("is_small_team"):
        label = _SMALL_TEAM_QR_LABELS.get(field_name)
        if label:
            return label
    return _QR_LABELS.get(field_name, field_name)


def _filter_options_by_profile(
    field_name: str, options: list[dict], profile: dict,
) -> list[dict]:
    """Remove QR options that are irrelevant for the user's profile."""
    remove_values: set[str] = set()
    # Size-based filters
    if profile.get("is_solo"):
        remove_values |= _SOLO_QR_REMOVE.get(field_name, set())
    if profile.get("is_small_team"):
        remove_values |= _SMALL_TEAM_QR_REMOVE.get(field_name, set())
    # Expertise-based filters
    if profile.get("is_expert"):
        remove_values |= _EXPERT_QR_REMOVE.get(field_name, set())
    elif profile.get("is_intermediate"):
        remove_values |= _INTERMEDIATE_QR_REMOVE.get(field_name, set())
    if not remove_values:
        return options
    filtered = [o for o in options if o["value"] not in remove_values]
    # Safety: never return empty list — keep at least original
    return filtered if filtered else options


def _get_freetext_suggestions(
    field_name: str, collected: dict, profile: dict | None = None,
) -> list[str]:
    """Get branche-specific + profile-aware suggestions for a freetext field."""
    # Expert override takes priority
    if profile and profile.get("is_expert"):
        expert = _EXPERT_FREETEXT_SUGGESTIONS.get(field_name)
        if expert:
            return expert
    # Solo override
    if profile and profile.get("is_solo"):
        solo = _SOLO_FREETEXT_SUGGESTIONS.get(field_name)
        if solo:
            return solo
    # Default: branche-specific
    suggestions_map = FREETEXT_SUGGESTIONS.get(field_name, {})
    if not suggestions_map:
        return []
    branche = collected.get("branche", "default")
    return suggestions_map.get(branche, suggestions_map.get("default", []))


# ---------------------------------------------------------------------------
# Fix 4: R1 profile loading for Strategy sessions
# ---------------------------------------------------------------------------

def _load_r1_profile_for_strategy(session, db) -> dict | None:
    """Load R1 collected_fields via briefing to compute user profile for Strategy.

    Strategy sessions only have strategy fields in collected_fields.
    To enable profile-aware QR filtering, we need the R1 data
    (hauptleistung, ki_einsatz, ki_kompetenz, digitalisierungsgrad, etc.)

    Returns a pre-computed profile dict, or None if R1 data unavailable.
    """
    if not getattr(session, "briefing_id", None):
        return None
    try:
        briefing = db.query(Briefing).filter(Briefing.id == session.briefing_id).first()
        if not briefing:
            return None
        # Briefing.answers contains the R1 form data
        r1_data = getattr(briefing, "answers", None) or {}
        if not r1_data or not isinstance(r1_data, dict):
            return None
        return compute_user_profile(r1_data)
    except Exception as exc:
        log.warning("[CHAT] Could not load R1 profile for strategy: %s", exc)
        return None


def _build_bundesland_options(country: str) -> list[dict]:
    """Build bundesland/region QR options for the given country."""
    codes = BUNDESLAND_VALUES.get(country, BUNDESLAND_VALUES.get("DE", []))
    return [{"value": code, "label": BUNDESLAND_LABELS.get(code, code)} for code in codes]
