# IST-ZUSTAND ANALYSE - KI-Readiness-Report Backend

**Datum:** 29.12.2025
**Version:** 5.4.3-PLATIN+++
**Analysiert von:** Claude Code (Opus 4.5)

---

## EXECUTIVE SUMMARY

Das Backend-System ist technisch ausgereift mit ~100 Python-Dateien, ~50 Prompt-Templates und paralleler LLM-Generierung. **Das Hauptproblem ist die fehlende Individualisierung**: Quick Wins sind statisch, Executive Summary nutzt generische Labels statt echter Briefing-Daten, und viele Freitext-Felder werden ignoriert.

---

## Task 1.1: Backend-Struktur

### Verzeichnisse
```
/home/user/api-ki-backend-neu/
├── gpt_analyze.py        # 365KB - Hauptdatei!
├── main.py               # FastAPI Entry Point
├── field_registry.py     # Felddefinitionen
├── prompts/              # Prompt-Templates
│   ├── de/               # ~50 deutsche Prompts
│   └── en/               # ~50 englische Prompts
├── services/             # ~100 Service-Module
├── routes/               # API-Endpunkte
├── utils/                # Hilfsfunktionen
└── templates/            # HTML-Templates
```

### Wichtigste Python-Dateien
| Datei | Funktion | Größe |
|-------|----------|-------|
| `gpt_analyze.py` | Report-Generierung | 365KB |
| `services/prompt_loader.py` | Prompt-Loading | 9KB |
| `services/prompt_enhancer.py` | Kontext-Injektion | 25KB |
| `services/extra_sections.py` | Business Case | 15KB |
| `utils/encoding_fixer.py` | UTF-8 Fix | 4KB |

### Briefing-Verarbeitung
- **Briefing geladen in:** `gpt_analyze.py:5636-5647`
- **Normalisierung:** `services/answers_normalizer.py`
- **Score-Berechnung:** `gpt_analyze.py:5683-5688` (`_calculate_realistic_score`)
- **Variablen-Build:** `gpt_analyze.py:2535-2795` (`_build_prompt_vars`)

---

## Task 1.2: Prompt-Dateien

### Prompt-Übersicht (prompts/de/)

| Prompt-Name | Datei | unternehmensgroesse | branche | hauptleistung | zeitersparnis_prioritaet | scores |
|-------------|-------|:-------------------:|:-------:|:-------------:|:------------------------:|:------:|
| executive_summary | `prompts/de/executive_summary.md` | ✅ (COMPANY_SIZE) | ❌ (nur Label) | ❌ (nur Label) | ❌ | ❌ |
| quick_wins | `prompts/de/quick_wins.md` | ✅ (COMPANY_SIZE) | ❌ (nur Text) | ❌ (nur Text) | ❌ | ❌ |
| roadmap_90d | `prompts/de/roadmap_90d.md` | ✅ | ❌ | ❌ | ❌ | ✅ |
| gamechanger | `prompts/de/gamechanger.md` | ✅ | ✅ | ✅ | ❌ | ✅ |
| foerderpotenzial | `prompts/de/foerderpotenzial.md` | ✅ | ✅ | ✅ | ❌ | ✅ |
| risks | `prompts/de/risks.md` | ✅ | ✅ | ✅ | ❌ | ✅ |
| recommendations | `prompts/de/recommendations.md` | ✅ | ✅ | ✅ | ❌ | ✅ |

### Kritische Beobachtung
- `COMPANY_SIZE` (solo/team/kmu) wird konsistent verwendet
- `HAUPTLEISTUNG` wird oft nur als Text eingebettet, nicht für Logik
- `zeitersparnis_prioritaet` wird **in keinem Prompt** verwendet!
- `vision_3_jahre` wird **in keinem Prompt** verwendet!
- `ki_guardrails` wird nur für Guardrail-Detection verwendet, nicht für Empfehlungen

---

## Task 1.3: Datenfluss

```
📥 Briefing-Laden
   Datei: gpt_analyze.py:5636
   Zeile: br = db.get(Briefing, briefing_id)
   ↓
🔧 Encoding Fix
   Datei: gpt_analyze.py:5642
   Funktion: clean_briefing_data(raw_answers)
   ↓
📊 Score-Berechnung
   Datei: gpt_analyze.py:5683-5688
   Funktion: _calculate_realistic_score(answers)
   Scores: governance, security, value, enablement, overall
   ↓
💰 Business Case
   Datei: gpt_analyze.py:5693-5707
   Funktion: calc_business_case(answers)
   ↓
📝 Prompt-Variable Build
   Datei: gpt_analyze.py:2535-2795
   Funktion: _build_prompt_vars(briefing, scores)
   ⚠️ Felder fehlen:
   - zeitersparnis_prioritaet (nicht als Variable)
   - vision_3_jahre (nicht als Variable)
   - ki_guardrails (nicht für Empfehlungen)
   ↓
🤖 Parallel GPT-Calls
   Datei: gpt_analyze.py:5041-5117
   Workers: 10 parallel
   Sections: 35 parallel
   ↓
📄 HTML-Rendering
   Datei: services/report_renderer.py
   Template: templates/pdf_template.html
```

---

## Task 1.4: Executive Summary Prompt - Analyse

**Datei:** `prompts/de/executive_summary.md`
**Länge:** 242 Zeilen

### Verwendete Variablen
| Variable | Quelle | Verwendung |
|----------|--------|------------|
| `{{BRANCH_CONTEXT_LABEL}}` | `generate_short_labels()` | Generisches Branchen-Label |
| `{{OFFERING_LABEL}}` | `generate_short_labels()` | Generisches Angebots-Label |
| `{{HAUPTUMSATZTREIBER}}` | Mapping aus `branche` | ❌ Nicht die echte hauptleistung! |
| `COMPANY_SIZE` | Jinja2 if/else | ✅ Korrekt |

### Problem
```
❌ Die Executive Summary nutzt NICHT die echte `hauptleistung` aus dem Briefing!

Stattdessen wird ein generisches Label basierend auf `branche` generiert:
- branche="beratung" → OFFERING_LABEL="KI-Readiness-Analysen & Workflow-Automatisierung"

Aber im Briefing 368 steht:
- hauptleistung="Beratung von Unternehmen zur Integration von KI..."
- zeitersparnis_prioritaet="Umsetzung und Programmierung..."
- strategische_ziele="- neue Märkte und Kunden/Unternehmen erschliessen"

→ Diese Freitext-Felder werden NICHT in der Executive Summary verwendet!
```

---

## Task 1.5: Quick Wins Logik - KRITISCH

**Datei:** `prompts/de/quick_wins.md`
**Implementierung:** **STATISCH** mit Jinja2 if/else

### Der Code (Auszug):
```markdown
{% if COMPANY_SIZE == "solo" %}
Die folgenden 3 Quick Wins sind speziell für Solo-Selbstständige im Bereich **{{HAUPTLEISTUNG}}** konzipiert:

### QUICK WIN #1: E-Mail-Entwürfe automatisieren (5-8 Std./Monat)
### QUICK WIN #2: Dokument-Zusammenfassungen beschleunigen (4-6 Std./Monat)
### QUICK WIN #3: Angebots- und Präsentationserstellung (4-5 Std./Monat)

{% elif COMPANY_SIZE == "team" %}
[...]
{% else %}
[...]
{% endif %}
```

### Problem

| Aspekt | Status | Erklärung |
|--------|--------|-----------|
| Score-abhängig? | ❌ NEIN | Security-Score 60 vs 70 → identische Quick Wins |
| Verwendet `hauptleistung`? | ❌ NEIN | Nur als Text eingebettet, nicht für Logik |
| Verwendet `zeitersparnis_prioritaet`? | ❌ NEIN | Komplett ignoriert! |
| Verwendet `branche` für Empfehlungen? | ❌ NEIN | Nur als Text |

### Konkretes Beispiel
```
Briefing 368 (KI-Berater):
- hauptleistung: "Beratung von Unternehmen zur Integration von KI"
- zeitersparnis_prioritaet: "Umsetzung und Programmierung"
- branche: "beratung"
- unternehmensgroesse: "solo"

Bekommt IDENTISCHE Quick Wins wie ein Fotograf:
- hauptleistung: "Hochzeitsfotografie"
- zeitersparnis_prioritaet: "Bildbearbeitung"
- branche: "medien"
- unternehmensgroesse: "solo"

→ Beide bekommen: E-Mail-Automatisierung, Dokument-Zusammenfassungen, Angebotserstellung
→ Das macht keinen Sinn für einen KI-Berater!
```

---

## Task 1.6: Seiten-Reihenfolge

**Datei:** `gpt_analyze.py:5041-5079`

| Seite | Section Key | HTML Key | Generator |
|-------|-------------|----------|-----------|
| 1 | Cover | - | Template |
| 2 | executive_summary | EXECUTIVE_SUMMARY_HTML | GPT + Prompt |
| 3 | executive_decision | EXECUTIVE_DECISION_HTML | GPT + Prompt |
| 4 | ki_stack_summary | KI_STACK_SUMMARY_HTML | GPT + Prompt |
| 5 | quick_wins | QUICK_WINS_HTML | GPT + **STATISCH** |
| 6 | roadmap | PILOT_PLAN_HTML | GPT + Prompt |
| 7 | roadmap_12m | ROADMAP_12M_HTML | GPT + Prompt |
| 8 | business_roi | ROI_HTML | Berechnung |
| 9 | business_case | BUSINESS_CASE_HTML | GPT + Berechnung |
| 10 | risks | RISKS_HTML | GPT + Prompt |
| 11 | recommendations | RECOMMENDATIONS_HTML | GPT + Prompt |
| 12 | gamechanger | GAMECHANGER_HTML | GPT + Prompt |
| 13 | foerderpotenzial | FOERDERPOTENZIAL_HTML | GPT + Prompt |
| ... | ... | ... | ... |

**35 Sektionen** werden parallel generiert (max 10 Workers).

---

## Task 1.7: UTF-8 Encoding

**Datei:** `utils/encoding_fixer.py`
**Status:** ✅ Implementiert

### Implementierung
```python
# gpt_analyze.py:5642
raw_answers = clean_briefing_data(raw_answers)

# utils/encoding_fixer.py:28-83
def fix_utf8_encoding(text: str) -> str:
    """Fix double-encoded UTF-8 German umlauts."""
    # Verwendet ftfy wenn vorhanden, sonst manuelle Ersetzung
    replacements = {
        'Ã¤': 'ä', 'Ã¶': 'ö', 'Ã¼': 'ü',
        'Ã„': 'Ä', 'Ã–': 'Ö', 'Ãœ': 'Ü',
        ...
    }
```

### Problem
⚠️ Das Encoding-Problem in `briefing-368-full.json` ("FragebÃ¶gen") deutet darauf hin, dass die Daten **vor** dem Speichern in der DB bereits falsch encodiert waren. Der Fixer greift nur beim Laden.

---

## GEFUNDENE PROBLEME (priorisiert)

### 🔴 KRITISCH - Problem 1: Quick Wins sind STATISCH

**Wo:** `prompts/de/quick_wins.md`
**Was:** Quick Wins sind hartcodiert mit Jinja2 if/else nach COMPANY_SIZE
**Impact:**
- Alle Solo-User bekommen identische Quick Wins
- `hauptleistung` wird ignoriert
- `zeitersparnis_prioritaet` wird ignoriert
- `branche` wird nur als Text eingebettet

**Warum kritisch:**
Der Report wirkt generisch und nicht individuell. Ein KI-Berater bekommt "E-Mail-Automatisierung" statt "Report-Template-Automatisierung".

---

### 🔴 KRITISCH - Problem 2: Freitext-Felder werden nicht genutzt

**Wo:** `gpt_analyze.py:2535-2795` (`_build_prompt_vars`)
**Was:** Diese wichtigen Felder sind NICHT als Prompt-Variablen verfügbar:
- `zeitersparnis_prioritaet`
- `vision_3_jahre`
- `geschaeftsmodell_evolution`
- `ki_guardrails` (für Empfehlungen)

**Impact:**
Die individuellsten Antworten des Users werden nicht für die Report-Generierung verwendet.

**Warum kritisch:**
Der User gibt Freitext ein mit "Umsetzung und Programmierung als Zeitfresser" - aber Quick Wins empfehlen E-Mail-Automatisierung.

---

### 🔴 KRITISCH - Problem 3: Executive Summary nutzt generische Labels

**Wo:** `services/prompt_enhancer.py:335-400` (`generate_short_labels`)
**Was:**
- `{{OFFERING_LABEL}}` wird aus `branche` gemappt, nicht aus `hauptleistung`
- branche="beratung" → "KI-Readiness-Analysen & Workflow-Automatisierung"
- Echte `hauptleistung` wird überschrieben

**Impact:**
Executive Summary beschreibt nicht das echte Geschäft des Users.

---

### 🟡 WICHTIG - Problem 4: Scores nicht in Quick Wins

**Wo:** `prompts/de/quick_wins.md`
**Was:** Security-Score, Governance-Score etc. beeinflussen Quick Wins nicht
**Impact:**
User mit Security-Score 30 bekommt keine Security-Quick-Wins priorisiert.

---

### 🟡 WICHTIG - Problem 5: Keine Branchen-spezifischen Quick Wins

**Wo:** `prompts/de/quick_wins.md`
**Was:** Branche wird nur als Text eingebettet ("im Bereich {{BRANCHE_LABEL}}")
**Impact:**
- Finance-Branche: Sollte Compliance-Tools empfehlen
- Kreativ-Branche: Sollte Design-Tools empfehlen
- Aber alle bekommen: ChatGPT, Claude, Notion

---

### 🟢 MINOR - Problem 6: UTF-8 bei bestehenden DB-Einträgen

**Wo:** Datenbank (historische Daten)
**Was:** Encoding-Fix greift nur bei neuen Daten
**Impact:** Alte Reports haben ggf. falsche Umlaute

---

## Priorisierte Fix-Liste

| Prio | Problem | Fix | Aufwand |
|------|---------|-----|---------|
| ⚡ 1 | Quick Wins statisch | Quick Wins als LLM-Prompt mit Kontext | Mittel |
| ⚡ 2 | Freitext-Felder fehlen | Variablen in `_build_prompt_vars` ergänzen | Klein |
| ⚡ 3 | Executive Summary generisch | `hauptleistung` statt Label verwenden | Klein |
| 🔥 4 | Scores in Quick Wins | Score-Kontext in Prompt einfügen | Mittel |
| 🔥 5 | Branchen-spezifisch | Branchen-Mapping für Empfehlungen | Mittel |
| 🔧 6 | UTF-8 Migration | DB-Migration Script | Klein |

---

## Betroffene Dateien

| Datei | Änderung | Priorität |
|-------|----------|-----------|
| `prompts/de/quick_wins.md` | Komplett überarbeiten | SOFORT |
| `gpt_analyze.py:2535-2795` | Variablen ergänzen | SOFORT |
| `prompts/de/executive_summary.md` | `{{HAUPTLEISTUNG}}` nutzen | HOCH |
| `services/prompt_enhancer.py:335-400` | Labels aus echten Daten | HOCH |
| `prompts/de/recommendations.md` | Freitext-Kontext nutzen | MITTEL |

---

## Empfehlung

### Phase 1: Quick Wins (Sofort)
1. `prompts/de/quick_wins.md` in dynamischen LLM-Prompt umwandeln
2. Kontext-Block mit `hauptleistung`, `zeitersparnis_prioritaet`, `scores` einfügen
3. Branchen-spezifische Tool-Empfehlungen

### Phase 2: Prompt-Variablen (Diese Woche)
1. `_build_prompt_vars` um fehlende Felder erweitern:
   - `ZEITERSPARNIS_PRIORITAET`
   - `VISION_3_JAHRE`
   - `GESCHAEFTSMODELL_EVOLUTION`
   - `KI_GUARDRAILS`
2. In Executive Summary und Recommendations nutzen

### Phase 3: Score-Integration (Nächste Woche)
1. Score-Thresholds für Empfehlungen definieren
2. Security < 50 → Security-Quick-Wins priorisieren
3. Governance < 50 → Governance-Quick-Wins priorisieren

---

## Nächste Schritte

**Warte auf Freigabe von Wolf für Phase 2 (Implementierung)**

Die Analyse ist abgeschlossen. Die kritischsten Probleme sind:
1. Quick Wins sind statisch → **Individualisierung = 0**
2. Freitext-Felder werden ignoriert → **Verschwendete User-Eingaben**
3. Generische Labels statt echter Daten → **Report wirkt unpersönlich**

---

*Bericht erstellt: 29.12.2025 von Claude Code (Opus 4.5)*
