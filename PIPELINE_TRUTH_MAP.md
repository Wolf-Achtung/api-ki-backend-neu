# PIPELINE TRUTH MAP - Report Generation Flow

**Version:** 1.0
**Datum:** 2026-01-18

---

## 1. Prozessmodell

| Prozess | Startkommando | Datei | Env-Flags | Verantwortlich |
|---------|---------------|-------|-----------|----------------|
| **web** | `uvicorn main:app --host 0.0.0.0 --port $PORT` | `main.py` | PORT, LOG_LEVEL, ENV, CORS_*, ENABLE_* | API Server, Router Mounting |
| **worker** | `python -m workers.briefings_worker` | `workers/briefings_worker.py` | WORKER_POLL_INTERVAL, WORKER_ID | Briefings Processing, Pipeline Execution |
| **pdf** | External HTTP | `services/pdf_client.py` | PDF_SERVICE_URL, PDF_TIMEOUT_MS | PDF Rendering via Puppeteer |

---

## 2. Report Generation Flow (Hauptpfad)

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: WORKER CLAIM                                            │
│ File: workers/briefings_worker.py:claim_next_briefing()         │
│ Input: None (DB Poll)                                           │
│ Output: Briefing object with status='processing'                │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: PIPELINE START                                          │
│ File: gpt_analyze.py:14104 run_briefing_pipeline()              │
│ Input: db, briefing_id, email, run_id                           │
│ Output: Report record with status                               │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: ANALYSIS                                                │
│ File: gpt_analyze.py:11989 analyze_briefing()                   │
│ Input: db, briefing_id, run_id                                  │
│ Output: (analysis_id, html_content, metadata)                   │
└─────────────────────────────────────────────────────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────────────────────┐  ┌─────────────────────────────────────┐
│ STEP 3a: SCORES        │  │ STEP 3b: CONTENT GENERATION         │
│ _calculate_realistic_  │  │ _generate_content_sections()        │
│ score() + _calibrate_  │  │ File: gpt_analyze.py:10266          │
│ scores()               │  │ 31 sections parallel (workers=10)   │
│ File: gpt_analyze.py   │  │ Output: Dict[section_key, html]     │
│ :1584-1730             │  │                                     │
└────────────────────────┘  └─────────────────────────────────────┘
         │                            │
         └──────────┬─────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: ZERO-LEAK GUARD                                         │
│ File: services/zero_leak_engine.py                              │
│ Function: precommit_zero_leak_all_sections(sections)            │
│ Input: All generated sections                                   │
│ Output: Cleaned sections (CRITICAL=suppress, BENIGN=clean)      │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: QUALITY ENFORCER                                        │
│ File: services/content_quality_enforcer.py                      │
│ Functions:                                                      │
│   - apply_grammar_fixes(html)                                   │
│   - apply_solo_language_normalizer(sections, size)              │
│   - apply_extended_siezen_guard(sections)                       │
│   - apply_ellipsis_fix(sections)                                │
│ Input: Sections from zero-leak                                  │
│ Output: Polished sections                                       │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: VALIDATION + CONSISTENCY                                │
│ File: services/report_validator.py + consistency_engine.py      │
│ Checks:                                                         │
│   - Word count (min 100-800 per section)                        │
│   - Placeholder detection                                       │
│   - Template phrases                                            │
│   - KPI consistency                                             │
│   - Tools consistency                                           │
│ Input: Polished sections                                        │
│ Output: Validation results + warnings                           │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: HTML RENDER                                             │
│ File: services/report_renderer.py:401 render()                  │
│ Steps:                                                          │
│   1. Language detection (de/en)                                 │
│   2. Template selection (pdf_template.html/pdf_template_en.html)│
│   3. Context building (sections + scores + aliases)             │
│   4. Jinja2 rendering                                           │
│   5. Post-processing (leak cleanup, pagebreak cleanup)          │
│ Input: briefing_obj, sections, scores, meta                     │
│ Output: {html: str, meta: dict}                                 │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 8: HTML OPTIMIZATION                                       │
│ File: services/html_minifier.py                                 │
│ Functions:                                                      │
│   - compress_html(html)                                         │
│   - compress_long_tables(html, max_rows)                        │
│   - remove_empty_sections(html, min_chars)                      │
│   - optimize_html_for_pdf_v3()                                  │
│ Input: Rendered HTML                                            │
│ Output: Optimized HTML (< 1MB)                                  │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 9: PDF GENERATION                                          │
│ File: services/pdf_client.py:205 render_pdf_from_html()         │
│ External Call: POST {PDF_SERVICE_URL}/generate-pdf              │
│ Options: A4, printBackground, displayHeaderFooter               │
│ Timeout: 60s, Retries: 3 with exponential backoff               │
│ Input: Optimized HTML + meta + pdf_options                      │
│ Output: PDF bytes or URL                                        │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 10: EMAIL DELIVERY                                         │
│ File: gpt_analyze.py:14008 _send_emails()                       │
│ Service: Resend API                                             │
│ Recipients: User + Admin (if enabled)                           │
│ Attachments: PDF + Briefing JSON (admin only)                   │
│ Input: Report, PDF URL/bytes                                    │
│ Output: Email delivery status                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. KPI Authority Table (Single Source of Truth)

| KPI | Quelle der Wahrheit | Datei:Zeile | Wo injiziert | Wo nochmal berechnet | Risikostelle |
|-----|---------------------|-------------|--------------|----------------------|--------------|
| **ROI_12M** | `calculate_roi(annual_savings, investment_total)` | bc_engine_v2.py:893 | inject_canonical_to_sections():614 | simulation_engine (G34), bc_reconciler | Doppelte Berechnung: G30 vs G34. Healing modifiziert ROI nachträglich |
| **PAYBACK_MONTHS** | `calculate_payback(investment, monthly_savings)` | bc_engine_v2.py:913 | inject_canonical_to_sections():614 | simulation_engine | Nullified wenn negativ. Healing regeneriert Payback |
| **CAPEX_EUR** | `BusinessCaseCanonical.capex_eur` | bc_engine_v2.py:599 | inject_canonical_to_sections() | - | AI Act CAPEX Factor wird NICHT in ROI reflektiert |
| **OPEX_MONTH_EUR** | `BusinessCaseCanonical.opex_month_eur` | bc_engine_v2.py:602 | inject_canonical_to_sections() | - | Defaults werden NACH ROI-Calc injiziert → MISMATCH |
| **HOURLY_RATE** | `get_hourly_rate(size)` | bc_engine_v2.py:109-114 | inject_canonical_to_sections():554 | roi_calculator.py | Keine User-Overrides möglich. Size-Normalisierung kritisch |
| **SZENARIEN** | `generate_scenarios()` | bc_engine_v2.py:1449-1520 | via scenarios dict | - | Multiple Healing (heal→normalize→ensure) nicht idempotent |
| **SIMULATION P50/P80** | `run_monte_carlo_simulation()` | bc_simulation.py:786 | NICHT inject_canonical | - | Separate Engine, kann von G30-ROI abweichen (>15% acceptable) |

### Kritische Inkonsistenz-Pfade

```
PFAD 1: ROI Doppelberechnung
  G30: calculate_roi() → BusinessCaseReport.roi_12m
       ↓
  inject_canonical_to_sections() → sections["ROI_12M"]
       ↓
  G34: run_monte_carlo_simulation() → samples ROI nochmal
       ↓
  P50 kann ≠ ROI_12M (bis 15% Abweichung "acceptable")

PFAD 2: Scenario Healing Chain
  generate_scenarios() → 3 Scenarios (opt/real/cons)
       ↓
  heal_scenario_consistency() → Sortiert nach ROI, labels neu
       ↓  [ROI kann sich ÄNDERN!]
  normalize_scenario_order() → RENORMALISIERT nochmal
       ↓  [ROI kann sich NOCHMAL ÄNDERN!]
  ensure_scenario_consistency() → Kombiniert
       ↓
  _bc_healed Flag → Verhindert Re-Check in consistency_engine

PFAD 3: OPEX/CAPEX AI Act
  AI Act Module: capex_factor, opex_factor
       ↓
  Faktoren werden angewendet
       ↓
  ABER: ROI wird NICHT mit modifiziertem CAPEX neuberechnet!
```

---

## 4. Section Generation Details

### 31 Parallel Sections

| Section Key | Min Words | Gate | Fallback |
|-------------|-----------|------|----------|
| EXECUTIVE_SUMMARY_HTML | 150+ | LeakDetector | generic_fallback |
| QUICK_WINS_HTML | 100+ | ValidationGate | _fallback_quick_wins_html() |
| RISKS_HTML | 200+ | SizeValidator | _get_fallback_content() |
| GAMECHANGER_HTML | 250+ | SizeValidator | generic_fallback |
| RECOMMENDATIONS_HTML | 250+ | ValidationGate | _get_fallback_content() |
| ROADMAP_12M_HTML | 250+ | SizeValidator | fallback_roadmap_html |
| BUSINESS_CASE_HTML | 200+ | ValidationGate | bc_template_fallback |
| FOERDERPOTENZIAL_HTML | 300+ | ValidationGate | _get_fallback_content() |
| STRATEGIE_GOVERNANCE_HTML | 200+ | SizeValidator | governance_fallback |
| TOOLS_EMPFEHLUNGEN_HTML | 100+ | - | toolbox_default |
| AI_ACT_SUMMARY_HTML | 150+ | LeakDetector | ai_act_fallback |

### Generation Flow per Section

```
1. Prompt-Loading (services/prompt_loader.py)
   ↓
2. Variablen-Interpolation (_build_prompt_vars)
   ↓
3. LLM-Aufruf (GPT-4/Claude, temp=0.7-0.9, max_tokens=1500-4000)
   ↓
4. HTML-Sanierung
   ↓
5. Leak-Detection (services/zero_leak_engine.py)
   ↓
6. Word-Count-Check
   ↓
7. Fallback wenn nötig (_get_fallback_content)
```

---

## 5. Typische Performance Metriken

| Komponente | Duration |
|------------|----------|
| Score Calculation | ~100ms |
| Content Generation (31 parallel) | ~45-90s |
| Zero-Leak Guard | ~500ms |
| Validation/Consistency | ~1-2s |
| HTML Rendering | ~2-3s |
| PDF Rendering | ~15-30s |
| Email Delivery | ~2-5s |
| **TOTAL** | **~65-130 seconds** |

---

## 6. Environment Variables (Kritisch)

| Variable | Default | Impact |
|----------|---------|--------|
| `PDF_SERVICE_URL` | (required) | PDF-Service Endpoint |
| `PDF_TIMEOUT_MS` | 90000 | PDF-Rendering Timeout |
| `GPT_PARALLEL_WORKERS` | 10 | Max parallele LLM-Aufrufe |
| `HARD_STOP_MAX_FALLBACKS` | 5 | Max Fallback Attempts |
| `REPORT_TEMPLATE_PATH_DE` | templates/pdf_template.html | DE-Template |
| `REPORT_TEMPLATE_PATH_EN` | templates/pdf_template_en.html | EN-Template |
| `DISABLE_EMAILS` | "0" | Email-Kill-Switch |
| `ENABLE_ADMIN_NOTIFY` | "1" | Admin-Benachrichtigungen |
