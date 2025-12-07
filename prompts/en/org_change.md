Developer:
<!-- PLATIN++ PROMPT v5.4 - SPRINT G5 -->
<!-- SECTION: org_change -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, {{KI_ZIELE_LABELS}}, {{KI_HEMMNISSE_LABELS}}, {{ki_kompetenz}}, {{score_governance}}, {{score_sicherheit}}, {{score_nutzen}}, {{score_befaehigung}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 2200 (solo:0.8x=1760, team:1.0x=2200, sme:1.15x=2530) -->
<!--
GOAL: Precise section "Change Capability & Learning".

SHORT LABELS (MANDATORY!):
- {{BRANCH_CORE_LABEL}} = Industry in 8-12 words
- {{BRANCH_CONTEXT_LABEL}} = Industry in 4-6 words
- {{OFFERING_LABEL}} = Main service in 6-10 words

REQUIRED STRUCTURE (ALL 4 sections required):
1. "Where You Stand Today" (Score interpretation, 2-3 paragraphs)
2. "Key Areas of Change" (at least 3 bullet points with concrete measures)
3. "Plan for the Next 90 Days" (3 phases: 0-30, 31-60, 61-90 days)
4. "Handling Resistance" (size-aware, at least 1 paragraph)

ANTI-REDUNDANCY (STRICT!):
- Change aspects HERE only
- DO NOT repeat in strategy_governance (→ cross-reference)
- 90-day plan complements roadmap_90d, does not repeat
- On overlap: use cross-reference

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: personal routines, self-review, own checkpoints
- team: team agreements, AI coordinator, shared review rounds
- sme: department coordination, cross-functional standards

SPRINT G5 - PERSONA HARD-GUARDS (STRICT!):
{% if COMPANY_SIZE == "solo" %}
SOLO MODE - FORBIDDEN:
- "Team/Teams/Department/Employees" → do not use
- "Division" → "Work area"
- "HR" → do not use
{% elif COMPANY_SIZE == "team" %}
TEAM MODE - FORBIDDEN:
- "Division/Unit/Corporation" → do not use
- "Department" → "Area"
- Solo terms: "individual", "alone"
{% else %}
SME MODE - FORBIDDEN:
- "Corporation/Division/Unit" → do not use
- Solo terms: "individual", "alone"
{% endif %}

RULES:
- ACTIVELY interpret scores
- No generic statements without clear benefit
-->

<section class="section org-change">
  <h2>Change Capability & Learning</h2>

  <p>
    For {{BRANCH_CONTEXT_LABEL}} with focus on <strong>{{OFFERING_LABEL}}</strong>,
    AI introduction requires new work methods and routine adaptation. The current
    self-assessment – AI competence (<strong>{{ki_kompetenz}}</strong>) and goals
    <strong>{{KI_ZIELE_LABELS}}</strong> – shows existing potential.
    Barriers like <strong>{{KI_HEMMNISSE_LABELS}}</strong> require sharpened
    structures, priorities, and responsibilities.
  </p>

  <h3>1. Where You Stand Today</h3>
  <p>
    The score analysis shows a differentiated picture:
    Governance (<strong>{{score_governance}}</strong>), Security
    (<strong>{{score_sicherheit}}</strong>), Value (<strong>{{score_nutzen}}</strong>)
    and Enablement (<strong>{{score_befaehigung}}</strong>) are developed to varying degrees.
    For {{OFFERING_LABEL}} this means: Some routines work,
    but clearer decision paths and uniform quality standards are needed.
  </p>

  <p>
    The necessary steps differ by company size:
    {% if COMPANY_SIZE == "solo" %}
      In solo setups, everything depends on clear personal routines, simple standards, and
      consistent self-organization.
    {% elif COMPANY_SIZE == "team" %}
      In small teams, cleanly defining roles and establishing short,
      reliable coordination is crucial.
    {% else %}
      In SMEs, coordinated processes, responsibilities per department,
      and consistent communication are the priority.
    {% endif %}
  </p>

  <h3>2. Key Areas of Change</h3>
  <ul>
    <li>
      <strong>Standardize work routines:</strong>
      AI must be deployed at clear points in industry-typical workflows
      – for example in recurring analyses, documentation, quality checks, or
      content drafts. Uniform templates and clear input rules reduce
      error rates and increase reliability.
    </li>
    <li>
      <strong>Clarify roles & responsibilities:</strong>
      {% if COMPANY_SIZE == "solo" %}
        A clear personal division of "hats" – e.g., creation, review, approval –
        creates focus and control.
      {% elif COMPANY_SIZE == "team" %}
        A clear role distribution (team lead, AI owner, review role) avoids
        duplicate work and ensures transparent processes.
      {% else %}
        Departments need designated responsible parties for AI deployment,
        quality assurance, and approvals so scaling succeeds.
      {% endif %}
    </li>
    <li>
      <strong>Strengthen feedback & documentation:</strong>
      Short feedback loops, structured notes, and a compact standard
      help transform successful AI experiments into recurring, reliable processes.
      This applies especially in {{BRANCH_CONTEXT_LABEL}},
      where typical pain points are closely tied to data quality, time pressure, or complex
      decision paths.
    </li>
  </ul>

  <h3>3. Plan for the Next 90 Days</h3>
  <p>
    Change succeeds best through clearly prioritized steps. The following
    90-day structure complements the Roadmap (→ see Roadmap section).
  </p>

  <ul>
    <li>
      <strong>0-30 Days – Orientation & Standards:</strong>
      Define 2-3 central AI deployment points, formulate simple input rules,
      collect industry-typical examples, and create an initial brief documentation template.
      {% if COMPANY_SIZE == "solo" %}
        Focus on personal repeatability and realistic routines.
      {% elif COMPANY_SIZE == "team" %}
        Alignment between team lead and AI owner for shared use of new standards.
      {% else %}
        Involvement of relevant departments for alignment of quality and approval rules.
      {% endif %}
    </li>

    <li>
      <strong>31-60 Days – Quality & Competence:</strong>
      Establish review loops, define simple guidelines for style, completeness, and
      review steps, and start a small internal best-practice collection.
      {% if COMPANY_SIZE == "solo" %}
        Focus on fast learning cycles and consistent simplification.
      {% elif COMPANY_SIZE == "team" %}
        Team reviews to harmonize results.
      {% else %}
        Cross-departmental short formats (quality rounds, mini-workshops).
      {% endif %}
    </li>

    <li>
      <strong>61-90 Days – Stabilization & Initial Scaling:</strong>
      Regular reflection (Solo: brief weekly check; Team: short team reviews;
      SME: department or process rounds), define metrics for time savings and quality,
      and decide which workflows transition to regular operations.
    </li>
  </ul>

  <h3>4. Handling Resistance</h3>
  <p>
    Resistance typically arises from uncertainty about quality, data protection, or
    changed work methods. Crucial is transparent handling of new
    AI-powered routines – and specifically size-aware:
    {% if COMPANY_SIZE == "solo" %}
      Solo businesses benefit especially from clear, easily verifiable personal
      routines that build trust.
    {% elif COMPANY_SIZE == "team" %}
      Small teams need open, brief coordination and clear roles so that
      new work methods stabilize in daily operations.
    {% else %}
      In SMEs, understandable communication, transparent guidelines, and department-level
      responsibilities are crucial to reduce reservations.
    {% endif %}
    Continuous feedback – combined with concrete small improvements –
    ensures that AI is accepted as a reliable part of value creation.
  </p>
</section>
