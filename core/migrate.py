# -*- coding: utf-8 -*-
"""Database migration module for KI-Backend (synchron, mit kompatiblem async-Wrapper)."""
import logging
from sqlalchemy import text
from core.db import engine

logger = logging.getLogger("core.migrate")

DDL = [
    # users
    """    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        last_login TIMESTAMP WITH TIME ZONE,
        is_active BOOLEAN DEFAULT TRUE,
        is_admin BOOLEAN DEFAULT FALSE
    )""",

    # login_codes (mit code_hash)
    """    CREATE TABLE IF NOT EXISTS login_codes (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        code_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
        consumed_at TIMESTAMP WITH TIME ZONE,
        attempts INTEGER DEFAULT 0,
        ip_address VARCHAR(45)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_login_codes_email  ON login_codes(email)",
    "CREATE INDEX IF NOT EXISTS idx_login_codes_expires ON login_codes(expires_at)",

    # login_audit
    """    CREATE TABLE IF NOT EXISTS login_audit (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        action VARCHAR(50) NOT NULL,
        success BOOLEAN NOT NULL,
        ip_address VARCHAR(45),
        user_agent TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    )""",
    "CREATE INDEX IF NOT EXISTS idx_login_audit_email ON login_audit(email)",

    # briefings
    """    CREATE TABLE IF NOT EXISTS briefings (
        id SERIAL PRIMARY KEY,
        title VARCHAR(500) NOT NULL,
        content TEXT NOT NULL,
        topic VARCHAR(200) NOT NULL,
        language VARCHAR(10) DEFAULT 'de',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        published_at TIMESTAMP WITH TIME ZONE,
        is_draft BOOLEAN DEFAULT TRUE,
        author_email VARCHAR(255),
        metadata JSONB DEFAULT '{}'::jsonb
    )""",

    # briefing_drafts
    """    CREATE TABLE IF NOT EXISTS briefing_drafts (
        id SERIAL PRIMARY KEY,
        briefing_id INTEGER REFERENCES briefings(id) ON DELETE CASCADE,
        content TEXT NOT NULL,
        version INTEGER NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        created_by VARCHAR(255)
    )""",

    # analyses
    """    CREATE TABLE IF NOT EXISTS analyses (
        id SERIAL PRIMARY KEY,
        user_email VARCHAR(255) NOT NULL,
        company_name VARCHAR(500),
        analysis_data JSONB NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        completed_at TIMESTAMP WITH TIME ZONE,
        status VARCHAR(50) DEFAULT 'pending'
    )""",

    # reports
    """    CREATE TABLE IF NOT EXISTS reports (
        id SERIAL PRIMARY KEY,
        analysis_id INTEGER REFERENCES analyses(id) ON DELETE CASCADE,
        user_email VARCHAR(255) NOT NULL,
        report_data JSONB NOT NULL,
        pdf_url VARCHAR(1000),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        downloaded_at TIMESTAMP WITH TIME ZONE
    )"""
]

def migrate_all_sync() -> None:
    logger.info("Starting database migrations (sync)...")
    with engine.begin() as conn:
        for ddl in DDL:
            conn.execute(text(ddl))
    logger.info("✅ All migrations completed successfully (sync)")

# Kompatibler async-Wrapper (ruft die sync-Variante auf)
async def migrate_all() -> None:  # pragma: no cover
    migrate_all_sync()
