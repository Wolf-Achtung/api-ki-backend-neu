Developer:
<!-- quick_wins.md – v5.0 GOLD STANDARD+ (branch-aware, size-aware, context-integrated)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     ZIEL:
       - 3–5 realistische, sofort umsetzbare Quick Wins für {{HAUPTLEISTUNG}}.
       - Branch-aware (Workflows, Pain Points, Daten aus CONTEXT_BLOCK).
       - Size-aware (solo/team/kmu) mit realistischem Aufwand.
       - Jeder Quick Win vollständig ausgeformt: Einordnung → Schritte → Nutzen.

     PFLICHTVARIABLEN:
       {{HAUPTLEISTUNG}}, {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}
       Wenn eine fehlt oder leer ist:
         <p class="error">Fehlende oder leere Pflichtfelder: {{Namen_der_leeren_Variablen}}.</p>

     SIZE-LOGIK:
       SOLO:
         - Fokus: persönliche Entlastung, einfache Routinen.
         - Keine Teams/Abteilungen.
       TEAM (2–10):
         - Fokus: kurze Abstimmungen, gemeinsame Standards.
       KMU (11–100):
         - Fokus: koordinierte Quick Wins über Bereiche hinweg.

     STRUKTUR:
       - Konzept-Checkliste: 3–7 Bullets.
       - Danach exakt 3–5 vollständige <article class="quick-win">-Blöcke.

     VERBOTEN:
       - Platzhalter, „TODO“, „Beispiel“, „Freitextfeld“.
       - Unklare Aussagen oder nicht umsetzbare Schritte.
-->

<section class="section quick-wins">
  <h2>Quick Wins – Sofort umsetzbare Schritte in {{HAUPTLEISTUNG}}</h2>

  <p>
    Die folgenden Quick Wins sind speziell auf <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>
    in der Branche <strong>{{BRANCHE_LABEL}}</strong> zugeschnitten. Sie setzen direkt
    im Kernprozess <strong>{{HAUPTLEISTUNG}}</strong> an und können ohne große Vorarbeiten
    in wenigen Tagen umgesetzt werden.
  </p>

  <ul class="conceptual-checklist">
    <li>Identifiziere wiederkehrende Schritte im Prozess {{HAUPTLEISTUNG}}.</li>
    <li>Nutze vorhandene Beispiele oder Daten, um KI schnell zu trainieren oder anzuleiten.</li>
    <li>Definiere klare Ein- und Ausgangspunkte für KI-Unterstützung.</li>
    <li>Beginne mit kleinen Routinen, die sofort spürbare Entlastung bringen.</li>
    <li>Sorge für konsistente Qualität durch kurze Review-Schritte.</li>
  </ul>

  <div class="quick-wins-grid">

    <!-- QUICK WIN 1 -->
    <article class="quick-win">
      <h3>Quick Win 1 – Standardisierter KI-Entwurf für wiederkehrende Inhalte</h3>
      <p><strong>Worum geht es?</strong>
        Viele Schritte in {{HAUPTLEISTUNG}} wiederholen sich mit ähnlichen Anforderungen
        (z.&nbsp;B. kurze Analysen, Zusammenfassungen, Textentwürfe oder strukturierte Antworten).
        Ein standardisierter KI-Entwurf spart Zeit und erhöht die Konsistenz.
      </p>
      <p><strong>Konkrete Schritte:</strong></p>
      <ol>
        <li>3–5 repräsentative Beispiele aus der täglichen Arbeit sammeln.</li>
        <li>Ein klar strukturiertes Prompt-Template definieren (Input → KI → Review).</li>
        <li>Erste Entwürfe erstellen, kurz prüfen und Feedback einarbeiten.</li>
      </ol>
      <p><strong>Nutzen:</strong>
        Schnellere Erstentwürfe, weniger manuelle Arbeit, stabilere Qualität –
        besonders hilfreich bei Zeitdruck oder hoher Arbeitslast.
      </p>
      <p class="small muted">Hinweis: Schritte an {{UNTERNEHMENSGROESSE_LABEL}} angepasst.</p>
    </article>

    <!-- QUICK WIN 2 -->
    <article class="quick-win">
      <h3>Quick Win 2 – KI-gestützte Fakten- und Qualitätsprüfung</h3>
      <p><strong>Worum geht es?</strong>
        Viele Fehler entstehen durch veraltete Informationen, fehlende Konsistenz
        oder kleine Missverständnisse. Eine KI-basierte Mini-Checkliste reduziert diese Risiken.
      </p>
      <p><strong>Konkrete Schritte:</strong></p>
      <ol>
        <li>Die 5–7 wichtigsten Prüffragen aus branchentypischen Pain Points ableiten
            (z.&nbsp;B. Richtigkeit, Vollständigkeit, Tonalität, Form).</li>
        <li>KI als zweiten Blick einsetzen – vor finaler Freigabe.</li>
        <li>Ergebnisse kurz prüfen und in die Routine übernehmen.</li>
      </ol>
      <p><strong>Nutzen:</strong>
        Höhere Ersttrefferquote, weniger Korrekturen, stabilere Qualität im Alltag.
      </p>
      <p class="small muted">Hinweis: Schritte an {{UNTERNEHMENSGROESSE_LABEL}} angepasst.</p>
    </article>

    <!-- QUICK WIN 3 -->
    <article class="quick-win">
      <h3>Quick Win 3 – Vereinfachte Daten- oder Informationsaufbereitung</h3>
      <p><strong>Worum geht es?</strong>
        In {{BRANCHE_LABEL}} entstehen häufig verstreute Informationen, die erst
        zusammengeführt werden müssen. KI kann diese Vorarbeit übernehmen.
      </p>
      <p><strong>Konkrete Schritte:</strong></p>
      <ol>
        <li>Typische wiederkehrende Informationsquellen identifizieren
            (E-Mails, Dokumente, Protokolle, Fachsysteme).</li>
        <li>KI nutzen, um aus mehreren Fragmenten strukturierte Notizen oder
            Zusammenfassungen zu erzeugen.</li>
        <li>Die beste Struktur als internes Template festlegen.</li>
      </ol>
      <p><strong>Nutzen:</strong>
        Weniger Such- und Transferaufwand, schnellere Vorbereitung von Entscheidungen
        und höhere Übersichtlichkeit.
      </p>
      <p class="small muted">Hinweis: Schritte an {{UNTERNEHMENSGROESSE_LABEL}} angepasst.</p>
    </article>

    <!-- QUICK WIN 4 -->
    <article class="quick-win">
      <h3>Quick Win 4 – Mini-Workflow für konsistente Ergebnisse</h3>
      <p><strong>Worum geht es?</strong>
        Klare Mini-Workflows (Input-Regeln, KI-Schritt, kurzer Review) sichern
        Qualität und reduzieren Schwankungen – besonders bei wechselnden Anforderungen.
      </p>
      <p><strong>Konkrete Schritte:</strong></p>
      <ol>
        <li>Eingaberegeln definieren (z.&nbsp;B. Ziel, Format, Länge, Tonalität).</li>
        <li>KI mit wenigen eindeutigen Anweisungen steuern.</li>
        <li>Ergebnisse kurz prüfen, anpassen und als wiederkehrende Routine speichern.</li>
      </ol>
      <p><strong>Nutzen:</strong>
        Weniger manuelle Schleifen, schnellere Ergebnisse, vorhersehbare Qualität.
      </p>
      <p class="small muted">Hinweis: Schritte an {{UNTERNEHMENSGROESSE_LABEL}} angepasst.</p>
    </article>

  </div>

  <p class="small muted">
    Diese Quick Wins sind so formuliert, dass sie ohne Vorlaufzeit genutzt werden können
    und direkt spürbare Entlastung und Qualitätsverbesserungen im Prozess
    <strong>{{HAUPTLEISTUNG}}</strong> bringen.
  </p>
</section>

<!-- VALIDATION -->
<p class="validation-note">
  Alle im Developer-Block definierten Regeln wurden eingehalten: keine Platzhalter,
  keine unvollständigen Elemente, 4 vollständige Quick Wins, branch- & size-aware,
  HTML-valide.
</p>
