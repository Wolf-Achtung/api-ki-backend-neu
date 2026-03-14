**IMPORTANT – Length limit: Your response must not exceed 1100 words. Cut rather than exceed.**

<!-- PLATIN+++ PROMPT v6.1 - SPRINT G5 -->
<!-- SECTION: org_change -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, {{KI_ZIELE_LABELS}}, {{KI_HEMMNISSE_LABELS}}, {{ki_kompetenz}}, {{score_governance}}, {{score_sicherheit}}, {{score_nutzen}}, {{score_befaehigung}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 2200 (solo:0.8x=1760, team:1.0x=2200, kmu:1.15x=2530) -->
<!--
GOAL: Provide a precise “Changeability & Learning” section.

SHORT LABELS (MANDATORY!):
- {{BRANCH_CORE_LABEL}} = Branch in 8–12 words
- {{BRANCH_CONTEXT_LABEL}} = Branch in 4–6 words
- {{OFFERING_LABEL}} = Main offering in 6–10 words

MANDATORY STRUCTURE (4 sections):
1. "Where you stand today" (score interpretation, 2–3 paragraphs)
2. "Key areas for change" (min. 3 bullet points)
3. "Plan for the next 90 days" (3 phases: 0–30, 31–60, 61–90)
4. "Handling resistance" (size‑aware)

ANTI‑REDUNDANCY (STRICT! — HIGHEST PRIORITY!):
- Address change aspects HERE.
- Do NOT repeat them in strategy_governance (→ cross reference).
- The 90‑day plan complements roadmap_90d and does not repeat it.
- Where overlap occurs: use a cross reference.
- Do NOT copy text blocks from other sections (Roadmap, Quick Wins, Governance).
- Every sentence must be UNIQUELY formulated for this section.
- This section covers EXCLUSIVELY organisational change: roles, responsibilities, change management, acceptance.
- Reference other sections with short labels ("the phases defined in the Roadmap", "the framework described in the Governance section") instead of quoting content.
- Max 1 sentence of context per reference, then immediately continue with NEW content.
- SELF-CHECK BEFORE OUTPUT: Re-read every sentence — does it contain phrasing that appears verbatim or near-verbatim in roadmap_90d, gamechanger, or quick_wins? If yes: completely rephrase with new sentence structure and vocabulary.

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: Personal routines, self‑review, own checkpoints.
- team: Team agreements, AI coordinator, joint review rounds.
- kmu: Department‑coordination, cross‑department standards.

SPRINT G5 – PERSONA HARD‑GUARDS (STRICT!):
{% if COMPANY_SIZE == "solo" %}
SOLO MODE – PROHIBITED:
- "team/teams/department/employee" → do not use
- "division" or "unit" → do not use
- "department" → use "work area"
- "HR" → do not use
{% elif COMPANY_SIZE == "team" %}
TEAM MODE – PROHIBITED:
- "division/unit/corporate" → do not use
- "department" → use "area"
- Solo terms: "individual person", "alone" → do not use
{% else %}
KMU MODE – PROHIBITED:
- "corporation/division/unit" → do not use
- Solo terms: "individual person", "alone" → do not use
{% endif %}

RULES:
- Actively interpret scores.
- Avoid generic statements without clear benefit.
-->

<section class="section org-change">
  <h2>Changeability &amp; Learning</h2>

  <p>
    For {{BRANCH_CONTEXT_LABEL}} the introduction of AI requires new working methods.
    The current self‑assessment shows existing potential.
  </p>
  <p>
    Hindrances such as <strong>{{KI_HEMMNISSE_LABELS}}</strong> require sharpened
    structures and clear responsibilities.
  </p>

  <h3>1. Where you stand today</h3>
  <p>
    <strong>Score overview:</strong> Governance ({{score_governance}}), Security ({{score_sicherheit}}),
    Value ({{score_nutzen}}), Enablement ({{score_befaehigung}}).
  </p>
  <p>
    Some routines already work. There is a need for clearer decision paths and unified standards.
  </p>
  <p>
    {% if COMPANY_SIZE == "solo" %}
      In solo setups personal routines and consistent self‑organisation count.
    {% elif COMPANY_SIZE == "team" %}
      In small teams clear role definitions and short alignments are crucial.
    {% else %}
      In SMEs coordinated processes and responsibilities per work area are the focus.
    {% endif %}
  </p>

  <h3>2. Key areas for change</h3>
  <ul>
    <li>
      <strong>Unify work routines:</strong>
      AI must be used at clear points in branch‑specific workflows – such as recurring analyses,
      documentation, quality controls or content drafting. Uniform templates and clear input rules reduce
      error rates and increase reliability.
    </li>
    <li>
      <strong>Clarify roles &amp; responsibilities:</strong>
      {% if COMPANY_SIZE == "solo" %}
        A clear personal division of the “hats” – for example creation, review and approval – creates focus and control.
      {% elif COMPANY_SIZE == "team" %}
        A clear division of roles (team lead, AI owner, review role) avoids duplicate work and ensures transparent processes.
      {% else %}
        Work areas need defined responsible persons for AI use, quality assurance and approvals so that scaling succeeds.
      {% endif %}
    </li>
    <li>
      <strong>Strengthen feedback &amp; documentation:</strong>
      Short feedback loops, structured notes and a compact standard help to transform successful AI experiments into recurring, reliable processes.
      This is particularly important in {{BRANCH_CONTEXT_LABEL}}, where typical pain points are closely linked to data quality, time pressure or complex
      decision paths.
    </li>
  </ul>

  <h3>3. Plan for the next 90 days</h3>
  <p>
    Change succeeds best through clearly prioritised steps. The following
    90‑day structure complements the roadmap (→ see roadmap section).
  </p>

  <ul>
    <li>
      <strong>0–30 days – Orientation &amp; standards:</strong>
      Define 2–3 central AI use cases, formulate simple input rules,
      collect branch‑specific examples and create a first, short documentation template.
      {% if COMPANY_SIZE == "solo" %}
        Focus on personal repeatability and realistic routines.
      {% elif COMPANY_SIZE == "team" %}
        Coordination between team lead and AI owner to jointly use the new standards.
      {% else %}
        Involve relevant work areas to coordinate quality and approval rules.
      {% endif %}
    </li>

    <li>
      <strong>31–60 days – Quality &amp; competence:</strong>
      Establish review loops, define simple guidelines on style, completeness and review steps
      and start a small internal best‑practice collection.
      {% if COMPANY_SIZE == "solo" %}
        Focus on rapid learning cycles and consistent simplification.
      {% elif COMPANY_SIZE == "team" %}
        Team reviews to harmonise results.
      {% else %}
        Cross‑area short formats (quality rounds, mini‑workshops).
      {% endif %}
    </li>

    <li>
      <strong>61–90 days – Stabilisation &amp; initial scaling:</strong>
      Regular reflection (Solo: short weekly check; Team: short team reviews; KMU: work area or process rounds),
      set metrics for time savings and quality and decide which workflows are transferred to routine operation.
    </li>
  </ul>

  <h3>4. Handling resistance</h3>
  <p>
    Resistance arises from uncertainty about quality, data protection or changed working methods.
  </p>
  <p>
    {% if COMPANY_SIZE == "solo" %}
      Clear, verifiable routines build trust.
    {% elif COMPANY_SIZE == "team" %}
      Open coordination and clear roles stabilise new working methods.
    {% else %}
      Understandable communication and work‑area‑close responsibilities reduce reservations.
    {% endif %}
  </p>
  <p>
    Continuous feedback ensures that AI is accepted as a reliable component.
  </p>
</section>

<!-- Output guidelines:
     - Four sections structured as described above.
     - Use bold headings for the 0–30, 31–60 and 61–90 day phases.
     - Actively interpret the scores and avoid generic statements.
     - Write directly final, client‑ready content. -->
