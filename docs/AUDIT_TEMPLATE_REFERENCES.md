# Audit: PDF-Template-Referenzen im gesamten Codebase

**Datum:** 2026-03-02
**Zweck:** Vollständige Bestandsaufnahme aller Referenzen auf `pdf_template.html` / `pdf_template_en.html` vor der Migration auf `pdf_template_v6.html`

---

## 1. Templates-Verzeichnis – Ist-Zustand

```
templates/
├── pdf_template.html        (321.421 Bytes, DE, v5.4.3)
├── pdf_template_en.html     (279.212 Bytes, EN)
├── KI-READY-2025.webp
├── dsgvo.svg
├── eu-ai.svg
├── ki-ready-2025.webp
├── ki-sicherheit-logo.webp
├── tuev-logo-transparent.webp
└── partials/
    ├── grundlagen_dsgvo_ai_act.html
    ├── guide_kreativtools_2025.html
    ├── tools_overview.html
    └── use_cases_kmu_generic.html
```

> **Hinweis:** `pdf_template_v6.html` existiert noch NICHT im Repository.
> Es gibt **keine** `railway.toml`, `railway.json`, `Dockerfile` oder `docker-compose.yml`.

---

## 2. Fundstellen-Tabelle

### 2.1 PRODUKTIONSCODE – Muss geändert werden

| # | Datei | Zeile | Referenz-Typ | Kontext / Auszug | Bewertung |
|---|-------|-------|-------------|-------------------|-----------|
| 1 | `services/report_renderer.py` | 535 | Hardcoded Default (EN) | `default_tpl = "templates/pdf_template_en.html"` | **MUSS GEÄNDERT** |
| 2 | `services/report_renderer.py` | 536 | Env-Var (EN) | `os.getenv("REPORT_TEMPLATE_PATH_EN")` | **MUSS GEÄNDERT** |
| 3 | `services/report_renderer.py` | 545 | Hardcoded Default (DE) | `default_tpl = "templates/pdf_template.html"` | **MUSS GEÄNDERT** |
| 4 | `services/report_renderer.py` | 546 | Env-Var (DE) | `os.getenv("REPORT_TEMPLATE_PATH_DE")` | **MUSS GEÄNDERT** |
| 5 | `services/report_renderer.py` | 547 | Env-Var (Legacy) | `os.getenv("REPORT_TEMPLATE_PATH")` | **MUSS GEÄNDERT** |
| 6 | `services/report_renderer.py` | 446 | Template-Dir Env | `os.getenv("REPORT_TEMPLATE_DIR", "templates")` | KEIN HANDLUNGSBEDARF (Ordner bleibt) |
| 7 | `settings.py` | 115 | PDFConfig Default | `template_path: str = "templates/pdf_template.html"` | **MUSS GEÄNDERT** |
| 8 | `settings.py` | 312 | PDFConfig Init | `os.getenv("REPORT_TEMPLATE_PATH", "templates/pdf_template.html")` | **MUSS GEÄNDERT** |
| 9 | `services/report_pipeline.py` | 74 | Legacy Renderer | `os.getenv("REPORT_TEMPLATE_PATH", "templates/pdf_template.html")` | **MUSS GEÄNDERT** |

### 2.2 ENVIRONMENT-KONFIGURATION

| # | Datei | Zeile | Referenz-Typ | Kontext / Auszug | Bewertung |
|---|-------|-------|-------------|-------------------|-----------|
| 10 | `docs/env.txt` | 34 | Env-Dump (Railway) | `REPORT_TEMPLATE_PATH="templates/pdf_template.html"` | **MUSS GEÄNDERT** (Railway!) |
| 11 | `docs/env.proposed.txt` | 223 | Vorgeschlagene Env | `REPORT_TEMPLATE_PATH="templates/pdf_template.html"` | OPTIONAL (Vorschlag) |
| 12 | `.env.example` | – | Nicht vorhanden | `REPORT_TEMPLATE_PATH` ist **nicht** in `.env.example` | OPTIONAL (hinzufügen?) |

### 2.3 TOOLS & VALIDIERUNG

| # | Datei | Zeile | Referenz-Typ | Kontext / Auszug | Bewertung |
|---|-------|-------|-------------|-------------------|-----------|
| 13 | `tools/env_sanity_checker.py` | 12 | Kommentar | `Pflicht-Keys (… REPORT_TEMPLATE_PATH …)` | KEIN HANDLUNGSBEDARF |
| 14 | `tools/env_sanity_checker.py` | 17 | Required-Liste | `REQUIRED = ["… REPORT_TEMPLATE_PATH …"]` | KEIN HANDLUNGSBEDARF (Var-Name bleibt) |

### 2.4 SCRIPTS

| # | Datei | Zeile | Referenz-Typ | Kontext / Auszug | Bewertung |
|---|-------|-------|-------------|-------------------|-----------|
| 15 | `scripts/release_blocker_gate.py` | 189 | Gate Check | `base / "templates" / "pdf_template.html"` (Regex-Check) | OPTIONAL (v6 hinzufügen) |
| 16 | `scripts/release_blocker_gate.py` | 316 | Gate Check | `base / "templates" / "pdf_template.html"` (Regex-Check) | OPTIONAL (v6 hinzufügen) |
| 17 | `scripts/release_blocker_gate.py` | 327 | Gate Check | `base / "templates" / "pdf_template.html"` (Regex-Check) | OPTIONAL (v6 hinzufügen) |
| 18 | `scripts/smoke_test.py` | 2+27 | Smoke Test | Nutzt `report_pipeline.render_report_html()` → erbt Template-Pfad | KEIN HANDLUNGSBEDARF (indirekt) |
| 19 | `apply_i_serie.py` | 117+ | Patch-Script | Direkte Referenzen auf `templates/pdf_template.html` (6x) | KEIN HANDLUNGSBEDARF (historisch) |

### 2.5 TESTS

| # | Datei | Zeile | Referenz-Typ | Kontext / Auszug | Bewertung |
|---|-------|-------|-------------|-------------------|-----------|
| 20 | `tests/test_year_audit.py` | 20 | Template-Read | `"templates" / "pdf_template.html"` | OPTIONAL |
| 21 | `tests/test_year_audit.py` | 28 | Template-Read | `"templates" / "pdf_template_en.html"` | OPTIONAL |
| 22 | `tests/test_year_audit.py` | 123 | Both Templates | `["pdf_template.html", "pdf_template_en.html"]` | OPTIONAL |
| 23 | `tests/test_p1_sprint_fixes.py` | 23,53,188,200,549 | Template-Read (5x) | `"templates" / "pdf_template.html"` | OPTIONAL |
| 24 | `tests/test_p04_pdf_preflight.py` | 139 | Template-Read | `"templates" / "pdf_template.html"` | OPTIONAL |
| 25 | `tests/test_final_check_wrap.py` | 18,36,53,167,188 | Template-Read (5x) | `"templates/pdf_template.html"` | OPTIONAL |
| 26 | `tests/test_final_check_wrap.py` | 66 | Template-Read | `"templates/pdf_template_en.html"` | OPTIONAL |
| 27 | `tests/test_finalJ_release_blockers.py` | 476 | Template-Read | `"templates/pdf_template.html"` | OPTIONAL |
| 28 | `tests/test_finalF_layout_glitches.py` | 28,43 | Template-Read (2x) | `"templates" / "pdf_template.html"` | OPTIONAL |
| 29 | `tests/test_dcl_decision_confidence.py` | 295 | Template-Read | `"templates" / "pdf_template.html"` | OPTIONAL |
| 30 | `tests/test_g24_branch_deep_dive.py` | 167,180,193,213,364,365,385 | Template-Read (7x) | Both templates, multiple checks | OPTIONAL |
| 31 | `tests/test_fix497_quality_gates.py` | 302,310,318 | Template-Read (3x) | `"templates/pdf_template.html"` | OPTIONAL |
| 32 | `tests/test_g21_platin_design.py` | 30–235,378,394 | Template-Read (16x) | Both templates, extensive CSS checks | OPTIONAL |
| 33 | `tests/test_g20_ki_stack_summary.py` | 140,151,162 | Template-Read (3x) | Both templates | OPTIONAL |

### 2.6 DOKUMENTATION

| # | Datei | Zeile | Referenz-Typ | Bewertung |
|---|-------|-------|-------------|-----------|
| 34 | `DIFF-REPORT-Templates.md` | 23,31 | Doku | KEIN HANDLUNGSBEDARF |
| 35 | `BACKEND_ANALYSE_2026-01-06.md` | 50,51,312–314 | Analyse-Doku | KEIN HANDLUNGSBEDARF |
| 36 | `backend-analyse.txt` | 460,461,556,557 | Analyse-Dump | KEIN HANDLUNGSBEDARF |
| 37 | `RELEASE_READINESS_PLAN.md` | 20 | Release-Doku | KEIN HANDLUNGSBEDARF |
| 38 | `REGENERATION-LOG.md` | 29,190,222 | Log | KEIN HANDLUNGSBEDARF |
| 39 | `TRANSLATION-MAP.md` | 5,6,336,350,384 | i18n-Doku | KEIN HANDLUNGSBEDARF |
| 40 | `IST-BERICHT-i18n.md` | 104,105,216,269,270,327,328,349,384,408 | i18n-Report | KEIN HANDLUNGSBEDARF |
| 41 | `PIPELINE_TRUTH_MAP.md` | 99,251,252 | Pipeline-Doku | KEIN HANDLUNGSBEDARF |
| 42 | `SPRINT_G_VISUAL_POLISH_REPORT.md` | 229,230 | Sprint-Report | KEIN HANDLUNGSBEDARF |
| 43 | `docs/PROJEKT_ANALYSE_REPORT.md` | 57,58,160,218,219,238,277,278,434 | Analyse | KEIN HANDLUNGSBEDARF |
| 44 | `docs/FIX_503A_FORensics.md` | 35,52,137,138,347,358 | Debug-Doku | KEIN HANDLUNGSBEDARF |
| 45 | `docs/B3_TOOLS_ENGINE_V3.md` | 325,336,347 | Tools-Doku | KEIN HANDLUNGSBEDARF |
| 46 | `docs/debug/year_audit_2025_2026.md` | 25–73 | Debug-Doku | KEIN HANDLUNGSBEDARF |
| 47 | `docs/IST_ANALYSE_BERICHT.md` | 107 | Analyse-Doku | KEIN HANDLUNGSBEDARF |
| 48 | `briefing/KI-Report-Quality-Fixes-Implementation-Guide.md` | 24,558,609,690,715 | Briefing-Doku | KEIN HANDLUNGSBEDARF |
| 49 | `docs/fix503a/render_debug_extracts/quick_wins_section.html` | 3 | Debug-Extract | KEIN HANDLUNGSBEDARF |

### 2.7 I18N / KONFIGURATION

| # | Datei | Zeile | Referenz-Typ | Bewertung |
|---|-------|-------|-------------|-----------|
| 50 | `i18n/ui_labels.json` | 13 | Kommentar-Feld | KEIN HANDLUNGSBEDARF |

### 2.8 BACKUP-DATEIEN

| # | Datei | Zeile | Referenz-Typ | Bewertung |
|---|-------|-------|-------------|-----------|
| 51 | `gpt_analyze.py` | 8754,17513 | Kommentar | KEIN HANDLUNGSBEDARF |
| ~~52~~ | ~~`gpt_analyze.py.pre-b726`~~ | — | entfernt (KIS-1128 Sprint C1) | — |
| ~~53~~ | ~~`gpt_analyze.py.bak-b725`~~ | — | entfernt (KIS-1128 Sprint C1) | — |

---

## 3. Zusammenfassung nach Kategorie

### MUSS GEÄNDERT werden (9 Stellen in 4 Dateien)

| Datei | Stellen | Beschreibung |
|-------|---------|-------------|
| `services/report_renderer.py` | 5 | Template-Selection-Logik (Z.535, 536, 545, 546, 547) |
| `settings.py` | 2 | PDFConfig Default + Init (Z.115, 312) |
| `services/report_pipeline.py` | 1 | Legacy Renderer (Z.74) |
| `docs/env.txt` | 1 | Railway Env-Dump – **spiegelt LIVE-Konfiguration!** (Z.34) |

### OPTIONAL (kann v6-Support bekommen, muss aber nicht sofort)

| Datei | Stellen | Beschreibung |
|-------|---------|-------------|
| `docs/env.proposed.txt` | 1 | Env-Vorschlag (Z.223) |
| `.env.example` | 0 | Kein REPORT_TEMPLATE_PATH vorhanden → hinzufügen? |
| `scripts/release_blocker_gate.py` | 3 | Gate Checks prüfen nur v5 Template (Z.189, 316, 327) |
| Tests (13 Dateien) | ~50+ | Alle Tests lesen nur v5 Template – v6-Tests separat anlegen |

### KEIN HANDLUNGSBEDARF (Docs, Kommentare, Backups)

| Kategorie | Dateien | Beschreibung |
|-----------|---------|-------------|
| Dokumentation | ~16 .md-Dateien | Historische Referenzen |
| ~~Backup-Dateien~~ | — | entfernt (KIS-1128 Sprint C1, recoverable via `git log --all`) |
| Tools | 1 (env_sanity_checker) | Prüft nur Env-Var-Name, nicht Wert |
| i18n | 1 (ui_labels.json) | Nur Kommentar |
| Patch-Scripts | 1 (apply_i_serie.py) | Historische Patches |

---

## 4. Environment-Variablen – Übersicht

| Variable | Wo definiert | Wo gelesen | Aktueller Wert |
|----------|-------------|------------|----------------|
| `REPORT_TEMPLATE_PATH` | `docs/env.txt` (Railway) | `report_renderer.py:547`, `report_pipeline.py:74`, `settings.py:312` | `templates/pdf_template.html` |
| `REPORT_TEMPLATE_PATH_DE` | Nirgends definiert | `report_renderer.py:546` | *(nicht gesetzt)* |
| `REPORT_TEMPLATE_PATH_EN` | Nirgends definiert | `report_renderer.py:536` | *(nicht gesetzt)* |
| `REPORT_TEMPLATE_DIR` | Nirgends definiert | `report_renderer.py:446` | *(nicht gesetzt, Default: `templates`)* |

---

## 5. Template-Selection-Logik (report_renderer.py:530–556)

```
Sprache = EN?
├── Ja → REPORT_TEMPLATE_PATH_EN gesetzt?
│   ├── Ja → verwende Env-Wert
│   └── Nein → "templates/pdf_template_en.html" (Hardcoded)
└── Nein (DE) → REPORT_TEMPLATE_PATH_DE gesetzt?
    ├── Ja → verwende Env-Wert
    └── Nein → REPORT_TEMPLATE_PATH gesetzt? (Legacy)
        ├── Ja → verwende Env-Wert
        └── Nein → "templates/pdf_template.html" (Hardcoded)
```

---

## 6. Railway-Umgebung (aus docs/env.txt)

```
REPORT_TEMPLATE_PATH="templates/pdf_template.html"   ← GESETZT auf Railway!
REPORT_TEMPLATE_PATH_DE=                              ← NICHT gesetzt
REPORT_TEMPLATE_PATH_EN=                              ← NICHT gesetzt
```

### Schnellster Weg, v6 zu aktivieren:

**Option A: Env-Var auf Railway ändern** (kein Code-Deployment nötig)
```
REPORT_TEMPLATE_PATH="templates/pdf_template_v6.html"
```

**Option B: Code-Default ändern + Deploy** (nachhaltiger)
- Hardcoded Defaults in `report_renderer.py` und `settings.py` ändern
- Neues Deployment auf Railway

**Option C: Parallelbetrieb mit Env-Var pro Sprache**
```
REPORT_TEMPLATE_PATH_DE="templates/pdf_template_v6.html"
REPORT_TEMPLATE_PATH_EN="templates/pdf_template_v6_en.html"
REPORT_TEMPLATE_PATH="templates/pdf_template_v6.html"   # Legacy Fallback
```

---

## 7. Migrationsplan-Empfehlung

### Phase 1: Vorbereitung (kein Risiko)
1. `pdf_template_v6.html` ins `templates/`-Verzeichnis legen
2. Tests für v6-Template separat anlegen
3. `release_blocker_gate.py` um v6-Checks erweitern (optional)

### Phase 2: Aktivierung (DE, über Env-Var)
1. Railway Env-Var setzen: `REPORT_TEMPLATE_PATH="templates/pdf_template_v6.html"`
2. Alternativ: `REPORT_TEMPLATE_PATH_DE="templates/pdf_template_v6.html"`
3. Testen → bei Problemen sofort zurückrollen (Env-Var auf alten Wert)

### Phase 3: Code-Defaults aktualisieren
1. `report_renderer.py:545` → `"templates/pdf_template_v6.html"`
2. `settings.py:115` → `"templates/pdf_template_v6.html"`
3. `settings.py:312` → Fallback-Default ändern
4. `services/report_pipeline.py:74` → Fallback-Default ändern

### Phase 4: Aufräumen
1. Alte Template-Datei behalten (für Rollback)
2. Dokumentation aktualisieren
3. Tests auf v6 umstellen oder dual testen

---

## 8. Risikobewertung

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| v6-Template hat Jinja2-Syntax-Fehler | Mittel | Hoch (Report bricht ab) | `_self_check()` in report_renderer.py validiert bei jedem Render-Aufruf |
| Env-Var vergessen (Pipeline nutzt altes Template) | Niedrig | Mittel | `report_pipeline.py` liest REPORT_TEMPLATE_PATH – gleiche Var |
| Tests schlagen fehl nach Migration | Hoch | Niedrig (nur CI) | Tests prüfen v5-spezifische CSS-Klassen/Inhalte |
| EN-Template nicht migriert | Mittel | Mittel | EN hat eigene Logik, muss separat bedacht werden |

---

*Erstellt durch Claude Code – Audit-Task, kein Code geändert.*
