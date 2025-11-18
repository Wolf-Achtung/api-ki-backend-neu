<!-- Quick Wins (DE) - ENHANCED mit Context-System v2.0 -->
<!-- Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown‑Fences.
     Nutze die Platzhalter:
     - {BRANCHE_LABEL}, {UNTERNEHMENSGROESSE_LABEL}, {BUNDESLAND_LABEL}, {HAUPTLEISTUNG}
     - {report_date}, {report_year}, {kundencode}, {report_id}
     Schreibe präzise, fachlich, motivierend – kein Marketing‑Sprech. -->

<section class="section quick-wins">
  <h2>Quick Wins (0–90 Tage)</h2>
  
  <!-- CONTEXT-INJECTION BLOCK - wird vom PromptBuilder dynamisch eingefügt -->
  {CONTEXT_BLOCK}
  <!-- END CONTEXT-INJECTION -->
  
  <p><strong>Aufgabe:</strong> Erstelle 6 konkrete Quick Wins die <em>spezifisch</em> auf {{HAUPTLEISTUNG}} in der Branche {{BRANCHE_LABEL}} für ein Unternehmen der Größe {{UNTERNEHMENSGROESSE_LABEL}} zugeschnitten sind.</p>
  
  <p><strong>Anforderungen pro Quick Win:</strong></p>
  <ul class="requirements small">
    <li>Titel: Prägnant, maximal 6 Worte, KEIN Marketing-Sprech</li>
    <li>Beschreibung: 1-2 Sätze, KONKRETES Tool/API nennen (z.B. "GPT-4 API", "Fireflies.ai", "Make.com")</li>
    <li>Zeitersparnis: Realistisch für die Unternehmensgröße {{UNTERNEHMENSGROESSE_LABEL}}
      <ul>
        <li>Solo: 3-15h/Monat pro Quick Win</li>
        <li>Team (2-10): 5-25h/Monat pro Quick Win</li>
        <li>KMU (11-100): 10-40h/Monat pro Quick Win</li>
      </ul>
    </li>
  </ul>
  
  <p><strong>Quick Wins müssen:</strong></p>
  <ol class="constraints small">
    <li><strong>Branchen-typische Workflows</strong> optimieren (siehe Context oben)</li>
    <li><strong>Pain Points</strong> der Branche addressieren (siehe Context oben)</li>
    <li><strong>Mit vorhandenen Tools</strong> kompatibel sein (siehe Context oben)</li>
    <li><strong>Budget-konform</strong> sein (siehe Context oben für Max-Budgets)</li>
    <li><strong>Verbotene Empfehlungen vermeiden</strong> (siehe Context oben)</li>
    <li><strong>Hauptleistung direkt verbessern:</strong> "{{HAUPTLEISTUNG}}"</li>
  </ol>
  
  <p><strong>Output-Format:</strong></p>
  <ul class="quick-wins-list">
    <li>
      <strong>[Prägnanter Titel]:</strong>
      [Beschreibung mit konkretem Tool/API-Namen]
      Ersparnis: <em>[X] h/Monat</em>
    </li>
    <!-- 5 weitere Quick Wins nach gleichem Format -->
  </ul>
  
  <p class="summary"><strong>Gesamt-Zeitersparnis: [Summe aller Quick Wins] h/Monat</strong></p>
  
  <p class="note small muted">
    <strong>Hinweis:</strong> Diese Quick Wins basieren auf den typischen Workflows und Pain Points 
    der Branche {{BRANCHE_LABEL}} für Unternehmen der Größe {{UNTERNEHMENSGROESSE_LABEL}}.
    Die Zeitersparnisse sind konservativ geschätzt und setzen voraus, dass die Tools 
    kontinuierlich genutzt werden.
  </p>
</section>
