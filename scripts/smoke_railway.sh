
#!/usr/bin/env bash
set -euo pipefail

BASE="http://127.0.0.1:${PORT:-8080}"
AUTH="${SMOKE_AUTH_TOKEN:-}"

curl_opts=(-fsS --retry 10 --retry-connrefused --retry-delay 1)

echo "→ Smoke (Railway local) BASE=$BASE"

# 1) health
curl "${curl_opts[@]}" "$BASE/api/healthz" >/dev/null
echo "✓ healthz"

# 2) optional analyze
if [[ -n "${SMOKE_BRIEFING_ID:-}" ]]; then
  curl "${curl_opts[@]}" -X POST "$BASE/api/analyze"     -H 'Content-Type: application/json'     ${AUTH:+ -H "Authorization: Bearer $AUTH"}     -d "{"briefing_id": ${SMOKE_BRIEFING_ID}}" >/dev/null
  echo "✓ analyze(sync)"
fi

# 3) optional report
if [[ -n "${SMOKE_ANALYSIS_ID:-}" ]]; then
  curl "${curl_opts[@]}" -X POST "$BASE/api/report"     -H 'Content-Type: application/json'     ${AUTH:+ -H "Authorization: Bearer $AUTH"}     -d "{"analysis_id": ${SMOKE_ANALYSIS_ID}}" >/dev/null
  echo "✓ report(pdf)"
fi

echo "🎉 SMOKE OK (Railway)"
