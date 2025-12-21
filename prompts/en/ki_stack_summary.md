SYSTEM MODE (mandatory):
This is NOT a response to a request.
A finished report text is generated.
There is no dialogue, no question, no user.
The text is written directly into a PDF.

OUTPUT CONTRACT:
- Declarative report statements only
- No address, no questions, no meta commentary
- No imperatives
- No references to inputs, messages, or users
- No self-references

START FORMAT (mandatory):
Begin with a neutral noun-led sentence
(e.g. "The current state…", "The recommended approach…").

NOT ALLOWED:
"how can I help", "I don't see a question", "describe your request",
"you haven't asked", "please", "question".

<!-- G20 – KI-Stack Summary Card (EN) -->

TASK
Generate a compact, C-level-ready "AI Stack Summary Card" as an HTML block without any <h1> or <h2> tags.
This block is placed directly after the Executive Summary in a PDF report.

CONTEXT SOURCES (available above):
- Questionnaire evaluation
- Branch profile (including {{BRANCH_SHORT_LABEL}})
- Tools Engine 3.0 results
- Funding alignment (relevant programmes)
- Starter kit / quick wins
- Business-case metrics (ROI, payback, time savings per month)

IMPORTANT
- Use a neutral, professional, motivating tone.
- Neutral formulations only – no direct address.
- Return only the HTML, no introduction.

CONTENT STRUCTURE (5 fixed components)

1) Top 3 tools (score-based from Tools Engine 3.0)
   - The three most relevant tools from the context.
   - For each tool, output:
     - Name
     - Category: Automation / Analysis / Collaboration / Compliance / Research
     - One-line benefit sentence (clear, specific, no buzzwords).

2) Top 2 funding programmes (from funding alignment)
   - Two programmes that fit best with the size, branch and planned AI use cases.
   - For each programme:
     - Name
     - Estimated funding rate OR a clear relevance indicator
     - One-line benefit sentence in the context of the planned AI implementation.

3) Starter kit short path (condensed starter kit)
   - Exactly three steps:
     1. Setup (foundations)
     2. Workflow (embed in concrete processes)
     3. Optimisation (fine-tuning, standards, governance)
   - Each step in 1–2 sentences, practical and actionable.

4) 3 key business-case KPIs
   - Realistic values from the business case:
     - ROI rate (in %)
     - Payback (months)
     - Time savings per month (in hours or currency)
   - Brief explanation of what these KPIs mean for decision makers.

5) Branch badge + risk indicator
   - Branch label: {{BRANCH_SHORT_LABEL}}.
   - AI Act risk level (low / medium / elevated) based on branch, use cases and data.
   - 1–2 sentences about what this risk level implies.

SIZE-AWARE LOGIC

- SOLO:
  - Focus on feasibility, focus, a small toolset and clear priorities.
  - Starter kit oriented towards personal workflow and time savings.
  - Minimum length: 150 words.

- TEAM:
  - Focus on collaboration, roles, basic governance and simple standards.
  - Choose tools and programmes that strengthen team workflows.
  - Minimum length: 180 words.

- SME:
  - Focus on scaling, standardisation, responsibilities and risk management.
  - Position funding and KPIs more strategically, as an investment case.
  - Minimum length: 200 words.

Global maximum length: 350 words (all components combined).

HTML REQUIREMENTS & DESIGN (G21 PLATIN++)

**Available CSS Classes:**
- `.pair-card` – Card for individual tools or funding programmes
- `.pair-card-icon` – Icon container (appropriate SVG icons)
- `.pair-card-content` – Main card content
- `.pair-card-name` – Tool/Programme name (bold)
- `.pair-card-category` – Category badge
- `.pair-card-description` – Description (one line)

- `.step-cards` – Grid for 3 steps (Starter Kit)
- `.step-card` – Individual step card
- `.step-card-number` – Step number (1, 2, 3)
- `.step-card-title` – Step title
- `.step-card-body` – Step description

- `.kpi-triple` – Grid for 3 KPIs
- `.kpi` – Individual KPI block
- `.kpi-label` – KPI label
- `.kpi-value` – KPI value (large, bold, blue)
- `.kpi-sub` – Additional information

- `.badge-block` – Container for Branch + Risk
- `.badge-block-item` – Individual badge
- `.badge-block-label` – Label
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
    <h3 class="stack-section-title">Top 3 Recommended Tools</h3>
    <div class="pair-card">
      <div class="pair-card-icon">[SVG Icon]</div>
      <div class="pair-card-content">
        <h4 class="pair-card-name">Tool Name</h4>
        <span class="pair-card-category">Automation</span>
        <p class="pair-card-description">Brief description in one sentence.</p>
      </div>
    </div>
  </div>

  <!-- Funding Programmes -->
  <div class="stack-section">
    <h3 class="stack-section-title">Relevant Funding Programmes</h3>
  </div>

  <!-- Starter Kit -->
  <div class="stack-section">
    <h3 class="stack-section-title">Starter Kit in 3 Steps</h3>
    <div class="step-cards">
      <div class="step-card">
        <div class="step-card-number">1</div>
        <h4 class="step-card-title">Setup</h4>
        <div class="step-card-body">Description...</div>
      </div>
    </div>
  </div>

  <!-- KPIs -->
  <div class="stack-section">
    <h3 class="stack-section-title">Business Case Metrics</h3>
    <div class="kpi-triple">
      <div class="kpi">
        <span class="kpi-label">ROI</span>
        <span class="kpi-value">45%</span>
        <span class="kpi-sub">after 12 months</span>
      </div>
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

Return exactly one HTML block containing the five components:
1. Top 3 tools
2. Top 2 funding programmes
3. Starter kit short path
4. Business-case KPIs
5. Branch badge + AI Act risk level

<!-- ZERO-LEAK POLICY (N4.6) -->
FORBIDDEN – NEVER USE:
- No questions to the reader
- No calls to action
- No assistant language
- No offers
- No interactive elements
- No placeholders (except defined ones)
- No meta commentary

The output is a FINAL REPORT SECTION, not a conversation.
