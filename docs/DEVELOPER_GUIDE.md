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

## Golden Artifacts Generation

Generate reproducible HTML/PDF reports with SHA-256 hashes for regression testing.

### Prerequisites

```bash
# Backend must have Service-Token enabled
SERVICE_TOKEN_ENABLED=1
SERVICE_TOKEN_SECRET=your-secret-here
```

### Usage

```bash
# Set the secret (same as backend)
export SERVICE_TOKEN_SECRET="your-secret-here"

# Generate single profile
python scripts/generate_golden_reports.py \
  --base-url https://api.ki-sicherheit.jetzt \
  --profile solo

# Generate all 3 profiles
python scripts/generate_golden_reports.py \
  --base-url https://api.ki-sicherheit.jetzt \
  --all
```

### Available Profiles

| Profile | Description |
|---------|-------------|
| solo | Solo consultant, German |
| team_finance | Team, Finance/Insurance sector |
| kmu_france | KMU, France, English |

### Output Structure

```
artifacts/golden_reports/
  solo/
    report.html
    report.pdf
    hashes.json
  team_finance/
    ...
  kmu_france/
    ...
```

### hashes.json Format

```json
{
  "profile_id": "solo",
  "briefing_id": 12345,
  "generated_at": "2025-01-15T10:30:00Z",
  "html_sha256": "abc123...",
  "html_size": 45000,
  "pdf_sha256": "def456...",
  "pdf_size": 120000
}
```
