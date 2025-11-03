# -*- coding: utf-8 -*-
from __future__ import annotations
"""Robuster PDF‑Client mit Backoff/Timeout & sauberen Headern.
Fix: X-Request-Id immer als str; prefer run_id/request_id."""
import json
import logging
import os
import random
import time
from typing import Any, Dict, Optional
from uuid import uuid4

import requests

log = logging.getLogger(__name__)

PDF_SERVICE_URL = (os.getenv("PDF_SERVICE_URL") or "").rstrip("/")
PDF_TIMEOUT = int(os.getenv("PDF_TIMEOUT_MS", "90000")) / 1000.0  # Sekunden
MAX_RETRIES = 3

def _as_str(v: Any, default: str = "n/a") -> str:
    """Warum: requests erfordert Header-Werte als str/bytes."""
    if v is None:
        return default
    try:
        return v if isinstance(v, str) else str(v)
    except Exception:
        return default

def render_pdf_from_html(html: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not PDF_SERVICE_URL:
        return {"error": "PDF_SERVICE_URL not configured"}
    meta = meta or {}
    # Bevorzugt stringbasierte Korrelations-ID
    rid = meta.get("request_id") or meta.get("run_id") or meta.get("analysis_id") or uuid4().hex
    rid = _as_str(rid)
    url = f"{PDF_SERVICE_URL}/generate-pdf"

    payload = {"html": html, "meta": meta}
    headers = {
        "Content-Type": "application/json",
        "X-Request-Id": rid,                  # Fix: sicher als str
        "User-Agent": "ki-backend/1 pdf-client",
    }

    last_err: Optional[str] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log.info("services.pdf_client: Calling PDF service: %s (timeout=%.1fs, rid=%s)", url, PDF_TIMEOUT, rid)
            r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=PDF_TIMEOUT)
            if r.ok:
                ct = (r.headers.get("content-type") or "").lower()
                if "application/pdf" in ct:
                    log.info("services.pdf_client: PDF generated successfully: %s bytes", len(r.content))
                    return {"pdf_bytes": r.content, "pdf_url": None}
                # Fallback: JSON mit URL
                try:
                    data = r.json()
                except Exception:
                    data = {}
                log.info("services.pdf_client: PDF service returned URL response (rid=%s)", rid)
                return {"pdf_bytes": None, "pdf_url": data.get("url"), "meta": data}
            last_err = f"{r.status_code} {r.text[:200]}"
        except Exception as exc:
            last_err = str(exc)
        # Exponentielles Backoff + Jitter
        time.sleep((2 ** (attempt - 1)) + random.random() * 0.2)

    return {"error": f"PDF service failed after {MAX_RETRIES} attempts: {last_err}"}