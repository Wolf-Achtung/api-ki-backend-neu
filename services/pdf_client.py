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
# Optional shared secret for the PDF service. When set, it is sent as the
# X-PDF-Secret header so the service can authenticate the backend.
PDF_SHARED_SECRET = os.getenv("PDF_SHARED_SECRET", "")
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


def build_footer_template(report_id: str, report_date: str, build_id: str = "", lang: str = "de") -> str:
    """
    Build Puppeteer footerTemplate with page numbers and report metadata.

    Args:
        report_id: Report ID (e.g., "R-20251219-KND")
        report_date: Report date in DD.MM.YYYY format
        lang: Report language — "en" renders "Page x / y" (KIS-1253, Lauf 1132)

    Returns:
        HTML string for footerTemplate
    """
    # Fallback for missing values
    report_id_display = report_id if report_id else "–"
    report_date_display = report_date if report_date else "–"
    build_id_display = f" · Build: {build_id}" if build_id else ""
    page_word = "Page" if str(lang or "de").lower().startswith("en") else "Seite"

    return f'''<div style="width:100%; font-size:9px; padding:0 14mm; box-sizing:border-box; color:#666;
            display:flex; align-items:center; justify-content:space-between;">
  <div>
    {page_word} <span class="pageNumber"></span> / <span class="totalPages"></span>
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
        log.info("[PDF-META] Stamped author='%s' (%d→%d bytes)", PDF_AUTHOR, len(pdf_bytes), len(stamped))
        return stamped
    except ImportError:
        log.warning("[PDF-META] PyMuPDF (fitz) not installed — cannot stamp metadata. Install via: pip install PyMuPDF")
        return pdf_bytes
    except Exception as e:
        log.warning("[PDF-META] Failed to stamp PDF metadata: %s", e)
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

    # FIX-KIS-1027.5.1-A: Decision-Cutoff-Trace Checkpoint 7/N
    # (HTTP-payload boundary to make-ki-pdfservice — letzte Backend-Stelle
    # vor Chromium-Render). Wenn der Decision-Block hier noch 3 <li> hat,
    # liegt der Cutoff in Chromium/Puppeteer; wenn schon kuerzer, ist
    # er backend-seitig.
    try:
        import hashlib
        import re as _re
        _dec_re = _re.compile(
            r'<div\b[^>]*\bid="decision"[^>]*>.*?(?=<!--|<div\b[^>]*\bclass="section\b)',
            _re.DOTALL | _re.IGNORECASE,
        )
        _match = _dec_re.search(html or "")
        if _match:
            _target = _match.group(0)
            _li = len(_re.findall(r'<li\b', _target, _re.IGNORECASE))
            _sha = hashlib.sha256(_target.encode("utf-8", errors="replace"), usedforsecurity=False).hexdigest()[:16]
            log.info(
                "[DECISION-CUTOFF-TRACE] stage=7_pdf_client_http_send run_id=%s "
                "len=%d li=%d sha=%s mode=html",
                rid, len(_target), _li, _sha,
            )
        else:
            log.info(
                "[DECISION-CUTOFF-TRACE] stage=7_pdf_client_http_send run_id=%s "
                "NOT-FOUND mode=html",
                rid,
            )
    except Exception as _trace_err:
        log.warning(
            "[DECISION-CUTOFF-TRACE] stage=7_pdf_client_http_send run_id=%s "
            "TRACE-ERROR=%s",
            rid, _trace_err,
        )

    # [TRACE-1027.5.3] Struktur-Analyse fuer Decision- + 90-Tage-Roadmap-Block
    # unmittelbar vor pdfservice-Boundary. Hypothese (Sprint 1027.5.3 Schritt 1b):
    # Cutoff sitzt in #decision ul/ol break-inside:avoid (pdf_template_v7.html
    # Z.685-694). 1027.5-H1 hat .exec-decision-box entfreezt, aber die
    # <ul>-Ebene darunter blieb atomar. Diese Trace prueft die LLM-Content-
    # Struktur (UL-Wrapper vs. flache <li>-Liste vs. .exec-decision-box-Klasse).
    # Additiv, kein Template/CSS-Change. Wegwerf-Trace wie 1027.5.1-A.
    # Self-contained: eigener re-Import + eigener Decision-Match (Checkpoint 7
    # liegt im separaten try-Block; dessen Variablen sind nicht garantiert da).
    try:
        import json as _json
        import re as _t2_re

        def _t2_analyze_block(target: str, role: str) -> Dict[str, Any]:
            if not target:
                return {"role": role, "found": False}
            has_ul = bool(_t2_re.search(r'<ul\b[^>]*>', target, _t2_re.IGNORECASE))
            has_ol = bool(_t2_re.search(r'<ol\b[^>]*>', target, _t2_re.IGNORECASE))
            li_matches = _t2_re.findall(
                r'<li\b[^>]*>(.*?)</li>',
                target,
                _t2_re.DOTALL | _t2_re.IGNORECASE,
            )
            li_text = [
                _t2_re.sub(r'\s+', ' ', _t2_re.sub(r'<[^>]+>', '', li)).strip()
                for li in li_matches
            ]
            return {
                "role": role,
                "found": True,
                "block_len": len(target),
                "has_ul_wrapper": has_ul,
                "has_ol_wrapper": has_ol,
                "li_count": len(li_matches),
                "li_lengths": [len(t) for t in li_text],
                "first_chars_per_li": [t[:60] for t in li_text],
            }

        # Decision-Block — Selektor identisch zu Checkpoint 7
        _t2_dec_re = _t2_re.compile(
            r'<div\b[^>]*\bid="decision"[^>]*>.*?(?=<!--|<div\b[^>]*\bclass="section\b)',
            _t2_re.DOTALL | _t2_re.IGNORECASE,
        )
        _t2_dec_match = _t2_dec_re.search(html or "")
        if _t2_dec_match:
            _dec_raw = _t2_dec_match.group(0)
            _dec_struct = _t2_analyze_block(_dec_raw, "decision")
            _dec_struct["has_exec_decision_box_class"] = (
                "exec-decision-box" in _dec_raw
            )
            _dec_struct["has_decision_card_class"] = (
                "decision-card" in _dec_raw
            )
            log.info(
                "[TRACE-1027.5.3] decision_struct=%s run_id=%s",
                _json.dumps(_dec_struct, ensure_ascii=False),
                rid,
            )
        else:
            log.info(
                "[TRACE-1027.5.3] decision_struct={\"found\":false} run_id=%s",
                rid,
            )

        # 90-Tage-Roadmap-Block — <section id="roadmap-90d">...</section>.
        # Lazy-match; Annahme: LLM-Content im Wrapper enthaelt keine
        # genesteten </section>-Tags. Falls doch, faengt der except-Branch.
        _t2_rm_re = _t2_re.compile(
            r'<section\b[^>]*\bid="roadmap-90d"[^>]*>.*?</section>',
            _t2_re.DOTALL | _t2_re.IGNORECASE,
        )
        _t2_rm_match = _t2_rm_re.search(html or "")
        if _t2_rm_match:
            _rm_raw = _t2_rm_match.group(0)
            _rm_struct = _t2_analyze_block(_rm_raw, "roadmap_90d")
            _rm_struct["has_roadmap_phase_card_class"] = (
                "roadmap-phase-card" in _rm_raw
            )
            _phases = _t2_re.findall(
                r'Phase\s*\d+',
                _rm_raw,
                _t2_re.IGNORECASE,
            )
            _phases_norm = sorted({p.lower().replace(" ", "") for p in _phases})
            _rm_struct["phase_count"] = len(_phases_norm)
            # Erste 60 Zeichen je Phase-Marker (auf entgetagter Variante)
            _rm_text = _t2_re.sub(r'<[^>]+>', ' ', _rm_raw)
            _phase_snippets = _t2_re.findall(
                r'Phase\s*\d+[^\n]{0,80}',
                _rm_text,
                _t2_re.IGNORECASE,
            )
            _rm_struct["first_chars_per_phase"] = [
                _t2_re.sub(r'\s+', ' ', p).strip()[:60]
                for p in _phase_snippets[:6]
            ]
            log.info(
                "[TRACE-1027.5.3] roadmap_struct=%s run_id=%s",
                _json.dumps(_rm_struct, ensure_ascii=False),
                rid,
            )
        else:
            log.info(
                "[TRACE-1027.5.3] roadmap_struct={\"found\":false} run_id=%s",
                rid,
            )
    except Exception as _t2_err:
        log.warning(
            "[TRACE-1027.5.3] STRUCT-TRACE-ERROR=%s run_id=%s",
            _t2_err, rid,
        )
    url = f"{PDF_SERVICE_URL}/generate-pdf"

    # Build payload with optional PDF options
    payload: Dict[str, Any] = {"html": html, "meta": meta}

    # Default pagination: unless the caller explicitly configured the header/footer,
    # add a page-number footer so ALL report types (status report, strategy report,
    # potential analysis, briefing) are consistently paginated. Callers that set
    # displayHeaderFooter themselves (e.g. the status report with its own footer)
    # are left untouched.
    pdf_options = dict(pdf_options) if pdf_options else {}
    if "displayHeaderFooter" not in pdf_options:
        pdf_options["displayHeaderFooter"] = True
        pdf_options.setdefault("headerTemplate", "<div></div>")
        pdf_options.setdefault(
            "footerTemplate",
            build_footer_template(
                report_id=meta.get("report_id", "") or meta.get("display_id", ""),
                report_date=meta.get("report_date", ""),
                lang=str(meta.get("lang") or meta.get("LANG") or "de"),
            ),
        )
        _margin = dict(pdf_options.get("margin") or {})
        _margin.setdefault("top", "12mm")
        _margin.setdefault("right", "12mm")
        _margin.setdefault("bottom", "20mm")  # room for the footer
        _margin.setdefault("left", "12mm")
        pdf_options["margin"] = _margin

    # Add PDF options (for Puppeteer page.pdf() settings)
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
    if PDF_SHARED_SECRET:
        headers["X-PDF-Secret"] = PDF_SHARED_SECRET

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
