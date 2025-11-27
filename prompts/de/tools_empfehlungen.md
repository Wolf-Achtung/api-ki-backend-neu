Developer:
<!--
  tools_empfehlungen.md – v4.1 GOLD STANDARD+ (size-aware, branchen-aware, validator-safe)

  ZIEL DES PROMPTS
  - Erzeuge eine klar strukturierte, praxistaugliche Tool-Empfehlungssektion ("KI-Stack"),
    die zu Branche {{BRANCHE_LABEL}}, Unternehmensgröße {{UNTERNEHMENSGROESSE_LABEL}}
    und Hauptleistung {{HAUPTLEISTUNG}} passt.
  - Der Text soll Solo, kleine Teams und KMU gleichermaßen adressieren, aber
    je nach Größe andere Schwerpunkte setzen.
  - Output ist reines HTML (kein Markdown, keine Developer-Sätze).

  VARIABLEN
  - {{BRANCHE_LABEL}}            → z. B. "Beratung & Dienstleistungen"
  - {{UNTERNEHMENSGROESSE_LABEL}}→ verbale Größe, z. B. "Solo", "2–10 (Kleines Team)", "11–100 (KMU)"
  - {{HAUPTLEISTUNG}}            → z. B. "Beratung von Unternehmen zur Integration von KI …"
  - {{COMPANY_SIZE}}             → "solo", "small_team" oder "kmu"

  GRÖSSENLOGIK (INHALTLICH)
  - solo:
      * Empfehlung: maximal 3–5 Tools im Kernstack, einfache Bedienung, geringer Integrationsaufwand.
      * Beispiele: 1 KI-Assistent, 1 Wissens-/Notiz-Tool, 1 Formular-/Automations-Tool.
      * Keine Begriffe wie "Abteilung", "Projektteam", "Bereich" verwenden.
  - small_team:
      * Empfehlung: gemeinsamer Workspace, Kollaboration, Rechte-/Rollenkonzepte.
      * Tools für Aufgabenverteilung, gemeinsames Wissens-Repo, einfache Workflows.
  - kmu:
      * Empfehlung: klar definierter Stack mit Governance, Rollen und Monitoring.
      * Tools für Teamarbeit, Rechteverwaltung, ggf. fachbereichsspezifische Lösungen.

  STIL & REGELN
  - Schreibe konkret, aber produktneutral (keine Produktnamen wie "Notion", "Monday", "Slack").
  - Fokus auf Toolkategorien und ihren Zweck im Prozess {{HAUPTLEISTUNG}}.
  - Keine Wörter wie "Platzhalter", "Content wird erstellt", "TODO", "Freitextfeld".
  - Kein Verweis auf den Prompt oder die Variablen im sichtbaren Text.
  - Output muss alleine lesbar sein, ohne weitere Erklärungen.

-->

<section class="section tools">
  <h2>Empfohlener KI-Stack für {{BRANCHE_LABEL}}</h2>

  <p>
    Für den Kernprozess <strong>{{HAUPTLEISTUNG}}</strong> empfiehlt sich ein klar strukturierter
    KI-Stack, der zur Größe <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> passt. Er soll
    Ihren Alltag spürbar entlasten, ohne die Organisation zu überfordern, und sich später
    schrittweise erweitern lassen.
  </p>

  <p>
    Die folgenden Bausteine bilden eine Empfehlung für einen leichtgewichtigen KI-Stack:
    ein solides Fundament aus Assistent, Wissensspeicher und Kollaboration, ergänzende
    Tools für die wichtigsten Use Cases sowie einfache Mechanismen für Qualität und Sicherheit.
  </p>

  <h3>1. Fundament &amp; Basis-Infrastruktur</h3>
  <ul>
    <li>
      <strong>KI-Assistent für Alltagstätigkeiten</strong> –
      z.&nbsp;B. zur Erstellung und Überarbeitung von Texten, zur Strukturierung von Notizen,
      zur Vorbereitung von Workshops oder zur Verdichtung von Fragebogen-Antworten.
    </li>
    <li>
      <strong>Wissens- und Dokumentenspeicher</strong> –
      ein zentraler Ort für Fragebögen, Report-Templates, Best-Practice-Beispiele,
      Protokolle und KI-Prompt-Sammlungen. Wichtig ist eine klare Struktur, damit Inhalte schnell gefunden werden.
    </li>
    <li>
      <strong>Kollaborations- bzw. Aufgaben-Tool</strong> –
      für Planung, Aufgabenlisten und Statusübersichten. Bei Solo-Unternehmen reicht
      eine einfache Aufgabenverwaltung, bei Teams sollten Zuständigkeiten und Fristen
      transparent abbildbar sein.
    </li>
  </ul>

  <h3>2. Tools für den Kernprozess {{HAUPTLEISTUNG}}</h3>
  <ul>
    <li>
      <strong>Formular- oder Fragebogen-Tool</strong> –
      zur strukturierten Erfassung von Kundendaten und Antworten (z.&nbsp;B. Online-Formulare
      mit klaren Skalen und offenen Antwortmöglichkeiten).
    </li>
    <li>
      <strong>Auswertungs- und Berichtswerkzeug</strong> –
      unterstützt die Verarbeitung der Antworten mit Hilfe von KI, die Erstellung von
      Reifegrad-Analysen, Handlungsempfehlungen und Reports in einheitlichem Layout.
    </li>
    <li>
      <strong>Automations-Tool</strong> –
      verbindet Fragebogen, Auswertung und Report-Erstellung (z.&nbsp;B. Trigger beim Absenden
      des Formulars, automatische Erstellung eines Berichts, Benachrichtigung per E-Mail).
    </li>
    <li>
      <strong>Spezifische Fach-Tools je Branche</strong> –
      je nach Branche {{BRANCHE_LABEL}} können zusätzliche Lösungen sinnvoll sein,
      etwa für Terminplanung, Dokumentenfreigaben, Medienproduktion oder Analyse von Geschäftszahlen.
    </li>
  </ul>

  <h3>3. Governance, Sicherheit &amp; Qualität</h3>
  <ul>
    <li>
      <strong>Einfache Richtlinien &amp; Rollen</strong> –
      kurze, schriftliche Regeln, welche Daten in KI-Tools eingegeben werden dürfen,
      wie Reports freigegeben werden und wer im Zweifel entscheidet. Bei Solo-Unternehmen
      genügt eine kompakte Checkliste, in Teams sollten Verantwortlichkeiten klar benannt sein.
    </li>
    <li>
      <strong>Dokumentation der KI-Nutzung</strong> –
      eine Übersicht, welche Tools wofür eingesetzt werden, mit welchem Datenumfang und
      welchen Schutzmaßnahmen. Diese Dokumentation ist hilfreich für Audits und für
      Anpassungen bei neuen regulatorischen Anforderungen.
    </li>
    <li>
      <strong>Qualitätskontrolle</strong> –
      kurze Prüfprozesse für wichtige KI-Ergebnisse (z.&nbsp;B. Vier-Augen-Prinzip bei Management-
      Reports, stichprobenartige Reviews, Definition von Mindeststandards für Struktur und Tonalität).
    </li>
  </ul>

  <h3>4. Einführung in Etappen</h3>
  <p>
    Statt alle Tools auf einmal einzuführen, sollte der KI-Stack in Etappen aufgebaut werden.
    Beginnen Sie mit einem stabilen Fundament aus Assistent, Wissensspeicher und einfacher
    Aufgabensteuerung. Anschließend folgen 1–2 Tools für den wichtigsten Use Case aus
    <strong>{{HAUPTLEISTUNG}}</strong>, bevor Spezial- und Governance-Elemente ausgebaut werden.
  </p>

  <table class="table tools-priorities">
    <thead>
      <tr>
        <th>Stufe</th>
        <th>Baustein</th>
        <th>Rolle im Prozess {{HAUPTLEISTUNG}}</th>
        <th>Empfohlener Zeitpunkt</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>1</td>
        <td>Assistent, Wissensspeicher, Aufgabenverwaltung</td>
        <td>
          Unterstützt die tägliche Arbeit, sichert Wissen und schafft Transparenz
          über Aufgaben und To-dos.
        </td>
        <td>innerhalb der ersten 30 Tage</td>
      </tr>
      <tr>
        <td>2</td>
        <td>Formular-Tool &amp; Auswertungs-Setup</td>
        <td>
          Ermöglicht die strukturierte Erfassung von Kundendaten und die KI-gestützte Analyse
          der Antworten mit konsistenten Reports.
        </td>
        <td>Tag 30–60</td>
      </tr>
      <tr>
        <td>3</td>
        <td>Automation &amp; Governance-Bausteine</td>
        <td>
          Reduziert manuelle Zwischenschritte, stärkt Sicherheit und Qualität
          und macht den Prozess skalierbar.
        </td>
        <td>ab etwa 60 Tagen</td>
      </tr>
    </tbody>
  </table>

  <p class="small muted">
    Der empfohlene KI-Stack ist bewusst schlank gehalten: Für {{UNTERNEHMENSGROESSE_LABEL}}
    steht im Vordergrund, schnell Nutzen im Kernprozess {{HAUPTLEISTUNG}} zu erzeugen und
    später bei Bedarf weitere Bausteine hinzuzufügen. So bleiben Kosten und Komplexität
    beherrschbar, während die Grundlage für eine spätere Skalierung gelegt wird.
  </p>
</section>
