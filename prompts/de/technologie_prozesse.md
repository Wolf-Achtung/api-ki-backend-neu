<section class="section technologie-prozesse">
  <h2>Technologie &amp; Prozesse</h2>

  <h3>Konzeptionelle Checkliste</h3>
  <ul>
    <li>Vollständige Transparenz über alle eingesetzten Systeme – Frontend, Backend, KI, Datenhaltung.</li>
    <li>Klare Zuordnung der Verantwortlichkeiten je Layer.</li>
    <li>Nachvollziehbarer Datenfluss vom Nutzerinput bis zum finalen PDF-Report.</li>
    <li>Eindeutige technische Integrationspunkte zwischen Frontend, Backend, KI und PDF-Service.</li>
    <li>Abgrenzung zwischen IST-Stack und geplanten Erweiterungen.</li>
    <li>Technisch präzise, auditfähig und ohne unnötige Abstraktion.</li>
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
        <td>Interaktiver KI-Readiness-Fragebogen, UI-Logik, Autosave, Submit-Flow</td>
        <td>Netlify</td>
      </tr>
      <tr>
        <td>Backend</td>
        <td>FastAPI (Python)</td>
        <td>
          Annahme & Validierung der Formulardaten, Prompt-Orchestrierung (mehrschichtig),
          Report-Builder, Business-Case-Berechnungen, Research-Einbindung, Validator & Replacer.
        </td>
        <td>Railway</td>
      </tr>
      <tr>
        <td>Datenbank</td>
        <td>PostgreSQL</td>
        <td>Briefings, Nutzerprofile, Scores, Reports, Systemlogs</td>
        <td>Railway</td>
      </tr>
      <tr>
        <td>KI / Modelle</td>
        <td>OpenAI GPT-4.1 / GPT-5.x, Perplexity, Tavily</td>
        <td>
          Mehrstufige Prompt-Analyse, Research-Snippets, Branchenkontext,
          Size-Aware-Logik, Validierung der Inhalte.
        </td>
        <td>OpenAI / Perplexity / Tavily API</td>
      </tr>
      <tr>
        <td>Formular</td>
        <td>Eigener React-Formbuilder (Frontend + Backend-Submit)</td>
        <td>
          Erfassung aller Eingaben; dynamische Validierung; Multi-Page-Wizard;
          Webhook-freie, direkte API-Kommunikation.
        </td>
        <td>Netlify / Railway</td>
      </tr>
      <tr>
        <td>PDF-Service</td>
        <td>WeasyPrint (dedizierter Render-Worker)</td>
        <td>Rendering der HTML-Reports als PDF (A4, Corporate Layout)</td>
        <td>Railway</td>
      </tr>
      <tr>
        <td>E-Mail</td>
        <td>Resend API</td>
        <td>Versand der fertigen Reports, Login-Codes, interne Systemmeldungen</td>
        <td>Resend</td>
      </tr>
    </tbody>
  </table>

  <h3>Datenfluss (Hauptprozess)</h3>
  <ol>
    <li>Nutzer:innen füllen den webbasierten Formbuilder aus (React-Frontend mit Autosave).</li>
    <li>Der Submit sendet die Daten per HTTPS an FastAPI; Validierung & Speicherung in PostgreSQL.</li>
    <li>
      FastAPI startet die Analyse:
      <ul>
        <li>PromptEnhancer injiziert Branchen- und Size-Kontext (CONTEXT_BLOCK).</li>
        <li>Mehrschichtige GPT-Prompts erzeugen Executive Summary, Roadmaps, Risiken, Empfehlungen usw.</li>
        <li>Research-Pipeline ruft Perplexity/Tavily ab und integriert die Snippets kontrolliert.</li>
      </ul>
    </li>
    <li>Business-Case-Logik berechnet CAPEX/OPEX/ROI basierend auf Eingaben.</li>
    <li>Report-Validator prüft HTML-Qualität, Size-Mismatch, verbotene Tokens & Konsistenz.</li>
    <li>Der finale HTML-Report wird an den dedizierten PDF-Service übergeben.</li>
    <li>WeasyPrint rendert das PDF; FastAPI sendet es via Resend per E-Mail an die Nutzer:innen.</li>
  </ol>

  <h3>Geplante Änderungen (Q1–Q4)</h3>
  <ul>
    <li>
      <strong>Q1:</strong> Einführung einer Redis-Queue für parallele GPT-Jobs,
      Stabilisierung von Bulk-Generierungen und Timeouts.
    </li>
    <li>
      <strong>Q2:</strong> Integration einer Supabase-basierten Auth für Partnerzugänge
      (z. B. Berater:innen, Reseller, White-Label-Instanzen).
    </li>
    <li>
      <strong>Q3:</strong> Vereinheitlichte Systemlogs (Analyse, PDF-Service, Research)
      zur besseren Auditierbarkeit und Fehlersuche.
    </li>
    <li>
      <strong>Q4:</strong> Retool-basiertes Admin-Dashboard für Monitoring,
      Report-Management, Rechnungsläufe und Audit-Exports.
    </li>
  </ul>

  <p class="small muted">
    Diese Übersicht bildet den vollständigen Technologie- und Prozessrahmen ab und
    unterstützt die technische Weiterentwicklung in Richtung Skalierbarkeit,
    Stabilität und Auditierbarkeit.
  </p>
</section>
