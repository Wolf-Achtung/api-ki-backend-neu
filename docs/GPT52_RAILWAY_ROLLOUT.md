# GPT-5.2 Railway Rollout Playbook

## Overview

This document describes the minimal-risk rollout procedure for the GPT-5.2 model routing feature.

**Architecture**: Task-based routing (FAST/REASONING/DEFAULT) optimizes model usage per section type.

---

## Phase 0/1: Scaffolding (Zero-Change)

The routing infrastructure is deployed but inactive. No ENV changes needed.

### Safe Defaults

If `OPENAI_MODEL_FAST` and `OPENAI_MODEL_REASONING` are **not set**, the system uses `OPENAI_MODEL` (existing behavior preserved).

| ENV Variable | Default Value | Notes |
|--------------|---------------|-------|
| `OPENAI_MODEL_FAST` | `OPENAI_MODEL` | Falls back to primary model |
| `OPENAI_MODEL_REASONING` | `OPENAI_MODEL` | Falls back to primary model |
| `OPENAI_MODEL_FALLBACK` | `gpt-4o-mini` | Stable fallback (unchanged) |
| `OPENAI_REASONING_EFFORT` | `high` | Reasoning intensity |

### Deploy Without Activation

```bash
# 1. Merge to main
git merge claude/fetch-golden-artifacts-E2eVs

# 2. Railway deploy (automatic or manual)
# No ENV changes → Zero-Change confirmed

# 3. Verify logs in Railway
# Search for: "[GPT5.2] Model Routing enabled"
```

---

## Phase 2: Enable GPT-5.2

Activate GPT-5.2 models via Railway ENV overrides.

### Railway Variables

Set these in Railway → Service → Variables:

```bash
# Quick tasks (HTML snippets, badges, KPI formatting)
OPENAI_MODEL_FAST=gpt-5.2-chat-latest

# Complex analysis (Consistency, Governance, Auto-Heal)
OPENAI_MODEL_REASONING=gpt-5.2

# Stable fallback (keep stable, NOT 5.2)
OPENAI_MODEL_FALLBACK=gpt-4.1-mini

# Reasoning intensity (low|medium|high, use xhigh selectively)
OPENAI_REASONING_EFFORT=high
```

### Activation Steps

1. **Railway → Variables**: Add/update the ENV variables above
2. **Redeploy**: Trigger a redeploy in Railway
3. **Verify logs**: Search Railway logs for `[GPT5.2] Model Routing enabled`

---

## Verification

Run the Golden Reports validation to confirm quality:

```bash
python scripts/generate_golden_reports.py \
  --base-url <railway-url> \
  --all \
  --use-manifest
```

### Summary Gate Must Pass

The Summary Gate validates quality automatically. Required metrics:

| Metric | Required Value |
|--------|----------------|
| `errors` | `0` |
| `sections_missing` | `0` |
| `badges_missing` | `[]` |
| `json_valid` | `true` |

---

## Rollback

If issues occur, revert to previous model configuration:

### Quick Rollback

1. **Railway → Variables**: Remove or reset these variables:
   - `OPENAI_MODEL_FAST` → remove or set to `gpt-4o`
   - `OPENAI_MODEL_REASONING` → remove or set to `gpt-4o`
2. **Redeploy**: Trigger a redeploy
3. **Verify**: Confirm logs show previous model configuration

### Full Rollback (Code)

If code rollback needed:

```bash
git revert <commit-hash>
git push origin main
# Railway auto-deploys
```

---

## Section Routing Reference

| Tier | Sections | Model ENV |
|------|----------|-----------|
| **REASONING** | consistency_check, auto_heal, governance_narrative, compliance_analysis, ai_act_assessment, executive_summary, risk_analysis, strategic_recommendations | `OPENAI_MODEL_REASONING` |
| **FAST** | html_snippet, badge_generation, kpi_format, table_render, label_generation, status_badge | `OPENAI_MODEL_FAST` |
| **DEFAULT** | All others | `OPENAI_MODEL` |

---

## Troubleshooting

### No Model Routing Logs

If `[GPT5.2] Model Routing enabled` is not visible in Railway logs:
- Check if ENV variables are correctly set (case-sensitive)
- Verify the service redeployed after ENV changes
- Check for startup errors in logs

### Quality Degradation

If Summary Gate fails after enabling GPT-5.2:
1. Check which sections are failing
2. Consider adjusting `OPENAI_REASONING_EFFORT` (try `medium`)
3. Rollback if persistent issues

---

**Version**: 1.0.0
**Last Updated**: 2024-12 (GPT-5.2 Scaffolding Release)
