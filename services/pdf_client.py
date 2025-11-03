# file: app/services/pdf_client.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import os, logging, time
from typing import Dict, Any, Optional
import requests

log = logging.getLogger(__name__)

PDF_SERVICE_URL = os.getenv("PDF_SERVICE_URL", "")
PDF_TIMEOUT_MS = int(os.getenv("PDF_TIMEOUT_MS", "90000"))  # 90 s
_MAX_RETRIES = 2
_RETRY_STATUSES = {502, 503, 504}

def render_pdf_from_html(html: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Ruft externen PDF‑Service auf (JSON), gibt url/bytes zurück. Warum: klare Fehlerbilder & Retries."""
    if not PDF_SERVICE_URL:
        return {"pdf_url": None, "pdf_bytes": None, "error": "PDF service not configured"}
    endpoint = PDF_SERVICE_URL.rstrip("/") + "/generate-pdf"
    payload = {
        "html": html,
        "filename": f"KI-Status-Report-{(meta or {}).get('briefing_id', 'report')}.pdf",
        "maxBytes": 15 * 1024 * 1024
    }
    timeout = PDF_TIMEOUT_MS / 1000.0
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    last_err: Optional[str] = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            log.info("Calling PDF service: %s (timeout=%.1fs) [try %d]", endpoint, timeout, attempt+1)
            r = requests.post(endpoint, json=payload, headers=headers, timeout=timeout)
            if r.status_code >= 200 and r.status_code < 300:
                data = r.json() if "application/json" in (r.headers.get("Content-Type") or "") else {}
                url = data.get("url") or data.get("pdf_url")
                if url:
                    return {"pdf_url": url, "pdf_bytes": None, "error": None}
                # Fallback: Binärdaten
                if r.content and len(r.content) > 1024:
                    return {"pdf_url": None, "pdf_bytes": r.content, "error": None}
                return {"pdf_url": None, "pdf_bytes": None, "error": "empty_response"}
            # Retry bei 50x
            if r.status_code in _RETRY_STATUSES and attempt < _MAX_RETRIES:
                time.sleep(0.8 * (attempt + 1))
                continue
            last_err = f"HTTP {r.status_code}: {r.text[:200]}"
            break
        except requests.Timeout:
            if attempt < _MAX_RETRIES:
                time.sleep(0.8 * (attempt + 1))
                continue
            last_err = f"timeout_{int(timeout)}s"
        except Exception as exc:
            last_err = str(exc)
            break
    log.error("PDF generation failed: %s", last_err)
    return {"pdf_url": None, "pdf_bytes": None, "error": last_err}
