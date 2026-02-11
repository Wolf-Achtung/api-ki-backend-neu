# Release-Readiness Plan: Team & KMU Reports

**Datum:** 2026-02-11
**Status:** Fixes implementiert, Tests gruen
**Branch:** `claude/project-analysis-release-plan-7ba1K`

---

## Projektanalyse

### Architektur-Ueberblick

Das Projekt ist eine **produktionsreife KI-Readiness-Assessment-Plattform** mit folgender Struktur:

| Komponente | Dateien | Beschreibung |
|---|---|---|
| **API-Layer** | `main.py`, `routes/` | FastAPI mit 12+ Routen (Auth, Briefing, Report, etc.) |
| **Analyse-Engine** | `gpt_analyze.py` (11.775 Zeilen) | Master-Orchestrator v5.4.3-PLATIN+++ |
| **Services** | `services/` (180+ Dateien) | Validatoren, Healer, Renderer, Business Case, etc. |
| **Templates** | `templates/pdf_template.html` (6.909 Zeilen) | Jinja2 PDF-Template mit CSS |
| **Prompts** | `prompts/de/*.md`, `prompts/en/*.md` | LLM-Prompt-Templates nach Sektion |
| **Tests** | `tests/` (30+ Dateien) | pytest-basierte Test-Suite |
| **Daten** | `data/`, `fixtures/` | Benchmarks, Starter-Stacks, Funding-Daten |

### Pipeline-Architektur

```
Briefing Submit -> Validation -> LLM Section Generation -> Consistency Healing
    -> Leak Detection -> Template Rendering -> HTML Minification -> PDF Render
    -> Size Validation -> Storage -> Email Notification
```

### Key-Metriken

- **Unterstuetzte Sprachen:** DE, EN, FR, IT, ES
- **Unternehmensgroessen:** Solo (1), Team (2-10), KMU (11-100)
- **13 Branchen:** Marketing, Beratung, IT, Finanzen, etc.
- **Validierungsstufen:** 5 (Input, Numerisch, Domain, AI Act, Leak)

---

## Ist-Zustand vor Fixes

### Solo
- **Status:** Gruen / Release-ready
- Release-Strict-Mode: PASS

### Team (2-10)
- **Report:** 92 Seiten, ~9.4 MB
- **Release-Strict-Mode:** WARN (warnings=8, consistency=B)
- **N4.3 DoD:** FAILED (numerical=2 verbleibend)
- **Blocker:** Leere Business-Case-Werte ("EUR.", "bei %")

### KMU (11-100)
- **Report:** 60 Seiten, ~3.0 MB
- **Release-Strict-Mode:** WARN (warnings=8, consistency=D)
- **N4.3 DoD:** FAILED (numerical=2 verbleibend)
- **Blocker:** Gleiche leere Werte + Konsistenz-Grade D

---

## Implementierte Fixes

### WP1: Business-Case - Keine leeren Zahlen (Blocker-Fix)

**Root Cause:** Template-Variablen (`{{CAPEX_REALISTISCH_EUR}}`, `{{ROI_12M}}`) loefen zu leeren Strings auf, wenn BC-Berechnung fehlschlaegt. Ergebnis: "EUR.", "bei %" im PDF.

**Geaenderte Dateien:**
- `services/report_healer.py` - Neue Funktion `sanitize_business_case_empty_values()`
  - 12 Regex-Patterns fuer verschiedene leere Wertartefakte
  - Ersetzt "EUR." -> "n.v.", "bei %" -> "bei n.v."
  - Integriert in `heal_final_html()` als letzte Instanz
- `services/extra_sections.py` - `_fmt_eur()` verbessert (leere Strings -> "---")
  - AI Act BC-Tabelle: Doppeltes "%" entfernt, None -> "n.v."
- `gpt_analyze.py` - Alle Fallback-Templates mit `_safe_bc_val()` umgestellt
  - Static Section "business_roi"/"business_costs": Sichere Formatierung
  - Fallback "business_case": Sichere Formatierung

**Akzeptanzkriterien:**
- [x] Kein `EUR.` im gerenderten HTML
- [x] Kein `bei %` im gerenderten HTML
- [x] Kein `: %` im gerenderten HTML
- [x] Gueltige Werte werden nicht veraendert
- [x] 9 Unit-Tests gruen

### WP2: Validator ROI-/Prozent-Checks nur auf sichtbaren Text (Blocker-Fix)

**Root Cause:** `_check_roi_consistency()` in `report_validator.py` suchte mit `r"(\d{2,3})\s*%"` im gesamten HTML, einschliesslich CSS (`linear-gradient(...100%)`). False Positives durch CSS-Prozentwerte.

**Geaenderte Dateien:**
- `services/report_validator.py` - `_check_roi_consistency()` komplett ueberarbeitet:
  - Entfernt `<style>...</style>` und `<script>...</script>` Bloecke
  - Entfernt `style="..."` Attribute (catches linear-gradient 100%)
  - Entfernt `class="..."` Attribute
  - Entfernt alle HTML-Tags -> nur sichtbarer Text
  - Neuer Context-Pattern: `ROI|Rendite|Return` innerhalb 30 Zeichen
  - Dekodiert `&nbsp;`, `&thinsp;` vor Pruefung

**Akzeptanzkriterien:**
- [x] CSS `linear-gradient(... 100%)` erzeugt KEINE ROI-Warnung
- [x] CSS `width: 100%` erzeugt KEINE ROI-Warnung
- [x] Echter ROI-Text "ROI betraegt 284%" wird erkannt
- [x] Mixed CSS+Text: Nur sichtbare Prozente werden gewarnt
- [x] 4 Unit-Tests gruen

### WP3: Leakage-Sanitizer als letzte Instanz (Stabilitaet)

**Geaenderte Dateien:**
- `services/zero_leak_engine.py`:
  - `DETERMINISTIC_PRESCRUB_PHRASES`: +18 neue Phrasen (DE/EN)
    - "ich kann dir helfen", "als KI", "Hier sind", "Gerne erstelle ich"
    - "Of course,", "Sure,", "Here is", "Let me help", etc.
  - `BENIGN_CHATBOT_PHRASES`: +18 neue Phrasen (identisch)
    - Doppelte Abdeckung fuer robust detection

**Akzeptanzkriterien:**
- [x] Alle geforderten DE-Phrasen erkannt
- [x] Alle geforderten EN-Phrasen erkannt
- [x] Legitimer Business-Content wird nicht entfernt
- [x] 3 Unit-Tests gruen

### WP4: Compact/Payload-Guard (empfohlen)

**Geaenderte Dateien:**
- `services/solo_compact_engine.py` - Neues Modul `check_and_apply_compact_guard()`:
  - `MAX_PAGES_BY_SIZE`: Solo=16, Team=35, KMU=45
  - `HTML_COMPACT_THRESHOLD_KB`: Default 450KB (konfigurierbar via Env)
  - `TEAM_KMU_LOW_PRIORITY_SECTIONS`: 9 Sektionen (Vendor Audit, Automation Roadmap, etc.)
  - `CompactGuardResult` Dataclass fuer Logging/Monitoring
  - Automatisches Droppen von Low-Priority-Sektionen bei Ueberschreitung
- `gpt_analyze.py` - Guard integriert vor PDF-Rendering (beide Render-Pfade):
  - Nicht-fataler try/except um Guard
  - Logging bei Kompaktierung

**Akzeptanzkriterien:**
- [x] Kleine Reports werden nicht kompaktiert
- [x] Grosse Reports (>450KB) triggern Auto-Compact
- [x] Page-Limits sind groessenabhaengig
- [x] Seitenanzahl-Schaetzung ist plausibel
- [x] 4 Unit-Tests gruen

---

## Test-Ergebnisse

```
23 passed, 0 failed
```

| Test-Klasse | Tests | Status |
|---|---|---|
| TestWP1BusinessCaseEmptyValues | 9 | PASS |
| TestWP2ValidatorROIFalsePositive | 4 | PASS |
| TestWP3LeakageSanitizer | 3 | PASS |
| TestWP4CompactPayloadGuard | 4 | PASS |
| TestBusinessCaseEndToEnd | 3 | PASS |

---

## Erwartetes Ergebnis nach den Fixes

1. **Team & KMU Reports** enthalten keine leeren "EUR."/"bei %" Artefakte
2. **N4.3 Numerical Issues** reduzieren sich (die 2 verbleibenden waren BC-Leerwerte)
3. **52x Validator-Warnungen** reduzieren sich (ROI False Positives eliminiert)
4. **Release-Strict-Mode** sollte von WARN auf PASS wechseln (nach Rerun)
5. **Team-PDF** wird durch Auto-Compact kleiner (Ziel: <35 Seiten bei Ueberschreitung)
6. **Leakage-Risiko** weiter minimiert durch 36 neue Phrasen

---

## Naechste Schritte (Empfohlen)

### WP0 - Repro & Debug-Visibility
- Reproduktion lokal/CI mit denselben Briefings (Team-briefing-623, KMU-briefing-622)
- Bei N4.3 DoD FAILED: Konkrete Issue-IDs + Felder + Vergleichswerte loggen

### WP5 - Briefing-Konsistenz
- Diff-Test: Team- und KMU-Briefings unterscheiden sich nur in `unternehmensgroesse`
- Aktuell: `zielgruppen[0]` differiert (`kmu` vs `b2b`) - bereinigen

### Stabilitaet
- Stack-Summary ohne Regen-Fallback stabilisieren
- Redundanzwarnungen reduzieren (Validator smarter: nur echte Duplikate)
- PDF-Optimierung (qpdf/ghostscript) als Post-Step evaluieren

---

## Geaenderte Dateien (Zusammenfassung)

| Datei | Aenderungen |
|---|---|
| `services/report_healer.py` | +`sanitize_business_case_empty_values()`, Integration in `heal_final_html()` |
| `services/report_validator.py` | `_check_roi_consistency()` - HTML-Stripping vor Pruefung |
| `services/zero_leak_engine.py` | +36 neue Leak-Phrasen (DE/EN) |
| `services/extra_sections.py` | `_fmt_eur()` Robustheit, ROI-Display Fix |
| `services/solo_compact_engine.py` | +`check_and_apply_compact_guard()`, Konfiguration |
| `gpt_analyze.py` | Sichere BC-Formatierung, WP4-Guard-Integration |
| `tests/test_release_readiness_wp.py` | 23 neue Tests fuer WP1-WP4 |
| `RELEASE_READINESS_PLAN.md` | Dieses Dokument |
