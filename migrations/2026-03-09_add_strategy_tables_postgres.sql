-- Migration: Add strategy_questions and strategy_reports tables for Report 3 (KI-Strategiebericht)
-- Date: 2026-03-09
-- Author: Claude Code
-- NOTE: DO NOT auto-apply. Wolf applies this manually after review.

BEGIN;

-- =============================================================================
-- Table: strategy_questions
-- Stores the additional questions (S1-S10) for the strategy report.
-- One entry per briefing.
-- =============================================================================
CREATE TABLE IF NOT EXISTS strategy_questions (
    id SERIAL PRIMARY KEY,
    briefing_id INTEGER NOT NULL REFERENCES briefings(id) ON DELETE CASCADE,

    -- Pflichtfragen S1-S7
    s1_budget VARCHAR(50) NOT NULL,           -- "Unter 5.000€" / "5.000–15.000€" / etc.
    s2_zeitrahmen VARCHAR(50) NOT NULL,       -- "Sofort (1-3 Monate)" / etc.
    s3_prioritaeten JSONB NOT NULL,           -- ["Kosten senken", "Umsatz steigern", ...]  (max 3)
    s4_engpass VARCHAR(100) NOT NULL,         -- "Zu wenig Know-how" / etc.
    s5_software TEXT,                          -- Freitext, max 200 Zeichen
    s6_foerderinteresse VARCHAR(50) NOT NULL, -- "Ja, dringend" / etc.
    s7_entscheidung VARCHAR(100) NOT NULL,    -- "Entscheide allein" / etc.

    -- Optionale Fragen S8-S10
    s8_erfahrung VARCHAR(50),                 -- "Noch keine" / "Experimentiert" / etc.
    s9_ansatz VARCHAR(50),                    -- "Cloud-SaaS" / "On-Premise" / etc.
    s10_datenschutz VARCHAR(50),              -- "Hoch" / "Mittel" / "Niedrig"

    -- Metadaten
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ein Eintrag pro Briefing
    UNIQUE(briefing_id)
);

CREATE INDEX IF NOT EXISTS ix_strategy_questions_briefing_id ON strategy_questions(briefing_id);

-- =============================================================================
-- Table: strategy_reports
-- Tracks status, cached research/calculations, generated sections, PDF, and email
-- for each strategy report. One entry per briefing.
-- =============================================================================
CREATE TABLE IF NOT EXISTS strategy_reports (
    id SERIAL PRIMARY KEY,
    briefing_id INTEGER NOT NULL REFERENCES briefings(id) ON DELETE CASCADE,

    -- Status
    status VARCHAR(30) DEFAULT 'pending' NOT NULL,  -- pending / researching / generating / completed / failed

    -- Recherche-Ergebnisse (JSON, gecached)
    research_context JSONB,

    -- Berechnete Werte (vom Backend-Calculator)
    calculated_values JSONB,

    -- Generierte Sections (JSON, jede Section separat)
    sections JSONB,

    -- PDF
    pdf_available BOOLEAN DEFAULT FALSE NOT NULL,
    pdf_generated_at TIMESTAMP WITH TIME ZONE,

    -- Email
    email_sent BOOLEAN DEFAULT FALSE NOT NULL,
    email_sent_at TIMESTAMP WITH TIME ZONE,

    -- Timing
    research_duration_seconds FLOAT,
    generation_duration_seconds FLOAT,
    total_duration_seconds FLOAT,

    -- Payment (Platzhalter für Mollie)
    payment_status VARCHAR(30) DEFAULT 'beta' NOT NULL,  -- beta / paid / free
    payment_id VARCHAR(100),

    -- Metadaten
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ein Eintrag pro Briefing
    UNIQUE(briefing_id)
);

CREATE INDEX IF NOT EXISTS ix_strategy_reports_briefing_id ON strategy_reports(briefing_id);
CREATE INDEX IF NOT EXISTS ix_strategy_reports_status ON strategy_reports(status);

COMMIT;
