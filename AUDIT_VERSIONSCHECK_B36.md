# AUDIT: Versions-Check report_healer.py + SIZE_PROFILES Konflikt-Analyse

**Datum:** 2026-02-28 (Re-Check)
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
| CHECK 3b: Team EXECUTIVE_SUMMARY | 4500 | **3000** (L2833) | **FAIL** |
| CHECK 4: Plaintext-Budgets solo/team | vorhanden | **nur KMU** (L3022-3038) | **FAIL** |
| CHECK 5: `FIX-B36b` Treffer | ≥2 | **2** | OK |
| CHECK 6: `_default` solo/team/kmu | 1500/2000/3000 | **1000/1500/3000** (L2830/L2920/L3040) | **FAIL** |

### Diagnose

```
CHECK 1: FIX-B36a = 20 Treffer                    → B36a-Kommentare vorhanden ✓
CHECK 2: KMU STRATEGIE_GOVERNANCE = 10000 (L2940)  → KMU-Budgets erhöht ✓
CHECK 3: Solo EXECUTIVE_SUMMARY = 2000 (L2743)     → Solo NICHT erhöht ✗ (soll 3500)
         Team EXECUTIVE_SUMMARY = 3000 (L2833)     → Team NICHT erhöht ✗ (soll 4500)
CHECK 4: Plaintext-Budgets nur in KMU (L3022-3038) → Solo/Team haben KEINE ✗
         Solo-Block L2742-2830: 0 lowercase keys (nur "_default")
         Team-Block L2832-2920: 0 lowercase keys (nur "_default")
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
- Solo/Team haben keine Plaintext-Budgets (17 fehlende Einträge)
- Solo/Team `_default` nicht erhöht (1000/1500 statt 1500/2000)

**Aktion:** Solo+Team Budgets fehlen. FINAL-Version muss deployed werden.

---

## 2. SIZE_PROFILES Konflikt-Tabelle

### Erklärung

- **SP** = `config/size_profiles.py` → `SIZE_PROFILES[segment]["section_budgets"]`
- **Healer IST** = `services/report_healer.py` → `SEGMENT_BUDGETS[segment]` (aktuell deployed, V1)
- **Healer SOLL** = Erwartete FINAL-Werte (aus Auftragskontext)
- **Konflikt** = SP < Healer bedeutet: GLOBAL-TRUNCATION kürzt Content VOR dem Healer

**WICHTIG — Wann greifen SP-Werte überhaupt?**

SP-Werte werden **NUR** via GLOBAL-TRUNCATION (gpt_analyze.py L13461) angewendet,
und **NUR** für Sections in `truncation_targets` (L13418-13422):
```
RISKS_HTML, GAMECHANGER_HTML, FOERDERPOTENZIAL_HTML, RECOMMENDATIONS_HTML,
ORG_CHANGE_HTML, BUSINESS_CASE_HTML, PILOT_PLAN_HTML, ROADMAP_12M_HTML,
DATA_READINESS_HTML, STRATEGIE_GOVERNANCE_HTML, UNTERNEHMENSPROFIL_MARKT_HTML,
MONETARISIERUNG_HTML, KI_SKILLPLAN_HTML, QUICK_WINS_HTML
```

**NICHT in truncation_targets** (SP-Wert irrelevant für diese):
```
EXECUTIVE_SUMMARY_HTML, ROADMAP_90D_HTML, TOOLS_EMPFEHLUNGEN_HTML,
TECHNOLOGIE_PROZESSE_HTML, BRANCH_DEEP_DIVE_HTML, TEMPLATES_START_HTML,
SOFORT_START_HTML, WETTBEWERB_BENCHMARK_HTML, KI_AKTIVITAETEN_ZIELE_HTML
```

### 2.1 Angeforderte Vergleichstabelle (10 Sections × 3 Segmente)

| Section | SP solo | Healer solo IST | Healer solo SOLL | SP team | Healer team IST | Healer team SOLL | SP kmu | Healer kmu IST | In Targets? | Konflikt? |
|---------|---------|-----------------|------------------|---------|-----------------|------------------|--------|----------------|-------------|-----------|
| EXECUTIVE_SUMMARY_HTML | 4000 (L68) | 2000 (L2743) | 3500 | 7000 (L158) | 3000 (L2833) | 4500 | 14000 (L243) | 6000 (L2927) | **NEIN** | Kein SP-Konflikt (nicht in Targets). Healer IST zu niedrig. |
| STRATEGIE_GOVERNANCE_HTML | 3000 (L81) | 5000 (L2756) | 5500 | 9000 (L171) | 5000 (L2846) | 7500 | 18000 (L256) | 10000 (L2940) | **JA** | **Solo: SP=3000 < Healer=5000 → SP killt 2000 chars** |
| TECHNOLOGIE_PROZESSE_HTML | 3000 (L86) | 2000 (L2761) | 4500 | 8000 (L176) | 3000 (L2851) | 6000 | 12000 (L261) | 8000 (L2945) | **NEIN** | Kein SP-Konflikt. Healer IST zu niedrig. |
| UNTERNEHMENSPROFIL_MARKT_HTML | 3000 (L82) | 5000 (L2757) | 7500 | 8000 (L172) | 5000 (L2847) | 10500 | 16000 (L257) | 14000 (L2941) | **JA** | **Solo: SP=3000 < Healer=5000 → SP killt 2000 chars** |
| PILOT_PLAN_HTML | 3000 (L79) | 1200 (L2754) | 3000 | 6000 (L169) | 1800 (L2844) | 4000 | 8000 (L254) | 5000 (L2938) | **JA** | Kein SP-Konflikt (SP ≥ Healer IST überall). Healer IST zu niedrig. |
| DATA_READINESS_HTML | 3000 (L80) | 1200 (L2755) | 3500 | 8000 (L170) | 1800 (L2845) | 4500 | 10000 (L255) | 6000 (L2939) | **JA** | Kein SP-Konflikt aktuell. **NACH SOLL: Solo SP=3000 < SOLL=3500!** |
| TOOLS_EMPFEHLUNGEN_HTML | 3000 (L85) | 5000 (L2760) | 5000 | 9000 (L175) | 5000 (L2850) | 6000 | 18000 (L260) | 8000 (L2944) | **NEIN** | Kein SP-Konflikt (nicht in Targets). |
| TEMPLATES_START_HTML | _def=1000 (L99) | 2500 (L2782) | 4500 | _def=2500 (L189) | 3500 (L2872) | 6000 | _def=3000 (L263) | 8000 (L2970) | **NEIN** | Kein SP-Konflikt (nicht in Targets). Healer IST zu niedrig. |
| SOFORT_START_HTML | _def=1000 (L99) | 1500 (L2794) | 4500 | _def=2500 (L189) | 2000 (L2884) | 6000 | _def=3000 (L263) | 8000 (L2982) | **NEIN** | **BUDGET_EXEMPT** (L3077) — Healer wendet kein Budget an! |
| BRANCH_DEEP_DIVE_HTML | 3000 (L92) | 12000 (L2774) | 12000 | 8000 (L182) | 6000 (L2864) | 10000 | _def=3000 (L263) | 14000 (L2962) | **NEIN** | Kein SP-Konflikt (nicht in Targets). |

### 2.2 Detaillierte SP-Konflikte: Alle Sections in truncation_targets

Für die 14 Sections die GLOBAL-TRUNCATION durchlaufen, zeige ich wo SP < Healer:

**Solo — aktuelle SP-Konflikte:**

| Section (in Targets) | SP solo | Healer solo IST | SP < Healer? | Healer EXEMPT? | Effektives Limit |
|----------------------|---------|-----------------|--------------|----------------|------------------|
| STRATEGIE_GOVERNANCE_HTML | 3000 (L81) | 5000 (L2756) | **JA: -2000** | Nein | SP=3000 |
| UNTERNEHMENSPROFIL_MARKT_HTML | 3000 (L82) | 5000 (L2757) | **JA: -2000** | Nein | SP=3000 |
| FOERDERPOTENZIAL_HTML | 3000 (L76) | 5000 (L2751) | **JA: -2000** | Nein | SP=3000 |
| ORG_CHANGE_HTML | 3000 (L77) | 4000 (L2752) | **JA: -1000** | Nein | SP=3000 |
| RECOMMENDATIONS_HTML | 3000 (L73) | 6000 (L2748) | **JA: -3000** | **JA** (L3077) | SP=3000 (einziges Limit!) |
| GAMECHANGER_HTML | 1500 (L75) | 1500 (L2750) | Gleich | **JA** (L3077) | SP=1500 (einziges Limit!) |
| RISKS_HTML | 7000 (L74) | 35000 (L2749) | **JA: -28000** | **JA** (L3077) | SP=7000 (einziges Limit!) |
| PILOT_PLAN_HTML | 3000 (L79) | 1200 (L2754) | Nein | Nein | Healer=1200 |
| DATA_READINESS_HTML | 3000 (L80) | 1200 (L2755) | Nein | Nein | Healer=1200 |
| MONETARISIERUNG_HTML | 3000 (L83) | 1200 (L2758) | Nein | Nein | Healer=1200 |
| KI_SKILLPLAN_HTML | 3000 (L84) | 1200 (L2759) | Nein | Nein | Healer=1200 |
| ROADMAP_12M_HTML | 8000 (L72) | 8000 (L2747) | Gleich | Nein | 8000 |
| QUICK_WINS_HTML | 8000 (L69) | 8000 (L2744) | Gleich | Nein | 8000 |
| BUSINESS_CASE_HTML | 5000 (L78) | 10000 (L2753) | **JA: -5000** | Nein | SP=5000 (FIX-BC1 Override auf min 5000) |

**Solo hat 5 echte SP-Konflikte** (wo SP den Content unter Healer-Budget schneidet):
STRATEGIE_GOVERNANCE, UNTERNEHMENSPROFIL_MARKT, FOERDERPOTENZIAL, ORG_CHANGE, BUSINESS_CASE.
Plus 3 BUDGET_EXEMPT-Sections wo SP das einzige Limit ist: RECOMMENDATIONS, GAMECHANGER, RISKS.

**Team — aktuelle SP-Konflikte:**

| Section (in Targets) | SP team | Healer team IST | SP < Healer? | Healer EXEMPT? | Effektives Limit |
|----------------------|---------|-----------------|--------------|----------------|------------------|
| FOERDERPOTENZIAL_HTML | 9000 (L166) | 12000 (L2841) | **JA: -3000** | Nein | SP=9000 |
| ORG_CHANGE_HTML | 8000 (L167) | 9000 (L2842) | **JA: -1000** | Nein | SP=8000 |
| QUICK_WINS_HTML | 7000 (L159) | 10000 (L2834) | **JA: -3000** | Nein | SP=7000 |
| ROADMAP_12M_HTML | 8500 (L162) | 12000 (L2837) | **JA: -3500** | Nein | SP=8500 |
| GAMECHANGER_HTML | 8000 (L165) | 10000 (L2840) | **JA: -2000** | **JA** (L3077) | SP=8000 (einziges Limit!) |
| RECOMMENDATIONS_HTML | 10000 (L163) | 12000 (L2838) | **JA: -2000** | **JA** (L3077) | SP=10000 (einziges Limit!) |
| BUSINESS_CASE_HTML | 8000 (L168) | 8000 (L2843) | Gleich | Nein | 8000 |
| STRATEGIE_GOVERNANCE_HTML | 9000 (L171) | 5000 (L2846) | Nein | Nein | Healer=5000 |
| UNTERNEHMENSPROFIL_MARKT_HTML | 8000 (L172) | 5000 (L2847) | Nein | Nein | Healer=5000 |
| PILOT_PLAN_HTML | 6000 (L169) | 1800 (L2844) | Nein | Nein | Healer=1800 |
| DATA_READINESS_HTML | 8000 (L170) | 1800 (L2845) | Nein | Nein | Healer=1800 |
| MONETARISIERUNG_HTML | 6000 (L173) | 1800 (L2848) | Nein | Nein | Healer=1800 |
| KI_SKILLPLAN_HTML | 6000 (L174) | 1800 (L2849) | Nein | Nein | Healer=1800 |
| RISKS_HTML | 9000 (L164) | 35000 (L2839) | **JA: -26000** | **JA** (L3077) | SP=9000 (einziges Limit!) |

**Team hat 4 echte SP-Konflikte** plus 3 BUDGET_EXEMPT wo SP einziges Limit ist.

**KMU — SP-Konflikte:**

Für alle 14 Sections in truncation_targets gilt bei KMU: **SP ≥ Healer** (KMU SP-Budgets sind großzügig).
**KMU hat 0 SP-Konflikte.**

---

## 3. NEUER FUND: Healer SIZE_PROFILES-Fallback ist ein No-Op-Bug

### Bug-Beschreibung (report_healer.py L3090-3093)

```python
if budget is None:
    # Fallback: SIZE_PROFILES als Single Source of Truth
    sp = SIZE_PROFILES.get(segment, {})    # ← Gibt volles Profil-Dict zurück
    budget = sp.get(section_name, ...)     # ← Sucht "EXECUTIVE_SUMMARY_HTML" als Top-Level-Key
                                           #   → findet NICHTS → fällt auf _default
```

**Problem:** `SIZE_PROFILES["solo"]` hat als Top-Level-Keys:
```
display_name, employee_range, segment, tonality, forbidden_enterprise_terms,
forbidden_persona_terms, section_budgets, min_words, max_pages, ...
```

Die Section-Budgets liegen UNTER `sp["section_budgets"]["EXECUTIVE_SUMMARY_HTML"]`,
aber der Code sucht `sp["EXECUTIVE_SUMMARY_HTML"]` — das existiert nicht.

### Verifikation (Python-Test)

```
Healer fallback for EXECUTIVE_SUMMARY_HTML: FELL_TO_DEFAULT
Correct lookup for EXECUTIVE_SUMMARY_HTML: 4000
```

### Impact

- **Geringe Auswirkung aktuell:** Der Fallback greift NUR wenn eine Section weder per exact match noch per uppercase_HTML-Mapping in SEGMENT_BUDGETS gefunden wird. Alle 10 Audit-Sections SIND in SEGMENT_BUDGETS → Bug betrifft sie nicht.
- **Relevanz für neue Sections:** Wenn eine neue Section NUR in SIZE_PROFILES definiert wird (nicht in SEGMENT_BUDGETS), fällt sie immer auf `_default` statt den SP-Wert zu nutzen.
- **Der Kommentar "SIZE_PROFILES als Single Source of Truth" ist irreführend** — der Code tut das NICHT.

### Fix (B37l)

```python
# Zeile 3091-3093 ersetzen durch:
sp_budgets = SIZE_PROFILES.get(segment, {}).get("section_budgets", {})
budget = sp_budgets.get(section_name, sp_budgets.get(section_name.upper() + "_HTML", default_budget))
```

---

## 4. gpt_analyze.py Budget-Quellen

### 4.1 GLOBAL-TRUNCATION (L13415-13559)

```
Quelle:  config/size_profiles.py → get_section_budget(segment, key)
Import:  L13427: from config.size_profiles import get_section_budget, get_min_words
Aufruf:  L13461: _budget = get_section_budget(_trunc_segment, key)
```

**Antwort auf Kernfrage:** JA — gpt_analyze.py nutzt `SIZE_PROFILES.section_budgets` direkt als Budget-Quelle für GLOBAL-TRUNCATION. Diese Funktion (size_profiles.py L356-369) liest korrekt aus `profile["section_budgets"]` — anders als der Healer-Fallback (Bug oben).

**Konsequenz:** Für Sections IN truncation_targets gilt: Wenn SP-Wert < Healer-Budget, wird Content VOR dem Healer beschnitten. Die B36-Erhöhungen im Healer sind dann **wirkungslos** für diese Sections.

Für Sections **NICHT** in truncation_targets: SP-Wert ist irrelevant. Nur der Healer bestimmt das Budget.

### 4.2 Truncation Targets (L13418-13422) — 14 Sections

```
RISKS_HTML, GAMECHANGER_HTML, FOERDERPOTENZIAL_HTML, RECOMMENDATIONS_HTML,
ORG_CHANGE_HTML, BUSINESS_CASE_HTML, PILOT_PLAN_HTML, ROADMAP_12M_HTML,
DATA_READINESS_HTML, STRATEGIE_GOVERNANCE_HTML, UNTERNEHMENSPROFIL_MARKT_HTML,
MONETARISIERUNG_HTML, KI_SKILLPLAN_HTML, QUICK_WINS_HTML
```

**NICHT in Targets** (kein GLOBAL-TRUNCATION → SP irrelevant):
```
EXECUTIVE_SUMMARY_HTML, ROADMAP_90D_HTML, TOOLS_EMPFEHLUNGEN_HTML,
TECHNOLOGIE_PROZESSE_HTML, BRANCH_DEEP_DIVE_HTML, TEMPLATES_START_HTML,
SOFORT_START_HTML, WETTBEWERB_BENCHMARK_HTML, KI_AKTIVITAETEN_ZIELE_HTML
```

### 4.3 Budget-Override: FIX-BC1 (L13462-13466)

```python
if key in ("BUSINESS_CASE_HTML", "business_case") and _budget < 5000:
    _budget = 5000  # Override für zu enge Budgets
```

Einziger hardcodierter Budget-Override in GLOBAL-TRUNCATION.

### 4.4 POST-TRIM-HEAL (L13561-13664 + L15987-16053)

Zwei separate Healing-Loops, beide für die gleichen 4 Sections:

```python
# Loop 1 (L13565): Nach GLOBAL-TRUNCATION
_heal_critical_sections = ["gamechanger", "roadmap_12m", "executive_summary", "tools_empfehlungen"]
# Max 2 Iterationen, heilt Sections unter min_words

# Loop 2 (L16001, FIX-629): POST-TRIM-HEAL Guard
_HEAL_CRITICAL_SECTIONS = ["executive_summary", "tools_empfehlungen", "gamechanger", "roadmap_12m"]
# Gap-Limit: nur innerhalb 30 Wörter unter Minimum (L16028)
```

**Risiko:** 10 der 14 truncation_target-Sections werden nach Truncation **NICHT** geheilt:
STRATEGIE_GOVERNANCE, UNTERNEHMENSPROFIL_MARKT, FOERDERPOTENZIAL, ORG_CHANGE,
PILOT_PLAN, DATA_READINESS, MONETARISIERUNG, KI_SKILLPLAN, BUSINESS_CASE, QUICK_WINS.

### 4.5 RESCUE LOOP (L16246)

Dritter Healing-Mechanismus — breiter:
- Hat KEIN Gap-Limit (heilt jede Section unter min_words)
- Greift erst beim Quality Gate (spät in der Pipeline)
- Expandiert jede Section die unter min_words steht

### 4.6 Vollständige Budget-Kette

```
LLM generiert Content
  ↓ (max_tokens: NICHT segment-abhängig, L1289)
  ↓
GLOBAL-TRUNCATION (gpt_analyze.py L13415)
  Budget-Quelle: SIZE_PROFILES.section_budgets ← HIER GREIFEN SP-WERTE
  NUR für 14 Sections in truncation_targets
  ↓
POST-TRIM-HEAL Loop 1 (gpt_analyze.py L13561)
  min_words-Quelle: SIZE_PROFILES.min_words
  NUR für 4 Sections: gamechanger, roadmap_12m, executive_summary, tools_empfehlungen
  ↓
Content Quality Enforcer (content_quality_enforcer.py)
  Segment-abhängig: Solo-Term-Replacement, Solo-RISKS-Padding
  ↓
POST-TRIM-HEAL Loop 2 (gpt_analyze.py L15987)
  min_words-Quelle: SIZE_PROFILES.min_words
  NUR für 4 Sections, nur innerhalb 30-Wort-Gap
  ↓
RESCUE LOOP (gpt_analyze.py L16246)
  Jede Section unter min_words, kein Gap-Limit
  ↓
Healer apply_segment_budget() (report_healer.py L3045)
  Budget-Quelle: SEGMENT_BUDGETS ← HIER GREIFEN HEALER-WERTE
  Hierarchie: exact > uppercase_HTML > SIZE_PROFILES fallback (BROKEN!) > _default
  ↓
BUDGET_EXEMPT bypass (L3077)
  RISKS, GAMECHANGER, RECOMMENDATIONS, VENDOR_AUDIT, SOFORT_START,
  AUTOMATION_ROADMAP, BENCHMARK_ENGINE, BUSINESS_CASE_SIM,
  RISK_ENGINE, RISK_ENGINE_V3, RECOMMENDATIONS_ENGINE, CHALLENGE_30_TAGE
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

## 5. solo_compact_engine.py Schwellenwerte

### 5.1 Compact-Auslösung (L650-664)

| Parameter | Solo | Team | KMU | Datei:Zeile |
|-----------|------|------|-----|-------------|
| MAX_PAGES | 16 | 70 | 45 | solo_compact_engine.py:651-653 |
| HTML_COMPACT_THRESHOLD_KB | 300 | 500 | 550 | solo_compact_engine.py:662-664 |

**Trigger-Logik** (L726-736):
```python
needs_compact = False
if size_kb > threshold:  needs_compact = True   # HTML > KB-Schwelle
if pages > max_pages:    needs_compact = True   # Seiten > Max
```

Beide Bedingungen sind **ODER-verknüpft** — ein Trigger reicht.

### 5.2 Solo-Kompaktierung: Was passiert beim Trigger?

**a) SOLO_COMPACT_WORD_LIMITS (L165-172)** — harte Wort-Limits:

| Section | Word-Limit | ~Char-Äquivalent (×7) | Healer IST | Problem? |
|---------|-----------|----------------------|------------|----------|
| EXECUTIVE_SUMMARY_HTML | 400 | ~2800 | 2000 | Nein (Healer enger) |
| QUICK_WINS_HTML | 600 | ~4200 | 8000 | **JA** — Compact killt 47% |
| ROADMAP_90D_HTML | 500 | ~3500 | 5000 | **JA** — Compact killt 30% |
| ROADMAP_12M_HTML | 600 | ~4200 | 8000 | **JA** — Compact killt 47% |
| PILOT_PLAN_HTML | 400 | ~2800 | 1200 | Nein (Healer enger) |
| DATA_READINESS_HTML | 300 | ~2100 | 1200 | Nein (Healer enger) |

**b) SOLO_COMPACT_EXCLUDED (L145-161)** — diese Sections werden komplett GEDROPPT:
```
BRANCH_DEEP_DIVE_HTML, RISK_ENGINE_HTML, RISK_ENGINE_V3_HTML,
BUSINESS_CASE_SIM_HTML, BENCHMARKS_HTML, AUTOMATION_ROADMAP_HTML,
FUNDING_BRANCH_ALIGNMENT_HTML, TOOLS_FUNDING_ALIGNMENT_HTML,
TOOLS_BRANCH_ALIGNMENT_HTML, ROI_TRACKING_HTML, KICKOFF_HTML,
PROMPT_FRAMEWORK_HTML, ROADMAP_12M_HTML, BUSINESS_CASE_HTML,
FOERDERPOTENZIAL_HTML
```

### 5.3 Risikoanalyse: B36-Budgets → Compact-Trigger

**Aktuelles Solo-HTML-Budget (Summe aller Healer SEGMENT_BUDGETS solo):**
```
Alle Solo-Sections addiert:     ~205.000 chars ≈ 200KB
+ HTML/CSS/Template-Overhead:   ~60-100KB
Geschätzte Gesamtgröße:         ~260-300KB
Schwelle:                       300KB
Headroom:                       0-40KB → KNAPP
```

**Nach FINAL-Version (SOLL-Budgets für Solo):**
```
Alle Solo-Sections addiert:     ~280.000 chars ≈ 273KB (geschätzt)
+ HTML/CSS/Template-Overhead:   ~60-100KB
Geschätzte Gesamtgröße:         ~333-373KB
Schwelle:                       300KB
Headroom:                       NEGATIV → TRIGGER!
```

**Antwort auf Kernfrage:** JA — nach FINAL B36-Deployment wird Solo **sehr wahrscheinlich** die 300KB-Schwelle überschreiten. Das löst Solo-Kompaktierung aus, die dann:
1. QUICK_WINS und ROADMAP_12M auf 600 Wörter kürzt
2. BRANCH_DEEP_DIVE, BUSINESS_CASE, FOERDERPOTENZIAL komplett droppt

**Die Budget-Erhöhungen werden dadurch teilweise zunichte gemacht.**

**Empfehlung:** Solo HTML_COMPACT_THRESHOLD auf 400-450KB erhöhen, BEVOR Solo-Budgets erhöht werden.

### 5.4 Team/KMU WP4 Compact Guard

Wenn Team/KMU die Schwelle überschreitet, werden Low-Priority-Sections gedroppt (L670-683):
```
Tier 1: FUNDING_BRANCH_ALIGNMENT, TOOLS_FUNDING_ALIGNMENT, TOOLS_BRANCH_ALIGNMENT,
        AUTOMATION_ROADMAP, ROI_TRACKING, BUSINESS_CASE_SIM, KICKOFF
Tier 2: MARKET_INSIGHTS, NEWS_BOX
```

---

## 6. Empfehlung: Was muss als nächstes gefixt werden?

### Priorität 1: SOFORT (vor nächstem Deploy)

| # | Was | Wo | Warum |
|---|-----|-----|-------|
| **B37a** | Solo SEGMENT_BUDGETS auf 55% von KMU erhöhen | report_healer.py L2742-2830 | Solo-Content 50-78% zu kurz |
| **B37b** | Team SEGMENT_BUDGETS auf 75% von KMU erhöhen | report_healer.py L2832-2920 | Team-Content 50-78% zu kurz |
| **B37c** | Solo/Team Plaintext-Budgets hinzufügen | report_healer.py (nach L2829/L2919) | "roadmap" etc. fallen auf _default=1000/1500 |
| **B37d** | Solo/Team `_default` erhöhen | report_healer.py L2830, L2920 | solo: 1000→1500, team: 1500→2000 |

### Priorität 2: VOR Solo-Budget-Deploy

| # | Was | Wo | Warum |
|---|-----|-----|-------|
| **B37e** | Solo HTML_COMPACT_THRESHOLD auf 400-450KB | solo_compact_engine.py L662 | Sonst triggert Compact nach Budget-Erhöhung |

### Priorität 3: NACH Testrun

| # | Was | Wo | Warum |
|---|-----|-----|-------|
| **B37f** | Solo SP: STRATEGIE_GOVERNANCE, UNTERNEHMENSPROFIL_MARKT, FOERDERPOTENZIAL, ORG_CHANGE erhöhen | size_profiles.py L76-82 | 4 echte SP-Konflikte wo GLOBAL-TRUNCATION Content killt |
| **B37g** | Team SP: FOERDERPOTENZIAL, ORG_CHANGE, QUICK_WINS, ROADMAP_12M erhöhen | size_profiles.py L159-166 | 4 echte SP-Konflikte |
| **B37h** | Alle SP: TEMPLATES_START, SOFORT_START explizit hinzufügen | size_profiles.py (alle 3 Segmente) | Fehlen, fallen auf _default |
| **B37i** | Sanity-Check erweitern: SP ≥ Healer für truncation_targets prüfen | size_profiles.py L388 | Automatische Konflikterkennung |

### Priorität 4: Bug-Fix (niedrige Dringlichkeit)

| # | Was | Wo | Warum |
|---|-----|-----|-------|
| **B37l** | Healer SIZE_PROFILES-Fallback Dict-Nesting fixen | report_healer.py L3090-3093 | Fallback ist No-Op (falsches Dict-Level). Fix: `sp.get("section_budgets", {})` |

### Priorität 5: Monitoring

| # | Was | Wo | Warum |
|---|-----|-----|-------|
| **B37j** | HTML-Gesamtgröße nach B37a/b loggen | gpt_analyze.py / report_renderer.py | Compact-Trigger-Risiko überwachen |
| **B37k** | POST-TRIM-HEAL auf alle 14 target-Sections erweitern | gpt_analyze.py L13565, L16001 | Nur 4 von 14 werden geheilt |

---

## 7. Korrekturen gegenüber vorherigem Audit (v1)

| # | Was war falsch | Korrektur |
|---|----------------|-----------|
| 1 | "BRANCH_DEEP_DIVE_HTML steht in der target-Liste (L13421)" | **FALSCH** — BRANCH_DEEP_DIVE ist NICHT in truncation_targets. L13421 enthält DATA_READINESS, STRATEGIE_GOVERNANCE, UNTERNEHMENSPROFIL_MARKT |
| 2 | Solo-Tabelle zeigte SP-Konflikte für TEMPLATES_START, SOFORT_START, BRANCH_DEEP_DIVE | **IRRELEVANT** — diese Sections sind nicht in truncation_targets, SP wird nie angewendet |
| 3 | KMU "3 SP-Konflikte" für TEMPLATES_START, SOFORT_START, BRANCH_DEEP_DIVE | **IRRELEVANT** — gleicher Grund: nicht in truncation_targets |
| 4 | SOFORT_START_HTML als "SP killt Content" markiert | **FALSCH** — SOFORT_START ist BUDGET_EXEMPT (L3077), weder SP noch Healer greifen |
| 5 | NEU: Healer SIZE_PROFILES-Fallback (L3090-3093) ist No-Op-Bug | Wurde im v1-Audit nicht erkannt. Dict-Nesting-Fehler: `sp.get(section_name)` sucht im Profile-Dict statt in `sp["section_budgets"]` |

---

## 8. Zusammenfassung

```
┌─────────────────────────────────────────────────────────────────┐
│  VERSION V1 DEPLOYED (nur KMU-Budgets erhöht)                   │
│                                                                 │
│  SIZE_PROFILES (config/size_profiles.py)                        │
│  → GLOBAL-TRUNCATION Budget-Quelle (NUR für 14 target-Sections)│
│  → Solo: 5 echte Konflikte (SP < Healer)                       │
│  → Team: 4 echte Konflikte (SP < Healer)                       │
│  → KMU: 0 Konflikte                                            │
│                                                                 │
│  SEGMENT_BUDGETS (report_healer.py L2741)                       │
│  → Solo/Team: Noch auf pre-B36 Werten (20-36% von KMU)         │
│  → SIZE_PROFILES-Fallback (L3090): No-Op-Bug (Dict-Nesting)    │
│                                                                 │
│  WP4 Compact Guard (solo_compact_engine.py L699)                │
│  → Solo 300KB Schwelle: Nach B37 WIRD Compact triggern          │
│  → B37e (Schwelle erhöhen) MUSS vor B37a (Budgets erhöhen)      │
│                                                                 │
│  REIHENFOLGE DER FIXES:                                         │
│  1. B37e: Solo Compact-Schwelle auf 400-450KB                   │
│  2. B37a+b+c+d: Healer Solo/Team Budgets erhöhen                │
│  3. B37f+g: SP Solo/Team für target-Sections erhöhen            │
│  4. B37l: Healer SP-Fallback Bug fixen                          │
└─────────────────────────────────────────────────────────────────┘
```
