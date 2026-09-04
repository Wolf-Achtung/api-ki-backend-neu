Developer:
<!-- costs_overview.md – v4.0 GOLD STANDARD+ (CFO-Level Cost Breakdown, size- & branch-aware)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     BRANCHENBEZEICHNUNG-REGEL:
     Die Branchenbezeichnung "{{BRANCHE_LABEL}}" darf MAXIMAL 2x im gesamten Text vorkommen.
     Ab der 3. Verwendung NUR noch Kurzformen: "Ihr Unternehmen", "Ihre Branche", "Ihr Geschäftsfeld".

     ZWECK:
       - Ergänzung zum Business Case, aber OHNE Wiederholung seiner Inhalte.
       - Branchen- und größenabhängige Kostendynamiken klar benennen.
       - CFO- und kaufmännisch verwertbare Struktur liefern (Transparenz + Steuerungshebel).
       - Nutzung der Daten aus dem CONTEXT_BLOCK (branch + size), den der PromptEnhancer injiziert.

     VARIABLEN:
       - {{BRANCHE_LABEL}}
       - {{UNTERNEHMENSGROESSE_LABEL}}
       - {{HAUPTLEISTUNG}}

     Nicht verwenden:
       - Wiederholung des Business Case (keine ROI-/Payback-Berechnung).
       - Regieanweisungen, Platzhaltertexte, Beispieltexte wie „xxx".
       - Unstrukturierte Ausgaben – immer mit section / table / lists.

     CROSS-SECTION-ZAHLEN (VERBINDLICH):
       - Nenne NIE konkrete ROI-Werte, Payback-Zeiträume oder Investitionssummen aus dem Business Case.
       - Erfinde KEINE Euro-Beträge für Kostenpositionen — beschreibe Kostenstruktur QUALITATIV.
       - Wenn du auf Business-Case-Zahlen verweisen willst: „Details siehe Business Case."
       - Erfinde KEINE Lizenzpreise, Tool-Kosten oder Stundensätze, die nicht im Input stehen.

     SIZE-AWARE-LOGIK (verbindlich):
       - SOLO:
           - Sehr schlanke Tool-Landschaft.
           - Fokus auf Basis-Modelle, 1–2 Kern-Tools, niedrige laufende Kosten.
           - Schulung = minimal + Selbstlernanteil.
       - TEAM (2–10):
           - Mehrere Nutzer:innen → Lizenzmultiplikatoren.
           - Typische Risiken: Tool-Wildwuchs, doppelte Lizenzen, fehlende Verantwortlichkeiten.
           - Schulungsaufwand verteilt.
       - KMU (11–100):
           - Mehrbereichs-Strukturen, Procurement-relevant.
           - Notwendigkeit: Tool-Konsolidierung, Standardisierung, Lizenz- & Rechteverwaltung.
           - Schulung/Enablement als wiederkehrender Posten.

     BRANCHEN-AWARE (verbindlich):
       - Nutze branchenspezifische Tools, Workflows, Pain Points und typische Datenherkünfte aus dem CONTEXT_BLOCK.
       - Branchenabhängig variieren:
           - fachliche Spezial-Tools (z. B. Schnitt- und Grading-Software, DAW und Stimmsynthese, Redaktionssystem, Game-Engine, Media-Asset-Management)
           - Compliance-/Regulatorik-Aufwände (z. B. Finanzen, Gesundheit)
           - Datenaufbereitungskosten (z. B. Produktion vs. Dienstleistung)
           - Integrationskosten (ERP/CRM/Branchensysteme)

     ZIEL:
       - Am Ende soll ein CFO oder Geschäftsführender glasklar verstehen:
           1) Welche Kostenblöcke in seiner Branche in der Regel auftreten.
           2) Wie sich die Unternehmensgröße auf die Kostenstruktur auswirkt.
           3) Wo realistische Einspar- und Konsolidierungspotenziale liegen.

     OUTPUT-STRUKTUR:
       - <section class="section costs-overview">
           - h2
           - Einleitung (branch + size)
           - 1) Konzept-Checkliste
           - 2) Tool-by-Tool Breakdown
           - 3) Versteckte Kosten (branch- & size-aware)
           - 4) Optimierungspotenziale (klarer CFO-Fokus)
           - Schlussnotiz
-->

<section class="section costs-overview">
  <h2>Detaillierte Kostenübersicht</h2>

  <p>
    Diese Kostenübersicht ergänzt den Business Case um eine transparente,
    branchen- und größenabhängige Darstellung der laufenden und einmaligen Aufwände
    rund um <strong>{{HAUPTLEISTUNG}}</strong> in der Branche
    <strong>{{BRANCHE_LABEL}}</strong>. Die Struktur ist auf die Unternehmensgröße
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> zugeschnitten:
    In kleinen Setups stehen wenige, klar ausgewählte Kern-Tools im Mittelpunkt,
    während in Teams und KMU Faktoren wie Lizenzmultiplikatoren, Compliance-Aufwände
    und Tool-Konsolidierung stärker ins Gewicht fallen.
  </p>

  <!-- 1) KURZE KONZEPT-CHECKLISTE -->
  <ul class="concept-checklist">
    <li>Trennung zwischen einmaligen Investitionen (Setup, Onboarding) und laufenden Kosten (Lizenzen, Infrastruktur).</li>
    <li>Branchenspezifische Spezial-Tools berücksichtigen (laut CONTEXT_BLOCK).</li>
    <li>Größenabhängige Kostentreiber identifizieren (Solo: Kern-Tools; KMU: Multi-User-Lizenzen, Compliance-Aufwände).</li>
    <li>Versteckte Kosten (Zeit, Abstimmungen, Governance) systematisch einplanen.</li>
    <li>Optimierungspotenziale klar zuordnen: Reduktion, Standardisierung, Automatisierung.</li>
  </ul>

  <!-- 2) TOOL-BY-TOOL BREAKDOWN -->
  <h3>Kostenübersicht je Tool / System</h3>
  <table class="table">
    <thead>
      <tr>
        <th>Position</th>
        <th>Art</th>
        <th>Menge / Nutzer:innen</th>
        <th>Monatliche Kosten</th>
        <th>Jährliche Kosten</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Basis-KI-Plattform / Modellzugang</td>
        <td>Laufend</td>
        <td>
          <!-- size-aware -->
          {{UNTERNEHMENSGROESSE_LABEL}}:<br>
          Solo: 1 Account<br>
          Team: 2–5 Accounts<br>
          KMU: 5–20 Accounts
        </td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>

      <tr>
        <td>Workflow-/Automatisierungstools</td>
        <td>Laufend</td>
        <td>
          Branchentypisch (laut CONTEXT_BLOCK):<br>
          z.&nbsp;B. Marketing: Content-Automation;<br>
          IT/Tech: API-/Script-Automation;<br>
          Gesundheit/Finanzen: Compliance-Workflow-Tools.
        </td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>

      <tr>
        <td>Fachspezifische KI- oder Branchen-Tools</td>
        <td>Laufend</td>
        <td>
          Variiert nach Sparte (z.&nbsp;B. Schnittsystem, DAW, Redaktionssystem, Game-Engine, Media-Asset-Management, CRM)
        </td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>

      <tr>
        <td>Speicher- & Infrastrukturkosten (Cloud/Hosting)</td>
        <td>Laufend</td>
        <td>Je nach Datenvolumen & Workflows ({{BRANCHE_LABEL}})</td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>

      <tr>
        <td>Datenaufbereitung & Integration (einmalig/periodisch)</td>
        <td>Einmalig / periodisch</td>
        <td>Abhängig von Quellsystemen (CRM, ERP, Produktion, etc.)</td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>

      <tr>
        <td>Schulung & Enablement</td>
        <td>Einmalig / wiederkehrend</td>
        <td>
          Solo: Selbstlern-Fokus<br>
          Team: kurze Workshops<br>
          KMU: Trainingsreihe + Richtlinien
        </td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>

      <tr>
        <td>Externe Beratung / Implementierung</td>
        <td>Einmalig</td>
        <td>Projektumfang (Use-Case-Design, Integration, Dokumentation)</td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>
    </tbody>
  </table>

  <!-- 3) VERSTECKTE KOSTEN -->
  <h3>Versteckte und indirekte Kosten</h3>
  <ul class="hidden-costs">
    <li>Interne Abstimmungszeiten: stärker ausgeprägt in Team/KMU-Strukturen.</li>
    <li>Anpassung vorhandener Workflows an KI-gestützte Prozesse.</li>
    <li>Aufwände für die Pflege und Aktualisierung von Vorlagen, Prompts und Dokumentation.</li>
    <li>Branchenspezifische Zusatzaufwände:
      <ul>
        <li>Film/TV und Postproduktion: Archiv-Verschlagwortung, Rechte-Metadaten, Speicher für Rohmaterial.</li>
        <li>Verlag und Agentur: Asset-Management, Markenrichtlinien, Freigabeprozesse.</li>
        <li>Audio und Games: Lizenzprüfung für Stimmen und Assets, Qualitätssicherung.</li>
      </ul>
    </li>
    <li>Kleinere Zusatzlizenzen (z.&nbsp;B. Speicher, Plug-ins, optionale Add-ons).</li>
    <li>Kontextwechsel und Lernzeiten bei neuen Tools.</li>
  </ul>

  <!-- 4) OPTIMIERUNGSPOTENZIALE -->
  <h3>Ansatzpunkte zur Optimierung der laufenden Kosten</h3>
  <ol class="optimization-list">
    <li><strong>Tool-Konsolidierung:</strong> Reduktion parallel genutzter Systeme (besonders relevant für Teams und KMU).</li>
    <li><strong>Lizenz-Review:</strong> aktive vs. bezahlte Nutzer:innen, jährliche statt monatliche Abrechnung.</li>
    <li><strong>Standardisierung:</strong> feste Templates, klare Governance, minimiert Abstimmungszeiten.</li>
    <li><strong>Automatisierung:</strong> wiederkehrende Tätigkeiten mit Low-Code-/KI-Workflows reduzieren Workload & Kosten.</li>
    <li><strong>Daten-Optimierung:</strong> bessere Datenqualität senkt Integrations- und Fehlerkosten.</li>
  </ol>

  <p class="small muted">
    Diese Kostenübersicht dient als strukturierter Rahmen für Planung, Controlling und
    Priorisierung. Je nach Unternehmensgröße <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>
    verschiebt sich der Fokus zwischen schlanken Kernkosten (Solo), Vermeidung von
    Doppelstrukturen (Team) und Standardisierung über mehrere Bereiche hinweg (KMU).
  </p>
</section>
