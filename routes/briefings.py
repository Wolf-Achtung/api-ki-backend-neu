# file: routes/briefings.py
# -*- coding: utf-8 -*-
"""
Gold-Standard+ Briefing-Submit (vollständig)
- Akzeptiert JSON und multipart/form-data
- Eingebauter Label-Normalizer (Branche/Unternehmensgröße/Bundesland)
- Pflichtfeld-Validierung mit klaren 422-Fehlern
- Persistenz + Background-Analyse (lazy import), 202 Accepted
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Body, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field

logger = logging.getLogger("briefings")
logger.setLevel(logging.INFO)

# ------------------- optionale DB-Imports (tolerant) -------------------
SessionLocal = None
Briefing = None
try:
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
    except Exception:
        pass

router = APIRouter(prefix="/briefings", tags=["briefings"])

# ------------------- Mapping-Tabellen -------------------
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

# ------------------- Utilities -------------------
def _slug(s: Any) -> str:
    if s is None:
        return ""
    return " ".join(str(s).strip().lower().replace("_", " ").split())

def _normalize(data: Dict[str, Any]) -> Dict[str, Any]:
    """Akzeptiert UI-Labels oder Slugs und liefert kanonische Werte zurück."""
    out = dict(data or {})
    base = out.get("answers") if isinstance(out.get("answers"), dict) else out

    email = base.get("email") or out.get("email")
    b = _slug(base.get("branche") or out.get("branche"))
    s = _slug(base.get("unternehmensgroesse") or out.get("unternehmensgroesse"))
    bl = _slug(base.get("bundesland") or out.get("bundesland"))
    hl = (base.get("hauptleistung") or out.get("hauptleistung") or "").strip()

    canon_b = BRANCH_MAP.get(b, base.get("branche") or out.get("branche"))
    canon_s = SIZE_MAP.get(s, base.get("unternehmensgroesse") or out.get("unternehmensgroesse"))
    canon_bl = BUNDESLAND_MAP.get(bl, base.get("bundesland") or out.get("bundesland"))

    def put(k, v):
        if isinstance(out.get("answers"), dict):
            out["answers"][k] = v
        out[k] = v

    put("email", email)
    put("branche", canon_b)
    put("unternehmensgroesse", canon_s)
    put("bundesland", canon_bl)
    put("hauptleistung", hl)

    return out

def _validate_required(data: Dict[str, Any]) -> None:
    miss = [k for k in REQUIRED if not (data.get(k) or (isinstance(data.get("answers"), dict) and data["answers"].get(k)))]
    if miss:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Fehlende/ungültige Felder: {', '.join(miss)}")

def _trigger_analysis(briefing_id: int, email: Optional[str]) -> None:
    """Lazy import, damit fehlende Analyse-Module den Submit nicht blockieren."""
    try:
        from gpt_analyze import run_analysis_for_briefing  # type: ignore
        run_analysis_for_briefing(briefing_id=briefing_id, email=email)
    except Exception as exc:  # pragma: no cover
        logger.exception("analysis failed: %s", exc)

# ------------------- Endpoint -------------------
@router.post("/submit")
async def submit(request: Request, background: BackgroundTasks):
    # 1) Tolerant parsen
    ctype = request.headers.get("content-type", "")
    data: Dict[str, Any] = {}
    if "application/json" in ctype:
        try:
            data = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Ungültiges JSON")
    else:
        form = await request.form()
        for k, v in form.multi_items():
            data[k] = v
        if isinstance(data.get("answers"), str):
            try:
                data["answers"] = json.loads(data["answers"])
            except Exception:
                pass

    # 2) Normalisieren & validieren
    normalized = _normalize(data)
    _validate_required(normalized)
    lang = (normalized.get("lang") or (normalized.get("answers") or {}).get("lang") or "de")

    # 3) Persistenz
    if not SessionLocal or not Briefing:
        logger.warning("DB layer not available – dry acknowledge")
        return JSONResponse({"ok": True, "id": None, "dry_run": True, "lang": lang}, status_code=202)

    answers = normalized.get("answers") if isinstance(normalized.get("answers"), dict) else normalized
    email = normalized.get("email")

    db = SessionLocal()
    try:
        obj = Briefing(answers=answers, lang=lang, email=email)
        db.add(obj); db.commit(); db.refresh(obj)

        # 4) Analyse asynchron starten
        background.add_task(_trigger_analysis, briefing_id=obj.id, email=email)

        return JSONResponse({"ok": True, "id": obj.id, "lang": lang}, status_code=202)
    except Exception as exc:
        logger.exception("briefing persist failed: %s", exc)
        raise HTTPException(status_code=500, detail="Persistenz fehlgeschlagen")
    finally:
        try:
            db.close()
        except Exception:
            pass
