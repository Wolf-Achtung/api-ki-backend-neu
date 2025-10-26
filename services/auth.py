# services/auth.py - FIXED VERSION mit login_audit Tabelle
import logging
from database import get_db_engine
from sqlalchemy import text

log = logging.getLogger(__name__)

def _ensure_login_codes_table():
    """Erstellt die login_codes UND login_audit Tabellen falls sie nicht existieren"""
    engine = get_db_engine()
    with engine.connect() as conn:
        # 1. login_codes Tabelle
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS login_codes (
                id SERIAL PRIMARY KEY,
                email TEXT NOT NULL,
                code_hash TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                expires_at TIMESTAMPTZ NOT NULL,
                consumed_at TIMESTAMPTZ,
                attempts INTEGER DEFAULT 0,
                ip TEXT
            );
        """))
        
        # 2. login_audit Tabelle (für Rate Limiting)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS login_audit (
                id SERIAL PRIMARY KEY,
                email TEXT,
                ip TEXT,
                action TEXT NOT NULL,
                ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                success BOOLEAN DEFAULT TRUE,
                error_msg TEXT
            );
        """))
        
        # 3. Indizes für Performance
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_login_codes_email 
            ON login_codes(email);
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_login_codes_expires 
            ON login_codes(expires_at);
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_login_audit_action_ts 
            ON login_audit(action, ts);
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_login_audit_email_ip 
            ON login_audit(email, ip);
        """))
        
        conn.commit()
        log.info("✓ Login-codes and login-audit tables ready")
