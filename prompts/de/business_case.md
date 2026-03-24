Developer:
<!-- PLATIN++ PROMPT v5.5 - SPRINT G17.P -->
<!-- SECTION: business_case -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{COMPANY_SIZE}}, {{hauptleistung}}, {{BUNDESLAND_LABEL}}, {{CAPEX_REALISTISCH_EUR}}, {{OPEX_REALISTISCH_EUR}}, {{EINSPARUNG_MONAT_EUR}}, {{PAYBACK_MONTHS}}, {{ROI_12M}}, {{OFFERING_LABEL}}, {{ROI_STUNDEN_MONAT}}, {{ROI_STUNDENSATZ_EUR}}, {{ROI_JAHRESERSPARNIS_EUR}}, {{ROI_CAPEX_EUR}}, {{ROI_OPEX_MONAT_EUR}}, {{ROI_OPEX_JAHR_EUR}}, {{ROI_NETTONUTZEN_EUR}}, {{ROI_RAW_PCT}}, {{ROI_CAPPED_PCT}} -->
<!-- TOKEN-BUDGET: 1800 (solo:0.8x=1440, team:1.0x=1800, kmu:1.15x=2070) -->
<!-- FIX-506: Canonical KPI Contract -->

## WICHTIGSTE REGEL (vor allem anderen beachten)
ROI-Planwerte dürfen NIEMALS über 200% liegen.
Wenn deine Berechnung einen höheren Wert ergibt, verwende IMMER "{{ROI_12M}}% (gedeckelt)".
Payback NIEMALS unter 1 Monat angeben.
Alle Zahlen KONSERVATIV schätzen — lieber unter- als überschätzen.
Rechne NIEMALS selbst — verwende AUSSCHLIESSLICH die vorberechneten Variablen.
Diese Regel hat Vorrang vor allen anderen Anweisungen.

## ROI-Herleitung (EXAKT diese Werte verwenden, NICHT selbst rechnen)

Schreibe die ROI-Herleitung EXAKT so:

1. Jahresersparnis: {{ROI_STUNDEN_MONAT}}h/Monat × {{ROI_STUNDENSATZ_EUR}}€/h × 12 = {{ROI_JAHRESERSPARNIS_EUR}}€
2. Abzüglich Einmalinvestition: {{ROI_CAPEX_EUR}}€
3. Abzüglich laufende Jahreskosten: {{ROI_OPEX_MONAT_EUR}}€/Monat × 12 = {{ROI_OPEX_JAHR_EUR}}€
4. Nettonutzen: {{ROI_JAHRESERSPARNIS_EUR}}€ - {{ROI_CAPEX_EUR}}€ - {{ROI_OPEX_JAHR_EUR}}€ = {{ROI_NETTONUTZEN_EUR}}€
5. ROI (berechnet): {{ROI_NETTONUTZEN_EUR}}€ / {{ROI_CAPEX_EUR}}€ × 100 = {{ROI_RAW_PCT}}%
6. Planwert (gedeckelt): {{ROI_CAPPED_PCT}}% (konservative Obergrenze: 200%)

REGELN:
- Verwende AUSSCHLIESSLICH die oben angegebenen Werte
- Rechne NIEMALS selbst — alle Zahlen sind vorberechnet
- Ändere KEINE Werte
- Die Reihenfolge der Schritte muss exakt eingehalten werden

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

BRANCHENBEZEICHNUNG-REGEL:
Die Branchenbezeichnung "{{BRANCHE_LABEL}}" darf MAXIMAL 2x im gesamten Text vorkommen.
Ab der 3. Verwendung NUR noch Kurzformen: "Ihr Unternehmen", "Ihre Branche", "Ihr Geschäftsfeld".

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

ROI-GUARDRAIL (STRIKT):
- ROI-PLANWERTE IMMER zwischen 50% und 200% halten
- Werte über 200%: als "Planwert (gedeckelt): {{ROI_CAPPED_PCT}}%" kennzeichnen
- In Herleitungen: NUR die vorberechneten Variablen verwenden, NIEMALS selbst rechnen
- Payback NIEMALS unter 1 Monat angeben
- Alle Zahlen KONSERVATIV schätzen — lieber unter- als überschätzen
- KEINE Emojis in den Warnhinweisen

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

FAKTEN- UND ANNAHMEN-TRENNUNG (VERBINDLICH):
- Harte Eingabedaten, Scores, deterministische Zahlen und explizite Nutzerangaben als Tatsachen behandeln.
- Schlussfolgerungen aus mehreren Signalen als Einordnung formulieren, nicht als gesicherte Tatsache.
- Branchenübliche Muster, Benchmarks oder fehlende Detailinformationen nur als Annahme oder plausible Ableitung formulieren.
SPRACHMUSTER:
- Faktisch: „Der Score liegt bei ...", „Genannt wurde ...", „Vorgegeben ist ..."
- Abgeleitet: „Daraus ergibt sich ...", „Das spricht dafür, dass ..."
- Annahme: „Erfahrungsgemäß ist zu erwarten ...", „Wahrscheinlich relevant ist ..."

ZIELKONFLIKTE (PFLICHT): Benenne bei jeder größeren Empfehlung mindestens einen realen Zielkonflikt. Beispiele: Geschwindigkeit vs. Qualität, Automatisierung vs. Kontrolle, Datenschutz vs. Bequemlichkeit, Standardisierung vs. Individualität, Investition heute vs. Nutzen später. Formuliere Trade-offs knapp im Fließtext, ohne zusätzliche Sonderbox. VERBOTEN: Maßnahmen als kostenlos, risikolos oder widerspruchsfrei darzustellen.

BEGRIFFSKONSISTENZ (VERBINDLICH — OPT-A7):
Verwende diese Begriffe einheitlich im gesamten Report:
- „KI-Governance" = Oberbegriff für Regeln, Rollen, Freigaben rund um KI-Nutzung. „KI-Richtlinie" = das konkrete Dokument.
- „ROI" = immer „ROI", bei erster Nennung pro Abschnitt „Return on Investment (ROI)".
- „Break-Even" = Zeitpunkt der Amortisation im Fließtext. „Amortisation" nur in Tabellen/KPIs.
- „EU AI Act" = immer, bei erster Nennung „EU AI Act (KI-Verordnung der EU)". NICHT standalone „KI-Verordnung".
- „AVV" = bei erster Nennung „AV-Vertrag (AVV)", danach nur „AVV".
- „KI-Ausgabe" = allgemein für KI-Ergebnisse. „KI-Entwurf" = Text, der noch geprüft werden muss. NICHT „KI-Output".
- „Prüfschritt" = allgemein. „Freigabe" = formaler Akt. „Vier-Augen-Prinzip" = zwei Personen prüfen. NICHT „Review".
- „DSGVO" = nie ausschreiben. „Tool" = Software. „Werkzeug" = nur in Metaphern. Nicht im selben Absatz wechseln.

SZENARIO-EINORDNUNG (VERBINDLICH — OPT-A5):
Wenn du die drei Szenarien (konservativ/realistisch/optimistisch) darstellst, ergänze bei jedem Szenario eine kurze Einordnung der Annahmen (1–2 Sätze):
- Konservativ: Unter welchen realistischen Bedingungen tritt dieses Szenario ein? (etwa: langsamere Einführung, mehr Nacharbeit, Schulung verzögert)
- Realistisch: Was muss gegeben sein, damit dieser Pfad eintritt? (etwa: Quick Wins greifen, Team arbeitet mit, KI-Richtlinie ist verbindlich)
- Optimistisch: Welche Voraussetzungen müssten erfüllt sein? (etwa: schnelle Akzeptanz, wenig Reibung, straffe Koordination)
Formuliere die Einordnung praxisnah für den Unternehmenskontext, nicht generisch. Nutze „Annahme:" als Einleitung.
Die Szenario-ZAHLEN (ROI %, Break-Even Monate) kommen deterministisch aus dem Calculator — NICHT ändern. Nur die sprachliche Einordnung ergänzen.

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
