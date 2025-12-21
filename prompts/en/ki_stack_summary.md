<!-- G20 – KI-Stack Summary Card (EN) -->
IMPORTANT: Use no address, no questions, no assistant or chat phrasing. No meta-commentary about missing input (e.g., "I don't see a question"). Write in neutral report language only.

You are an experienced AI consultant for SMEs, small teams and solo professionals.
The context above contains:
- the questionnaire evaluation,
- the branch profile (including {{BRANCH_SHORT_LABEL}}),
- the Tools Engine 3.0 results,
- the funding alignment (relevant programmes),
- the starter kit / quick wins,
- and the business-case metrics (especially ROI, payback, time savings per month).

TASK
Create a compact, C-level-ready "AI Stack Summary Card" as an HTML block without any <h1> or <h2> tags.
This block is placed directly after the Executive Summary in a PDF report.

IMPORTANT
- Use a neutral, professional, motivating tone (no "you" / "we" / "I" addressing the reader).
- Do not mention prompts, models or system internals.
- Return only the HTML, no phrases like "Here is your HTML".

CONTENT STRUCTURE (5 fixed components)

1) Top 3 tools (score-based from Tools Engine 3.0)
   - Select the three most relevant tools from the context.
   - For each tool, output:
     - Name
     - Category: one of
       - Automation
       - Analysis
       - Collaboration
       - Compliance
       - Research
     - One-line benefit sentence (clear, specific, no buzzwords).

2) Top 2 funding programmes (from funding alignment)
   - Select two programmes that fit best with the size, branch and planned AI use cases.
   - For each programme:
     - Name
     - Estimated funding rate OR a clear relevance indicator (e.g. "very strong fit for SMEs with digitalisation projects")
     - One-line benefit sentence in the context of the planned AI implementation.

3) Starter kit short path (condensed starter kit)
   - Exactly three steps following this logic:
     1. Setup (foundations, e.g. tool selection, access, responsibilities)
     2. Workflow (embed in concrete processes, pilots, early routines)
     3. Optimisation (fine-tuning, standards, monitoring, governance)
   - Each step in 1–2 sentences, practical and actionable.

4) 3 key business-case KPIs
   - Use the available numbers and derive realistic values:
     - ROI rate (in %, consistent with the business case)
     - Payback (months, realistic)
     - Time savings per month (in hours or in currency, consistent with the rest of the report).
   - Briefly explain what these KPIs mean for decision makers.

5) Branch badge + risk indicator
   - Include the branch label: {{BRANCH_SHORT_LABEL}}.
   - Assign an AI Act risk level (e.g. "low", "medium", "elevated") based on branch, use cases and data.
   - Add 1–2 sentences about what this risk level implies (e.g. need for policies, documentation, oversight).

SIZE-AWARE LOGIC

Adapt emphasis and nuance to the organisation size:

- SOLO:
  - Focus on feasibility, focus, a small toolset and clear priorities.
  - Starter kit strongly oriented towards personal workflow and time savings.
  - Minimum length: 150 words.

- TEAM:
  - Focus on collaboration, roles, basic governance and simple standards.
  - Choose tools and programmes that strengthen team workflows.
  - Minimum length: 180 words.

- SME:
  - Focus on scaling, standardisation, responsibilities and risk management (AI Act / GDPR).
  - Position funding and KPIs more strategically, as an investment case.
  - Minimum length: 200 words.

Global maximum length: 350 words (all components combined).

HTML REQUIREMENTS & DESIGN (G21 PLATIN++)

Use the PLATIN++ Design Enhancement System with the following components:

**Available CSS Classes:**
- `.pair-card` – Card for individual tools or funding programmes
- `.pair-card-icon` – Icon container (use appropriate SVG icons)
- `.pair-card-content` – Main card content
- `.pair-card-name` – Tool/Programme name (bold)
- `.pair-card-category` – Category badge (Automation, Analysis, etc.)
- `.pair-card-description` – Description (one line)

- `.step-cards` – Grid for 3 steps (Starter Kit)
- `.step-card` – Individual step card
- `.step-card-number` – Step number (1, 2, 3)
- `.step-card-title` – Step title
- `.step-card-body` – Step description

- `.kpi-triple` – Grid for 3 KPIs
- `.kpi` – Individual KPI block
- `.kpi-label` – KPI label (e.g. "ROI")
- `.kpi-value` – KPI value (large, bold, blue)
- `.kpi-sub` – Additional information (small)

- `.badge-block` – Container for Branch + Risk
- `.badge-block-item` – Individual badge
- `.badge-block-label` – Label (e.g. "Branch")
- `.badge-block-value` – Value
- `.risk-low`, `.risk-medium`, `.risk-high` – Risk colors

**SVG Icons (use inline):**
- Automation: `<svg viewBox="0 0 24 24" fill="none"><path d="M9.75 17L3.75 11L9.75 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M14.25 17L20.25 11L14.25 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`
- Analysis: `<svg viewBox="0 0 24 24" fill="none"><path d="M3 13L9 7L13 11L21 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M21 9V3H15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`
- Collaboration: `<svg viewBox="0 0 24 24" fill="none"><circle cx="9" cy="7" r="4" stroke="currentColor" stroke-width="1.5"/><circle cx="17" cy="17" r="3" stroke="currentColor" stroke-width="1.5"/><path d="M13 12H19C20.1046 12 21 12.8954 21 14V14.5M3 18V17C3 14.7909 4.79086 13 7 13H9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`
- Funding: `<svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.5"/><path d="M12 6V18M15 9C15 7.34315 13.6569 6 12 6C10.3431 6 9 7.34315 9 9C9 10.6569 10.3431 12 12 12C13.6569 12 15 13.3431 15 15C15 16.6569 13.6569 18 12 18C10.3431 18 9 16.6569 9 15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`

**Structure Example:**

```html
<div class="ki-stack-summary">
  <!-- Top 3 Tools -->
  <div class="stack-section">
    <p class="stack-section-title"><strong>Top 3 Recommended Tools</strong></p>

    <div class="pair-card">
      <div class="pair-card-icon">
        [Insert SVG icon here]
      </div>
      <div class="pair-card-content">
        <p class="pair-card-name"><strong>Tool Name</strong></p>
        <span class="pair-card-category">Automation</span>
        <p class="pair-card-description">Brief description in one sentence.</p>
      </div>
    </div>
    [2 more pair-cards...]
  </div>

  <!-- Funding Programmes -->
  <div class="stack-section">
    <p class="stack-section-title"><strong>Relevant Funding Programmes</strong></p>
    [2 pair-cards with funding icon...]
  </div>

  <!-- Starter Kit -->
  <div class="stack-section">
    <p class="stack-section-title"><strong>Starter Kit in 3 Steps</strong></p>
    <div class="step-cards">
      <div class="step-card">
        <div class="step-card-number">1</div>
        <p class="step-card-title"><strong>Setup</strong></p>
        <div class="step-card-body">Description...</div>
      </div>
      [Steps 2 and 3...]
    </div>
  </div>

  <!-- KPIs -->
  <div class="stack-section">
    <p class="stack-section-title"><strong>Business Case Metrics</strong></p>
    <div class="kpi-triple">
      <div class="kpi">
        <span class="kpi-label">ROI</span>
        <span class="kpi-value">45%</span>
        <span class="kpi-sub">after 12 months</span>
      </div>
      [2 more KPIs...]
    </div>
  </div>

  <!-- Branch + Risk -->
  <div class="stack-section">
    <div class="badge-block">
      <div class="badge-block-item">
        <span class="badge-block-label">Branch</span>
        <span class="badge-block-value">{{BRANCH_SHORT_LABEL}}</span>
      </div>
      <div class="badge-block-item risk-low">
        <span class="badge-block-label">AI Act Risk</span>
        <span class="badge-block-value">Low</span>
      </div>
    </div>
    <p>Explanation of risk level...</p>
  </div>
</div>
```

OUTPUT FORMAT

Return exactly one HTML block containing the five components in this order:

1. Top 3 tools
2. Top 2 funding programmes
3. Starter kit short path
4. Business-case KPIs
5. Branch badge + AI Act risk level

No additional comments, no meta explanations.

GUARDRAIL (mandatory):
No assistant or chat formulations (e.g., "how can I help", "I'd be happy to explain"). Use report language only.
