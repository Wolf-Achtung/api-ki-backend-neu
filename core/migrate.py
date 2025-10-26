# -*- coding: utf-8 -*-
"""
Idempotente Datenbankmigrationen - können mehrfach ausgeführt werden.
Erstellt alle benötigten Tabellen und Indizes schema-tolerant.
"""
from __future__ import annotations

import logging
from sqlalchemy import text
from sqlalchemy.engine import Engine

log = logging.getLogger(__name__)


def run_migrations(engine: Engine) -> None:
    """
    Führt alle Migrationen aus (idempotent).
    
    Schema-Update-Strategie:
    1. Tabellen erstellen (IF NOT EXISTS)
    2. Spalten hinzufügen (IF NOT EXISTS via information_schema Check)
    3. Constraints/Indizes erstellen (IF NOT EXISTS)
    """
    log.info("Starting database migrations...")
    
    with engine.begin() as conn:
        # ====================================================================
        # USERS Tabelle
        # ====================================================================
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT now(),
                last_login_at TIMESTAMPTZ
            );
        """))
        
        # Unique Index auf email (case-insensitive)
        conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE tablename = 'users' AND indexname = 'ix_users_email_lower'
                ) THEN
                    CREATE UNIQUE INDEX ix_users_email_lower ON users (LOWER(email));
                END IF;
            END $$;
        """))
        
        log.info("✓ users table ready")
        
        # ====================================================================
        # LOGIN_CODES Tabelle (für Magic-Code Auth)
        # ====================================================================
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS login_codes (
                id SERIAL PRIMARY KEY,
                email TEXT NOT NULL,
                code VARCHAR(64) NOT NULL,
                purpose VARCHAR(40) DEFAULT 'login',
                created_at TIMESTAMPTZ DEFAULT now(),
                expires_at TIMESTAMPTZ NOT NULL,
                consumed_at TIMESTAMPTZ,
                attempts INTEGER DEFAULT 0,
                ip_address VARCHAR(64),
                user_agent TEXT
            );
        """))
        
        # WICHTIG: user_id Spalte entfernen falls sie existiert (legacy cleanup)
        conn.execute(text("""
            DO $$ BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                      AND table_name = 'login_codes' 
                      AND column_name = 'user_id'
                ) THEN
                    -- Erst Foreign Key Constraint droppen falls vorhanden
                    IF EXISTS (
                        SELECT 1 FROM pg_constraint 
                        WHERE conname = 'fk_login_codes_user_id'
                    ) THEN
                        ALTER TABLE login_codes DROP CONSTRAINT fk_login_codes_user_id;
                    END IF;
                    
                    -- Dann Spalte droppen
                    ALTER TABLE login_codes DROP COLUMN user_id;
                    RAISE NOTICE 'Dropped legacy user_id column from login_codes';
                END IF;
            END $$;
        """))
        
        # Indizes
        for idx in [
            "CREATE INDEX IF NOT EXISTS ix_login_codes_email ON login_codes(LOWER(email))",
            "CREATE INDEX IF NOT EXISTS ix_login_codes_code ON login_codes(code)",
            "CREATE INDEX IF NOT EXISTS ix_login_codes_consumed_at ON login_codes(consumed_at)",
            "CREATE INDEX IF NOT EXISTS ix_login_codes_created_at ON login_codes(created_at)",
            "CREATE INDEX IF NOT EXISTS ix_login_codes_expires_at ON login_codes(expires_at)",
        ]:
            conn.execute(text(idx))
        
        log.info("✓ login_codes table ready")
        
        # ====================================================================
        # LOGIN_AUDIT Tabelle (für Rate-Limiting und Compliance)
        # ====================================================================
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS login_audit (
                id BIGSERIAL PRIMARY KEY,
                ts TIMESTAMPTZ DEFAULT now(),
                email TEXT,
                ip TEXT,
                action TEXT,
                status TEXT,
                user_agent TEXT,
                detail TEXT
            );
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_login_audit_email_ts 
            ON login_audit(LOWER(email), ts DESC);
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_login_audit_ip_ts 
            ON login_audit(ip, ts DESC);
        """))
        
        log.info("✓ login_audit table ready")
        
        # ====================================================================
        # BRIEFINGS Tabelle
        # ====================================================================
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS briefings (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                lang VARCHAR(5) DEFAULT 'de',
                answers JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ DEFAULT now()
            );
        """))
        
        # Foreign Key (falls users existiert)
        conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'fk_briefings_user_id'
                ) THEN
                    ALTER TABLE briefings 
                    ADD CONSTRAINT fk_briefings_user_id 
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
                END IF;
            END $$;
        """))
        
        # Indizes
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_briefings_user_id ON briefings(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_briefings_created_at ON briefings(created_at DESC)"))
        
        log.info("✓ briefings table ready")
        
        # ====================================================================
        # BRIEFING_DRAFTS Tabelle (für Draft-Speicherung)
        # ====================================================================
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS briefing_drafts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                lang VARCHAR(5) DEFAULT 'de',
                payload JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ DEFAULT now(),
                updated_at TIMESTAMPTZ DEFAULT now()
            );
        """))
        
        # Spalte "email" hinzufügen falls sie nicht existiert
        conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                      AND table_name = 'briefing_drafts' 
                      AND column_name = 'email'
                ) THEN
                    ALTER TABLE briefing_drafts ADD COLUMN email TEXT;
                END IF;
            END $$;
        """))
        
        # Unique constraint für email (ein Draft pro Email)
        conn.execute(text("""
            DO $$ BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                      AND table_name = 'briefing_drafts' 
                      AND column_name = 'email'
                ) AND NOT EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'uq_briefing_drafts_email'
                ) THEN
                    ALTER TABLE briefing_drafts 
                    ADD CONSTRAINT uq_briefing_drafts_email UNIQUE (email);
                END IF;
            END $$;
        """))
        
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_briefing_drafts_user_id ON briefing_drafts(user_id)"))
        
        # Index auf email nur wenn Spalte existiert
        conn.execute(text("""
            DO $$ BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                      AND table_name = 'briefing_drafts' 
                      AND column_name = 'email'
                ) AND NOT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE tablename = 'briefing_drafts' 
                      AND indexname = 'ix_briefing_drafts_email'
                ) THEN
                    CREATE INDEX ix_briefing_drafts_email ON briefing_drafts(LOWER(email));
                END IF;
            END $$;
        """))
        
        log.info("✓ briefing_drafts table ready")
        
        # ====================================================================
        # ANALYSES Tabelle
        # ====================================================================
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS analyses (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                briefing_id INTEGER,
                html TEXT,
                meta JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ DEFAULT now()
            );
        """))
        
        # Foreign Keys
        conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_analyses_briefing_id') THEN
                    ALTER TABLE analyses 
                    ADD CONSTRAINT fk_analyses_briefing_id 
                    FOREIGN KEY (briefing_id) REFERENCES briefings(id) ON DELETE SET NULL;
                END IF;
            END $$;
        """))
        
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_analyses_briefing_id ON analyses(briefing_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_analyses_created_at ON analyses(created_at DESC)"))
        
        log.info("✓ analyses table ready")
        
        # ====================================================================
        # REPORTS Tabelle
        # ====================================================================
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS reports (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                briefing_id INTEGER,
                analysis_id INTEGER,
                user_email TEXT,
                status TEXT DEFAULT 'pending',
                pdf_url TEXT,
                pdf_bytes_len INTEGER,
                email_sent_user BOOLEAN DEFAULT FALSE,
                email_sent_admin BOOLEAN DEFAULT FALSE,
                email_error_user TEXT,
                email_error_admin TEXT,
                created_at TIMESTAMPTZ DEFAULT now(),
                updated_at TIMESTAMPTZ
            );
        """))
        
        # Foreign Keys
        for fk_sql in [
            """DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_reports_briefing_id') THEN
                    ALTER TABLE reports ADD CONSTRAINT fk_reports_briefing_id 
                    FOREIGN KEY (briefing_id) REFERENCES briefings(id) ON DELETE SET NULL;
                END IF;
            END $$;""",
            """DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_reports_analysis_id') THEN
                    ALTER TABLE reports ADD CONSTRAINT fk_reports_analysis_id 
                    FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE SET NULL;
                END IF;
            END $$;"""
        ]:
            conn.execute(text(fk_sql))
        
        # Indizes
        for idx in [
            "CREATE INDEX IF NOT EXISTS ix_reports_status ON reports(status)",
            "CREATE INDEX IF NOT EXISTS ix_reports_user_email ON reports(LOWER(user_email))",
            "CREATE INDEX IF NOT EXISTS ix_reports_created_at ON reports(created_at DESC)",
            "CREATE INDEX IF NOT EXISTS ix_reports_briefing_id ON reports(briefing_id)",
        ]:
            conn.execute(text(idx))
        
        log.info("✓ reports table ready")
    
    log.info("✅ All migrations completed successfully!")


def verify_schema(engine: Engine) -> dict:
    """
    Verifiziert dass alle wichtigen Tabellen existieren.
    
    Returns:
        Dict mit Status pro Tabelle
    """
    required_tables = [
        "users",
        "login_codes",
        "login_audit",
        "briefings",
        "briefing_drafts",
        "analyses",
        "reports",
    ]
    
    status = {}
    
    with engine.begin() as conn:
        for table in required_tables:
            result = conn.execute(
                text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                          AND table_name = :table
                    )
                """),
                {"table": table}
            ).scalar()
            
            status[table] = bool(result)
    
    return status


if __name__ == "__main__":
    # Test-Lauf
    from core.db import engine
    
    print("Running migrations...")
    run_migrations(engine)
    
    print("\nVerifying schema...")
    status = verify_schema(engine)
    
    for table, exists in status.items():
        symbol = "✓" if exists else "✗"
        print(f"  {symbol} {table}")
    
    all_ok = all(status.values())
    print(f"\n{'✅ All tables exist!' if all_ok else '⚠️  Some tables missing!'}")
