# -*- coding: utf-8 -*-
"""Pydantic schemas for the conversational AI questionnaire (Chat)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Chat Message
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime
    turn: int
    fields_extracted: Optional[dict] = None
    section_index: Optional[int] = None
    quick_replies: Optional[list] = None


# ---------------------------------------------------------------------------
# Quick Replies
# ---------------------------------------------------------------------------

class QuickReplyOption(BaseModel):
    value: str
    label: str
    description: Optional[str] = None
    style: Optional[str] = None  # KIS-1128C V8-BE: "primary" | "secondary"


class QuickReply(BaseModel):
    field: str
    label: str
    options: list[QuickReplyOption]
    multi_select: bool = False
    max_select: Optional[int] = None
    optional: bool = False


# ---------------------------------------------------------------------------
# Session State (returned with every turn)
# ---------------------------------------------------------------------------

class ChatSessionState(BaseModel):
    session_id: UUID
    report_type: str
    status: str

    # Progress
    current_section: int
    current_section_name: str
    total_sections: int = 8
    progress_percent: int

    # Fields
    collected_fields: dict
    collected_count: int
    missing_required: list[str]
    missing_optional: list[str]
    total_fields: int

    # Next steps
    next_fields: list[str]
    next_fields_meta: Optional[dict[str, dict]] = None
    is_completable: bool

    # Draft-Pattern (Sprint 1: always null/false until Sprint 2 activates writes)
    pending_field: Optional[str] = None
    pending_value: Optional[Any] = None
    dialog_mode: bool = False
    edit_mode: bool = False  # KIS-1131 FX-5: exposed so frontend can detect edit state

    # Phase tracking (hybrid conversation model, KIS-1124 Sprint 2)
    conversation_phase: str = "phase_1"
    selected_blocks: list[str] = []
    completed_blocks: list[str] = []
    current_block: Optional[str] = None
    unsurveyed_note: Optional[str] = None

    # Block progress (KIS-1128C V7-BE)
    block_label: Optional[str] = None
    block_progress: int = 0
    block_total: int = 0

    # Quick Replies
    quick_replies: Optional[list[QuickReply]] = None


# ---------------------------------------------------------------------------
# POST /api/chat/start
# ---------------------------------------------------------------------------

class ChatStartRequest(BaseModel):
    report_type: Literal["r1", "strategy", "kpa"] = "r1"
    lang: str = "de"
    consent_report: bool
    briefing_id: Optional[int] = None  # Required for strategy (existing R1 briefing)
    prefill: Optional[dict[str, Any]] = None


class ChatStartResponse(BaseModel):
    session_id: UUID
    state: ChatSessionState
    welcome_message: str


# ---------------------------------------------------------------------------
# POST /api/chat/message
# ---------------------------------------------------------------------------

class ChatMessageRequest(BaseModel):
    session_id: UUID
    message: str
    quick_reply_field: Optional[str] = None
    quick_reply_value: Optional[str] = None


# ---------------------------------------------------------------------------
# GET /api/chat/session/{session_id}
# ---------------------------------------------------------------------------

class ChatSessionResponse(BaseModel):
    state: ChatSessionState
    messages: list[ChatMessage]
    resumable: bool
    last_activity: datetime


# ---------------------------------------------------------------------------
# POST /api/chat/confirm  (Draft-Pattern — Sprint 2 logic, Sprint 1 skeleton)
# ---------------------------------------------------------------------------

class ConfirmFieldRequest(BaseModel):
    session_id: UUID
    field: str
    value: Optional[Any] = None  # Optional: user can send corrected value
    action: str = "confirm"  # "confirm" or "edit"


# ---------------------------------------------------------------------------
# POST /api/chat/complete  (not in PoC)
# ---------------------------------------------------------------------------

class ChatCompleteRequest(BaseModel):
    session_id: UUID
    confirmed: bool = True


class ChatCompleteResponse(BaseModel):
    success: bool
    briefing_id: int
    report_type: str
    redirect_url: str


# ---------------------------------------------------------------------------
# POST /api/chat/fallback  (not in PoC)
# ---------------------------------------------------------------------------

class ChatFallbackRequest(BaseModel):
    session_id: UUID


class ChatFallbackResponse(BaseModel):
    prefill_answers: dict
    missing_fields: list[str]
    current_section: int
    form_url: str


# ---------------------------------------------------------------------------
# GET /api/chat/session/{session_id}/fields  (S4-BE-3: form switch)
# ---------------------------------------------------------------------------

class ChatFieldsExportResponse(BaseModel):
    """Export collected fields for form pre-fill on chat→form switch."""
    fields: dict
    conversation_phase: str
    selected_blocks: list[str]
    completed_blocks: list[str]
    current_block: Optional[str] = None
    collected_count: int
    report_type: str


# ---------------------------------------------------------------------------
# GET /api/chat/sessions
# ---------------------------------------------------------------------------

class ChatSessionSummary(BaseModel):
    session_id: UUID
    report_type: str
    status: str
    current_section: int
    collected_count: int
    total_fields: int
    progress_percent: int
    created_at: datetime
    last_activity: datetime
    resumable: bool
