-- Migration: Add s5_vision to strategy_questions table
-- Date: 2026-07-06 (KIS-1268)
-- Purpose: Das Formular (strategy.html) sendet die "Persönliche KI-Vision"
-- seit jeher als s5_vision, aber Schema/Modell kannten das Feld nicht —
-- die Eingabe ging still verloren und {s5_vision} im Prompt blieb leer.

BEGIN;

ALTER TABLE strategy_questions
    ADD COLUMN IF NOT EXISTS s5_vision TEXT;

COMMENT ON COLUMN strategy_questions.s5_vision IS 'Persönliche KI-Vision (Freitext, optional)';

COMMIT;
