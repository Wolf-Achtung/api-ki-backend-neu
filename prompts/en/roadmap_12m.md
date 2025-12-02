Developer:
<!-- roadmap_12m.md – v7.0 PLATIN+ STABILIZED
     Respond exclusively with valid HTML. No Markdown fences.
-->

> **PLATIN+ – Section "12-Month Roadmap"**
> Minimum length: **at least 900 words**
> Structure: 4 sections (Months 1-3, 4-6, 7-12, Conclusion & Sustainability) with clear customer-side responsibilities.
>
> Write directly PDF-ready prose (only HTML paragraphs and subheadings), **no placeholders, no meta-comments, no references to word count or "this section..."**.

---

### VARIABLES (from Briefing)

- **{{BRANCHE_LABEL}}** – Industry label
- **{{UNTERNEHMENSGROESSE_LABEL}}** – Company size
- **{{HAUPTLEISTUNG}}** – Core service/main process
- **COMPANY_SIZE** – `solo` | `team` | `kmu`
- Business Case variables: CAPEX, OPEX, Payback, ROI_12M

---

### SIZE-AWARE LOGIC (STRICTLY FOLLOW!)

**COMPANY_SIZE == "solo":**
- NEVER: "department", "build team", "hire staff", "HR", "project team"
- INSTEAD: "own work methods", "personal workflows", "self-review", "own competence"
- Roles: "owner", "yourself", "sole proprietor"

**COMPANY_SIZE == "team":**
- Small groups (2-10 people), informal structures
- "Team members", "AI coordinator", "shared standards"

**COMPANY_SIZE == "kmu":**
- Formal structures, departments, governance
- "Department heads", "governance board", "cross-functional"

---

### REQUIRED STRUCTURE (strictly follow)

1. **Months 1-3 – Foundation & Pilot Setup**
   - At least 200 words prose
   - Goal: Create foundations for AI usage, realize first Quick Wins
   - Describe: Use-case prioritization, build prompt library, initial quality standards
   - Governance aspect: First rules for AI output, data protection basics
   - Responsible: {size-aware role designation}
   - KPIs: 2-3 measurable success criteria

2. **Months 4-6 – Piloting & Quality Standards**
   - At least 200 words prose
   - Goal: Anchor AI processes in daily operations, establish stable workflows
   - Describe: Workflow integration, expand prompt library, build monitoring
   - Governance aspect: Review processes, incident handling, training material
   - Responsible: {size-aware role designation}
   - KPIs: Time savings, quality metrics, usage rate

3. **Months 7-12 – Expansion, Scaling & Governance**
   - At least 250 words prose
   - Goal: Multiply successful workflows, open new areas
   - Describe: Scaling to additional use cases, systematic success measurement
   - Governance aspect: Finalize governance framework, audit preparation, compliance
   - Responsible: {size-aware role designation}
   - KPIs: ROI demonstrable, use case count, governance maturity level

4. **Conclusion & Sustainability (12-Month Review)**
   - At least 200 words prose
   - Goal: Consolidate learnings, prepare Roadmap 2.0
   - Describe: Annual review, strategic development, budget for year 2
   - Governance aspect: Compliance status, lessons learned, Roadmap 2.0
   - Responsible: {size-aware role designation}
   - Outlook on year 2

---

### FORMAT RULES

- **HTML only:** `<h3>`, `<h4>`, `<p>` – no lists, no bullets
- Each section begins with `<h3>` for the phase
- Structure sub-aspects with `<h4>`
- Prose in `<p>` tags
- At end: Brief closing paragraph on overall assessment

---

### STYLE GUIDELINES

- Factual, concrete, no filler phrases
- Clear reference to {{BRANCHE_LABEL}}, {{HAUPTLEISTUNG}} and business case
- Realistic time estimates and resource estimates
- Clearly name customer-side responsibilities
- No developer language, no placeholders, no meta-comments
- No mention of word count in output

---

<section class="section roadmap-12m">
  <h2>Strategic 12-Month Roadmap</h2>

  <p>
    This roadmap shows how a company of size <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>
    can sustainably establish and expand AI-powered work methods in
    <strong>{{HAUPTLEISTUNG}}</strong> within one year. It builds on the
    experiences of the first 90 days, leverages industry-typical workflows from
    <strong>{{BRANCHE_LABEL}}</strong>, and combines quick wins with strategic depth.
  </p>

  <!-- Phase 1: Months 1-3 -->
  <h3>Months 1-3: Foundation & Pilot Setup</h3>
  <!-- At least 200 words prose with goal, measures, governance, KPIs -->

  <!-- Phase 2: Months 4-6 -->
  <h3>Months 4-6: Piloting & Quality Standards</h3>
  <!-- At least 200 words prose with goal, measures, governance, KPIs -->

  <!-- Phase 3: Months 7-12 -->
  <h3>Months 7-12: Expansion, Scaling & Governance</h3>
  <!-- At least 250 words prose with goal, measures, governance, KPIs -->

  <!-- Phase 4: Conclusion -->
  <h3>Conclusion & Sustainability (12-Month Review)</h3>
  <!-- At least 200 words prose with annual review, learnings, Roadmap 2.0 -->

  <p class="small muted">
    This 12-month roadmap creates the foundation for sustainable, strategically anchored
    AI usage in <strong>{{HAUPTLEISTUNG}}</strong>. It combines quick operational wins
    with long-term strategic development and prepares scaling for year 2.
  </p>
</section>

<!-- PLATIN+ REINFORCEMENT: This section MUST contain at least 900 words.
     Check your output: Count the words and expand each phase with additional
     details on goals, measures, governance, and KPIs if the minimum length is not reached.
     NEVER shorten – always deliver complete, detailed content per phase. -->
