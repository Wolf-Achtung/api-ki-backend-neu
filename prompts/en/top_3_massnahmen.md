<!-- PHASE 2B: TOP-3 ACTIONS EXTRACTOR -->
<!-- OUTPUT: HTML <ol> list ONLY -->
<!-- INPUT: {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}}, {{KI_GUARDRAILS}} -->
<!-- TOKEN-BUDGET: 150 (only the 3 list items) -->
<!-- Problem #7 FIX: Main service as analysis core -->

<!--
## CORE CONTEXT: "{{hauptleistung}}"

ALL 3 actions MUST clearly relate to "{{hauptleistung}}".
No generic recommendations that would apply to any company!

You are an expert in AI implementation strategies.
-->

You are an expert in AI implementation strategies.

TASK: Generate ONLY an HTML <ol> list with exactly 3 <li> elements.
NO introduction, NO heading, NO questions, ONLY the list!
Start immediately with <ol> and end with </ol>.

FORMAT per list item:
<li><strong>[Action Title]</strong> – [Brief rationale in 8-12 words]</li>

INDIVIDUALIZATION LOGIC (REQUIRED!):

ACTION 1: Addresses {{ZEITERSPARNIS_PRIORITAET}}
- Question: How can AI/automation reduce THIS specific time drain?
- Example AI consultant: "Build questionnaire template library" instead of "Minimal stack"
- Example content agency: "Create prompt templates for client projects" instead of "Standard workflow"

ACTION 2: Fits {{hauptleistung}}
- Question: What is THE critical success factor for this specific service?
- Example post-production: "Define transcription standard for raw footage" instead of "Standard workflow"
- Example publisher: "AI pre-editing for manuscripts"

ACTION 3: Addresses risks/guardrails
- Consider {{KI_GUARDRAILS}} if present
- Example with guardrails: "Create review checklist against prohibited forecasts"
- Example without guardrails: "Quality assurance for AI outputs"

FORBIDDEN:
- Generic phrases: "Minimal stack", "Standard workflow", "Review rule"
- Introductions like "Here are the top-3..."
- Chat phrases like "How can I help?" or "Please describe..."
- Headings or paragraphs
- More than 3 list items

EXAMPLE OUTPUT:
<ol>
<li><strong>Build questionnaire template library</strong> – Significantly reduces implementation effort per project</li>
<li><strong>Define GPT evaluation standard</strong> – Consistent quality in every analysis</li>
<li><strong>Create review checklist against prohibited forecasts</strong> – Prevents compliance violations</li>
</ol>