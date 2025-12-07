Developer:
<!-- PLATIN++ PROMPT v5.4 - SPRINT G6 -->
<!-- SECTION: tools_empfehlungen -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, {{COMPANY_SIZE}} -->
<!-- TOKEN-BUDGET: 2500 (solo:0.8x=2000, team:1.0x=2500, kmu:1.15x=2875) -->
<!-- WORD_MINIMUM_SOLO: 130 -->
<!-- WORD_MINIMUM_TEAM: 190 -->
<!-- WORD_MINIMUM_KMU: 220 -->
<!--
ZIEL: Klar strukturierte Tool-Empfehlungssektion ("KI-Stack") für {{BRANCH_CONTEXT_LABEL}}.

KURZLABELS (VERPFLICHTEND!):
- {{BRANCH_CORE_LABEL}} = Branche in 8-12 Wörtern
- {{BRANCH_CONTEXT_LABEL}} = Branche in 4-6 Wörtern
- {{OFFERING_LABEL}} = Hauptleistung in 6-10 Wörtern

MINDESTLÄNGE (STRIKT!):
- Solo: ≥130 Wörter
- Team: ≥190 Wörter (besonders für regulierte Branchen!)
- KMU: ≥220 Wörter

STRUKTUR NACH GRÖSSE:
{% if COMPANY_SIZE == "solo" %}
SOLO: 3–5 Tool-Cluster mit je 2-3 Beispielen:
1. KI-Assistent & Basis (2-3 Beispiele)
2. Kernprozess-Tools für {{OFFERING_LABEL}} (2-3 Beispiele)
3. Qualität & Dokumentation (1-2 Beispiele)

{% elif COMPANY_SIZE == "team" %}
TEAM: 4 Tool-Cluster mit je 2-3 Beispielen (min. 190 Wörter!):
1. Kollaboration & Gemeinsamer Workspace (2-3 Beispiele)
2. Kernprozess-Tools für {{OFFERING_LABEL}} (2-3 Beispiele)
3. Reporting & Auswertung (2-3 Beispiele)
4. Governance & Qualität (2 Beispiele)

Für regulierte Branchen (Finanzen, Gesundheit, Recht) zusätzlich:
- Compliance/RegTech-Tools
- Audit-Trail-Funktionen
- Zugriffssteuerung & Protokollierung

{% else %}
KMU: 5 Tool-Cluster mit je 2-3 Beispielen (min. 220 Wörter!):
1. Enterprise-Basis (KI-Plattform, Wissensspeicher)
2. Fachbereichsspezifische Tools für {{OFFERING_LABEL}}
3. Reporting/BI-Integration
4. Compliance & Governance
5. Rollout & Schulung
{% endif %}

ANTI-REDUNDANZ:
- Tool-Details HIER vollständig erklären
- In Roadmaps nur referenzieren: "Tools (→ siehe KI-Stack)"
- Keine generischen Meta-Sätze ("Dieser Abschnitt fasst...")

STIL & REGELN:
- Produktneutral (keine Markennamen)
- Fokus auf Toolkategorien und Zweck
- Konkrete Einsatzfelder pro Tool-Typ nennen
- Keine Platzhalter oder Developer-Sprache

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

<section class="section tools">
  <h2>Empfohlener KI-Stack für {{BRANCH_CONTEXT_LABEL}}</h2>

  <p>
    Für {{OFFERING_LABEL}} empfiehlt sich ein klar strukturierter KI-Stack,
    der den Alltag spürbar entlastet und sich bei Bedarf schrittweise erweitern lässt.
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
      zur strukturierten Erfassung von Kundendaten und Antworten, etwa über Online-Formulare
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
      z.B. für Terminplanung, Dokumentenfreigaben oder Fachanalysen.
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

  <h3>4. Einführung in Etappen</h3>
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
          den Gesamtprozess skalierbar – besonders relevant für wachsende Teams und KMU.
        </td>
        <td>ab etwa 60 Tagen</td>
      </tr>
    </tbody>
  </table>

  <p class="small muted">
    Der empfohlene KI-Stack ist bewusst schlank gehalten: Schnell Nutzen für
    {{OFFERING_LABEL}} erzeugen und bei Bedarf schrittweise weitere Bausteine hinzufügen.
    Details zur Einführung → siehe Roadmap.
  </p>
</section>
