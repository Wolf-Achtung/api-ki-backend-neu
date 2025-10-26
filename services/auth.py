# -*- coding: utf-8 -*-
"""
Authentication service: code generation & verification with SHA-256 hashing
ROBUST: Works with both 'used' and 'consumed_at' column variations
"""
from __future__ import annotations

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

# Configuration
LOGIN_CODE_TTL_MINUTES = int(os.getenv("LOGIN_CODE_TTL_MINUTES", "10"))
CODE_LENGTH = 6


def hash_code(code: str) -> str:
    """Hash a login code using SHA-256"""
    return hashlib.sha256(code.encode()).hexdigest()


def _table_has_column(db: Session, table: str, column: str) -> bool:
    """Check if a column exists in a table"""
    try:
        result = db.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = :table AND column_name = :col
        """), {"table": table, "col": column}).scalar()
        return result > 0
    except:
        return False


def generate_code(db: Session, user: dict) -> str:
    """
    Generate a 6-digit login code, hash it, and store in DB.
    Returns the plain code (for sending via email).
    
    ROBUST: Works with both schema variations
    """
    # Ensure table exists
    _ensure_login_codes_table(db)
    
    email = user.get("email")
    if not email:
        raise ValueError("User must have email")
    
    # Invalidate old codes - handle both 'used' and 'consumed_at' columns
    has_used = _table_has_column(db, "login_codes", "used")
    has_consumed = _table_has_column(db, "login_codes", "consumed_at")
    
    if has_consumed:
        invalidate_sql = text("""
            UPDATE login_codes 
            SET consumed_at = now() 
            WHERE email = :email AND consumed_at IS NULL
        """)
    elif has_used:
        invalidate_sql = text("""
            UPDATE login_codes 
            SET used = true 
            WHERE email = :email AND (used = false OR used IS NULL)
        """)
    else:
        # Fallback: delete old codes
        invalidate_sql = text("DELETE FROM login_codes WHERE email = :email")
    
    db.execute(invalidate_sql, {"email": email})
    db.commit()
    
    # Generate 6-digit code
    code = f"{secrets.randbelow(1000000):06d}"
    code_hash_value = hash_code(code)
    
    # Store hashed code - build INSERT dynamically
    expires_at = datetime.utcnow() + timedelta(minutes=LOGIN_CODE_TTL_MINUTES)
    
    # Build column list based on what exists
    columns = ["email", "code_hash", "created_at", "expires_at", "attempts"]
    values = [":email", ":hash", "now()", ":exp", "0"]
    
    if has_used:
        columns.append("used")
        values.append("false")
    
    if has_consumed:
        columns.append("consumed_at")
        values.append("NULL")
    
    insert_sql = text(f"""
        INSERT INTO login_codes ({", ".join(columns)})
        VALUES ({", ".join(values)})
    """)
    
    db.execute(insert_sql, {
        "email": email,
        "hash": code_hash_value,
        "exp": expires_at
    })
    db.commit()
    
    return code


def verify_code(db: Session, user: dict, code: str) -> bool:
    """
    Verify a login code by hashing the input and comparing with DB.
    ROBUST: Works with both schema variations
    """
    email = user.get("email")
    if not email:
        return False
    
    code_hash_value = hash_code(code)
    
    # Check schema
    has_used = _table_has_column(db, "login_codes", "used")
    has_consumed = _table_has_column(db, "login_codes", "consumed_at")
    
    # Build WHERE clause based on schema
    if has_consumed:
        where_clause = "consumed_at IS NULL"
    elif has_used:
        where_clause = "(used = false OR used IS NULL)"
    else:
        where_clause = "1=1"
    
    # Find valid code
    sql = text(f"""
        SELECT id, expires_at, attempts
        FROM login_codes
        WHERE email = :email 
          AND code_hash = :hash
          AND {where_clause}
        ORDER BY created_at DESC
        LIMIT 1
    """)
    
    result = db.execute(sql, {
        "email": email,
        "hash": code_hash_value
    }).mappings().first()
    
    if not result:
        # Increment failed attempts
        try:
            inc_sql = text(f"""
                UPDATE login_codes
                SET attempts = attempts + 1
                WHERE email = :email AND {where_clause}
            """)
            db.execute(inc_sql, {"email": email})
            db.commit()
        except:
            pass
        return False
    
    # Check if expired
    if result["expires_at"] < datetime.utcnow():
        return False
    
    # Check attempts (max 5)
    if result["attempts"] >= 5:
        return False
    
    # Mark as consumed/used
    if has_consumed:
        update_sql = text("UPDATE login_codes SET consumed_at = now() WHERE id = :id")
    elif has_used:
        update_sql = text("UPDATE login_codes SET used = true WHERE id = :id")
    else:
        # Fallback: delete
        update_sql = text("DELETE FROM login_codes WHERE id = :id")
    
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
        except:
            pass
    
    db.commit()
    return True


def get_current_user(db: Session, token: str = None, email: str = None):
    """Get current user from token or email."""
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
    return None


def _ensure_login_codes_table(db: Session):
    """
    Ensure login_codes table exists with correct schema.
    ROBUST: Creates table with both consumed_at and makes 'used' optional if it exists
    """
    try:
        # Create table if not exists - with consumed_at as primary status field
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
        
        # If 'used' column exists, make it optional and set default
        has_used = _table_has_column(db, "login_codes", "used")
        if has_used:
            try:
                # Make it nullable and set default
                db.execute(text("ALTER TABLE login_codes ALTER COLUMN used DROP NOT NULL"))
                db.execute(text("ALTER TABLE login_codes ALTER COLUMN used SET DEFAULT false"))
                db.execute(text("UPDATE login_codes SET used = false WHERE used IS NULL"))
                db.commit()
            except:
                db.rollback()
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_login_codes_email ON login_codes(email)",
            "CREATE INDEX IF NOT EXISTS idx_login_codes_code_hash ON login_codes(code_hash)",
            "CREATE INDEX IF NOT EXISTS idx_login_codes_expires ON login_codes(expires_at)",
            "CREATE INDEX IF NOT EXISTS idx_login_codes_consumed ON login_codes(consumed_at)",
        ]
        
        for idx_sql in indexes:
            try:
                db.execute(text(idx_sql))
            except:
                pass
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        # Non-fatal - table might already exist with different structure
        pass


def cleanup_expired_codes(db: Session):
    """Clean up expired login codes (call periodically)"""
    try:
        sql = text("""
            DELETE FROM login_codes
            WHERE expires_at < now()
        """)
        db.execute(sql)
        db.commit()
    except Exception:
        db.rollback()
