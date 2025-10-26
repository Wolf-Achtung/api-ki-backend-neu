# -*- coding: utf-8 -*-
"""
Authentication service: code generation & verification with SHA-256 hashing
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


def generate_code(db: Session, user: dict) -> str:
    """
    Generate a 6-digit login code, hash it, and store in DB.
    Returns the plain code (for sending via email).
    
    Table structure expected:
    - login_codes(id, user_id, code_hash, created_at, expires_at, consumed_at, attempts)
    """
    # Ensure table exists with code_hash column
    _ensure_login_codes_table(db)
    
    # Invalidate old codes for this user
    invalidate_sql = text("""
        UPDATE login_codes 
        SET consumed_at = now() 
        WHERE user_id = :uid AND consumed_at IS NULL
    """)
    db.execute(invalidate_sql, {"uid": user["id"]})
    db.commit()
    
    # Generate 6-digit code
    code = f"{secrets.randbelow(1000000):06d}"
    code_hash_value = hash_code(code)
    
    # Store hashed code
    expires_at = datetime.utcnow() + timedelta(minutes=LOGIN_CODE_TTL_MINUTES)
    
    insert_sql = text("""
        INSERT INTO login_codes (user_id, code_hash, created_at, expires_at, attempts)
        VALUES (:uid, :hash, now(), :exp, 0)
    """)
    db.execute(insert_sql, {
        "uid": user["id"],
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
    code_hash_value = hash_code(code)
    
    # Find valid code
    sql = text("""
        SELECT id, expires_at, consumed_at, attempts
        FROM login_codes
        WHERE user_id = :uid 
          AND code_hash = :hash
          AND consumed_at IS NULL
        ORDER BY created_at DESC
        LIMIT 1
    """)
    
    result = db.execute(sql, {
        "uid": user["id"],
        "hash": code_hash_value
    }).mappings().first()
    
    if not result:
        return False
    
    # Check if expired
    if result["expires_at"] < datetime.utcnow():
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
    
    # Update user last_login
    update_user_sql = text("""
        UPDATE users
        SET last_login = now()
        WHERE id = :uid
    """)
    db.execute(update_user_sql, {"uid": user["id"]})
    
    db.commit()
    return True


def _ensure_login_codes_table(db: Session):
    """
    Ensure login_codes table exists with correct schema.
    This handles migration from old 'code' column to 'code_hash'.
    """
    # Create table if not exists
    create_sql = text("""
        CREATE TABLE IF NOT EXISTS login_codes (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
            code_hash TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now(),
            expires_at TIMESTAMPTZ NOT NULL,
            consumed_at TIMESTAMPTZ,
            attempts INTEGER DEFAULT 0
        )
    """)
    db.execute(create_sql)
    
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
        except:
            pass
        
        # 2. Delete old codes (can't migrate plaintext to hash)
        delete_old_sql = text("DELETE FROM login_codes")
        db.execute(delete_old_sql)
        
        # 3. Drop old code column
        try:
            alter_drop_sql = text("""
                ALTER TABLE login_codes 
                DROP COLUMN IF EXISTS code
            """)
            db.execute(alter_drop_sql)
        except:
            pass
        
        # 4. Make code_hash NOT NULL
        try:
            alter_not_null_sql = text("""
                ALTER TABLE login_codes 
                ALTER COLUMN code_hash SET NOT NULL
            """)
            db.execute(alter_not_null_sql)
        except:
            pass
    
    # Create indexes for performance
    try:
        index_sql = text("""
            CREATE INDEX IF NOT EXISTS idx_login_codes_user_id 
            ON login_codes(user_id)
        """)
        db.execute(index_sql)
        
        index_hash_sql = text("""
            CREATE INDEX IF NOT EXISTS idx_login_codes_code_hash 
            ON login_codes(code_hash)
        """)
        db.execute(index_hash_sql)
    except:
        pass
    
    db.commit()


def cleanup_expired_codes(db: Session):
    """Clean up expired login codes (call periodically)"""
    sql = text("""
        DELETE FROM login_codes
        WHERE expires_at < now()
    """)
    db.execute(sql)
    db.commit()
