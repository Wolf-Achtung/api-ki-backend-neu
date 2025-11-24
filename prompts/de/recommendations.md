<!-- recommendations.md – v2.4 GOLD STANDARD+ BRANCHE, SIZE & FÖRDERUNG
     Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences. -->

<!-- KONTEXT-VARIABLEN
     {{BRANCHE}} / {{BRANCHE_LABEL}}
     {{COMPANY_SIZE}} in {solo, team, kmu}
     {{UNTERNEHMENSGROESSE_LABEL}}
     {{HAUPTLEISTUNG}}
     {{BUNDESLAND_LABEL}}
     {score_gesamt}, {score_governance}, {score_sicherheit},
     {score_befaehigung}, {score_nutzen}
     {CONTEXT_QUICK_WINS}, {CONTEXT_ROADMAP_90D}, {CONTEXT_GAMECHANGER}
     {CONTEXT_FOERDERPOTENZIAL} (falls vorhanden – textuelle Beschreibung)
-->

<section class="section recommendations">
  <h2>Empfehlungen</h2>

  <p>
    Die folgenden Handlungsempfehlungen bauen auf den Analyse-Ergebnissen,
    den Quick Wins und der Roadmap auf. Sie sind speziell auf
    <strong>{{HAUPTLEISTUNG}}</strong> in der Branche
    <strong>{{BRANCHE_LABEL}}</strong> und die Unternehmensgröße
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> zugeschnitten.
  </p>

  <ol class="recommendations-list">
    <li>
      <h3>[H/M/N] Prägnanter Titel (max. 10 Wörter)</h3>
      <p>
        <strong>Ziel:</strong>
        [Welches konkrete Problem im Kernprozess von {{HAUPTLEISTUNG}}
        wird gelöst? Bezug auf Scores und/oder Quick Wins.]
      </p>
      <p>
        <strong>Nutzen / ROI:</strong>
        [messbare Wirkung: z. B. −X % Durchlaufzeit, −Z % Fehler/Nachbesserungen,
        +Y € Umsatz/Monat, geringeres Risiko, bessere Compliance.]
      </p>
      <p>
        <strong>Zeitrahmen:</strong>
        [30 / 60 / 90 Tage] mit 1–2 Meilensteinen
        (z. B. „Pilot abgeschlossen“, „Richtlinie verabschiedet“).
      </p>
      <p>
        <strong>Verantwortlich:</strong>
        [Rollen, passend zu {{COMPANY_SIZE}} – z. B. „Sie selbst“ (solo),
        „kleines Projektteam“, „Fachbereich + IT“.]
      </p>
      <p>
        <strong>Abhängigkeiten:</strong>
        [z. B. Bezug auf bestimmten Quick Win, Tool oder Governance-Baustein.]
      </p>
    </li>
    <!-- 4–6 weitere Empfehlungen im selben Muster -->
  </ol>

  <h3>Prioritäten-Überblick</h3>
  <table class="table">
    <thead>
      <tr>
        <th>Priorität</th>
        <th>Empfehlung</th>
        <th>Zeitrahmen</th>
        <th>Hauptnutzen</th>
      </tr>
    </thead>
    <tbody>
      <!-- 5–7 Zeilen, je Empfehlung -->
    </tbody>
  </table>

  <p class="small">
    <strong>Branchen- & Förder-Check:</strong>
    Mindestens eine Empfehlung adressiert branchentypische Besonderheiten
    (z. B. Regulatorik in Finanzen/Gesundheit, Urheberrecht in Medien,
    Baustellendokumentation im Bauwesen). Falls im Kontext konkrete
    Förderprogramme für {{BUNDESLAND_LABEL}} genannt werden
    ({CONTEXT_FOERDERPOTENZIAL}), kann eine Empfehlung die
    <em>Prüfung und Beantragung</em> dieser Förderung enthalten –
    ohne neue Programme oder Beträge zu erfinden.
  </p>
</section>
