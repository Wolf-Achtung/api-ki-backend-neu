-- Sprint 1027.3 / Item H: Pre-/Post-Healer-Section-Snapshots in analyses.
--
-- Spalte raw_sections speichert ein zweistufiges JSONB-Dict:
--   {"pre_healer":  {"EXECUTIVE_DECISION_HTML": "<html>...", ...},
--    "post_healer": {"EXECUTIVE_DECISION_HTML": "<html>...", ...}}
--
-- Diagnose-Query-Beispiel:
--   SELECT raw_sections->'pre_healer'->>'EXECUTIVE_DECISION_HTML'
--        = raw_sections->'post_healer'->>'EXECUTIVE_DECISION_HTML'
--          AS healer_unchanged
--   FROM analyses WHERE id = <analysis_id>;
--
-- GIN-Index begründet: Diagnose-Queries der Form
--   WHERE raw_sections @> '{...}' / raw_sections ? 'key' / @?
-- sind ohne Index Full-Scan auf einer wachsenden Tabelle.

ALTER TABLE analyses
  ADD COLUMN IF NOT EXISTS raw_sections JSONB DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_analyses_raw_sections_gin
  ON analyses USING GIN (raw_sections);
