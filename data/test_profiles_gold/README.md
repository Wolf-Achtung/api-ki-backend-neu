# Gold Baseline Profiles

## Purpose
Canonical gold baseline profiles for the KI-Briefing system.

## Usage
- Reference for regression testing
- Baseline for comparison with optimized variants
- Source of truth for profile structure and content

## Rules
- Changes require explicit review and approval
- Modifications should be rare and intentional
- All changes must be versioned and documented
- Do NOT use directly for Golden Artifact runs (use `test_profiles_gold_optimized/` instead)

## Related
- `test_profiles_gold_optimized/` - Optimized variants used for Golden Artifact generation
- `golden_profiles_manifest.json` - Manifest defining which profiles are used for Golden Runs
