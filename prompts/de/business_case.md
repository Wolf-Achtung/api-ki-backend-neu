Developer:
<!-- PLATIN++ PROMPT v5.5 - SPRINT G17.P -->
<!-- SECTION: business_case -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{COMPANY_SIZE}}, {{hauptleistung}}, {{BUNDESLAND_LABEL}}, {{CAPEX_REALISTISCH_EUR}}, {{OPEX_REALISTISCH_EUR}}, {{EINSPARUNG_MONAT_EUR}}, {{PAYBACK_MONTHS}}, {{ROI_12M}}, {{OFFERING_LABEL}} -->
<!-- TOKEN-BUDGET: 1800 (solo:0.8x=1440, team:1.0x=1800, kmu:1.15x=2070) -->
<!--
###############################################################################
##                    🚨 KRITISCH: HAUPTLEISTUNG INTEGRATION 🚨              ##
###############################################################################

DIE VARIABLE {{hauptleistung}} ENTHÄLT DAS KERNGESCHÄFT DES USERS.
SIE MUSS MINDESTENS 5x IM BUSINESS CASE ERSCHEINEN!

PFLICHT-STELLEN FÜR {{hauptleistung}}:
1. ✅ Im Einleitungsabsatz: "Für Ihr Geschäftsmodell ({{hauptleistung}})..."
2. ✅ Bei "Monatlicher Effekt": ROI-Berechnung für {{hauptleistung}}
3. ✅ Bei "Amortisation": Payback spezifisch für {{hauptleistung}}
4. ✅ Bei "Einordnung nach Größe": {{hauptleistung}}-Skalierung
5. ✅ Bei "Erlöspotenziale": Neue Produkte basierend auf {{hauptleistung}}

⚠️ BUSINESS CASE OHNE HAUPTLEISTUNG-BEZUG IST GENERISCH UND WERTLOS!

###############################################################################
-->
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

SPRINT G18 - ANTI-REDUNDANZ (STRIKT!):
- Datenlage/Data Readiness NICHT erneut beschreiben – gehört in data_readiness.md
- Maximal EIN kurzer Verweis auf Data Readiness ist erlaubt (z.B. "→ siehe Datenlage")
- CAPEX/OPEX-Blöcke nur HIER – nicht in anderen Sections wiederholen
- Fokus: ROI, Payback, Investition – KEINE Datenlage-Analyse

SPRINT G18 - NARRATIVE VERBINDUNGEN:
- Starter Kit referenzieren: "Die Starter Kits ermöglichen eine kosteneffiziente Umsetzung der Quick Wins..."
- Bezug zu Roadmap: "Amortisation erfolgt bereits in Phase 2 der 90-Tage-Roadmap..."
- Förderpotenzial ankündigen: "Details zur möglichen Förderung → siehe Förderpotenzial"

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

  <!-- G17.P: Neue Einleitung mit {{hauptleistung}}-Bezug -->
  <p>
    Für Ihr Geschäftsmodell <strong>{{hauptleistung}}</strong> in der Branche <strong>{{BRANCHE_LABEL}}</strong>
    lässt sich ein konkreter Investitionsrahmen ableiten. Der Business Case für {{hauptleistung}} zeigt, welche
    Aufwände für Setup und laufenden Betrieb realistisch sind und in welchem Zeitraum
    sich diese amortisieren. Im Fokus stehen Zeitersparnis, Qualitätsgewinne und ein
    nachvollziehbarer Payback für Ihr Kerngeschäft. Die Quick Wins aus der Roadmap beschleunigen den ROI
    für {{hauptleistung}} zusätzlich → siehe Sofortmaßnahmen.
  </p>

  <h3>Investition und laufende Kosten</h3>
  <p>
    Die einmaligen Aufwände für Aufbau und Einführung liegen bei rund
    <strong>{{CAPEX_REALISTISCH_EUR}}&nbsp;€</strong>. Hinzu kommen monatliche Betriebskosten
    von etwa <strong>{{OPEX_REALISTISCH_EUR}}&nbsp;€</strong> – hauptsächlich für den KI-Einsatz,
    Infrastruktur, Tools und potenzielle Lizenzen.
  </p>

  <h3>Monatlicher Effekt bei {{hauptleistung}}</h3>
  <p>
    Bei {{hauptleistung}} ist im täglichen Einsatz eine realistische Entlastung von rund
    <strong>{{EINSPARUNG_MONAT_EUR}}&nbsp;€ pro Monat</strong> erreichbar. Sie entsteht aus
    Zeitgewinn bei {{hauptleistung}}-Prozessen, geringeren manuellen Schleifen und einer konsistenteren Ergebnisqualität.
    Voraussetzung ist, dass der neue Workflow für {{hauptleistung}} im Alltag konsequent genutzt wird.
  </p>

  <h3>Amortisation und ROI</h3>
  <p>
    <strong>Einfache Rechnung:</strong> Investition ({{CAPEX_REALISTISCH_EUR}} €) geteilt durch
    monatliche Einsparung ({{EINSPARUNG_MONAT_EUR}} €) ergibt eine Amortisation nach etwa
    <strong>{{PAYBACK_MONTHS}} Monaten</strong>. Der ROI nach 12 Monaten liegt bei
    <strong>{{ROI_12M}}&nbsp;%</strong> – ein realistischer Wert bei konsequenter Nutzung.
  </p>

  <h3>Einordnung für {{hauptleistung}} nach Unternehmensgröße</h3>
  {% if COMPANY_SIZE == "solo" %}
  <p>
    Je stärker <strong>{{hauptleistung}}</strong> auf wiederkehrenden Aufgaben beruht,
    desto schneller wirkt sich Ihre Investition für {{hauptleistung}} aus.
  </p>
  {% elif COMPANY_SIZE == "team" %}
  <p>
    Je stärker <strong>{{hauptleistung}}</strong> auf wiederkehrenden Aufgaben beruht,
    desto schneller wirkt sich die Team-Investition für {{hauptleistung}} aus.
  </p>
  {% else %}
  <p>
    Je stärker <strong>{{hauptleistung}}</strong> auf standardisierbaren Aufgaben beruht,
    desto schneller die Amortisation für {{hauptleistung}}.
  </p>
  {% endif %}

  <h3>Verbindung zu Fördermöglichkeiten</h3>
  <p>
    In <strong>{{BUNDESLAND_LABEL}}</strong> existieren Förderprogramme für KI-Projekte.
    Eine Förderung verkürzt die Amortisation. Details → siehe Förderkapitel.
  </p>

  <h3>Zusätzliche Erlöspotenziale durch {{hauptleistung}}</h3>
  <p>
    Neben Effizienzgewinnen bei {{hauptleistung}} bieten KI-Prozesse weitere Erlöspotenziale:
  </p>
  <ul>
    <li>Digitale Produkte basierend auf {{hauptleistung}} (automatisierte Analysen, Reports)</li>
    <li>Neue Serviceformate für {{hauptleistung}} (Workshops, Beratung)</li>
    <li>Skalierbare {{hauptleistung}}-Angebote</li>
  </ul>

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
