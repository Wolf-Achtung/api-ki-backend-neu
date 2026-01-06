# TRANSLATION-MAP: DE → EN Template

**Analyse-Datum:** 2026-01-06
**Projekt:** api-ki-backend-neu
**Source:** pdf_template.html (DE v5.4.3)
**Target:** pdf_template_en.html (to be generated)

---

## SUMMARY

| Kategorie | Anzahl | Status |
|-----------|--------|--------|
| ui() Calls (bereits i18n) | 62 | ✅ Keep as-is |
| ui() Keys im Template mit Default | 46 | ⚠️ Defaults übersetzen |
| ui() Keys in ui_labels.json | 13 | ✅ Already i18n |
| **HTML Texte (hardcoded)** | **~85** | 🔴 Translate |
| CSS Comments (optional) | ~50 | 🟡 Low priority |
| **TOTAL TO TRANSLATE** | **~85** | - |

---

## ✅ SAFE: UI() CALLS (bereits internationalisiert)

### UI() Keys im Template verwendet (62 Calls, 59 unique keys)

Die meisten ui() Calls haben **Default-Werte** im Template selbst:
```jinja2
{{ ui("toc_title", "So lesen Sie diesen Report") }}
```

Diese Default-Werte müssen für EN übersetzt werden.

### UI() Keys in ui_labels.json verfügbar (13 von 59):

```
company_label_colon
deep_dive_for
feedback_cta
industry_benchmark_kicker
industry_benchmark_title
industry_funding_sub
industry_funding_title
industry_optimized
industry_specific
industry_tools_sub
industry_tools_title
missing_info
recommendations
```

**Status:** Diese sind bereits 5-sprachig (de/en/fr/es/it) in ui_labels.json definiert.

### UI() Keys mit Default-Werten im Template (46 Keys - müssen übersetzt werden):

| Key | DE Default | EN Translation |
|-----|------------|----------------|
| `appendix_intro` | "Die folgenden detaillierten Analysen wurden für Solo-Reports in den Appendix verschoben, um den Kernbericht kompakt zu halten. Alle Inhalte sind vollständig und können bei Bedarf herangezogen werden." | "The following detailed analyses have been moved to the appendix for solo reports to keep the main report concise. All content is complete and can be referenced as needed." |
| `appendix_subtitle` | "Erweiterte Analysen für die Vertiefung" | "Extended analyses for deeper insights" |
| `appendix_title` | "Detailanalysen & Engines" | "Detailed Analyses & Engines" |
| `eu_funding_badge` | "EU-Förderprogramme gelistet" | "EU Funding Programs Listed" |
| `exec_continue` | "Details und Begründungen folgen ab Seite 4 – je nach Informationsbedarf." | "Details and rationale follow from page 4 – depending on your information needs." |
| `exec_decision_title` | "Entscheidung & Fokus" | "Decision & Focus" |
| `funding_eic_horizon` | "EIC Accelerator / Horizon Europe" | "EIC Accelerator / Horizon Europe" |
| `funding_fit` | "Eignung:" | "Fit:" |
| `funding_fit_high` | "Hoch – KMU-fokussiert, KI-Projekte förderfähig" | "High – SME-focused, AI projects eligible" |
| `funding_fit_medium` | "Mittel – für skalierbare KI-Innovationen" | "Medium – for scalable AI innovations" |
| `funding_go_digital` | "go-digital / ZIM" | "go-digital / ZIM" |
| `funding_next_1` | "Förderfähigkeit innerhalb 7 Tagen prüfen" | "Check eligibility within 7 days" |
| `funding_next_2` | "Projektskizze mit Partner erstellen (14 Tage)" | "Create project outline with partner (14 days)" |
| `funding_quick_paths` | "Schnellste Förderpfade für Ihr Unternehmen" | "Fastest Funding Paths for Your Business" |
| `funding_req_eu` | "EU-Rechtsform, Innovationsgrad, TRL 5+" | "EU legal entity, innovation grade, TRL 5+" |
| `funding_req_kmu` | "KMU-Status, Sitz in DE, <500 MA" | "SME status, based in EU, <500 employees" |
| `funding_requirements` | "Voraussetzungen:" | "Requirements:" |
| `gamechanger_kicker` | "Strategische Optionen" | "Strategic Options" |
| `gamechanger_title` | "Gamechanger-Analyse" | "Gamechanger Analysis" |
| `gdpr_link_text` | "Datenschutzerklärung" | "Privacy Policy" |
| `ki_stack_pill` | "Empfohlene Tools, Förderung und nächste Schritte" | "Recommended tools, funding, and next steps" |
| `ki_stack_title` | "Ihr KI-Stack auf einen Blick" | "Your AI Stack at a Glance" |
| `risk_axis_x` | "X-Achse:" | "X-Axis:" |
| `risk_axis_x_desc` | "Eintrittswahrscheinlichkeit (gering → hoch)" | "Probability of occurrence (low → high)" |
| `risk_axis_y` | "Y-Achse:" | "Y-Axis:" |
| `risk_axis_y_desc` | "Schadensausmaß bei Eintritt (gering → kritisch)" | "Impact severity if it occurs (low → critical)" |
| `risk_color_green` | "Akzeptabel – Monitoring genügt" | "Acceptable – monitoring sufficient" |
| `risk_color_red` | "Kritisch – sofort handeln" | "Critical – act immediately" |
| `risk_color_yellow` | "Beobachten – Maßnahmen planen" | "Watch – plan mitigations" |
| `risk_legend_title` | "📊 So lesen Sie die Risiko-Matrix" | "📊 How to Read the Risk Matrix" |
| `roadmap_kicker` | "90-Tage-Plan" | "90-Day Plan" |
| `roadmap_title` | "Roadmap-Entscheidung" | "Roadmap Decision" |
| `toc_group_decision` | "Entscheidungsübersicht" | "Decision Overview" |
| `toc_group_economics` | "Wirtschaft & Risiko" | "Economics & Risk" |
| `toc_group_implementation` | "Umsetzung & Tiefe" | "Implementation & Depth" |
| `toc_item_compliance` | "Risiko- & Compliance-Einordnung (AI Act / DSGVO / Vendor)" | "Risk & Compliance Assessment (AI Act / GDPR / Vendor)" |
| `toc_item_funding` | "Förderoptionen & nächste Schritte" | "Funding Options & Next Steps" |
| `toc_item_industry` | "Branchen- & Tool-Einordnung" | "Industry & Tool Assessment" |
| `toc_item_roadmap` | "Roadmap (90 Tage / 12 Monate)" | "Roadmap (90 Days / 12 Months)" |
| `toc_item_roi` | "Wirtschaftlichkeit (ROI/Payback) & Annahmen" | "Business Case (ROI/Payback) & Assumptions" |
| `toc_item_summary` | "Executive Summary & Kurzurteil" | "Executive Summary & Quick Assessment" |
| `toc_item_top3` | "Top-3 Maßnahmen & 90-Tage-Fokus" | "Top 3 Actions & 90-Day Focus" |
| `toc_note` | "Ab Seite 4: Vertiefung und Detailanalysen" | "From page 4: Detailed analysis and deep dives" |
| `toc_title` | "So lesen Sie diesen Report" | "How to Read This Report" |
| `top3_title` | "Top-3 MUSS-Maßnahmen" | "Top 3 Must-Do Actions" |

---

## 🔴 TRANSLATE: HTML TEXTE (Hardcoded)

### 1. PAGE 1: Title & Headers (P0 - Critical)

| Zeile | DE Text | EN Translation | Context |
|-------|---------|----------------|---------|
| 5779 | `KI-Status-Report` | `AI Status Report` | Eyebrow |
| 5787 | `KI-Readiness Report` | `AI Readiness Report` | H1 Title |
| 5828 | `Reifegrad:` | `Maturity Level:` | Score label |
| 5831 | `Potenzial: +X Punkte` | `Potential: +X points` | Score sub |
| 5838 | `alt="KI-Sicherheit.jetzt"` | `alt="KI-Sicherheit.jetzt"` | Keep as brand |

### 2. PAGE 1: Dimension Labels (P0 - Critical)

| Zeile | DE Text | EN Translation |
|-------|---------|----------------|
| 5847 | `Governance` | `Governance` |
| 5858 | `Sicherheit` | `Security` |
| 5869 | `Wertschöpfung` | `Value Creation` |
| 5880 | `Befähigung` | `Enablement` |

### 3. PAGE 1: KPI Labels (P0 - Critical)

| Zeile | DE Text | EN Translation |
|-------|---------|----------------|
| 5892 | `Std.` | `hrs` |
| 5895 | `Zeitersparnis/Monat` | `Time Savings/Month` |
| 5898 | `bei Umsetzung der Empfehlungen` | `when implementing recommendations` |
| 5906 | `ROI (12 Monate)` | `ROI (12 Months)` |
| 5909 | `Payback: X Monate` | `Payback: X months` |
| 5917 | `AI Act Risiko` | `AI Act Risk` |
| 5920 | `DSGVO-konforme Empfehlung` | `GDPR-compliant recommendation` |

### 4. PAGE 1: Trust Badges (P0 - Critical)

| Zeile | DE Text | EN Translation |
|-------|---------|----------------|
| 5929 | `Erstellt von:` | `Created by:` |
| 5929 | `TÜV-zertifizierter KI-Manager` | `TÜV-certified AI Manager` |
| 5937 | `EU AI Act konform` | `EU AI Act compliant` |
| 5941 | `DSGVO-orientiert` | `GDPR-oriented` |
| 5945 | `Keine Rechtsberatung` | `Not legal advice` |

### 5. PAGE 2: Executive Decision (P1)

| Zeile | DE Text | EN Translation |
|-------|---------|----------------|
| 5969 | `Ihr KI-Reifegrad` | `Your AI Maturity` |
| 5977 | `Erwarteter ROI` | `Expected ROI` |
| 5980 | `nach 12 Monaten` | `after 12 months` |
| 5991 | `Final-Check` | `Final Check` |
| 6016 | `Diese Risiken wurden als hoch/kritisch eingestuft und erfordern sofortige Aufmerksamkeit.` | `These risks have been classified as high/critical and require immediate attention.` |
| 6027 | `Strategische Empfehlungen` | `Strategic Recommendations` |
| 6037 | `Weiterführende Details` | `Further Details` |

### 6. PAGE 3: TOC Sections (P1)

| Zeile | DE Text | EN Translation |
|-------|---------|----------------|
| 6066 | `Heute ineffizient` | `Currently Inefficient` |
| 6070-6073 | (List items about inefficiency) | See below |
| 6081 | `In 90 Tagen anders` | `Different in 90 Days` |
| 6085-6087 | (List items about future state) | See below |

**Inefficiency List:**
- `Entwicklung und Optimierung von Abläufen` → `Developing and optimizing processes`
- `Einzelschritte ohne Standard-Bausteine` → `Individual steps without standard building blocks`
- `Compliance-Prüfungen kosten Zeit` → `Compliance checks cost time`

**Future State List:**
- `Standard-Analyse-Backbone statt Handwerk` → `Standard analysis backbone instead of manual work`
- `Klare Prüfpunkte + Module` → `Clear checkpoints + modules`
- `Messbare Zeitgewinne` → `Measurable time savings`

### 7. PAGE 4+: Section Headers (P1)

| Zeile | DE Text | EN Translation |
|-------|---------|----------------|
| 6187 | `Executive KI-Stack` | `Executive AI Stack` |
| 6212 | `Kontext` | `Context` |
| 6215 | `Strategischer Kontext & Leitplanken` | `Strategic Context & Guardrails` |
| 6218 | `Ihre strategischen Vorgaben` | `Your strategic guidelines` |
| 6229 | `Strategische Prioritäten` | `Strategic Priorities` |
| 6239 | `Zeitfresser & Pain-Points` | `Time Wasters & Pain Points` |
| 6249 | `Hauptleistung` | `Main Service` |
| 6259 | `Laufende/geplante KI-Projekte` | `Ongoing/planned AI Projects` |

### 8. Roadmap Timeline (P1)

| Zeile | DE Text | EN Translation |
|-------|---------|----------------|
| 6605 | `Pilotierung` | `Piloting` |
| 6606 | `31–60 Tage` | `31–60 days` |
| 6610-6613 | (List items) | See below |
| 6622 | `Verstetigung` | `Consolidation` |
| 6623 | `61–90 Tage` | `61–90 days` |
| 6627-6630 | (List items) | See below |

**Piloting Phase List:**
- `Pilot-Workflow testen` → `Test pilot workflow`
- `Wöchentliche Reviews` → `Weekly reviews`
- `Best Practices dokumentieren` → `Document best practices`
- `Metriken definieren` → `Define metrics`

**Consolidation Phase List:**
- `Abläufe verstetigen` → `Consolidate processes`
- `KI-Leitlinien definieren` → `Define AI guidelines`
- `Nächste Use Cases priorisieren` → `Prioritize next use cases`
- `Wirkungsmessung durchführen` → `Measure impact`

### 9. Section Headers (P1)

| Zeile | DE Text | EN Translation |
|-------|---------|----------------|
| 6644 | `Wirtschaftlichkeit` | `Business Case` |
| 6645 | `Business Case` | `Business Case` |
| 6649 | `Einsparpotenziale & Investition` | `Savings Potential & Investment` |
| 7015 | `Projektstart` | `Project Start` |
| 7016 | `Kickoff-Vorlage` | `Kickoff Template` |
| 7020 | `Agenda & Fragenkatalog` | `Agenda & Questions` |
| 7032 | `Anleitung` | `Guide` |
| 7033 | `Prompt-Framework` | `Prompt Framework` |
| 7037 | `5-Schritte zum perfekten Prompt` | `5 Steps to the Perfect Prompt` |

### 10. Annex Sections (P2)

| Zeile | DE Text | EN Translation |
|-------|---------|----------------|
| 7047 | `Kreativ-Tools 2025 – modulare Alternativen` | `Creative Tools 2025 – Modular Alternatives` |
| 7048-7057 | (Full paragraph about creative tools) | See EN template |
| 7060 | `Glossar – zentrale KI-Begriffe` | `Glossary – Key AI Terms` |
| 7061 | `Die wichtigsten Begriffe aus diesem Report (max. 12 Einträge, kompakt).` | `The most important terms from this report (max. 12 entries, compact).` |

### 11. Glossary Entries (P2)

| DE Term | DE Definition | EN Term | EN Definition |
|---------|---------------|---------|---------------|
| AI Act (EU) | Europäische KI-Verordnung mit Pflichten je nach Risikoklasse. | AI Act (EU) | European AI regulation with obligations based on risk class. |
| API | Programmierschnittstelle zur Software-Anbindung. | API | Programming interface for software integration. |
| DSGVO | Datenschutz-Grundverordnung für personenbezogene Daten. | GDPR | General Data Protection Regulation for personal data. |
| Fine-Tuning | Nachtrainieren eines Modells auf eigene Daten. | Fine-Tuning | Retraining a model on custom data. |
| Guardrails | Prüfschritte, die KI-Ausgaben validieren/filtern. | Guardrails | Validation steps that filter AI outputs. |
| Halluzination | Plausibel klingende, aber faktisch falsche Modellausgabe. | Hallucination | Plausible-sounding but factually incorrect model output. |
| LLM | Large Language Model (GPT-4, Claude, Llama). | LLM | Large Language Model (GPT-4, Claude, Llama). |
| Prompt | Eingabeinstruktion an ein KI-Modell. | Prompt | Input instruction to an AI model. |
| RAG | Retrieval-Augmented Generation – KI mit eigener Wissensbasis. | RAG | Retrieval-Augmented Generation – AI with its own knowledge base. |
| Responsible AI | Verantwortungsvolle KI-Nutzung mit Ethik & Compliance. | Responsible AI | Responsible AI use with ethics & compliance. |
| Token | Grundeinheit der Modellverarbeitung (~3-4 Zeichen). | Token | Basic unit of model processing (~3-4 characters). |
| Human-in-the-Loop | Menschliche Kontrolle bei KI-Entscheidungsprozessen. | Human-in-the-Loop | Human oversight in AI decision processes. |

### 12. Legal/Impressum (P2)

| Zeile | DE Text | EN Translation |
|-------|---------|----------------|
| 7092 | `Rechtliches & Transparenz` | `Legal Information & Transparency` |
| 7095 | `Impressum` | `Legal Notice` |
| 7096 | `Verantwortlich für den Inhalt:` | `Responsible for content:` |
| 7103 | `Haftungsausschluss` | `Disclaimer` |
| 7104 | `Dieses Projekt dient ausschließlich der Information. Trotz sorgfältiger Prüfung übernehme ich keine Haftung für Inhalte externer Links.` | `This project is for informational purposes only. Despite careful review, I assume no liability for the content of external links.` |
| 7105 | `Urheberrecht` | `Copyright` |
| 7106 | `Alle Inhalte dieser Website unterliegen dem deutschen Urheberrecht, alle Bilder wurden mit Hilfe von KI erzeugt.` | `All content on this website is subject to German copyright law. All images were generated with the help of AI.` |
| 7109 | `Hinweis zum EU AI Act` | `EU AI Act Notice` |
| 7110 | `Diese Website informiert über Pflichten, Risiken und Fördermöglichkeiten beim Einsatz von KI nach EU AI Act und DSGVO. Sie ersetzt keine Rechtsberatung.` | `This website provides information about obligations, risks, and funding opportunities when using AI under the EU AI Act and GDPR. It does not constitute legal advice.` |
| 7115 | `Datenschutzerklärung` | `Privacy Policy` |
| 7116 | `Der Schutz Ihrer persönlichen Daten ist mir ein besonderes Anliegen.` | `The protection of your personal data is of particular concern to me.` |
| 7117 | `Kontakt mit mir` | `Contact` |
| 7118 | `Wenn Sie per Formular oder E-Mail Kontakt aufnehmen, werden Ihre Angaben zur Bearbeitung sechs Monate gespeichert.` | `If you contact me via form or email, your information will be stored for processing for six months.` |
| 7119 | `Cookies` | `Cookies` |
| 7120 | `Diese Website verwendet keine Cookies zur Nutzerverfolgung oder Analyse.` | `This website does not use cookies for user tracking or analytics.` |
| 7121 | `Ihre Rechte laut DSGVO` | `Your Rights under GDPR` |
| 7123-7126 | (List of GDPR rights) | See below |

**GDPR Rights List:**
- `Auskunft, Berichtigung oder Löschung Ihrer Daten` → `Information, correction, or deletion of your data`
- `Datenübertragbarkeit` → `Data portability`
- `Widerruf erteilter Einwilligungen` → `Revocation of given consent`
- `Beschwerde bei der Datenschutzbehörde` → `Complaint to the data protection authority`

### 13. Feedback Section (P2)

| Zeile | DE Text | EN Translation |
|-------|---------|----------------|
| 7193 | `Ihr Feedback ist uns wichtig!` | `Your Feedback Matters!` |
| 7196 | `Was hat Ihnen gefallen?` | `What did you like?` |
| 7196 | `Was können wir verbessern?` | `What can we improve?` |
| 7197 | `Nehmen Sie sich 2 Minuten Zeit für unser Feedback-Formular:` | `Take 2 minutes for our feedback form:` |
| ~7200 | `📝 Feedback geben` | `📝 Give Feedback` |

### 14. Appendix Headers (P2)

| Zeile | DE Text | EN Translation |
|-------|---------|----------------|
| 7155 | `DPIA-Analyse & AI Act Konformität` | `DPIA Analysis & AI Act Compliance` |
| 7162 | `Vendor Audit – KI-TÜV für Tools & Anbieter` | `Vendor Audit – AI Audit for Tools & Providers` |
| 7169 | `Automations-Roadmap & Prozessanalyse` | `Automation Roadmap & Process Analysis` |
| 7176 | `Monte-Carlo Simulation & Szenarioanalyse` | `Monte Carlo Simulation & Scenario Analysis` |

---

## 📚 TRANSLATION SOURCES

### 1. Formbuilder EN (bereitgestellt)

**Verfügbare Übersetzungen aus formbuilder_en:**
- Block titles (8 items)
- Field labels (~50 items)
- Field descriptions (~50 items)
- UI strings (Next, Back, Submit, etc.)

**Beispiel-Mappings:**
```
DE: "Was ist Ihre Hauptleistung?"
EN: "What is your main service or most important product?"

DE: "Branche"
EN: "Industry"

DE: "Unternehmensgröße"
EN: "Company size"

DE: "Land"
EN: "Country"
```

### 2. UI Labels JSON

**116 Keys verfügbar** mit 5-sprachiger Übersetzung (de/en/fr/es/it)

### 3. EN Template (existierend)

`pdf_template_en.html` enthält bereits viele EN-Übersetzungen:
- Page 1 Header-Section
- Page 2 Decision-Section
- Page 3 TOC-Section
- Legal Notice / Impressum
- Feedback Section
- Glossary (EN-Version)

---

## 🎯 IMPLEMENTATION STRATEGY

### Phase 1: Copy EN Template as Base (~70% done)

Das existierende `pdf_template_en.html` enthält bereits die meisten Übersetzungen für:
- Page 1-3 Content
- Legal/Impressum
- Glossary (EN)
- Feedback Section

**Action:** EN-Template als Basis nutzen, fehlende Sections aus DE ergänzen.

### Phase 2: Add Missing Sections (~20%)

Aus DE-Template übernehmen und übersetzen:
- Content Sections (Business Case, Risks, etc.)
- Roadmap Timeline Modern
- Strategic Context Section
- Appendix Structure

### Phase 3: Verify ui() Default Values (~10%)

Alle 46 ui() Keys mit Default-Werten im Template prüfen:
- Option A: Default-Werte im Template auf EN ändern
- Option B: Keys zu ui_labels.json hinzufügen (besser)

---

## 📋 IMPLEMENTATION CHECKLIST

### Pre-Implementation:

- [ ] Review this Translation Map with Wolf
- [ ] Confirm translation priorities (P0 → P2)
- [ ] Decide: ui() defaults in Template vs ui_labels.json

### Implementation:

- [ ] Copy pdf_template.html → pdf_template_en.html (new version)
- [ ] Replace all hardcoded DE texts with EN translations
- [ ] Update ui() default values to EN
- [ ] Test EN report generation
- [ ] QA: Verify no German text remains

---

## 📊 COMPLEXITY ESTIMATE

| Category | Items | Effort | Priority |
|----------|-------|--------|----------|
| Page 1 Labels | ~20 | Low | P0 |
| Page 2-3 Labels | ~15 | Low | P0 |
| Section Headers | ~20 | Low | P1 |
| Explanatory Text | ~10 | Medium | P1 |
| Legal/Impressum | ~15 | Low | P2 |
| Glossary | ~12 | Low | P2 |
| ui() Defaults | 46 | Low | P1 |
| **TOTAL** | **~138** | **Medium** | - |

**Estimated Time:** 2-3 hours for translation work

---

## 🚀 NEXT STEPS

1. [ ] Wolf reviews this Translation Map
2. [ ] Prioritize: Start with P0 (Page 1 content)
3. [ ] Decide ui() strategy (defaults vs ui_labels.json)
4. [ ] Execute template translation
5. [ ] Test with EN report generation
6. [ ] Add 46 missing ui() keys to ui_labels.json (optional but recommended)

---

**Translation Map Version:** 1.0
**Created:** 2026-01-06
**Analyzed by:** Claude Code (Opus 4.5)
**Next:** Phase 6.2 Template EN Regeneration
