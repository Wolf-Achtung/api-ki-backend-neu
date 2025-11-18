<!-- Roadmap 90 Tage (DE) - ENHANCED mit Context-System v2.0 -->
<!-- Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.
     Nutze die Platzhalter:
     - {BRANCHE_LABEL}, {UNTERNEHMENSGROESSE_LABEL}, {BUNDESLAND_LABEL}, {HAUPTLEISTUNG}
     - {report_date}, {report_year}, {kundencode}, {report_id}
     Schreibe präzise, fachlich, motivierend – kein Marketing-Sprech. -->

<section class="section roadmap-90d">
  <h2>Roadmap 90 Tage (Pilot-Phase)</h2>
  
  <!-- CONTEXT-INJECTION BLOCK -->
  {CONTEXT_BLOCK}
  <!-- END CONTEXT-INJECTION -->
  
  <p><strong>Aufgabe:</strong> Erstelle einen konkreten 90-Tage-Plan für {{HAUPTLEISTUNG}} 
  als {{UNTERNEHMENSGROESSE_LABEL}} in der Branche {{BRANCHE_LABEL}}.</p>
  
  <p><strong>Der Plan muss:</strong></p>
  <ol class="requirements small">
    <li><strong>Spezifisch sein:</strong> Keine generischen Phasen wie "Analyse", "Konzeption", sondern konkrete Deliverables</li>
    <li><strong>Auf Hauptleistung fokussieren:</strong> Wie wird "{{HAUPTLEISTUNG}}" in 90 Tagen verbessert?</li>
    <li><strong>Größe berücksichtigen:</strong> Realistische Meilensteine für {{UNTERNEHMENSGROESSE_LABEL}} (siehe verbotene Empfehlungen oben)</li>
    <li><strong>Budget-konform sein:</strong> Innerhalb der Budget-Grenzen aus dem Context oben</li>
    <li><strong>Messbar sein:</strong> Jeder Meilenstein braucht klare Erfolgskriterien</li>
  </ol>
  
  <p><strong>Format (6 Meilensteine à 2 Wochen):</strong></p>
  <div class="timeline">
    <div class="milestone">
      <h4>Woche 1-2: [Konkreter Meilenstein-Titel]</h4>
      <p><strong>Ziel:</strong> [Spezifisches, messbares Ziel für {{HAUPTLEISTUNG}}]</p>
      <p><strong>Erwartetes Ergebnis:</strong> [Konkretes Deliverable, kein "Konzept"]</p>
      <p><strong>Verantwortliche Rollen:</strong> [Realistische Rollen für {{UNTERNEHMENSGROESSE_LABEL}}]</p>
      <p><strong>Benötigte Ressourcen:</strong> [Budget-konforme Tools/Services]</p>
    </div>
    
    <!-- 5 weitere Meilensteine nach gleichem Format -->
  </div>
  
  <p class="note small muted">
    <strong>Hinweis:</strong> Dieser Plan dient als Leitfaden und sollte je nach Projektfortschritt angepasst werden.
    Die Meilensteine berücksichtigen die typischen Workflows und Constraints der Branche {{BRANCHE_LABEL}}
    für Unternehmen der Größe {{UNTERNEHMENSGROESSE_LABEL}}.
  </p>
</section>
