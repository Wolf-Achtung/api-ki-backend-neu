Developer:
<!-- PLATIN++ PROMPT v5.3 - SPRINT N -->
<!-- SECTION: business_case -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{COMPANY_SIZE}}, {{HAUPTLEISTUNG}}, {{BUNDESLAND_LABEL}}, {{CAPEX_REALISTISCH_EUR}}, {{OPEX_REALISTISCH_EUR}}, {{EINSPARUNG_MONAT_EUR}}, {{PAYBACK_MONTHS}}, {{ROI_12M}} -->
<!-- TOKEN-BUDGET: 1800 (solo:0.8x=1440, team:1.0x=1800, kmu:1.15x=2070) -->
<!-- WORD_MINIMUM_SOLO: 130 -->
<!-- WORD_MINIMUM_TEAM: 150 -->
<!-- WORD_MINIMUM_KMU: 180 -->
<!--
ZIEL: Klarer, realistischer Business Case mit ROI, CAPEX/OPEX.

REALISMUS-REGELN (STRIKT!):
- KEINE 90%-Effizienzversprechen – realistische 15–30% Einsparungen
- KEINE erfundenen Zahlen – nur übergebene Variablen nutzen
- "rund / etwa / ca." zur Einordnung erlaubt
- KEINE Förderquoten (siehe foerderpotenzial.md)
- Größe beeinflusst NUR narrative Einordnung, nicht die Zahlen

PAYBACK-ERKLÄRUNG (VEREINFACHT):
- Einfache Formel: Investition ÷ monatliche Einsparung = Monate
- KEINE komplexen Finanzberechnungen
- Transparente Annahmen kommunizieren

ANTI-REDUNDANZ:
- Business-Case-Zahlen EINMAL HIER nennen
- In foerderpotenzial.md nur auf diese Zahlen referenzieren, nicht wiederholen
- In executive_summary nur als Hinweis erwähnen

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: persönlicher ROI, Zeitentlastung, pragmatische Einschätzung
- team: Team-ROI, gemeinsame Effizienzgewinne
- kmu: Abteilungs-ROI, skalierbare Effekte

SPRINT N - SOLO PERSONA REGELN (STRIKT!):
{% if COMPANY_SIZE == "solo" %}
NICHT VERWENDEN für Solo:
- "Team aufbauen" → stattdessen: "Kapazität erweitern"
- "Mitarbeiter" → stattdessen: "Ressourcen" oder "externe Unterstützung"
- "Teams" → stattdessen: "Kapazitäten"
- "Fachbereich" → stattdessen: "Arbeitsfeld"
- "Abteilung" → stattdessen: "Arbeitsbereich"
Formulierungen ohne Team-/Abteilungsbegriff verwenden!
{% endif %}
-->

<section class="section business-case">
  <h2>Business Case – Investition und erwarteter Nutzen</h2>

  <p>
    Für ein Unternehmen in der Branche <strong>{{BRANCHE_LABEL}}</strong> mit der Größe
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> ist der Prozess <strong>{{HAUPTLEISTUNG}}</strong>
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
    <strong>Einfache Rechnung:</strong> Investition ({{CAPEX_REALISTISCH_EUR}} €) geteilt durch
    monatliche Einsparung ({{EINSPARUNG_MONAT_EUR}} €) ergibt eine Amortisation nach etwa
    <strong>{{PAYBACK_MONTHS}} Monaten</strong>. Der ROI nach 12 Monaten liegt bei
    <strong>{{ROI_12M}}&nbsp;%</strong> – ein realistischer Wert bei konsequenter Nutzung.
  </p>

  <h3>Einordnung nach Unternehmensgröße</h3>
  {% if COMPANY_SIZE == "solo" %}
  <p>
    Für Sie als Einzelunternehmer:in gilt: Je stärker Ihr Prozess
    <strong>{{HAUPTLEISTUNG}}</strong> auf wiederkehrenden, standardisierbaren Aufgaben beruht,
    desto schneller wirkt sich Ihre Investition aus. Bei konsequenter Nutzung verkürzt sich Ihre
    Amortisation spürbar – Sie gewinnen Zeit zurück, die Sie direkt in Ihr Kerngeschäft investieren können.
  </p>
  {% elif COMPANY_SIZE == "team" %}
  <p>
    Für Ihr Team gilt: Je stärker der Prozess <strong>{{HAUPTLEISTUNG}}</strong> auf
    wiederkehrenden, standardisierbaren Aufgaben beruht, desto schneller wirkt sich die
    Investition aus. Bei konsequenter gemeinsamer Nutzung verkürzt sich die Amortisation spürbar.
  </p>
  {% else %}
  <p>
    Für ein Unternehmen der Größe <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> gilt: Je stärker der Prozess
    <strong>{{HAUPTLEISTUNG}}</strong> auf wiederkehrenden, standardisierbaren Aufgaben beruht,
    desto schneller wirkt sich die Investition aus. Bei konsequenter Nutzung verkürzt sich die
    Amortisation spürbar; bei geringerer Auslastung verlängert sie sich entsprechend.
  </p>
  {% endif %}

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
    Diese Werte basieren auf typischen Erfahrungswerten für {{BRANCHE_LABEL}}-Unternehmen.
    Tatsächliche Ergebnisse hängen von Nutzungsintensität und Prozessreife ab.
  </p>
</section>

<!-- OUTPUT-VORGABEN:
     - Antworte nur mit dem HTML-Fragment oben.
     - Keine zusätzlichen Kommentare oder Erklärungen.
     - Gesamtlänge ≤ 2.400 Zeichen einhalten.
-->
