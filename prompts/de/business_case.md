Developer:
<!-- business_case.md – v3.0 GOLD STANDARD+ (ROI, CAPEX/OPEX, size-aware)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     VERFÜGBARE VARIABLEN:
       {{BRANCHE_LABEL}}
       {{COMPANY_SIZE}}            // solo | team | kmu
       {{HAUPTLEISTUNG}}
       {{BUNDESLAND_LABEL}}
       {{CAPEX_REALISTISCH_EUR}}
       {{OPEX_REALISTISCH_EUR}}
       {{EINSPARUNG_MONAT_EUR}}
       {{PAYBACK_MONTHS}}
       {{ROI_12M}}

     REGELN:
       - Keine eigenen Zahlen erfinden. Ausschließlich die Variablen nutzen.
       - „rund / etwa / ca.“ zur sprachlichen Einordnung erlaubt.
       - Keine Förderquoten nennen (dafür eigenes Kapitel).
       - Output = valides HTML-Fragment.
       - Größe (solo/team/kmu) beeinflusst NUR die narrative Einordnung, nicht die Zahlen.
-->

<section class="section business-case">
  <h2>Business Case – Investition und erwarteter Nutzen</h2>

  <p>
    Für ein Unternehmen in der Branche <strong>{{BRANCHE_LABEL}}</strong> mit der Größe
    <strong>{{COMPANY_SIZE}}</strong> ist der Prozess <strong>{{HAUPTLEISTUNG}}</strong>
    ein zentraler Hebel der Wertschöpfung. Der folgende Business Case zeigt auf,
    welche finanziellen Wirkungen eine systematische Nutzung von KI realistisch entfalten kann.
  </p>

  <h3>Investition und laufende Kosten</h3>
  <p>
    Die einmaligen Aufwände für Aufbau und Einführung liegen bei rund
    <strong>{{CAPEX_REALISTISCH_EUR}}&nbsp;€</strong>. Hinzu kommen monatliche Betriebskosten
    von etwa <strong>{{OPEX_REALISTISCH_EUR}}&nbsp;€</strong> – hauptsächlich für den KI-Einsatz,
    Infrastruktur, Tools und potenzielle Lizenzen.
  </p>

  <h3>Monatlicher Effekt im Kerngeschäft</h3>
  <p>
    Im täglichen Einsatz ist eine realistische Entlastung von rund
    <strong>{{EINSPARUNG_MONAT_EUR}}&nbsp;€ pro Monat</strong> erreichbar. Sie entsteht aus
    Zeitgewinn, geringeren manuellen Schleifen und einer konsistenteren Ergebnisqualität.
    Voraussetzung ist, dass der neue Workflow im Alltag konsequent genutzt wird.
  </p>

  <h3>Amortisation und ROI</h3>
  <p>
    Unter diesen Annahmen amortisiert sich die Investition nach etwa
    <strong>{{PAYBACK_MONTHS}} Monaten</strong>. Auf zwölf Monate gerechnet ergibt sich ein
    erwarteter Return on Investment von <strong>{{ROI_12M}}&nbsp;%</strong>.
    Dieser Wert dient als realistische Orientierung und zeigt die wirtschaftliche Tragfähigkeit des Vorhabens.
  </p>

  <h3>Einordnung nach Unternehmensgröße</h3>
  <p>
    Für <strong>{{COMPANY_SIZE}}</strong> gilt: Je stärker der Prozess
    <strong>{{HAUPTLEISTUNG}}</strong> auf wiederkehrenden, standardisierbaren Aufgaben beruht,
    desto schneller wirkt sich die Investition aus. Bei konsequenter Nutzung verkürzt sich die
    Amortisation spürbar; bei geringerer Auslastung verlängert sie sich entsprechend.
  </p>

  <h3>Verbindung zu Fördermöglichkeiten (qualitativ)</h3>
  <p>
    In <strong>{{BUNDESLAND_LABEL}}</strong> existieren Programme, die KI- und
    Digitalisierungsprojekte unterstützen können. Werden Teile der einmaligen Investition
    gefördert, verbessert sich der Business Case durch eine verkürzte Amortisationsdauer
    und einen höheren effektiven ROI. Konkrete Programme und Details werden im
    Förderkapitel erläutert.
  </p>

  <p class="small muted">
    Hinweis: Diese Darstellung dient als transparente Orientierung. Für Investitionsentscheidungen
    empfiehlt sich die Ergänzung um konservative, Basis- und optimistische Szenarien.
  </p>
</section>

<!-- OUTPUT-VORGABEN:
     - Antworte nur mit dem HTML-Fragment oben.
     - Keine zusätzlichen Kommentare oder Erklärungen.
     - Gesamtlänge ≤ 2.400 Zeichen einhalten.
-->
