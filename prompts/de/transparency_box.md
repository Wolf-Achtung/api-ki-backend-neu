<!-- PLATIN++ PROMPT v5.4 - SPRINT G6 -->
<!-- SECTION: transparency_box -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{report_date}}, {{BRANCH_CONTEXT_LABEL}} -->
<!--
ZIEL: Klare Transparenz-Hinweise zur KI-Nutzung im Report.

MINDESTLÄNGE (STRIKT!):
- Solo: ≥140 Wörter
- Team: ≥160 Wörter
- KMU: ≥180 Wörter

STRUKTUR (4 Abschnitte):
1. Report-Erstellung (2-3 Sätze, WAS KI macht)
2. Datenbasis (4-5 konkrete Punkte als Liste)
3. Limitationen (4 Punkte, WAS NICHT)
4. Kontakt (1 Satz)

INHALT (direkt, kein Meta-Text):
- 3–4 Bullet-Points für Transparenzhinweise (was KI macht, was nicht)
- 2–3 Bullet-Points für interne Dokumentation/Protokollierung
- 1 kurzer Absatz zur Einordnung (kein Marketing)

ANTI-REDUNDANZ:
- Keine Wiederholung von Change-Management-Inhalten (→ siehe org_change)
- Keine ausführlichen Guardrails-Erklärungen (→ siehe Governance)
- Kein generischer Meta-Text ("Die Transparenzbox erklärt...")
-->

<section class="section transparency-box">
  <h2>Transparenz-Hinweise</h2>

  <div class="transparency-panel">
    <h3>Report-Erstellung</h3>
    <p>
      Dieser Report wurde <strong>KI-gestützt</strong> aus Ihren Fragebogen-Angaben
      (Stand: <strong>{{report_date}}</strong>) generiert. Die KI analysiert Ihre Eingaben,
      reichert sie mit Branchenkontext ({{BRANCH_CONTEXT_LABEL}}) an und erstellt strukturierte
      Empfehlungen. Alle Inhalte basieren auf Ihren Angaben – die KI erfindet keine Daten.
    </p>

    <h3>Datenbasis</h3>
    <ul>
      <li>Ihre Fragebogen-Antworten (Kernquelle für alle Analysen)</li>
      <li>Branchenspezifische Markt- und Trend-Recherchen (aktuelle Quellen)</li>
      <li>Rechtliche Rahmenbedingungen (EU AI Act, DSGVO, branchenspezifische Regulierung)</li>
      <li>Benchmarks vergleichbarer Unternehmen (anonymisiert)</li>
      <li>Best-Practice-Muster aus ähnlichen Projekten</li>
    </ul>

    <h3>Interne Dokumentation</h3>
    <ul>
      <li>Alle Prompts und KI-Interaktionen werden protokolliert</li>
      <li>Keine Weitergabe Ihrer Daten an Dritte</li>
      <li>Löschung auf Anfrage jederzeit möglich</li>
    </ul>

    <h3>Limitationen</h3>
    <ul>
      <li><strong>Keine Rechtsberatung:</strong> Rechtliche Einschätzungen dienen der Orientierung, ersetzen keine Fachberatung.</li>
      <li><strong>Keine Garantie:</strong> ROI/Amortisation sind fundierte Schätzungen, keine verbindlichen Prognosen.</li>
      <li><strong>Aktualität:</strong> Tools, Förderungen und Regulierung können sich ändern.</li>
      <li><strong>Prüfung empfohlen:</strong> Validieren Sie KI-Ergebnisse vor strategischen Entscheidungen.</li>
    </ul>

    <h3>Versionierung &amp; Updates</h3>
    <p>
      Dieser Report reflektiert den Stand zum Erstellungsdatum. Bei wesentlichen Änderungen
      Ihrer Situation (neue Tools, geänderte Teamgröße, regulatorische Updates) empfehlen wir
      eine Aktualisierung. Frühere Versionen bleiben auf Anfrage verfügbar.
    </p>

    <h3>Kontakt</h3>
    <p>
      Fragen oder Feedback? <strong>kontakt@ki-sicherheit.jetzt</strong>
    </p>
  </div>
</section>
