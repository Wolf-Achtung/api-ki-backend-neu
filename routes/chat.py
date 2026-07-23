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

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text as _sa_text

from core.audit import _resolve_client_ip, _truncate, anonymize_ip
from core.security import AuthenticatedPrincipal, step5_principal
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
    InspirationClickRequest,
    QuickReply,
    QuickReplyOption,
)
from services.chat_normalizer import (
    BUNDESLAND_LABELS,
    BUNDESLAND_VALUES,
    ENUM_VALUES,
    FIELD_REGISTRY,
    NormResult,
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
    is_pointer_phrase,
    is_section_complete,
    normalize_field,
)
from services.field_templates import (
    FIELD_DESCRIPTIONS_SHORT,
    FIELD_DESCRIPTIONS_SHORT_EN,
    FIELD_EXAMPLES,
    FIELD_EXAMPLES_EN,
    FIELD_QUESTIONS,
    get_confirmation,
    get_template_question,
    is_template_field,
)


def _is_en_lang(lang: str | None) -> bool:
    """True when the session/interface language is English (e.g. 'en', 'en-GB')."""
    return bool(lang) and str(lang).strip().lower().startswith("en")

router = APIRouter(prefix="/chat", tags=["chat"])
log = logging.getLogger(__name__)

# Feature flag: Draft-Pattern (Sprint 1 infra — default off)
DRAFT_MODE_ENABLED = os.getenv("DRAFT_MODE_ENABLED", "false").lower() == "true"


def _cleared_draft(prev: dict | None) -> dict:
    """KIS-1237: Pending-Draft zurücksetzen, OHNE persistente Marker zu verlieren.

    draft_state trägt neben dem transienten Pending-Zustand auch
    ``contradiction_acks`` (KIS-1235-P3: welche Live-Abgleich-Fragen schon
    gestellt wurden). Die alten Reset-Literale ``{"pending_field": None, ...}``
    haben die Acks bei jedem QR-Klick mitgelöscht — dieselbe Rückfrage
    („Kurzer Abgleich: …") wurde dadurch an JEDE Antwort erneut angehängt.
    """
    out: dict = {"pending_field": None, "pending_value": None, "dialog_mode": False}
    acks = (prev or {}).get("contradiction_acks")
    if acks:
        out["contradiction_acks"] = acks
    return out

# KIS-1131: Canonical summary marker — used for both emission and detection.
SUMMARY_MARKER = "**Zusammenfassung Ihrer Angaben:**"
# EN summary marker (lang=en sessions) — detection checks both markers.
SUMMARY_MARKER_EN = "**Summary of your details:**"

# ---------------------------------------------------------------------------
# Skip / Decline detection (module scope so tests can import)
# ---------------------------------------------------------------------------
# Exact-match skip words: whole-message equality check after strip+lower.
SKIP_WORDS: frozenset[str] = frozenset({
    "weiter", "skip", "überspringen", "nächste", "weiter bitte", "nächste frage",
})

# EN-only skip words — merged with SKIP_WORDS for lang=en sessions ONLY,
# so German session behaviour stays byte-identical.
SKIP_WORDS_EN: frozenset[str] = frozenset({
    "next", "continue", "next question", "skip it", "pass",
})

# Substring patterns that mark a message as a decline. Checked via
# `any(p in msg_lower for p in _DECLINE_PATTERNS)`; only effective when
# Haiku produced no extraction this turn.
_DECLINE_PATTERNS: list[str] = [
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
    # KIS-1160: plain "nein" / "nö" must register as decline so Sonnet
    # receives the decline help-context instead of praising earlier answers.
    "nein", "nö", "nein danke",
]

# EN-only decline patterns — applied ONLY for lang=en sessions (in addition
# to the German list), so German session behaviour stays byte-identical.
_DECLINE_PATTERNS_EN: list[str] = [
    "don't know", "dont know", "do not know", "no idea", "not sure",
    "can't say", "cannot say", "hard to say", "no preference",
    "doesn't matter", "does not matter", "skip this", "skip that",
    "no comment", "i'd have to check", "would have to check",
]


def is_decline_message(message: str) -> bool:
    """True when the stripped, lowered *message* contains any decline marker."""
    msg_lower = message.strip().lower()
    return any(p in msg_lower for p in _DECLINE_PATTERNS)


def is_skip_word(message: str) -> bool:
    """True when *message* (after strip+lower) is an exact skip word."""
    return message.strip().lower() in SKIP_WORDS


# ---------------------------------------------------------------------------
# Help-Request detection (KIS-1163)
# ---------------------------------------------------------------------------
# Natural-language hints that tell us the user is asking for clarification
# rather than answering. Previously only the explicit "__HELP_REQUEST__"
# sentinel (injected by the frontend help button) fired this path, so
# sentences like "welche gibt es denn?" fell through to the generic
# Haiku-skip path and Sonnet drifted onto the broadest related topic
# (DSGVO → EU AI Act). When any hint matches, event_stream routes through
# build_help_context, which pins the currently-asked field in the prompt.
_HELP_REQUEST_HINTS: frozenset[str] = frozenset({
    "welche gibt es",
    "welche möglichkeiten",
    "was meinst du",
    "was meinen sie",
    "wie meinst du das",
    "wie meinen sie das",
    "was bedeutet",
    "was heißt das",
    "erkläre mir",
    "erklär mir",
    "kannst du erklären",
    "können sie erklären",
    "gib mir beispiele",
    "nenne mir beispiele",
})

# EN-only help hints — applied ONLY for lang=en sessions (in addition to
# the German set), so German session behaviour stays byte-identical.
_HELP_REQUEST_HINTS_EN: frozenset[str] = frozenset({
    "what do you mean",
    "what does that mean",
    "what does this mean",
    "can you explain",
    "could you explain",
    "please explain",
    "give me examples",
    "give me an example",
    "what options are there",
    "which options are there",
})


def is_natural_help_request(message: str, lang: str = "de") -> bool:
    """True when *message* reads like a clarification request in natural
    German — used in addition to the explicit ``__HELP_REQUEST__`` sentinel
    so free-form rückfragen also trigger the field-specific help flow.
    For lang=en sessions, English clarification phrases are matched too."""
    if not message:
        return False
    msg_lower = message.strip().lower()
    if any(h in msg_lower for h in _HELP_REQUEST_HINTS):
        return True
    if _is_en_lang(lang):
        return any(h in msg_lower for h in _HELP_REQUEST_HINTS_EN)
    return False


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
    """Return Block D fields based on branche (Beratung → reduced set).

    ``datenschutz`` is intentionally NOT part of this list: it's a consent
    field (``skip_in_chat: True``), captured at session start via
    ``req.consent_report`` and seeded into ``collected_fields`` there.
    Including it here caused the Block-D head to ask a question with no
    QR options (see Bug C diagnosis).
    """
    if branche == "beratung":
        return ["datenschutzbeauftragter", "ai_act_kenntnis",
                "ki_hemmnisse", "governance_richtlinien"]
    return [
        "datenschutzbeauftragter", "technische_massnahmen",
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
        # KIS-1235-P3: Wirtschafts-Kontext für den Business Case.
        # KIS-1240: durchschnittshonorar entfernt — die Frage wirkte
        # übergriffig (Nutzer-Feedback 04.07.); der Wert wird jetzt aus
        # Jahresumsatz × Projekte/Monat abgeleitet (gpt_analyze).
        "projekte_pro_monat",
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
        "top_zeitfresser",  # KIS-1235-P3: Quick-Win-Anker
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

# EN block labels for lang=en sessions (user-visible in transition texts/QRs).
BLOCK_LABELS_EN: dict[str, str] = {
    "A": "Funding & budget",
    "B": "AI strategy & roadmap",
    "C": "Tools & automation",
    "D": "Legal & data protection",
}


def _block_label_for_lang(block_id: str, lang: str = "de") -> str:
    if _is_en_lang(lang):
        return BLOCK_LABELS_EN.get(block_id, BLOCK_LABELS.get(block_id, block_id))
    return BLOCK_LABELS.get(block_id, block_id)


def _summary_action_qr(lang: str = "de") -> "QuickReply":
    """Summary-phase action buttons (start report / correct answers)."""
    if _is_en_lang(lang):
        return QuickReply(
            field="__summary_action__",
            label="Next step",
            options=[
                QuickReplyOption(value="__start_report__", label="Start analysis", style="primary"),
                QuickReplyOption(value="__edit_summary__", label="Correct details", style="secondary"),
            ],
            multi_select=False,
        )
    return QuickReply(
        field="__summary_action__",
        label="Nächster Schritt",
        options=[
            QuickReplyOption(value="__start_report__", label="Auswertung starten", style="primary"),
            QuickReplyOption(value="__edit_summary__", label="Angaben korrigieren", style="secondary"),
        ],
        multi_select=False,
    )


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


# KIS-1136 rest-fix: Strategy free-text fields must NOT receive a force-default.
# Writing "keine_angabe" (or any sentinel) would bypass the partially-surveyed
# detection (routes/chat.py ~l.3031) and send a meaningless string into the
# report pipeline. Skipping the write keeps the field absent from `collected`,
# so Fix 1 marks the block as _chat_partially_surveyed and the section is
# shortened cleanly. Matches the omit semantic already established in
# _REPORT_BLOCK_DEFAULTS["B"] (None entries).
_FORCE_DEFAULT_SKIP: frozenset[str] = frozenset({
    "strategische_ziele",
    "vision_3_jahre",
    "ki_guardrails",
    "geschaeftsmodell_evolution",
})


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


R1_WELCOME_EN = (
    "Welcome to ki-sicherheit.jetzt! I'll guide you through a short "
    "assessment — it takes about 10–15 minutes. At the end you'll receive "
    "an individual AI report with concrete recommendations for your "
    "business. Your answers are used exclusively for this analysis.\n\n"
    "What industry is your company in? "
    "If you're not sure, simply describe what you do "
    "— I'll help with the classification."
)

STRATEGY_WELCOME_EN = (
    "Welcome back! Based on your AI readiness analysis, I'll now prepare "
    "your individual AI strategy report.\n\n"
    "I still need a few details about your concrete implementation planning. "
    "This takes about 3 minutes. If you're unsure about a question, "
    "just ask — I'm happy to explain.\n\n"
    "Let's begin: What budget have you planned specifically for AI "
    "implementation over the next 12 months?"
)


def _get_welcome(report_type: str, lang: str = "de") -> str:
    if _is_en_lang(lang):
        return STRATEGY_WELCOME_EN if report_type == "strategy" else R1_WELCOME_EN
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

    # Seed consent into collected_fields for r1 so Block D never lands on
    # the ``datenschutz`` consent bool at the block head (Bug C fix).
    # The prefill dict takes precedence — tests or form→chat handover may
    # explicitly (un)set the flag.
    initial_collected = dict(req.prefill or {})
    if req.report_type == "r1" and "datenschutz" not in initial_collected:
        initial_collected["datenschutz"] = True

    session = ChatSession(
        report_type=req.report_type,
        lang=req.lang,
        consent_report=True,
        consent_at=now,
        collected_fields=initial_collected,
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
    welcome_qr = _build_quick_replies(first_fields, req.report_type, lang=req.lang)
    state.quick_replies = welcome_qr

    # Save welcome message
    welcome = _get_welcome(req.report_type, req.lang)
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
async def chat_message(
    req: ChatMessageRequest,
    request: Request,
    db: Session = Depends(get_db),
):
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
    # Session language (set at /start via req.lang; default "de").
    _lang = getattr(session, "lang", None) or "de"
    _lang_en = _is_en_lang(_lang)
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
        # KIS-1161 hotfix v2: must be defined for ALL turn paths (QR click, edit
        # mode, …), not only the free-text branch where the pre-Haiku gate
        # lives. Reading this flag before the free-text branch runs would
        # otherwise raise UnboundLocalError on every QR-click turn.
        _is_low_quality_input = False

        _is_qr_click = bool(req.quick_reply_field and req.quick_reply_value)
        # KIS-1163: Sentinel from the frontend help button + natural-language
        # rückfragen both route through the help-context flow so Sonnet pins
        # the currently-asked field and cannot drift onto unrelated topics.
        _is_help_request = (
            "__HELP_REQUEST__" in req.message
            or (not _is_qr_click and is_natural_help_request(req.message, _lang))
        )

        # Edit-mode detection: check if user wants to change a field after summary
        _is_in_edit_mode = bool(_draft_state_snapshot.get("edit_mode"))
        _edit_words = {"ändern", "etwas ändern", "korrigieren", "anpassen", "nein, etwas ändern", "nein ändern"}
        if _lang_en:
            _edit_words = _edit_words | {"change", "edit", "correct", "change something", "no, change something"}
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
                session.draft_state = _cleared_draft(session.draft_state)

            # --- QR value write (single code path, draft-agnostic) ---
            # KIS-1131 FX-3: Skip meta-fields (__*__) — they are control signals,
            # not data fields, and would produce "Unknown field" warnings in normalize_field.
            if qr_field != "_draft_action" and not qr_field.startswith("__"):
                qr_result = normalize_field(qr_field, req.quick_reply_value, collected, report_type=rt)
                # FIX: Chip-Klicks aus FREETEXT_SUGGESTIONS sind explizite User-Bestätigungen
                # und sollen den is_low_quality_text-Check umgehen (sonst Loop bei 1-Wort-Chips
                # wie "Recherche", "Administration" in zeitersparnis_prioritaet)
                if qr_result.confidence == "low" and qr_field in FREETEXT_SUGGESTIONS:
                    _chip_profile = compute_user_profile(collected)
                    _chip_suggestions = _get_freetext_suggestions(qr_field, collected, _chip_profile, lang=_lang)
                    if req.quick_reply_value in _chip_suggestions:
                        qr_result = NormResult(req.quick_reply_value, "high", False)
                # KIS-1242: QR-Klick = Wahrheit. Wenn der geklickte Wert einer
                # der VON UNS ANGEBOTENEN Chips ist, wird er IMMER persistiert —
                # auch wenn der Normalizer ihn nicht kennt. 3. Testlauf-Abbruch
                # 04.07.: projekte_pro_monat fehlte in ENUM_VALUES, der Klick
                # "unter_2" wurde als low confidence verworfen und dieselbe
                # Frage kam endlos wieder (7/8-Schleife).
                if qr_result.confidence == "low":
                    _offered = {o["value"] for o in (_QR_OPTIONS.get(qr_field) or [])}
                    if req.quick_reply_value in _offered:
                        qr_result = NormResult(req.quick_reply_value, "high", False)
                        log.warning(
                            "[CHAT][KIS-1242] Normalizer kennt %s=%r nicht — Wert stammt "
                            "aus eigenen QR-Optionen, wird verbatim übernommen "
                            "(Registry-Lücke prüfen!)",
                            qr_field, req.quick_reply_value,
                        )
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

            # KIS-1161 Hotfix: Pre-Haiku pointer guard. Catch "siehe oben" /
            # "s.o." / "wie oben" / "dito" / "idem" / "ebenso" at the raw
            # message layer. Without this, Haiku resolves the pointer against
            # the conversation context and returns substantive content from an
            # earlier turn — bypassing the normalizer-level validator.
            _is_low_quality_input = (
                not _is_qr_click
                and not _is_help_request
                and not _is_edit_request
                and not _is_in_edit_mode
                and is_pointer_phrase(req.message)
            )
            if _is_low_quality_input:
                _no_extraction = True
                log.info(
                    "[CHAT] Pre-Haiku reject: pointer phrase %r for field %s — re-ask",
                    req.message, cur_field,
                )

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

            if _is_help_request or _is_low_quality_input:
                # Skip extraction entirely (pointer phrase or help request).
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
                        draft_state = _cleared_draft(draft_state)
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
        if _lang_en:
            # EN-only additions (lang-gated so DE behaviour is unchanged)
            _BLOCK_SKIP_PATTERNS = _BLOCK_SKIP_PATTERNS + [
                "that's enough", "thats enough", "next topic", "next section",
                "next area", "create the report", "generate the report",
                "enough for the report", "move on",
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
        # KIS-1160: "nein" / "nö" recognized as decline so Sonnet gets the
        # decline help-context instead of drifting onto unrelated praise.
        skip_words = (SKIP_WORDS | SKIP_WORDS_EN) if _lang_en else SKIP_WORDS
        _decline_patterns = (_DECLINE_PATTERNS + _DECLINE_PATTERNS_EN) if _lang_en else _DECLINE_PATTERNS
        _msg_lower = req.message.strip().lower()
        _is_skip_word = _msg_lower in skip_words
        _is_decline = (not normalized and not _is_qr_click and not _is_help_request
                       and any(p in _msg_lower for p in _decline_patterns))
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
                    session.draft_state = _cleared_draft(draft_state)
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
        # KIS-1237: Auch ohne Draft-Mode NIE blind {} schreiben — draft_state
        # trägt persistente Marker (contradiction_acks), die den Turn
        # überleben müssen. Basis ist immer der aktuelle Session-Zustand
        # (ORM-Wert dieses Turns, sonst der Snapshot vom Turn-Anfang).
        _draft_current = (
            getattr(session, 'draft_state', None) or _draft_state_snapshot or None
        )
        if DRAFT_MODE_ENABLED or _is_edit_request or _is_in_edit_mode:
            _draft_for_sql = json.dumps(_draft_current or _cleared_draft(None))
        else:
            _draft_for_sql = json.dumps(_cleared_draft(_draft_current))

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
                "ds": _draft_for_sql,
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
                        if _fd_field in _FORCE_DEFAULT_SKIP:
                            # KIS-1136 rest-fix: leave strategy free-text fields
                            # absent so Fix 1 marks the block as partially
                            # surveyed and the pipeline omits the section.
                            log.info(
                                "[CHAT] Phase 2 field safeguard: %s asked %d× "
                                "without extraction — skipping force-default "
                                "(omit via _chat_partially_surveyed)",
                                _fd_field, _fd_count,
                            )
                            _field_ask_counts.pop(_fd_field, None)
                            continue
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

        # Hotfix 1027.2.2-B: is_last_section korrekt über ALLE Sections
        # berechnen — nicht nur über die aktuelle. KIS-1194 zeigte, dass das
        # LLM-System-Prompt sonst nach Sektion 0 fälschlich den ABSCHLUSS-Block
        # (mit "Strategiebericht wird jetzt erstellt"-Cue) bekommt. Die
        # Bedingung ist binär und kombiniert: aktuelle Sektion IST die letzte
        # UND es gibt global keine offenen Felder (required oder optional) mehr.
        _is_last_section_complete = False
        if _current_section >= len(sections) - 1:
            _all_sections_complete = True
            for _si in range(len(sections)):
                _mr, _mo = get_missing_fields(collected, _si, rt)
                if _mr or _mo:
                    _all_sections_complete = False
                    break
            if _all_sections_complete and not next_fields:
                _is_last_section_complete = True

        log.info(
            "[CHAT] Turn %d: normalized=%s, next=%s, no_extraction=%s, is_last_section=%s",
            turn, list(normalized.keys()), next_fields, _no_extraction,
            _is_last_section_complete,
        )

        # Pre-compute next-field QR context so Sonnet can create
        # coherent transitions (KIS-1123 Fix 1).
        _next_field_qr_context = None
        if next_fields:
            _preview_qrs = _build_quick_replies(next_fields, rt, collected, lang=_lang)
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

        # KIS-1161 Hotfix: Pointer phrase ("siehe oben", "dito", …) — ask
        # Sonnet to re-pose the question with a constructive nudge so the
        # user gives a substantive answer for THIS field. Constructive, not
        # accusatory; keep the original question intact.
        if _is_low_quality_input and not _help_ctx and _asked_field:
            _lq_label = (
                FIELD_DESCRIPTIONS.get(_asked_field, _asked_field)
                .split("(")[0].strip()
            )
            _help_ctx = (
                f"\n\nAKTUELLER MODUS: KONKRETISIERUNG GEWÜNSCHT\n"
                f"Der Nutzer hat mit einem Verweis (z.B. 'siehe oben', 's.o.', "
                f"'dito') auf eine frühere Antwort verwiesen, statt eine eigene "
                f"Antwort für \"{_lq_label}\" zu geben. Jede Frage erfasst einen "
                f"anderen Aspekt, daher brauchen wir hier eine spezifische Angabe.\n"
                f"REAGIERE SO:\n"
                f"- Stelle die ursprüngliche Frage erneut, klar und konkret.\n"
                f"- Ergänze einen kurzen Hinweis, dass eine eigene Formulierung "
                f"hier hilft (z.B. 'Können Sie das in einem Satz konkretisieren?').\n"
                f"- Konstruktiv und einladend, NICHT vorwurfsvoll.\n"
                f"- Maximal 2 Sätze total."
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
            # KIS-1241: Genau ZWEI Wege, ein Klick, keine Bestätigung.
            # 2. Abbruch am 04.07.: Die Bereichs-Chips + Schnellmodus +
            # Bestätigen-Schritt überforderten; der Selected-State des
            # empfohlenen Buttons war unsichtbar (blau auf blau).
            if _lang_en:
                _checkpoint_text = (
                    "I now have a good picture of your business — "
                    "I could already create a solid AI report from this.\n\n"
                    "You have two options: the quick report based on what "
                    "you've shared so far — or you answer a few more "
                    "in-depth questions (about 10 minutes), which makes the "
                    "business case, roadmap and compliance sections "
                    "considerably more concrete. "
                    "My recommendation: the full report.\n\n"
                    "At the end you can review and correct all your answers."
                )
            else:
                _checkpoint_text = (
                    "Ich habe jetzt ein gutes Bild von Ihrem Unternehmen — "
                    "damit kann ich bereits einen soliden KI-Report erstellen.\n\n"
                    "Sie haben zwei Möglichkeiten: den Schnell-Report aus den "
                    "bisherigen Angaben — oder Sie beantworten noch einige "
                    "vertiefende Fragen (ca. 10 Minuten), dann werden Business "
                    "Case, Roadmap und Compliance-Teil deutlich konkreter. "
                    "Meine Empfehlung: der vollständige Report.\n\n"
                    "Am Ende prüfen Sie alle Angaben nochmal und können korrigieren."
                )

        # Block completion: inject inter-block transition text
        _block_transition_text = None
        if _cur_conv_phase == "phase_2" and rt == "r1" and _block_just_completed:
            _completed_label = _block_label_for_lang(_cur_block, _lang)
            _remaining_blocks_after = [b for b in _phase_state.get("selected_blocks", [])
                                       if b not in _phase_state.get("completed_blocks", [])]
            if _remaining_blocks_after:
                _next_label = _block_label_for_lang(_remaining_blocks_after[0], _lang)
                if _lang_en:
                    _block_transition_text = (
                        f'Section \u201c{_completed_label}\u201d completed. '
                        f'Shall we continue with \u201c{_next_label}\u201d, '
                        f'or is this enough for the report?'
                    )
                else:
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
                if _lang_en:
                    _block_transition_text = (
                        f'Section \u201c{_completed_label}\u201d completed \u2014 '
                        f'that covers all selected areas. '
                        f'I will now prepare your summary.'
                    )
                else:
                    _block_transition_text = (
                        f'Bereich \u201e{_completed_label}\u201c abgeschlossen \u2014 '
                        f'damit haben wir alle gew\u00e4hlten Bereiche behandelt. '
                        f'Ich erstelle jetzt Ihre Zusammenfassung.'
                    )

        # KIS-1128B V1-BE-2: Template mode — bypass Sonnet for QR-to-QR turns.
        # When user clicked a QR button AND the next field has a deterministic
        # template, serve the response without calling Sonnet (~200ms vs ~3300ms).
        _template_text = None
        # KIS-1243: Kopplungs-Garantie — hat das nächste Feld deterministische
        # Chips (FIELD_EXAMPLES / FREETEXT_SUGGESTIONS), muss auch die Frage
        # deterministisch sein, sonst laufen Sonnet-Frage und Chips
        # auseinander (Tools-Block Anlauf 4: Zeitfresser-Chips unter der
        # Tools-Frage). Template-Mode greift daher auch nach Freitext-Turns —
        # aber nur, wenn der Turn sauber committed hat (mindestens ein Feld
        # normalisiert, kein neuer Draft, keine Rückfrage).
        _nf_for_tpl = next_fields[0] if next_fields else None
        _nf_has_deterministic_chips = bool(_nf_for_tpl) and (
            _nf_for_tpl in FIELD_EXAMPLES or _nf_for_tpl in FREETEXT_SUGGESTIONS
        )
        _clean_commit_turn = bool(normalized) and not _draft_new_field
        if (
            (_is_qr_click or (_nf_has_deterministic_chips and _clean_commit_turn))
            and not _lang_en  # EN: templates are German → let Sonnet answer in English
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
                    if _lang_en:
                        await queue.put("Your report is now being generated. You will receive it shortly.")
                    else:
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
                    is_last_section=_is_last_section_complete,
                    lang=_lang,
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
                _pqr = _build_quick_replies(next_fields[:1], rt, collected, _profile_ctx, lang=_lang)
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
            if _lang_en:
                error_msg = "Sorry, something went wrong. Please try again."
            else:
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

        # KIS-1146: Strategy has no phase_state, so the r1 "summary" branch
        # never fires. Precompute whether the strategy questionnaire is
        # completable (last section + no next field + all required across
        # all sections filled). Optional fields are opt-out.
        _strategy_completion_ready = (
            rt == "strategy"
            and _current_section >= len(sections) - 1
            and not next_fields
            and not any(
                get_missing_fields(collected, _si, rt)[0]
                for _si in range(len(sections))
            )
        )

        # KIS-1255: Nach „Auswertung starten“ dürfen die Summary-Zweige
        # unten KEINE Quick-Replies mehr senden. Vorher kamen
        # ['Auswertung starten', 'Angaben korrigieren'] ein zweites Mal mit
        # der Bestätigung „Ihre Auswertung wird jetzt erstellt“ — das
        # Frontend renderte den Start-Button doppelt (Status- UND
        # Strategie-Fragebogen, Läufe 1121/1123). Guard steckt als
        # `not _report_start_requested` in beiden Summary-Bedingungen.
        if _checkpoint_triggered or _final_phase == "checkpoint":
            # Checkpoint: show topic selection buttons
            # KIS-1241: Genau ZWEI Ein-Klick-Optionen, Single-Select — kein
            # „1 ausgewählt — Bestätigen"-Zwischenschritt mehr. Die
            # Einzelbereichs-Chips (A–D) und der Schnellmodus sind bewusst
            # entfernt: Nutzer können nicht einschätzen, was sie in den
            # Bereichen erwartet (2. Testlauf-Abbruch 04.07.). Das Backend
            # versteht A–D-Werte weiterhin (Legacy-Sessions).
            # KIS-1250: DE-Zweig bewusst zuerst — test_kis1240_ux_fixes prüft
            # das Quelltext-Fenster um das erste Checkpoint-QR-Vorkommen.
            if not _lang_en:
                _cp_options = [
                    QuickReplyOption(
                        value="ALL",
                        label="Vollständiger Report (empfohlen) · ~10 Min",
                        style="primary",
                    ),
                    QuickReplyOption(
                        value="REPORT",
                        label="Schnell-Report jetzt erstellen",
                    ),
                ]
                quick_replies = [QuickReply(
                    field="__checkpoint__",
                    label="Wie geht es weiter?",
                    options=_cp_options,
                    multi_select=False,
                )]
            else:
                _cp_options = [
                    QuickReplyOption(
                        value="ALL",
                        label="Full report (recommended) · ~10 min",
                        style="primary",
                    ),
                    QuickReplyOption(
                        value="REPORT",
                        label="Create quick report now",
                    ),
                ]
                quick_replies = [QuickReply(
                    field="__checkpoint__",
                    label="How would you like to continue?",
                    options=_cp_options,
                    multi_select=False,
                )]
        elif _final_phase == "summary" and not _report_start_requested and not _is_edit_request and (not _is_in_edit_mode or _edit_applied):
            # KIS-1124-HOTFIX: Summary phase needs action buttons so user can
            # start the report or request edits. Previously was [] → user had
            # to type manually, which is not discoverable.
            # KIS-1131 FX-2: Suppress during edit-mode (but show again after edit applied).
            quick_replies = [_summary_action_qr(_lang)]
        elif _final_phase == "phase_1" and _post_phase_1a:
            # Phase 1a: show QR for next sequential QR field
            if _no_extraction and _asked_field and _asked_field not in collected:
                qr_next = [_asked_field]
            else:
                _next_qr = _get_next_phase_1a_field(collected)
                qr_next = [_next_qr] if _next_qr else []
            quick_replies = _build_quick_replies(qr_next, rt, collected, _profile_ctx, lang=_lang)
        elif _final_phase == "phase_1":
            # Phase 1b: open conversation — show QR for structured fields
            # KIS-1124 Testrun 3 Bugs 16+17: Show QR buttons for fields that
            # need structured input (digitalisierungsgrad, ki_kompetenz) to
            # prevent Doppelfrage and unclear free text answers.
            # KIS-1142: ki_ziele added — multi-select with 8 canonical options
            # in _QR_OPTIONS. Freetext answers still accepted via
            # _FREETEXT_EXTRACTION_FIELDS (extractor preserves user wording).
            _p1b_qr_fields = [f for f in next_fields
                              if f in ("digitalisierungsgrad", "ki_kompetenz",
                                       "ki_ziele")]
            quick_replies = _build_quick_replies(
                _p1b_qr_fields, rt, collected, _profile_ctx, lang=_lang,
            ) if _p1b_qr_fields else []
        elif _final_phase == "phase_2" and rt == "r1":
            if _block_just_completed:
                # Block just completed — show inter-block transition QR
                _remaining_blocks_qr = [b for b in _phase_state.get("selected_blocks", [])
                                        if b not in _phase_state.get("completed_blocks", [])]
                if _remaining_blocks_qr:
                    _next_b = _remaining_blocks_qr[0]
                    if _lang_en:
                        quick_replies = [QuickReply(
                            field="__block_transition__",
                            label="Next step",
                            options=[
                                QuickReplyOption(value="continue",
                                                 label=f"Continue: {_block_label_for_lang(_next_b, _lang)}"),
                                QuickReplyOption(value="report", label="Create report"),
                            ],
                            multi_select=False,
                        )]
                    else:
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
                quick_replies = _build_quick_replies(qr_next, rt, collected, _profile_ctx, lang=_lang)
        elif _strategy_completion_ready and not _report_start_requested and not _is_edit_request and (not _is_in_edit_mode or _edit_applied):
            # KIS-1146: Strategy completion — emit __summary_action__ QR manually.
            # Mirrors the r1 summary branch above (line ~1913) since strategy
            # lacks phase_state. Same guard semantics: not an edit request,
            # and either not in edit mode or an edit was just applied.
            quick_replies = [_summary_action_qr(_lang)]
        else:
            # Legacy / Strategy: section-based QR
            if _no_extraction and _asked_field and _asked_field not in collected:
                qr_next = [_asked_field]
            else:
                qr_next = get_next_fields(collected, _current_section, max_fields=1, report_type=rt)

            if _is_qr_click and not (req.quick_reply_field == "__checkpoint__"):
                quick_replies = _build_quick_replies(qr_next, rt, collected, _profile_ctx, lang=_lang)
            elif DRAFT_MODE_ENABLED and _pending_after_turn:
                quick_replies = [QuickReply(
                    field="_draft_action",
                    label="Confirm entry" if _lang_en else "Angabe bestätigen",
                    options=[
                        QuickReplyOption(value="confirm", label="✓ Accept" if _lang_en else "✓ Übernehmen"),
                        QuickReplyOption(value="edit", label="✏️ Edit" if _lang_en else "✏️ Ändern"),
                    ],
                    multi_select=False,
                )]
            elif DRAFT_MODE_ENABLED and _signal == "question":
                quick_replies = []
            elif _is_edit_request or (_is_in_edit_mode and not _edit_applied):
                quick_replies = []
            else:
                quick_replies = _build_quick_replies(qr_next, rt, collected, _profile_ctx, lang=_lang)

        # ------------------------------------------------------------------
        # Post-process response text (KIS-1124 Testrun 3: Bugs 13, 14, 9)
        # ------------------------------------------------------------------
        _qr_labels = []
        if quick_replies:
            for qr in quick_replies:
                _qr_labels.extend(opt.label for opt in (qr.options or []))
        full_response = _post_process_response(full_response, _qr_labels or None, lang=_lang)

        # KIS-1235: Leere Antwort abfangen — im Testlauf blieb nach dem
        # Blockwechsel ("Weiter: KI-Strategie & Roadmap") die Frage komplett
        # aus (Chips ohne Frage-Bubble). Ohne Text rendert das Frontend
        # keine Assistant-Bubble; hier deterministisch die nächste Frage
        # als Fallback einsetzen.
        if not full_response.strip() and not _report_start_requested:
            _fallback = None
            if next_fields:
                # EN: template questions are German → use generic EN question
                _fallback = None if _lang_en else get_template_question(next_fields[0])
                if not _fallback:
                    if _lang_en:
                        _fb_label = _QR_LABELS_EN.get(next_fields[0]) or get_field_label(next_fields[0], rt)
                        if _fb_label:
                            _fallback = f"Next up: {_fb_label} — how does that look for you?"
                    else:
                        _fb_label = get_field_label(next_fields[0], rt)
                        if _fb_label:
                            _fallback = f"Dann weiter: {_fb_label} — wie sieht das bei Ihnen aus?"
            if not _fallback and quick_replies:
                _fallback = "How would you like to proceed?" if _lang_en else "Wie möchten Sie fortfahren?"
            if _fallback:
                log.warning(
                    "[CHAT][KIS-1235] Leere Antwort nach Post-Processing (turn %s, next=%s) — Fallback-Frage eingesetzt",
                    turn, next_fields[:1] if next_fields else None,
                )
                full_response = _fallback

        # ------------------------------------------------------------------
        # KIS-1240: Frage-Garantie. Solange Felder offen sind, MUSS die
        # Antwort eine Frage enthalten. Abgebrochener Testlauf 04.07.:
        # Sonnet meldete bei 8/9 "damit vollständig", stellte keine Frage,
        # keine Chips — der Nutzer saß in einer Sackgasse. Hier wird die
        # Template-Frage fürs nächste Feld deterministisch angehängt.
        # ------------------------------------------------------------------
        if (next_fields and full_response.strip()
                and "?" not in full_response
                and not _report_start_requested
                and not _checkpoint_triggered
                and _final_phase not in ("summary", "checkpoint")):
            # EN: template questions are German → use generic EN question
            _ng_q = None if _lang_en else get_template_question(next_fields[0])
            if not _ng_q:
                if _lang_en:
                    _ng_label = _QR_LABELS_EN.get(next_fields[0]) or get_field_label(next_fields[0], rt)
                    _ng_q = (f"Next up: {_ng_label} — how does that look for you?"
                             if _ng_label else "")
                else:
                    _ng_label = get_field_label(next_fields[0], rt)
                    _ng_q = (f"Dann weiter: {_ng_label} — wie sieht das bei Ihnen aus?"
                             if _ng_label else "")
            if _ng_q and _ng_q not in full_response:
                full_response = f"{full_response}\n\n{_ng_q}"
                log.info(
                    "[CHAT][KIS-1240] Frage-Garantie: Template-Frage für %s angehängt (turn %s)",
                    next_fields[0], turn,
                )

        # ------------------------------------------------------------------
        # KIS-1235-P3: Live-Widerspruchs-Check. Direkt nach einer gespeicherten
        # Antwort werden die gesammelten Angaben auf bekannte Spannungen
        # geprüft (regelbasiert, kein LLM-Call). Jede Spannung wird genau
        # EINMAL pro Session kurz angesprochen — der Nutzer kann antworten
        # oder einfach weitermachen. Flag: CHAT_LIVE_CONTRADICTION_CHECK.
        # ------------------------------------------------------------------
        if (normalized and full_response.strip()
                and not _report_start_requested
                and not _checkpoint_triggered
                and _final_phase != "summary"
                and os.getenv("CHAT_LIVE_CONTRADICTION_CHECK", "1").strip().lower()
                not in ("0", "false", "no", "off")):
            try:
                from services.briefing_contradictions import detect_contradictions_chat
                _live_findings = detect_contradictions_chat(collected)
                _acks = list((session.draft_state or {}).get("contradiction_acks", []))
                _fresh = [(k, t) for k, t in _live_findings if k not in _acks]
                if _fresh:
                    _lc_key, _lc_text = _fresh[0]
                    full_response = f"{full_response}\n\n{_lc_text}"
                    session.draft_state = {
                        **(session.draft_state or {}),
                        "contradiction_acks": _acks + [_lc_key],
                    }
                    log.info("[CHAT][KIS-1235-P3] Live-Abgleich gestellt: %s", _lc_key)
            except Exception as _lc_exc:
                log.debug("[CHAT][KIS-1235-P3] Live-Abgleich übersprungen: %s", _lc_exc)

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
            summary_text = build_summary(collected, rt, lang=_lang)
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
                # KIS: Dispatch by report_type, matching /api/chat/complete (chat.py:2519-2522).
                # Without this branch, strategy sessions fall through to _complete_r1 and
                # create an empty r1 Briefing instead of triggering the strategy pipeline.
                if rt == "strategy":
                    _briefing_id = await _complete_strategy(session, collected, db, now)
                else:
                    _briefing_id = _complete_r1(session, collected, db, now, request)
                _redirect_url = _complete_redirect(rt, _briefing_id, session.lang)
                log.info("[CHAT] Report triggered: briefing_id=%s, session=%s", _briefing_id, session.id)
                yield f"event: report_started\ndata: {json.dumps({'briefing_id': _briefing_id, 'redirect_url': _redirect_url})}\n\n"
            except Exception as exc:
                log.error("[CHAT] Report completion failed: %s", exc, exc_info=True)
                _cmp_err = (
                    "Report generation failed. Please try again."
                    if _lang_en else
                    "Report-Erstellung fehlgeschlagen. Bitte versuchen Sie es erneut."
                )
                yield f"event: error\ndata: {json.dumps({'code': 'completion_error', 'message': _cmp_err})}\n\n"
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
    pending_field_db = pending.get("pending_field")

    _recovery = False
    if not pending_field_db:
        # Fallback: pending_field wurde zwischen SSE-Emit und Confirm-Click
        # überschrieben (Race mit weiterem Stream-Turn, der signal="confirm"
        # setzte). Wenn Client Field+Value mitliefert und Feld noch nicht
        # in collected_fields ist, akzeptieren wir den Confirm trotzdem.
        if (req.action == "confirm"
            and req.field
            and req.value is not None
            and req.field not in (session.collected_fields or {})):
            _recovery = True
        else:
            raise HTTPException(status_code=400, detail="Kein offener Entwurf vorhanden")

    rt = session.report_type
    now = datetime.now(timezone.utc)

    if req.action == "confirm":
        if _recovery:
            field = req.field
            value = req.value
        else:
            field = pending["pending_field"]
            value = req.value if req.value is not None else pending["pending_value"]

        collected = dict(session.collected_fields or {})
        collected[field] = value
        session.collected_fields = collected

        field_meta = dict(session.field_meta or {})
        field_meta[field] = {
            "confidence": "high",
            "source_turn": session.turn_count,
            "raw_input": "confirmed_via_endpoint_recovery" if _recovery else "confirmed_via_endpoint",
            "normalized": True,
            "confirmed": True,
        }
        session.field_meta = field_meta
        session.draft_state = _cleared_draft(session.draft_state)
        session.updated_at = now

        # Section transition check (raw SQL inside, commits internally)
        _check_section_transition(session, collected, db, rt)
        db.commit()  # for remaining ORM fields (collected_fields, draft_state, etc.)

        next_fields = get_next_fields(collected, session.current_section, report_type=rt)
        log.info("[CHAT] Confirm endpoint: %s=%r confirmed", field, value)

        return {
            "status": "confirmed_recovered" if _recovery else "confirmed",
            "field": field,
            "value": value,
            "next_fields": next_fields,
            "progress_percent": calculate_progress(collected, rt),
        }

    elif req.action == "edit":
        cleared_field = pending["pending_field"]
        session.draft_state = _cleared_draft(session.draft_state)
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
    state.quick_replies = _build_quick_replies(
        state.next_fields, rt, session.collected_fields, _profile_ctx,
        lang=getattr(session, "lang", None) or "de",
    )

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
    _fm_lang = getattr(session, "lang", None) or "de"
    _fm_en = _is_en_lang(_fm_lang)

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
            if _fm_en:
                # EN: question falls back to the EN field label; option labels
                # use label_en (fallback: DE label — never crash).
                question = _QR_LABELS_EN.get(field) or FIELD_QUESTIONS.get(field, get_field_label(field))
                if qr_options:
                    qr_options = [
                        {**o, "label": o.get("label_en") or o["label"]}
                        for o in qr_options
                    ]
            else:
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
                "label": _block_label_for_lang(block_id, _fm_lang),
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
# POST /api/chat/inspiration-click — KIS-1138 chip-click telemetry
# ===========================================================================

@router.post("/inspiration-click", status_code=204)
async def chat_inspiration_click(req: InspirationClickRequest) -> Response:
    """Log an inspiration-chip click.

    KIS-1138: Lightweight telemetry — grep-able log line, no DB write.
    No auth (mirrors other chat endpoints), no rate-limit (users click at
    most 3 chips per field). Validation: field must be one of the 4
    FIELD_EXAMPLES keys, chip_index must be 0..2.
    """
    if req.field not in FIELD_EXAMPLES:
        raise HTTPException(status_code=400, detail="unknown field")
    if not 0 <= req.chip_index < len(FIELD_EXAMPLES[req.field]):
        raise HTTPException(status_code=400, detail="chip_index out of range")

    log.info(
        "[CHAT-INSPIRATION] field=%s chip_index=%d briefing=%s",
        req.field, req.chip_index, req.briefing_id,
    )
    return Response(status_code=204)


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
    principal: AuthenticatedPrincipal = Depends(step5_principal),
):
    """Finalize chat session and submit collected data to report pipeline.

    Auth (Wolf E5 Frage 2: C):
        /chat/start bleibt offen — anonyme Sessions sind erlaubt (Lead-Funnel).
        /chat/complete erfordert JWT (oder X-Service-Token), wenn
        STEP5_JWT_ENFORCEMENT=on: das schließt die anonyme Briefing-Erzeugung
        am Ende des Chats. Frontend muss vor der Auswertung Login einbauen.
    """
    # principal wird aktuell nur für Auth-Gating verwendet; user_id-Auflösung
    # läuft weiterhin über _resolve_user (Cookie/Header → DB-User).
    _ = principal
    session = db.query(ChatSession).filter(ChatSession.id == req.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session nicht gefunden")

    # KIS-1131 Fix 3: Idempotency check BEFORE status guard — the SSE stream
    # may have already completed the session via _complete_r1(), so a
    # subsequent /complete call should return the existing briefing_id
    # instead of 400.
    rt = session.report_type
    if session.status == "completed" and session.briefing_id:
        redirect = _complete_redirect(rt, session.briefing_id, session.lang)
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

    redirect = _complete_redirect(rt, briefing_id, session.lang)

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
    lang: str = "de",
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
    # Skipped for lang=en responses — the whole answer is English there and
    # blanket-stripping words like "Great" would mutilate legitimate prose
    # (e.g. "Great Britain"). Flattery openers are still forbidden via prompt.
    if not _is_en_lang(lang):
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

    # KIS-1235: Satzgrenzen-Trim — endet der Text mitten im Wort/Satz
    # (Testlauf: "… verpflichtet. Bei K"), das Fragment nach dem letzten
    # Satzende entfernen. Ursachen: max_tokens-Abbruch im Stream oder
    # Filter oben. Nur trimmen, wenn ein früheres Satzende existiert und
    # der Verlust klein bleibt (<40 %), damit nie eine ganze Antwort kippt.
    if result and result[-1] not in '.!?…:)»"\'':
        _last_end = max(result.rfind('.'), result.rfind('!'), result.rfind('?'))
        if _last_end > 0 and _last_end >= len(result) * 0.6:
            _dropped = result[_last_end + 1:].strip()
            log.warning("[POST-PROCESS] Satzfragment am Ende entfernt: %r", _dropped[:80])
            result = result[:_last_end + 1].strip()

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
    # Pass metadata so the report pipeline knows which areas were surveyed.
    # FIX-KIS-1027.5-C: Field renamed from _chat_unsurveyed_blocks to
    # _chat_blocks_skipped — semantically klar: "user opted out / never entered".
    # Vermeidet Debug-Falle ("nicht erfragt" wirkte wie "Chat nicht durchlaufen").
    if unsurveyed:
        answers["_chat_blocks_skipped"] = unsurveyed
        answers["_chat_surveyed_blocks"] = surveyed_blocks
        log.info("[CHAT] Complete R1: skipped blocks %s → defaults applied", unsurveyed)

    # KIS-1136 Fix 3: Blocks selected but never entered → treat as unsurveyed
    completed_blocks = ps.get("completed_blocks", [])
    selected_not_entered = [b for b in surveyed_blocks if b not in completed_blocks]
    if selected_not_entered:
        for block_id in selected_not_entered:
            defaults = _REPORT_BLOCK_DEFAULTS.get(block_id, {})
            for field, default_val in defaults.items():
                if field not in answers and default_val is not None:
                    answers[field] = default_val
        unsurveyed = unsurveyed + selected_not_entered
        surveyed_blocks = [b for b in surveyed_blocks if b not in selected_not_entered]
        # FIX-KIS-1027.5-C: renamed to _chat_blocks_skipped (s.o.)
        answers["_chat_blocks_skipped"] = unsurveyed
        answers["_chat_surveyed_blocks"] = surveyed_blocks
        log.info("[CHAT] Complete R1: selected but never entered blocks %s → treated as unsurveyed", selected_not_entered)

    # KIS-1136 Fix 1: Surveyed (entered) blocks — check for missing required text fields
    _partially_surveyed = []
    for block_id in surveyed_blocks:
        if block_id == "D":
            branche = answers.get("branche", "")
            block_fields = _get_datenschutz_block_fields(branche)
        else:
            block_fields = BLOCK_FIELDS.get(block_id, [])
        _missing_in_block = []
        for field_name in block_fields:
            field_def = FIELD_REGISTRY.get(field_name, {})
            is_required = field_def.get("required", False)
            is_text = field_def.get("type") == "text"
            skip = field_def.get("skip_in_chat", False)
            if is_required and is_text and not skip and field_name not in answers:
                _missing_in_block.append(field_name)
        if _missing_in_block:
            _partially_surveyed.append({
                "block": block_id,
                "missing": _missing_in_block,
            })
    if _partially_surveyed:
        answers["_chat_partially_surveyed"] = _partially_surveyed
        log.warning("[CHAT-COMPLETE] Partially surveyed blocks: %s", _partially_surveyed)

    # Extract user from JWT — user_id may already be set from /start
    user_id, user_email = _resolve_user(request, db)
    if not user_id:
        user_id = session.user_id  # fallback to session's user_id
    if user_email:
        answers["email"] = user_email
    from core.pii import mask_email as _kis1268_mask
    log.info("[CHAT] Complete R1: user_email=%s, user_id=%s", _kis1268_mask(user_email), user_id)

    audit_request_ip = anonymize_ip(_resolve_client_ip(request)) if request else None
    audit_request_ua = (
        _truncate(request.headers.get("user-agent"), limit=500) if request else None
    )

    briefing = Briefing(
        user_id=user_id,
        lang=session.lang,
        answers=answers,
        status="accepted",
        accepted_at=now,
        source="chat",
        request_ip=audit_request_ip,
        request_ua=audit_request_ua,
    )
    db.add(briefing)
    db.flush()

    session.status = "completed"
    session.completed_at = now
    session.briefing_id = briefing.id
    session.updated_at = now
    db.commit()
    log.info(
        "📝 BRIEFING-CREATED id=%d user_email=%s ip=%s ua=%s source=chat",
        briefing.id,
        _kis1268_mask(user_email),
        audit_request_ip or "(none)",
        _truncate(audit_request_ua, limit=80) or "(none)",
    )
    # mypy: SQLAlchemy Column.id is inferred as Any → cast für signature compliance
    return int(briefing.id)


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

    # FIX-KIS-1027.4-3A: Admin-Briefing-Mail (Fb1+Fb2) am Chat-Abschluss,
    # NICHT erst am Strategy-Pipeline-Ende. Vorher wurde diese Mail erst nach
    # Strategy-Generierung verschickt, und der frühere R1-report_ready-Mail-Pfad
    # rendert nur Fb1 — Fb2 fehlte über mehrere Minuten in jeder Admin-Übersicht.
    try:
        from services.strategy_pipeline import _send_admin_briefing_email
        _send_admin_briefing_email(briefing_id, db)
    except Exception as admin_exc:
        log.warning(
            "[CHAT] Admin briefing email failed (Fb1+Fb2) for briefing_id=%d: %s",
            briefing_id, admin_exc,
        )

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

    # mypy: session.briefing_id ist Optional[int] / Any → cast für signature
    return int(briefing_id)


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


def _complete_redirect(report_type: str, briefing_id: int, lang: str = "de") -> str:
    """Build the redirect URL after completion."""
    # KIS-1251: lang=en mitgeben, damit status.html/strategy.html englisch rendern
    _lang_suffix = "&lang=en" if str(lang or "de").lower().startswith("en") else ""
    if report_type == "strategy":
        return f"/strategy.html?briefing_id={briefing_id}&status=generating{_lang_suffix}"
    return f"/formular/status.html?id={briefing_id}{_lang_suffix}"


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
    # KIS-1138: Default-initialize every new local at function top before any
    # conditional branch sets or reads it (KIS-1161 v2 UnboundLocalError guard).
    field_examples: list[str] | None = None
    field_examples_for: str | None = None

    _ss_lang = getattr(session, "lang", None) or "de"
    _ss_en = _is_en_lang(_ss_lang)
    # EN sessions get EN inspiration chips (same keys, fallback DE list).
    _examples_map = {**FIELD_EXAMPLES, **FIELD_EXAMPLES_EN} if _ss_en else FIELD_EXAMPLES

    rt = session.report_type
    sections = get_sections_for_report(rt)
    registry = get_registry_for_report(rt)
    collected = collected_override if collected_override is not None else (session.collected_fields or {})
    section_idx = section_override if section_override is not None else session.current_section
    section = sections[section_idx]

    missing_req, missing_opt = get_missing_fields(collected, section_idx, rt)
    # Always 1 field at a time (Smart Grouping disabled, KIS-1122)
    next_fields = get_next_fields(collected, section_idx, max_fields=1, report_type=rt)

    # Phase tracking (hybrid conversation model, KIS-1124) — hoisted above
    # the field_examples block so the chip trigger can consult current_block.
    ps = _get_phase_state(session)

    # KIS-1138: Surface inspiration chips for the 4 strategic-imaginative
    # Block-B freetext fields. Defensive copy so callers can't mutate the
    # module-level dict. Concrete-experiential fields are deliberately absent
    # from FIELD_EXAMPLES and therefore always yield None here.
    #
    # Two cooperating paths:
    #   1. Block-aware (Phase 2 hybrid): when current_block is set, read the
    #      first uncollected field of that block. In the real hybrid flow
    #      section_idx stays pinned (checkpoint) while blocks advance, so the
    #      section pipeline never surfaces Block-B fields as next_fields[0].
    #   2. Section-based (fallback): next_fields[0] from the section pipeline.
    #      Still correct when callers set current_section directly (tests).
    _cur_blk_for_chips = ps.get("current_block")
    if _cur_blk_for_chips:
        _remaining_block_fields = _get_block_fields(_cur_blk_for_chips, collected)
        if _remaining_block_fields and _remaining_block_fields[0] in _examples_map:
            field_examples = list(_examples_map[_remaining_block_fields[0]])
            field_examples_for = _remaining_block_fields[0]
    if field_examples is None:
        _next_field = next_fields[0] if next_fields else None
        if _next_field and _next_field in _examples_map:
            field_examples = list(_examples_map[_next_field])
            field_examples_for = _next_field

    # KIS-1139: Drop chips the user has already chosen for this field. On a
    # clarifying follow-up turn Sonnet re-asks the same field, so field_examples
    # points at it again — without this filter the user sees their own previous
    # answer back as an inspiration chip. Sources of "already given":
    #   - collected[field] after commit
    #   - draft_state.pending_value mid-draft (the actual bug state; value is
    #     staged in draft_state but not yet in collected_fields).
    # When every chip was consumed, return None so the UI renders nothing
    # instead of an empty chip bar.
    if field_examples and field_examples_for:
        _draft_for_filter = getattr(session, "draft_state", None) or {}
        _used: set[str] = set()
        _collected_answer = collected.get(field_examples_for)
        if isinstance(_collected_answer, str) and _collected_answer.strip():
            _used.add(_collected_answer.strip().casefold())
        if _draft_for_filter.get("pending_field") == field_examples_for:
            _pv = _draft_for_filter.get("pending_value")
            if isinstance(_pv, str) and _pv.strip():
                _used.add(_pv.strip().casefold())
        if _used:
            field_examples = [
                chip for chip in field_examples
                if chip.strip().casefold() not in _used
            ]
            if not field_examples:
                field_examples = None
                field_examples_for = None

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
    if rt == "strategy":
        # KIS-1146: Strategy has no phase_state and never writes SUMMARY_MARKER
        # when optional fields are skipped. Signal completable once the user
        # reaches the last section with all required fields filled.
        _strategy_all_req_done = not any(
            get_missing_fields(collected, _si, rt)[0]
            for _si in range(len(sections))
        )
        completable = last_section and _strategy_all_req_done and not _editing
    else:
        completable = summary_sent and (all_done or _in_summary_phase) and not _editing

    # KIS-1124: Unsurveyed note — only in summary phase when blocks were skipped
    unsurveyed_note: str | None = None
    if ps["conversation_phase"] == "summary":
        _all_blocks = ["A", "B", "C", "D"]
        _unsurveyed = [b for b in _all_blocks if b not in ps["selected_blocks"]]
        if _unsurveyed:
            if _ss_en:
                _names = [BLOCK_LABELS_EN.get(b, b) for b in _unsurveyed]
                unsurveyed_note = (
                    f"Areas not covered in depth: {', '.join(_names)}. "
                    "These will be supplemented in the report with industry-standard defaults."
                )
            else:
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
        _blk_label = _block_label_for_lang(_cur_blk, _ss_lang) if _ss_en else BLOCK_LABELS.get(_cur_blk, "")
        if _cur_blk == "D":
            _blk_all = _get_datenschutz_block_fields(collected.get("branche", ""))
        else:
            _blk_all = BLOCK_FIELDS.get(_cur_blk, [])
        # KIS-1131 Fix 2: Exclude smart-skipped fields from progress count
        _skip_count = sum(1 for f in _blk_all
                         if f in collected and _smart_skip_field(f, collected) is not None)
        _blk_total = len(_blk_all) - _skip_count
        _blk_progress = len([f for f in _blk_all if f in collected]) - _skip_count

    # KIS-1162: Single source of truth for the UI section header. In Phase 2
    # the legacy current_section_name lags behind because sections don't align
    # with the hybrid thematic blocks. block_label, when present, always names
    # the currently active block; otherwise we fall back to the legacy label,
    # which is correct for Phase 1 / checkpoint / summary / strategy flows.
    display_section_title = _blk_label or section_name
    if _ss_en and not _blk_label:
        # EN header: translate the legacy section name (fallback: DE name)
        try:
            from services.chat_conversation import _SECTION_NAMES_EN
            display_section_title = _SECTION_NAMES_EN.get(section_name, section_name)
        except Exception:
            pass

    return ChatSessionState(
        session_id=session.id,
        report_type=session.report_type,
        status=session.status,
        current_section=section_idx,
        current_section_name=section_name,
        display_section_title=display_section_title,
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
        edit_mode=bool(draft.get("edit_mode")),  # KIS-1131 FX-5
        conversation_phase=ps["conversation_phase"],
        selected_blocks=ps["selected_blocks"],
        completed_blocks=ps["completed_blocks"],
        current_block=ps["current_block"],
        unsurveyed_note=unsurveyed_note,
        block_label=_blk_label,
        block_progress=_blk_progress,
        block_total=_blk_total,
        field_examples=field_examples,
        field_examples_for=field_examples_for,
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
            if SUMMARY_MARKER in content or SUMMARY_MARKER_EN in content:
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
    # KIS-1240: fehlte — das Enum-Feld wurde ohne Chips gestellt, Nutzer
    # tippten Freitext ("1-2") und die Extraktion wurde zum Glücksspiel.
    "projekte_pro_monat": [
        {"value": "unter_2", "label": "Unter 2"},
        {"value": "2_5", "label": "2–5"},
        {"value": "6_10", "label": "6–10"},
        {"value": "ueber_10", "label": "Über 10"},
        {"value": "keine_angabe", "label": "Schwankt stark / keine Angabe"},
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
    "projekte_pro_monat": "Aufträge/Projekte pro Monat",
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
    "zeitersparnis_prioritaet": "Entlastungs-Bereiche", "geschaeftsmodell_evolution": "Geschäftsmodell-Ideen",
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

# EN field labels for quick replies (lang=en sessions).
# Fallback is always the German label from _QR_LABELS — never crash.
_QR_LABELS_EN: dict[str, str] = {
    # Sektion 0
    "branche": "Industry", "unternehmensgroesse": "Company size",
    "selbststaendig": "Business type", "country": "Country",
    "bundesland": "Federal state / region", "hauptleistung": "Main service",
    "jahresumsatz": "Annual revenue",
    "projekte_pro_monat": "Orders/projects per month",
    # Sektion 1
    "zielgruppen": "Target groups", "it_infrastruktur": "IT infrastructure",
    "interne_ki_kompetenzen": "Internal AI team", "datenquellen": "Available data",
    # Sektion 2
    "digitalisierungsgrad": "Digitalisation level (1–10)",
    "prozesse_papierlos": "Paperless processes", "automatisierungsgrad": "Degree of automation",
    "ki_einsatz": "Current AI use", "ki_kompetenz": "AI competence",
    # Sektion 3
    "ki_ziele": "AI goals", "anwendungsfaelle": "Use cases",
    "ki_projekte": "Existing AI projects", "pilot_bereich": "Pilot area",
    "zeitersparnis_prioritaet": "Areas for relief", "geschaeftsmodell_evolution": "Business model ideas",
    "vision_3_jahre": "3-year vision",
    # Sektion 4
    "strategische_ziele": "Strategic goals", "ki_guardrails": "AI guardrails",
    "massnahmen_komplexitaet": "Implementation effort", "roadmap_vorhanden": "AI roadmap",
    "governance_richtlinien": "Governance guidelines", "change_management": "Willingness to change",
    # Sektion 5
    "zeitbudget": "Time budget per week", "vorhandene_tools": "Systems in use",
    "trainings_interessen": "Training topics", "vision_prioritaet": "Strategic lever",
    "innovationsprozess": "Innovation process", "regulierte_branche": "Regulated industry",
    # Sektion 6
    "datenschutz": "Data protection",  # r1 consent bool (summary display only)
    "datenschutzbeauftragter": "Data protection officer", "technische_massnahmen": "Protection measures",
    "folgenabschaetzung": "Data protection impact assessment", "meldewege": "Reporting channels",
    "loeschregeln": "Deletion policies", "ai_act_kenntnis": "EU AI Act knowledge",
    "ki_hemmnisse": "AI barriers",
    # Sektion 7
    "bisherige_foerdermittel": "Previous funding", "interesse_foerderung": "Funding interest",
    "erfahrung_beratung": "Consulting experience", "investitionsbudget": "Investment budget",
    "marktposition": "Market position", "benchmark_wettbewerb": "Competitor comparison",
    "risikofreude": "Risk appetite (1–5)",
    # Strategy
    "s1_budget": "AI implementation budget", "s2_zeitrahmen": "Implementation timeframe",
    "s3_prioritaeten": "Top priorities (max. 3)", "s4_engpass": "Biggest bottleneck",
    "s5_software": "Software in use", "s5_vision": "AI vision",
    "s6_foerderinteresse": "Funding interest", "s7_entscheidung": "Decision structure",
    "s8_erfahrung": "AI experience", "s9_ansatz": "Infrastructure approach",
    "s10_datenschutz": "Data protection priority",
    "wettbewerber_anzahl": "Competitors", "kundenbindung_typ": "Customer relationships",
    "datenreife": "Data maturity",
}


# ---------------------------------------------------------------------------
# EN option labels (lang=en sessions).
# Source: /formular/formbuilder_en_SINGLE_FULL.js (matched by option value);
# fields missing there (projekte_pro_monat, digitalisierungsgrad grouping,
# risikofreude, strategy fields) translated to match the same register.
# VALUES stay untouched (backend enums) — the loop below only injects a
# "label_en" display key into the existing _QR_OPTIONS entries.
# Purely numeric / product-name options (prozesse_papierlos, s5_software,
# bundesland proper nouns) intentionally have no EN label (DE label is
# language-neutral and used as fallback).
# ---------------------------------------------------------------------------
_QR_OPTION_LABELS_EN: dict[str, dict[str, str]] = {
    "branche": {
        "marketing": "Marketing & Advertising", "beratung": "Consulting & Services",
        "it": "IT & Software", "finanzen": "Finance & Insurance",
        "handel": "Retail & E-Commerce", "bildung": "Education",
        "verwaltung": "Public Administration", "gesundheit": "Healthcare",
        "bau": "Construction & Architecture", "medien": "Media & Creative Industries",
        "industrie": "Manufacturing & Production", "logistik": "Transport & Logistics",
        "gastronomie": "Hospitality & Tourism",
    },
    "unternehmensgroesse": {
        "1": "1 (Solo/Freelancer)", "2–10": "2–10 (Small team)", "11–100": "11–100 (SME)",
    },
    "selbststaendig": {
        "freiberufler": "Freelancer / self-employed",
        "kapitalgesellschaft": "Single-person corporation (GmbH/UG)",
        "einzelunternehmer": "Sole proprietor (registered business)",
        "sonstiges": "Other",
    },
    "country": {
        "DE": "Germany", "AT": "Austria", "CH": "Switzerland", "GB": "United Kingdom",
    },
    "jahresumsatz": {
        "unter_100k": "Up to €100,000", "100k_500k": "€100,000–500,000",
        "500k_2m": "€500,000–2M", "2m_10m": "€2–10M",
        "ueber_10m": "Over €10M", "keine_angabe": "Prefer not to say",
    },
    "projekte_pro_monat": {
        "unter_2": "Under 2", "2_5": "2–5", "6_10": "6–10",
        "ueber_10": "Over 10", "keine_angabe": "Varies a lot / no answer",
    },
    "zielgruppen": {
        "b2b": "B2B (business customers)", "b2c": "B2C (consumers)",
        "kmu": "SMEs", "grossunternehmen": "Large enterprises",
        "selbststaendige": "Self-employed/freelancers", "oeffentliche_hand": "Public sector",
        "privatpersonen": "Private individuals", "startups": "Startups", "andere": "Other",
    },
    "it_infrastruktur": {
        "cloud": "Cloud-based (e.g. Microsoft 365)", "on_premise": "Own data center (on-premises)",
        "hybrid": "Hybrid (cloud + own servers)", "unklar": "Unclear / still open",
    },
    "interne_ki_kompetenzen": {
        "ja": "Yes", "nein": "No", "in_planung": "In planning",
    },
    "datenquellen": {
        "kundendaten": "Customer data (CRM, service)", "verkaufsdaten": "Sales/order data",
        "produktionsdaten": "Production/operations data", "personaldaten": "Personnel/HR data",
        "marketingdaten": "Marketing/campaign data", "sonstige": "Other data sources",
    },
    "digitalisierungsgrad": {
        "2": "Low (1–3)", "5": "Medium (4–5)", "7": "Advanced (6–7)",
        "8": "High (8–9)", "9": "Fully digital (10)",
    },
    "automatisierungsgrad": {
        "sehr_niedrig": "Very low", "eher_niedrig": "Rather low",
        "mittel": "Medium", "eher_hoch": "Rather high", "sehr_hoch": "Very high",
    },
    "ki_einsatz": {
        "chatbots": "Chatbots / customer service", "marketing": "Marketing & content",
        "vertrieb": "Sales & CRM", "datenanalyse": "Data analysis",
        "produktion": "Production / logistics", "hr": "HR management",
        "andere": "Other areas", "noch_keine": "Not yet in use",
    },
    "ki_kompetenz": {
        "hoch": "High", "mittel": "Medium", "niedrig": "Low", "keine": "None",
    },
    "ki_ziele": {
        "effizienz": "Increase efficiency", "automatisierung": "Automation",
        "neue_produkte": "New products/services", "kundenservice": "Improve customer service",
        "datenauswertung": "Better use of data", "kosten_senken": "Reduce costs",
        "wettbewerbsfaehigkeit": "Competitiveness", "keine_angabe": "Still unclear",
    },
    "anwendungsfaelle": {
        "chatbots": "Chatbots / FAQ automation", "content_generation": "Content generation",
        "datenanalyse": "Data analysis & reporting", "dokumentation": "Documentation & knowledge",
        "prozess_automation": "Process automation", "personalisierung": "Personalization",
        "andere": "Other", "keine_angabe": "Still unclear",
    },
    "pilot_bereich": {
        "kundenservice": "Customer service", "marketing": "Marketing / content",
        "vertrieb": "Sales", "verwaltung": "Administration / back office",
        "produktion": "Production / logistics", "andere": "Other",
    },
    "massnahmen_komplexitaet": {
        "niedrig": "Low", "mittel": "Medium", "hoch": "High", "unklar": "Unclear",
    },
    "roadmap_vorhanden": {
        "ja": "Yes", "teilweise": "Partially", "nein": "No",
    },
    "governance_richtlinien": {
        "ja": "Yes", "teilweise": "Partially", "nein": "No",
    },
    "change_management": {
        "sehr_hoch": "Very high", "hoch": "High", "mittel": "Medium",
        "niedrig": "Low", "sehr_niedrig": "Very low",
    },
    "zeitbudget": {
        "unter_2": "Under 2 hours", "2_5": "2–5 hours",
        "5_10": "5–10 hours", "ueber_10": "Over 10 hours",
    },
    "vorhandene_tools": {
        "crm": "CRM (HubSpot, Salesforce)", "erp": "ERP (SAP, Odoo)",
        "projektmanagement": "Project management (Asana, Trello)",
        "marketing_automation": "Marketing automation",
        "buchhaltung": "Accounting software", "keine": "None / other",
    },
    "trainings_interessen": {
        "prompt_engineering": "Prompt engineering", "llm_basics": "LLM basics",
        "datenqualitaet_governance": "Data quality & governance",
        "automatisierung": "Automation & scripts",
        "ethik_recht": "Ethical & legal basics", "keine": "None / still unclear",
    },
    "vision_prioritaet": {
        "gpt_services": "AI-powered services and products",
        "kundenservice": "Customer service optimization",
        "datenprodukte": "Data-based offerings",
        "prozessautomation": "Internal process automation",
        "marktfuehrerschaft": "Technology leadership",
        "keine_angabe": "Still unclear",
    },
    "innovationsprozess": {
        "innovationsteam": "Innovation team", "mitarbeitende": "Through employees",
        "kunden": "With customers", "berater": "External consultants",
        "zufall": "By chance", "unbekannt": "No clear strategy",
    },
    "regulierte_branche": {
        "gesundheit": "Healthcare & medicine", "finanzen": "Finance & insurance",
        "oeffentlich": "Public sector", "recht": "Legal services",
        "vertraulich_nda": "Confidential client data / NDA",
        "keine": "None of these industries",
    },
    "datenschutzbeauftragter": {
        "ja": "Yes", "nein": "No", "teilweise": "Partially (external/planning)",
    },
    "technische_massnahmen": {
        "alle": "All relevant measures", "teilweise": "Partially in place", "keine": "None yet",
    },
    "folgenabschaetzung": {
        "ja": "Yes, completed", "nein": "No, not yet", "teilweise": "In planning",
    },
    "meldewege": {
        "ja": "Yes, clearly defined", "teilweise": "Partially in place",
        "nein": "No, not yet regulated",
    },
    "loeschregeln": {
        "ja": "Yes, documented", "teilweise": "Partially in place",
        "nein": "No, not yet defined",
    },
    "ai_act_kenntnis": {
        "sehr_gut": "Very good", "gut": "Good",
        "gehoert": "Heard of it", "unbekannt": "Not yet familiar",
    },
    "ki_hemmnisse": {
        "rechtsunsicherheit": "Legal uncertainty", "datenschutz": "Data protection",
        "knowhow": "Lack of know-how", "budget": "Limited budget",
        "teamakzeptanz": "Team acceptance", "zeitmangel": "Lack of time",
        "it_integration": "IT integration", "keine": "No barriers", "andere": "Other",
    },
    "bisherige_foerdermittel": {"ja": "Yes", "nein": "No"},
    "interesse_foerderung": {
        "ja": "Yes, suggest programmes", "nein": "No need",
        "unklar": "Unclear, please advise",
    },
    "erfahrung_beratung": {"ja": "Yes", "nein": "No", "unklar": "Unclear"},
    "investitionsbudget": {
        "unter_2000": "Under €2,000", "2000_10000": "€2,000–10,000",
        "10000_50000": "€10,000–50,000", "ueber_50000": "Over €50,000",
        "unklar": "Still unclear",
    },
    "marktposition": {
        "marktfuehrer": "Market leader", "oberes_drittel": "Upper third",
        "mittelfeld": "Midfield", "nachzuegler": "Laggard",
        "unsicher": "Hard to assess",
    },
    "benchmark_wettbewerb": {
        "ja": "Yes, regularly", "nein": "No", "selten": "Rarely",
    },
    "risikofreude": {
        "1": "1 (very cautious)", "2": "2", "3": "3 (balanced)",
        "4": "4", "5": "5 (keen to experiment)",
    },
    # --- Strategy ---
    "s1_budget": {
        "unter_2000": "Under €2,000", "2000_10000": "€2,000 – 10,000",
        "10000_50000": "€10,000 – 50,000", "ueber_50000": "Over €50,000",
        "unklar": "Still unclear",
    },
    "s2_zeitrahmen": {
        "Sofort (1-3 Monate)": "Immediately (1–3 months)",
        "Kurzfristig (3-6 Monate)": "Short term (3–6 months)",
        "Mittelfristig (6-12 Monate)": "Medium term (6–12 months)",
        "Langfristig (12-18 Monate)": "Long term (12–18 months)",
    },
    "s3_prioritaeten": {
        "Kosten senken": "Reduce costs", "Umsatz steigern": "Increase revenue",
        "Qualität verbessern": "Improve quality",
        "Geschwindigkeit erhöhen": "Increase speed",
        "Compliance sichern": "Ensure compliance",
        "Neue Geschäftsfelder": "New business areas",
        "Fachkräftemangel kompensieren": "Compensate skills shortage",
        "Kundenerlebnis verbessern": "Improve customer experience",
    },
    "s4_engpass": {
        "Zu wenig Know-how": "Not enough know-how", "Kein Budget": "No budget",
        "Fehlende Daten": "Missing data",
        "Widerstand im Team": "Resistance in the team",
        "Regulatorische Unsicherheit": "Regulatory uncertainty",
        "Kein klarer Use Case": "No clear use case", "Andere": "Other",
    },
    "s6_foerderinteresse": {
        "Ja, dringend": "Yes, urgently", "Ja, wenn passend": "Yes, if suitable",
        "Nein, eigenes Budget": "No, own budget", "Weiß nicht": "Don't know",
    },
    "s7_entscheidung": {
        "Entscheide allein": "I decide alone",
        "Brauche Vorlage für Geschäftsleitung": "Proposal for management",
        "Muss Gesellschafter überzeugen": "Convince shareholders",
        "Muss Aufsichtsrat/Beirat informieren": "Inform advisory/supervisory board",
    },
    "s8_erfahrung": {
        "Noch keine": "None yet", "Experimentiert": "Experimenting",
        "Erste Tools im Einsatz": "First tools in use", "Fortgeschritten": "Advanced",
    },
    "s9_ansatz": {
        "Cloud-SaaS": "Cloud SaaS", "On-Premise": "On-premise",
        "Hybrid": "Hybrid", "Egal": "Still unclear / no preference",
    },
    "s10_datenschutz": {
        "Hoch": "High", "Mittel": "Medium", "Niedrig": "Low",
    },
    "wettbewerber_anzahl": {
        "wenige": "Few (1–3)", "mehrere": "Several (4–10)",
        "viele": "Many (more than 10)", "unklar": "Hard to assess",
    },
    "kundenbindung_typ": {
        "einmalig": "Mostly one-off customers",
        "wiederkehrend": "Recurring customers / contracts",
        "gemischt": "Mix of both",
    },
    "datenreife": {
        "keine": "Hardly any / no structured data",
        "basis": "Basic data (CRM, accounting)",
        "umfangreich": "Extensive own data assets",
        "unklar": "Not sure",
    },
}

# Inject "label_en" into the existing _QR_OPTIONS entries (display-only key;
# values and German labels stay byte-identical).
for _f_en, _lbls_en in _QR_OPTION_LABELS_EN.items():
    for _o_en in _QR_OPTIONS.get(_f_en, []):
        _l_en = _lbls_en.get(str(_o_en.get("value")))
        if _l_en:
            _o_en["label_en"] = _l_en
del _f_en, _lbls_en, _o_en, _l_en


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
# EN freetext suggestions (lang=en sessions). Suggestion chips are taken over
# verbatim as the user's answer, so they MUST be English for EN sessions.
# Fallback: German suggestions — never crash.
# ---------------------------------------------------------------------------

FREETEXT_SUGGESTIONS_EN: dict[str, dict[str, list[str]]] = {
    "zeitersparnis_prioritaet": {
        "beratung": ["Proposal writing", "Client documentation", "Research", "Administration"],
        "it": ["Bug tracking", "Documentation", "Meetings", "Deployment"],
        "bau": ["Measurement & costing", "Site documentation", "Communication with authorities"],
        "handel": ["Order processing", "Inventory", "Customer communication"],
        "marketing": ["Content creation", "Reporting", "Campaign planning", "Client briefings"],
        "finanzen": ["Compliance checks", "Reporting", "Customer communication"],
        "gesundheit": ["Documentation", "Appointment management", "Billing"],
        "gastronomie": ["Order management", "Staff scheduling", "Bookkeeping"],
        "bildung": ["Lesson preparation", "Participant management", "Certificate creation", "Evaluations"],
        "verwaltung": ["Application processing", "Reporting", "Citizen communication", "Documentation"],
        "medien": ["Briefings & concepts", "Rights management", "Post-production", "Project coordination"],
        "industrie": ["Quality documentation", "Maintenance planning", "Supplier communication", "Reporting"],
        "logistik": ["Route planning", "Shipment tracking", "Customs documentation", "Customer communication"],
        "default": ["Emails & communication", "Documentation", "Research", "Administration"],
    },
    "ki_projekte": {
        "default": ["Used ChatGPT in the team", "Automation experiments", "No projects yet"],
    },
}

_EXPERT_FREETEXT_SUGGESTIONS_EN: dict[str, list[str]] = {
    "ki_projekte": ["API integration (OpenAI, Anthropic, etc.)", "Own AI workflows", "RAG / retrieval systems"],
}

_SOLO_FREETEXT_SUGGESTIONS_EN: dict[str, list[str]] = {
    "ki_projekte": ["AI tools in use", "Automation experiments", "No projects yet"],
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

# EN variants of the profile-aware label overrides (lang=en sessions).
_SOLO_QR_LABELS_EN: dict[str, str] = {
    "ki_kompetenz": "AI competence",
    "change_management": "Willingness to change",
    "interne_ki_kompetenzen": "AI/digitalisation skills",
    "innovationsprozess": "Innovation approach",
}

_SMALL_TEAM_QR_LABELS_EN: dict[str, str] = {
    "innovationsprozess": "Innovation approach",
}

_EXPERT_QR_LABELS_EN: dict[str, str] = {
    "pilot_bereich": "AI expansion potential",
    "ki_projekte": "Active AI projects",
}

_INTERMEDIATE_QR_LABELS_EN: dict[str, str] = {
    "pilot_bereich": "Next AI project",
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
        {"value": "ja", "label": "Ja, mit externen Partnern", "label_en": "Yes, with external partners"},
        {"value": "nein", "label": "Nein, alles selbst", "label_en": "No, all myself"},
        {"value": "in_planung", "label": "Geplant", "label_en": "Planned"},
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
    lang: str = "de",
) -> list[QuickReply]:
    """Build quick reply buttons for enum fields and freetext suggestions.

    Profile-aware: adapts labels and filters options based on
    Solo/Team/Expert/Intermediate detection from collected_fields.

    lang="en" selects EN display labels (option "label_en" / _QR_LABELS_EN /
    FREETEXT_SUGGESTIONS_EN) with German fallback — never crash. Option
    VALUES are untouched. Default "de" is byte-identical to before.

    Args:
        profile_context: Optional pre-computed profile dict. Used by
            Strategy sessions to pass R1-derived profile data that
            isn't in the Strategy collected_fields.
    """
    registry = get_registry_for_report(report_type)
    collected = collected_fields or {}
    profile = profile_context or compute_user_profile(collected)
    _en = _is_en_lang(lang)
    replies = []

    for field_name in next_fields:
        if field_name in collected:
            continue  # Already collected — no buttons

        reg = registry.get(field_name, {})

        # Freetext suggestions (for selected text fields)
        if reg.get("type") == "text" and field_name in FREETEXT_SUGGESTIONS:
            suggestions = _get_freetext_suggestions(field_name, collected, profile, lang=lang)
            if suggestions:
                options = [QuickReplyOption(value=s, label=s) for s in suggestions]
                label = _get_context_label(field_name, profile, lang=lang)
                is_optional = not reg.get("required", False)
                _sugg_suffix = "(suggestions)" if _en else "(Vorschläge)"
                replies.append(QuickReply(
                    field=field_name, label=f"{label} {_sugg_suffix}", options=options,
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
            QuickReplyOption(
                value=o["value"],
                label=(o.get("label_en") or o["label"]) if _en else o["label"],
                description=o.get("description"),
            )
            for o in options_data
        ]
        label = _get_context_label(field_name, profile, lang=lang)
        is_multi = reg.get("type") == "multi"
        max_sel = reg.get("max_select") if is_multi else None
        is_optional = not reg.get("required", False)
        if _en:
            _desc = FIELD_DESCRIPTIONS_SHORT_EN.get(field_name) or FIELD_DESCRIPTIONS_SHORT.get(field_name)
        else:
            _desc = FIELD_DESCRIPTIONS_SHORT.get(field_name)
        replies.append(QuickReply(
            field=field_name, label=label, options=options,
            multi_select=is_multi, max_select=max_sel,
            optional=is_optional,
            description=_desc,
        ))

    return replies


def _get_context_label(field_name: str, profile: dict, lang: str = "de") -> str:
    """Get profile-aware QR label. Priority: expert > intermediate > solo > small_team > default.

    lang="en" resolves the EN variant of the matched override / default label,
    falling back to the German label — never crash.
    """
    _en = _is_en_lang(lang)
    if profile.get("is_expert"):
        label = _EXPERT_QR_LABELS.get(field_name)
        if label:
            if _en:
                return _EXPERT_QR_LABELS_EN.get(field_name, label)
            return label
    if profile.get("is_intermediate"):
        label = _INTERMEDIATE_QR_LABELS.get(field_name)
        if label:
            if _en:
                return _INTERMEDIATE_QR_LABELS_EN.get(field_name, label)
            return label
    if profile.get("is_solo"):
        label = _SOLO_QR_LABELS.get(field_name)
        if label:
            if _en:
                return _SOLO_QR_LABELS_EN.get(field_name, label)
            return label
    if profile.get("is_small_team"):
        label = _SMALL_TEAM_QR_LABELS.get(field_name)
        if label:
            if _en:
                return _SMALL_TEAM_QR_LABELS_EN.get(field_name, label)
            return label
    if _en:
        return _QR_LABELS_EN.get(field_name) or _QR_LABELS.get(field_name, field_name)
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
    lang: str = "de",
) -> list[str]:
    """Get branche-specific + profile-aware suggestions for a freetext field.

    lang="en" serves the EN suggestion sets (fallback: German — never crash).
    """
    _en = _is_en_lang(lang)
    # Expert override takes priority
    if profile and profile.get("is_expert"):
        expert = (
            _EXPERT_FREETEXT_SUGGESTIONS_EN.get(field_name) if _en else None
        ) or _EXPERT_FREETEXT_SUGGESTIONS.get(field_name)
        if expert:
            return expert
    # Solo override
    if profile and profile.get("is_solo"):
        solo = (
            _SOLO_FREETEXT_SUGGESTIONS_EN.get(field_name) if _en else None
        ) or _SOLO_FREETEXT_SUGGESTIONS.get(field_name)
        if solo:
            return solo
    # Default: branche-specific
    suggestions_map = (
        FREETEXT_SUGGESTIONS_EN.get(field_name) if _en else None
    ) or FREETEXT_SUGGESTIONS.get(field_name, {})
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
