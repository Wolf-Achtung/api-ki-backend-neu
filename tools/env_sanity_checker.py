# -*- coding: utf-8 -*-
"""
tools/env_sanity_checker.py
---------------------------
Kleines Hilfsskript, das in der Railway-Konsole (Shell) laufen kann:

python tools/env_sanity_checker.py

Prüft u. a.:
- Vorhandensein & Format von DATABASE_URL
- Einzeilige CORS_ORIGINS
- Pflicht-Keys (OPENAI_API_KEY, REPORT_TEMPLATE_PATH, PDF_SERVICE_URL)
"""
import os, sys, re
from sqlalchemy.engine.url import make_url

REQUIRED = ["DATABASE_URL", "OPENAI_API_KEY", "REPORT_TEMPLATE_PATH", "PDF_SERVICE_URL"]

def ok(msg): print("✅", msg)
def bad(msg): print("❌", msg)

def main():
    errors = 0
    # DATABASE_URL
    db = os.getenv("DATABASE_URL")
    if not db:
        bad("DATABASE_URL fehlt"); errors += 1
    else:
        try:
            make_url(db)  # parst nur, verbindet nicht
            ok("DATABASE_URL parsbar")
        except Exception as exc:
            errors += 1
            bad(f"DATABASE_URL nicht parsbar: {exc}")
    # CORS_ORIGINS
    cors = os.getenv("CORS_ORIGINS", "")
    if "\n" in cors or "\r" in cors:
        errors += 1
        bad("CORS_ORIGINS enthält Zeilenumbruch – bitte in eine Zeile bringen")
    else:
        ok("CORS_ORIGINS einzeilig")
    # Pflicht-Keys
    for k in REQUIRED:
        if not os.getenv(k):
            errors += 1
            bad(f"{k} fehlt")
    if errors:
        print(f"\n⚠️  {errors} Problem(e) gefunden.")
        sys.exit(1)
    ok("Environment sieht gut aus.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
