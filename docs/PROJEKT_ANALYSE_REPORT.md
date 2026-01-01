# Projekt-Analyse: ki-sicherheit.jetzt

**Datum:** 2026-01-01
**Analyst:** Claude (Opus 4.5)
**Version:** v5.4.3-PLATIN+++

---

## 1. Projekt-Übersicht

| Kategorie | Technologie |
|-----------|-------------|
| **Framework** | FastAPI (Python) |
| **PDF-Library** | Externer PDF-Service via HTTP (Puppeteer-basiert) |
| **Template-Engine** | Jinja2 |
| **AI-Integration** | OpenAI GPT-4/o1 + Anthropic Claude (Dual-Model) |
| **Datenbank** | SQLAlchemy (PostgreSQL) |

### Wichtige Entry-Points

- **Haupt-App**: `main.py` (FastAPI App, Zeile 93)
- **Report-Generierung**: `gpt_analyze.py` (>8000 Zeilen, Kern-Logik)
- **Template-Rendering**: `services/report_renderer.py` (Zeile 277: `render()`)
- **PDF-Client**: `services/pdf_client.py` (externe PDF-Service Kommunikation)
- **Report-API**: `routes/report.py` (REST-Endpoints)

---

## 2. Verzeichnisstruktur

```
api-ki-backend-neu/
├── main.py                     # FastAPI App Entry-Point
├── gpt_analyze.py              # Kern: GPT-Analyse & Report-Generierung (~8000 Zeilen)
├── models.py                   # SQLAlchemy Models (Briefing, Analysis, Report)
├── settings.py                 # Konfiguration
│
├── routes/                     # API-Router
│   ├── analyze.py              # /api/analyze Endpoints
│   ├── briefings.py            # /api/briefings Endpoints
│   ├── report.py               # /api/report Endpoints (PDF/HTML)
│   ├── dashboard.py            # Dashboard-API
│   └── ...
│
├── services/                   # Business-Logik Services
│   ├── report_renderer.py      # Template → HTML Rendering
│   ├── pdf_client.py           # PDF-Service Client
│   ├── prompt_loader.py        # Prompt-Dateien laden
│   ├── prompt_enhancer.py      # Prompt-Anreicherung
│   ├── extra_sections.py       # Business Case, Benchmarks, etc.
│   ├── branch_profile_engine.py # Branchen-Profil-Generierung
│   ├── llm_client.py           # OpenAI/Anthropic Client
│   ├── anthropic_client.py     # Claude-spezifischer Client
│   └── ... (~80+ Service-Module)
│
├── templates/                  # Jinja2 Templates
│   ├── pdf_template.html       # Haupt-Template (DE) - ~4000 Zeilen
│   ├── pdf_template_en.html    # Haupt-Template (EN)
│   └── partials/               # Wiederverwendbare Template-Teile
│       ├── grundlagen_dsgvo_ai_act.html
│       ├── guide_kreativtools_2025.html
│       ├── tools_overview.html
│       └── use_cases_kmu_generic.html
│
├── prompts/                    # LLM-Prompt-Definitionen
│   ├── de/                     # Deutsche Prompts (~50 Dateien)
│   │   ├── executive_summary.md
│   │   ├── quick_wins.md
│   │   ├── recommendations.md
│   │   ├── risks.md
│   │   ├── roadmap_12m.md
│   │   └── ...
│   └── en/                     # Englische Prompts (~55 Dateien)
│
├── data/                       # Statische Daten
│   ├── branch_contexts/        # Branchen-Kontexte (JSON)
│   │   ├── beratung.json
│   │   ├── it_software.json
│   │   └── en/                 # Englische Versionen
│   ├── size_contexts/          # Größen-Kontexte
│   ├── funding/                # Förderprogramm-Daten
│   └── test_profiles_gold/     # Test-Profile für QA
│
├── admin/                      # Admin-Dashboard
│   ├── admin.css               # Einzige externe CSS-Datei
│   └── *.html                  # Admin-Templates
│
├── knowledge/                  # Wissensbasis-HTML
│   ├── four_pillars.html
│   ├── kmu_keypoints.html
│   └── en/                     # Englische Wissensbasis
│
├── scripts/                    # Utility-Scripts
├── tests/                      # Test-Suite
└── utils/                      # Helper-Module
```

---

## 3. Datenfluss

### Vollständiger Pipeline-Fluss

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           DATENFLUSS: FRAGEBOGEN → PDF                          │
└─────────────────────────────────────────────────────────────────────────────────┘

[1] FRAGEBOGEN (Frontend)
    │
    ▼
[2] POST /api/briefings/submit
    │ → routes/briefings.py
    │ → Speichert Briefing in DB (models.Briefing)
    │
    ▼
[3] ANALYSE-TRIGGER
    │ → gpt_analyze.py:run_async()
    │ → Lädt Briefing aus DB
    │ → Extrahiert answers (Fragebogen-Antworten)
    │
    ▼
[4] SCORE-BERECHNUNG (gpt_analyze.py:1520-1561)
    │ → _calculate_scores(answers)
    │     ├── Governance-Score (max 100)
    │     ├── Security-Score (max 100)
    │     ├── Value-Score (max 100)
    │     ├── Enablement-Score (max 100)
    │     └── Overall-Score (Durchschnitt)
    │
    │ → _calibrate_scores(scores, answers) (Zeile 1665+)
    │     ├── Size-Caps anwenden (solo: max 75, klein: 82, etc.)
    │     └── Status-Faktoren (testphase: 0.85, pilot: 0.90)
    │
    ▼
[5] SECTION-GENERIERUNG (gpt_analyze.py:5532+)
    │ → Für jede Section (executive_summary, quick_wins, risks, ...):
    │     │
    │     ├── [5a] Prompt laden (services/prompt_loader.py)
    │     │        └── prompts/de/<section>.md
    │     │
    │     ├── [5b] Prompt anreichern (services/prompt_enhancer.py)
    │     │        ├── Branchen-Context einfügen
    │     │        ├── Größen-Context einfügen
    │     │        ├── Score-Werte einfügen
    │     │        └── Persona-Filter (solo/team/kmu)
    │     │
    │     ├── [5c] GPT/Claude aufrufen (services/llm_client.py)
    │     │        ├── Modell: GPT-4o/o1 oder Claude
    │     │        ├── max_tokens: 4096 (kritische Sections)
    │     │        └── Fallback bei Fehler/zu kurz
    │     │
    │     └── [5d] Ergebnis als SECTION_HTML speichern
    │
    ▼
[6] TEMPLATE-RENDERING (services/report_renderer.py:277)
    │ → render(briefing, run_id, generated_sections, ...)
    │     │
    │     ├── Sprache erkennen (DE/EN)
    │     ├── Template wählen (pdf_template.html / _en.html)
    │     ├── Jinja2-Context aufbauen:
    │     │   ├── LANG, OWNER_NAME, report_date, report_id
    │     │   ├── score_gesamt, score_governance, etc.
    │     │   ├── EXECUTIVE_SUMMARY_HTML, QUICK_WINS_HTML, etc.
    │     │   └── ui() Funktion für i18n
    │     │
    │     ├── Template rendern → html
    │     ├── Logos einbetten (base64)
    │     ├── HTML optimieren (Minifizierung)
    │     ├── Leak-Phrasen entfernen (N2.5)
    │     └── Locale-Rewrite (EN-Sonderbehandlung)
    │
    ▼
[7] PDF-GENERIERUNG (services/pdf_client.py:205+)
    │ → render_pdf_from_html(html, meta, pdf_options)
    │     │
    │     ├── HTML-Größe validieren (max 1024 KB)
    │     ├── POST an PDF_SERVICE_URL/generate-pdf
    │     │   (Puppeteer-basierter externer Service)
    │     ├── PDF-Größe validieren (max 20 MB)
    │     └── Retries mit Exponential-Backoff
    │
    ▼
[8] SPEICHERUNG
    │ → models.Analysis (html, sections als JSON)
    │ → models.Report (status, pdf_url/pdf_bytes)
    │
    ▼
[9] ABRUF
    GET /api/report/pdf/{briefing_id}
    → routes/report.py:172
```

---

## 4. Kritische Dateien für Optimierung

### 4.1 Score-Berechnung

| Datei | Zeilen | Funktion | Beschreibung |
|-------|--------|----------|--------------|
| `gpt_analyze.py` | 1520-1561 | `_calculate_scores()` | Berechnet Raw-Scores aus Antworten |
| `gpt_analyze.py` | 1565-1735 | `_calibrate_scores()` | Wendet Size-Caps und Status-Faktoren an |
| `gpt_analyze.py` | 6279-6284 | Section-Zuweisung | Schreibt Scores in `sections` Dict |

**Score-Variablen (Template):**
- `score_gesamt` / `score_overall`
- `score_governance`
- `score_sicherheit` / `score_security`
- `score_wertschoepfung` / `score_value`
- `score_befaehigung` / `score_enablement`
- `score_rating` (Text: "Anfänger", "Fortgeschritten", etc.)

### 4.2 Template-Hauptdatei

| Datei | Größe | Beschreibung |
|-------|-------|--------------|
| `templates/pdf_template.html` | ~4000 Zeilen | Haupt-Template (DE) |
| `templates/pdf_template_en.html` | ~4000 Zeilen | Haupt-Template (EN) |

**Wichtige Template-Sektionen:**

| Zeile (ca.) | Sektion | Variable |
|-------------|---------|----------|
| 2955-3012 | Hero-Score | `{{ score_gesamt }}`, `{{ score_rating }}` |
| 2985-3012 | Dimension-Scores | `{{ score_governance }}`, `{{ score_sicherheit }}`, etc. |
| 3476-3491 | Quick Wins | `{{ QUICK_WINS_HTML }}` |
| 3493-3534 | Branch Profile | `{{ BRANCH_PROFILE_HTML }}` |
| 3535-3586 | Risk Engine | `{{ RISK_ENGINE_HTML }}` |
| 3644-3673 | Business Case | `{{ BUSINESS_CASE_ENGINE_HTML }}` |

### 4.3 CSS/Styling

**Wichtig:** CSS ist **inline im Template** - keine separaten CSS-Dateien für den PDF-Report!

| Datei | Zeilen (im Template) | Beschreibung |
|-------|---------------------|--------------|
| `pdf_template.html` | 8-1200 | Inline `<style>` Block |
| `admin/admin.css` | 30 Zeilen | Nur für Admin-Dashboard |

**CSS-Tokens (Custom Properties):**
```css
:root {
    /* Farben */
    --color-bg-page: #ffffff;
    --color-text-strong: #0f172a;
    --color-brand-primary: #3b82f6;
    --color-success: #22c55e;
    --color-warning: #f59e0b;
    --color-critical: #dc2626;

    /* Typography */
    --font-h1: 28pt;
    --font-h2: 20pt;
    --font-body: 11pt;

    /* Spacing (8pt Grid) */
    --space-sm: 8pt;
    --space-md: 16pt;
    --space-lg: 24pt;
}
```

**Score-relevante CSS-Klassen:**
- `.score-badge` (Zeile 319-356)
- `.dimension-score-item` (Zeile 2709-2728)
- `.hero-metric-card` (Header-Bereich)
- `.kpi-card` (KPI-Anzeigen)

### 4.4 Quick Wins

| Datei | Zeilen | Beschreibung |
|-------|--------|--------------|
| `gpt_analyze.py` | 4371+ | Quick-Wins Handler (dynamisch) |
| `gpt_analyze.py` | 5146+ | Legacy Quick-Wins Prompt |
| `prompts/de/quick_wins.md` | - | Prompt-Template |
| `pdf_template.html` | 3476-3491 | Template-Sektion |
| `pdf_template.html` | 632-660 | CSS: `.quick-wins-grid`, `.quick-win-card` |

### 4.5 Branchen-Context

| Datei | Beschreibung |
|-------|--------------|
| `data/branch_contexts/*.json` | Branchen-spezifische Daten |
| `services/prompt_enhancer.py:1406+` | Context-Loader |
| `services/prompt_enhancer.py:158-405` | `BRANCH_CONTEXT_LABELS_DE/EN` |

---

## 5. Gefundene Probleme

### 5.1 Score-Inkonsistenz

**Status:** ⚠️ Potenzielle Fallback-Werte gefunden

| Datei | Zeile | Code | Default-Wert |
|-------|-------|------|--------------|
| `gpt_analyze.py` | 3052 | `score_gov = scores.get("governance", 50)` | 50 |
| `gpt_analyze.py` | 3053 | `score_sec = scores.get("sicherheit", 50)` | 50 |
| `gpt_analyze.py` | 4379 | `score_security = scores.get("security", 50)` | 50 |
| `gpt_analyze.py` | 4380 | `score_governance = scores.get("governance", 50)` | 50 |

**Analyse:**
- Die Hauptberechnung in `_calculate_scores()` (Zeile 1520) gibt korrekte Werte zurück
- Fallback-Werte `50` werden nur verwendet wenn `scores.get()` fehlschlägt
- Die Kalibrierung (Zeile 1665) wendet Size-Caps an (z.B. solo max 75)
- **Risiko:** Wenn Score-Dict unvollständig, wird 50 als Default verwendet

**Fix-Vorschlag:**
- Prüfen ob alle Score-Keys konsistent sind (`security` vs `sicherheit`)
- Zentralen Score-Default definieren statt überall `50`

### 5.2 Tippfehler "Enwicklung"

**Status:** ✅ Nicht gefunden

- Grep nach "Enwicklung" ergab **keine Treffer**
- Der Tippfehler existiert nicht mehr im Code

### 5.3 Abgeschnittene Texte

**Token-Limits gefunden:**

| Datei | Zeile | Limit | Kontext |
|-------|-------|-------|---------|
| `gpt_analyze.py` | 1246-1253 | 4096 | PLATIN+ kritische Sections |
| `gpt_analyze.py` | 1249 | Variable | `EXEC_SUMMARY_MAX_TOKENS` |
| `gpt_analyze.py` | 1251 | Variable | `GAMECHANGER_MAX_TOKENS` |
| `gpt_analyze.py` | 1340-1344 | ENV-basiert | `OPENAI_MAX_TOKENS` |

**Truncation-Warnung (Zeile 1820):**
```python
"⚠️ LLM section=%s finished with reason=length (hit token limit %d) – risk of truncation"
```

**Analyse:**
- Token-Limits sind konfigurierbar via ENV-Variablen
- Bei `reason=length` wird gewarnt aber nicht automatisch erweitert
- **Mögliche Ursache für abgeschnittene Texte:** Token-Limit erreicht

**Fix-Vorschlag:**
- Prüfen ob `max_tokens` für alle Sections ausreichend
- Bei `reason=length` ggf. Section nachgenerieren lassen

### 5.4 Weitere Beobachtungen

**Default-Werte mit 60:**
- `gpt_analyze.py:2877`: `roi_raw = briefing.get("ROI_12M") or 60`
- `gpt_analyze.py:5666`: Stundensatz Default 60€

**String-Truncation in Logs (nicht im Output):**
- `[:100]` Pattern für Log-Messages (nicht für User-Output)
- Keine problematische Truncation für Final-HTML gefunden

---

## 6. Template-Variablen Mapping

### Scores
```python
sections["score_gesamt"] = scores.get("overall", 0)
sections["score_governance"] = scores.get("governance", 0)
sections["score_sicherheit"] = scores.get("security", 0)
sections["score_wertschoepfung"] = scores.get("value", 0)
sections["score_befaehigung"] = scores.get("enablement", 0)
```

### Haupt-Sektionen
```python
# Mapping: section_name → Template-Variable
("executive_summary", "EXECUTIVE_SUMMARY_HTML")
("quick_wins", "QUICK_WINS_HTML")
("roadmap_90d_decision", "ROADMAP_90D_DECISION_HTML")
("roadmap_12m", "ROADMAP_12M_HTML")
("business_case", "BUSINESS_CASE_HTML")
("risks", "RISKS_HTML")
("recommendations", "RECOMMENDATIONS_HTML")
```

### Meta-Daten
```python
ctx = {
    "LANG": lang,
    "OWNER_NAME": sections.get("OWNER_NAME"),
    "report_date": sections.get("report_date"),
    "report_id": sections.get("report_id"),
    "report_year": sections.get("report_year"),
    "BRANCHE_LABEL": sections.get("BRANCHE_LABEL"),
    "UNTERNEHMENSGROESSE_LABEL": sections.get("UNTERNEHMENSGROESSE_LABEL"),
    "BUNDESLAND_LABEL": sections.get("BUNDESLAND_LABEL"),
    "HAUPTLEISTUNG": sections.get("HAUPTLEISTUNG"),
}
```

---

## 7. Empfohlene Reihenfolge der Fixes

### Priorität 1: Kritische Fixes
1. **Score-Konsistenz prüfen** - Sicherstellen dass `security` und `sicherheit` nicht gemischt werden
2. **Token-Limits prüfen** - ENV `OPENAI_MAX_TOKENS_*` für abgeschnittene Sections erhöhen

### Priorität 2: Design-Optimierungen
3. **CSS-Variablen nutzen** - Score-Farben über Custom Properties steuern
4. **Score-Darstellung** - Hero-Score und Dimension-Cards CSS anpassen
5. **Quick-Wins Layout** - Grid-Layout für bessere Lesbarkeit

### Priorität 3: Wartbarkeit
6. **CSS extrahieren** - Inline-Styles in separate Datei auslagern
7. **Template-Partials** - Wiederholende Blöcke in Partials auslagern

---

## 8. Wichtige Code-Referenzen

### Score-Berechnung
- `gpt_analyze.py:1520` → `_calculate_scores()`
- `gpt_analyze.py:1665` → `_calibrate_scores()`
- `gpt_analyze.py:6279-6284` → Score-Zuweisung zu Sections

### Template-Rendering
- `services/report_renderer.py:277` → `render()`
- `services/report_renderer.py:454-466` → Context-Aufbau
- `services/report_renderer.py:478` → Jinja2 Template-Render

### PDF-Generierung
- `services/pdf_client.py:205` → `render_pdf_from_html()`
- `services/pdf_client.py:61` → HTML-Size-Validierung
- `services/pdf_client.py:179` → Footer-Template

### Quick Wins
- `gpt_analyze.py:4371` → Quick-Wins Handler
- `prompts/de/quick_wins.md` → Prompt-Definition
- `pdf_template.html:3476` → Template-Sektion

---

## 9. Nächste Schritte

Mit diesem Analyse-Report können wir:

1. ✅ Die genauen Dateien und Zeilen für jeden Fix identifizieren
2. ✅ Die richtige Reihenfolge der Änderungen planen
3. ✅ Sicherstellen, dass Fixes keine Seiteneffekte haben
4. ✅ Das Design-Briefing auf die tatsächliche CSS-Struktur anpassen

**Bereit für Phase 2: Implementierung der Fixes!**
