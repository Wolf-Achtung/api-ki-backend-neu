# -*- coding: utf-8 -*-
"""
Utilities for robust UTF-8 handling and safe HTML sanitization for model snippets.
"""
from __future__ import annotations
import logging
import re
from html import escape

LOGGER = logging.getLogger(__name__)

CODEFENCE_RE = re.compile(r"^```[a-zA-Z0-9]*\s*|\s*```$", re.MULTILINE)
LEADING_H1_RE = re.compile(r"^\s*<h1[^>]*>.*?</h1>\s*", re.IGNORECASE | re.DOTALL)
LEADING_HEADING_TEXT_RE = re.compile(r"^\s*(Executive\s+Summary|Quick\s+Wins|Business\s+Case.*|Risiko.*|Gamechanger).*", re.IGNORECASE)

def ensure_utf8(s: str) -> str:
    """
    Best-effort fix for common mojibake (e.g., 'fÃ¼r' -> 'für').
    If 'Ã' sequences are present, try latin-1 roundtrip.
    """
    if s is None:
        return ""
    if isinstance(s, bytes):
        try:
            return s.decode("utf-8", errors="strict")
        except Exception:
            try:
                return s.decode("latin-1", errors="replace")
            except Exception:
                return s.decode("utf-8", errors="ignore")
    # string path
    if "Ã" in s or "â" in s:
        try:
            b = s.encode("latin-1", errors="ignore")
            fixed = b.decode("utf-8", errors="ignore")
            # if it improved, use it
            if "Ã" not in fixed:
                return fixed
        except Exception as exc:
            LOGGER.debug("latin-1 roundtrip failed: %s", exc)
    return s

def strip_codefences(html_snippet: str) -> str:
    if not html_snippet:
        return ""
    s = ensure_utf8(html_snippet)
    s = CODEFENCE_RE.sub("", s).strip()
    # common stray backticks
    s = s.replace("```html", "").replace("```", "")
    return s.strip()

def drop_leading_heading(html_snippet: str) -> str:
    """Remove an initial H1 or a plain 'Executive Summary' heading from the snippet."""
    if not html_snippet:
        return ""
    s = strip_codefences(html_snippet)
    s = LEADING_H1_RE.sub("", s).strip()
    # also remove leading raw heading text if the model emitted it
    lines = s.splitlines()
    if lines and LEADING_HEADING_TEXT_RE.match(lines[0] or ""):
        lines = lines[1:]
    return "\n".join(lines).strip()

def normalize_model_html(snippet: str) -> str:
    """
    Full normalization pipeline for model outputs used inside the PDF template.
    - Fix UTF-8 mojibake
    - Strip code fences (```html)
    - Remove duplicated headings
    - Trim whitespace
    """
    if not snippet:
        return ""
    s = ensure_utf8(snippet)
    s = strip_codefences(s)
    s = drop_leading_heading(s)
    return s.strip()

def safe_text(s: str) -> str:
    """Escape text for HTML contexts (not for snippets that are already HTML)."""
    return escape(ensure_utf8(s or ""))

__all__ = [
    "ensure_utf8",
    "strip_codefences",
    "drop_leading_heading",
    "normalize_model_html",
    "safe_text",
]
