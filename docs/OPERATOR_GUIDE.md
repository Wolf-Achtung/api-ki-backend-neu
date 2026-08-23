# Operator Guide - Release R1

This guide covers the operational aspects of the KI-Readiness Backend for system administrators and operators.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Environment Configuration](#environment-configuration)
3. [Starting and Stopping](#starting-and-stopping)
4. [Health Monitoring](#health-monitoring)
5. [E2E Validation](#e2e-validation)
6. [Troubleshooting](#troubleshooting)
7. [Common Issues](#common-issues)

---

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL database
- OpenAI API key
- PDF Service URL (for PDF generation)

### Minimal Setup

1. Copy environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your credentials:
   ```bash
   # Required
   DATABASE_URL=postgresql://user:pass@host:5432/db
   JWT_SECRET=your-secure-secret-here
   OPENAI_API_KEY=sk-...
   PDF_SERVICE_URL=https://your-pdf-service.com
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run database migrations (also applied automatically on app start
   via `core/migrate.py` + `migrations/*.sql`):
   ```bash
   python scripts/migrate.py
   ```

5. Start the server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

---

## Environment Configuration

### Required Variables

These **must** be set before production deployment:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` |
| `JWT_SECRET` | Secret for JWT signing (change from default!) | Random 64+ chars |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `PDF_SERVICE_URL` | PDF generation service URL | `https://...` |
| `SMTP_HOST` | SMTP server for notifications | `smtp.example.com` |
| `SMTP_USER` | SMTP username | `user@example.com` |
| `SMTP_PASS` | SMTP password | `***` |

### Recommended Variables

These enhance functionality:

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | For executive summary generation | - |
| `PERPLEXITY_API_KEY` | For research pipeline | - |
| `TAVILY_API_KEY` | Research fallback | - |
| `ADMIN_NOTIFY_EMAIL` | Alert notifications | - |

### Feature Flags (Release R1 Defaults)

| Flag | Sprint | Default | Description |
|------|--------|---------|-------------|
| `AI_ACT_ENABLED` | G7 | `1` | AI Act risk classification |
| `REPORT_VERSIONING_ENABLED` | G11 | `1` | Version history |
| `ENABLE_DASHBOARD_API` | G11 | `1` | Dashboard endpoints |
| `RATE_LIMIT_ENABLED` | G12 | `1` | Rate limiting |
| `LLM_CIRCUIT_BREAKER_ENABLED` | G12 | `1` | Circuit breaker |
| `LLM_SHORT_RETRY_ENABLED` | G14 | `1` | LLM retry with backoff |
| `ENABLE_PREMIUM_FUNDING` | G11 | `0` | Premium funding features |

### Validate Configuration

Run the configuration validator:

```bash
python -c "from services.config_validation import print_release_validation; print_release_validation()"
```

Or via API:
```bash
curl http://localhost:8000/api/dashboard/config-validation
```

---

## Starting and Stopping

### Local Development

```bash
# Start with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start with specific workers
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
```

### Production (Railway)

The application auto-starts on Railway via `Procfile`:

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

To restart on Railway:
1. Go to Railway dashboard
2. Select deployment
3. Click "Redeploy"

### Docker (if applicable)

```bash
# Build
docker build -t ki-backend .

# Run
docker run -p 8000:8000 --env-file .env ki-backend
```

---

## Health Monitoring

### Release Health Endpoint

Check overall system health:

```bash
curl http://localhost:8000/api/dashboard/release-health
```

Response includes:
- `status`: `green` / `yellow` / `red`
- `metrics.reports_last_24h`: Report count
- `metrics.fallback_rate_pct`: Fallback percentage (should be < 10%)
- `metrics.pdf_error_rate_pct`: PDF errors (should be < 5%)
- `metrics.ai_act_high_risk_share_pct`: High-risk share
- `circuit_breakers`: Circuit breaker status (G14)
- `alerts`: Active alerts

### Status Interpretation

| Status | Meaning | Action |
|--------|---------|--------|
| `green` | All metrics within thresholds | None required |
| `yellow` | Warning thresholds exceeded | Monitor closely |
| `red` | Critical thresholds exceeded | Investigate immediately |

### Thresholds (R1 Defaults)

| Metric | Warning | Critical |
|--------|---------|----------|
| `fallback_rate_pct` | 10% | 25% |
| `pdf_error_rate_pct` | 5% | 15% |
| `ai_act_high_risk_share_pct` | 50% | 80% |

---

## E2E Validation

### Run E2E Checks

Validate the system with gold profiles:

```bash
# Mock mode (default, no API calls)
python scripts/run_release_e2e_check.py

# Live mode (requires running server)
python scripts/run_release_e2e_check.py --live --base-url http://localhost:8000
```

### Expected Results

| Profile | Expected Risk Level | BC Modifiers |
|---------|--------------------| -------------|
| solo_beratung_ki_assessments | minimal/none | No |
| team_finance_insurance_advisory | high-risk/limited | Yes |
| kmu_france_eu_core_en_gold | minimal/limited | Optional |

### Acceptance Criteria for R1

- All three profiles: `OK` or `WARN` (no `FAIL`)
- `/api/dashboard/release-health` returns `green` or `yellow`
- No critical errors in logs

---

## Troubleshooting

### AI Act Errors

**Symptom**: Reports show incorrect risk level

**Check**:
1. Verify `AI_ACT_ENABLED=1`
2. Check branch/industry mapping in `services/ai_act_module.py`
3. Review logs for `[AI-ACT]` entries

**Action**:
- Temporarily set `AI_ACT_FAIL_ON_INCONSISTENCY=0` (soft mode)
- Review business case modifiers

### PDF Generation Errors

**Symptom**: PDF generation fails or times out

**Check**:
1. Verify `PDF_SERVICE_URL` is accessible
2. Check `PDF_TIMEOUT_MS` (default: 90000ms)
3. Look for `[PDF-G14]` log entries

**Action**:
- Increase timeout: `PDF_TIMEOUT_MS=180000`
- Check HTML payload size (`MAX_HTML_PAYLOAD_KB=350`)
- Enable PDF guard logging: check for oversized content

### Circuit Breaker Open

**Symptom**: Research results empty, circuit breaker alerts

**Check**:
1. `/api/dashboard/release-health` → `circuit_breakers`
2. Look for `[PPLX-CIRCUIT]` log entries

**Action**:
- Wait for auto-reset (`PPLX_CIRCUIT_RESET_SEC=120`)
- Check Perplexity API status
- Verify API key is valid

### Rate Limiting

**Symptom**: 429 errors, requests rejected

**Check**:
1. Current rate: `REPORT_RATE_LIMIT_PER_MINUTE=5`
2. Global limit: `REPORT_RATE_LIMIT_GLOBAL=20`

**Action**:
- Increase limits temporarily for testing
- Implement request queuing on client side

---

## Common Issues

### 1. "JWT_SECRET must be changed from default"

**Cause**: Using default JWT secret in production

**Fix**: Generate a new secret:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```
Set this as `JWT_SECRET` in your environment.

### 2. "Required ENV variable not set: DATABASE_URL"

**Cause**: Database not configured

**Fix**: Set `DATABASE_URL` with your PostgreSQL connection string.

### 3. High Fallback Rate

**Cause**: LLM timeouts or errors

**Fix**:
1. Check LLM retry settings (`LLM_MAX_RETRIES=2`)
2. Review timeout: `FALLBACK_TIMEOUT_SEC=60`
3. Check OpenAI API status

### 4. Reports Taking Too Long

**Cause**: Multiple API calls timing out

**Fix**:
1. Enable short retry: `LLM_SHORT_RETRY_ENABLED=1`
2. Reduce max tokens: `LLM_SHORT_RETRY_MAXTOKENS=1200`
3. Check research provider timeouts

---

## Support

For issues not covered here:
1. Check logs for specific error messages
2. Review recent changes in git history
3. Contact the development team

---

*Release R1 - Sprint G15*
*Last updated: 2025-12*
