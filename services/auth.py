
# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import os
from secrets import randbelow
from datetime import datetime, timedelta
from typing import Dict, Set, Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

# try to import project's DB session factory
try:
    from core.db import get_db  # type: ignore
except Exception:
    # very small fallback to avoid hard crashes if core.db is not importable
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    _eng = create_engine(os.getenv("DATABASE_URL", ""), pool_pre_ping=True, future=True)
    _Session = sessionmaker(bind=_eng, autoflush=False, autocommit=False)
    def get_db():
        db = _Session()
        try:
            yield db
        finally:
            db.close()

DEFAULT_TTL_MINUTES = int(os.getenv("LOGIN_CODE_TTL_MINUTES", "10"))
CODE_LENGTH = int(os.getenv("LOGIN_CODE_LENGTH", "6"))
HASH_SECRET = os.getenv("JWT_SECRET", "static-dev-secret")

def _columns(db: Session, table: str) -> Set[str]:
    rows = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name=:t"), {"t": table}).fetchall()
    return {r[0] for r in rows}

def _hash_code(code: str, email: str) -> str:
    return hashlib.sha256(f"{code}:{email}:{HASH_SECRET}".encode("utf-8")).hexdigest()

def _gen_code() -> str:
    return str(randbelow(10 ** CODE_LENGTH)).zfill(CODE_LENGTH)

def generate_code(db: Session, user) -> str:
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
    if "user_id" in cols and user_id is not None: row["user_id"] = user_id
    if "email" in cols: row["email"] = email
    if "code_hash" in cols: row["code_hash"] = ch
    elif "code" in cols: row["code"] = ch
    if "created_at" in cols: row["created_at"] = now
    if "expires_at" in cols: row["expires_at"] = exp
    if "consumed_at" in cols: row["consumed_at"] = None
    if "used" in cols: row["used"] = False
    if "attempts" in cols: row["attempts"] = 0
    if not row: row = {"email": email, "code": ch}
    cols_sql = ", ".join(row.keys())
    vals_sql = ", ".join(f":{k}" for k in row.keys())
    db.execute(text(f"INSERT INTO login_codes ({cols_sql}) VALUES ({vals_sql})"), row)
    db.commit()
    return code

def verify_code(db: Session, user, code_input: str) -> bool:
    email = getattr(user, "email", None) or (user.get("email") if isinstance(user, dict) else None)
    user_id = getattr(user, "id", None) if not isinstance(user, dict) else user.get("id")
    if not email:
        return False
    cols = _columns(db, "login_codes")
    if not cols:
        return False
    ch = _hash_code(code_input, email)
    where, p = [], {}
    if "user_id" in cols and user_id is not None: where += ["user_id=:uid"]; p["uid"] = user_id
    elif "email" in cols: where += ["email=:mail"]; p["mail"] = email
    if "code_hash" in cols: where += ["code_hash=:ch"]; p["ch"] = ch
    elif "code" in cols: where += ["code=:ch"]; p["ch"] = ch
    if "consumed_at" in cols: where += ["consumed_at IS NULL"]
    elif "used" in cols: where += ["used=FALSE"]
    sel = text(f"SELECT * FROM login_codes WHERE {' AND '.join(where) or 'TRUE'} ORDER BY " +
               ("created_at DESC" if "created_at" in cols else "id DESC") + " LIMIT 1")
    row = db.execute(sel, p).fetchone()
    if not row:
        return False
    if "expires_at" in cols and row._mapping.get("expires_at") and datetime.utcnow() > row._mapping["expires_at"]:
        return False
    upd = None
    if "consumed_at" in cols: upd = text("UPDATE login_codes SET consumed_at=now() WHERE id=:id")
    elif "used" in cols: upd = text("UPDATE login_codes SET used=TRUE WHERE id=:id")
    if upd:
        db.execute(upd, {"id": row._mapping["id"]})
        db.commit()
    return True

# ------------------------------------------------------------------
# Minimaler Security-Helper, damit routes.report importieren kann
# ------------------------------------------------------------------
class SimpleUser(dict):
    """Leichtgewichtiger User-Container: {'id': int|None, 'email': str, 'role': str}"""
    pass

def _lookup_user_by_email(db: Session, email: str) -> Optional[SimpleUser]:
    row = db.execute(text("SELECT id, email FROM users WHERE lower(email)=lower(:e) LIMIT 1;"), {"e": email}).mappings().first()
    if row:
        return SimpleUser(id=row["id"], email=row["email"], role="user")
    return None

def get_current_user(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
    x_user_email: Optional[str] = Header(None),
) -> SimpleUser:
    """
    Sehr einfache Auth für Admin/Backend-Nutzung:
    - Admin: Authorization: Bearer <ADMIN_API_TOKEN>
    - User:  X-User-Email: user@example.com  (muss in users liegen)
    """
    admin_token = os.getenv("ADMIN_API_TOKEN", "")
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        if admin_token and token == admin_token:
            return SimpleUser(id=0, email="admin@local", role="admin")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_admin_token")

    if x_user_email:
        u = _lookup_user_by_email(db, x_user_email.strip().lower())
        if u:
            return u
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unknown_email")

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication_required")
