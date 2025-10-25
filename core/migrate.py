# -*- coding: utf-8 -*-
from __future__ import annotations
from sqlalchemy import text
from sqlalchemy.engine import Engine

def run_migrations(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS login_codes (id BIGSERIAL PRIMARY KEY);"))
        for ddl in [
            "ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS user_id BIGINT",
            "ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS email TEXT",
            "ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS code VARCHAR(128)",
            "ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS code_hash VARCHAR(128)",
            "ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS used BOOLEAN DEFAULT FALSE",
            "ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS attempts INTEGER DEFAULT 0",
            "ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now()",
            "ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ",
            "ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS consumed_at TIMESTAMPTZ",
        ]: conn.execute(text(ddl))

        conn.execute(text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='uq_login_codes_codehash') THEN
                IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='login_codes' AND column_name='code_hash') THEN
                    ALTER TABLE login_codes ADD CONSTRAINT uq_login_codes_codehash UNIQUE (code_hash);
                END IF;
            END IF;
        END $$;"""))

        conn.execute(text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='uq_login_codes_code') THEN
                IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='login_codes' AND column_name='code') THEN
                    ALTER TABLE login_codes ADD CONSTRAINT uq_login_codes_code UNIQUE (code);
                END IF;
            END IF;
        END $$;"""))

        for idx in [
            "CREATE INDEX IF NOT EXISTS ix_login_codes_email ON login_codes(email)",
            "CREATE INDEX IF NOT EXISTS ix_login_codes_user_id ON login_codes(user_id)",
            "CREATE INDEX IF NOT EXISTS ix_login_codes_consumed_at ON login_codes(consumed_at)",
            "CREATE INDEX IF NOT EXISTS ix_login_codes_created_at ON login_codes(created_at)",
        ]: conn.execute(text(idx))

        # audit table for rate limiting & visibility
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS login_audit (
            id BIGSERIAL PRIMARY KEY,
            ts TIMESTAMPTZ DEFAULT now(),
            email TEXT,
            ip TEXT,
            action TEXT,
            status TEXT,
            user_agent TEXT,
            detail TEXT
        );"""))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_login_audit_email_ts ON login_audit(email, ts DESC);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_login_audit_ip_ts ON login_audit(ip, ts DESC);"))

        # reports baseline
        conn.execute(text("CREATE TABLE IF NOT EXISTS reports (id BIGSERIAL PRIMARY KEY);"))
        for ddl in [
            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS user_id BIGINT",
            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS briefing_id BIGINT",
            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS analysis_id BIGINT",
            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS user_email TEXT",
            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS status TEXT",
            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS pdf_url TEXT",
            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS pdf_bytes_len INTEGER",
            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now()",
            "ALTER TABLE reports ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ",
        ]: conn.execute(text(ddl))
        for idx in [
            "CREATE INDEX IF NOT EXISTS ix_reports_status ON reports(status)",
            "CREATE INDEX IF NOT EXISTS ix_reports_user_email ON reports(user_email)",
            "CREATE INDEX IF NOT EXISTS ix_reports_created_at ON reports(created_at)",
        ]: conn.execute(text(idx))
