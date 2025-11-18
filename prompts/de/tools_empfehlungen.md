<!-- Tools Empfehlungen (DE) - ENHANCED mit Context-System v2.0 -->
<!-- Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown‑Fences.
     Nutze die Platzhalter:
     - {BRANCHE_LABEL}, {UNTERNEHMENSGROESSE_LABEL}, {BUNDESLAND_LABEL}, {HAUPTLEISTUNG}
     - {report_date}, {report_year}, {kundencode}, {report_id}
     Schreibe präzise, fachlich, motivierend – kein Marketing‑Sprech. -->

<section class="section tools-empfehlungen">
  <h2>Empfohlene KI‑Tools &amp; Software</h2>
  
  <!-- CONTEXT-INJECTION BLOCK -->
  {CONTEXT_BLOCK}
  <!-- END CONTEXT-INJECTION -->
  
  <p>Die folgende Tabelle stellt ausgewählte KI‑Tools vor, die {{BRANCHE_LABEL}} als {{UNTERNEHMENSGROESSE_LABEL}} 
  im Bundesland {{BUNDESLAND_LABEL}} bei der Optimierung von "{{HAUPTLEISTUNG}}" unterstützen können.</p>
  
  <p><strong>Tool-Auswahl-Kriterien:</strong></p>
  <ul class="criteria small">
    <li><strong>Branchen-Fit:</strong> Passt zu typischen Tools der Branche (siehe Context oben)</li>
    <li><strong>Budget-konform:</strong> Innerhalb der Budget-Grenzen (siehe Context oben)</li>
    <li><strong>Quick Wins-relevant:</strong> Setzt die Quick Wins um</li>
    <li><strong>Integration:</strong> Kompatibel mit vorhandenen Standard-Tools</li>
    <li><strong>DSGVO:</strong> EU-Hosting oder DSGVO-konform</li>
  </ul>
  
  <table class="table">
    <thead>
      <tr>
        <th style="width:15%;">Name</th>
        <th style="width:30%;">Beschreibung</th>
        <th style="width:20%;">Kernfunktion</th>
        <th style="width:20%;">Preismodell</th>
        <th style="width:15%;">DSGVO/Hinweis</th>
      </tr>
    </thead>
    <tbody>
      <!-- 
      WICHTIG: Empfehle 5-7 Tools die:
      1. Aus dem Context "Typische Tools" kompatibel sind
      2. Die Quick Wins umsetzen
      3. Budget-konform sind (siehe Context)
      4. NICHT aus der verbotenen Liste stammen
      
      Beispiel für {{BRANCHE_LABEL}} + {{UNTERNEHMENSGROESSE_LABEL}}:
      - GPT-4 API (wenn KI-Content relevant)
      - Make.com oder Zapier (wenn Automation relevant)
      - Fireflies.ai (wenn Meetings dokumentiert werden)
      - Notion AI (wenn Dokumentation wichtig ist)
      - etc.
      
      Format pro Zeile:
      -->
      <tr>
        <td><strong>[Tool-Name]</strong></td>
        <td>[Kurze Beschreibung, 1-2 Sätze, bezogen auf {{HAUPTLEISTUNG}}]</td>
        <td>[Kernfunktion für diese Branche]</td>
        <td>[Preis/Monat oder Pricing-Modell]</td>
        <td>[DSGVO-Status + relevante Hinweise]</td>
      </tr>
      <!-- 4-6 weitere Tools -->
    </tbody>
  </table>
  
  <p class="small muted">
    <strong>Hinweis:</strong> Diese Auswahl basiert auf öffentlich verfügbaren Informationen und 
    berücksichtigt die typischen Workflows der Branche {{BRANCHE_LABEL}} sowie die Budget-Constraints 
    für {{UNTERNEHMENSGROESSE_LABEL}}. Die Liste stellt keine Rechtsberatung dar.
  </p>
</section>
