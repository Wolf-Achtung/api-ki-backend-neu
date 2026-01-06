# PHASE 5: DATA MAPPING STANDARDIZATION PLAN

## Overview

This plan addresses all mapping inconsistencies identified in the Comprehensive Audit.

**Objective:** Standardize company size, Bundesland, and Branche mappings across all services.

---

## PHASE 5A: Company Size Standardization [CRITICAL]

### Standard Values
```
Questionnaire Input → Standard Internal Value → Display Label (DE/EN)
"1"                 → "solo"                   → "Einzelunternehmen" / "Solo entrepreneur"
"2-10"              → "small"                  → "Kleinunternehmen" / "Small business"
"11-100"            → "medium"                 → "Mittelstand (KMU)" / "Medium enterprise (SME)"
```

### FIX 5A.1: benchmark_engine.py

**File:** `services/benchmark_engine.py`

**Changes Required:**

1. **Line 240-241** - Update SIZE_BENCHMARK_MULTIPLIERS:
```python
# BEFORE:
SIZE_BENCHMARK_MULTIPLIERS = {
    "team": {"kpi": 1.0, "tools": 1.0, "risk": 1.0, "automation": 1.0, "funding": 1.0, "strategy": 1.0},
    "kmu": {"kpi": 1.15, "tools": 1.1, "risk": 0.9, "automation": 1.15, "funding": 1.2, "strategy": 1.15},
}

# AFTER:
SIZE_BENCHMARK_MULTIPLIERS = {
    "solo": {"kpi": 0.85, "tools": 0.9, "risk": 1.1, "automation": 0.8, "funding": 0.9, "strategy": 0.85},
    "small": {"kpi": 1.0, "tools": 1.0, "risk": 1.0, "automation": 1.0, "funding": 1.0, "strategy": 1.0},
    "medium": {"kpi": 1.15, "tools": 1.1, "risk": 0.9, "automation": 1.15, "funding": 1.2, "strategy": 1.15},
}
```

2. **Line 1092** - Update size_labels (DE):
```python
# BEFORE:
size_labels = {"solo": "Einzelunternehmer", "team": "Team", "kmu": "KMU"}

# AFTER:
size_labels = {"solo": "Einzelunternehmen", "small": "Kleinunternehmen", "medium": "Mittelstand (KMU)"}
```

3. **Line 1109** - Update size_labels (EN):
```python
# BEFORE:
size_labels = {"solo": "solo entrepreneur", "team": "team", "kmu": "SME"}

# AFTER:
size_labels = {"solo": "solo entrepreneur", "small": "small business", "medium": "SME"}
```

4. **Line 1413-1436** - Update _normalize_size():
```python
def _normalize_size(size: Any) -> str:
    """Normalize company size to standard labels: solo, small, medium."""
    if not size:
        return "small"

    size_str = str(size).lower().strip()

    # Solo: 1 person
    solo_keywords = ["solo", "einzelunternehmer", "einzelunternehmen", "freelancer", "selbststaendig", "1", "one"]
    # Small: 2-10 employees (was "team")
    small_keywords = ["team", "klein", "small", "startup", "2-10", "5", "2"]
    # Medium: 11-100 employees (was "kmu")
    medium_keywords = ["kmu", "sme", "mittel", "medium", "10-50", "50", "11-100", "enterprise"]

    for kw in solo_keywords:
        if kw in size_str:
            return "solo"

    for kw in medium_keywords:
        if kw in size_str:
            return "medium"

    for kw in small_keywords:
        if kw in size_str:
            return "small"

    return "small"
```

5. **Line 1238, 1246** - Update fallback:
```python
# BEFORE:
size_label = _normalize_size(briefing.get("unternehmensgroesse", briefing.get("company_size", "team")))
size_mult = SIZE_BENCHMARK_MULTIPLIERS.get(size_label, SIZE_BENCHMARK_MULTIPLIERS["team"])

# AFTER:
size_label = _normalize_size(briefing.get("unternehmensgroesse", briefing.get("company_size", "small")))
size_mult = SIZE_BENCHMARK_MULTIPLIERS.get(size_label, SIZE_BENCHMARK_MULTIPLIERS["small"])
```

---

### FIX 5A.2: business_case_simulation.py

**File:** `services/business_case_simulation.py`

Update all size references from "team"/"kmu" to "small"/"medium".

---

### FIX 5A.3: executive_summary_diamond.py

**File:** `services/executive_summary_diamond.py`

Update SIZE_MULTIPLIERS:
```python
SIZE_MULTIPLIERS = {
    "solo": 0.7,
    "small": 1.0,    # was "team"
    "medium": 1.2,   # was "kmu"
}
```

---

### FIX 5A.4: performance_layer_v5.py

**File:** `services/performance_layer_v5.py`

Remove "large" and "enterprise" - replace with "medium":
```python
# BEFORE:
if size in ["large", "enterprise"]:
    ...

# AFTER:
if size == "medium":
    ...
```

---

### FIX 5A.5: fallback_guard.py

**File:** `services/fallback_guard.py`

Update keyword detection at lines 256-260:
```python
# BEFORE:
if "solo" in size_raw or "freiberuf" in size_raw:
    ...
elif "team" in size_raw or "klein" in size_raw:
    ...

# AFTER:
if "solo" in size_raw or "freiberuf" in size_raw or "einzelunternehm" in size_raw:
    ...
elif "small" in size_raw or "klein" in size_raw or "team" in size_raw:
    ...
elif "medium" in size_raw or "kmu" in size_raw or "mittel" in size_raw:
    ...
```

---

### FIX 5A.6: tools_html_output.py

**File:** `services/tools_html_output.py`

Update size mappings at lines 208-221.

---

## PHASE 5B: Bundesland Code Standardization [MEDIUM]

### Standard: Lowercase 2-letter codes

```
"be" → Berlin
"by" → Bayern
"bw" → Baden-Württemberg
...
```

### FIX 5B.1: Case-insensitive lookup

Add to all Bundesland lookups:
```python
bundesland_code = str(bundesland).lower()[:2]
bundesland_name = BUNDESLAND_MAPPING.get(bundesland_code, bundesland)
```

### FIX 5B.2: Test file updates

Update `tests/test_funding_en_phase2.py`:
```python
# BEFORE:
"bundesland": "BY",

# AFTER:
"bundesland": "by",
```

---

## PHASE 5C: Branche/Industry Mapping [MEDIUM]

### Standard: 12 Questionnaire Branchen

```python
BRANCHE_MAPPING = {
    "marketing": "Marketing & Werbung",
    "beratung": "Beratung & Dienstleistungen",
    "it": "IT & Software",
    "handwerk": "Handwerk & Bau",
    "handel": "Handel & E-Commerce",
    "gesundheit": "Gesundheit & Soziales",
    "finanzen": "Finanzen & Versicherungen",
    "industrie": "Industrie / Produktion",
    "bildung": "Bildung & Schulung",
    "gastronomie": "Gastronomie & Tourismus",
    "kreativ": "Kreativwirtschaft",
    "sonstige": "Sonstige",
}
```

### FIX 5C.1: benchmark_engine.py

Update `_get_industry_benchmarks()` to handle all 12 Branchen.

---

## IMPLEMENTATION CHECKLIST

### Phase 5A (Critical - Do First)
- [ ] FIX 5A.1: benchmark_engine.py - SIZE_BENCHMARK_MULTIPLIERS
- [ ] FIX 5A.1: benchmark_engine.py - size_labels (DE)
- [ ] FIX 5A.1: benchmark_engine.py - size_labels (EN)
- [ ] FIX 5A.1: benchmark_engine.py - _normalize_size()
- [ ] FIX 5A.1: benchmark_engine.py - fallback values
- [ ] FIX 5A.2: business_case_simulation.py
- [ ] FIX 5A.3: executive_summary_diamond.py
- [ ] FIX 5A.4: performance_layer_v5.py
- [ ] FIX 5A.5: fallback_guard.py
- [ ] FIX 5A.6: tools_html_output.py

### Phase 5B (Medium)
- [ ] FIX 5B.1: Case-insensitive Bundesland lookups
- [ ] FIX 5B.2: Test file updates

### Phase 5C (Medium)
- [ ] FIX 5C.1: benchmark_engine.py - 12 Branchen support

---

## TESTING

After each fix phase:

```bash
# 1. Type check
mypy --config-file mypy.ini core/ routes/ services/ main.py settings.py

# 2. Run tests
pytest tests/ -v -x

# 3. Specific test files
pytest tests/test_g17_8_funding_optimizer.py -v
pytest tests/test_g26_funding_engine_v2.py -v
pytest tests/test_funding_en_phase2.py -v
```

---

## RISK ASSESSMENT

| Fix | Risk Level | Rollback Strategy |
|-----|------------|-------------------|
| 5A.1-6 | HIGH | Git revert to pre-fix commit |
| 5B.1-2 | LOW | Case-insensitive is backward compatible |
| 5C.1 | MEDIUM | Fallback to "sonstige" for unmapped |

---

## DEPENDENCIES

Phase 5 builds on:
- Phase 1-4 (Content improvements)
- Phase 4 (Live data integration) - uses Bundesland codes

Ensure live_data_integration.py works with standardized values.
