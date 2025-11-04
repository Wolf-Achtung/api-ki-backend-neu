#!/usr/bin/env bash
set -euo pipefail
BASE="${BACKEND_BASE:-}"
if [[ -z "${BASE}" ]]; then
  echo "::error ::BACKEND_BASE is not set (e.g. https://api-ki-backend-neu-production.up.railway.app)"
  exit 2
fi
echo "Using BACKEND_BASE=${BASE}"

# 1) Router-Status
curl -sSf "${BASE}/api/router-status" | tee /tmp/router-status.json >/dev/null
# check keys exist
python - <<'PY'
import json,sys
data=json.load(open('/tmp/router-status.json'))
need=['auth','briefings','analyze','report']
missing=[k for k in need if not data.get('routers',{}).get(k,False)]
if missing:
    print(f"::error ::Missing mounted routers: {missing}")
    sys.exit(2)
print("router-status OK")
PY

# 2) Preflight briefings
curl -sSf -X OPTIONS "${BASE}/api/briefings/submit" >/dev/null

# 3) Dry-run submit (keine DB/Analyse)
curl -sSf -X POST "${BASE}/api/briefings/submit" \
  -H "Content-Type: application/json" -H "x-dry-run: 1" \
  -d '{"answers":{"unternehmen":"CI Smoke GmbH"},"lang":"de"}' >/dev/null

# 4) Analyze route reachable (404 allowed if id not found)
set +e
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE}/api/analyze/run" \
  -H "Content-Type: application/json" -H "x-dry-run: 1" \
  -d '{"briefing_id": 999999}')
set -e
if [[ "${HTTP_CODE}" != "200" && "${HTTP_CODE}" != "202" && "${HTTP_CODE}" != "404" && "${HTTP_CODE}" != "503" ]]; then
  echo "::error ::Unexpected status on /api/analyze/run (got ${HTTP_CODE})"
  exit 2
fi
echo "Smoke OK"
