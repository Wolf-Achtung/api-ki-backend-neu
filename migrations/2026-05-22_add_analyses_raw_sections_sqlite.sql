-- Sprint 1027.3 / Item H: Pre-/Post-Healer-Section-Snapshots in analyses.
-- SQLite-Variant: Spalte als JSON (= TEXT mit JSON1-Extension);
-- kein GIN-Index (SQLite kennt keine GIN-Indizes — JSON1 erlaubt
-- json_extract über regulärem Index, falls künftig nötig).
-- Tests/Lokal-Dev werden auf SQLite gefahren; Production läuft auf
-- Postgres (siehe migrations/2026-05-22_add_analyses_raw_sections_postgres.sql).

ALTER TABLE analyses ADD COLUMN raw_sections JSON DEFAULT NULL;
