# -*- coding: utf-8 -*-
"""
routes/coach.py — Post-Report Coach chat endpoints.

Endpoints (mounted via main.py with prefix "/api"):
  POST /api/coach/init      — Check briefing + return non-sensitive metadata
  POST /api/coach/message   — Stream Opus-4.6 coach response via SSE
"""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services.coach_service import load_report_context, stream_coach_response

router = APIRouter(prefix="/coach", tags=["coach"])
log = logging.getLogger(__name__)


class CoachInitRequest(BaseModel):
    briefing_id: int


class CoachMessage(BaseModel):
    role: str
    content: str


class CoachMessageRequest(BaseModel):
    briefing_id: int
    message: str = Field(..., min_length=1, max_length=5000)
    history: list[CoachMessage] = Field(default_factory=list)


@router.post("/init")
async def coach_init(req: CoachInitRequest) -> dict[str, Any]:
    """
    Verify the briefing exists and return minimal metadata for the frontend.

    Report content is NOT returned here — it's injected server-side into the
    system prompt on /message calls only.
    """
    try:
        ctx = load_report_context(req.briefing_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        log.exception("[COACH] init failed for briefing %s", req.briefing_id)
        raise HTTPException(status_code=500, detail="coach_init_failed") from exc

    return {
        "briefing_id": req.briefing_id,
        "report_types": ctx["report_types"],
        "branche": ctx["branche"],
        "size": ctx["size"],
        "ready": True,
    }


@router.post("/message")
async def coach_message(req: CoachMessageRequest) -> StreamingResponse:
    """Stream the coach response for a single user turn."""
    briefing_id = req.briefing_id
    user_message = req.message
    history = [m.model_dump() for m in req.history]

    # Fail fast if the briefing doesn't exist — avoid opening a broken stream.
    try:
        load_report_context(briefing_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        log.exception("[COACH] context load failed for briefing %s", briefing_id)
        raise HTTPException(status_code=500, detail="coach_context_failed") from exc

    async def event_stream():
        try:
            async for chunk in stream_coach_response(
                briefing_id=briefing_id,
                user_message=user_message,
                history=history,
            ):
                if not chunk:
                    continue
                yield f"data: {json.dumps({'text': chunk}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:
            log.exception("[COACH] streaming failure")
            yield f"data: {json.dumps({'error': str(exc)[:200]}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
