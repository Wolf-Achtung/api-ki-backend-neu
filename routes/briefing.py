
# routes/briefing.py
# Robust async trigger for briefing analysis with graceful fallbacks.
# FastAPI router that does not hard-depend on gpt_analyze.run_async.

from fastapi import APIRouter, BackgroundTasks, Request
from pydantic import BaseModel
import logging

log = logging.getLogger("routes.briefing")
router = APIRouter(prefix="/api", tags=["briefing"])


class BriefingPayload(BaseModel):
    # Collect the full dynamic questionnaire without strict schema
    # to remain forward-compatible with added fields.
    email: str | None = None
    lang: str | None = "de"
    # Everything else (answers) is captured as a dict
    # by accepting arbitrary types:
    class Config:
        extra = "allow"


# Detect available analyze function(s) in gpt_analyze
AnalyzeFn = None
try:
    from gpt_analyze import run_async as AnalyzeFn  # type: ignore
except Exception as e1:
    try:
        from gpt_analyze import run as AnalyzeFn  # type: ignore
    except Exception as e2:
        try:
            from gpt_analyze import analyze as AnalyzeFn  # type: ignore
        except Exception as e3:
            log.warning("No analyze function available in gpt_analyze (run_async/run/analyze). "
                        "Falling back to 'no-op'. Details: %s | %s | %s", e1, e2, e3)
            AnalyzeFn = None


def _safe_run(payload: dict) -> None:
    if AnalyzeFn is None:
        log.info("Briefing received but no analyze function present. Skipping.")
        return
    try:
        AnalyzeFn(payload)  # run synchronously inside background task
        log.info("Background analysis finished successfully.")
    except Exception as ex:
        log.exception("Background analysis failed: %s", ex)


@router.post("/briefing_async")
async def briefing_async(data: BriefingPayload, background: BackgroundTasks):
    """Queue analysis in the background. Always returns 200 quickly.

    Frontend should display a thank-you message immediately.
    """
    try:
        background.add_task(_safe_run, data.dict())
        log.info("Queued background analysis (lang=%s, email=%s).", data.lang, data.email)
        return {"queued": True, "message": "Analysis queued"}
    except Exception as ex:
        log.exception("Analyse nicht gestartet (optional): %s", ex)
        # Keep 200 OK to avoid blocking UX; mark queued=False for monitoring
        return {"queued": False, "message": f"Analysis not started: {ex.__class__.__name__}"}
