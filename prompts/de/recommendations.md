Developer:
<!-- recommendations.md – v9.0 PDF-SLIMDOWN-STRICT
     Antworte ausschließlich mit validem HTML. Keine Markdown-Fences.

     **STRIKTE TOKEN-BEGRENZUNG (KRITISCH!):**
     MAXIMAL 500-600 Wörter Output (5 Empfehlungen × 80-100 Wörter + Tabelle).

     STRUKTUR (Pflicht-Elemente):
       1. Kurze Einleitung (30-40 Wörter)
       2. GENAU 5 Empfehlungen, je mit:
          - Schwerpunkt (1 Satz)
          - Maßnahme (1-2 Sätze)
          - Nutzen (1 Satz)
          - Aufwand (1 Satz, size-aware)
       3. Kompakte Prioritäten-Tabelle (5 Zeilen)

     **ANTI-REDUNDANZ (STRIKT!):**
     - KEINE Wiederholung von Quick Wins (wurden dort genannt)
     - KEINE Wiederholung von Roadmap-Inhalten
     - Fokus auf ERGÄNZENDE strategische Empfehlungen

     VARIABLEN:
       {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, {{COMPANY_SIZE}}

     SIZE-AWARE (COMPANY_SIZE):
       solo: Inhaber:in, persönliche Schritte, niedriges Budget
       team: Teamlead/KI-Owner, gemeinsame Workflows, mittleres Budget
       kmu: Fachbereiche, Governance, strukturierte Investitionen
-->

<section class="section recommendations">
  <h2>Handlungsempfehlungen</h2>

  <p>
    Für <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in der Branche <strong>{{BRANCHE_LABEL}}</strong>
    ergeben sich folgende strategische Empfehlungen für <strong>{{HAUPTLEISTUNG}}</strong>.
  </p>

  <ol class="recommendations-list">

    <li>
      <h3>Empfehlung 1: Standard-Workflow etablieren</h3>
      <p><strong>Schwerpunkt:</strong> Einen zentralen KI-gestützten Workflow für {{HAUPTLEISTUNG}} aufbauen.</p>
      <p><strong>Maßnahme:</strong> Klare Input-/Output-Regeln definieren, Qualitätsprüfung integrieren.</p>
      <p><strong>Nutzen:</strong> Direkte Entlastung, konsistente Ergebnisse.</p>
      <p><strong>Aufwand:</strong> {% if COMPANY_SIZE == "solo" %}1-2 Tage{% elif COMPANY_SIZE == "team" %}3-5 Tage{% else %}1-2 Wochen{% endif %}.</p>
    </li>

    <li>
      <h3>Empfehlung 2: Qualitätssicherung systematisieren</h3>
      <p><strong>Schwerpunkt:</strong> KI-gestützte Konsistenzprüfung für Dokumente und Ergebnisse.</p>
      <p><strong>Maßnahme:</strong> Review-Schritt vor Freigabe einführen (Fakten, Ton, Compliance).</p>
      <p><strong>Nutzen:</strong> Weniger Nacharbeit, geringeres Fehlerrisiko.</p>
      <p><strong>Aufwand:</strong> {% if COMPANY_SIZE == "solo" %}1-2 Tage{% elif COMPANY_SIZE == "team" %}3-5 Tage{% else %}1-2 Wochen{% endif %}.</p>
    </li>

    <li>
      <h3>Empfehlung 3: Wissensmanagement aufbauen</h3>
      <p><strong>Schwerpunkt:</strong> Zentrale Wissensbasis für Vorlagen, Standards, Best Practices.</p>
      <p><strong>Maßnahme:</strong> KI-gestützte Bibliothek für wiederkehrende Materialien erstellen.</p>
      <p><strong>Nutzen:</strong> Schnellere Einarbeitung, stabile Ergebnisqualität.</p>
      <p><strong>Aufwand:</strong> {% if COMPANY_SIZE == "solo" %}2-3 Tage{% elif COMPANY_SIZE == "team" %}1 Woche{% else %}2-3 Wochen{% endif %}.</p>
    </li>

    <li>
      <h3>Empfehlung 4: Branchenspezifischen Use Case pilotieren</h3>
      <p><strong>Schwerpunkt:</strong> Ein klar abgegrenzter Pilot-Use-Case aus {{BRANCHE_LABEL}}.</p>
      <p><strong>Maßnahme:</strong> Einen Use Case mit hoher Sichtbarkeit und schnellem ROI umsetzen.</p>
      <p><strong>Nutzen:</strong> Sichtbarer Erfolg, Momentum für weitere Schritte.</p>
      <p><strong>Aufwand:</strong> {% if COMPANY_SIZE == "solo" %}1-3 Tage{% elif COMPANY_SIZE == "team" %}3-7 Tage{% else %}1-3 Wochen{% endif %}.</p>
    </li>

    <li>
      <h3>Empfehlung 5: Governance & Leitplanken definieren</h3>
      <p><strong>Schwerpunkt:</strong> Klare Regeln für KI-Nutzung, Datenschutz, Freigaben.</p>
      <p><strong>Maßnahme:</strong> {% if COMPANY_SIZE == "solo" %}Persönliche Checkliste{% elif COMPANY_SIZE == "team" %}Team-Leitfaden{% else %}Policy-Dokument{% endif %} erstellen.</p>
      <p><strong>Nutzen:</strong> Rechtssicherheit, Vertrauen bei Kund:innen.</p>
      <p><strong>Aufwand:</strong> {% if COMPANY_SIZE == "solo" %}1-2 Tage{% elif COMPANY_SIZE == "team" %}3-5 Tage{% else %}2-4 Wochen{% endif %}.</p>
    </li>

  </ol>

  <h3>Prioritäten-Überblick</h3>
  <table class="table">
    <thead>
      <tr><th>Priorität</th><th>Empfehlung</th><th>Zeitrahmen</th><th>Hauptnutzen</th></tr>
    </thead>
    <tbody>
      <tr><td>1</td><td>Standard-Workflow</td><td>{% if COMPANY_SIZE == "solo" %}0–3 Mon.{% else %}0–6 Mon.{% endif %}</td><td>Entlastung & Qualität</td></tr>
      <tr><td>2</td><td>Qualitätssicherung</td><td>{% if COMPANY_SIZE == "solo" %}3–6 Mon.{% else %}3–9 Mon.{% endif %}</td><td>Weniger Nacharbeit</td></tr>
      <tr><td>3</td><td>Wissensmanagement</td><td>{% if COMPANY_SIZE == "solo" %}6–12 Mon.{% else %}6–9 Mon.{% endif %}</td><td>Stabile Ergebnisse</td></tr>
      <tr><td>4</td><td>Pilot-Use-Case</td><td>{% if COMPANY_SIZE == "kmu" %}9–12 Mon.{% else %}6–12 Mon.{% endif %}</td><td>Sichtbarer Erfolg</td></tr>
      <tr><td>5</td><td>Governance</td><td>{% if COMPANY_SIZE == "solo" %}3–6 Mon.{% else %}6–9 Mon.{% endif %}</td><td>Rechtssicherheit</td></tr>
    </tbody>
  </table>
</section>
