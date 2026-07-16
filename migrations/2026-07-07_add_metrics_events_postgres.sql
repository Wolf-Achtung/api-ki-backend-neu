-- Migration: metrics_events (KIS-1269 — cookiefreie Reichweitenmessung)
-- Anonyme Zaehl-Events, keine IP, keine User-Referenz.

BEGIN;

CREATE TABLE IF NOT EXISTS metrics_events (
    id          BIGSERIAL PRIMARY KEY,
    event       VARCHAR(40) NOT NULL,
    page        VARCHAR(120),
    lang        VARCHAR(8),
    ref         VARCHAR(120),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_metrics_events_event ON metrics_events (event);
CREATE INDEX IF NOT EXISTS ix_metrics_events_created_at ON metrics_events (created_at);

COMMIT;
