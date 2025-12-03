# Prompt Framework – 5 Steps to the Perfect Prompt

<!-- persona:solo -->
<!-- Solo: Quickly applicable, 1 example is enough, no theory -->
<!-- persona:team -->
<!-- Team: Build shared prompt library, share best practices -->
<!-- persona:kmu -->
<!-- SME: Standardized prompts for recurring tasks, quality assurance -->

## The 5-Step Framework

Every good prompt contains these five elements:

### 1. Context
*Background information for the AI*

> "You work for a mid-sized consulting company in the DACH region."

### 2. Role
*What expertise should the AI assume?*

> "Act as an experienced business consultant focused on process optimization."

### 3. Goal
*What should be achieved?*

> "Create a summary of the key insights from the meeting notes."

### 4. Constraints
*Limitations and quality criteria*

> "Maximum 5 bullet points. No jargon without explanation. Focus on actionable items."

### 5. Format
*How should the output look?*

> "Output as a numbered list with priority indication (high/medium/low)."

---

## Complete Example Prompt

```
Context: You support a 20-person team in implementing AI tools.

Role: You are an AI trainer with experience in change management.

Goal: Create a training plan for the first 4 weeks.

Constraints:
- Max. 2 hours of training per week
- Focus on practical exercises
- No prior knowledge required

Format: Table with Week, Topic, Duration, Learning Objective
```

---

## Tips for Better Prompts

| Problem | Solution |
|---------|----------|
| Result too vague | More context + specific constraints |
| Result too long | Format specification (e.g., "max. 200 words") |
| Wrong tone | Define role (e.g., "formal", "casual") |
| Unsuitable examples | Explicitly mention industry/context |

---

## Using Variables

For recurring prompts: Build in placeholders.

```
Create a [DOCUMENT_TYPE] for [TARGET_AUDIENCE]
on the topic [TOPIC].
Length: [LENGTH]. Tone: [TONE].
```

---
*Tip: Improve prompts iteratively. First version → Review result → Adjust prompt.*
