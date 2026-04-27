# -*- coding: utf-8 -*-
from __future__ import annotations
"""Synchrones Migrations‑Hilfsmodul (SQLAlchemy 2.x)
- nutzt Engine.begin() Kontext für atomare Transaktionen
- kompatibel zu psycopg v3
- Idempotenz: CREATE TABLE IF NOT EXISTS + CREATE INDEX IF NOT EXISTS
"""
from sqlalchemy import text
from sqlalchemy.engine import Engine
import logging

log = logging.getLogger("core.migrate")

DDL = [
    # users
    text("""    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        last_login TIMESTAMPTZ,
        is_active BOOLEAN DEFAULT TRUE,
        is_admin BOOLEAN DEFAULT FALSE
    )"""),
    # login_codes
    text("""    CREATE TABLE IF NOT EXISTS login_codes (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        code_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        expires_at TIMESTAMPTZ NOT NULL,
        consumed_at TIMESTAMPTZ,
        attempts INTEGER DEFAULT 0,
        ip_address VARCHAR(45)
    )"""),
    text("CREATE INDEX IF NOT EXISTS idx_login_codes_email ON login_codes(email)"),
    text("CREATE INDEX IF NOT EXISTS idx_login_codes_expires ON login_codes(expires_at)"),
    # login_audit
    text("""    CREATE TABLE IF NOT EXISTS login_audit (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        action VARCHAR(50) NOT NULL,
        success BOOLEAN NOT NULL,
        ip_address VARCHAR(45),
        user_agent TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    )"""),
    text("CREATE INDEX IF NOT EXISTS idx_login_audit_email ON login_audit(email)"),
    # briefings (leichtgewichtig – answers/jsonb optional je nach Modell)
    text("""    CREATE TABLE IF NOT EXISTS briefings (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        lang VARCHAR(10) DEFAULT 'de',
        answers JSONB DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ DEFAULT NOW()
    )"""),
    # analyses
    text("""    CREATE TABLE IF NOT EXISTS analyses (
        id SERIAL PRIMARY KEY,
        briefing_id INTEGER,
        user_id INTEGER,
        analysis_data JSONB DEFAULT '{}'::jsonb,
        html TEXT,
        status VARCHAR(50) DEFAULT 'pending',
        created_at TIMESTAMPTZ DEFAULT NOW()
    )"""),
    # reports
    text("""    CREATE TABLE IF NOT EXISTS reports (
        id SERIAL PRIMARY KEY,
        briefing_id INTEGER,
        analysis_id INTEGER,
        user_email VARCHAR(255),
        report_data JSONB DEFAULT '{}'::jsonb,
        pdf_url VARCHAR(1000),
        pdf_bytes_len INTEGER,
        created_at TIMESTAMPTZ DEFAULT NOW()
    )"""),
    # feedbacks
    text("""    CREATE TABLE IF NOT EXISTS feedbacks (
        id SERIAL PRIMARY KEY,
        payload JSONB NOT NULL DEFAULT '{}'::jsonb,
        source VARCHAR(64) NOT NULL DEFAULT 'feedback_form_v1',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )"""),
    text("CREATE INDEX IF NOT EXISTS idx_feedbacks_created_at ON feedbacks(created_at)"),
    # reports_history (Sprint G11 — report versioning)
    text("""    CREATE TABLE IF NOT EXISTS reports_history (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
        version INTEGER NOT NULL DEFAULT 1,
        scores_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        bc_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        ai_act_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        labels_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        section_stats_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        html_path VARCHAR(512),
        pdf_path VARCHAR(512),
        lang VARCHAR(5) NOT NULL DEFAULT 'de',
        size_category VARCHAR(32),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE(report_id, version)
    )"""),
    text("CREATE INDEX IF NOT EXISTS ix_reports_history_user_report ON reports_history(user_id, report_id)"),
    text("CREATE INDEX IF NOT EXISTS ix_reports_history_created_at ON reports_history(created_at)"),
    text("CREATE INDEX IF NOT EXISTS ix_reports_history_report_id ON reports_history(report_id)"),
    text("CREATE INDEX IF NOT EXISTS ix_reports_history_user_id ON reports_history(user_id)"),
    # appetizer_leads (KI-Potenzial-Check)
    text("""    CREATE TABLE IF NOT EXISTS appetizer_leads (
        id SERIAL PRIMARY KEY,
        firma VARCHAR(100),
        branche VARCHAR(50) NOT NULL,
        mitarbeiter VARCHAR(10) NOT NULL,
        hauptleistung TEXT,
        zeitaufwand_repetitiv VARCHAR(20) NOT NULL,
        ki_erfahrung VARCHAR(20) NOT NULL,
        groesste_herausforderung TEXT,
        email VARCHAR(200),
        newsletter_optin BOOLEAN DEFAULT FALSE,
        score_wert INTEGER NOT NULL,
        score_einordnung VARCHAR(20) NOT NULL,
        result_json JSONB,
        created_at TIMESTAMP DEFAULT NOW(),
        converted_to_report BOOLEAN DEFAULT FALSE,
        converted_at TIMESTAMP
    )"""),
    text("CREATE INDEX IF NOT EXISTS idx_appetizer_leads_email ON appetizer_leads(email)"),
    # appetizer_analytics (anonymous, always saved)
    text("""    CREATE TABLE IF NOT EXISTS appetizer_analytics (
        id SERIAL PRIMARY KEY,
        branche VARCHAR(50) NOT NULL,
        mitarbeiter VARCHAR(10) NOT NULL,
        score_wert INTEGER NOT NULL,
        score_einordnung VARCHAR(20) NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    )"""),
    text("CREATE INDEX IF NOT EXISTS idx_appetizer_analytics_branche ON appetizer_analytics(branche)"),
    # chat_sessions (Konversationeller KI-Fragebogen)
    text("""    CREATE TABLE IF NOT EXISTS chat_sessions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        report_type VARCHAR(20) NOT NULL DEFAULT 'r1',
        lang VARCHAR(5) DEFAULT 'de',
        user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        briefing_id INTEGER REFERENCES briefings(id) ON DELETE SET NULL,
        consent_report BOOLEAN DEFAULT FALSE,
        consent_at TIMESTAMPTZ,
        collected_fields JSONB DEFAULT '{}'::jsonb,
        field_meta JSONB DEFAULT '{}'::jsonb,
        current_section INTEGER DEFAULT 0,
        status VARCHAR(20) DEFAULT 'active',
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        last_activity_at TIMESTAMPTZ DEFAULT NOW(),
        completed_at TIMESTAMPTZ,
        messages JSONB DEFAULT '[]'::jsonb,
        turn_count INTEGER DEFAULT 0,
        conversation_summary TEXT,
        draft_state JSONB DEFAULT '{}'::jsonb
    )"""),
    # FIX: draft_state column was missing — existing tables need ALTER TABLE
    text("ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS draft_state JSONB DEFAULT '{}'::jsonb"),
    # KIS-1124 Sprint 2: phase tracking for hybrid conversation model
    text("ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS phase_state JSONB DEFAULT '{}'::jsonb"),
    text("CREATE INDEX IF NOT EXISTS idx_chat_sessions_status ON chat_sessions(status)"),
    text("CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_chat_sessions_activity ON chat_sessions(last_activity_at)"),
    # Hotfix 2026-04-27: Admin-Cancel + Audit (briefings)
    text("ALTER TABLE briefings ADD COLUMN IF NOT EXISTS cancel_reason TEXT"),
    text("ALTER TABLE briefings ADD COLUMN IF NOT EXISTS cancelled_at  TIMESTAMPTZ"),
    text("ALTER TABLE briefings ADD COLUMN IF NOT EXISTS source        TEXT"),
    text("ALTER TABLE briefings ADD COLUMN IF NOT EXISTS request_ip    TEXT"),
    text("ALTER TABLE briefings ADD COLUMN IF NOT EXISTS request_ua    TEXT"),
    text("CREATE INDEX IF NOT EXISTS ix_briefings_cancelled_at ON briefings (cancelled_at)"),
]

def migrate_all(engine: Engine) -> None:
    log.info("Starting DB migrations (sync/psycopg3)...")
    with engine.begin() as conn:
        for stmt in DDL:
            conn.execute(stmt)
    log.info("✓ Migrations completed.")
