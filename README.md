# KI-Readiness Backend

Backend API for KI-Readiness analysis and report generation.

## Release R1 - How to Run

This is the first production release (R1) of the KI-Readiness Backend, consolidated after Sprints G1-G15.

### Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 3. Run migrations (laufen auch automatisch beim App-Start)
python scripts/migrate.py

# 4. Start server
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Validate Configuration

```bash
# Check release configuration
python -c "from services.config_validation import print_release_validation; print_release_validation()"
```

### Run E2E Checks

```bash
# Validate with gold profiles (mock mode)
python scripts/run_release_e2e_check.py

# Live mode
python scripts/run_release_e2e_check.py --live --base-url http://localhost:8000
```

### Check Release Health

```bash
# Via API
curl http://localhost:8000/api/dashboard/release-health
```

Expected response:
```json
{
  "status": "green",
  "metrics": {
    "reports_last_24h": 10,
    "fallback_rate_pct": 5.0,
    "pdf_error_rate_pct": 0.0
  }
}
```

## Documentation

- **[Operator Guide](docs/OPERATOR_GUIDE.md)** - Operations, monitoring, troubleshooting
- **[Architecture](docs/ARCHITECTURE.md)** - System architecture documentation

## Feature Summary (G1-G15)

| Sprint | Features |
|--------|----------|
| G1-G6 | Core report generation, scoring, business case |
| G7 | AI Act compliance classification |
| G8 | Validation framework, section min-words |
| G9-G10 | Research pipeline, funding recommendations |
| G11 | Product mode: versioning, dashboard, delta engine |
| G12 | Resilience: circuit breaker, rate limiting, degradation monitor |
| G13 | Polish: prompt tuning, redundancy filter, fallback optimization |
| G14 | Stability: LLM retry, Perplexity circuit breaker, performance hardening |
| G15 | Release R1: configuration, E2E checks, health monitoring |

## API Endpoints

### Core
- `POST /api/briefings/submit` - Submit briefing for report generation
- `GET /api/reports/{id}` - Get report by ID
- `GET /api/reports/list` - List reports

### Dashboard (G11/G15)
- `GET /api/dashboard/overview` - Dashboard overview
- `GET /api/dashboard/trends` - Trend analysis
- `GET /api/dashboard/ai-act-summary` - AI Act summary
- `GET /api/dashboard/release-health` - Release health status
- `GET /api/dashboard/config-validation` - Configuration validation

## Environment Variables

See [`.env.example`](.env.example) for all available configuration options.

### Required for Production
- `DATABASE_URL` - PostgreSQL connection
- `JWT_SECRET` - JWT signing secret (change from default!)
- `OPENAI_API_KEY` - OpenAI API key
- `PDF_SERVICE_URL` - PDF generation service

## Tests

```bash
# Run all tests
pytest

# Run specific sprint tests
pytest tests/test_g14_stability.py -v
pytest tests/test_g13_polish.py -v
```

## License

Proprietary - All rights reserved

---

*Release R1 - Sprint G15*
