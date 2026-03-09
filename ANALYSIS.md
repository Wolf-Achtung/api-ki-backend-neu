# Codebase Analysis for Strategy Report Feature (Report 3)

**Date:** 2026-03-09
**Branch:** `claude/report-3-backend-phase-a-xXqgo`

---

## Directory Structure

```
api-ki-backend-neu/
├── main.py                  # FastAPI app, router mounting via mount_router()
├── models.py                # SQLAlchemy models (User, Briefing, Analysis, Report, LoginCode, Feedback, ReportHistory)
├── settings.py              # Pydantic v2 settings (AppSettings.from_env())
├── core/
│   ├── db.py                # Engine, SessionLocal, Base, get_session()
│   ├── mailer.py            # Core mailer
│   ├── migrate.py           # Migration helper
│   └── security.py          # JWT, service tokens
├── routes/
│   ├── _bootstrap.py        # get_db() dependency, SecureModel, rate_limiter
│   ├── auth.py              # Auth endpoints
│   ├── briefings.py         # Briefing submission
│   ├── analyze.py           # Analysis endpoints
│   ├── report.py            # Report 1 endpoints (prefix="/report")
│   ├── feedback.py          # Feedback
│   ├── smoke.py             # Smoke tests
│   ├── monitoring.py        # Health/diagnostics
│   ├── admin.py             # Admin (ENV-gated)
│   ├── admin_sql.py         # Raw SQL admin (ENV-gated)
│   ├── reports_registry.py  # Report versioning
│   ├── dashboard.py         # Dashboard API
│   ├── funding.py           # Premium funding
│   ├── feedback_dashboard.py
│   └── tools_dashboard.py
├── services/
│   ├── provider_perplexity.py   # Perplexity API client (search function, circuit breaker)
│   ├── provider_tavily.py       # Tavily API client (search function)
│   ├── anthropic_client.py      # Anthropic Claude client (call_anthropic function)
│   ├── llm_client.py            # LLM retry layer (LLMClient, call_llm_with_retry)
│   ├── pdf_client.py            # PDF service client (render_pdf_from_html)
│   ├── report_pipeline.py       # Report 1 pipeline (build_context, etc.)
│   ├── gamechanger_deep_dive.py # Report 2 / KI-Potenzial-Analyse
│   ├── business_case_engine_v2.py # Business case calculations
│   ├── research.py              # Research orchestration
│   ├── research_pipeline.py     # Research pipeline
│   ├── email.py / email_sender.py / mailer.py  # Email services
│   └── ...                      # Many more services
├── prompts/
│   ├── de/                  # German prompts (markdown files)
│   ├── en/                  # English prompts
│   └── prompt_manifest.json
├── templates/
│   ├── pdf_template_v7.html # Main PDF template
│   ├── gamechanger_deep_dive_v1.html
│   └── partials/
├── migrations/
│   ├── 2025-11-08_*.sql     # Login codes migrations
│   └── 2025-12-15_*.sql     # Briefing worker fields
├── workers/
│   └── briefings_worker.py  # DB-backed queue worker
└── tests/                   # Extensive test suite
```

## Key Services and Their Locations

| Service | File | Key Functions |
|---------|------|---------------|
| DB Session | `core/db.py` | `SessionLocal`, `get_session()`, `Base` |
| DB Dependency | `routes/_bootstrap.py` | `get_db()` |
| Perplexity API | `services/provider_perplexity.py` | `search(topic, days, max_items)` |
| Tavily API | `services/provider_tavily.py` | `search(query, max_results, days)` |
| Anthropic/Claude | `services/anthropic_client.py` | `call_anthropic(prompt, section, system_prompt, ...)` |
| LLM Retry | `services/llm_client.py` | `call_llm_with_retry(call_fn, section, max_tokens)` |
| PDF Rendering | `services/pdf_client.py` | `render_pdf_from_html(html, meta, pdf_options)` |
| Report Pipeline | `services/report_pipeline.py` | `build_context(briefing, snippets)` |
| Business Case | `services/business_case_engine_v2.py` | Business case calculations |
| Email | `services/email.py`, `services/email_sender.py` | Email sending |

## ENV Variables Required (Existing)

```bash
DATABASE_URL          # PostgreSQL connection string
OPENAI_API_KEY        # OpenAI API key
ANTHROPIC_API_KEY     # Anthropic API key
PERPLEXITY_API_KEY    # Perplexity API key
TAVILY_API_KEY        # Tavily API key
PDF_SERVICE_URL       # Puppeteer PDF microservice URL
RESEND_API_KEY        # Email service (via settings.mail)
JWT_SECRET            # Auth JWT secret
```

## New ENV Variables (Report 3)

```bash
STRATEGY_ADMIN_KEY    # Admin key for beta unlock endpoint
```

## How the Existing Pipeline is Orchestrated

1. **Briefing Submission**: `POST /api/briefings/submit` → saves to `briefings` table (status='accepted')
2. **Worker Processing**: `workers/briefings_worker.py` polls DB for accepted briefings
3. **Analysis**: `gpt_analyze.py` runs full LLM analysis pipeline, saves to `analyses` table
4. **Report Generation**: `routes/report.py` endpoints serve HTML/PDF from analysis data
5. **PDF**: `services/pdf_client.py` calls external Puppeteer service
6. **Email**: Sent via Resend API

## Router Mounting Pattern

Routers are mounted in `main.py` via `_build_router_config()` → `mount_router()`:
```python
cfg.append(("routes.module_name", "/api", "route_name"))
# mount_router imports the module's `router` and calls app.include_router(router, prefix="/api")
```

Each route module defines its own sub-prefix in the router:
```python
router = APIRouter(prefix="/report", tags=["report"])  # → /api/report/...
```

## Migration Convention

- Raw SQL files in `migrations/` directory
- Named with date prefix: `YYYY-MM-DD_description_postgres.sql`
- Separate files for PostgreSQL and SQLite when needed
- NOT auto-applied — applied manually by Wolf

## Models Pattern

- SQLAlchemy ORM with `Mapped[]` type hints
- `Base` from `core.db`
- JSONB with SQLite fallback via dynamic import
- DateTime with timezone awareness
