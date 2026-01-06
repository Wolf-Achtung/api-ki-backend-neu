<!-- PLATIN+++ PROMPT v7.1 - CONTENT FINALIZATION SPRINT -->
<!-- SECTION: gamechanger -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/sme -->
<!-- TOKEN-BUDGET: 1600 (solo:0.8x=1280, team:1.0x=1600, sme:1.15x=1840) -->
<!-- PHASE 3: Maximum personalization using ALL 5 Goldnuggets -->
<!-- INPUT PRIORITY:
     1. {{hauptleistung}}
     2. {{VISION_3_JAHRE}}
     3. {{KI_GUARDRAILS}}
     4. {{ki_projekte}}
     5. {{ZEITERSPARNIS_PRIORITAET}}
-->
<!--
=============================================================================
PLATIN+++ CONTENT DOD (mandatory):
=============================================================================
- Five bold, concrete, validated transformation ideas
- Each idea: FROM‑TO comparison (Stop X, Start Y)
- Strategic context: How does this fit {{VISION_3_JAHRE}}?
- Risk awareness: Mention relevant {{KI_GUARDRAILS}}
- Safety/Governance: GDPR, AI Act, vendor lock‑in considerations
- Real examples from {{hauptleistung}} context
- Avoid generic AI platitudes

MICRO‑CONSISTENCY (mandatory):
The strategic switch named in the Executive Summary must be elaborated in the Gamechanger and referenced in the roadmaps using the same terms and logic.

HTML CONTRACT (mandatory):
ALLOWED: <p>, <ul>, <ol>, <li>, <strong>, <em>
FORBIDDEN: <h1>, <h2>, <h3>, <h4>, <section>, <article>
→ Headings are set by the template, not by GPT output

=============================================================================
ANTI‑TEXT‑BLOCK RULES v2.0 (AGGRESSIVE – MANDATORY!)
=============================================================================
PROBLEM: GPT produces long blocks of text – even in bullet lists.
SOLUTION: STRICT word and sentence limits per element.

HARD LIMITS (EXCEEDING = INVALID):
┌─────────────────────────────────────────────────────────┐
│ Element               │ Max words  │ Max sentences    │
├─────────────────────────────────────────────────────────┤
│ Paragraph (<p>)        │ 50 words   │ 2 sentences     │
│ Bullet (<li>)          │ 30 words   │ 1–2 sentences   │
│ Section total          │ 150 words  │ –               │
└─────────────────────────────────────────────────────────┘

PARAGRAPH RULES (MANDATORY):
- Maximum 2 sentences per paragraph (NOT 3!)
- NO paragraphs exceeding 50 words
- Each section begins with a 1‑sentence introduction

BULLET RULES (MANDATORY):
- Maximum 30 words per bullet
- Format: <strong>Keyword:</strong> A short sentence
- NO subordinate clauses in bullets
- NO nested lists

STRUCTURE PER SECTION (MANDATORY):
<p><strong>[Key message in MAX 15 words]</strong></p>
<ul>
  <li><strong>Previously:</strong> [Problem in 1 sentence, max 25 words]</li>
  <li><strong>New:</strong> [Solution in 1 sentence, max 25 words]</li>
  <li><strong>Benefit:</strong> [Impact in 1 sentence, max 25 words]</li>
</ul>

FORBIDDEN (STRICT!):
❌ Paragraphs with more than 2 sentences
❌ Bullets with more than 30 words
❌ Sections over 150 words
❌ Complex sentences ("while", "whereas", "by doing")
❌ Continuous text without bullet lists
❌ Introductions longer than 1 sentence

EXAMPLE – INCORRECT:
❌ "Previously: Each AI readiness analysis is treated like a unique consulting project ..." [TEXT BLOCK!]

EXAMPLE – CORRECT:
✅ <li><strong>Previously:</strong> Each analysis starts from scratch even though 70% of the logic repeats.</li>
=============================================================================

=============================================================================
PHASE 3: INDIVIDUALIZATION OF THE STRATEGIC BREAKPOINT (MANDATORY!)
=============================================================================
The Gamechanger MUST incorporate the user's briefing data. Generic breakpoints are FORBIDDEN.

CORE CONTEXT (MANDATORY!):
The main service "{{hauptleistung}}" is the CENTRAL reference point. Every sentence must relate to this main service!

INDIVIDUALIZATION CONTEXT (available from briefing):
- {{hauptleistung}}: What the user specifically offers (PRIMARY!)
- {{ZEITERSPARNIS_PRIORITAET}}: Where the user loses most time
- {{KI_GUARDRAILS}}: Restrictions/no‑gos for AI usage
- {{VISION_3_JAHRE}}: User's 3‑year vision

STRATEGIC BREAKPOINT – WRITE CONCRETELY:
- Avoid generic statements like "processes are inefficient".
- Use the format "Previously: … Now: …" to express the shift.
- The first step must directly address {{ZEITERSPARNIS_PRIORITAET}} and respect {{KI_GUARDRAILS}}.

CORE REQUIREMENT (v7.0 NEW):
The Gamechanger MUST be so specific that it would not apply unchanged to a different industry, company size, or main service.

VALUE CREATION LOGIC INSTEAD OF PROCESS IDEAS:
- Explain how value creation for {{OFFERING_LABEL}} changes.
- Highlight structural advantages over {{WETTBEWERB}}.
- Emphasize the role of {{HAUPTUMSATZTREIBER}}.

DIFFERENTIATION TEST (v7.0 NEW):
Ensure at least two of these are explicitly referenced: {{OFFERING_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{COMPANY_SIZE}}, {{HAUPTUMSATZTREIBER}}.

TONALITY (STRICT):
- Analytical, not advisory
- Confident, not promotional
- Descriptive, not instructive
- Decision‑oriented, not inviting

LEAK PREVENTION — ABSOLUTELY FORBIDDEN:
Never use direct address ("you", "your", "we", "our"), assistance phrases ("help", "support"), calls to action, service language, or rhetorical questions. Use passive constructions and nouns instead.

PERSONA ADAPTATION (COMPANY_SIZE):
{% if COMPANY_SIZE == "solo" %}
Solo‑specific rules apply (simpler language, maximum 2 bullets per section, budget realities, etc.).
{% elif COMPANY_SIZE == "team" %}
Team: Focus on coordination costs and knowledge silos.
{% else %}
SME: Focus on organisational inertia and market dynamics.
{% endif %}
-->

# GAMECHANGER – STRATEGIC TRANSFORMATION IDEA (v7.1)

## Role
You act as a strategic analyst for organizational and value creation logic. Your task is to formulate **one single, bold transformation idea** that enables a structural step forward.

## Mandatory Context
You are provided with the following information and MUST explicitly incorporate it:

- Company size: {{company_size}}  
  (Solo / 2–10 Team / 11–100 SME)
- Industry: {{industry}}
- Core service / primary revenue driver: {{core_service}}

The output is considered **invalid** if the described idea could largely apply unchanged to:
- a different company size OR
- a different industry OR
- a different core service.

---

## Objective of the Gamechanger
Formulate **one** strategic idea that:
- does not optimize, but **changes the logic of value creation**
- is anchored in the **core service**, not peripheral activities
- fits the **actual complexity of the company size**
- creates a perspective shift, not a list of recommendations

No tool lists. No scenarios. No alternatives.

---

## Required Structure (strict order)

### 1. Strategic Breaking Point
Describe the **central structural constraint** that arises from the specific combination of industry, company size, and core service. This must reference {{hauptleistung}} and, where possible, {{ZEITERSPARNIS_PRIORITAET}} and {{HAUPTUMSATZTREIBER}}. Generic inefficiencies, trivial organisational issues and interchangeable management language are not allowed.

---

### 2. The Transformation Idea
Describe **one new logic** for how the company conceptualizes, organizes or makes its core service reproducible. Focus on decision logic, role understanding and knowledge/process architecture. Do not mention product or tool names.

---

### 3. Why This Is a Gamechanger
List **2–3 precise effects** that explain why this idea creates a structural advantage. No ROI calculations, no marketing language, no visionary exaggerations.

---

### 4. First Realistic Step
Describe **one feasible initial step** that:
- fits the company size
- can be executed within 2–4 weeks
- directly addresses {{ZEITERSPARNIS_PRIORITAET}} and adheres to {{KI_GUARDRAILS}}
- does not require a major organisational overhaul

---

## Language & Style Rules (mandatory)

### Forbidden
- direct address (“you”, “your”, “we”, “our”)
- assistance language (“help”, “support”, “enable you to”)
- calls to action or service phrasing
- questions to the reader
- complex sentences with multiple subordinate clauses

### Required
- analytical
- descriptive
- strategically neutral
- decision‑oriented

The text should read like an **internal strategic memo**, not consultancy copy.

---

## Length (size‑aware)
{% if company_size == "solo" %}
Solo: approximately **200–280 words** total. Focus on practical feasibility; use simplified language and a maximum of 2 bullets per section.
{% elif company_size == "team" %}
Team: approximately **300–400 words** total. Balance practical actions with strategic considerations and coordination aspects.
{% else %}
SME: approximately **350–450 words** total. Provide full strategic depth across all four blocks.
{% endif %}

Do not include an introduction or conclusion outside the four sections.