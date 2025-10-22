# -*- coding: utf-8 -*-
from __future__ import annotations
import logging
from typing import Optional, Dict, Any
import json
import base64
import requests
from settings import settings

logger = logging.getLogger(__name__)

def render_pdf_from_html(html: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Send HTML to external PDF service and return dict with keys:
    { 'pdf_bytes': bytes | None, 'pdf_url': str | None, 'error': str | None }
    """
    url = settings.PDF_SERVICE_URL
    if not url:
        # No PDF service configured – return None but not an error
        logger.warning("PDF_SERVICE_URL not configured – skipping PDF generation.")
        return {"pdf_bytes": None, "pdf_url": None, "error": None}

    try:
        payload = {"html": html, "meta": meta or {}}
        resp = requests.post(str(url), json=payload, timeout=60)
        if resp.status_code >= 400:
            return {"pdf_bytes": None, "pdf_url": None, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        # Accept either bytes (application/pdf) or JSON {pdf_base64|pdf_url}
        ctype = resp.headers.get("content-type", "").split(";")[0].strip().lower()
        if ctype == "application/pdf":
            return {"pdf_bytes": resp.content, "pdf_url": None, "error": None}
        data = resp.json()
        if isinstance(data, dict) and ("pdf_base64" in data or "pdf" in data):
            b64 = data.get("pdf_base64") or data.get("pdf")
            return {"pdf_bytes": base64.b64decode(b64), "pdf_url": data.get("url"), "error": None}
        if isinstance(data, dict) and "url" in data:
            return {"pdf_bytes": None, "pdf_url": data.get("url"), "error": None}
        return {"pdf_bytes": None, "pdf_url": None, "error": "Unexpected PDF response"}
    except Exception as exc:
        logger.exception("PDF generation failed: %s", exc)
        return {"pdf_bytes": None, "pdf_url": None, "error": str(exc)}
