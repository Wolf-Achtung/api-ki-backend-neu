Developer:
<!-- PLATIN++ PROMPT -->
<!-- SECTION: gamechanger -->
<!-- VERSION: v7.0 PLATIN++ V5 -->
<!-- OUTPUT: HTML -->
<!-- SIZE-AWARE: solo/team/sme -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, {{STRATEGISCHE_ZIELE}}, {{GESCHAEFTSMODELL_EVOLUTION}}, {{VISION_3_JAHRE}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 3000 (solo:0.8x=2400, team:1.0x=3000, sme:1.15x=3450) -->
<!--
GOAL: 2–3 realistic gamechangers for {{HAUPTLEISTUNG}}.

MANDATORY STRUCTURE (per gamechanger):
1. Core idea (2-3 sentences)
2. Affected value creation (specific)
3. Benefit (quantifiable if possible)
4. Prerequisites (size-aware)
5. First step in the next 90 days

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: automation, personal relief, scalable templates
        FORBIDDEN: "departments", "teams", "areas"
- team: collaborative workflows, roles, simple governance
- sme: scalable processes, clear responsibilities, pilot areas

ANTI-REDUNDANCY:
- Gamechangers complement business case, don't repeat it
- Link to Roadmap, but no duplication

RULES:
- No invented data
- Concrete reference to {{HAUPTLEISTUNG}} required
-->

<section class="section gamechanger">
  <h2>AI as a Gamechanger for Your Business Model</h2>

  <p>
    For a company in the <strong>{{BRANCHE_LABEL}}</strong> industry with size
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> and focus on
    <strong>{{HAUPTLEISTUNG}}</strong>, several AI scenarios emerge that can
    noticeably transform value creation in the coming years. The following
    proposals directly connect to your strategic goals
    ({{STRATEGISCHE_ZIELE}}) as well as the planned evolution of your business model
    ({{GESCHAEFTSMODELL_EVOLUTION}}) and your vision for the next three years
    ({{VISION_3_JAHRE}}).
  </p>

  <ol class="gamechanger-list">

    <!-- GAMECHANGER 1 -->
    <li>
      <h3>1. AI-Powered Standardization & Automation of Core Processes</h3>
      <p><strong>Core Idea:</strong>
        Recurring tasks in {{HAUPTLEISTUNG}} are standardized through AI-powered templates,
        automations, and structured decision pathways so that quality and speed
        significantly increase.
      </p>
      <p><strong>Affected Value Creation:</strong>
        Creation, analysis, internal coordination, customer documentation.
      </p>
      <p><strong>Benefit:</strong>
        Less manual routine work, more stable results, and a consistent
        customer experience – regardless of daily form or workload.
      </p>
      <p><strong>Prerequisites:</strong>
        5–10 typical examples, defined quality criteria, clear input rules;
        {% if COMPANY_SIZE == "solo" %}personal routines{% elif COMPANY_SIZE == "team" %}team role assignment{% else %}involved functional areas{% endif %}.
      </p>
      <p><strong>First Step in the Next 90 Days:</strong>
        Select a prioritized sub-process and stabilize it with AI templates + review steps
        as a mini-pilot.
      </p>
    </li>

    <!-- GAMECHANGER 2 -->
    <li>
      <h3>2. Building an AI-Powered Knowledge Pool for Decisions & Proposals</h3>
      <p><strong>Core Idea:</strong>
        Central information, examples, best practices, and internal expertise are
        bundled with AI support, so that research, proposal processes, or analyses
        proceed significantly faster and more consistently.
      </p>
      <p><strong>Affected Value Creation:</strong>
        Proposal development, planning, internal coordination, knowledge transfer.
      </p>
      <p><strong>Benefit:</strong>
        Less search effort, significant time savings, better decision quality, and
        higher recognition value for customers.
      </p>
      <p><strong>Prerequisites:</strong>
        Structured examples and internal content; brief rules for quality and
        updates; {% if COMPANY_SIZE == "solo" %}personal organization{% elif COMPANY_SIZE == "team" %}team coordination{% else %}cross-functional coordination{% endif %}.
      </p>
      <p><strong>First Step in the Next 90 Days:</strong>
        Bundle 10–15 real content pieces, generate first AI-powered summaries, and
        integrate these as a knowledge base into daily work.
      </p>
    </li>

    <!-- GAMECHANGER 3 -->
    <li>
      <h3>3. AI-Based Quality Assurance & Consistent Customer Results</h3>
      <p><strong>Core Idea:</strong>
        Quality, precision, and consistency are improved through AI-powered review mechanisms
        that consider industry-specific requirements
        (e.g., tone, structure, completeness, risks, sensitive content).
      </p>
      <p><strong>Affected Value Creation:</strong>
        Customer communication, content production, internal reviews, final output.
      </p>
      <p><strong>Benefit:</strong>
        Fewer errors, fewer correction loops, and a significantly higher
        first-time-right rate – especially relevant under time pressure or high workload.
      </p>
      <p><strong>Prerequisites:</strong>
        5–7 clear review criteria, uniform templates, defined escalation logic;
        {% if COMPANY_SIZE == "solo" %}personal routine{% elif COMPANY_SIZE == "team" %}review roles{% else %}quality assurance + functional areas{% endif %}.
      </p>
      <p><strong>First Step in the Next 90 Days:</strong>
        Introduce an AI-powered mini-checklist and apply it to every output
        before results are used internally or externally.
      </p>
    </li>

  </ol>

  <h3>What These Gamechangers Have in Common</h3>
  <ul>
    <li>They build on existing strengths of {{HAUPTLEISTUNG}} and amplify them with AI.</li>
    <li>They consider the resources and decision pathways of a {{UNTERNEHMENSGROESSE_LABEL}} company.</li>
    <li>They can be piloted with manageable risk and scaled step by step upon success.</li>
  </ul>

  <p class="small muted">
    The gamechangers serve as strategic guardrails and support your company
    in moving from initial AI steps toward sustainable, scalable value creation.
  </p>
</section>

<!-- DEV: PDF-SLIMDOWN v2.0 - Target: 500-700 words, compact but complete -->
