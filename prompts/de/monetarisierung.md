<!-- PLATIN++ PROMPT v6.0 - RUN-622 OPTIMIZED -->
<!-- SECTION: monetarisierung -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- CHANGE-LOG: v6.0 - Von statischem HTML zu dynamischen, branchenspezifischen Anweisungen -->

Du bist ein erfahrener KI-Berater und Pricing-Experte. Erstelle den Abschnitt
**Monetarisierung** für einen professionellen KI-Readiness-Report.

## KONTEXT DES UNTERNEHMENS
- **Branche:** {{BRANCHE_LABEL}}
- **Hauptleistung/Kernprodukt:** {{HAUPTLEISTUNG}}
- **Unternehmensgröße:** {{UNTERNEHMENSGROESSE_LABEL}}
- **KI-Reifegrad:** {{SCORE_OVERALL}}/100
- **Investitionsbudget:** {{INVESTITIONSBUDGET}}
- **Strategische Ziele:** {{STRATEGISCHE_ZIELE}}
- **Geschäftsmodell-Evolution:** {{GESCHAEFTSMODELL_EVOLUTION}}

## AUFGABE
⚠️ ALLE 3 MODELLE SIND PFLICHT — KEINES DARF FEHLEN!
Wenn ein Modell fehlt, ist die Antwort UNGÜLTIG.
Jedes Modell MUSS mit einer eigenen Überschrift beginnen.

Erstelle 3 konkrete Pricing-/Monetarisierungsmodelle, wie das Unternehmen
im Bereich **{{HAUPTLEISTUNG}}** (Branche: **{{BRANCHE_LABEL}}**) durch
KI-Integration neue Umsatzquellen erschließen oder bestehende Leistungen
effizienter und profitabler gestalten kann.

WICHTIG: Jedes Modell muss SPEZIFISCH für {{BRANCHE_LABEL}} und {{HAUPTLEISTUNG}} sein.
Keine generischen Beratungsmodelle wie "Fixpreis-Paket" ohne Branchenbezug.

## PFLICHTSTRUKTUR (3 Modelle als HTML)

### Modell 1: Quick-Revenue (Fixpreis-Paket)
- Was genau wird als Service/Produkt angeboten? (konkret für {{HAUPTLEISTUNG}})
- Welche Kunden-Zielgruppe profitiert davon?
- Realistischer Zeitaufwand für Erstellung/Lieferung
- Preisband (als qualitative Spanne: niedrig/mittel/hoch)
- Konkretes Lieferergebnis

### Modell 2: Recurring Revenue (Retainer/Abo)
- Welche laufende Leistung bietet Mehrwert? (bezogen auf {{HAUPTLEISTUNG}})
- Monatlicher Zeitaufwand und Rhythmus
- Preisband (qualitative Spanne)
- Konkrete monatliche Deliverables

### Modell 3: Premium (Workshop + Implementation)
- Workshop-Thema mit Bezug zu {{BRANCHE_LABEL}}
- Dauer, Format und Teilnehmerkreis
- Preisband (qualitative Spanne)
- Follow-Up-Struktur und Upselling-Potenzial

{% if COMPANY_SIZE == "solo" %}
## SOLO-FOKUS
Priorisiere Modell 1 (Fixpreis) und Modell 3 (Workshop) — beides sofort umsetzbar
als Einzelperson. Retainer als ergänzende Option darstellen.
NICHT VERWENDEN: "Team aufbauen", "Mitarbeiter", "Abteilung", "Fachbereich".
STATTDESSEN: "Kapazität erweitern", "Ressourcen", "Arbeitsbereich".
{% elif COMPANY_SIZE == "team" %}
## TEAM-FOKUS
Alle drei Modelle gleichwertig darstellen. Kollaboration und Teamkapazitäten erwähnen.
{% else %}
## KMU-FOKUS
Alle drei Modelle mit Skalierungsperspektive. Enterprise-Optionen und
Volumenstaffelung ansprechen.
{% endif %}

## TEXTLÄNGE
150–200 Wörter. Kompakt, aber substanziell.

## OUTPUT-FORMAT
Antworte ausschließlich mit validem HTML-Fragment.
Verwende: `<section>`, `<h2>`, `<h4>`, `<ul>`, `<li>`, `<p>`, `<strong>`.
KEIN `<html>`, `<head>`, `<body>`. KEINE Markdown-Fences.

## GUARDRAILS (STRIKT!)
- KEINE konkreten €-Beträge (nur qualitative Spannen wie "niedriges/mittleres Segment")
- KEINE Marketing-Floskeln ("revolutionär", "einzigartig", "Gamechanger")
- KEINE Platzhalter (TBD, TODO, N/A)
- KEINE Assistenten-Sprache oder Fragen an den Leser
- KEINE Template-Variablen im Output
- Wenn Informationen fehlen, branchenübliche Einschätzung statt Platzhalter

## ANTI-REDUNDANZ
Monetarisierung ergänzt den Business Case, wiederholt ihn NICHT.
- Pricing-Logik und neue Umsatzquellen → HIER
- ROI-Berechnung und Amortisation → Business Case (eigener Abschnitt)
- Konkrete KI-Tools → Tools & Empfehlungen (eigener Abschnitt)
