# Vollständiges Field-Audit — Alle Fragebogen-Felder

**Datum:** 2026-03-22
**Schema-Version:** 1.7.0
**Scope:** api-ki-backend-neu (Backend), formbuilder_de_SINGLE_FULL.js (Frontend-Referenz)
**Methode:** Systematischer Grep über alle .py, .js, .json, .md, .j2, .html Dateien

---

## Legende — Feldtyp-Klassifizierung

| Typ | Bedeutung | Beschreibung |
|-----|-----------|-------------|
| **A** | Kernfeld | Fließt in Scoring + Prompts + wird persistiert |
| **B** | Prompt-only | Fließt in Prompts aber nicht direkt in Scoring |
| **C** | Display-only | Wird nur in Profile-Box / Zusammenfassung angezeigt |
| **D** | Unused | Im Frontend vorhanden, Backend ignoriert es weitgehend |
| **E** | Strategy-only | Nur in Strategy-Pipeline verwendet |

---

## Übersichtsmatrix — Hauptfragebogen (50 Felder)

### Block 1 — Firmendaten & Branche

| # | Field Key | FE-Typ | Scoring | Prompt-Var | Profile-Box | Coverage-Guard | Normalizer | Context-Adapter | Tests | Typ |
|---|-----------|--------|---------|------------|-------------|----------------|------------|-----------------|-------|-----|
| 1 | `branche` | select | Indirekt (Stundensatz, Branchen-Logik) | `{BRANCHE_LABEL}`, `{BRANCHE}`, `{branche}` | ✅ (als BRANCHE_LABEL) | ✅ | ✅ (BRANCHE_MAP) | ✅ L47,52 | 19 Profile | **A** |
| 2 | `unternehmensgroesse` | select | ✅ (Size-Logik L1471,1911,1937) | `{UNTERNEHMENSGROESSE_LABEL}`, `{COMPANY_SIZE}` | ✅ (als UG_LABEL) | ✅ | ✅ (UG_MAP) | ✅ L48,53 | 19 Profile | **A** |
| 3 | `selbststaendig` | select | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 0 | **D** |
| 4 | `bundesland` | select | Indirekt (BAFA-Förderquote) | `{BUNDESLAND_LABEL}`, `{BUNDESLAND}` | ✅ (als BL_LABEL) | ✅ | ✅ (BL_LABELS) | ✅ L49,54 | 19 Profile | **A** |
| 5 | `country` | select | Indirekt (Compliance-Pfad EN/DE) | ❌ direkt | ❌ | ❌ | ❌ | ❌ | 7 Profile | **B** |
| 6 | `hauptleistung` | textarea | Indirekt (Freetext-Injection L1203) | `{HAUPTLEISTUNG}`, `{OFFERING_LABEL}` | ✅ | ✅ | ✅ (_shorten) | ✅ L57 | 19 Profile | **A** |
| 7 | `zielgruppen` | checkbox | ❌ | `{ZIELGRUPPEN}` (via context_adapter) | ✅ | ❌ | ❌ | ✅ L72 | 0 in gold | **B** |
| 8 | `jahresumsatz` | select | Indirekt (Stundensatz L9216) | `{JAHRESUMSATZ_LABEL}` | ✅ | ✅ | ✅ (UMSATZ_LABELS) | ❌ | 19 Profile | **B** |
| 9 | `it_infrastruktur` | select | ✅ (evaluators/compliance.py: hosting 15%) | `{IT_INFRASTRUKTUR_LABEL}` (base_vars L9379) | ✅ | ❌ | ✅ (IT_LABELS) | ❌ | 0 | **A** |
| 10 | `interne_ki_kompetenzen` | select | ❌ | `{INTERNE_KI_KOMPETENZEN_LABEL}` | ✅ | ❌ | ❌ | ❌ | 0 | **B** |
| 11 | `datenquellen` | checkbox | ❌ | `{DATENQUELLEN_LABELS}` (base_vars L9138,9373) | ✅ | ❌ | ❌ | ✅ L73 | 0 | **B** |

### Block 2 — Status Quo

| # | Field Key | FE-Typ | Scoring | Prompt-Var | Profile-Box | Coverage-Guard | Typ |
|---|-----------|--------|---------|------------|-------------|----------------|-----|
| 12 | `digitalisierungsgrad` | slider | ✅ (L1753: Digi-Score Bonus) | `{DIGITALISIERUNGSGRAD}` (L9153) | ✅ | ❌ | **A** |
| 13 | `prozesse_papierlos` | select | ✅ (evaluators/efficiency.py: digital 25%) | `{PROZESSE_PAPIERLOS_LABEL}` (L9141,9375) | ✅ | ❌ | **A** |
| 14 | `automatisierungsgrad` | select | ✅ (evaluators/efficiency.py: auto_potential 30%) | `{AUTOMATISIERUNGSGRAD_LABEL}` (L9371) | ✅ | ❌ | **A** |
| 15 | `ki_einsatz` | checkbox | ✅ (L1890: Reifegrad-Logik) | ❌ direkt | ✅ | ❌ | **A** |
| 16 | `ki_kompetenz` | select | ✅ (L1735: ai_skills→Enablement) | `{KI_KNOWHOW}` (L9082), `{ki_kompetenz}` | ✅ | ✅ | **A** |

### Block 3 — Ziele & Use Cases

| # | Field Key | FE-Typ | Scoring | Prompt-Var | Profile-Box | Coverage-Guard | Typ |
|---|-----------|--------|---------|------------|-------------|----------------|-----|
| 17 | `ki_ziele` | checkbox | ✅ (L1691,1712: goals) | `{KI_ZIELE_LABELS}`, `{PROJEKTZIEL}` | ✅ | ✅ | **A** |
| 18 | `ki_projekte` | textarea | ✅ (L1733: pilot_planned) | `{KI_PROJEKTE}` (L9065,9098) | ✅ | ✅ | **A** |
| 19 | `anwendungsfaelle` | checkbox | ✅ (L1713: use_cases) | `{ki_usecases}` (context_adapter L79) | ✅ | ✅ | **A** |
| 20 | `zeitersparnis_prioritaet` | textarea | Indirekt (Freetext L1213) | `{ZEITERSPARNIS_PRIORITAET}` (L9059,9086) | ✅ | ❌ | **A** |
| 21 | `pilot_bereich` | select | ✅ (L1733: pilot_planned) | ❌ direkt | ✅ | ✅ | **A** |
| 22 | `geschaeftsmodell_evolution` | textarea | Indirekt (Freetext L1223) | `{GESCHAEFTSMODELL_EVOLUTION}` (L9061,9090) | ✅ | ❌ | **B** |
| 23 | `vision_3_jahre` | textarea | ✅ (L1690: maturity_level) | `{VISION_3_JAHRE}` (L9088), ⚠️ `{VISION_PRIORITAET}` Alias! | ✅ | ✅ | **A** |

### Block 4 — Strategie & Governance

| # | Field Key | FE-Typ | Scoring | Prompt-Var | Profile-Box | Coverage-Guard | Typ |
|---|-----------|--------|---------|------------|-------------|----------------|-----|
| 24 | `strategische_ziele` | textarea | ✅ (L1208,1732: goals) | `{STRATEGISCHE_ZIELE}` (L9063,9094), `{PROJEKTZIEL}` | ✅ | ❌ (⚠️ fehlt!) | **A** |
| 25 | `ki_guardrails` | textarea | ❌ (nur Freetext L1234) | `{KI_GUARDRAILS}` (L9062,9092) | ❌ | ❌ | **B** |
| 26 | `massnahmen_komplexitaet` | select | ✅ (L1762: direkt mapped) | `{MASSNAHMEN_KOMPLEXITAET}` (L9159) | ✅ | ❌ | **A** |
| 27 | `roadmap_vorhanden` | select | ✅ (L1687: maturity +8/+4) | ❌ direkt | ✅ | ❌ | **A** |
| 28 | `governance_richtlinien` | select | ✅ (L1696: governance +8/+4) | `{GOVERNANCE_RICHTLINIEN_LABEL}` | ✅ | ✅ | **A** |
| 29 | `change_management` | select | ✅ (L1737: change_mgmt) | `{CHANGE_MANAGEMENT_LABEL}` | ✅ | ✅ | **A** |

### Block 5 — Ressourcen & Präferenzen

| # | Field Key | FE-Typ | Scoring | Prompt-Var | Profile-Box | Coverage-Guard | Typ |
|---|-----------|--------|---------|------------|-------------|----------------|-----|
| 30 | `zeitbudget` | select | ✅ (L1736: training_budget) | `{ZEITBUDGET}` (L9132, ctx_adapter L59) | ✅ | ✅ | **A** |
| 31 | `vorhandene_tools` | checkbox | ❌ | `{VORHANDENE_TOOLS_LABELS}` (L9381,9385) | ✅ | ❌ | **B** |
| 32 | `regulierte_branche` | checkbox | ❌ | `{REGULIERTE_BRANCHE_LABELS}` (L9377) | ✅ | ❌ | **B** |
| 33 | `trainings_interessen` | checkbox | ✅ (L1724: security_training) | `{TRAININGS_INTERESSEN}` (L9147, ctx_adapter L71) | ✅ | ✅ | **A** |
| 34 | `vision_prioritaet` | select | ✅ (L1730: roi_expected→Value) | `{VISION_PRIORITAET}` (ctx_adapter L58, ⚠️ gpt_analyze maps to vision_3_jahre!) | ✅ | ✅ | **A** |

### Block 6 — Rechtliches & Compliance

| # | Field Key | FE-Typ | Scoring | Prompt-Var | Profile-Box | Coverage-Guard | Typ |
|---|-----------|--------|---------|------------|-------------|----------------|-----|
| 35 | `datenschutzbeauftragter` | select | ✅ (L1716,1967: gdpr_aware) | `{DATENSCHUTZBEAUFTRAGTER_LABEL}` (ctx_adapter L64) | ✅ | ✅ | **A** |
| 36 | `technische_massnahmen` | select | ✅ (L1717: data_protection) | `{DATENSCHUTZ}` Alias (ctx_adapter L62) | ✅ | ✅ | **A** |
| 37 | `folgenabschaetzung` | select | ✅ (L1723: risk_assessment) | `{FOLGENABSCHAETZUNG_LABEL}` | ✅ | ✅ | **A** |
| 38 | `meldewege` | select | ✅ (L1748: _sec_meldewege_bonus) | `{MELDEWEGE}` (L9156) | ✅ | ❌ | **A** |
| 39 | `loeschregeln` | select | ✅ (evaluators/compliance.py: retention 15%) | `{LOESCHREGELN}` (L9140, ctx_adapter L66-67) | ✅ | ❌ | **A** |
| 40 | `ai_act_kenntnis` | select | ✅ (L1744: _gov_ai_act_bonus) | `{AI_ACT_KENNTNIS}` (L9154, ctx_adapter L65) | ✅ | ❌ | **A** |
| 41 | `ki_hemmnisse` | checkbox | ❌ | `{KI_HEMMNISSE_LABELS}` (L9054,9083, ctx_adapter L70) | ✅ | ❌ | **B** |

### Block 7 — Förderung & Investition

| # | Field Key | FE-Typ | Scoring | Prompt-Var | Profile-Box | Coverage-Guard | Typ |
|---|-----------|--------|---------|------------|-------------|----------------|-----|
| 42 | `bisherige_foerdermittel` | select | ✅ (L1760: direkt mapped) | `{BISHERIGE_FOERDERMITTEL}` (L9157) | ✅ | ❌ | **A** |
| 43 | `interesse_foerderung` | select | ❌ | ❌ direkt | ✅ | ❌ | **C** |
| 44 | `erfahrung_beratung` | select | ✅ (L1761: direkt mapped) | `{ERFAHRUNG_BERATUNG}` (L9158) | ✅ | ❌ | **A** |
| 45 | `investitionsbudget` | select | ✅ (L1711: budget→Value) | `{INVESTITIONSBUDGET}` (L9038,9131) | ✅ | ✅ | **A** |
| 46 | `marktposition` | select | ❌ | ❌ direkt | ✅ | ❌ | **C** |
| 47 | `benchmark_wettbewerb` | select | ❌ | ❌ direkt | ✅ | ❌ | **C** |
| 48 | `innovationsprozess` | select | ✅ (L1739: innovation_culture) | ❌ direkt (indirekt via Score) | ✅ | ✅ | **A** |
| 49 | `risikofreude` | slider | ✅ (L1759: direkt mapped) | `{RISIKOFREUDE}` (L9155) | ✅ | ❌ | **A** |

### Block 8 — Datenschutz

| # | Field Key | FE-Typ | Scoring | Prompt-Var | Profile-Box | Coverage-Guard | Typ |
|---|-----------|--------|---------|------------|-------------|----------------|-----|
| 50 | `datenschutz` | privacy | ✅ (L1716: gdpr_aware) | ❌ | ❌ | ✅ | **A** |

---

## Strategy-Felder (S1–S10)

| # | Field Key | FE-Typ | Strategy-Pipeline | Prompt-Var | Typ |
|---|-----------|--------|-------------------|------------|-----|
| 51 | `s1_budget` | radio | ✅ (L275) | Ja (Strategy-Prompts) | **E** |
| 52 | `s2_zeitrahmen` | radio | ✅ (L276) | Ja | **E** |
| 53 | `s3_prioritaeten` | checkbox | ✅ (L277, join(",")) | Ja | **E** |
| 54 | `s4_engpass` | radio | ✅ (L278) | Ja | **E** |
| 55 | `s5_tools` | checkbox | ❌ (nicht in Pipeline!) | ❌ | **D** |
| 56 | `s5_tools_other` | text | ❌ | ❌ | **D** |
| 57 | `s5_vision` | textarea | ❌ | ❌ | **D** |
| 58 | `s5_software` | — | ✅ (L279) | Ja | **E** |
| 59 | `s6_foerderinteresse` | radio | ✅ (L280) | Ja | **E** |
| 60 | `s7_entscheidung` | radio | ✅ (L281) | Ja | **E** |
| 61 | `s8_erfahrung` | radio | ✅ (L282) | Ja | **E** |
| 62 | `s9_ansatz` | radio | ✅ (L283) | Ja | **E** |
| 63 | `s10_datenschutz` | radio | ✅ (L284) | Ja | **E** |

---

## Typ-Zusammenfassung

| Typ | Anzahl | Felder |
|-----|--------|--------|
| **A — Kernfeld** | 37 | branche, unternehmensgroesse, bundesland, hauptleistung, digitalisierungsgrad, **prozesse_papierlos**, **automatisierungsgrad**, ki_einsatz, ki_kompetenz, ki_ziele, ki_projekte, anwendungsfaelle, zeitersparnis_prioritaet, pilot_bereich, vision_3_jahre, strategische_ziele, massnahmen_komplexitaet, roadmap_vorhanden, governance_richtlinien, change_management, zeitbudget, trainings_interessen, vision_prioritaet, datenschutzbeauftragter, technische_massnahmen, folgenabschaetzung, meldewege, **loeschregeln**, ai_act_kenntnis, bisherige_foerdermittel, erfahrung_beratung, investitionsbudget, innovationsprozess, risikofreude, datenschutz, **it_infrastruktur** |
| **B — Prompt-only** | 7 | country, zielgruppen, jahresumsatz, interne_ki_kompetenzen, datenquellen, geschaeftsmodell_evolution, vorhandene_tools, regulierte_branche, ki_hemmnisse, ki_guardrails |
| **C — Display-only** | 3 | interesse_foerderung, marktposition, benchmark_wettbewerb |
| **D — Unused** | 5 | **selbststaendig**, **s5_tools**, **s5_tools_other**, **s5_vision**, (**country** teilweise) |
| **E — Strategy-only** | 9 | s1_budget, s2_zeitrahmen, s3_prioritaeten, s4_engpass, s5_software, s6_foerderinteresse, s7_entscheidung, s8_erfahrung, s9_ansatz, s10_datenschutz |

---

## Anomalien & Risiken

### 1. Namenskollision: VISION_PRIORITAET

| Stelle | Was passiert |
|--------|-------------|
| `context_adapter.js:58` | `ctx.VISION_PRIORITAET = form.vision_prioritaet \|\| ""` — korrekt, mappt Formularwert |
| `gpt_analyze.py:9080` | `"VISION_PRIORITAET": vision_3_jahre` — **ÜBERSCHREIBT** mit vision_3_jahre! |

**Ergebnis:** In Prompt-Templates ist `{VISION_PRIORITAET}` = Inhalt von `vision_3_jahre` (Freetext), NICHT das Select-Feld `vision_prioritaet`. Das Select-Feld wirkt nur über den Score. Der context_adapter-Wert wird vom Python-Backend überschrieben.

### 2. Typ-Mismatches (Frontend sendet Array, Backend erwartet ggf. String)

| Feld | FE sendet | Backend erwartet | Risiko |
|------|-----------|------------------|--------|
| `zielgruppen` | Array | context_adapter: `joinArr()` → OK | Niedrig |
| `datenquellen` | Array | context_adapter: `joinArr()` → OK | Niedrig |
| `ki_einsatz` | Array | gpt_analyze: `_safe_lower()` auf String-Ergebnis → **potentiell falsch** bei Array | Mittel |
| `ki_ziele` | Array | gpt_analyze: `", ".join()` → OK, explizit Array | Niedrig |
| `anwendungsfaelle` | Array | gpt_analyze: List-Handling → OK | Niedrig |
| `ki_hemmnisse` | Array | gpt_analyze: `isinstance(list)` check → OK | Niedrig |
| `trainings_interessen` | Array | gpt_analyze: `len()` check → OK | Niedrig |
| `vorhandene_tools` | Array | Nur Prompt+ProfileBox, `_fmt()` handles lists → OK | Niedrig |
| `regulierte_branche` | Array | Nur Prompt+ProfileBox → OK | Niedrig |

**Einziges echtes Risiko:** `ki_einsatz` in Zeile 1890 — `_safe_lower(answers.get("ki_einsatz", ""))` — wenn Array kommt, wird `str(["chatbots", "marketing"])` zu einem String konvertiert, was unschön aber funktional ist (substring-match in der Reifegrad-Logik).

### 3. Tote Felder (im Frontend, Backend ignoriert)

| Feld | Frontend-Block | Backend-Nutzung |
|------|----------------|-----------------|
| **`selbststaendig`** | Block 1 (showIf: solo) | Nirgendwo gelesen, nicht in Scoring, nicht in Prompts, nicht in Profile-Box |
| **`s5_tools`** | Strategy-Form | Nicht in strategy_pipeline.py (stattdessen `s5_software`) |
| **`s5_tools_other`** | Strategy-Form | Nicht in strategy_pipeline.py |
| **`s5_vision`** | Strategy-Form | Nicht in strategy_pipeline.py |

### 4. Fehlende Fallbacks / Defaults

| Feld | Problem |
|------|---------|
| `hauptleistung` | Wird auf 77 Zeichen truncated (L8886), aber kein Fallback-Label wenn leer — Profile-Box zeigt leere Zelle |
| `jahresumsatz` | Bei "keine_angabe" wird Stundensatz-Ableitung auf Branch-Default zurückgefallen → OK |
| `country` | Default "DE" in Frontend-Submit, aber Backend hat keinen expliziten Default |
| `ki_hemmnisse` | Fallback auf Legacy-Key "hemmnisse" (L9056) — Altdaten-Kompatibilität |

### 5. Inkonsistente Benennung

| Variation 1 | Variation 2 | Kontext |
|-------------|-------------|---------|
| `ki_kompetenz` | `KI_KNOWHOW` | context_adapter & Prompts verwenden KI_KNOWHOW als Alias für ki_kompetenz |
| `strategische_ziele` | `PROJEKTZIEL` | PROJEKTZIEL = ki_ziele ∥ strategische_ziele (Fallback-Kette) |
| `technische_massnahmen` | `DATENSCHUTZ` | context_adapter mappt technische_massnahmen auf DATENSCHUTZ (irreführend!) |
| `vision_prioritaet` | `VISION_PRIORITAET` | In gpt_analyze.py mappt VISION_PRIORITAET auf vision_3_jahre (Kollision!) |
| `loeschregeln` | `LOECHREGELN` | Tippfehler-Variante in context_adapter L66 (beide Versionen vorhanden) |

### 6. Coverage-Guard Lücken

Felder die im Scoring benutzt werden, aber NICHT im Coverage-Guard (`EXPECTED_FIELDS`) stehen:

| Feld | Scoring-Nutzung |
|------|-----------------|
| `roadmap_vorhanden` | maturity_level (+8/+4) |
| `change_management` | enablement_score |
| `innovationsprozess` | innovation_culture |
| `meldewege` | _sec_meldewege_bonus |
| `ai_act_kenntnis` | _gov_ai_act_bonus |
| `digitalisierungsgrad` | Digi-Score Bonus |
| `risikofreude` | Direkt mapped |
| `bisherige_foerdermittel` | Direkt mapped |
| `massnahmen_komplexitaet` | Direkt mapped |

### 7. Strategy-Felder: `s5_tools` vs. `s5_software` Diskrepanz

Das Frontend-Formular (strategy.html) definiert `s5_tools`, aber die `strategy_pipeline.py` liest `s5_software` (L279). Die Felder `s5_tools`, `s5_tools_other` und `s5_vision` werden im Strategy-Submit gesendet, aber nie verarbeitet.

---

## Evaluator-Module (services/evaluators/)

Neben der Scoring-Pipeline in `gpt_analyze.py` gibt es **dedizierte Evaluator-Module** mit eigener Scoring-Logik:

### services/evaluators/efficiency.py

| Dimension | Gewicht | Feld | Zugriff |
|-----------|---------|------|---------|
| `digital` | 25% | `prozesse_papierlos`, `digitalisierungsgrad` | `a.get('prozesse_papierlos')`, `a.get('digitalisierungsgrad')` |
| `zeitbudget` | 25% | `zeitbudget` | `a.get('zeitbudget')` |
| `auto_potential` | 30% | `automatisierungsgrad` | `a.get('automatisierungsgrad')` |
| `skills` | 20% | `ki_kompetenz` | `a.get('ki_kompetenz')` |

**Bedeutung:** `automatisierungsgrad` und `prozesse_papierlos` sind DOCH Scoring-relevant (nicht nur Prompt-only)! Sie fließen über den Efficiency-Evaluator in den Gesamtscore. Korrekte Klassifizierung: **Typ A**.

### services/evaluators/innovation.py

| Dimension | Gewicht | Feld | Zugriff |
|-----------|---------|------|---------|
| `vision` | 35% | `vision_3_jahre`, `roadmap_vorhanden` | `a.get('vision_3_jahre')`, `a.get('roadmap_vorhanden')` |
| `culture` | 25% | `innovationsprozess` | `a.get('innovationsprozess')` |
| `use_case_novelty` | 25% | `anwendungsfaelle` | `a.get('anwendungsfaelle', [])` — erwartet Array, nutzt `len()` |
| `experimentation` | 15% | `pilot_bereich`, `ki_projekte` | `a.get('pilot_bereich')`, `a.get('ki_projekte')` |

### services/evaluators/compliance.py

| Dimension | Gewicht | Feld | Zugriff |
|-----------|---------|------|---------|
| `gdpr_awareness` | 25% | `datenschutz`, `datenschutzbeauftragter` | `a.get('datenschutz')`, `a.get('datenschutzbeauftragter')` |
| `technical_measures` | 25% | `technische_massnahmen` | `a.get('technische_massnahmen')` |
| `dpia` | 20% | `folgenabschaetzung` | `a.get('folgenabschaetzung')` |
| `retention` | 15% | `loeschregeln` | `a.get('loeschregeln')` |
| `hosting` | 15% | `it_infrastruktur` | `a.get('it_infrastruktur')` |

### Korrektur der Typ-Klassifizierung

Durch die Evaluator-Module werden folgende Felder von **Typ B** zu **Typ A** hochgestuft:

| Feld | Alter Typ | Neuer Typ | Grund |
|------|-----------|-----------|-------|
| `prozesse_papierlos` | B (Prompt-only) | **A** (Kern) | efficiency.py: digital dimension (25%) |
| `automatisierungsgrad` | B (Prompt-only) | **A** (Kern) | efficiency.py: auto_potential (30%) |
| `it_infrastruktur` | B (Prompt-only) | **A** (Kern) | compliance.py: hosting dimension (15%) |
| `loeschregeln` | B (Prompt-only) | **A** (Kern) | compliance.py: retention dimension (15%) |

---

## Feld-Flussdiagramm (vereinfacht)

```
Frontend (formbuilder)
  → POST /briefings/submit  {answers: {...}}
    → models.py: Briefing.answers (JSON column)  ← ALLE Felder persistiert
      → answers_normalizer.py: branche/size/bundesland normalisiert + Labels
        → gpt_analyze.py:
            1. calculate_score(answers) → Scoring-Pipeline (28 Felder)
            2. base_vars = {...} → Prompt-Template-Variablen (40+ Variablen)
            3. profile_box.build_profile_box(answers) → HTML für PDF (46 Felder)
            4. coverage_guard.analyze_coverage(answers) → Qualitäts-Check (23 Felder)
        → context_adapter.js: buildContext(form) → Legacy Prompt-Context (15 Mappings)
```

---

## Summary

| Kategorie | Anzahl |
|-----------|--------|
| Gesamtzahl Felder (Hauptfragebogen) | **50** |
| Gesamtzahl Felder (Strategy) | **13** |
| Typ A (Kern — Scoring + Prompts) | **37** |
| Typ B (Prompt-only) | **7** |
| Typ C (Display-only) | **3** |
| Typ D (Unused) — ⚠️ | **5** (`selbststaendig`, `s5_tools`, `s5_tools_other`, `s5_vision`, `country` teilweise) |
| Typ E (Strategy-only) | **9** |
| Anomalien gefunden | **7** |
| Kritische Risiken | **2** (VISION_PRIORITAET Namenskollision, s5_tools/s5_software Diskrepanz) |

### Handlungsempfehlung (nach Priorität)

1. **VISION_PRIORITAET Namenskollision auflösen** — `gpt_analyze.py:9080` sollte `vision_3_jahre` unter eigenem Variablennamen `VISION_3_JAHRE` führen (tut es bereits in L9088!), die Zeile mit `VISION_PRIORITAET` sollte den tatsächlichen `vision_prioritaet`-Wert tragen
2. **`selbststaendig` Feld anbinden** — wird im Frontend abgefragt (bei Solo), aber Backend nutzt es nirgends → entweder in Profile-Box / Compliance aufnehmen oder aus Frontend entfernen
3. **Strategy `s5_tools` → `s5_software` Alignment** — Frontend und Backend verwenden unterschiedliche Keys
4. **Coverage-Guard ergänzen** — 9 Scoring-relevante Felder fehlen in EXPECTED_FIELDS
5. **`DATENSCHUTZ` Alias klären** — `technische_massnahmen` wird als `DATENSCHUTZ` in context_adapter gemappt, was irreführend ist
6. **`LOECHREGELN` Tippfehler** — context_adapter L66 hat `LOECHREGELN` statt `LOESCHREGELN` (auch wenn L67 die korrekte Version hat)
