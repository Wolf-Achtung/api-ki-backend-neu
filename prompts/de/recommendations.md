Developer:
<!-- recommendations.md – v5.0 GOLD STANDARD+ (branch-aware, size-aware, actionable)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences im OUTPUT.

     ZIEL:
       - Erzeuge 3–6 präzise, sofort nutzbare Handlungsempfehlungen.
       - Jede Empfehlung muss vollständig ausformuliert sein:
         Problem → Maßnahme → Nutzen → Aufwand → Verantwortlich → Förderchance.
       - Abhängig von Branche, Hauptleistung, Unternehmensgröße und Bundesland.
       - Erstelle zusätzlich eine klare Prioritäten-Tabelle (3–6 Einträge).

     INPUT-VARIABLEN:
       {{BRANCHE_LABEL}}
       {{UNTERNEHMENSGROESSE_LABEL}}
       {{HAUPTLEISTUNG}}
       {{BUNDESLAND_LABEL}}
       {{COMPANY_SIZE}}   // "solo", "team", "kmu", durch PromptEnhancer gesetzt

     SIZE-AWARE REGELWERK:
       SOLO:
         - Keine Abteilungen/Teams/Bereiche.
         - Empfehlungen = realistische, kleine Schritte.
         - Verantwortlich = Inhaber:in / Geschäftsführung.
         - Budget klein halten.

       TEAM (2–10):
         - Rollen erlaubt (Teamlead, KI-Owner).
         - Gemeinsame Workflows, abgestimmte Prozesse.
         - Verantwortlichkeiten klar zuweisen.

       KMU (11–100):
         - Bereichsübergreifende Maßnahmen.
         - Governance, Standards, Dokumentation.
         - Verantwortliche pro Fachbereich.

     BRANCHEN-AWARE REGELWERK (aus CONTEXT_BLOCK holen):
       - Marketing/Kreativ: Content-Qualität, Templates, Automatisierung.
       - Beratung/Dienstleistung: Wissensmanagement, Angebotsprozesse, Dokumentation.
       - Finanzen/Versicherung: Compliance, DSGVO, Datengenauigkeit.
       - Gesundheit/Pflege: sensible Daten + strenge Dokumentation.
       - IT/Software: Automatisierung, Code-Assistenz, Modellkontrolle.
       - Industrie/Produktion: Datenaufbereitung, Sensorik, Workflow-Optimierung.
       - E-Commerce/Handel: Produktdaten, Textautomatisierung, Qualitätschecks.
       - Laufende Tools/Workflows/Pain Points sollen in den Empfehlungen berücksichtigt werden.

     OUTPUT-QUALITÄT:
       - 3–6 Empfehlungen, keine Platzhalter, keine Beispielmarker.
       - 3–5 Sätze pro Empfehlung.
       - Keine Wiederholungen, keine Floskeln.
       - Klare geschäftliche Wirkung.

     PRIORITÄTEN-TABELLE:
       - 3–6 Einträge.
       - Jede Zeile = konkrete Kurzform der obigen Empfehlungen.
       - Zeitrahmen size-aware:
           SOLO: eher 0–3 / 3–6 / 6–12 Monate
           TEAM: 0–6 / 6–9 / 9–12 Monate
           KMU: 0–6 / 6–9 / 9–12 Monate

     VERBOTEN:
       - Wörter wie „Platzhalter“, „Freitextfeld“, „TODO“.
       - „Titel der Empfehlung …“ oder generische Mustertexte.
       - Rohvariablen im sichtbaren Output.
       - Mehrdeutige Aussagen ohne konkrete Handlungsanleitung.
-->

<section class="section recommendations">
  <h2>Handlungsempfehlungen – Ihre nächsten Schritte mit KI</h2>

  <p>
    Für ein Unternehmen in der Branche <strong>{{BRANCHE_LABEL}}</strong> mit der Größe
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> ergeben sich mehrere unmittelbar
    realisierbare Hebel, um KI im Prozess <strong>{{HAUPTLEISTUNG}}</strong> wirksam
    einzusetzen. Die folgenden Empfehlungen sind priorisiert, praxisnah und auf
    realistische Ressourcen abgestimmt.
  </p>

  <ol class="recommendations-list">

    <!-- EMPFEHLUNG 1 – branch- & size-aware -->
    <li>
      <h3>Empfehlung&nbsp;1</h3>
      <p><strong>Schwerpunkt:</strong> Verbesserung eines zentralen, wiederkehrenden Schritts in {{HAUPTLEISTUNG}}, der laut branchentypischen Workflows häufig Zeit bindet.</p>
      <p><strong>Maßnahme:</strong>
        Einführung eines KI-gestützten Standard-Workflows (z.&nbsp;B. Analyse, Textentwurf, Qualitätscheck) mit klaren Regeln für Eingaben und Prüfschritte.
      </p>
      <p><strong>Nutzen &amp; Wirkung:</strong>
        Direkt messbare Entlastung, höhere Konsistenz und stabilere Qualität, insbesondere bei schwankender Auslastung.
      </p>
      <p><strong>Aufwand &amp; Budget:</strong>
        Niedrig – realisierbar in wenigen Tagen; Toolkosten abhängig von genutzter Plattform (typ. zweistelliger bis niedriger dreistelliger Bereich/Monat).
      </p>
      <p><strong>Verantwortlich:</strong>
        {% if COMPANY_SIZE == "solo" %}Inhaber:in{% elif COMPANY_SIZE == "team" %}Teamlead oder KI-Owner{% else %}Fachbereich + verantwortliche Leitung{% endif %}.
      </p>
      <p><strong>Förderchance:</strong>
        Je nach Bundesland {{BUNDESLAND_LABEL}} bestehen häufig Zuschussprogramme für digitale Prozessoptimierung (Machbarkeit abhängig vom Fördertopf).
      </p>
    </li>

    <!-- EMPFEHLUNG 2 -->
    <li>
      <h3>Empfehlung&nbsp;2</h3>
      <p><strong>Schwerpunkt:</strong>
        KI-gestützte Konsistenzprüfung für Dokumente, Inhalte oder Datenstrukturen, abgestimmt auf branchentypische Anforderungen.
      </p>
      <p><strong>Maßnahme:</strong>
        Einrichten eines automatisierten Review-Schritts (z.&nbsp;B. Faktencheck, Tonalität, Markenrichtlinien, Compliance), der vor Freigabe ausgeführt wird.
      </p>
      <p><strong>Nutzen &amp; Wirkung:</strong>
        Weniger Nachbearbeitung, geringeres Risiko von Fehlern, stabilere Qualität über mehrere Aufträge hinweg.
      </p>
      <p><strong>Aufwand &amp; Budget:</strong>
        Mittel – 2–5 Tage Setup; Lizenzen abhängig von Nutzerzahl.
      </p>
      <p><strong>Verantwortlich:</strong>
        {% if COMPANY_SIZE == "solo" %}Inhaber:in{% elif COMPANY_SIZE == "team" %}Teamlead bzw. Qualitätsverantwortliche{% else %}Qualitätsmanagement + Fachbereich{% endif %}.
      </p>
      <p><strong>Förderchance:</strong>
        In mehreren Bundesländern bestehen Förderprogramme für Qualitäts- und Effizienzsteigerungen (Prüfung im Rahmen des Reports empfohlen).
      </p>
    </li>

    <!-- EMPFEHLUNG 3 -->
    <li>
      <h3>Empfehlung&nbsp;3</h3>
      <p><strong>Schwerpunkt:</strong>
        Dokumentation & Wissensmanagement verbessern – ein typisches Pain Point laut Branchenkontext.
      </p>
      <p><strong>Maßnahme:</strong>
        Aufbau einer KI-gestützten Wissensbibliothek (z.&nbsp;B. Vorlagen, Standards, Checklisten), die Arbeitsmaterial zentralisiert und vereinfacht.
      </p>
      <p><strong>Nutzen &amp; Wirkung:</strong>
        Schnellere Einarbeitung, höhere Ersttrefferquote, weniger Rückfragen und konsistentere Ergebnisse im Tagesgeschäft.
      </p>
      <p><strong>Aufwand &amp; Budget:</strong>
        Niedrig bis mittel – abhängig vom vorhandenen Material; laufende Kosten gering.
      </p>
      <p><strong>Verantwortlich:</strong>
        {% if COMPANY_SIZE == "solo" %}Inhaber:in{% elif COMPANY_SIZE == "team" %}KI-Owner oder Teamlead{% else %}Wissensmanagement / Prozessverantwortliche{% endif %}.
      </p>
      <p><strong>Förderchance:</strong>
        Wissens- und Prozessdigitalisierung ist in vielen Ländern förderfähig; Prüfung für {{BUNDESLAND_LABEL}} empfohlen.
      </p>
    </li>

    <!-- EMPFEHLUNG 4 – optionaler vierter Block -->
    <li>
      <h3>Empfehlung&nbsp;4</h3>
      <p><strong>Schwerpunkt:</strong> Ein branchenspezifischer Use Case aus dem CONTEXT_BLOCK (z.&nbsp;B. Content-Automation, Datenanalyse, Compliance, Produktionsoptimierung).</p>
      <p><strong>Maßnahme:</strong>
        Pilotierung eines einmaligen, klar abgegrenzten KI-Use-Cases, der hohe Sichtbarkeit und schnellen ROI verspricht.
      </p>
      <p><strong>Nutzen &amp; Wirkung:</strong>
        Sichtbarer Nutzen unmittelbar im Alltag, Momentum für weitere Digitalisierungsschritte.
      </p>
      <p><strong>Aufwand &amp; Budget:</strong>
        Abhängig von Größe: 
        {% if COMPANY_SIZE == "solo" %}1–3 Tage{% elif COMPANY_SIZE == "team" %}3–7 Tage{% else %}1–3 Wochen inkl. Abstimmung{% endif %}.
      </p>
      <p><strong>Verantwortlich:</strong>
        {% if COMPANY_SIZE == "solo" %}Inhaber:in{% elif COMPANY_SIZE == "team" %}Pilotverantwortliche:r + Team{% else %}Projektleitung + Fachbereich{% endif %}.
      </p>
      <p><strong>Förderchance:</strong>
        Viele Förderprogramme priorisieren Pilot-Use-Cases mit klarer Zielsetzung.
      </p>
    </li>

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

      <tr>
        <td>1</td>
        <td>Standard-Workflow für {{HAUPTLEISTUNG}} einführen</td>
        <td>
          {% if COMPANY_SIZE == "solo" %}0–3 Monate{% else %}0–6 Monate{% endif %}
        </td>
        <td>Sofortige Entlastung & Qualitätssteigerung</td>
      </tr>

      <tr>
        <td>2</td>
        <td>KI-gestützte Konsistenz- & Qualitätsprüfung etablieren</td>
        <td>
          {% if COMPANY_SIZE == "solo" %}3–6 Monate{% else %}3–9 Monate{% endif %}
        </td>
        <td>Weniger Nacharbeit & geringeres Risiko</td>
      </tr>

      <tr>
        <td>3</td>
        <td>Wissensbibliothek/Standards zentralisieren</td>
        <td>
          {% if COMPANY_SIZE == "solo" %}6–12 Monate{% else %}6–9 Monate{% endif %}
        </td>
        <td>Schnellere Einarbeitung & stabile Ergebnisse</td>
      </tr>

      <tr>
        <td>4</td>
        <td>Klar definierten KI-Pilot umsetzen</td>
        <td>
          {% if COMPANY_SIZE == "kmu" %}9–12 Monate{% else %}6–12 Monate{% endif %}
        </td>
        <td>Sichtbarer Nutzen & Momentum für Skalierung</td>
      </tr>

    </tbody>
  </table>

  <p class="small muted">
    Die Empfehlungen sind so formuliert, dass sie unmittelbar in die Projektplanung übernommen
    werden können und konsistent mit Roadmap, Business Case, Benchmarking und Quick Wins wirken.
  </p>
</section>
