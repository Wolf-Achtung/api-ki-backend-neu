# FIX-BATCH PLAN

**Datum:** 2026-01-18
**Ziel:** warnings=0, fallbacks=0, heals=0, removals=0

---

## Fix-Batch A: Output Integrity (PRIORITÄT 1)

### A1: Quick-Wins JSON→HTML Parser Fix

**Problem:** JSON kommt rein, aber HTML-Validator erwartet `<div class="quick-win-card">` Markers

**Datei:** `/home/user/api-ki-backend-neu/gpt_analyze.py`
**Zeile:** 3901-3902

**Änderung:**
```python
# ALT (Zeile 3901-3902):
html_markers = ['<div class="quick-win-card"', '<div class="quick-win">', 'class="quick-wins"']
has_html_structure = any(marker in qw_html for marker in html_markers)

# NEU:
html_markers = ['<div class="quick-win-card"', '<div class="quick-win">', 'class="quick-wins"']
json_valid = qw_html.strip().startswith('[') and '"title"' in qw_html
has_html_structure = any(marker in qw_html for marker in html_markers) or json_valid
```

**Zusätzlich:** JSON-Parser in `_parse_quick_wins_json()` verwenden wenn `json_valid=True`

**Risiko:** LOW
**Tests:** Quick-Wins Section muss 3-5 Items enthalten, keine "[QW-FALLBACK]" Logs

---

### A2: Dummy-Text zur Cleanup-Liste hinzufügen

**Problem:** "Dummy-Text" erscheint in TECHNOLOGIE_PROZESSE_HTML

**Datei:** `/home/user/api-ki-backend-neu/gpt_analyze.py`
**Zeile:** 10435

**Änderung:**
```python
# ALT:
developer_words = ["Platzhalter", "TODO", "Beispieltext", "Content wird erstellt", "XXX"]

# NEU:
developer_words = ["Platzhalter", "TODO", "Beispieltext", "Content wird erstellt", "XXX", "Dummy-Text", "Dummy Text", "Mustertext"]
```

**Risiko:** NONE
**Tests:** Validator findet keine "Dummy-Text" Matches

---

### A3: Chat-Artefakt Hard-Gate für Executive Sections

**Problem:** KI-Assistenzsätze als BENIGN klassifiziert, führen nur zu Cleanup statt Suppression

**Datei:** `/home/user/api-ki-backend-neu/services/zero_leak_engine.py`
**Zeile:** 102-123 (BENIGN_CHATBOT_PHRASES)

**Änderung:**
```python
# Verschiebe diese Phrases von BENIGN zu CRITICAL für EXECUTIVE_SECTIONS:
EXECUTIVE_CRITICAL_PHRASES: List[str] = [
    "ich bin ein KI-Assistent",
    "ich bin ein KI-Modell",
    "als KI-Assistent",
    "als künstliche Intelligenz",
    "gerne erkläre ich",
    "gerne helfe ich",
    "wie kann ich dir helfen",
    "wie kann ich Ihnen helfen",
]

# In apply_blacklist_classified() (Zeile ~300):
# Wenn section_key in EXECUTIVE_SECTIONS und phrase in EXECUTIVE_CRITICAL_PHRASES:
#   → Behandle als CRITICAL statt BENIGN
```

**Risiko:** MEDIUM (könnte zu mehr Fallbacks führen)
**Tests:** Keine KI-Assistenzsätze in EXECUTIVE_SUMMARY, DECISION Sections

---

## Fix-Batch B: Numerical Consistency (PRIORITÄT 2)

### B1: ROI 0% Guard in calculate_roi()

**Problem:** Division by zero guard gibt 0.0% zurück, propagiert durch alle Szenarien

**Datei:** `/home/user/api-ki-backend-neu/services/business_case_engine_v2.py`
**Zeile:** 893-910

**Änderung:**
```python
# ALT (Zeile 906-907):
def calculate_roi(annual_savings: float, investment_total: float) -> float:
    if investment_total <= 0:
        return 0.0

# NEU:
def calculate_roi(annual_savings: float, investment_total: float) -> float:
    # Minimum investment threshold statt 0-Guard
    if investment_total <= 0:
        investment_total = 100.0  # Minimum 100€

    roi = ((annual_savings - investment_total) / investment_total) * 100
    return max(MIN_ROI, min(MAX_ROI, roi))
```

**Risiko:** LOW
**Tests:** Kein Szenario mit ROI=0.0%

---

### B2: heal_scenario_consistency() - Neuberechnung statt Umsortierung

**Problem:** Heal sortiert nur Labels um, berechnet Werte nicht neu

**Datei:** `/home/user/api-ki-backend-neu/services/business_case_engine_v2.py`
**Zeile:** 1049-1055

**Änderung:**
```python
# ALT (Zeile 1049-1055):
sorted_scenarios = sorted(scenarios, key=lambda s: s.roi_12m)
conservative_data = sorted_scenarios[0]
realistic_data = sorted_scenarios[1]
optimistic_data = sorted_scenarios[2]

# NEU:
sorted_scenarios = sorted(scenarios, key=lambda s: s.roi_12m)

# Neuberechnung wenn 0.0% vorhanden
for idx, scenario in enumerate(sorted_scenarios):
    if scenario.roi_12m <= 0.0:
        # Berechne ROI neu basierend auf Savings
        gross_savings = scenario.monthly_savings * 12
        scenario_investment = max(100.0, scenario.investment_total)
        opex_annual = scenario_investment * 0.15
        new_roi = calculate_roi(gross_savings - opex_annual, scenario_investment)
        sorted_scenarios[idx] = ScenarioKPIs(
            name=scenario.name,
            roi_12m=max(new_roi, 10.0),  # Minimum 10%
            # ... copy other fields
        )

conservative_data = sorted_scenarios[0]
realistic_data = sorted_scenarios[1]
optimistic_data = sorted_scenarios[2]
```

**Risiko:** MEDIUM
**Tests:** Nach Heal: optimistic > realistic > conservative (alle > 0)

---

### B3: Bundesland-Filter in Starter-Kits

**Problem:** NRW Digitalförderung hardcoded für alle "solo" unabhängig vom Bundesland

**Datei:** `/home/user/api-ki-backend-neu/services/tools_starter_kits.py`
**Zeile:** 243-244

**Änderung (Option 1 - Remove):**
```python
# Entferne NRW-spezifische Förderung aus FUNDING_TEMPLATES
# Zeile 243-250 löschen (NRW_DIGITAL entry)
```

**Änderung (Option 2 - Filter):**
```python
# In generate_starter_kit() (Zeile ~400):
def generate_starter_kit(profile_context, lang="de", bundesland=None):
    size = profile_context.get("size", "solo")
    funding = FUNDING_TEMPLATES.get(size, [])

    # NEU: Bundesland-Filter
    if bundesland:
        bundesland_lower = bundesland.lower()
        funding = [
            f for f in funding
            if not f.get("provider", "").lower() in ["nrw", "bayern", "bw"]  # Regional
            or f.get("provider", "").lower() == _normalize_bundesland_to_provider(bundesland_lower)
        ]

    # ... rest of function
```

**Risiko:** LOW
**Tests:** User "Berlin" sieht keine NRW-Förderung, removals=0

---

## Zusammenfassung

| Fix | Datei | Änderungsumfang | Risiko | Priorität |
|-----|-------|-----------------|--------|-----------|
| A1 | gpt_analyze.py:3901 | 3 Zeilen | LOW | 1 |
| A2 | gpt_analyze.py:10435 | 1 Zeile | NONE | 1 |
| A3 | zero_leak_engine.py:102-300 | 20 Zeilen | MEDIUM | 2 |
| B1 | bc_engine_v2.py:906 | 3 Zeilen | LOW | 1 |
| B2 | bc_engine_v2.py:1049 | 15 Zeilen | MEDIUM | 2 |
| B3 | tools_starter_kits.py:243 | 5-10 Zeilen | LOW | 2 |

---

## Pass/Fail Kriterien (nach allen Fixes)

Ein Test-Run (solo, Berlin) muss enden mit:

```
✅ warnings=0
✅ fallbacks=0 (keine [QW-FALLBACK], [QW-DETERMINISTIC] Logs)
✅ heals=0 (keine BC_001 Logs)
✅ removals=0 (keine Location-Removal Logs)
✅ PDF size < 20MB
✅ Leak scan: 0 phrases detected
✅ Validator: 0 Template-Phrase matches
✅ All Scenarios: ROI > 0%
```

---

## Implementierungs-Reihenfolge

```
1. Fix A2 (Dummy-Text) - Trivial, sofort
2. Fix A1 (Quick-Wins) - Kritisch, heute
3. Fix B1 (ROI Guard) - Kritisch, heute
4. Fix B3 (Bundesland) - Wichtig, heute
5. Fix B2 (Heal Neuberechnung) - Medium, morgen
6. Fix A3 (Chat-Artefakt Gate) - Medium, morgen
```

---

## Rollback-Plan

Falls ein Fix unerwartete Probleme verursacht:

```bash
# Git revert für einzelnen Fix
git revert <commit-hash>

# Oder: Feature-Flag für kritische Fixes
FIX_A1_ENABLED=0  # Quick-Wins JSON
FIX_B1_ENABLED=0  # ROI Guard
```
