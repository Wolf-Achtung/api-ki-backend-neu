# -*- coding: utf-8 -*-
"""
API‑Route zur Entgegennahme von KI‑Briefings.

Diese Datei ersetzt die ursprüngliche Implementierung und bringt zusätzliche
Robustheit und Validierung nach dem Gold‑Standard moderner Softwareentwicklung.

Wesentliche Verbesserungen:

* Unterstützung sowohl für flache JSON‑Payloads als auch für verschachtelte
  Strukturen mit einem ``answers``‑Schlüssel. Wenn vorhanden, wird der
  ``answers``‑Block als eigentliche Antworten verwendet, andernfalls wird
  die komplette Payload als Antworten interpretiert. Überflüssige Keys wie
  ``queue_analysis`` werden ignoriert.
* E-Mail‑Adressen können über ``email`` oder ``kontakt_email`` in der
  Payload angegeben werden. Falls weder diese noch ein JWT‑Header eine
  Adresse liefern, wird ein HTTP‑422‑Fehler ausgegeben. So wird sichergestellt,
  dass der Report immer zugestellt werden kann.
* Unternehmensnamen (Keys ``unternehmen``, ``firma``, ``company``) werden
  konsequent aus den Antworten entfernt, um die Datenschutz‑Policy zu
  erfüllen. E-Mail‑Felder werden ebenfalls aus den Antworten entfernt,
  bevor sie gespeichert werden.
* Einheitliches UTF‑8‑Encoding und klare Fehlermeldungen für ungültige
  Eingaben. JSON‑ und FormData‑Inputs werden robust geparst und validiert.
* Dry‑Run‑Unterstützung: Wird der Header ``x-dry-run`` mit ``1`` oder
  ``true`` gesendet, so wird keine Datenbankoperation ausgeführt und
  lediglich eine Bestätigungsantwort mit ``dry_run`` zurückgegeben.

Die Route akzeptiert Anfragen auf ``/api/briefings/submit`` (POST) und
kompatible FormData‑Anfragen. Sie legt ein ``Briefing`` im Datenbank‑Model
an und stößt die Hintergrundanalyse via ``gpt_analyze.run_async`` an.
"""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, UploadFile, Form
from fastapi.responses import JSONResponse

from core.db import SessionLocal  # type: ignore
from models import Briefing  # type: ignore

router = APIRouter(prefix="/api/briefings", tags=["briefings"])

_SANITIZE_KEYS = {"unternehmen", "firma", "company"}


def _coerce_json(v: Any) -> Dict[str, Any]:
    """Konvertiert Byte‑ oder String‑Inhalte in ein Wörterbuch.

    Bei Parsing‑Fehlern wird ein leeres Dict zurückgegeben. Dies dient
    insbesondere dem Parsing von multipart/form-data‑Feldern, die JSON
    enthalten könnten.
    """
    if isinstance(v, dict):
        return v
    if isinstance(v, (bytes, bytearray)):
        try:
            return json.loads(v.decode("utf-8"))
        except Exception:
            return {}
    if isinstance(v, str):
        v = v.strip()
        if not v:
            return {}
        try:
            return json.loads(v)
        except Exception:
            return {}
    return {}


def _sanitize_answers(data: Dict[str, Any]) -> Dict[str, Any]:
    """Entfernt unerwünschte Schlüssel aus den Antworten.

    Derzeit werden Unternehmensnamen (``unternehmen``, ``firma``, ``company``)
    entfernt, um die Datenschutz‑Policy zu erfüllen. Weiterhin werden die
    Felder ``email`` und ``kontakt_email`` entfernt, da sie nicht im
    Report gespeichert, sondern separat verarbeitet werden.
    """
    out = dict(data or {})
    for k in list(out.keys()):
        kl = k.lower()
        if kl in _SANITIZE_KEYS or kl in {"email", "kontakt_email"}:
            out.pop(k, None)
    return out


def _extract_user_email_from_headers(request: Request) -> str:
    """Liest eine mögliche E-Mail aus vordefinierten Headern aus.

    Frontend‑Anwendungen können eine E-Mail über verschiedene Header
    mitsenden (``x-user-email``, ``x-auth-email``, ``x-client-email``).
    Liefert den ersten Wert zurück oder einen leeren String.
    """
    for name in ("x-user-email", "x-auth-email", "x-client-email"):
        v = request.headers.get(name)
        if v:
            return v.strip()
    return ""


def _trigger_analysis_lazy(briefing_id: int, email: Optional[str]) -> None:
    """Lädt das Analysemodul nur bei Bedarf und startet die Analyse.

    Durch den Lazy‑Import wird verhindert, dass ein fehlgeschlagener Import
    des Analysemoduls beim Router‑Mounting den Serverstart blockiert.
    """
    from gpt_analyze import run_async  # type: ignore  # noqa: WPS433
    run_async(briefing_id=briefing_id, email=email)


@router.options("/submit")
async def submit_options() -> JSONResponse:
    """CORS‑Preflight: Gibt einen minimalistischen OK‑Status zurück."""
    return JSONResponse({"ok": True}, media_type="application/json; charset=utf-8")


@router.post("/submit", status_code=202)
async def submit_briefing(request: Request, background: BackgroundTasks) -> JSONResponse:
    """Erfasst ein neues Briefing und stößt die Analyse an.

    Unterstützt sowohl JSON‑Payloads als auch multipart/form-data. Die
    Antworten werden bereinigt und in der Datenbank gespeichert. Eine
    E-Mail ist erforderlich, um den Report an den Nutzer zu senden. Die
    E-Mail kann in den Feldern ``email`` oder ``kontakt_email`` übermittelt
    werden. Andernfalls wird aus den JWT‑Headern versucht, eine E-Mail zu
    extrahieren. Fehlt diese vollständig, wird ein HTTP‑422‑Fehler
    zurückgegeben.
    """
    # Dry‑Run: Keine DB‑Operationen ausführen
    if (request.headers.get("x-dry-run", "").strip().lower() in {"1", "true", "yes"}):
        return JSONResponse(
            {"ok": True, "dry_run": True, "briefing_id": -1},
            status_code=202,
            media_type="application/json; charset=utf-8",
        )

    # Bestimmen des Content‑Types
    content_type = (request.headers.get("content-type") or "").lower()
    full_payload: Dict[str, Any] = {}

    if "application/json" in content_type:
        try:
            full_payload = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")
    else:
        # multipart/form-data oder andere Formulare
        form = await request.form()
        # Wenn ein 'answers' oder 'data' Feld vorhanden ist, versuchen wir es als JSON zu parsen
        raw = form.get("answers") or form.get("data")
        if raw is not None:
            full_payload = _coerce_json(raw)
        else:
            # ansonsten aus den Formfeldern ein Dictionary bilden
            for k, v in form.multi_items():
                # UploadFile wird ignoriert, nur einfache Felder aufnehmen
                if isinstance(v, UploadFile):
                    continue
                full_payload[k] = v

    if not isinstance(full_payload, dict):
        raise HTTPException(status_code=422, detail="Body must be a JSON object or form data")

    # Determinieren, ob die eigentlichen Antworten unter 'answers' verschachtelt sind
    answers = full_payload.get("answers") if isinstance(full_payload.get("answers"), dict) else None
    if answers is not None:
        answers_dict = dict(answers)  # copy
    else:
        answers_dict = dict(full_payload)

    # Sprache übernehmen: preferiere explicit gesetztes 'lang'
    lang = (full_payload.get("lang") or answers_dict.get("lang") or "de").lower()
    answers_dict["lang"] = lang

    # Email aus Payload extrahieren (top‑level und answers)
    email = (
        full_payload.get("email")
        or full_payload.get("kontakt_email")
        or answers_dict.get("email")
        or answers_dict.get("kontakt_email")
        or _extract_user_email_from_headers(request)
        or None
    )
    if not email:
        raise HTTPException(status_code=422, detail="Missing email: please provide 'email' or 'kontakt_email'")

    # Sanitizing: Entferne unerwünschte Schlüssel aus den Antworten
    sanitized_answers = _sanitize_answers(answers_dict)

    # Briefing anlegen
    db = SessionLocal()
    try:
        briefing = Briefing(answers=sanitized_answers, lang=lang)
        db.add(briefing)
        db.commit()
        db.refresh(briefing)

        # Hintergrundanalyse starten
        background.add_task(_trigger_analysis_lazy, briefing_id=briefing.id, email=email)

        return JSONResponse(
            {"ok": True, "id": briefing.id},
            status_code=202,
            media_type="application/json; charset=utf-8",
        )
    finally:
        db.close()