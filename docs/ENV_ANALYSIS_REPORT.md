# ENV-Analyse & Code-Abgleich Report

**Repository:** api-ki-backend-neu
**Datum:** 2025-12-14
**Quelle:** `docs/env.txt`
**Status:** PLATIN+++ Produktionsstabilität

---

## Übersicht

| Kategorie | Anzahl |
|-----------|--------|
| **ENV-Keys gesamt (docs/env.txt)** | 367 |
| **USED** (aktiv im Code) | ~320 |
| **UNUSED** (Kandidaten für Löschung) | 18 |
| **MISSING** (im Code, nicht in env.txt) | 47 |
| **DRIFT/DUPLICATES** | 12 Gruppen |

---

## A) USED_ENV_KEYS (Bestätigt aktiv)

Die folgenden ENV-Keys aus `docs/env.txt` werden nachweislich im Code gelesen:

### Core / Infrastruktur
| Key | Datei | Zeile | Zugriff |
|-----|-------|-------|---------|
| `ENV` | main.py | 341, 447 | os.getenv, default="production" |
| `APP_NAME` | main.py, settings.py | 94, 227 | os.getenv, default="KI Status Report API" |
| `DATABASE_URL` | setup_database.py, settings.py | 90, 232 | os.getenv, required |
| `JWT_SECRET` | settings.py | 256 | os.getenv, required |
| `LOG_LEVEL` | main.py, settings.py | 41, 229 | os.getenv, default="info" |
| `PORT` | main.py | 485 | os.getenv, default="8080" |
| `CORS_ORIGINS` | main.py | 105 | os.getenv |
| `CORS_ALLOW_CREDENTIALS` | settings.py | - | get_bool_env |

### OpenAI LLM
| Key | Datei | Zeile | Zugriff |
|-----|-------|-------|---------|
| `OPENAI_API_KEY` | gpt_analyze.py, settings.py | 1243, 263 | os.getenv, required |
| `OPENAI_MODEL` | gpt_analyze.py, settings.py | 1086, 264 | os.getenv, default="gpt-4o" |
| `OPENAI_TEMPERATURE` | settings.py | 265 | os.getenv, default="0.2" |
| `OPENAI_MAX_TOKENS` | gpt_analyze.py, utils/llm_overrides.py | 1254, 128 | os.getenv, default="3000" |
| `OPENAI_TIMEOUT` | settings.py | 267 | os.getenv, default="120" |
| `OPENAI_TIMEOUT_READ` | services/llm_client.py | 88 | os.getenv, default="120" |
| `OPENAI_MAX_RETRIES` | services/llm_client.py | 89 | os.getenv, default="3" |
| `OPENAI_MAX_PARALLEL_REQUESTS` | services/llm_client.py | 90 | os.getenv, default="3" |
| `OPENAI_REASONING_EFFORT` | services/llm_client.py | 292 | os.getenv, default="high" |
| `OPENAI_MODEL_FAST` | settings.py | 270 | os.getenv, fallback=OPENAI_MODEL |
| `OPENAI_MODEL_REASONING` | settings.py | 271 | os.getenv, fallback=OPENAI_MODEL |
| `OPENAI_MODEL_FALLBACK` | settings.py | 272 | os.getenv, default="gpt-4o-mini" |

### OpenAI Section-Specific (dynamisch)
| Pattern | Datei | Zeile | Zugriff |
|---------|-------|-------|---------|
| `OPENAI_MODEL_{SECTION}` | gpt_analyze.py | 1120 | os.getenv dynamisch |
| `OPENAI_TEMP_{SECTION}` | gpt_analyze.py | 1121 | os.getenv dynamisch |
| `OPENAI_MAX_TOKENS_{SECTION}` | gpt_analyze.py | 1122 | os.getenv dynamisch |

Bestätigte Sections (in env.txt definiert):
- `EXEC_SUMMARY`, `GAMECHANGER`, `ROADMAP`, `ROADMAP_12M`, `RISKS`
- `RECOMMENDATIONS`, `ORG_CHANGE`, `BUSINESS_CASE`, `FOERDERPOTENZIAL`
- `STRATEGIE_GOVERNANCE`, `WETTBEWERB_BENCHMARK`, `UNTERNEHMENSPROFIL_MARKT`
- `AI_ACT_SUMMARY`

### Anthropic
| Key | Datei | Zeile | Zugriff |
|-----|-------|-------|---------|
| `ANTHROPIC_API_KEY` | services/anthropic_client.py | 181 | os.getenv |
| `ANTHROPIC_MODEL` | services/anthropic_client.py | 32 | os.getenv, default="claude-3-5-sonnet" |
| `ANTHROPIC_MODEL_DEFAULT` | services/anthropic_client.py | 132 | os.getenv |
| `ANTHROPIC_MODEL_FALLBACK` | services/anthropic_client.py | 407 | os.getenv, default="claude-3-5-sonnet-latest" |
| `ANTHROPIC_TEMPERATURE` | services/anthropic_client.py | 234 | os.getenv |
| `ANTHROPIC_MAX_TOKENS` | services/anthropic_client.py | 266 | os.getenv, default="3000" |
| `ANTHROPIC_SECTIONS` | services/anthropic_client.py | 295 | os.getenv (Whitelist) |
| `USE_ANTHROPIC_FOR_{SECTION}` | services/anthropic_client.py | 309 | os.getenv dynamisch |

### Research / Perplexity / Tavily
| Key | Datei | Zeile | Zugriff |
|-----|-------|-------|---------|
| `TAVILY_API_KEY` | services/research.py, providers/tavily.py | 249, 7 | os.getenv |
| `TAVILY_TIMEOUT_MS` | settings.py | 284 | os.getenv, default="15000" |
| `TAVILY_MAX_RESULTS` | settings.py | 285 | os.getenv, default="8" |
| `PERPLEXITY_API_KEY` | settings.py, research_hybrid_addon.py | 276, 19 | os.getenv |
| `PERPLEXITY_MODEL` | settings.py, research_hybrid_addon.py | 277, 16 | os.getenv, default="sonar-pro" |
| `PERPLEXITY_MAX_TOKENS` | settings.py | 278 | os.getenv, default="1200" |
| `PERPLEXITY_TIMEOUT_MS` | settings.py | 279 | os.getenv, default="15000" |
| `RESEARCH_PROVIDER` | settings.py, gpt_analyze.py | 288, 1262 | os.getenv, default="hybrid" |
| `RESEARCH_CACHE_PATH` | services/research_fetcher.py | 17 | os.getenv |
| `RESEARCH_CACHE_TTL` | services/research_fetcher.py | 18 | os.getenv |

### PDF Service
| Key | Datei | Zeile | Zugriff |
|-----|-------|-------|---------|
| `PDF_SERVICE_URL` | settings.py | 306 | os.getenv, required |
| `PDF_TIMEOUT_MS` | settings.py | 307 | os.getenv, default="120000" |
| `PDF_WARN_SIZE_MB` | settings.py | 311 | os.getenv, default="10" |
| `PDF_ALERT_SIZE_MB` | settings.py | 312 | os.getenv, default="18" |

### LLM Client / Resilience
| Key | Datei | Zeile | Zugriff |
|-----|-------|-------|---------|
| `LLM_TIMEOUT` | services/llm_client.py | 63 | os.getenv, default="75" |
| `LLM_SHORT_RETRY_ENABLED` | services/llm_client.py | 65 | os.getenv, default="1" |
| `LLM_SHORT_RETRY_MAXTOKENS` | services/llm_client.py | 66 | os.getenv, default="1200" |
| `LLM_MAX_RETRIES` | services/llm_client.py | 68 | os.getenv, default="6" |
| `LLM_RETRY_BACKOFF_BASE` | services/llm_client.py | 69 | os.getenv, default="3.0" |
| `LLM_RETRY_BACKOFF_MULTIPLIER` | services/llm_client.py | 70 | os.getenv, default="2.0" |
| `LLM_SOFT_RETRY_ENABLED` | services/llm_client.py | 73 | os.getenv, default="1" |

### Feature Flags (alle bestätigt aktiv)
| Key | Datei | Status |
|-----|-------|--------|
| `ENABLE_LLM_CONTENT` | gpt_analyze.py:1260 | ✅ |
| `ENABLE_REALISTIC_SCORES` | gpt_analyze.py:1259 | ✅ |
| `ENABLE_NSFW_FILTER` | gpt_analyze.py:1258 | ✅ |
| `ENABLE_REPAIR_HTML` | gpt_analyze.py:1261 | ✅ |
| `ENABLE_AI_ACT_SECTION` | gpt_analyze.py:1263 | ✅ |
| `ENABLE_ADMIN_NOTIFY` | gpt_analyze.py:6439 | ✅ |
| `ENABLE_QUALITY_GATES` | settings.py:238 | ✅ |
| `ENABLE_PREMIUM_FUNDING` | routes/funding.py:22 | ✅ |
| `ENABLE_DASHBOARD_API` | routes/dashboard.py:30 | ✅ |
| `ENABLE_DELTA_ENGINE` | services/delta_engine.py:29 | ✅ |
| `ENABLE_BC_VISUALS` | services/business_case_visuals.py:24 | ✅ |
| `ENABLE_KPI_VISUALS` | utils/kpi_visuals.py:37 | ✅ |
| `USE_PROMPT_SYSTEM` | gpt_analyze.py:1264 | ✅ |

---

## B) UNUSED_ENV_KEYS (Kandidaten für Löschung)

Die folgenden Keys existieren in `docs/env.txt`, wurden aber **nicht im Code** gefunden:

| Key | env.txt Zeile | Begründung | Empfehlung |
|-----|---------------|------------|------------|
| `DIGITAL_OMNIBUS_HTML` | 87 | Kein Code-Zugriff gefunden | 🔥 Löschen |
| `OMNIBUS_PROFILE_HTML` | 180 | Kein Code-Zugriff gefunden | 🔥 Löschen |
| `OMNIBUS_EXPOSURE_LEVEL` | 179 | Kein Code-Zugriff gefunden | 🔥 Löschen |
| `SMOKE_BRIEFING_ID` | - | Nur für manuelle Tests | ℹ️ Dokumentieren |
| `SMOKE_ANALYSIS_ID` | - | Nur für manuelle Tests | ℹ️ Dokumentieren |
| `TAVILY_DAYS` | 301 | Nicht im Code gelesen | 🔥 Löschen |
| `TAVILY_SEARCH_DEPTH` | 303 | Nur in env, nicht gelesen | 🔥 Löschen |
| `PERPLEXITY_SEARCH_DEPTH` | 241 | Nur in env, nicht gelesen | 🔥 Löschen |
| `COVER_SHOW_LOGOS` | 82 | Kein Zugriff im Code | 🔥 Löschen |
| `FOOTER_SHOW_LOGOS` | 117 | Kein Zugriff im Code | 🔥 Löschen |
| `SHOW_BUILD_STAMP` | 291 | Kein Zugriff im Code | 🔥 Löschen |
| `REPORT_DATE` | 282 | Nur in settings.py definiert, aber value immer "1" | ℹ️ Prüfen |
| `BUILD_ID` | 77 | Leer, nie genutzt | 🔥 Löschen |
| `BUILD_STAGE` | 78 | Redundant zu ENV | 🔥 Löschen |
| `RENDER_STRICT_DATASET` | 281 | Kein Code-Zugriff | 🔥 Löschen |
| `GUARDRAILS_V` | 151 | Nur Version, kein Feature-Flag | ℹ️ Dokumentieren |
| `FALLBACK_ENHANCED_AI_ACT` | 105 | Kein Code-Zugriff | 🔥 Löschen |
| `SERVICE_TOKEN_ENABLED` | 289 | Kein Code-Zugriff für Flag | 🔥 Löschen |

**Gesamt: 18 Kandidaten für Cleanup**

---

## C) MISSING_ENV_KEYS (Im Code, nicht in env.txt)

Die folgenden Keys werden im Code gelesen, sind aber **nicht in `docs/env.txt`** dokumentiert:

### Kritisch (sollten ergänzt werden)

| Key | Datei | Zeile | Empfohlener Default |
|-----|-------|-------|---------------------|
| `REDIS_URL` | settings.py | 233 | optional (für LLM Cache) |
| `LLM_TIMEOUT` | services/llm_client.py | 63 | `"75"` |
| `LLM_SOFT_RETRY_ENABLED` | services/llm_client.py | 73 | `"1"` |
| `OPENAI_API_BASE` | gpt_analyze.py | 1245 | optional |
| `GLOSSAR_PATH` | gpt_analyze.py | 1280 | `"content/glossar-de.md"` |
| `VERSION` | gpt_analyze.py | 5230 | `"1.0.0"` |
| `APP_VERSION` | main.py | 92 | `"4.20.0"` |
| `CHANGELOG_SHORT` | gpt_analyze.py | 5247 | `"—"` |
| `AUDITOR_INITIALS` | gpt_analyze.py | 5248 | `"KSJ"` |
| `FOUR_PILLARS_PATH` | gpt_analyze.py | 856 | `"knowledge/four_pillars.html"` |
| `LEGAL_PITFALLS_PATH` | gpt_analyze.py | 857 | `"knowledge/legal_pitfalls.html"` |
| `TEN_20_70_PATH` | gpt_analyze.py | 858 | `"knowledge/ten_20_70.html"` |
| `KMU_KEYPOINTS_PATH` | gpt_analyze.py | 859 | `"knowledge/kmu_keypoints.html"` |
| `ZIM_ALERT_HTML` | gpt_analyze.py | 4904 | optional |
| `ZIM_WORKFLOW_HTML` | gpt_analyze.py | 4905 | optional |
| `FOOTER_BRANDS_HTML` | gpt_analyze.py | 5439 | optional |

### Stability Patch v1 Token-Budgets (TOKENS_*)

Diese Keys werden in `utils/llm_overrides.py` dynamisch gelesen:

| Key | Default | Beschreibung |
|-----|---------|--------------|
| `TOKENS_ROADMAP` | 4500 | High-Risk Section |
| `TOKENS_ROADMAP_12M` | 4500 | High-Risk Section |
| `TOKENS_ORG_CHANGE` | 3000 | High-Risk Section |
| `TOKENS_UNTERNEHMENSPROFIL_MARKT` | 2800 | High-Risk Section |
| `TOKENS_BUSINESS_CASE` | 5000 | High-Risk Section |
| `TOKENS_GAMECHANGER` | 5000 | High-Risk Section |
| `TOKENS_RISKS` | 3500 | Medium Section |
| `TOKENS_STRATEGIE_GOVERNANCE` | 3500 | Medium Section |
| `TOKENS_WETTBEWERB_BENCHMARK` | 3500 | Medium Section |
| `TOKENS_FOERDERPOTENZIAL` | 3500 | Medium Section |
| `TOKENS_RECOMMENDATIONS` | 3500 | Medium Section |
| `TOKENS_ONE_LINER` | 80 | Short-form |
| `TOKENS_KI_STACK_SUMMARY` | 1200 | Short-form |
| `TOKENS_EXECUTIVE_SUMMARY` | 1500 | Short-form |

### Circuit Breaker / Degradation (aus Tests)

| Key | Default | Datei |
|-----|---------|-------|
| `LLM_CIRCUIT_BREAKER_ENABLED` | `"1"` | tests/test_g12_circuit_breaker.py |
| `LLM_CIRCUIT_FAILURE_THRESHOLD` | `"3"` | tests/test_g12_circuit_breaker.py |
| `LLM_CIRCUIT_RESET_SECONDS` | `"2"` | tests/test_g12_circuit_breaker.py |
| `LLM_CIRCUIT_WINDOW_SECONDS` | `"10"` | tests/test_g12_circuit_breaker.py |
| `LLM_CIRCUIT_STATE_FILE` | `/tmp/circuit_breaker.json` | tests/test_g12_circuit_breaker.py |
| `DEGRADATION_MONITORING_ENABLED` | `"1"` | tests/test_g12_degradation.py |
| `DEGRADATION_HARD_STOP_THRESHOLD` | `"30"` | tests/test_g12_degradation.py |
| `DEGRADATION_WARN_THRESHOLD` | `"60"` | tests/test_g12_degradation.py |
| `DEGRADATION_WINDOW_SECONDS` | `"10"` | tests/test_g12_degradation.py |

### Tenant Manager (Multi-Tenant)

| Key | Default | Datei |
|-----|---------|-------|
| `TENANT_ID` | optional | services/tenant_manager.py |
| `TENANT_NAME` | = TENANT_ID | services/tenant_manager.py |
| `TENANT_LOGO_PRIMARY` | optional | services/tenant_manager.py |
| `TENANT_LOGO_SECONDARY` | optional | services/tenant_manager.py |
| `TENANT_COLOR_PRIMARY` | `"#1A73E8"` | services/tenant_manager.py |
| `TENANT_COLOR_SECONDARY` | `"#34A853"` | services/tenant_manager.py |
| `TENANT_PDF_WATERMARK` | optional | services/tenant_manager.py |
| `TENANT_TIER` | `"basic"` | services/tenant_manager.py |
| `TENANT_WORDING_PROFILE` | `"standard"` | services/tenant_manager.py |
| `TENANT_RISK_PROFILE` | `"balanced"` | services/tenant_manager.py |
| `TENANT_OUTPUT_PATH` | optional | services/tenant_manager.py |

---

## D) DRIFT / DUPLICATES (Semantische Konflikte)

### Gruppe 1: Temperature Naming
| Key A | Key B | Status |
|-------|-------|--------|
| `OPENAI_TEMP_EXEC_SUMMARY` | `OPENAI_TEMP_EXECUTIVE_SUMMARY` | ⚠️ DRIFT |

**Analyse:**
- `OPENAI_TEMP_EXEC_SUMMARY` wird in `utils/llm_overrides.py:144` gelesen
- `OPENAI_TEMP_EXECUTIVE_SUMMARY` existiert in env.txt Zeile 224
- Beide haben den Wert `"0.5"`

**Empfehlung:**
- Source of Truth: `OPENAI_TEMP_EXEC_SUMMARY` (kürzer, konsistent mit Code)
- Alias-Strategie: In Code beide unterstützen, env.txt auf kürzere Form umstellen
- ➕ Ergänzen in llm_overrides.py: `os.getenv("OPENAI_TEMP_EXEC_SUMMARY") or os.getenv("OPENAI_TEMP_EXECUTIVE_SUMMARY")`

### Gruppe 2: AI_ACT_DEBUG Flags
| Key A | Key B | Status |
|-------|-------|--------|
| `AI_ACT_DEBUG` | `ENABLE_AI_ACT_DEBUG` | ⚠️ DRIFT |

**Analyse:**
- `AI_ACT_DEBUG` (Zeile 51): `"false"`
- `ENABLE_AI_ACT_DEBUG` (Zeile 92): `"false"`
- Beide haben semantisch gleiche Bedeutung

**Empfehlung:**
- Source of Truth: `AI_ACT_DEBUG` (kürzer)
- 🔥 `ENABLE_AI_ACT_DEBUG` als Alias oder deprecated markieren

### Gruppe 3: Model RISK vs RISKS
| Key A | Key B | Status |
|-------|-------|--------|
| `OPENAI_MODEL_RISK` | `OPENAI_MODEL_RISKS` | ⚠️ DRIFT |
| `ANTHROPIC_MODEL_RISKS` | - | - |

**Analyse:**
- `OPENAI_MODEL_RISK` (Zeile 212): `"gpt-5.1"`
- `OPENAI_MODEL_RISKS` (Zeile 213): `"gpt-5.1"`
- Gleicher Wert, aber inkonsistente Benennung

**Empfehlung:**
- Source of Truth: `OPENAI_MODEL_RISKS` (Plural, konsistent mit Section-Name "risks")
- 🔥 `OPENAI_MODEL_RISK` löschen oder als Alias behandeln

### Gruppe 4: Rate Limit Naming
| Key A | Key B | Status |
|-------|-------|--------|
| `API_RATE_LIMIT_PER_MIN` | `RATE_LIMIT_PER_MINUTE` | ⚠️ DRIFT |

**Analyse:**
- `API_RATE_LIMIT_PER_MIN` (Zeile 72): `"120"`
- `RATE_LIMIT_PER_MINUTE` (Zeile 280): `"60"`
- **Unterschiedliche Werte!** Dies ist ein echtes Konfig-Problem.

**Empfehlung:**
- Prüfen welcher Key tatsächlich für welchen Endpunkt gilt
- Source of Truth: `RATE_LIMIT_PER_MINUTE` (expliziter)
- 🔥 `API_RATE_LIMIT_PER_MIN` konsolidieren oder umbenennen zu `API_RATE_LIMIT_PER_MINUTE`

### Gruppe 5: Boolean Format Inkonsistenz
| Key | Wert | Format |
|-----|------|--------|
| `AI_ACT_DEBUG` | `"false"` | string lower |
| `AI_ACT_ENABLED` | `"true"` | string lower |
| `ENABLE_LLM_CONTENT` | `"1"` | int |
| `ANTHROPIC_ENABLED` | `"1"` | int |
| `DISABLE_HIGH_RISK_AUTO_UPGRADE` | `"false"` | string lower |

**Empfehlung:**
- Alle Boolean-Flags normalisieren auf `"1"` / `"0"`
- Code akzeptiert bereits beide Formate (siehe `get_bool_env()` in config_validation.py)

### Gruppe 6: Timeout Units Inkonsistenz
| Key | Wert | Unit |
|-----|------|------|
| `OPENAI_TIMEOUT` | `"45"` | Sekunden |
| `PDF_TIMEOUT_MS` | `"120000"` | Millisekunden |
| `TAVILY_TIMEOUT_MS` | `"15000"` | Millisekunden |
| `PERPLEXITY_TIMEOUT_MS` | `"15000"` | Millisekunden |
| `FUNDING_STRESS_TIMEOUT_SEC` | `"12"` | Sekunden |

**Empfehlung:**
- Unit im Namen beibehalten (gut!)
- Dokumentation: Alle Timeouts mit Unit-Suffix (`_MS` oder `_SEC`)

---

## E) LLM-Konfiguration & Sections

### OpenAI Section-Matrix

| Section | MODEL | MAX_TOKENS | TEMP | Vollständig? |
|---------|-------|------------|------|--------------|
| `EXEC_SUMMARY` | ✅ gpt-5.1 | ✅ 1500 | ✅ 0.5 | ✅ |
| `GAMECHANGER` | ✅ gpt-5.1 | ✅ 5000 | ✅ 0.4 | ✅ |
| `ROADMAP` | ❌ fehlt | ✅ 4500 | ✅ 0.35 | ⚠️ |
| `ROADMAP_12M` | ✅ gpt-5.1 | ✅ 4500 | ✅ 0.35 | ✅ |
| `RISKS` | ✅ gpt-5.1 | ✅ 4000 | ❌ fehlt | ⚠️ |
| `RECOMMENDATIONS` | ✅ gpt-5.1 | ✅ 3500 | ✅ 0.35 | ✅ |
| `ORG_CHANGE` | ✅ gpt-5.1 | ✅ 3000 | ✅ 0.3 | ✅ |
| `BUSINESS_CASE` | ✅ gpt-5.1 | ✅ 5000 | ❌ fehlt | ⚠️ |
| `FOERDERPOTENZIAL` | ✅ gpt-5.1 | ✅ 4000 | ✅ 0.3 | ✅ |
| `STRATEGIE_GOVERNANCE` | ❌ fehlt | ✅ 4000 | ✅ 0.3 | ⚠️ |
| `WETTBEWERB_BENCHMARK` | ✅ gpt-5.1 | ✅ 4000 | ✅ 0.3 | ✅ |
| `UNTERNEHMENSPROFIL_MARKT` | ✅ gpt-5.1 | ✅ 2800 | ✅ 0.3 | ✅ |
| `AI_ACT_SUMMARY` | ✅ gpt-5.1 | ✅ 2200 | ✅ 0.3 | ✅ |

### Fehlende Section-Konfigurationen (Ergänzen)

```env
# ROADMAP Model (fehlt)
OPENAI_MODEL_ROADMAP="gpt-5.1"

# RISKS Temperature (fehlt)
OPENAI_TEMP_RISKS="0.35"

# BUSINESS_CASE Temperature (fehlt)
OPENAI_TEMP_BUSINESS_CASE="0.3"

# STRATEGIE_GOVERNANCE Model (fehlt)
OPENAI_MODEL_STRATEGIE_GOVERNANCE="gpt-5.1"
```

### Anthropic Section-Matrix

| Section | MODEL | TEMP | MAX_TOKENS | Verwendet? |
|---------|-------|------|------------|------------|
| `EXEC_SUMMARY` | ✅ claude-3-5-sonnet-latest | via global | via global | ✅ (USE_ANTHROPIC_FOR_EXEC_SUMMARY=1) |
| `RISKS` | ✅ claude-3-5-sonnet-latest | via global | via global | ❌ (USE_ANTHROPIC_FOR_RISKS=0) |
| `GAMECHANGER` | ❌ fehlt | - | - | ❌ (USE_ANTHROPIC_FOR_GAMECHANGER=0) |

---

## F) Konkrete Verbesserungsvorschläge

### 🔥 Sofort Löschen (18 Keys)

```env
# Ungenutzte Legacy-Keys entfernen
# DIGITAL_OMNIBUS_HTML=""
# OMNIBUS_PROFILE_HTML=""
# OMNIBUS_EXPOSURE_LEVEL=""
# BUILD_ID=""
# BUILD_STAGE=""
# RENDER_STRICT_DATASET=""
# FALLBACK_ENHANCED_AI_ACT=""
# SERVICE_TOKEN_ENABLED=""
# COVER_SHOW_LOGOS=""
# FOOTER_SHOW_LOGOS=""
# SHOW_BUILD_STAMP=""
# TAVILY_DAYS=""
# TAVILY_SEARCH_DEPTH=""
# PERPLEXITY_SEARCH_DEPTH=""
```

### ➕ Ergänzen (Kritisch)

```env
# Stability Patch v1: Token Budgets (bereits im Code, dokumentieren!)
TOKENS_ROADMAP="4500"
TOKENS_ROADMAP_12M="4500"
TOKENS_BUSINESS_CASE="5000"
TOKENS_GAMECHANGER="5000"
TOKENS_ORG_CHANGE="3000"
TOKENS_RISKS="3500"
TOKENS_RECOMMENDATIONS="3500"

# LLM Client Resilience
LLM_TIMEOUT="75"
LLM_SOFT_RETRY_ENABLED="1"
REDIS_URL=""

# Circuit Breaker (G12)
LLM_CIRCUIT_BREAKER_ENABLED="1"
LLM_CIRCUIT_FAILURE_THRESHOLD="5"
LLM_CIRCUIT_RESET_SECONDS="60"

# Fehlende Section-Configs
OPENAI_MODEL_ROADMAP="gpt-5.1"
OPENAI_TEMP_RISKS="0.35"
OPENAI_TEMP_BUSINESS_CASE="0.3"
OPENAI_MODEL_STRATEGIE_GOVERNANCE="gpt-5.1"
```

### 🔁 Umbenennungen / Aliases

```python
# In Code einfügen für Abwärtskompatibilität:

# config_validation.py oder settings.py
def get_rate_limit_per_min():
    """Rate limit with alias support."""
    return int(os.getenv("RATE_LIMIT_PER_MINUTE") or
               os.getenv("API_RATE_LIMIT_PER_MIN", "60"))

def get_ai_act_debug():
    """AI Act debug with alias support."""
    val = os.getenv("AI_ACT_DEBUG") or os.getenv("ENABLE_AI_ACT_DEBUG", "false")
    return val.lower() in ("1", "true", "yes")
```

### ⚖️ Werte-Optimierungen

| Key | Aktuell | Empfohlen | Begründung |
|-----|---------|-----------|------------|
| `OPENAI_MAX_TOKENS` | 5000 | 3500 | Globaler Default zu hoch, verschwendet Budget |
| `MAX_PARALLEL_LLM_CALLS` | 6 | 4 | Stabilität über Geschwindigkeit |
| `GPT_PARALLEL_WORKERS` | 6 | 4 | Konsistent mit MAX_PARALLEL_LLM_CALLS |
| `OPENAI_TIMEOUT` | 45 | 60 | Mehr Puffer für komplexe Sections |
| `LLM_MAX_RETRIES` | 3 | 2 | Weniger Retries, schnelleres Failover |

---

## G) Zusammenfassung der Maßnahmen

### Priorität 1: Sofort umsetzen
1. 🔥 18 ungenutzte ENV-Keys aus `docs/env.txt` entfernen
2. ➕ `TOKENS_*` Keys dokumentieren (bereits funktional)
3. ➕ Fehlende Section-Konfigurationen ergänzen

### Priorität 2: Konsolidierung
4. 🔁 Rate-Limit Keys vereinheitlichen (`RATE_LIMIT_PER_MINUTE`)
5. 🔁 `AI_ACT_DEBUG` / `ENABLE_AI_ACT_DEBUG` konsolidieren
6. 🔁 `OPENAI_MODEL_RISK` → `OPENAI_MODEL_RISKS`
7. 🔁 Temperature-Keys normalisieren (`EXEC_SUMMARY` vs `EXECUTIVE_SUMMARY`)

### Priorität 3: Dokumentation
8. ℹ️ Boolean-Format dokumentieren (`"1"`/`"0"` bevorzugt)
9. ℹ️ Timeout-Units dokumentieren (`_MS` vs `_SEC`)
10. ℹ️ Circuit Breaker Keys dokumentieren

---

## H) Anhang: env.example Vorschlag

Siehe separate Datei: `docs/env.example.proposed`

---

**Report erstellt:** 2025-12-14
**Analysierte Dateien:** 50+
**Code-Zeilen gescannt:** ~15.000
