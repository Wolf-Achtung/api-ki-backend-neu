# file: routes/briefings.py
# -*- coding: utf-8 -*-
"""
Gold-Standard+ Briefing-Submit (JWT-Email-Extraktion)
- Akzeptiert JSON und multipart/form-data
- Extrahiert Email aus JWT-Token falls nicht im Body
- Eingebauter Label-Normalizer (Branche/Unternehmensgröße/Bundesland)
- Pflichtfeld-Validierung mit klaren 422-Fehlern
- Persistenz + Background-Analyse (lazy import), 202 Accepted
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status, Depends
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

# ------------------- JWT Helper (optional) -------------------
def get_current_user_email(request: Request) -> Optional[str]:
    """
    Extrahiert Email aus JWT-Token falls vorhanden.
    Tolerant - gibt None zurück wenn Token fehlt oder ungültig.
    """
    try:
        # Versuche JWT aus Authorization Header zu laden
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.replace("Bearer ", "")
        
        # Lazy import von JWT-Decoder
        try:
            import jwt
            import os
            
            secret = os.getenv("JWT_SECRET")
            if not secret:
                logger.warning("JWT_SECRET nicht gesetzt")
                return None
            
            # Decode token
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            
            # Email extrahieren (verschiedene mögliche Keys)
            email = (
                payload.get("email") or 
                payload.get("sub") or 
                payload.get("user_email") or
                payload.get("userEmail")
            )
            
            if email:
                logger.info(f"Email aus JWT extrahiert: {email}")
                return email
                
        except Exception as e:
            logger.debug(f"JWT decode fehlgeschlagen: {e}")
            return None
            
    except Exception:
        return None

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
    "11-100": "kmu",
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

# Email ist optional im Body (kann aus JWT kommen)
REQUIRED = ("branche", "unternehmensgroesse", "bundesland", "hauptleistung")
REQUIRED_WITH_EMAIL = ("email", "branche", "unternehmensgroesse", "bundesland", "hauptleistung")

# ------------------- Utilities -------------------
def _slug(s: Any) -> str:
    """Normalisiert String zu lowercase slug"""
    if s is None:
        return ""
    return " ".join(str(s).strip().lower().replace("_", " ").split())

def _get_value(data: Dict[str, Any], key: str) -> Any:
    """Extrahiert Wert aus data oder data['answers']"""
    if key in data and data[key]:
        return data[key]
    if isinstance(data.get("answers"), dict) and key in data["answers"]:
        return data["answers"][key]
    return None

def _normalize(data: Dict[str, Any], jwt_email: Optional[str] = None) -> Dict[str, Any]:
    """
    Akzeptiert UI-Labels oder Slugs und liefert kanonische Werte zurück.
    Erstellt flache Struktur mit allen relevanten Feldern.
    Nutzt jwt_email als Fallback wenn email nicht im Body.
    """
    out = dict(data or {})
    
    # Extrahiere Werte aus beiden möglichen Positionen
    email = _get_value(out, "email") or jwt_email  # JWT-Email als Fallback!
    branche_raw = _get_value(out, "branche")
    groesse_raw = _get_value(out, "unternehmensgroesse")
    bundesland_raw = _get_value(out, "bundesland")
    hauptleistung = _get_value(out, "hauptleistung")
    
    # Normalisiere mit Mapping-Tabellen
    branche_slug = _slug(branche_raw)
    groesse_slug = _slug(groesse_raw)
    bundesland_slug = _slug(bundesland_raw)
    
    canon_branche = BRANCH_MAP.get(branche_slug, branche_raw)
    canon_groesse = SIZE_MAP.get(groesse_slug, groesse_raw)
    canon_bundesland = BUNDESLAND_MAP.get(bundesland_slug, bundesland_raw)
    
    # Schreibe normalisierte Werte zurück (flach UND in answers)
    result = dict(out)
    result["email"] = email
    result["branche"] = canon_branche
    result["unternehmensgroesse"] = canon_groesse
    result["bundesland"] = canon_bundesland
    result["hauptleistung"] = hauptleistung
    
    # Wenn answers existiert, aktualisiere auch dort
    if isinstance(result.get("answers"), dict):
        result["answers"]["email"] = email
        result["answers"]["branche"] = canon_branche
        result["answers"]["unternehmensgroesse"] = canon_groesse
        result["answers"]["bundesland"] = canon_bundesland
        result["answers"]["hauptleistung"] = hauptleistung
    
    return result

def _validate_required(data: Dict[str, Any]) -> None:
    """
    Validiert Pflichtfelder in normalisierten Daten.
    Gibt detaillierte Fehlermeldung mit tatsächlichen Werten zurück.
    """
    missing = []
    invalid = []
    
    for key in REQUIRED_WITH_EMAIL:
        value = data.get(key)
        
        # Prüfe ob Wert existiert und nicht leer ist
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(key)
        # Zusätzliche Validierung für Email
        elif key == "email" and "@" not in str(value):
            invalid.append(f"{key}='{value}' (keine gültige Email)")
    
    if missing or invalid:
        error_parts = []
        if missing:
            error_parts.append(f"Fehlende Felder: {', '.join(missing)}")
        if invalid:
            error_parts.append(f"Ungültige Werte: {', '.join(invalid)}")
        
        error_msg = "; ".join(error_parts)
        
        # Debug-Logging
        logger.warning(f"Validierung fehlgeschlagen: {error_msg}")
        logger.debug(f"Erhaltene Daten: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg
        )

def _trigger_analysis(briefing_id: int, email: Optional[str]) -> None:
    """Lazy import, damit fehlende Analyse-Module den Submit nicht blockieren."""
    try:
        from gpt_analyze import run_analysis_for_briefing  # type: ignore
        run_analysis_for_briefing(briefing_id=briefing_id, email=email)
        logger.info(f"Analyse für Briefing {briefing_id} gestartet")
    except Exception as exc:
        logger.exception(f"Analyse fehlgeschlagen für Briefing {briefing_id}: {exc}")

# ------------------- Endpoint -------------------
@router.post("/submit")
async def submit(request: Request, background: BackgroundTasks):
    """
    Briefing-Submit Endpoint mit JWT-Email-Extraktion.
    Akzeptiert JSON oder multipart/form-data.
    Extrahiert Email aus JWT-Token falls nicht im Body vorhanden.
    """
    # 0) Versuche Email aus JWT zu extrahieren
    jwt_email = get_current_user_email(request)
    if jwt_email:
        logger.info(f"JWT-Email gefunden: {jwt_email}")
    else:
        logger.debug("Keine JWT-Email gefunden, erwarte Email im Body")
    
    # 1) Tolerant parsen
    ctype = request.headers.get("content-type", "")
    data: Dict[str, Any] = {}
    
    try:
        if "application/json" in ctype:
            data = await request.json()
            logger.info("Empfangen: JSON Request")
        else:
            form = await request.form()
            for k, v in form.multi_items():
                data[k] = v
            # Parse answers-JSON falls als String gesendet
            if isinstance(data.get("answers"), str):
                try:
                    data["answers"] = json.loads(data["answers"])
                except Exception as e:
                    logger.warning(f"Konnte answers-String nicht parsen: {e}")
            logger.info("Empfangen: Form Data Request")
    except Exception as e:
        logger.error(f"Request-Parsing fehlgeschlagen: {e}")
        raise HTTPException(status_code=400, detail=f"Ungültiges Request-Format: {str(e)}")
    
    # Debug-Logging für eingehende Daten
    logger.debug(f"Raw Request Data: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    # 2) Normalisieren & validieren (mit JWT-Email als Fallback)
    try:
        normalized = _normalize(data, jwt_email=jwt_email)
        logger.debug(f"Normalisierte Daten: {json.dumps(normalized, ensure_ascii=False, indent=2)}")
        
        _validate_required(normalized)
        logger.info("Validierung erfolgreich")
    except HTTPException:
        # Validation error - re-raise
        raise
    except Exception as e:
        logger.exception(f"Normalisierung/Validierung fehlgeschlagen: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Interne Verarbeitung fehlgeschlagen: {str(e)}"
        )
    
    lang = (normalized.get("lang") or 
            (normalized.get("answers", {}) if isinstance(normalized.get("answers"), dict) else {}).get("lang") or 
            "de")
    
    # 3) Persistenz
    if not SessionLocal or not Briefing:
        logger.warning("DB layer not available – dry acknowledge")
        return JSONResponse(
            {"ok": True, "id": None, "dry_run": True, "lang": lang},
            status_code=202
        )
    
    # Bereite answers-Objekt vor (entweder aus nested structure oder flach)
    answers = normalized.get("answers") if isinstance(normalized.get("answers"), dict) else normalized
    email = normalized.get("email")
    
    db = SessionLocal()
    try:
        obj = Briefing(answers=answers, lang=lang, email=email)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        
        logger.info(f"✅ Briefing {obj.id} erfolgreich gespeichert für {email}")
        
        # 4) Analyse asynchron starten
        background.add_task(_trigger_analysis, briefing_id=obj.id, email=email)
        
        return JSONResponse(
            {"ok": True, "id": obj.id, "lang": lang},
            status_code=202
        )
    except Exception as exc:
        logger.exception(f"Briefing-Persistenz fehlgeschlagen: {exc}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Datenbank-Fehler: {str(exc)}"
        )
    finally:
        try:
            db.close()
        except Exception:
            pass
