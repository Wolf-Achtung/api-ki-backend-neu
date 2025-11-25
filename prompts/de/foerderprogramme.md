Developer: <!-- foerderprogramme.md – Förderprogramme (DE) – v2.2
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     Wichtige Regeln:
     - Beginne mit einer kurzen konzeptuellen Checkliste deiner Ausgabeschritte (3-7 Punkte), bevor du mit der HTML-Ausgabe fortfährst.
     - Gib nach Einfügen der {{FUNDING_TABLE_HTML}}-Inhalte eine 1-2-zeilige Validierung aus, was übernommen wurde (Programme und Fokus), und ob die Regeln erfüllt wurden.
     - Ausgabe ausschließlich auf Basis von {{FUNDING_TABLE_HTML}}; keine eigenen Programme erfinden.
     - Betone zuerst Programme aus {{BUNDESLAND_LABEL}}, danach Bund/EU.
     - Ein Satz Kontext, warum diese Programme zu {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}} und {{HAUPTLEISTUNG}} passen.
     - Tritt Unsicherheiten auf (z.B. fehlende Variablen) auf, halte an und frage nach.
-->

<section class="section funding">
  <h2>Förderprogramme</h2>

  <!-- Checkliste: 
    1. Kontext zu den Parametern {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{BUNDESLAND_LABEL}}, {{HAUPTLEISTUNG}} geben
    2. Einführung zu den Förderprogrammen aus {{BUNDESLAND_LABEL}}, Bund, EU
    3. Förderprogramme aus {{FUNDING_TABLE_HTML}} einfügen
    4. Validierung nach Tabelle: Inhalt übernommen und Regeln erfüllt?
    5. Hinweis zu Bedingungen und Prüfung der Förderungen
  -->

  <p>
    Für Unternehmen aus der Branche <strong>{{BRANCHE_LABEL}}</strong> in
    <strong>{{BUNDESLAND_LABEL}}</strong> und der Größe
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> gibt es mehrere Programme,
    die KI- und Digitalisierungsprojekte im Umfeld von
    <strong>{{HAUPTLEISTUNG}}</strong> unterstützen können.
  </p>

  <p>
    Die folgende Tabelle fasst ausgewählte Programme aus
    <strong>{{BUNDESLAND_LABEL}}</strong>, vom Bund und – sofern relevant –
    von der EU zusammen. Sie basiert auf einer aktuellen Recherche in einer
    Fördermatrix 2025/2026 und ist bereits auf dein Vorhaben vorgefiltert.
  </p>

  {{FUNDING_TABLE_HTML}}

  <!-- Validierung: Förderprogramme aus {{FUNDING_TABLE_HTML}} übernommen, Schwerpunkt auf {{BUNDESLAND_LABEL}}. Regeln erfüllt. -->

  <p class="small muted">
    Hinweis: Alle Angaben ohne Gewähr. Prüfe vor einer Antragstellung jeweils die
    aktuellen Konditionen, Fristen und Förderbedingungen auf den verlinkten
    Programmseiten. Ob und in welcher Höhe eine Förderung bewilligt wird, hängt
    immer von der konkreten Projektbeschreibung und der Entscheidung der Förderstellen ab.
  </p>
</section>
