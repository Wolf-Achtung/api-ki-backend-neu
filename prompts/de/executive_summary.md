Developer:
<!-- executive_summary.md – v3.0 GOLD STANDARD+ (Summary + Size-Layer + Context-Integration)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences im OUTPUT.

     ZIEL:
     - Eine perfekt strukturierte, einseitige Executive Summary generieren,
       die alle Kernaspekte des KI-Status-Reports in 3–5 prägnanten Abschnitten verdichtet.

     VERBOTEN:
     - Keine Platzhalter-Strings ("Platzhalter", "[...]", "{XYZ}").
     - Keine technischen Pipeline-Begriffe (CONTEXT_..., SCORE_..., etc.).
     - Keine Roh-Variablennamen im Output ({{BRANCHE_LABEL}} etc. dürfen im HTML aber stehen bleiben).

     KONTEXTQUELLEN (werden als Klartext geliefert):
     - Quick Wins (CONTEXT_QUICK_WINS)
     - 90-Tage-Roadmap (CONTEXT_ROADMAP_90D)
     - 12-Monats-Roadmap (CONTEXT_ROADMAP_12M)
     - Business Case (CAPEX, OPEX, Payback, ROI_12M)
     - Förderpotenzial
     - Tool-Empfehlungen
     - Scores: Governance, Sicherheit, Wertschöpfung, Befähigung, Gesamt

     VERFÜGBARE FRAGEBOGEN-VARIABLEN (Labels):
     - {{BRANCHE_LABEL}}
     - {{UNTERNEHMENSGROESSE_LABEL}}
     - {{HAUPTLEISTUNG}}
     - {{BUNDESLAND_LABEL}}

     GRÖSSENLOGIK (Solo / Team / KMU)
     --------------------------------------------------------------
     INTERN: COMPANY_SIZE ∈ {"solo","team","kmu"}.

     SOLO ("1 (Solo" im Label):
       - Direkte Sie-Ansprache.
       - Keine Begriffe wie Abteilung, Bereich, Team.
       - Fokus: persönliche Entlastung, schnelle Resultate, pragmatische Umsetzung.
       - Maßnahmen immer realistisch für eine einzelne Person.

     TEAM (2–10):
       - Leichte Organisationssprache erlaubt ("Team", "Kolleg:innen").
       - Verantwortlichkeiten = Rollen, keine Abteilungen.
       - Fokus: gemeinsame Routinen, schnelle Abstimmungen, klare Prioritäten.

     KMU (11–100):
       - Organisationssprache erlaubt: Teams, Bereiche, Verantwortliche.
       - Kein Konzernvokabular ("Division", "Business Unit").
       - Fokus: skalierbare Umsetzung, Governance, Bereichs-Abstimmung.

     STIL:
       - Klar, präzise, geschäftsorientiert.
       - Keine Buzzwords, kein Marketingtext.
       - Maximal 5 Absätze, jeweils max. 4 Sätze.
       - Verdichtung statt Wiederholung: 3–5 stärkste Botschaften des Reports.

-->

<section class="section executive-summary">
  <h2>Executive Summary</h2>

  <p>
    Diese Executive Summary fasst die aktuelle KI-Positionierung eines Unternehmens in der
    Branche <strong>{{BRANCHE_LABEL}}</strong> zusammen – ausgerichtet auf die
    Unternehmensgröße <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> und den Kernprozess
    <strong>{{HAUPTLEISTUNG}}</strong>. Sie liefert einen klaren Überblick zu Ausgangslage,
    Stärken, zentralen Hebeln und den nächsten Schritten, die für eine wirkungsvolle KI-Einführung
    entscheidend sind.
  </p>

  <h3>Ausgangslage & Scores</h3>
  <p>
    Die Score-Ergebnisse zeigen ein differenziertes Bild: Governance, Sicherheit,
    Wertschöpfungspotenzial und Befähigung geben Hinweise darauf, wo das Unternehmen bereits
    solide Grundlagen besitzt und wo noch strukturelle oder organisatorische Lücken bestehen.
    Die Kombination aus Stärken – etwa in klar definierten Arbeitsroutinen oder ersten digitalen
    Standards – und einzelnen Entwicklungsfeldern bildet die Basis für die folgenden Empfehlungen.
  </p>

  <h3>Wichtigste Quick Wins & kurzfristige Maßnahmen</h3>
  <p>
    Die Quick Wins betreffen vor allem jene Schritte im Prozess <strong>{{HAUPTLEISTUNG}}</strong>,
    die sich kurzfristig standardisieren oder teilautomatisieren lassen. Dazu zählen typische
    wiederkehrende Aufgaben, die in den nächsten 90 Tagen durch klar definierte Workflows,
    bessere Vorlagen oder KI-gestützte Unterstützung spürbare Entlastung bringen können.
    Diese Maßnahmen sind der direkte Einstieg in eine stabilere und effizientere Arbeitsweise.
  </p>

  <h3>Business Case & Förderpotenzial</h3>
  <p>
    Der Business Case zeigt eine realistische Relation zwischen Investition (CAPEX/OPEX),
    monatlicher Entlastung und Amortisationsdauer. Die erwartete Wirkung ist klar positiv –
    sowohl in Zeitersparnis als auch im qualitativen Zugewinn. Zusätzlich können Förderprogramme
    auf Landes- oder Bundesebene die anfängliche Investition spürbar reduzieren und die
    Wirtschaftlichkeit beschleunigen.
  </p>

  <h3>Nächste Schritte für Geschäftsführung</h3>
  <p>
    Die Geschäftsführung sollte die Umsetzung in drei Schritten priorisieren: Erstens die
    kurzfristigen Quick Wins, zweitens ein klar definierter Pilotprozess als realer Test unter
    Alltagsbedingungen, drittens der Aufbau leichter Governance- und Dokumentationsstandards,
    um die Qualität der Ergebnisse dauerhaft sicherzustellen. Diese drei Bausteine legen den
    Grundstein für die nachfolgenden 12-Monats-Initiativen und eine skalierbare Nutzung von KI.
  </p>
</section>
