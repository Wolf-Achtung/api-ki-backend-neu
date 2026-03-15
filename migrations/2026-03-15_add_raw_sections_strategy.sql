-- Add raw_sections column to strategy_reports table
-- Stores pre-sanitizer LLM outputs for re-render and sanitizer iteration
ALTER TABLE strategy_reports ADD COLUMN IF NOT EXISTS raw_sections JSONB;
