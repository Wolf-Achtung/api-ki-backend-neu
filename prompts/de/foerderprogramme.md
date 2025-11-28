Developer:
<!-- foerderprogramme.md – v5.0 GOLD STANDARD+ (förderlogik, size-aware, placeholder-safe)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     ZIEL:
       - Qualitative Einschätzung des Förderpotenzials für ein KI-/Digitalisierungsprojekt.
       - Nutze ausschließlich das aus der Research-Pipeline gelieferte {{FOERDERPROGRAMME_HTML}}.
       - Keine eigenen Programme, Zahlen oder Fördersätze erfinden.

     VERFÜGBARE VARIABLEN:
       - {{FOERDERPROGRAMME_HTML}}, {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}
       - Falls {{FOERDERPROGRAMME_HTML}} leer ist:
           Gib einen neutralen, generischen Hinweis aus (z.B. "Die Förderrecherche wird noch durchgeführt.").
           NIEMALS <p class="error">...</p> im finalen Bericht ausgeben.
       - Stelle sicher, dass der Abschnitt trotzdem sinnvoll und vollständig bleibt.

     SIZE-AWARE-LOGIK (COMPANY_SIZE ∈ {"solo","team","kmu"}):
       SOLO:
         - Fokus: kleine Förderprogramme, Einstiegsberatung, Innovationsgutscheine.
         - Sprache: klar, pragmatisch, niedriger bürokratischer Aufwand.
       TEAM (2–10):
         - Programme für Prozessdigitalisierung, Weiterbildung, Pilotprojekte.
         - Sprache: Team-Rollen, einfache Abstimmungswege.
       KMU (11–100):
         - Zusätzlich Programme für Investitionen, Verbundprojekte, Kooperationen.
         - Sprache: Fachbereiche, Verantwortliche, strukturierte Antragsschritte.

     STIL:
       - 3–4 strukturierte Abschnitte: Einleitung, Programme, Bedeutung für Business Case, Nächste Schritte.
       - Kein Marketing-Ton, kein Pathos, keine übertriebenen Versprechen.
       - Keine „Platzhalter“-Wörter, kein „Content wird erstellt“.

     HTML-STRUKTUR (genau ein <section>-Block):
       <section class="section funding"> … </section>
-->

<section class="section funding">
  <h2>Förderprogramme für Ihr KI-Vorhaben</h2>

  <p>
    Für Unternehmen der Größe <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in der Branche
    <strong>{{BRANCHE_LABEL}}</strong> können Förderprogramme einen wichtigen Beitrag leisten,
    um KI- und Digitalisierungsprojekte wirtschaftlich abzusichern. Je nach Unternehmensgröße
    reichen die Möglichkeiten von Einstiegs- und Beratungsprogrammen über Zuschüsse für
    Prozessdigitalisierung bis hin zu größeren Investitions- und Kooperationsvorhaben.
  </p>

  <h3>Ausgewählte Programme im Überblick</h3>
  <p>
    Die folgenden Programme stammen direkt aus der aktuellen Förderrecherche und berücksichtigen
    regionale sowie thematische Förderprioritäten:
  </p>

  <!-- ANWEISUNG: Falls {{FOERDERPROGRAMME_HTML}} leer ist oder weniger als 50 Zeichen enthält, -->
  <!-- ersetze den folgenden Block durch einen generischen Fallback-Text mit typischen Förderbereichen. -->
  <!-- Ansonsten: gib {{FOERDERPROGRAMME_HTML}} direkt aus. -->

  {{FOERDERPROGRAMME_HTML}}

  <!-- FALLBACK-ANWEISUNG (nur verwenden wenn {{FOERDERPROGRAMME_HTML}} fehlt): -->
  <!-- Die Förderrecherche für {{BRANCHE_LABEL}} und {{BUNDESLAND_LABEL}} ist derzeit noch in Bearbeitung. -->
  <!-- Typische Förderbereiche für {{UNTERNEHMENSGROESSE_LABEL}}: -->
  <!-- - Digitalisierungsförderung (z.B. Digital Jetzt, Investitionsförderung) -->
  <!-- - Innovationsgutscheine und Beratungsförderung -->
  <!-- - KI-spezifische Förderungen auf Landes- und Bundesebene -->

  <h3>Was das für Ihren Business Case bedeutet</h3>
  <p>
    Eine passende Förderung kann die im Business Case dargestellten Investitionskosten reduzieren
    und die Amortisation des Projekts beschleunigen. Für <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>
    bedeutet dies konkret:
  </p>
  <ul>
    <li>Solo-Unternehmen: geringere Einstiegshürden und Entlastung bei Beratungs- oder Setup-Kosten.</li>
    <li>Kleine Teams: Unterstützung bei Prozessdigitalisierung, Schulungen und Pilotprojekten.</li>
    <li>KMU: zusätzliche Spielräume für strukturelle Investitionen, Pilotflächen und Skalierungsprojekte.</li>
  </ul>
  <p>
    Die tatsächliche Förderquote hängt vom jeweiligen Programm, den konkreten Projektinhalten
    und den Antragsvoraussetzungen ab und muss vor Antragstellung im Detail geprüft werden.
    Typische Zuschussbereiche liegen – je nach Programm – im Spektrum von etwa
    <strong>30–50&nbsp;%</strong> der förderfähigen Ausgaben, ohne dass hier neue Zahlen
    oder Programme ergänzt werden.
  </p>

  <h3>Nächste Schritte</h3>
  <ul>
    <li>
      Einen strukturierten Fördercheck durchführen: Programme aus der Übersicht mit
      <strong>{{BRANCHE_LABEL}}</strong> und <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>
      abgleichen und Fristen sowie Fördergegenstände prüfen.
    </li>
    <li>
      Ein förderfähiges Vorhaben definieren – idealerweise ein klar abgegrenzter KI-Pilot
      oder ein Digitalisierungsprojekt im Kernprozess <strong>{{HAUPTLEISTUNG}}</strong>.
    </li>
    <li>
      Eine kompakte Projektbeschreibung erstellen (Ziele, Maßnahmen, Zeitplan, erwarteter
      Nutzen, grobe Kosten), die als Grundlage für Antragsunterlagen dienen kann.
    </li>
    <li>
      Optional den Austausch mit regionalen Beratungsstellen oder zuständigen Ansprechpersonen suchen,
      um Förderfähigkeit, Kombinationsmöglichkeiten und Aufwand realistisch einzuschätzen.
    </li>
  </ul>

  <p class="small muted">
    Hinweis: Förderquoten, Fristen und inhaltliche Schwerpunkte der Programme können sich ändern.
    Die hier dargestellte Übersicht basiert auf einer zum Zeitpunkt der Report-Erstellung
    aktuellen Förderrecherche und sollte vor Antragstellung stets mit den offiziellen
    Programmunterlagen abgeglichen werden.
  </p>
</section>
