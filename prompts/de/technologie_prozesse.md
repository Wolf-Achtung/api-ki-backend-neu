<section class="section technologie-prozesse">
  <h2>Technologie &amp; Prozesse</h2>

  <h3>Konzeptionelle Checkliste</h3>
  <ul>
    <li>Vollständige Transparenz über alle eingesetzten Systeme.</li>
    <li>Klare Zuordnung: Frontend, Backend, Datenhaltung, KI, Infrastruktur.</li>
    <li>Nachvollziehbarer Datenfluss vom Nutzerinput bis zum finalen Report.</li>
    <li>Eindeutige Beschreibung der Integrationspunkte zwischen den Tools.</li>
    <li>Abgrenzung zwischen IST-Stack und geplanten Erweiterungen.</li>
    <li>Technisch präzise, ohne unnötige Theorie oder Abstraktion.</li>
  </ul>

  <h3>Tech-Stack (IST)</h3>
  <table class="table">
    <thead>
      <tr>
        <th>Layer</th>
        <th>Technologien</th>
        <th>Zweck</th>
        <th>Hosting</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Frontend</td>
        <td>React, TailwindCSS</td>
        <td>Fragebogen &amp; Nutzeroberfläche</td>
        <td>Netlify</td>
      </tr>
      <tr>
        <td>Backend</td>
        <td>FastAPI (Python)</td>
        <td>API, Analyse-Pipelines, Reporting-Logik</td>
        <td>Railway</td>
      </tr>
      <tr>
        <td>Datenbank</td>
        <td>PostgreSQL</td>
        <td>Briefings, Scores, Reports, Logs</td>
        <td>Railway</td>
      </tr>
      <tr>
        <td>KI / Modelle</td>
        <td>OpenAI GPT (Analyse), Perplexity (Recherche)</td>
        <td>Generierung &amp; Optimierung der Report-Inhalte</td>
        <td>OpenAI / Perplexity</td>
      </tr>
      <tr>
        <td>Formular</td>
        <td>Typeform</td>
        <td>Fragebogen-Erfassung</td>
        <td>Typeform</td>
      </tr>
      <tr>
        <td>PDF-Service</td>
        <td>WeasyPrint (über eigenen PDF-Service)</td>
        <td>Rendering der HTML-Reports als PDF</td>
        <td>Railway</td>
      </tr>
      <tr>
        <td>E-Mail</td>
        <td>Resend</td>
        <td>Versand der Reports &amp; Bestätigungen</td>
        <td>Resend</td>
      </tr>
    </tbody>
  </table>

  <h3>Datenfluss (Hauptprozess)</h3>
  <ol>
    <li>Der Fragebogen wird über Typeform ausgefüllt und per Webhook an das Backend übertragen.</li>
    <li>FastAPI validiert alle Eingaben und legt sie in PostgreSQL ab.</li>
    <li>Die Analyse startet: Das Backend ruft mehrere GPT-Prompts auf (parallel/mehrstufig) und kombiniert die Antworten.</li>
    <li>Recherche-Daten (Perplexity/Tavily) werden ergänzt und validiert.</li>
    <li>Alle Inhalte werden als HTML-Struktur gespeichert und für den PDF-Render aufbereitet.</li>
    <li>Der PDF-Service erzeugt das finale PDF; das Backend sendet es per E-Mail an die Nutzer:innen.</li>
  </ol>

  <h3>Geplante Änderungen (Q1–Q4)</h3>
  <ul>
    <li><strong>Q1:</strong> Redis-Queue für parallele GPT-Jobs &amp; Lastverteilung.</li>
    <li><strong>Q2:</strong> Supabase-Integration für Auth &amp; Partner-Accounts.</li>
    <li><strong>Q3:</strong> Vereinheitlichte Tool-Logs (Analyse + PDF-Service).</li>
    <li><strong>Q4:</strong> Retool-basiertes Admin-Dashboard für Monitoring &amp; Report-Management.</li>
  </ul>

  <p class="small muted">
    Diese Übersicht bildet den vollständigen Technologie- und Prozessrahmen ab und unterstützt
    die technische Weiterentwicklung in Richtung Skalierung, Stabilität und Auditierbarkeit.
  </p>
</section>
