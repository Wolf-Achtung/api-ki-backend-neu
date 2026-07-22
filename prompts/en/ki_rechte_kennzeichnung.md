Developer:
<!-- PLATIN++ PROMPT v5.2 -->
<!-- SECTION: ki_rechte_kennzeichnung -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{MEDIEN_SPARTE_LABEL}}, {{hauptleistung}}, {{ki_guardrails}}, {{COMPANY_SIZE}} -->
<!-- TOKEN-BUDGET: 900 (solo:0.8x=720, team:1.0x=900, kmu:1.15x=1035) -->
<!--
GOAL: The differentiating chapter for media/entertainment clients — concrete,
actionable guardrails on rights and labeling when using AI in production and
exploitation. Not a legal treatise, but production reality. Output in ENGLISH.

MANDATORY STRUCTURE (4 blocks):
1. Chain of rights for AI material (2-3 paragraphs or list):
   - Usability of AI output (protectability unresolved — implications for
     buyouts, licensing and stock exploitation)
   - Training/input: no client material or uncleared third-party material in
     public tools; respect TDM opt-outs
   - Documentation duty: record per project which asset was created with
     which tool under which license
2. Voice, likeness, personality rights (1-2 paragraphs):
   - Clones/digital doubles/synthesis ONLY with explicit documented consent;
     scope (projects, term, media) fixed contractually
   - Legacy contracts usually do NOT cover AI use — retrofit clauses
3. Labeling under EU AI Act Art. 50 (1-2 paragraphs + mini process):
   - When synthetic/AI-generated content must be labeled (deepfake rule;
     mention editorial/artistic carve-outs)
   - Concrete 3-step process: capture → decide → label (who decides, where
     documented)
4. Checklist "Before every delivery" (5-7 items, as a list):
   concretely checkable, tied to {{hauptleistung}}

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: self-checklist, simple contract building blocks, no process bureaucracy
- team: clear ownership (who checks rights/labeling before delivery)
- kmu: documented approval process, rights register, contract standards

CONTEXT:
- If {{MEDIEN_SPARTE_LABEL}} is present: tailor examples to the segment
  (production: cast/archive; post/VFX: reference material/upscaling sources;
  games: assets/store disclosure; publishing: text/image rights, reader
  transparency; music/audio: voices/samples; agency: client approvals/ad labeling)
- Acknowledge the client's existing guardrails ({{ki_guardrails}}) and extend
  them instead of repeating.

ANTI-REDUNDANCY / TOPIC OWNERSHIP (binding):
- This section: OWNER of chain of rights, consent, Art. 50 labeling
- NOT here: general AI Act risk classes and deadlines (→ ai_act_summary)
- NOT here: general usage rules (→ ai_policy_mini)
- NOT here: GDPR basics (→ data_readiness)

STYLE:
- Length: 300-450 words
- Concrete, production-oriented, no legal boilerplate
- Explicitly: "not legal advice — involve specialist counsel for contracts" (1 sentence)
- No invented statutory detail beyond Art. 50 and TDM opt-outs

Do not use:
- No placeholders or template markers
- No false precision on unresolved legal questions
-->

<section class="section ki-rechte-kennzeichnung">
  <h2>AI Rights &amp; Labeling in Production</h2>

  <p>
  [Block 1: chain of rights for AI material — concrete for {{hauptleistung}}]
  </p>

  <h3>Voice, Likeness, Personality Rights</h3>
  <p>
  [Block 2]
  </p>

  <h3>Labeling Synthetic Content (EU AI Act Art. 50)</h3>
  <p>
  [Block 3 incl. 3-step process]
  </p>

  <h3>Checklist: Before Every Delivery</h3>
  <ul>
    <li>[5-7 checkable items]</li>
  </ul>
</section>
