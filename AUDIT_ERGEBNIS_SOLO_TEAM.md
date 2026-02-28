# AUDIT: Solo & Team Segment-Konsistenz nach FIX-B36a

**Datum:** 2026-02-28
**Scope:** Budget-Konsistenz aller segment-abhängigen Dateien (solo/team/kmu)
**Anlass:** FIX-B36a erhöhte KMU-Budgets; Solo/Team-Budgets proportional gesetzt aber NICHT log-validiert
**Auditor:** Claude Code Audit Pipeline

---

## 1. Executive Summary

1. **KRITISCH:** Die Healer-SEGMENT_BUDGETS für Solo und Team wurden bei FIX-B36a **NICHT** proportional (55%/75% von KMU) angepasst. Solo/Team-Budgets stehen noch auf den alten, niedrigen Werten und verursachen **exakt denselben 50-78% Content-Verlust**, der für KMU behoben wurde.
2. **KRITISCH:** SIZE_PROFILES (config/size_profiles.py) — die vom GLOBAL-TRUNCATION genutzt werden — haben für Solo ebenfalls drastisch zu niedrige Werte (17-38% von KMU statt 55%).
3. **HOCH:** KMU-only Plaintext-Budgets (17 lowercase Sections) fehlen für Solo und Team komplett — diese Sections fallen auf `_default` (solo=1000, team=1500).
4. **MITTEL:** FIX-B726-COMPACT entfernt identische 14 Sections für alle Segmente ohne Differenzierung.
5. **MITTEL:** Drei unabhängige Budget-Systeme (SIZE_PROFILES → GLOBAL-TRUNCATION → SEGMENT_BUDGETS → Healer) ohne zentrale Synchronisation.

---

## 2. Budget-Konsistenz-Matrix

### 2.1 Drei Budget-Systeme im Überblick

| System | Datei | Genutzt von | Stage |
|--------|-------|-------------|-------|
| `SIZE_PROFILES.section_budgets` | `config/size_profiles.py` | GLOBAL-TRUNCATION in `gpt_analyze.py` (L13461) | Pre-Render |
| `SEGMENT_BUDGETS` | `services/report_healer.py` (L2741) | `apply_segment_budget()` | Pre-Render (nach GLOBAL) |
| `SOLO_COMPACT_WORD_LIMITS` | `services/solo_compact_engine.py` (L165) | `process_for_solo_compact()` | Pre-Render (Solo only) |
| WP4 Compact Guard | `services/solo_compact_engine.py` (L650) | `check_and_apply_compact_guard()` | Post-Render |

**Budget-Hierarchie im Healer** (L3082-3093):
1. Exact match in SEGMENT_BUDGETS → Healer-lokale Tabelle
2. Uppercase_HTML-Mapping in SEGMENT_BUDGETS
3. SIZE_PROFILES-Fallback (nur wenn 1+2 nicht matchen)
4. `_default` aus SEGMENT_BUDGETS

### 2.2 SOLO Budget-Vergleich — Kritische Sections

| Section | SIZE_PROFILES (GLOBAL) | Healer SEGMENT_BUDGETS | KMU Healer (B36a) | Solo/KMU Ratio | Soll (55%) | DELTA | Status |
|---------|----------------------|----------------------|-------------------|---------------|------------|-------|--------|
| EXECUTIVE_SUMMARY_HTML | 4.000 | **2.000** | 6.000 | 33% | 3.300 | **-1.300** | KRITISCH |
| PILOT_PLAN_HTML | 3.000 | **1.200** | 5.000 | 24% | 2.750 | **-1.550** | KRITISCH |
| DATA_READINESS_HTML | 3.000 | **1.200** | 6.000 | 20% | 3.300 | **-2.100** | KRITISCH |
| MONETARISIERUNG_HTML | 3.000 | **1.200** | 4.000 | 30% | 2.200 | **-1.000** | KRITISCH |
| KI_SKILLPLAN_HTML | 3.000 | **1.200** | 4.000 | 30% | 2.200 | **-1.000** | KRITISCH |
| TECHNOLOGIE_PROZESSE_HTML | 3.000 | **2.000** | 8.000 | 25% | 4.400 | **-2.400** | KRITISCH |
| UNTERNEHMENSPROFIL_MARKT_HTML | 3.000 | 5.000 | 14.000 | 36% | 7.700 | **-2.700** | HOCH |
| SOFORT_START_HTML | (kein SP) | **1.500** | 8.000 | 19% | 4.400 | **-2.900** | KRITISCH |
| TEMPLATES_START_HTML | (kein SP) | **2.500** | 8.000 | 31% | 4.400 | **-1.900** | HOCH |
| FOERDERPOTENZIAL_HTML | 3.000 | 5.000 | 12.000 | 42% | 6.600 | **-1.600** | HOCH |
| ORG_CHANGE_HTML | 3.000 | 4.000 | 10.000 | 40% | 5.500 | **-1.500** | HOCH |
| STRATEGIE_GOVERNANCE_HTML | 3.000 | 5.000 | 10.000 | 50% | 5.500 | -500 | OK~ |
| TOOLS_EMPFEHLUNGEN_HTML | 3.000 | 5.000 | 8.000 | 63% | 4.400 | +600 | OK |
| ROADMAP_90D_HTML | 3.000 | 5.000 | 8.000 | 63% | 4.400 | +600 | OK |
| ROADMAP_12M_HTML | 8.000 | 8.000 | 14.000 | 57% | 7.700 | +300 | OK |
| BRANCH_DEEP_DIVE_HTML | 3.000 | 12.000 | 14.000 | 86% | 7.700 | +4.300 | OK |
| QUICK_WINS_HTML | 8.000 | 8.000 | 12.000 | 67% | 6.600 | +1.400 | OK |
| WETTBEWERB_BENCHMARK_HTML | 2.000 | 5.000 | 8.000 | 63% | 4.400 | +600 | OK |
| KI_AKTIVITAETEN_ZIELE_HTML | 2.000 | 2.000 | 5.000 | 40% | 2.750 | **-750** | MITTEL |
| `_default` | 1.000 | **1.000** | 3.000 | 33% | 1.650 | **-650** | HOCH |

### 2.3 TEAM Budget-Vergleich — Kritische Sections

| Section | SIZE_PROFILES (GLOBAL) | Healer SEGMENT_BUDGETS | KMU Healer (B36a) | Team/KMU Ratio | Soll (75%) | DELTA | Status |
|---------|----------------------|----------------------|-------------------|---------------|------------|-------|--------|
| EXECUTIVE_SUMMARY_HTML | 7.000 | **3.000** | 6.000 | 50% | 4.500 | **-1.500** | KRITISCH |
| PILOT_PLAN_HTML | 6.000 | **1.800** | 5.000 | 36% | 3.750 | **-1.950** | KRITISCH |
| DATA_READINESS_HTML | 8.000 | **1.800** | 6.000 | 30% | 4.500 | **-2.700** | KRITISCH |
| MONETARISIERUNG_HTML | 6.000 | **1.800** | 4.000 | 45% | 3.000 | **-1.200** | KRITISCH |
| KI_SKILLPLAN_HTML | 6.000 | **1.800** | 4.000 | 45% | 3.000 | **-1.200** | KRITISCH |
| TECHNOLOGIE_PROZESSE_HTML | 8.000 | **3.000** | 8.000 | 38% | 6.000 | **-3.000** | KRITISCH |
| UNTERNEHMENSPROFIL_MARKT_HTML | 8.000 | **5.000** | 14.000 | 36% | 10.500 | **-5.500** | KRITISCH |
| STRATEGIE_GOVERNANCE_HTML | 9.000 | **5.000** | 10.000 | 50% | 7.500 | **-2.500** | HOCH |
| TOOLS_EMPFEHLUNGEN_HTML | 9.000 | **5.000** | 8.000 | 63% | 6.000 | **-1.000** | HOCH |
| SOFORT_START_HTML | (kein SP) | **2.000** | 8.000 | 25% | 6.000 | **-4.000** | KRITISCH |
| TEMPLATES_START_HTML | (kein SP) | **3.500** | 8.000 | 44% | 6.000 | **-2.500** | HOCH |
| BRANCH_DEEP_DIVE_HTML | 8.000 | **6.000** | 14.000 | 43% | 10.500 | **-4.500** | HOCH |
| KI_AKTIVITAETEN_ZIELE_HTML | 3.000 | 3.000 | 5.000 | 60% | 3.750 | **-750** | MITTEL |
| ROADMAP_90D_HTML | 6.000 | 5.000 | 8.000 | 63% | 6.000 | **-1.000** | HOCH |
| FOERDERPOTENZIAL_HTML | 9.000 | 12.000 | 12.000 | 100% | 9.000 | +3.000 | OK |
| ORG_CHANGE_HTML | 8.000 | 9.000 | 10.000 | 90% | 7.500 | +1.500 | OK |
| ROADMAP_12M_HTML | 8.500 | 12.000 | 14.000 | 86% | 10.500 | +1.500 | OK |
| QUICK_WINS_HTML | 7.000 | 10.000 | 12.000 | 83% | 9.000 | +1.000 | OK |
| WETTBEWERB_BENCHMARK_HTML | 5.000 | 8.000 | 8.000 | 100% | 6.000 | +2.000 | OK |
| `_default` | 2.500 | **1.500** | 3.000 | 50% | 2.250 | **-750** | HOCH |

### 2.4 SIZE_PROFILES Solo/KMU Ratio — GLOBAL-TRUNCATION Budgets

Die SIZE_PROFILES werden von GLOBAL-TRUNCATION (gpt_analyze.py L13461) genutzt und begrenzen Content VOR dem Healer:

| Section | Solo SP | KMU SP | Ratio | Soll 55% | Status |
|---------|---------|--------|-------|----------|--------|
| EXECUTIVE_SUMMARY_HTML | 4.000 | 14.000 | 29% | 7.700 | KRITISCH |
| STRATEGIE_GOVERNANCE_HTML | 3.000 | 18.000 | 17% | 9.900 | KRITISCH |
| TOOLS_EMPFEHLUNGEN_HTML | 3.000 | 18.000 | 17% | 9.900 | KRITISCH |
| FOERDERPOTENZIAL_HTML | 3.000 | 18.000 | 17% | 9.900 | KRITISCH |
| UNTERNEHMENSPROFIL_MARKT_HTML | 3.000 | 16.000 | 19% | 8.800 | KRITISCH |
| ORG_CHANGE_HTML | 3.000 | 16.000 | 19% | 8.800 | KRITISCH |
| RECOMMENDATIONS_HTML | 3.000 | 20.000 | 15% | 11.000 | KRITISCH |
| TECHNOLOGIE_PROZESSE_HTML | 3.000 | 12.000 | 25% | 6.600 | KRITISCH |
| PILOT_PLAN_HTML | 3.000 | 8.000 | 38% | 4.400 | HOCH |
| DATA_READINESS_HTML | 3.000 | 10.000 | 30% | 5.500 | HOCH |
| MONETARISIERUNG_HTML | 3.000 | 8.000 | 38% | 4.400 | HOCH |
| GAMECHANGER_HTML | 1.500 | 16.000 | 9% | 8.800 | **EXTREM** |
| RISKS_HTML | 7.000 | 18.000 | 39% | 9.900 | HOCH |

**Hinweis:** GAMECHANGER und RISKS sind in `BUDGET_EXEMPT_SECTIONS` des Healers, daher greift die SP-Begrenzung hier hauptsächlich beim GLOBAL-TRUNCATION.

### 2.5 Fehlende Plaintext-Budgets (Solo/Team)

KMU hat 17 explizite Plaintext-Section-Budgets (L3022-3038). Solo und Team haben KEINE.

Für Sections die per Plaintext-Key (`"strategie_governance"`) ankommen:
- **Healer Tier 2** mapped auf `"STRATEGIE_GOVERNANCE_HTML"` → findet den HTML-Budget → OK
- **Aber `"roadmap"` → `"ROADMAP_HTML"` → NICHT in SEGMENT_BUDGETS** → fällt auf SIZE_PROFILES → fällt auf `_default`

| Plaintext-Key | KMU Budget | Solo (Tier 2 Mapping) | Solo effektiv | Verlust |
|---------------|-----------|----------------------|--------------|---------|
| `roadmap` | 10.000 | → `ROADMAP_HTML` nicht gefunden | `_default`=1.000 | **90%** |
| `ki_stack_summary` | 5.000 | → `KI_STACK_SUMMARY_HTML` nicht gefunden | `_default`=1.000 | **80%** |

---

## 3. Konflikte — sortiert nach Priorität

### Priorität 1: BLOCKER — B36-Budgets werden zunichte gemacht

#### K1: Solo Healer-Budgets nicht B36-proportional [BLOCKER]
- **Datei:** `services/report_healer.py` L2742-2830 (SEGMENT_BUDGETS → "solo")
- **Problem:** 11 Sections haben Budgets bei 20-33% von KMU statt der angestrebten 55%
- **Betroffene Sections:** EXECUTIVE_SUMMARY (2000), PILOT_PLAN (1200), DATA_READINESS (1200), MONETARISIERUNG (1200), KI_SKILLPLAN (1200), TECHNOLOGIE_PROZESSE (2000), SOFORT_START (1500), TEMPLATES_START (2500), UNTERNEHMENSPROFIL_MARKT (5000→7700), ORG_CHANGE (4000→5500), FOERDERPOTENZIAL (5000→6600)
- **Risiko:** 10/10
- **Empfohlene Werte:** Alle auf 55% der KMU-B36a-Werte setzen (siehe Tabelle 2.2)

#### K2: Team Healer-Budgets nicht B36-proportional [BLOCKER]
- **Datei:** `services/report_healer.py` L2832-2920 (SEGMENT_BUDGETS → "team")
- **Problem:** 10 Sections haben Budgets bei 30-50% von KMU statt der angestrebten 75%
- **Betroffene Sections:** EXECUTIVE_SUMMARY (3000→4500), PILOT_PLAN (1800→3750), DATA_READINESS (1800→4500), MONETARISIERUNG (1800→3000), KI_SKILLPLAN (1800→3000), TECHNOLOGIE_PROZESSE (3000→6000), SOFORT_START (2000→6000), UNTERNEHMENSPROFIL_MARKT (5000→10500), STRATEGIE_GOVERNANCE (5000→7500), TEMPLATES_START (3500→6000)
- **Risiko:** 10/10
- **Empfohlene Werte:** Alle auf 75% der KMU-B36a-Werte setzen (siehe Tabelle 2.3)

#### K3: Solo SIZE_PROFILES Budgets zu niedrig für GLOBAL-TRUNCATION [BLOCKER]
- **Datei:** `config/size_profiles.py` L67-100 (solo → section_budgets)
- **Problem:** Solo SP-Budgets liegen bei 9-38% von KMU. Da GLOBAL-TRUNCATION diese Werte nutzt, wird Content VOR dem Healer bereits zu stark gekürzt.
- **Betroffene Sections:** GAMECHANGER (1500 → 8800), STRATEGIE_GOVERNANCE (3000 → 9900), TOOLS_EMPFEHLUNGEN (3000 → 9900), FOERDERPOTENZIAL (3000 → 9900), UNTERNEHMENSPROFIL_MARKT (3000 → 8800), ORG_CHANGE (3000 → 8800)
- **Risiko:** 9/10
- **Aber:** GAMECHANGER, RISKS, RECOMMENDATIONS sind `BUDGET_EXEMPT` im Healer. Dennoch begrenzt GLOBAL-TRUNCATION den Content vor dem Healer.
- **Hinweis:** Solo-Sections sollen bewusst kürzer sein als KMU. 55% von KMU ist ein guter Ausgangspunkt, aber einige Solo-Sections (z.B. GAMECHANGER) brauchen möglicherweise weniger weil der Report insgesamt kompakter ist. **Log-Validierung empfohlen.**

#### K4: Fehlende Solo/Team Plaintext-Budgets [BLOCKER für "roadmap", "ki_stack_summary"]
- **Datei:** `services/report_healer.py` — Solo/Team Sections
- **Problem:** KMU hat 17 Plaintext-Budgets (L3022-3038), Solo/Team haben 0
- **Kritischste Keys:** `"roadmap"` → `_default`=1000 (statt KMU: 10000), `"ki_stack_summary"` → `_default`=1000 (statt KMU: 5000)
- **Risiko:** 8/10 (nur wenn Plaintext-Keys genutzt werden, meistens kommen HTML-Keys)

### Priorität 2: Inkonsistenzen die Truncation verursachen könnten

#### K5: WP4 Compact Guard kann B36-Erhöhungen zunichte machen
- **Datei:** `services/solo_compact_engine.py` L650-664
- **Problem:** HTML-Größen-Schwellen (solo:300KB, team:500KB, kmu:550KB) wurden bei B36 nicht angepasst. Größere Section-Budgets → mehr HTML → eher Compact Guard Trigger.
- **Risiko:** 6/10 (nur relevant wenn Gesamtgröße Schwelle überschreitet)
- **Aktueller Wert:** kmu=550KB
- **Empfehlung:** Nach B37-Budget-Erhöhungen Monitoring der HTML-Gesamtgröße, ggf. KMU-Schwelle auf 650KB erhöhen

#### K6: FIX-B726-COMPACT entfernt gleiche Sections für alle Segmente
- **Datei:** `gpt_analyze.py` L17062-17087
- **Problem:** 14 Appendix-Sections werden für solo, team UND kmu identisch entfernt
- **Risiko:** 5/10 (wahrscheinlich gewollt, aber KMU hat mehr Seitenbudget → könnte mehr Sections behalten)
- **Empfehlung:** Differenzierung prüfen — KMU könnte GLOSSAR_HTML und KICKOFF_VORLAGE_HTML behalten

#### K7: Team SIZE_PROFILES teilweise unter 75% von KMU
- **Datei:** `config/size_profiles.py` L157-190 (team → section_budgets)
- **Problem:** Team SP-Budgets liegen bei 50-67% von KMU statt 75% für: EXECUTIVE_SUMMARY (7000/14000=50%), RECOMMENDATIONS (10000/20000=50%), STRATEGIE_GOVERNANCE (9000/18000=50%)
- **Risiko:** 5/10 (GLOBAL-TRUNCATION nutzt diese Werte)
- **Empfehlung:** Team SP-Budgets auf 75% von KMU anheben

#### K8: text_healing.py universelle 50-Wort-Grenze
- **Datei:** `services/text_healing.py` L1032
- **Problem:** `truncate_to_complete_sentence(max_words=50)` schneidet ALLE Absätze auf 50 Wörter — segment-unabhängig
- **Risiko:** 4/10 (wird aus `_aggressive_text_truncation` in gpt_analyze.py aufgerufen, greift nur bei AGGRESSIVE-TRUNCATION)

#### K9: content_quality_enforcer solo 500-Wort-Floor für RISKS
- **Datei:** `services/content_quality_enforcer.py` L3566
- **Problem:** `apply_risks_solo_padding()` erzwingt min 500 Wörter für RISKS_HTML bei Solo — hardcodiert, nicht aus SIZE_PROFILES
- **Risiko:** 3/10 (RISKS ist BUDGET_EXEMPT, daher kein Truncation-Konflikt; aber könnte zu unerwartet langem Content führen)

#### K10: report_validator.py MIN_SECTION_LENGTH_BY_SIZE weicht von SIZE_PROFILES ab
- **Datei:** `services/report_validator.py` L750-806
- **Problem:** Validator hat eigene min_words-Tabelle die teilweise von SIZE_PROFILES abweicht
  - Validator team executive_summary: 120 vs SP: 140
  - Validator team tools_empfehlungen: 190 vs SP: 190 (OK)
  - Validator team transparency_box: 150 vs SP: 120
- **Risiko:** 3/10 (kleine Abweichungen, Validator ist weniger strikt)

### Priorität 3: Nice-to-have Optimierungen

#### K11: Solo _default Budget sehr niedrig
- **Datei:** `services/report_healer.py` L2830
- **Problem:** Solo `_default`=1000 chars, KMU `_default`=3000. Jede ungemappte Section bekommt nur 1000 chars.
- **Risiko:** 2/10 (betrifft nur Sections ohne expliziten Budget-Eintrag)
- **Empfehlung:** Solo `_default` auf 1650 (55% von 3000)

#### K12: _SECTION_MAX_TOKENS nicht segment-abhängig
- **Datei:** `gpt_analyze.py` L1289-1333
- **Problem:** LLM generiert für alle Segmente gleich viel Content (5000-8000 tokens). Dann wird für Solo/Team 50-78% davon gelöscht.
- **Risiko:** 2/10 (funktional korrekt, aber ineffizient — kostet unnötige API-Tokens)
- **Empfehlung:** Langfristig segment-abhängige Token-Limits für LLM-Calls

#### K13: Legacy platin_min_words nicht segment-abhängig
- **Datei:** `gpt_analyze.py` L11772-11793
- **Problem:** `platin_min_words` Dictionary nutzt fixe Werte (z.B. gamechanger=850) für alle Segmente, obwohl Solo nur 100 min_words hat
- **Risiko:** 2/10 (triggert nur 2-Pass-Expand, generiert mehr Content der dann sowieso getrimmt wird)

---

## 4. Implementierungsplan

### FIX-B37a: Solo SEGMENT_BUDGETS proportional erhöhen [BLOCKER]

**Datei:** `services/report_healer.py` — SEGMENT_BUDGETS → "solo"

Alle Werte auf **55% der KMU-B36a-Werte** setzen (aufgerundet auf 100er):

```python
"solo": {
    "EXECUTIVE_SUMMARY_HTML": 3300,    # war 2000, 55% von 6000
    "QUICK_WINS_HTML": 8000,           # bleibt (67% > 55%)
    "QUICK_WINS_HTML_LEFT": 8000,      # bleibt
    "ROADMAP_90D_HTML": 5000,          # bleibt (63% > 55%)
    "ROADMAP_12M_HTML": 8000,          # bleibt (57% ≈ 55%)
    "RECOMMENDATIONS_HTML": 8300,      # war 6000, 55% von 15000
    "RISKS_HTML": 35000,              # BUDGET_EXEMPT, bleibt
    "GAMECHANGER_HTML": 1500,          # BUDGET_EXEMPT, bleibt
    "FOERDERPOTENZIAL_HTML": 6600,     # war 5000, 55% von 12000
    "ORG_CHANGE_HTML": 5500,           # war 4000, 55% von 10000
    "BUSINESS_CASE_HTML": 10000,       # bleibt (BUSINESS_CASE hat FIX-BC1 Override)
    "PILOT_PLAN_HTML": 2800,           # war 1200, 55% von 5000
    "DATA_READINESS_HTML": 3300,       # war 1200, 55% von 6000
    "STRATEGIE_GOVERNANCE_HTML": 5500, # war 5000, 55% von 10000
    "UNTERNEHMENSPROFIL_MARKT_HTML": 7700,  # war 5000, 55% von 14000
    "MONETARISIERUNG_HTML": 2200,      # war 1200, 55% von 4000
    "KI_SKILLPLAN_HTML": 2200,         # war 1200, 55% von 4000
    "TOOLS_EMPFEHLUNGEN_HTML": 5000,   # bleibt (63% > 55%)
    "TECHNOLOGIE_PROZESSE_HTML": 4400, # war 2000, 55% von 8000
    # ... Engine-Sections bleiben ...
    "BRANCH_DEEP_DIVE_HTML": 12000,    # bleibt (86% > 55%)
    "AI_ACT_SUMMARY_HTML": 3300,       # war 2000, 55% von 6000
    "TEMPLATES_START_HTML": 4400,      # war 2500, 55% von 8000
    "SOFORT_START_HTML": 4400,         # war 1500, 55% von 8000
    "WETTBEWERB_BENCHMARK_HTML": 5000, # bleibt (63%)
    "KI_AKTIVITAETEN_ZIELE_HTML": 2800, # war 2000, 55% von 5000
    "_default": 1650,                  # war 1000, 55% von 3000
}
```

### FIX-B37b: Team SEGMENT_BUDGETS proportional erhöhen [BLOCKER]

**Datei:** `services/report_healer.py` — SEGMENT_BUDGETS → "team"

Alle Werte auf **75% der KMU-B36a-Werte** setzen (aufgerundet):

```python
"team": {
    "EXECUTIVE_SUMMARY_HTML": 4500,    # war 3000, 75% von 6000
    "QUICK_WINS_HTML": 10000,          # bleibt (83% > 75%)
    "QUICK_WINS_HTML_LEFT": 10000,     # bleibt
    "ROADMAP_90D_HTML": 6000,          # war 5000, 75% von 8000
    "ROADMAP_12M_HTML": 12000,         # bleibt (86% > 75%)
    "RECOMMENDATIONS_HTML": 12000,     # bleibt (80% > 75%)
    "RISKS_HTML": 35000,              # BUDGET_EXEMPT, bleibt
    "GAMECHANGER_HTML": 10000,         # BUDGET_EXEMPT, bleibt
    "FOERDERPOTENZIAL_HTML": 12000,    # bleibt (100% > 75%)
    "ORG_CHANGE_HTML": 9000,           # bleibt (90% > 75%)
    "BUSINESS_CASE_HTML": 8000,        # bleibt (80% > 75%)
    "PILOT_PLAN_HTML": 3800,           # war 1800, 75% von 5000
    "DATA_READINESS_HTML": 4500,       # war 1800, 75% von 6000
    "STRATEGIE_GOVERNANCE_HTML": 7500, # war 5000, 75% von 10000
    "UNTERNEHMENSPROFIL_MARKT_HTML": 10500, # war 5000, 75% von 14000
    "MONETARISIERUNG_HTML": 3000,      # war 1800, 75% von 4000
    "KI_SKILLPLAN_HTML": 3000,         # war 1800, 75% von 4000
    "TOOLS_EMPFEHLUNGEN_HTML": 6000,   # war 5000, 75% von 8000
    "TECHNOLOGIE_PROZESSE_HTML": 6000, # war 3000, 75% von 8000
    # ... Engine-Sections bleiben ...
    "BRANCH_DEEP_DIVE_HTML": 10500,    # war 6000, 75% von 14000
    "AI_ACT_SUMMARY_HTML": 4500,       # war 3000, 75% von 6000
    "TEMPLATES_START_HTML": 6000,      # war 3500, 75% von 8000
    "SOFORT_START_HTML": 6000,         # war 2000, 75% von 8000
    "WETTBEWERB_BENCHMARK_HTML": 8000, # bleibt (100% ≥ 75%)
    "KI_AKTIVITAETEN_ZIELE_HTML": 3800, # war 3000, 75% von 5000
    "_default": 2250,                  # war 1500, 75% von 3000
}
```

### FIX-B37c: Solo/Team Plaintext-Budgets hinzufügen [HOCH]

**Datei:** `services/report_healer.py` — SEGMENT_BUDGETS → "solo" und "team"

17 Plaintext-Einträge analog zu KMU hinzufügen (proportional):

```python
# Solo (55% von KMU):
"executive_summary": 2200,    "strategie_governance": 4400,
"technologie_prozesse": 3300,  "tools_empfehlungen": 3300,
"templates_start": 3300,       "branch_deep_dive": 6600,
"unternehmensprofil_markt": 5500, "roadmap": 5500,
"roadmap_90d": 3300,           "data_readiness": 2800,
"ki_stack_summary": 2800,      "pilot_plan": 2200,
"monetarisierung": 1650,       "ki_skillplan": 1650,
"org_change": 4400,            "business_case": 4400,
"foerderpotenzial": 5500,

# Team (75% von KMU):
"executive_summary": 3000,    "strategie_governance": 6000,
"technologie_prozesse": 4500,  "tools_empfehlungen": 4500,
"templates_start": 4500,       "branch_deep_dive": 9000,
"unternehmensprofil_markt": 7500, "roadmap": 7500,
"roadmap_90d": 4500,           "data_readiness": 3800,
"ki_stack_summary": 3800,      "pilot_plan": 3000,
"monetarisierung": 2250,       "ki_skillplan": 2250,
"org_change": 6000,            "business_case": 6000,
"foerderpotenzial": 7500,
```

### FIX-B37d: Solo SIZE_PROFILES Budgets anpassen [HOCH]

**Datei:** `config/size_profiles.py` — SIZE_PROFILES → "solo" → section_budgets

Die Solo-SP-Budgets sind zu niedrig für die GLOBAL-TRUNCATION. Anpassen auf **55% von KMU-SP**:

```python
# Nur Sections anpassen die unter 55% liegen:
"EXECUTIVE_SUMMARY_HTML": 7700,    # war 4000, 55% von 14000
"RECOMMENDATIONS_HTML": 11000,     # war 3000, 55% von 20000
"FOERDERPOTENZIAL_HTML": 9900,     # war 3000, 55% von 18000
"ORG_CHANGE_HTML": 8800,           # war 3000, 55% von 16000
"STRATEGIE_GOVERNANCE_HTML": 9900, # war 3000, 55% von 18000
"UNTERNEHMENSPROFIL_MARKT_HTML": 8800, # war 3000, 55% von 16000
"TOOLS_EMPFEHLUNGEN_HTML": 9900,   # war 3000, 55% von 18000
"TECHNOLOGIE_PROZESSE_HTML": 6600, # war 3000, 55% von 12000
"PILOT_PLAN_HTML": 4400,           # war 3000, 55% von 8000
"DATA_READINESS_HTML": 5500,       # war 3000, 55% von 10000
"MONETARISIERUNG_HTML": 4400,      # war 3000, 55% von 8000
"KI_SKILLPLAN_HTML": 4400,         # war 3000, 55% von 8000
"GAMECHANGER_HTML": 8800,          # war 1500, 55% von 16000
"RISKS_HTML": 9900,                # war 7000, 55% von 18000
```

**ACHTUNG:** Solo-SP-Erhöhungen müssen mit dem max_pages=25 Solo-Limit und dem 300KB HTML-Threshold kompatibel bleiben. **Log-basierte Validierung ERFORDERLICH** vor Deployment!

### FIX-B37e: Team SIZE_PROFILES Budgets nachziehen [MITTEL]

**Datei:** `config/size_profiles.py` — SIZE_PROFILES → "team" → section_budgets

Team SP auf 75% von KMU-SP anheben wo < 75%:

```python
"EXECUTIVE_SUMMARY_HTML": 10500,   # war 7000, 75% von 14000
"RECOMMENDATIONS_HTML": 15000,     # war 10000, 75% von 20000
"STRATEGIE_GOVERNANCE_HTML": 13500, # war 9000, 75% von 18000
"TOOLS_EMPFEHLUNGEN_HTML": 13500,  # war 9000, 75% von 18000
"GAMECHANGER_HTML": 12000,         # war 8000, 75% von 16000
"FOERDERPOTENZIAL_HTML": 13500,    # war 9000, 75% von 18000
"ORG_CHANGE_HTML": 12000,          # war 8000, 75% von 16000
"BUSINESS_CASE_HTML": 12000,       # war 8000, 75% von 16000
"UNTERNEHMENSPROFIL_MARKT_HTML": 12000, # war 8000, 75% von 16000
```

### FIX-B37f: sanity_check_profiles erweitern [NICE-TO-HAVE]

**Datei:** `config/size_profiles.py` — `sanity_check_profiles()`

Zusätzliche Prüfungen einbauen:
1. Solo-Budget >= 55% von KMU-Budget (±5% Toleranz)
2. Team-Budget >= 75% von KMU-Budget (±5% Toleranz)
3. Healer SEGMENT_BUDGETS >= SIZE_PROFILES für gleiche Section+Segment

---

## 5. Empfehlung

### Sofort ändern (vor nächstem Deploy):
1. **FIX-B37a** + **FIX-B37b**: Healer SEGMENT_BUDGETS Solo/Team proportional erhöhen → `services/report_healer.py`
2. **FIX-B37c**: Plaintext-Budgets für Solo/Team hinzufügen → `services/report_healer.py`

### Nach Testrun ändern:
3. **FIX-B37d**: Solo SIZE_PROFILES anpassen → `config/size_profiles.py`
   - **Risiko:** Könnte Solo-Reports über max_pages=25 / 300KB treiben
   - **Vorher:** Einen Solo-Testrun mit aktuellen Werten + Logging der HTML-Größe
4. **FIX-B37e**: Team SIZE_PROFILES nachziehen → `config/size_profiles.py`

### Nicht jetzt (Monitoring + langfristig):
5. FIX-B726-COMPACT Segment-Differenzierung (K6)
6. Segment-abhängige _SECTION_MAX_TOKENS (K12)
7. WP4 Compact Guard Schwellen-Monitoring (K5)

### Dateien die NICHT geändert werden müssen:
- `b25_enforcer.py` — Keine segment-abhängige Budget-Logik
- `services/text_healing.py` — Keine segment-abhängige Logik
- `services/pipeline_sanitizers.py` — Keine segment-abhängige Logik
- `services/report_renderer.py` — Nur Labels, keine Budgets
- `services/solo_final_pass.py` — Nur Sprach-Normalisierung, keine Budgets

---

## 6. Risiko-Zusammenfassung

| FIX | Risiko | Impact | Dateien | Aufwand |
|-----|--------|--------|---------|---------|
| B37a | 10/10 | Solo-Content 50-78% zu kurz | report_healer.py | ~30 min |
| B37b | 10/10 | Team-Content 50-78% zu kurz | report_healer.py | ~30 min |
| B37c | 8/10 | Plaintext-Sections auf _default | report_healer.py | ~15 min |
| B37d | 9/10 | GLOBAL-TRUNCATION killt Solo-Content | size_profiles.py | ~20 min (+ Testrun) |
| B37e | 5/10 | GLOBAL-TRUNCATION limitiert Team | size_profiles.py | ~15 min |
| B37f | 2/10 | Keine automatische Konsistenz-Prüfung | size_profiles.py | ~30 min |

---

## 7. Anhang: Vollständige Datei-Abhängigkeiten

```
gpt_analyze.py (20151 Zeilen)
├── GLOBAL-TRUNCATION (L13415) → config/size_profiles.py::get_section_budget()
├── POST-TRIM-HEAL (L13561) → config/size_profiles.py::get_min_words()
├── FIX-B726-COMPACT (L17062) → Entfernt 14 Sections für alle Segmente
├── FIX-629 POST-TRIM-HEAL (L15988) → config/size_profiles.py::get_min_words()
├── COMPACT_REPORT_MODE (L8728) → solo+team=compact, kmu=full (aber B724 erzwingt auch kmu)
└── _SECTION_MAX_TOKENS (L1289) → NICHT segment-abhängig

services/report_healer.py
├── SEGMENT_BUDGETS (L2741) → Drei lokale Budget-Tabellen (solo/team/kmu)
├── apply_segment_budget() (L3045) → Hierarchie: SEGMENT_BUDGETS > SIZE_PROFILES > _default
├── BUDGET_EXEMPT_SECTIONS (L3077) → RISKS, GAMECHANGER, RECOMMENDATIONS, etc.
├── FIX-B36b Clean Ending (L3171) → Entfernt "..." Truncation-Artefakte
└── FIX-G Sentence Trimming (L3146) → Guard bei 80% von Budget

config/size_profiles.py
├── SIZE_PROFILES (L29) → section_budgets + min_words pro Segment
├── get_section_budget() (L356) → Wird von GLOBAL-TRUNCATION und POST-TRIM-HEAL genutzt
├── get_min_words() (L372) → Wird von GLOBAL-TRUNCATION, POST-TRIM-HEAL, Validator genutzt
└── sanity_check_profiles() (L388) → Prüft budget >= min_words * 7

services/solo_compact_engine.py
├── SOLO_COMPACT_WORD_LIMITS (L165) → max_words für Solo-Light-Sections
├── MAX_PAGES_BY_SIZE (L650) → solo=16, team=70, kmu=45
├── HTML_COMPACT_THRESHOLD_BY_SIZE (L661) → solo=300KB, team=500KB, kmu=550KB
└── TEAM_KMU_LOW_PRIORITY_SECTIONS (L670) → Sections die bei Compact gedroppt werden

services/content_quality_enforcer.py
├── SOLO_TERM_REPLACEMENTS (L28) → Enterprise-zu-Solo Sprach-Normalisierung
├── apply_risks_solo_padding() (L3549) → Hardcodierter 500-Wort-Floor für Solo RISKS
└── apply_risk_truncation() (L3474) → Hardcodierter 2500-Char-Limit für AI_ACT_SUMMARY

services/report_validator.py
├── MIN_SECTION_LENGTH_BY_SIZE (L750) → Eigene min_words pro Segment (teilweise ≠ SIZE_PROFILES)
├── MAX_REPORT_PAGES_BY_SIZE (L818) → solo=25, team=35, kmu=45
└── SIZE_FORBIDDEN (L528) → Segment-spezifische verbotene Begriffe
```
