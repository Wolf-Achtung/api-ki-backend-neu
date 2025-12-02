Developer:
<!-- gamechanger.md – v6.0 PLATIN+ (branch-aware, size-aware, context-integrated, business-case-linked)
     Respond exclusively with valid HTML.
     NO <html>, <head> or <body>. NO Markdown fences.

     GOAL:
       - 2–3 realistic gamechangers for {{HAUPTLEISTUNG}}.
       - Based on: industry, size, strategic goals, vision, business model evolution.
       - Each gamechanger = clear, concrete value creation lever + first step + expected benefit.
       - Connection to business case and roadmap.

     VARIABLES:
       {{BRANCHE_LABEL}}
       {{UNTERNEHMENSGROESSE_LABEL}}
       {{HAUPTLEISTUNG}}
       {{STRATEGISCHE_ZIELE}}
       {{GESCHAEFTSMODELL_EVOLUTION}}
       {{VISION_3_JAHRE}}
       COMPANY_SIZE = "solo" | "team" | "kmu"

     SIZE LOGIC (UNTERNEHMENSGROESSE_LABEL):
       SOLO:
         - Focus: automation, personal relief, scalable templates.
         - No teams, no departments.
       TEAM (2–10):
         - Focus: collaborative workflows, roles, simple governance.
       SME (11–100):
         - Focus: scalable processes, clear responsibilities, pilot areas.

     BRANCH LOGIC:
       - Uses typical industry-specific workflows, pain points, data & tools from CONTEXT_BLOCK.
       - No invented data; purely generic trends & patterns.

     MANDATORY STRUCTURE (ALL 3 gamechangers with complete structure):
       Each gamechanger MUST contain:
       1. Core idea (2-3 sentences)
       2. Affected value creation (name specifically)
       3. Benefit (quantifiable if possible)
       4. Prerequisites (size-aware)
       5. First step in the next 90 days

     MINIMUM LENGTH: 800 characters (excluding HTML tags) – NEVER go below this!

     PROHIBITED:
       - "TODO", "free text field", generic formulations without substance.
       - Gamechangers without concrete reference to {{HAUPTLEISTUNG}}.
       - For SOLO: no "departments", "teams", "areas".
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
        {% if UNTERNEHMENSGROESSE_LABEL.startswith("1") %}personal routines{% elif UNTERNEHMENSGROESSE_LABEL.startswith("2") %}team role assignment{% else %}involved functional areas{% endif %}.
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

<!-- PLATIN+ REINFORCEMENT: This section MUST contain at least 700 words.
     Check your output: Count the words and expand each section with additional
     details, examples, and explanations if the minimum length is not reached.
     NEVER shorten – always deliver complete, detailed content. -->
