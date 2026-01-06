<!-- PLATIN+++ PROMPT v6.1 - CONTENT FINALISATION SPRINT -->
<!-- SECTION: executive_summary -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- TOKEN-BUDGET: 1200 (solo:0.8x=960, team:1.0x=1200, sme:1.15x=1380) -->
<!-- PHASE 3: Maximum personalization using ALL 5 Goldnuggets -->
<!-- INPUT: {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, {{HAUPTUMSATZTREIBER}}, {{STRATEGISCHE_ZIELE}}, COMPANY_SIZE -->
<!-- INPUT NEW: {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}}, {{STRATEGISCHE_ZIELE}}, {{KI_GUARDRAILS}} -->
<!--
=============================================================================
PLATIN+++ CONTENT DOD (mandatory):
=============================================================================
- Transformation report WITH safety & governance guardrails
- Clearly identify the central strategic switch
- Explicitly replace old logic (format: "Stop X, Start Y")
- Use the main service ({{HAUPTUMSATZTREIBER}}) as point of reference
- Describe decisions, not tools
- NO consulting language, NO calls to action
- Short paragraphs: one idea per paragraph, 2–4 sentences

MICRO‑CONSISTENCY (mandatory):
The strategic switch named in the Executive Summary must be elaborated in the Gamechanger and referenced in the roadmaps with the same terminology and logic.

HTML CONTRACT (mandatory):
ALLOWED: <p>, <ul>, <ol>, <li>, <strong>, <em>
FORBIDDEN: <h1>, <h2>, <h3>, <h4>, <section>, <article>
→ Headings are provided by the template, not by the GPT output.

=============================================================================
PHASE 2: INDIVIDUALISATION CONTEXT (MANDATORY)
=============================================================================
The following fields come directly from the briefing and must take precedence over generic labels when present:

- CORE BUSINESS OF THE USER (PRIMARY): {{hauptleistung}}
- WHERE THE USER LOSES TIME (for concrete recommendations): {{ZEITERSPARNIS_PRIORITAET}}
- STRATEGIC OBJECTIVES (for three decisions): {{STRATEGISCHE_ZIELE}}
- RESTRICTIONS / GUARDRAILS (for responsible AI use): {{KI_GUARDRAILS}}

IMPORTANT:
- If {{hauptleistung}} is provided, use it instead of {{OFFERING_LABEL}}.
- If {{ZEITERSPARNIS_PRIORITAET}} is provided, base the decisions on it.
- If {{KI_GUARDRAILS}} is provided, mention restrictions in the next step.

=============================================================================
EXECUTIVE SUMMARY v7.0 — CONTENT QUALITY PACK
=============================================================================
The Executive Summary is NOT:
- a recap of the report
- a technical explanation
- a list of scores or analyses
- "consultant prose" with long complex sentences

The Executive Summary IS:
A concise strategic positioning that can be read in under 60 seconds. It answers: “What is the decision – and what is the first step?”

Target audience: A decision maker with little time. Tone: factual, short, action‑oriented. No fluff.

=============================================================================
MANDATORY STRUCTURE v7.0 — CONCISE AND CONCRETE
=============================================================================

ELEMENT 1: PROFILE SENTENCE (1 sentence)
- Exactly one sentence that gets to the point of the situation
- PRIMARY: Use the actual {{hauptleistung}} when available
- FALLBACK: "{{BRANCH_CONTEXT_LABEL}} focused on {{OFFERING_LABEL}} faces [core challenge]."
- EXAMPLE with real data: "A consulting company focused on {{hauptleistung}} faces the challenge of making {{ZEITERSPARNIS_PRIORITAET}} more efficient."
- Maximum 25 words

ELEMENT 2: THREE DECISIONS (ordered list)
- Exactly 3 bullets, numbered
- Each bullet = 1 clear decision (not analysis)
- Format per bullet: "[Verb] + [What] – [Why in 5–7 words]"
- Examples (INDIVIDUALISED, not generic!):
  • "1. [Reference to {{hauptleistung}}] – [concrete benefit for this service]."
  • "2. [Reference to {{ZEITERSPARNIS_PRIORITAET}}] – [how it saves time]."
  • "3. [Reference to {{KI_GUARDRAILS}} or quality] – [risk mitigation]."

ELEMENT 3: CONCRETE NEXT STEP (1 sentence)
- One sentence with the immediately actionable first step
- PRIMARY: Refer to {{ZEITERSPARNIS_PRIORITAET}} when present
- Format: "Concrete next step: [What exactly to do] [in what timeframe]."
- Example: "Concrete next step: Standardise the process for {{ZEITERSPARNIS_PRIORITAET}} with a template – decide today."
- If {{KI_GUARDRAILS}} is present: Respect restrictions (e.g. "without client data", "with a review rule").

ELEMENT 4: INDIVIDUAL TAKEAWAY (MANDATORY) — Content Quality Pack v1.2
- End the Executive Summary with **exactly one sentence** beginning **“If you do only one thing:”**.
- This sentence must:
  • capture the **most important starting action** from the prioritised recommendations,
  • be **concrete** (clear workflow or process step),
  • be **industry‑ and size‑specific**,
  • be **risk‑aware** (e.g. without client data, with review rule, no automated decisions),
  • contain no generic statements.
- The sentence may contain **no more than 25–30 words**.

IMPORTANT:
- This sentence distils the Top‑3 Must‑Do / safe start / Roadmap Phase 0.
- Do not invent a new recommendation.
- Avoid marketing wording.

=============================================================================
STYLE RULES v7.0 (STRICT)
=============================================================================
- Average sentence length: 18–22 words
- Use verbs, avoid nominal style
- FORBIDDEN: “fundamental”, “exponential”, “critical threshold”, “holistic”
- Each paragraph must contain an action statement: decide / stop / start / check

ATTITUDE SENTENCE (MANDATORY) in Element 3:
A subordinate clause MUST emphasise: decisions remain with humans, not tools.

=============================================================================
TONALITY (STRICT)
=============================================================================
- Calm, not pushy
- Decision‑oriented, not salesy
- Strategically sober, not enthusiastic
- Fact‑based and confident, not advisory

READABILITY (v6.1 NEW):
- Maximum ONE abstract idea per paragraph
- 2–4 sentences per paragraph (no more)
- No complex sentences – one main clause, maximum one subordinate clause
- Tone: analytical, confident, decision‑oriented

=============================================================================
LEAK PREVENTION — ABSOLUTELY FORBIDDEN
=============================================================================
NEVER USE:
- Direct address: "you", "your", "du", "wir"
- Assistance phrases: "help", "support", "accompany"
- Invitations: "if needed", "if desired"
- CTA language: "contact", "inquire"
- Service phrases: "gladly", "of course"
- Questions to the reader
- Consulting formulas: "we recommend", "you should"
- Tool names or feature lists

INSTEAD:
- Third person: "the company", "the organisation"
- Passive constructions: "can be", "is created"
- Substantive nouns: "the decision", "the alignment"

=============================================================================
PERSONA ADAPTATION (COMPANY_SIZE)
=============================================================================
{% if COMPANY_SIZE == "solo" %}
SOLO: Focus on personal strategic positioning. The decision concerns the orientation of the individual’s work.
{% elif COMPANY_SIZE == "team" %}
TEAM: Focus on collective working methods. The decision concerns collaboration and common standards.
{% else %}
SME: Focus on organisational positioning. The decision concerns strategic positioning in the market.
{% endif %}

=============================================================================
ANTI‑PATTERNS
=============================================================================
- NO listing of report contents ("In this report you will find…")
- NO score listings ("The governance score is…")
- NO preview of roadmap or quick wins
- NO generic AI advantages
- NO buzzwords ("transformation", "disruption", "next level")
-->

<section class="section executive-summary">
  <!-- The template provides the section heading -->

  <p>
    <!--
    ELEMENT 1: PROFILE SENTENCE (1 sentence, max. 25 words)
    Format: "[Industry] focused on [main service] faces [core challenge]."
    Use {{hauptleistung}} literally if provided; otherwise fall back to {{OFFERING_LABEL}}.
    -->
  </p>

  <ol>
    <!--
    ELEMENT 2: THREE DECISIONS (numbered list)
    Exactly 3 bullets. Each bullet uses the format: "[Verb] + [What] – [Why]".
    Example: "Standardise instead of improvising – consistent quality without extra effort."
    -->
    <li><!-- Decision 1: [Verb] + [What] – [Why] --></li>
    <li><!-- Decision 2: [Verb] + [What] – [Why] --></li>
    <li><!-- Decision 3: [Verb] + [What] – [Why] --></li>
  </ol>

  <p>
    <!--
    ELEMENT 3: CONCRETE NEXT STEP (1 sentence)
    Format: "Concrete next step: [What] [Timeframe]."
    MANDATORY: A subordinate clause emphasising that decisions remain with humans, not tools.
    -->
    <strong>Concrete next step:</strong>
    <!-- [Action implementable within 30 minutes] – decisions remain with humans, not tools. -->
  </p>

  <p class="takeaway">
    <!--
    ELEMENT 4: INDIVIDUAL TAKEAWAY (mandatory)
    Start with "If you do only one thing:" and provide the single most important start action.
    Must reference {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}} or {{KI_GUARDRAILS}}.
    -->
    <strong>If you do only one thing:</strong> <!-- individual sentence here -->
  </p>

</section>