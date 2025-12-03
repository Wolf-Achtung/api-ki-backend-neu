Developer:
<!-- PLATIN++ PROMPT -->
<!-- SECTION: business_case -->
<!-- VERSION: v4.0 PLATIN++ V5 -->
<!-- OUTPUT: HTML -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{COMPANY_SIZE}}, {{HAUPTLEISTUNG}}, {{BUNDESLAND_LABEL}}, {{CAPEX_REALISTISCH_EUR}}, {{OPEX_REALISTISCH_EUR}}, {{EINSPARUNG_MONAT_EUR}}, {{PAYBACK_MONTHS}}, {{ROI_12M}} -->
<!-- TOKEN-BUDGET: 1800 (solo:0.8x=1440, team:1.0x=1800, kmu:1.15x=2070) -->
<!--
ZIEL: Klarer Business Case mit ROI, CAPEX/OPEX.

REGELN:
- KEINE eigenen Zahlen erfinden – nur Variablen nutzen
- "rund / etwa / ca." zur Einordnung erlaubt
- KEINE Förderquoten (siehe foerderpotenzial.md)
- Größe beeinflusst NUR narrative Einordnung, nicht die Zahlen

ANTI-REDUNDANZ:
- Business-Case-Zahlen EINMAL HIER nennen
- In foerderpotenzial.md nur auf diese Zahlen referenzieren, nicht wiederholen
- In executive_summary nur als Hinweis erwähnen

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: persönlicher ROI, Zeitentlastung, pragmatische Einschätzung
- team: Team-ROI, gemeinsame Effizienzgewinne
- kmu: Abteilungs-ROI, skalierbare Effekte
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

  <h3>Zusätzliche Erlöspotenziale (Monetarisierung)</h3>
  <p>
    Neben der Effizienzsteigerung bieten KI-gestützte Prozesse auch Erlöspotenziale:
    Digitale Produkte (z.B. automatisierte Analysen, Reports), neue Serviceformate
    (Workshops, Beratung) oder skalierbare Angebote können den ROI zusätzlich verbessern.
    Details zu Pricing-Modellen finden sich im Kapitel "Monetarisierung".
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
