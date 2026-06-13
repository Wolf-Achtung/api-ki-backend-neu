<!-- G20 – AI‑Stack Summary Card (EN) -->
OUTPUT RULE (mandatory): Write exclusively declarative report sentences. Do not use direct address, questions, meta‑comments, hints about missing inputs or imperatives. Never begin with verbs such as “describe”, “write”, “answer”, “help”. Do not refer to the reader or to “messages/questions”.

START FORMAT: Begin with a neutral noun phrase (e.g. “The current state…”, “The recommended approach…”, “The strategic framework…”).

NOT ALLOWED: “how can I help”, “I see no question”, “describe your concern”, “you have not asked a question”, “please”, “question”, “message”.

IMPORTANT: Do not use any form of address, questions or assistant/chat language. Avoid meta‑comments about missing inputs (e.g. “I don’t see a question”). Write solely in neutral report language.

<!-- G20 – AI‑Stack Summary Card (EN) -->

## Task
Create a compact, C‑level‑appropriate **AI‑Stack Summary Card** as an HTML block without `<h1>` or `<h2>` tags. The block will be placed directly after the executive summary in a PDF report.

### Context sources (available above):
- Questionnaire evaluation
- Branch profile (including {{BRANCH_SHORT_LABEL}})
- Tools Engine 3.0 results
- Funding analysis (funding programmes)
- Starter kit / quick wins
- Business case metrics (ROI, payback, time savings per month)

### Important guidelines
- Write in a factual, professional, motivating tone.
- Neutral formulations – no “you” or “we”.
- Output only the HTML structure, no introduction.

### Content structure (5 fixed building blocks)

1. **Top 3 tools** (score-based from the Tools Engine 3.0)
   - The three most relevant tools from the available context.
   - For each tool provide:
     - **Name**
     - **Category**: Automation / Analysis / Collaboration / Compliance / Research
     - **One‑line benefit** (exactly one sentence, clear and concrete, without buzzwords)

2. **Top‑2 funding programmes** (from funding alignment)
   - Two programmes that are particularly well suited to the profile (size + industry + project).
   - For each programme:
     - **Name**
     - Estimated funding rate **OR** a clear relevance indicator
     - One‑line statement on the added value in the context of the planned AI adoption

3. **Starter kit short path** (condensed starter kit)
   - Exactly three steps:
     1. **Setup** (create foundations)
     2. **Workflow** (concrete integration into processes)
     3. **Optimisation** (fine‑tuning, standards, governance)
   - Each step: 1–2 sentences, clearly understandable and implementation‑oriented.

4. **3 most important business case KPIs**
   - Realistic values from the business case:
     - **ROI rate** (in %)
     - **Payback** (months)
     - **Time savings per month** (in hours or euros)
   - Briefly comment on what these KPIs mean for the decision level.

5. **Branch badge + risk indicator**
   - **Branch label**: {{BRANCH_SHORT_LABEL}}.
   - **AI‑Act risk class**: use the canonical value {{AI_ACT_RISK_LEVEL}} EXACTLY
     (exactly one of: minimal / limited / high-risk). Do NOT guess and do NOT
     translate it into a custom low/medium/high scale — the value MUST match the
     cover and the AI‑Act compact section.
   - Badge class matching the value: minimal → risk-low, limited → risk-medium,
     high-risk → risk-high.
   - 1–2 sentences explaining what this risk class means in concrete terms.

### Size‑aware logic

- **SOLO (one‑person setup):**
  - Focus on feasibility, concentration, few tools and clear priorities.
  - Tailor the starter kit to personal work style and time savings.
  - Text length: **at least 150 words**.
- **TEAM (small teams, 2–15 people):**
  - Focus on collaboration, roles, first governance approaches and simple standards.
  - Choose tools and funding programmes so that team workflows benefit.
  - Text length: **at least 180 words**.
- **SME:**
  - Focus on scaling, standardisation, responsibilities and risk management.
  - Present funding programmes and KPIs strategically and investment‑oriented.
  - Text length: **at least 200 words**.

**Maximum total length:** 350 words (all building blocks combined).

### HTML requirements & design (G21 PLATIN++)

**Available CSS classes:**
- `.pair-card` – card for individual tools or funding programmes
- `.pair-card-icon` – icon container (appropriate SVG icons)
- `.pair-card-content` – main content of the card
- `.pair-card-name` – name of the tool/programme (bold)
- `.pair-card-category` – category badge
- `.pair-card-description` – description (one line)

- `.step-cards` – grid for three steps (starter kit)
- `.step-card` – individual step card
- `.step-card-number` – step number (1, 2, 3)
- `.step-card-title` – title of the step
- `.step-card-body` – description of the step

- `.kpi-triple` – grid for three KPIs
- `.kpi` – single KPI block
- `.kpi-label` – KPI designation
- `.kpi-value` – KPI value (large, bold, blue)
- `.kpi-sub` – additional information

- `.badge-block` – container for branch + risk
- `.badge-block-item` – single badge
- `.badge-block-label` – label
- `.badge-block-value` – value
- `.risk-low`, `.risk-medium`, `.risk-high` – risk colours

**SVG icons (use inline):**
- **Automation:** `<svg viewBox="0 0 24 24" fill="none"><path d="M9.75 17L3.75 11L9.75 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M14.25 17L20.25 11L14.25 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`
- **Analysis:** `<svg viewBox="0 0 24 24" fill="none"><path d="M3 13L9 7L13 11L21 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M21 9V3H15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`
- **Collaboration:** `<svg viewBox="0 0 24 24" fill="none"><circle cx="9" cy="7" r="4" stroke="currentColor" stroke-width="1.5"/><circle cx="17" cy="17" r="3" stroke="currentColor" stroke-width="1.5"/><path d="M13 12H19C20.1046 12 21 12.8954 21 14V14.5M3 18V17C3 14.7909 4.79086 13 7 13H9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`
- **Funding:** `<svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.5"/><path d="M12 6V18M15 9C15 7.34315 13.6569 6 12 6C10.3431 6 9 7.34315 9 9C9 10.6569 10.3431 12 12 12C13.6569 12 15 13.3431 15 15C15 16.6569 13.6569 18 12 18C10.3431 18 9 16.6569 9 15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`

### Structure example

```html
<div class="ki-stack-summary">
  <!-- Top‑3 Tools -->
  <div class="stack-section">
    <p class="stack-section-title"><strong>Top‑3 recommended tools</strong></p>
    <div class="pair-card">
      <div class="pair-card-icon">[SVG Icon]</div>
      <div class="pair-card-content">
        <p class="pair-card-name"><strong>Tool name</strong></p>
        <span class="pair-card-category">Automation</span>
        <p class="pair-card-description">Short description in one sentence.</p>
      </div>
    </div>
  </div>
  <!-- Funding programmes -->
  <div class="stack-section">
    <p class="stack-section-title"><strong>Suitable funding programmes</strong></p>
    [2 pair-cards with funding icon …]
  </div>
  <!-- Starter kit -->
  <div class="stack-section">
    <p class="stack-section-title"><strong>Starter kit in 3 steps</strong></p>
    <div class="step-cards">
      <div class="step-card">
        <div class="step-card-number">1</div>
        <p class="step-card-title"><strong>Setup</strong></p>
        <div class="step-card-body">Description …</div>
      </div>
    </div>
  </div>
  <!-- KPIs -->
  <div class="stack-section">
    <p class="stack-section-title"><strong>Business case KPIs</strong></p>
    <div class="kpi-triple">
      <div class="kpi">
        <span class="kpi-label">ROI</span>
        <span class="kpi-value">45%</span>
        <span class="kpi-sub">after 12 months</span>
      </div>
    </div>
  </div>
  <!-- Branch + Risk -->
  <div class="stack-section">
    <div class="badge-block">
      <div class="badge-block-item">
        <span class="badge-block-label">Industry</span>
        <span class="badge-block-value">{{BRANCH_SHORT_LABEL}}</span>
      </div>
      <div class="badge-block-item risk-low">
        <span class="badge-block-label">AI Act risk</span>
        <span class="badge-block-value">minimal</span>
      </div>
    </div>
    <p>Explanation of the risk level …</p>
  </div>
</div>
```

### Output format

Return **only** the finished HTML block with the five building blocks:
1. Top 3 tools
2. Top‑2 funding programmes
3. Starter kit short path
4. Business case KPIs
5. Branch badge + AI‑Act risk level

### Zero‑leak policy (N4.6)

**Forbidden – never use:**
- Questions to the reader
- Requests
- Assistant language
- Offers
- Interactive elements
- Placeholders (except defined ones)
- Meta comments

The output is a **final report section**, not a conversation.