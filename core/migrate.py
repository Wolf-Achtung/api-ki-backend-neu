# -*- coding: utf-8 -*-
from __future__ import annotations
"""
Idempotente Migrationen:
- login_codes: Tabelle + Indizes + Unique-Constraint (falls fehlen)
- reports: Kompatibilitätsfixes (user_email NULL, task_id NULL, status, Audit-Felder, TIMESTAMPTZ)
Mehrfaches Ausführen ist gefahrlos.
"""
from sqlalchemy import text
from sqlalchemy.engine import Engine

def _is_postgres(engine: Engine) -> bool:
    try:
        return engine.url.get_backend_name().startswith("postgresql")
    except Exception:
        return False

def run_migrations(engine: Engine) -> None:
    if not _is_postgres(engine):
        return

    stmts = [
        # --- login_codes (neu/absichern) ---
        """
        CREATE TABLE IF NOT EXISTS login_codes (
            id SERIAL PRIMARY KEY,
            email VARCHAR(320) NOT NULL,
            code VARCHAR(64) NOT NULL,
            purpose VARCHAR(40) NOT NULL DEFAULT 'login',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            consumed_at TIMESTAMP WITH TIME ZONE NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            ip_address VARCHAR(64) NULL,
            user_agent TEXT NULL
        );
        """,
        # Unique-Constraint für code
        """
        DO $$ BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'uq_login_codes_code'
          ) THEN
            ALTER TABLE login_codes ADD CONSTRAINT uq_login_codes_code UNIQUE (code);
          END IF;
        END $$;
        """,
        # Indizes
        "CREATE INDEX IF NOT EXISTS ix_login_codes_email ON login_codes (email);",            "CREATE INDEX IF NOT EXISTS ix_login_codes_expires_at ON login_codes (expires_at);",            "CREATE INDEX IF NOT EXISTS ix_login_codes_consumed_at ON login_codes (consumed_at);",
        # --- reports (Kompatibilitätsfixes; idempotent) ---
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS user_email VARCHAR(320);",            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS task_id VARCHAR(128);",            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS status VARCHAR(32) NOT NULL DEFAULT 'pending';",            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS pdf_url VARCHAR(1024);",            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS pdf_bytes_len INTEGER;",            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE;",            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE;",            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS email_sent_user BOOLEAN NOT NULL DEFAULT false;",            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS email_sent_admin BOOLEAN NOT NULL DEFAULT false;",            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS email_error_user TEXT;",            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS email_error_admin TEXT;",
        # user_email darf NULL sein
        """
        DO $$ BEGIN
          IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='reports' AND column_name='user_email'
                  AND is_nullable='NO'
          ) THEN
            ALTER TABLE reports ALTER COLUMN user_email DROP NOT NULL;
          END IF;
        END $$;
        """,            # task_id darf NULL sein
        """
        DO $$ BEGIN
          IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='reports' AND column_name='task_id'
          ) THEN
            ALTER TABLE reports ALTER COLUMN task_id DROP NOT NULL;
          END IF;
        END $$;
        """,            # created_at → TIMESTAMPTZ heben (falls nötig)
        """
        DO $$ BEGIN
          IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='reports' 
              AND column_name='created_at' 
              AND data_type='timestamp without time zone'
          ) THEN
            ALTER TABLE reports 
              ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE 
              USING created_at AT TIME ZONE 'UTC';
          END IF;
        END $$;
        """
    ]

    with engine.begin() as conn:
        for s in stmts:
            conn.execute(text(s))