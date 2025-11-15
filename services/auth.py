# -*- coding: utf-8 -*-
"""
Authentication service: code generation & verification with SHA-256 hashing
Compatible with email-based login_codes table (no user_id)
"""
from __future__ import annotations

import logging
import os
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

log = logging.getLogger(__name__)

# Configuration
LOGIN_CODE_TTL_MINUTES = int(os.getenv("LOGIN_CODE_TTL_MINUTES", "10"))
CODE_LENGTH = 6


def hash_code(code: str) -> str:
    """Hash a login code using SHA-256"""
    return hashlib.sha256(code.encode()).hexdigest()


def generate_code(db: Session, user: dict) -> str:
    """
    Generate a 6-digit login code, hash it, and store in DB.
    Returns the plain code (for sending via email).
    
    Table structure expected:
    - login_codes(id, email, code_hash, created_at, expires_at, consumed_at, attempts)
    """
    # Ensure table exists with code_hash column
    _ensure_login_codes_table(db)
    
    email = user.get("email")
    if not email:
        raise ValueError("User must have email")
    
    # Invalidate old codes for this email
    invalidate_sql = text("""
        UPDATE login_codes 
        SET consumed_at = now() 
        WHERE email = :email AND consumed_at IS NULL
    """)
    db.execute(invalidate_sql, {"email": email})
    db.commit()
    
    # Generate 6-digit code
    code = f"{secrets.randbelow(1000000):06d}"
    code_hash_value = hash_code(code)
    
    # Store hashed code
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=LOGIN_CODE_TTL_MINUTES)
    
    insert_sql = text("""
        INSERT INTO login_codes (email, code_hash, created_at, expires_at, attempts)
        VALUES (:email, :hash, now(), :exp, 0)
    """)
    db.execute(insert_sql, {
        "email": email,
        "hash": code_hash_value,
        "exp": expires_at
    })
    db.commit()
    
    return code  # Return plain code for email


def verify_code(db: Session, user: dict, code: str) -> bool:
    """
    Verify a login code by hashing the input and comparing with DB.
    Returns True if valid, False otherwise.
    """
    email = user.get("email")
    if not email:
        return False
    
    code_hash_value = hash_code(code)
    
    # Find valid code
    sql = text("""
        SELECT id, expires_at, consumed_at, attempts
        FROM login_codes
        WHERE email = :email 
          AND code_hash = :hash
          AND consumed_at IS NULL
        ORDER BY created_at DESC
        LIMIT 1
    """)
    
    result = db.execute(sql, {
        "email": email,
        "hash": code_hash_value
    }).mappings().first()
    
    if not result:
        # Increment failed attempts for any matching code_hash
        try:
            inc_sql = text("""
                UPDATE login_codes
                SET attempts = attempts + 1
                WHERE email = :email AND consumed_at IS NULL
            """)
            db.execute(inc_sql, {"email": email})
            db.commit()
        except Exception as e:
            log.warning("Failed to increment login attempts for %s: %s", email, str(e))
            db.rollback()
        return False
    
    # Check if expired
    if result["expires_at"] < datetime.now(timezone.utc):
        return False
    
    # Check attempts (max 5)
    if result["attempts"] >= 5:
        return False
    
    # Mark as consumed
    update_sql = text("""
        UPDATE login_codes
        SET consumed_at = now()
        WHERE id = :id
    """)
    db.execute(update_sql, {"id": result["id"]})
    
    # Update user last_login if user has id
    if user.get("id"):
        try:
            update_user_sql = text("""
                UPDATE users
                SET last_login = now()
                WHERE id = :uid
            """)
            db.execute(update_user_sql, {"uid": user["id"]})
        except Exception as e:
            log.warning("Failed to update last_login for user %s: %s", user["id"], str(e))
    
    db.commit()
    return True


def get_current_user(db: Session, token: str = None, email: str = None):
    """
    Get current user from token or email.
    This is a placeholder - implement proper session/JWT handling in production.
    
    For now, just lookup by email if provided.
    """
    if email:
        sql = text("""
            SELECT id, email, is_active, is_admin 
            FROM users 
            WHERE lower(email) = lower(:email)
            LIMIT 1
        """)
        result = db.execute(sql, {"email": email}).mappings().first()
        if result:
            return dict(result)
    
    # TODO: Implement proper token validation
    # For now return None if no email provided
    return None


def _ensure_login_codes_table(db: Session):
    """
    Ensure login_codes table exists with correct schema.
    This handles migration from old 'code' column to 'code_hash'.
    
    Schema: email-based (no user_id foreign key)
    """
    # Create table if not exists
    create_sql = text("""
        CREATE TABLE IF NOT EXISTS login_codes (
            id BIGSERIAL PRIMARY KEY,
            email TEXT NOT NULL,
            code_hash TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now(),
            expires_at TIMESTAMPTZ NOT NULL,
            consumed_at TIMESTAMPTZ,
            attempts INTEGER DEFAULT 0,
            ip TEXT
        )
    """)
    db.execute(create_sql)
    db.commit()
    
    # Create login_audit table for rate limiting
    audit_sql = text("""
        CREATE TABLE IF NOT EXISTS login_audit (
            id BIGSERIAL PRIMARY KEY,
            email TEXT,
            ip TEXT,
            action TEXT NOT NULL,
            ts TIMESTAMPTZ NOT NULL DEFAULT now(),
            success BOOLEAN DEFAULT TRUE,
            error_msg TEXT
        )
    """)
    db.execute(audit_sql)
    db.commit()
    
    # Check if old 'code' column exists
    check_col_sql = text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'login_codes' 
          AND column_name = 'code'
    """)
    has_old_col = db.execute(check_col_sql).scalar()
    
    if has_old_col:
        # Migrate from old structure
        # 1. Add code_hash column if not exists
        try:
            alter_add_sql = text("""
                ALTER TABLE login_codes
                ADD COLUMN IF NOT EXISTS code_hash TEXT
            """)
            db.execute(alter_add_sql)
            db.commit()
        except Exception as e:
            log.warning("Failed to add code_hash column: %s", str(e))
            db.rollback()

        # 2. Delete old codes (can't migrate plaintext to hash)
        try:
            delete_old_sql = text("DELETE FROM login_codes")
            db.execute(delete_old_sql)
            db.commit()
        except Exception as e:
            log.warning("Failed to delete old codes: %s", str(e))
            db.rollback()

        # 3. Drop old code column
        try:
            alter_drop_sql = text("""
                ALTER TABLE login_codes
                DROP COLUMN IF EXISTS code CASCADE
            """)
            db.execute(alter_drop_sql)
            db.commit()
        except Exception as e:
            log.warning("Failed to drop old code column: %s", str(e))
            db.rollback()

        # 4. Make code_hash NOT NULL
        try:
            alter_not_null_sql = text("""
                ALTER TABLE login_codes
                ALTER COLUMN code_hash SET NOT NULL
            """)
            db.execute(alter_not_null_sql)
            db.commit()
        except Exception as e:
            log.warning("Failed to make code_hash NOT NULL: %s", str(e))
            db.rollback()
    
    # Create indexes for performance (only on columns that exist)
    try:
        index_email_sql = text("""
            CREATE INDEX IF NOT EXISTS idx_login_codes_email
            ON login_codes(email)
        """)
        db.execute(index_email_sql)
        db.commit()
    except Exception as e:
        log.debug("Failed to create email index: %s", str(e))
        db.rollback()

    try:
        index_hash_sql = text("""
            CREATE INDEX IF NOT EXISTS idx_login_codes_code_hash
            ON login_codes(code_hash)
        """)
        db.execute(index_hash_sql)
        db.commit()
    except Exception as e:
        log.debug("Failed to create code_hash index: %s", str(e))
        db.rollback()

    try:
        index_expires_sql = text("""
            CREATE INDEX IF NOT EXISTS idx_login_codes_expires
            ON login_codes(expires_at)
        """)
        db.execute(index_expires_sql)
        db.commit()
    except Exception as e:
        log.debug("Failed to create expires index: %s", str(e))
        db.rollback()

    # Create indexes for login_audit (rate limiting)
    try:
        index_audit_action_sql = text("""
            CREATE INDEX IF NOT EXISTS idx_login_audit_action_ts
            ON login_audit(action, ts)
        """)
        db.execute(index_audit_action_sql)
        db.commit()
    except Exception as e:
        log.debug("Failed to create audit action index: %s", str(e))
        db.rollback()

    try:
        index_audit_email_ip_sql = text("""
            CREATE INDEX IF NOT EXISTS idx_login_audit_email_ip
            ON login_audit(email, ip)
        """)
        db.execute(index_audit_email_ip_sql)
        db.commit()
    except Exception as e:
        log.debug("Failed to create audit email/ip index: %s", str(e))
        db.rollback()


def cleanup_expired_codes(db: Session):
    """Clean up expired login codes (call periodically)"""
    try:
        sql = text("""
            DELETE FROM login_codes
            WHERE expires_at < now()
        """)
        db.execute(sql)
        db.commit()
    except Exception as e:
        db.rollback()
        raise
