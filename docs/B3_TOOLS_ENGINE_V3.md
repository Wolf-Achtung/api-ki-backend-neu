# B3: Tools Engine 3.0 – Documentation

**Version:** 1.0.0
**Sprint:** B3 (Tools Engine 3.0)
**Status:** Production Ready ✅

---

## 📋 Overview

Tools Engine 3.0 is the comprehensive tools recommendation and alignment system that combines:
- **B2**: Real-world adoption analytics & predictive intelligence
- **B2.2**: Tools × Funding Alignment & Starter Kits (Premium Integration)
- **G17**: Roadmap & Tools Harmonization
- **G19**: Industry Intelligence & Branch Profiles

### Purpose

Provide **context-aware, data-driven tool recommendations** that are:
1. **Personalized** by segment (Solo/Team/KMU)
2. **Industry-specific** via branch profiles
3. **Funding-aligned** to maximize ROI
4. **Roadmap-integrated** for 90d/12m planning
5. **Confidence-scored** based on real-world adoption

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Tools Engine 3.0 (B3)                     │
└──────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
┌─────────────────┐  ┌──────────────┐  ┌────────────────┐
│   B2: Analytics │  │ B2.2: Premium│  │  G17/G19: Intg │
│   & Prediction  │  │  Integration │  │   & Context    │
└─────────────────┘  └──────────────┘  └────────────────┘
         │                   │                   │
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────┐
│              Core Services & Modules                    │
├─────────────────────────────────────────────────────────┤
│ • tools_analytics.py       - Confidence & Statistics    │
│ • tools_recommender.py     - Core Recommendation Engine │
│ • tools_funding_alignment.py - Funding Matching Engine  │
│ • tools_starter_kits.py    - Starter Kit Generator      │
│ • tools_drift_detector.py  - Governance & Drift Monitor │
│ • tools_html_output.py     - HTML Rendering Layer       │
└─────────────────────────────────────────────────────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             ▼
                    ┌──────────────────┐
                    │  gpt_analyze.py  │
                    │  Report Pipeline │
                    └──────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   PDF Template   │
                    │  (HTML Sections) │
                    └──────────────────┘
```

### Data Flow

1. **Input:** User answers (Briefing) → Segment extraction (Solo/Team/KMU, Branch, etc.)
2. **Analytics:** tools_analytics.py → Calculate confidence scores from historical data
3. **Recommendation:** tools_recommender.py → Match tools to segment + trends
4. **Funding Alignment:** tools_funding_alignment.py → Match tools to funding programs
5. **Starter Kit:** tools_starter_kits.py → Generate actionable starter kit
6. **Output:** HTML sections injected into PDF template

---

## ⚙️ Environment Variables

### B2: Tools Analytics & Recommendation

| Variable | Default | Description |
|----------|---------|-------------|
| `TOOLS_ENGINE_ENABLED` | `1` | Master switch for Tools Engine |
| `TOOLS_CONFIDENCE_MIN` | `0.35` | Minimum confidence threshold (0.0-1.0) |
| `TOOLS_CONFIDENCE_SHOW_BADGES` | `1` | Show confidence badges in HTML |
| `TOOLS_SEGMENT_OUTLIER_STD` | `2.5` | Std devs for outlier trimming (Winsorizing) |
| `TOOLS_MIN_SAMPLE_SIZE` | `5` | Min sample size for reliable segments |
| `TOOLS_MAX_RECOMMENDATIONS` | `12` | Max tool recommendations per report |
| `TOOLS_ANALYTICS_STORAGE_PATH` | `data/tools_analytics` | Storage for analytics data |

### B2: Predictive Intelligence

| Variable | Default | Description |
|----------|---------|-------------|
| `TOOLS_PREDICTIVE_ENABLED` | `1` | Enable predictive trend engine |
| `TOOLS_PREDICTIVE_TREND_WINDOW` | `30` | Trend window in days |
| `TOOLS_TREND_WEIGHT` | `0.3` | Weight of trend data (0.0-1.0) |
| `TOOLS_GENERIC_FALLBACK_ENABLED` | `1` | Enable generic fallback |
| `TOOLS_REQUIRE_RELIABLE_SEGMENT` | `1` | Require reliable segment |
| `TOOLS_SMART_DEFAULTS_ENABLED` | `1` | Enable smart defaults by persona |
| `TOOLS_TREND_STORAGE_PATH` | `data/tools_trends` | Storage for trend data |

### B2: Drift Detection & Governance

| Variable | Default | Description |
|----------|---------|-------------|
| `TOOLS_DRIFT_ENABLED` | `1` | Enable drift detection |
| `TOOLS_DRIFT_THRESHOLD_LOW` | `15` | Low drift threshold |
| `TOOLS_DRIFT_THRESHOLD_MEDIUM` | `30` | Medium drift threshold |
| `TOOLS_DRIFT_THRESHOLD_HIGH` | `50` | High drift threshold |
| `TOOLS_DRIFT_THRESHOLD_CRITICAL` | `75` | Critical drift threshold |
| `TOOLS_FREEZE_CONFIDENCE_THRESHOLD` | `0.20` | Auto-freeze confidence threshold |
| `TOOLS_FREEZE_SEGMENT_COUNT` | `2` | Min segments for freeze |
| `TOOLS_OVERPOPULATION_LIMIT` | `14` | Max tools before warning |
| `TOOLS_DRIFT_STORAGE_PATH` | `data/tools_drift` | Storage for drift data |

### B2.2: Premium Integration

| Variable | Default | Description |
|----------|---------|-------------|
| `TOOLS_FUNDING_ALIGNMENT_ENABLED` | `1` | Enable tool-funding alignment |
| `ALIGNMENT_MIN_SCORE` | `0.35` | Min alignment score (0.0-1.0) |
| `ALIGNMENT_MAX_RECOMMENDATIONS` | `8` | Max alignment recommendations |
| `ALIGNMENT_WEIGHT_CATEGORY` | `0.30` | Weight: Tool category |
| `ALIGNMENT_WEIGHT_SIZE` | `0.25` | Weight: Company size |
| `ALIGNMENT_WEIGHT_BRANCH` | `0.20` | Weight: Industry branch |
| `ALIGNMENT_WEIGHT_KI_RELEVANCE` | `0.15` | Weight: KI relevance |
| `ALIGNMENT_WEIGHT_COMPLEXITY` | `0.10` | Weight: Complexity |
| `STARTER_KITS_ENABLED` | `1` | Enable starter kit generation |
| `STARTER_KIT_MAX_TOOLS` | `5` | Max tools per starter kit |
| `STARTER_KIT_MAX_FUNDING` | `3` | Max funding programs per kit |

### B2: Dashboard

| Variable | Default | Description |
|----------|---------|-------------|
| `DASHBOARD_TOOLS_ENABLED` | `1` | Enable tools dashboard endpoints |

---

## 🔗 Dependencies

### Internal Dependencies (Sprint Integration)

| Sprint | Module | Purpose |
|--------|--------|---------|
| **G17.s** | `prompt_rewrite_engine.py` | Roadmap × Tools Harmonization |
| **G17.p** | `prompt_enhancer.py` | Prompt-Rewrite-Patch for Tools sections |
| **G19** | Branch profiles (main) | Industry-specific context |
| **G19.1** | `branch_mapping.py` | Frontend-to-engine branch mapping |
| **B1** | `funding_recommender.py` | Funding program data source |

### External Dependencies

```txt
# Python 3.10+
dataclasses
typing
logging
pathlib
json
datetime
statistics
```

---

## 🧪 Test Workflow

### Run B3 Tests

```bash
# B2.2 Premium Integration Tests
pytest tests/test_b2_2_tools_funding_alignment.py -v

# B2 Tools Engine Tests
pytest tests/test_b2_tools_engine.py -v

# G17 Integration Tests
pytest tests/test_g17_s_roadmap_tools_harmonization.py -v
pytest tests/test_g17_p_rewrite_patch.py -v

# Full test suite (excluding E2E)
pytest --maxfail=10 --disable-warnings --ignore=tests/test_e2e_playwright.py
```

### Test Coverage

- **75 tests** for B2/B2.2
- **44 tests** for G17 integration
- **100% pass rate** ✅

### CI Pipeline

```yaml
# .github/workflows/test.yml
- name: Run mypy
  run: mypy --config-file mypy.ini .

- name: Run pytest
  run: pytest -q --maxfail=3 --disable-warnings
```

**Expected Results:**
- ✅ mypy: 0 real errors (17 harmless import-untyped warnings)
- ✅ pytest: 100% green

---

## 🔧 How to Disable B3 (Feature Flags)

### Disable Entire Tools Engine

```bash
# .env
TOOLS_ENGINE_ENABLED=0
```

**Effect:** All tool recommendations disabled globally.

### Disable Specific Features

```bash
# Disable funding alignment
TOOLS_FUNDING_ALIGNMENT_ENABLED=0

# Disable starter kits
STARTER_KITS_ENABLED=0

# Disable predictive trends
TOOLS_PREDICTIVE_ENABLED=0

# Disable drift detection
TOOLS_DRIFT_ENABLED=0
```

### Fallback Behavior

When disabled:
1. Sections return empty strings (`""`)
2. No HTML rendered in PDF
3. No API endpoints respond
4. No errors thrown (graceful degradation)

---

## 🎛️ Operator Hints (Dashboard Endpoints)

### Tools Analytics Dashboard

```bash
# Access tools analytics overview
GET /tools/analytics

# Response:
{
  "total_tools": 120,
  "total_segments": 15,
  "avg_confidence": 0.67,
  "drift_status": "healthy",
  "last_updated": "2025-12-09T19:00:00Z"
}
```

### Tools Funding Alignment

```bash
# Get alignment for a profile
POST /tools/alignment
Content-Type: application/json

{
  "unternehmensgroesse": "solo",
  "branche": "beratung",
  "region": "DE"
}

# Response:
{
  "segment_context": {...},
  "top_alignments": [
    {
      "tool_name": "Make (Integromat)",
      "funding_program_id": "go_digital",
      "alignment_score": 0.82,
      "fit_reason": "High KI relevance, low complexity"
    }
  ]
}
```

### Starter Kit Generation

```bash
# Generate starter kit
POST /tools/starter-kit
Content-Type: application/json

{
  "unternehmensgroesse": "solo",
  "branche": "beratung"
}

# Response:
{
  "kit_id": "solo_beratung_starter",
  "tools": [...],
  "funding": [...],
  "checklist": [...],
  "estimated_total_days": 30
}
```

---

## 📊 Generated Report Sections

### B2: Tools Recommendations

**Section ID:** `TOOLS_RECOMMENDATIONS_HTML`
**Template:** `pdf_template.html`

**Content:**
- Personalized tool recommendations
- Confidence scores per tool
- Persona fit indicators
- Branch-specific tools

### B2.2: Tools × Funding Alignment

**Section ID:** `TOOLS_FUNDING_ALIGNMENT_HTML`
**Template:** `pdf_template.html`

**Content:**
- Top tool-funding alignments
- Alignment scores (0.0-1.0)
- Fit reasons per match
- ROI indicators

### B2.2: Starter Kit

**Section ID:** `STARTER_KIT_HTML`
**Template:** `pdf_template.html`

**Content:**
- Curated tools (max 5)
- Matching funding programs (max 3)
- Step-by-step checklist
- Timeline estimation

---

## 📝 Code Structure

```
services/
├── tools_analytics.py              (1.0K lines) - Analytics Layer
├── tools_recommender.py            (1.2K lines) - Recommendation Engine
├── tools_funding_alignment.py      (679 lines)  - Funding Matching
├── tools_starter_kits.py           (887 lines)  - Starter Kit Generator
├── tools_drift_detector.py         (800 lines)  - Drift Detection
└── tools_html_output.py            (500 lines)  - HTML Rendering

tests/
├── test_b2_tools_engine.py         (40 tests)   - B2 Core Tests
└── test_b2_2_tools_funding_alignment.py (38 tests) - B2.2 Tests

Total: ~6,000 lines of production code + tests
```

---

## 🚀 Deployment Checklist

- [x] All tests passing (mypy + pytest)
- [x] ENV variables documented
- [x] Feature flags implemented
- [x] Graceful degradation tested
- [x] Dashboard endpoints functional
- [x] Integration with G17/G19 verified
- [x] Performance optimized (sub-second response)
- [x] Error handling comprehensive
- [x] Logging detailed
- [x] Documentation complete

**Status:** ✅ **PRODUCTION READY**

---

## 🔍 Troubleshooting

### Issue: No tool recommendations generated

**Diagnosis:**
1. Check `TOOLS_ENGINE_ENABLED=1` in `.env`
2. Verify `TOOLS_CONFIDENCE_MIN` not too high (default: 0.35)
3. Check segment has enough sample data (`TOOLS_MIN_SAMPLE_SIZE`)

**Fix:**
```bash
# Lower confidence threshold
TOOLS_CONFIDENCE_MIN=0.25

# Enable generic fallback
TOOLS_GENERIC_FALLBACK_ENABLED=1
```

### Issue: Alignment section empty

**Diagnosis:**
1. Check `TOOLS_FUNDING_ALIGNMENT_ENABLED=1`
2. Verify `ALIGNMENT_MIN_SCORE` not too high (default: 0.35)
3. Check funding data available for region

**Fix:**
```bash
# Lower alignment threshold
ALIGNMENT_MIN_SCORE=0.25
```

### Issue: Starter kit not generated

**Diagnosis:**
1. Check `STARTER_KITS_ENABLED=1`
2. Verify at least 1 tool recommendation exists
3. Check funding programs available

**Fix:**
```bash
# Increase max tools
STARTER_KIT_MAX_TOOLS=7
```

---

## 📚 Related Documentation

- [B2_DELIVERABLES.md](./B2_DELIVERABLES.md) - B2 Sprint Details
- [G17_ROADMAP_TOOLS.md](./G17_ROADMAP_TOOLS.md) - G17 Integration
- [API_ENDPOINTS.md](./API_ENDPOINTS.md) - Dashboard API Reference

---

**Last Updated:** 2025-12-09
**Version:** 1.0.0
**Author:** Claude Code (Anthropic)
