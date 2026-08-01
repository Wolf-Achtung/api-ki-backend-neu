-- Migration: anthropic_usage (KIS-1270 — Prompt-Caching-Wirtschaftlichkeit)
-- Persistiert die [CACHE-USAGE]-Daten je Call; cost_usd cache-korrekt.

BEGIN;

CREATE TABLE IF NOT EXISTS anthropic_usage (
    id          BIGSERIAL PRIMARY KEY,
    call_site   VARCHAR(120) NOT NULL,
    model       VARCHAR(80)  NOT NULL,
    input_tokens                 INTEGER NOT NULL DEFAULT 0,
    cache_creation_input_tokens  INTEGER NOT NULL DEFAULT 0,
    cache_read_input_tokens      INTEGER NOT NULL DEFAULT 0,
    output_tokens                INTEGER NOT NULL DEFAULT 0,
    cost_usd    DOUBLE PRECISION NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_anthropic_usage_call_site  ON anthropic_usage (call_site);
CREATE INDEX IF NOT EXISTS ix_anthropic_usage_model      ON anthropic_usage (model);
CREATE INDEX IF NOT EXISTS ix_anthropic_usage_created_at ON anthropic_usage (created_at);

COMMIT;
