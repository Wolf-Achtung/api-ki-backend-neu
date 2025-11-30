Developer:
<!-- roadmap_90d.md – v6.0 PLATIN+ STREAMLINED
     Ziel: 6 Phasen mit je 80-100 Wörtern (= 500-700 Wörter gesamt).
     Antworte ausschließlich mit validem HTML. Keine Markdown-Fences.

     STRUKTUR (6 Phasen):
       Phase 1: Woche 1-2 – Zielbild & Prioritäten
       Phase 2: Woche 3-4 – Datenqualität & Workflow-Grundlagen
       Phase 3: Woche 5-6 – Quick-Wins & erste Wirkung
       Phase 4: Woche 7-8 – Qualitätsstandards
       Phase 5: Woche 9-10 – Monitoring & Iteration
       Phase 6: Woche 11-13 – Konsolidierung & Skalierungsvorbereitung

     Pro Phase PFLICHT:
       - Ziel (1-2 Sätze)
       - Deliverables (3-4 Bullets)
       - Rollen (size-aware)
       - KPI (1-2 messbare Kennzahlen)

     VARIABLEN:
       {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, COMPANY_SIZE

     SIZE-AWARE (COMPANY_SIZE):
       solo: persönliche Routinen, eigene Dokumentation, keine Teams
       team: Rollen, gemeinsame Standards, Abstimmung
       kmu: Fachbereiche, Governance, Pilotflächen

     REGELN:
       - Branchenspezifische Workflows aus CONTEXT_BLOCK nutzen
       - Sachlich, konkret, keine Floskeln
       - Keine Platzhalter, keine Developer-Sprache
-->

<section class="section roadmap-90d">
  <h2>Strategische 90-Tage-Roadmap</h2>

  <p>
    Diese Roadmap zeigt, wie ein Unternehmen der Größe <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>
    innerhalb von 90 Tagen KI-gestützte Arbeitsweisen im Bereich
    <strong>{{HAUPTLEISTUNG}}</strong> strukturiert etabliert. Sie nutzt typische
    Workflows, Datenarten und Pain Points der Branche <strong>{{BRANCHE_LABEL}}</strong>
    und verbindet schnelle Wirkung mit soliden Grundlagen.
  </p>

  <p>
    Die folgenden Phasen schaffen Klarheit, reduzieren Reibungspunkte und sorgen dafür,
    dass KI nach 90 Tagen dauerhaft, stabil und messbar Mehrwert liefert.
  </p>

  <ol>

    <!-- PHASE 1 – Woche 1–2 -->
    <li>
      <h3>Woche 1–2: Zielbild, Use-Case-Rahmen & Prioritäten</h3>
      <p><strong>Ziel:</strong> Klar definieren, wo KI im Bereich {{HAUPTLEISTUNG}} den stärksten Nutzen bringt – gestützt auf branchentypische Workflows und Pain Points.</p>
      <p><strong>Deliverables:</strong></p>
      <ul>
        <li>Fokus-Definition: 1–2 priorisierte Aufgaben aus {{BRANCHE_LABEL}} mit hohem Wirkungspotenzial.</li>
        <li>Übersicht branchentypischer Beispiele (5–10 Fälle).</li>
        <li>Mini-Checkliste für Qualität, Fakten, Tonalität und Freigabe.</li>
      </ul>
      <p><strong>Rollen &amp; Verantwortlichkeiten:</strong><br>
        {% if COMPANY_SIZE == "solo" %}
          Persönliche Priorisierung & Dokumentation.
        {% elif COMPANY_SIZE == "team" %}
          Teamlead + KI-Owner.
        {% else %}
          Fachbereich + Prozessverantwortliche.
        {% endif %}
      </p>
      <p><strong>KPI:</strong> Priorisierte Use Cases + erste Qualitätskriterien definiert.</p>
    </li>

    <!-- PHASE 2 – Woche 3–4 -->
    <li>
      <h3>Woche 3–4: Datenqualität, Beispiele & Workflow-Grundlagen</h3>
      <p><strong>Ziel:</strong> Saubere Basis schaffen, damit KI stabile, belastbare Ergebnisse liefert.</p>
      <p><strong>Deliverables:</strong></p>
      <ul>
        <li>Sammlung typischer Fälle (mind. 10) aus {{BRANCHE_LABEL}} – real, vollständig, strukturiert.</li>
        <li>Erste stabile Workflow-Schritte (Input → KI → Review → Freigabe).</li>
        <li>Definition messbarer Kriterien: Vollständigkeit, Korrektheit, Stil.</li>
      </ul>
      <p><strong>Rollen &amp; Verantwortlichkeiten:</strong><br>
        {% if COMPANY_SIZE == "solo" %}
          Eigene Dokumentation.
        {% elif COMPANY_SIZE == "team" %}
          Gemeinsame Qualitätsdefinition im Team.
        {% else %}
          Fachbereich + Qualitätssicherung.
        {% endif %}
      </p>
      <p><strong>KPI:</strong> Dokumentierte Workflows + strukturierte Beispiele vorhanden.</p>
    </li>

    <!-- PHASE 3 – Woche 5–6 -->
    <li>
      <h3>Woche 5–6: Quick-Wins & erste messbare Wirkung</h3>
      <p><strong>Ziel:</strong> Spürbare Entlastung durch die ersten 1–2 KI-gestützten Quick-Wins.</p>
      <p><strong>Deliverables:</strong></p>
      <ul>
        <li>Implementierung der 1–2 wirkungsstärksten Quick-Wins (branchenabhängig: z. B. Angebotsentwurf, Content-Draft, Datenprüfung).</li>
        <li>Kurztests: Zeitersparnis, Konsistenz, Risikominderung.</li>
        <li>Lern-/Fehlerliste für spätere Standards.</li>
      </ul>
      <p><strong>Rollen &amp; Verantwortlichkeiten:</strong><br>
        {% if COMPANY_SIZE == "solo" %}
          Umsetzung durch Inhaber:in.
        {% elif COMPANY_SIZE == "team" %}
          KI-Owner + direkt Beteiligte.
        {% else %}
          Fachbereich + Prozessverantwortliche.
        {% endif %}
      </p>
      <p><strong>KPI:</strong> Erste Wirkung (10–25&nbsp;% Zeitgewinn).</p>
    </li>

    <!-- PHASE 4 – Woche 7–8 -->
    <li>
      <h3>Woche 7–8: Qualitätsstandards & einheitliche Arbeitsweise</h3>
      <p><strong>Ziel:</strong> Reproduzierbare Ergebnisse sicherstellen, bevor Prozesse automatisiert werden.</p>
      <p><strong>Deliverables:</strong></p>
      <ul>
        <li>Kurz-Styleguide für KI-Ergebnisse (Stil, Fakten, Fachlichkeit).</li>
        <li>Dokumentation der neuen Arbeitsweise (Input-Regeln, Prüfschritte, Freigaben).</li>
        <li>Abstimmung zwischen beteiligten Rollen/Fachbereichen.</li>
      </ul>
      <p><strong>Rollen &amp; Verantwortlichkeiten:</strong><br>
        {% if COMPANY_SIZE == "solo" %}
          Self-Review-Prozesse.
        {% elif COMPANY_SIZE == "team" %}
          Teamreview + Qualitätsverantwortliche.
        {% else %}
          Fachbereich + Qualitätssicherung + Datenschutz/IT.
        {% endif %}
      </p>
      <p><strong>KPI:</strong> Höhere Ersttrefferquote, weniger Korrekturen.</p>
    </li>

    <!-- PHASE 5 – Woche 9–10 -->
    <li>
      <h3>Woche 9–10: Monitoring, Reporting & iterative Verbesserung</h3>
      <p><strong>Ziel:</strong> Wirkung sichtbar machen und Optimierungen ableiten.</p>
      <p><strong>Deliverables:</strong></p>
      <ul>
        <li>Einfaches Monitoring (Zeit, Qualität, Fehler, Konsistenz).</li>
        <li>Kurzbericht zu Fortschritt und offenen Herausforderungen.</li>
        <li>Optimierte Templates und Workflows.</li>
      </ul>
      <p><strong>Rollen &amp; Verantwortlichkeiten:</strong><br>
        {% if COMPANY_SIZE == "solo" %}
          Persönliche Analyse & Anpassung.
        {% elif COMPANY_SIZE == "team" %}
          Owner + Teamreview.
        {% else %}
          Fachbereich + ggf. Controlling/IT.
        {% endif %}
      </p>
      <p><strong>KPI:</strong> Dokumentierte Verbesserungen + Trendlinien.</p>
    </li>

    <!-- PHASE 6 – Woche 11–13 -->
    <li>
      <h3>Woche 11–13: Entscheidung, Konsolidierung & Vorbereitung der Skalierung</h3>
      <p><strong>Ziel:</strong> Auf Basis echter Ergebnisse entscheiden, wie KI weiter ausgebaut wird.</p>
      <p><strong>Deliverables:</strong></p>
      <ul>
        <li>Bewertung der KI-Eignung und Wirkung für {{HAUPTLEISTUNG}}.</li>
        <li>Strategische Entscheidung: Stabilisieren / Ausweiten / Vertiefen.</li>
        <li>Skalierungs-Backlog (Use Cases, Automatisierungen, Integrationen).</li>
      </ul>
      <p><strong>Rollen &amp; Verantwortlichkeiten:</strong><br>
        {% if COMPANY_SIZE == "solo" %}
          Geschäftsführung.
        {% elif COMPANY_SIZE == "team" %}
          Führung + KI-Owner.
        {% else %}
          Management + Bereichsleitung.
        {% endif %}
      </p>
      <p><strong>KPI:</strong> Priorisiertes Backlog + klare Entscheidung für die nächsten 6–12 Monate.</p>
    </li>

  </ol>

  <p class="small muted">
    Diese 90-Tage-Roadmap legt die strukturelle Grundlage für eine stabile, sichere
    und wirkungsorientierte Einführung von KI in <strong>{{HAUPTLEISTUNG}}</strong>.
    Sie schafft klare Arbeitsweisen, schnelle Vorteile und eine belastbare Basis für
    Pilotprojekte und Skalierung im Folgejahr.
  </p>
</section>
