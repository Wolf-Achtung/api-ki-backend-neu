Developer:
<!-- PLATIN++ PROMPT v5.2 -->
<!-- SECTION: prompt_framework -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/sme -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}} -->
<!-- TOKEN-BUDGET: 700 (solo:0.8x=560, team:1.0x=700, sme:1.15x=805) -->
<!--
GOAL: Compact 5-step framework for effective AI prompts.

REQUIRED STRUCTURE:
1. The 5 Steps (Context, Role, Goal, Constraints, Format)
2. Complete Example
3. Troubleshooting Table
4. Variable Usage

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: Quickly applicable, 1 example is enough, no theory
- team: Build shared prompt library, share best practices
- sme: Standardised prompts for recurring tasks, quality assurance

SIZE-AWARE RESPONSIBILITIES:
- solo: Own prompts, learning-by-doing
- team: Prompt sharing within team, peer review
- sme: Central prompt library, quality control

ANTI-REDUNDANCY:
- Prompt techniques HERE, not in skillplan (general skill development there)
- Focus on STRUCTURE, not on specific use cases
- No overlap with tools (tool selection there, prompt technique here)

STYLE:
- Text length: 150-200 words
- Practical, with concrete example
- No theoretical treatises

Do not use:
- No placeholders or template markers
- No repetition of skillplan content
- No tool-specific instructions
-->

<section class="section prompt-framework">
  <h2>Prompt Framework: 5 Steps to the Perfect Prompt</h2>

  <p>
    Effective prompts for <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>
    in <strong>{{BRANCHE_LABEL}}</strong>.
  </p>

  <div class="framework-steps">
    <h4>The 5 Elements of a Good Prompt</h4>
    <table class="table">
      <thead>
        <tr>
          <th>#</th>
          <th>Element</th>
          <th>Function</th>
          <th>Example</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>1</td>
          <td><strong>Context</strong></td>
          <td>Background for the AI</td>
          <td>"You work for a consulting company."</td>
        </tr>
        <tr>
          <td>2</td>
          <td><strong>Role</strong></td>
          <td>AI expertise</td>
          <td>"Act as an experienced process consultant."</td>
        </tr>
        <tr>
          <td>3</td>
          <td><strong>Goal</strong></td>
          <td>What should be achieved</td>
          <td>"Create a summary of the meeting results."</td>
        </tr>
        <tr>
          <td>4</td>
          <td><strong>Constraints</strong></td>
          <td>Limitations</td>
          <td>"Max. 5 points, no jargon."</td>
        </tr>
        <tr>
          <td>5</td>
          <td><strong>Format</strong></td>
          <td>Output form</td>
          <td>"Numbered list with priority."</td>
        </tr>
      </tbody>
    </table>

    <h4>Troubleshooting</h4>
    <table class="table">
      <thead>
        <tr>
          <th>Problem</th>
          <th>Solution</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Result too vague</td>
          <td>More context + more specific constraints</td>
        </tr>
        <tr>
          <td>Result too long</td>
          <td>Format specification (e.g. "max. 200 words")</td>
        </tr>
        <tr>
          <td>Wrong tone</td>
          <td>Define role (e.g. "formal", "casual")</td>
        </tr>
        <tr>
          <td>Unsuitable examples</td>
          <td>Explicitly mention industry/context</td>
        </tr>
      </tbody>
    </table>
  </div>

  <p class="small muted">
    Tip: Improve prompts iteratively. First version -> Check result -> Adjust prompt.
  </p>
</section>
