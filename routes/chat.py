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

router = APIRouter(prefix="/chat", tags=["chat"])
log = logging.getLogger(__name__)

# Feature flag: Draft-Pattern (Sprint 1 infra — default off)
DRAFT_MODE_ENABLED = os.getenv("DRAFT_MODE_ENABLED", "false").lower() == "true"

R1_WELCOME = (
    "Willkommen bei ki-sicherheit.jetzt! Ich bin ein KI-Assistent und "
    "führe Sie durch eine kurze Bestandsaufnahme Ihres Unternehmens.\n\n"
    "Lassen Sie uns mit den Grundlagen beginnen: "
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
    from services.chat_conversation import generate_response, FIELD_DESCRIPTIONS

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
            _sa_text("SELECT collected_fields, field_meta, current_section, draft_state "
                     "FROM chat_sessions WHERE id = :sid"),
            {"sid": str(session.id)}
        ).fetchone()
        collected = dict(_row[0] or {})
        field_meta = dict(_row[1] or {})
        _current_section = _row[2]
        _draft_state_snapshot = dict(_row[3] or {})
        log.info("[CHAT] Turn %d init: collected_keys=%s", turn, list(collected.keys()))

        # Draft-mode tracking variables (only meaningful when DRAFT_MODE_ENABLED)
        _signal = None
        _draft_new_field = None
        _draft_new_value = None
        _draft_confirmed_field = None
        _draft_confirmed_value = None
        _pending_after_turn = False  # True when a pending draft exists AFTER this turn's processing

        _is_qr_click = bool(req.quick_reply_field and req.quick_reply_value)

        if _is_qr_click:
            # Quick reply: direct write, no Draft — user click is explicit confirmation.
            # This applies to both QR (single-select) and MS (multi-select) fields,
            # regardless of DRAFT_MODE_ENABLED. Only free-text goes through Draft.
            qr_field = req.quick_reply_field

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
            if qr_field != "_draft_action":
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

            missing_req, missing_opt = get_missing_fields(collected, _current_section, rt)
            _all_missing = missing_req + missing_opt
            asked_fields = get_next_fields(collected, _current_section, report_type=rt)
            cur_field = asked_fields[0] if asked_fields else ""
            cur_desc = FIELD_DESCRIPTIONS.get(cur_field, "")

            # Draft-mode: read pending state for extractor context
            _draft = dict(_draft_state_snapshot)
            _pf = _draft.get("pending_field") if DRAFT_MODE_ENABLED else None
            _pv = _draft.get("pending_value") if DRAFT_MODE_ENABLED else None

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
                        timeout=30,
                    )
                except asyncio.TimeoutError:
                    log.warning("[CHAT] Extraction timeout, retrying once...")
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
                            timeout=30,
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

        # Handle "weiter" / skip for optional fields
        skip_words = {"weiter", "skip", "überspringen", "nächste", "weiter bitte", "nächste frage"}
        _skip_confirmed_draft = False
        if req.message.strip().lower() in skip_words and not normalized:
            # In draft mode with pending: "weiter" confirms the pending value
            # but does NOT also skip the next field (confirm only).
            if DRAFT_MODE_ENABLED:
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
                    if not skip_reg.get("required"):
                        collected[skip_field] = "" if skip_reg.get("type") == "text" else None
                        field_meta[skip_field] = {
                            "confidence": "high", "source_turn": turn,
                            "raw_input": "skipped", "normalized": True, "confirmed": True,
                        }
                        log.info("[CHAT] User skipped optional field: %s", skip_field)

        # Evaluate conditionals: remove hidden fields BEFORE writing
        for cond_field in ["selbststaendig", "bundesland"]:
            if cond_field in collected and not is_field_visible(cond_field, collected):
                del collected[cond_field]
                if cond_field in field_meta:
                    del field_meta[cond_field]

        # Raw SQL write — direct SET, no ORM involvement.
        # `collected` was read fresh at turn start and contains the full
        # desired state (previous fields + this turn's additions/deletions).
        db.execute(
            _sa_text("""
                UPDATE chat_sessions
                SET collected_fields = CAST(:cf AS jsonb),
                    field_meta = CAST(:fm AS jsonb),
                    updated_at = :ts
                WHERE id = :sid
            """),
            {
                "sid": str(session.id),
                "cf": json.dumps(collected),
                "fm": json.dumps(field_meta),
                "ts": now,
            }
        )
        db.commit()

        # Check section transition (raw SQL inside, commits internally)
        section_advanced = _check_section_transition(session, collected, db, rt)
        if section_advanced:
            _current_section = session.current_section

        # Determine next fields
        sections = get_sections_for_report(rt)
        missing_req, missing_opt = get_missing_fields(collected, _current_section, rt)
        all_missing = missing_req + missing_opt
        next_fields = get_next_fields(collected, _current_section, report_type=rt)
        current_section = sections[_current_section]

        log.info("[CHAT] Turn %d: normalized=%s, next=%s", turn, list(normalized.keys()), next_fields)

        # ------------------------------------------------------------------
        # Phase 2: Stream Sonnet response with heartbeat keepalive
        # ------------------------------------------------------------------
        _SENTINEL = object()
        queue: asyncio.Queue = asyncio.Queue()

        # Draft context for Sonnet
        _ds = dict(_draft_state_snapshot)

        async def _token_producer():
            try:
                async for token in generate_response(
                    session_messages=list(session.messages),
                    collected_fields=collected,
                    missing_fields=all_missing,
                    next_fields=next_fields,
                    section=current_section,
                    report_type=rt,
                    draft_mode=DRAFT_MODE_ENABLED,
                    pending_field=_ds.get("pending_field"),
                    pending_value=_ds.get("pending_value"),
                    dialog_mode=_ds.get("dialog_mode", False),
                ):
                    await queue.put(token)
            except Exception as exc:
                await queue.put(exc)
            finally:
                await queue.put(_SENTINEL)

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

        # QR generation — QR clicks always get normal next-field buttons.
        # Draft suppression only applies to free-text turns.
        qr_next = get_next_fields(collected, _current_section, report_type=rt)

        # Fix 4: For strategy sessions, load R1 profile for context-aware QR
        _profile_ctx = None
        if rt == "strategy":
            _profile_ctx = _load_r1_profile_for_strategy(session, db)

        if _is_qr_click:
            # QR clicks are explicit user actions — never show confirm/edit
            # buttons. Draft was already handled in the QR housekeeping step.
            quick_replies = _build_quick_replies(qr_next, rt, collected, _profile_ctx)
        elif DRAFT_MODE_ENABLED and _pending_after_turn:
            # Free-text turn with pending draft value → show confirm/edit
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
            # Dialog mode → no QR buttons
            quick_replies = []
        else:
            quick_replies = _build_quick_replies(qr_next, rt, collected, _profile_ctx)

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
        last_section = _current_section >= len(sections) - 1
        all_fields_done = len(qr_next) == 0 and last_section
        if all_fields_done and not _has_summary_been_sent(session):
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

        state = _build_session_state(session, collected_override=collected, section_override=_current_section)
        state.quick_replies = quick_replies
        # Draft fields only included when DRAFT_MODE_ENABLED — otherwise identical to pre-draft output
        _draft_exclude = None if DRAFT_MODE_ENABLED else {"pending_field", "pending_value", "dialog_mode"}
        yield f"event: state_update\ndata: {state.model_dump_json(exclude=_draft_exclude)}\n\n"

        if quick_replies:
            qr_data = [qr.model_dump() for qr in quick_replies]
            yield f"event: quick_replies\ndata: {json.dumps(qr_data)}\n\n"

        yield f"event: done\ndata: {json.dumps({'turn': turn})}\n\n"

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
    next_fields = get_next_fields(session.collected_fields, session.current_section, report_type=rt)
    _profile_ctx = _load_r1_profile_for_strategy(session, db) if rt == "strategy" else None
    state.quick_replies = _build_quick_replies(next_fields, rt, session.collected_fields, _profile_ctx)

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
    if session.status != "active":
        raise HTTPException(status_code=400, detail="Session ist nicht aktiv")
    if not req.confirmed:
        raise HTTPException(status_code=400, detail="Bestätigung erforderlich")

    rt = session.report_type
    sections = get_sections_for_report(rt)

    # Idempotency: if already completed, return existing briefing_id
    if session.status == "completed" and session.briefing_id:
        redirect = _complete_redirect(rt, session.briefing_id)
        return ChatCompleteResponse(
            success=True,
            briefing_id=session.briefing_id,
            report_type=rt,
            redirect_url=redirect,
        )

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
    next_fields = get_next_fields(collected, section_idx, report_type=rt)

    total = len(registry)
    collected_count = len(collected)

    section_name: str = section["name"]

    # is_completable: only after last section and summary has been sent
    last_section = section_idx >= len(sections) - 1
    all_done = len(missing_req) == 0 and len(missing_opt) == 0
    summary_sent = _has_summary_been_sent(session)
    completable = last_section and all_done and summary_sent

    # Draft-Pattern state (backward-compatible: old sessions without column → {})
    draft = getattr(session, 'draft_state', None) or {}

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
        is_completable=completable,
        pending_field=draft.get("pending_field"),
        pending_value=draft.get("pending_value"),
        dialog_mode=draft.get("dialog_mode", False),
    )


def _has_summary_been_sent(session: ChatSession) -> bool:
    """Check if the summary message has already been sent in this session."""
    messages = session.messages or []
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            content = msg.get("content", "")
            if "Zusammenfassung" in content and ("korrekt?" in content or "korrekt" in content):
                return True
            break  # Only check the last assistant message
    return False


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
    "digitalisierungsgrad": [
        {"value": "1", "label": "1 (kaum digital)"},
        {"value": "2", "label": "2"},
        {"value": "3", "label": "3"},
        {"value": "4", "label": "4"},
        {"value": "5", "label": "5 (halb-halb)"},
        {"value": "6", "label": "6"},
        {"value": "7", "label": "7"},
        {"value": "8", "label": "8"},
        {"value": "9", "label": "9"},
        {"value": "10", "label": "10 (voll digital)"},
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
                replies.append(QuickReply(
                    field=field_name, label=f"{label} (Vorschläge)", options=options,
                ))
            continue

        # Only build QR for enum/multi fields with known options
        if reg.get("chat_mode") not in ("QR", "qr"):
            continue

        # Dynamic bundesland options based on collected country
        if field_name == "bundesland":
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
        replies.append(QuickReply(
            field=field_name, label=label, options=options,
            multi_select=is_multi, max_select=max_sel,
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
        # Briefing.questionnaire contains the R1 form data
        r1_data = getattr(briefing, "questionnaire", None) or {}
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
