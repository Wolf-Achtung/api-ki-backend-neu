
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

# Projektabhängige Helfer
from core.db import get_db  # type: ignore

try:
    # wenn vorhanden, nutzen wir die bereits gelieferten Security‑Helfer
    from services.auth import get_current_user, SimpleUser  # type: ignore
except Exception:
    # Minimal-Fallback nur für lokale Tests (nicht produktiv); erzwingt Header X-User-Email
    from fastapi import Header

    class SimpleUser(dict):  # pragma: no cover
        pass

    def get_current_user(x_user_email: Optional[str] = Header(None)) -> SimpleUser:  # pragma: no cover
        if not x_user_email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication_required")
        return SimpleUser(id=None, email=x_user_email.strip().lower(), role="user")


log = logging.getLogger("routes.briefings")
router = APIRouter(tags=["briefings"])


# --------- Hilfsfunktionen (Schema-robust mit information_schema) ----------------

def _cols(db: Session, table: str) -> set[str]:
    rows = db.execute(
        text("SELECT column_name FROM information_schema.columns WHERE table_name=:t"),
        {"t": table},
    ).fetchall()
    return {r[0] for r in rows}


def _now() -> datetime:
    return datetime.utcnow()


def _infer_email(data: Dict[str, Any], fallback: Optional[str]) -> Optional[str]:
    # Versucht mehrere Varianten aus dem Formular
    for key in ("email", "e_mail", "kontakt_email", "kontaktEmail", "kontakt-email"):
        v = data.get(key)
        if isinstance(v, str) and "@" in v:
            return v.strip().lower()
    if fallback and "@" in fallback:
        return fallback.strip().lower()
    return None


def _insert_or_update_draft(db: Session, table: str, email: str, payload: Dict[str, Any]) -> None:
    cols = _cols(db, table)
    if not cols:
        raise HTTPException(status_code=500, detail=f"table {table} missing")

    row: Dict[str, Any] = {}
    if "email" in cols:
        row["email"] = email
    if "payload" in cols:
        row["payload"] = json.dumps(payload)
    elif "content" in cols:
        row["content"] = json.dumps(payload)
    if "updated_at" in cols:
        row["updated_at"] = _now()
    if "created_at" in cols and "created_at" not in row:
        row["created_at"] = _now()

    # upsert per email, falls unique(email) existiert – andernfalls einfache Insert-then-Update-Strategie
    if "email" in cols:
        # try PG upsert
        try:
            db.execute(
                text(f"""
                    INSERT INTO {table} ({", ".join(row.keys())})
                    VALUES ({", ".join(f":{k}" for k in row.keys())})
                    ON CONFLICT (email) DO UPDATE SET
                        {", ".join(f"{k}=excluded.{k}" for k in row.keys() if k != "created_at")}
                """),
                row,
            )
            db.commit()
            return
        except Exception as exc:
            log.warning("upsert failed (will fallback): %s", exc)

    # Fallback: update by email else insert
    if "email" in cols:
        res = db.execute(text(f"UPDATE {table} SET "
                              + ", ".join(f"{k}=:{k}" for k in row.keys() if k != "created_at")
                              + " WHERE email=:email"), row)
        if res.rowcount and res.rowcount > 0:
            db.commit()
            return

    db.execute(
        text(f"INSERT INTO {table} ({', '.join(row.keys())}) VALUES ({', '.join(f':{k}' for k in row.keys())})"),
        row,
    )
    db.commit()


def _select_latest_draft(db: Session, table: str, email: str) -> Optional[Dict[str, Any]]:
    cols = _cols(db, table)
    if not cols:
        return None
    where = "email=:email" if "email" in cols else "TRUE"
    order = "updated_at DESC" if "updated_at" in cols else "id DESC"
    row = db.execute(text(f"SELECT * FROM {table} WHERE {where} ORDER BY {order} LIMIT 1"), {"email": email}).mappings().first()
    if not row:
        return None
    # map payload/content back to dict
    payload = None
    if "payload" in row and row["payload"] is not None:
        try:
            payload = row["payload"] if isinstance(row["payload"], dict) else json.loads(row["payload"])
        except Exception:
            payload = None
    elif "content" in row and row["content"] is not None:
        try:
            payload = row["content"] if isinstance(row["content"], dict) else json.loads(row["content"])
        except Exception:
            payload = None
    return {"id": row.get("id"), "email": row.get("email"), "payload": payload}


# ----------------------- Schemas -----------------------

class DraftPayload(BaseModel):
    data: Dict[str, Any]  # form state (Schlüssel=Feldname aus Formbuilder)
    email: Optional[str] = None  # optional Übergabe


class BriefingSubmit(BaseModel):
    data: Dict[str, Any]
    email: Optional[str] = None


# ----------------------- Endpoints ---------------------

@router.get("/briefings/draft")
def get_draft(
    request: Request,
    db: Session = Depends(get_db),
    user: SimpleUser = Depends(get_current_user),
):
    email = _infer_email({}, user.get("email"))
    email = request.query_params.get("email", email)  # erlaubt ?email=...
    if not email:
        return {"ok": True, "draft": None}

    item = _select_latest_draft(db, "briefing_drafts", email)
    return {"ok": True, "draft": item}


@router.put("/briefings/draft", status_code=200)
def put_draft(
    payload: DraftPayload,
    db: Session = Depends(get_db),
    user: SimpleUser = Depends(get_current_user),
):
    email = _infer_email(payload.data, payload.email or user.get("email"))
    if not email:
        # Draft ohne E‑Mail noch nicht speicherbar (z. B. Schritt 1). Nicht als Fehler werten.
        return {"ok": False, "skipped": True, "reason": "email_missing"}

    _insert_or_update_draft(db, "briefing_drafts", email, payload.data)
    return {"ok": True}


@router.get("/briefings/me/latest")
def get_my_latest(
    request: Request,
    db: Session = Depends(get_db),
    user: SimpleUser = Depends(get_current_user),
):
    email = _infer_email({}, user.get("email"))
    email = request.query_params.get("email", email)
    if not email:
        return {"ok": True, "briefing": None}

    # Versuche zuerst finalisierte Briefings, sonst Draft
    b_cols = _cols(db, "briefings")
    if b_cols:
        where = "email=:email" if "email" in b_cols else "TRUE"
        order = "created_at DESC" if "created_at" in b_cols else "id DESC"
        row = db.execute(text(f"SELECT * FROM briefings WHERE {where} ORDER BY {order} LIMIT 1"),
                         {"email": email}).mappings().first()
        if row:
            return {"ok": True, "briefing": {"id": row.get("id"), "email": row.get("email"),
                                             "payload": row.get("payload") or row.get("content") }}
    # Draft fallback
    return {"ok": True, "briefing": _select_latest_draft(db, "briefing_drafts", email)}


def _insert_briefing(db: Session, email: str, data: Dict[str, Any]) -> int:
    cols = _cols(db, "briefings")
    if not cols:
        # minimal fallback: schreibe in drafts und kehre id=-1 zurück
        _insert_or_update_draft(db, "briefing_drafts", email, data)
        return -1
    row: Dict[str, Any] = {}
    if "email" in cols:
        row["email"] = email
    if "payload" in cols:
        row["payload"] = json.dumps(data)
    elif "content" in cols:
        row["content"] = json.dumps(data)
    if "created_at" in cols:
        row["created_at"] = _now()
    if "updated_at" in cols:
        row["updated_at"] = _now()
    sql = text(f"INSERT INTO briefings ({', '.join(row.keys())}) "
               f"VALUES ({', '.join(f':{k}' for k in row.keys())}) "
               f"{'RETURNING id' if 'id' in cols else ''}")
    res = db.execute(sql, row)
    db.commit()
    if 'id' in cols:
        try:
            rid = res.fetchone()[0]
            return int(rid)
        except Exception:
            return -1
    return -1


def _enqueue_analysis(background: BackgroundTasks, db: Session, briefing_id: int, email: str, data: Dict[str, Any]) -> None:
    """
    Hintergrundjob: Analyse + PDF + Mail. Nutzt vorhandene Services, wenn verfügbar.
    """
    def task() -> None:
        try:
            import logging as _logging
            _lg = _logging.getLogger("analyze.task")
            _lg.info("analysis started for %s", email)

            # 1) Analyse
            try:
                import gpt_analyze as analyzer  # type: ignore
                result = analyzer.run_analysis(data)  # erwartete Funktion
            except Exception as exc:
                _lg.exception("analysis failed: %s", exc)
                result = {"error": str(exc), "sections": {}}

            # 2) PDF-Service
            pdf_url = None
            try:
                import requests
                pdf_svc = os.getenv("PDF_SERVICE_URL", "").rstrip("/")
                if pdf_svc:
                    r = requests.post(f"{pdf_svc}/render", json={"briefing_id": briefing_id, "email": email, "analysis": result}, timeout=60)
                    if r.ok:
                        pdf_url = (r.json() or {}).get("pdf_url")
            except Exception as exc:
                _lg.warning("pdf render failed: %s", exc)

            # 3) Speichern in analyses/reports, wenn Tabellen existieren
            try:
                cols_a = _cols(db, "analyses")
                if cols_a:
                    row = {}
                    if "briefing_id" in cols_a: row["briefing_id"] = briefing_id
                    if "result" in cols_a: row["result"] = json.dumps(result)
                    if "status" in cols_a: row["status"] = "done"
                    if "created_at" in cols_a: row["created_at"] = _now()
                    if "updated_at" in cols_a: row["updated_at"] = _now()
                    db.execute(
                        text(f"INSERT INTO analyses ({', '.join(row.keys())}) VALUES ({', '.join(f':{k}' for k in row.keys())})"),
                        row,
                    )
                cols_r = _cols(db, "reports")
                if cols_r:
                    row = {}
                    if "briefing_id" in cols_r: row["briefing_id"] = briefing_id
                    if "pdf_url" in cols_r: row["pdf_url"] = pdf_url
                    if "email_to" in cols_r: row["email_to"] = email
                    if "created_at" in cols_r: row["created_at"] = _now()
                    db.execute(
                        text(f"INSERT INTO reports ({', '.join(row.keys())}) VALUES ({', '.join(f':{k}' for k in row.keys())})"),
                        row,
                    )
                db.commit()
            except Exception as exc:
                _lg.warning("persisting results failed: %s", exc)

            # 4) E-Mail (optional)
            try:
                if os.getenv("SMTP_HOST"):
                    from services.mailer import send_mail  # type: ignore
                    send_mail(to=email, subject="Ihre KI‑Auswertung", body="Ihr Report ist fertig.", attachments=[pdf_url] if pdf_url else [])
            except Exception as exc:
                _lg.warning("send mail failed: %s", exc)

            _lg.info("analysis finished for %s", email)
        except Exception as exc:
            try:
                log.exception("background task error: %s", exc)
            except Exception:
                pass

    background.add_task(task)


@router.post("/briefing_async", status_code=202)
def submit_briefing_async(
    payload: BriefingSubmit,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    user: SimpleUser = Depends(get_current_user),
):
    email = _infer_email(payload.data, payload.email or user.get("email"))
    if not email:
        raise HTTPException(status_code=400, detail="email_required")

    # 1) endgueltiges Briefing speichern
    briefing_id = _insert_briefing(db, email, payload.data)

    # 2) eventuellen Draft loeschen/markieren (optional)
    try:
        if briefing_id != -1 and "email" in _cols(db, "briefing_drafts"):
            db.execute(text("DELETE FROM briefing_drafts WHERE email=:email"), {"email": email})
            db.commit()
    except Exception:
        pass

    # 3) Analyse + PDF + Mail im Hintergrund
    _enqueue_analysis(background, db, briefing_id, email, payload.data)

    return {"ok": True, "queued": True, "briefing_id": briefing_id}
