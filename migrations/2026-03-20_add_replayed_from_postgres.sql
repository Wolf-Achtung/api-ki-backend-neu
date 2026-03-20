-- Migration: Add replayed_from column to briefings table (PostgreSQL)
-- Purpose: Track source briefing ID for replay deduplication
-- Date: 2026-03-20

ALTER TABLE briefings ADD COLUMN IF NOT EXISTS replayed_from INTEGER;
CREATE INDEX IF NOT EXISTS ix_briefings_replayed_from ON briefings (replayed_from);
