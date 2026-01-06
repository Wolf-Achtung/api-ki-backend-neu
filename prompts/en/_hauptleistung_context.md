# Main service context injection – internal guidelines

This internal file defines how to generate the context block for the variable `{{hauptleistung}}` (“main service”). It is not used directly in user‑facing output but informs other prompts about the company’s core process or offering.

## Purpose

The `{{hauptleistung}}` variable represents the central business process or service that the company wishes to optimise with AI (e.g. “manually editing trailer rough cuts”, “managing claims processing workflows”). Providing a rich and specific context for this variable enables highly personalised recommendations, roadmaps and risk assessments.

## Guidelines

1. **Source of information:** Use the answers from the client questionnaire, the industry profile and any existing documentation to derive a 1–2 sentence description of the main service. The context should capture the essence of what is performed, who is involved and why it is critical for the business.
2. **Language:** Write in clear, professional English. Use neutral, descriptive language and avoid jargon. Do not translate the variable name `{{hauptleistung}}`; keep it in German to ensure system compatibility.
3. **Personalisation:** Where possible, include modifiers that reflect the company’s size, region and sector. Mention whether the service is highly manual, regulated, creative, repetitive, customer‑facing or back‑office.
4. **Tone:** Maintain an informative tone. Do not include instructions, questions or marketing language. Avoid personal pronouns (“you”, “we”); refer to the company and its service in the third person.
5. **Length:** Aim for 30–50 words. Keep the description concise but meaningful.
6. **Usage:** The resulting description is injected into other prompts as context; do not reference this file or explain the generation process in user‑facing outputs.

## Example

```
{{hauptleistung}}: Managing the end‑to‑end claims process for automotive insurance, from customer intake through document verification to payout, currently performed manually across disparate systems and subject to strict regulatory oversight.
```

This example shows how to describe the core service in neutral, succinct terms. Adjust the wording to the actual service and industry context.
