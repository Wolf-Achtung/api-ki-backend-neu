#!/usr/bin/env python3
import os, sys

REQUIRED = [
    "DATABASE_URL",
    "JWT_SECRET", "JWT_ALGORITHM", "JWT_EXPIRE_DAYS",
    "BACKEND_BASE", "SITE_URL",
    "OPENAI_API_KEY", "OPENAI_MODEL",
]

def require(keys):
    missing = [k for k in keys if not os.getenv(k)]
    return missing

def warn_provider():
    provider = os.getenv("EMAIL_PROVIDER","").lower()
    if provider not in {"resend","smtp"}:
        print("WARN: EMAIL_PROVIDER should be 'resend' or 'smtp'")
    if provider == "resend" and not os.getenv("RESEND_API_KEY"):
        print("WARN: RESEND_API_KEY missing while EMAIL_PROVIDER=resend")
    if provider == "smtp":
        for k in ("SMTP_HOST","SMTP_PORT","SMTP_USER","SMTP_PASSWORD","SMTP_FROM"):
            if not os.getenv(k): print(f"WARN: {k} missing while EMAIL_PROVIDER=smtp")

def warn_cors():
    origins = os.getenv("CORS_ORIGINS","")
    if not origins:
        print("WARN: CORS_ORIGINS empty — Browser wird blockiert.")
    creds = os.getenv("CORS_ALLOW_CREDENTIALS","0")
    if creds == "1":
        print("INFO: CORS_ALLOW_CREDENTIALS=1 — Access-Control-Allow-Credentials wird gesendet.")

def warn_redis():
    if os.getenv("ENABLE_LLM_CACHE","0") == "1" and not os.getenv("REDIS_URL"):
        print("WARN: ENABLE_LLM_CACHE=1 aber REDIS_URL fehlt.")
    if os.getenv("ENABLE_LLM_CACHE","0") == "0":
        print("INFO: LLM-Cache deaktiviert (Redis optional).")

def main():
    missing = require(REQUIRED)
    if missing:
        print("ERROR: Missing required variables:")
        for m in missing: print("  -", m)
        sys.exit(1)
    warn_provider()
    warn_cors()
    warn_redis()
    print("OK: .env looks consistent.")

if __name__ == "__main__":
    main()
