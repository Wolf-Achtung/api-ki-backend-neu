-- Migration: Add cancel + audit columns to briefings table (SQLite)
-- Sprint: Admin-Cancel + Whitelist-Enforcement Hotfix
-- SQLite 3.35+ unterstützt IF NOT EXISTS für ALTER TABLE ADD COLUMN.
-- Falls die Ziel-DB älter ist, einzeln ausführen und vorhandene Spalten überspringen.

ALTER TABLE briefings ADD COLUMN cancel_reason TEXT;
ALTER TABLE briefings ADD COLUMN cancelled_at  DATETIME;
ALTER TABLE briefings ADD COLUMN source        TEXT;
ALTER TABLE briefings ADD COLUMN request_ip    TEXT;
ALTER TABLE briefings ADD COLUMN request_ua    TEXT;

CREATE INDEX IF NOT EXISTS ix_briefings_cancelled_at ON briefings (cancelled_at);
