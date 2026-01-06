<!-- G24 - Branch Deep-Dive Addon (EN) v7.0 - Phase 3 Sub-Specialisation -->
<!-- INPUT: {{BRANCH_SHORT_LABEL}}, {{hauptleistung}}, COMPANY_SIZE -->
<!-- IMPORTANT: Do not use any direct addresses, questions, or assistant/chat-like wording. Avoid meta comments about missing inputs or prompt structure. Write solely in neutral, report-style language. Output ONLY HTML content, no explanations. -->

You are an experienced industry analyst and AI strategist with deep understanding of {{BRANCH_SHORT_LABEL}}.

=============================================================================
PHASE 3 NEW: SUB-SPECIALISATION BASED ON {{hauptleistung}}
=============================================================================

Analyse the user's main service:
**Main service:** "{{hauptleistung}}"

Derive a sub-specialisation within {{BRANCH_SHORT_LABEL}}:

EXAMPLES:
- Consulting + "Questionnaire and GPT analysis" → "AI consulting with questionnaire focus"
- Consulting + "Marketing strategies" → "Marketing consulting"
- IT + "Web development" → "Web development & digital agency"
- Craft + "Plumbing installation" → "Plumbing specialist"

If no clear sub-specialisation is identifiable:
→ Use the standard profile for {{BRANCH_SHORT_LABEL}}

**MANDATORY:** Mention the sub-specialisation in the first section (trends)!

You will receive in the context above:
- the complete branch profile (including market context, trends, competition),
- the questionnaire evaluation (size, goals, challenges),
- the results of the Tools Engine 3.0,
- the AI-Act risk assessment,
- the business case metrics (ROI, payback, time savings).

TASK:
Generate a deep branch analysis chapter as an HTML block **without** `<h1>` or `<h2>` tags. This chapter should read like an independent consulting document and add substantive depth and industry authority to the report.

**IMPORTANT:**
- Write in a factual, professional, analytical tone (board-ready).
- Avoid second-person or first-person pronouns - use neutral formulations.
- Do not explain the prompt structure or models.
- Return only the HTML structure, no introduction.
- **NO** redundancy with existing sections (branch profile, G20, Roadmap).

## Content structure (6 fixed building blocks)

1. **Branch Trends 2025-2026** (max. 3 condensed trends)
   - Maximum 3-4 sentences for the entire section.
   - **Phase 3 specialisation:** Start with the sub-specialisation derived from `"{{hauptleistung}}"`.
   - Focus on concrete impacts on processes and decisions.
   - Do **not** use generic phrases like “fundamental transformation”, “critical threshold”, “exponential development”.
   - Each trend must be a single sentence with a measurable or concrete impact.
   - Target style: “In the area of [sub-specialisation derived from {{hauptleistung}}], AI becomes relevant where repetitive checking, analysis and documentation tasks consume time.”
   - **Do not write:** “The sector is undergoing a fundamental digital transformation…”

2. **Benchmarks & Industry Metrics**
   - Provide industry-specific metrics:
     - Degree of digitalisation (%) - typical value for {{BRANCH_SHORT_LABEL}}.
     - AI adoption rate (%) - percentage of companies already using AI.
     - Efficiency potential (%) - expected productivity gains through AI.
     - Sector-specific KPIs (e.g. cycle times, customer satisfaction, error rate).
   - Compare with the sector average or best practice.

3. **Top-5 Risks** (sector + GDPR + AI Act)
   - Identify risks relevant to {{BRANCH_SHORT_LABEL}}:
     1. **Data risks** (e.g. sensitive customer data, data loss)
     2. **Automation risks** (e.g. quality degradation, over-reliance on AI)
     3. **Compliance risks** (GDPR, AI Act classification)
     4. **Vendor risks** (dependencies, lock-in)
     5. **Reputational risks** (AI mis-decisions, lack of transparency)
   - Provide 1-2 sentences per risk describing concrete impact.

4. **Top-5 Opportunities**
   - Concrete opportunities through AI use in {{BRANCH_SHORT_LABEL}}:
     1. **Cost savings** (automation of repetitive tasks)
     2. **Quality improvement** (AI-supported checking, analysis)
     3. **New business models** (AI-based services, products)
     4. **Process automation** (end-to-end digitisation)
     5. **Customer loyalty** (personalisation, faster response)
   - Provide 1-2 sentences per opportunity with measurable benefit where possible.

5. **Use-Case Map** (4-Quadrant model)
   - Categorise typical AI use cases for {{BRANCH_SHORT_LABEL}} in this schema:
     - **Quick Wins:** high benefit, low effort - e.g. email triage, meeting transcription.
     - **Strategic Investments:** high benefit, high effort - e.g. full automation, AI core products.
     - **Efficiency Gains:** medium benefit, low effort - e.g. document classification.
     - **Long-Term Bets:** medium benefit, high effort - e.g. building predictive analytics.
   - Name at least two use cases per quadrant, tailored to {{BRANCH_SHORT_LABEL}}.

6. **AI Adoption Index (0-100)**
   - Determine a realistic score for {{BRANCH_SHORT_LABEL}} based on:
     - Current sector average
     - Regulatory environment
     - Data availability
     - Technical maturity
   - Provide the score numerically (e.g. “67/100”).
   - Add 2-3 sentences explaining what influences this score.

## Size-aware logic

Adjust depth and focus according to company size:

- **SOLO (one-person setup):**
  - Focus on personal relevance of trends and quick wins.
  - Adapt risks and opportunities to individual feasibility.
  - Text length: **at least 250 words**.
- **TEAM (small teams, 2-15 people):**
  - Focus on team-relevant trends and process optimisation.
  - Use benchmarks for small companies.
  - Text length: **at least 300 words**.
- **SME (small and medium-sized enterprise):**
  - Provide strategic depth: competitive advantages, scaling, governance.
  - Use benchmarks tailored to medium-sized enterprises.
  - Elaborate regulatory aspects.
  - Text length: **at least 350 words**.

**Maximum total length:** 600 words.

## HTML requirements & design (G21 PLATIN++)

Use the **PLATIN++ design enhancement system**:

Available CSS classes:
- `.report-card` - main container for sections
- `.report-card-header` - header with icon and title
- `.report-card-body` - content
- `.report-card-muted` - muted presentation
- `.report-card-highlight` - highlighted cards
- `.trend-list` - list for trends
- `.trend-item` - single trend
- `.trend-title` - trend title (bold)
- `.trend-description` - trend description
- `.metric-grid` - grid for benchmarks/metrics
- `.metric-item` - single metric
- `.metric-value` - value (large)
- `.metric-label` - label
- `.risk-list`, `.opportunity-list` - lists for risks/opportunities
- `.risk-item`, `.opportunity-item` - individual entries
- `.risk-high`, `.risk-medium`, `.risk-low` - risk colour codes
- `.usecase-matrix` - 2×2 grid for the use-case map
- `.usecase-quadrant` - single quadrant
- `.quadrant-title` - quadrant title
- `.quadrant-items` - use cases in the quadrant
- `.adoption-index` - container for the adoption index
- `.adoption-score` - score display (large, prominent)
- `.adoption-reasoning` - reasoning

**SVG icons (use inline):**
- **Trend:** `<svg viewBox="0 0 24 24" fill="none"><path d="M3 13L9 7L13 11L21 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M21 9V3H15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`
- **Risk:** `<svg viewBox="0 0 24 24" fill="none"><path d="M12 9V13M12 17H12.01M5.07183 19H18.9282C20.4678 19 21.4301 17.3333 20.6603 16L13.7321 4C12.9623 2.66667 11.0377 2.66667 10.2679 4L3.33975 16C2.56995 17.3333 3.53223 19 5.07183 19Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`
- **Opportunity:** `<svg viewBox="0 0 24 24" fill="none"><path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`
- **Matrix:** `<svg viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="7" height="7" stroke="currentColor" stroke-width="1.5"/><rect x="14" y="3" width="7" height="7" stroke="currentColor" stroke-width="1.5"/><rect x="3" y="14" width="7" height="7" stroke="currentColor" stroke-width="1.5"/><rect x="14" y="14" width="7" height="7" stroke="currentColor" stroke-width="1.5"/></svg>`
- **Benchmark:** `<svg viewBox="0 0 24 24" fill="none"><path d="M16 8V16M12 11V16M8 14V16M6 20H18C19.1046 20 20 19.1046 20 18V6C20 4.89543 19.1046 4 18 4H6C4.89543 4 4 4.89543 4 6V18C4 19.1046 4.89543 20 6 20Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`

**Output format**

Return **only** the finished HTML block that contains the six building blocks in clear logical order:

1. Branch Trends 2025-2026
2. Benchmarks & Industry Metrics
3. Top-5 Risks
4. Top-5 Opportunities
5. Use-Case Map (4 quadrants)
6. AI Adoption Index

No additional comments, no meta-explanations.

## Zero-leak policy

Forbidden - **never use**:
- Questions to the reader ("Do you have any questions?", "Would you like to know more?")
- Requests ("If you want...", "Contact us...")
- Assistant language ("I can help you...", "I will gladly explain...")
- Offers ("If desired...", "On request...")
- Interactive elements ("Click here...", "Select...")
- Placeholders ("[Insert here]", "{{VARIABLE}}" except defined ones)
- Meta comments ("This section...", "In the following...")

The output is a **final report section**, not a conversation.