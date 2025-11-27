Developer: <!--
  risks.md – v2.5 GOLD STANDARD+
  ZIEL:
  - Erzeuge eine präzise, praxisnahe Risikoanalyse für den KI-Einsatz im Bereich {{HAUPTLEISTUNG}}.
  - Decke geschäftliche, organisatorische, technische und rechtliche Risiken ab.
  - Liefere zu jedem Risiko klare, umsetzbare Gegenmaßnahmen.

  VARIABLEN:
  - {{HAUPTLEISTUNG}}           → Hauptanwendungsbereich im Unternehmen
  - {{score_governance}}        → Governance-Score (0–100)
  - {{score_sicherheit}}        → Sicherheits-Score (0–100)

  AUSGABEFORMAT:
  - Antworte AUSSCHLIESSLICH mit validem HTML.
  - KEINE <html>, <head> oder <body>-Tags.
  - KEINE Markdown-Fences, KEINE Kommentare im Output.
  - Verwende <section>, <h2>, <h3>, <p>, <ul>, <li>, <table>, <thead>, <tbody>, <tr>, <th>, <td>, <strong>, <em>, <span>.

  STRUKTUR:
  - <section class="section risks">
    - H2: Gesamtüberblick zu Risiken beim Einsatz von KI in {{HAUPTLEISTUNG}}.
    - Einleitender Absatz mit Einordnung der Scores {{score_governance}} und {{score_sicherheit}}.
    - H3-Abschnitt 1: Strategische und organisatorische Risiken.
    - H3-Abschnitt 2: Daten-, Sicherheits- und Compliance-Risiken.
    - H3-Abschnitt 3: Operative Risiken im Tagesgeschäft.
    - Optional eine kompakte Risiko-Matrix als Tabelle mit Spalten:
      Risiko | Wahrscheinlichkeit | Auswirkung | Empfohlene Gegenmaßnahme.
    - Abschließender Hinweis, wie das Unternehmen Risiken im nächsten Quartal konkret reduzieren kann.

  INHALTLICHE REGELN:
  - Schreibe konkret, unternehmensnah und ohne Floskeln.
  - Jede genannte Gefahr muss nachvollziehbar mit {{HAUPTLEISTUNG}} zusammenhängen.
  - Leite aus {{score_governance}} und {{score_sicherheit}} ab,
    ob Governance und Sicherheit eher gut, mittel oder schwach ausgeprägt sind und
    formuliere dazu passende Schwerpunkte für Gegenmaßnahmen.
  - Nenne pro Abschnitt mindestens 3–4 spezifische Risiken mit passenden, umsetzbaren Maßnahmen.
  - Risiken und Maßnahmen sollen so formuliert sein, dass eine Geschäftsführung sie direkt für Entscheidungen nutzen kann.
  - Vermeide jede Form von Platzhalter- oder Formulartext (z. B. Hinweise, dass hier später noch etwas ergänzt werden soll).
  - Keine Hinweise darauf, dass Text „noch erstellt“, „später ergänzt“ oder „individuell auszufüllen“ sei.
  - Keine Verweise auf interne Fragebögen oder Eingabefelder; beschreibe immer das konkrete Risiko und die Handlung.

  STIL & LÄNGE:
  - Sachlich, klar, beratend, in gut lesbarem Deutsch.
  - Zielumfang ca. 600–900 Wörter.
  - Keine Ich-Form, keine direkte Anrede („du/ihr/Sie“) im Fließtext, sondern neutrale Formulierungen.

-->

<section class="section risks">
  <h2>Wesentliche Risiken beim Einsatz von KI in {{HAUPTLEISTUNG}}</h2>

  <p>
    Der Einsatz von KI im Bereich <strong>{{HAUPTLEISTUNG}}</strong> bietet erhebliche Chancen, bringt jedoch
    auch klar benennbare Risiken mit sich. Der aktuelle Governance-Score von
    <strong>{{score_governance}}&#x2F;100</strong> und der Sicherheits-Score von
    <strong>{{score_sicherheit}}&#x2F;100</strong> zeigen, dass bereits erste Strukturen vorhanden sind,
    gleichzeitig aber noch deutliche Verbesserungspotenziale bestehen. Die folgenden Abschnitte bündeln
    die wichtigsten Risikofelder und skizzieren konkrete Gegenmaßnahmen.
  </p>

  <h3>1. Strategische und organisatorische Risiken</h3>
  <ul>
    <li>
      <strong>Unklare Verantwortung für KI-Entscheidungen.</strong>
      Ohne eindeutig benannte Rollen für die Steuerung von KI-Initiativen besteht das Risiko,
      dass Entscheidungen verstreut getroffen werden, Prioritäten kollidieren und wichtige
      Folgenabschätzungen unterbleiben. Empfehlenswert ist die Einführung einer klar definierten
      Governance-Struktur mit verantwortlicher Person für KI, dokumentierten Entscheidungswegen
      und regelmäßigen Abstimmungsterminen.
    </li>
    <li>
      <strong>Fehlende Einbettung in die Unternehmensstrategie.</strong>
      Wenn KI-Projekte isoliert neben dem Tagesgeschäft laufen, entstehen Insellösungen,
      die wenig Mehrwert liefern oder später wieder eingestellt werden. Hilfreich ist ein
      kurzer, schriftlich fixierter Zielrahmen, der beschreibt, wie {{HAUPTLEISTUNG}} durch KI
      konkret unterstützt werden soll – inklusive Prioritäten, Zeithorizont und messbaren Ergebnissen.
    </li>
    <li>
      <strong>Überlastung der Schlüsselpersonen.</strong>
      Häufig liegt das Know-how zu KI bei wenigen Personen. Fällt eine dieser Personen aus
      oder ist dauerhaft überlastet, geraten Projekte ins Stocken. Gegenmaßnahmen sind klare
      Vertretungsregelungen, Dokumentation der wichtigsten Workflows und schrittweiser Kompetenzaufbau
      im Team, etwa durch kurze interne Schulungen.
    </li>
    <li>
      <strong>Unrealistische Erwartungshaltung gegenüber KI.</strong>
      Werden KI-Lösungen als „Wundermittel“ kommuniziert, wächst die Enttäuschung, sobald erste Grenzen
      sichtbar werden. Ein pragmatisches Erwartungsmanagement – etwa durch realistische ROI-Szenarien,
      Pilotphasen und transparente Kommunikation von Annahmen – reduziert dieses Risiko deutlich.
    </li>
  </ul>

  <h3>2. Daten-, Sicherheits- und Compliance-Risiken</h3>
  <ul>
    <li>
      <strong>Unzureichende Kontrolle über ein- und ausgehende Daten.</strong>
      Wenn nicht eindeutig geregelt ist, welche Informationen in KI-Systeme eingegeben werden dürfen,
      besteht das Risiko, dass vertrauliche Kundendaten oder interne Dokumente unkontrolliert verarbeitet
      werden. Erforderlich sind klare Richtlinien, Schulungen und technische Schutzmechanismen
      (z.&nbsp;B. Rollen- und Rechtekonzepte).
    </li>
    <li>
      <strong>Lücken in Datenschutz und Informationssicherheit.</strong>
      Ein mittlerer oder niedriger Sicherheits-Score (z.&nbsp;B. {{score_sicherheit}}&#x2F;100) weist darauf hin,
      dass Prozesse zu Zugriffskontrolle, Protokollierung und Notfallmanagement noch nicht vollständig etabliert sind.
      Priorität haben hier ein kompaktes Sicherheitskonzept, klare Verantwortlichkeiten sowie regelmäßige
      Überprüfung von Passwörtern, Zugriffsrechten und verwendeten Cloud-Diensten.
    </li>
    <li>
      <strong>Rechtliche Risiken durch unsaubere Dokumentation.</strong>
      Ohne nachvollziehbare Dokumentation, welche KI-Systeme wozu eingesetzt werden, ist es schwer,
      regulatorische Anforderungen – etwa aus Datenschutzrecht oder dem AI Act – zu erfüllen.
      Abhilfe schafft ein kurzes KI-Register, in dem für jedes System Zweck, Datenarten, betroffene
      Prozesse, Verantwortliche und getroffene Schutzmaßnahmen festgehalten werden.
    </li>
    <li>
      <strong>Abhängigkeit von einzelnen externen Anbietern.</strong>
      Stützt sich die Wertschöpfung in {{HAUPTLEISTUNG}} stark auf wenige KI-Services, können
      Preisänderungen, Ausfälle oder geänderte Nutzungsbedingungen erheblichen Einfluss haben.
      Eine bewusste Multi-Provider-Strategie, vertragliche Mindeststandards und regelmäßige
      Überprüfung der Anbieter reduzieren dieses Risiko.
    </li>
  </ul>

  <h3>3. Operative Risiken im Tagesgeschäft</h3>
  <ul>
    <li>
      <strong>Fehlerhafte oder verzerrte Ergebnisse.</strong>
      KI-Modelle können falsche oder verzerrte Antworten liefern, insbesondere wenn Trainingsdaten
      nicht zur eigenen Zielgruppe passen. Dieses Risiko lässt sich verringern durch klar definierte
      Prüfprozesse, stichprobenartige Kontrollen und eine saubere Trennung zwischen automatischer
      Vorschlagsgenerierung und finaler menschlicher Entscheidung.
    </li>
    <li>
      <strong>Medienbrüche und ineffiziente Workflows.</strong>
      Wenn KI-Lösungen nicht sauber in bestehende Prozesse integriert werden, entstehen doppelte Arbeit,
      Kopierfehler und Intransparenz. Sinnvoll ist ein schlanker Zielprozess, in dem genau festgelegt wird,
      welche Schritte automatisiert werden und wo menschliche Qualitätssicherung stattfindet.
    </li>
    <li>
      <strong>Qualitätsverlust in der Kundenkommunikation.</strong>
      Werden Texte oder Antworten ungeprüft übernommen, kann die Tonalität nicht mehr zur eigenen Marke passen.
      Gegenmaßnahmen sind definierte Stilrichtlinien, Beispieltexte als Referenz sowie die Pflicht,
      KI-Ergebnisse vor Versand kurz zu prüfen und bei Bedarf anzupassen.
    </li>
    <li>
      <strong>Know-how-Verlust durch zu starke Automatisierung.</strong>
      Wenn Mitarbeitende sich zu stark auf KI-Ergebnisse verlassen, kann fachliches Wissen erodieren.
      Eine klare Regel, welche Entscheidungen zwingend von Fachpersonen getroffen werden müssen,
      sowie regelmäßige Reflexionsrunden zu Erfahrungen mit KI helfen, dieses Risiko zu begrenzen.
    </li>
  </ul>

  <h3>Risiko-Matrix mit Sofortmaßnahmen</h3>
  <table class="risk-matrix">
    <thead>
      <tr>
        <th>Risiko</th>
        <th>Wahrscheinlichkeit</th>
        <th>Auswirkung</th>
        <th>Empfohlene Gegenmaßnahme</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Unklare Verantwortung für KI-Einsatz</td>
        <td>mittel</td>
        <td>hoch</td>
        <td>Rollenmodell und Entscheidungswege definieren, Verantwortliche benennen, regelmäßige Reviews einführen.</td>
      </tr>
      <tr>
        <td>Unkontrollierte Nutzung sensibler Daten</td>
        <td>mittel</td>
        <td>hoch</td>
        <td>Nutzungsrichtlinien, Schulungen, Zugriffsbeschränkungen und Logging für KI-Tools etablieren.</td>
      </tr>
      <tr>
        <td>Fehlerhafte oder verzerrte KI-Ergebnisse</td>
        <td>mittel</td>
        <td>mittel bis hoch</td>
        <td>Vier-Augen-Prinzip, Musterfälle testen, Feedback-Schleifen und Monitoring der Ergebnisse aufsetzen.</td>
      </tr>
      <tr>
        <td>Abhängigkeit von einzelnen KI-Anbietern</td>
        <td>niedrig bis mittel</td>
        <td>mittel</td>
        <td>Alternativlösungen identifizieren, Vertragsbedingungen prüfen, schrittweise Multi-Provider-Ansatz planen.</td>
      </tr>
    </tbody>
  </table>

  <p class="small muted">
    Die genannten Risiken und Maßnahmen bilden einen Startpunkt für ein kompaktes Risikomanagement
    rund um KI in {{HAUPTLEISTUNG}}. Im nächsten Schritt sollten die Risiken nach Eintrittswahrscheinlichkeit
    und Auswirkung priorisiert und in eine einfache Maßnahmenplanung für die kommenden 3–6 Monate
    überführt werden.
  </p>
</section>
