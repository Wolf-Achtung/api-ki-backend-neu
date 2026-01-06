# COMPREHENSIVE PROJECT AUDIT REPORT
## Data Mapping & Field Usage Analysis

**Date:** 2026-01-06
**Scope:** Complete backend analysis for mapping errors and unused fields

---

## EXECUTIVE SUMMARY

| Category | Issues Found | Critical | Medium | Low |
|----------|-------------|----------|--------|-----|
| Company Size Mappings | 7 | 5 | 2 | 0 |
| Bundesland Codes | 3 | 1 | 2 | 0 |
| Branche Mappings | 2 | 1 | 1 | 0 |
| Country Mappings | 0 | 0 | 0 | 0 |
| Field Usage | 1 | 0 | 1 | 0 |
| Fallback Logic | 2 | 1 | 1 | 0 |
| **TOTAL** | **15** | **8** | **7** | **0** |

---

## 1. COMPANY SIZE MAPPING ISSUES [CRITICAL]

### 1.1 Problem Description
The questionnaire provides company sizes as:
- `"1"` → should map to `"solo"`
- `"2-10"` → should map to `"small"`
- `"11-100"` → should map to `"medium"`

However, multiple services use **non-standard values**: `"team"`, `"kmu"`, `"large"`, `"enterprise"`

### 1.2 Affected Files

| File | Line(s) | Issue | Severity |
|------|---------|-------|----------|
| `services/benchmark_engine.py` | 240-241 | SIZE_BENCHMARK_MULTIPLIERS uses "team", "kmu" | CRITICAL |
| `services/benchmark_engine.py` | 1416, 1421-1434 | _normalize_size() returns "team"/"kmu" | CRITICAL |
| `services/business_case_simulation.py` | 79-80, 544-553 | Uses "team", "kmu" mappings | CRITICAL |
| `services/executive_summary_diamond.py` | 50, 57, 534+ | SIZE_MULTIPLIERS with "team", "kmu" | CRITICAL |
| `services/performance_layer_v5.py` | 57-58, 87, 95 | Uses "large", "enterprise" | CRITICAL |
| `services/fallback_guard.py` | 104, 110, 253-260 | Uses "team", "kmu" | MEDIUM |
| `services/tools_html_output.py` | 208-221 | Uses "team", "kmu" | MEDIUM |

### 1.3 Code Examples

**benchmark_engine.py:240-241** (CRITICAL):
```python
SIZE_BENCHMARK_MULTIPLIERS = {
    "team": {"kpi": 1.0, "tools": 1.0, ...},
    "kmu": {"kpi": 1.15, "tools": 1.1, ...},
}
```
**Should be:**
```python
SIZE_BENCHMARK_MULTIPLIERS = {
    "solo": {"kpi": 0.9, ...},
    "small": {"kpi": 1.0, ...},  # was "team"
    "medium": {"kpi": 1.15, ...},  # was "kmu"
}
```

**benchmark_engine.py:1413-1436** (CRITICAL):
```python
def _normalize_size(size: Any) -> str:
    # Returns "team", "kmu" instead of "small", "medium"
    team_keywords = ["team", "klein", "small", "startup", "2-10", "5"]
    kmu_keywords = ["kmu", "sme", "mittel", "medium", "10-50", "50", "enterprise"]
    ...
    return "team"  # Should return "small"
```

---

## 2. BUNDESLAND CODE ISSUES [MEDIUM]

### 2.1 Problem Description
- `live_data_integration.py` expects **lowercase** codes: `"be"`, `"by"`, `"nw"`
- `funding_service_en.py` normalizes to **uppercase**: `"BY"`, `"BE"`, `"BW"`
- Tests use **uppercase** codes

### 2.2 Affected Files

| File | Line(s) | Issue | Severity |
|------|---------|-------|----------|
| `services/live_data_integration.py` | 40-57 | BUNDESLAND_MAPPING uses lowercase keys | MEDIUM |
| `services/funding_service_en.py` | 211 | Normalizes to uppercase | MEDIUM |
| `tests/test_funding_en_phase2.py` | 38, 69 | Uses uppercase "BY" | CRITICAL |

### 2.3 Recommended Fix
Standardize to **lowercase** everywhere, or ensure case-insensitive lookups:
```python
bundesland_name = BUNDESLAND_MAPPING.get(bundesland.lower(), bundesland)
```

---

## 3. BRANCHE/INDUSTRY MAPPING ISSUES [MEDIUM]

### 3.1 Problem Description
The questionnaire provides 12 specific Branchen:
1. Marketing & Werbung
2. Beratung & Dienstleistungen
3. IT & Software
4. Handwerk & Bau
5. Handel & E-Commerce
6. Gesundheit & Soziales
7. Finanzen & Versicherungen
8. Industrie / Produktion
9. Bildung & Schulung
10. Gastronomie & Tourismus
11. Kreativwirtschaft
12. Sonstige

However, some services use different/simplified mappings.

### 3.2 Affected Files

| File | Line(s) | Issue | Severity |
|------|---------|-------|----------|
| `services/benchmark_engine.py` | 634 | Uses generic "manufacturing" | CRITICAL |
| `services/benchmark_engine.py` | 669 | _get_industry_benchmarks doesn't map all 12 Branchen | MEDIUM |

---

## 4. COUNTRY MAPPINGS [OK]

### 4.1 Status: COMPLIANT

`services/live_data_integration.py` has comprehensive COUNTRY_MAPPING:
```python
COUNTRY_MAPPING = {
    "DE": "Deutschland",
    "AT": "Österreich",
    "CH": "Schweiz",
    "FR": "Frankreich",
    ...
}
```

No issues found.

---

## 5. FREITEXT FIELD USAGE (hauptleistung) [OK]

### 5.1 Status: PROPERLY USED

The `hauptleistung` field is used correctly in:
- `services/research_policy.py:92` - Prompt enhancement
- `services/ai_act_module.py:975-976` - Use case fallback
- `services/tools_recommender.py:590-626` - Keyword matching
- `services/research_pipeline.py:422-423` - Query building
- `services/profile_box.py:14` - Display label

No issues found.

---

## 6. PROMPT TEMPLATE ISSUES [INFO]

### 6.1 Prompt Files Structure
- **DE prompts:** 57 files in `/prompts/de/`
- **EN prompts:** 57 files in `/prompts/en/`

All prompts use Markdown format with placeholders.

### 6.2 Potential Issues
- Some EN prompts may still contain German placeholders
- Need verification that all 12 Branchen are represented in prompts

---

## 7. FALLBACK LOGIC ISSUES [MEDIUM]

### 7.1 Fallback Guard System

`services/fallback_guard.py` has a comprehensive fallback coordination system but uses deprecated company size values.

| File | Line(s) | Issue | Severity |
|------|---------|-------|----------|
| `services/fallback_guard.py` | 253-260 | size mapping uses "team", "kmu" | CRITICAL |
| `services/fallback_guard.py` | 256-258 | solo/team/kmu keyword detection | MEDIUM |

### 7.2 Code Example
```python
# Line 256-260
if "solo" in size_raw or "freiberuf" in size_raw:
    ...
elif "team" in size_raw or "klein" in size_raw:
    ...
```

---

## PRIORITY FIX LIST

### Phase 5A: Critical Fixes (MUST FIX)

| Priority | File | Function/Section | Fix Description |
|----------|------|------------------|-----------------|
| P1 | benchmark_engine.py | SIZE_BENCHMARK_MULTIPLIERS | Replace "team"→"small", "kmu"→"medium" |
| P1 | benchmark_engine.py | _normalize_size() | Return "small"/"medium" instead of "team"/"kmu" |
| P1 | business_case_simulation.py | size mappings | Update to solo/small/medium |
| P1 | executive_summary_diamond.py | SIZE_MULTIPLIERS | Update to solo/small/medium |
| P1 | performance_layer_v5.py | size handling | Remove "large"/"enterprise", use solo/small/medium |

### Phase 5B: Medium Fixes (SHOULD FIX)

| Priority | File | Function/Section | Fix Description |
|----------|------|------------------|-----------------|
| P2 | fallback_guard.py | size detection | Update keyword matching |
| P2 | tools_html_output.py | size references | Update to solo/small/medium |
| P2 | tests/*.py | bundesland codes | Standardize to lowercase |
| P2 | benchmark_engine.py | _get_industry_benchmarks | Add all 12 Branchen mappings |

### Phase 5C: Low Priority (NICE TO HAVE)

| Priority | File | Function/Section | Fix Description |
|----------|------|------------------|-----------------|
| P3 | funding_service_en.py | bundesland handling | Use lowercase consistently |
| P3 | prompts/en/* | German placeholders | Check and translate |

---

## TESTING REQUIREMENTS

After fixes, run:
```bash
# Type checking
mypy --config-file mypy.ini core/ routes/ services/ main.py settings.py

# Unit tests
pytest tests/ -v

# Integration tests (if available)
pytest tests/integration/ -v
```

---

## APPENDIX: File Reference

### Services with Size Mappings
1. `services/benchmark_engine.py`
2. `services/business_case_engine_v2.py` (COMPLIANT - uses normalize_company_size)
3. `services/business_case_simulation.py`
4. `services/executive_summary_diamond.py`
5. `services/performance_layer_v5.py`
6. `services/fallback_guard.py`
7. `services/tools_html_output.py`
8. `services/funding_service_en.py`

### Services with Bundesland Mappings
1. `services/live_data_integration.py`
2. `services/funding_service_en.py`
3. `services/research_policy.py`
4. `gpt_analyze.py`

### Services with Branche/Industry Mappings
1. `services/benchmark_engine.py`
2. `gpt_analyze.py` (Phase 3 - COMPLIANT with 12 Branchen)
3. `services/tools_recommender.py`
