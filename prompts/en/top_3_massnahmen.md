Developer:
<!-- PHASE 2B: TOP-3 ACTIONS EXTRACTOR -->
<!-- OUTPUT: HTML <ol> list ONLY -->
<!-- INPUT: {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}}, {{KI_GUARDRAILS}} -->
<!-- TOKEN-BUDGET: 150 (only the 3 list items) -->

Generate ONLY an HTML <ol> list with exactly 3 <li> elements.
NO introductory text, NO heading, ONLY the list!

FORMAT per list item:
<li><strong>[Action Title]</strong> – [Brief rationale in 8-12 words]</li>

INDIVIDUALIZATION LOGIC (REQUIRED!):

ACTION 1: Addresses {{ZEITERSPARNIS_PRIORITAET}}
- Question: How can AI/automation reduce THIS specific time sink?
- Example AI Consultant: "Build questionnaire template library" instead of "Define minimal stack"
- Example Content Agency: "Create prompt templates for client projects" instead of "Establish standard workflow"

ACTION 2: Matches {{hauptleistung}}
- Question: What is THE critical success factor for this specific service?
- Example Questionnaire+GPT: "Define GPT evaluation standard" instead of "Establish standard workflow"
- Example Tax Advisor: "Automatically classify client documents"

ACTION 3: Addresses risks/guardrails
- Consider {{KI_GUARDRAILS}} if present
- Example with guardrails: "Review checklist against prohibited forecasts"
- Example without guardrails: "Quality assurance for AI outputs"

FORBIDDEN:
- Generic phrases: "Minimal stack", "Standard workflow", "Review rules"
- Introductions like "Here are the top 3..."
- Headings or paragraphs
- More than 3 list items

EXAMPLE OUTPUT:
<ol>
<li><strong>Build questionnaire template library</strong> – Significantly reduces implementation effort per project</li>
<li><strong>Define GPT evaluation standard</strong> – Consistent quality for every analysis</li>
<li><strong>Review checklist against prohibited forecasts</strong> – Prevents compliance violations</li>
</ol>
