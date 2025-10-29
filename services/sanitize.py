# -*- coding: utf-8 -*-
"""
UTF-8 & HTML-Snippet Normalizer for model outputs (removes ``` fences, fixes mojibake).
"""
from __future__ import annotations
import logging, re
from html import escape

LOGGER = logging.getLogger(__name__)

CODEFENCE_RE = re.compile(r"^```[a-zA-Z0-9]*\s*|\s*```$", re.MULTILINE)
LEADING_H1_RE = re.compile(r"^\s*<h1[^>]*>.*?</h1>\s*", re.IGNORECASE | re.DOTALL)
LEADING_HEADING_TEXT_RE = re.compile(r"^\s*(Executive\s+Summary|Quick\s+Wins|Business\s+Case.*|Risiko.*|Gamechanger).*", re.IGNORECASE)

def ensure_utf8(s: str) -> str:
    if s is None:
        return ""
    if isinstance(s, bytes):
        try:
            return s.decode("utf-8")
        except Exception:
            try:
                return s.decode("latin-1", errors="replace")
            except Exception:
                return s.decode("utf-8", errors="ignore")
    if "Ã" in s or "â" in s:
        try:
            b = s.encode("latin-1", errors="ignore")
            fixed = b.decode("utf-8", errors="ignore")
            if "Ã" not in fixed:
                return fixed
        except Exception:
            pass
    return s

def strip_codefences(html_snippet: str) -> str:
    if not html_snippet:
        return ""
    s = ensure_utf8(html_snippet)
    s = CODEFENCE_RE.sub("", s).strip()
    return s.replace("```html", "").replace("```", "").strip()

def drop_leading_heading(html_snippet: str) -> str:
    if not html_snippet:
        return ""
    s = strip_codefences(html_snippet)
    s = LEADING_H1_RE.sub("", s).strip()
    lines = s.splitlines()
    if lines and LEADING_HEADING_TEXT_RE.match(lines[0] or ""):
        lines = lines[1:]
    return "\n".join(lines).strip()

def normalize_model_html(snippet: str) -> str:
    if not snippet:
        return ""
    s = ensure_utf8(snippet)
    s = strip_codefences(s)
    s = drop_leading_heading(s)
    return s.strip()

def safe_text(s: str) -> str:
    return escape(ensure_utf8(s or ""))
