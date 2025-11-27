Developer:
<!-- costs_overview.md – v3.2 GOLD STANDARD+ (CFO-Level Cost Breakdown, size-aware)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     ZWECK:
       - Ergänzung zum Business Case, aber OHNE Wiederholung seiner Inhalte.
       - Detaillierte, transparente Breakdown-Darstellung für CFO/Controlling/Procurement.
       - Tool-by-Tool Liste, versteckte Kosten, Optimierungspotenziale – skaliert nach Unternehmensgröße.

     VERFÜGBARE VARIABLEN:
       - {{BRANCHE_LABEL}}
       - {{UNTERNEHMENSGROESSE_LABEL}}

     VERBOTEN:
       - Wiederholung des Business Case (keine erneute ROI-Berechnung).
       - Textfragmente wie „Platzhalter“, „Freitextfeld“, „TODO“.
       - Unstrukturierte Ausgaben (alles muss in <section>, Tabellen oder Listen stehen).

     SIZE-AWARE-LOGIK:
       - SOLO:
           - Sehr schlanke Tool-Landschaft, Fokus auf wenige Kern-Dienste.
           - Laufende Kosten klein halten, Free-/Low-Cost-Varianten berücksichtigen.
       - TEAM:
           - Mehrere Nutzer:innen, aber noch keine komplexen Strukturen.
           - Risiken: Tool-Wildwuchs, doppelte Lizenzen, unklare Zuständigkeiten.
       - KMU:
           - Mehrere Bereiche, mehrere Rollen, ggf. Mischformen aus Self-Service und zentraler Beschaffung.
           - Wichtig: Konsolidierung, Standards, klare Verantwortung für Budgets und Lizenzen.

     OUTPUT:
       - Valides HTML-Fragment.
       - Klare Untergliederung:
         1) Kurz-Einordnung
         2) Tool-by-Tool Breakdown
         3) Versteckte Kosten
         4) Optimierungspotenziale
-->

<section class="section costs-overview">
  <h2>Detaillierte Kostenübersicht</h2>

  <p>
    Diese Kostenübersicht ergänzt den Business Case um eine transparente Darstellung der
    laufenden und einmaligen Aufwände für den KI-Einsatz rund um
    <strong>{{BRANCHE_LABEL}}</strong>. Die Struktur ist auf die Unternehmensgröße
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> zugeschnitten: Für sehr kleine Setups
    geht es vor allem darum, wenige Kern-Tools wirtschaftlich zu nutzen; in größeren
    Organisationen rücken Konsolidierung, Lizenzen und Governance stärker in den Fokus.
  </p>

  <!-- 1) KURZE KONZEPT-CHECKLISTE -->
  <ul class="concept-checklist">
    <li>Eindeutige Trennung zwischen Investitionen, laufenden Kosten und Zusatzaufwänden.</li>
    <li>Tool-by-Tool Breakdown mit klarer Zuordnung pro Position.</li>
    <li>Versteckte bzw. indirekte Kosten vollständig offenlegen.</li>
    <li>Optimierungspotenziale strukturiert aufführen – angepasst an {{UNTERNEHMENSGROESSE_LABEL}}.</li>
    <li>Keine Wiederholung des Business Case, sondern vertiefende Detailansicht.</li>
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
        <td>1&nbsp;Account (Solo) bis mehrere Nutzer:innen (Team/KMU)</td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>
      <tr>
        <td>Workflow-/Automatisierungstools</td>
        <td>Laufend</td>
        <td>1–3 aktive Nutzende</td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>
      <tr>
        <td>Fachspezifische KI-Tools (z.&nbsp;B. Branchenlösungen)</td>
        <td>Laufend</td>
        <td>nach Bedarf</td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>
      <tr>
        <td>Speicher- und Infrastrukturkosten</td>
        <td>Laufend</td>
        <td>Projekt- oder Mandanten-basiert</td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>
      <tr>
        <td>Onboarding, Schulung, Enablement</td>
        <td>Einmalig / periodisch</td>
        <td>abhängig von Anzahl der Beteiligten</td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>
      <tr>
        <td>Externe Beratung / Implementierungsunterstützung</td>
        <td>Einmalig / projektbezogen</td>
        <td>Projektumfang</td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>
    </tbody>
  </table>

  <!-- 3) VERSTECKTE KOSTEN -->
  <h3>Versteckte und indirekte Kosten</h3>
  <ul class="hidden-costs">
    <li>Interne Abstimmungszeiten für neue Workflows und Freigaben.</li>
    <li>Aufwände für Pflege und Aktualisierung von Vorlagen, Prompts und Dokumentation.</li>
    <li>Zusätzliche Zeit für Datenschutz-, Compliance- und Qualitätsprüfungen.</li>
    <li>Kleinere Zusatzlizenzen (z.&nbsp;B. Speicher, optionale Add-ons, erweiterte Nutzung).</li>
    <li>Kontextwechsel und Lernzeiten beim Einführen neuer Tools.</li>
  </ul>

  <!-- 4) OPTIMIERUNGSPOTENZIALE -->
  <h3>Ansatzpunkte zur Optimierung der laufenden Kosten</h3>
  <ol class="optimization-list">
    <li>Konsolidierung von Tools, um Mehrfachkosten zu reduzieren und Verwaltung zu vereinfachen.</li>
    <li>Klar definierte Workflows zur Minimierung interner Abstimmungszeiten.</li>
    <li>Regelmäßige Überprüfung der Lizenznutzung (aktive vs. bezahlte Zugänge).</li>
    <li>Automatisierung wiederkehrender Schritte zur Senkung der laufenden Aufwände.</li>
    <li>Gezielte Nutzung von Jahres- oder Paketpreisen, sofern wirtschaftlich sinnvoll.</li>
  </ol>

  <p class="small muted">
    Die dargestellten Positionen sollen nicht jede einzelne Rechnung abbilden, sondern
    einen strukturierten Rahmen für die Kostenplanung bieten. Je nach
    Unternehmensgröße <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> kann der Fokus
    stärker auf der Begrenzung einzelner Kernkosten (Solo), der Vermeidung von
    Doppelstrukturen (Team) oder der Standardisierung und Konsolidierung über mehrere
    Bereiche hinweg (KMU) liegen.
  </p>
</section>
