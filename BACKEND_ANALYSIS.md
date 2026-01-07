# Backend Analysis Report - COMPANY_SIZE Variable Issue

**Date:** 2026-01-07
**Analyst:** Claude Code
**Priority:** P0 - BLOCKING

---

## Executive Summary

**CRITICAL FINDING:** The backend has a mapping inconsistency that causes COMPANY_SIZE to receive the wrong values when processing prompts.

**Root Cause:** The backend code in `gpt_analyze.py` (lines 7041-7047) expects old-style values (`"solo"`, `"klein"`, `"kmu"`) but the frontend sends new-style values (`"1"`, `"2–10"`, `"11–100"`).

---

## Detailed Analysis

### 1. Frontend Values (CORRECT)

From `formbuilder_de_SINGLE_FULL.js` and normalized forms:

```javascript
// unternehmensgroesse options:
{ value: "1", label: "1 (Solo-Selbstständig/Freiberuflich)" }
{ value: "2–10", label: "2–10 (Kleines Team)" }  // Note: en-dash (U+2013)
{ value: "11–100", label: "11–100 (KMU)" }       // Note: en-dash (U+2013)
```

### 2. Backend Normalization (`answers_normalizer.py`)

File: `services/answers_normalizer.py` (lines 35-46)

```python
UNTERNEHMENSGROESSE_MAP = {
    "1 (solo-selbstständig/freiberuflich)": "solo",
    "solo": "solo",
    "2–10 (kleines team)": "team",
    "2-10 (kleines team)": "team",
    "2-10": "team",
    "team": "team",
    "11–100 (kmu)": "kmu",
    "11-100 (kmu)": "kmu",
    "11-100": "kmu",
    "kmu": "kmu",
}
```

**Issue:** The raw value `"1"` is NOT in the map! It only maps `"1 (solo-selbstständig/freiberuflich)"`.

### 3. Backend COMPANY_SIZE Mapping (`gpt_analyze.py`)

**Location 1:** Lines 7041-7047 (PRIMARY ISSUE)

```python
# Map unternehmensgroesse to COMPANY_SIZE for roadmap/gamechanger prompts
# Actual sizes from questionnaire: solo (1), klein (2-10), kmu (11-100)
size_raw = briefing.get("unternehmensgroesse", "solo")  # ❌ Default assumes old format
size_map = {
    "solo": "solo",   # 1 (Solo-Selbstständig/Freiberuflich)
    "klein": "team",  # 2-10 (Kleines Team)
    "kmu": "kmu",     # 11-100 (KMU)
}
company_size = size_map.get(size_raw, "team")  # ❌ Doesn't handle "1", "2–10", "11–100"
```

**Problem:** If frontend sends `"1"`, it doesn't match any key → falls back to `"team"` (wrong!)

**Location 2:** Lines 3013-3021 (CORRECT implementation exists!)

```python
company_size = briefing_data.get("unternehmensgroesse", "1")  # "1", "2–10", "11–100"
size_mapping = {
    "1": "solo",
    "2–10": "small",
    "11–100": "medium"
}
company_size_normalized = size_mapping.get(str(company_size), "solo")
```

**This is the correct approach** - but it uses different output values ("solo", "small", "medium")!

**Location 3:** Line 12095

```python
'{COMPANY_SIZE}': answers.get('unternehmensgroesse', 'solo'),
```

**Problem:** Directly passes raw value without any mapping, with wrong default.

### 4. What Prompts Expect

The prompts use Jinja2 conditionals checking for:

```jinja2
{% if COMPANY_SIZE == "solo" %}
{% elif COMPANY_SIZE == "team" %}
{% else %}  <!-- kmu -->
{% endif %}
```

### 5. The Mismatch

| Frontend Sends | Backend Expected | Prompt Checks | Result |
|----------------|------------------|---------------|--------|
| `"1"` | `"solo"` | `"solo"` | ❌ No match (falls to "team") |
| `"2–10"` | `"klein"` | `"team"` | ❌ No match |
| `"11–100"` | `"kmu"` | `"kmu"` | ❌ No match |

---

## Fix Options

### Option A: Fix Backend Mapping (RECOMMENDED - 1 file change)

Update `gpt_analyze.py` lines 7041-7047 to handle frontend values:

```python
size_raw = briefing.get("unternehmensgroesse", "1")  # Frontend sends "1", "2–10", "11–100"
size_map = {
    # Frontend V2 values (primary)
    "1": "solo",
    "2–10": "team",   # en-dash
    "2-10": "team",   # hyphen fallback
    "11–100": "kmu",  # en-dash
    "11-100": "kmu",  # hyphen fallback
    # Legacy fallback (if normalized)
    "solo": "solo",
    "klein": "team",
    "kmu": "kmu",
}
company_size = size_map.get(size_raw, "team")
```

**Pros:** Single file fix, prompts remain readable
**Cons:** None significant

### Option B: Fix All Prompts (Per briefing - 40+ files)

Update all prompts to use frontend values:

```jinja2
{% if COMPANY_SIZE == "1" %}
{% elif COMPANY_SIZE == "2–10" %}
{% else %}  <!-- 11–100 -->
{% endif %}
```

**Pros:** Prompts match frontend exactly
**Cons:** 40+ files to update, less readable ("1" vs "solo")

---

## Backend Files Summary

| File | Lines | Issue | Fix Needed |
|------|-------|-------|------------|
| `gpt_analyze.py` | 7041-7047 | Wrong mapping keys | YES (critical) |
| `gpt_analyze.py` | 12095 | Raw value passed | YES (minor) |
| `answers_normalizer.py` | 35-46 | Missing "1" key | YES (add entry) |

---

## Recommendation

**Implement Option A (Backend Fix)** for these reasons:

1. Single point of fix (1-2 files vs 40+ prompt files)
2. Prompts remain human-readable ("solo", "team", "kmu")
3. Backend normalization is the proper architectural pattern
4. Reduces future maintenance burden

However, if the decision is to fix prompts (Option B), the fix script in the briefing will work.

---

## Files Where Variables Are Set

### Primary Location (needs fix)
- `gpt_analyze.py:7087` - Sets `COMPANY_SIZE` for templates

### Secondary Locations (for context)
- `gpt_analyze.py:3013-3021` - Correct mapping exists (different function)
- `gpt_analyze.py:11141` - Sets `sections["COMPANY_SIZE"]`
- `services/answers_normalizer.py` - Normalizes `unternehmensgroesse`

---

## Conclusion

**Backend needs fix:** YES
**Primary fix location:** `gpt_analyze.py` lines 7041-7047
**Alternative:** Fix all prompts to use "1", "2–10", "11–100" values

The current backend assumes old-style values that no longer come from the frontend, causing 100% personalization failure.
