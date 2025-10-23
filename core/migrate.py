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
    """Idempotente Minimal-Migrationen für 'reports'.
    Ziel: Kompatibilität mit asynchroner/inline Report-Erzeugung ohne Queue.
    - reports.user_id            -> hinzufügen (nullable, FK users.id, ON DELETE SET NULL)
    - reports.task_id            -> sicherstellen, aber NULL zulassen (DROP NOT NULL)
    - reports.status             -> hinzufügen, NOT NULL, DEFAULT 'pending'
    - reports.pdf_url            -> hinzufügen (falls fehlt)
    - reports.pdf_bytes_len      -> hinzufügen (falls fehlt)
    - reports.created_at         -> TIMESTAMPTZ sicherstellen
    - reports.updated_at         -> hinzufügen (nullable), optional
    Mehrfaches Ausführen ist gefahrlos.
    """
    if not _is_postgres(engine):
        return

    stmts = [
        # Spalten hinzufügen, falls nicht vorhanden
        """ALTER TABLE reports ADD COLUMN IF NOT EXISTS user_id INTEGER NULL;""",
        """ALTER TABLE reports ADD COLUMN IF NOT EXISTS task_id VARCHAR(128);""",
        """ALTER TABLE reports ADD COLUMN IF NOT EXISTS status VARCHAR(32) NOT NULL DEFAULT 'pending';""",
        """ALTER TABLE reports ADD COLUMN IF NOT EXISTS pdf_url VARCHAR(1024);""",
        """ALTER TABLE reports ADD COLUMN IF NOT EXISTS pdf_bytes_len INTEGER;""",
        """ALTER TABLE reports ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE;""",
        """ALTER TABLE reports ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE;""",

        # task_id darf NULL sein (wir generieren optional eine lokale ID ohne externe Queue)
        """DO $$ BEGIN
             IF EXISTS (
               SELECT 1 FROM information_schema.columns 
               WHERE table_name='reports' AND column_name='task_id'
             ) THEN
               ALTER TABLE reports ALTER COLUMN task_id DROP NOT NULL;
             END IF;
           END $$;""",

        # FK auf users.id (idempotent)
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

        # created_at auf TIMESTAMPTZ heben, falls nötig
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
