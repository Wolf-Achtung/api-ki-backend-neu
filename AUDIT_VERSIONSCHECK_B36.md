# AUDIT: Versions-Check report_healer.py + SIZE_PROFILES Konflikt-Analyse

**Datum:** 2026-02-28
**Scope:** Versions-Identifikation report_healer.py, SIZE_PROFILES-Konflikte, Budget-Quellen, Compact-Schwellen
**Branch:** `claude/audit-pipeline-segments-9MYM3`

---

## 1. Versions-Ergebnis: VERSION V1 (nur KMU)

### Beweis-Tabelle

| Check | Erwartung FINAL | Ist-Wert | Match? |
|-------|----------------|----------|--------|
| CHECK 1: `FIX-B36a` Treffer | ≥20 | **20** | OK |
| CHECK 2: KMU STRATEGIE_GOVERNANCE | 10000 | **10000** (L2940) | OK |
| CHECK 3: Solo EXECUTIVE_SUMMARY | 3500 | **2000** (L2743) | **FAIL** |
| CHECK 4: Plaintext-Budgets solo/team | vorhanden | **nur KMU** (L3022-3038) | **FAIL** |
| CHECK 5: `FIX-B36b` Treffer | ≥2 | **2** | OK |
| CHECK 6: `_default` solo/team/kmu | 1500/2000/3000 | **1000/1500/3000** (L2830/2920/3040) | **FAIL** |

### Diagnose

```
CHECK 1: FIX-B36a = 20 Treffer                    → B36a-Kommentare vorhanden ✓
CHECK 2: KMU STRATEGIE_GOVERNANCE = 10000 (L2940)  → KMU-Budgets erhöht ✓
CHECK 3: Solo EXECUTIVE_SUMMARY = 2000 (L2743)     → Solo NICHT erhöht ✗ (soll 3500)
         Team EXECUTIVE_SUMMARY = 3000 (L2833)     → Team NICHT erhöht ✗ (soll 4500)
CHECK 4: Plaintext-Budgets nur in KMU (L3022-3038) → Solo/Team haben KEINE ✗
CHECK 5: FIX-B36b = 2 Treffer                      → Clean Ending vorhanden ✓
CHECK 6: _default solo=1000 (L2830)                 → NICHT erhöht ✗ (soll 1500)
         _default team=1500 (L2920)                 → NICHT erhöht ✗ (soll 2000)
         _default kmu=3000 (L3040)                  → Korrekt ✓
```

### Fazit

**VERSION V1 (nur KMU):** FIX-B36a ist vorhanden und hat die KMU-Budgets korrekt erhöht.
Aber Solo- und Team-Budgets wurden **NICHT** aktualisiert:
- Solo EXECUTIVE_SUMMARY steht bei 2000 statt 3500
- Team EXECUTIVE_SUMMARY steht bei 3000 statt 4500
- Solo/Team haben keine Plaintext-Budgets
- Solo/Team `_default` nicht erhöht

**Aktion:** Solo+Team Budgets fehlen. FINAL-Version muss deployed werden.

---

## 2. SIZE_PROFILES Konflikt-Tabelle

### Erklärung der Spalten
- **SP** = `config/size_profiles.py` → `SIZE_PROFILES[segment]["section_budgets"]`
- **Healer** = `services/report_healer.py` → `SEGMENT_BUDGETS[segment]`
- **Konflikt** = SP < Healer bedeutet: GLOBAL-TRUNCATION (gpt_analyze.py L13461) kürzt Content auf SP-Wert, BEVOR der Healer ihn sieht. Der höhere Healer-Wert ist dann wirkungslos.

### Solo: SIZE_PROFILES vs Healer SEGMENT_BUDGETS

| Section | SP solo | Healer solo | SP < Healer? | Impact |
|---------|---------|-------------|--------------|--------|
| EXECUTIVE_SUMMARY_HTML | 4000 (L68) | 2000 (L2743) | Nein | Healer ist Bottleneck |
| STRATEGIE_GOVERNANCE_HTML | 3000 (L81) | 5000 (L2756) | **JA: -2000** | SP killt Content vor Healer |
| TECHNOLOGIE_PROZESSE_HTML | 3000 (L86) | 2000 (L2761) | Nein | Healer ist Bottleneck |
| UNTERNEHMENSPROFIL_MARKT_HTML | 3000 (L82) | 5000 (L2757) | **JA: -2000** | SP killt Content vor Healer |
| PILOT_PLAN_HTML | 3000 (L79) | 1200 (L2754) | Nein | Healer ist Bottleneck |
| DATA_READINESS_HTML | 3000 (L80) | 1200 (L2755) | Nein | Healer ist Bottleneck |
| TOOLS_EMPFEHLUNGEN_HTML | 3000 (L85) | 5000 (L2760) | **JA: -2000** | SP killt Content vor Healer |
| TEMPLATES_START_HTML | _(kein SP-Eintrag)_ | 2500 (L2782) | **JA** | SP→_default=1000 (L99) |
| SOFORT_START_HTML | _(kein SP-Eintrag)_ | 1500 (L2794) | **JA** | SP→_default=1000 (L99) |
| BRANCH_DEEP_DIVE_HTML | 3000 (L92) | 12000 (L2774) | **JA: -9000** | SP killt 75% vor Healer |
| GAMECHANGER_HTML | 1500 (L75) | 1500 (L2750) | Gleich | Healer EXEMPT (L3077) |
| RECOMMENDATIONS_HTML | 3000 (L73) | 6000 (L2748) | **JA: -3000** | SP killt Content vor Healer |
| FOERDERPOTENZIAL_HTML | 3000 (L76) | 5000 (L2751) | **JA: -2000** | SP killt Content vor Healer |
| ORG_CHANGE_HTML | 3000 (L77) | 4000 (L2752) | **JA: -1000** | SP killt Content vor Healer |
| QUICK_WINS_HTML | 8000 (L69) | 8000 (L2744) | Gleich | OK |
| ROADMAP_12M_HTML | 8000 (L72) | 8000 (L2747) | Gleich | OK |
| MONETARISIERUNG_HTML | 3000 (L83) | 1200 (L2758) | Nein | Healer ist Bottleneck |
| KI_SKILLPLAN_HTML | 3000 (L84) | 1200 (L2759) | Nein | Healer ist Bottleneck |

**Solo-Konflikte: 8 Sections** wo SP den Content vor dem Healer beschneidet.

Besonders kritisch:
- `BRANCH_DEEP_DIVE_HTML`: SP=3000 vs Healer=12000 → SP killt 75% des Contents
- `RECOMMENDATIONS_HTML`: SP=3000 vs Healer=6000 → SP killt 50% (aber BUDGET_EXEMPT im Healer!)
- `TEMPLATES_START_HTML`: SP=_default(1000) vs Healer=2500 → kein SP-Eintrag!
- `SOFORT_START_HTML`: SP=_default(1000) vs Healer=1500 → kein SP-Eintrag!

**Wichtig:** GAMECHANGER_HTML, RISKS_HTML, RECOMMENDATIONS_HTML sind `BUDGET_EXEMPT_SECTIONS` im Healer (L3077). Für diese greift NUR der SP-Wert via GLOBAL-TRUNCATION.

### Team: SIZE_PROFILES vs Healer SEGMENT_BUDGETS

| Section | SP team | Healer team | SP < Healer? | Impact |
|---------|---------|-------------|--------------|--------|
| EXECUTIVE_SUMMARY_HTML | 7000 (L158) | 3000 (L2833) | Nein | Healer ist Bottleneck |
| STRATEGIE_GOVERNANCE_HTML | 9000 (L171) | 5000 (L2846) | Nein | Healer ist Bottleneck |
| TECHNOLOGIE_PROZESSE_HTML | 8000 (L176) | 3000 (L2851) | Nein | Healer ist Bottleneck |
| UNTERNEHMENSPROFIL_MARKT_HTML | 8000 (L172) | 5000 (L2847) | Nein | Healer ist Bottleneck |
| PILOT_PLAN_HTML | 6000 (L169) | 1800 (L2844) | Nein | Healer ist Bottleneck |
| DATA_READINESS_HTML | 8000 (L170) | 1800 (L2845) | Nein | Healer ist Bottleneck |
| TOOLS_EMPFEHLUNGEN_HTML | 9000 (L175) | 5000 (L2850) | Nein | Healer ist Bottleneck |
| TEMPLATES_START_HTML | _(kein SP-Eintrag)_ | 3500 (L2872) | **JA** | SP→_default=2500 (L189) |
| SOFORT_START_HTML | _(kein SP-Eintrag)_ | 2000 (L2884) | Nein | SP→_default=2500 > 2000 |
| BRANCH_DEEP_DIVE_HTML | 8000 (L182) | 6000 (L2864) | Nein | Healer ist Bottleneck |
| GAMECHANGER_HTML | 8000 (L165) | 10000 (L2840) | **JA: -2000** | Healer EXEMPT, SP ist Limit |
| RECOMMENDATIONS_HTML | 10000 (L163) | 12000 (L2838) | **JA: -2000** | Healer EXEMPT, SP ist Limit |
| FOERDERPOTENZIAL_HTML | 9000 (L166) | 12000 (L2841) | **JA: -3000** | SP killt Content vor Healer |
| ORG_CHANGE_HTML | 8000 (L167) | 9000 (L2842) | **JA: -1000** | SP killt Content vor Healer |
| QUICK_WINS_HTML | 7000 (L159) | 10000 (L2834) | **JA: -3000** | SP killt Content vor Healer |
| ROADMAP_12M_HTML | 8500 (L162) | 12000 (L2837) | **JA: -3500** | SP killt Content vor Healer |
| MONETARISIERUNG_HTML | 6000 (L173) | 1800 (L2848) | Nein | Healer ist Bottleneck |
| KI_SKILLPLAN_HTML | 6000 (L174) | 1800 (L2849) | Nein | Healer ist Bottleneck |

**Team-Konflikte: 7 Sections** wo SP den Content vor dem Healer beschneidet.

Besonders kritisch:
- `ROADMAP_12M_HTML`: SP=8500 vs Healer=12000 → 3500 chars unnötig gelöscht
- `QUICK_WINS_HTML`: SP=7000 vs Healer=10000 → 3000 chars unnötig gelöscht
- `FOERDERPOTENZIAL_HTML`: SP=9000 vs Healer=12000 → 3000 chars unnötig gelöscht

### KMU: SIZE_PROFILES vs Healer SEGMENT_BUDGETS

| Section | SP kmu | Healer kmu (B36a) | SP < Healer? | Impact |
|---------|--------|-------------------|--------------|--------|
| EXECUTIVE_SUMMARY_HTML | 14000 (L243) | 6000 (L2927) | Nein | Healer ist Bottleneck |
| STRATEGIE_GOVERNANCE_HTML | 18000 (L256) | 10000 (L2940) | Nein | Healer ist Bottleneck |
| TECHNOLOGIE_PROZESSE_HTML | 12000 (L261) | 8000 (L2945) | Nein | Healer ist Bottleneck |
| UNTERNEHMENSPROFIL_MARKT_HTML | 16000 (L257) | 14000 (L2941) | Nein | Healer ist Bottleneck |
| PILOT_PLAN_HTML | 8000 (L254) | 5000 (L2938) | Nein | Healer ist Bottleneck |
| DATA_READINESS_HTML | 10000 (L255) | 6000 (L2939) | Nein | Healer ist Bottleneck |
| TOOLS_EMPFEHLUNGEN_HTML | 18000 (L260) | 8000 (L2944) | Nein | Healer ist Bottleneck |
| TEMPLATES_START_HTML | _(kein SP-Eintrag)_ | 8000 (L2970) | **JA** | SP→_default=3000 (L263) |
| SOFORT_START_HTML | _(kein SP-Eintrag)_ | 8000 (L2982) | **JA** | SP→_default=3000 (L263) |
| BRANCH_DEEP_DIVE_HTML | _(kein SP-Eintrag)_ | 14000 (L2962) | **JA** | SP→_default=3000 (L263) |

**KMU-Konflikte: 3 Sections** ohne SP-Eintrag, aber mit hohem Healer-Budget.

**Kritisch:** `BRANCH_DEEP_DIVE_HTML` hat SP=_default(3000) vs Healer=14000.
Da BRANCH_DEEP_DIVE im `truncation_targets` steht (gpt_analyze.py L13421), wird der Content
auf 3000 chars begrenzt, obwohl der Healer 14000 erlaubt.

**Hinweis:** `TEMPLATES_START_HTML` und `SOFORT_START_HTML` stehen NICHT in `truncation_targets` (L13418-13422), daher greift die SP-Begrenzung für diese Sections NICHT via GLOBAL-TRUNCATION. Der Healer-Wert ist maßgeblich.

---

## 3. gpt_analyze.py Budget-Quellen

### 3.1 GLOBAL-TRUNCATION (L13415-13559)

```
Quelle:  config/size_profiles.py → get_section_budget(segment, key)
Import:  L13427: from config.size_profiles import get_section_budget, get_min_words
Aufruf:  L13461: _budget = get_section_budget(_trunc_segment, key)
```

**Antwort auf Kernfrage:** JA — gpt_analyze.py nutzt `SIZE_PROFILES.section_budgets` direkt als Budget-Quelle für GLOBAL-TRUNCATION.

**Konsequenz:** Wenn SIZE_PROFILES niedrigere Werte hat als SEGMENT_BUDGETS im Healer, wird Content VOR dem Healer beschnitten. Die B36-Erhöhungen im Healer sind dann **wirkungslos** für die betroffenen Sections.

### 3.2 Truncation Targets (L13418-13422)

Nur diese 14 Sections durchlaufen GLOBAL-TRUNCATION:
```
RISKS_HTML, GAMECHANGER_HTML, FOERDERPOTENZIAL_HTML, RECOMMENDATIONS_HTML,
ORG_CHANGE_HTML, BUSINESS_CASE_HTML, PILOT_PLAN_HTML, ROADMAP_12M_HTML,
DATA_READINESS_HTML, STRATEGIE_GOVERNANCE_HTML, UNTERNEHMENSPROFIL_MARKT_HTML,
MONETARISIERUNG_HTML, KI_SKILLPLAN_HTML, QUICK_WINS_HTML
```

**NICHT in Targets** (keine GLOBAL-TRUNCATION):
```
EXECUTIVE_SUMMARY_HTML, ROADMAP_90D_HTML, TOOLS_EMPFEHLUNGEN_HTML,
TECHNOLOGIE_PROZESSE_HTML, BRANCH_DEEP_DIVE_HTML*, TEMPLATES_START_HTML,
SOFORT_START_HTML, WETTBEWERB_BENCHMARK_HTML, KI_AKTIVITAETEN_ZIELE_HTML
```

*BRANCH_DEEP_DIVE_HTML steht in der target-Liste (L13421)!

### 3.3 Budget-Override: FIX-BC1 (L13462-13466)

```python
if key in ("BUSINESS_CASE_HTML", "business_case") and _budget < 5000:
    _budget = 5000  # Override für zu enge Budgets
```

Dies ist der EINZIGE hardcodierte Budget-Override in GLOBAL-TRUNCATION.

### 3.4 POST-TRIM-HEAL (L13561-13664 + L15987-16053)

Zwei separate Healing-Loops:

**Loop 1** (L13561): Nach GLOBAL-TRUNCATION, 4 kritische Sections:
```python
_heal_critical_sections = ["gamechanger", "roadmap_12m", "executive_summary", "tools_empfehlungen"]
```
- Nutzt `get_min_words()` aus SIZE_PROFILES
- Max 2 Iterationen
- Heilt Sections die unter min_words gefallen sind

**Loop 2** (L15987, FIX-629): POST-TRIM-HEAL Guard, 4 kritische Sections:
```python
_HEAL_CRITICAL_SECTIONS = ["executive_summary", "tools_empfehlungen", "gamechanger", "roadmap_12m"]
```
- Gleiche 4 Sections wie Loop 1
- Gap-Limit: innerhalb 30 Wörter unter Minimum (L16028)
- Expandiert auf min_words + 20

**Risiko:** Sections die NICHT in den Heal-Listen stehen (STRATEGIE_GOVERNANCE, TECHNOLOGIE_PROZESSE, PILOT_PLAN, DATA_READINESS, etc.) werden nach Truncation NICHT geheilt.

### 3.5 RESCUE LOOP (L16246)

Ein dritter Healing-Mechanismus für SECTION_TOO_SHORT Validierungsfehler:
- Hat KEIN Gap-Limit (anders als POST-TRIM-HEAL)
- Greift erst beim Quality Gate
- Erweitert jede Section die unter min_words steht

### 3.6 Vollständige Budget-Kette

```
LLM generiert Content
  ↓ (max_tokens: NICHT segment-abhängig, L1289)
  ↓
GLOBAL-TRUNCATION (gpt_analyze.py L13415)
  Budget-Quelle: SIZE_PROFILES.section_budgets ← HIER GREIFEN SP-WERTE
  Nur für 14 Sections in truncation_targets
  ↓
POST-TRIM-HEAL Loop 1 (gpt_analyze.py L13561)
  min_words-Quelle: SIZE_PROFILES.min_words
  Nur für 4 Sections: gamechanger, roadmap_12m, executive_summary, tools_empfehlungen
  ↓
Content Quality Enforcer (content_quality_enforcer.py)
  Segment-abhängig: Solo-Term-Replacement, Solo-RISKS-Padding
  ↓
POST-TRIM-HEAL Loop 2 (gpt_analyze.py L15987)
  min_words-Quelle: SIZE_PROFILES.min_words
  Nur für 4 Sections, nur innerhalb 30-Wort-Gap
  ↓
RESCUE LOOP (gpt_analyze.py L16246)
  Jede Section unter min_words, kein Gap-Limit
  ↓
Healer apply_segment_budget() (report_healer.py L3045)
  Budget-Quelle: SEGMENT_BUDGETS ← HIER GREIFEN HEALER-WERTE
  Hierarchie: exact > uppercase_HTML > SIZE_PROFILES fallback > _default
  ↓
BUDGET_EXEMPT bypass (L3077)
  RISKS, GAMECHANGER, RECOMMENDATIONS, VENDOR_AUDIT, etc.
  ↓
Sentence-Trimming FIX-G (report_healer.py L3146)
  Guard bei 80% von Budget
  ↓
FIX-B36b Clean Ending Check
  Entfernt "..." Truncation-Artefakte
  ↓
WP4 Compact Guard (solo_compact_engine.py L699)
  Post-Render, wenn HTML > KB/Seiten-Schwelle
```

---

## 4. solo_compact_engine.py Schwellenwerte

### 4.1 Compact-Auslösung (L650-664)

| Parameter | Solo | Team | KMU | Datei:Zeile |
|-----------|------|------|-----|-------------|
| MAX_PAGES | 16 | 70 | 45 | solo_compact_engine.py:650-654 |
| HTML_COMPACT_THRESHOLD_KB | 300 | 500 | 550 | solo_compact_engine.py:661-664 |

**Trigger-Logik** (L726-736):
```python
needs_compact = False
if size_kb > threshold:  needs_compact = True   # HTML > KB-Schwelle
if pages > max_pages:    needs_compact = True   # Seiten > Max
```

Beide Bedingungen sind ODER-verknüpft.

### 4.2 Solo-Kompaktierung: SOLO_COMPACT_WORD_LIMITS (L165-172)

Wenn Solo-Compact triggert, gelten diese **harten Wort-Limits**:

| Section | Word-Limit | ~Char-Äquivalent (×7) | Healer-Budget | Problem? |
|---------|-----------|----------------------|---------------|----------|
| EXECUTIVE_SUMMARY_HTML | 400 | ~2800 | 2000 | Nein (Healer enger) |
| QUICK_WINS_HTML | 600 | ~4200 | 8000 | **JA** — Compact killt 47% |
| ROADMAP_90D_HTML | 500 | ~3500 | 5000 | Nein (Compact enger) |
| ROADMAP_12M_HTML | 600 | ~4200 | 8000 | **JA** — Compact killt 47% |
| PILOT_PLAN_HTML | 400 | ~2800 | 1200 | Nein (Healer enger) |
| DATA_READINESS_HTML | 300 | ~2100 | 1200 | Nein (Healer enger) |

### 4.3 Risikoanalyse: B36-Budgets → Compact-Trigger

**Aktuelles Solo-HTML-Budget (Summe der Healer SEGMENT_BUDGETS):**
```
Solo Content-Sections:    ~130.000 chars ≈ 127KB (nur text, ohne HTML-Overhead)
Mit HTML-Overhead (×1.5):  ~190KB
Schwelle:                  300KB
Headroom:                  ~110KB (37%)
```

**Nach FINAL-Version (55% von KMU):**
```
Solo Content-Sections:    ~200.000 chars ≈ 195KB (geschätzt)
Mit HTML-Overhead (×1.5):  ~293KB
Schwelle:                  300KB
Headroom:                  ~7KB (2%) ← KRITISCH KNAPP!
```

**Antwort auf Kernfrage:** JA — nach FINAL B36-Deployment besteht ein **hohes Risiko** dass Solo die 300KB-Schwelle erreicht. Das würde die Solo-Kompaktierung auslösen, die dann QUICK_WINS und ROADMAP_12M auf 600 Wörter kürzt und weitere Sections droppt.

**Empfehlung:** Solo HTML_COMPACT_THRESHOLD auf 400KB erhöhen, BEVOR die Solo-Budgets erhöht werden.

### 4.4 Team/KMU WP4 Compact Guard

Wenn Team/KMU die Schwelle überschreitet, werden Low-Priority-Sections gedroppt (L670-683):
```
Tier 1: FUNDING_BRANCH_ALIGNMENT, TOOLS_FUNDING_ALIGNMENT, TOOLS_BRANCH_ALIGNMENT,
        AUTOMATION_ROADMAP, ROI_TRACKING, BUSINESS_CASE_SIM, KICKOFF
Tier 2: MARKET_INSIGHTS, NEWS_BOX
```

Zusätzlich werden zu lange Text-Blöcke (>800 chars) per Regex gekürzt (L791-800).

---

## 5. Empfehlung: Was muss als nächstes gefixt werden?

### Priorität 1: SOFORT (vor nächstem Deploy)

| # | Was | Wo | Warum |
|---|-----|-----|-------|
| **B37a** | Solo SEGMENT_BUDGETS auf 55% von KMU setzen | report_healer.py L2742-2830 | Solo-Content wird um 50-78% gekürzt |
| **B37b** | Team SEGMENT_BUDGETS auf 75% von KMU setzen | report_healer.py L2832-2920 | Team-Content wird um 50-78% gekürzt |
| **B37c** | Solo/Team Plaintext-Budgets hinzufügen | report_healer.py (neu, nach L2829/L2919) | "roadmap" etc. fallen auf _default=1000/1500 |
| **B37d** | Solo/Team `_default` erhöhen | report_healer.py L2830, L2920 | solo: 1000→1500, team: 1500→2000 |

### Priorität 2: VOR Solo-Budget-Deploy

| # | Was | Wo | Warum |
|---|-----|-----|-------|
| **B37e** | Solo HTML_COMPACT_THRESHOLD auf 400KB | solo_compact_engine.py L662 | Sonst triggert Compact bei ~300KB nach Budget-Erhöhung |

### Priorität 3: NACH Testrun

| # | Was | Wo | Warum |
|---|-----|-----|-------|
| **B37f** | Solo SIZE_PROFILES.section_budgets erhöhen | size_profiles.py L67-99 | 8 Sections wo SP < Healer → GLOBAL-TRUNCATION killt Content |
| **B37g** | Team SIZE_PROFILES.section_budgets nachziehen | size_profiles.py L157-189 | 7 Sections wo SP < Healer |
| **B37h** | KMU SP: BRANCH_DEEP_DIVE, TEMPLATES_START, SOFORT_START hinzufügen | size_profiles.py L242-263 | Fehlen komplett, fallen auf _default=3000 |
| **B37i** | Sanity-Check erweitern: SP ≥ Healer prüfen | size_profiles.py L388 | Automatische Erkennung von SP/Healer-Konflikten |

### Priorität 4: Monitoring

| # | Was | Wo | Warum |
|---|-----|-----|-------|
| **B37j** | HTML-Größe nach B37a/b loggen | gpt_analyze.py / report_renderer.py | Compact-Trigger-Risiko überwachen |
| **B37k** | POST-TRIM-HEAL auf alle Sections erweitern | gpt_analyze.py L13565, L16001 | Nur 4 Sections werden geheilt, viele andere fallen durch |

---

## 6. Zusammenfassung der Konflikte

```
┌─────────────────────────────────────────────────────────────────┐
│  SIZE_PROFILES (config/size_profiles.py)                        │
│  → Genutzt von: GLOBAL-TRUNCATION (gpt_analyze.py L13461)      │
│  → Problem: Solo-Werte zu niedrig (1500-3000 chars)             │
│  → 8 Solo-Konflikte, 7 Team-Konflikte, 3 KMU-Konflikte         │
│                                                                 │
│  GLOBAL-TRUNCATION kürzt auf SP-Wert                            │
│          ↓                                                      │
│  POST-TRIM-HEAL expandiert NUR 4 Sections                       │
│          ↓                                                      │
│  SEGMENT_BUDGETS (report_healer.py L2741)                       │
│  → Problem: Solo/Team noch auf pre-B36 Werten                   │
│  → Healer kürzt NOCHMAL auf niedrigere Werte                    │
│          ↓                                                      │
│  WP4 Compact Guard (solo_compact_engine.py L699)                │
│  → Risiko: Solo 300KB-Schwelle nach B37 knapp                   │
│  → Compact DROPPT ganze Sections oder kürzt auf 600 Wörter      │
│                                                                 │
│  DREIFACH-TRUNCATION für Solo/Team:                              │
│  GPT Output → SP-Cap → Healer-Cap → Compact-Cap                 │
│  Jeder Schritt kann Content vernichten                           │
└─────────────────────────────────────────────────────────────────┘
```
