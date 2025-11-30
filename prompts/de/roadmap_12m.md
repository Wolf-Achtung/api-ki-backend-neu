Developer:
<!-- roadmap_12m.md – v7.0 PLATIN+ STREAMLINED
     Ziel: 4 Quartale mit je 200-250 Wörtern (= 900-1100 Wörter gesamt).
     Antworte ausschließlich mit validem HTML. Keine Markdown-Fences.

     STRUKTUR (4 Quartale):
       Q1 (Monate 1-3): Grundlagen & Quick Wins
       Q2 (Monate 4-6): Pilotierung & Integration
       Q3 (Monate 7-9): Ausbau & Skalierung
       Q4 (Monate 10-12): Optimierung & Strategie 2.0

     Pro Quartal PFLICHT:
       - Ziel (1-2 Sätze)
       - Deliverables (4+ Bullets)
       - Rollen (size-aware)
       - KPI (2-3 messbare Kennzahlen)
       - Governance/Sicherheit (1-2 Bullets)

     VARIABLEN:
       {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, COMPANY_SIZE

     SIZE-AWARE (COMPANY_SIZE):
       solo: persönliche Entwicklung, eigene Automatisierung, keine Teams/Bereiche
       team: Rollen, Team-Koordination, gemeinsame Prozesse
       kmu: Fachbereiche, Governance, Skalierung, Pilotflächen

     REGELN:
       - Branchenspezifische Workflows aus CONTEXT_BLOCK nutzen
       - Governance-Elemente in jedem Quartal
       - Sachlich, konkret, keine Floskeln
       - Keine Platzhalter, keine Developer-Sprache
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
    <p><strong>KPI:</strong> 2–3 Quick Wins produktiv, erste Zeitersparnis messbar (min. 10%), Qualitätskriterien definiert.</p>
    <p><strong>Governance &amp; Sicherheit:</strong>
      {% if COMPANY_SIZE == "solo" %}
        Persönliche Checkliste für KI-Output-Prüfung erstellen, Datenschutz-Basics dokumentieren.
      {% elif COMPANY_SIZE == "team" %}
        Team-Regeln für KI-Nutzung vereinbaren, Review-Prozess für kritische Outputs definieren.
      {% else %}
        KI-Richtlinie (Draft) erstellen, Datenschutz-Folgenabschätzung für Pilotprojekte durchführen.
      {% endif %}
    </p>
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
    <p><strong>KPI:</strong> Stabile Workflows produktiv, Monitoring etabliert, messbare Qualitätsverbesserung (min. 20% Zeitersparnis).</p>
    <p><strong>Governance &amp; Sicherheit:</strong>
      {% if COMPANY_SIZE == "solo" %}
        Regelmäßiger Selbst-Audit (monatlich), Dokumentation aller KI-gestützten Prozesse.
      {% elif COMPANY_SIZE == "team" %}
        Quartals-Review mit Team, Incident-Prozess für KI-Fehler definieren, Schulungsmaterial erstellen.
      {% else %}
        Governance-Board einrichten, Audit-Trail für kritische Entscheidungen, Compliance-Checks formalisieren.
      {% endif %}
    </p>
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
    <p><strong>KPI:</strong> 5–8 Use Cases produktiv, ROI nachweisbar (min. 30% des Business Case), Governance-Strukturen etabliert.</p>
    <p><strong>Governance &amp; Sicherheit:</strong>
      {% if COMPANY_SIZE == "solo" %}
        Jährlicher Sicherheits-Check, Backup-Strategie für KI-generierte Inhalte, Notfallplan bei Tool-Ausfällen.
      {% elif COMPANY_SIZE == "team" %}
        Halbjährliches Governance-Review, Risiko-Register aktualisieren, Schulungs-Refresher für alle.
      {% else %}
        KI-Richtlinie finalisieren und kommunizieren, externes Audit vorbereiten, Risiko-Management formalisieren.
      {% endif %}
    </p>
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
    <p><strong>KPI:</strong> Vollständiger Jahresreview dokumentiert, Roadmap 2.0 priorisiert, Budget für Jahr 2 gesichert, ROI erreicht.</p>
    <p><strong>Governance &amp; Sicherheit:</strong>
      {% if COMPANY_SIZE == "solo" %}
        Jahres-Audit durchführen, Compliance-Status dokumentieren, Learnings für Roadmap 2.0 aufbereiten.
      {% elif COMPANY_SIZE == "team" %}
        Team-Retrospektive zu Governance, Richtlinien-Update, Lessons Learned dokumentieren und teilen.
      {% else %}
        Management-Report zu KI-Governance, Compliance-Zertifizierung evaluieren, strategische Risiko-Bewertung für Jahr 2.
      {% endif %}
    </p>
  </div>

  <p class="small muted">
    Diese 12-Monats-Roadmap schafft die Grundlage für eine nachhaltige, strategisch verankerte
    KI-Nutzung in <strong>{{HAUPTLEISTUNG}}</strong>. Sie verbindet schnelle operative Erfolge
    mit langfristiger strategischer Entwicklung und bereitet die Skalierung für Jahr 2 vor.
  </p>
</section>
