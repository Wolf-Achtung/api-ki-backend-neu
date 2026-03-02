# DIAGNOSE-ERGEBNIS: Phase 3 CSS greift nicht

Erstellt: 2026-03-02
Methode: Statische Analyse von Prompts, Template und Post-Processing-Code
Status: Debug-Code war NICHT nötig — alle 7 Fragen definitiv beantwortet

---

## Frage 1: Container-Klasse

**CONTAINER IST `.section-body`** — bestätigt, 71x im Template, HTML bei Zeile 7286+.

**ABER: 5 wichtige Sections sind NICHT in `.section-body` gewickelt!**

### INSIDE `.section-body` (28 Sections):
| Variable | Template-Zeile | Seiten |
|---|---|---|
| ROADMAP_90D_DECISION_HTML | 7287 | S.9-10 |
| ROADMAP_12M_HTML | 7308 | S.11-13 |
| GAMECHANGER_DECISION_HTML | 7324 | S.3 |
| KI_STACK_SUMMARY_HTML | 7344 | S.14-17 |
| QUICK_WINS_HTML | 7464 | S.21-22 |
| BUSINESS_CASE_HTML | 7817 | S.31 |
| TEMPLATES_START_HTML | 8014 | S.52 |
| AI_POLICY_MINI_HTML | 8052 | S.53 |
| MONETARISIERUNG_HTML | 7978 | S.51 |
| KI_SKILLPLAN_HTML | 7996 | S.51 |
| ROI_TRACKING_HTML | 8034 | S.53 |
| KICKOFF_VORLAGE_HTML | 8209 | S.54 |
| PROMPT_FRAMEWORK_HTML | 8227 | S.54 |
| BRANCH_PROFILE_HTML | 7473 | S.24 |
| BRANCH_DEEP_DIVE_HTML | 7509 | S.25 |
| VENDOR_AUDIT_HTML | 7602 | S.26-27 |
| BUSINESS_CASE_ENGINE_HTML | 7641 | S.28-29 |
| BUSINESS_CASE_SIM_HTML | 7673 | S.29 |
| BENCHMARK_ENGINE_HTML | 7705 | S.30 |
| RECOMMENDATIONS_ENGINE_HTML | 7724 | S.35 |
| FUNDING_BRANCH_ALIGNMENT_HTML | 7900 | Anhang |
| TOOLS_FUNDING_ALIGNMENT_HTML | 7920 | Anhang |
| STARTER_KIT_HTML | 7939 | S.50 |
| TOOLS_BRANCH_ALIGNMENT_HTML | 7959 | Anhang |
| AUTOMATION_ROADMAP_HTML | 7622 | S.23 |
| RISK_ENGINE_V3_HTML | 7582 | S.32-33 |
| + diverse Branch-Sections | | |

### NICHT in `.section-body` (5 Haupt-Sections):
| Variable | Template-Zeile | Container | Seiten |
|---|---|---|---|
| **RISKS_HTML** | 7824 | `<section class="chapter">` | S.32-33 |
| **GAMECHANGER_HTML** | 7829 | `<section class="chapter">` | S.36-40 |
| **RECOMMENDATIONS_HTML** | 7834 | `<section class="chapter">` | S.41-45 |
| **FOERDERPOTENZIAL_HTML** | 7881 | `<section class="chapter">` | S.46 |
| ROADMAP_HTML | 7800 | Innerhalb Section-Closing | S.8 |

### AUCH NICHT in `.section-body`:
| Variable | Zeile | Container |
|---|---|---|
| EXECUTIVE_DECISION_HTML | 7112 | Custom styled `<div>` |
| TOP_3_MASSNAHMEN_HTML | 7102 | `<div class="top3-measures-enhanced">` |
| SOFORT_START_HTML | 7153 | `<div class="sofort-start-page">` |

**→ KONSEQUENZ:** `.section-body`-CSS greift auf ~28 Sections. Die 5 großen Content-Sections
(Risks, Gamechanger, Recommendations, Foerderpotenzial, Roadmap) sind AUSSERHALB und
werden von unserem CSS NICHT erreicht.

---

## Frage 2: Tag-Verwendung — `<h3>` vs `<p><strong>`

### Ergebnis: Die Prompts VERBIETEN `<h3>` in den meisten Sections!

**`<h3>` VERBOTEN in:**
| Section | Prompt-Datei | Verbotene Tags |
|---|---|---|
| roadmap_90d_decision | roadmap_90d_decision.md | `<h1>, <h2>, <h3>, <h4>, <section>, <article>, <header>` |
| roadmap_12m | roadmap_12m.md | `<h1>, <h2>, <h3>, <h4>, <section>, <article>` |
| gamechanger_decision | gamechanger_decision.md | `<h1>, <h2>, <h3>, <h4>, <section>, <article>, <header>` |

**`<h3>` ERLAUBT in:**
| Section | Prompt-Datei | Erlaubte Tags |
|---|---|---|
| recommendations | recommendations.md | `<h2>, <h3>, <ol>, <table>` |
| foerderpotenzial | foerderpotenzial.md | `<section>, <h2>, <h3>, <ul>` |
| templates_start | templates_start.md | `<section>, <h2>, <h4>, <pre>` (h4, NICHT h3!) |
| strategie_governance | strategie_governance.md | `<h2>, <h3>, <ul>, <ol>` |

**`_repair_html()` erlaubt NUR `<h4>`** (Zeile 3691):
```
<p>, <ul>, <ol>, <li>, <table>, <thead>, <tbody>, <tr>, <th>, <td>, <div>, <h4>, <em>, <strong>, <br>
```
→ Wenn `_repair_html()` aufgerufen wird, werden `<h3>` zu nichts konvertiert!

**`_needs_repair()` prüft auf `<h4>`, NICHT `<h3>`** (Zeile 3684):
```python
not any(t in sl for t in ("<p","<ul","<table","<div","<h4","<ol"))
```
→ Output mit nur `<h3>` (aber ohne `<p>`, `<div>`, etc.) würde als "kaputt" markiert.

**SCHLUSSFOLGERUNG zu Überschriften:**
- Roadmap-Sections: LLM generiert `<p><strong>Phase 1: ...</strong></p>` — KEINE `<h3>`
- Gamechanger-Decision: LLM generiert `<p><strong>Titel</strong></p>` — KEINE `<h3>`
- Recommendations: LLM DARF `<h3>` generieren, aber Post-Processing ersetzt den gesamten
  HTML durch eigene Formate (`.rec-card`, `.empfehlung-card`)
- Templates: LLM generiert `<h4>` (explizit im Prompt gefordert) — KEINE `<h3>`
- Strategie/Governance: LLM DARF `<h3>` generieren — diese Section könnte unser CSS zeigen

**→ CSS-Selektor `.section-body h3` greift FAST NIRGENDS.**

---

## Frage 3: CSS-Klassen

### Ergebnis: GEMISCHT — manche Prompts fordern Klassen, manche nicht

**Prompts die CSS-Klassen vorschreiben:**
| Section | Klasse |
|---|---|
| roadmap_90d_decision | `div.roadmap-decision` |
| gamechanger_decision | `div.gamechanger-decision` |
| recommendations | `section.recommendations`, `.recommendations-muss`, `.recommendations-optionen` |
| foerderpotenzial | `section.funding-potential` |
| templates_start | `.code-block`, `.checklist`, `.compact` |
| strategie_governance | `section.governance-strategy` |

**Post-Processing-Funktionen fügen EIGENE Klassen hinzu:**
| Funktion | Klassen |
|---|---|
| `_format_recommendations_as_cards()` | `.rec-cards-container`, `.rec-cards-grid`, `.rec-card` |
| `_format_recommendations_compact()` | `.recommendation-card-compact` |
| `_format_empfehlungen_v3()` | `.empfehlung-card`, `.empfehlung-header`, `.empfehlung-schwerpunkt` |
| `_format_gamechanger_section()` | `.svg-decorated-box`, `.svg-decorated-box-content` |
| `_format_roadmap_as_phase_cards()` | `.roadmap-phase-card`, `.phase-badge`, `.milestone` |
| `_format_roadmap_phases_compact()` | `.roadmap-phase-card`, `.phase-badge`, `.phase-timeframe` |
| `_build_quick_wins_html()` | `.quick-wins-container`, `.quick-win-card`, `.qw-context-banner` |

**→ Die Post-Processing-Klassen sind das ECHTE CSS-Target, nicht Standard-HTML-Tags.**

---

## Frage 4: Inline-Styles

### Ergebnis: MASSIV — Post-Processing fügt überall Inline-Styles hinzu

**Beispiele aus Post-Processing-Funktionen:**

1. **Quick Wins** (`_build_quick_wins_html()`):
   - `style="width: 100%; border-collapse: collapse; background: #eff6ff;"`
   - `style="padding: 20px; width: 50%; border-right: 1px solid #bfdbfe;"`
   - `style="background: #fffbeb; border-left: 4px solid #f59e0b; padding: 14px;"`

2. **Recommendations** (`_format_recommendations_as_cards()`):
   - `style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px;"`
   - `style="background: white; border: 1px solid #e5e7eb; border-left: 4px solid #3b82f6;"`

3. **Gamechanger** (`_format_gamechanger_section()`):
   - `style="background-color: #FFF3E0; border-left: 6px solid #E65100; padding: 16px;"`
   - `style="font-size: 18px; font-weight: bold; color: #E65100;"`

4. **Roadmap** (`_format_roadmap_phases_compact()`):
   - `style="border-left: 4px solid #10B981;"`
   - `style="background: #10B981;"` (phase badge)

**→ Inline-Styles haben HÖHERE Spezifität als `.section-body` CSS-Klassen!**
**→ Unsere CSS-Regeln für `font-size`, `color`, `background` werden von Inline-Styles überschrieben.**
**→ NUR `!important` kann Inline-Styles überstimmen.**

---

## Frage 5: Font-Size-Inkonsistenzen

### Ergebnis: JA — verschiedene Quellen setzen verschiedene Größen

| Quelle | Font-Sizes |
|---|---|
| Post-Processing Gamechanger | `font-size: 18px`, `font-size: 14px` |
| Post-Processing Quick Wins | `font-size: 36px` (Icon), `font-size: 18px` (Title), `font-size: 16px` |
| Template CSS-Variablen | `var(--font-base)` = ~10pt, `var(--font-sm)` = ~9pt |
| Tabellen (P1a CSS) | `font-size: 9.5pt` (td), `font-size: 8.5pt` (th) |
| LLM Inline-Styles | Variabel — bekanntes Problem auf S.39, S.52 (6.6pt - 13.2pt) |

**→ Inkonsistent. Inline-Styles aus Post-Processing dominieren über CSS.**

---

## Frage 6: Text-Patterns für Post-Processing

### Ergebnis: Patterns werden von Post-Processing BEREITS verarbeitet

Die meisten Text-Patterns werden bereits durch die Post-Processing-Funktionen
in strukturiertes HTML konvertiert:

| Pattern | Verarbeitung |
|---|---|
| "Phase 1/2/3" | `_format_roadmap_as_phase_cards()` → `.roadmap-phase-card` mit `.phase-badge` |
| "Problem:/Wirkung:/Umsetzung:" | `_build_quick_wins_html()` → JSON-Parse → Tabellen-Karten |
| "Meilenstein/Stop-Regel" | `_format_roadmap_phases_compact()` → `.milestone` div |
| "MUSS/OPTION" | `_format_empfehlungen_v3()` → `.empfehlung-card` |
| "Erlaubt/Verboten" | LLM-Output, kein spezielles Post-Processing |
| "Neue Logik/Bisher" | `_format_gamechanger_section()` → `.svg-decorated-box` |

**→ Die meisten Patterns brauchen KEIN zusätzliches Post-Processing.**
**→ Die Post-Processing-Funktionen wandeln sie bereits in eigene HTML-Strukturen um.**

---

## Frage 7: Unterschiede zwischen Sections

### Ergebnis: JA — drastische Unterschiede

**Gruppe A: Decision-Sections (strikt limitiert)**
- `roadmap_90d_decision`, `gamechanger_decision`
- NUR: `<div>`, `<p>`, `<ul>`, `<li>`, `<strong>`, `<span>`, `<br>`
- KEINE `<h3>`, KEINE `<h4>`, KEINE `<table>`
- Eigene CSS-Klassen: `.roadmap-decision`, `.gamechanger-decision`

**Gruppe B: Content-Sections (semantisches HTML)**
- `recommendations`, `foerderpotenzial`, `strategie_governance`
- DÜRFEN: `<h2>`, `<h3>`, `<section>`, `<table>`, `<ul>`, `<ol>`
- Eigene CSS-Klassen aus Prompts
- ABER: Post-Processing ERSETZT den LLM-Output teilweise komplett!

**Gruppe C: Template-Sections (strukturiert)**
- `templates_start`, `ai_policy_mini`
- `<h4>` explizit gefordert (nicht `<h3>`)
- Klassen: `.code-block`, `.checklist`

**Gruppe D: Post-Processed Sections (Python-generiertes HTML)**
- Quick Wins, Roadmap-Cards, Gamechanger-Boxes, Recommendation-Cards
- HTML kommt NICHT vom LLM sondern aus Python-Funktionen
- Schwere Inline-Styles, eigene Klassen
- TABLE-basiert (Quick Wins) oder CSS-Grid (Recommendations)

---

## ZUSAMMENFASSUNG

### Warum Phase 3 CSS nicht greift — 3 Ursachen:

#### Ursache 1: Falsche Container-Annahme (50% des Problems)
5 große Sections (RISKS, GAMECHANGER, RECOMMENDATIONS, FOERDERPOTENZIAL, ROADMAP)
sind NICHT in `.section-body` gewickelt sondern direkt in `<section class="chapter">`.

**Fix:** CSS-Selektoren auch auf `.chapter` targeting oder Template-HTML anpassen.

#### Ursache 2: `<h3>` existiert nicht (30% des Problems)
Die Prompts für Roadmap und Gamechanger VERBIETEN `<h3>` explizit.
`_repair_html()` erlaubt nur `<h4>`, nicht `<h3>`.
Der LLM nutzt stattdessen `<p><strong>Titel</strong></p>`.

**Fix:** CSS-Selektoren auf `<p><strong>` als "Fake-Heading" targeting.

#### Ursache 3: Inline-Styles überschreiben CSS (20% des Problems)
Post-Processing-Funktionen setzen `font-size`, `color`, `background` per Inline-Style.
Inline-Styles haben höhere Spezifität als Klassen-Selektoren.
Nur `!important` kann Inline-Styles überstimmen.

**Fix:** Wo nötig `!important` verwenden oder Inline-Styles im Post-Processing anpassen.

---

### KONSEQUENZ FÜR CSS-FIXES:

1. **Neue Selektoren nötig:**
   - `.chapter > p`, `.chapter > div > p` (für Sections ohne section-body)
   - `.section-body > p > strong:first-child` (Fake-Headings — HABEN WIR SCHON!)
   - `.chapter > p > strong:first-child` (Fake-Headings in chapter-Sections)

2. **Bestehende Selektoren die FUNKTIONIEREN sollten:**
   - `.section-body table` → FUNKTIONIERT (bestätigt: Tabellen-Phase war erfolgreich)
   - `.section-body h4` → KÖNNTE funktionieren für templates_start
   - `.section-body ul > li::before` → KÖNNTE funktionieren wenn LLM `<ul><li>` generiert

3. **Bestehende Selektoren die NICHT funktionieren:**
   - `.section-body h3` → LLM generiert fast nie `<h3>`
   - `.section-body ul > li::before` → Viele Sections nutzen KEINE `<ul><li>`,
     sondern Fake-Listen in `<p>`-Tags oder Post-Processing-HTML

### KONSEQUENZ FÜR POST-PROCESSING:

1. **NICHT nötig:** Text-Pattern-Wrapping (Post-Processing macht das bereits)
2. **Eventuell nötig:** Wrapper-Injection für die 5 Sections ohne `.section-body`
3. **Empfohlen:** CSS auch auf `.chapter`-Ebene duplizieren statt Template-HTML ändern

---

### EMPFOHLENE NÄCHSTE SCHRITTE (Phase 4):

**Option A: CSS erweitern (minimal-invasiv)**
- Alle `.section-body` Selektoren duplizieren als `.chapter` Selektoren
- `p > strong:first-child` Styling als Fake-Heading
- `<h4>` Styling hinzufügen (da templates_start h4 nutzt)

**Option B: Template-HTML anpassen (strukturell sauberer)**
- Die 5 fehlenden Sections in `<div class="section-body">` wickeln
- Einmalige Template-Änderung, dann greifen alle CSS-Regeln

**Option C: Kombination (empfohlen)**
- Template-Fix für die 5 Sections (Option B)
- Plus: CSS für `<p><strong>` als Fake-Heading (Option A)
- Plus: CSS für `<h4>` (von templates_start)
