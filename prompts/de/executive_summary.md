Developer:
<!-- executive_summary.md – v4.0 PLATIN++ KOMPAKT (max 6 Sätze Struktur)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences im OUTPUT.

     ZIEL:
     - Eine KOMPAKTE Executive Summary in genau 6 Sätzen.
     - Keine Wiederholung von Details – nur die Essenz.

     PFLICHTSTRUKTUR (6 Sätze – STRIKT EINHALTEN!):
     1. Ausgangslage (1 Satz): Branche + Größe + aktueller KI-Status
     2. Strategische Ziele (1 Satz): Was will das Unternehmen mit KI erreichen?
     3. Größter Pain Point (1 Satz): Der wichtigste Zeitfresser/Schmerzpunkt
     4. Quick Wins Ausblick (1 Satz): 2-3 konkrete Sofortmaßnahmen
     5. Roadmap Hinweis (1 Satz): 90-Tage und 12-Monats-Perspektive
     6. Guardrails/Risiken (1 Satz): Falls vorhanden, sonst Business-Case-Hinweis

     VERBOTEN:
     - Mehr als 6 Sätze
     - Keine Platzhalter-Strings
     - Keine technischen Pipeline-Begriffe
     - Keine Wiederholungen aus anderen Sektionen

     VERFÜGBARE VARIABLEN:
     - {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}

     GRÖSSENLOGIK:
     SOLO: Sie-Ansprache, keine Abteilungen, persönliche Entlastung
     TEAM: "Team", "Kolleg:innen", gemeinsame Routinen
     KMU: Teams, Bereiche, skalierbare Umsetzung

-->

<section class="section executive-summary">
  <h2>Executive Summary</h2>

  <p>
    <!-- SATZ 1: Ausgangslage -->
    Das Unternehmen in der Branche <strong>{{BRANCHE_LABEL}}</strong> (Größe: <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>)
    zeigt im Kernprozess <strong>{{HAUPTLEISTUNG}}</strong> ein solides Fundament für den KI-Einsatz,
    mit klaren Stärken und einzelnen Entwicklungsfeldern.

    <!-- SATZ 2: Strategische Ziele -->
    Strategisch steht die Entlastung bei wiederkehrenden Aufgaben und die Qualitätssteigerung
    durch standardisierte KI-Workflows im Mittelpunkt.

    <!-- SATZ 3: Größter Pain Point -->
    Der größte Hebel liegt bei zeitintensiven, manuellen Prozessen, die sich durch klare Vorlagen
    und KI-Unterstützung deutlich beschleunigen lassen.

    <!-- SATZ 4: Quick Wins -->
    Die Quick Wins umfassen konkrete Sofortmaßnahmen wie Vorlagen-Automatisierung,
    strukturierte Dokumentation und erste KI-gestützte Qualitätsprüfungen.

    <!-- SATZ 5: Roadmap -->
    Die 90-Tage-Roadmap setzt diese Maßnahmen um, während die 12-Monats-Perspektive
    Governance und Skalierung adressiert.

    <!-- SATZ 6: Risiken/Business Case -->
    Der Business Case ist positiv; Förderprogramme können die Anfangsinvestition zusätzlich reduzieren.
  </p>
</section>
