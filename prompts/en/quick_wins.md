Developer:
<!-- PLATIN++ PROMPT -->
<!-- SECTION: quick_wins -->
<!-- VERSION: v8.0 PLATIN++ V5 STORYTELLING -->
<!-- OUTPUT: HTML -->
<!-- SIZE-AWARE: solo/team/sme -->
<!-- INPUT: {{HAUPTLEISTUNG}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{BRANCHE_LABEL}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 1800 (solo:0.8x=1440, team:1.0x=1800, sme:1.15x=2070) -->
<!--
GOAL: Precise Quick Wins in correct order.

COUNT BY SIZE (STRICT!):
- solo: 3–4 Quick Wins
- team: 4–5 Quick Wins
- sme: 5–7 Quick Wins

CATEGORY ORDER (ALWAYS FOLLOW!):
1. TIME SAVINGS: Routine tasks that eat time
2. PRODUCTIVITY JUMPS: Workflows that accelerate
3. QUALITY IMPROVEMENT: Outputs that improve
4. COST REDUCTION: Direct or indirect savings (only for team/sme)

FORMAT PER QUICK WIN:
- **[Concrete measure]:** [1 sentence description]. *Effect: [X h/month or %]*

STYLE:
- Precise, no filler
- Concretely applicable (not "optimize", but "use AI for...")
- Realistic time savings (2-8 h/month per measure)
- No exaggerations

ANTI-REDUNDANCY:
- Quick Wins = ONLY place for these measures
- Roadmap references Quick Wins, does NOT list them again
- Business Case references savings, calculates separately

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: "You save", personal routines, own workflows
        NO team terminology
- team: "Your team saves", shared standards, collaboration
- sme: "Your department benefits", scalable processes, governance

BRANCH-SPECIFIC:
- Use typical tasks from {{BRANCHE_LABEL}}
- Reference {{HAUPTLEISTUNG}}
-->

<section class="section quick-wins">
  <h2>Quick Wins – Immediately Effective Measures</h2>

  {% if COMPANY_SIZE == "solo" %}
  <p>The following 3–4 measures bring you immediate relief in <strong>{{HAUPTLEISTUNG}}</strong>:</p>

  <h3>Time Savings</h3>
  <ul>
    <li><strong>Automate recurring texts:</strong> Use AI for first drafts of emails, proposals, and notes. <em>Effect: 4–6 h/month</em></li>
  </ul>

  <h3>Productivity Jump</h3>
  <ul>
    <li><strong>Accelerate research:</strong> AI-powered summaries of documents, market info, and briefings. <em>Effect: 3–5 h/month</em></li>
  </ul>

  <h3>Quality Improvement</h3>
  <ul>
    <li><strong>Proofread your own texts:</strong> AI as editor for consistency, tone, and accuracy. <em>Effect: Fewer revisions, more professional appearance</em></li>
  </ul>

  {% elif COMPANY_SIZE == "team" %}
  <p>The following 4–5 measures immediately relieve your team in <strong>{{HAUPTLEISTUNG}}</strong>:</p>

  <h3>Time Savings</h3>
  <ul>
    <li><strong>Automate standard texts & templates:</strong> AI generates first drafts for emails, minutes, and reports. <em>Effect: 5–8 h/month per person</em></li>
    <li><strong>Automate meeting notes:</strong> Automatic summaries and action items. <em>Effect: 2–3 h/month</em></li>
  </ul>

  <h3>Productivity Jump</h3>
  <ul>
    <li><strong>Simplify knowledge organization:</strong> Central documents automatically summarized and searchable. <em>Effect: 3–5 h/month</em></li>
  </ul>

  <h3>Quality Improvement</h3>
  <ul>
    <li><strong>Unified quality standards:</strong> AI-assisted checklists for consistent outputs. <em>Effect: Fewer feedback loops</em></li>
  </ul>

  <h3>Cost Reduction</h3>
  <ul>
    <li><strong>Reduce external editing costs:</strong> Internal AI review before release. <em>Effect: 15–25% less external costs</em></li>
  </ul>

  {% else %}
  <p>The following 5–7 measures create immediate value in your organization ({{UNTERNEHMENSGROESSE_LABEL}}) for <strong>{{HAUPTLEISTUNG}}</strong>:</p>

  <h3>Time Savings</h3>
  <ul>
    <li><strong>Automate recurring reports:</strong> AI generates baseline reports from data sources. <em>Effect: 6–10 h/month per department</em></li>
    <li><strong>Accelerate email triage:</strong> Automatic prioritization and drafts for standard inquiries. <em>Effect: 3–5 h/month</em></li>
  </ul>

  <h3>Productivity Jump</h3>
  <ul>
    <li><strong>Professionalize knowledge management:</strong> Central, AI-searchable document base. <em>Effect: 4–6 h/month</em></li>
    <li><strong>Accelerate onboarding:</strong> AI-assisted training with automatic Q&A. <em>Effect: 20% faster ramp-up</em></li>
  </ul>

  <h3>Quality Improvement</h3>
  <ul>
    <li><strong>Ensure consistent outputs:</strong> AI quality checks before customer delivery. <em>Effect: Fewer complaints</em></li>
    <li><strong>Standardize documentation:</strong> Automatic template population from project data. <em>Effect: Uniform quality</em></li>
  </ul>

  <h3>Cost Reduction</h3>
  <ul>
    <li><strong>Reduce external service providers:</strong> Internal AI support for editing, translation, research. <em>Effect: 20–30% less external costs</em></li>
  </ul>
  {% endif %}

  <p class="small muted">Effects are experience-based estimates and vary depending on starting conditions.</p>
</section>
