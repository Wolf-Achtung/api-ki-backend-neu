# Prompt Framework – Guidelines for high‑quality generative prompts (G37)

This document defines a common framework for crafting robust and high‑quality prompts used throughout the AI transformation toolkit. It is not a runtime prompt itself but a set of principles and template elements to guide prompt authors.

## Purpose

Modern AI systems require clear, structured and context‑rich instructions to deliver accurate and relevant outputs. This framework ensures consistency across all prompts, maximises personalisation using the available data and enforces safety, compliance and quality standards.

## Core components

Every prompt should contain the following sections or logic elements:

1. **Header / Meta comment:** A hidden comment block (if used) specifying the version, section name, output format (e.g. HTML, JSON), size‑awareness, token budget and input variables. Keep variable names in the original language; do not translate them.
2. **Role definition:** A clear statement of the assistant’s role (e.g. “You are an AI transformation strategist…”). This shapes the voice and the scope of the response.
3. **Context injection:** A concise summary of relevant input variables (company, industry, size, maturity, region, main challenges). Use bold or list formatting to highlight key facts. Encourage the assistant to use all provided context without referencing the variable names directly.
4. **Tasks / Objectives:** A numbered list of actions or questions the assistant must address. Make each task specific and outcome‑oriented (“Provide three concrete recommendations…”, “Summarise the strategic switch…”).
5. **Size‑aware guidelines:** Define how the output should vary for solos, small teams and SMEs. Specify word counts, focus areas and tone differences. Use Jinja conditions (`{% if COMPANY_SIZE == "solo" %}`) to implement variations when embedding prompts into templates.
6. **Output specification:** Describe the required format: plain text, HTML fragment, structured JSON, or another markup. List allowed HTML tags or JSON keys. For JSON, provide a schema; for HTML, specify allowed elements and maximum length. Forbid Markdown or code fences unless explicitly needed.
7. **Validation & quality rules:** Include bullet points describing forbidden elements (e.g. no generic AI platitudes, no placeholders, no references to the prompt itself), required safety considerations (e.g. respect {{KI_GUARDRAILS}}, avoid high‑risk use cases), and micro‑consistency rules (e.g. link the strategic switch to the roadmap phases).
8. **Examples:** Provide an illustrative example showing the structure and tone without using the actual company data. Make it clear that the example is illustrative and must not be copied verbatim. Highlight the use of dynamic variables and structural elements.

## Personalisation

Prompts in this toolkit rely on five “gold nuggets” to drive personalisation: the main service (`{{hauptleistung}}`), the time‑saving priority (`{{ZEITERSPARNIS_PRIORITAET}}`), ongoing AI projects (`{{ki_projekte}}`), AI guardrails / no‑gos (`{{KI_GUARDRAILS}}`) and the three‑year vision (`{{VISION_3_JAHRE}}`). The framework mandates referencing these variables where relevant, ordered by priority. Prompts should draw on these nuggets to tailor recommendations, roadmaps and risks to the user’s unique situation.

## Safety & compliance

All prompts must incorporate legal and ethical guardrails. This includes compliance with the EU AI Act, GDPR, intellectual property laws and any company‑specific policies. Prompts should instruct the assistant to avoid high‑risk or prohibited applications, to flag potential compliance issues and to include references to applicable articles or guidelines when necessary. When describing funding or vendor options, ensure that the suggestions are plausible and legal within the region and sector.

## Implementation notes

- **Language:** Write all prompts in clear, professional English unless explicitly targeting another language. Avoid idioms and culturally specific references. For solo users, choose singular pronouns; for teams and SMEs, use plural forms and neutral corporate tone.
- **Reusability:** Use modular sections that can be reused across prompts (e.g. the same instructions for ROI calculations or risk matrix formatting). Avoid redundancy; refer to other modules rather than duplicating their content.
- **Token budgeting:** Respect the specified token budget and apply multipliers for different sizes. If a prompt is likely to exceed the budget, instruct the assistant to prioritise essential information and condense repetitive details.
- **Versioning:** Include a version identifier in the header comment to track changes and compatibility. When updating prompts, increment the version and note the changes in the progress log.

## Example template (simplified)

```
<!-- PLATIN+++ ENGINE v7.0 - GXX YOUR SECTION NAME -->
<!-- OUTPUT: JSON ONLY -->
<!-- SIZE-AWARE: solo/team/sme -->
<!-- TOKEN-BUDGET: 800 (solo:0.8x=640, team:1.0x=800, sme:1.15x=920) -->
<!-- INPUT VARS: {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}}, {{ki_projekte}}, {{KI_GUARDRAILS}}, {{VISION_3_JAHRE}} -->

# Your Section Name – Descriptive subtitle

## Role
You are an expert advisor in …

## Context
…

## Tasks
1. …
2. …

## Size‑aware guidance
…

## Output
Specify that the output must be JSON with a given schema.

## Validation rules
…

```

Use this example as a starting point when developing new prompts. Adapt the sections, tasks and output format to the specific purpose while adhering to the framework principles outlined above.
