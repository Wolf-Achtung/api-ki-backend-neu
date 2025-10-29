# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, Dict, Any

def items_to_html(items: List[Dict[str, Any]], title: str | None = None) -> str:
    if not items:
        return "<p>Keine aktuellen Einträge gefunden.</p>"
    rows = []
    for it in items:
        title = (it.get("title") or it.get("url") or "").strip()
        url = (it.get("url") or "").strip()
        snippet = (it.get("snippet") or "").strip()
        row = f'<li><a href="{url}" rel="noopener" target="_blank">{title}</a><br><span style="font-size:12px;color:#5b6b7a">{snippet}</span></li>'
        rows.append(row)
    return "<ul>" + "\n".join(rows) + "</ul>"
