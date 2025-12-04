# Sprint F - CI/CD Stabilization & Auto-QA Report

**Version:** PLATIN++ V5
**Sprint:** F - CI/CD Stabilization & Auto-QA
**Date:** 2025-12-04
**Status:** COMPLETED

---

## Executive Summary

Sprint F delivers comprehensive CI/CD stabilization and automated quality assurance infrastructure for the PLATIN++ V5 KI-Report system. All requested features have been implemented:

| Component | Status | Description |
|-----------|--------|-------------|
| Prompt Linter | COMPLETE | Full PLATIN++ V5 validation |
| Auto QA Script | COMPLETE | 8-profile regression testing |
| Monitoring Extensions | COMPLETE | Sprint F metrics added |
| Auto-Healing Extensions | COMPLETE | Token overflow, degradation, persona filter |
| CI/CD Workflow | COMPLETE | GitHub Actions updated |

---

## 1. CI/CD Checks Implemented

### 1.1 PDF Size Assertions

| Threshold | Action | Implementation |
|-----------|--------|----------------|
| > 10 MB | Warning | `pdf_size_warning` counter |
| > 18 MB | CI Error | `pdf_size_critical` counter |
| > 20 MB | Block | `pdf_size_blocked` counter |

**Location:** `services/monitoring.py:record_pdf_generation()`

### 1.2 HTML Payload Assertions

| Threshold | Action | Implementation |
|-----------|--------|----------------|
| > 300 KB | Warning | `html_payload_warning` counter |
| > 350 KB | CI Error | `html_payload_error` counter |

**Location:** `services/monitoring.py:record_html_payload()`

### 1.3 Prompt Linter (`scripts/prompt_linter.py`)

Validates all prompt files against PLATIN++ V5 standards:

| Check | Description | Severity |
|-------|-------------|----------|
| PLATIN++ Headers | Required metadata comments | ERROR |
| SIZE-AWARE | Token multiplier compliance | ERROR |
| ANTI-REDUNDANCY | No content overlap | WARNING |
| Persona Terms | Forbidden term detection | ERROR |
| Global Forbidden | VERBOTEN, REINFORCEMENT, etc. | ERROR |
| Format Compliance | HTML output, variables | WARNING |

**Exit Codes:**
- `0` - All checks pass
- `1` - Errors found
- `2` - Warnings only (pass with `--fail-on-warning`)

---

## 2. Auto QA Regression Script (`scripts/auto_qa.py`)

### 2.1 Test Profiles Validated

| Profile ID | Persona | Lang | Funding Route | Guardrails |
|------------|---------|------|---------------|------------|
| solo_de_base | solo | de | DE | false |
| team_de_base | team | de | DE | false |
| kmu_de_base | kmu | de | DE | false |
| solo_en_base | solo | en | EN-DE | false |
| solo_de_guardrails | solo | de | DE | true |
| kmu_de_full | kmu | de | DE | false |
| kmu_france_eu_core_en | kmu | en | EN-EU-Core | false |
| kmu_france_eu_core_en_gold | kmu | en | EN-EU-Core | false |

### 2.2 Validation Checks

| Check Category | Validations |
|----------------|-------------|
| Profile Structure | Required fields, JSON validity |
| Guardrails Detection | v5 Confidence Engine compliance |
| Funding Routing | DE/EN-DE/EN-EU-Core routing |
| Persona Compliance | Term validation per size |
| PDF Size | Threshold validation |
| Fallback Count | Max 2 warning, max 3 critical |
| Section Words | Minimum 50 words guarantee |

---

## 3. Monitoring Extensions

### 3.1 New Metrics Added

```python
# PDF Metrics
pdf.size_mb              # Histogram
pdf.size_blocked         # Counter (> 20MB)

# HTML Payload Metrics
html_payload_kb          # Timed metric
html_payload_warning     # Counter (> 300KB)
html_payload_error       # Counter (> 350KB)

# Prompt Engine Metrics
prompt_fallbacks_total   # Counter
prompt_section_failures_total  # Counter
prompt_size_mismatch_total     # Counter

# Persona Metrics
persona_violation_total  # Counter
persona_violation_{type} # By violation type

# Guardrails Metrics
guardrail_high_confidence_hits  # Counter

# Funding Metrics
funding_route_mismatch_total    # Counter
```

### 3.2 Recording Functions

| Function | Purpose |
|----------|---------|
| `record_persona_violation()` | Track persona term violations |
| `record_funding_route_mismatch()` | Track routing mismatches |
| `record_prompt_size_mismatch()` | Track SIZE-AWARE violations |
| `record_html_payload()` | Track HTML size metrics |
| `record_guardrail_high_confidence_hit()` | Track high-confidence guardrail hits |

---

## 4. Auto-Healing Extensions

### 4.1 Token-Overflow Auto-Fix

**Location:** `services/auto_healing.py:auto_fix_token_overflow()`

Progressive shortening strategy:
1. Remove examples (z.B., e.g., etc.)
2. Truncate long bullet points (> 120 chars)
3. Remove redundant paragraphs

```python
SIZE_TOKEN_MULTIPLIERS = {
    "solo": 0.8,
    "team": 1.0,
    "kmu": 1.15,
}
```

### 4.2 Fallback-Degradation Mode

**Location:** `services/auto_healing.py:FallbackDegradationManager`

| Level | Description | Token Multiplier |
|-------|-------------|------------------|
| 0 | Full quality | 1.0x |
| 1 | Reduced examples | 0.85x |
| 2 | Minimal content | 0.7x |
| 3 | Emergency fallback | 0.5x |

### 4.3 Persona-Rewrite Filter

**Location:** `services/auto_healing.py:apply_persona_rewrite_filter()`

Automatic detection and replacement of forbidden persona terms:

| Persona | Forbidden Terms (Sample) |
|---------|-------------------------|
| solo | Abteilungen, Team-Meeting, Governance-Board |
| team | Sie allein, Ein-Personen-Betrieb, Enterprise-Architektur |
| kmu | Sie allein, Solo-Unternehmer, ohne Team |

---

## 5. CI/CD Workflow Updates

### 5.1 GitHub Actions Jobs

| Job | Purpose | Dependencies |
|-----|---------|--------------|
| `prompt-linter` | PLATIN++ V5 prompt validation | - |
| `auto-qa` | Regression test profiles | prompt-linter |
| `platin-quality` | Core test suite | prompt-linter, auto-qa |
| `html-payload-check` | HTML size validation | - |
| `prompt-validation` | Prompt file structure | - |
| `test-profile-validation` | JSON profile validation | - |
| `quality-summary` | Aggregate results | all jobs |

### 5.2 Trigger Configuration

```yaml
on:
  push:
    branches: [ main, develop, 'feature/**' ]
  pull_request:
    branches: [ main ]
```

---

## 6. Files Modified/Created

### 6.1 New Files

| File | Purpose |
|------|---------|
| `scripts/prompt_linter.py` | PLATIN++ V5 prompt validation |
| `scripts/auto_qa.py` | Automated regression testing |
| `data/test_profiles_gold/kmu_france_eu_core_en_gold.json` | Gold standard profile |

### 6.2 Modified Files

| File | Changes |
|------|---------|
| `services/monitoring.py` | Sprint F metrics extensions |
| `services/auto_healing.py` | Token overflow, degradation, persona filter |
| `.github/workflows/platin_quality.yml` | Full CI/CD workflow update |

---

## 7. Quality Gate Summary

### 7.1 Pre-Sprint Status

- CI/CD: Basic pytest only
- Monitoring: Core metrics only
- Auto-healing: Basic section recovery

### 7.2 Post-Sprint Status

| Area | Coverage |
|------|----------|
| Prompt Validation | 100% (all prompt files) |
| Profile Regression | 8 profiles validated |
| Monitoring Metrics | 15+ new Sprint F metrics |
| Auto-Healing | 3 new recovery mechanisms |
| CI/CD Jobs | 7 parallel quality checks |

---

## 8. Recommendations for Sprint G

1. **Template & Visual Polish**
   - PDF template refinements
   - CSS optimization for HTML output

2. **Performance Optimization**
   - Cache prompt linter results
   - Parallel profile validation

3. **Extended Monitoring**
   - Grafana dashboard templates
   - Alert rule definitions

---

## Appendix: Metric Reference

### Counter Metrics
```
pdf_size_warning
pdf_size_critical
pdf_size_blocked
html_payload_warning
html_payload_error
prompt_fallbacks_total
prompt_section_failures_total
prompt_size_mismatch_total
persona_violation_total
guardrail_high_confidence_hits
funding_route_mismatch_total
auto_heal_token_overflow_fixed
```

### Timed Metrics (Histogram)
```
pdf_size_mb
html_payload_kb
prompt_size_variance_pct
guardrail_confidence
```

### Gauge Metrics
```
pdf_last_size_mb
html_last_payload_kb
```

---

**Report Generated:** 2025-12-04
**Sprint F Status:** COMPLETE
**Next Sprint:** G - Template & Visual Polish
