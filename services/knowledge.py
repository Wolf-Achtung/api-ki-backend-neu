# -*- coding: utf-8 -*-
"""services.knowledge — Drop-in HTML partial loader (safe-mode)
This module provides a single helper used by gpt_analyze to embed curated HTML
partials into the PDF report. If your project already has services/knowledge.py,
you can SKIP this file or merge the 'load_html_partial' function.

Functions
---------
load_html_partial(path: str) -> str | None
    Reads an HTML file (UTF‑8). Returns sanitized string (very light) or None.
"""
from __future__ import annotations

import os
import re
from typing import Optional

def load_html_partial(path: str) -> Optional[str]:
    path = path.strip()
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            html = f.read()
        # remove stray <script> blocks for safety in PDF context
        html = re.sub(r'<\s*script[^>]*>.*?<\s*/\s*script\s*>', '', html, flags=re.I|re.S)
        return html.strip()
    except Exception:
        return None
