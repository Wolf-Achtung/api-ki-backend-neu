**WICHTIG – Längenlimit: Deine Antwort darf maximal 1200 Wörter umfassen. Kürze lieber als zu überziehen.**

Developer:
<!-- PLATIN++ PROMPT v5.5 - SPRINT G17.S -->
<!-- SECTION: tools_empfehlungen -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{BRANCH_SHORT_LABEL}}, {{OFFERING_LABEL}}, {{COMPANY_SIZE}}, {{hauptleistung}} -->
<!-- TOKEN-BUDGET: 2800 (solo:0.8x=2240, team:1.0x=2800, kmu:1.15x=3220) -->
<!--
=============================================================================
Problem #7 FIX: Hauptleistung als Analyse-Kern
=============================================================================
-->
{% include '_hauptleistung_context.md' %}
<!-- WORD_MINIMUM_SOLO: 150 -->
<!-- WORD_MINIMUM_TEAM: 200 -->
<!-- WORD_MINIMUM_KMU: 250 -->
<!--
ZIEL: Klar strukturierte Tool-Empfehlungssektion ("KI-Stack") für {{BRANCH_CONTEXT_LABEL}}.

KURZLABELS (VERPFLICHTEND!):
- {{BRANCH_CORE_LABEL}} = Branche in 8-12 Wörtern
- {{BRANCH_CONTEXT_LABEL}} = Branche in 4-6 Wörtern
- {{BRANCH_SHORT_LABEL}} = Kurzform in 3-5 Wörtern (G17.S)
- {{OFFERING_LABEL}} = Hauptleistung in 6-10 Wörtern

MINDESTLÄNGE (STRIKT – G17.S UPDATE!):
- Solo: ≥150 Wörter (inkl. Responsible AI-Abschnitt)
- Team: ≥200 Wörter (besonders für regulierte Branchen!)
- KMU: ≥250 Wörter (inkl. Responsible AI-Abschnitt)

STRUKTUR NACH GRÖSSE:
{% if COMPANY_SIZE == "solo" %}
SOLO: 4 Tool-Cluster mit je 2-3 Beispielen:
1. KI-Assistent & Basis (2-3 Beispiele)
2. Kernprozess-Tools für {{OFFERING_LABEL}} (2-3 Beispiele)
3. Qualität & Dokumentation (1-2 Beispiele)
4. Responsible AI & Governance Tools (SPRINT G17.S – PFLICHT!)

{% elif COMPANY_SIZE == "team" %}
TEAM: 5 Tool-Cluster mit je 2-3 Beispielen (min. 200 Wörter!):
1. Kollaboration & Gemeinsamer Workspace (2-3 Beispiele)
2. Kernprozess-Tools für {{OFFERING_LABEL}} (2-3 Beispiele)
3. Reporting & Auswertung (2-3 Beispiele)
4. Governance & Qualität (2 Beispiele)
5. Responsible AI & Governance Tools (SPRINT G17.S – PFLICHT!)

SPRINT G17.S – TEAM FINANCE ERWEITERUNG (regulierte Branchen):
Für Finanzen, Gesundheit, Recht VERPFLICHTEND zusätzliche Unterabschnitte:
- Kern-Plattformen & Data Hub: Rolle, Nutzen, Integrationslogik (2-3 Sätze)
- Risiko- & Compliance-Tools: Bezug zu BAIT/VAIT/MaRisk (Funktionsklassen, keine Firmennamen)
- Reporting & Kollaboration: Interne Koordination, Dokumentation, Prüfpfade (2-3 Sätze)

{% else %}
KMU: 6 Tool-Cluster mit je 2-3 Beispielen (min. 250 Wörter!):
1. Enterprise-Basis (KI-Plattform, Wissensspeicher)
2. Fachbereichsspezifische Tools für {{OFFERING_LABEL}}
3. Reporting/BI-Integration
4. Compliance & Governance
5. Einführung & Schulung
6. Responsible AI & Governance Tools (SPRINT G17.S – PFLICHT!)
{% endif %}

SPRINT G17.S – RESPONSIBLE AI & GOVERNANCE TOOLS (ALLE GRÖSSEN):
Dieser Unterabschnitt ist VERPFLICHTEND und enthält:
- Audit-Spuren: Tools für Nachvollziehbarkeit von KI-Entscheidungen
- Versionierung: Dokumentation von Prompt-Versionen und Modelländerungen
- Kontrollmechanismen: Qualitätsprüfung vor Freigabe, Review-Workflows
Länge: Solo +30-50 Wörter, Team +40-60 Wörter, KMU +50-70 Wörter
Keine Markennamen, nur Toolklassen!

ANTI-REDUNDANZ (G17.S VERSCHÄRFT):
- Tool-Details HIER vollständig erklären
- In Roadmaps nur referenzieren: "Tools (→ siehe KI-Stack)"
- Keine generischen Meta-Sätze ("Dieser Abschnitt fasst...")
- KEINE Dopplung von Tools-Engine-Ausgabe (TOOLS_HTML aus B2-Engine)
- Beschreibe Einsatzlogik, NICHT nochmal die Tools selbst

SPRINT G18 - NARRATIVE VERBINDUNGEN:
- Einleitend erwähnen: "Diese Tool-Klassen unterstützen die Phasen der Roadmap 90d/12m..."
- Starter Kit referenzieren: "Im Starter Kit finden Sie eine kuratierte Auswahl..."
- Bezug zu Förderprogrammen herstellen wo relevant

STIL & REGELN:
- Produktneutral (keine Markennamen)
- Fokus auf Toolkategorien und Zweck
- Konkrete Einsatzfelder pro Tool-Typ nennen
- Keine Platzhalter oder Developer-Sprache
- Gesamtlänge: 180–250 Wörter, keine Bullet-Orgien, keine Tool-Listen
- Fokus auf Funktionslogik statt Markennamen

SPRINT G6 - PERSONA HARD-GUARDS (STRIKT!):
{% if COMPANY_SIZE == "solo" %}
SOLO-MODUS - VERBOTEN:
- "Abteilung" → "Arbeitsbereich"
- "Projektteam" → "Projektkapazität"
- "Teams" → "Ressourcen"
{% elif COMPANY_SIZE == "team" %}
TEAM-MODUS - VERBOTEN:
- "Division/Unit/Konzern" → nicht verwenden
- Solo-Begriffe: "Einzelperson", "allein"
{% else %}
KMU-MODUS - VERBOTEN:
- "Konzern/Division/Unit" → nicht verwenden
- Solo-Begriffe: "Einzelperson", "allein"
{% endif %}
-->

ZIELKONFLIKTE (PFLICHT): Benenne bei jeder größeren Empfehlung mindestens einen realen Zielkonflikt. Beispiele: Geschwindigkeit vs. Qualität, Automatisierung vs. Kontrolle, Datenschutz vs. Bequemlichkeit, Standardisierung vs. Individualität, Investition heute vs. Nutzen später. Formuliere Trade-offs knapp im Fließtext, ohne zusätzliche Sonderbox. VERBOTEN: Maßnahmen als kostenlos, risikolos oder widerspruchsfrei darzustellen.

BEGRIFFSKONSISTENZ (VERBINDLICH — OPT-A7):
Verwende diese Begriffe einheitlich im gesamten Report:
- „KI-Governance" = Oberbegriff für Regeln, Rollen, Freigaben rund um KI-Nutzung. „KI-Richtlinie" = das konkrete Dokument.
- „ROI" = immer „ROI", bei erster Nennung pro Abschnitt „Return on Investment (ROI)".
- „Break-Even" = Zeitpunkt der Amortisation im Fließtext. „Amortisation" nur in Tabellen/KPIs.
- „EU AI Act" = immer, bei erster Nennung „EU AI Act (KI-Verordnung der EU)". NICHT standalone „KI-Verordnung".
- „AVV" = bei erster Nennung „AV-Vertrag (AVV)", danach nur „AVV".
- „KI-Ausgabe" = allgemein für KI-Ergebnisse. „KI-Entwurf" = Text, der noch geprüft werden muss. NICHT „KI-Output".
- „Prüfschritt" = allgemein. „Freigabe" = formaler Akt. „Vier-Augen-Prinzip" = zwei Personen prüfen. NICHT „Review".
- „DSGVO" = nie ausschreiben. „Tool" = Software. „Werkzeug" = nur in Metaphern. Nicht im selben Absatz wechseln.

<!-- SPRINT 2: OPT-B8 Tool-Entscheidungshilfe stärken -->
Formuliere verständlich für einen Geschäftsführer ohne KI-Vorwissen. Tool-Namen bei erster Nennung in einem Halbsatz erklären, etwa „Microsoft Copilot (KI-Assistent in Word, Outlook und Excel)".

TOOL-ENTSCHEIDUNGSHILFE (PFLICHT):
(a) KLARE STARTEMPFEHLUNG: Formuliere im Einleitungstext eine konkrete Empfehlung „Starten Sie mit [Tool/Toolklasse X]", basierend auf dem Abschnitt „Einführung in Etappen". Der Leser muss wissen, welches Tool ZUERST kommt. Begründe in 1 Satz, warum gerade dieses.
(b) STARTREIHENFOLGE: Die bestehende Etappen-Tabelle (Stufe 1/2/3) ist die Startreihenfolge. Ergänze in der Einleitung einen Hinweis: „Folgen Sie der Reihenfolge: erst [Stufe 1], dann [Stufe 2], dann [Stufe 3]."
(c) WARNUNG VOR OVER-ENGINEERING: Ergänze im Abschnitt „Einführung in Etappen" einen Satz: „Führen Sie maximal 1–2 Tools gleichzeitig ein. Mehr parallele Einführungen erhöhen Schulungsaufwand und Fehlerrisiko überproportional."
(d) ENTSCHEIDUNGSLOGIK NACH VORHANDENEM STACK: Falls der Kunde bereits Software nutzt, soll der Text darauf eingehen: „Sie nutzen bereits [vorhandene Software] — deshalb empfehlen wir als Einstieg [Tool/Kategorie], weil es sich direkt integrieren lässt." Nutze {{hauptleistung}} als Kontext.
CONSTRAINT: Vendor-Audit-Daten (Risk Engine) unverändert. Keine konkreten Preise im Prompt. Bestehende Wortlimits einhalten.
<!-- /SPRINT 2 -->

<section class="section tools">
  <h2>Empfohlener KI-Stack für {{BRANCH_CONTEXT_LABEL}}</h2>

  <p>
    {% if hauptleistung %}
    Für "{{hauptleistung}}" empfiehlt sich ein klar strukturierter KI-Stack,
    der konkret bei dieser Hauptleistung Zeit spart und sich schrittweise erweitern lässt.
    {% else %}
    Für {{OFFERING_LABEL}} empfiehlt sich ein klar strukturierter KI-Stack,
    der den Alltag spürbar entlastet und sich bei Bedarf schrittweise erweitern lässt.
    {% endif %}
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
      für Entwürfe, Textüberarbeitung, Strukturierung von Notizen und die Verdichtung
      von Eingaben. Bei Solo-Setups genügt ein zentraler Assistent; in Teams und KMU
      sollte er so eingebunden sein, dass mehrere Personen ihn konsistent nutzen.
    </li>
    <li>
      <strong>Wissens- und Dokumentenspeicher</strong> –
      ein zentraler Ort für Templates, Best-Practice-Beispiele und Prompt-Sammlungen.
      Klare Struktur ermöglicht schnelles Finden und gemeinsames Verständnis.
    </li>
    <li>
      <strong>Kollaborations- bzw. Aufgaben-Tool</strong> –
      zur Planung von Aufgaben, Deadlines und Zuständigkeiten.
      Solo: einfache Aufgabenlisten; Teams/KMU: Verantwortlichkeiten und Abhängigkeiten.
    </li>
  </ul>

  <h3>2. Tools für den Kernprozess {{OFFERING_LABEL}}</h3>
  <ul>
    <li>
      <strong>Formular- oder Fragebogen-Tool</strong> –
      zur strukturierten Erfassung von Kundendaten und Antworten, wie über Online-Formulare
      mit klaren Skalen und offenen Feldern. Für Solo-Setups reicht eine kompakte Lösung;
      Teams und KMU profitieren von Mehrnutzerfähigkeit und einfachen Auswertungsmöglichkeiten.
    </li>
    <li>
      <strong>Auswertungs- und Berichtswerkzeug</strong> –
      unterstützt die Verarbeitung mit Hilfe von KI und die Erstellung von
      Analysen und Reports. Template-Ansatz für professionelle, konsistente Ergebnisse.
    </li>
    <li>
      <strong>Automations-Tool</strong> –
      verknüpft Eingabe, Auswertung und Ergebnis-Erstellung. Typische Abläufe:
      Formular → Analyse → Report → Versand. Solo: einfache Automationen;
      KMU: Integration in bestehende Abläufe.
    </li>
    <li>
      <strong>Branchenspezifische Fach-Tools</strong> –
      je nach {{BRANCH_CONTEXT_LABEL}} können zusätzliche Lösungen sinnvoll sein,
      wie für Terminplanung, Dokumentenfreigaben oder Fachanalysen.
      Diese sollten den Stack ergänzen, nicht verkomplizieren.
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

  <!-- G17.S: Responsible AI & Governance Tools (PFLICHT für alle Größen) -->
  <h3>4. Responsible AI &amp; Governance Tools</h3>
  <ul>
    <li>
      <strong>Audit-Spuren &amp; Nachvollziehbarkeit</strong> –
      Werkzeuge, die automatisch protokollieren, welche KI-Anfragen gestellt wurden,
      welche Ergebnisse zurückkamen und wer diese freigegeben hat. Diese Transparenz
      ist unverzichtbar für Qualitätsaudits und regulatorische Prüfungen.
    </li>
    <li>
      <strong>Versionierung &amp; Änderungsdokumentation</strong> –
      Systeme zur Verwaltung von Prompt-Versionen, Modellständen und
      Konfigurationsänderungen. So bleibt nachvollziehbar, welche Ergebnisse
      unter welchen Bedingungen entstanden sind.
    </li>
    <li>
      <strong>Kontrollmechanismen &amp; Review-Workflows</strong> –
      definierte Prüfpunkte vor der Freigabe wichtiger KI-Outputs. Je nach Größe
      können das einfache Checklisten (Solo), Peer-Reviews (Team) oder formale
      Freigabeprozesse mit Vier-Augen-Prinzip (KMU) sein.
    </li>
  </ul>

  {% if COMPANY_SIZE == "team" %}
  <!-- G17.S: Team Finance Erweiterung für regulierte Branchen -->
  <h3>5. Spezifische Tools für regulierte Branchen</h3>
  <ul>
    <li>
      <strong>Kern-Plattformen &amp; Data Hub</strong> –
      In Finanz- und Compliance-intensiven Umfeldern ist eine zentrale Datenplattform
      essenziell. Sie bündelt Informationen aus verschiedenen Quellen und ermöglicht
      konsistente, nachvollziehbare Auswertungen für interne und externe Prüfungen.
    </li>
    <li>
      <strong>Risiko- &amp; Compliance-Tools</strong> –
      Werkzeuge zur Überwachung regulatorischer Anforderungen (z.&nbsp;B. nach
      BAIT/VAIT/MaRisk-Standards). Funktionsklassen umfassen Risikomonitoring,
      automatisierte Meldewesenberichte und Anomalie-Erkennung in Transaktionsdaten.
    </li>
    <li>
      <strong>Reporting &amp; Kollaboration</strong> –
      Lösungen für revisionssichere Dokumentation, Prüfpfade und interne
      Abstimmungsprozesse. Diese sollten nahtlos in bestehende Workflows
      integrierbar sein und klare Verantwortlichkeiten abbilden.
    </li>
  </ul>
  {% endif %}

  <h3>{% if COMPANY_SIZE == "team" %}6{% else %}5{% endif %}. Einführung in Etappen</h3>
  <p>
    Statt alle Tools gleichzeitig einzuführen, sollte der KI-Stack in überschaubaren
    Etappen aufgebaut werden. Zunächst ein stabiles Fundament aus Assistent,
    Wissensspeicher und Aufgabensteuerung, anschließend ein Formular- und
    Auswertungs-Setup und schließlich gezielte Automationen
    und Governance-Bausteine.
  </p>

  <table class="table tools-priorities">
    <thead>
      <tr>
        <th>Stufe</th>
        <th>Baustein</th>
        <th>Rolle im Prozess</th>
        <th>Empfohlener Zeitpunkt</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>1</td>
        <td>Assistent, Wissensspeicher, Aufgabenverwaltung</td>
        <td>
          Unterstützt die tägliche Arbeit, sichert Wissen und schafft Transparenz.
        </td>
        <td>innerhalb der ersten 30 Tage</td>
      </tr>
      <tr>
        <td>2</td>
        <td>Formular-Tool &amp; Auswertungs-Setup</td>
        <td>
          Macht Daten für {{OFFERING_LABEL}} strukturiert nutzbar und
          ermöglicht KI-gestützte Auswertungen.
        </td>
        <td>Tag 30–60</td>
      </tr>
      <tr>
        <td>3</td>
        <td>Automation &amp; Governance-Bausteine</td>
        <td>
          Reduziert manuelle Zwischenschritte, stärkt Sicherheit und Qualität und macht
          den Gesamtprozess erweiterbar – besonders relevant für wachsende Teams und KMU.
        </td>
        <td>ab rund 60 Tagen</td>
      </tr>
    </tbody>
  </table>

  <p class="small muted">
    Der empfohlene KI-Stack ist bewusst schlank gehalten: Schnell Nutzen für
    {{OFFERING_LABEL}} erzeugen und bei Bedarf schrittweise weitere Bausteine hinzufügen.
    Details zur Einführung → siehe Roadmap.
  </p>
</section>
