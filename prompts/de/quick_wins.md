Developer:
<!-- PLATIN++ PROMPT v5.2 -->
<!-- SECTION: quick_wins -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{HAUPTLEISTUNG}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{BRANCHE_LABEL}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 1800 (solo:0.8x=1440, team:1.0x=1800, kmu:1.15x=2070) -->
<!--
ZIEL: Präzise Quick Wins in korrekter Reihenfolge.

ANZAHL NACH GRÖSSE (STRIKT!):
- solo: 3–4 Quick Wins
- team: 4–5 Quick Wins
- kmu: 5–7 Quick Wins

REIHENFOLGE DER KATEGORIEN (IMMER EINHALTEN!):
1. ZEITERSPARNIS: Routineaufgaben, die Zeit fressen
2. PRODUKTIVITÄTSSPRÜNGE: Arbeitsabläufe, die sich beschleunigen
3. QUALITÄTSVERBESSERUNG: Outputs, die besser werden
4. KOSTENSENKUNG: Direkte oder indirekte Einsparungen (nur bei team/kmu)

FORMAT PRO QUICK WIN:
- **[Konkrete Maßnahme]:** [1 Satz Beschreibung]. *Effekt: [X h/Monat oder %]*

STIL:
- Präzise, keine Floskeln
- Konkret anwendbar (nicht "optimieren Sie", sondern "nutzen Sie KI für...")
- Realistische Zeiteinsparungen (2-8 h/Monat pro Maßnahme)
- Keine Übertreibungen

ANTI-REDUNDANZ:
- Quick Wins = EINZIGE Stelle für diese Maßnahmen
- Roadmap verweist auf Quick Wins, listet sie NICHT erneut
- Business Case referenziert Einsparungen, rechnet sie aber separat

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: "Sie sparen", persönliche Routinen, eigene Workflows
        KEINE Team-Begriffe
- team: "Das Team spart", gemeinsame Standards, Kollaboration
- kmu: "Der Fachbereich profitiert", skalierbare Prozesse, Governance

BRANCHENSPEZIFIK:
- Nutze typische Aufgaben aus {{BRANCHE_LABEL}}
- Beziehe dich auf {{HAUPTLEISTUNG}}
-->

## Quick Wins – Sofort wirksame Maßnahmen

{% if COMPANY_SIZE == "solo" %}
Die folgenden 3–4 Maßnahmen bringen Ihnen als Einzelunternehmer:in im Bereich **{{HAUPTLEISTUNG}}** sofortige Entlastung:

### Zeitersparnis
- **Wiederkehrende Texte automatisieren:** Nutzen Sie KI für Erst-Entwürfe von E-Mails, Angeboten und Protokollen. *Effekt: 4–6 h/Monat*

### Produktivitätssprung
- **Recherche beschleunigen:** KI-gestützte Zusammenfassungen von Dokumenten, Marktinfos und Briefings. *Effekt: 3–5 h/Monat*

### Qualitätsverbesserung
- **Eigene Texte gegenlesen lassen:** KI als Lektorat für Konsistenz, Tonalität und Fehlerfreiheit. *Effekt: Weniger Nachbesserungen, professionellerer Auftritt*

{% elif COMPANY_SIZE == "team" %}
Die folgenden 4–5 Maßnahmen entlasten Ihr Team im Bereich **{{HAUPTLEISTUNG}}** sofort:

### Zeitersparnis
- **Standardtexte & Vorlagen automatisieren:** KI erzeugt Erstentwürfe für E-Mails, Protokolle und Reports. *Effekt: 5–8 h/Monat pro Person*
- **Meeting-Protokolle automatisieren:** Automatische Zusammenfassungen und Action Items. *Effekt: 2–3 h/Monat*

### Produktivitätssprung
- **Wissensorganisation vereinfachen:** Zentrale Dokumente werden automatisch zusammengefasst und durchsuchbar. *Effekt: 3–5 h/Monat*

### Qualitätsverbesserung
- **Einheitliche Qualitätsstandards:** KI-gestützte Checklisten für konsistente Outputs. *Effekt: Weniger Feedback-Schleifen*

### Kostensenkung
- **Externe Lektoratskosten reduzieren:** Interne KI-Prüfung vor Freigabe. *Effekt: 15–25% weniger externe Kosten*

{% else %}
Die folgenden 5–7 Maßnahmen schaffen in Ihrem Unternehmen ({{UNTERNEHMENSGROESSE_LABEL}}) im Bereich **{{HAUPTLEISTUNG}}** sofort Mehrwert:

### Zeitersparnis
- **Wiederkehrende Reports automatisieren:** KI generiert Basis-Reports aus Datenquellen. *Effekt: 6–10 h/Monat pro Bereich*
- **E-Mail-Triage beschleunigen:** Automatische Priorisierung und Entwürfe für Standardanfragen. *Effekt: 3–5 h/Monat*

### Produktivitätssprung
- **Wissensmanagement professionalisieren:** Zentrale, KI-durchsuchbare Dokumentenbasis. *Effekt: 4–6 h/Monat*
- **Onboarding beschleunigen:** KI-gestützte Einarbeitung mit automatischen Q&A. *Effekt: 20% schnellere Einarbeitung*

### Qualitätsverbesserung
- **Konsistente Outputs sicherstellen:** KI-Qualitätschecks vor Kundenversand. *Effekt: Weniger Reklamationen*
- **Dokumentation standardisieren:** Automatische Template-Befüllung aus Projekt-Daten. *Effekt: Einheitliche Qualität*

### Kostensenkung
- **Externe Dienstleister reduzieren:** Interne KI-Unterstützung für Lektorat, Übersetzung, Recherche. *Effekt: 20–30% weniger externe Kosten*
{% endif %}

*Die Effekte sind erfahrungsbasierte Orientierungswerte und variieren je nach Ausgangslage.*
