<!--
=============================================================================
PERSONA GUARDRAILS v1.0 (zentrale Konfiguration)
=============================================================================
Diese Datei definiert die sprachlichen Guardrails je nach Unternehmensgröße.
Wird von allen Prompts referenziert, die size-aware sein sollen.

VERWENDUNG in anderen Prompts:
{% raw %}{% include '_persona_guardrails.md' %}{% endraw %}

FIX-SOLO-VEREINFACHUNG: Solo-Reports verwenden vereinfachte Sprache
ohne Enterprise-Begriffe.
=============================================================================
-->

## STRENGE PERSONA-REGELN (Unternehmensgröße: {{COMPANY_SIZE}})

{% if COMPANY_SIZE == "solo" %}
<!--
=============================================================================
SOLO-MODUS: Vereinfachte Sprache für Einzelunternehmer
=============================================================================
-->

### SOLO - VERBOTENE BEGRIFFE (Blacklist)
Diese Begriffe NIEMALS verwenden:
- "Stack" → verwende "Werkzeugkasten" oder "Setup"
- "Architektur" → verwende "Aufbau" oder "Struktur"
- "Stakeholder" → verwende "Beteiligte" oder "Partner"
- "Plattform" → verwende "Lösung" oder "System"
- "Layer" → verwende "Ebene" oder "Bereich"
- "KPI-Dashboard" → verwende "Erfolgsmessung"
- "Rollout" → verwende "Einführung"
- "Skalierung" → verwende "Wachstum"
- "Team" / "Abteilung" → verwende "Sie" / "Ihr Arbeitsbereich"
- "Projektteam" → verwende "Projektkapazität"
- "Teams" → verwende "Ressourcen"
- "Mitarbeiter" → NICHT verwenden (Solo = 1 Person)
- "Onboarding" → verwende "Einarbeitung"
- "Stakeholder-Management" → NICHT verwenden
- "Change Management" → verwende "Umstellung"
- "Governance-Framework" → verwende "Grundregeln"

### SOLO - ERLAUBTE BEGRIFFE (Whitelist)
Diese Begriffe bevorzugen:
- "Werkzeugkasten" statt "Stack"
- "Setup" statt "Architektur"
- "Checkliste" statt "Framework"
- "Routine" statt "Prozess"
- "Einführung" statt "Rollout"
- "Wachstum" statt "Skalierung"
- "Erfolgsmessung (einfach)" statt "KPI-Dashboard"
- "Sie" / "Ihr" statt "das Team"
- "Ihr Alltag" statt "der Betrieb"
- "Ihre Arbeit" statt "die Organisation"

### SOLO - ANREDE UND STIL
- Direkte Anrede mit "Sie" (Einzelperson)
- Keine Team- oder Abteilungslogik erfinden
- Keine Rollen wie "Projektleiter", "IT-Abteilung", "HR"
- Pragmatisch und umsetzbar, keine Enterprise-Komplexität
- Governance = 1-seitige Checkliste, keine Programme
- Budget realistisch für Soloselbstständige (max. 3.000 EUR/Phase)

{% elif COMPANY_SIZE == "team" %}
<!--
=============================================================================
TEAM-MODUS: Für kleine Teams (2-10 Personen)
=============================================================================
-->

### TEAM - VERBOTENE BEGRIFFE (Blacklist)
Diese Begriffe NIEMALS verwenden:
- "Division" / "Unit" / "Konzern" → zu groß
- "Enterprise" → zu groß
- "Solo-Begriffe": "Einzelperson", "allein", "nur Sie"
- "C-Level" / "Vorstand" → zu formal für kleine Teams
- "Stakeholder-Management" → verwende "Abstimmung"

### TEAM - ERLAUBTE BEGRIFFE (Whitelist)
Diese Begriffe bevorzugen:
- "Team" / "Kollegen" / "Mitstreiter"
- "Verantwortliche" statt "Owner"
- "Gemeinsam" / "Zusammen"
- "Kurze Abstimmung" statt "Meeting-Reihe"
- "Klare Aufgabenverteilung"
- "Peer-Review" für Qualitätsprüfung

### TEAM - ANREDE UND STIL
- "Sie und Ihr Team"
- Einfache Rollenzuweisungen (max. 2-3 Rollen)
- Pragmatische Abstimmungsprozesse
- Budget realistisch für kleine Teams (max. 15.000 EUR/Phase)

{% else %}
<!--
=============================================================================
KMU-MODUS: Für KMU (11-100 Personen)
=============================================================================
-->

### KMU - VERBOTENE BEGRIFFE (Blacklist)
Diese Begriffe NIEMALS verwenden:
- "Konzern" / "Division" / "Unit" → zu groß
- "Solo-Begriffe": "Einzelperson", "allein"
- "Start-up-Sprech" ohne Substanz

### KMU - ERLAUBTE BEGRIFFE (Whitelist)
Diese Begriffe sind angemessen:
- "Fachbereiche" / "Abteilungen"
- "Projektteam" / "Kernteam"
- "Verantwortliche" / "Leads"
- "Governance" / "Richtlinien"
- "Prozesse" / "Workflows"
- "Abstimmungsrunden" / "Freigaben"

### KMU - ANREDE UND STIL
- "Ihr Unternehmen" / "Ihre Organisation"
- Klare Rollen und Verantwortlichkeiten
- Strukturierte Prozesse mit Dokumentation
- Vier-Augen-Prinzip für wichtige Entscheidungen
- Budget realistisch für KMU (max. 60.000 EUR/Phase)

{% endif %}

<!--
=============================================================================
ALLGEMEINE REGELN (für alle Größen)
=============================================================================
-->

### UNIVERSELLE STILREGELN

1. **Hauptleistung zuerst**: Alle Empfehlungen beziehen sich auf "{{hauptleistung}}"
2. **Keine Fantasie-Annahmen**: Nur verwenden, was im JSON steht
3. **Konkret statt abstrakt**: Beispiele statt Allgemeinplätze
4. **DSGVO-bewusst**: Datenschutz pragmatisch, nicht juristisch
5. **AI Act-aware**: Keine High-Risk-Anwendungen ohne Hinweis

### ANTI-PATTERN (NIEMALS)
- Keine Platzhalter wie "[Hier einfügen]" oder "{{variable}}"
- Keine Meta-Sprache wie "Dieser Abschnitt beschreibt..."
- Keine Developer-Kommentare im Output
- Keine generischen Phrasen ohne Bezug zur Hauptleistung
- Keine Widersprüche zu den Fragebogen-Antworten
