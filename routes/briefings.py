# -*- coding: utf-8 -*-
from __future__ import annotations

"""
routes/briefings.py
-------------------
Gold-Standard+ Briefing-Endpoint mit robuster Normalisierung und tolerantem Parsing.

- POST /api/briefings/submit  → 202 Accepted (async Analyse)
- Akzeptiert JSON und multipart/form-data
- Normalisiert UI-Labels (Branche/Größe/Bundesland) → Slugs
- Sanitiert PII in den gespeicherten Antworten
- Dry-Run via Header "x-dry-run: 1"
- Sauberes Logging, klare Fehler

Abhängigkeiten, die im Projekt erwartet werden:
- db.SessionLocal  (SQLAlchemy Session)
- models.Briefing  (SQLAlchemy Model mit Feldern: id:int, answers:JSON, lang:str, email:str optional)
- gpt_analyze.run_analysis_for_briefing(briefing_id:int, email:str|None)
"""

import json
import logging
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Body, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field

logger = logging.getLogger("briefings")
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# DB-Anbindung (tolerant importieren)
# ---------------------------------------------------------------------------
SessionLocal = None
Briefing = None

try:  # project-local imports
    from db import SessionLocal as _SessionLocal
    from models import Briefing as _Briefing
    SessionLocal = _SessionLocal
    Briefing = _Briefing
except Exception:
    try:
        from .db import SessionLocal as _SessionLocal  # type: ignore
        from .models import Briefing as _Briefing      # type: ignore
        SessionLocal = _SessionLocal
        Briefing = _Briefing
    except Exception as exc:  # pragma: no cover
        logger.warning("DB modules not found at import time: %s", exc)

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/briefings", tags=["briefings"])

# ---------------------------------------------------------------------------
# Normalisierung & Validierung
# ---------------------------------------------------------------------------
BRANCH_MAP = {
    "beratung & dienstleistungen": "beratung",
    "beratung": "beratung",
    "it & software": "it",
    "it": "it",
    "finanzen & versicherungen": "finanzen",
    "finanzen": "finanzen",
    "handel & e-commerce": "handel",
    "e-commerce": "handel",
    "handel": "handel",
    "bildung": "bildung",
    "verwaltung": "verwaltung",
    "gesundheit & pflege": "gesundheit",
    "gesundheit": "gesundheit",
    "bauwesen & architektur": "bau",
    "bau": "bau",
    "medien & kreativwirtschaft": "medien",
    "medien": "medien",
    "industrie & produktion": "industrie",
    "industrie": "industrie",
    "transport & logistik": "logistik",
    "logistik": "logistik",
}

SIZE_MAP = {
    "1 (solo-selbstständig/freiberuflich)": "solo",
    "solo": "solo",
    "2–10 (kleines team)": "team",
    "2-10 (kleines team)": "team",
    "2-10": "team",
    "team": "team",
    "11–100 (kmu)": "kmu",
    "11-100 (kmu)": "kmu",
    "kmu": "kmu",
}

BUNDESLAND_MAP = {
    "berlin": "BE", "be": "BE",
    "bayern": "BY", "by": "BY",
    "baden-württemberg": "BW", "bw": "BW",
    "niedersachsen": "NI", "ni": "NI",
    "hessen": "HE", "he": "HE",
    "hamburg": "HH", "hh": "HH",
    "bremen": "HB", "hb": "HB",
    "sachsen": "SN", "sn": "SN",
    "sachsen-anhalt": "ST", "st": "ST",
    "thüringen": "TH", "th": "TH",
    "mecklenburg-vorpommern": "MV", "mv": "MV",
    "schleswig-holstein": "SH", "sh": "SH",
    "rheinland-pfalz": "RP", "rp": "RP",
    "saarland": "SL", "sl": "SL",
    "nordrhein-westfalen": "NW", "nrw": "NW", "nw": "NW",
    "brandenburg": "BB", "bb": "BB",
}

REQUIRED = ("email", "branche", "unternehmensgroesse", "bundesland", "hauptleistung")

def _slugify(s: Any) -> str:
    if s is None:
        return ""
    return " ".join(str(s).strip().lower().replace("_", " ").split())

def _normalize_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """Akzeptiert UI-Labels oder Slugs und liefert kanonische Werte."""
    out = dict(data or {})
    # answers verschachtelt?
    if "answers" in out and isinstance(out["answers"], dict):
        base = out["answers"]
    else:
        base = out

    # Pflichtfelder vorab zusammenziehen
    email = base.get("email") or out.get("email")
    branche = base.get("branche") or out.get("branche")
    size = base.get("unternehmensgroesse") or out.get("unternehmensgroesse")
    bundesland = base.get("bundesland") or out.get("bundesland")
    hauptleistung = base.get("hauptleistung") or out.get("hauptleistung")

    # Slugify
    b = _slugify(branche)
    s = _slugify(size)
    bl = _slugify(bundesland)

    canon_branche = BRANCH_MAP.get(b, branche if isinstance(branche, str) else "")
    canon_size = SIZE_MAP.get(s, size if isinstance(size, str) else "")
    canon_state = BUNDESLAND_MAP.get(bl, bundesland if isinstance(bundesland, str) else "")

    # zurückschreiben (in answers, falls vorhanden)
    def put(k, v):
        if "answers" in out and isinstance(out["answers"], dict):
            out["answers"][k] = v
        out[k] = v

    put("email", email)
    put("branche", canon_branche)
    put("unternehmensgroesse", canon_size)
    put("bundesland", canon_state)
    put("hauptleistung", (hauptleistung or "").strip())

    # Sanitize: Namen/E-Mail aus Textfeldern entfernen (PII minimieren)
    def _sanitize_text(val: Any) -> Any:
        if not isinstance(val, str):
            return val
        t = val.strip()
        # einfache PII-Filter
        t = t.replace(out.get("email","") or "", "[geschwärzt]")
        return t

    # alle string-Felder leicht bereinigen
    for k, v in list(out.items()):
        if isinstance(v, str):
            out[k] = _sanitize_text(v)

    if "answers" in out and isinstance(out["answers"], dict):
        for k, v in list(out["answers"].items()):
            if isinstance(v, str):
                out["answers"][k] = _sanitize_text(v)

    return out

def _validate_required(data: Dict[str, Any]) -> None:
    errs = []
    for key in REQUIRED:
        if not (data.get(key) or (isinstance(data.get("answers"), dict) and data["answers"].get(key))):
            errs.append(key)
    if errs:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Fehlende oder ungültige Felder: {', '.join(errs)}"
        )

# ---------------------------------------------------------------------------
# Pydantic-Minimalmodell für reine JSON-Bodys (optional)
# ---------------------------------------------------------------------------
class BriefingIn(BaseModel):
    email: EmailStr
    branche: str
    unternehmensgroesse: str
    bundesland: str
    hauptleistung: str
    answers: Optional[Dict[str, Any]] = None
    lang: Optional[str] = Field(default="de")

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _trigger_analysis_lazy(briefing_id: int, email: Optional[str]) -> None:
    """Import on demand, damit Importfehler im Analysepfad nicht den Request abbrechen."""
    try:
        from gpt_analyze import run_analysis_for_briefing  # type: ignore
        run_analysis_for_briefing(briefing_id=briefing_id, email=email)
    except Exception as exc:  # pragma: no cover
        logger.exception("analysis task failed: %s", exc)

# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@router.post("/submit")
async def submit_briefing(request: Request, background: BackgroundTasks):
    # 1) Request-Body tolerant parsen (JSON oder form-data)
    content_type = request.headers.get("content-type","")
    data: Dict[str, Any] = {}
    if "application/json" in content_type:
        try:
            data = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Ungültiges JSON")
    else:
        # form-data / x-www-form-urlencoded
        form = await request.form()
        for k, v in form.multi_items():
            data[k] = v

        # verschachtelte answers (als JSON-String)?
        if "answers" in data and isinstance(data["answers"], str):
            try:
                data["answers"] = json.loads(data["answers"])
            except Exception:
                pass

    dry_run = request.headers.get("x-dry-run", "0") in ("1","true","yes")
    lang = data.get("lang") or (data.get("answers") or {}).get("lang") or "de"

    # 2) Normalisieren & validieren
    normalized = _normalize_payload(data)
    _validate_required(normalized)

    # 3) DB-Speichern
    if not SessionLocal or not Briefing:
        # Keine DB? -> Dry-Acknowledge (für lokale Tests)
        logger.warning("Session/Model not available – dry acknowledge")
        if not dry_run:
            logger.warning("No DB layer configured; skipping persistence")
        return JSONResponse({"ok": True, "id": None, "dry_run": True}, status_code=202)

    answers = normalized.get("answers") if isinstance(normalized.get("answers"), dict) else normalized
    email = normalized.get("email")
    sanitized_answers = dict(answers or {})
    # sensible PII herausnehmen
    sanitized_answers.pop("email", None)

    db = SessionLocal()
    try:
        obj = Briefing(answers=sanitized_answers, lang=lang, email=email)
        db.add(obj)
        db.commit()
        db.refresh(obj)

        if not dry_run:
            background.add_task(_trigger_analysis_lazy, briefing_id=obj.id, email=email)

        return JSONResponse({"ok": True, "id": obj.id, "lang": lang}, status_code=202)
    except Exception as exc:
        logger.exception("briefing persist failed: %s", exc)
        raise HTTPException(status_code=500, detail="Persistenz fehlgeschlagen")
    finally:
        try:
            db.close()
        except Exception:
            pass