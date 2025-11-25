<!-- foerderprogramme.md – Förderprogramme (DE) – v2.2
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     VARIABLEN:
     - {{BRANCHE_LABEL}}
     - {{UNTERNEHMENSGROESSE_LABEL}}
     - {{BUNDESLAND_LABEL}}
     - {{HAUPTLEISTUNG}}
     - {{FUNDING_TABLE_HTML}}: vorgefilterte Programme aus Research/Fördermatrix.

     REGELN:
     - Gib nur die Programme aus {{FUNDING_TABLE_HTML}} wieder; keine eigenen Programme erfinden.
     - Betone zuerst Programme aus {{BUNDESLAND_LABEL}}, danach Bund/EU.
     - Ein Satz Kontext, warum diese Programme zu {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}
       und {{HAUPTLEISTUNG}} passen.
-->

<section class="section funding">
  <h2>Förderprogramme</h2>

  <p>
    Für Unternehmen aus der Branche <strong>{{BRANCHE_LABEL}}</strong> in 
    <strong>{{BUNDESLAND_LABEL}}</strong> und der Größe 
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> gibt es mehrere Programme, 
    die KI‑ und Digitalisierungsprojekte im Umfeld von 
    <strong>{{HAUPTLEISTUNG}}</strong> unterstützen können.
  </p>

  <p>
    Die folgende Tabelle fasst ausgewählte Programme aus 
    <strong>{{BUNDESLAND_LABEL}}</strong>, vom Bund und – sofern relevant – 
    von der EU zusammen. Sie basiert auf einer aktuellen Recherche in einer 
    Fördermatrix 2025/2026 und ist bereits auf dein Vorhaben vorgefiltert.
  </p>

  {{FUNDING_TABLE_HTML}}

  <p class="small muted">
    Hinweis: Alle Angaben ohne Gewähr. Prüfe vor einer Antragstellung jeweils die
    aktuellen Konditionen, Fristen und Förderbedingungen auf den verlinkten 
    Programmseiten. Ob und in welcher Höhe eine Förderung bewilligt wird, hängt 
    immer von der konkreten Projektbeschreibung und der Entscheidung der Förderstellen ab.
  </p>
</section>
