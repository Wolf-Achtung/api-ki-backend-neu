#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Setup Script für KI-Sicherheit.jetzt
Erstellt alle benötigten Tabellen und fügt Testuser + Admin ein.

Usage:
    # Option 1: Mit .env Datei
    python setup_database.py
    
    # Option 2: Mit Environment Variable
    export DATABASE_URL="postgresql://..."
    python setup_database.py
    
    # Option 3: Als Argument
    python setup_database.py --db-url "postgresql://..."

Requirements:
    pip install psycopg2-binary
    pip install python-dotenv  # Optional, nur wenn .env genutzt wird
"""
import os
import sys
import argparse
from datetime import datetime
from typing import List, Tuple

try:
    import psycopg2
    from psycopg2 import sql, extras
except ImportError:
    print("❌ Fehler: psycopg2 nicht installiert!")
    print("Installation: pip install psycopg2-binary")
    sys.exit(1)

# python-dotenv ist OPTIONAL
try:
    from dotenv import load_dotenv
    load_dotenv()
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False


# ============================================================================
# KONFIGURATION
# ============================================================================

# Testuser (normale Nutzer)
TESTUSERS: List[str] = [
    "j.hohl@freenet.de",
    "kerstin.geffert@gmail.com",
    "post@zero2.de",
    "giselapeter@peter-partner.de",
    "wolf.hohl@web.de",
    "geffertj@mac.com",
    "geffertkilian@gmail.com",
    "levent.graef@posteo.de",
    "birgit.cook@ulitzka-partner.de",
    "alexander.luckow@icloud.com",
    "frank.beer@kabelmail.de",
    "patrick@silk-relations.com",
    "marc@trailerhaus-onair.de",
    "norbert@trailerhaus.de",
    "sonia-souto@mac.com",
    "christian.ulitzka@ulitzka-partner.de",
    "srack@gmx.net",
    "buss@maria-hilft.de",
    "w.beestermoeller@web.de",
]

# Admin User
ADMIN_USER: str = "bewertung@ki-sicherheit.jetzt"


# ============================================================================
# DATENBANK CONNECTION
# ============================================================================

def get_database_url(args=None) -> str:
    """Hole DATABASE_URL aus Command-Line, Environment oder .env"""

    # 1. Priorität: Command-Line Argument
    if args and args.db_url:
        return str(args.db_url)
    
    # 2. Priorität: Environment Variable
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("❌ Fehler: DATABASE_URL nicht gefunden!")
        print("")
        print("🎯 3 Möglichkeiten:")
        print("")
        print("1️⃣  Als Argument übergeben:")
        print('   python setup_database.py --db-url "postgresql://..."')
        print("")
        print("2️⃣  Als Environment Variable setzen:")
        print('   export DATABASE_URL="postgresql://user:pass@host:port/db"')
        print('   python setup_database.py')
        print("")
        if HAS_DOTENV:
            print("3️⃣  In .env Datei:")
            print('   echo "DATABASE_URL=postgresql://..." > .env')
            print('   python setup_database.py')
        else:
            print("3️⃣  Mit .env Datei (installiere zuerst python-dotenv):")
            print('   pip install python-dotenv')
            print('   echo "DATABASE_URL=postgresql://..." > .env')
            print('   python setup_database.py')
        print("")
        sys.exit(1)
    
    return db_url


def connect_db(args=None):
    """Verbinde zur Datenbank"""
    db_url = get_database_url(args)
    
    try:
        conn = psycopg2.connect(db_url)
        return conn
    except psycopg2.Error as e:
        print(f"❌ Datenbankverbindung fehlgeschlagen: {e}")
        sys.exit(1)


# ============================================================================
# TABELLEN ERSTELLEN
# ============================================================================

def create_users_table(cursor) -> bool:
    """Erstelle users Tabelle"""
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                last_login TIMESTAMPTZ
            );
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email 
            ON users(email);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_active 
            ON users(is_active);
        """)
        
        print("✅ Tabelle 'users' erstellt")
        return True
    except psycopg2.Error as e:
        print(f"❌ Fehler beim Erstellen der users Tabelle: {e}")
        return False


def create_login_codes_table(cursor) -> bool:
    """Erstelle login_codes Tabelle"""
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_codes (
                id BIGSERIAL PRIMARY KEY,
                email TEXT NOT NULL,
                code_hash TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                expires_at TIMESTAMPTZ NOT NULL,
                consumed_at TIMESTAMPTZ,
                attempts INTEGER DEFAULT 0,
                ip TEXT
            );
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_login_codes_email 
            ON login_codes(email);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_login_codes_code_hash 
            ON login_codes(code_hash);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_login_codes_expires 
            ON login_codes(expires_at);
        """)
        
        print("✅ Tabelle 'login_codes' erstellt")
        return True
    except psycopg2.Error as e:
        print(f"❌ Fehler beim Erstellen der login_codes Tabelle: {e}")
        return False


def create_login_audit_table(cursor) -> bool:
    """Erstelle login_audit Tabelle"""
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_audit (
                id BIGSERIAL PRIMARY KEY,
                email TEXT,
                ip TEXT,
                action TEXT NOT NULL,
                ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                success BOOLEAN DEFAULT TRUE,
                error_msg TEXT
            );
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_login_audit_action_ts 
            ON login_audit(action, ts);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_login_audit_email_ip 
            ON login_audit(email, ip);
        """)
        
        print("✅ Tabelle 'login_audit' erstellt")
        return True
    except psycopg2.Error as e:
        print(f"❌ Fehler beim Erstellen der login_audit Tabelle: {e}")
        return False


# ============================================================================
# USER HINZUFÜGEN
# ============================================================================

def insert_users(cursor, emails: List[str], is_admin: bool = False) -> int:
    """Füge User in die Datenbank ein"""
    inserted = 0
    
    for email in emails:
        try:
            cursor.execute("""
                INSERT INTO users (email, is_active, is_admin, created_at)
                VALUES (%s, TRUE, %s, NOW())
                ON CONFLICT (email) DO NOTHING
                RETURNING id;
            """, (email, is_admin))
            
            result = cursor.fetchone()
            if result:
                inserted += 1
                user_type = "Admin" if is_admin else "User"
                print(f"  ✅ {user_type}: {email}")
            else:
                print(f"  ⏭️  Bereits vorhanden: {email}")
                
        except psycopg2.Error as e:
            print(f"  ❌ Fehler bei {email}: {e}")
    
    return inserted


# ============================================================================
# HAUPTPROGRAMM
# ============================================================================

def main():
    """Hauptfunktion"""
    # Parse Command-Line Arguments
    parser = argparse.ArgumentParser(
        description='Setup database for KI-Sicherheit.jetzt',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup_database.py
  python setup_database.py --db-url "postgresql://user:pass@host:port/db"
  export DATABASE_URL="..." && python setup_database.py
        """
    )
    parser.add_argument(
        '--db-url',
        type=str,
        help='PostgreSQL connection URL (overrides DATABASE_URL env var)'
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 KI-Sicherheit.jetzt - Database Setup")
    print("=" * 60)
    print("")
    
    # Verbindung herstellen
    print("📡 Verbinde zur Datenbank...")
    conn = connect_db(args)
    cursor = conn.cursor()
    print("✅ Verbindung hergestellt")
    print("")
    
    try:
        # Tabellen erstellen
        print("📊 Erstelle Tabellen...")
        print("-" * 60)
        
        success = True
        success &= create_users_table(cursor)
        success &= create_login_codes_table(cursor)
        success &= create_login_audit_table(cursor)
        
        if not success:
            print("")
            print("❌ Fehler beim Erstellen der Tabellen!")
            conn.rollback()
            return 1
        
        conn.commit()
        print("")
        
        # User hinzufügen
        print("👥 Füge User hinzu...")
        print("-" * 60)
        
        # Admin
        print("🔑 Admin-User:")
        admin_count = insert_users(cursor, [ADMIN_USER], is_admin=True)
        
        print("")
        print("👤 Test-User:")
        user_count = insert_users(cursor, TESTUSERS, is_admin=False)
        
        conn.commit()
        print("")
        
        # Zusammenfassung
        print("=" * 60)
        print("✅ Setup abgeschlossen!")
        print("=" * 60)
        print(f"📊 Tabellen: 3 erstellt (users, login_codes, login_audit)")
        print(f"👤 User: {user_count} neue Testuser hinzugefügt")
        print(f"🔑 Admin: {admin_count} neue Admin-User hinzugefügt")
        print(f"📧 Gesamt: {user_count + admin_count} neue User")
        print("")
        print("🎉 Datenbank ist bereit!")
        print("")
        
        return 0
        
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        conn.rollback()
        return 1
        
    finally:
        cursor.close()
        conn.close()
        print("👋 Verbindung geschlossen")


if __name__ == "__main__":
    sys.exit(main())
