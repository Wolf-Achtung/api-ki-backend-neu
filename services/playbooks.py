# -*- coding: utf-8 -*-
"""
services/playbooks.py
--------------------
Branchen-Snippets („Playbooks“) mit 3 Micro-Use-Cases inkl. Nutzen &
ersten Umsetzungsschritten.

Public:
    build_playbooks(answers: dict) -> str  # returns PLAYBOOKS_HTML
"""
from __future__ import annotations
from typing import Dict, List

def _ul(items: List[str]) -> str:
    return "<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>"

PLAYBOOKS = {
    "beratung": [
        ("Lead‑Qualifizierung mit RAG", _ul([
            "Website‑Anfragen automatisch clustern und scoren (Intent, Fit).",
            "Antwortvorschläge & Termine automatisch vorbereiten.",
            "CRM‑Sync inkl. Quellen‑Protokollierung (Audit‑Log)."
        ])),
        ("Report‑Factory", _ul([
            "Vorlagen‑Katalog (Jinja/Markdown) + Wissensbasis (RAG).",
            "Automatisierte Auswertung/Generierung mit Guardrails.",
            "Qualitätsprüfung (Faktencheck, Stil, DSGVO‑Checkliste)."
        ])),
        ("Meeting‑IQ & CRM‑Sync", _ul([
            "Transkription, Aktionspunkte, Risiken, Nächste Schritte.",
            "Automatische CRM‑Einträge & Aufgaben für Team.",
            "Datenschutz: Opt‑in, Speicherdauer, Löschregeln."
        ])),
    ],
    "it_software": [
        ("Developer‑Copilot On‑Prem", _ul([
            "AI‑Pairing in IDE, hausinternes RAG auf Codebase.",
            "Security‑Policies (Secrets, Lizenzen) enforced.",
            "Telemetry anonymisiert; kein Code‑Leak."
        ])),
        ("Ticket‑Triage", _ul([
            "Auto‑Kategorisierung, SLA‑Vorhersage, Priorisierung.",
            "Antwortvorschläge & Wissensartikel verlinken.",
            "Feedback‑Loop → Modellfeintuning."
        ])),
        ("Release‑Notes‑Generator", _ul([
            "Commits/PRs zusammenfassen, Stakeholder‑Versionen.",
            "Screenshots/Links automatisch einbetten.",
            "Freigabe‑Workflow (4‑Augen‑Prinzip)."
        ])),
    ],
}

def build_playbooks(answers: Dict) -> str:
    branche = (answers or {}).get("branche", "")
    blocks = PLAYBOOKS.get(branche) or PLAYBOOKS["beratung"]
    html = ""
    for title, body in blocks:
        html += f"<h4>{title}</h4>{body}"
    return html
