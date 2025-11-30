Developer:
<!-- foerderpotenzial.md – v7.0 PLATIN+ STABILIZED (business-case-integrated, size-aware, min 900 WÖRTER)

     ╔══════════════════════════════════════════════════════════════════════════════╗
     ║  KRITISCH: MINDESTLÄNGE = 900 WÖRTER (nicht Zeichen!)                        ║
     ║  Antworte IMMER mit einem VOLLSTÄNDIGEN, AUSFÜHRLICHEN Text.                 ║
     ║  Kurze Antworten sind INAKZEPTABEL und führen zu Validierungsfehlern.        ║
     ╚══════════════════════════════════════════════════════════════════════════════╝

     AUSGABEFORMAT:
       - Antworte ausschließlich mit validem HTML.
       - KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     ZWECK:
       - Qualitative Einschätzung des Förderpotenzials basierend auf Kern-Fördermatrix.
       - Business-Case-Variablen AKTIV nutzen und einordnen, NICHT neu berechnen.
       - Typische Zuschussbereiche nennen (z. B. „30–50 %"), KEINE neuen Eurobeträge erfinden.
       - Kern-Matrix liefert realistische, geprüfte Programme (DE/AT/EU, 2025/26-aktuell).

     VERFÜGBARE VARIABLEN (MÜSSEN ALLE im Text verwendet werden!):
       {{BUNDESLAND_LABEL}}           ← Bundesland des Unternehmens
       {{BRANCHE_LABEL}}              ← Branche des Unternehmens
       {{UNTERNEHMENSGROESSE_LABEL}}  ← Größenkategorie (Solo/Team/KMU)
       {{HAUPTLEISTUNG}}              ← Kernleistung des Unternehmens
       {{CAPEX_REALISTISCH_EUR}}      ← Investitionskosten (einmalig)
       {{OPEX_REALISTISCH_EUR}}       ← Laufende Kosten pro Monat
       {{EINSPARUNG_MONAT_EUR}}       ← Monatliche Entlastung/Einsparung
       {{PAYBACK_MONTHS}}             ← Amortisationsdauer in Monaten
       {{ROI_12M}}                    ← Return on Investment nach 12 Monaten (%)

     SIZE-AWARE LOGIK (COMPANY_SIZE ∈ {"solo","team","kmu"}):
       SOLO:
         - Fokus: niedrige Einstiegshürden, kleinere Projektvolumina (<10.000€), einfache Programme.
         - Typische Programme: Beratungsförderung, Gründerzuschüsse, Digitalisierungsgutscheine.
         - Förderquoten: häufig 50-80% bei Beratung, 30-50% bei Investitionen.
       TEAM (2–10):
         - Fokus: Prozessdigitalisierung, Weiterbildungen, leichtgewichtige Innovationsförderung.
         - Typische Programme: Digitalbonus, KMU-innovativ, go-digital.
         - Förderquoten: typisch 40-60% bei Digitalisierung, bis 50% bei Innovation.
       KMU (11–100):
         - Fokus: strukturelle Digitalisierungs-/Investitionsförderungen, Pilot- und Skalierungsprojekte.
         - Typische Programme: Digital Jetzt, ZIM, ERP-Digitalisierungskredit.
         - Förderquoten: typisch 30-50%, bei ZIM bis 55% möglich.

     ╔══════════════════════════════════════════════════════════════════════════════╗
     ║  PFLICHTSTRUKTUR – ALLE 4 ABSCHNITTE MÜSSEN VOLLSTÄNDIG AUSGEFÜHRT WERDEN!   ║
     ╚══════════════════════════════════════════════════════════════════════════════╝

     ABSCHNITT 1: "Einordnung des Business Case ohne Förderung" (mind. 200-250 Wörter)
       PFLICHTINHALTE:
       - Nenne EXPLIZIT alle 5 Zahlen: CAPEX, OPEX, Einsparung, Payback, ROI
       - Ordne jede Zahl im Kontext der Branche {{BRANCHE_LABEL}} ein
       - Erkläre, warum der Business Case auch ohne Förderung tragfähig ist
       - Beschreibe die wirtschaftliche Attraktivität des Projekts
       - Gehe auf die Besonderheiten für {{UNTERNEHMENSGROESSE_LABEL}} ein

     ABSCHNITT 2: "Wie Fördermittel den Business Case verbessern können" (mind. 250-300 Wörter)
       PFLICHTINHALTE (MINDESTENS 5 ausführliche Bulletpoints):
       - Kürzere Amortisationsdauer: konkrete Rechnung mit {{PAYBACK_MONTHS}}
       - Höherer effektiver ROI: wie sich {{ROI_12M}}% durch Förderung verdoppeln kann
       - Reduziertes finanzielles Risiko: Bezug auf {{CAPEX_REALISTISCH_EUR}}
       - Mehr Spielraum für Qualität und Schulung: wie Einsparungen genutzt werden können
       - Bessere Planungssicherheit: Projektbudget-Planung mit bewilligter Förderung
       - Optional: Skalierungsmöglichkeiten, Team-Entwicklung, Innovation

     ABSCHNITT 3: "Passende Förderschwerpunkte für Ihr Vorhaben" (mind. 200-250 Wörter)
       PFLICHTINHALTE (MINDESTENS 4 Förderkategorien mit Erklärung):
       - Digitalisierungsförderung: spezifisch für {{HAUPTLEISTUNG}}
       - Innovationsförderung: branchenspezifisch für {{BRANCHE_LABEL}}
       - Qualifizierungsförderung: Schulungen und Kompetenzaufbau
       - Beratungsförderung: externe Expertise und Strategieentwicklung
       - Jede Kategorie mit 2-3 Sätzen Erklärung und Relevanz

     ABSCHNITT 4: "Nächste Schritte für die Förderprüfung" (mind. 200-250 Wörter)
       PFLICHTINHALTE (MINDESTENS 5 konkrete Schritte):
       1. Programmauswahl mit Bezug auf {{BRANCHE_LABEL}} und {{BUNDESLAND_LABEL}}
       2. Projektbeschreibung mit Bezug auf {{CAPEX_REALISTISCH_EUR}}
       3. Kumulierungsprüfung für {{BUNDESLAND_LABEL}}
       4. Beratung einholen (Kammern, Förderberatungen)
       5. Zeitplanung (4-8 Wochen Vorlauf einplanen)
       - Jeden Schritt mit 2-3 Sätzen erklären

     ╔══════════════════════════════════════════════════════════════════════════════╗
     ║  ABSOLUTE MINDESTLÄNGE: 900 WÖRTER Gesamttext (ohne HTML-Tags)               ║
     ║  Ziel: 900-1200 Wörter für vollständige, professionelle Analyse              ║
     ║  NIEMALS kürzer als 900 Wörter antworten!                                    ║
     ╚══════════════════════════════════════════════════════════════════════════════╝

     REGELN:
       - Keine Platzhalter, keine internen Funktionshinweise im HTML.
       - ALLE Business-Case-Zahlen EXPLIZIT im Text erwähnen und einordnen.
       - Förderquoten nur als Bereiche formulieren („typischerweise 30–50 %").
       - Sprachlich neutral, geschäftlich, ohne Werbung.
       - Erkläre verständlich, WARUM sich das Projekt wirtschaftlich lohnt.
       - Erkläre, wie Förderung das finanzielle Risiko reduziert.
       - Jeder Abschnitt muss AUSFÜHRLICH und VOLLSTÄNDIG sein.
-->

<section class="section funding-potential">
  <h2>Förderpotenzial für Ihr KI-Projekt</h2>

  <p>
    Unternehmen in der Branche <strong>{{BRANCHE_LABEL}}</strong> im Bundesland
    <strong>{{BUNDESLAND_LABEL}}</strong> und der Größe
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> verfügen für Vorhaben im Bereich
    <strong>{{HAUPTLEISTUNG}}</strong> häufig über gute Voraussetzungen für eine Förderung.
    Die Kombination aus Digitalisierungsfokus, KI-Unterstützung und klarer Prozessverbesserung
    entspricht den Schwerpunkten vieler Programme auf Landes- und Bundesebene – unabhängig davon,
    ob es sich um ein Solo-Unternehmen, ein kleines Team oder ein wachsendes KMU handelt.
  </p>

  <h3>1. Einordnung des Business Case ohne Förderung</h3>
  <p>
    Der aktuelle Business Case zeigt einmalige Investitionen von etwa
    <strong>{{CAPEX_REALISTISCH_EUR}}&nbsp;€</strong> sowie laufende Kosten von
    rund <strong>{{OPEX_REALISTISCH_EUR}}&nbsp;€ pro Monat</strong>. Die erwartete
    monatliche Entlastung liegt bei ungefähr
    <strong>{{EINSPARUNG_MONAT_EUR}}&nbsp;€</strong>, was zu einer
    Amortisationsdauer von etwa <strong>{{PAYBACK_MONTHS}} Monaten</strong> und
    einem realistischen ROI von rund <strong>{{ROI_12M}}&nbsp;%</strong> im ersten Jahr führt.
  </p>
  <p>
    Diese Ausgangslage ist für viele Förderstellen attraktiv: Das Projekt ist betriebswirtschaftlich
    plausibel, der Nutzen klar erkennbar und der Eigenbeitrag – je nach Unternehmensgröße –
    grundsätzlich tragfähig. Fördermittel können diese Situation zusätzlich verbessern, indem
    sie einen Teil der Investitionsbelastung abfedern.
  </p>
  <p>
    Konkret bedeutet das für ein Unternehmen der Größe <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>
    in der Branche <strong>{{BRANCHE_LABEL}}</strong>: Die Investition von {{CAPEX_REALISTISCH_EUR}}&nbsp;€
    amortisiert sich bei einer monatlichen Einsparung von {{EINSPARUNG_MONAT_EUR}}&nbsp;€ nach etwa
    {{PAYBACK_MONTHS}} Monaten. Der ROI von {{ROI_12M}}&nbsp;% zeigt, dass sich das Projekt auch ohne
    externe Unterstützung wirtschaftlich rechnet – mit Förderung wird die Rentabilität noch deutlich attraktiver.
  </p>

  <h3>2. Wie Fördermittel den Business Case verbessern können</h3>
  <p>
    Viele Programme in {{BUNDESLAND_LABEL}} und auf Bundesebene unterstützen KI- und
    Digitalisierungsinitiativen, indem sie einen Teil der förderfähigen Investitionskosten
    bezuschussen. Je nach Programm, Unternehmensgröße und Projektschwerpunkt bewegen sich
    die Zuschussquoten typischerweise im Bereich von etwa
    <strong>30–50&nbsp;%</strong> der anerkannten Kosten. Für ein Investitionsvolumen von
    {{CAPEX_REALISTISCH_EUR}}&nbsp;€ könnte das eine Entlastung von
    mehreren tausend Euro bedeuten.
  </p>

  <ul>
    <li>
      <strong>Kürzere Amortisationsdauer:</strong>
      Durch eine Beteiligung an den Investitionskosten sinkt der Eigenanteil; die Amortisation
      kann sich von {{PAYBACK_MONTHS}} Monaten auf deutlich weniger verkürzen, ohne dass der
      erwartete Nutzen verändert wird.
    </li>
    <li>
      <strong>Höherer effektiver ROI:</strong>
      Wenn ein Teil der Investitionen über Zuschüsse abgedeckt wird, steigt der Effektiv-Ertrag
      je eingesetztem Euro – der aktuelle ROI von {{ROI_12M}}&nbsp;% kann sich bei 40%
      Förderung auf über das Doppelte erhöhen.
    </li>
    <li>
      <strong>Reduziertes finanzielles Risiko:</strong>
      Für <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> kann ein Zuschuss den Schritt in ein
      ambitionierteres Projekt erleichtern, ohne die Liquidität unnötig zu belasten. Die
      laufenden Kosten von {{OPEX_REALISTISCH_EUR}}&nbsp;€/Monat bleiben dabei tragbar.
    </li>
    <li>
      <strong>Mehr Spielraum für Qualität und Schulung:</strong>
      Einsparungen durch Förderung können genutzt werden, um zusätzliche Maßnahmen für
      Qualität, Sicherheit oder Qualifizierung vorzusehen – wichtig für nachhaltige KI-Nutzung.
    </li>
    <li>
      <strong>Bessere Planungssicherheit:</strong>
      Mit bewilligter Förderung lässt sich das Projektbudget verlässlicher planen und das
      Risiko bei unerwarteten Mehrkosten besser abfedern.
    </li>
  </ul>

  <h3>3. Passende Förderschwerpunkte für Ihr Vorhaben</h3>
  <p>
    Basierend auf der Branche <strong>{{BRANCHE_LABEL}}</strong>, dem Schwerpunkt
    <strong>{{HAUPTLEISTUNG}}</strong> und der Unternehmensgröße
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> kommen folgende Förderkategorien in Frage:
  </p>
  <ul>
    <li>
      <strong>Digitalisierungsförderung:</strong>
      Programme für KI-gestützte Prozessoptimierung, Automatisierung und digitale Werkzeuge.
    </li>
    <li>
      <strong>Innovationsförderung:</strong>
      Zuschüsse für neuartige KI-Anwendungen, Pilotprojekte und Technologieentwicklung.
    </li>
    <li>
      <strong>Qualifizierungsförderung:</strong>
      Mittel für Schulungen, Weiterbildungen und den Aufbau von KI-Kompetenzen im Team.
    </li>
    <li>
      <strong>Beratungsförderung:</strong>
      Unterstützung für externe Expertise bei der KI-Strategieentwicklung und Umsetzung.
    </li>
  </ul>

  <h3>4. Nächste Schritte für die Förderprüfung</h3>
  <ol>
    <li>
      <strong>Programmauswahl:</strong> 1–2 Programme aus dem Förderkapitel auswählen, die zu
      <strong>{{BRANCHE_LABEL}}</strong>, <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>
      und <strong>{{HAUPTLEISTUNG}}</strong> passen (z.&nbsp;B. mit Fokus auf
      Digitalisierungsprojekte, Prozessoptimierung oder Qualifizierung).
    </li>
    <li>
      <strong>Projektbeschreibung:</strong> Eine kompakte Projektbeschreibung erstellen (Ziele, Maßnahmen, Zeitplan,
      erwarteter Nutzen, grobe Kosten mit Bezug auf die berechneten {{CAPEX_REALISTISCH_EUR}}&nbsp;€),
      die als Grundlage für Antragsunterlagen und interne Entscheidungen genutzt werden kann.
    </li>
    <li>
      <strong>Kumulierungsprüfung:</strong> Prüfen, ob Programme aus {{BUNDESLAND_LABEL}} mit Bundes- oder EU-Programmen
      kombiniert werden dürfen und welche Vorgaben für Kumulierung gelten.
    </li>
    <li>
      <strong>Beratung einholen:</strong> Optional Rücksprache mit Förderberatungen, Kammern oder Finanzierungspartnern halten,
      um Chancen, Aufwand und sinnvolle Programmkombinationen realistisch einzuschätzen.
    </li>
    <li>
      <strong>Zeitplanung:</strong> Förderanträge benötigen typischerweise 4–8 Wochen Vorlauf – dies bei der
      Projektplanung berücksichtigen und frühzeitig mit der Antragsvorbereitung beginnen.
    </li>
  </ol>

  <p class="small muted">
    Hinweis: Förderquoten, Fristen und Anforderungen können sich ändern. Die hier
    beschriebenen Einschätzungen beziehen sich auf Programme, die im Rahmen einer
    aktuellen Fördermatrix (2025/2026) berücksichtigt wurden. Vor Antragstellung
    sollten die offiziellen Richtlinien und Konditionen der jeweiligen Programme
    im Detail geprüft werden.
  </p>
</section>
