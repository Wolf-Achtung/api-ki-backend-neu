-- ============================================================
-- HOTFIX: Briefings sofort canceln (Notfall-Tool)
--
-- Voraussetzung: Migration 2026-04-27_add_cancel_and_audit_columns_postgres.sql
-- ist gelaufen (cancel_reason, cancelled_at-Spalten existieren). Bei Container-
-- Restart laufen ALTERs aus core/migrate.py automatisch — kein manueller Schritt.
--
-- Verwendung (Komma-Liste, KEINE Quotes pro ID):
--   psql "$DATABASE_URL" -v briefing_ids="1040,1050" -f ops/cancel_briefings.sql
--
-- Aktive Status (lt. Worker-Code workers/briefings_worker.py:166,185):
--   accepted | queued | processing | analyzing
-- Terminal: done | failed | skipped | error | cancelled
-- ============================================================

\set ON_ERROR_STOP on

-- 1. Sanity-Check: was würde gecancelt? (vorher anzeigen)
SELECT b.id,
       u.email AS user_email,
       b.status,
       b.created_at,
       b.accepted_at,
       b.processing_at,
       b.worker_id,
       b.source,
       b.request_ip
  FROM briefings b
  LEFT JOIN users u ON u.id = b.user_id
 WHERE b.id = ANY(string_to_array(:'briefing_ids', ',')::int[])
 ORDER BY b.id;

-- 2. Cancel — nur wenn Job noch aktiv ist
UPDATE briefings
   SET status        = 'cancelled',
       worker_id     = NULL,
       cancel_reason = 'admin_manual_cancel',
       cancelled_at  = NOW()
 WHERE id = ANY(string_to_array(:'briefing_ids', ',')::int[])
   AND status IN ('accepted', 'queued', 'processing', 'analyzing');

-- 3. Bestätigung
SELECT id, status, cancel_reason, cancelled_at, worker_id
  FROM briefings
 WHERE id = ANY(string_to_array(:'briefing_ids', ',')::int[])
 ORDER BY id;
