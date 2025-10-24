# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Defensive, idempotente Migrationen für Legacy-DBs.
- Repariert login_codes (email, code, created_at, expires_at, consumed_at) inkl. Constraints/Indizes.
- Härtet reports für PDF/E-Mail-Statusfelder ab.
- Reihenfolge: erst Spalten sicherstellen/umbenennen, dann Constraints/Indizes.
"""
import logging
from sqlalchemy import text
from sqlalchemy.engine import Engine

log = logging.getLogger(__name__)

def _exec(conn, sql: str) -> None:
    sql = sql.strip()
    if not sql:
        return
    try:
        log.debug("MIGRATE: %s", sql.replace("\n", " ")[:240])
        conn.execute(text(sql))
    except Exception as exc:
        # Wir loggen den Fehler, geben ihn aber weiter, damit Startup fehlschlägt (sichtbar im Log)
        log.error("MIGRATE failed: %s :: %s", exc.__class__.__name__, exc)
        raise

def run_migrations(engine: Engine) -> None:
    with engine.begin() as conn:
        # --- 1) LOGIN_CODES: Tabelle anlegen, dann Spalten, dann Constraints/Indizes ---
        _exec(conn, """
        CREATE TABLE IF NOT EXISTS login_codes (
            id SERIAL PRIMARY KEY,
            email VARCHAR(320),
            code VARCHAR(64),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            expires_at TIMESTAMPTZ,
            consumed_at TIMESTAMPTZ
        );
        """)

        # Bekannte Legacy-Spalten umbenennen → Zielschema
        _exec(conn, """
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='login_codes' AND column_name='email_address'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='login_codes' AND column_name='email'
            ) THEN
                ALTER TABLE login_codes RENAME COLUMN email_address TO email;
            END IF;
        END $$;
        """)

        _exec(conn, """
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='login_codes' AND column_name='login_code'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='login_codes' AND column_name='code'
            ) THEN
                ALTER TABLE login_codes RENAME COLUMN login_code TO code;
            END IF;
        END $$;
        """)

        _exec(conn, """
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='login_codes' AND column_name='used_at'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='login_codes' AND column_name='consumed_at'
            ) THEN
                ALTER TABLE login_codes RENAME COLUMN used_at TO consumed_at;
            END IF;
        END $$;
        """)

        # Fehlende Spalten addieren (idempotent)
        _exec(conn, "ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS email VARCHAR(320);")
        _exec(conn, "ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS code VARCHAR(64);")
        _exec(conn, "ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();")
        _exec(conn, "ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;")
        _exec(conn, "ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS consumed_at TIMESTAMPTZ;")

        # Constraints/Indizes NACHDEM die Spalten existieren
        _exec(conn, """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_login_codes_code') THEN
                ALTER TABLE login_codes ADD CONSTRAINT uq_login_codes_code UNIQUE (code);
            END IF;
        END $$;
        """)
        _exec(conn, "CREATE INDEX IF NOT EXISTS ix_login_codes_email ON login_codes (email);")
        _exec(conn, "CREATE INDEX IF NOT EXISTS ix_login_codes_consumed_at ON login_codes (consumed_at);")

        # --- 2) REPORTS: optionale Felder für PDF/E-Mail/Status/Audit absichern ---
        _exec(conn, "ALTER TABLE reports ADD COLUMN IF NOT EXISTS user_email VARCHAR(320);")
        _exec(conn, "ALTER TABLE reports ADD COLUMN IF NOT EXISTS task_id VARCHAR(64);")
        _exec(conn, "ALTER TABLE reports ADD COLUMN IF NOT EXISTS pdf_url TEXT;")
        _exec(conn, "ALTER TABLE reports ADD COLUMN IF NOT EXISTS pdf_bytes_len INTEGER;")
        _exec(conn, "ALTER TABLE reports ADD COLUMN IF NOT EXISTS status VARCHAR(16) DEFAULT 'pending';")
        _exec(conn, "ALTER TABLE reports ADD COLUMN IF NOT EXISTS email_sent_user BOOLEAN DEFAULT FALSE;")
        _exec(conn, "ALTER TABLE reports ADD COLUMN IF NOT EXISTS email_sent_admin BOOLEAN DEFAULT FALSE;")
        _exec(conn, "ALTER TABLE reports ADD COLUMN IF NOT EXISTS email_error_user TEXT;")
        _exec(conn, "ALTER TABLE reports ADD COLUMN IF NOT EXISTS email_error_admin TEXT;")
        _exec(conn, "ALTER TABLE reports ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ;")

        _exec(conn, "CREATE INDEX IF NOT EXISTS ix_reports_status ON reports (status);")
        _exec(conn, "CREATE INDEX IF NOT EXISTS ix_reports_updated_at ON reports (updated_at);")
