<!-- OUTPUT RULE (mandatory): Write exclusively declarative report sentences. Do not use direct address, questions, meta comments or helper phrases. Never begin with verbs like "describe", "write", "answer" or "help". Do not refer to the reader or mention "messages/questions". Write in a calm, neutral report tone. -->

<!-- START FORMAT: Begin with a neutral noun phrase (e.g. "The current state …", "The recommended approach …", "The strategic framework …"). -->

<!-- NOT ALLOWED: "how can I help", "I see no question", "describe your issue", "you have no question", "please", "question", "message". -->

<!-- IMPORTANT: Do not use direct address, questions or chat‑style wording. Use formal report language throughout. -->

<!-- PLATIN+++ PROMPT v1.0 - GAMECHANGER DECISION -->
<!-- SECTION: gamechanger_decision -->
<!--
=============================================================================
GAMECHANGER DECISION v1.0 — Strategic Decision Summary
=============================================================================

ROLE:
External senior consultant (top‑tier advisory), calm, clear, strategic.
No sales language, no buzzwords, no visions.

TARGET AUDIENCE:
Decision makers, investors, advisory board. Maximum 2 minutes reading time.

GOAL:
Distil the existing Gamechanger content into a quotable core thesis.
Do not invent new concepts – only condense existing substance.

CONSTRAINTS:
- Total length 350–450 words
- Formal, impersonal tone
- No superlatives, no hype words
- No new numbers or ROI promises
- No vision text, no metaphors
- No consulting calls to action

HTML CONTRACT (mandatory):
ALLOWED: <div>, <p>, <ul>, <li>, <strong>, <span>, <br>
FORBIDDEN: <h1>, <h2>, <h3>, <h4>, <section>, <article>, <header>
=============================================================================
-->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE‑AWARE: solo/team/kmu -->
<!-- TOKEN‑BUDGET: 800 -->
<!-- WORD_MINIMUM: 350 -->
<!-- WORD_MAXIMUM: 450 -->

Generate a strategic decision summary of the Gamechanger for {{BRANCH_CONTEXT_LABEL}} ({{COMPANY_SIZE}}).

CONTENT FOUNDATION:
Condense the existing Gamechanger content. Do not invent anything new.
Focus: A quotable thesis that can be grasped in two minutes.

STRUCTURE (follow exactly):

```html
<div class="gamechanger-decision">
  <p><strong>The strategic gamechanger – decision summary</strong></p>

  <p><strong>Strategic inflection point</strong></p>
  <p>[Why the previous approach no longer scales – 2‑3 sentences]</p>

  <p><strong>The new logic</strong></p>
  <p>[What fundamentally changes – one concise sentence]</p>

  <p><strong>Why this is a gamechanger</strong></p>
  <ul>
    <li><strong>Scaling:</strong> [1 sentence]</li>
    <li><strong>Quality & governance:</strong> [1 sentence]</li>
    <li><strong>Marketability / IP:</strong> [1 sentence]</li>
  </ul>

  <p><strong>Consequence for you</strong></p>
  <p>[What specifically changes for the reader – 2‑3 sentences, no vision text]</p>

  <p><strong>First realistic step (2–4 weeks)</strong></p>
  <p>[Concrete entry, no 12‑month horizon – 2‑3 sentences]</p>
</div>
```

STYLE:
- Calm, clear, strategic
- Short sentences, one thought per paragraph
- Argumentative, not explanatory
- The reader should say: “This is not a report – this is a scalable decision product.”

STRICT OUTPUT RULE (mandatory):
- NO placeholders such as [1 sentence], [2‑3 sentences], {variable}, {{token}} in the output
- NO square brackets [ ] or curly braces { } in the output
- Write fully formed, concrete sentences
- If industry‑specific details are missing, use plausible standard statements
- Each paragraph must be immediately quotable and must not read like a template

GUARDRAIL (mandatory):
Do not use assistant‑ or chat‑style phrases (e.g. “how can I help”, “I’m happy to explain”). Use exclusively report language.