-- Migration: Add reports_history table for report versioning (Sprint G11)
-- Date: 2026-04-01
-- Author: Claude Code (KIS-1098-BE-4)
-- NOTE: DO NOT auto-apply. Wolf applies this manually after review.

BEGIN;

-- =============================================================================
-- Table: reports_history
-- Stores complete snapshots of reports for version comparison,
-- delta analysis, and historical tracking.
-- =============================================================================
CREATE TABLE IF NOT EXISTS reports_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    version INTEGER NOT NULL DEFAULT 1,

    -- Core scores (Governance, Security, Benefit, etc.)
    scores_json JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Business Case data (CAPEX, OPEX, ROI, Payback)
    bc_json JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- AI Act compliance data (Risk Level, Modifiers, Metrics)
    ai_act_json JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Labels (BRANCH_*, OFFERING_*, CR_LABELS)
    labels_json JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Section word counts for delta comparison
    section_stats_json JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- File paths
    html_path VARCHAR(512),
    pdf_path VARCHAR(512),

    -- Metadata
    lang VARCHAR(5) NOT NULL DEFAULT 'de',
    size_category VARCHAR(32),

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- One version per report
    UNIQUE(report_id, version)
);

CREATE INDEX IF NOT EXISTS ix_reports_history_user_report ON reports_history(user_id, report_id);
CREATE INDEX IF NOT EXISTS ix_reports_history_created_at ON reports_history(created_at);
CREATE INDEX IF NOT EXISTS ix_reports_history_report_id ON reports_history(report_id);
CREATE INDEX IF NOT EXISTS ix_reports_history_user_id ON reports_history(user_id);

COMMIT;
