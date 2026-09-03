# Tranche 2 — gegengeprüft am 03.09.2026

Der ENV-Audit (`docs/env-audit-2026-09.md`) stammt von **vor** KIS-1266.
Seither wurden mehrere Variablen im Code angeschlossen. Wer die alte
Liste ungeprüft abarbeitet, löscht funktionierende Konfiguration.

Diese Liste ist gegen den Stand von `main` am 03.09.2026 neu geprüft:
jeder Name wurde in `services/`, `routes/`, `core/`, `workers/`,
`utils/`, `scripts/`, `gpt_analyze.py`, `main.py` und `settings.py`
gesucht, Testdateien ausgenommen.

## Löschen — 37 Variablen

Kein Leser im Code. Railway startet den Dienst nach dem Löschen neu;
das ist der einzige Effekt. **Nicht während eines Testlaufs.**

```
ANTHROPIC_BASE_URL
ANTHROPIC_ENABLED
API_RATE_LIMIT_PER_MIN
AUTH_ALLOW_DEV_CONSOLE
AUTH_SEND_MAIL
CORS_MAX_AGE
DEBUG_LOG_HTML_SNAPSHOT
DEBUG_LOG_PROMPTS
DISABLE_HIGH_RISK_AUTO_UPGRADE
ENABLE_GUARDRAILS
ENABLE_METRICS
ENABLE_PERPLEXITY
ENABLE_PROMPT_LABELS
ENABLE_SENSITIVITY_TABLE
ENABLE_TAVILY
FEEDBACK_SECRET
GUARDRAILS_V
HARD_FAIL_ON_HTML_ERRORS
HARD_FAIL_ON_VALIDATION_ERRORS
MARKET_INSIGHTS_ENABLED
MAX_GUARDRAIL_HITS
MAX_PARALLEL_LLM_CALLS
MAX_PARALLEL_SECTIONS
OPENAI_MAX_TOKENS_PROMPT_FRAMEWORK
PERPLEXITY_MAX_TOKENS
PERPLEXITY_RATE_LIMIT_PER_HOUR
PERPLEXITY_TIMEOUT_MS
REPORT_ADMIN_EMAIL
RESEARCH_COUNTRY
RESEARCH_DAYS_DEFAULT
RESEARCH_DAYS_MAX
RESEARCH_DAYS_MIN
RESEARCH_LANG
RESEARCH_RSS_EXTRA_PATH
STARTER_KITS_MAX_TOOLS
TOKEN_LIMIT_HTML_REPAIR
USE_STOCK_IMAGES
```

Zu den letzten sieben (`RESEARCH_DAYS_*`, `RESEARCH_LANG`,
`RESEARCH_COUNTRY`, `PERPLEXITY_TIMEOUT_MS`, `PERPLEXITY_MAX_TOKENS`):
Sie werden in `settings.py` in Pydantic-Felder eingelesen, aber **kein
einziger Verbraucher liest diese Felder**. Sie sind damit wirkungslos —
geprüft, nicht vermutet.

## Nicht löschen — 8 Variablen, die der Audit falsch einordnet

Diese standen auf der alten Liste, werden aber **heute gelesen und
wirken**:

| Variable | Wird gelesen in | Seit |
|---|---|---|
| `USE_INTERNAL_RESEARCH` | `gpt_analyze.py` | KIS-1266 |
| `RESEARCH_INCLUDE_FUNDING` | `services/research_policy.py` | KIS-1266 |
| `RESEARCH_INCLUDE_TOOLS` | `services/research_policy.py` | KIS-1266 |
| `RESEARCH_EXCLUDE` | `services/research_policy.py` | KIS-1266 |
| `RATE_LIMIT_PER_MINUTE` | `services/rate_limit.py` | — |
| `REPORT_TEMPLATE_PATH` | `services/report_renderer.py` | — |
| `ENABLE_LIVE_TOOL_PRICING` | `services/live_data_integration.py` | — |
| `ENABLE_LIVE_FOERDERPROGRAMME` | `services/live_data_integration.py` | — |

Die drei `RESEARCH_INCLUDE_*`/`RESEARCH_EXCLUDE`-Listen sind seit
KIS-1266 an die Tavily-Suche angeschlossen — genau die Verbesserung, die
der Audit unter Punkt 6 empfohlen hatte. Sie zu löschen würde die
Domänenfilter wieder abschalten.

## Ebenfalls nicht löschen

`TAVILY_MAX_RESULTS`, `TAVILY_TIMEOUT_MS`, `TAVILY_RATE_LIMIT_PER_HOUR`
werden in `services/live_data_integration.py` gelesen. Ob dieses Modul im
Report-Pfad aktiv ist, wurde hier nicht geprüft — im Zweifel stehen
lassen, sie kosten nichts.

`MISE_PYTHON_GITHUB_ATTESTATIONS` gehört zum Railway-Build und bleibt.

## Reihenfolge

1. Die 37 oben löschen. Kein Deploy nötig, nur ein Neustart.
2. Danach einen Report erzeugen und mit `scripts/compare_reports.py`
   gegen den letzten Lauf halten. Bleiben die Kennzahlen gleich und
   meldet die Rückfall-Prüfung nichts, war das Löschen folgenlos.
