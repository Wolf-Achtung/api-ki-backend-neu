# -*- coding: utf-8 -*-
from __future__ import annotations
"""
scripts/smoke_ci.py – minimaler CI-fähiger Smoke-Test
Nutzung:
  BASE_URL=https://api.example.com   SMOKE_BRIEFING_ID=123   python scripts/smoke_ci.py
Optional:
  AUTH_TOKEN=<Bearer>    # falls Briefing-Endpoints Auth erfordern
  TIMEOUT=20
"""
import json, os, sys, time
import requests

BASE = os.getenv("BASE_URL")
if not BASE:
    print("❌ BASE_URL fehlt"); sys.exit(2)
TIMEOUT = int(os.getenv("TIMEOUT", "20"))
AUTH = os.getenv("AUTH_TOKEN", "")

def _headers():
    h = {"Content-Type":"application/json"}
    if AUTH: h["Authorization"] = f"Bearer {AUTH}"
    return h

def _get(path):
    url = f"{BASE.rstrip('/')}{path}"
    r = requests.get(url, headers=_headers(), timeout=TIMEOUT)
    return r.status_code, r.headers.get("content-type",""), r.text

def _post(path, payload):
    url = f"{BASE.rstrip('/')}{path}"
    r = requests.post(url, headers=_headers(), data=json.dumps(payload), timeout=TIMEOUT)
    return r.status_code, r.headers.get("content-type",""), r.text

def must_ok(status, name, body=None):
    if status // 100 != 2:
        print(f"❌ {name} failed: HTTP {status}")
        if body: print(body[:400])
        sys.exit(1)
    print(f"✅ {name}")

def main():
    # 1) Health
    s, ct, body = _get("/api/healthz")
    must_ok(s, "healthz", body)

    # 2) Optional: Analyze (sync) – benötigt gültige Briefing-ID
    brief_id = os.getenv("SMOKE_BRIEFING_ID")
    analysis_id = None
    if brief_id:
        s, ct, body = _post("/api/analyze", {"briefing_id": int(brief_id)})
        must_ok(s, "analyze(sync)", body)
        try:
            data = json.loads(body)
            if data.get("ok"):
                analysis_id = data.get("analysis_id")
                print(f"ℹ️ analysis_id={analysis_id}")
        except Exception:
            pass

    # 3) Optional: Report (aus analyze-Ergebnis oder SMOKE_ANALYSIS_ID)
    report_from = os.getenv("SMOKE_ANALYSIS_ID") or analysis_id
    if report_from:
        s, ct, body = _post("/api/report", {"analysis_id": int(report_from)})
        must_ok(s, "report(pdf)", body)

    print("🎉 SMOKE OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
