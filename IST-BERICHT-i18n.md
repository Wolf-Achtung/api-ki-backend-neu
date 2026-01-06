# IST-BERICHT: Internationalisierung (i18n) - PHASE 6.1

**Erstellt:** 2026-01-06
**Status:** IST-Analyse abgeschlossen
**Umfang:** Vollständige Bestandsaufnahme aller EN-Ressourcen

---

## 1. EXECUTIVE SUMMARY

Das Repository verfügt bereits über **grundlegende i18n-Infrastruktur**, die jedoch **unvollständig und veraltet** ist. Die EN-Version liegt ca. 1-2 Sprints hinter der DE-Version zurück.

| Bereich | Status | Abdeckung |
|---------|--------|-----------|
| Prompts | ⚠️ Veraltet | 46 von 48 (96%) |
| Templates | ⚠️ Veraltet | 1 von 1 (100%), aber nur ~48% Größe |
| Funding Service | ✅ Aktuell | 100% funktional |
| UI Labels | ✅ Aktuell | 5-sprachig (de/en/fr/es/it) |
| Knowledge Base | ✅ Vorhanden | 7 HTML-Dateien |
| Branch Contexts | ✅ Vorhanden | 12 EN-Kontexte |
| Frontend | ❌ Fehlt | Kein formbuilder_en.js |

---

## 2. DETAILLIERTE BESTANDSAUFNAHME

### 2.1 Services

#### `services/funding_service_en.py` ✅ AKTUELL
- **Version:** 2.0.0
- **Letztes Update:** Phase 5B (kürzlich)
- **Funktionen:**
  - `get_funding_for_germany_en()` - Deutsche Förderprogramme auf EN
  - `get_funding_eu_core_en()` - EU-Core Programme für Nicht-DE Länder
  - `render_funding_html_en()` - HTML-Rendering
  - `render_funding_eu_core_html_en()` - EU-Core HTML-Rendering
- **Status:** Verwendet unified types (`FundingProgramView`, `FundingRenderContext`)
- **Bewertung:** Production-ready, gut strukturiert

#### `services/funding_service.py` (DE-Version zum Vergleich)
- **Version:** 1.0.0
- **Features:** Multi-Country Support (DE, AT, EU)
- **Unterschied zu EN:** DE-Version hat `FundingService` Klasse mit mehr Abstraktion

### 2.2 Data Files - Funding

| Datei | Status | Beschreibung |
|-------|--------|--------------|
| `data/funding/funding_de_en.json` | ✅ Aktuell | Deutsche Programme auf EN, 10+ Programme |
| `data/funding/funding_eu_core_en.json` | ✅ Aktuell | EU-Core Programme, 10+ Programme |
| `data/funding/funding_de.json` | ✅ Vorhanden | DE-Programme auf DE |
| `data/funding/funding_eu.json` | ✅ Vorhanden | EU-Programme auf DE |
| `data/funding/config.json` | ✅ Vorhanden | Funding-Konfiguration |

### 2.3 Prompts-Struktur

#### Prompts in BEIDEN Sprachen (46 Dateien):
```
ai_act_summary.md          automation_roadmap_engine.md
benchmark_engine.md        branch_deep_dive.md
business_case.md           business_case_engine_v2.md
business_case_simulation.md costs_overview.md
data_readiness.md          exec_snapshot.md
executive_decision.md      executive_summary.md
foerderpotenzial.md        foerderprogramme.md
funding_engine_v2.md       gamechanger.md
gamechanger_decision.md    ki_aktivitaeten_ziele.md
ki_skillplan.md            ki_stack_summary.md
monetarisierung.md         next_actions.md
org_change.md              prompt_framework.md
quick_wins.md              recommendations.md
recommendations_engine.md  risk_engine_v2.md
risk_engine_v3.md          risks.md
roadmap_12m.md             roadmap_90d.md
roadmap_90d_decision.md    strategie_governance.md
templates_start.md         technologie_prozesse.md
tools_empfehlungen.md      tools_engine_v4.md
top_3_massnahmen.md        transparency_box.md
unternehmensprofil_markt.md vendor_audit_engine.md
wettbewerb_benchmark.md    ai_policy_mini.md
kickoff_vorlage.md         roi_tracking.md
```

#### NUR in DE (2 Dateien - interne Helpers):
- `_hauptleistung_context.md` - Context-Template
- `_solo_language_rules.md` - Solo-Sprachregeln

#### NUR in EN (10 Dateien - EN-spezifische Versionen):
- `ai_activities_goals.md` - EN-Version von ki_aktivitaeten_ziele
- `competition_benchmark.md` - EN-Version von wettbewerb_benchmark
- `funding.md` - Generischer Funding-Prompt
- `funding_eu_core.md` - EU-Core Funding Prompt
- `funding_potential.md` - EN-Version von foerderpotenzial
- `kickoff_template.md` - EN-Version von kickoff_vorlage
- `monetization.md` - EN-Version von monetarisierung
- `strategy_governance.md` - EN-Version von strategie_governance
- `technology_processes.md` - EN-Version von technologie_prozesse
- `tools_recommendations.md` - EN-Version von tools_empfehlungen

### 2.4 Templates

| Template | DE | EN | Status |
|----------|----|----|--------|
| `pdf_template.html` | ✅ 7.220 Zeilen | - | Aktuell (v6.1+) |
| `pdf_template_en.html` | - | ⚠️ 3.499 Zeilen | **VERALTET** (~48% Größe) |

#### Template-Analyse:
- **DE-Template:** PLATIN++ v6.1+, alle Sections, vollständig
- **EN-Template:** PLATIN++ v5.2, fehlen ~3.700 Zeilen
- **Fehlende Sections im EN-Template:**
  - Erweiterter Branchen-Deep-Dive
  - Erweiterte Business-Case Sections
  - Neuere Risk-Engine Visualisierungen
  - Phase 5 Improvements

### 2.5 Knowledge Base

#### `knowledge/en/` (7 Dateien):
```
ai_act_summary.html    (3.102 Bytes)
creative_tools.html    (2.693 Bytes)
four_pillars.html      (1.253 Bytes)
glossary.html          (2.637 Bytes)
legal_pitfalls.html    (  968 Bytes)
sme_keypoints.html     (  453 Bytes)
ten_20_70.html         (  733 Bytes)
```

#### `knowledge/` (DE, 4 Dateien im Root):
```
four_pillars.html      (1.268 Bytes)
kmu_keypoints.html     (  496 Bytes)
legal_pitfalls.html    (1.058 Bytes)
ten_20_70.html         (  786 Bytes)
```

**Struktur-Problem:** DE-Dateien liegen im Root, EN in Subfolder. Inkonsistent.

### 2.6 Branch Contexts

| Sprache | Anzahl | Location |
|---------|--------|----------|
| DE | 15 | `data/branch_contexts/*.json` (Root) |
| EN | 12 | `data/branch_contexts/en/*.json` |

**EN-Kontexte vorhanden:**
- commerce.json, consulting.json, construction_architecture.json
- creative_media.json, education.json, energy_utility.json
- finance_insurance.json, healthcare.json, it_software.json
- logistics_transport.json, manufacturing.json, public_sector.json

**Fehlende EN-Kontexte:** bau, beratung, bildung, gesundheit, handel, industrie, logistik, marketing, medien, verwaltung (teilweise DE-spezifische Namen, teilweise redundant mit EN)

### 2.7 UI Labels

`i18n/ui_labels.json`:
- **Sprachen:** de, en, fr, es, it (5 Sprachen!)
- **Einträge:** ~150+ Labels
- **Status:** ✅ Sehr gut strukturiert, zentral verwaltet
- **Quellen:** Templates, prompt_enhancer, report_validator, html_sanitizer

### 2.8 Test Profiles

`data/test_profiles_en/` (7 Dateien):
- kmu_france_eu_core_en.json
- team_it_guardrails_extreme_en.json
- team_it_en.json
- solo_consulting_de_funding_en.json
- kmu_guardrails_en.json
- kmu_industry_en.json
- solo_consulting_en.json

### 2.9 Frontend

- **formbuilder_en.js:** ❌ Existiert NICHT
- **Gefundene JS-Dateien:**
  - `adapter/context_adapter.js`
  - `admin/admin.js`
  - `admin/detail.js`
- **Status:** Kein EN-spezifisches Frontend vorhanden

---

## 3. VERSIONS-VERGLEICH: DE vs EN

### 3.1 Prompt-Versionen

| Prompt | DE-Version | EN-Version | Delta |
|--------|------------|------------|-------|
| executive_summary.md | PLATIN+++ v6.1 | PLATIN++ v5.2 | ⚠️ 1 Major Version |
| Alle anderen | ~v6.x | ~v5.x | ⚠️ Teilweise veraltet |

**Beispiel executive_summary.md:**
- DE: 1500 Token-Budget, 250 Word-Minimum, Phase 2 Individualisierung
- EN: 600 Token-Budget, keine Micro-Consistency Rules

### 3.2 Template-Features

| Feature | DE | EN |
|---------|----|----|
| Zeilen | 7.220 | 3.499 |
| Version | v6.1+ | v5.2 |
| Branch Deep-Dive | ✅ | ⚠️ Basic |
| Business Case Engine v2 | ✅ | ⚠️ Möglicherweise fehlt |
| Risk Engine v3 | ✅ | ⚠️ Möglicherweise fehlt |
| Glossar | ✅ Erweitert | ✅ Vorhanden |
| Impressum/Legal | ✅ | ✅ EN-Übersetzung |
| Feedback Section | ✅ | ✅ EN-Übersetzung |

---

## 4. GAP-ANALYSE

### 4.1 Kritische Gaps (Must-Fix)

1. **Template pdf_template_en.html**
   - Fehlen ~3.700 Zeilen Content
   - Fehlende neue Sections von v5.2 → v6.1+
   - **Impact:** EN-Reports unvollständig

2. **Prompt-Synchronisation**
   - 46 Prompts müssen auf v6.x aktualisiert werden
   - Fehlende Token-Budget Anpassungen
   - Fehlende Micro-Consistency Rules
   - **Impact:** EN-Output-Qualität niedriger

3. **Frontend (formbuilder_en.js)**
   - Existiert nicht
   - **Impact:** Keine EN-Benutzeroberfläche

### 4.2 Moderate Gaps

1. **Knowledge Base Struktur**
   - DE im Root, EN in Subfolder
   - **Empfehlung:** Beide in `knowledge/de/` und `knowledge/en/`

2. **Branch Contexts**
   - 15 DE vs 12 EN
   - Naming-Inkonsistenz (DE: "handel" vs EN: "commerce")

3. **Helper Prompts**
   - `_hauptleistung_context.md` fehlt für EN
   - `_solo_language_rules.md` fehlt für EN (wahrscheinlich nicht nötig)

### 4.3 Nice-to-Have

1. **Weitere Sprachen**
   - ui_labels.json hat bereits fr/es/it
   - Prompts/Templates nur de/en

---

## 5. ARCHITEKTUR-EMPFEHLUNG

### 5.1 Empfohlene i18n-Struktur

```
/
├── i18n/
│   └── ui_labels.json          # Zentrale UI-Labels (✅ bereits vorhanden)
│
├── prompts/
│   ├── de/                     # ✅ bereits vorhanden
│   │   └── *.md
│   └── en/                     # ✅ bereits vorhanden, aber veraltet
│       └── *.md
│
├── templates/
│   ├── pdf_template.html       # DE (umbenennen zu pdf_template_de.html?)
│   └── pdf_template_en.html    # EN (aktualisieren)
│
├── knowledge/
│   ├── de/                     # NEU: DE-Dateien hierhin verschieben
│   │   └── *.html
│   └── en/                     # ✅ bereits vorhanden
│       └── *.html
│
├── data/
│   ├── branch_contexts/
│   │   ├── de/                 # NEU: DE-Kontexte hierhin verschieben
│   │   │   └── *.json
│   │   └── en/                 # ✅ bereits vorhanden
│   │       └── *.json
│   │
│   └── funding/
│       ├── config.json
│       ├── funding_de.json
│       ├── funding_de_en.json  # DE-Programme auf EN
│       ├── funding_eu.json
│       └── funding_eu_core_en.json
│
├── services/
│   ├── funding_service.py      # Haupt-Service (multi-lang capable)
│   └── funding_service_en.py   # EN-spezifisch (ggf. mergen?)
│
└── static/
    └── js/
        ├── formbuilder.js      # DE (aktuell)
        └── formbuilder_en.js   # NEU: EN-Version benötigt
```

### 5.2 Service-Architektur

**Option A: Getrennte Services (aktuell)**
- funding_service.py (DE)
- funding_service_en.py (EN)
- **Pro:** Klare Trennung
- **Con:** Code-Duplikation

**Option B: Unified Service (empfohlen)**
```python
class FundingService:
    def get_recommendations(self, country, lang, answers):
        if lang == "en" and country == "DE":
            return self._get_germany_en(answers)
        elif lang == "en" and country != "DE":
            return self._get_eu_core_en(answers)
        else:
            return self._get_de(answers)
```

### 5.3 Template-Strategie

**Empfehlung:** Template-Inheritance statt Duplikation
```
pdf_base.html          # Shared CSS, Layout, Struktur
├── pdf_template_de.html  # DE-spezifische Inhalte
└── pdf_template_en.html  # EN-spezifische Inhalte
```

---

## 6. IMPLEMENTATION SCHÄTZUNG

### 6.1 Aufwandsschätzung nach Bereich

| Bereich | Aufwand | Beschreibung |
|---------|---------|--------------|
| Template-Sync | HIGH | 3.700 Zeilen synchronisieren, alle neuen Sections |
| Prompt-Updates | MEDIUM-HIGH | 46 Prompts auf v6.x aktualisieren |
| Frontend EN | MEDIUM | formbuilder_en.js erstellen |
| Knowledge-Reorg | LOW | Dateien verschieben |
| Branch-Context-Sync | LOW-MEDIUM | 3 fehlende Kontexte, Naming harmonisieren |
| Testing | MEDIUM | EN-Reports testen, Regressions prüfen |

### 6.2 Priorisierte Roadmap

**Phase 6.2 - Template-Sync (höchste Priorität)**
- pdf_template_en.html auf v6.1+ aktualisieren
- Alle fehlenden Sections einfügen
- CSS/Styling synchronisieren

**Phase 6.3 - Prompt-Updates (hohe Priorität)**
- Alle 46 EN-Prompts auf aktuelle DE-Versionen updaten
- Token-Budgets anpassen
- Micro-Consistency Rules hinzufügen

**Phase 6.4 - Frontend**
- formbuilder_en.js erstellen
- Language-Switcher implementieren

**Phase 6.5 - Strukturbereinigung**
- Knowledge-Base-Struktur vereinheitlichen
- Branch-Contexts vervollständigen
- Service-Konsolidierung prüfen

### 6.3 Aufwands-Matrix

| Phase | Story Points | Priorität | Abhängigkeiten |
|-------|--------------|-----------|----------------|
| 6.2 Template-Sync | 13 | P0 | - |
| 6.3 Prompt-Updates | 8 | P1 | - |
| 6.4 Frontend | 5 | P2 | 6.2, 6.3 |
| 6.5 Strukturbereinigung | 3 | P3 | - |
| Testing & QA | 5 | P1 | 6.2, 6.3 |

**Gesamt:** ~34 Story Points (entspricht ca. 2-3 Sprints bei normalem Tempo)

---

## 7. NÄCHSTE SCHRITTE

### Sofort (Phase 6.2)
1. [ ] pdf_template_en.html mit pdf_template.html diff analysieren
2. [ ] Fehlende Sections identifizieren und einfügen
3. [ ] CSS-Updates synchronisieren

### Kurzfristig (Phase 6.3)
1. [ ] executive_summary.md EN auf v6.1 updaten (Pilot)
2. [ ] Systematische Prompt-Aktualisierung planen
3. [ ] Automatisiertes Diff-Tool für Prompts erstellen

### Mittelfristig (Phase 6.4-6.5)
1. [ ] formbuilder_en.js entwickeln
2. [ ] Language-Switcher im Frontend
3. [ ] Strukturbereinigung durchführen

---

## 8. ANHANG: VOLLSTÄNDIGE FILE-LISTE

### EN-Files gefunden (75 Dateien):

**Services (1):**
- services/funding_service_en.py

**Templates (1):**
- templates/pdf_template_en.html

**Data - Funding (2):**
- data/funding/funding_de_en.json
- data/funding/funding_eu_core_en.json

**Data - Test Profiles (7):**
- data/test_profiles_en/kmu_france_eu_core_en.json
- data/test_profiles_en/team_it_guardrails_extreme_en.json
- data/test_profiles_en/team_it_en.json
- data/test_profiles_en/solo_consulting_de_funding_en.json
- data/test_profiles_en/kmu_guardrails_en.json
- data/test_profiles_en/kmu_industry_en.json
- data/test_profiles_en/solo_consulting_en.json

**Knowledge (7):**
- knowledge/en/ai_act_summary.html
- knowledge/en/creative_tools.html
- knowledge/en/four_pillars.html
- knowledge/en/glossary.html
- knowledge/en/legal_pitfalls.html
- knowledge/en/sme_keypoints.html
- knowledge/en/ten_20_70.html

**Branch Contexts (12):**
- data/branch_contexts/en/commerce.json
- data/branch_contexts/en/consulting.json
- data/branch_contexts/en/construction_architecture.json
- data/branch_contexts/en/creative_media.json
- data/branch_contexts/en/education.json
- data/branch_contexts/en/energy_utility.json
- data/branch_contexts/en/finance_insurance.json
- data/branch_contexts/en/healthcare.json
- data/branch_contexts/en/it_software.json
- data/branch_contexts/en/logistics_transport.json
- data/branch_contexts/en/manufacturing.json
- data/branch_contexts/en/public_sector.json

**Prompts (56):**
- Alle 56 Prompts in prompts/en/

**i18n (1):**
- i18n/ui_labels.json (5-sprachig)

---

*IST-BERICHT erstellt am 2026-01-06 durch automatisierte Analyse*
