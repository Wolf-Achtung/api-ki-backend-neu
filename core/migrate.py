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
]

def migrate_all(engine: Engine) -> None:
    log.info("Starting DB migrations (sync/psycopg3)...")
    with engine.begin() as conn:
        for stmt in DDL:
            conn.execute(stmt)
    log.info("✓ Migrations completed.")
