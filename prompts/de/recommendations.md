Developer:
<!-- PLATIN++ PROMPT v5.4 - SPRINT G5 -->
<!-- SECTION: recommendations -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 600 (solo:0.8x=480, team:1.0x=600, kmu:1.15x=690) -->
<!--
ZIEL: 5 strategische Handlungsempfehlungen für {{OFFERING_LABEL}}.

KURZLABELS (VERPFLICHTEND!):
- {{BRANCH_CORE_LABEL}} = Branche in 8-12 Wörtern
- {{BRANCH_CONTEXT_LABEL}} = Branche in 4-6 Wörtern
- {{OFFERING_LABEL}} = Hauptleistung in 6-10 Wörtern

STRUKTUR (Pflicht-Elemente):
1. Kurze Einleitung (30-40 Wörter)
2. GENAU 5 Empfehlungen, je mit:
   - Schwerpunkt (1 Satz)
   - Maßnahme (1-2 Sätze)
   - Nutzen (1 Satz)
   - Aufwand (1 Satz, size-aware)
3. Kompakte Prioritäten-Tabelle (5 Zeilen)

ANTI-REDUNDANZ (STRIKT!):
- KEINE Wiederholung von Quick Wins (→ siehe Abschnitt Quick Wins)
- KEINE Wiederholung von Roadmap-Inhalten (→ siehe Roadmap)
- Fokus auf ERGÄNZENDE strategische Empfehlungen
- Bei Überschneidung: Querverweis nutzen

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: Inhaber:in, persönliche Schritte, niedriges Budget
- team: Teamlead/KI-Owner, gemeinsame Workflows, mittleres Budget
- kmu: Fachbereiche, Governance, strukturierte Investitionen

SPRINT G5 - PERSONA HARD-GUARDS (STRIKT!):
{% if COMPANY_SIZE == "solo" %}
SOLO-MODUS - VERBOTEN:
- "Team/Teams" → "Kapazität/Kapazitäten"
- "Abteilung/Fachbereich" → nicht verwenden
- "Mitarbeiter" → "externe Unterstützung"
{% elif COMPANY_SIZE == "team" %}
TEAM-MODUS - VERBOTEN:
- "Abteilung/Fachbereich" → "Bereich"
- "Division/Unit/Konzern" → nicht verwenden
- Solo-Begriffe: "Einzelperson", "allein"
{% else %}
KMU-MODUS - VERBOTEN:
- "Konzern/Division/Unit" → nicht verwenden
- Solo-Begriffe: "Einzelperson", "allein"
{% endif %}
-->

<section class="section recommendations">
  <h2>Handlungsempfehlungen</h2>

  <p>
    Für {{BRANCH_CONTEXT_LABEL}} ergeben sich folgende strategische Empfehlungen
    für <strong>{{OFFERING_LABEL}}</strong>.
  </p>

  <ol class="recommendations-list">

    <li>
      <h3>Empfehlung 1: Standard-Workflow etablieren</h3>
      <p><strong>Schwerpunkt:</strong> Einen zentralen KI-gestützten Workflow für {{OFFERING_LABEL}} aufbauen.</p>
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
      <p><strong>Schwerpunkt:</strong> Ein klar abgegrenzter Pilot-Use-Case aus {{BRANCH_CONTEXT_LABEL}}.</p>
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


<!-- ZERO-LEAK POLICY (N4.6) -->
<!--
VERBOTEN – NIEMALS VERWENDEN:
- Keine Fragen an den Leser ("Haben Sie Fragen?", "Möchten Sie mehr erfahren?")
- Keine Aufforderungen ("Wenn Sie möchten...", "Kontaktieren Sie uns...")
- Keine Assistenten-Sprache ("Ich kann Ihnen helfen...", "Gerne erkläre ich...")
- Keine Angebote ("Bei Bedarf...", "Falls gewünscht...")
- Keine interaktiven Elemente ("Klicken Sie hier...", "Wählen Sie...")
- Keine Platzhalter ("[Hier einfügen]", "{{VARIABLE}}" außer definierten)
- Keine Meta-Kommentare ("Dieser Abschnitt...", "Im Folgenden...")

Der Output ist ein FINALER REPORT-ABSCHNITT, kein Gespräch.
-->
