Developer:
<!-- roadmap_12m.md – v5.0 GOLD STANDARD+ (branch-aware, size-aware, context-integrated)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>; KEINE Markdown-Fences im OUTPUT.

     ZIEL:
       - Erzeuge eine strategische, branchenspezifische 12-Monats-Roadmap für {{HAUPTLEISTUNG}}.
       - Nutze aktiv den CONTEXT_BLOCK (Workflows, Pain Points, Tools, Daten).
       - Size-aware Umsetzung für solo/team/kmu.
       - Jede Phase (Quartal) enthält: Ziel, Deliverables, Rollen, KPI.
       - 4 Quartale (Q1–Q4).

     VARIABLEN:
       {{BRANCHE_LABEL}}
       {{UNTERNEHMENSGROESSE_LABEL}}
       {{HAUPTLEISTUNG}}
       COMPANY_SIZE ∈ {"solo","team","kmu"}

     SIZE-AWARE:
       SOLO:
         - Fokus: persönliche Entwicklung, Angebotsausbau, eigene Automatisierung.
         - Keine Teams, keine Abteilungen, keine "Bereiche".
       TEAM:
         - Fokus: Rollen, Team-Koordination, gemeinsame Prozesse, Wissenstransfer.
       KMU:
         - Fokus: Fachbereiche, Governance, Skalierung, Pilotflächen.

     BRANCHEN-AWARE (verbindlich):
       - Verwende typische Workflows, Datenarten, Tools & Pain Points aus CONTEXT_BLOCK.
       - Marketing/Kreativ: Content-Pipelines, Kampagnenmanagement, Asset-Verwaltung.
       - Beratung/Dienstleistung: Wissensmanagement, Angebotserstellung, Dokumentation.
       - Finanzen/Versicherung: Compliance, Datenvalidierung, Risikoanalyse.
       - Gesundheit/Pflege: sensible Daten, Qualitätssicherung, Freigabeprozesse.
       - IT/Software: Code-Assistenz, Automatisierung, Testing & Deployment.
       - Industrie/Produktion: Sensor-/Prozessdaten, Qualitätskontrollen, Wartung.
       - E-Commerce/Handel: Produktdaten, Feed-Management, Textautomatisierung.

     VERBOTEN:
       - "TODO", "Freitextfeld", generische Formulierungen ohne Substanz.
       - Rohvariablen im sichtbaren Output.
       - Bei SOLO: keine "Abteilungen", "Teams", "Bereiche" (nur persönliche Formulierungen).
-->

<section class="section roadmap-12m">
  <h2>Strategische 12-Monats-Roadmap</h2>

  <p>
    Diese Roadmap zeigt, wie ein Unternehmen der Größe <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>
    innerhalb eines Jahres KI-gestützte Arbeitsweisen im Bereich
    <strong>{{HAUPTLEISTUNG}}</strong> nachhaltig etabliert und ausbaut. Sie baut auf den
    Erfahrungen der ersten 90 Tage auf, nutzt branchentypische Workflows der Branche
    <strong>{{BRANCHE_LABEL}}</strong> und verbindet schnelle Erfolge mit strategischer Tiefe.
  </p>

  <div class="roadmap-phase">
    <h3>Q1 (Monate 1–3): Grundlagen schaffen & Quick Wins realisieren</h3>
    <p><strong>Ziel:</strong> Solide Basis für KI-Nutzung legen und erste messbare Erfolge erzielen.</p>
    <p><strong>Deliverables:</strong></p>
    <ul>
      <li>Definition von 3–5 priorisierten Use Cases für {{HAUPTLEISTUNG}} mit klarem Wirkungspotenzial.</li>
      <li>Aufbau einer Prompt-Bibliothek mit 10–15 dokumentierten Beispielen aus {{BRANCHE_LABEL}}.</li>
      <li>Implementierung von 2–3 Quick Wins mit direkter Zeitersparnis (10–25 % im Zielbereich).</li>
      <li>Erste Qualitätsstandards und Freigabeprozesse für KI-Output etablieren.</li>
    </ul>
    <p><strong>Rollen &amp; Verantwortlichkeiten:</strong><br>
      {% if COMPANY_SIZE == "solo" %}
        Persönliche Umsetzung, Dokumentation eigener Workflows, Self-Review-Prozesse etablieren.
      {% elif COMPANY_SIZE == "team" %}
        KI-Owner + direkt Beteiligte, gemeinsame Qualitätsdefinition, Wissenstransfer im Team.
      {% else %}
        Fachbereich + Prozessverantwortliche + IT/Datenschutz, bereichsübergreifende Abstimmung.
      {% endif %}
    </p>
    <p><strong>KPI:</strong> 2–3 Quick Wins produktiv, erste Zeitersparnis messbar, Qualitätskriterien definiert.</p>
  </div>

  <div class="roadmap-phase">
    <h3>Q2 (Monate 4–6): Pilotierung & Workflow-Integration</h3>
    <p><strong>Ziel:</strong> KI-gestützte Prozesse in den Arbeitsalltag integrieren und verstetigen.</p>
    <p><strong>Deliverables:</strong></p>
    <ul>
      <li>Etablierung stabiler Workflows für die wichtigsten Use Cases (Input → KI → Review → Freigabe).</li>
      <li>Erweiterung der Prompt-Bibliothek auf 25–30 praxiserprobte Beispiele.</li>
      <li>Kontinuierliches Monitoring: Zeitersparnis, Qualität, Fehlerquoten, Konsistenz dokumentieren.</li>
      <li>Schulungs- und Onboarding-Materialien für neue Use Cases erstellen.</li>
    </ul>
    <p><strong>Rollen &amp; Verantwortlichkeiten:</strong><br>
      {% if COMPANY_SIZE == "solo" %}
        Eigene Workflow-Optimierung, regelmäßige Selbstreflexion, Dokumentation von Learnings.
      {% elif COMPANY_SIZE == "team" %}
        Team-Koordination, gemeinsame Reviews, Wissensaustausch, Rolle "KI-Koordinator" definieren.
      {% else %}
        Fachbereiche + QS-Verantwortliche, Prozessharmonisierung, erste Governance-Strukturen.
      {% endif %}
    </p>
    <p><strong>KPI:</strong> Stabile Workflows produktiv, Monitoring etabliert, messbare Qualitätsverbesserung.</p>
  </div>

  <div class="roadmap-phase">
    <h3>Q3 (Monate 7–9): Ausbau & Skalierung</h3>
    <p><strong>Ziel:</strong> Erfolgreiche Workflows multiplizieren und neue Anwendungsbereiche erschließen.</p>
    <p><strong>Deliverables:</strong></p>
    <ul>
      <li>Ausbau auf 5–8 produktive Use Cases mit nachweisbarem ROI.</li>
      {% if COMPANY_SIZE == "solo" %}
      <li>Erweiterung des eigenen Leistungsportfolios durch KI-gestützte Angebote.</li>
      <li>Optimierung persönlicher Automatisierungen und Tool-Integration.</li>
      {% elif COMPANY_SIZE == "team" %}
      <li>Rollout bewährter Workflows auf weitere Teammitglieder und Aufgabenbereiche.</li>
      <li>Definition von Verantwortlichkeiten und Zuständigkeiten für KI-Prozesse im Team.</li>
      {% else %}
      <li>Pilotierung in weiteren Fachbereichen, Identifikation von Synergien und Best Practices.</li>
      <li>Governance-Rahmen definieren: Richtlinien, Freigabeprozesse, Compliance-Checks.</li>
      {% endif %}
      <li>Aufbau systematischer Erfolgsmessung (Dashboard, KPIs, Trendanalysen).</li>
    </ul>
    <p><strong>Rollen &amp; Verantwortlichkeiten:</strong><br>
      {% if COMPANY_SIZE == "solo" %}
        Strategische Weiterentwicklung des eigenen Geschäftsmodells, Kooperationspartner evaluieren.
      {% elif COMPANY_SIZE == "team" %}
        Teamleitung + KI-Koordinator, Skill-Entwicklung fördern, kontinuierliches Team-Learning.
      {% else %}
        Bereichsleitung + Governance-Verantwortliche + Controlling, strategische Steuerung.
      {% endif %}
    </p>
    <p><strong>KPI:</strong> 5–8 Use Cases produktiv, ROI nachweisbar, Governance-Strukturen etabliert.</p>
  </div>

  <div class="roadmap-phase">
    <h3>Q4 (Monate 10–12): Optimierung & strategische Weiterentwicklung</h3>
    <p><strong>Ziel:</strong> KI-Nutzung optimieren, Learnings konsolidieren und Roadmap 2.0 vorbereiten.</p>
    <p><strong>Deliverables:</strong></p>
    <ul>
      <li>Systematische Auswertung aller Use Cases: Wirkung, Effizienz, Risiken, Optimierungspotenziale.</li>
      <li>Finalisierung der Governance- und Compliance-Strukturen (Leitlinien, Audit-Prozesse, Verantwortlichkeiten).</li>
      <li>Strategische Roadmap 2.0 für Jahr 2: Priorisierung nächster Use Cases, Budget, Ressourcen.</li>
      {% if COMPANY_SIZE == "solo" %}
      <li>Bewertung des eigenen KI-Reifegrads und Entscheidung über strategische Investitionen.</li>
      {% elif COMPANY_SIZE == "team" %}
      <li>Team-Retrospektive: Learnings dokumentieren, Best Practices konsolidieren, Skills weiterentwickeln.</li>
      {% else %}
      <li>Management-Review: Strategische Entscheidung über Ausbaustufen, Integration, Automatisierung.</li>
      {% endif %}
      <li>Aufbau eines strukturierten Change-Management-Ansatzes für kontinuierliche Verbesserung.</li>
    </ul>
    <p><strong>Rollen &amp; Verantwortlichkeiten:</strong><br>
      {% if COMPANY_SIZE == "solo" %}
        Geschäftsführung, strategische Neuausrichtung, ggf. externe Expertise einbeziehen.
      {% elif COMPANY_SIZE == "team" %}
        Führung + Team, gemeinsame strategische Planung, Ressourcenallokation für Jahr 2.
      {% else %}
        Management + Bereichsleitungen + Controlling, Budget-Freigabe, strategische Weichenstellung.
      {% endif %}
    </p>
    <p><strong>KPI:</strong> Vollständiger Jahresreview dokumentiert, Roadmap 2.0 priorisiert, Budget für Jahr 2 gesichert.</p>
  </div>

  <p class="small muted">
    Diese 12-Monats-Roadmap schafft die Grundlage für eine nachhaltige, strategisch verankerte
    KI-Nutzung in <strong>{{HAUPTLEISTUNG}}</strong>. Sie verbindet schnelle operative Erfolge
    mit langfristiger strategischer Entwicklung und bereitet die Skalierung für Jahr 2 vor.
  </p>
</section>
