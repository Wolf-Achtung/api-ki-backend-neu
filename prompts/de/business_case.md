<!-- business_case.md – v2.3 GOLD STANDARD+ ROI & SIZE
     Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences. -->

<!-- KONTEXT-VARIABLEN
     {{BRANCHE_LABEL}}
     {{COMPANY_SIZE}} in {solo, team, kmu}
     {{HAUPTLEISTUNG}}
     {{BUNDESLAND_LABEL}} (für qualitative Förder-Hinweise, keine eigenen Zahlen!)
     {{CAPEX_REALISTISCH_EUR}}
     {{OPEX_REALISTISCH_EUR}}
     {{EINSPARUNG_MONAT_EUR}}
     {{PAYBACK_MONTHS}}
     {{ROI_12M}}
-->

<section class="section business-case">
  <h2>Business-Case – Wirtschaftlichkeit der KI-Lösung</h2>

  <p>
    Der folgende Business-Case fasst die wirtschaftlichen Effekte der geplanten
    KI-Unterstützung für <strong>{{HAUPTLEISTUNG}}</strong> in der Branche
    <strong>{{BRANCHE_LABEL}}</strong> zusammen. Die Interpretation orientiert sich
    an Ihrer Unternehmensgröße <strong>{{COMPANY_SIZE}}</strong> und den realistisch
    geschätzten Investitions- und Einsparungswerten.
  </p>

  <p>
    <strong>Investition & laufende Kosten:</strong>
    Einmalige Aufwände (CAPEX) von rund {{CAPEX_REALISTISCH_EUR}} für Implementierung,
    Setup und erste Anpassungen sowie laufende Betriebskosten (OPEX) von etwa
    {{OPEX_REALISTISCH_EUR}} pro Monat.
  </p>

  <p>
    <strong>Monatliche Einsparung:</strong>
    Basierend auf den Quick Wins und den angegebenen Volumina ergibt sich eine
    realistische Entlastung von ungefähr {{EINSPARUNG_MONAT_EUR}} pro Monat.
    Auf dieser Basis amortisiert sich die Investition nach rund
    {{PAYBACK_MONTHS}} Monaten; der erwartete ROI im ersten Jahr liegt bei
    etwa {{ROI_12M}} %.
  </p>

  <h3>Einordnung nach Unternehmensgröße</h3>
  <p>
    Für {{COMPANY_SIZE}} bedeutet diese Relation aus CAPEX, OPEX und Einsparung,
    dass die Investition vor allem dann attraktiv ist, wenn die neue Arbeitsweise
    im Kernprozess {{HAUPTLEISTUNG}} konsequent genutzt wird. Bei sehr geringer
    Auslastung verlängert sich die Amortisation entsprechend; bei hoher Nutzung
    kann sie sich deutlich verkürzen.
  </p>

  <h3>Sensitivität (+/− 20 %)</h3>
  <p>
    Fällt die tatsächliche Einsparung etwa 20 % niedriger aus als angenommen,
    verlängert sich die Amortisationsdauer entsprechend – der Business-Case bleibt
    jedoch in der Regel tragfähig, solange {{PAYBACK_MONTHS}} Monate für Sie
    akzeptabel sind. Liegt die Einsparung 20 % höher, verbessert sich der ROI
    deutlich und die Investition spielt sich schneller wieder ein.
  </p>

  <h3>Hebel zur Verbesserung des ROI</h3>
  <ul>
    <li>
      <strong>Nutzung ausweiten:</strong>
      Mehr Vorgänge/Kampagnen/Projekte über den neuen KI-Workflow laufen lassen,
      sodass die Fixkosten auf mehr Fälle verteilt werden.
    </li>
    <li>
      <strong>Weitere Use Cases ergänzen:</strong>
      Auf derselben Infrastruktur zusätzliche Teilprozesse von {{HAUPTLEISTUNG}}
      automatisieren (z. B. Voranalyse, Reporting, Qualitätssicherung).
    </li>
    <li>
      <strong>Preis-/Leistungsmodell optimieren:</strong>
      Dort, wo Ihr Geschäftsmodell es zulässt (z. B. Beratung, Agenturen, Medien),
      den durch KI erhöhten Wert pro Projekt/Leistung in Honoraren oder Paketen
      abbilden.
    </li>
    <li>
      <strong>Förderungen nutzen:</strong>
      Falls im Report passende Förderprogramme für {{BUNDESLAND_LABEL}} genannt werden,
      können diese die effektive Anfangsinvestition senken – ohne zusätzliche
      Zahlen zu erfinden.
    </li>
  </ul>

  <h3>Fazit</h3>
  <p>
    Insgesamt ergibt sich ein konservativer, aber tragfähiger Business-Case:
    Die Investition in KI für {{HAUPTLEISTUNG}} lässt sich mit den vorhandenen Zahlen
    nachvollziehbar begründen. Entscheidend ist, dass die Quick Wins zügig umgesetzt,
    die Nutzung konsequent gesteigert und Governance-/Qualitätsanforderungen
    parallel berücksichtigt werden.
  </p>
</section>
