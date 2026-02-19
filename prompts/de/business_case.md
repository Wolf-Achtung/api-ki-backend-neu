Developer:
<!-- PLATIN++ PROMPT v5.5 - SPRINT G17.P -->
<!-- SECTION: business_case -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{COMPANY_SIZE}}, {{hauptleistung}}, {{BUNDESLAND_LABEL}}, {{CAPEX_REALISTISCH_EUR}}, {{OPEX_REALISTISCH_EUR}}, {{EINSPARUNG_MONAT_EUR}}, {{PAYBACK_MONTHS}}, {{ROI_12M}}, {{OFFERING_LABEL}} -->
<!-- TOKEN-BUDGET: 1800 (solo:0.8x=1440, team:1.0x=1800, kmu:1.15x=2070) -->
<!-- FIX-506: Canonical KPI Contract -->
<!--
###############################################################################
**WICHTIG – Längenlimit: Deine Antwort darf maximal 1100 Wörter umfassen. Kürze lieber als zu überziehen.**

##                    CANONICAL KPI CONTRACT (STRICT)                        ##
###############################################################################

You MUST NOT:
- invent, estimate or round KPI values
- use example numbers beyond provided variables
- restate KPIs in alternative wording

You MAY ONLY:
- reference provided canonical variables: {{CAPEX_REALISTISCH_EUR}}, {{OPEX_REALISTISCH_EUR}},
  {{EINSPARUNG_MONAT_EUR}}, {{PAYBACK_MONTHS}}, {{ROI_12M}}
- use "rund" for contextual descriptions (NOT "etwa" or "ca.")
- explain QUALITATIVE benefits WITHOUT inventing numbers

If a KPI is missing: use the provided variable or leave field empty.

BANNED PATTERNS (hard fail in STRICT_MODE):
- "z. B." / "z.B."
- "typischerweise"
- "etwa" (use "rund" instead)
- "ca."
- invented percentages or time estimates

###############################################################################
-->
<!--
###############################################################################
##                    HAUPTLEISTUNG INTEGRATION (BALANCIERT)                 ##
###############################################################################

DIE VARIABLE {{hauptleistung}} ENTHÄLT DAS KERNGESCHÄFT DES USERS.

🎯 ZIEL: 3-5 NATÜRLICHE ERWÄHNUNGEN (NICHT MEHR!)
⚠️ MAXIMUM 6x - Mehr wirkt mechanisch!

VERTEILUNG (STRIKT!):
1. ✅ Im Einleitungsabsatz: 1x {{hauptleistung}} (PFLICHT)
2. ✅ Bei "Monatlicher Effekt": 1x (PFLICHT)
3. ✅ Bei "Einordnung nach Größe": 1x (PFLICHT)
4. ❌ Amortisation: Nutze "Ihr Kerngeschäft" als Synonym
5. ❌ Erlöspotenziale: Nutze "diese Leistung" als Synonym

NATÜRLICHE SPRACHE - SYNONYME NUTZEN:
- "Ihr Kerngeschäft" statt wiederholtem {{hauptleistung}}
- "diese Leistung" / "Ihre Dienstleistung" als Alternative

###############################################################################
-->
<!-- WORD_MINIMUM_SOLO: 130 -->
<!-- WORD_MINIMUM_TEAM: 150 -->
<!-- WORD_MINIMUM_KMU: 180 -->
<!--
ZIEL: Klarer, realistischer Business Case mit ROI, CAPEX/OPEX.

###############################################################################
##                    ROI KONSISTENZ (SINGLE SOURCE OF TRUTH)                ##
###############################################################################

ALLE ROI-WERTE MÜSSEN {{ROI_12M}} VERWENDEN!

⚠️ KONSISTENZ-REGEL (STRIKT!):
- Der ROI-Wert ist {{ROI_12M}} - DIESEN WERT ÜBERALL VERWENDEN
- KEINE anderen ROI-Prozentsätze erfinden oder berechnen
- KEINE widersprüchlichen ROI-Angaben in anderen Sektionen

Wenn in ANDEREN Sektionen ROI erwähnt wird:
- → VERWEIS: "Der ROI liegt bei {{ROI_12M}}% (→ siehe Business Case)"
- → NIEMALS: andere Prozentsätze nennen

###############################################################################

###############################################################################
##                    STANDORT KONSISTENZ (KRITISCH!)                        ##
###############################################################################

⚠️ KEINE FALSCHEN BUNDESLÄNDER NENNEN!

Das Bundesland des Users ist: {{BUNDESLAND_LABEL}}
- NUR dieses Bundesland erwähnen
- KEINE anderen Bundesländer halluzinieren!

VERBOTEN:
❌ "Berlin" wenn {{BUNDESLAND_LABEL}} ≠ "Berlin"
❌ "Bayern" wenn {{BUNDESLAND_LABEL}} ≠ "Bayern"
❌ Förderprogramme eines anderen Bundeslandes nennen

###############################################################################

REALISMUS-REGELN (STRIKT!):
- KEINE 90%-Effizienzversprechen – realistische 15–30% Einsparungen
- KEINE erfundenen Zahlen – nur übergebene Variablen nutzen
- "rund" zur Einordnung erlaubt (NICHT "etwa" oder "ca.")
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
- Maximal EIN kurzer Verweis auf Data Readiness ist erlaubt ("→ siehe Datenlage")
- CAPEX/OPEX-Blöcke nur HIER – nicht in anderen Sections wiederholen
- Fokus: ROI, Payback, Investition – KEINE Datenlage-Analyse

SPRINT G18 - NARRATIVE VERBINDUNGEN:
- Starter Kit referenzieren: "Die Starter Kits ermöglichen eine kosteneffiziente Umsetzung der Quick Wins..."
- Bezug zu Roadmap: "Amortisation erfolgt bereits in Phase 2 der 90-Tage-Roadmap..."
- Förderpotenzial ankündigen: "Details zur möglichen Förderung → siehe Förderpotenzial"

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: persönlicher ROI, Zeitentlastung, pragmatische Einschätzung
- team: Team-ROI, gemeinsame Effizienzgewinne
- kmu: Abteilungs-ROI, erweiterbare Effekte

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

  <!-- BALANCIERT: 1x {{hauptleistung}} in Einleitung -->
  <p>
    Für Ihr Geschäftsmodell <strong>{{hauptleistung}}</strong> in der Branche <strong>{{BRANCHE_LABEL}}</strong>
    lässt sich ein konkreter Investitionsrahmen ableiten. Der Business Case zeigt, welche
    Aufwände für Setup und laufenden Betrieb realistisch sind und in welchem Zeitraum
    sich diese amortisieren. Im Fokus stehen Zeitersparnis, Qualitätsgewinne und ein
    nachvollziehbarer Payback. Die Quick Wins aus der Roadmap beschleunigen den ROI zusätzlich → siehe Sofortmaßnahmen.
  </p>

  <h3>Investition und laufende Kosten</h3>
  <p>
    Die einmaligen Aufwände für Aufbau und Einführung liegen bei rund
    <strong>{{CAPEX_REALISTISCH_EUR}}&nbsp;€</strong>. Hinzu kommen monatliche Betriebskosten
    von rund <strong>{{OPEX_REALISTISCH_EUR}}&nbsp;€</strong> – hauptsächlich für den KI-Einsatz,
    Infrastruktur, Tools und potenzielle Lizenzen.
  </p>

  <h3>Monatlicher Effekt</h3>
  <p>
    Bei {{hauptleistung}} ist im täglichen Einsatz eine realistische Entlastung von rund
    <strong>{{EINSPARUNG_MONAT_EUR}}&nbsp;€ pro Monat</strong> erreichbar. Sie entsteht aus
    Zeitgewinn bei Kernprozessen, geringeren manuellen Schleifen und einer konsistenteren Ergebnisqualität.
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
    Je stärker <strong>{{hauptleistung}}</strong> auf wiederkehrenden Aufgaben beruht,
    desto schneller wirkt sich Ihre Investition aus.
  </p>
  {% elif COMPANY_SIZE == "team" %}
  <p>
    Je stärker <strong>{{hauptleistung}}</strong> auf wiederkehrenden Aufgaben beruht,
    desto schneller wirkt sich die Team-Investition aus.
  </p>
  {% else %}
  <p>
    Je stärker <strong>{{hauptleistung}}</strong> auf standardisierbaren Aufgaben beruht,
    desto schneller die Amortisation.
  </p>
  {% endif %}

  <h3>Verbindung zu Fördermöglichkeiten</h3>
  <p>
    In <strong>{{BUNDESLAND_LABEL}}</strong> existieren Förderprogramme für KI-Projekte.
    Eine Förderung verkürzt die Amortisation. Details → siehe Förderkapitel.
  </p>

  <h3>Zusätzliche Erlöspotenziale</h3>
  <p>
    Neben Effizienzgewinnen bieten KI-Prozesse weitere Erlöspotenziale:
  </p>
  <ul>
    <li>Digitale Produkte (automatisierte Analysen, Reports)</li>
    <li>Neue Serviceformate (Workshops, Beratung)</li>
    <li>Skalierbare Angebote basierend auf Ihrem Kerngeschäft</li>
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
