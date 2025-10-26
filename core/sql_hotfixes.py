# -*- coding: utf-8 -*-
"""Predefined SQL hotfixes that can be applied via the admin endpoint.
All scripts are idempotent and safe to run multiple times.
"""
from __future__ import annotations

HOTFIX_LOGIN_CODES_V2 = """
-- CRITICAL FIX: Remove NOT NULL constraint from 'used' column and set default
-- This fixes the "null value in column used violates not-null constraint" error
BEGIN;

-- 1. Make 'used' column nullable if it exists
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'login_codes' AND column_name = 'used'
    ) THEN
        ALTER TABLE login_codes ALTER COLUMN used DROP NOT NULL;
        ALTER TABLE login_codes ALTER COLUMN used SET DEFAULT false;
        UPDATE login_codes SET used = false WHERE used IS NULL;
    END IF;
END $$;

-- 2. Ensure consumed_at column exists
ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS consumed_at TIMESTAMPTZ;

-- 3. Migrate data: if 'used' is true, set consumed_at to created_at
UPDATE login_codes 
SET consumed_at = created_at 
WHERE used = true AND consumed_at IS NULL;

-- 4. Create indexes for performance
CREATE INDEX IF NOT EXISTS ix_login_codes_email ON login_codes (email);
CREATE INDEX IF NOT EXISTS ix_login_codes_code_hash ON login_codes (code_hash);
CREATE INDEX IF NOT EXISTS ix_login_codes_consumed_at ON login_codes (consumed_at);
CREATE INDEX IF NOT EXISTS ix_login_codes_expires_at ON login_codes (expires_at);

COMMIT;
"""

HOTFIX_LOGIN_CODES_REPORTS_V1 = """
-- Idempotent hotfix: prepare login_codes & reports for magic-code login and report status
BEGIN;

CREATE TABLE IF NOT EXISTS login_codes (
    id BIGSERIAL PRIMARY KEY
);

ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS email       TEXT;
ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS code_hash   VARCHAR(64);
ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS created_at  TIMESTAMPTZ DEFAULT now();
ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS expires_at  TIMESTAMPTZ;
ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS consumed_at TIMESTAMPTZ;
ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS attempts    INTEGER DEFAULT 0;
ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS ip         TEXT;

-- Make 'used' optional if it exists
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'login_codes' AND column_name = 'used'
    ) THEN
        ALTER TABLE login_codes ALTER COLUMN used DROP NOT NULL;
        ALTER TABLE login_codes ALTER COLUMN used SET DEFAULT false;
    END IF;
END $$;

UPDATE login_codes SET email = COALESCE(email, '') WHERE email IS NULL;
UPDATE login_codes SET code_hash = COALESCE(code_hash, substr(md5(random()::text),1,64)) WHERE code_hash IS NULL;

ALTER TABLE login_codes ALTER COLUMN email SET NOT NULL;
ALTER TABLE login_codes ALTER COLUMN code_hash SET NOT NULL;

CREATE INDEX IF NOT EXISTS ix_login_codes_email       ON login_codes (email);
CREATE INDEX IF NOT EXISTS ix_login_codes_consumed_at ON login_codes (consumed_at);
CREATE INDEX IF NOT EXISTS ix_login_codes_created_at  ON login_codes (created_at);
CREATE INDEX IF NOT EXISTS ix_login_codes_code_hash   ON login_codes (code_hash);

CREATE TABLE IF NOT EXISTS reports ( id BIGSERIAL PRIMARY KEY );

ALTER TABLE reports ADD COLUMN IF NOT EXISTS user_id        BIGINT;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS briefing_id    BIGINT;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS analysis_id    BIGINT;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS status         TEXT;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS pdf_url        TEXT;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS pdf_bytes_len  INTEGER;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS user_email     TEXT;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS created_at     TIMESTAMPTZ DEFAULT now();
ALTER TABLE reports ADD COLUMN IF NOT EXISTS updated_at     TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS ix_reports_user_email ON reports (user_email);
CREATE INDEX IF NOT EXISTS ix_reports_status     ON reports (status);
CREATE INDEX IF NOT EXISTS ix_reports_created_at ON reports (created_at);

COMMIT;
"""

HOTFIXES = {
    "login_codes_v2": HOTFIX_LOGIN_CODES_V2,
    "login_codes_reports_v1": HOTFIX_LOGIN_CODES_REPORTS_V1,
}
