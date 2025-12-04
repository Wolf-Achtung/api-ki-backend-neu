<!-- technologie_prozesse.md – v2.0 PDF-SLIMDOWN-STRICT
     Antworte ausschließlich mit validem HTML.

     **STRIKTE TOKEN-BEGRENZUNG:**
     MAXIMAL 300-400 Wörter Output.

     **STRUKTUR (kompakt):**
     1. Kurze Einleitung (2 Sätze)
     2. Prozessketten-Fokus (Haupt-Datenfluss)
     3. Kurze Tabelle: 4-5 Layer mit Zweck
     4. Geplante Änderungen (3-4 Punkte kurz)

     **Nicht verwenden:**
     - Keine Tool-Liste (kommt in tools_empfehlungen)
     - Fokus auf Prozessketten, nicht auf konkrete Tools
     - Keine redundanten Tech-Details
-->

<section class="section technologie-prozesse">
  <h2>Technologie & Prozesse</h2>

  <p>
    Diese Übersicht zeigt den Datenfluss vom Fragebogen bis zum fertigen PDF-Report.
    Der Fokus liegt auf den Prozessketten, nicht auf einzelnen Tools.
  </p>

  <h3>Systemarchitektur</h3>
  <table class="table">
    <thead>
      <tr><th>Layer</th><th>Funktion</th></tr>
    </thead>
    <tbody>
      <tr><td>Frontend</td><td>Fragebogen-Erfassung, Validierung, Submit</td></tr>
      <tr><td>Backend</td><td>Prompt-Orchestrierung, Report-Builder, Business-Case-Berechnung</td></tr>
      <tr><td>KI/Analyse</td><td>Mehrschichtige Prompt-Analyse, Research-Integration</td></tr>
      <tr><td>PDF-Service</td><td>HTML→PDF Rendering, Layout-Optimierung</td></tr>
      <tr><td>Delivery</td><td>E-Mail-Versand des fertigen Reports</td></tr>
    </tbody>
  </table>

  <h3>Datenfluss (Hauptprozess)</h3>
  <ol>
    <li>Nutzer:in füllt Fragebogen aus (Autosave aktiv)</li>
    <li>Submit → Validierung → Speicherung</li>
    <li>Prompt-Engine injiziert Branchen- und Größen-Kontext</li>
    <li>KI generiert Sektionen (Executive Summary, Roadmaps, Risiken, etc.)</li>
    <li>Business-Case-Logik berechnet CAPEX/OPEX/ROI</li>
    <li>Validator prüft HTML-Qualität und Konsistenz</li>
    <li>PDF-Service rendert finalen Report</li>
    <li>Versand per E-Mail</li>
  </ol>

  <h3>Qualitätssicherung</h3>
  <ul>
    <li>Automatische Konsistenzprüfung aller Sektionen</li>
    <li>Size-Mismatch-Detection (Solo/Team/KMU)</li>
    <li>Plausibilitätsprüfung der Business-Case-Zahlen</li>
  </ul>

  <p class="small muted">
    Diese Architektur gewährleistet nachvollziehbare, qualitätsgesicherte Reports.
  </p>
</section>
