# -*- coding: utf-8 -*-
from __future__ import annotations
from sqlalchemy import text
from sqlalchemy.engine import Engine

def _is_postgres(engine: Engine) -> bool:
    try:
        return engine.url.get_backend_name().startswith("postgresql")
    except Exception:
        return False

def run_migrations(engine: Engine) -> None:
    """Idempotente Minimal-Migrationen:
    - sorgt dafür, dass 'reports.user_id' existiert (nullable, FK users.id, ON DELETE SET NULL)
    - stellt sicher, dass Kernspalten vorhanden sind (analysis_id, briefing_id, pdf_url, pdf_bytes_len, created_at)
    - setzt timestamptz bei created_at
    Mehrfaches Ausführen ist gefahrlos.
    """
    if not _is_postgres(engine):
        return

    stmts = [
        """ALTER TABLE reports ADD COLUMN IF NOT EXISTS user_id INTEGER NULL;""",
        """DO $$ BEGIN
             IF NOT EXISTS (
               SELECT 1 FROM information_schema.table_constraints 
               WHERE table_name='reports' AND constraint_type='FOREIGN KEY' AND constraint_name='reports_user_id_fkey'
             ) THEN
               BEGIN
                 ALTER TABLE reports
                   ADD CONSTRAINT reports_user_id_fkey FOREIGN KEY (user_id)
                   REFERENCES users(id) ON DELETE SET NULL;
               EXCEPTION WHEN duplicate_object THEN
                 NULL;
               END;
             END IF;
           END $$;""",
        """ALTER TABLE reports ADD COLUMN IF NOT EXISTS briefing_id INTEGER NULL;""",
        """ALTER TABLE reports ADD COLUMN IF NOT EXISTS analysis_id INTEGER NULL;""",
        """ALTER TABLE reports ADD COLUMN IF NOT EXISTS pdf_url VARCHAR(1024);""",
        """ALTER TABLE reports ADD COLUMN IF NOT EXISTS pdf_bytes_len INTEGER;""",
        """ALTER TABLE reports ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE;""",
        """DO $$ BEGIN
             IF EXISTS (
               SELECT 1 FROM information_schema.columns 
               WHERE table_name='reports' AND column_name='created_at' AND data_type='timestamp without time zone'
             ) THEN
               ALTER TABLE reports ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC';
             END IF;
           END $$;""",
    ]
    with engine.begin() as conn:
        for s in stmts:
            conn.execute(text(s))
