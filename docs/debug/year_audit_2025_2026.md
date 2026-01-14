# Year Audit: 2025 → 2026

**Version:** v14.35.21
**Date:** 2026-01-14
**Status:** ✅ CLASSIFIED

---

## Executive Summary

Das Repo enthält ~150 Fundstellen mit "2025". Diese wurden klassifiziert in:
- **MUSS dynamisch sein:** Templates/Headers mit Report-Jahr
- **KANN bleiben:** Funding-Programme, AI Act Fristen, historische Quellen

---

## 1. Classification

### 1.1 MUSS dynamisch sein (8 Stellen)

Diese Stellen sollten `{{report_year}}` oder `{{report_year}}/{{next_year}}` verwenden:

| Datei | Zeile | Aktuell | Vorschlag |
|-------|-------|---------|-----------|
| `templates/pdf_template.html` | 6522 | `2025/26` | `{{report_year}}/{{next_year_short}}` |
| `templates/pdf_template.html` | 6999 | `2025` | `{{report_year}}` |
| `templates/pdf_template.html` | 7244 | `2025` | `{{report_year}}` |
| `templates/pdf_template_en.html` | 6347 | `2025/26` | `{{report_year}}/{{next_year_short}}` |
| `templates/pdf_template_en.html` | 6808 | `2025` | `{{report_year}}` |
| `templates/pdf_template_en.html` | 7047 | `2025` | `{{report_year}}` |
| `templates/partials/guide_kreativtools_2025.html` | 1 | `2025` | Dateiname dynamisch oder `{{report_year}}` |
| `prompts/de/branch_deep_dive.md` | 70, 199, 296 | `2025–2026` | Dynamisch via Variable |

### 1.2 KANN bleiben (historisch/faktisch korrekt)

Diese Stellen referenzieren echte Daten:

| Kategorie | Beispiele | Begründung |
|-----------|-----------|------------|
| **AI Act Fristen** | `02.08.2025`, `02.08.2026` | Gesetzliche Deadlines |
| **Funding Deadlines** | `Q2 2025`, `Rolling 2025` | Echte Programmfristen |
| **Quellen/Studien** | `IW Köln 2025`, `PwC 2025` | Historische Referenzen |
| **Benchmark Data** | `year: 2025` | Daten aus 2025 |
| **CSS Classes** | `.year-2025` | Styling für Timeline |

### 1.3 Existierende dynamische Variablen

In `gpt_analyze.py` (Zeile 7127-7181):

```python
now = datetime.now()
report_year = now.strftime("%Y")  # "2026"
report_date = today  # "14.01.2026"

base_vars.update({
    "report_date": today,
    "report_year": report_year,  # ← Wird bereits gesetzt!
})
```

**Empfehlung:** `next_year` und `next_year_short` als zusätzliche Variablen hinzufügen.

---

## 2. Detailed Findings

### 2.1 Templates (HIGH PRIORITY)

```
templates/pdf_template.html:6522:   <h2>Branchenanalyse & Trends 2025/26</h2>
templates/pdf_template.html:6999:   <h2>KI-Skill-Fahrplan 2025</h2>
templates/pdf_template.html:7244:   <h2>Kreativ-Tools 2025 – modulare Alternativen</h2>
templates/pdf_template.html:7409:   © {{report_year}} KI-Sicherheit.jetzt  ← BEREITS DYNAMISCH ✓
```

### 2.2 Prompts (MEDIUM PRIORITY)

```
prompts/de/branch_deep_dive.md:70:  1) Branch Trends 2025–2026
prompts/de/branch_deep_dive.md:199: <h3>Branch Trends 2025–2026</h3>
prompts/en/branch_deep_dive.md:48:  1) Branch Trends 2025–2026
```

### 2.3 Services (OK - No change needed)

```
services/funding_engine_v2.py:      "year": 2025,  ← Funding-Datenbank, korrekt
services/ai_act_table.py:           ("2025-02-02", ...)  ← AI Act Fristen, korrekt
services/benchmarks.py:             "year": 2025,  ← Benchmark-Daten, korrekt
```

---

## 3. Recommended Fixes

### 3.1 Add Dynamic Year Variables (gpt_analyze.py)

```python
# Add after line 7130:
next_year = str(int(report_year) + 1)
next_year_short = next_year[-2:]  # "27" for 2027

base_vars.update({
    "report_year": report_year,
    "next_year": next_year,
    "next_year_short": next_year_short,
})
```

### 3.2 Update Template Headers

```html
<!-- BEFORE -->
<h2>Branchenanalyse & Trends 2025/26</h2>

<!-- AFTER -->
<h2>Branchenanalyse & Trends {{report_year}}/{{next_year_short}}</h2>
```

### 3.3 Prompts (Low Priority)

Die Prompts sollten {{REPORT_YEAR}} verwenden, aber da sie via GPT verarbeitet werden,
ist die Änderung optional. GPT kann das Jahr aus dem Kontext ableiten.

---

## 4. Acceptance Criteria

| Kriterium | Status |
|-----------|--------|
| Alle 2025-Fundstellen klassifiziert | ✅ |
| Dynamische Variablen existieren | ✅ (report_year) |
| Template-Footer bereits dynamisch | ✅ |
| Hardcoded Headers identifiziert | ✅ |
| Fix-Empfehlungen dokumentiert | ✅ |

---

## 5. Implementation Status

- [x] Audit durchgeführt
- [x] Klassifizierung dokumentiert
- [ ] `next_year` Variable hinzufügen (optional)
- [ ] Template Headers dynamisieren (optional)

**Note:** Die kritischsten Stellen (Footer) sind bereits dynamisch.
Die Header-Änderungen können in einem späteren Sprint erfolgen.
