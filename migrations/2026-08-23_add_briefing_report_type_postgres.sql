-- Migration: report_type auf briefings — Typ-Weiche fuer den Resilienz-Check
-- Datum: 2026-08-23 (Resilienz V1, Schritt 1; Entscheidung: docs/decision-resilienz-check.md)
-- Idempotent; wird von core/migrate.py beim App-Start angewandt.

ALTER TABLE briefings ADD COLUMN IF NOT EXISTS report_type VARCHAR(20) NOT NULL DEFAULT 'r1';
CREATE INDEX IF NOT EXISTS idx_briefings_report_type ON briefings(report_type);
