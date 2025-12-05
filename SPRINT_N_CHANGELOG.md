# SPRINT N CHANGELOG
## PLATIN++ v5.3 - Persona Leak Elimination & Length Stabilization

**Sprint Date:** 2024-12
**Version:** 5.3.0

---

## Overview

Sprint N addresses two critical issues:
1. **Persona Leaks**: Solo reports containing Team/KMU terminology
2. **Length Stabilization**: Sections not meeting minimum word counts

---

## Changes by Category

### 1. Prompt Enhancer (`services/prompt_enhancer.py`)

**Version:** 2.6.0 → 2.7.0-PLATIN++

#### New Features:
- Added `SOLO_FORBIDDEN_TERMS` list (30+ terms)
- Added `SOLO_PERSONA_REPLACEMENTS` dictionary for automatic substitution
- Added `apply_solo_persona_filter()` function
- Added `check_solo_persona_leaks()` validation function

#### Updated Token Budgets:
| Section | Old | New | Change |
|---------|-----|-----|--------|
| executive_summary | 800 | 1200 | +50% |
| tools_empfehlungen | 1800 | 2500 | +39% |
| gamechanger | 3000 | 3500 | +17% |
| roadmap_12m | 2800 | 4200 | +50% |

#### Updated PLATIN_CRITICAL_SECTIONS:
- Added `executive_summary` section config
- Added `tools_empfehlungen` section config
- Updated min_words for gamechanger: 500 → 750
- Updated min_words for roadmap_12m: 350 → 500 (base)

---

### 2. Report Validator (`services/report_validator.py`)

**Version:** 1.3.0 → 1.4.0-SPRINT-N

#### Extended SIZE_FORBIDDEN for Solo:
```python
"solo": [
    # Team-specific terms
    "PMO-Team", "Team aufbauen", "Team-Struktur", "Teamstruktur",
    "Teamwork", "Teamrollen", "Teammitglieder", "Change-Team",
    "Projektmanagement-Office",
    # Employee/HR terms
    "Mitarbeiter einstellen", "Mitarbeiterschulung", "Personalstrategien",
    "Belegschaft",
    # Department/Organization terms
    "Abteilung", "Abteilungen", "HR-Abteilung", "IT-Abteilung",
    "Fachbereich", "Fachbereiche", "Bereichsleiter", "bereichsübergreifend",
    # English equivalents
    "team building", "team members", "hire employees", "department", "departments",
]
```

#### Updated Minimum Word Counts:
| Section | Solo | Team | KMU |
|---------|------|------|-----|
| executive_summary | 150 | 180 | 200 |
| tools_empfehlungen | 120 | 160 | 200 |
| gamechanger | 750 | 750 | 750 |
| roadmap_12m | 500 | 600 | 700 |

#### New Features:
- `HARD_STOP_ON_SIZE_MISMATCH = True` - Blocks reports with persona leaks
- `CRITICAL_LENGTH_SECTIONS` list - Sections that trigger CRITICAL errors
- Enhanced `_check_size_specific_issues()` with normalized size detection
- Enhanced `_check_empty_or_short_sections()` with CRITICAL severity for critical sections

---

### 3. Prompt Manifest (`prompts/prompt_manifest.json`)

**Version:** 5.0 → 5.3

#### New Metadata:
- Added `_token_budgets` section with size-aware min_words
- Added `sprint` field: "N"
- Added `changes` documentation array

---

### 4. German Prompts (DE) - 12 Files Updated

All prompts updated to v5.3 with Sprint N persona rules:

| Prompt | Key Changes |
|--------|-------------|
| `business_case.md` | Added WORD_MINIMUM comments, Solo persona rules |
| `tools_empfehlungen.md` | Updated token budget (2500), min words (120/160/200) |
| `gamechanger.md` | Updated token budget (3500), min words (750), requires 3+ scenarios |
| `roadmap_12m.md` | Updated token budget (4200), min words (500/600/700) |
| `executive_summary.md` | Updated token budget (1200), min words (150/180/200) |
| `wettbewerb_benchmark.md` | Added COMPANY_SIZE variable, Solo persona rules |
| `monetarisierung.md` | Added COMPANY_SIZE variable, Solo persona rules |
| `foerderpotenzial.md` | Added COMPANY_SIZE variable, Solo persona rules |
| `ai_act_summary.md` | Added COMPANY_SIZE variable, Solo persona rules |
| `ki_skillplan.md` | Added COMPANY_SIZE variable, Solo persona rules |

#### Solo Persona Rules Added to All Prompts:
```jinja2
{% if COMPANY_SIZE == "solo" %}
NICHT VERWENDEN für Solo:
- "Team aufbauen" → stattdessen: "Kapazität erweitern"
- "Mitarbeiter" → stattdessen: "Ressourcen"
- "Teams" → stattdessen: "Kapazitäten"
- "Fachbereich" → stattdessen: "Arbeitsfeld"
- "Abteilung" → stattdessen: "Arbeitsbereich"
{% endif %}
```

---

## Replacement Mappings

### Solo-Forbidden Terms → Replacements

| Forbidden (DE) | Replacement (DE) |
|----------------|------------------|
| Team aufbauen | Kapazität erweitern |
| Team | Kapazität |
| Teams | Ressourcen |
| Mitarbeiter | Ressourcen |
| Mitarbeiter einstellen | Ressourcen smart bündeln |
| Fachbereich | Arbeitsfeld |
| Abteilung | Arbeitsfeld |

| Forbidden (EN) | Replacement (EN) |
|----------------|------------------|
| team building | capacity building |
| team members | collaborators |
| hire employees | bundle resources smartly |
| department | work area |

---

## Testing Requirements

### Required Test Profiles:
1. `solo_beratung_de` - 0 size-mismatch, 0 section-too-short
2. `solo_consulting_en_gold` - Clean persona, correct funding
3. `kmu_france_eu_core_en_gold` - EU-Core funding, no leakage
4. `team_it_de` - Team wording, no solo terms

### Success Criteria:
- [ ] 0 SECTION_TOO_SHORT warnings
- [ ] 0 SIZE_MISMATCH warnings
- [ ] 0 Fallbacks for critical sections
- [ ] Hard-Stop never triggered
- [ ] All minimum word counts met

---

## Migration Notes

- No database migrations required
- No API changes required
- Backward compatible with existing briefings
- New COMPANY_SIZE variable must be passed to prompt rendering

---

## Related Files

- `services/prompt_enhancer.py` (v2.7.0)
- `services/report_validator.py` (v1.4.0)
- `prompts/prompt_manifest.json` (v5.3)
- `prompts/de/*.md` (12 files updated)
