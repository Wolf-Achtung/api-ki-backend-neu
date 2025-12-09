Developer:
<!-- PLATIN++ PROMPT v5.4 - SPRINT G17.R -->
<!-- SECTION: roadmap_90d -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/sme -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 2800 (solo:0.8x=2240, team:1.0x=2800, sme:1.15x=3220) -->
<!--
GOAL: 90-Day Roadmap with 4 clear phases + milestones + effect section + booster sections.

MINIMUM LENGTH (STRICT!):
- Solo: ≥250 words
- Team: ≥320 words
- SME: ≥350 words

PHASE STRUCTURE (STRICTLY FOLLOW!):
- Phase 0 (Week 1–2): Setup – establish foundations
- Phase 1 (Week 3–5): Relief – implement Quick Wins
- Phase 2 (Week 6–10): Productive Use – stabilize workflows
- Phase 3 (Week 11–13): Consolidation – measure results, make decision
- MANDATORY: "Expected Effects after 90 Days" section at the end

BOOSTER SECTIONS (NEW - SPRINT G17.R):
- Solo: KPI Tracking & Mini-Dashboard Setup, Micro-Change-Management
- Team: Team Communication & Rollout Rituals, Documentation & Knowledge Repository
- SME: Change Communication at Leadership Level, KPI Framework for Work Areas

FORMAT:
- Each phase: Goal (1 sentence) + 3-5 bullets + Milestone
- Milestone = concrete, measurable, achievable
- NO long texts – only key points

ANTI-REDUNDANCY (STRICT!):
- Quick Wins described in quick_wins.md – DO NOT repeat
- Tools described in tools_recommendations.md – only reference
- Here: HOW and WHEN, not WHAT (that's in Quick Wins)

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: personal routines, self-review, own documentation
        FORBIDDEN: team, department, employees
- team: AI Owner, shared standards, review rounds
        FORBIDDEN: division, unit, corporation
- sme: work areas (NOT "departments"!), pilot areas, governance, rollout
       FORBIDDEN: corporation, division, unit

GUARDRAILS: Consider guardrails from strategic context.
-->

<section class="section roadmap-90d">
  <h2>90-Day Roadmap for {{HAUPTLEISTUNG}}</h2>

  <p>
    The following plan outlines concrete steps for AI implementation in
    {{BRANCHE_LABEL}} – divided into four phases with clear milestones.
  </p>

  {% if COMPANY_SIZE == "solo" %}
  <h3>Phase 0: Setup (Week 1–2)</h3>
  <p><strong>Goal:</strong> Establish working capability with AI.</p>
  <ul>
    <li>Set up access to AI assistant and run initial tests</li>
    <li>Create first prompt template for a core task in {{HAUPTLEISTUNG}}</li>
    <li>Define your own quality criteria: What is "good enough"?</li>
    <li>Set up simple knowledge repository for templates</li>
  </ul>
  <p><strong>🎯 Milestone:</strong> AI access works, first template ready for use.</p>

  <h3>Phase 1: Relief (Week 3–5)</h3>
  <p><strong>Goal:</strong> Noticeable time savings on routine tasks.</p>
  <ul>
    <li>Implement Quick Wins from "Immediate Measures" section (→ see Quick Wins)</li>
    <li>Note time savings per task (simple tally list is enough)</li>
    <li>Expand prompt library to 5–10 working templates</li>
    <li>Establish first routine: at least one task daily with AI support</li>
  </ul>
  <p><strong>🎯 Milestone:</strong> 3–5 hours/month demonstrably saved.</p>

  <h3>Phase 2: Productive Use (Week 6–10)</h3>
  <p><strong>Goal:</strong> Stable workflows for daily work in {{HAUPTLEISTUNG}}.</p>
  <ul>
    <li>Solidify routine: Input → AI draft → Own review → Release</li>
    <li>Create quality checklist for AI outputs (3–5 checkpoints)</li>
    <li>Make self-review a habit: briefly cross-check every output</li>
    <li>Refine and document prompt templates as needed</li>
    <li>Evaluate first automation options (→ see AI Stack)</li>
  </ul>
  <p><strong>🎯 Milestone:</strong> 70%+ of AI drafts directly usable.</p>

  <h3>Phase 3: Consolidation (Week 11–13)</h3>
  <p><strong>Goal:</strong> Evaluate results, plan next steps.</p>
  <ul>
    <li>Measure actual time savings and compare with target</li>
    <li>Assess quality of results: error rate, rework effort</li>
    <li>Decision: Expand, Deepen, or Stabilize?</li>
    <li>Prioritize next use cases for 12-month roadmap</li>
  </ul>
  <p><strong>🎯 Milestone:</strong> Clear decision and prioritized list for next quarter.</p>

  <h3>Expected Effects after 90 Days</h3>
  <ul>
    <li><strong>Time Savings:</strong> 15–25% on recurring tasks</li>
    <li><strong>Quality:</strong> More consistent outputs through standardized templates</li>
    <li><strong>Routine:</strong> AI is part of daily work, no longer a special action</li>
    <li><strong>Clarity:</strong> Solid basis for decision on further investments</li>
  </ul>

  <h3>KPI Tracking & Mini-Dashboard Setup</h3>
  <p>
    As a solopreneur, you need a pragmatic, time-saving reporting system.
    Focus on these three core KPIs for your AI usage:
  </p>
  <ul>
    <li><strong>Time Savings per Week:</strong> For each AI-assisted task, note the
    time saved compared to manual processing. A simple tally or spreadsheet is
    enough – target: 3–5 hours saved per month.</li>
    <li><strong>Output Volume:</strong> How many texts, emails, concepts, or other
    deliverables have you created with AI support? Track productivity gains
    quantitatively (e.g., "12 LinkedIn posts instead of 4 without AI").</li>
    <li><strong>Quality Rating:</strong> Rate your AI outputs on a scale of 1–5 stars.
    How often could you use a draft directly? Target: 70%+ first-pass quality.</li>
  </ul>
  <p>
    <strong>Setting up the Mini-Dashboard:</strong> Use a simple tool like Notion, Excel,
    or even a notebook. Create a weekly table with columns for task type, time spent
    (with/without AI), quality stars, and brief learnings. Reserve 15–20 minutes every
    Friday for documentation. After 90 days, you'll have reliable data for your
    investment decision and can demonstrate ROI concretely.
  </p>

  <h3>Micro-Change-Management (1-Person Operation)</h3>
  <p>
    Introducing new AI workflows requires conscious integration into your daily work
    routine – even when you work alone. Without a structured approach, there's a risk
    that new tools will be forgotten after initial enthusiasm.
  </p>
  <ul>
    <li><strong>Set Routine Anchors:</strong> Link AI usage to existing habits.
    Example: "After my morning coffee, I start with AI-assisted email drafting" or
    "Before each client meeting, I generate a conversation prep." Fixed triggers
    significantly increase implementation likelihood.</li>
    <li><strong>Self-Control without Pressure:</strong> Keep a "success checklist" with
    3–5 AI tasks per week. Check off what you've accomplished – without criticizing
    yourself for omissions. Visual progress motivates continuity.</li>
    <li><strong>Weekly Self-Review (30 min.):</strong> Every Friday morning or Sunday
    evening: What worked well? Where were there hurdles? Which prompts need refinement?
    Note 2–3 concrete improvement ideas for the following week.</li>
    <li><strong>Iterative Adaptation:</strong> Your AI workflow is a living system.
    Adapt templates and routines monthly to changing requirements in {{HAUPTLEISTUNG}}.
    What worked in the first month may not be optimal in the third month.</li>
  </ul>
  <p>
    <strong>Success Factor:</strong> Set realistic intermediate goals. Start with one
    AI task daily, increase to 2–3 after two weeks. This prevents overwhelm and builds
    sustainable competence.
  </p>

  {% elif COMPANY_SIZE == "team" %}
  <h3>Phase 0: Setup (Week 1–2)</h3>
  <p><strong>Goal:</strong> Establish team-wide AI working capability.</p>
  <ul>
    <li>Designate AI Owner (responsible for standards and quality)</li>
    <li>Set up shared access for all team members</li>
    <li>Create first templates for 2 prioritized use cases</li>
    <li>Conduct brief introduction for all participants (max. 30 min.)</li>
    <li>Set up shared knowledge repository (→ see AI Stack)</li>
  </ul>
  <p><strong>🎯 Milestone:</strong> Team has access, first templates distributed.</p>

  <h3>Phase 1: Relief (Week 3–5)</h3>
  <p><strong>Goal:</strong> Implement Quick Wins across the team.</p>
  <ul>
    <li>Roll out measures from "Immediate Measures" team-wide (→ see Quick Wins)</li>
    <li>Everyone tests at least 2 workflows for {{HAUPTLEISTUNG}}</li>
    <li>Share experiences in short weekly check (15 min./week)</li>
    <li>Document first time savings: Who saves how much where?</li>
    <li>Improve and share prompt templates together</li>
  </ul>
  <p><strong>🎯 Milestone:</strong> All team members actively using AI, first time savings documented.</p>

  <h3>Phase 2: Productive Use (Week 6–10)</h3>
  <p><strong>Goal:</strong> Establish unified quality standards in {{BRANCHE_LABEL}}.</p>
  <ul>
    <li>Document standard workflow: Input → AI → Peer Review → Release</li>
    <li>Create style guide for AI outputs (tonality, structure, checkpoints)</li>
    <li>Establish review rounds (30 min./week for best practices)</li>
    <li>Introduce quality metrics: first-pass quality, rework rate</li>
    <li>Evaluate and implement first automations if applicable</li>
  </ul>
  <p><strong>🎯 Milestone:</strong> Documented workflow, first-pass quality > 70%.</p>

  <h3>Phase 3: Consolidation (Week 11–13)</h3>
  <p><strong>Goal:</strong> Measure results, prepare scaling.</p>
  <ul>
    <li>Impact measurement: time, quality, error rate, satisfaction</li>
    <li>Document lessons learned: What works, what doesn't?</li>
    <li>Decision: Stabilize / Expand / Deepen</li>
    <li>Create and prioritize backlog for next use cases</li>
  </ul>
  <p><strong>🎯 Milestone:</strong> Clear decision, prioritized backlog for 12-month roadmap.</p>

  <h3>Expected Effects after 90 Days</h3>
  <ul>
    <li><strong>Time Savings:</strong> 20–30% on recurring tasks in the area</li>
    <li><strong>Quality:</strong> More consistent results through shared standards</li>
    <li><strong>Collaboration:</strong> Established review routines, shared knowledge</li>
    <li><strong>Scalability:</strong> Documented workflows for additional use cases</li>
    <li><strong>Decision Basis:</strong> Reliable data for investment decisions</li>
  </ul>

  <h3>Team Communication & Rollout Rituals</h3>
  <p>
    Successful AI adoption in your area requires structured communication and
    recurring formats that promote acceptance and skill development. Establish
    the following rituals:
  </p>
  <ul>
    <li><strong>AI Standup (15 min./week):</strong> Brief exchange at the start of
    each week: What did I try with AI? What worked? What challenges arose?
    The AI Owner moderates and collects topics for deeper exploration.</li>
    <li><strong>Establish Feedback Loop:</strong> Set up a dedicated channel
    (Slack channel, Teams group, or shared document) where participants share
    experiences, prompts, and tips. Low-barrier exchange accelerates learning.</li>
    <li><strong>Mini-Demos (30 min. every 2 weeks):</strong> One participant
    demonstrates a successful AI workflow live. Concrete use cases motivate
    more than theoretical training. Rotate presenters.</li>
    <li><strong>Acceptance Measures:</strong> Proactively address skeptics.
    Let them participate in selecting use cases. Show early successes
    transparently – nothing convinces more than measurable time savings among colleagues.</li>
    <li><strong>Structured Tool Onboarding:</strong> Create a 1-page guide for
    new participants: access, first steps, key prompts, contact person.
    This ensures no one gets left behind when joining later.</li>
  </ul>

  <h3>Documentation & Knowledge Repository</h3>
  <p>
    Knowledge that exists only in individual minds gets lost. Build a structured
    AI knowledge repository for your area from the beginning:
  </p>
  <ul>
    <li><strong>Create AI Handbook:</strong> A living document with best practices,
    proven prompts, quality criteria, and common mistakes. Monthly updates by
    the AI Owner, input from all participants.</li>
    <li><strong>Prompt Library:</strong> Collect all working prompt templates in
    a shared location (Notion, Confluence, SharePoint). Categorize by use case:
    text creation, research, analysis, email, etc.</li>
    <li><strong>Clarify Roles & Responsibilities:</strong>
      <ul>
        <li><em>AI Owner:</em> Coordinates standards, maintains knowledge repository,
        is first point of contact for questions.</li>
        <li><em>Participants:</em> Test workflows, provide feedback, share learnings.</li>
        <li><em>Quality Reviewer:</em> Reviews critical AI outputs before release.</li>
      </ul>
    </li>
    <li><strong>Document Lessons Learned:</strong> After each phase (Setup, Relief,
    Productive Use), briefly record: What did we learn? What would we do differently?
    These insights are invaluable for scaling.</li>
  </ul>
  <p>
    <strong>Tip:</strong> Keep documentation lean. 10 working prompts well-described
    are better than 50 untested templates without context.
  </p>

  {% else %}
  <h3>Phase 0: Setup (Week 1–2)</h3>
  <p><strong>Goal:</strong> Define pilot area and establish foundations.</p>
  <ul>
    <li>Select pilot area (one work area with high relief potential)</li>
    <li>Designate AI responsible (coordination, standards, contact person)</li>
    <li>Establish governance ground rules: What's allowed, what's not?</li>
    <li>Set up and document access for pilot area</li>
    <li>Create first templates for 2–3 prioritized use cases</li>
  </ul>
  <p><strong>🎯 Milestone:</strong> Pilot area ready to start, governance framework defined.</p>

  <h3>Phase 1: Relief (Week 3–5)</h3>
  <p><strong>Goal:</strong> Implement Quick Wins in pilot area.</p>
  <ul>
    <li>Deploy measures from "Immediate Measures" strategically (→ see Quick Wins)</li>
    <li>Pilot area trains each other (peer learning)</li>
    <li>Document and quantify first time savings</li>
    <li>Establish weekly short reviews in pilot area</li>
    <li>Set up feedback channel for questions and issues</li>
  </ul>
  <p><strong>🎯 Milestone:</strong> Pilot area actively using AI, measurable relief documented.</p>

  <h3>Phase 2: Productive Use (Week 6–10)</h3>
  <p><strong>Goal:</strong> Establish scalable processes for {{BRANCHE_LABEL}}.</p>
  <ul>
    <li>Document Standard Operating Procedures (SOPs) for AI workflows</li>
    <li>Establish QA process: Input → AI → Expert review → Release</li>
    <li>Define style guide and quality criteria for {{HAUPTLEISTUNG}}</li>
    <li>Develop training concept for rollout to additional areas</li>
    <li>Define KPIs: time savings, quality, usage rate</li>
  </ul>
  <p><strong>🎯 Milestone:</strong> SOPs documented, training concept ready, KPIs defined.</p>

  <h3>Phase 3: Consolidation (Week 11–13)</h3>
  <p><strong>Goal:</strong> Rollout decision and scaling plan.</p>
  <ul>
    <li>Business case validation based on pilot data (→ see Business Case)</li>
    <li>Summarize lessons learned from pilot area</li>
    <li>Decision: Rollout to additional areas? Yes/No/Adjustments?</li>
    <li>Create prioritized backlog for 12-month rollout</li>
    <li>Prepare resource planning for scaling</li>
  </ul>
  <p><strong>🎯 Milestone:</strong> Management decision made, rollout plan established.</p>

  <h3>Expected Effects after 90 Days</h3>
  <ul>
    <li><strong>Time Savings:</strong> 20–35% on routine tasks in pilot area</li>
    <li><strong>Quality:</strong> Standardized processes, documented quality criteria</li>
    <li><strong>Governance:</strong> Clear rules, responsibilities, documentation</li>
    <li><strong>Scalability:</strong> Proven SOPs and training concept for rollout</li>
    <li><strong>Business Case:</strong> Validated ROI assumptions based on real pilot data</li>
    <li><strong>Decision Basis:</strong> Solid foundation for management decision</li>
  </ul>

  <h3>Change Communication at Leadership Level</h3>
  <p>
    AI adoption in a mid-sized company requires strategic communication at
    leadership level. Without active involvement of decision-makers, even
    successful pilot projects fail due to lack of support for scaling.
  </p>
  <ul>
    <li><strong>Conduct Stakeholder Mapping:</strong> Identify all relevant
    decision-makers and influencers: executive leadership, area leads, works
    council (if applicable), IT leadership. Understand their perspective: Who
    sees opportunities, who has concerns? Adapt your communication accordingly.</li>
    <li><strong>Communicate Opportunities & Risks Transparently:</strong> Present
    a balanced analysis: What specific efficiency gains are realistic? What risks
    (data privacy, quality, dependencies) exist and how are they addressed?
    Honest communication builds trust and prevents later disappointments.</li>
    <li><strong>Involve Employee Representatives:</strong> If a works council exists,
    bring them on board early. Clarify together: What data is processed? Are there
    impacts on jobs or job content? Proactive involvement prevents resistance and delays.</li>
    <li><strong>Regular Status Updates:</strong> Establish a monthly brief report
    to executive leadership: pilot progress, milestones reached, measured effects,
    next steps. No surprises – continuous transparency is key to sustained
    management support.</li>
    <li><strong>Leverage Success Stories:</strong> Document concrete successes from
    the pilot area with measurable numbers. These "proof points" are your best
    argument basis for the rollout decision.</li>
  </ul>

  <h3>KPI Framework for Work Areas</h3>
  <p>
    A structured KPI framework enables objective assessment of AI usage across
    different work areas. Define metrics that can be captured without
    interpretation ambiguity:
  </p>
  <ul>
    <li><strong>Efficiency KPIs:</strong>
      <ul>
        <li><em>Time Savings per Process:</em> Comparison of processing time with
        and without AI support (target: 20–35% reduction)</li>
        <li><em>Throughput:</em> Number of processes handled per time unit
        (make increases measurable)</li>
        <li><em>Automation Rate:</em> Proportion of tasks that run fully or
        partially automated</li>
      </ul>
    </li>
    <li><strong>Quality KPIs:</strong>
      <ul>
        <li><em>First-Pass Quality Rate:</em> Proportion of AI outputs usable
        without rework (target: >70%)</li>
        <li><em>Error Rate:</em> Number of corrections or complaints per 100
        AI-assisted processes</li>
        <li><em>Customer Satisfaction:</em> Quality assessment by internal or
        external recipients</li>
      </ul>
    </li>
    <li><strong>Compliance KPIs:</strong>
      <ul>
        <li><em>Governance Adherence:</em> Proportion of processes reviewed
        according to defined standards</li>
        <li><em>Data Privacy Compliance:</em> Zero tolerance for violations,
        document regular audits</li>
        <li><em>Documentation Level:</em> Completeness of process documentation
        for regulatory requirements</li>
      </ul>
    </li>
    <li><strong>Adoption KPIs:</strong>
      <ul>
        <li><em>Usage Rate:</em> Proportion of employees actively using AI tools</li>
        <li><em>Training Coverage:</em> Percentage of trained employees in pilot area</li>
        <li><em>Feedback Score:</em> Regular satisfaction survey (NPS or 1–5 scale)</li>
      </ul>
    </li>
  </ul>
  <p>
    <strong>Implementation Note:</strong> Start with 3–5 core KPIs you can measure
    reliably. Only expand the framework once baseline measurement works. Avoid KPI
    overload – fewer, meaningful metrics are more valuable than extensive dashboards
    without consequences.
  </p>
  {% endif %}

  <h3>Risk Mitigation During Rollout</h3>
  <p>
    {% if COMPANY_SIZE == "solo" %}
    Start with low-criticality tasks to build experience. Always maintain a manual
    review step for important outputs. Document early error sources to iteratively
    improve your prompts and refine quality over time.
    {% elif COMPANY_SIZE == "team" %}
    Begin with clearly defined pilot tasks within your area. Establish peer reviews
    as a fixed part of the workflow. Collect feedback systematically and adjust
    templates based on concrete experiences.
    {% else %}
    Limit the initial pilot scope to non-critical processes. Define clear escalation
    paths for unexpected results. Conduct regular retrospectives and only scale to
    additional areas after validated quality.
    {% endif %}
  </p>

  <p class="small muted">
    This roadmap references Quick Wins (→ see Immediate Measures) and
    Tools (→ see AI Stack). Details on Change Management → see Organizational Change.
  </p>
</section>
