# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict, Optional
from fastapi import APIRouter, Body, HTTPException
import httpx
import base64

from settings import settings
from gpt_analyze import build_report

router = APIRouter()

@router.post("/report")
async def report(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Generates PDF via external PDF service.
    Accepts either ready-made HTML, or a questionnaire payload; if 'html' is absent,
    the backend will render the HTML first.
    """
    html: Optional[str] = payload.get("html")
    lang = str(payload.get("lang", "de")).lower()
    if not html:
        # Render HTML from payload
        try:
            html = build_report(payload, lang=lang)["html"]
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"HTML build failed: {exc}")

    if not settings.PDF_SERVICE_URL:
        # As fallback: return base64 to allow quick testing
        b64 = base64.b64encode(html.encode("utf-8")).decode("ascii")
        return {"ok": True, "pdf_url": None, "html_b64": b64, "note": "PDF service not configured – returning HTML base64."}

    # Call external PDF service (json post expected)
    try:
        with httpx.Client(timeout=settings.PDF_TIMEOUT_MS / 1000.0) as cli:
            r = cli.post(
                str(settings.PDF_SERVICE_URL),
                json={"html": html, "strip_scripts": True, "lang": lang},
                headers={"Content-Type": "application/json"},
            )
            r.raise_for_status()
            # Expect either JSON with url or raw pdf
            if "application/pdf" in r.headers.get("content-type", "").lower():
                # Return inline length for now
                return {"ok": True, "pdf_url": None, "pdf_bytes_len": len(r.content)}
            data = r.json()
            return {"ok": True, **data}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"PDF service error: {exc}")
