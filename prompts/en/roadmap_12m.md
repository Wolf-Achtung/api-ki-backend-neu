Developer:
<!-- roadmap_12m.md – v11.0 PDF-SLIMDOWN-STRICT
     Output: Markdown (converted to HTML server-side)
     No HTML tags, no code fences

     **STRICT TOKEN LIMIT (CRITICAL!):**
     This section MUST produce MAXIMUM 700-900 words output.
     The LLM MUST stop after ~900 words.

     **Word Limits (STRICTLY REDUCED):**
     - Solo: ~200 words (acceptable: 180–240)
     - Team: ~280 words (acceptable: 250–320)
     - SME: ~360 words (acceptable: 320–400)

     STRUCTURE: 4 phases with MAX 4 BULLETS each!
       1. Months 1–3: Foundation (~150 words)
       2. Months 4–6: Piloting (~150 words)
       3. Months 7–12: Scaling (~200 words)
       4. Conclusion: Sustainability (~100 words)

     **ANTI-REDUNDANCY (ABSOLUTELY STRICT!):**
     - NO repetition from roadmap_90d (90 days covered there)
     - NO pain point repetition (addressed in Quick Wins)
     - NO tool descriptions (see Tools Recommendations)
     - Focus: WHAT COMES AFTER the first 90 days?
     - NO justifications, only measures

     STOP SIGNALS: End at "Conclusion & Sustainability" section.
-->

---

### VARIABLES (from Briefing)

- **{{BRANCHE_LABEL}}** – Industry label
- **{{UNTERNEHMENSGROESSE_LABEL}}** – Company size
- **{{HAUPTLEISTUNG}}** – Core service/main process
- **COMPANY_SIZE** – `solo` | `team` | `kmu`

---

### SIZE-AWARE LOGIC (STRICTLY FOLLOW!)

**COMPANY_SIZE == "solo":**
- NEVER: "department", "build team", "employees", "HR", "project team"
- INSTEAD: "own workflows", "personal routine", "self-review"
- Max 4 bullets per phase, ~50 words per phase

**COMPANY_SIZE == "team":**
- Small groups (2-10), informal structures
- "Team members", "AI coordinator", "shared standards"
- Max 4 bullets per phase, ~70 words per phase

**COMPANY_SIZE == "kmu":**
- Formal structures, departments, governance
- "Department heads", "governance board", "cross-functional"
- Max 4 bullets per phase, ~90 words per phase

---

### REQUIRED STRUCTURE (STRICTLY COMPACT)

## Strategic 12-Month Roadmap

This roadmap shows the progression after the first 90 days for **{{HAUPTLEISTUNG}}** in the **{{BRANCHE_LABEL}}** industry with size **{{UNTERNEHMENSGROESSE_LABEL}}**.

## Months 1–3: Foundation & First Use Cases

- Establish priority workflow (building on 90-day successes)
- Sharpen quality criteria
- Initial success measurement (time, quality)
- {% if COMPANY_SIZE == "solo" %}Solidify personal AI routine{% elif COMPANY_SIZE == "team" %}Document team standards{% else %}Evaluate pilot area{% endif %}

**KPI:** At least 2 stable use cases in production.

## Months 4–6: Piloting & Quality Assurance

- Workflow optimization based on learnings
- Introduce consistent review processes
- Set up monitoring dashboard
- {% if COMPANY_SIZE == "solo" %}Create quality checklist{% elif COMPANY_SIZE == "team" %}Assign quality responsible{% else %}Formalize QA process{% endif %}

**KPI:** Measurable time savings, error rate < 10%.

## Months 7–12: Expansion & Scaling

- Explore new use cases from adjacent areas
- {% if COMPANY_SIZE == "kmu" %}Finalize governance framework{% else %}Document guidelines{% endif %}
- Expand success measurement (ROI proof)
- Secure knowledge transfer and best practices

**KPI:** ROI demonstrable, at least 3 productive use cases.

## Conclusion & Sustainability

- Conduct annual review
- Plan budget for year 2
- Create Roadmap 2.0 with new priorities
- {% if COMPANY_SIZE == "kmu" %}Document compliance status{% else %}Record learnings{% endif %}

**Outlook:** Foundation for continuous development established.

---

### FORMAT RULES

- **Markdown only:** `## ` for phase titles
- Bullet lists with `- ` (MAX 4 per phase!)
- Short KPI paragraph per phase
- **No HTML**, no code fences
- **MAX 900 words total!**

---

### STYLE GUIDELINES

- Factual, concrete, no filler phrases
- Strategically focused, not narrative
- No repetitions from 90-day roadmap
- No developer language, no placeholders
- End after "Conclusion & Sustainability"
