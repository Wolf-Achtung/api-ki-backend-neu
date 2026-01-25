# FIX-523A Prompt Audit Report

## Summary

- **Total files scanned:** 106
- **Clean files:** 28
- **Files with violations:** 78
- **Total violations:** 291

### Violations by Category

- **CHAT_PHRASE:** 6
- **CODE_FENCE:** 86
- **EXPLICIT_BLACKLIST:** 5
- **PLACEHOLDER_BAIT:** 36
- **TYPO_QUOTE:** 158

## Files with Violations

### prompts/de/_hauptleistung_context.md

**Violations:** 1

- **Line 10** [TYPO_QUOTE]: Typographic quote found: '
  ```
  {% raw %}{% include '_hauptleistung_context.md' %}{% endraw %}
  ```

### prompts/de/_solo_language_rules.md

**Violations:** 2

- **Line 10** [TYPO_QUOTE]: Typographic quote found: '
  ```
  {% include '_solo_language_rules.md' %}
  ```
- **Line 59** [TYPO_QUOTE]: Typographic quote found: '
  ```
  **DON'T:**
  ```

### prompts/de/ai_act_summary.md

**Violations:** 2

- **Line 32** [TYPO_QUOTE]: Typographic quote found: „
  ```
         - Kurzteil: „Was bedeutet das für Unternehmen dieser Größe?" (size-aware).
  ```
- **Line 110** [TYPO_QUOTE]: Typographic quote found: „
  ```
    <h3>Relevanz für „{{HAUPTLEISTUNG}}" in der Branche {{BRANCHE_LABEL}}</h3>
  ```

### prompts/de/automation_roadmap_engine.md

**Violations:** 2

- **Line 122** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 174** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** business_case, ki_reifegrad, funding_data, ki_anwendung, hauptherausforderungen, strategy_plan, risk_report_v3, tools_data

### prompts/de/benchmark_engine.md

**Violations:** 2

- **Line 114** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 191** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** ki_reifegrad, funding_data, ki_anwendung, auto_report, hauptherausforderungen, strategy_plan, kpi_data, risk_report_v3, tools_data

### prompts/de/branch_deep_dive.md

**Violations:** 6

- **Line 33** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  - use example numbers, ranges or scenarios
  ```
- **Line 45** [EXPLICIT_BLACKLIST]: Explicit blacklist naming forbidden words - may prime those words
  ```
  HARD BLACKLIST (Fail-Closed):
  ```
- **Line 46** [CHAT_PHRASE]: Chat phrase pattern found: \bwie kann ich (?:dir|Ihnen) helfen\b
  ```
  - "wie kann ich dir helfen" / "wie kann ich helfen"
  ```
- **Line 227** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```html
  ```
- **Line 324** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```
- **Line 346** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \{variable\}
  ```
  - Keine Platzhalter ("[Hier einfügen]", "{{VARIABLE}}" außer definierten)
  ```

**Unresolved variables:** BRANCH_SHORT_LABEL, VARIABLE

### prompts/de/business_case.md

**Violations:** 1

- **Line 63** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  ZIEL: Klarer, realistischer Business Case mit ROI, CAPEX/OPEX.
  ```

**Unresolved variables:** EINSPARUNG_MONAT_EUR, CAPEX_REALISTISCH_EUR, ROI_12M, PAYBACK_MONTHS, OPEX_REALISTISCH_EUR

### prompts/de/business_case_engine_v2.md

**Violations:** 4

- **Line 64** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 113** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```
- **Line 230** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 279** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** STRATEGY_SUMMARY, TOOLS_SUMMARY, COMPANY_NAME, BRANCH_DEEP_DIVE_SUMMARY, BRANCH_LABEL, MATURITY_LEVEL, EINSPARUNG_STUNDEN_MONAT, EINSPARUNG_MONAT_EUR, BRANCH_SHORT_LABEL, FUNDING_SUMMARY, ROI_12M, RISK_SUMMARY, PAYBACK_MONTHS, SIZE_LABEL

### prompts/de/business_case_simulation.md

**Violations:** 6

- **Line 84** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 110** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```
- **Line 211** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 237** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```
- **Line 241** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 267** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** BC_INVESTMENT_TOTAL, BRANCH_LABEL, BC_CONSERVATIVE_ROI, AUTO_PHASE_1_COUNT, AUTO_AVG_POTENTIAL, BRANCH_SHORT_LABEL, BC_REALISTIC_PAYBACK, RISK_RESIDUAL_SCORE, MATURITY_LEVEL, RISK_RESIDUAL_GRADE, AI_ACT_CONFORMITY, BC_REALISTIC_SAVINGS, SIZE_LABEL, AI_ACT_MISSING_CONTROLS, TOOLS_SUMMARY, COMPANY_NAME, AUTO_QUICK_WINS, DPIA_REQUIRED, FUNDING_SUMMARY, COMPLIANCE_STATUS, BC_OPTIMISTIC_ROI, BC_REALISTIC_ROI, BC_OPTIMISTIC_PAYBACK, BC_CONSERVATIVE_PAYBACK, AUTO_PROCESS_COUNT

### prompts/de/costs_overview.md

**Violations:** 1

- **Line 19** [TYPO_QUOTE]: Typographic quote found: „
  ```
         - Regieanweisungen, Platzhaltertexte, Beispieltexte wie „xxx".
  ```

### prompts/de/data_readiness.md

**Violations:** 2

- **Line 86** [TYPO_QUOTE]: Typographic quote found: „
  ```
      <li>Daten sind häufig auf mehrere Systeme verteilt, ohne einheitliche Struktur oder zentrale „Si
  ```
- **Line 96** [TYPO_QUOTE]: Typographic quote found: „
  ```
      <li><strong>KI-Pilotprojekt mit „sauberem“ Datenschnitt starten:</strong> Einen Prozess wählen, 
  ```

### prompts/de/executive_decision.md

**Violations:** 4

- **Line 10** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  - use example numbers, ranges or scenarios
  ```
- **Line 30** [TYPO_QUOTE]: Typographic quote found: „
  ```
  AUSGABEREGEL (zwingend): Schreibe ausschließlich deklarative Berichtssätze. Keine Anrede, keine Frag
  ```
- **Line 32** [TYPO_QUOTE]: Typographic quote found: „
  ```
  STARTFORMAT: Beginne mit einem neutralen Substantivsatz (wie „Der aktuelle Zustand…", „Die empfohlen
  ```
- **Line 84** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \[ein 
  ```
      <li><strong>Tun:</strong> [Ein konkreter Standard-Workflow, der sofort umsetzbar ist]</li>
  ```

### prompts/de/executive_summary.md

**Violations:** 6

- **Line 162** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \[konkret
  ```
  - FORMAT: "[Branche] mit {{hauptleistung}} steht vor [konkreter Herausforderung basierend auf {{ZEIT
  ```
- **Line 164** [TYPO_QUOTE]: Typographic quote found: , r
  ```
    • "Ein Beratungsunternehmen mit {{hauptleistung}} steht vor der Aufgabe, repetitive Analysen zu au
  ```
- **Line 309** [TYPO_QUOTE]: Typographic quote found: „
  ```
  **„Wenn Sie nur eines tun:"** beginnt.
  ```
- **Line 316** [TYPO_QUOTE]: Typographic quote found: „
  ```
  - **keine allgemeinen Aussagen** enthalten (z. B. „Starten Sie mit KI" ist unzulässig).
  ```
- **Line 329** [TYPO_QUOTE]: Typographic quote found: „
  ```
  „Wenn Sie nur eines tun: Starten Sie mit einer internen KI-Assistenz für Regelwerks- und Risikoanaly
  ```
- **Line 332** [TYPO_QUOTE]: Typographic quote found: „
  ```
  „Wenn Sie nur eines tun: Standardisieren Sie einen wiederkehrenden Analyse- oder Reporting-Workflow 
  ```

**Unresolved variables:** STRATEGISCHE_ZIELE

### prompts/de/foerderpotenzial.md

**Violations:** 1

- **Line 188** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \{variable\}
  ```
  - Keine Platzhalter ("[Hier einfügen]", "{{VARIABLE}}" außer definierten)
  ```

**Unresolved variables:** EINSPARUNG_MONAT_EUR, CAPEX_REALISTISCH_EUR, VARIABLE, ROI_12M, PAYBACK_MONTHS, OPEX_REALISTISCH_EUR

### prompts/de/funding_engine_v2.md

**Violations:** 2

- **Line 58** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 83** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** AI_ACT_RISK_LEVEL, BRANCH_LABEL, SIZE_LABEL, MATURITY_LEVEL

### prompts/de/gamechanger.md

**Violations:** 9

- **Line 155** [TYPO_QUOTE]: Typographic quote found: '
  ```
  {% include '_hauptleistung_context.md' %}
  ```
- **Line 198** [TYPO_QUOTE]: Typographic quote found: '
  ```
              Der Weg zu '{{VISION_3_JAHRE}}' beginnt mit Standardisierung der Auswertungslogik."
  ```
- **Line 324** [TYPO_QUOTE]: Typographic quote found: '
  ```
  {% include '_solo_language_rules.md' %}
  ```
- **Line 339** [EXPLICIT_BLACKLIST]: Explicit blacklist naming forbidden words - may prime those words
  ```
  VERBOTENE BEGRIFFE FÜR SOLO (Null-Toleranz):
  ```
- **Line 376** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \[konkret
  ```
        - Format: "Bisher: [konkretes Problem bei {{hauptleistung}}]"
  ```
- **Line 399** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \[konkret
  ```
        - Format: "Stattdessen: [konkreter Ansatz] → Weg zu {{VISION_3_JAHRE}}"
  ```
- **Line 556** [TYPO_QUOTE]: Typographic quote found: „
  ```
  - direkte Ansprache („Sie", „du", „wir")
  ```
- **Line 557** [TYPO_QUOTE]: Typographic quote found: „
  ```
  - Hilfsangebote („helfen", „unterstützen", „begleiten")
  ```
- **Line 558** [TYPO_QUOTE]: Typographic quote found: „
  ```
  - Call-to-Actions („bei Bedarf", „kontaktieren", „anfragen")
  ```

**Unresolved variables:** GESCHAEFTSMODELL_EVOLUTION, industry, core_service, WETTBEWERB

### prompts/de/gamechanger_decision.md

**Violations:** 16

- **Line 10** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  - use example numbers, ranges or scenarios
  ```
- **Line 22** [EXPLICIT_BLACKLIST]: Explicit blacklist naming forbidden words - may prime those words
  ```
  HARD BLACKLIST (Fail-Closed):
  ```
- **Line 23** [CHAT_PHRASE]: Chat phrase pattern found: \bwie kann ich (?:dir|Ihnen) helfen\b
  ```
  - "wie kann ich dir helfen" / "wie kann ich helfen"
  ```
- **Line 36** [TYPO_QUOTE]: Typographic quote found: „
  ```
  AUSGABEREGEL (zwingend): Schreibe ausschließlich deklarative Berichtssätze. Keine Anrede, keine Frag
  ```
- **Line 38** [TYPO_QUOTE]: Typographic quote found: „
  ```
  STARTFORMAT: Beginne mit einem neutralen Substantivsatz (wie „Der aktuelle Zustand…", „Die empfohlen
  ```
- **Line 40** [TYPO_QUOTE]: Typographic quote found: „
  ```
  NICHT ERLAUBT: „wie kann ich helfen", „ich sehe keine frage", „beschreibe dein anliegen", „du hast n
  ```
- **Line 52** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  Externer Senior-Berater (Top-Beratung), ruhig, klar, strategisch.
  ```
- **Line 89** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```html
  ```
- **Line 101** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \[1 Satz\]
  ```
      <li><strong>Erweiterung:</strong> [1 Satz]</li>
  ```
- **Line 102** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \[1 Satz\]
  ```
      <li><strong>Qualität & Governance:</strong> [1 Satz]</li>
  ```
- **Line 103** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \[1 Satz\]
  ```
      <li><strong>Marktfähigkeit / IP:</strong> [1 Satz]</li>
  ```
- **Line 110** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \[konkret
  ```
    <p>[Konkreter Einstieg, kein 12-Monats-Horizont – 2-3 Sätze]</p>
  ```
- **Line 112** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```
- **Line 118** [TYPO_QUOTE]: Typographic quote found: „
  ```
  - Der Leser soll sagen: „Das ist kein Report – das ist ein erweiterbares Entscheidungsprodukt."
  ```
- **Line 121** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \[1 Satz\]
  ```
  - KEINE Platzhalter wie [1 Satz], [2-3 Sätze], {variable}, {{token}}
  ```
- **Line 128** [TYPO_QUOTE]: Typographic quote found: „
  ```
  Keine Assistenz- oder Chat-Formulierungen (z. B. „wie kann ich helfen", „gerne erkläre ich"). Verwen
  ```

**Unresolved variables:** token

### prompts/de/ki_aktivitaeten_ziele.md

**Violations:** 2

- **Line 21** [TYPO_QUOTE]: Typographic quote found: „
  ```
         - Keine Platzhaltertexte („Platzhalter", „TODO" oder andere Template-Marker).
  ```
- **Line 25** [TYPO_QUOTE]: Typographic quote found: „
  ```
         - Wenn eine Pflichtvariable fehlerhaft oder nicht lesbar ist → „Fehler: Datenquelle nicht ver
  ```

**Unresolved variables:** TOOLS_AKTUELL

### prompts/de/ki_stack_summary.md

**Violations:** 9

- **Line 10** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  - use example numbers, ranges or scenarios
  ```
- **Line 22** [EXPLICIT_BLACKLIST]: Explicit blacklist naming forbidden words - may prime those words
  ```
  HARD BLACKLIST (Fail-Closed):
  ```
- **Line 23** [CHAT_PHRASE]: Chat phrase pattern found: \bwie kann ich (?:dir|Ihnen) helfen\b
  ```
  - "wie kann ich dir helfen" / "wie kann ich helfen"
  ```
- **Line 36** [TYPO_QUOTE]: Typographic quote found: „
  ```
  AUSGABEREGEL (zwingend): Schreibe ausschließlich deklarative Berichtssätze. Keine Anrede, keine Frag
  ```
- **Line 38** [TYPO_QUOTE]: Typographic quote found: „
  ```
  STARTFORMAT: Beginne mit einem neutralen Substantivsatz (wie „Der aktuelle Zustand…", „Die empfohlen
  ```
- **Line 40** [TYPO_QUOTE]: Typographic quote found: „
  ```
  NICHT ERLAUBT: „wie kann ich helfen", „ich sehe keine frage", „beschreibe dein anliegen", „du hast n
  ```
- **Line 47** [TYPO_QUOTE]: Typographic quote found: „
  ```
  Erzeuge eine kompakte, C-Level-taugliche „KI-Stack Summary Card" als HTML-Block ohne <h1> oder <h2>.
  ```
- **Line 153** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```html
  ```
- **Line 214** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** BRANCH_SHORT_LABEL

### prompts/de/next_actions.md

**Violations:** 1

- **Line 86** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \[konkret
  ```
    <strong>[Konkrete Aktion]</strong> (Woche [X–Y])<br/>
  ```

### prompts/de/org_change.md

**Violations:** 2

- **Line 9** [TYPO_QUOTE]: Typographic quote found: „
  ```
  ZIEL: Präziser Abschnitt „Veränderungsfähigkeit & Lernen".
  ```
- **Line 97** [TYPO_QUOTE]: Typographic quote found: „
  ```
          Eine klare persönliche Aufteilung der „Hüte" – wie Erstellung, Prüfung, Freigabe –
  ```

**Unresolved variables:** ki_kompetenz, score_befaehigung, score_nutzen, score_sicherheit

### prompts/de/quick_wins.md

**Violations:** 5

- **Line 23** [TYPO_QUOTE]: Typographic quote found: „
  ```
  - Wenn wirtschaftliche Details naheliegen: schreibe **nur** sinngemäß „siehe Business Case" (ohne Za
  ```
- **Line 26** [TYPO_QUOTE]: Typographic quote found: „
  ```
  - Formelle Anrede **„Sie"**, keine Du-Form.
  ```
- **Line 27** [CHAT_PHRASE]: Chat phrase pattern found: \bhier (?:sind|ist|haben Sie)\b
  ```
  - Kein Chat-Smalltalk, keine Meta-Sätze („gern", „natürlich", „hier sind…").
  ```
- **Line 27** [TYPO_QUOTE]: Typographic quote found: „
  ```
  - Kein Chat-Smalltalk, keine Meta-Sätze („gern", „natürlich", „hier sind…").
  ```
- **Line 30** [TYPO_QUOTE]: Typographic quote found: „
  ```
  - Keine vagen Floskeln; nutze **„optional"** statt unverbindlicher Formulierungen.
  ```

### prompts/de/recommendations.md

**Violations:** 3

- **Line 282** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \[konkret
  ```
        <p class="muss-detail">Für Ihr Kerngeschäft: [Konkrete Umsetzungsschritte]</p>
  ```
- **Line 298** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \[konkret
  ```
        <p class="muss-detail">Qualitätscheck für diesen Bereich: [Konkrete Checkliste]</p>
  ```
- **Line 345** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \{variable\}
  ```
  - Keine Platzhalter ("[Hier einfügen]", "{{VARIABLE}}" außer definierten)
  ```

**Unresolved variables:** VARIABLE

### prompts/de/recommendations_engine.md

**Violations:** 5

- **Line 69** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 90** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```
- **Line 205** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 227** [TYPO_QUOTE]: Typographic quote found: '
  ```
        "description": "Bereiten Sie den Förderantrag für 'go-digital' vor. Fördersumme bis zu 50% der
  ```
- **Line 310** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** STRATEGY_SUMMARY, TOOLS_SUMMARY, COMPANY_NAME, EINSPARUNG_STUNDEN_MONAT, BRANCH_LABEL, MATURITY_LEVEL, PAYBACK_MONTHS, BRANCH_SHORT_LABEL, FUNDING_SUMMARY, ROI_12M, RISK_SUMMARY, BUSINESS_CASE_SUMMARY, SIZE_LABEL

### prompts/de/risk_engine_v2.md

**Violations:** 4

- **Line 49** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 90** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```
- **Line 156** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 229** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** STRATEGY_SUMMARY, TOOLS_SUMMARY, COMPANY_NAME, BRANCH_DEEP_DIVE_SUMMARY, BRANCH_LABEL, MATURITY_LEVEL, EINSPARUNG_STUNDEN_MONAT, BRANCH_SHORT_LABEL, FUNDING_SUMMARY, ROI_12M, PAYBACK_MONTHS, SIZE_LABEL

### prompts/de/risk_engine_v3.md

**Violations:** 2

- **Line 61** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 98** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** automatisierte_entscheidungen, datentypen, ai_act_class, ki_anwendung, dsgvo_risk_level, vendor_risk_score

### prompts/de/risks.md

**Violations:** 3

- **Line 120** [TYPO_QUOTE]: Typographic quote found: „
  ```
        KI „on top" scheitert. Maßnahme: Kleine Piloten mit klarem Umfang.
  ```
- **Line 160** [TYPO_QUOTE]: Typographic quote found: „
  ```
        Unklare KI-Rolle. Maßnahme: Dokumentation „Wo unterstützt KI?".
  ```
- **Line 256** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \{variable\}
  ```
  - Keine Platzhalter ("[Hier einfügen]", "{{VARIABLE}}" außer definierten)
  ```

**Unresolved variables:** VARIABLE, score_sicherheit

### prompts/de/roadmap_90d.md

**Violations:** 9

- **Line 201** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \[Bezug zu
  ```
  → Überschrift DYNAMISCH: "Phase 0: [Bezug zu {{hauptleistung}}] Setup"
  ```
- **Line 203** [TYPO_QUOTE]: Typographic quote found: '
  ```
  → Referenz: "Beginnen Sie mit dem 'Startpunkt in 30 Minuten' aus der Zusammenfassung."
  ```
- **Line 208** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \[Bezug zu
  ```
  → Überschrift DYNAMISCH: "Phase 1: [Bezug zu {{ZEITERSPARNIS_PRIORITAET}}] Entlastung"
  ```
- **Line 346** [TYPO_QUOTE]: Typographic quote found: „
  ```
      quantitativ (z. B. „12 LinkedIn-Posts statt 4 ohne KI").</li>
  ```
- **Line 366** [TYPO_QUOTE]: Typographic quote found: „
  ```
      Gewohnheiten. Beispiel: „Nach dem Morgenkaffee starte ich mit dem KI-gestützten
  ```
- **Line 367** [TYPO_QUOTE]: Typographic quote found: „
  ```
      E-Mail-Entwurf" oder „Vor jedem Kundengespräch lasse ich mir eine Gesprächsvorbereitung
  ```
- **Line 369** [TYPO_QUOTE]: Typographic quote found: „
  ```
      <li><strong>Selbstkontrolle ohne Druck:</strong> Führen Sie eine „Erfolgs-Checkliste" mit
  ```
- **Line 598** [TYPO_QUOTE]: Typographic quote found: „
  ```
      aus dem Pilotbereich mit messbaren Zahlen. Diese „Proof Points" sind Ihre beste
  ```
- **Line 633** [TYPO_QUOTE]: Typographic quote found: , r
  ```
          <li><em>Datenschutz-Konformität:</em> Null-Toleranz bei Verstößen, regelmäßige
  ```

### prompts/de/roadmap_90d_decision.md

**Violations:** 7

- **Line 10** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  - use example numbers, ranges or scenarios
  ```
- **Line 30** [TYPO_QUOTE]: Typographic quote found: „
  ```
  AUSGABEREGEL (zwingend): Schreibe ausschließlich deklarative Berichtssätze. Keine Anrede, keine Frag
  ```
- **Line 32** [TYPO_QUOTE]: Typographic quote found: „
  ```
  STARTFORMAT: Beginne mit einem neutralen Substantivsatz (wie „Der aktuelle Zustand…", „Die empfohlen
  ```
- **Line 90** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \[Max\. \d
  ```
      <li><strong>Umsetzung:</strong> [Max. 2-3 konkrete Schritte]</li>
  ```
- **Line 98** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \[Max\. \d
  ```
      <li><strong>Umsetzung:</strong> [Max. 2-3 konkrete Schritte]</li>
  ```
- **Line 106** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \[Max\. \d
  ```
      <li><strong>Umsetzung:</strong> [Max. 2-3 konkrete Schritte]</li>
  ```
- **Line 124** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \[1 Satz\]
  ```
  - KEINE Platzhalter wie [1 Satz], [Max. 2-3 Schritte], {variable}, {{token}}
  ```

**Unresolved variables:** token

### prompts/de/templates_start.md

**Violations:** 1

- **Line 47** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \[konkret
  ```
  Aufgabe: [Konkrete Aufgabe in 1 Satz].
  ```

### prompts/de/tools_empfehlungen.md

**Violations:** 1

- **Line 13** [TYPO_QUOTE]: Typographic quote found: '
  ```
  {% include '_hauptleistung_context.md' %}
  ```

**Unresolved variables:** BRANCH_SHORT_LABEL

### prompts/de/tools_engine_v4.md

**Violations:** 2

- **Line 73** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 88** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** BRANCH_SHORT_LABEL, TOOL_CATEGORY, SIZE_LABEL, TOOL_NAME

### prompts/de/top_3_massnahmen.md

**Violations:** 2

- **Line 40** [CHAT_PHRASE]: Chat phrase pattern found: \bhier (?:sind|ist|haben Sie)\b
  ```
  - Einleitungen wie "Hier sind die Top-3..."
  ```
- **Line 41** [CHAT_PHRASE]: Chat phrase pattern found: \bbitte beschreib(?:e|en)\b
  ```
  - Chat-Phrasen wie "Wie kann ich helfen?" oder "Bitte beschreibe..."
  ```

### prompts/de/transparency_box.md

**Violations:** 1

- **Line 70** [TYPO_QUOTE]: Typographic quote found: , r
  ```
        Ihrer Situation (neue Tools, geänderte Teamgröße, regulatorische Updates) empfehlen wir
  ```

### prompts/de/unternehmensprofil_markt.md

**Violations:** 4

- **Line 21** [TYPO_QUOTE]: Typographic quote found: „
  ```
         - Verwende „Nicht angegeben" oder einen neutralen generischen Ersatz.
  ```
- **Line 35** [TYPO_QUOTE]: Typographic quote found: „
  ```
           - Schreibe „Nicht angegeben“ an der passenden Stelle.
  ```
- **Line 59** [TYPO_QUOTE]: Typographic quote found: „
  ```
         - KEINE Platzhaltertexte im sichtbaren Output (z. B. „Titel …“, „Beispiel …“).
  ```
- **Line 171** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \{variable\}
  ```
  - Keine Platzhalter ("[Hier einfügen]", "{{VARIABLE}}" außer definierten)
  ```

**Unresolved variables:** GESCHAEFTSMODELL_EVOLUTION, VARIABLE

### prompts/de/vendor_audit_engine.md

**Violations:** 2

- **Line 88** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 133** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** risk_report_v2, ai_act_class, ki_anwendung, dsgvo_risk_level, risk_report_v3, tools_data

### prompts/de/wettbewerb_benchmark.md

**Violations:** 3

- **Line 20** [TYPO_QUOTE]: Typographic quote found: „
  ```
    > Top 10% → „stark über Branchenniveau"
  ```
- **Line 21** [TYPO_QUOTE]: Typographic quote found: „
  ```
    zwischen Ø und Top 10% → „über Branchenniveau"
  ```
- **Line 22** [TYPO_QUOTE]: Typographic quote found: „
  ```
    < Ø → „unter Branchendurchschnitt"
  ```

**Unresolved variables:** score_sicherheit, score_gesamt, RESEARCH_PROVENANCE_HTML, score_befaehigung, score_nutzen

### prompts/en/_hauptleistung_context.md

**Violations:** 2

- **Line 6** [TYPO_QUOTE]: Typographic quote found: '
  ```
  customer's main service. Addresses Problem #7:
  ```
- **Line 10** [TYPO_QUOTE]: Typographic quote found: '
  ```
  {% raw %}{% include '_hauptleistung_context.md' %}{% endraw %}
  ```

### prompts/en/_solo_language_rules.md

**Violations:** 2

- **Line 10** [TYPO_QUOTE]: Typographic quote found: '
  ```
  {% include '_solo_language_rules.md' %}
  ```
- **Line 59** [TYPO_QUOTE]: Typographic quote found: '
  ```
  **DON'T:**
  ```

### prompts/en/ai_act_summary.md

**Violations:** 1

- **Line 220** [TYPO_QUOTE]: Typographic quote found: , r
  ```
      <li>Formulate an internal mini-guideline: data, review, approvals, usage limits.</li>
  ```

### prompts/en/ai_policy_mini.md

**Violations:** 3

- **Line 21** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  - team: Clear roles (creator, reviewer), hand‑off rules
  ```
- **Line 22** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  - kmu: Structured policy, responsibilities and documentation obligations
  ```
- **Line 32** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  - Complements the Risks section (risks there, rules here)
  ```

### prompts/en/automation_roadmap_engine.md

**Violations:** 4

- **Line 99** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  - `analytics_reporting`: analytics, dashboards, reports
  ```
- **Line 101** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  - `quality_assurance`: quality assurance, reviews
  ```
- **Line 122** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 174** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** business_case, ki_reifegrad, funding_data, ki_anwendung, hauptherausforderungen, strategy_plan, risk_report_v3, tools_data

### prompts/en/benchmark_engine.md

**Violations:** 2

- **Line 113** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 190** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** ki_reifegrad, funding_data, ki_anwendung, auto_report, hauptherausforderungen, strategy_plan, kpi_data, risk_report_v3, tools_data

### prompts/en/branch_deep_dive.md

**Violations:** 5

- **Line 11** [TYPO_QUOTE]: Typographic quote found: '
  ```
  Analyze the user's concrete main service:
  ```
- **Line 170** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```html
  ```
- **Line 267** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```
- **Line 286** [TYPO_QUOTE]: Typographic quote found: '
  ```
  - No assistant language ("I can help you...", "I'm happy to explain...")
  ```
- **Line 289** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \{variable\}
  ```
  - No placeholders ("[Insert here]", "{{VARIABLE}}" except defined ones)
  ```

**Unresolved variables:** BRANCH_SHORT_LABEL, VARIABLE

### prompts/en/business_case.md

**Violations:** 3

- **Line 12** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  GOAL: Clear, realistic business case with ROI, CAPEX/OPEX.
  ```
- **Line 28** [TYPO_QUOTE]: Typographic quote found: '
  ```
  - In foerderpotenzial.md only reference these numbers, don't repeat
  ```
- **Line 125** [TYPO_QUOTE]: Typographic quote found: , r
  ```
      <li>Digital products (automated analyses, reports)</li>
  ```

**Unresolved variables:** EINSPARUNG_MONAT_EUR, CAPEX_REALISTISCH_EUR, ROI_12M, PAYBACK_MONTHS, OPEX_REALISTISCH_EUR

### prompts/en/business_case_engine_v2.md

**Violations:** 4

- **Line 64** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 113** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```
- **Line 230** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 279** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** STRATEGY_SUMMARY, TOOLS_SUMMARY, COMPANY_NAME, BRANCH_DEEP_DIVE_SUMMARY, BRANCH_LABEL, MATURITY_LEVEL, EINSPARUNG_STUNDEN_MONAT, EINSPARUNG_MONAT_EUR, BRANCH_SHORT_LABEL, FUNDING_SUMMARY, ROI_12M, RISK_SUMMARY, PAYBACK_MONTHS, SIZE_LABEL

### prompts/en/business_case_simulation.md

**Violations:** 6

- **Line 84** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 110** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```
- **Line 211** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 237** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```
- **Line 241** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 267** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** BC_INVESTMENT_TOTAL, BRANCH_LABEL, BC_CONSERVATIVE_ROI, AUTO_PHASE_1_COUNT, AUTO_AVG_POTENTIAL, BRANCH_SHORT_LABEL, BC_REALISTIC_PAYBACK, RISK_RESIDUAL_SCORE, MATURITY_LEVEL, RISK_RESIDUAL_GRADE, AI_ACT_CONFORMITY, BC_REALISTIC_SAVINGS, SIZE_LABEL, AI_ACT_MISSING_CONTROLS, TOOLS_SUMMARY, COMPANY_NAME, AUTO_QUICK_WINS, DPIA_REQUIRED, FUNDING_SUMMARY, COMPLIANCE_STATUS, BC_OPTIMISTIC_ROI, BC_REALISTIC_ROI, BC_OPTIMISTIC_PAYBACK, BC_CONSERVATIVE_PAYBACK, AUTO_PROCESS_COUNT

### prompts/en/competition_benchmark.md

**Violations:** 1

- **Line 180** [TYPO_QUOTE]: Typographic quote found: , r
  ```
          Clarify roles (AI owner, reviewer), uniform templates and short review loops.
  ```

**Unresolved variables:** score_sicherheit, score_gesamt, RESEARCH_PROVENANCE_HTML, score_befaehigung, score_nutzen

### prompts/en/data_readiness.md

**Violations:** 4

- **Line 40** [TYPO_QUOTE]: Typographic quote found: , r
  ```
      * Focus: binding data governance, interfaces, roles and responsibilities.
  ```
- **Line 77** [TYPO_QUOTE]: Typographic quote found: , r
  ```
      <li>In regulated areas ({{REGULIERTE_BRANCHE_LABELS}}) data protection, retention and access rig
  ```
- **Line 98** [TYPO_QUOTE]: Typographic quote found: , r
  ```
      <li><strong>Clarify data protection & access rights:</strong> Define responsibilities, roles and
  ```
- **Line 104** [TYPO_QUOTE]: Typographic quote found: , r
  ```
      For sustainable scaling, however, structure, responsibilities and data quality
  ```

### prompts/en/exec_snapshot.md

**Violations:** 6

- **Line 34** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  5. **Summarise the risk situation** by mentioning the highest priority risk category from the risk e
  ```
- **Line 47** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  Deliver a single HTML fragment using `<div>`, `<p>`, `<ul>`, `<li>`, `<strong>` and `<span>` tags on
  ```
- **Line 52** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  - **Clarity:** Each sentence must be crisp and free from filler words. Avoid questions, rhetorical d
  ```
- **Line 54** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  - **Safety & compliance:** Respect {{KI_GUARDRAILS}}, avoid high‑risk use cases and ensure complianc
  ```
- **Line 58** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```
- **Line 76** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** COMPANY_NAME, BRANCH_LABEL, MATURITY_LEVEL, BRANCH_SHORT_LABEL, SIZE_LABEL

### prompts/en/executive_decision.md

**Violations:** 2

- **Line 52** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```html
  ```
- **Line 61** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

### prompts/en/executive_summary.md

**Violations:** 4

- **Line 55** [TYPO_QUOTE]: Typographic quote found: '
  ```
  USER'S CORE BUSINESS (PRIMARY):
  ```
- **Line 69** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  - If {{ZEITERSPARNIS_PRIORITAET}} is available, relate decisions to it
  ```
- **Line 174** [TYPO_QUOTE]: Typographic quote found: '
  ```
  The decision concerns the direction of one's own work.
  ```
- **Line 277** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  → EXAMPLE: "Core recommendation → From custom code to templates: Questionnaire library, prompt stand
  ```

**Unresolved variables:** STRATEGISCHE_ZIELE

### prompts/en/foerderpotenzial.md

**Violations:** 2

- **Line 195** [TYPO_QUOTE]: Typographic quote found: '
  ```
  - No assistant language ("I can help you...", "I'm happy to explain...")
  ```
- **Line 198** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \{variable\}
  ```
  - No placeholders ("[Insert here]", "{{VARIABLE}}" except defined ones)
  ```

**Unresolved variables:** EINSPARUNG_MONAT_EUR, CAPEX_REALISTISCH_EUR, VARIABLE, ROI_12M, PAYBACK_MONTHS, OPEX_REALISTISCH_EUR

### prompts/en/funding_engine_v2.md

**Violations:** 7

- **Line 25** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  1. **Identify suitable programmes:** Select **3–5 funding programmes** that best fit the company’s s
  ```
- **Line 29** [TYPO_QUOTE]: Typographic quote found: , r
  ```
     - `provider` – the issuing body (e.g. BMWK, regional ministry, EU Commission, private foundation)
  ```
- **Line 54** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 77** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```
- **Line 89** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  5. **No placeholders:** Do not output variable names or indicate missing data. If no suitable progra
  ```
- **Line 93** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```
- **Line 131** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** COMPANY_NAME, BRANCH_LABEL, MATURITY_LEVEL, HAUPTHERAUSFORDERUNGEN, BRANCH_SHORT_LABEL, SIZE_LABEL

### prompts/en/funding_potential.md

**Violations:** 1

- **Line 76** [TYPO_QUOTE]: Typographic quote found: , r
  ```
      <li><strong>Project description:</strong> Document goals, measures, timeline and anticipated ben
  ```

**Unresolved variables:** EINSPARUNG_MONAT_EUR, CAPEX_REALISTISCH_EUR, ROI_12M, PAYBACK_MONTHS, OPEX_REALISTISCH_EUR

### prompts/en/gamechanger.md

**Violations:** 8

- **Line 82** [TYPO_QUOTE]: Typographic quote found: '
  ```
  {% include '_hauptleistung_context.md' %}
  ```
- **Line 89** [TYPO_QUOTE]: Typographic quote found: '
  ```
  The Gamechanger MUST incorporate the user's concrete briefing data.
  ```
- **Line 100** [TYPO_QUOTE]: Typographic quote found: '
  ```
  - {{VISION_3_JAHRE}} = User's long-term vision
  ```
- **Line 110** [TYPO_QUOTE]: Typographic quote found: '
  ```
  ❌ FORBIDDEN: "Processes are inefficient and don't scale"
  ```
- **Line 125** [TYPO_QUOTE]: Typographic quote found: '
  ```
              The path to '{{VISION_3_JAHRE}}' begins with standardizing the evaluation logic."
  ```
- **Line 235** [TYPO_QUOTE]: Typographic quote found: '
  ```
  {% include '_solo_language_rules.md' %}
  ```
- **Line 247** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  - NO organizational terms (team, department, rollout, etc.)
  ```
- **Line 250** [EXPLICIT_BLACKLIST]: Explicit blacklist naming forbidden words - may prime those words
  ```
  FORBIDDEN TERMS FOR SOLO (Zero Tolerance):
  ```

**Unresolved variables:** GESCHAEFTSMODELL_EVOLUTION, industry, core_service, WETTBEWERB

### prompts/en/gamechanger_decision.md

**Violations:** 3

- **Line 54** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```html
  ```
- **Line 77** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```
- **Line 86** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \{variable\}
  ```
  - NO placeholders such as [1 sentence], [2‑3 sentences], {variable}, {{token}} in the output
  ```

**Unresolved variables:** token

### prompts/en/ki_stack_summary.md

**Violations:** 4

- **Line 70** [TYPO_QUOTE]: Typographic quote found: , r
  ```
    - Focus on collaboration, roles, first governance approaches and simple standards.
  ```
- **Line 74** [TYPO_QUOTE]: Typographic quote found: , r
  ```
    - Focus on scaling, standardisation, responsibilities and risk management.
  ```
- **Line 116** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```html
  ```
- **Line 172** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** BRANCH_SHORT_LABEL

### prompts/en/next_actions.md

**Violations:** 1

- **Line 21** [TYPO_QUOTE]: Typographic quote found: '
  ```
  - {{VISION_3_JAHRE}} = The user's long‑term vision
  ```

### prompts/en/org_change.md

**Violations:** 3

- **Line 96** [TYPO_QUOTE]: Typographic quote found: , r
  ```
          A clear personal division of the “hats” – for example creation, review and approval – create
  ```
- **Line 98** [TYPO_QUOTE]: Typographic quote found: , r
  ```
          A clear division of roles (team lead, AI owner, review role) avoids duplicate work and ensur
  ```
- **Line 105** [TYPO_QUOTE]: Typographic quote found: , r
  ```
        Short feedback loops, structured notes and a compact standard help to transform successful AI 
  ```

**Unresolved variables:** ki_kompetenz, score_befaehigung, score_nutzen, score_sicherheit

### prompts/en/quick_wins.md

**Violations:** 6

- **Line 69** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 86** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```
- **Line 152** [TYPO_QUOTE]: Typographic quote found: '
  ```
  **Customer's main service:** "Online shop for office furniture"
  ```
- **Line 164** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 171** [TYPO_QUOTE]: Typographic quote found: , r
  ```
      "description": "Currently you structure each consulting process (questionnaire, evaluation, repo
  ```
- **Line 209** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** STUNDENSATZ_EUR

### prompts/en/recommendations.md

**Violations:** 4

- **Line 144** [TYPO_QUOTE]: Typographic quote found: '
  ```
    - Measure 1: {{ZEITERSPARNIS_PRIORITAET}} (user's biggest time drain)
  ```
- **Line 145** [TYPO_QUOTE]: Typographic quote found: '
  ```
    - Measure 2: {{hauptleistung}} (user's concrete core service)
  ```
- **Line 218** [TYPO_QUOTE]: Typographic quote found: '
  ```
  - No assistant language ("I can help you...", "I'm happy to explain...")
  ```
- **Line 221** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \{variable\}
  ```
  - No placeholders ("[Insert here]", "{{VARIABLE}}" except defined ones)
  ```

**Unresolved variables:** VARIABLE

### prompts/en/recommendations_engine.md

**Violations:** 7

- **Line 65** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 86** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```
- **Line 93** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  - Focal areas (tools, risks, funding)
  ```
- **Line 200** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 202** [TYPO_QUOTE]: Typographic quote found: , r
  ```
    "summary": "For your medium‑sized manufacturing company seven prioritised recommendations were ide
  ```
- **Line 222** [TYPO_QUOTE]: Typographic quote found: '
  ```
        "description": "Prepare the funding application for 'go‑digital'. Funding of up to 50% of cons
  ```
- **Line 305** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** STRATEGY_SUMMARY, TOOLS_SUMMARY, COMPANY_NAME, EINSPARUNG_STUNDEN_MONAT, BRANCH_LABEL, MATURITY_LEVEL, PAYBACK_MONTHS, BRANCH_SHORT_LABEL, FUNDING_SUMMARY, ROI_12M, RISK_SUMMARY, BUSINESS_CASE_SUMMARY, SIZE_LABEL

### prompts/en/risk_engine_v2.md

**Violations:** 5

- **Line 53** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 94** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```
- **Line 108** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  For `high_risk`: documentation, risk management, logging, human oversight
  ```
- **Line 160** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 233** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** STRATEGY_SUMMARY, TOOLS_SUMMARY, COMPANY_NAME, BRANCH_DEEP_DIVE_SUMMARY, BRANCH_LABEL, MATURITY_LEVEL, EINSPARUNG_STUNDEN_MONAT, BRANCH_SHORT_LABEL, FUNDING_SUMMARY, ROI_12M, PAYBACK_MONTHS, SIZE_LABEL

### prompts/en/risk_engine_v3.md

**Violations:** 4

- **Line 47** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 91** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```
- **Line 104** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```
- **Line 167** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** HIGH_PRIORITY_RISKS, COMPANY_NAME, RISK_MATRIX, BRANCH_LABEL, MATURITY_LEVEL, BRANCH_SHORT_LABEL, MITIGATION_STRATEGIES, SIZE_LABEL

### prompts/en/risks.md

**Violations:** 6

- **Line 87** [TYPO_QUOTE]: Typographic quote found: '
  ```
  ✅ <li><strong>Lack of transparency:</strong> Customers don't understand AI decisions.
  ```
- **Line 220** [TYPO_QUOTE]: Typographic quote found: , r
  ```
          <td>Template standards, review loops, clear communication of benefits and limits.</td>
  ```
- **Line 231** [TYPO_QUOTE]: Typographic quote found: , r
  ```
          <td>Incorrect information in customer documents, reputation damage</td>
  ```
- **Line 241** [TYPO_QUOTE]: Typographic quote found: , r
  ```
      {{OFFERING_LABEL}}. In the next step, risks should be prioritized
  ```
- **Line 254** [TYPO_QUOTE]: Typographic quote found: '
  ```
  - No assistant language ("I can help you...", "I'm happy to explain...")
  ```
- **Line 257** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \{variable\}
  ```
  - No placeholders ("[Insert here]", "{{VARIABLE}}" except defined ones)
  ```

**Unresolved variables:** VARIABLE, score_sicherheit

### prompts/en/roadmap_12m.md

**Violations:** 4

- **Line 94** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  - Team: AI coordinator, shared standards, review rounds
  ```
- **Line 95** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  - SME: departments, governance board, rollout plan, compliance
  ```
- **Line 225** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  <p><em>🎯 End‑of‑year milestone:</em> Board decision for year 2, rollout plan in place.</p>
  ```
- **Line 240** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \{variable\}
  ```
  - No placeholders (“[Insert here]”, “{{VARIABLE}}” except defined ones) 
  ```

**Unresolved variables:** VARIABLE

### prompts/en/roadmap_90d.md

**Violations:** 6

- **Line 59** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  Instead of generic steps, refer to the user's concrete work.
  ```
- **Line 289** [TYPO_QUOTE]: Typographic quote found: , r
  ```
      <li>Assess the quality of {{hauptleistung}} results: error rate, rework effort</li>
  ```
- **Line 446** [TYPO_QUOTE]: Typographic quote found: , r
  ```
      <li><strong>Prompt library:</strong> Collect all working prompt templates in a shared storage (N
  ```
- **Line 454** [TYPO_QUOTE]: Typographic quote found: , r
  ```
      <li><strong>Document lessons learned:</strong> After each phase (setup, relief, productive use) 
  ```
- **Line 513** [TYPO_QUOTE]: Typographic quote found: , r
  ```
    <p><strong>Milestone:</strong> Management decision towards {{VISION_3_JAHRE}} made, rollout plan r
  ```
- **Line 519** [TYPO_QUOTE]: Typographic quote found: , r
  ```
      <li><strong>Governance:</strong> {{KI_GUARDRAILS}} as clear rules, responsibilities documented</
  ```

### prompts/en/roadmap_90d_decision.md

**Violations:** 10

- **Line 14** [TYPO_QUOTE]: Typographic quote found: '
  ```
  NOT ALLOWED: "how can I help", "I don't see a question", "describe your request", "you haven't asked
  ```
- **Line 16** [TYPO_QUOTE]: Typographic quote found: '
  ```
  IMPORTANT: Use no address, no questions, no assistant or chat phrasing. No meta-commentary about mis
  ```
- **Line 49** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```html
  ```
- **Line 56** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \[Max\. \d
  ```
      <li><strong>Implementation:</strong> [Max. 2-3 concrete steps]</li>
  ```
- **Line 64** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \[Max\. \d
  ```
      <li><strong>Implementation:</strong> [Max. 2-3 concrete steps]</li>
  ```
- **Line 72** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \[Max\. \d
  ```
      <li><strong>Implementation:</strong> [Max. 2-3 concrete steps]</li>
  ```
- **Line 77** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```
- **Line 91** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \[Max\. \d
  ```
  - NO placeholders like [1 sentence], [Max. 2-3 steps], {variable}, {{token}}
  ```
- **Line 98** [TYPO_QUOTE]: Typographic quote found: '
  ```
  No assistant or chat formulations (e.g., "how can I help", "I'd be happy to explain"). Use report la
  ```
- **Line 117** [TYPO_QUOTE]: Typographic quote found: , r
  ```
      <li><strong>Stop Rule:</strong> If quality deviations exceed 20% or adoption fails to materialis
  ```

**Unresolved variables:** token

### prompts/en/strategy_governance.md

**Violations:** 3

- **Line 15** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  - [✓] Provide a bullet list describing current status across five areas: guidelines & policy, change
  ```
- **Line 20** [TYPO_QUOTE]: Typographic quote found: , r
  ```
  - [✓] Do not duplicate governance content in other prompts (org_change, risks) and respect guardrail
  ```
- **Line 49** [TYPO_QUOTE]: Typographic quote found: , r
  ```
        <strong>Responsibilities &amp; Competencies:</strong> The appointment of a data protection off
  ```

**Unresolved variables:** DATENSCHUTZ_LABEL, MELDEWEGE_LABEL, LOESCHREGELN_LABEL, BRANCH_SHORT_LABEL, DATENSCHUTZBEAUFTRAGTER_LABEL, FOLGENABSCHAETZUNG_LABEL

### prompts/en/technologie_prozesse.md

**Violations:** 3

- **Line 34** [TYPO_QUOTE]: Typographic quote found: , r
  ```
        <tr><td>Backend</td><td>Prompt orchestration, report builder and business case logic</td></tr>
  ```
- **Line 35** [TYPO_QUOTE]: Typographic quote found: , r
  ```
        <tr><td>AI/Analysis</td><td>Multi‑layer prompt analysis, research integration and industry con
  ```
- **Line 46** [TYPO_QUOTE]: Typographic quote found: , r
  ```
      <li>AI generates the report sections (Executive Summary, 90‑day roadmap, risks, business case, e
  ```

### prompts/en/technology_processes.md

**Violations:** 3

- **Line 35** [TYPO_QUOTE]: Typographic quote found: , r
  ```
        <tr><td>Backend</td><td>Prompt orchestration, report builder and business case logic</td></tr>
  ```
- **Line 36** [TYPO_QUOTE]: Typographic quote found: , r
  ```
        <tr><td>AI/Analysis</td><td>Multi‑layer prompt analysis, research integration and industry con
  ```
- **Line 47** [TYPO_QUOTE]: Typographic quote found: , r
  ```
      <li>AI generates the report sections (Executive Summary, 90‑day roadmap, risks, business case, e
  ```

### prompts/en/tools_empfehlungen.md

**Violations:** 5

- **Line 31** [TYPO_QUOTE]: Typographic quote found: , r
  ```
        - Focus: Audit trail, versioning, review mechanisms
  ```
- **Line 144** [TYPO_QUOTE]: Typographic quote found: , r
  ```
      Add subsections for data platforms, risk & compliance tools, and
  ```
- **Line 175** [TYPO_QUOTE]: Typographic quote found: , r
  ```
      Policy management, data protection controls, risk monitoring, and audit capabilities.
  ```
- **Line 234** [TYPO_QUOTE]: Typographic quote found: '
  ```
  - No assistant language ("I can help you...", "I'm happy to explain...")
  ```
- **Line 237** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \{variable\}
  ```
  - No placeholders ("[Insert here]", "{{VARIABLE}}" except defined ones)
  ```

**Unresolved variables:** BRANCH_SHORT_LABEL, VARIABLE

### prompts/en/tools_engine_v4.md

**Violations:** 2

- **Line 73** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 88** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** BRANCH_SHORT_LABEL, TOOL_CATEGORY, SIZE_LABEL, TOOL_NAME

### prompts/en/tools_recommendations.md

**Violations:** 3

- **Line 18** [TYPO_QUOTE]: Typographic quote found: , r
  ```
    * **Team:** Five clusters: (1) Collaboration & shared workspace, (2) Core process tools for {{OFFE
  ```
- **Line 96** [TYPO_QUOTE]: Typographic quote found: , r
  ```
      Require audit trails for AI interactions, versioning systems for prompts and models, and defined
  ```
- **Line 116** [TYPO_QUOTE]: Typographic quote found: , r
  ```
      Implement enterprise‑grade compliance and governance modules: policy management, data protection
  ```

**Unresolved variables:** BRANCH_SHORT_LABEL

### prompts/en/unternehmensprofil_markt.md

**Violations:** 4

- **Line 32** [TYPO_QUOTE]: Typographic quote found: , r
  ```
           - Specific market shares, revenues, names of competitors
  ```
- **Line 90** [TYPO_QUOTE]: Typographic quote found: , r
  ```
        increased digitalization, rising expectations for quality and speed, as well as
  ```
- **Line 98** [TYPO_QUOTE]: Typographic quote found: , r
  ```
        <li><strong>Key Drivers:</strong> Industry-typical drivers include cost pressure, skills short
  ```
- **Line 171** [PLACEHOLDER_BAIT]: Placeholder pattern in non-comment: \{variable\}
  ```
  - No placeholders ("[Insert here]", "{{VARIABLE}}" except defined ones)
  ```

**Unresolved variables:** GESCHAEFTSMODELL_EVOLUTION, VARIABLE

### prompts/en/vendor_audit_engine.md

**Violations:** 2

- **Line 88** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```json
  ```
- **Line 133** [CODE_FENCE]: Code fence found - may prime LLM to output code blocks
  ```
  ```
  ```

**Unresolved variables:** risk_report_v2, ai_act_class, ki_anwendung, dsgvo_risk_level, risk_report_v3, tools_data

### prompts/en/wettbewerb_benchmark.md

**Violations:** 1

- **Line 179** [TYPO_QUOTE]: Typographic quote found: , r
  ```
          Clarify roles (AI owner, reviewer), uniform templates and short review loops.
  ```

**Unresolved variables:** score_sicherheit, score_gesamt, RESEARCH_PROVENANCE_HTML, score_befaehigung, score_nutzen

## Fix Hints

- **CODE_FENCE:** Remove code fences from prompt output examples; describe structure in prose
- **CHAT_PHRASE:** Remove conversational language from prompts
- **EXPLICIT_BLACKLIST:** Replace explicit forbidden-word lists with general rules
- **PLACEHOLDER_BAIT:** Replace [placeholder] patterns with concrete descriptions
- **HTML_ENTITY:** Replace &uuml; etc. with actual UTF-8 characters (ü)
- **TYPO_QUOTE:** Replace „  with ASCII quotes (")
