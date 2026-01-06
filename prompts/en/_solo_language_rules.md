# Solo persona language rules – internal reference

This internal document outlines vocabulary rules for prompts targeting solo entrepreneurs or freelancers. It is used to enforce consistent language that respects the context of one‑person businesses.

## Forbidden terms

When COMPANY_SIZE is `"solo"`, avoid using the following nouns and phrases, as they imply a team or larger organisation:

- employee(s), staff, workforce
- department, division, unit, business unit
- team members, colleagues
- management, leadership team
- HR, IT department, finance department

## Preferred alternatives

Use these terms instead to maintain a solo‑appropriate tone:

- “you” or “your business” (sparingly and professionally)
- “your processes” or “your workflows”
- “clients” or “customers” (when referring to external parties)
- “tasks” or “activities” instead of “team tasks”

## Tone guidelines

1. **Singular focus:** Address the solo professional as a single actor. Use singular verbs and avoid plural constructions that imply collaboration (e.g. say “Track your progress…” instead of “Track your team’s progress…”).
2. **Clarity without simplification:** Provide the same level of strategic and technical detail as for larger organisations, but tailor recommendations to a one‑person context. Do not oversimplify or assume lack of expertise.
3. **Empowerment:** Emphasise autonomy, flexibility and speed of decision‑making. Highlight benefits relevant to solo professionals, such as freeing time for creative work or reducing administrative overhead.
4. **Scalability:** When suggesting processes (e.g. version control or documentation routines), mention that these practices can scale as the business grows.

## Usage

Include a hidden Jinja block at the top of solo‑aware prompts to replace forbidden terms dynamically. For example:

```
{% if COMPANY_SIZE == "solo" %}
<!-- SOLO VOCABULARY RULES: replace employees/staff/colleagues/team/management/department/IT/HR etc. with business or workflow synonyms. -->
{% endif %}
```

This ensures that the model adjusts wording at runtime without cluttering the visible content.
