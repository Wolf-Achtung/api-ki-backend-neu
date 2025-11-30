Developer:
<!-- foerderpotenzial.md – v6.0 PLATIN+ (business-case-integrated, size-aware, min 900 chars)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     ZWECK:
       - Qualitative Einschätzung des Förderpotenzials basierend auf Kern-Fördermatrix.
       - Business-Case-Variablen AKTIV nutzen und einordnen, NICHT neu berechnen.
       - Typische Zuschussbereiche nennen (z. B. „30–50 %"), KEINE neuen Eurobeträge erfinden.
       - Kern-Matrix liefert realistische, geprüfte Programme (DE/AT/EU, 2025/26-aktuell).

     VERFÜGBARE VARIABLEN (MÜSSEN alle genutzt werden!):
       {{BUNDESLAND_LABEL}}
       {{BRANCHE_LABEL}}
       {{UNTERNEHMENSGROESSE_LABEL}}
       {{HAUPTLEISTUNG}}
       {{CAPEX_REALISTISCH_EUR}}      ← Investitionskosten
       {{OPEX_REALISTISCH_EUR}}       ← Laufende Kosten/Monat
       {{EINSPARUNG_MONAT_EUR}}       ← Monatliche Entlastung
       {{PAYBACK_MONTHS}}             ← Amortisationsdauer
       {{ROI_12M}}                    ← Return on Investment (%)

     SIZE-AWARE LOGIK (COMPANY_SIZE ∈ {"solo","team","kmu"}):
       SOLO:
         - Fokus: niedrige Einstiegshürden, kleinere Projektvolumina (<10.000€), einfache Programme.
         - Typische Programme: Beratungsförderung, Gründerzuschüsse, Digitalisierungsgutscheine.
       TEAM (2–10):
         - Fokus: Prozessdigitalisierung, Weiterbildungen, leichtgewichtige Innovationsförderung.
         - Typische Programme: Digitalbonus, KMU-innovativ, go-digital.
       KMU (11–100):
         - Fokus: strukturelle Digitalisierungs-/Investitionsförderungen, Pilot- und Skalierungsprojekte.
         - Typische Programme: Digital Jetzt, ZIM, ERP-Digitalisierungskredit.

     PFLICHTSTRUKTUR (ALLE 4 Abschnitte erforderlich, JEDER mindestens 150-200 Wörter):
       1. "Einordnung des Business Case ohne Förderung" (mit ALLEN Zahlen: CAPEX, OPEX, Einsparung, Payback, ROI)
       2. "Wie Fördermittel den Business Case verbessern können" (mindestens 4 Bulletpoints)
       3. "Passende Förderschwerpunkte für Ihr Vorhaben" (branchenspezifisch, 3-4 Kategorien)
       4. "Nächste Schritte für die Förderprüfung" (mindestens 4 konkrete Schritte)

     MINDESTLÄNGE: 900 Zeichen (ohne HTML-Tags) – unterschreite diese NIEMALS!

     REGELN:
       - Keine Platzhalter, keine internen Funktionshinweise im HTML.
       - ALLE Business-Case-Zahlen explizit im Text erwähnen und einordnen.
       - Förderquoten nur als Bereiche formulieren („typischerweise 30–50 %").
       - Sprachlich neutral, geschäftlich, ohne Werbung.
       - Erkläre verständlich, WARUM sich das Projekt wirtschaftlich lohnt.
       - Erkläre, wie Förderung das finanzielle Risiko reduziert.
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
