Developer:
<!-- roadmap_90d.md – v6.0 PLATIN+ STREAMLINED
     Goal: 6 phases with 80-100 words each (= 500-700 words total).
     Respond exclusively with valid HTML. No Markdown fences.

     STRUCTURE (6 Phases):
       Phase 1: Week 1-2 – Vision & Priorities
       Phase 2: Week 3-4 – Data Quality & Workflow Foundations
       Phase 3: Week 5-6 – Quick Wins & Initial Impact
       Phase 4: Week 7-8 – Quality Standards
       Phase 5: Week 9-10 – Monitoring & Iteration
       Phase 6: Week 11-13 – Consolidation & Scaling Preparation

     Per Phase REQUIRED:
       - Goal (1-2 sentences)
       - Deliverables (3-4 bullets)
       - Roles (size-aware)
       - KPI (1-2 measurable metrics)

     VARIABLES:
       {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, COMPANY_SIZE

     SIZE-AWARE (COMPANY_SIZE):
       solo: personal routines, own documentation, no teams
       team: roles, shared standards, coordination
       sme: departments, governance, pilot areas

     RULES:
       - Use industry-specific workflows from CONTEXT_BLOCK
       - Factual, concrete, no filler phrases
       - No placeholders, no developer language
-->

<section class="section roadmap-90d">
  <h2>Strategic 90-Day Roadmap</h2>

  <p>
    This roadmap shows how a company of size <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>
    can establish AI-powered work methods in <strong>{{HAUPTLEISTUNG}}</strong>
    in a structured way within 90 days. It leverages typical
    workflows, data types, and pain points of the <strong>{{BRANCHE_LABEL}}</strong> industry
    and combines quick impact with solid foundations.
  </p>

  <p>
    The following phases create clarity, reduce friction points, and ensure
    that AI delivers lasting, stable, and measurable value after 90 days.
  </p>

  <ol>

    <!-- PHASE 1 – Week 1-2 -->
    <li>
      <h3>Week 1-2: Vision, Use-Case Framework & Priorities</h3>
      <p><strong>Goal:</strong> Clearly define where AI in {{HAUPTLEISTUNG}} delivers the strongest benefit – based on industry-typical workflows and pain points.</p>
      <p><strong>Deliverables:</strong></p>
      <ul>
        <li>Focus definition: 1-2 prioritized tasks from {{BRANCHE_LABEL}} with high impact potential.</li>
        <li>Overview of industry-typical examples (5-10 cases).</li>
        <li>Mini checklist for quality, facts, tone, and approval.</li>
      </ul>
      <p><strong>Roles & Responsibilities:</strong><br>
        {% if COMPANY_SIZE == "solo" %}
          Personal prioritization & documentation.
        {% elif COMPANY_SIZE == "team" %}
          Team lead + AI owner.
        {% else %}
          Department + process owners.
        {% endif %}
      </p>
      <p><strong>KPI:</strong> Prioritized use cases + initial quality criteria defined.</p>
    </li>

    <!-- PHASE 2 – Week 3-4 -->
    <li>
      <h3>Week 3-4: Data Quality, Examples & Workflow Foundations</h3>
      <p><strong>Goal:</strong> Create a clean foundation so AI delivers stable, reliable results.</p>
      <p><strong>Deliverables:</strong></p>
      <ul>
        <li>Collection of typical cases (min. 10) from {{BRANCHE_LABEL}} – real, complete, structured.</li>
        <li>First stable workflow steps (Input → AI → Review → Approval).</li>
        <li>Definition of measurable criteria: completeness, accuracy, style.</li>
      </ul>
      <p><strong>Roles & Responsibilities:</strong><br>
        {% if COMPANY_SIZE == "solo" %}
          Own documentation.
        {% elif COMPANY_SIZE == "team" %}
          Joint quality definition in team.
        {% else %}
          Department + quality assurance.
        {% endif %}
      </p>
      <p><strong>KPI:</strong> Documented workflows + structured examples available.</p>
    </li>

    <!-- PHASE 3 – Week 5-6 -->
    <li>
      <h3>Week 5-6: Quick Wins & First Measurable Impact</h3>
      <p><strong>Goal:</strong> Noticeable relief through the first 1-2 AI-powered Quick Wins.</p>
      <p><strong>Deliverables:</strong></p>
      <ul>
        <li>Implementation of 1-2 highest-impact Quick Wins (industry-dependent: e.g., proposal draft, content draft, data review).</li>
        <li>Short tests: time savings, consistency, risk reduction.</li>
        <li>Learning/error list for later standards.</li>
      </ul>
      <p><strong>Roles & Responsibilities:</strong><br>
        {% if COMPANY_SIZE == "solo" %}
          Implementation by owner.
        {% elif COMPANY_SIZE == "team" %}
          AI owner + directly involved parties.
        {% else %}
          Department + process owners.
        {% endif %}
      </p>
      <p><strong>KPI:</strong> First impact (10-25% time savings).</p>
    </li>

    <!-- PHASE 4 – Week 7-8 -->
    <li>
      <h3>Week 7-8: Quality Standards & Consistent Work Methods</h3>
      <p><strong>Goal:</strong> Ensure reproducible results before processes are automated.</p>
      <p><strong>Deliverables:</strong></p>
      <ul>
        <li>Brief style guide for AI outputs (style, facts, expertise).</li>
        <li>Documentation of new work methods (input rules, review steps, approvals).</li>
        <li>Alignment between involved roles/departments.</li>
      </ul>
      <p><strong>Roles & Responsibilities:</strong><br>
        {% if COMPANY_SIZE == "solo" %}
          Self-review processes.
        {% elif COMPANY_SIZE == "team" %}
          Team review + quality responsible.
        {% else %}
          Department + quality assurance + data protection/IT.
        {% endif %}
      </p>
      <p><strong>KPI:</strong> Higher first-pass rate, fewer corrections.</p>
    </li>

    <!-- PHASE 5 – Week 9-10 -->
    <li>
      <h3>Week 9-10: Monitoring, Reporting & Iterative Improvement</h3>
      <p><strong>Goal:</strong> Make impact visible and derive optimizations.</p>
      <p><strong>Deliverables:</strong></p>
      <ul>
        <li>Simple monitoring (time, quality, errors, consistency).</li>
        <li>Brief report on progress and open challenges.</li>
        <li>Optimized templates and workflows.</li>
      </ul>
      <p><strong>Roles & Responsibilities:</strong><br>
        {% if COMPANY_SIZE == "solo" %}
          Personal analysis & adjustment.
        {% elif COMPANY_SIZE == "team" %}
          Owner + team review.
        {% else %}
          Department + controlling/IT if applicable.
        {% endif %}
      </p>
      <p><strong>KPI:</strong> Documented improvements + trend lines.</p>
    </li>

    <!-- PHASE 6 – Week 11-13 -->
    <li>
      <h3>Week 11-13: Decision, Consolidation & Scaling Preparation</h3>
      <p><strong>Goal:</strong> Decide on AI expansion based on real results.</p>
      <p><strong>Deliverables:</strong></p>
      <ul>
        <li>Assessment of AI suitability and impact for {{HAUPTLEISTUNG}}.</li>
        <li>Strategic decision: Stabilize / Expand / Deepen.</li>
        <li>Scaling backlog (use cases, automations, integrations).</li>
      </ul>
      <p><strong>Roles & Responsibilities:</strong><br>
        {% if COMPANY_SIZE == "solo" %}
          Management.
        {% elif COMPANY_SIZE == "team" %}
          Leadership + AI owner.
        {% else %}
          Management + department heads.
        {% endif %}
      </p>
      <p><strong>KPI:</strong> Prioritized backlog + clear decision for the next 6-12 months.</p>
    </li>

  </ol>

  <p class="small muted">
    This 90-day roadmap lays the structural foundation for a stable, secure,
    and impact-oriented introduction of AI in <strong>{{HAUPTLEISTUNG}}</strong>.
    It creates clear work methods, quick benefits, and a reliable basis for
    pilot projects and scaling in the following year.
  </p>
</section>
