-- Migration: report_type auf briefings (SQLite-Variante)
-- SQLite kennt kein IF NOT EXISTS fuer Spalten; Fehler beim Re-Run sind erwartet.

ALTER TABLE briefings ADD COLUMN report_type VARCHAR(20) NOT NULL DEFAULT 'r1';
