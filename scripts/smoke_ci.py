
# -*- coding: utf-8 -*-
from __future__ import annotations
"""
scripts/smoke_ci.py v1.1 – API-basierter Smoke-Test
Änderung: Legt bei Bedarf selbst ein Briefing an (/api/briefings/submit) und nutzt die ID.
ENV:
  BASE_URL (Pflicht), AUTH_TOKEN (optional)
  Optional: SMOKE_BRIEFING_ID, SMOKE_ANALYSIS_ID
"""
import json, os, sys, time
import requests

BASE = os.getenv("BASE_URL")
if not BASE:
    print("❌ BASE_URL fehlt"); sys.exit(2)
AUTH = os.getenv("AUTH_TOKEN", "")
TIMEOUT = int(os.getenv("TIMEOUT", "25"))

def _headers():
    h = {"Content-Type":"application/json"}
    if AUTH: h["Authorization"] = f"Bearer {AUTH}"
    return h

def _get(p): return requests.get(f"{BASE.rstrip('/')}{p}", headers=_headers(), timeout=TIMEOUT)
def _post(p, d): return requests.post(f"{BASE.rstrip('/')}{p}", headers=_headers(), json=d, timeout=TIMEOUT)

def must_ok(resp, name):
    if resp.status_code // 100 != 2:
        print(f"❌ {name} failed: HTTP {resp.status_code}")
        print(resp.text[:500])
        sys.exit(1)
    print(f"✅ {name}")

def main():
    # 1) health
    r = _get("/api/healthz"); must_ok(r, "healthz")

    # 2) analyze
    brief_id = os.getenv("SMOKE_BRIEFING_ID")
    if not brief_id:
        # anlegen via /briefings/submit
        payload = {
            "lang":"de",
            "answers":{
                "branche":"beratung",
                "unternehmensgroesse":"solo",
                "hauptleistung":"Smoke-Test",
                "ki_ziele":["effizienz","qualität"]
            },
            "queue_analysis": True
        }
        r = _post("/api/briefings/submit", payload); must_ok(r, "briefings/submit")
        try:
            brief_id = str(r.json().get("briefing_id"))
        except Exception:
            print("❌ konnte briefing_id nicht extrahieren"); sys.exit(1)
        print(f"ℹ️ briefing_id={brief_id}")

    r = _post("/api/analyze", {"briefing_id": int(brief_id)}); must_ok(r, "analyze(sync)")
    data = {}
    try: data = r.json()
    except Exception: pass
    analysis_id = os.getenv("SMOKE_ANALYSIS_ID") or str(data.get("analysis_id") or "")

    # 3) report (optional)
    if analysis_id:
        r = _post("/api/report", {"analysis_id": int(analysis_id)}); must_ok(r, "report(pdf)")

    print("🎉 SMOKE OK"); return 0

if __name__ == "__main__":
    sys.exit(main())
