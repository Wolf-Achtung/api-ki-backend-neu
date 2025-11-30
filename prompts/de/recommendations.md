Developer:
<!-- recommendations.md – v8.0 PLATIN+ STREAMLINED
     Ziel: 5-6 Empfehlungen mit je 100-120 Wörtern (= 800-1000 Wörter gesamt).
     Antworte ausschließlich mit validem HTML. Keine Markdown-Fences.

     STRUKTUR (Pflicht-Elemente):
       1. Einleitung (50-80 Wörter)
       2. 5-6 Empfehlungen, je mit:
          - Schwerpunkt (1-2 Sätze)
          - Maßnahme (2-3 Sätze, spezifisch)
          - Nutzen & Wirkung (2 Sätze)
          - Aufwand & Budget (1-2 Sätze, size-aware)
          - Verantwortlich (1 Satz, size-aware)
          - Förderchance (1-2 Sätze)
       3. Prioritäten-Tabelle (5 Zeilen)

     VARIABLEN – nutze alle mindestens einmal:
       {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}},
       {{BUNDESLAND_LABEL}}, {{COMPANY_SIZE}}

     SIZE-AWARE (COMPANY_SIZE):
       solo: Inhaber:in, persönliche Schritte, niedriges Budget
       team: Teamlead/KI-Owner, gemeinsame Workflows, mittleres Budget
       kmu: Fachbereiche, Governance, strukturierte Investitionen

     REGELN:
       - Empfehlungen branchenspezifisch und umsetzbar
       - Zeitrahmen size-aware (solo: 0-3/3-6/6-12, team/kmu: 0-6/6-9/9-12)
       - Sachlich, konkret, keine Floskeln
       - Keine Platzhalter, keine Developer-Sprache
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
      <h3>Empfehlung&nbsp;1: Quick Win – Standard-Workflow einführen</h3>
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
      <h3>Empfehlung&nbsp;2: Qualitätssicherung – KI-gestützte Konsistenzprüfung</h3>
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
      <h3>Empfehlung&nbsp;3: Wissensmanagement – Dokumentation &amp; Wissensbasis</h3>
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

    <!-- EMPFEHLUNG 4 – branchenspezifisch -->
    <li>
      <h3>Empfehlung&nbsp;4: Branchenspezifischer Use Case</h3>
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

    <!-- EMPFEHLUNG 5 – Governance & Sicherheit -->
    <li>
      <h3>Empfehlung&nbsp;5: Governance &amp; Sicherheit</h3>
      <p><strong>Schwerpunkt:</strong>
        Klare Richtlinien und Kontrollen für den KI-Einsatz etablieren, um Risiken zu minimieren und Compliance sicherzustellen.
      </p>
      <p><strong>Maßnahme:</strong>
        Erstellung eines kompakten KI-Leitfadens mit Regeln zu Datenschutz, Qualitätsprüfung und Freigabeprozessen. Definition von Verantwortlichkeiten und Eskalationswegen.
      </p>
      <p><strong>Nutzen &amp; Wirkung:</strong>
        Höhere Rechtssicherheit, transparente Prozesse und gestärktes Vertrauen bei Kund:innen und Partnern.
      </p>
      <p><strong>Aufwand &amp; Budget:</strong>
        {% if COMPANY_SIZE == "solo" %}Niedrig – persönliche Checkliste in 1-2 Tagen{% elif COMPANY_SIZE == "team" %}Mittel – Team-Workshop + Dokumentation in 3-5 Tagen{% else %}Mittel bis hoch – strukturierte Policy-Entwicklung in 2-4 Wochen{% endif %}.
      </p>
      <p><strong>Verantwortlich:</strong>
        {% if COMPANY_SIZE == "solo" %}Inhaber:in{% elif COMPANY_SIZE == "team" %}KI-Owner + Teamlead{% else %}Governance-Verantwortliche + Datenschutz/IT{% endif %}.
      </p>
      <p><strong>Förderchance:</strong>
        Beratungsförderung für Datenschutz und IT-Sicherheit in {{BUNDESLAND_LABEL}} prüfen.
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
        <td>Branchenspezifischen KI-Pilot umsetzen</td>
        <td>
          {% if COMPANY_SIZE == "kmu" %}9–12 Monate{% else %}6–12 Monate{% endif %}
        </td>
        <td>Sichtbarer Nutzen & Momentum für Skalierung</td>
      </tr>

      <tr>
        <td>5</td>
        <td>Governance & Sicherheitsrichtlinien etablieren</td>
        <td>
          {% if COMPANY_SIZE == "solo" %}3–6 Monate{% else %}6–9 Monate{% endif %}
        </td>
        <td>Rechtssicherheit & Vertrauen</td>
      </tr>

    </tbody>
  </table>

  <p class="small muted">
    Die Empfehlungen sind so formuliert, dass sie unmittelbar in die Projektplanung übernommen
    werden können und konsistent mit Roadmap, Business Case, Benchmarking und Quick Wins wirken.
  </p>
</section>

<!-- PLATIN+ REINFORCEMENT: Dieser Abschnitt MUSS mindestens 800 Wörter enthalten.
     Prüfe deine Ausgabe: Zähle die Wörter und erweitere jede Empfehlung mit zusätzlichen
     Details zu Maßnahmen, Nutzen und Aufwand, falls die Mindestlänge nicht erreicht wird.
     Kürze NIEMALS – liefere immer vollständige, ausführliche Inhalte. -->
