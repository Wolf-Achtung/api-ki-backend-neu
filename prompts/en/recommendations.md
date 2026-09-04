Developer:
<!-- PLATIN++ PROMPT v5.4 - SPRINT G5 -->
<!-- SECTION: recommendations -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/sme -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 600 (solo:0.8x=480, team:1.0x=600, sme:1.15x=690) -->
<!--
=============================================================================
GOAL (CONTENT QUALITY PACK v7.0): Clearly separate MUST vs. OPTIONS
=============================================================================

SHORT LABELS (MANDATORY!):
- {{BRANCH_CORE_LABEL}} = Industry in 8-12 words
- {{BRANCH_CONTEXT_LABEL}} = Industry in 4-6 words
- {{OFFERING_LABEL}} = Main service in 6-10 words

=============================================================================
STRUCTURE v7.0 — MUST vs. OPTIONS (MANDATORY!):
=============================================================================

SECTION 1: MUST-MEASURES (exactly 3 points)
- Numbered 1-3
- Per point: 1 sentence measure + 1 short sentence "Why now?" (7-10 words)
- Format: "<strong>1. [Measure]</strong> – [Why now in 7-10 words]"
- NO detailed explanations in this section
- PHASE 2b: PERSONALIZATION INSTEAD OF GENERIC (MANDATORY!)

PERSONALIZATION CONTEXT (available from briefing):
- {{hauptleistung}} = What the user specifically offers
- {{ZEITERSPARNIS_PRIORITAET}} = Where the user loses the most time
- {{KI_GUARDRAILS}} = Constraints/no-gos for AI usage
- {{VISION_3_JAHRE}} = Where the user wants to go long-term

MEASURE 1: MUST directly address {{ZEITERSPARNIS_PRIORITAET}}
→ Question: How can AI/automation reduce THIS specific time drain?
→ FORBIDDEN: "Define minimal stack" (too generic!)
→ Example post-production: "Transcribe and tag raw footage automatically – removes manual review before the edit"
→ Example publisher: "AI pre-editing for manuscripts – shortens the first correction loop"

MEASURE 2: MUST fit {{hauptleistung}}
→ Question: What is THE critical success factor for this specific service?
→ FORBIDDEN: "Establish standard workflow" (too general!)
→ Example Questionnaire+GPT: "Define GPT evaluation standard – consistent quality in every analysis"
→ Example Content Agency: "Prompt templates for client projects – scales output without quality loss"

MEASURE 3: MUST address risks/guardrails
→ Consider {{KI_GUARDRAILS}} explicitly when available
→ FORBIDDEN: "Introduce review rule" (too vague!)
→ Example with guardrails: "Review checklist against unauthorized predictions – prevents compliance violations"
→ Example without guardrails: "Quality assurance for AI outputs – protects against misinformation"

SECTION 2: OPTIONS (for later / Phase 2-3)
- Additional 2-4 recommendations marked as OPTIONS
- Explicitly marked as "later" or "Phase 2/3"
- Shorter description than MUST

PRIORITY TABLE:
- Compact table with all recommendations
- Columns: Priority | Recommendation | Timeframe | Main Benefit
- MUST recommendations in rows 1-3, OPTIONS from row 4

=============================================================================
STYLE RULES v7.0:
=============================================================================
- Average sentence length: maximum 18-22 words
- More verbs, less nominalization
- FORBIDDEN: "fundamental", "exponential", "holistic", "comprehensive"
- Every recommendation needs a clear action statement

=============================================================================
ANTI-TEXT-DESERT RULES v2.0 (AGGRESSIVE - MANDATORY!)
=============================================================================
PROBLEM: Recommendation sections become long text walls.
SOLUTION: COMPACT structure with hard word limits.

HARD LIMITS PER RECOMMENDATION:
┌─────────────────────────────────────────────────────────┐
│ Field                 │ Max Words  │ Max Sentences      │
├─────────────────────────────────────────────────────────┤
│ Recommendation Title  │ 8 words    │ -                  │
│ Focus                 │ 20 words   │ 1 sentence         │
│ Measure               │ 20 words   │ 1 sentence         │
│ Benefit & Impact      │ 15 words   │ 1 sentence         │
│ Effort & Budget       │ 12 words   │ 1 sentence         │
│ Funding Opportunity   │ 15 words   │ 1 sentence         │
└─────────────────────────────────────────────────────────┘

FORMAT PER RECOMMENDATION (MANDATORY):
<strong>N. Recommendation: [Title max 8 words]</strong>
<strong>Focus:</strong> [1 sentence, max 20 words]
<strong>Measure:</strong> [1 sentence, max 20 words]
<strong>Benefit:</strong> [1 sentence, max 15 words]
<strong>Effort:</strong> [Category] – [short description max 12 words]
<strong>Funding Opportunity:</strong> [1 sentence, max 15 words]

FORBIDDEN (STRICT!):
❌ More than 5 recommendations
❌ Descriptions over 20 words
❌ Multiple sentences per field
❌ Explanatory introductory texts between recommendations
❌ Nested sentences with subclauses

ANTI-REDUNDANCY (STRICT!):
- NO repetition of Quick Wins (→ see Quick Wins section)
- NO repetition of Roadmap content (→ see Roadmap)
- Focus on SUPPLEMENTARY strategic recommendations
- When overlapping: use cross-reference

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: Owner, personal steps, low budget
- team: Team lead/AI owner, shared workflows, medium budget
- sme: Departments, governance, structured investments

SPRINT G5 - PERSONA HARD-GUARDS (STRICT!):
{% if COMPANY_SIZE == "solo" %}
SOLO MODE - FORBIDDEN:
- "Team/Teams" → "Capacity/Capacities"
- "Department/Division" → do not use
- "Employees" → "external support"
{% elif COMPANY_SIZE == "team" %}
TEAM MODE - FORBIDDEN:
- "Department/Division" → "Area"
- "Division/Unit/Corporate" → do not use
- Solo terms: "Individual", "alone"
{% else %}
SME MODE - FORBIDDEN:
- "Corporate/Division/Unit" → do not use
- Solo terms: "Individual", "alone"
{% endif %}
-->

<section class="section recommendations">
  <h2>Action Recommendations</h2>

  <p>
    For {{BRANCH_CONTEXT_LABEL}} focused on <strong>{{OFFERING_LABEL}}</strong>
    the following prioritized recommendations apply.
  </p>

  <!-- SECTION 1: MUST-MEASURES (exactly 3) - PHASE 2b PERSONALIZED -->
  <!--
  IMPORTANT: These measures are DYNAMICALLY generated by the LLM based on:
  - Measure 1: {{ZEITERSPARNIS_PRIORITAET}} (user's biggest time drain)
  - Measure 2: {{hauptleistung}} (user's concrete core service)
  - Measure 3: {{KI_GUARDRAILS}} (constraints/no-gos)

  Do NOT use the static examples below!
  -->
  <h3>MUST – Implement Immediately</h3>
  <ol class="recommendations-muss">
    <li>
      <!--
      MACHINE GENERATED: Based on {{ZEITERSPARNIS_PRIORITAET}}
      Example: "Build questionnaire template library" instead of "Minimal stack"
      -->
      <strong>[Measure that directly addresses {{ZEITERSPARNIS_PRIORITAET}}]</strong> – [Why this measure saves time].
      <p class="muss-detail">[Concrete implementation for {{hauptleistung}}]</p>
    </li>
    <li>
      <!--
      MACHINE GENERATED: Based on {{hauptleistung}}
      Example: "Define GPT evaluation standard" instead of "Standard workflow"
      -->
      <strong>[Measure that optimizes {{hauptleistung}}]</strong> – [Why this improves the core service].
      <p class="muss-detail">[Concrete process steps for {{OFFERING_LABEL}}]</p>
    </li>
    <li>
      <!--
      MACHINE GENERATED: Based on {{KI_GUARDRAILS}} or general quality assurance
      Example: "Review checklist against unauthorized predictions" instead of "Review rule"
      -->
      <strong>[Quality/risk measure fitting {{KI_GUARDRAILS}}]</strong> – [Why this minimizes risks].
      <p class="muss-detail">[Concrete checklist or approval process]</p>
    </li>
  </ol>

  <!-- SECTION 2: OPTIONS (for later) -->
  <h3>OPTIONS – Phase 2/3</h3>
  <ul class="recommendations-optionen">
    <li>
      <strong>Build knowledge management</strong> – Central library for templates and best practices.
      <span class="option-timing">{% if COMPANY_SIZE == "solo" %}From month 3{% else %}From month 4-6{% endif %}</span>
    </li>
    <li>
      <strong>Expand industry-specific pilot</strong> – Visible success for additional use cases.
      <span class="option-timing">{% if COMPANY_SIZE == "solo" %}From month 6{% else %}From month 6-9{% endif %}</span>
    </li>
    <li>
      <strong>Formalize governance</strong> – {% if COMPANY_SIZE == "solo" %}Personal checklist{% elif COMPANY_SIZE == "team" %}Team guideline{% else %}Policy document{% endif %} for AI usage.
      <span class="option-timing">{% if COMPANY_SIZE == "solo" %}From month 3{% else %}From month 6{% endif %}</span>
    </li>
  </ul>

  <h3>Priority Overview</h3>
  <table class="table">
    <thead>
      <tr><th>Type</th><th>Recommendation</th><th>Timeframe</th><th>Main Benefit</th></tr>
    </thead>
    <tbody>
      <!-- PHASE 2b: Table is DYNAMICALLY generated based on the 3 MUST measures above -->
      <tr><td><strong>MUST</strong></td><td>[Short form Measure 1 - for {{ZEITERSPARNIS_PRIORITAET}}]</td><td>Immediately</td><td>Time savings</td></tr>
      <tr><td><strong>MUST</strong></td><td>[Short form Measure 2 - for {{hauptleistung}}]</td><td>Week 1-2</td><td>Quality improvement</td></tr>
      <tr><td><strong>MUST</strong></td><td>[Short form Measure 3 - for {{KI_GUARDRAILS}}]</td><td>Week 1-2</td><td>Risk minimization</td></tr>
      <tr><td>Option</td><td>Knowledge management</td><td>{% if COMPANY_SIZE == "solo" %}Month 3+{% else %}Month 4-6{% endif %}</td><td>Stable results</td></tr>
      <tr><td>Option</td><td>Expand pilot</td><td>{% if COMPANY_SIZE == "solo" %}Month 6+{% else %}Month 6-9{% endif %}</td><td>Visible success</td></tr>
      <tr><td>Option</td><td>Formalize governance</td><td>{% if COMPANY_SIZE == "solo" %}Month 3+{% else %}Month 6+{% endif %}</td><td>Legal certainty</td></tr>
    </tbody>
  </table>
</section>


<!-- ZERO-LEAK POLICY (N4.6) -->
<!--
FORBIDDEN – NEVER USE:
- No questions to the reader ("Do you have questions?", "Would you like to learn more?")
- No prompts ("If you would like...", "Contact us...")
- No assistant language ("I can help you...", "I'm happy to explain...")
- No offers ("If needed...", "If desired...")
- No interactive elements ("Click here...", "Select...")
- No placeholders ("[Insert here]", "{{VARIABLE}}" except defined ones)
- No meta-comments ("This section...", "In the following...")

The output is a FINAL REPORT SECTION, not a conversation.
-->

<!-- PHASE 2b: GENERIC PHRASES FORBIDDEN -->
<!--
=============================================================================
FORBIDDEN FOR MUST-MEASURES (STRICT!):
=============================================================================
The following phrases are TOO GENERIC and FORBIDDEN:
- "Define/establish minimal stack"
- "Establish standard workflow"
- "Introduce review rule"
- "Clarity before complexity"
- "One central tool"
- "Input → AI draft → Review"
- Any phrase that would fit EVERY user

USE INSTEAD:
- Concrete references to {{hauptleistung}}
- Concrete references to {{ZEITERSPARNIS_PRIORITAET}}
- Concrete references to {{KI_GUARDRAILS}}
- Industry-specific terms from {{BRANCH_CONTEXT_LABEL}}

EXAMPLE TRANSFORMATIONS:
❌ "Define minimal stack"
✅ "Build transcription pipeline for raw footage" (for post-production)
✅ "Set up pre-editing workflow for manuscripts" (for publisher)
✅ "Establish batch variants for social formats" (for content creation)

❌ "Establish standard workflow"
✅ "Define approval workflow for AI dubbing" (for recording studio)
✅ "Build localisation pipeline with term base" (for games studio)
✅ "Standardise pitch modules with client approval" (for agency)

❌ "Introduce review rule"
✅ "Review checklist against unauthorized predictions" (for health guardrails)
✅ "Four-eyes principle for tax assessments" (for financial compliance)
✅ "Fact-check before publication" (for content risks)
=============================================================================
-->
