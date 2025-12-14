# Optimized Gold Profiles

## Purpose
Optimized and hardened variants of the gold baseline profiles.
These are the **source of truth for Golden Artifact generation**.

## Usage
- Golden Artifact runs (HTML, PDF, SHA-256 hashes)
- CI/CD pipeline validation
- Reproducible report generation

## Rules
- Source profiles originate from `test_profiles_gold/`
- No ad-hoc or experimental profiles allowed
- All profiles must be listed in `golden_profiles_manifest.json`
- Changes require review to ensure artifact reproducibility

## Current Profiles
| Profile | Description |
|---------|-------------|
| `solo_beratung_ki_assessments_optimized.json` | Solo consultant, KI assessments |
| `team_finance_insurance_advisory_optimized.json` | Team, finance/insurance sector |
| `kmu_france_eu_core_en_gold_optimized.json` | SME France, EU core, English |

## Related
- `golden_profiles_manifest.json` - Authoritative list of profiles for Golden Runs
- `scripts/generate_golden_reports.py` - Script that consumes these profiles
