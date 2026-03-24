# Deutschsprachiges Prompt-Inventar

> **Stand:** 2026-03-24 | **Manifest-Version:** 5.5 (Sprint N3.1) | **Nur Inventar — keine Bewertung/Optimierung**

---

## 1. Report 1 (R1) — KI-Readiness-Report

Prompts in `prompts/de/`, geladen via `load_prompt()` in `gpt_analyze.py`.

| # | Datei (Pfad) | Report | Kapitel/Phase | Zweck (1 Satz) | Injizierte Variablen | Länge (ca. Zeichen) |
|---|---|---|---|---|---|---|
| 1 | `prompts/de/executive_summary.md` | R1 | Executive Summary | CEO-taugliche Zusammenfassung des KI-Readiness-Status | `BRANCH_CONTEXT_LABEL, HAUPTUMSATZTREIBER, KI_GUARDRAILS, OFFERING_LABEL, STRATEGISCHE_ZIELE, ZEITERSPARNIS_PRIORITAET, hauptleistung` | 19.372 |
| 2 | `prompts/de/executive_decision.md` | R1 | Executive Decision | Entscheidungsblock Tun/Lassen/Stop-Signal | `BRANCH_CONTEXT_LABEL, COMPANY_SIZE` | 4.539 |
| 3 | `prompts/de/quick_wins.md` | R1 | Quick Wins | Sofortmaßnahmen nach Kategorie | `BRANCHE_LABEL, UNTERNEHMENSGROESSE_LABEL, hauptleistung, ki_guardrails, score_governance, score_security` | 5.360 |
| 4 | `prompts/de/roadmap_90d.md` | R1 | 90-Tage-Roadmap | 4-Phasen-Plan mit Meilensteinen | `BRANCH_CONTEXT_LABEL, BRANCH_CORE_LABEL, HAUPTUMSATZTREIBER, KI_GUARDRAILS, OFFERING_LABEL, VISION_3_JAHRE, ZEITERSPARNIS_PRIORITAET, hauptleistung, ki_projekte` | 36.768 |
| 5 | `prompts/de/roadmap_90d_decision.md` | R1 | 90-Tage-Roadmap (Entscheidung) | Verdichtete Roadmap mit Stop-Regeln | `BRANCH_CONTEXT_LABEL, COMPANY_SIZE, token, variable` | 6.702 |
| 6 | `prompts/de/roadmap_12m.md` | R1 | 12-Monats-Roadmap | Langfrist-Planung (Q-Phasen/5-Dimensionen) | `BRANCH_CONTEXT_LABEL, BRANCH_CORE_LABEL, HAUPTUMSATZTREIBER, MASSNAHMEN_KOMPLEXITAET, OFFERING_LABEL` | 10.285 |
| 7 | `prompts/de/business_case.md` | R1 | Business Case | ROI, CAPEX/OPEX, Payback-Berechnung | `BRANCHE_LABEL, BUNDESLAND_LABEL, CAPEX_REALISTISCH_EUR, COMPANY_SIZE, EINSPARUNG_MONAT_EUR, OFFERING_LABEL, OPEX_REALISTISCH_EUR, PAYBACK_MONTHS, ROI_12M, ROI_CAPEX_EUR, ROI_CAPPED_PCT, ROI_JAHRESERSPARNIS_EUR, ROI_NETTONUTZEN_EUR, ROI_OPEX_JAHR_EUR, ROI_OPEX_MONAT_EUR, ROI_RAW_PCT, ROI_STUNDENSATZ_EUR, ROI_STUNDEN_MONAT, hauptleistung` | 11.747 |
| 8 | `prompts/de/costs_overview.md` | R1 | Kostenübersicht | Detaillierte Kostenaufstellung | `BRANCHE_LABEL, HAUPTLEISTUNG, UNTERNEHMENSGROESSE_LABEL` | 8.748 |
| 9 | `prompts/de/gamechanger.md` | R1 | Gamechanger | Strategische KI-Transformation | `BRANCH_CONTEXT_LABEL, COMPANY_SIZE, GESCHAEFTSMODELL_EVOLUTION, HAUPTUMSATZTREIBER, KI_GUARDRAILS, OFFERING_LABEL, VISION_3_JAHRE, WETTBEWERB, ZEITERSPARNIS_PRIORITAET, company_size, core_service, hauptleistung, industry` | 27.423 |
| 10 | `prompts/de/gamechanger_decision.md` | R1 | Gamechanger (Entscheidung) | Strategische Verdichtung des Gamechangers | `BRANCH_CONTEXT_LABEL, COMPANY_SIZE, token, variable` | 5.311 |
| 11 | `prompts/de/risks.md` | R1 | Risiken | Risiko-Matrix und Mitigationen | `BRANCH_CONTEXT_LABEL, BRANCH_CORE_LABEL, OFFERING_LABEL, score_governance, score_sicherheit` | 12.511 |
| 12 | `prompts/de/recommendations.md` | R1 | Empfehlungen | Handlungsempfehlungen | `BRANCH_CONTEXT_LABEL, BRANCH_CORE_LABEL, KI_GUARDRAILS, OFFERING_LABEL, VISION_3_JAHRE, ZEITERSPARNIS_PRIORITAET, hauptleistung` | 19.467 |
| 13 | `prompts/de/foerderpotenzial.md` | R1 | Förderpotenzial | Bundesprogramme DE | `BAFA_FOERDERQUOTE, BAFA_FOERDERUNG_DISPLAY, BAFA_MAX_FOERDERUNG, BISHERIGE_FOERDERMITTEL, BRANCHE_LABEL, BUNDESLAND_LABEL, CAPEX_REALISTISCH_EUR, COMPANY_SIZE, EINSPARUNG_MONAT_EUR, ERFAHRUNG_BERATUNG, HAUPTLEISTUNG, INTERESSE_FOERDERUNG_LABEL, OPEX_REALISTISCH_EUR, PAYBACK_MONTHS, ROI_12M, UNTERNEHMENSGROESSE_LABEL` | 14.326 |
| 14 | `prompts/de/foerderprogramme.md` | R1 | Förderprogramme (Referenz) | Programm-Übersicht (wird in foerderpotenzial injiziert) | `BRANCHE_LABEL, BUNDESLAND_LABEL, FOERDERPROGRAMME_HTML, HAUPTLEISTUNG, UNTERNEHMENSGROESSE_LABEL` | 5.911 |
| 15 | `prompts/de/tools_empfehlungen.md` | R1 | Tool-Empfehlungen | KI-Werkzeuge nach Kategorie | `BRANCH_CONTEXT_LABEL, BRANCH_CORE_LABEL, BRANCH_SHORT_LABEL, COMPANY_SIZE, OFFERING_LABEL, hauptleistung` | 13.494 |
| 16 | `prompts/de/ai_act_summary.md` | R1 | AI Act Summary | EU AI Act Relevanz | `BRANCHE_LABEL, COMPANY_SIZE, HAUPTLEISTUNG, UNTERNEHMENSGROESSE_LABEL, report_date` | 12.441 |
| 17 | `prompts/de/strategie_governance.md` | R1 | Strategie & Governance | KI-Governance-Framework | `BRANCHE_LABEL, BRANCH_SHORT_LABEL, CHANGE_MANAGEMENT_LABEL, COMPANY_SIZE, DATENSCHUTZBEAUFTRAGTER_LABEL, DATENSCHUTZ_LABEL, FOLGENABSCHAETZUNG_LABEL, GOVERNANCE_RICHTLINIEN_LABEL, INTERNE_KI_KOMPETENZEN_LABEL, LOESCHREGELN_LABEL, MELDEWEGE_LABEL, UNTERNEHMENSGROESSE_LABEL` | 9.881 |
| 18 | `prompts/de/wettbewerb_benchmark.md` | R1 | Wettbewerb & Benchmark | Wettbewerbsanalyse | `BRANCHE_LABEL, COMPANY_SIZE, RESEARCH_PROVENANCE_HTML, UNTERNEHMENSGROESSE_LABEL, report_date, score_befaehigung, score_gesamt, score_governance, score_nutzen, score_sicherheit` | 8.710 |
| 19 | `prompts/de/unternehmensprofil_markt.md` | R1 | Unternehmensprofil & Markt | Profil und Marktkontext | `BRANCHE_LABEL, BUNDESLAND_LABEL, GESCHAEFTSMODELL_EVOLUTION, HAUPTLEISTUNG, UNTERNEHMENSGROESSE_LABEL` | 10.576 |
| 20 | `prompts/de/technologie_prozesse.md` | R1 | Technologie & Prozesse | Tech-Stack und Prozessanalyse | *(keine)* | 3.829 |
| 21 | `prompts/de/data_readiness.md` | R1 | Daten-Readiness | Datenverfügbarkeit und -qualität | `AUTOMATISIERUNGSGRAD_LABEL, BRANCHE_LABEL, BRANCH_CONTEXT_LABEL, DATENQUELLEN_LABELS, HAUPTLEISTUNG, IT_INFRASTRUKTUR_LABEL, PROZESSE_PAPIERLOS_LABEL, REGULIERTE_BRANCHE_LABELS, UNTERNEHMENSGROESSE_LABEL, VORHANDENE_TOOLS_LABELS` | 8.994 |
| 22 | `prompts/de/org_change.md` | R1 | Organisatorischer Wandel | Change Management | `BRANCH_CONTEXT_LABEL, BRANCH_CORE_LABEL, KI_HEMMNISSE_LABELS, KI_ZIELE_LABELS, OFFERING_LABEL, ki_kompetenz, score_befaehigung, score_governance, score_nutzen, score_sicherheit` | 8.704 |
| 23 | `prompts/de/transparency_box.md` | R1 | Transparenz-Box | KI-Transparenzhinweise | `BRANCH_CONTEXT_LABEL, UNTERNEHMENSGROESSE_LABEL, report_date` | 2.927 |
| 24 | `prompts/de/ki_aktivitaeten_ziele.md` | R1 | KI-Aktivitäten & Ziele | Aktuelle KI-Nutzung und Ziele | `HAUPTLEISTUNG, KI_PROJEKTE, TOOLS_AKTUELL` | 3.544 |
| 25 | `prompts/de/next_actions.md` | R1 | Nächste Schritte | Priorisierte Aktionsliste | `BRANCH_CONTEXT_LABEL, COMPANY_SIZE, KI_GUARDRAILS, OFFERING_LABEL, VISION_3_JAHRE, ZEITERSPARNIS_PRIORITAET, hauptleistung` | 8.656 |
| 26 | `prompts/de/monetarisierung.md` | R1 | Monetarisierung | KI-basierte Geschäftsmodelle | `BRANCHE_LABEL, GESCHAEFTSMODELL_EVOLUTION, HAUPTLEISTUNG, INVESTITIONSBUDGET, SCORE_OVERALL, STRATEGISCHE_ZIELE, UNTERNEHMENSGROESSE_LABEL` | 3.929 |
| 27 | `prompts/de/ki_skillplan.md` | R1 | KI Skill-Plan | Team-Weiterentwicklung | `BRANCHE_LABEL, HAUPTLEISTUNG, KI_KNOWHOW, SCORE_OVERALL, TRAININGS_INTERESSEN, UNTERNEHMENSGROESSE_LABEL, VORHANDENE_TOOLS_LABELS` | 5.377 |
| 28 | `prompts/de/templates_start.md` | R1 | Templates Start | Prompt-Vorlagen Schnellstart | `BRANCHE_LABEL, HAUPTLEISTUNG, KI_GUARDRAILS, UNTERNEHMENSGROESSE_LABEL, ZEITERSPARNIS_PRIORITAET` | 3.707 |
| 29 | `prompts/de/roi_tracking.md` | R1 | ROI Tracking | Monatliche Erfolgskontrolle | `BRANCHE_LABEL, HAUPTLEISTUNG, UNTERNEHMENSGROESSE_LABEL` | 3.920 |
| 30 | `prompts/de/ai_policy_mini.md` | R1 | AI Mini-Policy | Kompakte KI-Regeln | `BRANCHE_LABEL, HAUPTLEISTUNG, UNTERNEHMENSGROESSE_LABEL` | 7.126 |
| 31 | `prompts/de/kickoff_vorlage.md` | R1 | Kickoff-Vorlage | Projektstart-Template | `BRANCHE_LABEL, HAUPTLEISTUNG, PROJEKTZIEL, UNTERNEHMENSGROESSE_LABEL, ZEITERSPARNIS_PRIORITAET` | 4.360 |
| 32 | `prompts/de/prompt_framework.md` | R1 | Prompt-Framework | 5-Schritte-Anleitung | `BRANCHE_LABEL, HAUPTLEISTUNG, UNTERNEHMENSGROESSE_LABEL` | 4.206 |
| 33 | `prompts/de/branch_deep_dive.md` | R1 | Branch Deep-Dive | Branch Deep-Dive Analyse | `BRANCH_SHORT_LABEL, hauptleistung` | 16.693 |
| 34 | `prompts/de/ki_stack_summary.md` | R1 | KI-Stack Übersicht | KI-Stack Summary Card | `BRANCH_SHORT_LABEL, PAYBACK_MONTHS, ROI_CAPPED_PCT, ROI_STUNDEN_MONAT` | 10.065 |
| 35 | `prompts/de/exec_snapshot.md` | R1 | Executive Snapshot | Kurzfassung Executive | `BRANCH_LABEL, COMPANY_NAME, EINSPARUNG_MONAT_EUR, EINSPARUNG_STUNDEN_MONAT, MATURITY_LEVEL, PAYBACK_MONTHS, ROI_12M, SIZE_LABEL` | 1.916 |
| 36 | `prompts/de/top_3_massnahmen.md` | R1 | Top-3-Maßnahmen | Die drei wichtigsten Maßnahmen | `KI_GUARDRAILS, ZEITERSPARNIS_PRIORITAET, hauptleistung` | 2.317 |
| 37 | `prompts/de/score_interpretation.md` | R1 | Score-Interpretation | Einordnung der Dimensions-Scores | `BRANCHE_LABEL, COMPANY_SIZE, hauptleistung, score_befaehigung, score_gesamt, score_governance, score_nutzen, score_sicherheit` | 1.900 |
| 38 | `prompts/de/advisor_note.md` | R1 | Persönliche Einschätzung | Wolf-Hohl-Persona: persönliche Advisor-Einschätzung | `BRANCHE_LABEL, COMPANY_SIZE, hauptleistung, score_befaehigung, score_gesamt_display, score_governance, score_nutzen, score_sicherheit` | 2.296 |

---

## 2. KPA — KI-Potenzialanalyse (Gamechanger Deep Dive)

Prompts in `prompts/de/`, geladen via `load_prompt()` in `services/gamechanger_deep_dive.py`.

| # | Datei (Pfad) | Report | Kapitel/Phase | Zweck (1 Satz) | Injizierte Variablen | Länge (ca. Zeichen) |
|---|---|---|---|---|---|---|
| 39 | `prompts/de/gc_strategic_analysis.md` | KPA | Section 1: Strategische Analyse | Strategischer Bruchpunkt-Analyse für Gamechanger Deep Dive | `BRANCHE_LABEL, COMPANY_SIZE, GAMECHANGER_HTML, HAUPTLEISTUNG, UNTERNEHMENSGROESSE_LABEL, gamechanger_decision` | 4.262 |
| 40 | `prompts/de/gc_implementation_plan.md` | KPA | Section 2: Implementierungsplan | 90-Tage Deep Dive Implementierungsplan für Gamechanger | `BRANCHE_LABEL, COMPANY_SIZE, GAMECHANGER_HTML, HAUPTLEISTUNG, RECOMMENDATIONS_HTML, UNTERNEHMENSGROESSE_LABEL, gamechanger_decision, roadmap_90d` | 3.601 |
| 41 | `prompts/de/gc_risk_assessment.md` | KPA | Section 3: Risikobewertung | Detaillierte Risikobewertung & Absicherung für Gamechanger Deep Dive | `BRANCHE_LABEL, COMPANY_SIZE, GAMECHANGER_HTML, HAUPTLEISTUNG, RISKS_HTML, UNTERNEHMENSGROESSE_LABEL, gamechanger_decision` | 3.226 |
| 42 | `prompts/de/gc_next_steps.md` | KPA | Section 4: Nächste Schritte | Konkrete nächste Schritte nach Gamechanger Deep Dive | `BRANCHE_LABEL, COMPANY_SIZE, HAUPTLEISTUNG, UNTERNEHMENSGROESSE_LABEL, gamechanger_decision, gc_implementation_plan_summary` | 2.663 |

---

## 3. Strategy — KI-Strategiebericht (Report 3)

Prompts in `prompts/strategy_prompts.py`, geladen via `STRATEGY_PROMPTS` dict in `services/strategy_pipeline.py`.

| # | Datei (Pfad) | Report | Kapitel/Phase | Zweck (1 Satz) | Injizierte Variablen | Länge (ca. Zeichen) |
|---|---|---|---|---|---|---|
| 43 | `prompts/strategy_prompts.py` → `SYSTEM_PROMPT_STRATEGY_REPORT` | Strategy | System-Prompt (alle Sections) | Globaler System-Prompt mit Stil-, Sprach-, ROI- und Vendor-Regeln | `hauptleistung, r1_roi_pct, r1_capex, vendor_audit_red_count, vendor_audit_green_count, vendor_audit_status` | ~5.200 |
| 44 | `prompts/strategy_prompts.py` → `STRATEGY_PROMPTS["S1"]` | Strategy | S1: Ausgangslage | KI-Readiness-Profil aus Report 1 zusammenfassen | `firmenname, branche, hauptleistung, segment, mitarbeiter, bundesland, readiness_score, reifegrad_label, staerken_top3, handlungsfelder_top3, potenziale_summary, s8_erfahrung, s1_budget, s2_zeitrahmen, s3_prioritaeten, s4_engpass` | ~1.900 |
| 45 | `prompts/strategy_prompts.py` → `STRATEGY_PROMPTS["S2"]` | Strategy | S2: Markt & Wettbewerb | KI-Adoption und Wettbewerbs-Benchmark der Branche | `branche, segment, bundesland, research_markt_trends, research_wettbewerb, research_branche_stats, firmenname` | ~1.700 |
| 46 | `prompts/strategy_prompts.py` → `STRATEGY_PROMPTS["S3"]` | Strategy | S3: Strategische Handlungsfelder | 3-5 Handlungsfelder nach Impact/Machbarkeit priorisieren | `firmenname, branche, hauptleistung, segment, s3_prioritaeten, s4_engpass, staerken_top3, handlungsfelder_top3, potenziale_summary, s2_trends_summary` | ~1.800 |
| 47 | `prompts/strategy_prompts.py` → `STRATEGY_PROMPTS["S4"]` | Strategy | S4: Tool-Landschaft & Empfehlungen | Konkrete KI-Tools/Plattformen pro Handlungsfeld empfehlen | `branche, hauptleistung, segment, s5_software, s8_erfahrung, s9_ansatz, s10_datenschutz, s3_handlungsfelder, research_tool_1, research_tool_2, research_integration, vendor_audit_red_count, vendor_audit_green_count, vendor_audit_status` | ~3.700 |
| 48 | `prompts/strategy_prompts.py` → `STRATEGY_PROMPTS["S5"]` | Strategy | S5: Investitionsplan & ROI | 3-Phasen-Investitionsplan mit ROI-Szenarien | `firmenname, branche, segment, s1_budget_label, budget_gesamt_jahr1, budget_phase_1, budget_phase_2, budget_phase_3, budget_software_monatlich, budget_software_jaehrlich, budget_implementierung, budget_schulung_einmalig, budget_schulung_laufend, budget_personal, zeitersparnis_stunden, stundensatz, zeitersparnis_euro, jaehrliche_ersparnis, roi_konservativ, roi_realistisch, roi_optimistisch, breakeven_konservativ, breakeven_realistisch, breakeven_optimistisch, foerder_potenzial, r1_roi_pct, r1_capex` | ~3.400 |
| 49 | `prompts/strategy_prompts.py` → `STRATEGY_PROMPTS["S6"]` | Strategy | S6: Umsetzungs-Roadmap | 12-Monats-Roadmap in 3 Phasen | `firmenname, branche, segment, s2_zeitrahmen, s4_engpass, s7_entscheidung, s3_handlungsfelder, s4_tools_summary, s5_budget_summary, budget_phase_1, budget_phase_2, budget_phase_3` | ~2.200 |
| 50 | `prompts/strategy_prompts.py` → `STRATEGY_PROMPTS["S7"]` | Strategy | S7: Fördermittel & Finanzierung | Top-5 Förderprogramme identifizieren | `firmenname, branche, segment, bundesland, s6_foerderinteresse, s1_budget, foerder_matches, research_foerdermittel, research_foerdermittel_eu, bafa_foerderquote, bafa_max_foerderung` | ~3.200 |
| 51 | `prompts/strategy_prompts.py` → `STRATEGY_PROMPTS["S8"]` | Strategy | S8: Risiken & Compliance | Risikomatrix und EU AI Act / DSGVO Compliance | `firmenname, branche, segment, s10_datenschutz, risiko_score, risiken_report1, s3_handlungsfelder, s4_tools_summary` | ~1.900 |
| 52 | `prompts/strategy_prompts.py` → `STRATEGY_PROMPTS["EXEC"]` | Strategy | Executive Summary | Prägnante Zusammenfassung (200-300 Wörter) | `firmenname, branche, hauptleistung, segment, readiness_score, reifegrad_label, anzahl_felder, top_handlungsfeld, quick_win, s1_budget_label, budget_gesamt_jahr1, budget_phase_1, budget_phase_2, budget_phase_3, zeitersparnis_euro, roi_konservativ, roi_realistisch, roi_optimistisch, breakeven_konservativ, breakeven_realistisch, breakeven_optimistisch, foerder_potenzial, s2_zeitrahmen, s5_investition_summary` | ~2.800 |
| 53 | `prompts/strategy_prompts.py` → `SECTION_TEMPLATE_NAECHSTE_SCHRITTE_SOLO` | Strategy | Nächste Schritte (Solo) | Statisches Template: 5 Schritte für Einzelunternehmer | *(keine — statisches HTML)* | ~660 |
| 54 | `prompts/strategy_prompts.py` → `SECTION_TEMPLATE_NAECHSTE_SCHRITTE_TEAM` | Strategy | Nächste Schritte (Team) | Statisches Template: 5 Schritte für Teams | *(keine — statisches HTML)* | ~660 |

---

## 4. Shared / System-Prompts (Prefix `_`)

Injiziert in andere Prompts via `prompt_loader.py` / `prompt_enhancer.py`.

| # | Datei (Pfad) | Report | Kapitel/Phase | Zweck (1 Satz) | Injizierte Variablen | Länge (ca. Zeichen) |
|---|---|---|---|---|---|---|
| 55 | `prompts/de/_hauptleistung_context.md` | R1 (shared) | System-Kontext | Branchenspezifischer Kontext für alle Prompts | `BRANCHE_LABEL, COMPANY_SIZE, KI_GUARDRAILS, OFFERING_LABEL, ZEITERSPARNIS_PRIORITAET, hauptleistung` | 1.797 |
| 56 | `prompts/de/_persona_guardrails.md` | R1 (shared) | System-Kontext | Persona-Guardrails (Solo/Team/KMU Anpassung) | `COMPANY_SIZE, hauptleistung, variable` | 5.421 |
| 57 | `prompts/de/_solo_language_rules.md` | R1 (shared) | System-Kontext | Solo-spezifische Sprachregeln (verbotene Team-Begriffe) | *(keine)* | 2.892 |

---

## 5. Engine-Prompts (nicht im Manifest registriert)

Auf Disk in `prompts/de/`, aber NICHT im `prompt_manifest.json` eingetragen. Werden von dedizierten Python-Engines in `services/` geladen.

| # | Datei (Pfad) | Report | Kapitel/Phase | Zweck (1 Satz) | Injizierte Variablen | Länge (ca. Zeichen) |
|---|---|---|---|---|---|---|
| 58 | `prompts/de/automation_roadmap_engine.md` | R1 | Engine: Automatisierungs-Roadmap | Prompt für `services/automation_roadmap_engine.py` | `branche, business_case, funding_data, hauptherausforderungen, ki_anwendung, ki_reifegrad, risk_report_v3, strategy_plan, tools_data, unternehmensgroesse` | 7.605 |
| 59 | `prompts/de/benchmark_engine.md` | R1 | Engine: Branchen-Benchmark | Prompt für `services/benchmark_engine.py` | `auto_report, branche, funding_data, hauptherausforderungen, ki_anwendung, ki_reifegrad, kpi_data, risk_report_v3, strategy_plan, tools_data, unternehmensgroesse` | 6.356 |
| 60 | `prompts/de/business_case_engine_v2.md` | R1 | Engine: Business Case v2 | Prompt für `services/business_case_engine_v2.py` | `BRANCH_DEEP_DIVE_SUMMARY, BRANCH_LABEL, BRANCH_SHORT_LABEL, BUNDESLAND, COMPANY_NAME, EINSPARUNG_MONAT_EUR, EINSPARUNG_STUNDEN_MONAT, FUNDING_SUMMARY, MATURITY_LEVEL, PAYBACK_MONTHS, RISK_SUMMARY, ROI_12M, SIZE_LABEL, STRATEGY_SUMMARY, TOOLS_SUMMARY` | 8.375 |
| 61 | `prompts/de/business_case_simulation.md` | R1 | Engine: Business Case Simulation | Monte-Carlo-Simulation Prompt für `services/business_case_simulation.py` | `AI_ACT_CONFORMITY, AI_ACT_MISSING_CONTROLS, AUTO_AVG_POTENTIAL, AUTO_PHASE_1_COUNT, AUTO_PROCESS_COUNT, AUTO_QUICK_WINS, BC_CONSERVATIVE_PAYBACK, BC_CONSERVATIVE_ROI, BC_INVESTMENT_TOTAL, BC_OPTIMISTIC_PAYBACK, BC_OPTIMISTIC_ROI, BC_REALISTIC_PAYBACK, BC_REALISTIC_ROI, BC_REALISTIC_SAVINGS, BRANCH_LABEL, BRANCH_SHORT_LABEL, BUNDESLAND, COMPANY_NAME, COMPLIANCE_STATUS, DPIA_REQUIRED, FUNDING_SUMMARY, MATURITY_LEVEL, RISK_RESIDUAL_GRADE, RISK_RESIDUAL_SCORE, SIZE_LABEL, TOOLS_SUMMARY` | 7.620 |
| 62 | `prompts/de/funding_engine_v2.md` | R1 | Engine: Förder-Engine v2 | Prompt für `services/funding_engine_v2.py` | `AI_ACT_RISK_LEVEL, BRANCH_LABEL, BUNDESLAND, MATURITY_LEVEL, SIZE_LABEL` | 2.572 |
| 63 | `prompts/de/recommendations_engine.md` | R1 | Engine: Empfehlungen-Engine | Prompt für `services/recommendations_engine.py` | `BRANCH_LABEL, BRANCH_SHORT_LABEL, BUNDESLAND, BUSINESS_CASE_SUMMARY, COMPANY_NAME, EINSPARUNG_STUNDEN_MONAT, FUNDING_SUMMARY, MATURITY_LEVEL, PAYBACK_MONTHS, RISK_SUMMARY, ROI_12M, SIZE_LABEL, STRATEGY_SUMMARY, TOOLS_SUMMARY` | 11.177 |
| 64 | `prompts/de/risk_engine_v2.md` | R1 | Engine: Risiko-Engine v2 | Prompt für `services/risk_engine_v2.py` | `BRANCH_DEEP_DIVE_SUMMARY, BRANCH_LABEL, BRANCH_SHORT_LABEL, BUNDESLAND, COMPANY_NAME, EINSPARUNG_STUNDEN_MONAT, FUNDING_SUMMARY, MATURITY_LEVEL, PAYBACK_MONTHS, ROI_12M, SIZE_LABEL, STRATEGY_SUMMARY, TOOLS_SUMMARY` | 7.376 |
| 65 | `prompts/de/risk_engine_v3.md` | R1 | Engine: Risiko-Engine v3 | Prompt für `services/risk_engine_v3.py` (DSGVO/AI Act Fokus) | `ai_act_class, automatisierte_entscheidungen, branche, datentypen, dsgvo_risk_level, ki_anwendung, unternehmensgroesse, vendor_risk_score` | 4.857 |
| 66 | `prompts/de/tools_engine_v4.md` | R1 | Engine: Tools-Engine v4 | Prompt für `services/tools_engine_v4.py` | `BRANCH_SHORT_LABEL, SIZE_LABEL, TOOL_CATEGORY, TOOL_NAME` | 2.805 |
| 67 | `prompts/de/vendor_audit_engine.md` | R1 | Engine: Vendor-Audit | Prompt für `services/vendor_audit_engine.py` | `ai_act_class, branche, dsgvo_risk_level, ki_anwendung, risk_report_v2, risk_report_v3, tools_data, unternehmensgroesse` | 5.393 |

---

## 6. Vollständigkeits-Check

### Manifest vs. Disk

| Metrik | Wert |
|---|---|
| **Manifest DE Einträge** | 42 |
| **Dateien in `prompts/de/` (ohne `_`-Prefix)** | 52 |
| **Dateien in `prompts/de/` (mit `_`-Prefix)** | 3 |
| **Strategy-Prompts in `strategy_prompts.py`** | 10 (System + S1-S8 + EXEC) + 2 statische Templates |
| **Gesamt deutschsprachige Prompt-Einheiten** | **67** |

### Im Manifest, aber NICHT auf Disk

*Keine* — alle 42 Manifest-Einträge haben eine korrespondierende `.md`-Datei.

### Auf Disk, aber NICHT im Manifest (10 Dateien)

| Datei | Grund |
|---|---|
| `automation_roadmap_engine.md` | Engine-Prompt, direkt von `services/automation_roadmap_engine.py` geladen |
| `benchmark_engine.md` | Engine-Prompt, direkt von `services/benchmark_engine.py` geladen |
| `business_case_engine_v2.md` | Engine-Prompt, direkt von `services/business_case_engine_v2.py` geladen |
| `business_case_simulation.md` | Engine-Prompt, direkt von `services/business_case_simulation.py` geladen |
| `funding_engine_v2.md` | Engine-Prompt, direkt von `services/funding_engine_v2.py` geladen |
| `recommendations_engine.md` | Engine-Prompt, direkt von `services/recommendations_engine.py` geladen |
| `risk_engine_v2.md` | Engine-Prompt, direkt von `services/risk_engine_v2.py` geladen |
| `risk_engine_v3.md` | Engine-Prompt, direkt von `services/risk_engine_v3.py` geladen |
| `tools_engine_v4.md` | Engine-Prompt, direkt von `services/tools_engine_v4.py` geladen |
| `vendor_audit_engine.md` | Engine-Prompt, direkt von `services/vendor_audit_engine.py` geladen |

> **Bewertung:** Alle 10 nicht-registrierten Dateien sind Engine-Prompts, die von dedizierten Python-Services direkt geladen werden und bewusst nicht im Manifest stehen. **Es fehlt nichts.** Die 3 `_`-Prefix-Dateien sind Shared-System-Prompts, die via Include-Mechanismus in andere Prompts injiziert werden.

### Zusammenfassung nach Report

| Report | Prompt-Dateien | davon im Manifest | davon Engine (nicht im Manifest) | davon Shared (`_`) |
|---|---|---|---|---|
| **R1 (KI-Readiness)** | 48 | 38 | 10 | — |
| **KPA (Potenzialanalyse)** | 4 | 4 | 0 | — |
| **Strategy (Strategiebericht)** | 12 | — | — | — |
| **Shared (System)** | 3 | — | — | 3 |
| **Gesamt** | **67** | **42** | **10** | **3** |

### Gesamtvolumen

| Kategorie | Zeichen (ca.) |
|---|---|
| R1 Manifest-Prompts (38 Dateien) | ~344.000 |
| KPA Prompts (4 Dateien) | ~13.750 |
| Engine-Prompts (10 Dateien) | ~64.140 |
| Shared System-Prompts (3 Dateien) | ~10.110 |
| Strategy-Prompts (`strategy_prompts.py`) | ~26.175 |
| **Gesamt** | **~458.175** |
