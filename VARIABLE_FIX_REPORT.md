# Variable Values Fix Report

**Date:** 2026-01-07
**Status:** COMPLETED

---

## Executive Summary

Instead of fixing 52 prompt files with 196 occurrences, we implemented a **single-point backend fix** that:
1. Handles frontend V2 values ("1", "2–10", "11–100")
2. Maps them to prompt-friendly values ("solo", "team", "kmu")
3. Maintains full backward compatibility with legacy values

**Total files modified:** 2 (vs. 52 if we had fixed prompts)
**Total line changes:** ~25 lines

---

## Files Modified

### 1. gpt_analyze.py (Primary Fix)

**Location:** Lines 7039-7062

**Change:** Updated the `size_map` dictionary to handle frontend V2 values

**Before:**
```python
size_raw = briefing.get("unternehmensgroesse", "solo")
size_map = {
    "solo": "solo",   # 1 (Solo-Selbstständig/Freiberuflich)
    "klein": "team",  # 2-10 (Kleines Team)
    "kmu": "kmu",     # 11-100 (KMU)
}
company_size = size_map.get(size_raw, "team")
```

**After:**
```python
size_raw = str(briefing.get("unternehmensgroesse", "1")).strip().lower()
size_map = {
    # Frontend V2 values (primary) - what the questionnaire sends
    "1": "solo",       # 1 (Solo-Selbstständig/Freiberuflich)
    "2–10": "team",    # 2–10 (Kleines Team) - en-dash U+2013
    "2-10": "team",    # 2-10 (Kleines Team) - hyphen fallback
    "11–100": "kmu",   # 11–100 (KMU) - en-dash U+2013
    "11-100": "kmu",   # 11-100 (KMU) - hyphen fallback
    # Legacy/normalized values (backward compatibility)
    "solo": "solo",
    "klein": "team",
    "kmu": "kmu",
    "team": "team",
    # Additional legacy variants
    "freiberufler": "solo",
    "freelancer": "solo",
    "small": "team",
    "medium": "kmu",
    "sme": "kmu",
}
company_size = size_map.get(size_raw, "team")
```

**Location:** Line 12110

**Change:** Use mapped value from sections instead of raw answers

**Before:**
```python
'{COMPANY_SIZE}': answers.get('unternehmensgroesse', 'solo'),
```

**After:**
```python
'{COMPANY_SIZE}': sections.get('COMPANY_SIZE', 'team'),  # Use mapped value from sections
```

---

### 2. services/answers_normalizer.py

**Location:** Lines 35-54

**Change:** Added frontend V2 raw values to the mapping

**Before:**
```python
UNTERNEHMENSGROESSE_MAP = {
    "1 (solo-selbstständig/freiberuflich)": "solo",
    "solo": "solo",
    ...
}
```

**After:**
```python
UNTERNEHMENSGROESSE_MAP = {
    # Frontend V2 raw values (primary)
    "1": "solo",                                  # Raw value from questionnaire
    "2–10": "team",                               # En-dash (U+2013)
    "2-10": "team",                               # Hyphen fallback
    "11–100": "kmu",                              # En-dash (U+2013)
    "11-100": "kmu",                              # Hyphen fallback
    # Frontend V2 with labels
    "1 (solo-selbstständig/freiberuflich)": "solo",
    ...
}
```

---

## Why Backend Fix is Better Than Prompt Fix

| Approach | Files Changed | Occurrences | Maintenance | Readability |
|----------|---------------|-------------|-------------|-------------|
| Backend Fix | 2 | ~25 lines | Low | Prompts stay readable ("solo") |
| Prompt Fix | 52 | 196 | High | Less readable ("1", "2–10") |

**Advantages of Backend Fix:**
1. Single point of truth for value mapping
2. Prompts remain human-readable with semantic values
3. Easy to add new values in the future
4. Proper architectural pattern (normalization at entry point)
5. Full backward compatibility with legacy data

---

## Mapping Summary

| Frontend Sends | Backend Maps To | Prompts Check For |
|----------------|-----------------|-------------------|
| "1" | "solo" | "solo" ✅ |
| "2–10" | "team" | "team" ✅ |
| "11–100" | "kmu" | "kmu" ✅ |

---

## Prompts Unchanged (As Designed)

The following 52 prompt files continue to work correctly using the semantic values:

- prompts/de/_solo_language_rules.md
- prompts/de/ai_act_summary.md
- prompts/de/business_case.md
- prompts/de/executive_summary.md
- prompts/de/gamechanger.md
- ... (and 47 more)

All `{% if COMPANY_SIZE == "solo" %}` conditionals now work because:
1. Frontend sends "1"
2. Backend maps "1" → "solo"
3. Prompt checks "solo" → MATCH ✅

---

## End of Report
