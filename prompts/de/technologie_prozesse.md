**WICHTIG – Längenlimit: Deine Antwort darf maximal 1100 Wörter umfassen. Kürze lieber als zu überziehen.**

<!-- PLATIN++ PROMPT v5.4 - SPRINT G6 -->
<!-- SECTION: technologie_prozesse -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!--
ZIEL: Präzise Technologie & Prozesse Übersicht.

MINDESTLÄNGE (STRIKT!):
- Solo: ≥180 Wörter
- Team: ≥210 Wörter
- KMU: ≥240 Wörter

STRUKTUR (4 Abschnitte):
1. Kurze Einleitung (2 Sätze, kein generischer Meta-Text!)
2. Systemarchitektur (Tabelle: 5 Layer mit Funktion)
3. Datenflüsse & Integrationen (Hauptprozess + size-aware Details)
4. Qualitätssicherung (3-4 Punkte)

{% if COMPANY_SIZE == "team" or COMPANY_SIZE == "kmu" %}
Für Team/KMU zusätzlich:
- Betriebsmodell/Support (1 Absatz)
- Ausblick: Cloud, EU-Hosting, Observability (kurz)
{% endif %}

ANTI-REDUNDANZ:
- Keine Tool-Liste (→ siehe KI-Stack)
- Fokus auf Prozessketten, nicht konkrete Tools
- Keine generischen Definitionen ("Eine Roadmap ist...")
-->

<section class="section technologie-prozesse">
  <h2>Technologie & Prozesse</h2>

  <p>
    Der Datenfluss vom Fragebogen bis zum fertigen PDF-Report basiert auf einer
    mehrschichtigen Architektur mit integrierter Qualitätssicherung.
  </p>

  <h3>Systemarchitektur</h3>
  <table class="table">
    <thead>
      <tr><th>Layer</th><th>Funktion</th></tr>
    </thead>
    <tbody>
      <tr><td>Frontend</td><td>Fragebogen-Erfassung, Validierung, Submit mit Autosave</td></tr>
      <tr><td>Backend</td><td>Prompt-Orchestrierung, Report-Builder, Business-Case-Berechnung</td></tr>
      <tr><td>KI/Analyse</td><td>Mehrschichtige Prompt-Analyse, Research-Integration, Branchen-Kontext</td></tr>
      <tr><td>PDF-Service</td><td>HTML→PDF Rendering, Layout-Optimierung, Branding</td></tr>
      <tr><td>Delivery</td><td>E-Mail-Versand, Archivierung, Nachverfolgung</td></tr>
    </tbody>
  </table>

  <h3>Datenfluss & Integrationen</h3>
  <ol>
    <li>Nutzer:in füllt Fragebogen aus (Autosave aktiv, Zwischenspeicherung)</li>
    <li>Submit → Validierung → Speicherung in sicherer Datenbank</li>
    <li>Prompt-Engine injiziert Branchen- und Größen-Kontext (size-aware)</li>
    <li>KI generiert Sektionen (Executive Summary, Roadmaps, Risiken, Business Case)</li>
    <li>Business-Case-Logik berechnet CAPEX/OPEX/ROI basierend auf Eingaben</li>
    <li>Validator prüft HTML-Qualität, Konsistenz und Persona-Compliance</li>
    <li>PDF-Service rendert finalen Report mit Corporate-Layout</li>
    <li>Versand per E-Mail mit Zustellbestätigung</li>
  </ol>

  <h3>Qualitätssicherung</h3>
  <ul>
    <li>Automatische Konsistenzprüfung aller Sektionen vor PDF-Erstellung</li>
    <li>Size-Mismatch-Detection: Solo/Team/KMU-spezifische Inhalte werden validiert</li>
    <li>Plausibilitätsprüfung der Business-Case-Zahlen (ROI, Payback, CAPEX)</li>
    <li>Platzhalter-Erkennung: Keine unvollständigen Inhalte im finalen Report</li>
  </ul>

  <h3>Betrieb & Erweiterung</h3>
  <p>
    Die Architektur ist für parallele Reportgenerierung ausgelegt. EU-Hosting gewährleistet
    DSGVO-Konformität. Monitoring überwacht Latenz und Fehlerquoten kontinuierlich.
  </p>

  <h3>Datensicherheit &amp; Compliance</h3>
  <p>
    {% if COMPANY_SIZE == "solo" %}
    DSGVO-konforme Tools mit EU-Hosting nutzen. Sensible Daten nur anonymisiert eingeben.
    {% elif COMPANY_SIZE == "team" %}
    Klare Regeln für Datentypen in KI-Tools. Zentraler Leitfaden für Rechtssicherheit.
    {% else %}
    KI-Richtlinien in Datenschutzprozesse integrieren. Regelmäßige Audits + Art.-30-Dokumentation.
    {% endif %}
  </p>

  <p class="small muted">
    Diese Architektur gewährleistet nachvollziehbare, qualitätsgesicherte Reports
    mit konsistenten Ergebnissen unabhängig von der Unternehmensgröße.
  </p>
</section>
