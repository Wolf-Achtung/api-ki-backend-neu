<!--
=============================================================================
SOLO SPRACH-REGELN v1.0 (zentrale Konfiguration)
=============================================================================
Diese Datei wird von allen Prompts referenziert, die Solo-gerechte Sprache
benötigen. Adressiert Problem #6: Enterprise-Sprache für Solo-Kunden.

VERWENDUNG in anderen Prompts (raw-gewrappt — ein scharfer Include-Tag hier
würde Selbst-Inklusion/Jinja-Rekursion auslösen, vgl. P6-Lint):
{% raw %}
{% if COMPANY_SIZE == "solo" %}
{% include '_solo_language_rules.md' %}
{% endif %}
{% endraw %}
=============================================================================
-->

## SOLO-SPRACHREGELN (STRIKT!)

### VERBOTENE ENTERPRISE-BEGRIFFE (Null-Toleranz für Solo):

**Technische Buzzwords:**
- "Engine", "Plattform", "Framework", "Pipeline", "Architektur"
- "Baukasten", "Modul", "Stack", "Layer", "API"
- "Dashboard", "Backend", "Frontend", "Deployment"

**Organisationsbegriffe:**
- "Rollout", "Change Management", "Transformation", "Skalierung"
- "Stakeholder", "Team-Meeting", "Abteilung", "Ressourcen"
- "Governance-Struktur", "Compliance-Framework", "Audit-Trail"

**Abstrakte Konzepte:**
- "Strategische Roadmap", "Meilenstein-Planung", "KPI-Dashboard"
- "Prozesslandschaft", "Wertschöpfungskette", "Matrixorganisation"
- "Enterprise-Software", "Unternehmensarchitektur"

### ERLAUBTE SOLO-BEGRIFFE (bevorzugt verwenden):

**Praktische Werkzeuge:**
- "Werkzeug", "Tool", "App", "Software", "Programm"
- "Vorlage", "Checkliste", "Ablauf", "Routine"
- "Arbeitsweise", "Vorgehen", "System"

**Persönliche Bezüge:**
- "Ihre Arbeitszeit", "Ihr Alltag", "Ihre Kunden"
- "Projekte", "Aufträge", "Anfragen", "Mandate"
- "Wochenplanung", "Tagesablauf", "Routine"

**Konkrete Handlungen:**
- "Zeit sparen", "automatisieren", "vereinfachen"
- "einrichten", "ausprobieren", "testen"
- "dokumentieren", "speichern", "wiederverwenden"

### TONFALL FÜR SOLO:

**DO:**
- Direkt und praktisch ("In 15 Minuten einrichtbar")
- Konkrete Zeitangaben ("spart 2-3 Stunden pro Woche")
- Persönliche Ansprache wo erlaubt ("Ihr erster Schritt")
- Niedrigschwellige Empfehlungen

**DON'T:**
- Abstrakte Konzepte ohne praktischen Bezug
- Organisatorischer Jargon
- Komplexe Prozessbeschreibungen
- Enterprise-Budgetvorstellungen

### BUDGET-REALITÄT FÜR SOLO:

- Max. Einmalinvestition: 5.000€ (typisch: 500-2.000€)
- Max. laufende Kosten: 200€/Monat (typisch: 50-100€)
- KEINE Enterprise-Software empfehlen (Salesforce, SAP, etc.)
- Fokus auf: ChatGPT Plus, Zapier, Notion, Make, etc.

### BEISPIEL-TRANSFORMATION:

**VORHER (Enterprise-Sprache - VERBOTEN für Solo):**
"Die Implementierung eines modularen Diagnose-Baukastens ermöglicht
die Skalierung der Auswertungs-Engine und Optimierung der
Prozesslandschaft durch systematisches Change Management."

**NACHHER (Solo-Sprache - RICHTIG):**
"Mit einer einfachen Checkliste und 3 Prompt-Vorlagen können
Sie Kundenanfragen in 30 statt 90 Minuten bearbeiten."
