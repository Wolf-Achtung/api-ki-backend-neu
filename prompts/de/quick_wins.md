<!-- quick_wins.md – v4.1 GOLD STANDARD+ (size-aware, branchen-aware, placeholder-sicher)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     KONTEXT:
     - {{HAUPTLEISTUNG}} beschreibt den zentralen Leistungsprozess.
     - {{BRANCHE_LABEL}} beschreibt die Branche des Unternehmens.
     - {{UNTERNEHMENSGROESSE_LABEL}} beschreibt die Unternehmensgröße (z. B. Solo, kleines Team, KMU).

     REGELN:
     - Gib 3–5 konkrete Quick Wins aus.
     - Jeder Quick Win muss direkt auf {{HAUPTLEISTUNG}} und die Realität von {{UNTERNEHMENSGROESSE_LABEL}}
       in {{BRANCHE_LABEL}} passen.
     - KEINE Meta-Instruktionen wie „Schritt 1 – beschreibe …“ oder „definiere ein Prüfverfahren“.
       Formuliere die Schritte direkt inhaltlich.
     - Nutze nur Informationen aus dem Kontext/Briefing. Keine frei erfundenen zusätzlichen Zahlen.
-->

<section class="section quick-wins">
  <h2>Quick Wins – Sofort umsetzbare Schritte in {{HAUPTLEISTUNG}}</h2>

  <p>
    Die folgenden Quick Wins sind speziell auf 
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in der Branche 
    <strong>{{BRANCHE_LABEL}}</strong> zugeschnitten. Sie setzen direkt im Kernprozess 
    <strong>{{HAUPTLEISTUNG}}</strong> an und lassen sich innerhalb weniger Tage umsetzen,
    ohne große Vorlaufzeit oder zusätzliche Personalkapazitäten.
  </p>

  <div class="quick-wins-grid">
    <!-- ERWARTETE STRUKTUR (Beispiel – Inhalte müssen vom Modell individuell formuliert werden):
         Für jeden Quick Win ein <article class="quick-win"> mit:

         <article class="quick-win">
           <h3>Quick Win X – Titel</h3>
           <p><strong>Worum geht es?</strong> Kurzbeschreibung der Aufgabe/Situation im Kontext von {{HAUPTLEISTUNG}}.</p>
           <p><strong>Konkrete Schritte:</strong></p>
           <ol>
             <li>Erster konkreter Schritt, den das Unternehmen sofort umsetzen kann.</li>
             <li>Zweiter Schritt, der den neuen KI-Workflow stabilisiert.</li>
             <li>Dritter Schritt, der die Nutzung im Alltag verankert (Checklisten, Templates etc.).</li>
           </ol>
           <p><strong>Nutzen:</strong> Qualitative Effekte + grobe Größenordnung der Zeitersparnis
              (z.&nbsp;B. „mehrere Stunden pro Monat“) ohne neue Zahlen zu erfinden.</p>
           <p class="small muted">Hinweis: Schritte so formulieren, dass sie für {{UNTERNEHMENSGROESSE_LABEL}}
              realistisch in kurzer Zeit machbar sind.</p>
         </article>

         Gib im Output keine Meta-Kommentare oder Platzhaltertexte aus, sondern direkt fertige Quick-Wins.
    -->
  </div>
</section>
