# -*- coding: utf-8 -*-
"""Predefined SQL hotfixes that can be applied via the admin endpoint.
All scripts are idempotent and safe to run multiple times.
"""
from __future__ import annotations

HOTFIX_LOGIN_CODES_REPORTS_V1 = """
-- Idempotent hotfix: prepare login_codes & reports for magic-code login and report status
BEGIN;

CREATE TABLE IF NOT EXISTS login_codes (
    id BIGSERIAL PRIMARY KEY
);

ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS email       TEXT;
ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS code        VARCHAR(64);
ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS created_at  TIMESTAMPTZ DEFAULT now();
ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS expires_at  TIMESTAMPTZ;
ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS consumed_at TIMESTAMPTZ;

UPDATE login_codes SET email = COALESCE(email, '') WHERE email IS NULL;
UPDATE login_codes SET code  = COALESCE(code,  substr(md5(random()::text),1,6)) WHERE code IS NULL;

ALTER TABLE login_codes ALTER COLUMN email SET NOT NULL;
ALTER TABLE login_codes ALTER COLUMN code  SET NOT NULL;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='uq_login_codes_code') THEN
    ALTER TABLE login_codes ADD CONSTRAINT uq_login_codes_code UNIQUE (code);
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_login_codes_email       ON login_codes (email);
CREATE INDEX IF NOT EXISTS ix_login_codes_consumed_at ON login_codes (consumed_at);
CREATE INDEX IF NOT EXISTS ix_login_codes_created_at  ON login_codes (created_at);

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
    "login_codes_reports_v1": HOTFIX_LOGIN_CODES_REPORTS_V1,
}