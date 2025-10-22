# -*- coding: utf-8 -*-
from __future__ import annotations
import logging, json, time, os
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timezone
import requests
from sqlalchemy.orm import Session
from sqlalchemy import select
from core.db import SessionLocal
from models import Briefing, Analysis
from settings import settings

logger = logging.getLogger(__name__)

PROMPT_PATH = os.environ.get("PROMPT_PATH", "prompts/prompt_de.md")

def _load_prompt_template() -> str:
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        # Fallback: minimal system prompt
        return ("Du bist ein erfahrener KI‑Berater für KMU. Erstelle eine klare, praxisnahe Analyse und Roadmap.\n"
                "Gib strukturierte HTML‑Abschnitte zurück (ohne <html>/<body>). Nutze die Antworten des Fragebogens.")

def _format_answers(answers: Dict[str, Any]) -> str:
    parts = []
    for k, v in answers.items():
        parts.append(f"- {k}: {json.dumps(v, ensure_ascii=False)}")
    return "\n".join(parts)

def _call_openai_chat(prompt: str) -> str:
    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set – returning fallback analysis.")
        return "<h2>Analyse (Entwicklungsmodus)</h2><p>Kein API‑Key konfiguriert. Dies ist eine Platzhalter‑Analyse.</p>"
    base = settings.OPENAI_API_BASE or "https://api.openai.com/v1"
    url = f"{base}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": settings.OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": _load_prompt_template()},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    resp = requests.post(url, headers=headers, json=body, timeout=60)
    if resp.status_code >= 400:
        raise RuntimeError(f"OpenAI error {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()
    return content

def analyze_briefing(db: Session, briefing_id: int) -> Tuple[int, str, Dict[str, Any]]:
    br = db.get(Briefing, briefing_id)
    if not br:
        raise ValueError("Briefing not found")
    prompt_user = (        "Unternehmens‑Kontext (Antworten aus dem Fragebogen):\n"
        f"{_format_answers(br.answers)}\n\n"
        "Bitte liefere eine strukturierte, handlungsorientierte Analyse mit konkreten Maßnahmen (Quick Wins, 30‑/90‑Tage‑Plan),\n"
        "gegliedert in: Zusammenfassung, Quick‑Wins, Maßnahmen nach Bereich, Tool‑Vorschläge, Förder‑/Compliance‑Hinweise (Bundesland),\n"
        "Risiken & Absicherung, Nächste Schritte. Nutze klare Zwischenüberschriften. Gebe HTML‑fragmente zurück."
    )

    html = _call_openai_chat(prompt_user)
    meta = {
        "model": settings.OPENAI_MODEL,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "briefing_id": briefing_id,
        "prompt_chars": len(prompt_user),
        "answers_keys": list(br.answers.keys()),
    }

    an = Analysis(user_id=br.user_id, briefing_id=briefing_id, html=html, meta=meta, created_at=datetime.now(timezone.utc))
    db.add(an)
    db.commit()
    db.refresh(an)
    return an.id, html, meta

def run_async(briefing_id: int, email: Optional[str] = None) -> None:
    """Background‑friendly wrapper: eigene DB‑Session, Exceptions geloggt."""
    try:
        db = SessionLocal()
        try:
            an_id, html, meta = analyze_briefing(db, briefing_id)
            logger.info("analysis created: id=%s", an_id)
            # Report‑Erstellung & E‑Mail optional über separate Endpoints/Jobs
        finally:
            db.close()
    except Exception as exc:
        logger.exception("run_async failed for briefing_id=%s: %s", briefing_id, exc)
