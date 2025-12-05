Developer:
<!-- ki_skillplan.md – v1.1 PLATIN++ SPRINT N (KI-Kompetenz-Fahrplan)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     ZIEL:
     - Klarer, verständlicher Kompetenzaufbau-Plan für KI-Nutzung.
     - 3 Stufen: Basis → Pro → Experte (mit Zeitrahmen).
     - Praxisnah, ohne Fachjargon, sofort umsetzbar.
     - Textlänge: 100–150 Wörter (STRIKT EINHALTEN!)

     VERFÜGBARE VARIABLEN:
       {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, {{COMPANY_SIZE}}

     SIZE-AWARE-LOGIK:
       SOLO: Fokus auf Selbstlernen, Online-Ressourcen, learning-by-doing
       TEAM: Gemeinsames Lernen, Peer-Reviews, interne Workshops
       KMU: Strukturierte Schulungen, externe Trainer, Zertifizierungen

     PFLICHTSTRUKTUR (3 Stufen):
     1. Basis (0–3 Monate)
        - Prompting-Grundlagen
        - Textautomatisierung (E-Mails, Vorlagen)
        - Erste Workflows testen
     2. Pro (3–9 Monate)
        - Workflow-Automatisierung
        - Datenqualität & Strukturierung
        - Analyseketten aufbauen
     3. Experte (9–18 Monate)
        - RAG (Retrieval-Augmented Generation)
        - KI-Agents & Automatisierung
        - Governance & Qualitätssicherung

     STIL:
       - Sehr verständlich, keine Fachbegriffe ohne Erklärung
       - Konkrete Beispiele statt Theorie
       - Motivierend, aber realistisch

     Nicht verwenden:
       - Keine Platzhalter oder Template-Marker
       - Keine technischen Pipeline-Begriffe
       - Keine übertriebenen Versprechen

     SPRINT N - SOLO PERSONA REGELN (STRIKT!):
     {% if COMPANY_SIZE == "solo" %}
     NICHT VERWENDEN für Solo:
     - "Team aufbauen" → stattdessen: "Kapazität erweitern"
     - "Mitarbeiter schulen" → stattdessen: "sich weiterbilden"
     - "Teams" → stattdessen: "Kapazitäten"
     - "Fachbereich" → stattdessen: "Arbeitsfeld"
     - "Abteilung" → stattdessen: "Arbeitsbereich"
     Formulierungen ohne Team-/Abteilungsbegriff verwenden!
     {% endif %}
-->

<section class="section skill-plan">
  <h2>KI-Kompetenz-Fahrplan</h2>

  <p>
    Für <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in <strong>{{BRANCHE_LABEL}}</strong>
    empfiehlt sich ein strukturierter Kompetenzaufbau in drei Stufen.
  </p>

  <div class="skill-levels">
    <div class="level basis">
      <h4>Stufe 1: Basis (0–3 Monate)</h4>
      <ul>
        <li><strong>Prompting lernen:</strong> Klare Anweisungen formulieren, Ergebnisse prüfen</li>
        <li><strong>Textautomatisierung:</strong> E-Mail-Vorlagen, Standardantworten, Dokumentenentwürfe</li>
        <li><strong>Erste Tests:</strong> KI im Alltag ausprobieren, Grenzen kennenlernen</li>
      </ul>
    </div>

    <div class="level pro">
      <h4>Stufe 2: Pro (3–9 Monate)</h4>
      <ul>
        <li><strong>Automatisierung:</strong> Wiederkehrende Abläufe mit KI-Unterstützung beschleunigen</li>
        <li><strong>Datenqualität:</strong> Strukturierte Eingaben, konsistente Formate, Prüfroutinen</li>
        <li><strong>Analyseketten:</strong> Mehrstufige Aufgaben (z.B. Recherche → Zusammenfassung → Handlungsempfehlung)</li>
      </ul>
    </div>

    <div class="level expert">
      <h4>Stufe 3: Experte (9–18 Monate)</h4>
      <ul>
        <li><strong>RAG-Systeme:</strong> KI mit eigenen Dokumenten/Datenbanken verbinden</li>
        <li><strong>KI-Agents:</strong> Automatisierte Assistenten für komplexe Aufgaben</li>
        <li><strong>Governance:</strong> Qualitätssicherung, Richtlinien, kontinuierliche Verbesserung</li>
      </ul>
    </div>
  </div>

  <p class="small muted">
    Tipp: Jede Stufe aufbauen, bevor die nächste beginnt – solide Grundlagen ermöglichen schnelleren Fortschritt.
  </p>
</section>
