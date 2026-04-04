-- Migration: Add S-Moat fields to strategy_questions table
-- Date: 2026-04-04
-- Purpose: Three new optional fields for the "KI-gestützter Wettbewerbsvorteil" section
-- NOTE: DO NOT auto-apply. Wolf applies this manually after review.

BEGIN;

ALTER TABLE strategy_questions
    ADD COLUMN IF NOT EXISTS wettbewerber_anzahl VARCHAR(50),
    ADD COLUMN IF NOT EXISTS kundenbindung_typ VARCHAR(50),
    ADD COLUMN IF NOT EXISTS datenreife VARCHAR(50);

COMMENT ON COLUMN strategy_questions.wettbewerber_anzahl IS 'wenige | mehrere | viele | unklar | NULL';
COMMENT ON COLUMN strategy_questions.kundenbindung_typ IS 'einmalig | wiederkehrend | gemischt | NULL';
COMMENT ON COLUMN strategy_questions.datenreife IS 'keine | basis | umfangreich | unklar | NULL';

COMMIT;
