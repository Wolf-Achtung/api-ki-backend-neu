Developer:
<!-- PLATIN++ PROMPT v5.3 - SPRINT N -->
<!-- SECTION: tools_empfehlungen -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, {{COMPANY_SIZE}} -->
<!-- TOKEN-BUDGET: 2500 (solo:0.8x=2000, team:1.0x=2500, kmu:1.15x=2875) -->
<!-- WORD_MINIMUM_SOLO: 120 -->
<!-- WORD_MINIMUM_TEAM: 160 -->
<!-- WORD_MINIMUM_KMU: 200 -->
<!-- RESEARCH: Tools können aus {{RESEARCH_PROVENANCE_HTML}} referenziert werden -->
<!--
ZIEL: Klar strukturierte Tool-Empfehlungssektion ("KI-Stack") für {{BRANCHE_LABEL}}.
MINDESTLÄNGE: solo≥120, team≥160, kmu≥200 Wörter (STRIKT EINHALTEN!)

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: 3–5 Tools, einfache Bedienung, geringer Integrationsaufwand
- team: gemeinsamer Workspace, Kollaboration, Rechte-/Rollenkonzepte
- kmu: definierter Stack mit Governance, Rollen, Monitoring, fachbereichsspezifisch

ANTI-REDUNDANZ:
- Tool-Details HIER vollständig erklären
- In Roadmaps nur referenzieren: "Tools (siehe KI-Stack)"

STIL & REGELN:
- Produktneutral (keine Markennamen)
- Fokus auf Toolkategorien und Zweck
- Keine Platzhalter oder Developer-Sprache

SPRINT N - SOLO PERSONA REGELN (STRIKT!):
{% if COMPANY_SIZE == "solo" %}
NICHT VERWENDEN für Solo:
- "Abteilung" → stattdessen: "Arbeitsbereich"
- "Projektteam" → stattdessen: "Projektkapazität"
- "Bereich" ist OK, aber nicht "Fachbereich"
- "Team aufbauen" → stattdessen: "Kapazität erweitern"
- "Mitarbeiter" → stattdessen: "externe Unterstützung" oder "Freelancer"
- "Teams" → stattdessen: "Ressourcen" oder "Kapazitäten"
- "Fachbereich" → stattdessen: "Arbeitsfeld"
Formulierungen ohne Team-/Abteilungsbegriff verwenden!
{% endif %}
-->

<section class="section tools">
  <h2>Empfohlener KI-Stack für {{BRANCHE_LABEL}}</h2>

  <p>
    Für den Kernprozess <strong>{{HAUPTLEISTUNG}}</strong> empfiehlt sich ein klar strukturierter
    KI-Stack, der zur Größe <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> passt. Er soll
    den Alltag spürbar entlasten, ohne die Organisation zu überfordern, und sich bei Bedarf
    schrittweise erweitern lassen.
  </p>

  <p>
    In der Praxis hat sich ein mehrstufiger Ansatz bewährt: Zunächst ein leichtgewichtiges
    Fundament, das Solo-Unternehmen, kleine Teams und KMU gleichermaßen nutzen können, dann
    gezielte Bausteine für den Kernprozess und schließlich ergänzende Elemente für Governance
    und Qualität.
  </p>

  <h3>Ausrichtung nach Unternehmensgröße</h3>
  <ul>
    <li>
      <strong>Solo-Unternehmen:</strong>
      Ein schlanker Stack mit 3–5 Kernbausteinen ist ausreichend – ein KI-Assistent,
      ein gut strukturierter Wissensspeicher und einfache Automatisierungen. Wichtig sind
      geringe Komplexität und möglichst wenig Pflegeaufwand.
    </li>
    <li>
      <strong>Kleine Teams (2–10 Personen):</strong>
      Der Fokus liegt auf einem gemeinsamen Workspace, klaren Zuständigkeiten und
      einfacher Aufgabenkoordination. Tools sollten Zusammenarbeit, geteiltes Wissen
      und abgestimmte Workflows unterstützen.
    </li>
    <li>
      <strong>KMU (11–100 Personen):</strong>
      Hier steht ein definierter KI-Stack mit Rollen, Rechten und Monitoring im Vordergrund.
      Fachbereiche benötigen eigenständige, aber kompatible Lösungen, die in ein
      übergreifendes Governance-Gerüst eingebettet sind.
    </li>
  </ul>

  <h3>1. Fundament &amp; Basis-Infrastruktur</h3>
  <ul>
    <li>
      <strong>KI-Assistent für Alltagstätigkeiten</strong> –
      für Entwürfe, Überarbeitung von Texten, Strukturierung von Notizen, Vorbereitung von
      Workshops oder die Verdichtung von Fragebogen-Antworten im Rahmen von {{HAUPTLEISTUNG}}.
      Bei Solo-Unternehmen genügt ein zentraler Assistent; in Teams und KMU sollte er so
      eingebunden sein, dass mehrere Personen ihn konsistent nutzen können.
    </li>
    <li>
      <strong>Wissens- und Dokumentenspeicher</strong> –
      ein zentraler Ort für Fragebögen, Report-Templates, Best-Practice-Beispiele,
      Protokolle und KI-Prompt-Sammlungen. Wichtig ist eine klare Struktur, damit Inhalte
      schnell gefunden und von allen Beteiligten verstanden werden.
    </li>
    <li>
      <strong>Kollaborations- bzw. Aufgaben-Tool</strong> –
      zur Planung von Aufgaben, Deadlines und Zuständigkeiten im Prozess {{HAUPTLEISTUNG}}.
      Solo-Unternehmen nutzen einfache Aufgabenlisten; kleine Teams und KMU sollten zusätzlich
      Verantwortlichkeiten, Status und Abhängigkeiten transparent abbilden können.
    </li>
  </ul>

  <h3>2. Tools für den Kernprozess {{HAUPTLEISTUNG}}</h3>
  <ul>
    <li>
      <strong>Formular- oder Fragebogen-Tool</strong> –
      zur strukturierten Erfassung von Kundendaten und Antworten, etwa über Online-Formulare
      mit klaren Skalen und offenen Feldern. Für Solo-Setups reicht eine kompakte Lösung;
      Teams und KMU profitieren von Mehrnutzerfähigkeit und einfachen Auswertungsmöglichkeiten.
    </li>
    <li>
      <strong>Auswertungs- und Berichtswerkzeug</strong> –
      unterstützt die Verarbeitung der Antworten mit Hilfe von KI, die Erstellung von
      Reifegrad-Analysen, Handlungsempfehlungen und Reports in einheitlichem Layout.
      Ein klarer Template-Ansatz sorgt dafür, dass alle Berichte in {{BRANCHE_LABEL}}
      professionell und konsistent wirken.
    </li>
    <li>
      <strong>Automations-Tool</strong> –
      verknüpft Fragebogen, Auswertung und Report-Erstellung. Typische Abläufe sind:
      Formularabsendung, automatische Erstellung eines Berichts, Versand per E-Mail
      oder Ablage im Wissensspeicher. Solo-Unternehmen nutzen einfache Automationen,
      KMU integrieren sie in bestehende Abläufe.
    </li>
    <li>
      <strong>Spezifische Fach-Tools je Branche</strong> –
      je nach {{BRANCHE_LABEL}} können zusätzliche Lösungen sinnvoll sein, etwa für
      Terminplanung, Dokumentenfreigaben, Medienproduktion oder Analyse von Geschäftszahlen.
      Diese Tools sollten den KI-Stack ergänzen, nicht unnötig verkomplizieren.
    </li>
  </ul>

  <h3>3. Governance, Sicherheit &amp; Qualität</h3>
  <ul>
    <li>
      <strong>Einfache Richtlinien &amp; Rollen</strong> –
      kurze, schriftliche Regeln, welche Daten in KI-Tools eingegeben werden dürfen,
      wie Ergebnisse geprüft und freigegeben werden und wer im Zweifel entscheidet.
      Solo-Unternehmen formulieren eine kompakte Checkliste; kleine Teams und KMU
      benennen Verantwortliche für Qualität, Datenschutz und Nutzung.
    </li>
    <li>
      <strong>Dokumentation der KI-Nutzung</strong> –
      eine Übersicht, welche Tools wofür eingesetzt werden, mit welchem Datenumfang
      und welchen Schutzmaßnahmen. Diese Dokumentation erleichtert Anpassungen an neue
      regulatorische Anforderungen und schafft Transparenz gegenüber Mitarbeitenden
      und externen Partnern.
    </li>
    <li>
      <strong>Qualitätskontrolle</strong> –
      kurze Prüfprozesse für wichtige KI-Ergebnisse, z.&nbsp;B. ein zweiter Blick auf
      Management-Reports, stichprobenartige Reviews oder Mindeststandards für Struktur
      und Tonalität. Je größer das Unternehmen, desto wichtiger ist eine klare Definition,
      wann ein Review verpflichtend ist.
    </li>
  </ul>

  <h3>4. Einführung in Etappen</h3>
  <p>
    Statt alle Tools gleichzeitig einzuführen, sollte der KI-Stack in überschaubaren
    Etappen aufgebaut werden. Zunächst ein stabiles Fundament aus Assistent,
    Wissensspeicher und Aufgabensteuerung, anschließend ein Formular- und
    Auswertungs-Setup für {{HAUPTLEISTUNG}} und schließlich gezielte Automationen
    und Governance-Bausteine.
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
          über Aufgaben und Prioritäten.
        </td>
        <td>innerhalb der ersten 30 Tage</td>
      </tr>
      <tr>
        <td>2</td>
        <td>Formular-Tool &amp; Auswertungs-Setup</td>
        <td>
          Macht Kundendaten im Rahmen von {{HAUPTLEISTUNG}} strukturiert nutzbar und
          ermöglicht KI-gestützte Auswertungen und Reports.
        </td>
        <td>Tag 30–60</td>
      </tr>
      <tr>
        <td>3</td>
        <td>Automation &amp; Governance-Bausteine</td>
        <td>
          Reduziert manuelle Zwischenschritte, stärkt Sicherheit und Qualität und macht
          den Gesamtprozess skalierbar – besonders relevant für wachsende Teams und KMU.
        </td>
        <td>ab etwa 60 Tagen</td>
      </tr>
    </tbody>
  </table>

  <p class="small muted">
    Der empfohlene KI-Stack ist bewusst schlank gehalten: Für {{UNTERNEHMENSGROESSE_LABEL}}
    steht im Vordergrund, schnell Nutzen im Kernprozess {{HAUPTLEISTUNG}} zu erzeugen und
    bei Bedarf schrittweise weitere Bausteine hinzuzufügen. So bleiben Kosten und
    Komplexität beherrschbar, während die Grundlage für eine spätere Skalierung gelegt wird.
  </p>
</section>
