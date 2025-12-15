-- Migration: Add worker queue fields to briefings table (SQLite)
-- Sprint: DB-Backed Worker for /api/briefings/submit
-- Date: 2025-12-15

-- SQLite doesn't support IF NOT EXISTS for ALTER TABLE, so we use a different approach
-- These columns may already exist, so errors are expected if re-running

ALTER TABLE briefings ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'done';
ALTER TABLE briefings ADD COLUMN accepted_at DATETIME;
ALTER TABLE briefings ADD COLUMN processing_at DATETIME;
ALTER TABLE briefings ADD COLUMN done_at DATETIME;
ALTER TABLE briefings ADD COLUMN error TEXT;
ALTER TABLE briefings ADD COLUMN worker_id VARCHAR(64);

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_briefings_status_accepted_at ON briefings (status, accepted_at);
CREATE INDEX IF NOT EXISTS ix_briefings_status ON briefings (status);

-- Mark all existing briefings as 'done'
UPDATE briefings SET status = 'done', done_at = created_at WHERE done_at IS NULL;
