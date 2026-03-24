# Prompt-Suite – Optimiert für DACH/EU

Diese Fassung ist nicht nur übersetzt, sondern für den deutschsprachigen und europäischen Business-Raum methodisch verbessert. Die Prompts sind copy-paste-fähig und stärker auf belastbare Management-Outputs ausgerichtet.

## Gemeinsamer Qualitätsrahmen für alle optimierten Prompts

Diese Regeln sollen **für alle 12 Prompts zusätzlich gelten**:

1. **Arbeite faktenbasiert und transparent.** Trenne sauber zwischen Fakten, Schätzungen, Annahmen und Hypothesen.
2. **Nutze standardmäßig EUR.** Ergänze lokale Währungen nur dort, wo sie für den Zielmarkt relevant sind.
3. **Nenne Datenstand und Unsicherheit.** Weise auf fehlende Daten, Proxy-Annahmen und methodische Grenzen hin.
4. **Berücksichtige DACH/EU-Kontext explizit.** Dazu gehören insbesondere Marktfragmentierung, Lokalisierung, Regulierung, Datenschutz, Beschaffung und unterschiedliche Länderlogiken.
5. **Nutze ein managementtaugliches Ausgabeformat.** Bevorzugt: Executive Summary, Methodik, Kernergebnisse, Risiken, Empfehlungen, Next Steps.
6. **Kennzeichne Zielkonflikte.** Zum Beispiel Wachstum vs. Profitabilität, Standardisierung vs. Lokalisierung, Geschwindigkeit vs. Compliance.
7. **Stelle nur dann Rückfragen, wenn zwingende Inputs fehlen.** Fehlen Daten, arbeite mit expliziten Annahmen statt mit stillschweigenden Lücken.
8. **Mache die Ergebnisse entscheidungsfähig.** Jede Analyse soll in priorisierte Handlungsoptionen oder Empfehlungen münden.

## 1. Marktgrößenbestimmung & TAM-Analyse

```text
Übernimm die Rolle eines Senior Market Strategist auf Tier-1-Beratungsniveau. Erstelle eine belastbare Marktgrößenanalyse für [PRODUKT / ANGEBOT] in [GEOGRAFIE] für [ZIELKUNDENSEGMENT].

Zusätzliche Anforderungen:
- Definiere den Markt eindeutig: relevante Produktkategorie, Kundenproblem, Preissegment und geografischer Zuschnitt.
- Berechne TAM, SAM und SOM mit einem Top-down- und einem Bottom-up-Ansatz.
- Nutze standardmäßig EUR; ergänze bei Bedarf lokale Währung und kennzeichne Wechselkursannahmen.
- Leite 3 Szenarien ab: konservativ, realistisch, ambitioniert.
- Ergänze eine 5-Jahres-CAGR-Projektion sowie die zentralen Wachstumstreiber und Bremsfaktoren.
- Vergleiche die Ergebnisse mit mindestens drei externen Marktreferenzen oder kennzeichne sauber, wo nur Annahmen möglich sind.
- Berücksichtige für DACH/EU: Marktfragmentierung, regulatorische Eintrittsbarrieren, Lokalisierung, Datenschutz- und Compliance-Anforderungen sowie länderspezifische Kaufkraftunterschiede.

Ausgabeformat:
1. Executive Summary
2. Marktdefinition und Methodik
3. TAM / SAM / SOM-Tabelle
4. Wachstumsprojektion über 5 Jahre
5. Vergleich mit externen Marktindikationen
6. Risiken, Unsicherheiten und wichtigste Annahmen
7. Investor-ready Summary Slide in komprimierter Form

Eingabe:
- Produkt / Angebot: [BESCHREIBUNG]
- Zielkunden: [SEGMENT]
- Geografie: [LAND / REGION / EU]
- Preismodell: [EINMALIG / SUBSCRIPTION / NUTZUNGSBASIERT / HYBRID]
- Relevante Annahmen oder vorhandene Daten: [OPTIONAL]
```

## 2. Wettbewerbsanalyse im Deep Dive

```text
Übernimm die Rolle eines Senior Competitive Strategy Lead. Erstelle eine belastbare Wettbewerbsanalyse für [BRANCHE / KATEGORIE] im relevanten Zielmarkt.

Zusätzliche Anforderungen:
- Unterscheide zwischen direkten Wettbewerbern, indirekten Wettbewerbern, Substituten und potenziellen neuen Marktteilnehmern.
- Bewerte Marktanteil nur dort, wo belastbare Daten oder nachvollziehbare Proxy-Indikatoren verfügbar sind.
- Vergleiche Preislogik, Leistungsumfang, Zielsegmente, Vertriebskanäle, Differenzierungsmerkmale und erkennbare Schwächen.
- Erstelle eine Positionierungskarte mit klar benannten Achsen.
- Identifiziere unbesetzte Marktsegmente, Nischen und strategische White Spaces.
- Bewerte die Wettbewerbsbedrohung je Anbieter auf einer 1-10-Skala und erkläre die Logik.
- Berücksichtige für DACH/EU: starke Marktfragmentierung, regionale Champions, Vertrieb über Partner, Ausschreibungslogik, Datenschutz- und Compliance-Anforderungen sowie Sprach-/Lokalisierungsbedarf.

Ausgabeformat:
1. Executive Summary
2. Wettbewerbslandschaft nach Kategorien
3. Vergleichstabelle der wichtigsten Anbieter
4. Positionierungskarte mit Erläuterung
5. White-Space-Analyse
6. Threat Rating je Anbieter mit Begründung
7. Strategische Implikationen für [UNTERNEHMEN]

Eingabe:
- Unternehmen / Angebot: [BESCHREIBUNG]
- Zielmarkt: [LAND / REGION / EU]
- Zielkundensegmente: [B2B / B2C / VERTIKAL]
- Relevante Wettbewerber, falls bekannt: [OPTIONAL]
```

## 3. Kundenpersona & Segmentierung

```text
Übernimm die Rolle eines Senior Customer Insights Lead. Entwickle vier belastbare Zielkundensegmente bzw. Personas für [PRODUKT / SERVICE].

Zusätzliche Anforderungen:
- Segmentiere nicht nur nach Demografie, sondern nach Bedürfnissen, Jobs-to-be-done, Kaufmotiven, Nutzungskontext und Zahlungsbereitschaft.
- Unterscheide, falls relevant, zwischen Nutzer, Käufer, Entscheider und Influencer.
- Beschreibe Pain Points, Kaufbarrieren, Trigger, bevorzugte Informationsquellen, Einwände und Preislogik.
- Leite konkrete Implikationen für Positionierung, Messaging, Angebotspaket und Kanäle ab.
- Berücksichtige für DACH/EU: Datenschutzsensibilität, Vertrauensaufbau, Qualitätserwartung, längere B2B-Entscheidungszyklen, Sprachraumunterschiede und regionale Mediengewohnheiten.

Ausgabeformat:
1. Segmentübersicht
2. Vier Personas mit strukturierter Steckbrief-Logik
3. Kaufbarrieren und Trigger je Persona
4. Kanal- und Content-Implikationen
5. Preis- und Angebotsimplikationen je Segment
6. Empfehlungen für Go-to-Market und Produktprioritäten

Eingabe:
- Produkt / Service: [BESCHREIBUNG]
- Branche / Kategorie: [BRANCHE]
- Zielmarkt: [LAND / REGION / EU]
- Bestehende Kundendaten oder Hypothesen: [OPTIONAL]
```

## 4. Branchen- und Trendanalyse

```text
Übernimm die Rolle eines Senior Industry Analyst. Erstelle einen strategischen Trendreport für [BRANCHE] mit Relevanz für [UNTERNEHMEN].

Zusätzliche Anforderungen:
- Unterscheide zwischen Makrotrends, Mikrotrends, Technologieumbrüchen, Kapitalmarkt- und Finanzierungsindikatoren.
- Bewerte die Relevanz jedes Trends nach Eintrittswahrscheinlichkeit, Zeithorizont und strategischem Einfluss.
- Nutze einen Zeithorizont von 0-12 Monaten, 1-3 Jahren und 3-5 Jahren.
- Leite konkrete Konsequenzen für Strategie, Produkt, Vertrieb, Preis und Betrieb ab.
- Berücksichtige für DACH/EU: regulatorische Dynamik, Energie- und Lohnkosten, Digitalisierungsgrad, industrielle Wertschöpfung, Datenschutz- und KI-Regulierung sowie Unterschiede zwischen USA- und EU-Finanzierungslogik.

Ausgabeformat:
1. Executive Summary
2. Fünf Makrokräfte
3. Sieben Mikrotrends der letzten 12 Monate
4. Kommende Technologieumbrüche
5. Kapital- und Investitionssignale
6. Zeithorizont-Matrix
7. „So what“: konkrete Implikationen für [UNTERNEHMEN]

Eingabe:
- Unternehmen: [BESCHREIBUNG]
- Branche: [BRANCHE]
- Zielmarkt: [LAND / REGION / EU]
- Besondere Fragestellungen: [OPTIONAL]
```

## 5. SWOT + Porters Five Forces

```text
Übernimm die Rolle eines Senior Strategy Advisor. Erstelle für [UNTERNEHMEN] eine kombinierte SWOT- und Porter’s-Five-Forces-Analyse mit klaren strategischen Konsequenzen.

Zusätzliche Anforderungen:
- Erarbeite eine differenzierte SWOT mit klaren, priorisierten Punkten.
- Verbinde SWOT und Five Forces in einer Kreuzanalyse: Welche Stärken helfen gegen welche Marktkräfte? Welche Schwächen verschärfen Risiken?
- Bewerte jede der fünf Kräfte auf einer 1-10-Skala und erläutere die Begründung.
- Leite daraus SO-, ST-, WO- und WT-Strategien ab.
- Berücksichtige für DACH/EU: Regulierung, Ausschreibungen, Zertifizierungen, Markteintrittsbarrieren, Abhängigkeit von Schlüsselzulieferern, Partnervertrieb und Fragmentierung.

Ausgabeformat:
1. Executive Summary
2. SWOT-Matrix
3. Five-Forces-Bewertung mit Punktzahl
4. Kreuzanalyse SWOT x Five Forces
5. Strategische Optionen nach Priorität
6. Risiken bei Nicht-Handeln

Eingabe:
- Unternehmen: [BESCHREIBUNG]
- Entwicklungsstufe: [IDEE / EARLY / GROWTH / ETABLIERT]
- Zielmarkt: [LAND / REGION / EU]
- Relevante Wettbewerbs- oder Beschaffungsbedingungen: [OPTIONAL]
```

## 6. Preisstrategieanalyse

```text
Übernimm die Rolle eines Senior Pricing Strategist. Entwickle eine tragfähige Preisstrategie für [PRODUKT / SERVICE].

Zusätzliche Anforderungen:
- Analysiere Preislogik, Paketierung, Abrechnungsmodell und Preisanker der Wettbewerber.
- Entwickle ein wertbasiertes Preismodell mit klarer Zahlungsbereitschaftslogik.
- Erarbeite drei Preisstufen mit klarer Feature-Abgrenzung und Upgrade-Logik.
- Definiere Rabattregeln, Freigabegrenzen und Margin-Schutz.
- Leite drei Umsatzszenarien ab und mache die zugrunde liegenden Annahmen transparent.
- Berücksichtige für DACH/EU: Nettopreis vs. Bruttopreis, Umsatzsteuer-Logik, längere B2B-Beschaffungszyklen, Rabattkultur, Jahresverträge, Datenschutz- und Compliance-Mehrwert sowie Preisvergleichbarkeit über Länder hinweg.

Ausgabeformat:
1. Executive Summary
2. Wettbewerbs- und Preislogik
3. Werttreiber und Zahlungsbereitschaft
4. Empfohlenes Pricing-Modell
5. Preisstufen und Leistungsumfang
6. Rabatt- und Promotionslogik
7. Umsatz- und Margenszenarien

Eingabe:
- Produkt / Service: [BESCHREIBUNG]
- Aktueller Preis: [PREIS]
- Kostenstruktur / Deckungsbeitrag: [KURZ BESCHREIBEN]
- Zielmarkt: [LAND / REGION / EU]
- Vertriebsmodell: [SELF-SERVE / SALES-LED / PARTNER]
```

## 7. Go-to-Market-Strategie

```text
Übernimm die Rolle eines Senior Go-to-Market Lead. Erstelle einen vollständigen GTM-Plan für [PRODUKT] im Zielmarkt [LAND / REGION / EU].

Zusätzliche Anforderungen:
- Definiere ICP / Zielsegmente, Wertversprechen, Kernbotschaften und Differenzierung.
- Plane Pre-Launch, Launch und die ersten 90 Tage nach Marktstart mit klaren Verantwortlichkeiten und Meilensteinen.
- Bewerte Akquisitionskanäle nach erwarteter Effizienz, Skalierbarkeit, Zeit bis Wirkung und Compliance.
- Entwickle eine Funnel-basierte Content- und Messaging-Strategie.
- Definiere 10 KPIs mit eindeutiger Formel, Zielwert und Messrhythmus.
- Leite Quick Wins für die ersten 14 Tage ab.
- Berücksichtige für DACH/EU: DSGVO-konforme Leadgenerierung, Double Opt-in, längere B2B-Sales-Zyklen, Partnervertrieb, Lokalisierung und Vertrauenssignale.

Ausgabeformat:
1. Executive Summary
2. Zielsegmente und Value Proposition
3. GTM-Roadmap 30 / 60 / 90+ Tage
4. Kanalpriorisierung
5. Messaging-Framework
6. Content-Plan je Funnel-Stufe
7. KPI-Set mit Benchmarks
8. Quick Wins und Frühindikatoren

Eingabe:
- Produkt: [BESCHREIBUNG]
- Zielmarkt: [MARKT]
- Budget: [BUDGET]
- Vertriebsmodell: [DIRECT / PARTNER / SELF-SERVE / HYBRID]
- Team / Ressourcen: [OPTIONAL]
```

## 8. Customer Journey Mapping

```text
Übernimm die Rolle eines Senior Customer Experience Strategist. Erstelle eine vollständige Customer Journey Map für [PRODUKT / SERVICE] entlang aller relevanten Phasen.

Zusätzliche Anforderungen:
- Nutze die Phasen Awareness, Consideration, Decision, Onboarding, Usage/Engagement, Loyalty/Expansion und Churn/Recovery.
- Beschreibe pro Phase Ziele, Kundenerwartungen, Emotionen, Verhaltensmuster, Kontaktpunkte, Pain Points und Optimierungschancen.
- Benenne für jede Phase die passenden KPIs, Systeme, Teams und Hebel.
- Leite konkrete Maßnahmen zur Conversion-, Retention- und Experience-Verbesserung ab.
- Berücksichtige für DACH/EU: Datenschutz- und Consent-Punkte, Service-Erwartungen, Sprache/Lokalisierung, Transparenzanforderungen und kanalübergreifende Konsistenz.

Ausgabeformat:
1. Executive Summary
2. Customer-Journey-Tabelle je Phase
3. Pain-Point-Analyse
4. Quick Wins vs. strukturelle Verbesserungen
5. KPI- und Tool-Matrix
6. Priorisierte Maßnahmenliste

Eingabe:
- Produkt / Service: [BESCHREIBUNG]
- Zielkundensegmente: [SEGMENTE]
- Kanäle / Touchpoints: [ONLINE / OFFLINE / PARTNER / CUSTOMER SUCCESS]
- Preis- und Vertragslogik: [OPTIONAL]
- Bestehende CX-Daten: [OPTIONAL]
```

## 9. Finanzmodellierung & Unit Economics

```text
Übernimm die Rolle eines Head of Finance / FP&A Lead. Erstelle ein belastbares Finanzmodell und eine Unit-Economics-Analyse für [UNTERNEHMEN].

Zusätzliche Anforderungen:
- Definiere sauber Umsatztreiber, Kostenblöcke, variable vs. fixe Kosten und zentrale Annahmen.
- Berechne CAC nach Kanal, LTV, LTV:CAC, Payback Period, Bruttomarge, Runway und Break-even.
- Erstelle ein 3-Jahres-Modell mit Szenarien und Sensitivitäten.
- Zeige die wichtigsten Frühindikatoren und finanziellen Red Flags.
- Berücksichtige für DACH/EU: Arbeitgebernebenkosten, Umsatzsteuerlogik, längere Zahlungsziele, Working Capital, Fördermittel, unterschiedliche Vertriebskanäle und ggf. Hardware-/Dienstleistungsmix.

Ausgabeformat:
1. Executive Summary
2. Annahmenübersicht
3. Umsatz- und Kostenmodell
4. Unit Economics
5. Cashflow, Burn und Runway
6. Szenarioanalyse
7. Red Flags und Steuerungsmaßnahmen

Eingabe:
- Geschäftsmodell: [BESCHREIBUNG]
- Aktueller Umsatz: [UMSATZ]
- Kostenstruktur: [KOSTEN]
- Zielmarkt: [LAND / REGION / EU]
- Verfügbare Finanzdaten: [OPTIONAL]
```

## 10. Risikobewertung & Szenarioplanung

```text
Übernimm die Rolle eines Enterprise Risk Lead. Erstelle ein belastbares Risk Assessment und eine Szenarioplanung für [UNTERNEHMEN / PROJEKT].

Zusätzliche Anforderungen:
- Identifiziere mindestens 15 wesentliche Risiken über Markt, Betrieb, Finanzen, Regulierung, Reputation, Technologie, Cyber, Daten und Personal hinweg.
- Bewerte jedes Risiko nach Eintrittswahrscheinlichkeit, Schadenshöhe, Geschwindigkeit des Eintritts und Kontrollierbarkeit.
- Benenne Frühwarnindikatoren, Verantwortlichkeiten sowie präventive und reaktive Maßnahmen.
- Erstelle Szenarien für Best Case, Base Case, Worst Case und Black Swan.
- Berücksichtige für DACH/EU: DSGVO, AI Act bzw. sektorale Regulierung, Lieferkettenabhängigkeiten, Energie- und Kostenvolatilität, Arbeitsrecht, Partner- und Plattformrisiken.

Ausgabeformat:
1. Executive Summary
2. Risiko-Register
3. Heatmap / Priorisierung
4. Frühwarnindikatoren
5. Mitigations- und Contingency-Plan
6. Szenariovergleich
7. Empfehlungen für Governance und Reporting

Eingabe:
- Unternehmen / Projekt: [BESCHREIBUNG]
- Entwicklungsstufe: [STUFE]
- Kritische Abhängigkeiten: [LIEFERANTEN / PLATTFORMEN / PERSONEN / REGULATORIK]
- Zielmarkt: [LAND / REGION / EU]
```

## 11. Markteintritts- & Expansionsstrategie

```text
Übernimm die Rolle eines Global Expansion Lead. Entwickle einen belastbaren Markteintritts- und Expansionsplan für [UNTERNEHMEN] in [ZIELMARKT].

Zusätzliche Anforderungen:
- Bewerte die Marktattraktivität anhand klarer Kriterien: Marktgröße, Wachstum, Wettbewerbsintensität, Margenpotenzial, Eintrittsbarrieren, regulatorische Komplexität und Umsetzungsaufwand.
- Vergleiche Eintrittsmodi wie Direktvertrieb, Partner, Distributor, digitale Expansion, Joint Venture oder Akquisition.
- Benenne Lokalisierungsanforderungen für Sprache, Preis, Produkt, Vertrieb, Support und Compliance.
- Berücksichtige für DACH/EU: Rechtsform, Steuern, Datenschutz, arbeitsrechtliche Fragen, länderspezifische Zertifizierungen, Ausschreibungen, Zahlungsgewohnheiten und Vertrieb über Partnernetzwerke.
- Leite eine realistische 12-Monats-Roadmap und KPI-Logik für 6 und 12 Monate ab.

Ausgabeformat:
1. Executive Summary
2. Marktattraktivitäts-Bewertung
3. Eintrittsmodus-Vergleich
4. Lokalisierungs- und Compliance-Anforderungen
5. 12-Monats-Roadmap
6. KPI-Set für 6 / 12 Monate
7. Risiken und Go / No-Go-Empfehlung

Eingabe:
- Unternehmen: [BESCHREIBUNG]
- Zielmarkt: [LAND / REGION]
- Verfügbare Ressourcen: [TEAM / BUDGET / PARTNER / ZEIT]
- Bisherige Internationalisierungserfahrung: [OPTIONAL]
```

## 12. Executive Strategy Synthesis

```text
Übernimm die Rolle eines Senior Strategy Advisor auf CEO-/Board-Niveau. Verdichte alle verfügbaren Informationen zu [UNTERNEHMEN] in eine klare, priorisierte Handlungsempfehlung.

Zusätzliche Anforderungen:
- Formuliere ein prägnantes Executive Summary ohne Floskeln.
- Beschreibe den Ist-Zustand faktenbasiert, schonungslos und mit klarer Priorisierung der Probleme.
- Leite drei strategische Optionen ab: defensiv, ausgewogen, offensiv.
- Vergleiche die Optionen nach Kapitalbedarf, Risiko, Umsetzbarkeit, Zeithorizont und strategischem Upside.
- Definiere die fünf wichtigsten Maßnahmen für die nächsten 90 Tage mit Owner, Zielbild und Erfolgskriterium.
- Berücksichtige für DACH/EU: Kapitaldisziplin, Profitabilitätsdruck, Compliance-Anforderungen, Investorenlogik, Lokalisierung und operative Realisierbarkeit.

Ausgabeformat:
1. Executive Summary
2. Ehrliche Ausgangslage
3. Drei strategische Pfade im Vergleich
4. Empfehlung mit Begründung
5. 90-Tage-Aktionsplan
6. Größtes Risiko und wichtigste Erkenntnis

Eingabe:
- Produkt: [BESCHREIBUNG]
- Markt: [LAND / REGION / EU]
- Entwicklungsstufe: [STUFE]
- Umsatz / Finanzen: [KENNZAHLEN]
- Ziele: [ZIELE]
- Größte Herausforderung: [HERAUSFORDERUNG]
```