# file: services/pdf_client.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Robuster PDF‑Client mit Backoff/Timeouts.
Warum: Stabilität ggü. Transienten im externen PDF‑Service."""
import os, time, json, random
from typing import Any, Dict, Optional
import requests

PDF_SERVICE_URL = (os.getenv("PDF_SERVICE_URL") or "https://make-ki-pdfservice-production.up.railway.app").rstrip("/")
PDF_TIMEOUT = int(os.getenv("PDF_TIMEOUT_MS", "90000")) / 1000.0  # s
MAX_RETRIES = 3

def render_pdf_from_html(html: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not PDF_SERVICE_URL:
        return {"error": "PDF_SERVICE_URL not configured"}
    url = f"{PDF_SERVICE_URL}/generate-pdf"
    payload = {"html": html, "meta": meta or {}}
    headers = {"Content-Type": "application/json", "X-Request-Id": payload["meta"].get("analysis_id","n/a")}
    last_err = None
    for attempt in range(1, MAX_RETRIES+1):
        try:
            r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=PDF_TIMEOUT)
            if r.ok:
                ct = (r.headers.get("content-type") or "").lower()
                if "application/pdf" in ct:
                    return {"pdf_bytes": r.content, "pdf_url": None}
                try:
                    data = r.json()
                except Exception:
                    data = {}
                return {"pdf_bytes": None, "pdf_url": data.get("url"), "meta": data}
            last_err = f"{r.status_code} {r.text[:200]}"
        except Exception as exc:
            last_err = str(exc)
        # exponentielles Backoff mit Jitter
        time.sleep((2 ** (attempt - 1)) + random.random() * 0.2)
    return {"error": f"PDF service failed after {MAX_RETRIES} attempts: {last_err}"}
