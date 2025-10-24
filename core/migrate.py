# -*- coding: utf-8 -*-
from __future__ import annotations
"""
Idempotente Migration (Hotfix):
- login_codes: Tabelle anlegen (falls fehlt)
- Sicherstellen, dass Spalte `code` existiert (legacy: `login_code`/`token` → RENAME; sonst ADD COLUMN)
- UNIQUE-Constraint auf `code` nur anlegen, wenn Spalte existiert
- Indizes abdecken (email, expires_at, consumed_at)
- reports: Kompatibilitätsfixe (nullable, status, audit, timestamptz)
Mehrfaches Ausführen ist sicher.
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
        # 1) login_codes anlegen (falls fehlt) – minimale kompatible Struktur ohne harte NOT NULL auf code
        """
        CREATE TABLE IF NOT EXISTS login_codes (
            id SERIAL PRIMARY KEY,
            email VARCHAR(320) NOT NULL,
            -- In manchen Legacy-Schemata kann diese Spalte anders heißen oder fehlen;
            -- wir erzwingen sie weiter unten idempotent.
            code VARCHAR(64),
            purpose VARCHAR(40) NOT NULL DEFAULT 'login',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            consumed_at TIMESTAMP WITH TIME ZONE NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            ip_address VARCHAR(64) NULL,
            user_agent TEXT NULL
        );
        """,

        # 2) Falls es alte Spaltennamen gibt → in `code` umbenennen; sonst `code` hinzufügen
        """
        DO $$
        BEGIN
          -- Falls Spalte `code` fehlt, aber `login_code` existiert → umbenennen
          IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='login_codes' AND column_name='code'
          ) AND EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='login_codes' AND column_name='login_code'
          ) THEN
            EXECUTE 'ALTER TABLE login_codes RENAME COLUMN login_code TO code';
          END IF;

          -- Falls Spalte `code` fehlt, aber `token` existiert → umbenennen
          IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='login_codes' AND column_name='code'
          ) AND EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='login_codes' AND column_name='token'
          ) THEN
            EXECUTE 'ALTER TABLE login_codes RENAME COLUMN token TO code';
          END IF;

          -- Falls `code` weiterhin fehlt → hinzufügen (NULL-able, um Altzeilen nicht zu brechen)
          IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='login_codes' AND column_name='code'
          ) THEN
            EXECUTE 'ALTER TABLE login_codes ADD COLUMN code VARCHAR(64)';
          END IF;
        END
        $$;
        """,

        # 3) UNIQUE-Constraint nur, wenn `code` existiert
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='login_codes' AND column_name='code'
          ) THEN
            IF NOT EXISTS (
              SELECT 1 FROM pg_constraint WHERE conname = 'uq_login_codes_code'
            ) THEN
              BEGIN
                ALTER TABLE login_codes ADD CONSTRAINT uq_login_codes_code UNIQUE (code);
              EXCEPTION WHEN undefined_column THEN
                -- Defensive: sollte nie passieren, da obige Prüfung greift
                NULL;
              WHEN duplicate_object THEN
                NULL;
              END;
            END IF;
          END IF;
        END
        $$;
        """,

        # 4) Indizes sicherstellen (idempotent)
        "CREATE INDEX IF NOT EXISTS ix_login_codes_email ON login_codes (email);",
        "CREATE INDEX IF NOT EXISTS ix_login_codes_expires_at ON login_codes (expires_at);",            "CREATE INDEX IF NOT EXISTS ix_login_codes_consumed_at ON login_codes (consumed_at);",
        # 5) reports – Kompatibilitätsfixe (wie zuvor)
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS user_email VARCHAR(320);",            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS task_id VARCHAR(128);",            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS status VARCHAR(32) NOT NULL DEFAULT 'pending';",            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS pdf_url VARCHAR(1024);",            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS pdf_bytes_len INTEGER;",            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE;",            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE;",            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS email_sent_user BOOLEAN NOT NULL DEFAULT false;",            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS email_sent_admin BOOLEAN NOT NULL DEFAULT false;",            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS email_error_user TEXT;",            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS email_error_admin TEXT;",
        # user_email darf NULL sein
        """
        DO $$ BEGIN
          IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='reports' AND column_name='user_email' AND is_nullable='NO'
          ) THEN
            ALTER TABLE reports ALTER COLUMN user_email DROP NOT NULL;
          END IF;
        END $$;
        """,

        # task_id darf NULL sein
        """
        DO $$ BEGIN
          IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='reports' AND column_name='task_id'
          ) THEN
            ALTER TABLE reports ALTER COLUMN task_id DROP NOT NULL;
          END IF;
        END $$;
        """,

        # created_at → TIMESTAMPTZ heben (falls nötig)
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
        """,
    ]

    with engine.begin() as conn:
        for s in stmts:
            conn.execute(text(s))
