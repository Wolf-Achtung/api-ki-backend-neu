#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix login_audit Table Schema
Löscht die alte Tabelle und erstellt sie mit dem richtigen Schema neu.

Usage:
    python fix_login_audit.py --db-url "postgresql://..."
    
    # Oder mit Environment Variable:
    export DATABASE_URL="postgresql://..."
    python fix_login_audit.py

Requirements:
    pip install psycopg2-binary
"""
import os
import sys
import argparse

try:
    import psycopg2
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


def get_database_url(args=None) -> str:
    """Hole DATABASE_URL aus Command-Line, Environment oder .env"""
    
    # 1. Priorität: Command-Line Argument
    if args and args.db_url:
        return args.db_url
    
    # 2. Priorität: Environment Variable
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("❌ Fehler: DATABASE_URL nicht gefunden!")
        print("")
        print("🎯 2 Möglichkeiten:")
        print("")
        print("1️⃣  Als Argument übergeben:")
        print('   python fix_login_audit.py --db-url "postgresql://..."')
        print("")
        print("2️⃣  Als Environment Variable setzen:")
        print('   export DATABASE_URL="postgresql://..."')
        print('   python fix_login_audit.py')
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


def fix_login_audit_table(cursor) -> bool:
    """Löscht alte login_audit Tabelle und erstellt sie mit korrektem Schema neu"""
    
    print("📋 Schema-Info:")
    print("-" * 60)
    print("❌ ALT (falsch):")
    print("   - email, ip, action, ts, success, error_msg")
    print("")
    print("✅ NEU (korrekt):")
    print("   - email, ip, action, ts, status, user_agent, detail")
    print("-" * 60)
    print("")
    
    try:
        # 1. Alte Tabelle löschen
        print("🗑️  Lösche alte login_audit Tabelle...")
        cursor.execute("DROP TABLE IF EXISTS login_audit;")
        print("✅ Alte Tabelle gelöscht")
        print("")
        
        # 2. Neue Tabelle mit korrektem Schema erstellen
        print("📊 Erstelle neue login_audit Tabelle...")
        cursor.execute("""
            CREATE TABLE login_audit (
                id BIGSERIAL PRIMARY KEY,
                ts TIMESTAMPTZ DEFAULT now(),
                email TEXT,
                ip TEXT,
                action TEXT,
                status TEXT,
                user_agent TEXT,
                detail TEXT
            );
        """)
        print("✅ Neue Tabelle erstellt")
        print("")
        
        # 3. Indizes erstellen
        print("🔍 Erstelle Indizes...")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_login_audit_action_ts 
            ON login_audit(action, ts);
        """)
        print("  ✅ Index: action, ts")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_login_audit_email_ip 
            ON login_audit(email, ip);
        """)
        print("  ✅ Index: email, ip")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_login_audit_status 
            ON login_audit(status);
        """)
        print("  ✅ Index: status")
        
        print("")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Fehler: {e}")
        return False


def main():
    """Hauptfunktion"""
    # Parse Command-Line Arguments
    parser = argparse.ArgumentParser(
        description='Fix login_audit table schema for KI-Sicherheit.jetzt',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fix_login_audit.py --db-url "postgresql://user:pass@host:port/db"
  export DATABASE_URL="..." && python fix_login_audit.py
        """
    )
    parser.add_argument(
        '--db-url',
        type=str,
        help='PostgreSQL connection URL'
    )
    parser.add_argument(
        '--no-confirm',
        action='store_true',
        help='Skip confirmation prompt'
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔧 Fix login_audit Table Schema")
    print("=" * 60)
    print("")
    
    # Warnung
    if not args.no_confirm:
        print("⚠️  WARNUNG:")
        print("   Dieser Script löscht die bestehende login_audit Tabelle")
        print("   und erstellt sie neu mit dem korrekten Schema.")
        print("")
        print("   Alle Daten in der Tabelle gehen verloren!")
        print("")
        
        response = input("Fortfahren? [y/N]: ").strip().lower()
        if response != 'y':
            print("❌ Abgebrochen")
            return 1
        print("")
    
    # Verbindung herstellen
    print("📡 Verbinde zur Datenbank...")
    conn = connect_db(args)
    cursor = conn.cursor()
    print("✅ Verbindung hergestellt")
    print("")
    
    try:
        # Tabelle fixen
        success = fix_login_audit_table(cursor)
        
        if not success:
            print("")
            print("❌ Fehler beim Fixen der Tabelle!")
            conn.rollback()
            return 1
        
        # Commit
        conn.commit()
        
        # Zusammenfassung
        print("=" * 60)
        print("✅ login_audit Tabelle erfolgreich gefixt!")
        print("=" * 60)
        print("")
        print("📋 Neues Schema:")
        print("   - id (BIGSERIAL PRIMARY KEY)")
        print("   - ts (TIMESTAMPTZ)")
        print("   - email (TEXT)")
        print("   - ip (TEXT)")
        print("   - action (TEXT)")
        print("   - status (TEXT)")
        print("   - user_agent (TEXT)")
        print("   - detail (TEXT)")
        print("")
        print("🔍 Indizes:")
        print("   - (action, ts)")
        print("   - (email, ip)")
        print("   - (status)")
        print("")
        print("🎯 Nächste Schritte:")
        print("   1. Backend in Railway neu starten (Redeploy)")
        print("   2. Login testen: https://make.ki-sicherheit.jetzt/login")
        print("   3. ✅ Sollte funktionieren!")
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
