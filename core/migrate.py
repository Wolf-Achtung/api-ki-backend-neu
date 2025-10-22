# -*- coding: utf-8 -*-
from __future__ import annotations
from sqlalchemy import text
from sqlalchemy.engine import Engine

DDL = {
    "users_add_is_admin": "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;",
    "users_add_last_login_at": "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP NULL;",
    "users_add_created_at": "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT NOW();",
    "users_add_email_unique": """
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_indexes
    WHERE schemaname = 'public' AND indexname = 'ix_users_email'
  ) THEN
    CREATE UNIQUE INDEX ix_users_email ON users (email);
  END IF;
END
$$;
""",

    "login_codes_create": """
CREATE TABLE IF NOT EXISTS login_codes (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  code_hash VARCHAR(128) NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  used BOOLEAN NOT NULL DEFAULT FALSE
);
""",

    "briefings_create": """
CREATE TABLE IF NOT EXISTS briefings (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
  lang VARCHAR(5) NOT NULL DEFAULT 'de',
  answers JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
""",

    "analyses_create": """
CREATE TABLE IF NOT EXISTS analyses (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
  briefing_id INTEGER NULL REFERENCES briefings(id) ON DELETE SET NULL,
  html TEXT NOT NULL,
  meta JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
""",

    "reports_create": """
CREATE TABLE IF NOT EXISTS reports (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
  briefing_id INTEGER NULL REFERENCES briefings(id) ON DELETE SET NULL,
  analysis_id INTEGER NULL REFERENCES analyses(id) ON DELETE SET NULL,
  pdf_url VARCHAR(1024),
  pdf_bytes_len INTEGER,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
""",
}

def _is_postgres(engine: Engine) -> bool:
    try:
        return engine.url.get_backend_name().startswith("postgresql")
    except Exception:
        return False

def run_migrations(engine: Engine) -> None:
    """Idempotente Minimal-Migrationen für bestehende Railway-DB.
    - Fügt fehlende Spalten in users hinzu (is_admin, created_at, last_login_at)
    - Legt Tabellen login_codes, briefings, analyses, reports an (falls nicht vorhanden)
    - Legt Unique-Index für users.email an
    Nur für PostgreSQL aktiv; SQLite wird durch ORM-CreateAll bedient.
    """
    if not _is_postgres(engine):
        return
    with engine.begin() as conn:
        for name, ddl in DDL.items():
            conn.execute(text(ddl))
