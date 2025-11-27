Developer:
<!-- quick_wins.md – v3.0 GOLD STANDARD+ (size-aware, branch-aware, validator-safe)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     ZIEL:
       - Erzeuge 3–5 konkrete, sofort nutzbare Quick Wins.
       - Quick Wins müssen direkt auf {{HAUPTLEISTUNG}} passen und realistisch für
         {{UNTERNEHMENSGROESSE_LABEL}} in der Branche {{BRANCHE_LABEL}} sein.
       - Jeder Quick Win enthält: kurze Einordnung, 2–4 konkrete Schritte, klaren Nutzen.

     PFLICHTVARIABLEN:
       - {{HAUPTLEISTUNG}}, {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}
       - Falls eine dieser Variablen fehlt oder leer ist:
           Gib NUR folgendes aus:
           <p class="error">Fehlende oder leere Pflichtfelder: {{Namen_der_leeren_Variablen}}.</p>
           KEINEN weiteren Output.

     SIZE-AWARE-LOGIK (über COMPANY_SIZE ∈ {"solo","team","kmu"}):
       SOLO:
         - Fokus: persönliche Entlastung, sehr einfache Maßnahmen.
         - Keine Teams/Abteilungen im Wording.
       TEAM (2–10):
         - Fokus: arbeitsteilige Umsetzung, kurze Abstimmungen.
         - Rollen: Teamlead, KI-Owner, Kolleg:innen.
       KMU (11–100):
         - Fokus: koordinierte, skalierbare Quick Wins über Bereiche hinweg.
         - Rollen: verantwortliche Fachbereiche, Prozessverantwortliche.

     AUSGABESTIL:
       - Klar verständlich, ohne Metatexte.
       - Keine Platzhalterwörter („Platzhalter“, „TODO“, „Freitextfeld“ etc.).
       - 3–7 kurze konzeptionelle „Was mache ich?“–Bullet Points zu Beginn.
       - Danach genau 3–5 <article class="quick-win"> Elemente.

     STRUKTUR EINES QUICK WINS:
       <article class="quick-win">
         <h3>Quick Win X – Titel</h3>
         <p><strong>Worum geht es?</strong> Kontext in {{HAUPTLEISTUNG}}.</p>
         <p><strong>Konkrete Schritte:</strong></p>
         <ol>
           <li>Schritt 1 …</li>
           <li>Schritt 2 …</li>
           <li>Schritt 3 …</li>
         </ol>
         <p><strong>Nutzen:</strong> Qualitative Effekte + Zeitgewinn ohne neue Zahlen.</p>
         <p class="small muted">Hinweis: Schritte an {{UNTERNEHMENSGROESSE_LABEL}} angepasst.</p>
       </article>

     VALIDATION AM ENDE:
       - Antworte nach der Generierung in 1–2 Sätzen, ob alle Regeln eingehalten wurden.
       - Falls nicht, minimal korrigieren.
-->

<section class="section quick-wins">
  <h2>Quick Wins – Sofort umsetzbare Schritte in {{HAUPTLEISTUNG}}</h2>

  <p>
    Die folgenden Quick Wins sind speziell auf <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> 
    in der Branche <strong>{{BRANCHE_LABEL}}</strong> zugeschnitten. Sie setzen direkt 
    im Kernprozess <strong>{{HAUPTLEISTUNG}}</strong> an und lassen sich innerhalb weniger Tage 
    umsetzen – ohne große Vorlaufzeit oder zusätzliche Ressourcen.
  </p>

  <!-- Konzeptuelle Checkliste (3–7 Bullet Points) -->
  <ul class="conceptual-checklist">
    <li>Fokussiere auf wiederkehrende Schritte in {{HAUPTLEISTUNG}}.</li>
    <li>Nutze Beispiele und Daten, die bereits im Alltag vorhanden sind.</li>
    <li>Standardisiere Ein- und Ausgangspunkte für KI-Assistenz.</li>
    <li>Etabliere kleine, realistische Routinen – abgestimmt auf {{UNTERNEHMENSGROESSE_LABEL}}.</li>
    <li>Verbessere Kundenergebnisse durch klare Formulierungen und konsistente Qualität.</li>
  </ul>

  <div class="quick-wins-grid">
    <!-- Das Modell generiert hier 3–5 voll ausgeformte <article class="quick-win">-Elemente -->
  </div>
</section>
