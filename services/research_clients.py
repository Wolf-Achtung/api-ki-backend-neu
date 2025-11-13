# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
import html, json, os

@dataclass
class Tool:
    title: str
    url: str
    category: str = "General"
    note: str = ""

def _e(s: str) -> str:
    return html.escape(str(s or ""), quote=True)

def get_tools_for(answers: Dict[str, Any]) -> List[Tool]:
    branche = (answers.get("BRANCHE_LABEL") or answers.get("branche") or "").lower()
    size = (answers.get("UNTERNEHMENSGROESSE_LABEL") or answers.get("unternehmensgroesse") or "").lower()
    tools: List[Tool] = [
        Tool("Microsoft 365 Copilot", "https://www.microsoft.com/microsoft-copilot", "Produktivität"),
        Tool("Notion AI", "https://www.notion.so/product/ai", "Wissensarbeit"),
        Tool("OpenAI GPT‑4o", "https://openai.com", "LLM"),
        Tool("Hugging Face", "https://huggingface.co", "Open‑Source/Models"),
        Tool("Make.com", "https://www.make.com", "Automatisierung"),
    ]
    if "marketing" in branche:
        tools.insert(0, Tool("Jasper", "https://www.jasper.ai", "Marketing"))
    if any(k in branche for k in ("industrie","produktion")):
        tools.insert(0, Tool("Azure Cognitive Search", "https://azure.microsoft.com/services/search/", "RAG"))
    if "solo" in size or "freiberuf" in size:
        tools.append(Tool("Tally Forms", "https://tally.so", "Formulare"))
    else:
        tools.append(Tool("Typeform", "https://www.typeform.com", "Formulare"))
    return tools

def tools_table_html(tools: List[Tool]) -> str:
    if not tools:
        return "<p class='small muted'>Keine passenden Tools gefunden.</p>"
    rows = []
    for t in tools:
        rows.append(f"<tr><td><strong>{_e(t.title)}</strong></td><td><a href='{_e(t.url)}'>{_e(t.url)}</a></td><td>{_e(t.category)}</td><td>{_e(t.note)}</td></tr>")
    return ("<table class='table'><thead><tr><th>Tool</th><th>Link</th><th>Kategorie</th><th>Hinweis</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>")

def load_funding_programs(path: str = "data/funding_programs.json"):
    for p in (path, os.path.join('/mnt/data', 'funding_programs.json')):
        try:
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)
                    if isinstance(data, list):
                        return data
        except Exception:
            pass
    return []

def funding_table_html(programs):
    if not programs:
        return "<p class='small muted'>Keine Förderprogramme gefunden.</p>"
    rows = []
    for p in programs[:20]:
        title = _e(p.get('title'))
        url = _e(p.get('url'))
        typ = _e(p.get('type','Förderung'))
        region = _e(p.get('region','DE/EU'))
        rows.append(f"<tr><td><strong>{title}</strong></td><td>{typ}</td><td>{region}</td><td><a href='{url}'>{url}</a></td></tr>")
    return ("<table class='table'><thead><tr><th>Programm</th><th>Typ</th><th>Region</th><th>Link</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>")
