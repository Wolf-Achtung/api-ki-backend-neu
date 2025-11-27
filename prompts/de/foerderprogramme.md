Developer:
<!-- foerderprogramme.md – v3.0 GOLD STANDARD+ (förderlogik, size-aware, placeholder-safe)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     ZIEL:
       - Erzeuge einen klaren Abschnitt über relevante Förderprogramme für KI-/Digitalisierungsprojekte.
       - Nutze ausschließlich das aus der Research-Pipeline gelieferte {{FOERDERPROGRAMME_HTML}}.
       - Keine eigenen Programme, Zahlen oder Fördersätze erfinden.

     PFLICHTVARIABLEN:
       - {{FOERDERPROGRAMME_HTML}}, {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}
       - Falls eine dieser Variablen nicht existiert oder leer ist: 
           Gib ausschließlich aus:
           <p class="error">Fehlende oder leere Pflichtfelder: {{Namen_der_leeren_Variablen}}.</p>
           und KEINEN weiteren Inhalt.

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
    um die Einführung und Weiterentwicklung von KI-Projekten effizienter und wirtschaftlich
    zu gestalten. Die folgenden Programme stammen direkt aus der aktuellen Förderrecherche
    und berücksichtigen regionale sowie thematische Förderprioritäten.
  </p>

  <h3>Ausgewählte Programme im Überblick</h3>
  {{FOERDERPROGRAMME_HTML}}

  <h3>Was das für Ihren Business Case bedeutet</h3>
  <p>
    Eine passende Förderung kann die anfänglichen Investitionskosten reduzieren und den
    in Ihrem Business Case beschriebenen Payback beschleunigen. Je nach Programm kann dies
    beispielsweise Beratungsleistungen, Qualifizierungsprojekte oder technologiebezogene
    Investitionen betreffen. Die genaue Förderquote hängt jedoch vom jeweiligen Programmstand
    sowie individuellen Kriterien ab und muss vor Antragstellung geprüft werden.
  </p>

  <h3>Nächste Schritte</h3>
  <ul>
    <li>Kurzfristig: Fördercheck durchführen, bereitgestellte Unterlagen sichten und mögliche Fristen prüfen.</li>
    <li>Mittelfristig: Ein potenziell förderfähiges Vorhaben definieren, etwa ein klar abgegrenzter KI-Pilot.</li>
    <li>Optional: Austausch mit regionalen Beratungsstellen oder zuständigen Ansprechpersonen zur Finalisierung der Unterlagen.</li>
  </ul>
</section>
