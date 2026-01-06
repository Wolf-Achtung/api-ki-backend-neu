# 🔄 PROMPT-SYNC-MAP: v5 → v6 Delta

**Analyse-Datum:** 2026-01-06
**Projekt:** api-ki-backend-neu
**Source:** prompts/de/ (v6.x/v7.x - PLATIN+++)
**Target:** prompts/en/ (v5.x - PLATIN++ → needs v6.x update)

---

## 📊 SUMMARY

| Kategorie | Anzahl | Priorität |
|-----------|--------|-----------|
| Identical (skip) | 0 | P3 |
| Minor Changes (<80% similar) | 0 | P2 |
| Moderate Changes (50-80% similar) | 11 | P1 |
| Major Changes (<50% similar) | 35 | P0 |
| Missing EN | 0 | P0 |
| EN-only (aliases) | 10 | P2 |
| DE Internal Files | 2 | - |
| **TOTAL** | **56** | - |

**Geschätzte Sync-Zeit:**
- P0 Only: 8-12 Stunden
- P0 + P1: 12-16 Stunden
- Full Sync: 16-20 Stunden

---

## 🔑 KEY FINDINGS

### Version Gap

| Metric | DE (v6.x) | EN (v5.x) |
|--------|-----------|-----------|
| PLATIN+++ | 7 | 5 |
| PLATIN++ | 22 | 27 |
| Latest versions | v7.0, v7.1, v8.0 | v5.2, v5.4 |
| Size-aware prompts | 30 | 37 |
| Token budgets (avg) | 1573 | 1605 |

### New Features in DE v6 (not in EN v5)

1. **5 Goldnuggets System** - Hyper-personalization using 5 key business inputs
2. **DOD (Definition of Done)** - Formal quality criteria for each prompt
3. **PLATIN+++ Level** - Enhanced premium content structure
4. **New Variables:**
   - `{{HAUPTUMSATZTREIBER}}` (10x) - Main revenue driver
   - `{{STRATEGISCHE_ZIELE}}` (3x) - Strategic goals
   - `{{FOERDERPROGRAMME_HTML}}` (3x) - Funding programs HTML
   - `{{WETTBEWERB}}` (2x) - Competition

### Variables Renamed (EN v5 → DE v6)

| EN v5 Variable | DE v6 Equivalent |
|----------------|------------------|
| `{{ai_application}}` | `{{ki_anwendung}}` (or removed) |
| `{{automated_decisions}}` | `{{automatisierte_entscheidungen}}` |
| `{{data_types}}` | `{{datentypen}}` |

---

## 🔴 P0: CRITICAL PROMPTS (35 prompts - Sofort synchronisieren)

### Top 15 Most Different (sorted by similarity)

| # | Prompt | Similarity | DE Lines | EN Lines | Δ Lines |
|---|--------|------------|----------|----------|---------|
| 1 | **gamechanger.md** | 3.1% | 510 | 101 | +409 |
| 2 | **executive_summary.md** | 3.6% | 310 | 70 | +240 |
| 3 | **technologie_prozesse.md** | 5.1% | 95 | 75 | +20 |
| 4 | **roadmap_90d.md** | 6.0% | 648 | 278 | +370 |
| 5 | **foerderprogramme.md** | 6.3% | 68 | 106 | -38 |
| 6 | **quick_wins.md** | 7.7% | 221 | 272 | -51 |
| 7 | **recommendations.md** | 12.6% | 264 | 120 | +144 |
| 8 | **transparency_box.md** | 14.6% | 80 | 61 | +19 |
| 9 | **risks.md** | 15.8% | 262 | 259 | +3 |
| 10 | **foerderpotenzial.md** | 18.6% | 169 | 127 | +42 |
| 11 | **strategie_governance.md** | 24.6% | 194 | 143 | +51 |
| 12 | **tools_empfehlungen.md** | 26.0% | 317 | 232 | +85 |
| 13 | **ai_act_summary.md** | 27.1% | 240 | 212 | +28 |
| 14 | **top_3_massnahmen.md** | 27.4% | 51 | 45 | +6 |
| 15 | **next_actions.md** | 29.0% | 180 | 120 | +60 |

### Remaining P0 Prompts (16-35)

| Prompt | Similarity | Impact |
|--------|------------|--------|
| wettbewerb_benchmark.md | 29.5% | Competition analysis |
| roadmap_90d_decision.md | 30.9% | Roadmap decisions |
| ai_policy_mini.md | 31.0% | AI policy |
| business_case.md | 31.9% | Business case |
| data_readiness.md | 32.5% | Data readiness |
| gamechanger_decision.md | 34.9% | Gamechanger decisions |
| org_change.md | 37.9% | Org change |
| ki_aktivitaeten_ziele.md | 39.6% | AI activities |
| costs_overview.md | 40.4% | Costs |
| executive_decision.md | 40.1% | Executive decisions |
| templates_start.md | 40.7% | Templates |
| ki_skillplan.md | 41.5% | Skills |
| kickoff_vorlage.md | 43.1% | Kickoff |
| risk_engine_v2.md | 44.9% | Risk engine v2 |
| roadmap_12m.md | 44.9% | 12-month roadmap |
| roi_tracking.md | 47.0% | ROI tracking |
| monetarisierung.md | 47.1% | Monetization |
| branch_deep_dive.md | 47.2% | Branch deep dive |

---

## 🟡 P1: IMPORTANT PROMPTS (11 prompts - Kurzfristig synchronisieren)

| Prompt | Similarity | Reason |
|--------|------------|--------|
| benchmark_engine.md | 50.4% | Engine - core functionality |
| recommendations_engine.md | 50.7% | Engine - core functionality |
| automation_roadmap_engine.md | 54.2% | Engine - core functionality |
| ki_stack_summary.md | 55.6% | KI Stack summary |
| exec_snapshot.md | 56.9% | Executive snapshot |
| funding_engine_v2.md | 57.1% | Funding engine |
| prompt_framework.md | 57.3% | Prompt framework |
| risk_engine_v3.md | 60.1% | Risk engine v3 |
| business_case_engine_v2.md | 62.8% | Business case engine |
| vendor_audit_engine.md | 63.4% | Vendor audit |
| business_case_simulation.md | 67.0% | Business case sim |

---

## 🟢 P2: EN-ONLY PROMPTS (10 prompts - Aliases/Translations)

These are **translation aliases** for German-named prompts:

| EN Prompt | DE Equivalent | Action |
|-----------|---------------|--------|
| strategy_governance.md | strategie_governance.md | Sync with DE |
| competition_benchmark.md | wettbewerb_benchmark.md | Sync with DE |
| ai_activities_goals.md | ki_aktivitaeten_ziele.md | Sync with DE |
| technology_processes.md | technologie_prozesse.md | Sync with DE |
| monetization.md | monetarisierung.md | Sync with DE |
| kickoff_template.md | kickoff_vorlage.md | Sync with DE |
| tools_recommendations.md | tools_empfehlungen.md | Sync with DE |
| funding.md | foerderprogramme.md | Sync with DE |
| funding_potential.md | foerderpotenzial.md | Sync with DE |
| funding_eu_core.md | (unique) | Keep as EN-specific |

---

## 📁 DE INTERNAL FILES (2 files)

| File | Purpose |
|------|---------|
| _hauptleistung_context.md | Context injection for hauptleistung |
| _solo_language_rules.md | Language rules for solo users |

**Action:** Consider adding EN versions if they contain language-specific content.

---

## 🔍 DETAILED ANALYSIS: TOP 5 CRITICAL PROMPTS

### 1. gamechanger.md (3.1% similar)

**DE Version (v7.1 PLATIN+++):**
- 510 lines (vs EN 101 lines)
- Has formal DOD (Definition of Done)
- Uses "5 Goldnuggets" for personalization
- Includes transformation report with safety/governance guardrails
- Explicit "Nicht mehr X, sondern Y" formula

**EN Version (v7.0):**
- Basic structure only
- Missing DOD and Goldnuggets
- Simpler transformation idea format

**Sync Priority:** 🔴 CRITICAL
**Estimated Effort:** 2-3 hours

---

### 2. executive_summary.md (3.6% similar)

**DE Version:**
- 310 lines (vs EN 70 lines)
- Comprehensive executive summary structure
- Multi-section layout

**EN Version:**
- Basic 70-line summary
- Missing most sections

**Sync Priority:** 🔴 CRITICAL
**Estimated Effort:** 2-3 hours

---

### 3. roadmap_90d.md (6.0% similar)

**DE Version (v7.0 PLATIN+++):**
- 648 lines (vs EN 278 lines)
- Phase 3 Hyper-Personalization
- Uses all 5 Goldnuggets
- Size-aware token budgets: solo=2240, team=2800, sme=3220

**EN Version:**
- Basic 278-line roadmap
- Missing personalization features

**Sync Priority:** 🔴 CRITICAL
**Estimated Effort:** 3-4 hours

---

### 4. recommendations.md (12.6% similar)

**DE Version:**
- 264 lines (vs EN 120 lines)
- Enhanced recommendation structure

**EN Version:**
- Basic 120-line recommendations

**Sync Priority:** 🔴 CRITICAL
**Estimated Effort:** 1-2 hours

---

### 5. risks.md (15.8% similar)

**DE Version:**
- 262 lines
- ~223 deletions, ~226 additions (almost complete rewrite)

**EN Version:**
- 259 lines (similar length but different content)

**Sync Priority:** 🔴 CRITICAL
**Estimated Effort:** 2-3 hours

---

## 📊 COMMON PATTERNS: v5 → v6 Changes

### Additions in v6 (apply to EN)

1. **PLATIN+++ Header Structure:**
```
<!-- PLATIN+++ PROMPT v7.1 - SPRINT INHALTLICHE FINALISIERUNG -->
<!-- SECTION: [section_name] -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/sme -->
<!-- TOKEN-BUDGET: [budget] -->
```

2. **DOD (Definition of Done) Sections:**
```
=============================================================================
PLATIN+++ CONTENT DOD (verbindlich):
=============================================================================
- [Quality criterion 1]
- [Quality criterion 2]
- ...
```

3. **5 Goldnuggets Reference:**
```
<!-- PHASE 3: Maximum personalization using ALL 5 Goldnuggets -->
<!-- INPUT: {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}}, {{ki_projekte}},
           {{KI_GUARDRAILS}}, {{VISION_3_JAHRE}} -->
```

4. **Size-Aware Token Budgets:**
```
<!-- TOKEN-BUDGET: 2800 (solo:0.8x=2240, team:1.0x=2800, sme:1.15x=3220) -->
```

### Removals in v6 (remove from EN)

1. Old v5.x header formats
2. Deprecated variable names (`{{ai_application}}`, etc.)

---

## 🎯 SYNCHRONIZATION STRATEGY

### Option A: P0 Only (Quick Win)
**Scope:** 35 critical prompts
**Time:** 8-12 hours
**Impact:** 80% quality improvement
**Recommended for:** Immediate deployment needs

### Option B: P0 + P1 (Comprehensive)
**Scope:** 46 prompts (35 P0 + 11 P1)
**Time:** 12-16 hours
**Impact:** 95% quality improvement
**Recommended for:** Quality-focused deployment

### Option C: Full Sync (Complete)
**Scope:** All 56 prompts + EN aliases
**Time:** 16-20 hours
**Impact:** 100% parity
**Recommended for:** Long-term maintenance

---

## 📋 IMPLEMENTATION PLAN

### Phase 6.3a: P0 Critical (8-12h)

**Method:** Manual translation with careful review
**Focus:** Preserve DE v6 structure, translate to EN

**Priority Order:**
1. gamechanger.md (most different, core feature)
2. executive_summary.md (user-facing, critical)
3. roadmap_90d.md (core deliverable)
4. recommendations.md (core deliverable)
5. risks.md (compliance critical)
6. ... (remaining P0 by similarity)

### Phase 6.3b: P1 Important (4-6h)

**Method:** Semi-automated with review
**Focus:** Engine prompts that affect output quality

### Phase 6.3c: P2 EN-Aliases (2-3h)

**Method:** Copy from synced DE prompts
**Focus:** Maintain alias functionality

---

## 📋 IMPLEMENTATION CHECKLIST

### Pre-Implementation:
- [ ] Review this Sync-Map with Wolf
- [ ] Decide: Option A, B, or C
- [ ] Backup prompts/en/ directory
- [ ] Set up test environment for EN reports

### Phase 6.3a (P0):
- [ ] gamechanger.md
- [ ] executive_summary.md
- [ ] roadmap_90d.md
- [ ] recommendations.md
- [ ] risks.md
- [ ] (continue with remaining 30 P0 prompts)
- [ ] Test EN report generation

### Phase 6.3b (P1):
- [ ] All 11 engine prompts
- [ ] Test EN report generation

### Phase 6.3c (P2):
- [ ] Update EN aliases from synced DE prompts
- [ ] Final integration test

---

## 💡 RECOMMENDATIONS

### Short-Term (This Sprint)
1. **Do Option A (P0 Only)** - Maximum impact with reasonable effort
2. Focus on user-facing prompts first (executive_summary, gamechanger)
3. Test thoroughly after each major prompt sync

### Medium-Term (Next Sprint)
1. Complete Option B (add P1 engines)
2. Implement automated sync checking
3. Add version tracking to prompts

### Long-Term
1. Consider single-source prompts with i18n placeholders
2. Automate sync validation in CI/CD
3. Version control for prompt changes

---

## 📊 APPENDIX: Full Prompt List by Priority

### P0 Critical (35 prompts)
```
gamechanger.md (3.1%), executive_summary.md (3.6%),
technologie_prozesse.md (5.1%), roadmap_90d.md (6.0%),
foerderprogramme.md (6.3%), quick_wins.md (7.7%),
recommendations.md (12.6%), transparency_box.md (14.6%),
risks.md (15.8%), foerderpotenzial.md (18.6%),
strategie_governance.md (24.6%), tools_empfehlungen.md (26.0%),
ai_act_summary.md (27.1%), top_3_massnahmen.md (27.4%),
next_actions.md (29.0%), wettbewerb_benchmark.md (29.5%),
roadmap_90d_decision.md (30.9%), ai_policy_mini.md (31.0%),
business_case.md (31.9%), data_readiness.md (32.5%),
gamechanger_decision.md (34.9%), org_change.md (37.9%),
ki_aktivitaeten_ziele.md (39.6%), costs_overview.md (40.4%),
executive_decision.md (40.1%), templates_start.md (40.7%),
ki_skillplan.md (41.5%), kickoff_vorlage.md (43.1%),
risk_engine_v2.md (44.9%), roadmap_12m.md (44.9%),
roi_tracking.md (47.0%), monetarisierung.md (47.1%),
branch_deep_dive.md (47.2%)
```

### P1 Important (11 prompts)
```
benchmark_engine.md (50.4%), recommendations_engine.md (50.7%),
automation_roadmap_engine.md (54.2%), ki_stack_summary.md (55.6%),
exec_snapshot.md (56.9%), funding_engine_v2.md (57.1%),
prompt_framework.md (57.3%), risk_engine_v3.md (60.1%),
business_case_engine_v2.md (62.8%), vendor_audit_engine.md (63.4%),
business_case_simulation.md (67.0%)
```

### P2 EN-Only Aliases (10 prompts)
```
strategy_governance.md, competition_benchmark.md,
ai_activities_goals.md, technology_processes.md,
monetization.md, kickoff_template.md,
tools_recommendations.md, funding.md,
funding_potential.md, funding_eu_core.md
```

---

**Sync-Map Version:** 1.0
**Created:** 2026-01-06
**Analyzed by:** Claude Code (Opus 4.5)
**Next:** Phase 6.3 Implementation based on selected option (A/B/C)
