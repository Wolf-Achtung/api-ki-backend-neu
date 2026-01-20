# FIX-503A Forensic Audit Report

**Scope:** QuickWins Rendering | Payback Canonical | Risk Matrix Table Wrap | Metrics Unification
**Repo:** `api-ki-backend-neu`
**Date:** 2026-01-20
**Status:** Forensik abgeschlossen - Root Causes identifiziert

---

## Executive Summary

Dieses Audit dokumentiert die **Root Causes** für vier Baustellen aus Report 498:
1. **QuickWins Rendering** - Seite 37 leer, Seite 16 nur Bullets
2. **Payback Canonical** - "9 Monate" statt 3.5 Monate
3. **Risk Matrix Table Wrap** - Wörter abgeschnitten
4. **Metrics Unification** - Pipeline grade=A obwohl 70+ Warnings

---

## 1. QuickWins Rendering

### Root Cause

**Validator misst falschen Key:** Der `ReportValidator` prüft `quick_wins` (Text-Liste), aber das Template rendert `QUICK_WINS_HTML` (HTML).

**Beweisstellen:**
- `services/report_validator.py:714` - Key-Mapping:
  ```python
  SECTION_KEY_MAP: Dict[str, str] = {
      ...
      "quick_wins": "quick_wins",  # ← Prüft TEXT, nicht HTML!
      ...
  }
  ```
- `templates/pdf_template.html:6661-6675` - Template nutzt `QUICK_WINS_HTML`:
  ```jinja
  {% if QUICK_WINS_HTML and QUICK_WINS_HTML|trim and '<' in QUICK_WINS_HTML %}
  <section class="section chapter">
      ...
      {{ QUICK_WINS_HTML|safe }}
  </section>
  {% endif %}
  ```

### Codepfade

| Datei | Zeile | Funktion |
|-------|-------|----------|
| `services/report_validator.py` | 714 | `SECTION_KEY_MAP["quick_wins"]` |
| `services/report_validator.py` | 618 | `MIN_SECTION_LENGTH_WORDS["quick_wins"]` |
| `services/report_validator.py` | 1138 | `_check_quick_wins_prompt_leaks()` |
| `templates/pdf_template.html` | 6661 | Quick Wins Section Rendering |

### Warum SECTION_TOO_SHORT getriggert wird

Der Validator misst die Wortanzahl von `sections["quick_wins"]` (Text-Liste mit ~15 Wörtern), nicht von `sections["QUICK_WINS_HTML"]` (HTML mit 458 Zeichen + 3 Items).

**Log-Beweis:**
```
Simple JSON converted to HTML (3 items...)
has_marker=True, has_class=True, len=458
...
SECTION_TOO_SHORT quick_wins: 15 Wörter
```

### Seite 37 leer - Hypothese

Es gibt möglicherweise einen zweiten Quick Wins Block im Starter-Kit oder Branch Deep Dive, der nicht befüllt wird. Die Hauptsektion (Seite 16) verwendet `QUICK_WINS_HTML`, aber Seite 37 verwendet eine andere Variable.

### Minimaler Fix-Vorschlag

1. **Option A:** Validator-Key-Mapping korrigieren:
   ```python
   SECTION_KEY_MAP["quick_wins"] = "QUICK_WINS_HTML"
   ```

2. **Option B:** Validator dual prüfen:
   ```python
   # In _check_empty_or_short_sections():
   if key == "quick_wins":
       html_key = "QUICK_WINS_HTML"
       if html_key in self.sections and self.sections[html_key]:
           continue  # HTML vorhanden, skip warning
   ```

3. **Option C:** Quick Wins nur einmal rendern (Template deduplizieren)

---

## 2. Payback Canonical: "9 Monate"

### Root Cause

**LLM-generierter Text nicht synchronisiert mit Canonical KPIs.**

Die kanonischen Werte werden korrekt gesetzt:
- `PAYBACK_MONTHS = 3.5` (Canonical)
- `PAYBACK_MONTHS_FMT_DE = "3,5"` (Formatiert)

Aber im Branch Deep Dive oder Business Case Narrative wird ein LLM-generierter Text verwendet, der "9 Monate" enthält - dieser stammt nicht aus den kanonischen Werten.

### Beweisstellen

- `gpt_analyze.py:13858` - Canonical Binding:
  ```python
  log.info(f"[{run_id}] ✅ [P0.1] Template bindings: PAYBACK={sections['PAYBACK_MONTHS_FMT_DE']}, ...")
  ```

- `services/business_case_simulation.py:257-259` - Simulation P50:
  ```python
  payback_p50: float = 0.0  # Monte Carlo P50
  ```

- Log zeigt Inkonsistenz:
  ```
  Centralized KPIs: PAYBACK_MONTHS=3.5
  ...
  Business Case pre-calculated: PAYBACK_P50=6.1 months
  ...
  [KPI_002] Payback-Zeiträume weichen stark voneinander ab
  ```

### Mögliche Quellen für "9 Monate"

1. **LLM-Textabschnitt:** Branch Deep Dive oder Tools-Empfehlungen mit hartcodierten/halluzinierten Werten
2. **Simulation P90:** `payback_p90` könnte höher sein als P50
3. **AI Act Compliance Delta:** `AI_ACT_BC_PAYBACK_DELTA` addiert Monate für Dokumentation
4. **Legacy-Sektion:** Alte Business Case Card ohne Canonical-Binding

### Codepfade

| Datei | Zeile | Variable |
|-------|-------|----------|
| `gpt_analyze.py` | 13858 | `PAYBACK_MONTHS_FMT_DE` |
| `services/business_case_engine_v2.py` | 273 | `PAYBACK_MONTHS` |
| `services/business_case_simulation.py` | 257 | `payback_p50` |
| `templates/pdf_template.html` | 6230 | `{{ PAYBACK_MONTHS_FMT_DE or PAYBACK_MONTHS }}` |
| `templates/pdf_template.html` | 7383 | `AI_ACT_BC_PAYBACK_DELTA` |

### Minimaler Fix-Vorschlag

1. **LLM-Postprocessing:** Payback-Werte in LLM-generierten Texten durch Canonical ersetzen:
   ```python
   # In llm_postprocessor.py oder content_quality_enforcer.py
   def enforce_canonical_payback(text: str, canonical_payback: float) -> str:
       """Replace any payback mentions with canonical value."""
       pattern = r"(?:Payback|Amortisation)[:\s]+(\d+(?:[.,]\d+)?)\s*(?:Monate|months)"
       return re.sub(pattern, f"Amortisation: {canonical_payback} Monate", text)
   ```

2. **Truth Map:** Ein `quality_truth.json` mit allen kanonischen KPIs, das vor Render validiert wird

---

## 3. Risk Matrix Table Wrap

### Root Cause

**CSS `table-layout: fixed` mit festen Spaltenbreiten verhindert Textumbruch trotz `overflow-wrap: anywhere`.**

### Beweisstellen

`services/risk_engine_v2.py:1068-1089`:
```python
html_parts.append(f'''
<table class="table-modern" style="width:100%;border-collapse:collapse;font-size:10pt;table-layout:fixed;">
    <colgroup>
        <col style="width:50%;">
        <col style="width:15%;">
        <col style="width:15%;">
        <col style="width:20%;">
    </colgroup>
    ...
    <td style="padding:8px;border-bottom:1px solid #f1f5f9;overflow-wrap:anywhere;word-break:break-word;hyphens:auto;">
```

### Problem-Analyse

1. `table-layout: fixed` mit `colgroup` gibt Spalten feste Breiten
2. WeasyPrint (PDF-Renderer) hat bekannte Probleme mit `overflow-wrap` in Tabellenzellen
3. Lange Wörter wie "Datennutzungsrichtlinien" werden abgeschnitten statt umgebrochen
4. CSS `hyphens: auto` funktioniert nur mit korrektem `lang`-Attribut

### Abgeschnittene Beispiele (PDF Seite 31)

- "Zeitblöc..." (Zeitblöcke)
- "Datennutzungsrichtlin..." (Datennutzungsrichtlinien)
- "sorgfältige Auswahl u..." (und...)
- "Strenge Faktenprüfun..." (Faktenprüfung)

### Minimaler Fix-Vorschlag

1. **CSS-Fix in risk_engine_v2.py:**
   ```python
   # Zeile 1089 - Erweiterte CSS für td
   <td style="padding:8px;border-bottom:1px solid #f1f5f9;
              overflow-wrap:anywhere;
              word-break:break-word;
              hyphens:auto;
              white-space:normal;  /* HINZUFÜGEN */
              overflow:visible;">   /* HINZUFÜGEN - kein hidden! */
   ```

2. **Alternative: table-layout entfernen:**
   ```python
   # Zeile 1068 - Auto statt fixed
   style="width:100%;border-collapse:collapse;font-size:10pt;table-layout:auto;"
   ```

3. **WeasyPrint-spezifisch:**
   ```css
   @media print {
       .risk-matrix-section td {
           white-space: pre-wrap !important;
       }
   }
   ```

---

## 4. Metrics Unification

### Root Cause

**Zwei separate Warning-Systeme, die nicht aggregiert werden:**

1. `ReportErrorGate.warnings` - Pipeline-Fehler während Generierung (Fallbacks, Heals)
2. `ReportValidator.errors` - Validierungs-Warnings nach Generierung (Content Quality)

### Beweisstellen

`gpt_analyze.py:13867-13884`:
```python
# FIX-497: Store gate metrics in sections
sections["PIPELINE_WARNINGS_COUNT"] = len(error_gate.warnings)  # ← nur Pipeline-Warnings!
sections["PIPELINE_FALLBACK_COUNT"] = error_gate.fallback_count
sections["PIPELINE_HEALS_COUNT"] = error_gate.heals_count
sections["PIPELINE_GRADE"] = "A" if (
    len(error_gate.warnings) == 0 and
    error_gate.fallback_count == 0 and
    error_gate.heals_count == 0
) else ...
```

`services/report_validator.py:1106-1110`:
```python
self.errors.append(
    ValidationError(
        severity=severity,
        category="SECTION_TOO_SHORT",
        ...
    )
)
```

### Warum "grade=A" trotz 70 Warnings

| Metric Source | Count | In Pipeline Grade? |
|---------------|-------|-------------------|
| `error_gate.warnings` | 0 | Yes |
| `error_gate.fallback_count` | 0 | Yes |
| `ReportValidator.errors (WARNING)` | 70 | **No!** |
| `G22 Consistency FAIL` | 1 | **No!** |

Die Pipeline metrics zeigen nur die `ReportErrorGate`-Warnings, nicht die `ReportValidator`-Warnings oder G22 Consistency-Ergebnisse.

### Codepfade

| Datei | Zeile | System |
|-------|-------|--------|
| `gpt_analyze.py` | 638 | `class ReportErrorGate` |
| `gpt_analyze.py` | 13883 | Pipeline metrics Logging |
| `services/report_validator.py` | 615 | `MIN_SECTION_LENGTH_WORDS` |
| `services/report_validator.py` | 1106 | Validator warnings |
| `services/consistency_engine.py` | 137 | `ConsistencyReport.issues` |

### Minimaler Fix-Vorschlag

1. **Unified QualityMetrics Objekt:**
   ```python
   @dataclass
   class QualityMetrics:
       pipeline_warnings: int = 0
       pipeline_fallbacks: int = 0
       validator_warnings: int = 0
       consistency_score: float = 100.0
       consistency_grade: str = "A"

       @property
       def total_warnings(self) -> int:
           return self.pipeline_warnings + self.validator_warnings

       @property
       def overall_grade(self) -> str:
           if self.total_warnings == 0 and self.consistency_grade in ("A", "B"):
               return "A"
           elif self.total_warnings <= 10 and self.consistency_grade in ("A", "B", "C"):
               return "B"
           else:
               return "C"
   ```

2. **Validator-Ergebnisse in Gate integrieren:**
   ```python
   # Nach ReportValidator.validate():
   validator = ReportValidator(sections, company_size)
   validator.validate()

   # Warnings zu error_gate hinzufügen
   for err in validator.errors:
       if err.severity == "WARNING":
           error_gate.warnings.append(f"[Validator] {err.category}: {err.message}")
   ```

3. **G22 Consistency in Pipeline Grade:**
   ```python
   # Consistency check vor Pipeline Grade Berechnung
   if consistency_report.grade in ("D", "F"):
       sections["PIPELINE_GRADE"] = "C"  # Downgrade
   ```

---

## Artifact-Verzeichnis

```
docs/fix503a/
├── run_498_log_snippets.txt           # Relevante Log-Stellen
├── report_498_notes.md                # PDF-Seitenreferenzen
└── render_debug_extracts/             # HTML/Code-Snippets
    ├── quick_wins_section.html        # Template-Extrakt Quick Wins
    ├── risk_matrix_table.html         # CSS-Problem Risk Matrix
    └── metrics_unification_issue.py   # Code-Dokumentation Metrics
```

---

## FIX-503B Plan (Nächste Phase)

Nach Bestätigung dieser Forensik-Ergebnisse:

| Commit | Scope | Änderungen |
|--------|-------|------------|
| 1 | QuickWins + Validator | Key-Mapping korrigieren, Template deduplizieren |
| 2 | Risk Matrix + Metrics | CSS-Fix, Unified QualityMetrics |

Geschätzte Dateien: 4-5 (report_validator.py, risk_engine_v2.py, gpt_analyze.py, pdf_template.html)

---

## Appendix: Grep-Befehle für weitere Analyse

```bash
# QuickWins Key-Mapping
grep -n "quick_wins" services/report_validator.py

# Payback-Quellen im Template
grep -n "PAYBACK" templates/pdf_template.html

# Risk Matrix CSS
grep -n "table-layout\|overflow-wrap" services/risk_engine_v2.py

# Pipeline metrics vs Validator
grep -n "PIPELINE_GRADE\|ValidationError" gpt_analyze.py services/report_validator.py
```
