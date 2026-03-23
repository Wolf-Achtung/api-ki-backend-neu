# -*- coding: utf-8 -*-
from __future__ import annotations
"""Robuster PDF‑Client (Gold‑Standard+)
- Fix: Header‑Typen strikt String (X‑Request‑Id etc.)
- Retries mit Exponential‑Backoff + Jitter; 429 berücksichtigt `Retry-After`.
- Liefert entweder PDF‑Bytes oder eine URL, plus klare Fehlertexte.
- PDF-SLIMDOWN v2.0: HTML/PDF Size Validation
- SPRINT G14-D: Enhanced retry categorization and metrics
"""
import json
import logging
import os
import random
import time
from typing import Any, Dict, Optional
from uuid import uuid4

import requests

log = logging.getLogger(__name__)

# PDF Author Metadata
PDF_AUTHOR = os.getenv("PDF_AUTHOR", "KI-Sicherheit.jetzt")
PDF_PRODUCER = os.getenv("PDF_PRODUCER", "KI-Sicherheit.jetzt")

PDF_SERVICE_URL = (os.getenv("PDF_SERVICE_URL") or "").rstrip("/")
PDF_TIMEOUT = int(os.getenv("PDF_TIMEOUT_MS", "90000")) / 1000.0  # Sekunden
MAX_RETRIES = int(os.getenv("PDF_MAX_RETRIES", "3"))

# PDF-SLIMDOWN v2.0: Size Validation Limits
# ENV-gesteuert: PDF_MAX_HTML_KB (Default: 1024 KB = 1 MB)
MAX_HTML_PAYLOAD_KB = int(os.getenv("PDF_MAX_HTML_KB", "1024"))  # Default: 1024 KB = 1 MB
MAX_PDF_SIZE_MB = int(os.getenv("MAX_PDF_SIZE_MB", "20"))  # 20MB default
WARN_PDF_SIZE_MB = 10  # Warning threshold at 10MB
WARN_HTML_SIZE_KB = 500  # Warning threshold at 500KB

# SPRINT G14-D: Error categorization for better diagnostics
TRANSIENT_ERRORS = {408, 429, 500, 502, 503, 504}  # Errors worth retrying
PERMANENT_ERRORS = {400, 401, 403, 404, 405}  # Don't retry these


def _as_str(v: Any, default: str = "n/a") -> str:
    # Warum: requests-Header müssen str/bytes sein.
    if v is None:
        return default
    try:
        return v if isinstance(v, str) else str(v)
    except Exception:
        return default


def _sleep_backoff(attempt: int, retry_after: Optional[str]) -> None:
    base = (2 ** (attempt - 1))
    if retry_after:
        try:
            # Retry-After kann Sekunden sein
            delay = max(float(retry_after), base)
        except Exception:
            delay = base + random.random() * 0.2
    else:
        delay = base + random.random() * 0.2
    time.sleep(delay)


def validate_html_size(html: str) -> Optional[str]:
    """
    PDF-SLIMDOWN v2.0: Validates HTML payload size before sending to PDF service.

    Args:
        html: The HTML content to validate

    Returns:
        None if valid, error message string if invalid
    """
    if not html:
        return "HTML content is empty"

    html_size_kb = len(html.encode('utf-8')) / 1024

    # Log payload size for monitoring
    log.info(
        "[PDF] HTML payload size before render: %.1fKB (limit=%dKB)",
        html_size_kb,
        MAX_HTML_PAYLOAD_KB
    )

    if html_size_kb > MAX_HTML_PAYLOAD_KB:
        error_msg = (
            f"PDF failed: HTML payload {html_size_kb:.1f}KB exceeds limit {MAX_HTML_PAYLOAD_KB}KB. "
            "Consider enabling SLIM mode or reducing content."
        )
        log.error("[PDF] %s", error_msg)
        return error_msg

    if html_size_kb > WARN_HTML_SIZE_KB:
        log.warning(
            "[PDF] HTML payload approaching limit: %.1fKB (warning threshold: %dKB, limit: %dKB)",
            html_size_kb,
            WARN_HTML_SIZE_KB,
            MAX_HTML_PAYLOAD_KB
        )

    log.debug("[PDF] HTML size validation passed: %.1fKB", html_size_kb)
    return None


def validate_pdf_size(pdf_bytes: bytes) -> Optional[str]:
    """
    PDF-SLIMDOWN v2.0: Validates generated PDF size.

    Args:
        pdf_bytes: The generated PDF bytes

    Returns:
        None if valid, error message string if invalid (but logs warning for large PDFs)
    """
    if not pdf_bytes:
        return None

    pdf_size_mb = len(pdf_bytes) / (1024 * 1024)

    if pdf_size_mb > MAX_PDF_SIZE_MB:
        log.error(
            "PDF-2 VIOLATION: Generated PDF too large: %.1fMB > %dMB limit",
            pdf_size_mb,
            MAX_PDF_SIZE_MB
        )
        return f"Generated PDF too large: {pdf_size_mb:.1f}MB exceeds {MAX_PDF_SIZE_MB}MB limit"

    if pdf_size_mb > WARN_PDF_SIZE_MB:
        log.warning(
            "PDF size warning: %.1fMB (approaching %dMB limit)",
            pdf_size_mb,
            MAX_PDF_SIZE_MB
        )

    log.debug("PDF size validation passed: %.2fMB", pdf_size_mb)
    return None


def slim_html_sections(sections: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optional Slim Mode – removes large comfort sections to reduce HTML payload size.

    This function is prepared for future use (G38+) but NOT activated by default.
    It removes sections that are nice-to-have but not essential for the core report.

    Args:
        sections: Dictionary containing HTML sections

    Returns:
        Modified sections dict with large non-essential sections removed

    Note:
        To activate, call this function before rendering HTML template.
        Example: sections = slim_html_sections(sections)
    """
    # Keys of large comfort sections that can be removed in slim mode
    SLIM_REMOVE_KEYS = [
        "NEWS_BOX_HTML",           # Market news (can be large)
        "MARKET_INSIGHTS_HTML",    # Market insights
        "KREATIV_SPECIAL_HTML",    # Creative special sections
        "RESEARCH_DETAILS_HTML",   # Detailed research output
        "RAW_RESEARCH_HTML",       # Raw research data
    ]

    removed_keys = []
    for key in SLIM_REMOVE_KEYS:
        if key in sections:
            sections.pop(key, None)
            removed_keys.append(key)

    if removed_keys:
        log.info(
            "[PDF-SLIM] Removed %d sections to reduce payload: %s",
            len(removed_keys),
            ", ".join(removed_keys)
        )

    return sections


def build_footer_template(report_id: str, report_date: str, build_id: str = "") -> str:
    """
    Build Puppeteer footerTemplate with page numbers and report metadata.

    Args:
        report_id: Report ID (e.g., "R-20251219-KND")
        report_date: Report date in DD.MM.YYYY format

    Returns:
        HTML string for footerTemplate
    """
    # Fallback for missing values
    report_id_display = report_id if report_id else "–"
    report_date_display = report_date if report_date else "–"
    build_id_display = f" · Build: {build_id}" if build_id else ""

    return f'''<div style="width:100%; font-size:9px; padding:0 14mm; box-sizing:border-box; color:#666;
            display:flex; align-items:center; justify-content:space-between;">
  <div>
    Seite <span class="pageNumber"></span> / <span class="totalPages"></span>
  </div>
  <div>
    Report-ID: {report_id_display} • {report_date_display}{build_id_display}
  </div>
</div>'''


def stamp_pdf_metadata(pdf_bytes: bytes) -> bytes:
    """Stamp author/producer metadata onto PDF bytes using PyMuPDF.

    Returns original bytes unchanged if PyMuPDF is not available or stamping fails.
    """
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        doc.set_metadata({
            "author": PDF_AUTHOR,
            "producer": PDF_PRODUCER,
        })
        stamped: bytes = doc.tobytes()
        doc.close()
        return stamped
    except ImportError:
        log.debug("[PDF] PyMuPDF not available — skipping metadata stamp")
        return pdf_bytes
    except Exception as e:
        log.warning("[PDF] Failed to stamp PDF metadata: %s", e)
        return pdf_bytes


def render_pdf_from_html(
    html: str,
    meta: Optional[Dict[str, Any]] = None,
    pdf_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Render HTML to PDF via PDF service.

    SPRINT G14-D: Enhanced with error categorization and retry metrics.
    Footer Support: Added pdf_options parameter for Puppeteer page.pdf() settings.

    Args:
        html: HTML content to render
        meta: Optional metadata dict
        pdf_options: Optional PDF rendering options (footerTemplate, headerTemplate,
                     displayHeaderFooter, margin, etc.)

    Returns:
        Dict with pdf_bytes/pdf_url or error
    """
    if not PDF_SERVICE_URL:
        return {"error": "PDF_SERVICE_URL not configured"}

    # PDF-SLIMDOWN v2.0: Validate HTML payload size (PDF-1)
    html_error = validate_html_size(html)
    if html_error:
        return {"error": html_error, "validation_error": "html_size"}

    meta = meta or {}
    rid = meta.get("request_id") or meta.get("run_id") or meta.get("analysis_id") or uuid4().hex
    rid = _as_str(rid)
    url = f"{PDF_SERVICE_URL}/generate-pdf"

    # Build payload with optional PDF options
    payload: Dict[str, Any] = {"html": html, "meta": meta}

    # Add PDF options if provided (for Puppeteer page.pdf() settings)
    if pdf_options:
        payload["pdf_options"] = pdf_options
        log.debug("[PDF] Using custom PDF options: %s", list(pdf_options.keys()))
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/pdf, application/json",
        "X-Request-Id": rid,
        "X-Client-Version": "ki-backend/1 pdf-client G14",
        "User-Agent": "ki-backend/1 pdf-client",
    }

    # SPRINT G14-D: Track retry metrics
    retry_count = 0
    last_err: Optional[str] = None
    last_status: Optional[int] = None
    start_time = time.time()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log.info(
                "[PDF-G14] Calling PDF service: %s (attempt=%d/%d, timeout=%.1fs, rid=%s)",
                url,
                attempt,
                MAX_RETRIES,
                PDF_TIMEOUT,
                rid,
            )
            r = requests.post(
                url,
                headers=headers,
                data=json.dumps(payload),
                timeout=PDF_TIMEOUT,
            )
            last_status = r.status_code

            if r.ok:
                ct = (r.headers.get("content-type") or "").lower()
                if "application/pdf" in ct:
                    # PDF-SLIMDOWN v2.0: Validate generated PDF size (PDF-2)
                    pdf_error = validate_pdf_size(r.content)
                    if pdf_error:
                        return {"error": pdf_error, "validation_error": "pdf_size"}

                    elapsed = time.time() - start_time
                    log.info(
                        "[PDF-G14] PDF generated successfully: %d bytes (%.2fMB) in %.1fs, retries=%d",
                        len(r.content),
                        len(r.content) / (1024 * 1024),
                        elapsed,
                        retry_count,
                    )
                    return {
                        "pdf_bytes": stamp_pdf_metadata(r.content),
                        "pdf_url": None,
                        "retry_count": retry_count,
                        "elapsed_sec": elapsed,
                    }
                # Fallback: JSON mit URL
                try:
                    data = r.json()
                except Exception:
                    data = {}
                log.info(
                    "[PDF-G14] PDF service returned URL response (rid=%s)",
                    rid,
                )
                return {
                    "pdf_bytes": None,
                    "pdf_url": data.get("url"),
                    "meta": data,
                    "retry_count": retry_count,
                }

            # SPRINT G14-D: Error categorization
            last_err = f"{r.status_code} {r.text[:200]}"

            if r.status_code in PERMANENT_ERRORS:
                # Don't retry permanent errors
                log.error(
                    "[PDF-G14] Permanent error %d, not retrying: %s",
                    r.status_code,
                    last_err[:100],
                )
                return {
                    "error": f"PDF service returned {r.status_code}: {last_err}",
                    "status_code": r.status_code,
                    "retry_count": retry_count,
                }

            if r.status_code in TRANSIENT_ERRORS:
                retry_count += 1
                log.warning(
                    "[PDF-G14] Transient error %d, will retry (attempt %d/%d)",
                    r.status_code,
                    attempt,
                    MAX_RETRIES,
                )
                _sleep_backoff(attempt, r.headers.get("Retry-After"))
                continue

            # Unknown error - treat as transient
            retry_count += 1
            _sleep_backoff(attempt, None)
            continue

        except requests.exceptions.Timeout as exc:
            retry_count += 1
            last_err = f"Timeout after {PDF_TIMEOUT}s"
            log.warning(
                "[PDF-G14] Timeout on attempt %d/%d: %s",
                attempt,
                MAX_RETRIES,
                exc,
            )
            _sleep_backoff(attempt, None)
            continue

        except requests.exceptions.ConnectionError as exc:
            retry_count += 1
            last_err = f"Connection error: {exc}"
            log.warning(
                "[PDF-G14] Connection error on attempt %d/%d: %s",
                attempt,
                MAX_RETRIES,
                exc,
            )
            _sleep_backoff(attempt, None)
            continue

        except Exception as exc:
            retry_count += 1
            last_err = str(exc)
            log.error(
                "[PDF-G14] Unexpected error on attempt %d/%d: %s",
                attempt,
                MAX_RETRIES,
                exc,
            )
            _sleep_backoff(attempt, None)
            continue

    elapsed = time.time() - start_time
    return {
        "error": f"PDF service failed after {MAX_RETRIES} attempts: {last_err}",
        "retry_count": retry_count,
        "last_status": last_status,
        "elapsed_sec": elapsed,
    }
