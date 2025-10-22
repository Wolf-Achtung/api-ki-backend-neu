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
    if not _is_postgres(engine):
        return
    stmts = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITH TIME ZONE NULL;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE;",
        """DO $$ BEGIN
             IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='created_at' AND data_type='timestamp without time zone') THEN
               ALTER TABLE users ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC';
             END IF;
           END $$;""",
        """DO $$ BEGIN
             IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='ix_users_email') THEN
               CREATE UNIQUE INDEX ix_users_email ON users (email);
             END IF;
           END $$;""",

        """CREATE TABLE IF NOT EXISTS login_codes (
              id SERIAL PRIMARY KEY,
              user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              code_hash VARCHAR(128) NOT NULL,
              expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
              used BOOLEAN NOT NULL DEFAULT FALSE
            );""",

        """CREATE TABLE IF NOT EXISTS briefings (
              id SERIAL PRIMARY KEY,
              user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
              lang VARCHAR(5) NOT NULL DEFAULT 'de',
              answers JSONB NOT NULL DEFAULT '{}'::jsonb,
              created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );""",

        """CREATE TABLE IF NOT EXISTS analyses (
              id SERIAL PRIMARY KEY,
              user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
              briefing_id INTEGER NULL REFERENCES briefings(id) ON DELETE SET NULL,
              html TEXT NOT NULL,
              meta JSONB NOT NULL DEFAULT '{}'::jsonb,
              created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );""",

        """CREATE TABLE IF NOT EXISTS reports (
              id SERIAL PRIMARY KEY,
              user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
              briefing_id INTEGER NULL REFERENCES briefings(id) ON DELETE SET NULL,
              analysis_id INTEGER NULL REFERENCES analyses(id) ON DELETE SET NULL,
              pdf_url VARCHAR(1024),
              pdf_bytes_len INTEGER,
              created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );"""
    ]
    with engine.begin() as conn:
        for s in stmts:
            conn.execute(text(s))
