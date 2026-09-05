# PLATIN++ v5.3 Architecture Overview

## System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        PLATIN++ v5.3                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Briefing  │───▶│   Analyze   │───▶│  Guardrails │         │
│  │    Input    │    │  (GPT/LLM)  │    │    v5.0     │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         │                  │                  │                 │
│         ▼                  ▼                  ▼                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Prompt    │    │   Report    │    │  Error Gate │         │
│  │   Loader    │    │  Validator  │    │  Hard-Stop  │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         │                  │                  │                 │
│         ▼                  ▼                  ▼                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Prompt    │    │    HTML     │    │    PDF      │         │
│  │  Enhancer   │    │  Sanitizer  │    │   Service   │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         │                  │                  │                 │
│         ▼                  ▼                  ▼                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              Monitoring & Alerts                     │       │
│  └─────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Prompt System (services/prompt_loader.py)
- Manifest-driven prompt discovery (prompt_manifest.json)
- LRU-cached manifest loading
- Jinja2 + variable interpolation support
- Language fallback chain (specific → default)

### 2. Prompt Enhancer (services/prompt_enhancer.py)
- Context injection (guardrails, user inputs)
- Deduplication cache (prevents repetition)
- Size-aware token multipliers:
  - Solo: 0.8x (20% reduction)
  - Team: 1.0x (baseline)
  - KMU: 1.15x (15% increase)
- Solo persona governance simplification

### 3. Guardrails v5.0 (services/guardrails.py)
- Confidence-based detection
- Three detection methods:
  - explicit_keyword (0.7 confidence)
  - negation_action (0.9 confidence)
  - sensitive_area (0.6 confidence)
- Multi-signal boost: +0.15 confidence

### 4. Report Validator (services/report_validator.py)
- Placeholder detection
- Template text detection
- Word count validation (size-specific)
- Section completeness checks

### 5. Error Gate (gpt_analyze.py)
- ReportErrorGate class with categories:
  - critical_errors (blocking)
  - warnings (non-blocking)
  - guardrail_leaks
  - placeholder_violations
  - size_mismatches
- hard_stop_if_invalid() prevents bad reports

### 6. Funding (services/funding_recommender.py, services/funding_service_en.py)
- Size-, region- and sparte-aware filtering; one status rule (`ist_beantragbar`)
- Routing logic (see docs/FUNDING_ROUTING.md):
  - DE (lang=de) → data/funding_programmes_core_2025.json
  - EN + country=DE → data/funding/funding_de_en.json
  - EN + country≠DE → data/funding/funding_eu_core_en.json
- `services/funding_service.py` and `data/funding/funding_de.json` were
  removed on 2026-09-05 (no report read them)

## Data Flow

1. **Briefing** → User answers questionnaire
2. **Analyze** → GPT generates section content
3. **Guardrails** → Detects/handles constraints
4. **Validator** → Checks content quality
5. **Error Gate** → Blocks invalid reports
6. **Template** → Renders HTML
7. **Sanitizer** → Cleans HTML output
8. **PDF** → Generates final document
9. **Monitoring** → Tracks metrics/alerts

## Version Info

- **Version**: PLATIN++ v5.3
- **Manifest**: prompt_manifest.json v5.3
- **Updated**: 2025-12
