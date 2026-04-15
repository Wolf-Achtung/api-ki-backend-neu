# Report-System Audit — 8-Phasen-Gutachten

**Datum:** 15.04.2026
**Auditor:** Senior-Gutachter (5 Rollen)
**Scope:** R1 KI-Status-Report, KPA KI-Potenzial-Analyse, Strategiebericht
**Branch:** `claude/review-report-system-Srlse`

---

## A. Executive Summary

### Gesamturteil

Das Report-System ist technisch ambitioniert und funktional weitgehend vollständig. Die drei Reports werden durch eine komplexe Pipeline erzeugt: LLM-Generierung → deterministische Engines → Sanitizer-Kaskade → Jinja2-Template → Puppeteer/Chromium PDF. Die **KPA** (10 Seiten) liefert professionelle Ergebnisse mit korrekten Seitenumbrüchen. **R1** (20 Seiten) und **Strategiebericht** (16 Seiten) leiden unter systematischen Seitenumbruch-Problemen, Typografie-Inkonsistenzen und einer Mapping-Lücke.

### Wichtigste Stärken

- Robuste Multi-Engine-Pipeline mit >80 Post-Processing-Schritten
- Deterministische Sections (Business Case, Funding, Starter-Kit) liefern konsistente Qualität
- KPA-Template zeigt, dass das System korrekte Seitenumbrüche produzieren kann
- Umfangreiche Sanitizer-Kaskade verhindert LLM-Halluzinationen im Finanzteil
- Audit-Trail und Debug-Logging auf hohem Niveau

### Kritischste Schwächen

| # | Befund | Schwere | Betroffener Report |
|---|--------|---------|-------------------|
| **C1** | `PROMPT_VORLAGEN_HTML` wird nie gesetzt — `#prompts-section` ist Dead-Code (Guard existiert, Section wird korrekt ausgeblendet) | **NIEDRIG** | R1 |
| **C2** | Doppelter Page-Break in Challenge-Sektion (CSS + generiertes HTML) | **HOCH** | R1 |
| **C3** | `break-inside: avoid` auf großen Containern (`.scenarios-section`, `.business-case-engine-v2`) erzeugt halbleere Seiten | **HOCH** | R1 |
| **C4** | `#funding-section` erzwingt Seitenumbruch → 70% Leerraum nach AI Act | **HOCH** | R1 |
| **C5** | R1-Fließtext bei 10pt, Strategy bei 11pt, KPA bei 10pt — inkonsistente Familie | **MITTEL** | Alle |
| **C6** | Orphan/Widow-Werte R1=5/5, Strategy=5/5, KPA=3/3 — aggressivere Werte erzeugen mehr Leerraum | **MITTEL** | R1, Strategy |
| **C7** | `#prompts-section` ist Dead Code — Variable nie gesetzt, Guard existiert, Section korrekt ausgeblendet | **NIEDRIG** | R1 |

### Urteil zur professionellen Reife

**7/10** — Das System ist produktionsfähig, aber nicht ausgereift. Die KPA zeigt, wie es aussehen sollte. R1 und Strategy brauchen CSS-Korrekturen auf Template- und Generator-Ebene, um den gleichen Standard zu erreichen. Kein Inhaltsverlust festgestellt, aber eine Mapping-Lücke (`PROMPT_VORLAGEN_HTML`) und mehrere Layout-Artefakte.

---

## B. Phase 1 — Repository- und Systemaufnahme

### B.1 Systemarchitektur

```
Questionnaire (Briefing)
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  Content-Erzeugung                                  │
│  ├─ gpt_analyze.py (R1: ~1MB, Haupt-Orchestrator)  │
│  ├─ strategy_pipeline.py (Strategy)                 │
│  └─ gamechanger_deep_dive.py (KPA)                  │
│                                                     │
│  LLM-Calls (OpenAI/Claude) + Deterministische       │
│  Engines (Business Case, Funding, Vendor, Starter)  │
└──────────────┬──────────────────────────────────────┘
               │ sections dict
               ▼
┌─────────────────────────────────────────────────────┐
│  Sanitizer-Kaskade                                  │
│  ├─ report_healer.py (7 Fix-Passes)                 │
│  ├─ pipeline_sanitizers.py (Non-Latin)               │
│  ├─ b25_enforcer.py (Funding-Blacklist)              │
│  ├─ strategy_sanitizer.py (%-Plausibilität)          │
│  └─ content_quality_enforcer.py                      │
└──────────────┬──────────────────────────────────────┘
               │ sanitized sections
               ▼
┌─────────────────────────────────────────────────────┐
│  Template-Rendering                                 │
│  ├─ report_renderer.py → pdf_template_v7.html (R1)  │
│  ├─ strategy_renderer.py → strategy_report.html     │
│  └─ gamechanger_deep_dive.py → gamechanger_*.html   │
│                                                     │
│  Jinja2 Environment + Post-Render-Fixes (>40 Regex) │
└──────────────┬──────────────────────────────────────┘
               │ final HTML
               ▼
┌─────────────────────────────────────────────────────┐
│  PDF-Rendering                                      │
│  ├─ pdf_client.py → externer PDF-Service (Puppeteer)│
│  ├─ pdf_guard.py (Size-Limits, Truncation)           │
│  └─ PyMuPDF Metadata-Stamping                        │
└─────────────────────────────────────────────────────┘
```

### B.2 Report-spezifische Dateien

| Komponente | R1 | Strategy | KPA |
|-----------|-----|----------|-----|
| **Template** | `templates/pdf_template_v7.html` (93KB, 2089 Zeilen) | `templates/strategy_report.html` (42KB, 1249 Zeilen) | `templates/gamechanger_deep_dive_v1.html` (35KB, 811 Zeilen) |
| **Renderer** | `services/report_renderer.py` (102KB) | `services/strategy_renderer.py` (23KB) | `services/gamechanger_deep_dive.py` (35KB) |
| **Pipeline** | `gpt_analyze.py` (1MB) | `services/strategy_pipeline.py` (58KB) | (in gamechanger_deep_dive.py) |
| **Route** | `routes/report.py` (45KB) | `routes/strategy.py` (34KB) | (in routes/report.py) |
| **CSS** | Inline im Template | Inline im Template | Inline im Template |

### B.3 Gemeinsam genutzte Dateien

- `services/pdf_client.py` — PDF-Rendering für alle drei Reports
- `services/html_enhancer.py` — LLM-HTML → CSS-Design-Klassen (R1 + Strategy + KPA)
- `services/pipeline_sanitizers.py` — Non-Latin-Bereinigung (alle)
- `b25_enforcer.py` — Funding-Blacklist (R1 + Strategy)
- `services/extra_sections.py` — Score-Labels, Benchmarks, Funding-Tabelle (R1, teilweise Strategy)
- `services/sofort_start_generator.py` — Sofort-Start + Prompts + Challenge (nur R1)
- `services/business_case_engine_v2.py` — ROI-Szenarien (R1, Input für KPA)
- `services/vendor_audit_engine.py` — Vendor-Prüfung (R1, Input für KPA)
- `services/tools_starter_kits.py` — Starter-Kit HTML (R1)
- `services/funding_renderer.py` — Fördermittel-Rendering (R1)

### B.4 Zentrale technische Beobachtungen

1. **Kein gemeinsames CSS**: Jedes Template hat sein eigenes Inline-`<style>`, keine shared CSS-Datei. Design-Änderungen müssen in jedem Template einzeln erfolgen.

2. **Keine Jinja2-Macros in R1/KPA**: Nur der Strategiebericht nutzt ein `chapter_banner` Macro. R1 und KPA haben die Banner direkt im HTML.

3. **Massive Post-Processing-Kette in R1**: `render()` in `report_renderer.py` enthält >80 Regex-basierte Fixes nach dem Jinja2-Render. Jeder Fix ist mit einem Sprint-Code markiert (Z+1c, B734a, U1b, etc.).

4. **Generiertes HTML enthält eigene Break-Regeln**: `sofort_start_generator.py`, `business_case_engine_v2.py`, `vendor_audit_engine.py` und `quickwins_renderer.py` setzen `break-inside:avoid` und `page-break-before:always` per Inline-Style in generiertes HTML. Diese **überschreiben** Template-CSS-Regeln durch höhere Spezifität.

5. **Template-Pfad-Konfiguration**: R1 nutzt `REPORT_TEMPLATE_PATH_DE` Env-Var (Default: `templates/pdf_template.html`). `pdf_template_v7.html` muss explizit konfiguriert sein. Tests referenzieren v7, Runtime möglicherweise nicht.

---

## C. Phase 2 — End-to-End-Datenfluss

### C.1 R1 KI-Status-Report — Datenfluss

```
Briefing.answers
    │
    ├─► gpt_analyze.py: ~30 parallele LLM-Calls → sections dict
    │     Ergebnis: EXECUTIVE_SUMMARY_HTML, RISKS_HTML, GAMECHANGER_HTML,
    │               KI_STACK_SUMMARY_HTML, BRANCH_DEEP_DIVE_HTML, ...
    │
    ├─► Deterministische Engines (sequentiell nach LLM):
    │     sofort_start_generator.py → SOFORT_START_HTML (inkl. 4 Prompts + Lern-Prompt)
    │     sofort_start_generator.py → CHALLENGE_30_TAGE_HTML
    │     business_case_engine_v2.py → BUSINESS_CASE_ENGINE_HTML
    │     vendor_audit_engine.py → VENDOR_AUDIT_HTML
    │     tools_starter_kits.py → STARTER_KIT_HTML
    │     extra_sections.py → AI_ACT_DUTY_MATRIX_HTML, FOERDERPOTENZIAL_HTML, ...
    │     quickwins_renderer.py → QUICK_WINS_HTML
    │
    ├─► report_healer.py: 7 Fix-Passes (Persona, Dedup, ROI, Trim, Budget)
    │
    ├─► report_renderer.py render():
    │     1. Placeholder-Bereinigung (?, —, TBD, n/a)
    │     2. Poison-Phrase-Detection → Sections löschen
    │     3. <50-Zeichen-Sections → leer setzen
    │     4. Markup() wrapping für |safe
    │     5. ctx-Dict aufbauen mit **sections + ui() + Metadata
    │     6. Jinja2 render(pdf_template_v7.html, **ctx)
    │     7. >40 Post-Render Regex-Fixes
    │     8. Logo-Embedding, HTML-Optimierung
    │
    └─► pdf_client.py → Puppeteer PDF-Service
```

### C.2 Strategy — Datenfluss

```
Briefing.answers + R1-Analysis.meta + Strategy-Questions
    │
    ├─► strategy_pipeline.py: 8 Phasen (S1→S8 + exec_summary)
    │     Phasen 1-7: OpenAI GPT-4o, Phase 8 (Exec): Claude (Anthropic)
    │     + naechste_schritte: Statisches Template (nicht LLM-generiert)
    │
    ├─► strategy_sanitizer.py: %-Plausibilität, Sprach-Substitutionen
    ├─► pipeline_sanitizers.py: Non-Latin Strip
    ├─► b25_enforcer.py: Funding-Blacklist
    │
    ├─► strategy_renderer.py:
    │     1. Score-Neuberechnung (identische R1-Formel, Drift-Risiko!)
    │     2. _strip_prompt_leaks() auf alle Sections
    │     3. _strip_funding_total() auf S7
    │     4. ROI-Methodik-Note + "Mit Förderung"-Box in exec_summary
    │     5. Jinja2 render(strategy_report.html, **context)
    │     6. enhance_strategy_html() → CSS-Design-Klassen
    │     7. _enforce_budget_values() → Halluzinierte Zahlen korrigieren
    │
    └─► pdf_client.py → Puppeteer PDF-Service
```

### C.3 KPA — Datenfluss

```
R1-Analysis.sections + Briefing.answers
    │
    ├─► gamechanger_deep_dive.py:
    │     build_gamechanger_context() → Extraktion aus R1
    │     _extract_canonical_bc() → Business-Case-Werte mit Segment-Caps
    │     generate_deep_dive_sections():
    │       GC_BRUCHPUNKT_HTML (LLM)
    │       GC_IMPL_PLAN_HTML (LLM)
    │       BC_DEEP_DIVE_HTML (deterministisch — pure Python)
    │       GC_RISK_HTML (LLM)
    │       GC_NEXT_STEPS_HTML (LLM)
    │
    ├─► _enforce_kpa_break_even() → Payback-Monate korrigieren
    ├─► sanitize_non_latin_sections()
    ├─► enhance_kpa_html() → CSS-Design-Klassen
    │
    ├─► render_deep_dive_html():
    │     template_vars = {**sections, **context}
    │     Jinja2 render(gamechanger_deep_dive_v1.html, **template_vars)
    │
    └─► pdf_client.py → Puppeteer PDF-Service
```

### C.4 Content-Suppression-Risiken

Folgende Mechanismen können Inhalte **stillschweigend unterdrücken**:

| Mechanismus | Datei | Bedingung | Risiko |
|------------|-------|-----------|--------|
| POISON_PHRASES | report_renderer.py:672 | LLM-Metasprache in BRANCH_DEEP_DIVE / KI_STACK | Section → `""` |
| FIX-R5-6 | report_renderer.py:693 | `_HTML` Key < 50 Zeichen | Section → `""` |
| M8 Content Gate | report_renderer.py:756 | KICKOFF/NINETY_DAY < 30 Wörter | Section → `""` |
| W3/X3 Thin Hider | report_renderer.py:1134 | Section < 50 Wörter oder Platzhalter-Phrasen | Section → `""` |
| Y7 Dedup | report_renderer.py:1167 | ROADMAP_90D > 60% Überlappung mit ROADMAP | ROADMAP_90D → `""` |
| Y1-Y4 Empty | report_renderer.py:1191 | "Keine Daten" oder < 30 Non-Numeric-Zeichen | Section → `""` |
| PDFGuard Truncation | pdf_guard.py:217 | HTML > 1.2MB + TRUNCATE=1 | Sections gekürzt |
| HTML Size Limit | pdf_client.py:87 | HTML > 1024KB | **Kein PDF** |

---

## D. Phase 3 — Vollständigkeits- und Mapping-Audit

### D.1 R1: Kritische Mapping-Lücke

| Inhalt | Generiert? | An Template übergeben? | Im Template referenziert? | Im PDF sichtbar? | Befund |
|--------|-----------|----------------------|--------------------------|-----------------|--------|
| **PROMPT_VORLAGEN_HTML** | **NEIN** — nie gesetzt | Nein (leerer String) | JA — `#prompts-section` Z.1617 (mit `{% if %}` Guard) | Nein (Guard aktiv) | Dead Code — Guard verhindert leere Section |
| SOFORT_START_HTML (inkl. 4 Prompts) | Ja | Ja | Ja — `#sofort-start` Z.1400 | Ja | OK — Prompts sind hier, nicht in prompts-section |
| CHALLENGE_30_TAGE_HTML | Ja | Ja | Ja — `#challenge-section` Z.1639 | Ja | **DOPPELTER PAGE-BREAK** (siehe C2) |
| BUSINESS_CASE_ENGINE_HTML | Ja | Ja | Ja — `#business-case-compact` Z.1479 | Ja | break-inside:avoid auf großem Container |
| VENDOR_AUDIT_HTML | Ja | Ja, conditional | Ja — `#vendor-section` Z.1677 | Ja | OK |
| AI_ACT_DUTY_MATRIX_HTML | Ja | Ja, conditional | Ja — `#aiact-compact` Z.1706 | Ja | OK |
| FOERDERPOTENZIAL_HTML | Ja | Ja, conditional | Ja — `#funding-section` Z.1758 | Ja | Erzwungener Seitenumbruch davor |
| STARTER_KIT_HTML | Ja | Ja | Ja — `#tools-section` Z.1609 | Ja | OK |
| QUICK_WINS_HTML | Ja | Ja | Ja — `#quick-wins-section` Z.1455 | Ja | OK |
| ROADMAP_90D_DECISION_HTML | Ja | Ja | Ja — `#roadmap-90d` Z.1467 | Ja, wenn >50 Wörter | W3-Risiko |
| GAMECHANGER_DECISION_HTML | Ja | Ja, conditional | Ja — `#gamechanger-section` Z.1785 | Ja, wenn >50 Wörter | W3-Risiko |
| ADVISOR_NOTE_HTML | Ja | Ja, conditional | Ja — `#advisor-note` Z.1808 | Ja | OK |

**Zentraler Befund:** Die Prompts werden in `SOFORT_START_HTML` generiert (sofort_start_generator.py Z.1534-1599), aber das Template hat eine separate `#prompts-section` die `PROMPT_VORLAGEN_HTML` erwartet — ein Key der **nirgends im System** gesetzt wird. Das Ergebnis ist eine leere Section mit sichtbarem Header ("Copy-Paste Prompts") und Glance-Box aber ohne Inhalt im PDF.

### D.2 Strategy: Mapping-Prüfung

| Inhalt | Generiert? | An Template übergeben? | Befund |
|--------|-----------|----------------------|--------|
| exec_summary | Ja (Claude) | Ja + ROI-Note + Förder-Box injiziert | OK |
| section_s1 bis section_s8 | Ja (GPT-4o) | Ja, via _strip_prompt_leaks() | OK |
| section_s_moat | Ja, parallel | Ja, conditional `{% if section_s_moat %}` | Kann leer/fehlend sein → Kapitel 9 verschwindet |
| naechste_schritte | Statisches Template | Ja, ohne Sanitizer | OK |
| readiness_score | Neuberechnet | Ja | **Drift-Risiko**: identische Formel in pipeline + renderer |

### D.3 KPA: Mapping-Prüfung

| Inhalt | Generiert? | An Template übergeben? | Befund |
|--------|-----------|----------------------|--------|
| GC_BRUCHPUNKT_HTML | Ja (LLM) | Ja | OK |
| GC_IMPL_PLAN_HTML | Ja (LLM) | Ja | OK |
| BC_DEEP_DIVE_HTML | Ja (deterministisch) | Ja | OK |
| GC_RISK_HTML | Ja (LLM) | Ja | OK |
| GC_NEXT_STEPS_HTML | Ja (LLM) | Ja | OK |
| canonical_bc (hours/roi/payback) | Ja, mit Caps | Ja, für Cover-KPIs | OK |

**KPA hat keine Mapping-Lücken.** Alle 5 Sections + Cover-Daten sind durchgängig gemappt.

---

## E. Phase 4 — Vergleich der drei Reports als Produktfamilie

### E.1 Architektur-Vergleich

| Eigenschaft | R1 | Strategy | KPA |
|------------|-----|----------|-----|
| Seitenzahl | ~20 | ~16 | ~10 |
| Sections mit erzwungenem Seitenumbruch | 9 + 2 (Decision, Impressum) | 11 (jedes Kapitel via Macro) | 4 (via ID-Selektor) + 1 (Impressum inline) |
| Sections ohne erzwungenen Umbruch | 7 (flows, quick-wins bis aiact) | 0 | 1 (#dd-bruchpunkt) |
| Macro-System | Keines | `chapter_banner()` Macro | Keines |
| CSS-Architektur | break-before auf IDs + Inline-Styles im generierten HTML | page-break-before via `.page-break` Klasse | break-before auf IDs |
| body font-size | **10pt** | **11pt** (C5-Fix) | **10pt** |
| orphans/widows (body) | 4/4 | 5/5 | 4/4 |
| orphans/widows (content) | **5/5** | **5/5** | **3/3** |
| Max break-Verschachtelungstiefe | 5 Ebenen | 4 Ebenen | **3 Ebenen** |
| `break-inside:avoid` auf großen Containern | **JA** (.scenarios-section, .business-case-engine-v2) | Nein | Nein |
| Generiertes HTML mit eigenen break-Regeln | **JA** (Inline-Styles) | Nein (nur CSS-Klassen) | Nein |
| `@media print` Block | Ja (dupliziert Base-Regeln) | Ja (dupliziert Base-Regeln) | Ja (dupliziert Base-Regeln) |

### E.2 Warum die KPA funktioniert — Schlüsselunterschiede

Die KPA hat die besten Seitenumbrüche. Die Gründe:

1. **Flache Struktur**: Nur 5 Content-Sections + Cover + Impressum. Max 3 Ebenen break-Verschachtelung.
2. **`.section { break-inside: auto; }`**: Sections dürfen über Seiten fließen.
3. **Nur kleine Elemente geschützt**: `.glance-box`, `.kpi-card`, `.action-card` — nie größer als ~200px.
4. **Kein `break-inside:avoid` auf großen Containern**: Kein Container > 1/3 Seitenhöhe ist geschützt.
5. **Niedrige orphan/widow-Werte (3/3)**: Chromium hat mehr Freiheit beim Seitenumbruch.
6. **Kein generiertes HTML mit eigenen break-Regeln**: Alle break-Regeln kommen aus dem Template-CSS.

### E.3 Konsistenzen (gut)

- **Banner-Design**: Alle drei Templates nutzen `.chapter-banner` mit ähnlichem Gradient-Styling
- **Glance-Box**: "Auf einen Blick"-Boxen in R1 und KPA konsistent
- **Impressum-Struktur**: Identisch in allen drei Reports
- **Branchenspezifischer Disclaimer**: Identische Logik (Steuer/WP/Recht/Buchh.)
- **Score-Donut (Cover)**: R1 und Strategy nutzen SVG-basiertes Score-Widget

### E.4 Inkonsistenzen (störend)

| Element | R1 | Strategy | KPA | Bewertung |
|---------|-----|----------|-----|-----------|
| **Fließtext-Größe** | 10pt | 11pt | 10pt | Strategy ist Ausreißer nach oben — R1/KPA zu klein |
| **Section-Header-Stil** | Badge + Kicker + H2 | Banner-Macro mit Nummer + Kategorie | Banner mit Nummer + Kategorie | R1 mischt zwei Stile (mit/ohne Banner) |
| **Kapitel-Nummerierung** | Keine | 1–9 | 1–5 | R1 wirkt wie ein Magazin, Strategy/KPA wie ein Bericht |
| **Banner-Farbe** | Dunkelgrün (#1a3a2a) | Navy-Gradient (#0f172a→#1e3a5f) | Teal-Gradient (#134e4a→#0d9488) | Drei verschiedene Farbwelten |
| **TOC-Stil** | Mehrspaltig mit Level-Indicator | Einspaltig mit Nummern | Mini-TOC auf Cover | Drei völlig verschiedene Ansätze |
| **orphan/widow** | 5/5 | 5/5 | 3/3 | KPA toleranter = bessere Umbrüche |
| **Chapter-Banner-Implementierung** | Direkt im HTML | Jinja2-Macro | Direkt im HTML | Keine einheitliche Methode |

### E.5 Vereinheitlichungspotenziale

1. **Fließtext einheitlich 11pt**: Alle drei Reports auf 11pt body/section-body
2. **orphan/widow einheitlich 3/3**: KPA-Werte als Standard für alle
3. **Banner-System vereinheitlichen**: Ein gemeinsames Macro oder Partial für alle drei
4. **Farbsystem**: Gemeinsame Primärfarbe mit reportspezifischem Akzent wäre professioneller
5. **TOC-Ansatz**: Einheitlich oder bewusst reportspezifisch (aber dann dokumentiert)

---

## F. Phase 5 — Gestalterische und editoriale Bewertung

### F.1 Bewertungsmatrix (0–10)

| Kriterium | R1 | Strategy | KPA | Begründung |
|-----------|-----|----------|-----|------------|
| **Professionalität** | 7 | 8 | 8 | R1: gemischte Section-Stile (mit/ohne Banner). Strategy/KPA: konsistente Kapitelstruktur |
| **Übersichtlichkeit** | 5 | 7 | 8 | R1: 20 Seiten mit zu vielen Sektionstypen. Strategy: kompakt nach C4-Banner-Fix. KPA: 10 Seiten, klar strukturiert |
| **Layout** | 5 | 7 | 8 | R1: halbleere Seiten durch break-Probleme. Strategy: gut nach Banner-Kompression. KPA: sauber |
| **Typografie** | 6 | 7 | 6 | R1/KPA: 10pt Fließtext zu klein für Print. Strategy: 11pt besser. Alle: viele Font-Größen (>30 verschiedene) |
| **Fließtext-Lesbarkeit** | 5 | 7 | 6 | R1/KPA: 10pt bei A4-Print grenzwertig. Strategy: 11pt akzeptabel |
| **Informationshierarchie** | 6 | 8 | 7 | R1: zu flach — Badges, Kickers, Pills, Level-Dots, Banner gemischt. Strategy: klare Nummerierung. KPA: 5 Kapitel, klar |
| **Datenvisualisierung** | 7 | 7 | 7 | Gute KPI-Cards, Score-Widgets, Scenario-Cards in allen Reports |
| **Konsistenz** | 5 | 7 | 8 | R1: Section-Header-Stilbruch (mit/ohne Banner). Strategy: konsistent durch Macro. KPA: konsistent |
| **Markenwirkung** | 6 | 7 | 7 | Drei verschiedene Farbwelten schwächen die Markenkohärenz |
| **Vertrauenswirkung** | 7 | 8 | 8 | Gute Datenbasis, TÜV-Badge, Score-Donut wirken seriös |
| **Produktionsqualität** | 5 | 6 | 8 | R1: halbleere Seiten, leere Section. Strategy: orphan-Probleme möglich. KPA: produktionsreif |

### F.2 Zentrale gestalterische Befunde

**R1 — Fließtext zu klein (10pt)**
`pdf_template_v7.html` Z.82: `body { font-size: 10pt; }` und Z.264: `.section-body { font-size: 10pt; }`
Bei A4-Print (210mm breit, ~170mm Textbreite) ergibt 10pt ca. 85-90 Zeichen pro Zeile — zu lang für optimale Lesbarkeit (optimal: 60-75). 11pt würde die Zeilenlänge auf ~78 reduzieren.

**R1 — Zu viele visuelle Ebenen**
Der R1 nutzt gleichzeitig: `.level-indicator`, `.badge`, `.section-kicker`, `.section-pill`, `.chapter-banner`, `.glance-box`, `.xref`, `.section-transition`. Das sind 8 verschiedene UI-Elemente für Sektionsnavigation. Die KPA kommt mit 3 aus (Banner, Glance-Box, Section-Body).

**Alle — Zu viele Font-Größen**
R1 hat >45 verschiedene `font-size`-Deklarationen, Strategy >35, KPA >30. Eine professionelle Typografie nutzt 6-8 Stufen. Die Vielzahl erzeugt einen unruhigen visuellen Eindruck.

**R1 — Halbleere Seiten durch break-Kaskaden**
Fünf dokumentierte Problemstellen (S.5→6, S.11→12, S.13→14, S.15→16, S.16→17), alle verursacht durch `break-inside:avoid` auf zu großen Containern oder erzwungene Seitenumbrüche mit zu wenig Folge-Content.

---

## G. Phase 6 — Ursachenanalyse

### G.1 Ursachenzuordnung pro Befund

| Befund | Ursache | Ebene | Datei(en) |
|--------|---------|-------|-----------|
| **C1: PROMPT_VORLAGEN_HTML nie gesetzt** | Mapping-Lücke — Key wird in keiner Engine/Pipeline erzeugt, aber im Template referenziert | Mapping + Template | `gpt_analyze.py` (fehlt), `pdf_template_v7.html:1626` |
| **C2: Doppelter Page-Break Challenge** | Generator erzeugt `page-break-before:always` Inline-Div, Template-CSS setzt `break-before:page` auf `#challenge-section` | Generator + Template-CSS | `sofort_start_generator.py:1888,2137`, `pdf_template_v7.html:128` |
| **C3: break-inside:avoid auf großen Containern** | CSS-Regel + Inline-Styles verhindern Seitenumbruch innerhalb von Containern die > 50% der Seitenhöhe belegen | Template-CSS + Generator-Inline-Styles | `pdf_template_v7.html:887,890`, `business_case_engine_v2.py:2240,2242` |
| **C4: Erzwungener Seitenumbruch vor Funding** | `#funding-section` in der forced-break-Liste, aber vendor+aiact davor füllen die Seite nicht | Template-CSS | `pdf_template_v7.html:130` |
| **C5: Inkonsistente Fließtext-Größe** | C5-Fix hat nur Strategy auf 11pt gebracht, R1+KPA blieben bei 10pt | Template-CSS | `pdf_template_v7.html:82`, `strategy_report.html:95`, `gamechanger_deep_dive_v1.html` |
| **C6: Aggressive orphan/widow-Werte** | R1+Strategy: 5/5 statt KPA-bewährte 3/3. Höhere Werte → Chromium schiebt mehr Content auf nächste Seite | Template-CSS | `pdf_template_v7.html:269`, `strategy_report.html:533` |
| **C7: Fehlende {% if %}-Guard um prompts-section** | Template rendert Section immer, auch wenn Variable leer ist | Template | `pdf_template_v7.html:1616` |

### G.2 Ursachenmuster

**Muster 1: Generator-CSS vs. Template-CSS Konflikt**
Drei Generatoren (`sofort_start_generator.py`, `business_case_engine_v2.py`, `vendor_audit_engine.py`) setzen Inline-Styles mit `page-break-inside:avoid` und `break-inside:avoid`. Diese haben **höhere Spezifität** als Template-CSS-Regeln und können nicht durch Template-CSS überschrieben werden. Der C3-Fix (commit `9c974c3`) hat CSS-Regeln geändert, aber die Inline-Styles in den Generatoren nicht angepasst — daher keine Wirkung.

**Muster 2: "avoid-Kaskade" auf großen Containern**
Wenn ein Container mit `break-inside:avoid` nicht auf die aktuelle Seite passt, schiebt Chromium den gesamten Container auf die nächste Seite und füllt die vorherige Seite mit Leerraum. Bei Container-Höhe > 50% der Seite entsteht eine halbleere Seite. Betroffen:
- `.scenarios-section` (~3 Karten à 200px + Heading = ~700px bei Seitenhöhe ~960px)
- `.business-case-engine-v2` (Szenarien + Details = oft > 1 Seite)
- Erfolgs-Tracking Box (~250px mit `break-inside:avoid`)
- Einzelne Prompt-Boxen (~150px mit `page-break-inside:avoid`)

**Muster 3: Erzwungene Seitenumbrüche mit zu wenig Folge-Content**
`#funding-section` hat `break-before:page`, aber die Sections davor (`#vendor-section`, `#aiact-compact`) haben KEINEN erzwungenen Umbruch. Wenn vendor+aiact zusammen die Seite nicht füllen, bleibt der Rest leer.

**Muster 4: Frühere Fixes wirken nicht wegen Inline-Styles**
| Commit | CSS-Fix | Warum unwirksam |
|--------|---------|-----------------|
| `c21ea1a` | `orphans:3; widows:3` auf Fließtext | Seitenumbruch-Probleme sind nicht orphan/widow-basiert sondern container-basiert |
| `9c974c3` | `break-inside:auto` auf Phase/Kit/Vendor | **Inline-Styles** in generiertem HTML haben höhere Spezifität und überschreiben die CSS-Regeln |

---

## H. Phase 7 — Sichere Optimierungsstrategie

### H.1 Priorisierte Maßnahmen

#### M1: Doppelten Page-Break in Challenge entfernen [PRIO: HOCH]
- **Problem:** C2 — `#challenge-section` CSS + generierter `<div style="page-break-before:always">` = doppelter Umbruch
- **Ebene:** Generator (`sofort_start_generator.py`)
- **Änderung:** `<div style="page-break-before: always;"></div>` an Z.1888 und Z.2137 entfernen
- **Risiko:** GERING — Template-CSS erzwingt den Umbruch bereits
- **Inhaltsverlust:** Nein — nur ein leeres Div wird entfernt
- **Regression:** Keine — kein sichtbarer Content betroffen, KPA unberührt

#### M2: break-inside:avoid von großen Containern entfernen [PRIO: HOCH]
- **Problem:** C3 — `.scenarios-section` und `.business-case-engine-v2` > Seitenhöhe
- **Ebene:** Template-CSS (`pdf_template_v7.html`) + Generator-Inline-Styles (`business_case_engine_v2.py`)
- **Änderung:**
  - `pdf_template_v7.html` Z.887: `.scenarios-section { break-inside: avoid }` → `break-inside: auto`
  - `pdf_template_v7.html` Z.890: `.business-case-engine-v2 { break-inside: avoid }` → `break-inside: auto`
  - `business_case_engine_v2.py` Z.2240: Inline-Style `page-break-inside:avoid;break-inside:avoid` entfernen
  - `business_case_engine_v2.py` Z.2242: Inline-Style `page-break-inside:avoid;break-inside:avoid` entfernen
- **Risiko:** GERING — Einzelne `.scenario-card` behalten `break-inside:avoid`, nur der Gruppen-Container wird erlaubt zu brechen
- **Inhaltsverlust:** Nein — Content bleibt vollständig, nur Seitenumbruch-Verhalten ändert sich
- **Schutz:** ROI-Szenarien-3-Karten-Layout bleibt visuell erhalten (flex, min-width)

#### M3: #funding-section aus forced-break-Liste entfernen [PRIO: HOCH]
- **Problem:** C4 — Erzwungener Umbruch erzeugt 70% Leerraum nach AI Act
- **Ebene:** Template-CSS (`pdf_template_v7.html`)
- **Änderung:** `#funding-section` aus der break-before:page ID-Liste entfernen (Z.130)
- **Risiko:** GERING — Funding-Banner bleibt visuell trennend, Chapter-Banner hat `break-inside:avoid` + `break-after:avoid`
- **Inhaltsverlust:** Nein — Content unverändert
- **Regression:** Banner könnte am unteren Seitenrand beginnen, aber `break-after:avoid` verhindert Trennung vom Content

#### M4: Fehlende Guard für prompts-section [PRIO: MITTEL]
- **Problem:** C7 + C1 — Section rendert mit leerem Body
- **Ebene:** Template (`pdf_template_v7.html`)
- **Änderung:** `{% if PROMPT_VORLAGEN_HTML %}` Guard um `#prompts-section` Z.1616-1628 (analog zu vendor-section)
- **Risiko:** GERING — Section verschwindet nur wenn Variable leer ist (aktueller Zustand)
- **Inhaltsverlust:** Nein — Section hat aktuell keinen Content, Guard verhindert leere Section
- **Hinweis:** Langfristig sollte entweder `PROMPT_VORLAGEN_HTML` populiert oder die Section entfernt werden

#### M5: Fließtext auf 11pt anheben (R1) [PRIO: MITTEL]
- **Problem:** C5 — 10pt ist für A4-Print zu klein
- **Ebene:** Template-CSS (`pdf_template_v7.html`)
- **Änderung:** `body { font-size: 10pt }` → `11pt`, `.section-body { font-size: 10pt }` → `11pt`
- **Risiko:** MITTEL — Alle Seiteninhalte werden ~10% größer → mögliche Umbruch-Verschiebungen
- **Inhaltsverlust:** Nein — Text wird nur größer
- **Prüfung:** PDF muss nach Änderung visuell auf Umbrüche und Überlauf geprüft werden

#### M6: orphan/widow auf KPA-Niveau senken (R1) [PRIO: MITTEL]
- **Problem:** C6 — 5/5 zu aggressiv, erzeugt mehr Leerraum
- **Ebene:** Template-CSS (`pdf_template_v7.html`)
- **Änderung:** `.section-body p, .section-body li { orphans: 5; widows: 5 }` → `orphans: 3; widows: 3`
- **Risiko:** GERING — KPA beweist, dass 3/3 funktioniert
- **Inhaltsverlust:** Nein — nur Umbruch-Verhalten ändert sich

---

## I. Phase 8 — Prüfbare Umsetzungsempfehlungen

### I.1 Konkrete Änderungen pro Maßnahme

#### M1 — Doppelten Page-Break entfernen

**Datei:** `services/sofort_start_generator.py`
- **Z.1888:** `<div style="page-break-before: always;"></div>` → entfernen (Zeile löschen)
- **Z.2137:** `<div style="page-break-before: always;"></div>` → entfernen (Zeile löschen)

**Prüfung:** R1-PDF generieren → Challenge-Section darf nur EINEN Seitenumbruch vor sich haben, kein leerer Seiten-Artefakt.

#### M2 — break-inside:avoid von großen Containern

**Datei:** `templates/pdf_template_v7.html`
- **Z.887:** `.scenarios-section { break-inside: avoid; }` → `.scenarios-section { break-inside: auto; }`
- **Z.890:** `.business-case-engine-v2 { break-inside: avoid; }` → `.business-case-engine-v2 { break-inside: auto; }`

**Datei:** `services/business_case_engine_v2.py`
- **Z.2240:** `page-break-inside:avoid;break-inside:avoid;` aus dem Inline-Style der `.scenarios-section` entfernen
- **Z.2242:** `page-break-inside:avoid;break-inside:avoid;` aus dem Inline-Style des flex-Containers entfernen

**Prüfung:** Business-Case-Seite im PDF prüfen — Szenarien-Karten müssen weiterhin sichtbar und vollständig sein, dürfen jetzt aber zwischen Karten umbrechen.

#### M3 — Funding aus forced-break-Liste

**Datei:** `templates/pdf_template_v7.html`
- **Z.124-135:** `#funding-section,` aus der ID-Liste entfernen

**Prüfung:** AI-Act-Seite im PDF prüfen — Förderprogramme-Banner soll direkt nach AI-Act-Content folgen, kein 70%-Leerraum.

#### M4 — {% if %}-Guard um prompts-section

**Datei:** `templates/pdf_template_v7.html`
- **Z.1616:** `{% if PROMPT_VORLAGEN_HTML %}` vor der Section einfügen
- **Z.1628:** `{% endif %}` nach der Section einfügen

**Prüfung:** R1-PDF generieren → "Copy-Paste Prompts"-Section mit leerem Body darf NICHT mehr erscheinen. Die 4 Prompts im Sofort-Start müssen weiterhin vollständig sein.

#### M5 — Fließtext 11pt

**Datei:** `templates/pdf_template_v7.html`
- **Z.82:** `body { font-size: 10pt }` → `font-size: 11pt`
- **Z.264:** `.section-body { font-size: 10pt }` → `font-size: 11pt`

**Prüfung:** Visueller Vergleich — Text muss lesbar größer sein, kein Content darf abgeschnitten werden.

#### M6 — orphan/widow senken

**Datei:** `templates/pdf_template_v7.html`
- **Z.269:** `.section-body p, .section-body li { orphans: 5; widows: 5 }` → `orphans: 3; widows: 3`

**Prüfung:** Seitenumbrüche im Fließtext-Bereich prüfen — weniger Leerraum am Seitenende erwartet.

---

## J. Quick Wins (hohe Wirkung, geringes Risiko)

| # | Maßnahme | Aufwand | Risiko | Effekt |
|---|----------|---------|--------|--------|
| **QW1** | M1: Doppelten Page-Break in Challenge entfernen | 2 Zeilen | Gering | Eliminiert leere Seite vor Challenge |
| **QW2** | M4: `{% if %}` Guard um prompts-section | 2 Zeilen | Gering | Eliminiert leere Section im PDF |
| **QW3** | M3: `#funding-section` aus forced-break-Liste | 1 Zeile | Gering | Eliminiert 70% Leerraum nach AI Act |
| **QW4** | M6: orphan/widow 5/5 → 3/3 | 1 Zeile | Gering | Weniger aggressive Umbrüche |
| **QW5** | M2 (CSS-Teil): `.scenarios-section` + `.business-case-engine-v2` → `break-inside:auto` | 2 Zeilen | Gering | Halbleere Business-Case-Seite eliminiert |
| **QW6** | M2 (Generator-Teil): Inline-Styles in business_case_engine_v2.py entfernen | 2 Zeilen | Gering | Voraussetzung für QW5-Wirkung |
| **QW7** | M5: body font-size 10pt → 11pt | 2 Zeilen | Mittel | Bessere Lesbarkeit, konsistenter mit Strategy |

**Empfohlene Reihenfolge:** QW1 → QW2 → QW3 → QW4 → QW5+QW6 → QW7

---

## K. Schutzregeln für sichere Änderungen

### K.1 Inhalte die NICHT verloren gehen dürfen

- Alle 4 Copy-Paste Prompts + Lern-Prompt in SOFORT_START_HTML
- 30-Tage-Challenge Tagesaufgaben (30 Einträge)
- Erfolgs-Tracking Box mit 4-Wochen-Grid
- Tipps-Box (6 Tipps)
- 3 ROI-Szenarien (konservativ/realistisch/optimistisch) mit allen KPIs
- Business-Case-Detail-Tabelle
- Vendor-Audit-Karten mit RED/GREEN Badges
- AI-Act Pflichten-Matrix + Compliance-Lücken + Nächste Schritte
- Förderprogramme-Tabelle + Funding-Path-Karten
- Alle 8+1 Strategy-Sections + Executive Summary
- Alle 5 KPA-Sections + Cover-KPIs

### K.2 Mapping-sensible Stellen

- `PROMPT_VORLAGEN_HTML` → wird nie gesetzt. Wenn diese Variable künftig populiert wird, muss die `{% if %}` Guard entfernt werden.
- `section_s_moat` → conditional in Strategy-Template. Wenn LLM-Generierung fehlschlägt, verschwindet Kapitel 9 stillschweigend.
- `ROADMAP_90D_DECISION_HTML` → W3-Thin-Hider kann diese Section bei <50 Wörtern löschen.
- Jede `_HTML` Section < 50 Zeichen wird von FIX-R5-6 gelöscht.

### K.3 Änderungen die nur systemweit erfolgen dürfen

- Font-Size-Änderungen → in allen drei Templates gleichzeitig, um Konsistenz zu wahren
- break-Regel-Architektur → Änderungen am R1-Template NICHT auf KPA übertragen (KPA funktioniert!)
- Sanitizer-Logik → Änderungen an report_healer.py betreffen nur R1, Änderungen an pipeline_sanitizers.py betreffen alle

### K.4 Zwingende Regressionstests

Nach jeder Änderung:
1. R1-PDF generieren und visuell auf halbleere Seiten prüfen
2. Alle Sections auf Vollständigkeit prüfen (kein fehlender Content)
3. Challenge-Grid (7-Spalten) visuell prüfen
4. ROI-Szenarien-Karten visuell prüfen (3 Karten nebeneinander)
5. Vendor-Karten mit Badges prüfen
6. Score-Donut auf Cover prüfen
7. KPA-PDF generieren und sicherstellen, dass Seitenumbrüche UNVERÄNDERT sind
8. Strategy-PDF generieren und auf neue Artefakte prüfen

---

## L. Abnahme- und Prüfkriterien

Das System gilt als verbessert, wenn:

- [ ] `PROMPT_VORLAGEN_HTML`-Section rendert NICHT mehr leer im PDF (Guard aktiv)
- [ ] Keine doppelten Page-Breaks in der Challenge-Section
- [ ] Business-Case-Seite hat keinen >40% Leerraum
- [ ] AI-Act-Seite hat keinen >40% Leerraum vor Förderprogrammen
- [ ] Fließtext-Schrift in R1 mindestens 11pt
- [ ] Alle 4 Prompts + Lern-Prompt vollständig sichtbar im PDF
- [ ] 30-Tage-Challenge vollständig (30 Tage, Tracking, Tipps)
- [ ] ROI-Szenarien vollständig (3 Karten mit allen KPIs)
- [ ] KPA-Seitenumbrüche UNVERÄNDERT gut
- [ ] Keine neuen Layout-Artefakte in R1, Strategy oder KPA
- [ ] Kein Inhaltsverlust gegenüber dem aktuellen Stand

---

*Ende des 8-Phasen-Audits — Report-ID: AUDIT-20260415-001*
