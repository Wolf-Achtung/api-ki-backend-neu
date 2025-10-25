# -*- coding: utf-8 -*-
from __future__ import annotations

"""Authentication services (robust to schema drift).

This module avoids tight coupling to a specific ORM model for `login_codes`.
Instead, it introspects available columns and writes rows via SQL that match
the current database schema.

It supports both shapes:
- legacy:   login_codes(email, code, created_at, expires_at, consumed_at, ...)
- modern:   login_codes(user_id, email, code_hash, used, attempts, ...)

Public functions exposed (expected by routes.auth):
- generate_code(db, user) -> str
- verify_code(db, user, code_input) -> bool

`db` is expected to be a SQLAlchemy Session.
`user` must have at least `.id` and `.email`.
"""

import hashlib
import os
import secrets
from datetime import datetime, timedelta
from typing import Dict, Set

from sqlalchemy import text
from sqlalchemy.orm import Session


DEFAULT_TTL_MINUTES = int(os.getenv("LOGIN_CODE_TTL_MINUTES", "10"))
CODE_LENGTH = int(os.getenv("LOGIN_CODE_LENGTH", "6"))
MAX_ATTEMPTS = int(os.getenv("LOGIN_CODE_MAX_ATTEMPTS", "10"))
HASH_SECRET = os.getenv("JWT_SECRET", "static-dev-secret")  # reuse existing secret


def _columns(db: Session, table: str) -> Set[str]:
    q = text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = :tname
    """)
    rows = db.execute(q, {"tname": table}).fetchall()
    return {r[0] for r in rows}


def _now_utc() -> datetime:
    return datetime.utcnow()


def _hash_code(code: str, email: str) -> str:
    payload = f"{code}:{email}:{HASH_SECRET}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _gen_code() -> str:
    # numeric, zero-padded
    from secrets import randbelow
    return str(randbelow(10 ** CODE_LENGTH)).zfill(CODE_LENGTH)


def generate_code(db: Session, user) -> str:
    """Create a login code for the given user; return the *plain* code.

    The inserted row adapts to the available columns in table `login_codes`.
    """
    email = getattr(user, "email", None)
    user_id = getattr(user, "id", None)
    if not email:
        raise ValueError("User email missing")

    cols = _columns(db, "login_codes")
    if not cols:
        raise RuntimeError("Table login_codes not found")  # clear error

    code = _gen_code()
    code_hash = _hash_code(code, email)
    now = _now_utc()
    exp = now + timedelta(minutes=DEFAULT_TTL_MINUTES)

    # Build row dict only with existing columns
    row: Dict[str, object] = {}
    if "user_id" in cols and user_id is not None:
        row["user_id"] = user_id
    if "email" in cols:
        row["email"] = email
    if "code_hash" in cols:
        row["code_hash"] = code_hash
    elif "code" in cols:
        row["code"] = code_hash  # store hashed even if column name is 'code'
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

    # Fallback: in rare legacy tables without timestamps, row would be empty -> protect
    if not row:
        # guarantee at least email/code pair
        row = {"email": email, "code": code_hash}

    cols_sql = ", ".join(row.keys())
    vals_sql = ", ".join(f":{k}" for k in row.keys())
    sql = text(f"INSERT INTO login_codes ({cols_sql}) VALUES ({vals_sql})")
    db.execute(sql, row)
    db.commit()
    return code


def verify_code(db: Session, user, code_input: str) -> bool:
    """Verify a login code for a user; consumes the code if valid.

    Supports either 'code_hash' or 'code' column; matches against SHA-256 hash.
    """
    email = getattr(user, "email", None)
    user_id = getattr(user, "id", None)
    if not email:
        return False

    cols = _columns(db, "login_codes")
    if not cols:
        return False

    code_hash = _hash_code(code_input, email)
    # Prefer most recent non-consumed code for that user/email
    where_parts = []
    params = {}

    if "user_id" in cols and user_id is not None:
        where_parts.append("user_id = :uid")
        params["uid"] = user_id
    elif "email" in cols:
        where_parts.append("email = :mail")
        params["mail"] = email

    if "code_hash" in cols:
        where_parts.append("code_hash = :ch")
        params["ch"] = code_hash
    elif "code" in cols:
        where_parts.append("code = :ch")
        params["ch"] = code_hash

    if "consumed_at" in cols:
        where_parts.append("consumed_at IS NULL")
    elif "used" in cols:
        where_parts.append("used = FALSE")  # legacy

    where_sql = " AND ".join(where_parts) or "TRUE"
    order_sql = "created_at DESC" if "created_at" in cols else "id DESC"
    sel = text(f"SELECT * FROM login_codes WHERE {where_sql} ORDER BY {order_sql} LIMIT 1")
    row = db.execute(sel, params).fetchone()
    if not row:
        return False

    # Expiry check (if column exists)
    if "expires_at" in cols and row._mapping.get("expires_at") is not None:
        if datetime.utcnow() > row._mapping["expires_at"]:
            return False

    # Consume the code
    if "consumed_at" in cols:
        upd = text("UPDATE login_codes SET consumed_at = now() WHERE id = :id")
    elif "used" in cols:
        upd = text("UPDATE login_codes SET used = TRUE WHERE id = :id")
    else:
        # no consume flag -> accept once without consume
        return True
    db.execute(upd, {"id": row._mapping["id"]})
    db.commit()
    return True
