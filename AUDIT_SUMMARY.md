# AUDIT SUMMARY - Backend & Pipeline Full Audit

**Datum:** 2026-01-18
**Scope:** Report Generation Pipeline, Business Case Engine, Quality Gates

---

## Executive Summary

Das Backend folgt einem **2-Prozess-Modell**:
- **Web (API):** FastAPI/uvicorn - empfängt Requests, validiert, speichert zu DB
- **Worker (Async):** Polling-basierter Worker - verarbeitet Queue über Briefing Pipeline

### Kritische Findings

| Kategorie | Status | Handlungsbedarf |
|-----------|--------|-----------------|
| **Quick Wins JSON-Verwurf** | 🔴 KRITISCH | Prompt fordert JSON, Validator erwartet HTML |
| **ROI Szenarien 0%** | 🔴 KRITISCH | Division-by-Zero Guard + Heal-Logik unvollständig |
| **Chat-Artefakte im PDF** | 🟡 MITTEL | BENIGN-Klassifikation zu permissiv |
| **Bundesland-Injection** | 🟡 MITTEL | NRW hardcoded in Starter-Kits |
| **Dummy-Text in Sections** | 🟡 MITTEL | Nicht in Cleanup-Liste |
| **Dead Code** | 🟠 INFO | ~30k Zeilen (21.6%) ungenutzt/kalt |

---

## Architektur-Überblick

```
CLIENT REQUEST
    ↓
WEB PROCESS (uvicorn main:app)
    ├→ POST /api/briefings/submit → DB Queue
    ↓
WORKER PROCESS (briefings_worker.py)
    ├→ Poll DB: status='accepted'
    ├→ Atomic claim (FOR UPDATE SKIP LOCKED)
    ├→ run_briefing_pipeline()
        ├→ analyze_briefing()
        │   ├→ Score Calculation
        │   ├→ Content Generation (31 Sections, parallel)
        │   ├→ Zero-Leak Guard
        │   ├→ Quality Enforcer (Siezen, Truncation)
        │   └→ Validation + Consistency
        ├→ render() → HTML via Jinja2
        ├→ PDF Generation (external service)
        └→ Email Delivery (Resend API)
```

---

## Kernprobleme & Root-Causes

### 1. Quick Wins Verwurf (JSON vs HTML)

**Problem:** Log zeigt `[QW-FALLBACK] No HTML structure` obwohl JSON korrekt generiert wird.

**Root-Cause:**
- Prompt (`prompts/de/quick_wins.md:50`) fordert JSON-Array
- Validator (`gpt_analyze.py:3902`) prüft auf HTML-Markers
- JSON wird als "keine HTML-Struktur" erkannt → deterministischer Fallback

**Fix:** Option B: JSON→HTML Renderer erweitern (siehe FIX_BATCH_PLAN.md)

### 2. ROI Szenarien 0%

**Problem:** `Realistic 0.0% < Conservative 200%` → Heal → Optimistic bleibt 0

**Root-Cause:**
- `calculate_roi()` returnt 0.0% bei `investment_total ≤ 0`
- `heal_scenario_consistency()` sortiert nur um, berechnet nicht neu
- Wenn ein Szenario 0.0% hat, bleibt es 0.0%

**Fix:** Guard gegen 0% + Neuberechnung statt nur Umsortierung

### 3. Chat-Artefakte im PDF

**Problem:** KI-Assistenzsätze erscheinen im finalen PDF

**Root-Cause:**
- Assistenzsätze sind als BENIGN klassifiziert (nicht CRITICAL)
- BENIGN führt zu `CLEAN-AND-KEEP`, nicht Section-Suppression
- Lücken in BENIGN-Liste (z.B. "Gerne erkläre ich" fehlt)

**Fix:** KI-Assistenz-Phrasen als CRITICAL für Executive-Sections

### 4. Wrong Bundesland (NRW)

**Problem:** NRW-Förderung erscheint bei Nicht-NRW-Usern

**Root-Cause:**
- `tools_starter_kits.py:243` hat NRW Digitalförderung hardcoded für alle "solo"
- Keine Bundesland-Filterung vor Injection

**Fix:** Bundesland-Filter vor Starter-Kit-Injection

### 5. Dummy-Text in Sections

**Problem:** "Dummy-Text" in TECHNOLOGIE_PROZESSE_HTML

**Root-Cause:**
- LLM generiert den Text (unvollständiger Prompt?)
- "Dummy-Text" ist nicht in der Cleanup-Liste (`gpt_analyze.py:10435`)

**Fix:** Zur developer_words Liste hinzufügen

---

## KPI Authority (Single Source of Truth)

| KPI | Primary Source | Risikostelle |
|-----|----------------|--------------|
| ROI_12M | `calculate_roi()` (bc_engine_v2:893) | Doppelte Berechnung in G34 Simulation |
| PAYBACK_MONTHS | `calculate_payback()` (bc_engine_v2:913) | Nullified wenn negativ |
| CAPEX | `BusinessCaseCanonical` (bc_engine_v2:599) | AI Act Factor nicht in ROI reflektiert |
| OPEX | `BusinessCaseCanonical` (bc_engine_v2:602) | Defaults werden nach ROI-Calc injiziert |
| Szenarien | `generate_scenarios()` | Multiple Healing-Passes nicht idempotent |

---

## Quality Gates Status

| Gate | Severity | Status | Empfehlung |
|------|----------|--------|------------|
| Leak Detection | CRITICAL | ✅ Hard-fail | Beibehalten |
| Placeholder Check | CRITICAL | ✅ Hard-fail | Beibehalten |
| Template Phrases | WARNING | ⚠️ Warn-only | → CRITICAL für exec |
| Generic LLM Leaks | WARNING | ⚠️ Warn-only | → CRITICAL für exec |
| Tools Consistency | WARNING | ⚠️ Warn-only | → CRITICAL bei Widerspruch |

---

## Dead Code Summary

| Kategorie | Zeilen | Risiko |
|-----------|--------|--------|
| **Vollständig ungenutzt** | 4,923 | 3.5% |
| **Kalt (1-3 Imports)** | 25,945 | 18% |
| **Gesamt** | 30,868 | **21.6%** |

Top 3 Kandidaten für Cleanup:
1. `expert_agents/` (5,049 Zeilen) - nur Tests
2. `research_agents/` (4,896 Zeilen) - nur Tests
3. `routes/####auth.py` (288 Zeilen) - deaktiviert

---

## Empfohlene Fix-Batches

### Fix-Batch A: Output Integrity (PRIORITÄT 1)
- Quick-Wins JSON→HTML Parser fixen
- Dummy-Text zur Cleanup-Liste
- Chat-Artefakt Hard-Gate für Executive

### Fix-Batch B: Numerical Consistency (PRIORITÄT 2)
- ROI 0% Guard in calculate_roi()
- Heal-Funktion: Neuberechnung statt Umsortierung
- Bundesland-Filter in Starter-Kits

---

## Pass/Fail Kriterien (nach Fix)

Ein Run (solo, Berlin) muss enden mit:
- ✅ warnings=0
- ✅ fallbacks=0 (P0.2)
- ✅ heals=0 (consistency)
- ✅ removals=0 (location)
- ✅ PDF size < 20MB
- ✅ Leak scan clean
