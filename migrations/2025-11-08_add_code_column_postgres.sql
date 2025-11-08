-- migrations/2025-11-08_add_code_column_postgres.sql
-- Fügt 'code' zur Tabelle 'login_codes' hinzu, falls nicht vorhanden (idempotent).
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_name='login_codes' AND column_name='code'
  ) THEN
    ALTER TABLE login_codes ADD COLUMN code TEXT;
  END IF;
END $$;