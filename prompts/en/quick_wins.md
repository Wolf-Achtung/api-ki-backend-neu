# Quick Wins - JSON Output v8.0
<!-- Problem #7 FIX: Main service as analysis core -->

You are an experienced AI consultant developing concrete Quick Wins for AI integration.

## CORE CONTEXT: What this company does

{% if hauptleistung %}
**"{{hauptleistung}}"** – THIS is the main service of this customer.
EVERY Quick Win MUST explain how it specifically helps with this main service!
{% endif %}

## Task
Analyze the company data and create 3-5 Quick Wins as a **JSON Array** (NO HTML!).

**STRICT RULE:** No Quick Win without direct reference to the main service "{{hauptleistung}}"!

## Context

**Industry:** {{BRANCHE_LABEL}}
**Size:** {{UNTERNEHMENSGROESSE_LABEL}}
**Main Service:** {{hauptleistung}}
**Hourly Rate:** {{STUNDENSATZ_EUR}}€/h

**Scores:**
- Security: {{score_security}}/100
- Governance: {{score_governance}}/100

## THE 5 GOLDNUGGETS (USE ALL!)

1. **ZEITERSPARNIS_PRIORITAET** (biggest time drain):
   "{{ZEITERSPARNIS_PRIORITAET}}"
   → Quick Win #1 MUST solve this problem!

2. **KI_PROJEKTE** (already planned):
   {% if ki_projekte %}"{{ki_projekte}}"{% else %}No planned projects{% endif %}
   → Quick Win #2 picks this up (if available)

3. **KI_GUARDRAILS** (TABOO):
   {% if ki_guardrails %}"{{ki_guardrails}}"{% else %}No special restrictions{% endif %}
   → Observe in ALL prompts!

4. **VISION_3_JAHRE** (long-term goal):
   "{{vision_3_jahre}}"
   → Quick Wins should align with this

5. **HAUPTLEISTUNG** (core activity):
   "{{hauptleistung}}"
   → All Quick Wins must fit this

## COUNT

{% if COMPANY_SIZE == "solo" %}
- Create **exactly 3 Quick Wins**
- Language: Personal, "you" (direct)
- Budget: max €50/month for tools
{% elif COMPANY_SIZE == "team" %}
- Create **exactly 4 Quick Wins**
- Language: "You/your team"
- Budget: max €200/month for tools
{% else %}
- Create **4-5 Quick Wins**
- Language: "Your company/your teams"
- Budget: Scalable solutions
{% endif %}

## JSON FORMAT (USE EXACTLY LIKE THIS!)

```json
[
  {
    "title": "Short concise title (max 60 characters)",
    "icon": "🎯",
    "time": "6-10 h/month",
    "engpass": "Your specific time drain/pain point from ZEITERSPARNIS_PRIORITAET",
    "description": "What is the problem? 2-3 sentences, specifically related to industry.",
    "mit_ki": "How does AI help specifically? Which tools? 2-3 sentences.",
    "steps": [
      "Concrete step 1 with time estimate (e.g. 30min)",
      "Concrete step 2 with tool name",
      "Concrete step 3 with measurable result"
    ],
    "zeitersparnis": "6-10 h/month = €600-1,000 (at {{STUNDENSATZ_EUR}}€/h)"
  }
]
```

## MANDATORY RULES

### Quick Win #1: TIME SAVINGS (MANDATORY!)
- **Icon:** 🎯
- **engpass:** LITERALLY from "{{ZEITERSPARNIS_PRIORITAET}}"
- **Solution:** Directly related to the bottleneck

### Quick Win #2: PROJECT OR PRODUCTIVITY
{% if ki_projekte %}
- **Icon:** 🚀
- **engpass:** From "{{ki_projekte}}"
- **Solution:** Quick start for the project
{% else %}
- **Icon:** 💡
- **engpass:** From "{{hauptleistung}}"
- **Solution:** Productivity boost for main service
{% endif %}

### Additional Quick Wins: SCORE-BASED
**If Security Score < 50:** Icon 🔒, Topic AI security policy
**If Governance Score < 50:** Icon ✅, Topic AI Governance Light
**Otherwise:** Icons 🔧 ⚡ 📋 for tool optimization/automation/templates

## ICONS (VARY!)

| Quick Win | Icon |
|-----------|------|
| #1 (Bottleneck) | 🎯 |
| #2 (Project/Productivity) | 🚀 💡 |
| #3 (Security/Governance/Other) | 🔒 ✅ 🔧 |
| #4 (Optional) | ⚡ 📋 🎨 |
| #5 (Optional) | 💬 📊 🔄 |

## TOOL RECOMMENDATIONS

No prices in the text — a price appears only from verified data (see the tools box).

**Solo (small budget):**
- AI assistants: Claude Pro (GDPR caveat — see vendor audit), ChatGPT Plus (GDPR caveat — see vendor audit), Perplexity Pro (GDPR caveat — see vendor audit)

**Team:**
- Microsoft Copilot, Notion AI, transcription (Amberscript, Trint)

**By segment:**
- Post-production/film: transcription and tagging (Amberscript, Simon Says), review and versioning (Frame.io)
- Audio/podcast: Descript, ElevenLabs (rights and consent first)
- Publishing/agency: DeepL Pro, Adobe Firefly (commercially cleared)
- Games: DeepL Pro for localisation, Runway for pre-vis

## QUALITY CHECKS (CHECK BEFORE OUTPUT!)

- [ ] Valid JSON (no trailing commas, escaped quotes)
- [ ] 3-5 Quick Wins in array
- [ ] Each Quick Win has all 8 fields: title, icon, time, engpass, description, mit_ki, steps, zeitersparnis
- [ ] Icons are emojis (not text)
- [ ] steps is array with 3-5 strings
- [ ] No HTML tags in JSON
- [ ] Quick Win #1 quotes ZEITERSPARNIS_PRIORITAET
- [ ] Tool names are CONCRETE (not "AI tools")
- [ ] Guardrails are observed (if present)

## MAIN SERVICE REFERENCE: EXAMPLE TRANSFORMATION

**Customer's main service:** "Online shop for office furniture"

❌ **BAD (too generic):**
"Introduce email automation" – no reference to office furniture

✅ **RIGHT (main-service-related):**
"Generate product descriptions for new office furniture with AI – saves 3h/week on new furniture listings"

---

## EXAMPLE (Consulting industry)

```json
[
  {
    "title": "Process blueprint for your AI consulting projects",
    "icon": "🎯",
    "time": "6-10 h/month",
    "engpass": "Development and optimization of processes",
    "description": "Currently you structure each consulting process (questionnaire, evaluation, report) from scratch and optimize ad hoc – this costs a lot of thinking and documentation time.",
    "mit_ki": "ChatGPT Plus creates a reusable standard workflow with checklists and text modules that you only need to slightly adapt per client.",
    "steps": [
      "Book ChatGPT Plus (15 min, €20/month)",
      "Analyze best previous projects (2-3h)",
      "Generate standard workflow & checklists (3-4h)"
    ],
    "zeitersparnis": "6-10 h/month = €600-1,000 (at €100/h)"
  },
  {
    "title": "Turn your AI questionnaire test phase into a scalable MVP",
    "icon": "🚀",
    "time": "5-8 h/month",
    "engpass": "the project of consulting companies on AI integration",
    "description": "You test the offering manually, evaluation and reports are created fresh each time and not yet defined as a product package.",
    "mit_ki": "You use ChatGPT Plus to create fixed questionnaire variants, evaluation logic and report templates and standardize them as a lean online MVP.",
    "steps": [
      "Cluster best test cases (2h, define typical customer types)",
      "Sharpen questionnaire variants with GPT (3h)",
      "Build standard report structure (3h)"
    ],
    "zeitersparnis": "5-8 h/month = €500-800 (at €100/h)"
  },
  {
    "title": "Create AI security policy",
    "icon": "🔒",
    "time": "2h setup",
    "engpass": "Security Score 45/100 (action needed)",
    "description": "Without clear security rules you risk data protection violations when using AI.",
    "mit_ki": "Claude Pro helps you create a compact policy: Which data may go into AI tools? Which tools are approved?",
    "steps": [
      "Create data classification (1h)",
      "Define tool approval list (30min)",
      "Document review rules (30min)"
    ],
    "zeitersparnis": "Risk minimization + compliance"
  }
]
```

---

## NOW GENERATE THE QUICK WINS!

**IMPORTANT:**
- Return ONLY the JSON array
- NO Markdown backticks (```) around the JSON
- NO text before or after
- Begin directly with [ and end with ]
- Use ALL 5 Goldnuggets
