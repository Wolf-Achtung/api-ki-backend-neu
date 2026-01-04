# Prompt-Inventar: KI-Sicherheit.jetzt

## Übersicht
- **Gesamt:** 46 deutsche Prompts + englische Varianten
- **Speicherort:** `prompts/de/*.md`, `prompts/en/*.md`
- **Loader:** `services/prompt_loader.py`
- **Enhancer:** `services/prompt_enhancer.py` (Persona-Anpassung)

---

## Prompt-Struktur (Standard)

Jeder Prompt folgt diesem Schema:
```markdown
Developer:
<!-- PLATIN++ PROMPT vX.X - SPRINT XX -->
<!-- SECTION: section_name -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{VARIABLE1}}, {{VARIABLE2}}, ... -->
<!-- TOKEN-BUDGET: XXX (solo:0.8x, team:1.0x, kmu:1.15x) -->

[Struktur-Anweisungen]
[HTML-Template mit Jinja2-Variablen]
[Anti-Pattern-Regeln]
[Qualitäts-Selbstcheck]
```

---

## Kritische Prompts für die 7 Probleme

### 1. recommendations.md (Problem #5: Duplikate)
- **Pfad:** `prompts/de/recommendations.md`
- **Zweck:** 5-10 Handlungsempfehlungen generieren
- **Token-Budget:** 600 (solo: 480)
- **Input-Variablen:**
  - `{{BRANCH_CORE_LABEL}}` - Branche (8-12 Wörter)
  - `{{BRANCH_CONTEXT_LABEL}}` - Branche kurz (4-6 Wörter)
  - `{{OFFERING_LABEL}}` - Hauptleistung
  - `{{ZEITERSPARNIS_PRIORITAET}}` - Größter Zeitfresser
  - `{{KI_GUARDRAILS}}` - Einschränkungen
  - `{{COMPANY_SIZE}}` - solo/team/kmu
- **Problem:** Hat Anti-Redundanz-Hinweis (Zeile 104-108), wird aber nicht erzwungen

### 2. foerderpotenzial.md (Problem #1, #2: Förderung)
- **Pfad:** `prompts/de/foerderpotenzial.md`
- **Zweck:** Förderpotenzial-Sektion
- **Token-Budget:** 3200 (solo: 0.8x)
- **Input-Variablen:**
  - `{{BUNDESLAND_LABEL}}`
  - `{{BRANCHE_LABEL}}`
  - `{{UNTERNEHMENSGROESSE_LABEL}}`
  - `{{HAUPTLEISTUNG}}`
  - `{{CAPEX_REALISTISCH_EUR}}`
  - `{{ROI_12M}}`
- **Problem:** Zeile 21-22 erwähnt "Digital Jetzt" für KMU

### 3. gamechanger.md (Problem #6: Enterprise-Sprache)
- **Pfad:** `prompts/de/gamechanger.md`
- **Zweck:** Strategischer Bruchpunkt + Transformation
- **Token-Budget:** 350-450 Wörter
- **Input-Variablen:**
  - `{{hauptleistung}}`
  - `{{ZEITERSPARNIS_PRIORITAET}}`
  - `{{KI_GUARDRAILS}}`
  - `{{VISION_3_JAHRE}}`
- **Problem:** Zeile 97-136 definiert Individualisierung, aber Begriffe wie "Auswertungs-Engine" kommen aus LLM-Output

### 4. executive_summary.md
- **Pfad:** `prompts/de/executive_summary.md`
- **Zweck:** Management Summary
- **Token-Budget:** 1500, WORD_MINIMUM: 250
- **Struktur:**
  1. Profil-Satz (1 Satz, max 25 Wörter)
  2. Drei Entscheidungen (Bullet-Liste)
  3. Konkreter nächster Schritt
  4. "Wenn Sie nur eines tun:" Takeaway

---

## Vollständige Prompt-Liste

| Datei | Zweck | Token-Budget | Persona-aware |
|-------|-------|--------------|---------------|
| executive_summary.md | Management Summary | 1500 | ✓ |
| executive_decision.md | Entscheidungsblock | - | ✓ |
| recommendations.md | Handlungsempfehlungen | 600 | ✓ |
| top_3_massnahmen.md | Top-3 für Seite 2 | - | ✓ |
| foerderpotenzial.md | Förderprogramme | 3200 | ✓ |
| foerderprogramme.md | Förderliste | - | ✓ |
| gamechanger.md | Strategischer Bruchpunkt | 350-450 | ✓ |
| gamechanger_decision.md | Gamechanger kurz | - | ✓ |
| risks.md | Risikomatrix | 800+ | ✓ |
| risk_engine_v2.md | Risiko-Engine | - | ✓ |
| risk_engine_v3.md | Risiko-Engine v3 | - | ✓ |
| roadmap_90d.md | 90-Tage-Roadmap | 1000+ Zeichen | ✓ |
| roadmap_90d_decision.md | Roadmap kurz | - | ✓ |
| roadmap_12m.md | 12-Monats-Roadmap | 500-700 | ✓ |
| business_case.md | Business Case | - | ✓ |
| business_case_engine_v2.md | Business Case v2 | - | ✓ |
| business_case_simulation.md | ROI-Simulation | - | ✓ |
| costs_overview.md | Kostenübersicht | - | ✓ |
| quick_wins.md | Quick Wins | - | ✓ |
| tools_empfehlungen.md | Tool-Empfehlungen | - | ✓ |
| tools_engine_v4.md | Tool-Engine | - | ✓ |
| ki_stack_summary.md | KI-Stack | - | ✓ |
| ki_aktivitaeten_ziele.md | KI-Aktivitäten | - | ✓ |
| ki_skillplan.md | Skill-Plan | - | ✓ |
| strategie_governance.md | Governance | - | ✓ |
| org_change.md | Org-Wandel | - | ✓ |
| data_readiness.md | Datenreife | - | ✓ |
| wettbewerb_benchmark.md | Benchmarks | - | ✓ |
| benchmark_engine.md | Benchmark-Engine | - | ✓ |
| branch_deep_dive.md | Branchen-Tiefenanalyse | - | ✓ |
| unternehmensprofil_markt.md | Unternehmensprofil | 500+ | ✓ |
| ai_act_summary.md | EU AI Act | - | ✓ |
| ai_policy_mini.md | AI Policy | - | ✓ |
| automation_roadmap_engine.md | Automatisierung | - | ✓ |
| vendor_audit_engine.md | Vendor Audit | - | ✓ |
| next_actions.md | Nächste Schritte | - | ✓ |
| monetarisierung.md | Monetarisierung | - | - |
| roi_tracking.md | ROI Tracking | - | - |
| transparency_box.md | Transparenz | - | - |
| templates_start.md | Templates | - | - |
| prompt_framework.md | Prompt-Framework | - | - |
| kickoff_vorlage.md | Kickoff-Vorlage | - | - |
| exec_snapshot.md | Exec Snapshot | - | - |
| funding_engine_v2.md | Funding Engine | - | - |

---

## Inline-Prompts in gpt_analyze.py

Zusätzlich zu den Markdown-Dateien existieren hardcodierte Prompts in `gpt_analyze.py`:

| Zeile | Zweck |
|-------|-------|
| 7715-7765 | Quick-Win Templates mit "[X]-[Y] h/Monat" Platzhaltern |
| 7816-7820 | Fallback-Prompts für recommendations, risks, etc. |
| 5350+ | Förderpotenzial-Fallback HTML |
| 5770+ | Recommendations-Fallback HTML |

---

## Variablen-Mapping

### Aus Briefing
```python
{{hauptleistung}}              # Freitext: Was bietet der User an?
{{ZEITERSPARNIS_PRIORITAET}}   # Wo verliert der User Zeit?
{{KI_GUARDRAILS}}              # Einschränkungen für KI
{{VISION_3_JAHRE}}             # Langfristige Vision
{{unternehmensgroesse}}        # solo/team/kmu
{{branche}}                    # Branchenkategorie
{{bundesland}}                 # Standort
{{investitionsbudget}}         # Budget-Range
```

### Berechnet
```python
{{CAPEX_REALISTISCH_EUR}}      # Aus extra_sections.py
{{OPEX_REALISTISCH_EUR}}       # Aus extra_sections.py
{{EINSPARUNG_MONAT_EUR}}       # Aus roi_calculator.py
{{ROI_12M}}                    # Aus roi_calculator.py (Problem #3!)
{{PAYBACK_MONTHS}}             # Aus roi_calculator.py
```

### Generiert
```python
{{BRANCH_CORE_LABEL}}          # LLM-generiert aus Branche
{{BRANCH_CONTEXT_LABEL}}       # LLM-generiert, kürzer
{{OFFERING_LABEL}}             # LLM-generiert aus hauptleistung
```
