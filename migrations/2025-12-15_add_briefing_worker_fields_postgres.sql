-- Migration: Add worker queue fields to briefings table (PostgreSQL)
-- Sprint: DB-Backed Worker for /api/briefings/submit
-- Date: 2025-12-15

-- Add status column with default for existing rows
ALTER TABLE briefings ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'done';

-- Add timestamp columns
ALTER TABLE briefings ADD COLUMN IF NOT EXISTS accepted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
ALTER TABLE briefings ADD COLUMN IF NOT EXISTS processing_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE briefings ADD COLUMN IF NOT EXISTS done_at TIMESTAMP WITH TIME ZONE;

-- Add error and worker tracking
ALTER TABLE briefings ADD COLUMN IF NOT EXISTS error TEXT;
ALTER TABLE briefings ADD COLUMN IF NOT EXISTS worker_id VARCHAR(64);

-- Create index for efficient job claiming (status + accepted_at)
CREATE INDEX IF NOT EXISTS ix_briefings_status_accepted_at ON briefings (status, accepted_at);
CREATE INDEX IF NOT EXISTS ix_briefings_status ON briefings (status);

-- Mark all existing briefings as 'done' (they were already processed)
UPDATE briefings SET status = 'done', done_at = created_at WHERE status = 'done' AND done_at IS NULL;
