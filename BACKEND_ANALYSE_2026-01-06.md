# BACKEND-ANALYSE: api-ki-backend-neu
**Datum:** 2026-01-06
**Branch:** `claude/analyze-backend-structure-dZAUE`
**Letzter Commit:** `325c57d` - "Add files via upload"

---

## 1. FILE-LOCATIONS

### gpt_analyze.py (Hauptdatei)
- **Path:** `/home/user/api-ki-backend-neu/gpt_analyze.py`
- **Size:** 543,589 Bytes
- **Lines:** 11,775 Zeilen
- **Key Functions:**
  | Function | Zeile | Beschreibung |
  |----------|-------|--------------|
  | `ui()` | 608 | UI-Translations |
  | `_fix_typos()` | 1937-1944 | Typo-Korrektur |
  | `_call_openai()` | 1754 | LLM-Aufruf |
  | `_call_llm_for_section()` | 1866 | Section-Generation |
  | `_build_quick_wins_html()` | 2209 | Quick Wins HTML |
  | `_fallback_quick_wins_html()` | 2329 | Quick Wins Fallback |
  | `_get_fallback_content()` | 6037 | Fallback Content |
  | `_generate_content_section()` | 8073 | Content Section Generation |
  | `_generate_content_sections()` | 8839 | Alle Sections generieren |
  | `analyze_briefing()` | 9711 | Hauptanalyse-Funktion |
  | `run_briefing_pipeline()` | 11429 | Pipeline-Orchestrierung |

### services/business_case_engine_v2.py
- **Path:** `/home/user/api-ki-backend-neu/services/business_case_engine_v2.py`
- **Size:** ~50 KB
- **Lines:** 1,552 Zeilen
- **Key Functions:**
  | Function | Zeile | Beschreibung |
  |----------|-------|--------------|
  | `normalize_company_size()` | 143 | Größen-Normalisierung |
  | `get_funding_cap()` | 151 | Funding-Cap nach Größe |
  | `get_hourly_rate()` | 157 | Stundensatz nach Größe |
  | `get_max_time_savings()` | 170 | Max. Zeitersparnis |
  | `cap_time_savings()` | 176 | Zeitersparnis begrenzen |
  | `calculate_roi()` | 482-499 | ROI-Berechnung |
  | `calculate_payback()` | 502-519 | Payback-Berechnung |
  | `calculate_monthly_savings()` | 527 | Monatl. Ersparnis |
  | `validate_scenario_consistency()` | 546 | Szenario-Validierung |
  | `heal_scenario_consistency()` | 603 | Szenario-Heilung |
  | `normalize_scenario_order()` | 738 | ROI-Normalisierung |
  | `generate_business_case_report()` | 1139 | BC-Report generieren |
  | `business_case_report_to_html()` | 1356 | BC zu HTML |

### templates/pdf_template.html
- **Path:** `/home/user/api-ki-backend-neu/templates/pdf_template.html`
- **Lines:** 6,909 Zeilen
- **Key Sections:**
  | Section | Zeile | Beschreibung |
  |---------|-------|--------------|
  | Quick Wins CSS | 865-1127 | Quick Win Card Styling |
  | Roadmap CSS | 1132-1177 | Roadmap Grid Styles |
  | Page-Break Rules | 174-254, 1523-1589 | Seitenumbruch-Regeln |
  | 90-Tage Timeline CSS | 2101 | Timeline Styles |
  | Quick Wins Section | 5989-6002 | Quick Wins Template |
  | Roadmap Section | 6255-6326 | Roadmap Template |
  | Handlungsempfehlungen | 6237 | G32 Recommendations |

---

## 2. FUNCTION-LOCATIONS (für Fixes)

### PHASE 1 - Critical Fixes:

#### Typo Dictionary (TYPO_FIXES)
```python
# File: gpt_analyze.py
# Zeile: 1918-1934
TYPO_FIXES = {
    "Enwicklung": "Entwicklung",
    "Entwickung": "Entwicklung",
    "Enwicklungs": "Entwicklungs",
    "Optimerung": "Optimierung",
    "Automatsierung": "Automatisierung",
    "Automatiserung": "Automatisierung",
    "Digitalsierung": "Digitalisierung",
    "Digitaliseirung": "Digitalisierung",
    "Kommunikaion": "Kommunikation",
    "Dokumentaion": "Dokumentation",
    "Intergration": "Integration",
    "Implmentierung": "Implementierung",
    "Kundenaquise": "Kundenakquise",
    "Akquise": "Akquise",
    "Prozessoptimeirung": "Prozessoptimierung",
}
```
**FEHLT:** `"Froschung"`, `"beratung"` (Lowercase), `"Einzelunternehmer"` → **ERGÄNZEN!**

#### Nuclear Fix Section (Typo Application)
```python
# File: gpt_analyze.py
# Zeile: 9738-9779
# NUCLEAR FIX: Apply _fix_typos to ALL string fields
# Fix both: answers dict AND briefing object br
```

#### Zeitersparnis-Werte (Quick Wins)
```python
# File: gpt_analyze.py
# Zeile 7659: time_savings="8-12h/M"  (Fallback QW1)
# Zeile 7683: time_savings="8-12h/M"  (Fallback QW2)
# Zeile 7707: time_savings="6-10h/M"  (Fallback QW3)
# Zeile 7731: time_savings="6-10h/M"  (Fallback QW4)
# Zeile 7789: time_savings="5-8h/M"   (Fallback QW5)
# Zeile 7808: time_savings="4-6h/M"   (Fallback QW6)
# Zeile 7831: time_savings="3-5h/M"   (Fallback QW7)
# Zeile 7852: time_savings="5-8h/M pro Person"
# Zeile 7871: time_savings="10-15h/M gesamt"
```

#### Zeitersparnis-Caps (Business Case Engine)
```python
# File: services/business_case_engine_v2.py
# Zeile: 117-122
MAX_TIME_SAVINGS_BY_SIZE = {
    "solo": 25,                    # Solo: max 25h/Monat realistisch
    "team": 60,                    # Kleines Team: max 60h/Monat
    "kmu": 150,                    # KMU: max 150h/Monat
    "enterprise": 400,             # Größere Unternehmen: max 400h/Monat
}
```

#### ROI-Berechnung
```python
# File: services/business_case_engine_v2.py
# Zeile: 83-84 - ROI Constraints
MIN_ROI = -100.0  # -100% = total loss
MAX_ROI = 1000.0  # 1000% = 10x return  ← PRÜFEN: 200% Cap?

# Zeile: 482-499 - calculate_roi()
def calculate_roi(annual_savings: float, investment_total: float) -> float:
    if investment_total <= 0:
        return 0.0
    roi = ((annual_savings - investment_total) / investment_total) * 100
    return max(MIN_ROI, min(MAX_ROI, roi))  # ← AKTUELL: Cap bei 1000%
```

#### ROI-Explanation (Problem #3 Fix)
```python
# File: services/business_case_engine_v2.py
# Zeile: 190-264 - ROIExplanation class
# Enthält transparente Herleitung mit HTML-Output
```

---

## 3. DEPENDENCIES (requirements.txt)

| Package | Status | Version |
|---------|--------|---------|
| `openai` | ✅ VORHANDEN | `>=1.51,<2.0` |
| `anthropic` | ✅ VORHANDEN | `>=0.25,<1.0` |
| `tavily-python` | ✅ VORHANDEN | `>=0.3,<0.4` |
| `httpx` | ✅ VORHANDEN | `>=0.27,<0.28` |
| `weasyprint` | ⚠️ KOMMENTIERT | `# weasyprint>=61.0` |
| `beautifulsoup4` | ✅ VORHANDEN | `>=4.11,<5.0` |
| `feedparser` | ✅ VORHANDEN | `>=6.0,<7.0` |

**Fazit:** Alle kritischen Dependencies für Phase 4 (Live-Daten) sind bereits vorhanden!

---

## 4. ENV-KEYS (.env.example)

### LLM & Research
| Key | Status | Zeile |
|-----|--------|-------|
| `OPENAI_API_KEY` | ✅ SET | 35 |
| `ANTHROPIC_API_KEY` | ✅ SET | 43 |
| `TAVILY_API_KEY` | ⚠️ LEER | 59 |
| `PERPLEXITY_API_KEY` | ⚠️ LEER | 62 |

### Feature Flags (Phase 4 relevant)
| Key | Status | Default |
|-----|--------|---------|
| `ENABLE_PREMIUM_FUNDING` | ✅ VORHANDEN | `0` |
| `TOOLS_ENGINE_ENABLED` | ✅ VORHANDEN | `1` |
| `FUNDING_PREDICTIVE_ENABLED` | ✅ VORHANDEN | `1` |
| `RESEARCH_PROVIDER` | ✅ VORHANDEN | `hybrid` |

### FEHLT für Phase 4:
```bash
❌ ENABLE_LIVE_FOERDERPROGRAMME=  # FEHLT
❌ ENABLE_LIVE_TOOL_PRICING=      # FEHLT
```

---

## 5. CURRENT STATE ANALYSIS

### Typos Suche
```bash
# Suche nach "Froschung":
❌ NICHT GEFUNDEN in gpt_analyze.py (gut - kein Bug, aber Korrektur fehlt im Dict)

# Suche nach "beratung" (lowercase):
→ Alle Treffer sind korrekt im Kontext (z.B. "Rechtsberatung", "BAFA-Beratung")
→ Kein falsches lowercase "beratung" gefunden

# Suche nach "Einzelunternehmer":
❌ NICHT GEFUNDEN - Kein Treffer
```

**Status:** Die genannten Typos scheinen bereits behoben oder waren nie im Code. Das TYPO_FIXES Dict sollte trotzdem um weitere häufige Typos erweitert werden.

### Zeitersparnis-Werte Analysis
| Location | Aktuelle Werte | Problem |
|----------|---------------|---------|
| Fallback Quick Wins | 3-15h/M Range | Evtl. zu hoch für Solo |
| MAX_TIME_SAVINGS (Solo) | 25h | ✅ Realistisch |
| MAX_TIME_SAVINGS (Team) | 60h | ✅ Realistisch |
| KPI Display (Zeile 9034) | Dynamisch: `capped_h * 0.7 - 1.2` | ✅ Begrenzt |

### ROI-Logik Analysis
```python
# AKTUELLE IMPLEMENTIERUNG:
MAX_ROI = 1000.0  # 10x Return erlaubt

# ROI-Berechnung (Zeile 498):
roi = ((annual_savings - investment_total) / investment_total) * 100
return max(MIN_ROI, min(MAX_ROI, roi))

# ROI Assessment (Zeile 1321-1328):
- ROI >= 200%: "sehr attraktives ROI"
- ROI >= 100%: "solide mit ROI"
- ROI >= 50%:  "moderat positiv"
- ROI < 50%:   "sorgfältige Abwägung erforderlich"
```

**Problem:** MAX_ROI bei 1000% ist sehr hoch. Evtl. auf 200-300% begrenzen für Glaubwürdigkeit.

### ROI-Herleitung (Problem #3 Fix)
```python
# File: services/business_case_engine_v2.py
# Zeile: 190-264 - ROIExplanation Klasse

# Bereits implementiert:
- Transparente Schritt-für-Schritt Herleitung
- HTML-Output mit Formel
- Wird in generate_business_case_report() verwendet (Zeile 1222-1224)
```

**Status:** ✅ ROI-Herleitung ist implementiert und wird im Business Case angezeigt.

---

## 6. GIT-INFO

**Branch:** `claude/analyze-backend-structure-dZAUE`
**Status:** Clean (keine uncommitted changes)

**Letzte Commits:**
```
325c57d Add files via upload
84b32e2 Add files via upload
a200275 Fix typos in answers dict and briefing object
4671d83 Update gpt_analyze.py
cf95f2b Fix typos in zeitersparnis_prioritaet value
1a011e5 trigger: force railway redeploy
99ecfc0 fix: add transparent ROI calculation breakdown to funding section
f6df6e3 fix: replace generic risk phrases with concrete fact-based scenarios
d6fed47 fix: use default funding programs when regex extracts generic Land entries
39c1934 fix: gamechanger regex captures complete text with nested tags
```

---

## 7. ZUSAMMENFASSUNG FÜR FIX-BRIEFINGS

### Phase 1 - Typo-Fix (Schnell)
- **File:** `gpt_analyze.py`
- **Zeile:** 1918-1934 (TYPO_FIXES dict)
- **Action:** Dict erweitern um weitere häufige Typos
- **Nuclear Fix:** Bereits implementiert (Zeile 9738-9779)

### Phase 2 - Zeitersparnis-Anpassung (Mittel)
- **File 1:** `gpt_analyze.py` Zeile 7659-7871 (Fallback Quick Wins)
- **File 2:** `services/business_case_engine_v2.py` Zeile 117-122 (MAX_TIME_SAVINGS)
- **Action:** Werte für Solo/Team nach unten anpassen

### Phase 3 - ROI-Cap (Mittel)
- **File:** `services/business_case_engine_v2.py`
- **Zeile:** 84 (`MAX_ROI = 1000.0`)
- **Action:** Auf 200-300% begrenzen für Glaubwürdigkeit
- **ROI-Explanation:** ✅ Bereits implementiert

### Phase 4 - Live-Daten (Komplex)
- **Dependencies:** ✅ Alle vorhanden (tavily, httpx)
- **ENV-Keys:** ⚠️ TAVILY_API_KEY leer, ENABLE_LIVE_* fehlen
- **Services:** Neuer Service `services/live_data_integration.py` erstellen

---

## 8. QUICK-REFERENCE: Wichtige Zeilen

| Was | File | Zeile |
|-----|------|-------|
| TYPO_FIXES Dict | gpt_analyze.py | 1918-1934 |
| _fix_typos() | gpt_analyze.py | 1937-1944 |
| Nuclear Fix | gpt_analyze.py | 9738-9779 |
| Quick Wins Fallback | gpt_analyze.py | 7659-7871 |
| calculate_roi() | business_case_engine_v2.py | 482-499 |
| MAX_ROI Constant | business_case_engine_v2.py | 84 |
| MAX_TIME_SAVINGS | business_case_engine_v2.py | 117-122 |
| ROIExplanation | business_case_engine_v2.py | 190-264 |
| analyze_briefing() | gpt_analyze.py | 9711 |
| Page-Break CSS | pdf_template.html | 174-254 |
| Quick Wins Template | pdf_template.html | 5989-6002 |
| Roadmap Template | pdf_template.html | 6255-6326 |

---

**Analyse abgeschlossen: 2026-01-06**
**Bereit für Fix-Briefings!**
