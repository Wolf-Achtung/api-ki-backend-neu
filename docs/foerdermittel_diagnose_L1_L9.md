# Fördermittel-Diagnose L1–L9

Stand: 23.03.2026 | Vor Implementierung der Fixes

---

## 0a. Fragebogen-Felder im Backend

| Feld | Gelesen aus Briefing | In Prompts injiziert | An Recommendation-Engine | Report-Sections |
|------|---------------------|---------------------|-------------------------|-----------------|
| `interesse_foerderung` | `gpt_analyze.py:8829` | Ja: `INTERESSE_FOERDERUNG_LABEL` | Nein | Profile box |
| `bisherige_foerdermittel` | `gpt_analyze.py:9162` | Ja: `BISHERIGE_FOERDERMITTEL` | Nein | Profile box, Scoring |
| `investitionsbudget` | `gpt_analyze.py:9041,9136` | Ja: `INVESTITIONSBUDGET` | Nur Business Case (extra_sections.py:250), NICHT Funding-Engine | Business Case, ROI |
| `bundesland` | `gpt_analyze.py:9036-9038` | Ja: `BUNDESLAND_LABEL` | Ja: `get_foerderprogramme_extended()` | Foerderprogramme, Profile |
| `country` | Briefing answers | Minimal | Ja: Funding scope filter | Indirekt via Programme |
| `erfahrung_beratung` | `gpt_analyze.py:9163` | Ja: `ERFAHRUNG_BERATUNG` | Nein | Profile box |

**Befund:** Prompt-Variablen existieren, aber die Prompt-Templates (`foerderpotenzial.md`, `foerderprogramme.md`) nutzen `INTERESSE_FOERDERUNG_LABEL`, `BISHERIGE_FOERDERMITTEL` und `ERFAHRUNG_BERATUNG` **nicht aktiv**. Sie stehen nur als Kontext zur Verfügung.

## 0b. Recommendation-Engine-Architektur

- **Route:** `routes/funding.py` → `GET /api/funding/recommend`
- **Parameter:** `region`, `bundesland` (alias), `size`, `segment` (alias), `branch`, `ai_act_risk`, `lang`, `limit`
- **FEHLT als Parameter:** `investitionsbudget`, `interesse_foerderung`, `country`
- **Daten laden:** `services/funding_recommender.py:load_funding_programs()` → liest `data/funding_programmes_core_2025.json`, normalisiert via `_normalize_program()`
- **Filter für `status`/`deadline`:** KEINER. `go_digital` wird mit Score 1.0 empfohlen obwohl `deadline=ABGELAUFEN`.
- **Filter für `investitionsbudget`:** KEINER.

## 0c. Prompt-Analyse Fördermittel

| Section | Prompt-Datei | Referenziert `interesse_foerderung`? | Referenziert `bisherige_foerdermittel`? | Referenziert `investitionsbudget`? |
|---------|-------------|--------------------------------------|----------------------------------------|----------------------------------|
| `FOERDERPOTENZIAL_HTML` | `prompts/de/foerderpotenzial.md` | Nein | Nein | Nein (nur CAPEX/OPEX) |
| `FOERDERPROGRAMME_HTML` | `prompts/de/foerderprogramme.md` | Nein | Nein | Nein |
| `FUNDING_BRANCH_ALIGNMENT_HTML` | Runtime (G19) | Nein | Nein | Nein |
| S7 Strategy | `prompts/strategy_prompts.py:365-420` | Ja: `s6_foerderinteresse` | Nein | Ja: `s1_budget` |

## 0d. go-digital Status

- In DB als `id: "go_digital"` mit `deadline: "ABGELAUFEN"`, kein `status`-Feld
- `calculate_relevance_score()` liefert **1.0** für Bayern/Solo → wird als Top-Empfehlung angezeigt
- Blacklist (`final_sanitizer.py`) entfernt go-digital aus Report-Texten, aber **nicht aus `/api/funding/recommend`**
- Im embedded `CORE_FUNDING_PROGRAMS` (Fallback) ist go-digital auskommentiert, aber die JSON-Datei hat es aktiv

---

## Zusammenfassung der 9 Lücken

| # | Lücke | Status vor Fix |
|---|-------|---------------|
| L1 | 13/16 Bundesländer ohne regionales Programm | Nur BY, BE, BW haben Programme |
| L2 | go-digital in DB obwohl abgelaufen | Score 1.0, kein Status-Filter |
| L3 | Budget nicht in Engine | `investitionsbudget` wird ignoriert |
| L4 | `interesse_foerderung=nein` ignoriert | Prompt nutzt Variable nicht |
| L5 | `bisherige_foerdermittel=ja` ohne De-minimis | Prompt nutzt Variable nicht |
| L6 | CH/UK ohne Programme | CH/GB bekommen EU-Programme (falsch) |
| L7 | Branche nicht in Engine | Branche-Alignment nur via LLM |
| L8 | `erfahrung_beratung` nicht mit BAFA verknüpft | Prompt nutzt Variable nicht |
| L9 | EU-Länder ohne nationale Programme | Nur EU-weite Programme |
