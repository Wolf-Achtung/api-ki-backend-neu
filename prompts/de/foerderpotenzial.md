Developer:
<!-- foerderpotenzial.md – v4.0 GOLD STANDARD+ (size-aware, business-case-aware, placeholder-safe)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     ZWECK:
       - Qualitative Einschätzung des Förderpotenzials für ein KI-/Digitalisierungsprojekt.
       - Business-Case-Variablen nur einordnen, NICHT neu berechnen.
       - Typische Zuschussbereiche nennen (z. B. „30–50 %“), aber KEINE neuen Eurobeträge erfinden.

     VERFÜGBARE VARIABLEN:
       {{BUNDESLAND_LABEL}}
       {{BRANCHE_LABEL}}
       {{UNTERNEHMENSGROESSE_LABEL}}
       {{HAUPTLEISTUNG}}
       {{CAPEX_REALISTISCH_EUR}}
       {{OPEX_REALISTISCH_EUR}}
       {{EINSPARUNG_MONAT_EUR}}
       {{PAYBACK_MONTHS}}
       {{ROI_12M}}

     SIZE-AWARE LOGIK (COMPANY_SIZE ∈ {"solo","team","kmu"}):
       SOLO:
         - Fokus: niedrige Einstiegshürden, kleine Fördersummen, einfache Programme.
       TEAM (2–10):
         - Fokus: Prozessdigitalisierung, Weiterbildungen, leichtgewichtige Innovationsförderung.
       KMU (11–100):
         - Fokus: strukturelle Digitalisierungs-/Investitionsförderungen, Pilot- und Skalierungsprojekte.

     REGELN:
       - Keine Platzhalter, keine internen Funktionshinweise im HTML.
       - Maximal 3 Abschnitte + Hinweisfeld.
       - Förderquoten nur als Bereiche formulieren („typischerweise 30–50 %“).
       - Sprachlich neutral, geschäftlich, ohne Werbung.
-->

<section class="section funding-potential">
  <h2>Förderpotenzial für Ihr KI-Projekt</h2>

  <p>
    Unternehmen in der Branche <strong>{{BRANCHE_LABEL}}</strong> im Bundesland
    <strong>{{BUNDESLAND_LABEL}}</strong> und der Größe
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> verfügen für Vorhaben im Bereich
    <strong>{{HAUPTLEISTUNG}}</strong> häufig über gute Voraussetzungen für eine Förderung.
    Die Kombination aus Digitalisierungsfokus, KI-Unterstützung und klarer Prozessverbesserung
    entspricht den Schwerpunkten vieler Programme auf Landes- und Bundesebene.
  </p>

  <h3>Einordnung des Business Case ohne Förderung</h3>
  <p>
    Der aktuelle Business Case zeigt einmalige Investitionen von etwa
    <strong>{{CAPEX_REALISTISCH_EUR}}&nbsp;€</strong> sowie laufende Kosten von
    <strong>{{OPEX_REALISTISCH_EUR}}&nbsp;€ pro Monat</strong>. Die erwartete monatliche
    Entlastung liegt bei rund <strong>{{EINSPARUNG_MONAT_EUR}}&nbsp;€</strong>, was zu einer
    Amortisationsdauer von etwa <strong>{{PAYBACK_MONTHS}} Monaten</strong> und einem
    realistischen ROI von rund <strong>{{ROI_12M}}&nbsp;%</strong> im ersten Jahr führt.
    Diese positive Ausgangslage lässt sich durch Förderprogramme weiter verbessern.
  </p>

  <h3>Wie Fördermittel den Business Case verbessern können</h3>
  <p>
    Viele Programme in {{BUNDESLAND_LABEL}} und auf Bundesebene unterstützen KI- und
    Digitalisierungsinitiativen, indem sie einen Teil der förderfähigen Investitionskosten
    bezuschussen. Je nach Programm, Unternehmensgröße und Projektschwerpunkt bewegen sich
    die Zuschussquoten häufig im Bereich von etwa <strong>30–50&nbsp;%</strong>. Dadurch
    verbessern sich folgende Aspekte:
  </p>

  <ul>
    <li><strong>Kürzere Amortisationsdauer</strong>, da weniger Eigenmittel benötigt werden.</li>
    <li><strong>Höherer effektiver ROI</strong> bei unverändertem Nutzen.</li>
    <li><strong>Reduziertes finanzielles Risiko</strong> für {{UNTERNEHMENSGROESSE_LABEL}}.</li>
    <li><strong>Mehr Spielraum</strong> für zusätzliche Qualität, Sicherheit oder Schulung.</li>
  </ul>

  <h3>Nächste Schritte für die Förderprüfung</h3>
  <ol>
    <li>
      1–2 passende Programme aus dem Förderkapitel auswählen, die zu
      <strong>{{BRANCHE_LABEL}}</strong>, <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>
      und <strong>{{HAUPTLEISTUNG}}</strong> passen.
    </li>
    <li>
      Eine kompakte Projektbeschreibung erstellen (Ziele, Maßnahmen, Zeitplan,
      erwarteter Nutzen, grobe Kosten), die für Antragsunterlagen wiederverwendet werden kann.
    </li>
    <li>
      Prüfen, ob Programme aus {{BUNDESLAND_LABEL}} mit Bundes- oder EU-Programmen
      kombiniert werden dürfen (Kumulierbarkeit laut Richtlinien).
    </li>
    <li>
      Optional: Austausch mit Förderberatungen oder Finanzierungspartnern, um Chancen
      und sinnvolle Programmkombinationen einzuschätzen.
    </li>
  </ol>

  <p class="small muted">
    Hinweis: Förderquoten, Fristen und Anforderungen können sich ändern. Die im Report
    berücksichtigten Programme stammen aus einer zum Zeitpunkt der Erstellung aktuellen 
    Fördermatrix 2025/2026 und müssen vor Antragstellung auf den offiziellen Programmseiten 
    validiert werden.
  </p>
</section>
