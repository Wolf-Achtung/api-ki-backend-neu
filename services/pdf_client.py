# file: services/pdf_client.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Lightweight HTML→PDF Client (idempotent; robust headers)"""
import os
import logging
import uuid
from typing import Any, Dict, Optional

import requests

log = logging.getLogger("services.pdf_client")

PDF_SERVICE_URL = os.getenv("PDF_SERVICE_URL", "")
TIMEOUT_SEC = float(int(os.getenv("PDF_TIMEOUT_MS", "90000")) / 1000.0)

def _headers(run_id: Optional[str] = None) -> Dict[str, str]:
    rid = (run_id or uuid.uuid4().hex[:8])
    return {
        "User-Agent": "KI-Report-PDFClient/1.1",
        "X-Request-Id": str(rid),   # WICHTIG: immer str (Bugfix)
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
    }

def render_pdf_from_html(html: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Rendert HTML zu PDF über den externen Service.
    Gibt {pdf_bytes?, pdf_url?, error?} zurück.
    """
    try:
        if not PDF_SERVICE_URL:
            return {"error": "PDF_SERVICE_URL not configured"}
        payload = {"html": html, "meta": meta or {}}
        resp = requests.post(f"{PDF_SERVICE_URL}/generate-pdf", json=payload, headers=_headers(), timeout=TIMEOUT_SEC)
        resp.raise_for_status()
        data = resp.json() if resp.headers.get("content-type","" ).startswith("application/json") else {}
        # Pass‑through: Service kann bytes oder URL liefern
        return {
            "pdf_url": data.get("pdf_url"),
            "pdf_bytes": bytes.fromhex(data["pdf_hex"]) if isinstance(data.get("pdf_hex"), str) else None,
            "error": data.get("error"),
        }
    except Exception as exc:
        log.error("PDF client error: %s", exc)
        return {"error": str(exc)}
