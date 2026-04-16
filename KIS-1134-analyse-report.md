# KIS-1134 Analyse-Report — R1 Pagebreak, Förderdaten, Erfolgs-Tracking

**Datum:** 2026-04-16  
**Basis:** Testrun KIS-1133 (Briefing 1016), Pipeline G22=A/100, PLATIN+++  
**Status:** Analyse abgeschlossen — wartet auf Abstimmung mit Wolf für Fix-Briefing

---

## Abschnitt A — Pagebreak-Analyse

### A.1 Bestandsaufnahme: Alle break-Regeln in `pdf_template_v7.html`

#### Forced Page Breaks (break-before: page)

| Selektor | Zeile | Kommentar |
|----------|-------|-----------|
| `#mgmt-summary` | 127 | Major chapter |
| `#sofort-start` | 127 | Major chapter |
| `#business-case-compact` | 128 | Major chapter |
| `#challenge-section` | 129 | Major chapter |
| `#risks-compact` | 130 | Major chapter |
| `#outlook-section` | 131 | Major chapter |
| `#gamechanger-section` | 132 | Major chapter |
| `#advisor-note` | 133 | Major chapter |
| `#decision` | 138–139 | KIS-1126/C6: standalone GF-Vorlage |
| `.break-action-to-imprint` | 122 | Appendix-Trenner |
| `.appendix-section` | 906 | Jeder Anhang eigene Seite |
| `.appendix-cover` | 795 | Anhang-Deckblatt |

**Explizit KEIN forced break** (Zeile 141–143):  
`#quick-wins-section`, `#roadmap-90d`, `#tools-section`, `#prompts-section`, `#vendor-section`, `#aiact-compact`, `#funding-section`, `#next-steps`

#### break-inside / break-after Regeln

| Selektor | Regel | Zeile | Herkunft |
|----------|-------|-------|----------|
| `.section` | `break-inside: auto` | 148 | Basis |
| `.section h2/h3/h4` | `break-after: avoid` | 152–153 | KIS-1126/C3 |
| `.section .glance-box` | `break-after: avoid` | 156 | KIS-1126/C3 |
| `.section-body h3 + p/ul/ol/div` | `break-before: avoid` | 159–163 | KIS-1126/C3 |
| `h1, h2, h3, h4` (global) | `break-after: avoid` | 895–896 | Block Protection v7.1.2 |
| `.chapter-banner` | `break-inside: avoid; break-after: avoid` | 277–278 | KIS-1127/C4 |
| `.section-transition` | `break-before: avoid; break-inside: avoid` | 912–913 | Transition-Schutz |
| `.mgmt-card, .decision-card, .funding-card, .kpi-card, .glance-box, .contact-box, .card-nobreak` | `break-inside: avoid` | 876–879 | Block Protection |
| `.tool-card` | `break-inside: avoid; page-break-inside: avoid` | 936–938 | Kleine Karten zusammenhalten |
| `.vendor-card, .scenario-card` | `break-inside: avoid` | 883–884, 951–953 | Kleine Karten |
| `.starter-kit, .starter-kit__tools` | `break-inside: auto` | 927–933 | KIS-1127/C3: Große Container dürfen brechen |
| `.roadmap-phase-card` | `break-inside: auto` | 921–923 | KIS-1127/C3 |
| `.scenarios-section, .business-case-engine-v2` | `break-inside: auto` | 887–891 | M2-FIX |
| `.tip-box` | `page-break-inside: avoid` | 1057 | v7.1 |
| `.warning-box` | `page-break-inside: avoid` | 1079 | v7.1 |

#### Orphans/Widows

| Selektor | Wert | Zeile | Herkunft |
|----------|------|-------|----------|
| `body` | `orphans: 4; widows: 4` | 87–88 | Basis |
| `.section-body p, li` | `orphans: 3; widows: 3` | 269 | M6-FIX (war 5→3) |

---

### A.2 Mapping der 6 Bruchstellen

#### 1.1 — Fallstudie zerrissen (S.6→7)

- **HTML-Container:** `sofort_start_generator.py:3115–3168`, Inline-Div `<!-- FALLSTUDIE -->`, keine CSS-Klasse
- **Teil von:** `SOFORT_START_HTML` → `#sofort-start` (hat `break-before: page`)
- **CSS-Schutz:** KEINER. Der Fallstudie-Container hat weder eine CSS-Klasse noch ein inline `break-inside: avoid`
- **Struktur:** ~54 Zeilen HTML: Header + 2-Spalten-Grid (Unternehmen/ROI) + Ausgangslage + Lösung + 3-Spalten-Ergebnis-Grid + Zitat. Geschätzt ~350px Höhe
- **Diagnose: FEHLENDE REGEL** — Der Container braucht `break-inside: avoid` oder zumindest `class="card-nobreak"`. Die bestehende `.card-nobreak`-Klasse (Zeile 878) wäre passend
- **Caveat:** Bei sehr langen Fallstudien-Texten (branchenabhängig) könnte der Block eine Seite übersteigen. In dem Fall wäre `break-inside: avoid` kontraproduktiv. Empfehlung: `break-inside: avoid` mit Fallback-Test

#### 1.2 — "Quick Wins: Top 3"-Header als Orphan (S.7 Fuß)

- **HTML-Container:** `pdf_template_v7.html:1528–1543`, `<section id="quick-wins-section">`
- **Header-Elemente:** Badge + Kicker + `<h2>Quick Wins: Top 3</h2>` + `<div class="glance-box">`
- **CSS-Schutz:** `h2 { break-after: avoid }` (Zeile 896) + `.glance-box { break-after: avoid }` (Zeile 156). Der `h2` darf also nicht allein am Seitenende stehen
- **Diagnose: INHALTSPROBLEM** — Die Regeln existieren korrekt. Chromium/Puppeteer respektiert `break-after: avoid` aber nur, wenn genug Platz für Header + nächstes Element ist. Wenn der Sofort-Start-Content + Fallstudie die Seite fast füllt, bleibt nur Platz für den Header, nicht aber für die Glance-Box + ersten Quick-Win. Chromium bricht dann trotzdem
- **Empfehlung:** `#quick-wins-section` als Ganzes mit `break-before: page` versehen ODER den gesamten Section-Header (`.section-header` + `.glance-box`) in einen `card-nobreak`-Wrapper packen

#### 1.3 — Quick-Wins-Liste bricht zwischen Punkt 2 und 3 (S.7→8)

- **HTML-Container:** `QUICK_WINS_HTML` (LLM-generiert), injiziert in `<div class="section-body">` (Zeile 1541)
- **CSS-Schutz:** `.section-body p, li { orphans: 3; widows: 3 }` (Zeile 269). Kein `break-inside: avoid` auf dem `<ol>/<ul>`-Container
- **Diagnose: FEHLENDE REGEL** — Die LLM-generierten Quick Wins sind typischerweise eine nummerierte Liste `<ol>` mit 3 Items. Jedes Item kann eigene Sub-Elemente haben (Text + Tip-Box). Es fehlt ein Schutz auf Listenitem-Ebene
- **Empfehlung:** `.section-body ol > li, .section-body ul > li { break-inside: avoid }` hinzufügen. Alternativ: Wenn die Quick-Win-Items zu groß sind (>½ Seite), stattdessen nur `break-before: avoid` auf `li + li`

#### 1.4 — Starter-Kit Tool-Karte zerrissen (S.11→12)

- **HTML-Container:** Zwei Systeme im Einsatz:
  - `gpt_analyze.py:8461–8466`: `<div class="tool-card">` → hat CSS-Schutz (`break-inside: avoid`, Zeile 936–938)
  - `tools_starter_kits.py:780–791`: Inline-Div OHNE CSS-Klasse, kein Break-Schutz
- **Teil von:** `STARTER_KIT_HTML` → `#tools-section .section-body` (Zeile 1613)
- **CSS-Schutz von `.starter-kit`:** `break-inside: auto` (Zeile 927–929) — Container darf brechen
- **Diagnose: FALSCHE REGEL (teilweise)** — Das `tools_starter_kits.py`-Rendering nutzt Inline-Styles statt der CSS-Klasse `.tool-card`. Die CSS-Regel greift nicht. Die Karten aus `gpt_analyze.py` sind geschützt, die aus `tools_starter_kits.py` nicht
- **Empfehlung:** In `tools_starter_kits.py:781` `class="tool-card"` oder `class="card-nobreak"` zum Container-Div hinzufügen. Alternativ: Inline-Style `break-inside: avoid` ergänzen

#### 1.5 — Hinweis-Kasten zerrissen (S.16→17)

- **HTML-Container:** `extra_sections.py:862–866`, `<p class="small muted">` innerhalb `#funding-section`
- **CSS-Schutz:** KEINER. Die Klasse `.small.muted` hat keine break-Regeln. Es ist ein normaler Paragraph
- **Diagnose: FEHLENDE REGEL** — Der Hinweis-Text ist ein einzelner `<p>`-Block. Chromium bricht ihn mitten im Satz. `orphans: 3` auf `.section-body p` (Zeile 269) greift theoretisch, aber der Paragraph hat nur 2–3 Zeilen, daher kann ein Umbruch nach der ersten Zeile entstehen
- **Empfehlung:** Den Hinweis-Absatz in ein `<div class="card-nobreak">` wrappen, oder `page-break-inside: avoid` inline setzen. Alternativ: Die Klasse `.hinweis-box` einführen und in die Block-Protection-Liste (Zeile 876) aufnehmen

#### 1.6 — AI Act Kompakt nur "Risikoklasse: minimal" + 60% Whitespace (S.15)

- **HTML-Container:** `pdf_template_v7.html:1686–1721`, `<section id="aiact-compact">`
- **CSS-Schutz:** Kein forced `break-before: page` (Zeile 143: "flows naturally")
- **Content bei `minimal`-Risikoklasse:** Glance-Box ("Minimale regulatorische Anforderungen") + Risk-Banner (grün, `.risk-banner-low`) + Duty-Matrix mit nur 3 Zeilen (Zeile `ai_act_module.py:349–354`: Dokumentation, Qualitätsprüfung, Transparenz, alle "Empfohlen") + Note ("Best Practices, keine gesetzlichen Pflichten")
- **Kein Content-Gating** aktiv — die Sections werden generiert, nur mit weniger Zeilen
- **Diagnose: INHALTSPROBLEM** — Der vorhergehende Vendor-Audit-Block füllt die Seite bis ~40% Rest. Die AI-Act-Section hat zu wenig Content für `minimal`, füllt nur ~30% einer Seite. Kein erzwungener Pagebreak, aber der natürliche Flow erzeugt das Problem: Vendor-Audit endet, AI Act passt nicht mehr komplett drauf, wird auf neue Seite geschoben (wegen `.glance-box { break-after: avoid }` hält der Header-Block zusammen), füllt dann nur 30–40% der neuen Seite
- **Zusätzlicher Fund:** Der AI-Act-Fallback-Text in `gpt_analyze.py:10676–10679` enthält ebenfalls "Stand: Q1 2025" — separate Issue, gehört zu Abschnitt B
- **Empfehlung:** Zwei Optionen:
  1. **Content-Anreicherung:** Bei `minimal`-Risikoklasse zusätzlichen Kontext ausgeben (z.B. "Was ‚minimal' für Sie bedeutet" Absatz, Best-Practice-Checkliste)
  2. **Layout-Merge:** AI Act + Förderprogramme auf einer Seite zusammenführen (kein Break dazwischen — ist bereits so, M3-FIX hat `#funding-section` break entfernt). Problem ist aber, dass der Vendor-Audit davor zu viel Platz einnimmt

---

### A.3 KIS-1129-Fixes (M1–M6) — Was wurde gemacht?

Commit `305709a` ("8-Phasen Report-System Audit + 5 Seitenumbruch-/Typografie-Fixes"):

| Fix | Beschreibung | Selektor | Zeile | Scope |
|-----|--------------|----------|-------|-------|
| M1 | Duplicate break in Challenge entfernt | Generator-HTML | sofort_start_generator.py | Spezifisch |
| M2 | `break-inside: avoid→auto` für große Container | `.scenarios-section`, `.business-case-engine-v2` | 887–891 | Spezifisch |
| M3 | `#funding-section` aus forced-break-Liste entfernt | `#funding-section` | 125 (Kommentar) | Spezifisch |
| M5 | Font-Size 10pt→11pt | `.section-body`, `body` | 82, 263 | Global |
| M6 | Orphans/Widows 5→3 | `.section-body p, li` | 269 | Global |

Zusätzlich Commit `9c974c3` (C3) und `c21ea1a` (C3):
- Headings mit Content zusammenhalten (`break-after: avoid` auf h2/h3/h4)
- Große Container aufbrechen erlauben (`.starter-kit`, `.roadmap-phase-card`, `.vendor-audit-engine`)

**Alle Regeln gelten entweder GLOBAL (M5, M6, Heading-Regeln) oder für SPEZIFISCHE Klassen.** Inline-gestylte Container ohne Klasse (Fallstudie, Starter-Kit-Karten aus `tools_starter_kits.py`) profitieren nicht von den Fixes.

---

### A.4 Zusammenfassung pro Bruchstelle

| # | Ort | Diagnose | Ursache |
|---|-----|----------|---------|
| 1.1 | Fallstudie S.6→7 | **Fehlende Regel** | Inline-Container ohne CSS-Klasse, kein `break-inside: avoid` |
| 1.2 | Quick-Wins-Header S.7 | **Inhaltsproblem** | Regeln existieren, aber Chromium ignoriert bei Platzmangel |
| 1.3 | Quick-Wins-Liste S.7→8 | **Fehlende Regel** | Kein `break-inside: avoid` auf `<li>`-Ebene |
| 1.4 | Starter-Kit-Karte S.11→12 | **Falsche Regel** | `tools_starter_kits.py` nutzt Inline-Styles statt `.tool-card`-Klasse |
| 1.5 | Hinweis-Kasten S.16→17 | **Fehlende Regel** | `<p class="small muted">` hat keinen Break-Schutz |
| 1.6 | AI Act Kompakt S.15 | **Inhaltsproblem** | `minimal`-Risikoklasse = zu wenig Content (~30% Seite) |

---

## Abschnitt B — Förderdaten-Quelle ("Stand: Q1 2025")

### B.1 Fundstellen "Q1 2025" im Code

| # | Datei | Zeile | Kontext |
|---|-------|-------|---------|
| B1 | `services/extra_sections.py` | 865 | `können verfügbar sein. Stand: Q1 2025.'` — R1-Fördermatrix-Fußnote |
| B2 | `services/funding_service.py` | 289 | `{note_text} Stand: Q1 2025.'` — Multi-Country-Funding-Renderer |
| B3 | `gpt_analyze.py` | 10677 | `Stand: Q1 2025. Detaillierte Anforderungen entwickeln sich weiter` — AI-Act-Fallback-HTML |

**B1** ist die primäre Fundstelle für das gemeldete Problem. B2 ist der parallele Renderer für Multi-Country-Reports (EN/AT/CH). B3 gehört zum AI-Act-Block, nicht zum Förder-Block (betrifft aber ebenfalls den Zeitstempel).

### B.2 Daten-Architektur der Förderprogramme

#### Statische Datenbasis

**Primäre JSON-Datei:** `data/funding_programmes_core_2025.json` (477 Zeilen, 20 KB)
- Enthält ~20 Programme mit Feldern: `id`, `title`, `region`, `country_code`, `status`, `funding_rate`, `max_amount`, `suitable_for`, `relevance_ki`, `priority`, `deadline`
- Korrekt gepflegt: `go-digital` hat `"status": "expired"` und wird gefiltert (Zeile 7)
- Geladen in `extra_sections.py:727`: `data/funding_programmes_core_2025.json`

**Sekundäre Dateien:**
- `data/funding_programs.json` (3.2 KB) — Legacy/Fallback
- `data/funding/funding_de.json` (6.6 KB) — Alternative DE-Quelle
- `config/bafa.py` (3.5 KB) — Single Source of Truth für BAFA-Werte (Förderquote, Max-Zuschuss pro Bundesland)

#### Filterlogik in `build_core_funding_table_html()`

`extra_sections.py:712–869`:
1. Lädt JSON aus `funding_programmes_core_2025.json` (Zeile 727)
2. Filtert nach: `size_group` (solo/team/kmu), `country_code`, `status != "expired"` (Zeile ~770–807)
3. Priorisiert nach regionaler Relevanz (Bundesland-Match)
4. Rendert Top 6–8 Programme als HTML-Tabelle
5. **Hängt hardcoded Disclaimer an** (Zeile 862–866):
   ```python
   html_parts.append('  <p class="small muted" style="margin-top: 6pt;">')
   html_parts.append('    <strong>Hinweis:</strong> Diese Programme sind speziell für Ihr Unternehmensprofil ')
   html_parts.append(f'    ({size_label}) vorausgewählt. Weitere regionale und branchenspezifische Programme ')
   html_parts.append('    können verfügbar sein. Stand: Q1 2025.')
   ```

### B.3 Pipeline-Flow R1 vs. Strategy

#### R1-Report (das Problem)

Pipeline in `gpt_analyze.py:15568–15613`:

1. Ruft `build_core_funding_table_html(sections)` auf → statische Tabelle aus JSON
2. Wenn LLM-generiertes `FOERDERPOTENZIAL_HTML` vorhanden:
   - Entfernt LLM-halluzinierte `<table>`-Blöcke (Zeile 15594–15599)
   - Setzt programmatische Tabelle VOR LLM-Prosa (Zeile 15607–15610)
   - Header: "Kernprogramme für Ihr Profil (2025/2026)"
3. Wenn kein LLM-Content: Nur programmatische Tabelle (Zeile 15612–15613)

**Ergebnis:** R1 zeigt primär die statische Tabelle aus JSON + "Stand: Q1 2025"

#### Strategy-Report (funktioniert besser)

Pipeline in `services/strategy_pipeline.py:220–430`:
- S7-Section nutzt LLM-Generierung mit BAFA-Daten aus `config/bafa.py`
- Injiziert `foerder_matches` aus Research-Pipeline (wenn verfügbar)
- LLM generiert Fristen dynamisch ("BAFA bis 31.12.2026", "Aktuell prüfen")
- Kein hardcoded "Stand: Q1 2025" im Strategy-Renderer

#### Kernunterschied

| Aspekt | R1-Report | Strategy-Report |
|--------|-----------|-----------------|
| **Primäre Datenquelle** | `funding_programmes_core_2025.json` (statisch) | LLM + BAFA-Config |
| **Timestamp** | `"Stand: Q1 2025"` hardcoded | Keiner / LLM-generiert |
| **Halluzinations-Schutz** | Programmatische Tabelle ersetzt LLM-Tabellen | Prompt-Constraints + Content-Enforcer |
| **Aktualität** | An JSON-Datei gebunden | An Prompt-Wissen + Config gebunden |
| **Fristen** | Aus JSON (`deadline`-Feld) | LLM generiert ("bis 31.12.2026") |

### B.4 Warum "Q1 2025"?

Der Timestamp ist **dreifach hardcoded im Python-Code**, nicht in der JSON-Datei. Die JSON-Datei selbst enthält kein "Q1 2025" — sie hat individuelle `deadline`-Felder pro Programm. Der Disclaimer-Text wurde vermutlich bei der Erstimplementierung gesetzt und nie aktualisiert.

**Die JSON-Daten selbst sind gepflegt** (go-digital korrekt als "expired" markiert, andere Programme haben aktuelle Fristen). Nur der Zeitstempel-String im Renderer ist veraltet.

### B.5 Empfehlung

**Quick-Fix (empfohlen):** Alle drei "Q1 2025"-Strings durch dynamisches Quartal ersetzen:

```python
from datetime import datetime
_now = datetime.now()
_quartal = f"Q{(_now.month - 1) // 3 + 1} {_now.year}"
# → "Q2 2026" bei Generierung im April 2026
```

Betroffene Stellen:
1. `services/extra_sections.py:865` — `Stand: Q1 2025.` → `Stand: {_quartal}.`
2. `services/funding_service.py:289` — identisch
3. `gpt_analyze.py:10677` — AI-Act-Fallback, gleicher Fix

**Langfristig:** Prüfen, ob die JSON-Datei `funding_programmes_core_2025.json` regelmäßig aktualisiert wird, oder ob ein automatischer Expiry-Check (z.B. `deadline < today → status = "expired"`) sinnvoll wäre. Die Daten selbst sind aktuell, nur der Label-String nicht.
