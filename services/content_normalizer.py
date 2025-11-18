# -*- coding: utf-8 -*-
from __future__ import annotations
"""
services/content_normalizer.py
Hilfsfunktionen für Report-HTML: Score-Balken, Kreativ-Tools, Tool-Stacks, Glossar.
"""
from typing import Dict, Any, List
import os, re, html, json

def _read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def _safe(s: str) -> str:
    return html.escape(s, quote=True)

# ---------------- Score-Bars (CSS-only) ----------------
def build_score_bars_html(scores: Dict[str, Any]) -> str:
    def bar_row(label: str, val: Any) -> str:
        try:
            n = max(0, min(100, int(float(val))))
        except Exception:
            n = 0
        return (
            f"<tr><td>{_safe(label)}</td>"
            f"<td style='min-width:220px'>"
            f"<div style='height:8px;border-radius:6px;background:#eef2ff;overflow:hidden'>"
            f"<i style='display:block;height:100%;width:{n}%;background:linear-gradient(90deg,#3b82f6,#2563eb)'></i>"
            f"</div>"
            f"<div style='font-size:10px;color:#475569'>{n}/100</div>"
            f"</td></tr>"
        )

    rows = "".join([
        bar_row("Governance", scores.get("governance", 0)),
        bar_row("Sicherheit", scores.get("sicherheit", 0)),
        bar_row("Wertschöpfung", scores.get("wertschoepfung", 0) or scores.get("wertschöpfung", 0)),
        bar_row("Befähigung", scores.get("befaehigung", 0) or scores.get("befähigung", 0)),
        bar_row("Gesamt", scores.get("gesamt", 0)),
    ])
    return f"<table style='width:100%;border-collapse:collapse'>{rows}</table>"

# ---------------- Kreativ-Tools (txt -> HTML) ----------------
def build_kreativ_tools_html(path: str) -> str:
    raw = _read_file(path)
    if not raw.strip():
        return "<p>(Keine Kreativ‑Tools hinterlegt)</p>"
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    items: List[str] = []
    for ln in lines:
        # erwartet: Label – URL  (oder "Label | URL")
        m = re.match(r"^\s*(.+?)\s*[–|-|\|]\s*(https?://\S+)\s*$", ln)
        if m:
            label, url = m.group(1).strip(), m.group(2).strip()
            items.append(f"<li><a href='{_safe(url)}' target='_blank' rel='noopener'>{_safe(label)}</a></li>")
        else:
            # falls keine URL erkannt wird → als Text zeigen
            items.append(f"<li>{_safe(ln)}</li>")  # type: ignore[unreachable]
    return "<ul>" + "".join(items) + "</ul>"

# ---------------- Tool-Stacks nach Branche/Größe ----------------
_DEFAULT_STACKS = {
    "common": {
        "solo": ["OpenAI/Mistral (LLM)", "Make.com oder n8n (Automation)", "DuckDB + Python", "Chroma/Qdrant (RAG‑Light)"],
        "team": ["Mistral/Claude (LLM)", "n8n self‑hosted + Redis Queue", "Qdrant + LangChain", "Grafana + Loki Logs"],
        "kmu":  ["Azure OpenAI/Microsoft 365", "Event-Driven n8n", "Qdrant/Weaviate HA", "Keycloak SSO + OPA"],
    },
    "beratung": {
        "solo": ["Fakturoid/Odoo (CRM/Abrechnung)", "Tally/Typeform → Webhook", "Notion/Confluence Wissensbasis"],
    },
    "it": {
        "team": ["Feature Flags (Unleash)", "Infra-as-Code (Terraform)"],
        "kmu":  ["Backstage Developer Portal", "SAST/DAST Pipeline"],
    },
    "gesundheit": {
        "kmu": ["FHIR-Server", "DLP/Audit Trails", "EU-Hosting"],
    },
}

def build_tool_stack_html(branche: str, size: str) -> str:
    # Externe Datei erlaubt: STARTER_STACKS_PATH (JSON)
    path = os.getenv("STARTER_STACKS_PATH", "data/starter_stacks.json")
    stacks: dict[str, Any] = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            stacks = json.load(f)
    except Exception:
        stacks = {}
    # Merge: common + branche
    b = (branche or "").strip().lower()
    s = (size or "").strip().lower()
    common = stacks.get("common", {}) if isinstance(stacks, dict) else {}
    bran = stacks.get(b, {}) if isinstance(stacks, dict) else {}
    rows: List[str] = []
    for label, items in (
        ("Common", (common.get(s) or _DEFAULT_STACKS["common"].get(s) or [])),
        (b.capitalize(), (bran.get(s) or _DEFAULT_STACKS.get(b, {}).get(s) or [])),
    ):
        if not items:
            continue
        lis = "".join(f"<li>{_safe(it)}</li>" for it in items)
        rows.append(f"<div><strong>{_safe(label)}:</strong><ul>{lis}</ul></div>")
    return "<div>" + "".join(rows) + "</div>"

# ---------------- Glossar (Markdown-light) ----------------
def load_glossary_html(path: str) -> str:
    raw = _read_file(path)
    if not raw.strip():
        return "<p>(Kein Glossar hinterlegt)</p>"
    # Minimal: Zeilen als Absätze, **fett** → <strong>
    html_lines: List[str] = []
    for ln in raw.splitlines():
        ln = ln.rstrip()
        ln = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", ln)
        if ln.strip():
            html_lines.append(f"<p>{ln}</p>")
    return "".join(html_lines)