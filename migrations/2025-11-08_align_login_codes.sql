-- migrations/2025-11-08_align_login_codes.sql
-- Vereinheitlicht das Schema (optional). Führt "code" zusätzlich ein und
-- spiegelt den Hash aus code_hash, falls "code" später genutzt werden soll.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='login_codes' AND column_name='code'
  ) THEN
    ALTER TABLE login_codes ADD COLUMN code TEXT;
    UPDATE login_codes SET code = code_hash WHERE code IS NULL AND code_hash IS NOT NULL;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='login_codes' AND column_name='created_at'
  ) THEN
    ALTER TABLE login_codes ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW();
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='login_codes' AND column_name='expires_at'
  ) THEN
    ALTER TABLE login_codes ADD COLUMN expires_at TIMESTAMPTZ;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='login_codes' AND column_name='consumed_at'
  ) THEN
    ALTER TABLE login_codes ADD COLUMN consumed_at TIMESTAMPTZ;
  END IF;
END $$;