# 💡 OPTIMIZATION SUGGESTIONS: EN Prompts v6.x/v7.x

**Based on:** PROMPT-QA-REPORT.md
**Priority:** Ranked by impact
**Created:** 2026-01-07

---

## 🔴 PRIORITY 1: CRITICAL FIXES (Do First) - ~8 hours

### Fix 1: Resolve quick_wins.md Output Format Incompatibility

**Problem:** EN expects JSON output, DE expects Markdown/HTML

**Impact:** System will generate malformed data if EN prompts used with DE templates

**Files Affected:**
- `prompts/en/quick_wins.md`
- `prompts/de/quick_wins.md`

**Fix Option A - Align EN to DE (Recommended):**

```markdown
# In prompts/en/quick_wins.md

# CHANGE FROM:
<!-- OUTPUT: JSON ONLY -->

# TO:
<!-- OUTPUT: HTML ONLY -->

# AND remove JSON structure requirements, replace with:
## Output Structure
<ul class="quick-wins">
  <li>
    <strong>[Quick Win Title]</strong>
    <p>[Description]</p>
    <span class="time">[Time Investment]</span>
    <span class="savings">[Expected Savings]</span>
  </li>
</ul>
```

**Fix Option B - Align DE to EN:**
Update DE to match EN's JSON structure (requires backend changes)

**Validation:**
```bash
# Test that output format matches template expectations
# Generate sample output and verify structure
```

**Time Estimate:** 1-2 hours

---

### Fix 2: Align recommendations.md Structure (v7.1 vs v5.4)

**Problem:** Incompatible structures between EN (v7.1) and DE (v5.4)

**Files Affected:**
- `prompts/en/recommendations.md` (v7.1 - 6 fields per recommendation)
- `prompts/de/recommendations.md` (v5.4 - 3 Must-Do + Options)

**Fix Instructions:**

**Option A - Update DE to v7.1 (Recommended):**

```markdown
# Add to prompts/de/recommendations.md

=============================================================================
PLATIN+++ PROMPT v7.1 - RECOMMENDATION STRUCTURE
=============================================================================

Jede Empfehlung MUSS folgende 6 Elemente enthalten:

1. WAS: Konkrete Maßnahme (1 Satz)
2. WARUM: Strategischer Nutzen (1 Satz)
3. WIE: Umsetzungsschritte (2-3 Bullets)
4. WANN: Zeitrahmen (1 Wert)
5. RISIKO: Potenzielle Hürden (1 Satz)
6. ERFOLGSMETRIK: Messbarer Erfolg (1 KPI)

[Copy full structure from EN version]
```

**Option B - Downgrade EN to v5.4:**
Simplify EN structure to match DE's 3 Must-Do + Options format

**Critical:** Whichever option chosen, ensure backend expects correct format

**Time Estimate:** 2-3 hours

---

### Fix 3: Add PERSONA HARD-GUARDS to EN Prompts

**Problem:** EN lacks size-specific language enforcement rules

**Files Affected:**
- `prompts/en/recommendations.md`
- `prompts/en/executive_summary.md`
- `prompts/en/gamechanger.md`
- `prompts/en/roadmap_90d.md`
- `prompts/en/org_change.md`

**Template to Add (copy from DE, translate):**

```markdown
=============================================================================
PERSONA HARD-GUARDS (STRICT!)
=============================================================================
{% if COMPANY_SIZE == "solo" %}
SOLO MODE - FORBIDDEN TERMS:
- "Team/Teams/Department/Employees" → do not use
- "Division" → use "work field" instead
- "HR" → do not use
- "Rollout" → use "introduction" or "setup"
- "Stakeholder" → do not use
- Budget reality: Max €5,000 one-time, €200/month ongoing

SOLO MODE - REQUIRED LANGUAGE:
- Focus on personal effort and individual workflow
- Use "you" appropriately (where allowed)
- Emphasize practical, immediate applicability
{% elif COMPANY_SIZE == "team" %}
TEAM MODE - FORBIDDEN TERMS:
- "Division/Unit/Corporation" → do not use
- "Department" → use "area" instead
- Solo terms: "individual", "alone"
- Corporate language: "enterprise-wide", "organization"

TEAM MODE - REQUIRED LANGUAGE:
- Focus on coordination and shared standards
- Emphasize collaboration and team workflows
{% else %}
SME MODE - FORBIDDEN TERMS:
- "Corporation/Division/Unit" → do not use
- Solo terms: "individual", "alone"
- Enterprise terms: "global rollout", "enterprise transformation"

SME MODE - REQUIRED LANGUAGE:
- Focus on organizational positioning
- Include governance and compliance aspects
- Reference stakeholder management appropriately
{% endif %}
=============================================================================
```

**Time Estimate:** 2 hours (add to 5 files)

---

### Fix 4: Fix Variable Case Sensitivity in quick_wins.md

**Problem:** Uses lowercase variable names instead of standard uppercase

**File Affected:**
- `prompts/en/quick_wins.md`

**Fix - Search & Replace:**

```bash
# In prompts/en/quick_wins.md:

# Change:
{{ki_guardrails}} → {{KI_GUARDRAILS}}
{{vision_3_jahre}} → {{VISION_3_JAHRE}}

# Verify INPUT header also uses uppercase:
<!-- INPUT NEW: {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}}, {{ki_projekte}}, {{KI_GUARDRAILS}}, {{VISION_3_JAHRE}} -->
```

**Validation:**
```bash
grep -i "ki_guardrails\|vision_3_jahre" prompts/en/quick_wins.md
# Should only find UPPERCASE versions
```

**Time Estimate:** 15 minutes

---

### Fix 5: Add Missing Goldnuggets to executive_summary.md

**Problem:** Missing {{ki_projekte}} and {{VISION_3_JAHRE}}

**File Affected:**
- `prompts/en/executive_summary.md`

**Fix Instructions:**

```markdown
# Step 1: Update INPUT header (around line 7-8)

# FROM:
<!-- INPUT NEW: {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}}, {{STRATEGISCHE_ZIELE}}, {{KI_GUARDRAILS}} -->

# TO:
<!-- INPUT NEW: {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}}, {{STRATEGISCHE_ZIELE}}, {{KI_GUARDRAILS}}, {{ki_projekte}}, {{VISION_3_JAHRE}} -->

# Step 2: Add Phase 3 comment block after INPUT
<!-- PHASE 3: Maximum personalization using ALL 5 Goldnuggets -->
<!-- INPUT PRIORITY:
     1. {{hauptleistung}} - Core business context
     2. {{ZEITERSPARNIS_PRIORITAET}} - Time savings focus
     3. {{KI_GUARDRAILS}} - Safety boundaries
     4. {{ki_projekte}} - Current AI initiatives
     5. {{VISION_3_JAHRE}} - Strategic alignment
-->

# Step 3: Reference in Element 4 (Individual Takeaway)
<!-- If {{VISION_3_JAHRE}} available: align takeaway with 3-year vision -->
<!-- If {{ki_projekte}} available: reference ongoing projects -->
```

**Time Estimate:** 30 minutes

---

### Fix 6: Implement Jinja2 Conditionals in 4 SIZE-AWARE Files

**Problem:** SIZE-AWARE tag present but no actual implementation

**Files Affected:**
- `prompts/en/data_readiness.md`
- `prompts/en/quick_wins.md`
- `prompts/en/transparency_box.md`
- `prompts/en/roadmap_90d_decision.md`

**Template for data_readiness.md:**

```markdown
{% if COMPANY_SIZE == "solo" %}
## Data Readiness for Solo Operations
Focus on personal data management and simple tool integration.
Word count: 110-130 words
- Emphasize practical, low-overhead solutions
- No complex data governance requirements
{% elif COMPANY_SIZE == "team" %}
## Data Readiness for Team Collaboration
Focus on shared data access and team coordination.
Word count: 130-150 words
- Include data sharing protocols
- Address team-level permissions
{% else %}
## Data Readiness for SME Operations
Focus on organizational data governance and compliance.
Word count: 150-180 words
- Include compliance requirements (GDPR, AI Act)
- Address department-level data management
- Reference IT integration needs
{% endif %}
```

**Alternative Option:** Remove SIZE-AWARE tag if size differentiation not needed

**Time Estimate:** 2 hours (implement for all 4 files)

---

## 🟡 PRIORITY 2: IMPORTANT IMPROVEMENTS (Should Do Soon) - ~5 hours

### Improvement 1: Standardize KMU → SME Terminology

**Problem:** 15 files mix "KMU" (German) and "SME" (English)

**Files to Fix:**
- strategy_governance.md
- strategie_governance.md
- funding.md
- foerderprogramme.md
- technology_processes.md
- technologie_prozesse.md
- tools_recommendations.md
- tools_empfehlungen.md
- risk_engine_v2.md
- org_change.md
- costs_overview.md
- funding_potential.md
- business_case.md
- ai_policy_mini.md
- roadmap_12m.md

**Fix Script:**

```bash
#!/bin/bash
# Run from repository root

cd prompts/en

# Replace KMU with SME (case-sensitive)
for file in *.md; do
  sed -i 's/KMU/SME/g' "$file"
  sed -i 's/kmu/sme/g' "$file"
done

# Verify changes
grep -r "KMU\|kmu" *.md
# Should return 0 results (except inside German variable names like {{KI_GUARDRAILS}})
```

**Manual Verification Required:**
- Ensure SIZE-AWARE tags updated: `<!-- SIZE-AWARE: solo/team/sme -->`
- Ensure TOKEN-BUDGET uses `sme:` not `kmu:`

**Time Estimate:** 30 minutes

---

### Improvement 2: Restore Missing Content Sections

**Problem:** EN versions missing 40-57% of DE content

**Key Sections to Restore:**

**A) gamechanger.md - Add Phase 3 Individualization:**

```markdown
<!--
=============================================================================
PHASE 3: INDIVIDUALIZATION OF THE STRATEGIC BREAKPOINT (MANDATORY!)
=============================================================================

The Gamechanger MUST incorporate the user's briefing data.
Generic breakpoints are FORBIDDEN.

CORE CONTEXT (MANDATORY!):
The main service "{{hauptleistung}}" is the CENTRAL reference point.
Every sentence must relate to this main service!

INDIVIDUALIZATION CONTEXT (available from briefing):
- {{hauptleistung}} = What the user specifically offers (PRIMARY!)
- {{ZEITERSPARNIS_PRIORITAET}} = Where the user loses most time
- {{KI_GUARDRAILS}} = Restrictions/no-gos for AI usage
- {{VISION_3_JAHRE}} = User's 3-year vision

STRATEGIC BREAKPOINT – WRITE CONCRETELY:

EXAMPLE for briefing 369 (AI consultant with questionnaire creation):
- hauptleistung: "Questionnaire creation and GPT-supported evaluation"
- zeitersparnis_prioritaet: "Implementation/programming"
- vision_3_jahre: "Scalable AI consulting with automated analysis pipelines"

EXPECTED BREAKPOINT for briefing 369:
❌ FORBIDDEN: "Processes are inefficient and don't scale"
✅ CORRECT: "Previously: Each AI readiness analysis is custom-programmed.
            Although 70% of questionnaire logic repeats, every project starts from zero."

❌ FORBIDDEN: "No longer reactive, but proactive"
✅ CORRECT: "No longer custom-programming each evaluation,
            but establishing a reusable analysis toolkit for {{hauptleistung}}."
=============================================================================
-->
```

**B) executive_summary.md - Add VERBOTENE PHRASEN:**

```markdown
=============================================================================
FORBIDDEN PHRASES (Zero Tolerance):
=============================================================================
- "faces the challenge" → too vague, be specific
- "scalable processes" → generic, specify what scales
- "end-to-end system" → abstract, describe concrete outcome
- "standardization of workflows" → generic, name the workflow
- Any phrase that fits EVERY user → rewrite to be specific

CORRECT EXAMPLES:
✅ "A consulting firm creating AI readiness questionnaires faces
   fragmented evaluation logic across client projects."
✅ "Primary time sink: custom programming for each analysis."
✅ "Core recommendation → From custom code to templates:
   questionnaire library, prompt standards, review checklist."
=============================================================================
```

**Time Estimate:** 2-3 hours

---

### Improvement 3: Add WORD_MINIMUM to SIZE-AWARE Files

**Problem:** Only 6/25 SIZE-AWARE files define per-size word counts

**Template to Add:**

```markdown
<!-- WORD_MINIMUM_SOLO: [X] -->
<!-- WORD_MINIMUM_TEAM: [X] -->
<!-- WORD_MINIMUM_SME: [X] -->
```

**Standard Scaling (adjust per prompt):**
- Solo: 80% of Team
- Team: Base value
- SME: 120% of Team

**Example for a 200-word base prompt:**
```markdown
<!-- WORD_MINIMUM_SOLO: 160 -->
<!-- WORD_MINIMUM_TEAM: 200 -->
<!-- WORD_MINIMUM_SME: 240 -->
```

**Files Needing Update:** 19 SIZE-AWARE files without WORD_MINIMUM

**Time Estimate:** 1 hour

---

### Improvement 4: Fix Non-Standard Token Multipliers

**Problem:** 2 files use non-standard multipliers

**Files Affected:**
- `prompts/en/quick_wins.md`
- `prompts/en/transparency_box.md`

**Fix for quick_wins.md:**

```markdown
# FROM:
<!-- TOKEN-BUDGET: 2000 (solo:0.8x=1600, team:1.0x=2000, sme:1.2x=2400) -->

# TO:
<!-- TOKEN-BUDGET: 2000 (solo:0.8x=1600, team:1.0x=2000, sme:1.15x=2300) -->
```

**Fix for transparency_box.md:**

```markdown
# FROM:
<!-- TOKEN-BUDGET: 300 (solo:0.9x=270, team:1.0x=300, kmu:1.1x=330) -->

# TO:
<!-- TOKEN-BUDGET: 300 (solo:0.8x=240, team:1.0x=300, sme:1.15x=345) -->
```

**Time Estimate:** 15 minutes

---

### Improvement 5: Add Goldnuggets to Secondary Prompts

**Problem:** business_case.md, roadmap_12m.md, org_change.md have 0/5 Goldnuggets

**Template for business_case.md:**

```markdown
<!-- Add after existing INPUT line -->
<!-- INPUT NEW: {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}}, {{KI_GUARDRAILS}} -->
<!-- PHASE 3: Personalize business case with core context -->

# Usage in template:
## Investment Context for {{hauptleistung}}

The business case focuses on the core service "{{hauptleistung}}" and
addresses time savings in "{{ZEITERSPARNIS_PRIORITAET}}" while respecting
guardrails defined in "{{KI_GUARDRAILS}}".
```

**Similar updates needed for:**
- `roadmap_12m.md` - add 4 Goldnuggets (all except ki_projekte)
- `org_change.md` - add 4 Goldnuggets

**Time Estimate:** 1.5 hours

---

## 🟢 PRIORITY 3: POLISH & ENHANCEMENT (Nice to Have) - ~7 hours

### Enhancement 1: Rename German Filenames to English

**Problem:** 8 files have German names in EN directory

**Renames Required:**

```bash
cd prompts/en

# Rename German files
mv foerderprogramme.md funding_programs.md
mv foerderpotenzial.md funding_potential.md  # if different from existing
mv strategie_governance.md strategy_governance.md  # if different from existing
mv technologie_prozesse.md technology_processes.md  # if different from existing
mv top_3_massnahmen.md top_3_measures.md
mv ki_skillplan.md ai_skillplan.md
mv ki_aktivitaeten_ziele.md ai_activities_goals.md

# Remove duplicates (keep English name)
rm wettbewerb_benchmark.md  # keep competition_benchmark.md
rm tools_empfehlungen.md  # keep tools_recommendations.md
rm monetarisierung.md  # keep monetization.md
rm kickoff_vorlage.md  # keep kickoff_template.md
```

**Note:** Update any references in other files after rename

**Time Estimate:** 1 hour

---

### Enhancement 2: Add Missing Include Statements

**Problem:** gamechanger.md missing two include statements

**File Affected:**
- `prompts/en/gamechanger.md`

**Fix:**

```markdown
# Add after DOD section (around line 82):

{% include '_hauptleistung_context.md' %}

# Add in PERSONA-ANPASSUNG section (around line 123):

{% if COMPANY_SIZE == "solo" %}
{% include '_solo_language_rules.md' %}
{% endif %}
```

**Time Estimate:** 30 minutes

---

### Enhancement 3: Fix Minor Terminology Inconsistencies

**A) Rollout Spelling (2 files):**

```bash
# In prompts/en/tools_recommendations.md and tools_empfehlungen.md:
sed -i 's/Roll-out/rollout/g' prompts/en/tools_*.md
```

**B) Use Case Hyphenation:**

```bash
# Standardize to "use case" (two words)
sed -i 's/use-case/use case/g' prompts/en/*.md
sed -i 's/Use-Case/Use Case/g' prompts/en/*.md
# Keep .usecase- in CSS classes
```

**C) Single "boundaries" instance:**

```markdown
# In prompts/en/roadmap_90d.md, line 86:
# Change "boundaries" to "guardrails"
```

**Time Estimate:** 30 minutes

---

### Enhancement 4: Document Terminology Guidelines

**Create new file:** `prompts/STYLE_GUIDE.md`

```markdown
# EN Prompts Style Guide

## Company Size Terminology
- Use "SME" (not "KMU" or "small business")
- Solo → Team → SME (scaling order)
- Size-aware tags: `<!-- SIZE-AWARE: solo/team/sme -->`

## Hyphenation Rules
- "use case" (two words, no hyphen)
- "rollout" (single word)
- "guardrails" (not "boundaries" or "limits")

## Variables
- Keep German variable names: {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}}, etc.
- Use UPPERCASE for most variables
- Exception: {{hauptleistung}}, {{ki_projekte}} are lowercase

## Token Budgets
- Standard multipliers: solo:0.8x, team:1.0x, sme:1.15x
- Always include calculations: `(solo:0.8x=XXX, team:1.0x=YYY, sme:1.15x=ZZZ)`

## Word Limits
- Paragraphs: max 50 words, 2 sentences
- Bullets: max 30 words
- Sections: max 150 words
```

**Time Estimate:** 1 hour

---

### Enhancement 5: Standardize Character Encoding

**Problem:** Some files use en-dash (–) instead of hyphen (-)

**Fix:**

```bash
# Replace en-dash with hyphen in SIZE-AWARE tags
find prompts/en -name "*.md" -exec sed -i 's/SIZE–AWARE/SIZE-AWARE/g' {} \;

# Verify
grep -r "SIZE.*AWARE" prompts/en/*.md
```

**Time Estimate:** 15 minutes

---

## 🔧 IMPLEMENTATION PLAN

### Step 1: Critical Fixes (Must Do) - Day 1, ~8h
1. [ ] Fix quick_wins.md output format
2. [ ] Align recommendations.md structure
3. [ ] Add PERSONA HARD-GUARDS to 5 files
4. [ ] Fix variable case in quick_wins.md
5. [ ] Add Goldnuggets to executive_summary.md
6. [ ] Implement Jinja2 in 4 SIZE-AWARE files

### Step 2: Important Improvements (Should Do) - Day 2, ~5h
1. [ ] KMU → SME standardization (15 files)
2. [ ] Restore missing content sections
3. [ ] Add WORD_MINIMUM definitions
4. [ ] Fix token multipliers
5. [ ] Add Goldnuggets to 3 secondary prompts

### Step 3: Polish (Nice to Have) - Day 3, ~7h
1. [ ] Rename German filenames
2. [ ] Add missing includes
3. [ ] Fix minor terminology
4. [ ] Create style guide
5. [ ] Fix character encoding

**Total Estimated Time:** 20 hours

---

## 📋 FIX CHECKLIST

Copy this for tracking:

### CRITICAL FIXES
- [ ] Fix output format: quick_wins.md
- [ ] Align structure: recommendations.md
- [ ] Add PERSONA HARD-GUARDS: recommendations.md
- [ ] Add PERSONA HARD-GUARDS: executive_summary.md
- [ ] Add PERSONA HARD-GUARDS: gamechanger.md
- [ ] Add PERSONA HARD-GUARDS: roadmap_90d.md
- [ ] Add PERSONA HARD-GUARDS: org_change.md
- [ ] Fix variables: quick_wins.md (case sensitivity)
- [ ] Add Goldnuggets: executive_summary.md (+ki_projekte, +VISION_3_JAHRE)
- [ ] Implement Jinja2: data_readiness.md
- [ ] Implement Jinja2: quick_wins.md
- [ ] Implement Jinja2: transparency_box.md
- [ ] Implement Jinja2: roadmap_90d_decision.md

### IMPORTANT IMPROVEMENTS
- [ ] Standardize terminology: KMU → SME (15 files)
- [ ] Restore content: gamechanger.md (Phase 3 section)
- [ ] Restore content: executive_summary.md (VERBOTENE PHRASEN)
- [ ] Add WORD_MINIMUM: 19 SIZE-AWARE files
- [ ] Fix multipliers: quick_wins.md
- [ ] Fix multipliers: transparency_box.md
- [ ] Add Goldnuggets: business_case.md
- [ ] Add Goldnuggets: roadmap_12m.md
- [ ] Add Goldnuggets: org_change.md

### POLISH
- [ ] Rename: foerderprogramme.md → funding_programs.md
- [ ] Rename: top_3_massnahmen.md → top_3_measures.md
- [ ] Rename: ki_skillplan.md → ai_skillplan.md
- [ ] Remove duplicates: wettbewerb_benchmark.md, tools_empfehlungen.md
- [ ] Add includes: gamechanger.md
- [ ] Fix rollout spelling: 2 files
- [ ] Fix use case hyphenation: 11 files
- [ ] Fix "boundaries": roadmap_90d.md
- [ ] Create: STYLE_GUIDE.md
- [ ] Fix encoding: SIZE-AWARE tags

### VALIDATION
- [ ] All scripts pass
- [ ] Variable grep returns 0 mismatches
- [ ] Test report generated
- [ ] Manual review complete
- [ ] Ready for production

---

## 📊 EXPECTED QUALITY IMPROVEMENT

After implementing all fixes:

| Metric | Current | Expected | Change |
|--------|---------|----------|--------|
| Overall Quality | 68/100 | 88/100 | +20 |
| Structural Integrity | 76/100 | 90/100 | +14 |
| Variable Integrity | 61/100 | 95/100 | +34 |
| Content Quality | 55/100 | 80/100 | +25 |
| Consistency | 72/100 | 95/100 | +23 |
| Goldnuggets Integration | 65/100 | 90/100 | +25 |
| Size-Aware Logic | 70/100 | 90/100 | +20 |

**Production Ready Status:** YES (after Priority 1 & 2 fixes)

---

**Suggestions Version:** 1.0
**Created:** 2026-01-07
**Implementation Time:** 20 hours (Priority 1: 8h, Priority 2: 5h, Priority 3: 7h)
**Priority Order:** P1 Critical → P2 Important → P3 Polish
