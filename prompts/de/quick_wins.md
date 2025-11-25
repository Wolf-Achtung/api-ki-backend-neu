Developer: <!-- quick_wins.md – v4.1 GOLD STANDARD+ (size-aware, branch-aware, placeholder-safe)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     KONTEXT:
     - {{HAUPTLEISTUNG}} beschreibt den zentralen Leistungsprozess.
     - {{BRANCHE_LABEL}} beschreibt die Branche des Unternehmens.
     - {{UNTERNEHMENSGROESSE_LABEL}} beschreibt die Unternehmensgröße (z. B. Solo, kleines Team, KMU).

     Beginne mit einer knappen konzeptuellen Checkliste (3–7 Bullet-Points), was du tun wirst; halte die Punkte auf konzeptioneller Ebene.

     REGELN:
     - Gib 3–5 konkrete Quick Wins aus.
     - Jeder Quick Win muss direkt auf {{HAUPTLEISTUNG}} und die Realität von {{UNTERNEHMENSGROESSE_LABEL}} in {{BRANCHE_LABEL}} passen.
     - KEINE Meta-Instruktionen wie „Schritt 1 – beschreibe …“ oder „definiere ein Prüfverfahren“.
       Formuliere die Schritte direkt inhaltlich.
     - Nutze nur Informationen aus dem Kontext/Briefing. Keine frei erfundenen zusätzlichen Zahlen.

     - Falls mindestens eine der Variablen {{HAUPTLEISTUNG}}, {{BRANCHE_LABEL}} oder {{UNTERNEHMENSGROESSE_LABEL}} nicht übergeben oder leer ist, gib ein einzeiliges <p class="error">-Element mit folgender Meldung aus: "Fehlende oder leere Pflichtfelder: {{Namen_der_leeren_Variablen}}." und lass den restlichen Output weg.

     Nach der Generierung validiere in 1–2 Sätzen, ob alle Angaben den Regeln entsprechen; falls nicht, passe den Output minimal an.
-->

<section class="section quick-wins">
  <h2>Quick Wins – Sofort umsetzbare Schritte in {{HAUPTLEISTUNG}}</h2>
  <p>
    Die folgenden Quick Wins sind speziell auf <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in der Branche <strong>{{BRANCHE_LABEL}}</strong> zugeschnitten. Sie setzen direkt im Kernprozess <strong>{{HAUPTLEISTUNG}}</strong> an und lassen sich innerhalb weniger Tage umsetzen, ohne große Vorlaufzeit oder zusätzliche Personalkapazitäten.
  </p>
  <div class="quick-wins-grid">
    <!-- STRUCTURE EXAMPLE (Contents to be individuell generiert durch das Modell):
         Für jeden Quick Win verwende ein <article class="quick-win"> mit:
         <article class="quick-win">
           <h3>Quick Win X – Titel</h3>
           <p><strong>Worum geht es?</strong> Kurzbeschreibung der Aufgabe/Situation im Kontext von {{HAUPTLEISTUNG}}.</p>
           <p><strong>Konkrete Schritte:</strong></p>
           <ol>
             <li>Erster konkreter Schritt, den das Unternehmen sofort umsetzen kann.</li>
             <li>Zweiter Schritt, der den neuen KI-Workflow stabilisiert.</li>
             <li>Dritter Schritt, der die Nutzung im Alltag verankert (Checklisten, Templates etc.).</li>
           </ol>
           <p><strong>Nutzen:</strong> Qualitative Effekte + grobe Größenordnung der Zeitersparnis (z. B. „mehrere Stunden pro Monat“), ohne neue Zahlen zu erfinden.</p>
           <p class="small muted">Hinweis: Schritte so formulieren, dass sie für {{UNTERNEHMENSGROESSE_LABEL}} realistisch in kurzer Zeit machbar sind.</p>
         </article>
         Keine Meta-Kommentare oder Platzhaltertexte im Output – nur fertige Quick Wins.
    -->
  </div>
</section>

<!-- Output Format: 
     - Nur valides HTML ohne <html>, <head> oder <body>.
     - Keine Markdown-Fences.
-->

<!-- Variable Handling:
     - Pflichtvariablen: {{HAUPTLEISTUNG}}, {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}} müssen übergeben und nicht leer sein.
     - Fehlen eine oder mehrere Variablen oder sind sie leer, nur:
       <p class="error">Fehlende oder leere Pflichtfelder: {{Namen_der_leeren_Variablen}}.</p>
     - Sonst: Genau 3–5 <article class="quick-win">-Elemente, jeweils strukturiert:
         <article class="quick-win">
           <h3>Quick Win X – Titel</h3>
           <p><strong>Worum geht es?</strong> Kurzbeschreibung der Aufgabe/Situation im Kontext von {{HAUPTLEISTUNG}}.</p>
           <p><strong>Konkrete Schritte:</strong></p>
           <ol>
             <li>Erster konkreter Schritt, den das Unternehmen sofort umsetzen kann.</li>
             <li>Zweiter Schritt, der den neuen KI-Workflow stabilisiert.</li>
             <li>Dritter Schritt, der die Nutzung im Alltag verankert (Checklisten, Templates etc.).</li>
           </ol>
           <p><strong>Nutzen:</strong> Qualitative Effekte + grobe Größenordnung der Zeitersparnis (z. B. „mehrere Stunden pro Monat“), ohne neue Zahlen zu erfinden.</p>
           <p class="small muted">Hinweis: Schritte so formulieren, dass sie für {{UNTERNEHMENSGROESSE_LABEL}} realistisch in kurzer Zeit machbar sind.</p>
         </article>
     - Reihenfolge der Quick Wins ist beliebig, solange Struktur und Kontextbezug stimmen.
     - Platzhalter werden textuell wie {{HAUPTLEISTUNG}} eingesetzt.
     - Niemals leere Felder im HTML zurückgeben.
-->
