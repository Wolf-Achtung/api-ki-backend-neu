Developer:
<!-- foerderprogramme.md – v6.0 PLATIN++ KOMPAKT (size-aware, reduziert für Solo/Team)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

###############################################################################
##                    STANDORT KONSISTENZ (KRITISCH!)                        ##
###############################################################################

⚠️ KEINE FALSCHEN BUNDESLÄNDER NENNEN!

Das Bundesland des Users ist: {{BUNDESLAND_LABEL}}
- NUR dieses Bundesland in Förder-Kontexten verwenden
- KEINE anderen Bundesländer halluzinieren!
- NICHT "Berlin" schreiben wenn {{BUNDESLAND_LABEL}} = "Nordrhein-Westfalen"

VERBOTEN:
❌ Ein anderes Bundesland als {{BUNDESLAND_LABEL}} nennen
❌ Förderprogramme eines anderen Bundeslandes empfehlen
❌ "Berlin", "Bayern", "NRW", "Baden-Württemberg" etc. wenn nicht {{BUNDESLAND_LABEL}}

ERLAUBT:
✅ {{BUNDESLAND_LABEL}} verwenden (der echte Wert)
✅ "Ihr Bundesland" als generische Alternative
✅ Bundesprogramme (gelten überall)

###############################################################################

     KONDITIONALE LOGIK (L4/L5/L8/L9):

     INTERESSE AN FÖRDERUNG:
     {% if INTERESSE_FOERDERUNG_LABEL == "nein" or INTERESSE_FOERDERUNG_LABEL == "Kein Bedarf" %}
     → KURZ-VERSION: Nur 1-2 Sätze + Kurzliste (max 2 Programme).
       "Obwohl aktuell kein Förderbedarf besteht, stehen folgende Programme bereit:"
     {% endif %}

     BISHERIGE FÖRDERMITTEL:
     {% if BISHERIGE_FOERDERMITTEL == "ja" %}
     → Hinweis am Ende der Programmliste:
       "<p class='small muted'><strong>Hinweis:</strong> Da bereits Fördermittel bezogen wurden,
       ist die De-minimis-Grenze (300.000 € / 3 Jahre) zu beachten. Vor Antragstellung
       alle erhaltenen Beihilfen zusammenstellen.</p>"
     {% endif %}

     BERATUNGSERFAHRUNG:
     {% if ERFAHRUNG_BERATUNG == "nein" %}
     → BAFA-Beratungsförderung als erstes Programm in der Liste hervorheben.
     {% endif %}

     NICHT-DE/AT-LÄNDER (L9):
     {% if COUNTRY not in ["DE", "AT", ""] %}
     → Am Ende der Section einen Hinweis einbauen:
       "<p class='small muted'>Hinweis: Für Ihr Land sind in diesem Report primär EU-weite
       Programme aufgeführt. Zusätzliche nationale Förderprogramme können über die jeweilige
       nationale Wirtschaftsförderung recherchiert werden.</p>"
     {% endif %}

     THEMEN-OWNERSHIP (verbindlich):
     - Diese Section: OWNER für konkrete Förderprogramm-Liste und Förderquoten
     - NICHT hier: Business-Case-Einordnung (→ foerderpotenzial)
     - NICHT hier: Strategische Förder-Bewertung (→ foerderpotenzial)
     - Unterschied: foerderprogramme = LISTE, foerderpotenzial = ANALYSE

     ZIEL:
       - KOMPAKTE Förderübersicht – nicht alle Details, nur Essenz.
       - {{FOERDERPROGRAMME_HTML}} enthält die Fördermatrix.
       - Für Solo/Team: MAX 3 Programme mit je 1 Satz Beschreibung.
       - Für KMU: bis zu 5 Programme mit kurzen Beschreibungen.


     LANDES-SPEZIFISCHE PROGRAMME (PFLICHT wenn BUNDESLAND passt!):
     Wenn {{BUNDESLAND_LABEL}} = "Berlin":
       - IBB Pro FIT: Innovationsförderung für technologieorientierte Projekte,
         bis 400.000€ Zuschuss, Antrag über IBB (Investitionsbank Berlin).
         Link: https://www.ibb.de/de/foerderprogramme/pro-fit.html
       - Transfer BONUS: Technologietransfer-Förderung, bis 45.000€,
         für KMU die mit Forschungseinrichtungen kooperieren.
         Link: https://www.ibb.de/de/foerderprogramme/transfer-bonus.html
       - Digitalprämie Berlin (wenn aktiv): Zuschuss für Digitalisierung,
         prüfe aktuelle Verfügbarkeit.
       → Mindestens 1 Berliner Landesprogramm MUSS genannt werden!

     SIZE-AWARE PROGRAMMANZAHL (STRIKT EINHALTEN!):
       SOLO: MAX 3 Programme, je 1 Satz. Hinweis: "Details im Anhang"
       TEAM: MAX 3 Programme, je 1-2 Sätze. Hinweis: "Details im Anhang"
       KMU: MAX 5 Programme, je 2-3 Sätze.

     VERFÜGBARE VARIABLEN:
       - {{FOERDERPROGRAMME_HTML}}, {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}

     SIZE-AWARE-LOGIK:
       SOLO:
         - Fokus: Innovationsgutscheine, Beratungsförderung (niedriger Aufwand).
         - KEIN langer Text – nur Kurzhinweise.
       TEAM (2–10):
         - Programme für Prozessdigitalisierung, Weiterbildung.
         - Kompakte Darstellung.
       KMU (11–100):
         - Zusätzlich Investitionsförderung, Verbundprojekte.
         - Etwas ausführlicher erlaubt.

     STIL:
       - KOMPAKT: Einleitung (1-2 Sätze), Programmliste (kurz!), Nächster Schritt (1 Satz).
       - Keine langen Erklärungen.
       - Hinweis auf "Details im Anhang" für Solo/Team.

     HTML-STRUKTUR (genau ein <section>-Block):
       <section class="section funding"> … </section>
-->

<section class="section funding">
  <h2>Förderprogramme für Ihr KI-Vorhaben</h2>

  <p>
    Für <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in <strong>{{BRANCHE_LABEL}}</strong>
    stehen passende Förderprogramme zur Verfügung, die KI-Projekte wirtschaftlich absichern können.
  </p>

  <h3>Relevante Programme</h3>
  <!-- SIZE-AWARE: Solo/Team = max 3 Programme, KMU = max 5 Programme -->
  {{FOERDERPROGRAMME_HTML}}

  <p>
    <strong>Typische Förderquote:</strong> 30–50 % der förderfähigen Kosten.
    <!-- Für Solo/Team folgenden Hinweis anzeigen: -->
    <em>Ausführliche Programmbeschreibungen finden Sie im Anhang.</em>
  </p>

  <h3>Nächster Schritt</h3>
  <p>
    Prüfen Sie die passenden Programme für Ihr KI-Vorhaben im Kernprozess
    <strong>{{HAUPTLEISTUNG}}</strong> und starten Sie mit einem kompakten Fördercheck.
  </p>

  <p class="small muted">
    Hinweis: Förderquoten und Fristen können sich ändern – vor Antragstellung offizielle Unterlagen prüfen.
  </p>
</section>
