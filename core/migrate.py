"""Database migration module for KI-Backend"""
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import text
from core.database import get_db

logger = logging.getLogger("core.migrate")

async def migrate_all():
    """Run all database migrations"""
    logger.info("Starting database migrations...")
    
    async for db in get_db():
        try:
            # Users table
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_login TIMESTAMP WITH TIME ZONE,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_admin BOOLEAN DEFAULT FALSE
                )
            """))
            await db.commit()
            logger.info("✓ users table ready")
            
            # Login codes table - KORRIGIERT mit code_hash
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS login_codes (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) NOT NULL,
                    code_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    consumed_at TIMESTAMP WITH TIME ZONE,
                    attempts INTEGER DEFAULT 0,
                    ip_address VARCHAR(45)
                )
            """))
            
            # Index für schnellere Abfragen
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_login_codes_email 
                ON login_codes(email)
            """))
            
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_login_codes_expires 
                ON login_codes(expires_at)
            """))
            
            await db.commit()
            logger.info("✓ login_codes table ready")
            
            # Login audit table
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS login_audit (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) NOT NULL,
                    action VARCHAR(50) NOT NULL,
                    success BOOLEAN NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_login_audit_email 
                ON login_audit(email)
            """))
            
            await db.commit()
            logger.info("✓ login_audit table ready")
            
            # Briefings table
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS briefings (
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
                )
            """))
            await db.commit()
            logger.info("✓ briefings table ready")
            
            # Briefing drafts table
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS briefing_drafts (
                    id SERIAL PRIMARY KEY,
                    briefing_id INTEGER REFERENCES briefings(id) ON DELETE CASCADE,
                    content TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    created_by VARCHAR(255)
                )
            """))
            await db.commit()
            logger.info("✓ briefing_drafts table ready")
            
            # Analyses table
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id SERIAL PRIMARY KEY,
                    user_email VARCHAR(255) NOT NULL,
                    company_name VARCHAR(500),
                    analysis_data JSONB NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    completed_at TIMESTAMP WITH TIME ZONE,
                    status VARCHAR(50) DEFAULT 'pending'
                )
            """))
            await db.commit()
            logger.info("✓ analyses table ready")
            
            # Reports table
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS reports (
                    id SERIAL PRIMARY KEY,
                    analysis_id INTEGER REFERENCES analyses(id) ON DELETE CASCADE,
                    user_email VARCHAR(255) NOT NULL,
                    report_data JSONB NOT NULL,
                    pdf_url VARCHAR(1000),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    downloaded_at TIMESTAMP WITH TIME ZONE
                )
            """))
            await db.commit()
            logger.info("✓ reports table ready")
            
            logger.info("✅ All migrations completed successfully!")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Migration failed: {str(e)}")
            raise
        finally:
            await db.close()
            break  # Only run once
