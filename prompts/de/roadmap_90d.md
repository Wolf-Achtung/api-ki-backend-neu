Developer:
<!-- roadmap_90d.md – v3.0 GOLD STANDARD+ (90-Tage-Strategie, size-aware, validator-sicher)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>; KEINE Markdown-Fences.

     ZIEL:
     - Erzeuge eine strategische 90-Tage-Roadmap, die solide Grundlagen für KI legt:
       Struktur, Datenqualität, Qualitätsstandards, erste Quick-Wins, frühe Wirkung.
     - Roadmap ist bewusst strategisch, nicht operativ: Sie zeigt Richtung, Fokus,
       Verantwortlichkeiten und Entscheidungsregeln.

     VERFÜGBARE VARIABLEN:
       {{BRANCHE_LABEL}}
       {{UNTERNEHMENSGROESSE_LABEL}}
       {{HAUPTLEISTUNG}}

     INTERNER SIZE-MODE (aus PromptEnhancer):
       COMPANY_SIZE ∈ {"solo","team","kmu"}

       SOLO (1 Person):
         - Sie-Ansprache.
         - Keine „Teams“, „Bereiche“, „Abteilungen“.
         - Fokus: persönliche Entlastung, klare Routinen, brauchbare Standards.

       TEAM (2–10):
         - „Team“, „Kolleg:innen“, Rollen wie Teamlead / KI-Owner.
         - Fokus: Abstimmungen, arbeitsteilige Umsetzung, einfache Dokumentation.

       KMU (11–100):
         - „Fachbereiche“, „Teams“, „Verantwortliche“.
         - Fokus: Governance, stabilere Strukturen, Pilotbereiche, Standards.

     REGELN:
       - Keine verbotenen Wörter: „Platzhalter“, „Freitextfeld“, TODO, etc.
       - Max. 13 OL-Einträge (Woche 1–13).
       - Pro Phase: Ziel + Deliverables + Rollen/Verantwortlichkeit + KPI.
       - Output muss direkt verwendbares HTML sein.
-->

<section class="section roadmap-90d">
  <h2>Strategische 90-Tage-Roadmap</h2>

  <p>
    Diese 90-Tage-Roadmap beschreibt, wie ein Unternehmen der Größe
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> erste KI-gestützte Arbeitsweisen im
    Bereich <strong>{{HAUPTLEISTUNG}}</strong> etabliert und schrittweise stabilisiert.
    Sie kombiniert Quick Wins mit gezielten Struktur- und Qualitätsmaßnahmen und ist
    auf die Besonderheiten der Branche <strong>{{BRANCHE_LABEL}}</strong> abgestimmt.
  </p>

  <p>
    Die Roadmap schafft Klarheit, definiert Prioritäten und legt die Basis für Piloten
    und spätere Skalierung. Der operative Detailplan entsteht nach Abschluss dieser
    Phase, sobald erste Ergebnisse und Lernerfahrungen vorliegen.
  </p>

  <ol>
    <!-- Woche 1–2 -->
    <li>
      <h3>Woche 1–2: Strategische Ausrichtung & Zielbild</h3>
      <p><strong>Ziel:</strong> Klare Definition, wo und wie KI kurzfristig im Prozess
         <strong>{{HAUPTLEISTUNG}}</strong> unterstützen soll.</p>
      <p><strong>Deliverables:</strong></p>
      <ul>
        <li>Präziser Scope für die 90-Tage-Phase.</li>
        <li>Auswahl der ersten 1–2 Prozessbereiche mit messbarem Nutzenpotenzial.</li>
        <li>Sammlung relevanter Beispiele (Fälle, Texte, Vorgänge).</li>
      </ul>
      <p><strong>Rollen &amp; Verantwortlichkeiten:</strong><br>
        Solo: persönliche Priorisierung.<br>
        Team: Teamlead + KI-Owner.<br>
        KMU: fachlicher Owner + Prozessverantwortliche.
      </p>
      <p><strong>KPI:</strong> Scope klar; 1–2 priorisierte Prozessbereiche definiert.</p>
    </li>

    <!-- Woche 3–4 -->
    <li>
      <h3>Woche 3–4: Datenqualität & Workflow-Basis</h3>
      <p><strong>Ziel:</strong> Aufbau strukturierter Grundlagen für stabile KI-Ergebnisse.</p>
      <p><strong>Deliverables:</strong></p>
      <ul>
        <li>Aufbereitung typischer Fälle & Beispiele.</li>
        <li>Erste einheitliche Workflows (Struktur, Schritte, Hinweise).</li>
        <li>Definition einfacher Qualitätskriterien.</li>
      </ul>
      <p><strong>Rollen &amp; Verantwortlichkeiten:</strong><br>
        Solo: eigene Dokumentation.<br>
        Team: gemeinsame Qualitätsdefinition im Team.<br>
        KMU: Fachbereich + Qualitätssicherung.
      </p>
      <p><strong>KPI:</strong> Dokumentierte Workflows; mindestens 10 strukturierte Beispiele.</p>
    </li>

    <!-- Woche 5–6 -->
    <li>
      <h3>Woche 5–6: Quick-Wins & erste Wirkung</h3>
      <p><strong>Ziel:</strong> Quick-Wins integrieren, um spürbare Zeitersparnis und
         bessere Konsistenz zu erzielen.</p>
      <p><strong>Deliverables:</strong></p>
      <ul>
        <li>Implementierung von 1–2 Quick-Win-Maßnahmen.</li>
        <li>Kurztests zur Messung von Zeitersparnis & Ergebnisqualität.</li>
        <li>Erstellung einer Lern-/Fehlerliste.</li>
      </ul>
      <p><strong>Rollen &amp; Verantwortlichkeiten:</strong><br>
        Solo: Umsetzung durch Inhaberin/Inhaber.<br>
        Team: Owner + direkt beteiligte Kolleg:innen.<br>
        KMU: Fachbereich + Prozessverantwortliche.
      </p>
      <p><strong>KPI:</strong> Erste messbare Wirkung (10–25&nbsp;% Zeitgewinn).</p>
    </li>

    <!-- Woche 7–8 -->
    <li>
      <h3>Woche 7–8: Qualitätsstandards & Abstimmung</h3>
      <p><strong>Ziel:</strong> Reproduzierbare, verlässliche Ergebnisse vor
         weiteren Automatisierungen.</p>
      <p><strong>Deliverables:</strong></p>
      <ul>
        <li>Kurz-Styleguide für KI-Ergebnisse.</li>
        <li>Knappe Dokumentation der neuen Arbeitsweise.</li>
        <li>Interne Abstimmung zwischen relevanten Rollen.</li>
      </ul>
      <p><strong>Rollen &amp; Verantwortlichkeiten:</strong><br>
        Solo: Self-Review-Prozesse.<br>
        Team: Teamreview + Qualitätssicherung.<br>
        KMU: Fachbereich + Qualitätssicherung + Datenschutz/IT.
      </p>
      <p><strong>KPI:</strong> Weniger Korrekturschleifen, höhere Ersttrefferquote.</p>
    </li>

    <!-- Woche 9–10 -->
    <li>
      <h3>Woche 9–10: Monitoring & strategische Anpassung</h3>
      <p><strong>Ziel:</strong> Wirkung sichtbar machen und Verbesserungen ableiten.</p>
      <p><strong>Deliverables:</strong></p>
      <ul>
        <li>Einfaches Monitoring (Zeit, Qualität, Konsistenz).</li>
        <li>Kurzbericht zu Fortschritt & Herausforderungen.</li>
        <li>Optimierung der Vorlagen und Workflows.</li>
      </ul>
      <p><strong>Rollen &amp; Verantwortlichkeiten:</strong><br>
        Solo: persönliche Analyse.<br>
        Team: Owner + Teamreview.<br>
        KMU: Fachbereich + ggf. Controlling/IT.
      </p>
      <p><strong>KPI:</strong> Erste Trendlinien & dokumentierte Verbesserungen.</p>
    </li>

    <!-- Woche 11–13 -->
    <li>
      <h3>Woche 11–13: Entscheidung & Vorbereitung der Skalierung</h3>
      <p><strong>Ziel:</strong> Auf Basis der Erfahrungswerte entscheiden, ob
         Stabilisierung, Ausbau oder Skalierung folgt.</p>
      <p><strong>Deliverables:</strong></p>
      <ul>
        <li>Bewertung der KI-Eignung für {{HAUPTLEISTUNG}}.</li>
        <li>Strategischer Beschluss (Stabilisieren / Ausbauen / Vertiefen).</li>
        <li>Skalierungs-Backlog für Jahr&nbsp;2.</li>
      </ul>
      <p><strong>Rollen &amp; Verantwortlichkeiten:</strong><br>
        Solo: Geschäftsführung.<br>
        Team: Führung + KI-Owner.<br>
        KMU: Management + Bereichsleitung.
      </p>
      <p><strong>KPI:</strong> Strategische Entscheidung & priorisiertes Backlog vorhanden.</p>
    </li>
  </ol>

  <p class="small muted">
    Diese 90-Tage-Roadmap legt die Basis für eine verlässliche Einführung von KI
    in <strong>{{HAUPTLEISTUNG}}</strong>. Sie schafft Struktur, Qualität und
    messbare Wirkung – und bildet damit das Fundament für Piloten und Skalierung
    im weiteren Jahresverlauf.
  </p>
</section>
