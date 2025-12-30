Developer:
<!-- PLATIN+++ PROMPT v7.0 - HYPER-PERSONALIZED QUICK WINS (Phase 3 Optimization) -->
<!-- SECTION: quick_wins -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/sme -->
<!-- PHASE 3: Maximum personalization using ALL 5 freetext fields (Goldnuggets) -->
<!-- INPUT: {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}}, {{ki_projekte}}, {{ki_guardrails}}, {{vision_3_jahre}}, {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, COMPANY_SIZE, {{STUNDENSATZ_EUR}}, {{score_security}}, {{score_governance}} -->
<!-- TOKEN-BUDGET: 4000 (solo:0.9x=3600, team:1.0x=4000, sme:1.1x=4400) -->
<!--
=============================================================================
PLATIN+++ v7.0: HYPER-PERSONALIZED QUICK WINS (Phase 3 Sprint 1)
=============================================================================

CRITICAL v7.0 CHANGES (STRICTLY FOLLOW!):
1. ALL 5 Goldnuggets (freetext fields) MUST be used
2. Quick Win #1 QUOTES {{ZEITERSPARNIS_PRIORITAET}} VERBATIM in blockquote
3. Quick Win #2 references {{ki_projekte}} (if provided)
4. EVERY Quick Win contains a copy-paste prompt
5. Setup steps with CONCRETE time estimates

=============================================================================
THE 5 GOLDNUGGETS (Freetext Fields) - USE ALL OF THEM!
=============================================================================

1. HAUPTLEISTUNG - What does the business do?
   Value: "{{hauptleistung}}"
   → Use: All Quick Wins must fit the core business

2. ZEITERSPARNIS_PRIORITAET - Where does the user lose most time?
   Value: "{{ZEITERSPARNIS_PRIORITAET}}"
   → Use: Quick Win #1 MUST solve this problem and QUOTE IT VERBATIM!

3. KI_PROJEKTE - What is already planned?
   Value: "{{ki_projekte}}"
   → Use: Quick Win #2 picks up planned projects (if provided)

4. KI_GUARDRAILS - What is OFF-LIMITS?
   Value: "{{ki_guardrails}}"
   → Use: Respect in ALL Quick Wins, mention explicitly in prompts

5. VISION_3_JAHRE - Where should the journey go?
   Value: "{{vision_3_jahre}}"
   → Use: Quick Wins should align with long-term vision

=============================================================================
INDUSTRY AND SIZE (for complexity and tools):
=============================================================================

INDUSTRY: {{BRANCHE_LABEL}}
SIZE: {{UNTERNEHMENSGROESSE_LABEL}} (COMPANY_SIZE: {% if COMPANY_SIZE == "solo" %}solo{% elif COMPANY_SIZE == "team" %}team{% else %}sme{% endif %})
HOURLY RATE: {{STUNDENSATZ_EUR}}€/h

SCORES (for prioritization):
- Security: {{score_security}}/100 {% if score_security < 50 %}→ Prioritize Security Quick Win!{% endif %}
- Governance: {{score_governance}}/100 {% if score_governance < 50 %}→ Prioritize Governance Quick Win!{% endif %}

=============================================================================
COUNT BY SIZE:
=============================================================================
{% if COMPANY_SIZE == "solo" %}
- SOLO: Exactly 3 Quick Wins
- Language: "You" (personal, direct)
- Budget focus: max €50/month tools
- No team/enterprise jargon!
{% elif COMPANY_SIZE == "team" %}
- TEAM: Exactly 4 Quick Wins
- Language: "You/Your team"
- Budget focus: max €200/month tools
- Mention collaboration
{% else %}
- SME: Exactly 4-5 Quick Wins
- Language: "Your organization/Your teams"
- Budget focus: scalable solutions
- Include governance aspects
{% endif %}

=============================================================================
QUICK WIN #1 - FORMAT (STRICTLY FOLLOW!)
=============================================================================

Quick Win #1 MUST be structured like this:

### Quick Win #1: [Title related to {{ZEITERSPARNIS_PRIORITAET}}]

**🎯 Your Bottleneck:**
> "{{ZEITERSPARNIS_PRIORITAET}}"

**Currently:** [Describe the manual process based on {{hauptleistung}}, 1-2 sentences]
**With AI:** [What gets automated, specifically]

**⚡ Copy-Paste Prompt for [TOOL-NAME]:**
```
[REAL working prompt that fits {{hauptleistung}} and {{BRANCHE_LABEL}}]
[If {{ki_guardrails}} exists: Include "Note: {{ki_guardrails}}"]
```

**Setup in [X] Days:**
1. **[Step with tool name]** ([Time], [Cost])
2. **[Step]** ([Time])
3. **[Test/Rollout]** ([Time])

**ROI:** Saves [X]-[Y]h/month = €[Amount] (at {{STUNDENSATZ_EUR}}€/h)

---

=============================================================================
QUICK WIN #2 - FORMAT (if {{ki_projekte}} provided)
=============================================================================

{% if ki_projekte %}
Quick Win #2 MUST pick up {{ki_projekte}}:

### Quick Win #2: [Title related to {{ki_projekte}}]

**🎯 Your Planned Project:**
> "{{ki_projekte}}"

**Quick Start:** [How AI helps with the planned project]
{% if ki_guardrails %}
**⚠️ Keep in mind:** {{ki_guardrails}}
{% endif %}

**⚡ Copy-Paste Prompt:**
```
[Prompt fitting the planned project]
```

**Setup in [X] Days:**
1. **[Step]** ([Time])
2. **[Step]** ([Time])
3. **[Step]** ([Time])

**ROI:** [Concrete benefit]

---
{% else %}
Quick Win #2 focuses on productivity fitting {{hauptleistung}}.
{% endif %}

=============================================================================
ADDITIONAL QUICK WINS - FORMAT
=============================================================================

### Quick Win #X: [Title]

**Problem:** [1-2 sentences, related to {{BRANCHE_LABEL}} and {{hauptleistung}}]

**⚡ Copy-Paste Prompt:**
```
[Concrete prompt]
```

**Setup in [X] Days:**
1. **[Step]** ([Time])
2. **[Step]** ([Time])

**ROI:** [Time savings and € value]

---

=============================================================================
TOOL RECOMMENDATIONS (CONCRETE NAMES!)
=============================================================================

SOLO BUDGET (max €50/month):
- ChatGPT Plus: €20/month – Texts, brainstorming
- Claude Pro: €18/month – Long documents, analysis
- Perplexity Pro: €20/month – Research with sources

TEAM BUDGET (max €200/month):
- Microsoft Copilot: €22/user – Office integration
- Notion AI: €10/user – Knowledge management
- Otter.ai: €17/month – Meeting transcription

INDUSTRY-SPECIFIC:
- IT/Software: GitHub Copilot (€19/month)
- Consulting: Claude Pro + Perplexity Pro
- Marketing: Jasper (€49/month), Midjourney (€10/month)
- Finance/Legal: Microsoft Copilot (Compliance features)

=============================================================================
QUALITY CHECK BEFORE OUTPUT (ALL must be ✓!):
=============================================================================

□ Quick Win #1 quotes "{{ZEITERSPARNIS_PRIORITAET}}" VERBATIM in blockquote?
□ Quick Win #1 fits "{{hauptleistung}}"?
□ Quick Win #2 references "{{ki_projekte}}" (if provided)?
□ ALL Quick Wins have copy-paste prompts in code blocks?
□ ALL Quick Wins have 2-3 numbered setup steps with time estimates?
□ Tool names are CONCRETE (not "AI tools")?
□ "{{ki_guardrails}}" is respected (if provided)?
□ Language fits size (Solo: personal, Team: collaboration)?
□ Budget fits size?
□ ROI calculation uses {{STUNDENSATZ_EUR}}?

=============================================================================
ANTI-PATTERNS (DO NOT DO!):
=============================================================================

❌ "AI-powered automation" without concrete tool
❌ "Optimize your processes" without concrete prompt
❌ Generic email automation for everyone
❌ Truncated quotes ("Implementation and programming of pro...")
❌ Enterprise jargon for Solo ("Stakeholders", "Framework", "Pipeline")
❌ Setup "in a few minutes" (unrealistic!)
❌ Prompts without industry/activity context
❌ Ignoring guardrails

=============================================================================
EXAMPLE TRANSFORMATION:
=============================================================================

BEFORE (generic, bad):
"Process optimization for 'Implementation and programming of pro...':
AI-powered automation. Use Claude/GPT for templates."

AFTER (personalized, good):

### Quick Win #1: Auto-generate questionnaire templates

**🎯 Your Bottleneck:**
> "Implementation and programming of interesting projects"

**Currently:** Each AI readiness questionnaire is created manually (3-5h)
**With AI:** Claude generates structure and questions in 15 minutes

**⚡ Copy-Paste Prompt for Claude:**
```
Create an AI readiness questionnaire for [insert industry]:
- 15 questions, Likert scale 1-5
- Categories: Strategy, Data, Processes, Culture
- Output: JSON for Typeform
- Note: No health or financial forecasts
```

**Setup in 2 Days:**
1. **Activate Claude Pro** (10 min, €18/month)
2. **Test prompt** with 3 industries (2h)
3. **Create 5 templates** and save (4h)

**ROI:** Saves 8-12h/month = €800-1,200 (at €100/h)

=============================================================================
-->

## Quick Wins – Immediately Actionable Measures

{% if COMPANY_SIZE == "solo" %}
<p>The following <strong>3 Quick Wins</strong> are designed specifically for you as a solo professional in <strong>{{hauptleistung}}</strong>. They directly address your time drain and can be implemented with minimal budget.</p>
{% elif COMPANY_SIZE == "team" %}
<p>The following <strong>4 Quick Wins</strong> are designed for you and your team in <strong>{{hauptleistung}}</strong>. They improve collaboration and save time together.</p>
{% else %}
<p>The following <strong>4-5 Quick Wins</strong> are designed for your organization in <strong>{{hauptleistung}}</strong>. They offer scalable solutions with clear ROI.</p>
{% endif %}

<!--
=============================================================================
NOW GENERATE the Quick Wins following the rules above!

MANDATORY CHECKLIST:
✓ Quick Win #1: Quote "{{ZEITERSPARNIS_PRIORITAET}}" verbatim
✓ Quick Win #2: Reference "{{ki_projekte}}" (if provided)
✓ All: Copy-paste prompts in code blocks
✓ All: 2-3 numbered setup steps
✓ All: Concrete tool names and prices
✓ Respect: "{{ki_guardrails}}" (if provided)
✓ Language: {% if COMPANY_SIZE == "solo" %}Solo (personal, "You"){% elif COMPANY_SIZE == "team" %}Team ("You/Your team"){% else %}SME (professional){% endif %}
=============================================================================
-->

<p class="small muted">These Quick Wins are based on your specific situation in {{BRANCHE_LABEL}}. Time savings are experience-based estimates and vary depending on implementation.</p>
