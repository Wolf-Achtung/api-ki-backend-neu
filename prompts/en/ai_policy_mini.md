<!-- PLATIN+++ PROMPT v6.1 -->
<!-- SECTION: ai_policy_mini -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}} -->
<!-- TOKEN-BUDGET: 700 (solo:0.8x=560, team:1.0x=700, kmu:1.15x=805) -->
<!--
GOAL: Provide compact, immediately actionable AI usage rules without bureaucratic overhead.

MANDATORY STRUCTURE (7 core rules):
1. Data usage (what the AI may do and what it may not)
2. Review requirement (human review)
3. Transparency (labelling)
4. No automated decisions
5. Tool approval
6. Learning culture
7. Updating

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: 5 simple rules, immediately actionable, no bureaucracy
- team: Clear roles (creator, reviewer), hand‑off rules
- kmu: Structured policy, responsibilities and documentation obligations

SIZE‑AWARE RESPONSIBILITIES:
- solo: Self‑control, simple checklist
- team: Team lead reviews, peer‑review established
- kmu: Compliance officer, documented approval processes

ANTI‑REDUNDANCY:
- Governance ground rules belong HERE, not duplicated in the Strategy/Governance section.
- Do not overlap with AI Act Summary (legal details there)
- Complements the Risks section (risks there, rules here)

STYLE:
- Length: 120–180 words
- Practical, immediately usable
- Not legal advice, pragmatic guidelines

Do not use:
- Placeholders or template markers
- Legal jargon
- Repetition of guardrails from the risks section
-->

<section class="section ai-policy-mini">
  {% if COMPANY_SIZE == "solo" %}
  <h2>Your 5 AI rules</h2>

  <p>
    Simple, pragmatic rules for your daily AI use as a solo entrepreneur in
    <strong>{{BRANCHE_LABEL}}</strong>.
  </p>

  <div class="policy-rules">
    <div class="rule">
      <h4>1. Data check</h4>
      <p>Use only your own non‑sensitive data. No customer data without explicit permission.</p>
    </div>

    <div class="rule">
      <h4>2. Quick review</h4>
      <p>Read AI outputs once before forwarding them.</p>
    </div>

    <div class="rule">
      <h4>3. Labelling</h4>
      <p>For customer communications: be transparent when AI helped.</p>
    </div>

    <div class="rule">
      <h4>4. Decide yourself</h4>
      <p>AI provides suggestions – you decide, especially for contracts or finances.</p>
    </div>

    <div class="rule">
      <h4>5. Trusted tools</h4>
      <p>Use only AI tools you trust. No experiments with business data.</p>
    </div>
  </div>

  <div class="quick-check">
    <h4>Quick check before each AI use</h4>
    <ul>
      <li>Data OK? (no customer data)</li>
      <li>Tool trustworthy?</li>
      <li>Result checked?</li>
    </ul>
  </div>

  {% elif COMPANY_SIZE == "team" %}
  <h2>AI Mini‑Policy: 7 Core Rules</h2>

  <p>
    Compact rules for daily AI use in your team in <strong>{{BRANCHE_LABEL}}</strong>.
  </p>

  <div class="policy-rules">
    <div class="rule">
      <h4>1. Data usage</h4>
      <p><strong>Allowed:</strong> Internal, non‑personal data.</p>
      <p><strong>Not allowed:</strong> Customer data, HR data or confidential documents without permission.</p>
    </div>

    <div class="rule">
      <h4>2. Review requirement</h4>
      <p>Every AI output is reviewed by a team member before sharing it externally.</p>
    </div>

    <div class="rule">
      <h4>3. Transparency</h4>
      <p>For customer‑relevant content label when AI supported.</p>
    </div>

    <div class="rule">
      <h4>4. No automated decisions</h4>
      <p>AI provides suggestions – humans decide. Applies to HR topics, contracts and finances.</p>
    </div>

    <div class="rule">
      <h4>5. Tool approval</h4>
      <p>Use only AI tools approved by the team. Do not feed unknown tools with business data.</p>
    </div>

    <div class="rule">
      <h4>6. Learning culture</h4>
      <p>Discuss mistakes openly, learn from them and adapt processes together.</p>
    </div>

    <div class="rule">
      <h4>7. Updating</h4>
      <p>This policy is reviewed quarterly by the team and adjusted as needed.</p>
    </div>
  </div>

  <div class="quick-check">
    <h4>Quick check before each AI use</h4>
    <ul>
      <li>Data appropriate? (no sensitive personal data)</li>
      <li>Tool approved?</li>
      <li>Result checked?</li>
      <li>Transparency ensured?</li>
    </ul>
  </div>

  {% else %}
  <h2>AI Mini‑Policy: 7 Core Rules</h2>

  <p>
    Compact rules for daily AI use at
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in <strong>{{BRANCHE_LABEL}}</strong>.
  </p>

  <div class="policy-rules">
    <div class="rule">
      <h4>1. Data usage</h4>
      <p><strong>Allowed:</strong> Internal, non‑personal data.</p>
      <p><strong>Not allowed:</strong> Customer data, HR data or confidential documents without permission.</p>
    </div>

    <div class="rule">
      <h4>2. Review requirement</h4>
      <p>Every AI output is reviewed by a person before passing it on.</p>
    </div>

    <div class="rule">
      <h4>3. Transparency</h4>
      <p>For customer‑relevant content label when AI supported.</p>
    </div>

    <div class="rule">
      <h4>4. No automated decisions</h4>
      <p>AI provides suggestions – humans decide. Applies to HR topics, contracts and finances.</p>
    </div>

    <div class="rule">
      <h4>5. Tool approval</h4>
      <p>Use only approved AI tools. Do not feed unknown tools with company data.</p>
    </div>

    <div class="rule">
      <h4>6. Learning culture</h4>
      <p>Document mistakes, learn from them and adapt processes. No blame culture.</p>
    </div>

    <div class="rule">
      <h4>7. Updating</h4>
      <p>This policy is reviewed quarterly and adjusted as needed.</p>
    </div>
  </div>

  <div class="quick-check">
    <h4>Quick check before each AI use</h4>
    <ul>
      <li>Data appropriate? (no sensitive personal data)</li>
      <li>Tool approved?</li>
      <li>Result checked?</li>
      <li>Transparency ensured?</li>
    </ul>
  </div>
  {% endif %}

  <p class="small muted">
    This mini‑policy does not replace legal advice. When in doubt, seek counsel.
  </p>
</section>
