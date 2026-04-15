<!--
=============================================================================
HAUPTLEISTUNG CONTEXT BLOCK v1.0 (zentrale Konfiguration)
=============================================================================
Diese Datei wird von allen Prompts referenziert, die sich auf die
Hauptleistung des Kunden beziehen sollen. Adressiert Problem #7:
Generische Empfehlungen statt maßgeschneiderter Analyse.

VERWENDUNG in anderen Prompts:
{% raw %}{% include '_hauptleistung_context.md' %}{% endraw %}
=============================================================================
-->

## KERN-INFORMATION: Was dieses Unternehmen tut

{% if hauptleistung %}
Der Kunde beschreibt sein Geschäft so:
**"{{hauptleistung}}"**

Dies ist die WICHTIGSTE Information für diese Analyse.
{% else %}
**Hinweis:** Keine explizite Hauptleistung angegeben.
Nutze {{OFFERING_LABEL}} als Fallback: "{{OFFERING_LABEL}}"
{% endif %}

### STRENGE REGELN FÜR DIESE ANALYSE:

1. **JEDE Empfehlung** muss sich direkt auf "{{hauptleistung}}" beziehen
2. **KEINE generischen Phrasen** wie "Prozesse optimieren" oder "Effizienz steigern"
3. **KONKRETE BEISPIELE** müssen die Hauptleistung wörtlich aufgreifen
4. **QUICK WINS** müssen erklären, wie sie bei "{{hauptleistung}}" helfen

### BEISPIEL-TRANSFORMATION:

{% if hauptleistung %}
**VERBOTEN (zu generisch):**
"E-Mail-Automatisierung einführen, um Zeit zu sparen."

**RICHTIG (hauptleistungsbezogen):**
"E-Mail-Vorlagen für {{hauptleistung}}-Anfragen erstellen – spart 30 Min/Anfrage."
{% endif %}

### KONTEXT-VARIABLEN (verfügbar):

- **hauptleistung:** "{{hauptleistung}}"
- **ZEITERSPARNIS_PRIORITAET:** "{{ZEITERSPARNIS_PRIORITAET}}"
- **KI_GUARDRAILS:** "{{KI_GUARDRAILS}}"
- **BRANCHE:** "{{BRANCHE_LABEL}}"
- **COMPANY_SIZE:** "{{COMPANY_SIZE}}"
- **expertise_level:** "{{expertise_level}}"
- **expertise_label:** "{{expertise_label}}"

### KIS-1132: KOMPETENZ-KALIBRIERUNG
{% if expertise_level == "expert" %}
**ACHTUNG: Der Nutzer ist ein {{expertise_label}} (KI-Kompetenz: hoch).**
Er arbeitet bereits mit KI-APIs und baut eigene Systeme.
KEINE Einsteiger-Tipps. Empfehlungen muessen auf BESTEHENDEM Niveau aufbauen.
Fokus: Pipeline-Optimierung, Governance, Monitoring, Skalierung.
{% elif expertise_level == "intermediate" %}
**Der Nutzer ist ein {{expertise_label}} (KI-Kompetenz: mittel).**
Kennt Grundlagen, nutzt Tools aktiv. Keine Grundlagen-Erklärungen.
Fokus: Workflow-Optimierung, Automatisierung, spezialisierte Tools.
{% endif %}

