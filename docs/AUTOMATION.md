# P1 Automation Pipeline - Report Generation via Fixtures

This document describes how to use the automation pipeline to generate reference reports
without manual UI interaction. This is useful for:

- **CI/CD**: Automated report generation and validation
- **Development**: Quick report generation for testing
- **Regression Testing**: Compare reports across commits
- **Codespaces**: Generate reports in cloud environments

## Quick Start

```bash
# 1. Set up environment
cp .env.example .env.local
# Edit .env.local with your API_BASE_URL and SERVICE_TOKEN

# 2. Generate a Solo report
make gen:solo

# 3. Generate all reports
make gen:all
```

## Environment Variables

The automation scripts use a **fallback chain** for configuration, so you don't need to
set all variables - it will automatically use existing Railway environment variables.

### API Base URL

| Priority | Variable | Description |
|----------|----------|-------------|
| 1 | CLI `--base-url` | Command line argument |
| 2 | `API_BASE_URL` | Script canonical |
| 3 | `BACKEND_BASE` | Railway default |
| 4 | `SMOKE_BASE_URL` | Smoke test URL |
| 5 | (default) | `http://localhost:8000` |

### Service Token

| Priority | Variable | Description |
|----------|----------|-------------|
| 1 | CLI `--service-token` | Command line argument |
| 2 | `SERVICE_TOKEN` | Script canonical |
| 3 | `SMOKE_AUTH_TOKEN` | Railway smoke auth |

**Note**: `SERVICE_TOKEN_SECRET` is server-side configuration. The client uses `SERVICE_TOKEN`.

### Other Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POLL_INTERVAL` | `2` | Seconds between status checks |
| `POLL_TIMEOUT` | `300` | Max seconds to wait for completion |

## Fixtures

Fixtures are canonical JSON test profiles located in `fixtures/`:

| Fixture | Company Size | Expected Variant | Pages |
|---------|--------------|------------------|-------|
| `solo_freelancer.json` | 1 (Solo) | `solo_compact` | 12-16 |
| `team_startup.json` | 2-10 | `standard` | ~30 |
| `kmu_mittelstand.json` | 50+ | `standard` | ~40 |

### Fixture Structure

```json
{
  "fixture_id": "solo_freelancer",
  "expected_variant": "solo_compact",
  "expected_pages": "12-16",
  "lang": "de",
  "answers": {
    "unternehmensgroesse": "1",
    "branche": "beratung",
    // ... other form fields
  }
}
```

## CLI Usage

### Basic Submission

```bash
python scripts/submit_fixture.py fixtures/solo_freelancer.json
```

### With Polling

```bash
python scripts/submit_fixture.py fixtures/solo_freelancer.json --poll
```

### With PDF Download

```bash
python scripts/submit_fixture.py fixtures/solo_freelancer.json --poll --download-pdf artifacts/
```

### JSON Output (for CI)

```bash
python scripts/submit_fixture.py fixtures/solo_freelancer.json --poll --output-json
```

### Full Options

```bash
python scripts/submit_fixture.py fixtures/solo_freelancer.json \
  --poll \
  --timeout 300 \
  --interval 2 \
  --download-pdf artifacts/ \
  --output-json \
  --verbose
```

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success - report generated |
| `2` | Usage error / fixture invalid |
| `3` | Authentication failed |
| `4` | Timeout waiting for completion |
| `5` | Server returned failed status |

## Makefile Targets

```bash
# Individual reports
make gen:solo    # Solo-Compact (12-16 pages)
make gen:team    # Team report
make gen:kmu     # KMU/Mittelstand report

# All reports
make gen:all     # Generate all three in sequence

# CI mode (with artifacts)
make ci:reports  # Generate all + save to artifacts/

# Validation
make validate:solo  # Validate Solo constraints

# Cleanup
make clean:artifacts  # Remove artifacts directory
```

## CI Integration

### GitHub Actions

See `.github/workflows/report-smoke.yml` for the complete workflow.

```yaml
- name: Generate Reports
  run: make ci:reports
  env:
    API_BASE_URL: ${{ secrets.API_BASE_URL }}
    SERVICE_TOKEN: ${{ secrets.SERVICE_TOKEN }}

- name: Upload Artifacts
  uses: actions/upload-artifact@v4
  with:
    name: reports
    path: artifacts/
```

### Quality Gates

The CI checks these gates for Solo reports:
- `page_count <= 16` (Solo-Compact max)
- `solo_leak_count == 0` (no Team/KMU language)
- `validation.errors_count == 0` (no critical errors)

## Troubleshooting

### Authentication Failed (Exit Code 3)

```
ERROR: Authentication failed: {"detail":"Invalid service token"}
```

**Solution**: Check your `SERVICE_TOKEN` is correctly set. For Railway, ensure
`SERVICE_TOKEN_ENABLED=1` on the server.

### Timeout (Exit Code 4)

```
ERROR: Polling timed out after 300s. Last status: processing
```

**Solution**: Increase `POLL_TIMEOUT` or check if the server is overloaded.

### Fixture Not Found (Exit Code 2)

```
ERROR: Fixture not found: fixtures/my_fixture.json
```

**Solution**: Ensure the fixture file exists and the path is correct.

### No Token Warning

```
WARNING: No SERVICE_TOKEN set for remote URL - auth may fail
```

**Solution**: Set `SERVICE_TOKEN` or `SMOKE_AUTH_TOKEN` for non-localhost URLs.

## API Endpoints

### Submit Briefing

```
POST /api/briefings/submit
Content-Type: application/json
X-Service-Token: <token>

{
  "lang": "de",
  "answers": { ... },
  "queue_analysis": true
}
```

Response:
```json
{
  "briefing_id": 123,
  "status": "queued"
}
```

### Get Status

```
GET /api/briefings/{briefing_id}
X-Service-Token: <token>
```

Response:
```json
{
  "briefing_id": 123,
  "status": "done",
  "report_url": "https://.../api/report/html/123",
  "pdf_url": "https://.../api/report/pdf/123",
  "done_at": "2024-01-15T10:30:00Z"
}
```

### Get Validation Summary (Optional)

```
GET /api/briefings/{briefing_id}/validation
X-Service-Token: <token>
```

Response:
```json
{
  "errors_count": 0,
  "warnings_count": 2,
  "page_count": 14,
  "gates": {
    "solo_leak_count": 0,
    "page_count_valid": true
  }
}
```

## Local Development Setup

1. **Start the backend**:
   ```bash
   make run
   ```

2. **Generate a report**:
   ```bash
   API_BASE_URL=http://localhost:8000 make gen:solo
   ```

3. **View the PDF**:
   ```bash
   open artifacts/solo_freelancer_*.pdf
   ```

## Railway Deployment

For Railway, the environment variables are pre-configured:

- `BACKEND_BASE` → API URL
- `SMOKE_AUTH_TOKEN` → Auth token

Just run:
```bash
make gen:solo
```

The script will automatically use the Railway fallback chain.
