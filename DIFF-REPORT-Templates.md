# DIFF-REPORT: PDF Templates DE vs EN

**Analyse-Datum:** 2026-01-06
**Projekt:** api-ki-backend-neu
**Branch:** claude/analyze-i18n-setup-THKsk

---

## STATISTIK

| Metrik | DE Template | EN Template | Differenz |
|--------|-------------|-------------|-----------|
| **Zeilen** | 7.220 | 3.499 | **3.721 (51,5% fehlt)** |
| **Dateigröße** | 264 KB | 145 KB | 119 KB (45% kleiner) |
| **Version** | v5.4.3 + CI-DESIGN v2.0 | PLATIN++ v5.2 | ~2 Major Versions |
| **CSS-Classes** | 105 | 126 | +21 in EN (aber andere!) |
| **Platzhalter** | 160 | 111 | **49 fehlen in EN** |

---

## VERSION-DETAILS

### DE-Template (pdf_template.html)
```
Template v5.4.3 - 2026-01-01 - Pages 2,3,4 redesign active
CI-DESIGN v2.0 - Premium Report Template
PHASE 3: LAYOUT & STRUKTUR
PHASE 4: CONTENT-KOMPRIMIERUNG
```

### EN-Template (pdf_template_en.html)
```
PLATIN++ V5.2 PDF TEMPLATE (EN)
Sprint G – Visual Polish (Light Mode Only)
```

**Delta:** DE hat CI-DESIGN v2.0 mit Phase 3/4 Improvements, EN ist auf Sprint G (älter).

---

## KRITISCHE FEATURE-GAPS

### Fehlende visuelle Komponenten in EN

| Feature | DE Count | EN Count | Status |
|---------|----------|----------|--------|
| `hero-score-ring` (SVG Score Circle) | 14 | 0 | **FEHLT** |
| `dimension-card-modern` | 17 | 0 | **FEHLT** |
| `dimension-bar` (Progress Bars) | 14 | 0 | **FEHLT** |
| `roadmap-timeline-modern` | 21 | 0 | **FEHLT** |
| `roi-formula` | 3 | 0 | **FEHLT** |
| `appendix` (Appendix Sections) | 22 | 0 | **FEHLT** |
| `callout-modern` | 6 | 0 | **FEHLT** |
| `top3-measures-enhanced` | 1 | 0 | **FEHLT** |

---

## FEHLENDE CSS-KLASSEN IN EN

Die folgenden 29 CSS-Klassen existieren nur in DE:

```
active
appendix-intro
appendix-section
appendix-subsection
callout-content
callout-icon
callout-info
callout-modern
callout-text
callout-title
dimension-bar
dimension-bar-fill
dimension-card-modern
dimension-label
dimension-score
dimensions-grid-modern
hero-score-ring
phase
phase-content
phase-duration
phase-header
phase-marker
phase-title
roadmap-timeline-modern
roi-formula
roi-interpretation-box
score-content
score-number
top3-measures-enhanced
```

---

## FEHLENDE PLATZHALTER IN EN (49 Stück)

### Dimension Score Platzhalter (12)
```
{{ bef_color }}
{{ bef_level }}
{{ bef_score }}
{{ gov_color }}
{{ gov_level }}
{{ gov_score }}
{{ sec_color }}
{{ sec_level }}
{{ sec_score }}
{{ wert_color }}
{{ wert_level }}
{{ wert_score }}
```

### Content Section Platzhalter (6)
```
{{BUSINESS_CASE_HTML}}
{{FOERDERPOTENZIAL_HTML}}
{{GAMECHANGER_HTML}}
{{RECOMMENDATIONS_HTML}}
{{RISKS_HTML}}
{{ROADMAP_HTML}}
```

### UI Label Platzhalter (~31)
```
{{ ui("appendix_intro", ...) }}
{{ ui("appendix_subtitle", ...) }}
{{ ui("appendix_title", ...) }}
{{ ui("company_label_colon") }}
{{ ui("deep_dive_for") }}
{{ ui("exec_continue", ...) }}
{{ ui("exec_decision_title", ...) }}
{{ ui("feedback_cta") }}
{{ ui("gamechanger_kicker", ...) }}
{{ ui("gamechanger_title", ...) }}
{{ ui("industry_benchmark_kicker") }}
{{ ui("industry_benchmark_title") }}
{{ ui("industry_funding_sub") }}
{{ ui("industry_funding_title") }}
{{ ui("industry_optimized") }}
{{ ui("industry_specific") }}
{{ ui("industry_tools_sub") }}
{{ ui("industry_tools_title") }}
{{ ui("ki_stack_pill", ...) }}
{{ ui("ki_stack_title", ...) }}
{{ ui("missing_info") }}
{{ ui("recommendations") }}
{{ ui("roadmap_kicker", ...) }}
{{ ui("roadmap_title", ...) }}
{{ ui("toc_group_decision", ...) }}
{{ ui("toc_group_economics", ...) }}
{{ ui("toc_group_implementation", ...) }}
{{ ui("toc_item_*", ...) }} (6 items)
{{ ui("toc_note", ...) }}
{{ ui("toc_title", ...) }}
{{ ui("top3_title", ...) }}
```

---

## SEITEN-STRUKTUR VERGLEICH

### PAGE 1: Executive Orientation

| Komponente | DE | EN | Status |
|------------|----|----|--------|
| Header Layout | Centered Hero | Traditional Header | **UNTERSCHIEDLICH** |
| Score Display | Hero Score Ring (SVG) | Score Badge (simple) | **DE erweitert** |
| Dimension Scores | 4 Cards mit Progress Bars | 4 Text-Items | **DE erweitert** |
| 3 KPI Row | Mit Inline Styles | CSS-Classes | Äquivalent |
| Trust Badges | Vorhanden | Vorhanden | OK |

### PAGE 2: Executive Decision

| Komponente | DE | EN | Status |
|------------|----|----|--------|
| Header | Mit ui() Labels | Hardcoded "Decision & Focus" | Äquivalent |
| Final Check | Vorhanden | Vorhanden | OK |
| Top 3 Actions | TOP_3_MASSNAHMEN_HTML | TOP_3_MASSNAHMEN_HTML | OK |
| Continue Text | Mit ui() | Hardcoded EN | Äquivalent |

### PAGE 3: Executive TOC

| Komponente | DE | EN | Status |
|------------|----|----|--------|
| TOC Groups | Mit ui() Labels | Hardcoded EN | Äquivalent |
| Struktur | Identisch | Identisch | OK |

### PAGE 4+: Detail Sections (HAUPTUNTERSCHIED!)

| Section | DE (Zeile) | EN | Status |
|---------|------------|-----|--------|
| **Quick Wins Enhanced** | ~6149+ | **FEHLT** | **KRITISCH** |
| **Roadmap Timeline Modern** | 6560-6638 | **FEHLT** | **KRITISCH** |
| **Business Case Section** | 6640-6655 | **FEHLT** | **KRITISCH** |
| **Risks Section** | 6657-6659 | **FEHLT** | **KRITISCH** |
| **Gamechanger Section** | 6660-6662 | **FEHLT** | **KRITISCH** |
| **Recommendations Section** | 6663-6665 | **FEHLT** | **KRITISCH** |
| **Funding Trust Block** | 6666-6706 | Vorhanden | OK |
| **Förderpotenzial Section** | 6707-6709 | **FEHLT** | **KRITISCH** |
| **Funding × Branch Alignment** | 6710-6728 | **FEHLT** | P1 |
| **Tools × Funding Alignment** | 6729-6747 | **FEHLT** | P1 |
| **Starter Kit** | 6748-6765 | **FEHLT** | P2 |
| **Tools × Branch Alignment** | 6766-6784 | **FEHLT** | P1 |
| **Monetarisierung Section** | 6785-6799+ | Vorhanden (3077+) | Äquivalent |
| **ROI Tracking** | ~6800+ | Vorhanden (3129+) | Äquivalent |
| **AI Mini Policy** | ~6850+ | Vorhanden | Äquivalent |
| **Kickoff Template** | ~6900+ | Vorhanden | Äquivalent |
| **Prompt Framework** | ~6950+ | Vorhanden | Äquivalent |

### APPENDIX SECTIONS (Nur DE!)

| Section | DE Zeile | Status |
|---------|----------|--------|
| Appendix Intro | ~7000+ | **NUR DE** |
| Appendix Detail Sections | ~7050+ | **NUR DE** |
| Appendix Subsections | ~7100+ | **NUR DE** |

---

## KRITISCHE FINDINGS

### P0 - Sofort beheben (Kernfunktionalität)

1. **Fehlende Content Section Platzhalter**
   - `{{BUSINESS_CASE_HTML}}` fehlt komplett
   - `{{RISKS_HTML}}` fehlt komplett
   - `{{GAMECHANGER_HTML}}` fehlt komplett
   - `{{RECOMMENDATIONS_HTML}}` fehlt komplett
   - `{{ROADMAP_HTML}}` fehlt komplett
   - `{{FOERDERPOTENZIAL_HTML}}` fehlt komplett
   - **Impact:** EN-Report zeigt keine Hauptinhalte!
   - **Fix:** Sections aus DE übernehmen mit EN-Labels

2. **Hero Score Ring fehlt**
   - SVG-basierte Score-Visualisierung nicht vorhanden
   - **Impact:** Page 1 visuell schwächer
   - **Fix:** SVG + CSS aus DE kopieren

3. **Dimension Score Cards fehlen**
   - Moderne Progress-Bar Darstellung nicht vorhanden
   - **Impact:** Dimension Scores weniger aussagekräftig
   - **Fix:** Cards + CSS aus DE kopieren

### P1 - Kurzfristig (Enhanced Features)

4. **Roadmap Timeline Modern fehlt**
   - 3-Phasen Timeline mit Cards
   - **Impact:** Roadmap-Darstellung basic
   - **Fix:** Timeline-Komponente aus DE

5. **Industry Alignment Sections fehlen**
   - Funding × Branch, Tools × Branch, Tools × Funding
   - **Impact:** Keine branchenspezifischen Insights
   - **Fix:** Conditional Sections aus DE

6. **Appendix Struktur fehlt**
   - Für Solo-Reports werden Details in Appendix verschoben
   - **Impact:** Solo-Reports weniger kompakt
   - **Fix:** Appendix-Logik aus DE

### P2 - Mittelfristig (Polish)

7. **Callout Modern Styles fehlen**
   - Moderne Info-Boxen
   - **Fix:** CSS aus DE

8. **ROI Formula Box fehlt**
   - Visualisierung der ROI-Berechnung
   - **Fix:** Komponente aus DE

---

## SECTION-MAPPING (DE → EN)

| Nr | DE Section | EN Section | Status | Action |
|----|------------|------------|--------|--------|
| 1 | Page 1 Hero | Page 1 Header | ⚠️ Unterschiedlich | Upgrade EN |
| 2 | Page 2 Decision | Page 2 Decision | ✅ Äquivalent | Sync Labels |
| 3 | Page 3 TOC | Page 3 TOC | ✅ Äquivalent | Sync Labels |
| 4 | Quick Wins Enhanced | - | ❌ Fehlt | Add Section |
| 5 | Roadmap Timeline | - | ❌ Fehlt | Add Section |
| 6 | Business Case | - | ❌ Fehlt | Add Section |
| 7 | Risks | - | ❌ Fehlt | Add Section |
| 8 | Gamechanger | - | ❌ Fehlt | Add Section |
| 9 | Recommendations | - | ❌ Fehlt | Add Section |
| 10 | Funding Trust Block | Funding Trust Block | ✅ OK | - |
| 11 | Förderpotenzial | - | ❌ Fehlt | Add Section |
| 12 | Funding × Branch | - | ❌ Fehlt | Add Section |
| 13 | Tools × Funding | - | ❌ Fehlt | Add Section |
| 14 | Starter Kit | - | ❌ Fehlt | Add Section |
| 15 | Tools × Branch | - | ❌ Fehlt | Add Section |
| 16 | Monetarisierung | Monetization | ✅ OK | - |
| 17 | ROI Tracking | ROI Tracking | ✅ OK | - |
| 18 | AI Mini Policy | AI Mini Policy | ✅ OK | - |
| 19 | Appendix | - | ❌ Fehlt | Add Struktur |
| 20 | Impressum | Legal Notice | ✅ OK | - |
| 21 | Feedback | Feedback | ✅ OK | - |
| 22 | GDPR Disclaimer | GDPR Disclaimer | ✅ OK | - |

**Legende:**
- ✅ OK: Section identisch oder äquivalent
- ⚠️ Unterschiedlich: Section existiert aber anders strukturiert
- ❌ Fehlt: Section nicht vorhanden

---

## IMPLEMENTIERUNGS-EMPFEHLUNG

### Phase 6.2a: Critical Sections (P0) - ~3-4h

1. **Content Section Container hinzufügen**
   ```html
   <!-- BUSINESS CASE DETAIL -->
   <section class="section chapter">
       {{BUSINESS_CASE_HTML}}
   </section>
   <!-- RISKS, GAMECHANGER, RECOMMENDATIONS -->
   <section class="chapter">{{RISKS_HTML}}</section>
   <section class="chapter">{{GAMECHANGER_HTML}}</section>
   <section class="chapter">{{RECOMMENDATIONS_HTML}}</section>
   <section class="chapter">{{FOERDERPOTENZIAL_HTML}}</section>
   ```

2. **Hero Score Ring CSS hinzufügen** (~200 Zeilen CSS)
3. **Dimension Cards CSS hinzufügen** (~150 Zeilen CSS)

### Phase 6.2b: Enhanced Features (P1) - ~2-3h

4. **Roadmap Timeline Modern** (~100 Zeilen HTML + 200 CSS)
5. **Industry Alignment Sections** (~100 Zeilen, conditional)
6. **Appendix Struktur** (~150 Zeilen)

### Phase 6.2c: Polish (P2) - ~1-2h

7. **Callout Styles** (~50 Zeilen CSS)
8. **ROI Formula Box** (~30 Zeilen)
9. **Cleanup & Sync** (Labels, ui() calls)

---

## ZEILEN-BUDGET-SCHÄTZUNG

| Bereich | Zu addierende Zeilen | Priorität |
|---------|---------------------|-----------|
| CSS (Hero, Dimension, Modern) | ~600 | P0 |
| Content Sections (HTML) | ~500 | P0 |
| Roadmap Timeline | ~300 | P1 |
| Industry Alignments | ~200 | P1 |
| Appendix Struktur | ~200 | P1 |
| Polish & Sync | ~100 | P2 |
| **TOTAL** | **~1.900** | - |

**Erwartete EN-Template Größe nach Sync:** ~5.400 Zeilen (aktuell 3.499)

---

## NÄCHSTE SCHRITTE

1. [ ] **Review dieses Reports mit Wolf**
2. [ ] **Priorisierung bestätigen** (P0 zuerst?)
3. [ ] **Phase 6.2a starten** - Content Sections
4. [ ] **CSS-Blocks aus DE extrahieren** und anpassen
5. [ ] **Testing mit EN-Report** nach jedem Schritt
6. [ ] **ui() Labels sicherstellen** in ui_labels.json

---

**Report erstellt:** 2026-01-06
**Analysiert von:** Claude Code (Opus 4.5)
**Basis für:** Phase 6.2 Template-Sync Implementation
**Geschätzte Sync-Zeit:** 6-9 Stunden total
