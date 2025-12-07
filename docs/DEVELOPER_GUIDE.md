# PLATIN++ Developer Guide

## Adding a New Prompt

### 1. Create the prompt file

```bash
# German version
touch prompts/de/my_new_section.md

# English version
touch prompts/en/my_new_section.md
```

### 2. Add to manifest (prompts/prompt_manifest.json)

```json
{
  "de": {
    "my_new_section": {
      "title": "My New Section",
      "path": "my_new_section.md",
      "purpose": "Description of what this section does",
      "output": "html",
      "size_aware": true,
      "required": true,
      "tokens": {
        "base": 2000,
        "solo": 1600,
        "team": 2000,
        "kmu": 2300
      }
    }
  }
}
```

### 3. Write the prompt content

```markdown
# My New Section

## Instructions
Generate content for {{COMPANY_NAME}} based on:
- Company size: {{COMPANY_SIZE}}
- Industry: {{BRANCHE}}

## Output Format
Return HTML with <h2>, <p>, <ul> tags.

## Constraints
- Max tokens: {{MAX_TOKENS}}
- Language: {{LANG}}
```

### 4. Add to template (if needed)

Update `templates/report_platin.html` to include the new section.

### 5. Test

```bash
python -c "from services.prompt_loader import load_prompt; print(load_prompt('my_new_section', 'de'))"
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| PROMPTS_DEFAULT_LANG | de | Default prompt language |
| USE_PROMPT_SYSTEM | 1 | Enable manifest-based prompts |
| MAX_PDF_SIZE_MB | 12 | PDF size limit |
| ENABLE_MONITORING | 1 | Enable metrics collection |

## Error Categories

| Category | Blocking | Description |
|----------|----------|-------------|
| critical_errors | Yes | Stops report generation |
| warnings | No | Logged but continues |
| guardrail_leaks | Yes | GuardrailHit object leaked to output |
| placeholder_violations | Yes | Unresolved {{PLACEHOLDER}} |
| size_mismatches | Yes | Solo report with Team terms |
