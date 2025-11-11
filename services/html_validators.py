# -*- coding: utf-8 -*-
"""
services.html_validators
------------------------
Kleine HTML‑Checks für generierte Sektionen (optional).
"""
from __future__ import annotations
import re
from typing import Tuple

def validate_quick_wins_li_count(html: str, min_li: int = 4, max_li: int = 6) -> Tuple[bool, int]:
    """Zählt <li> in der Quick‑Wins‑Liste, ignoriert andere Listen."""
    if not html:
        return False, 0
    # Suche nur in der Hauptliste (class="quick-wins-list"), fallback: global <li>-Count
    m = re.search(r'(?is)<ul[^>]*class="[^"]*quick-wins-list[^"]*"[^>]*>(.*?)</ul>', html)
    scope = m.group(1) if m else html
    count = len(re.findall(r"(?is)<li\b", scope))
    ok = (min_li <= count <= max_li)
    return ok, count
