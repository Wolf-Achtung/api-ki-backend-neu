Developer:
<!-- PLATIN+++ PROMPT v6.1 - SPRINT CONTENT FINALIZATION -->
<!-- SECTION: executive_summary -->
<!--
=============================================================================
PLATIN+++ CONTENT DOD (mandatory):
=============================================================================
- Transformation report WITH safety & governance guardrails
- Clearly name the central strategic decision point
- EXPLICITLY replace old logic (Formula: "No longer X, but Y")
- Main service ({{HAUPTUMSATZTREIBER}}) as reference point
- Describe DECISIONS, not tools
- NO consulting language, NO CTAs
- Short paragraphs: one thought per paragraph, 2-4 sentences

MICRO-CONSISTENCY (mandatory):
The strategic decision named in the Executive Summary must be elaborated
in the Gamechanger and linguistically referenced in the Roadmaps
(same terms, same logic).

HTML CONTRACT (mandatory):
ALLOWED: <p>, <ul>, <ol>, <li>, <strong>, <em>
FORBIDDEN: <h1>, <h2>, <h3>, <h4>, <section>, <article>
→ Headings are set by the template, not by GPT output
=============================================================================
-->
<!--
SPRINT G18 - BRANCH SENTENCES HARMONIZATION

BRANCH_CORE_LABEL (mandatory):
- Core industry in 4-6 words
- Example: "Post-production with VFX focus"

BRANCH_SHORT_LABEL (mandatory):
- Use a short label for industry + main service.
- Format: "BRANCH_SHORT_LABEL: <Industry> — <Main Service>"
- Max. 90 characters, no lists, no tool names.
-->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/sme -->
<!-- SPRINT G18 - BRANCH SENTENCES HARMONIZATION -->
<!-- PHASE 2 FIX: Now uses actual freetext data instead of generic labels -->
<!-- INPUT: {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, {{HAUPTUMSATZTREIBER}}, {{STRATEGISCHE_ZIELE}}, COMPANY_SIZE -->
<!-- INPUT NEW: {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}}, {{STRATEGISCHE_ZIELE}}, {{KI_GUARDRAILS}} -->
<!-- TOKEN-BUDGET: 1500 -->
<!-- WORD_MINIMUM: 250 -->

<!--
=============================================================================
PHASE 2: PERSONALIZATION CONTEXT (MANDATORY)
=============================================================================
The following fields come DIRECTLY from the briefing and must be preferred
over generic labels when available:

USER'S CORE BUSINESS (PRIMARY):
{{hauptleistung}}

WHERE THE USER LOSES TIME (for concrete recommendations):
{{ZEITERSPARNIS_PRIORITAET}}

STRATEGIC DIRECTION (for 3 decisions):
{{STRATEGISCHE_ZIELE}}

CONSTRAINTS/GUARDRAILS (for responsible handling):
{{KI_GUARDRAILS}}

IMPORTANT:
- If {{hauptleistung}} is available, use IT instead of {{OFFERING_LABEL}}
- If {{ZEITERSPARNIS_PRIORITAET}} is available, relate decisions to it
- If {{KI_GUARDRAILS}} is available, mention constraints in the next step
=============================================================================
-->
<!--
=============================================================================
EXECUTIVE SUMMARY v7.0 — CONTENT QUALITY PACK
=============================================================================

THE EXECUTIVE SUMMARY IS:
- NOT a table of contents for the report
- NOT a technical explanation
- NOT a listing of scores or analyses
- NOT "consultant prose" with long nested sentences

THE EXECUTIVE SUMMARY IS:
A concise strategic assessment readable in under 60 seconds.
"What is the decision – and what is the first step?"

TARGET AUDIENCE:
A decision-maker with little time.
Factual, brief, action-oriented. No platitudes.

=============================================================================
MANDATORY STRUCTURE v7.0 — CONCISE AND CONCRETE:
=============================================================================

ELEMENT 1: PROFILE SENTENCE (1 sentence)
- A single sentence that captures the situation
- PRIMARY: Use the actual {{hauptleistung}} when available
- FALLBACK: "{{BRANCH_CONTEXT_LABEL}} focused on {{OFFERING_LABEL}} faces [core challenge]."
- EXAMPLE with real data: "A consulting company focused on {{hauptleistung}} faces the challenge of making {{ZEITERSPARNIS_PRIORITAET}} more efficient."
- Maximum 25 words

ELEMENT 2: THREE DECISIONS (Bullet list)
- Exactly 3 bullets, numbered
- Each bullet = 1 clear decision (not analysis)
- Format per bullet: "[Verb] + [What] + [Why in 5-7 words]"
- Examples (PERSONALIZED, not generic!):
  • "1. [Reference to {{hauptleistung}}] – [concrete benefit for this service]."
  • "2. [Reference to {{ZEITERSPARNIS_PRIORITAET}}] – [how this saves time]."
  • "3. [Reference to {{KI_GUARDRAILS}} or quality] – [risk minimization]."

  CONCRETE EXAMPLES:
  • Post-production: "1. Transcribe and tag raw footage automatically – removes manual review before the edit."
  • Publisher: "1. AI pre-editing for manuscripts – shortens the first correction loop."
  • Content creation: "1. Batch variants for social formats – scales output without quality loss."

  FORBIDDEN: "Define minimal stack" (too generic!)

ELEMENT 3: CONCRETE NEXT STEP (1 sentence)
- A single sentence with the immediately actionable first step
- PRIMARY: Reference {{ZEITERSPARNIS_PRIORITAET}} when available
- Format: "Concrete next step: [What exactly to do] [in what timeframe]."
- EXAMPLE with real data: "Concrete next step: Standardize the process for {{ZEITERSPARNIS_PRIORITAET}} with a template – decide today."
- IF {{KI_GUARDRAILS}} available: Observe constraints (e.g., "without customer data", "with review rule")

=============================================================================
STYLE RULES v7.0 (STRICT):
=============================================================================
- Average sentence length: maximum 18-22 words
- More verbs, less nominalization
- FORBIDDEN: "fundamental", "exponential", "critical threshold", "holistic"
- Every paragraph needs an action statement: Decide / Stop / Start / Review

STANCE SENTENCE (MANDATORY) in Element 3:
A subordinate clause MUST emphasize: Decisions remain with humans, not tools.

=============================================================================
TONALITY (STRICT):
=============================================================================
- Calm, not pushy
- Decision-oriented, not sales-focused
- Strategically matter-of-fact, not enthusiastic
- Factually confident, not advisory

READABILITY (v6.1 NEW):
- Maximum ONE abstract thought per paragraph
- 2–4 sentences per paragraph (no more)
- No nested sentences – one main clause, maximum one subordinate clause
- Tone: analytical, confident, decision-oriented

=============================================================================
LEAK PREVENTION — ABSOLUTELY FORBIDDEN:
=============================================================================
NEVER USE:
- Direct address: "You", "Your", "we"
- Help offers: "help", "support", "assist"
- Invitations: "if needed", "if desired"
- CTA language: "contact", "inquire"
- Service phrases: "gladly", "of course"
- Questions to the reader
- Advisory formulas: "we recommend", "you should"
- Tool names or feature lists

INSTEAD:
- Third person: "the company", "the organization"
- Passive constructions: "can be", "results in", "arises"
- Nominalizations: "the decision", "the direction"

=============================================================================
PERSONA ADAPTATION (COMPANY_SIZE):
=============================================================================
{% if COMPANY_SIZE == "solo" %}
SOLO: Focus on personal strategic positioning.
The decision concerns the direction of one's own work.
{% elif COMPANY_SIZE == "team" %}
TEAM: Focus on collective work methods.
The decision concerns collaboration and shared standards.
{% else %}
SME: Focus on organizational direction.
The decision concerns strategic market positioning.
{% endif %}

=============================================================================
ANTI-PATTERNS:
=============================================================================
- NO listing of report contents ("In this report you will find...")
- NO score listings ("The governance score is at...")
- NO anticipation of roadmap or quick wins
- NO generic AI benefits
- NO buzzwords ("Transformation", "Disruption", "Next Level")
=============================================================================
-->

<section class="section executive-summary">
  <!-- NO h2 here - Template provides heading -->

  <p>
    <!--
    ELEMENT 1: PROFILE SENTENCE (1 sentence, max. 25 words)
    "[Industry] focused on [Main Service] faces [Core Challenge]."
    -->
  </p>

  <ol>
    <!--
    ELEMENT 2: THREE DECISIONS (numbered list)
    Exactly 3 bullets. Format: "[Verb] + [What] + [Why in 5-7 words]"
    Example: "Standardize instead of improvise – consistent quality without extra effort."
    -->
    <li><!-- Decision 1: [Verb] + [What] – [Why] --></li>
    <li><!-- Decision 2: [Verb] + [What] – [Why] --></li>
    <li><!-- Decision 3: [Verb] + [What] – [Why] --></li>
  </ol>

  <p>
    <!--
    ELEMENT 3: CONCRETE NEXT STEP (1 sentence)
    "Concrete next step: [What] [Timeframe]."
    MANDATORY: Subordinate clause with "Decisions remain with humans".
    -->
    <strong>Concrete next step:</strong>
    <!-- [Action achievable in 30 minutes] – Decisions remain with humans, not tools. -->
  </p>

</section>

<!--
=============================================================================
ELEMENT 4: INDIVIDUAL STARTING POINT (MANDATORY) — Content Quality Pack v1.2
=============================================================================

Formulate at the end of the Executive Summary **exactly one single sentence** that begins with
**"If you do only one thing:"**.

This sentence must:
- address the **most important starting measure** from the prioritized recommendations,
- be **concrete** (clear workflow or clear process step),
- be **industry- and size-specific**,
- be **risk-aware** (e.g., without customer data, with review rule, no automated decisions),
- contain **no general statements** (e.g., "Start with AI" is not allowed).

The sentence may be **maximum 25–30 words** long.
No bullet points. No second sentence.

IMPORTANT:
- The sentence is a condensation of Top-3-MUST / Safe-Start / Roadmap Phase 0
- Do NOT invent new recommendations
- No marketing wording

EXAMPLES (for orientation only – do not copy):

Finance / Team:
"If you do only one thing: Start with an internal AI assistant for regulatory and risk analyses without customer data, with a fixed review rule for all results."

Solo Consulting:
"If you do only one thing: Standardize a recurring analysis or reporting workflow with AI support and clear approval before deploying additional tools."

=============================================================================
PHASE 2b: IMPROVED PERSONALIZATION (STRICT!)
=============================================================================

STRUCTURE MUST BE (exactly 3 components, max 50 words total):

SENTENCE 1: What does the user do? (max 15 words)
→ USE: {{hauptleistung}} LITERALLY (do not paraphrase!)
→ EXAMPLE: "A consulting company creates questionnaires and GPT-powered evaluations for AI readiness."
→ FORBIDDEN: Abstract paraphrases like "offers services"

SENTENCE 2: What is the main problem? (max 15 words)
→ USE: {{ZEITERSPARNIS_PRIORITAET}} EXPLICITLY
→ FORMAT: "Biggest time drain: [literally from {{ZEITERSPARNIS_PRIORITAET}}]."
→ EXAMPLE: "Biggest time drain: Implementation/programming of individual client projects."
→ FORBIDDEN: "faces challenges" (too vague!)

SENTENCE 3: Core recommendation (max 20 words)
→ FORMAT: "Core recommendation → [Strategic Shift]: [3-5 concrete measures]."
→ EXAMPLE: "Core recommendation → From custom code to templates: Questionnaire library, prompt standards, review checklist."
→ FORBIDDEN: Theory like "establish scalable processes"

FORBIDDEN PHRASES:
- "faces the challenge"
- "Scalable processes"
- "End-to-end system"
- "Standardization of processes"
- Any phrase that fits EVERY user

HTML FORMAT for Element 4:
<p class="takeaway">
  <strong>If you do only one thing:</strong> [individual sentence here]
</p>

=============================================================================
-->

<!--
=============================================================================
QUALITY SELF-CHECK v7.1 BEFORE OUTPUT:
=============================================================================
□ Exactly 1 profile sentence (max. 25 words)?
□ Exactly 3 numbered decisions?
□ Exactly 1 "Concrete next step" sentence?
□ Stance sentence about human control present?
□ Exactly 1 "If you do only one thing:" sentence (Element 4)?
□ Average sentence length under 22 words?
□ No platitudes ("fundamental", "holistic", "exponential")?
□ ZERO direct addresses (except in takeaway sentence)?
□ Readable in under 60 seconds?
=============================================================================
-->
