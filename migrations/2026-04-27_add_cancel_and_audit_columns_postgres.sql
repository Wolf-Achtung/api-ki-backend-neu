-- Migration: Add cancel + audit columns to briefings table (PostgreSQL)
-- Sprint: Admin-Cancel + Whitelist-Enforcement Hotfix
-- Idempotent via IF NOT EXISTS.

ALTER TABLE briefings ADD COLUMN IF NOT EXISTS cancel_reason TEXT;
ALTER TABLE briefings ADD COLUMN IF NOT EXISTS cancelled_at  TIMESTAMP WITH TIME ZONE;
ALTER TABLE briefings ADD COLUMN IF NOT EXISTS source        TEXT;
ALTER TABLE briefings ADD COLUMN IF NOT EXISTS request_ip    TEXT;
ALTER TABLE briefings ADD COLUMN IF NOT EXISTS request_ua    TEXT;

CREATE INDEX IF NOT EXISTS ix_briefings_cancelled_at ON briefings (cancelled_at);
