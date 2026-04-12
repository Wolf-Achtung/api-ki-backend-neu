-- Sprint 1: Draft-Pattern Infrastructure
-- Adds draft_state JSONB column to chat_sessions for pending field tracking.
-- Default empty object — backward compatible, no impact on existing sessions.

ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS draft_state JSONB DEFAULT '{}'::jsonb;
