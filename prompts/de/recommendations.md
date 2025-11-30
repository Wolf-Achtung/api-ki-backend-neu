Developer:
<!-- recommendations.md – v7.0 PLATIN+ STABILIZED (branch-aware, size-aware, actionable, min 800 WÖRTER)

     ╔══════════════════════════════════════════════════════════════════════════════╗
     ║  KRITISCH: MINDESTLÄNGE = 800 WÖRTER (nicht Zeichen!)                        ║
     ║  Antworte IMMER mit einem VOLLSTÄNDIGEN, AUSFÜHRLICHEN Text.                 ║
     ║  Kurze Antworten sind INAKZEPTABEL und führen zu Validierungsfehlern.        ║
     ╚══════════════════════════════════════════════════════════════════════════════╝

     AUSGABEFORMAT:
       - Antworte ausschließlich mit validem HTML.
       - KEIN <html>, <head> oder <body>. KEINE Markdown-Fences im OUTPUT.

     ZIEL:
       - Erzeuge 5–6 präzise, sofort nutzbare Handlungsempfehlungen.
       - Jede Empfehlung muss vollständig ausformuliert sein:
         Schwerpunkt → Maßnahme → Nutzen → Aufwand → Verantwortlich → Förderchance.
       - Abhängig von Branche, Hauptleistung, Unternehmensgröße und Bundesland.
       - Erstelle zusätzlich eine klare Prioritäten-Tabelle (5–6 Einträge).
       - Verknüpfung mit Roadmap und Business Case.

     INPUT-VARIABLEN (MÜSSEN ALLE im Text verwendet werden!):
       {{BRANCHE_LABEL}}              ← Branche des Unternehmens
       {{UNTERNEHMENSGROESSE_LABEL}}  ← Größenkategorie
       {{HAUPTLEISTUNG}}              ← Kernleistung/Anwendungsbereich
       {{BUNDESLAND_LABEL}}           ← Bundesland für Förderhinweise
       {{COMPANY_SIZE}}               ← "solo", "team", "kmu"

     ╔══════════════════════════════════════════════════════════════════════════════╗
     ║  PFLICHTSTRUKTUR – ALLE ELEMENTE MÜSSEN VOLLSTÄNDIG AUSGEFÜHRT WERDEN!       ║
     ╚══════════════════════════════════════════════════════════════════════════════╝

     TEIL 1: EINLEITUNG (mind. 50-80 Wörter)
       - Kontextualisierung für {{BRANCHE_LABEL}} und {{UNTERNEHMENSGROESSE_LABEL}}
       - Bezug auf {{HAUPTLEISTUNG}}
       - Überleitung zu den Empfehlungen

     TEIL 2: EMPFEHLUNGEN (mind. 5 Empfehlungen, je 100-120 Wörter = mind. 500-600 Wörter)
       JEDE Empfehlung MUSS folgende 6 Elemente enthalten (alle ausführlich!):
       1. <strong>Schwerpunkt:</strong> Was ist das Kernproblem/die Chance? (1-2 Sätze)
       2. <strong>Maßnahme:</strong> Was konkret tun? (2-3 Sätze, sehr spezifisch)
       3. <strong>Nutzen &amp; Wirkung:</strong> Welcher messbare Benefit? (2 Sätze)
       4. <strong>Aufwand &amp; Budget:</strong> Zeit und Kosten, size-aware (1-2 Sätze)
       5. <strong>Verantwortlich:</strong> Wer führt durch? (1 Satz, size-aware)
       6. <strong>Förderchance:</strong> Welche Programme in {{BUNDESLAND_LABEL}}? (1-2 Sätze)

       EMPFEHLUNG 1: Quick Win – Sofort umsetzbar (Standard-Workflow für {{HAUPTLEISTUNG}})
       EMPFEHLUNG 2: Qualitätssicherung – KI-gestützte Konsistenzprüfung
       EMPFEHLUNG 3: Wissensmanagement – Dokumentation & Wissensbasis aufbauen
       EMPFEHLUNG 4: Branchenspezifisch – Use Case passend zu {{BRANCHE_LABEL}}
       EMPFEHLUNG 5: Governance & Sicherheit – Richtlinien und Kontrollen
       EMPFEHLUNG 6 (optional): Skalierung – Nächster Entwicklungsschritt

     TEIL 3: PRIORITÄTEN-TABELLE (mind. 100-150 Wörter)
       - Tabelle mit MINDESTENS 5 Zeilen
       - Spalten: Priorität, Empfehlung, Zeitrahmen, Hauptnutzen
       - Zeitrahmen size-aware:
           SOLO: 0–3 / 3–6 / 6–12 Monate
           TEAM: 0–6 / 6–9 / 9–12 Monate
           KMU: 0–6 / 6–9 / 9–12 Monate
       - Kurzer Abschlussabsatz zur Priorisierung

     ╔══════════════════════════════════════════════════════════════════════════════╗
     ║  ABSOLUTE MINDESTLÄNGE: 800 WÖRTER Gesamttext (ohne HTML-Tags)               ║
     ║  Ziel: 800-1200 Wörter für vollständige, professionelle Empfehlungen         ║
     ║  NIEMALS kürzer als 800 Wörter antworten!                                    ║
     ╚══════════════════════════════════════════════════════════════════════════════╝

     SIZE-AWARE REGELWERK:
       SOLO:
         - Keine Abteilungen/Teams/Bereiche beim Berichtsempfänger selbst.
         - Falls Organisationsstrukturen erwähnt werden (z.B. bei Kunden-Zielgruppen),
           IMMER klar als "auf Kundenseite" markieren.
         - Empfehlungen = realistische, kleine Schritte.
         - Verantwortlich = Inhaber:in / Geschäftsführung.
         - Budget: niedrig bis mittel (zweistellig bis niedriger dreistelliger €/Monat).

       TEAM (2–10):
         - Rollen erlaubt (Teamlead, KI-Owner, Qualitätsverantwortliche).
         - Gemeinsame Workflows, abgestimmte Prozesse.
         - Verantwortlichkeiten klar zuweisen.
         - Budget: mittel (bis niedrige vierstellige Beträge).

       KMU (11–100):
         - Bereichsübergreifende Maßnahmen.
         - Governance, Standards, Dokumentation, Policies.
         - Verantwortliche pro Fachbereich.
         - Budget: kann höher sein, strukturierte Investitionen.

     BRANCHEN-AWARE REGELWERK (aus CONTEXT_BLOCK holen):
       - Marketing/Kreativ: Content-Qualität, Templates, Automatisierung, Brand Guidelines.
       - Beratung/Dienstleistung: Wissensmanagement, Angebotsprozesse, Dokumentation.
       - Finanzen/Versicherung: Compliance, DSGVO, Datengenauigkeit, Audit-Trail.
       - Gesundheit/Pflege: sensible Daten + strenge Dokumentation, Patientendaten.
       - IT/Software: Automatisierung, Code-Assistenz, Modellkontrolle, DevOps.
       - Industrie/Produktion: Datenaufbereitung, Sensorik, Workflow-Optimierung.
       - E-Commerce/Handel: Produktdaten, Textautomatisierung, Qualitätschecks.

     VERBOTEN:
       - Wörter wie „Platzhalter", „Freitextfeld", „TODO", „Beispieltext".
       - Generische Formulierungen ohne konkreten Inhalt.
       - Rohvariablen im sichtbaren Output.
       - Mehrdeutige Aussagen ohne konkrete Handlungsanleitung.
       - Zu kurze Empfehlungen (jede Empfehlung mindestens 80-100 Wörter!).
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
