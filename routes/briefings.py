# file: routes/briefings.py
# -*- coding: utf-8 -*-
"""
Simplified Briefing-Submit mit JWT-Email-Extraktion
- Akzeptiert JSON und multipart/form-data
- Extrahiert Email aus JWT-Token falls nicht im Body
- KEINE Mappings nötig (Fragebogen sendet bereits normalisierte Values!)
- Pflichtfeld-Validierung mit klaren 422-Fehlern
- Persistenz + Background-Analyse (lazy import), 202 Accepted
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
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

# ------------------- JWT Helper mit BESSEREM LOGGING -------------------
def get_current_user_email(request: Request) -> Optional[str]:
    """
    Extrahiert Email aus JWT-Token falls vorhanden.
    Tolerant - gibt None zurück wenn Token fehlt oder ungültig.
    WICHTIG: Loggt jetzt WARUM kein Token extrahiert werden konnte!
    """
    try:
        # Versuche JWT aus Authorization Header zu laden
        auth_header = request.headers.get("authorization", "")
        
        # DEBUG: Zeige ob Authorization-Header vorhanden ist
        if not auth_header:
            logger.warning("⚠️ Kein Authorization-Header vorhanden!")
            return None
            
        if not auth_header.startswith("Bearer "):
            logger.warning(f"⚠️ Authorization-Header hat falsches Format: '{auth_header[:20]}...'")
            return None
        
        token = auth_header.replace("Bearer ", "").strip()
        
        if not token:
            logger.warning("⚠️ Authorization-Header ist leer nach 'Bearer '")
            return None
        
        # Lazy import von JWT-Decoder
        try:
            import jwt
            import os
            
            secret = os.getenv("JWT_SECRET")
            if not secret:
                logger.error("❌ JWT_SECRET nicht gesetzt in ENV!")
                return None
            
            # Decode token
            logger.debug(f"🔍 Versuche JWT zu decoden (Token-Länge: {len(token)})")
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            
            # Email extrahieren (verschiedene mögliche Keys)
            email = (
                payload.get("email") or 
                payload.get("sub") or 
                payload.get("user_email") or
                payload.get("userEmail")
            )
            
            if email:
                logger.info(f"✅ JWT-Email gefunden: {email}")
                return email
            else:
                # Zeige welche Keys im Payload sind
                available_keys = list(payload.keys())
                logger.warning(f"⚠️ JWT Token vorhanden, aber keine Email darin! Keys: {available_keys}")
                return None
                
        except jwt.ExpiredSignatureError:
            logger.warning("⚠️ JWT Token ist abgelaufen!")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"⚠️ JWT decode fehlgeschlagen: {type(e).__name__}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Unerwarteter Fehler beim JWT-Decode: {type(e).__name__}: {str(e)}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Unerwarteter Fehler in get_current_user_email: {type(e).__name__}: {str(e)}")
        return None

router = APIRouter(prefix="/briefings", tags=["briefings"])

# Pflichtfelder (mit Email)
REQUIRED_WITH_EMAIL = ("email", "branche", "unternehmensgroesse", "bundesland", "hauptleistung")

# ------------------- Utilities -------------------
def _get_value(data: Dict[str, Any], key: str) -> Any:
    """Extrahiert Wert aus data oder data['answers']"""
    if key in data and data[key]:
        return data[key]
    if isinstance(data.get("answers"), dict) and key in data["answers"]:
        return data["answers"][key]
    return None

def _extract_fields(data: Dict[str, Any], jwt_email: Optional[str] = None) -> Dict[str, Any]:
    """
    Extrahiert die wichtigen Felder aus dem Request.
    Nutzt jwt_email als Fallback wenn email nicht im Body.
    KEINE Normalisierung nötig - Fragebogen sendet bereits normalisierte Values!
    """
    out = dict(data or {})
    
    # Extrahiere Werte aus beiden möglichen Positionen
    email = _get_value(out, "email") or jwt_email  # JWT-Email als Fallback!
    branche = _get_value(out, "branche")
    groesse = _get_value(out, "unternehmensgroesse")
    bundesland = _get_value(out, "bundesland")
    hauptleistung = _get_value(out, "hauptleistung")
    
    # Logging für Debugging
    logger.info(f"📋 Email-Quellen: Body={_get_value(out, 'email')}, JWT={jwt_email}, Final={email}")
    
    # Erstelle flache Struktur
    result = dict(out)
    result["email"] = email
    result["branche"] = branche
    result["unternehmensgroesse"] = groesse
    result["bundesland"] = bundesland
    result["hauptleistung"] = hauptleistung
    
    # Wenn answers existiert, aktualisiere auch dort
    if isinstance(result.get("answers"), dict):
        result["answers"]["email"] = email
        result["answers"]["branche"] = branche
        result["answers"]["unternehmensgroesse"] = groesse
        result["answers"]["bundesland"] = bundesland
        result["answers"]["hauptleistung"] = hauptleistung
    
    return result

def _validate_required(data: Dict[str, Any]) -> None:
    """
    Validiert Pflichtfelder.
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
        logger.warning(f"❌ Validierung fehlgeschlagen: {error_msg}")
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
        logger.info(f"✅ Analyse für Briefing {briefing_id} gestartet")
    except Exception as exc:
        logger.exception(f"❌ Analyse fehlgeschlagen für Briefing {briefing_id}: {exc}")

# ------------------- Endpoint -------------------
@router.post("/submit")
async def submit(request: Request, background: BackgroundTasks):
    """
    Briefing-Submit Endpoint mit JWT-Email-Extraktion.
    Akzeptiert JSON oder multipart/form-data.
    Extrahiert Email aus JWT-Token falls nicht im Body vorhanden.
    """
    # 0) Versuche Email aus JWT zu extrahieren
    logger.info("=" * 60)
    logger.info("🚀 Briefing-Submit gestartet")
    
    jwt_email = get_current_user_email(request)
    if jwt_email:
        logger.info(f"✅ JWT-Email erfolgreich extrahiert: {jwt_email}")
    else:
        logger.warning("⚠️ Keine JWT-Email gefunden - erwarte Email im Request-Body")
    
    # 1) Tolerant parsen
    ctype = request.headers.get("content-type", "")
    data: Dict[str, Any] = {}
    
    try:
        if "application/json" in ctype:
            data = await request.json()
            logger.info("📥 Empfangen: JSON Request")
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
            logger.info("📥 Empfangen: Form Data Request")
    except Exception as e:
        logger.error(f"❌ Request-Parsing fehlgeschlagen: {e}")
        raise HTTPException(status_code=400, detail=f"Ungültiges Request-Format: {str(e)}")
    
    # Debug-Logging für eingehende Daten (erste 500 Zeichen)
    logger.debug(f"Raw Request Data: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
    
    # 2) Felder extrahieren & validieren (mit JWT-Email als Fallback)
    try:
        extracted = _extract_fields(data, jwt_email=jwt_email)
        logger.info(f"📋 Extrahiert - Email: {extracted.get('email')}, Branche: {extracted.get('branche')}, Größe: {extracted.get('unternehmensgroesse')}")
        
        _validate_required(extracted)
        logger.info("✅ Validierung erfolgreich")
    except HTTPException:
        # Validation error - re-raise
        raise
    except Exception as e:
        logger.exception(f"❌ Extraktion/Validierung fehlgeschlagen: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Interne Verarbeitung fehlgeschlagen: {str(e)}"
        )
    
    lang = (extracted.get("lang") or 
            (extracted.get("answers", {}) if isinstance(extracted.get("answers"), dict) else {}).get("lang") or 
            "de")
    
    # 3) Persistenz
    if not SessionLocal or not Briefing:
        logger.warning("DB layer not available – dry acknowledge")
        return JSONResponse(
            {"ok": True, "id": None, "dry_run": True, "lang": lang},
            status_code=202
        )
    
    # Bereite answers-Objekt vor (entweder aus nested structure oder flach)
    answers = extracted.get("answers") if isinstance(extracted.get("answers"), dict) else extracted
    email = extracted.get("email")
    
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
        logger.exception(f"❌ Briefing-Persistenz fehlgeschlagen: {exc}")
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
