#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Emergency Hotfix Script - Repariert Login-Problem direkt in der Datenbank

Usage:
    python fix_login_schema.py

Voraussetzungen:
    - psycopg2 installiert: pip install psycopg2-binary
    - DATABASE_URL in .env oder als Umgebungsvariable
"""

import os
import sys
from urllib.parse import urlparse

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("❌ psycopg2 nicht gefunden!")
    print("   Installation: pip install psycopg2-binary")
    sys.exit(1)


HOTFIX_SQL = """
-- CRITICAL FIX: Remove NOT NULL constraint from 'used' column and set default
BEGIN;

-- 1. Make 'used' column nullable if it exists
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'login_codes' AND column_name = 'used'
    ) THEN
        ALTER TABLE login_codes ALTER COLUMN used DROP NOT NULL;
        ALTER TABLE login_codes ALTER COLUMN used SET DEFAULT false;
        UPDATE login_codes SET used = false WHERE used IS NULL;
        RAISE NOTICE '✓ Fixed used column';
    ELSE
        RAISE NOTICE '✓ used column does not exist (OK)';
    END IF;
END $$;

-- 2. Ensure consumed_at column exists
ALTER TABLE login_codes ADD COLUMN IF NOT EXISTS consumed_at TIMESTAMPTZ;

-- 3. Migrate data: if 'used' is true, set consumed_at to created_at
UPDATE login_codes 
SET consumed_at = created_at 
WHERE used = true AND consumed_at IS NULL;

-- 4. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_login_codes_email ON login_codes (email);
CREATE INDEX IF NOT EXISTS idx_login_codes_code_hash ON login_codes (code_hash);
CREATE INDEX IF NOT EXISTS idx_login_codes_consumed_at ON login_codes (consumed_at);
CREATE INDEX IF NOT EXISTS idx_login_codes_expires_at ON login_codes (expires_at);

COMMIT;
"""


def get_database_url():
    """Get DATABASE_URL from environment or .env file"""
    # Try environment first
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url
    
    # Try .env file
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                if line.startswith("DATABASE_URL="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    
    return None


def parse_database_url(url):
    """Parse postgres:// or postgresql:// URL"""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    
    parsed = urlparse(url)
    return {
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/"),
        "user": parsed.username,
        "password": parsed.password,
    }


def apply_hotfix(db_url):
    """Apply the hotfix SQL to the database"""
    print("🔧 Starte Hotfix...")
    print()
    
    # Parse URL
    db_params = parse_database_url(db_url)
    print(f"📡 Verbinde zu: {db_params['host']}:{db_params['port']}/{db_params['database']}")
    
    try:
        # Connect
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✅ Verbindung erfolgreich")
        print()
        
        # Execute hotfix
        print("⚙️  Führe Hotfix aus...")
        cursor.execute(HOTFIX_SQL)
        
        # Get all notices
        for notice in conn.notices:
            print(f"   {notice.strip()}")
        
        print()
        print("✨ Hotfix erfolgreich angewendet!")
        print()
        
        # Verify
        cursor.execute("""
            SELECT column_name, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'login_codes' 
              AND column_name IN ('used', 'consumed_at')
            ORDER BY column_name
        """)
        
        print("📊 Schema-Status:")
        for row in cursor.fetchall():
            col_name, nullable, default = row
            print(f"   - {col_name}: nullable={nullable}, default={default}")
        
        print()
        print("✅ Login sollte jetzt funktionieren!")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False


def main():
    print("=" * 60)
    print("🔧 Emergency Login Hotfix Script")
    print("=" * 60)
    print()
    
    # Get database URL
    db_url = get_database_url()
    
    if not db_url:
        print("❌ DATABASE_URL nicht gefunden!")
        print()
        print("Bitte setze DATABASE_URL:")
        print("  1. Als Umgebungsvariable: export DATABASE_URL='...'")
        print("  2. In .env Datei: DATABASE_URL=...")
        print()
        sys.exit(1)
    
    # Show masked URL
    masked = db_url.split("@")[-1] if "@" in db_url else "localhost"
    print(f"🔍 Gefundene DB: ...@{masked}")
    print()
    
    # Confirm
    response = input("Hotfix ausführen? (y/N): ").strip().lower()
    if response != "y":
        print("Abgebrochen.")
        sys.exit(0)
    
    print()
    
    # Apply
    success = apply_hotfix(db_url)
    
    print()
    print("=" * 60)
    
    if success:
        print("🎉 Fertig! Teste jetzt das Login:")
        print("   https://make.ki-sicherheit.jetzt/login")
        sys.exit(0)
    else:
        print("❌ Hotfix fehlgeschlagen. Bitte Logs prüfen.")
        sys.exit(1)


if __name__ == "__main__":
    main()
