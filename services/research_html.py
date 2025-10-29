# -*- coding: utf-8 -*-
from __future__ import annotations
import html
from typing import List, Dict

def items_to_html(items: List[Dict], title: str = "") -> str:
    out = []
    if title:
        out.append(f"<p><strong>{html.escape(title)}</strong></p>")
    out.append("<ul>")
    for it in items:
        t = html.escape(it.get("title","Item"))
        u = html.escape(it.get("url","#"))
        s = html.escape((it.get("summary") or "")[:180])
        out.append(f"<li><a href=\"{u}\">{t}</a><br><span class='small'>{s}</span></li>")
    out.append("</ul>")
    return "\n".join(out)
