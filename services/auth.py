# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import os
from secrets import randbelow
from datetime import datetime, timedelta
from typing import Dict, Set, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

# Optional Project-Imports (werden nur genutzt, wenn vorhanden)
try:
    from core.db import get_db  # noqa: F401
except Exception:
    # Fallback wird nicht benutzt – get_db kommt aus dem Projekt.
    pass

DEFAULT_TTL_MINUTES = int(os.getenv("LOGIN_CODE_TTL_MINUTES", "10"))
CODE_LENGTH = int(os.getenv("LOGIN_CODE_LENGTH", "6"))
HASH_SECRET = os.getenv("JWT_SECRET", "static-dev-secret")


def _columns(db: Session, table: str) -> Set[str]:
    rows = db.execute(
        text("SELECT column_name FROM information_schema.columns WHERE table_name=:t"),
        {"t": table},
    ).fetchall()
    return {r[0] for r in rows}


def _hash_code(code: str, email: str) -> str:
    return hashlib.sha256(f"{code}:{email}:{HASH_SECRET}".encode("utf-8")).hexdigest()


def _gen_code() -> str:
    return str(randbelow(10 ** CODE_LENGTH)).zfill(CODE_LENGTH)


def generate_code(db: Session, user) -> str:
    """Erzeugt einen Login‑Code und speichert einen Hash in login_codes.
    Unterstützt altes (email/code/used) und neues Schema (user_id/code_hash/expires_at/…).
    """
    email = getattr(user, "email", None) or (user.get("email") if isinstance(user, dict) else None)
    user_id = getattr(user, "id", None) if not isinstance(user, dict) else user.get("id")
    if not email:
        raise ValueError("User email missing")

    cols = _columns(db, "login_codes")
    if not cols:
        raise RuntimeError("Table login_codes not found")

    code = _gen_code()
    ch = _hash_code(code, email)
    now = datetime.utcnow()
    exp = now + timedelta(minutes=DEFAULT_TTL_MINUTES)

    row: Dict[str, object] = {}
    if "user_id" in cols and user_id is not None:
        row["user_id"] = user_id
    if "email" in cols:
        row["email"] = email
    if "code_hash" in cols:
        row["code_hash"] = ch
    elif "code" in cols:
        row["code"] = ch
    if "created_at" in cols:
        row["created_at"] = now
    if "expires_at" in cols:
        row["expires_at"] = exp
    if "consumed_at" in cols:
        row["consumed_at"] = None
    if "used" in cols:
        row["used"] = False
    if "attempts" in cols:
        row["attempts"] = 0

    if not row:
        # Minimales Fallback
        row = {"email": email, "code": ch}

    cols_sql = ", ".join(row.keys())
    vals_sql = ", ".join(f":{k}" for k in row.keys())
    db.execute(text(f"INSERT INTO login_codes ({cols_sql}) VALUES ({vals_sql})"), row)
    db.commit()
    return code


def verify_code(db: Session, user, code_input: str) -> bool:
    """Verifiziert einen Code. Schema‑robust und ohne Exceptions im Erfolgs/Fehlerfall.
    Gibt True/False zurück. Setzt consumed_at bzw. used, wenn vorhanden.
    """
    email = getattr(user, "email", None) or (user.get("email") if isinstance(user, dict) else None)
    user_id = getattr(user, "id", None) if not isinstance(user, dict) else user.get("id")
    if not email:
        return False

    cols = _columns(db, "login_codes")
    if not cols:
        return False

    ch = _hash_code(code_input, email)

    where, p = [], {}
    if "user_id" in cols and user_id is not None:
        where += ["user_id=:uid"]; p["uid"] = user_id
    elif "email" in cols:
        where += ["email=:mail"]; p["mail"] = email

    if "code_hash" in cols:
        where += ["code_hash=:ch"]; p["ch"] = ch
    elif "code" in cols:
        where += ["code=:ch"]; p["ch"] = ch

    if "consumed_at" in cols:
        where += ["consumed_at IS NULL"]
    elif "used" in cols:
        where += ["used=FALSE"]

    order_by = "created_at DESC" if "created_at" in cols else "id DESC"
    sel = text(f"SELECT * FROM login_codes WHERE {' AND '.join(where) or 'TRUE'} ORDER BY {order_by} LIMIT 1")
    row = db.execute(sel, p).fetchone()
    if not row:
        return False

    m = getattr(row, "_mapping", row)
    expires = m.get("expires_at") if isinstance(m, dict) else getattr(row, "expires_at", None)
    if expires and datetime.utcnow() > expires:
        return False

    # Update bei Erfolg – ClauseElement niemals direkt in if auswerten!
    upd = None
    if "consumed_at" in cols:
        upd = text("UPDATE login_codes SET consumed_at=now() WHERE id=:id")
    elif "used" in cols:
        upd = text("UPDATE login_codes SET used=TRUE WHERE id=:id")

    row_id = m.get("id") if isinstance(m, dict) else getattr(row, "id", None)
    if upd is not None and row_id is not None:
        db.execute(upd, {"id": row_id})
        db.commit()

    return True
