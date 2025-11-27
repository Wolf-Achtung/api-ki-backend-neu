Developer:
<!-- roadmap_12m.md – v5.0 GOLD STANDARD+ (branch-aware, size-aware, strategic)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     ZIEL:
       - Klare, strategische 12-Monats-Roadmap für KI in {{HAUPTLEISTUNG}}.
       - Nutzt aktiv CONTEXT_BLOCK (Workflows, Pain Points, Daten, Tools).
       - Size-aware Umsetzung für solo/team/kmu.
       - Pro Abschnitt: Ziel + Deliverables + Rollen/Verantwortlichkeit + KPIs.
       - Realistische, planbare Schritte für ein gesamtes Geschäftsjahr.

     VARIABLEN:
       {{BRANCHE_LABEL}}
       {{UNTERNEHMENSGROESSE_LABEL}}
       {{HAUPTLEISTUNG}}
       {{BUNDESLAND_LABEL}}
       COMPANY_SIZE = "solo" | "team" | "kmu"

     SIZE-LOGIK:
       SOLO:
         - Keine Abteilungen/Teams; pragmatische persönliche Routinen; niedrige Komplexität.
       TEAM:
         - Rollen & Abstimmungen; Teamlead + KI-Owner; arbeitsteilige Umsetzung.
       KMU:
         - Bereiche, Governance, dokumentierte Prozesse, skalierbare Rollouts.

     BRANCHEN-LOGIK:
       - Nutze typische Workflows, Pain Points & Daten aus CONTEXT_BLOCK.
       - Marketing/Kreativ = Content, Konsistenz, Freigabeprozesse.
       - Beratung/Dienstleistung = Wissensarbeit, Analysen, Angebotsprozesse.
       - Finanzen/Versicherung = Compliance, Datenqualität, Risikominderung.
       - Gesundheit/Pflege = sensible Daten, Freigaben, Qualität.
       - IT/Software = Automatisierung, Testing, Code-Prozesse.
       - Industrie/Produktion = Sensor-/Prozessdaten, Qualität & harmonisierte Workflows.
       - Handel/E-Commerce = Produktdaten, Textprozesse, Qualitätssicherung.

     VERBOTEN:
       - „Platzhalter“, „TODO“, „Freitext“, Beispieltexte.
       - Rohvariablen im Output.
-->

<section class="section roadmap-12m">
  <h2>12-Monats-Roadmap (Strategische Weiterentwicklung)</h2>

  <p>
    Diese Roadmap zeigt, wie der KI-Einsatz im Bereich
    <strong>{{HAUPTLEISTUNG}}</strong> innerhalb von zwölf Monaten strategisch,
    stabil und nachhaltig ausgebaut werden kann – abgestimmt auf die Möglichkeiten
    eines Unternehmens der Größe <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> und
    die branchenspezifischen Workflows, Pain Points und Daten in
    <strong>{{BRANCHE_LABEL}}</strong>.
  </p>

  <p>
    Sie baut direkt auf die 90-Tage-Phase auf: Erst Stabilisierung, dann Ausweitung
    und schließlich Skalierung und Governance – angepasst an Größe und Branche.
  </p>

  <!-- Q2 -->
  <h3>Q2 (Monate 4–6): Konsolidierung & Stabilisierung</h3>
  <p><strong>Ziel:</strong>
    Die in den ersten 90 Tagen etablierten KI-Workflows stabilisieren und in den
    Regelbetrieb überführen – inklusive Qualität, Datenbasis und Verlässlichkeit.
  </p>

  <p><strong>Deliverables:</strong></p>
  <ul>
    <li>Vollständig dokumentierte Workflows für {{HAUPTLEISTUNG}} (Input → KI → Review → Freigabe).</li>
    <li>Branchenspezifische Qualitätskriterien (abhängig von {{BRANCHE_LABEL}}).</li>
    <li>Best-Practice-Sammlung aus echten Fällen der ersten 90 Tage.</li>
    <li>Kurze Dokumentation zu Datenlage, Risiken, Freigaberegeln.</li>
  </ul>

  <p><strong>Rollen &amp; Verantwortlichkeiten:</strong><br>
    {% if COMPANY_SIZE == "solo" %}
      Persönliche Standardisierung & Routine.
    {% elif COMPANY_SIZE == "team" %}
      Teamlead + KI-Owner + beteiligte Kolleg:innen.
    {% else %}
      Fachbereich + Prozessverantwortliche + Qualitätssicherung.
    {% endif %}
  </p>

  <p><strong>KPIs Q2:</strong><br>
    • Konsistenz +20–40&nbsp;%<br>
    • weniger Korrekturschleifen<br>
    • dokumentierter Regelprozess für {{HAUPTLEISTUNG}}
  </p>

  <!-- Q3 -->
  <h3>Q3 (Monate 7–9): Erweiterung auf neue Use-Cases</h3>
  <p><strong>Ziel:</strong>
    Erfolgreiche Ansätze auf angrenzende Prozesse übertragen – auf Basis branchenspezifischer
    Pain Points und typischer Datenströme.
  </p>

  <p><strong>Deliverables:</strong></p>
  <ul>
    <li>Auswahl der 1–2 wirkungsstärksten neuen Use-Cases innerhalb {{BRANCHE_LABEL}}.</li>
    <li>Erweiterte Templates & Workflows (Qualität, Review, Freigabe).</li>
    <li>Aufbau einer kleinen internen Wissensbibliothek (Do's & Don’ts, Beispiele, Checklisten).</li>
    <li>Regelmäßige Review- und Optimierungszyklen.</li>
  </ul>

  <p><strong>Rollen &amp; Verantwortlichkeiten:</strong><br>
    {% if COMPANY_SIZE == "solo" %}
      Weiterentwicklung persönlicher Routinen & Tools.
    {% elif COMPANY_SIZE == "team" %}
      Teamlead + KI-Owner + Anwender:innen der neuen Use-Cases.
    {% else %}
      Fachbereich + IT + Verantwortliche des Erweiterungsbereichs.
    {% endif %}
  </p>

  <p><strong>KPIs Q3:</strong><br>
    • 1–2 neue Use-Cases produktiv im Einsatz<br>
    • bessere Durchlaufzeiten in angrenzenden Prozessen<br>
    • höhere Ersttrefferquote durch verfeinerte Templates
  </p>

  <!-- Q4 -->
  <h3>Q4 (Monate 10–12): Skalierung & Governance</h3>
  <p><strong>Ziel:</strong>
    KI auf struktureller Ebene verankern – mit klaren Verantwortlichkeiten,
    Qualitätsregeln, Freigaben und datengetriebenem Reporting.
  </p>

  <p><strong>Deliverables:</strong></p>
  <ul>
    <li>Skalierungsstrategie für weitere Teams/Prozesse (je nach Branche: z. B. weitere Content-Steps, Angebotsprozesse, Produktionsdaten, Compliance-Prüfungen).</li>
    <li>Leichtgewichtige Governance-Regeln (Qualität, Datenschutz, Freigabeprozess).</li>
    <li>Regelmäßiges, metrikenbasiertes Reporting (Zeit, Risiko, Qualität, Auslastung).</li>
    <li>Budget- und Investitionsfahrplan für das zweite Jahr.</li>
  </ul>

  <p><strong>Rollen &amp; Verantwortlichkeiten:</strong><br>
    {% if COMPANY_SIZE == "solo" %}
      Persönliche Qualitätsroutinen & dokumentierte Learnings.
    {% elif COMPANY_SIZE == "team" %}
      Teamlead + KI-Owner + Prozessverantwortliche.
    {% else %}
      Bereichsleitung + Management + Datenschutz/IT.
    {% endif %}
  </p>

  <p><strong>KPIs Q4:</strong><br>
    • 2–3 KI-Use-Cases stabil im Regelbetrieb<br>
    • dokumentierte Governance-Strukturen<br>
    • Reporting im Quartalsrhythmus
  </p>

  <h3>Jahresabschluss (Monat 12)</h3>
  <ul>
    <li>Bewertung aller produktiven Use-Cases (Qualität, Risiko, Zeitgewinn, Wirtschaftlichkeit).</li>
    <li>Planung der Roadmap für Jahr&nbsp;2 (Stabilisieren / Ausbauen / Skalieren).</li>
    <li>Abschlussdokumentation aller Workflows & Learnings.</li>
    <li>Prüfung von Fördermitteln in {{BUNDESLAND_LABEL}} (z. B. Modernisierung, Prozessdigitalisierung).</li>
  </ul>

  <p class="small muted">
    Diese 12-Monats-Roadmap macht KI zu einem stabilen, skalierbaren Bestandteil
    der Wertschöpfung eines Unternehmens der Größe <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>.
    Sie schafft Standards, Qualität und messbare Wirkung und bildet die Basis für
    Piloten und Skalierung im Folgejahr.
  </p>
</section>
