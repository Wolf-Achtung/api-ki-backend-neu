Developer: <!-- gamechanger.md – v3.0 GOLD STANDARD+ (realistische Wachstumsoptionen)
  
  Antworte ausschließlich mit validem HTML.
  Kein <html>, <head> oder <body>. Keine Markdown-Fences.

  VARIABLEN:
  - {{BRANCHE}}: Branche (Kurzform, z.B. "Beratung & Dienstleistungen").
  - {{UNTERNEHMENSGROESSE}}: solo | kleines Team | KMU (oder ähnlich).
  - {{MITARBEITER}}: grobe Mitarbeiterzahl (falls vorhanden).
  - {{HAUPTLEISTUNG}}: heutiger Kern der Wertschöpfung.
  - {{AKTUELLES_MODELL}}: Beschreibung des aktuellen Geschäftsmodells.
  - {{INVESTITIONSBUDGET}}: realistischer Investitionsrahmen.

  ZIEL:
  - 2–3 strategische Gamechanger-Szenarien skizzieren, wie das heutige Modell
    auf Basis von KI und Automatisierung weiterentwickelt werden kann.
  - Fokus auf neuen oder deutlich skalierbaren Erlösquellen, nicht auf reine Effizienz.

  REGELN:
  - Vorschläge müssen zu {{UNTERNEHMENSGROESSE}}, {{INVESTITIONSBUDGET}} und {{BRANCHE}} passen.
    Für Solo / kleines Team eher schlanke, iterativ ausbaubare Modelle vorschlagen.
  - Nur qualitative Aussagen zu Umsatzpotenzialen (z.B. „niedriger fünfstelliger Bereich p.a.“).
    Keine präzisen Euro-Beträge oder unrealistischen sechsstelligen Umsätze aus dem Nichts.
  - Alle Gamechanger klar aus {{HAUPTLEISTUNG}} und {{AKTUELLES_MODELL}} herleiten.

  OUTPUT VERBOSITY:
  - Skizziere maximal 3 Szenarien als eigenständige <article>-Elemente.
  - Jede Szenarienbeschreibung darf höchstens 5 kurze Absätze (<p>) enthalten, maximal 2 Sätze pro Absatz.
  - Halte die Beschreibungen kompakt und übersichtlich; vermeide Details, die nicht gefordert sind.
  - Priorisiere vollständige, umsetzbare Antworten innerhalb dieses Längenrahmens.
  - Falls Updates oder Rückfragen angesprochen werden, antworte mit maximal 2 Sätzen, außer der/die Nutzer:in verlangt explizit ausführlichere Betreuung.

-->

<section class="section gamechanger">
  <h2>Gamechanger – Wie sich das Geschäftsmodell mit KI weiterentwickeln kann</h2>

  <p>
    Auf Basis von {{AKTUELLES_MODELL}} in der Branche <strong>{{BRANCHE}}</strong> können
    mit KI verschiedene strategische Optionen entwickelt werden, die über reine
    Effizienzgewinne hinausgehen. Für {{UNTERNEHMENSGROESSE}} bedeutet ein „Gamechanger“
    insbesondere Angebote, die sich digital skalieren lassen, ohne dass der persönliche Einsatz in gleichem Maße mitwachsen muss.
  </p>

  <div class="gamechanger-grid">
    <!-- ERWARTETE STRUKTUR (Inhalte müssen vom Modell individuell formuliert werden):
         Für jeden Gamechanger:

         <article class="gamechanger">
           <h3>Gamechanger X – Titel</h3>
           <p><strong>Idee:</strong> Wie wird {{HAUPTLEISTUNG}} in ein skalierbareres
              Angebot übersetzt (z.B. Produktisierung, Plattform, Lizenzmodell)?</p>
           <p><strong>Was ändert sich gegenüber heute?</strong> Kurzer Vergleich zu {{AKTUELLES_MODELL}}.</p>
           <p><strong>Zielgruppe & Nutzen:</strong> Für wen ist das Angebot gedacht und welchen Mehrwert bietet es?</p>
           <p><strong>Skalierungspotenzial:</strong> Qualitative Einschätzung 
              (z.B. „bei guter Positionierung Potenzial für wiederkehrende Erlöse
              im niedrigen oder mittleren fünfstelligen Bereich pro Jahr“).</p>
           <p><strong>Erster Umsetzungsschritt in 6–12 Monaten:</strong>
              Ein konkreter, kleiner Startpunkt, der zu {{INVESTITIONSBUDGET}}
              und {{UNTERNEHMENSGROESSE}} passt (z.B. MVP, Pilot mit wenigen Kunden).
           </p>
         </article>
    -->
  </div>

  <p class="small muted">
    Hinweis: Die beschriebenen Szenarien sind strategische Optionen, keine Planung im engen betriebswirtschaftlichen Sinne.
    Für eine Umsetzung sollten sie durch konkrete Markt-Tests, Preismodelle und Business-Case-Rechnungen ergänzt werden.
  </p>
</section>
