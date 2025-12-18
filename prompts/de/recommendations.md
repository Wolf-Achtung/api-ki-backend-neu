Developer:
<!-- PLATIN++ PROMPT v5.4 - SPRINT G5 -->
<!-- SECTION: recommendations -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 600 (solo:0.8x=480, team:1.0x=600, kmu:1.15x=690) -->
<!--
=============================================================================
ZIEL (CONTENT QUALITY PACK v7.0): MUSS vs. OPTIONEN klar trennen
=============================================================================

KURZLABELS (VERPFLICHTEND!):
- {{BRANCH_CORE_LABEL}} = Branche in 8-12 Wörtern
- {{BRANCH_CONTEXT_LABEL}} = Branche in 4-6 Wörtern
- {{OFFERING_LABEL}} = Hauptleistung in 6-10 Wörtern

=============================================================================
STRUKTUR v7.0 — MUSS vs. OPTIONEN (PFLICHT!):
=============================================================================

ABSCHNITT 1: MUSS-MAßNAHMEN (genau 3 Punkte)
- Nummeriert 1-3
- Pro Punkt: 1 Satz Maßnahme + 1 Kurzsatz "Warum jetzt?" (7-10 Wörter)
- Format: "<strong>1. [Maßnahme]</strong> – [Warum jetzt in 7-10 Wörtern]"
- Beispiel: "<strong>1. Minimal-Stack festlegen</strong> – Klarheit vor Komplexität schafft Handlungsfähigkeit."
- KEINE Detailerklärungen in diesem Abschnitt

ABSCHNITT 2: OPTIONEN (für später / Phase 2-3)
- Weitere 2-4 Empfehlungen als OPTIONEN gekennzeichnet
- Explizit als "später" oder "Phase 2/3" markieren
- Kürzere Beschreibung als bei MUSS

PRIORITÄTEN-TABELLE:
- Kompakte Tabelle mit allen Empfehlungen
- Spalten: Priorität | Empfehlung | Zeitrahmen | Hauptnutzen
- MUSS-Empfehlungen in Zeile 1-3, OPTIONEN ab Zeile 4

=============================================================================
STILREGELN v7.0:
=============================================================================
- Durchschnittliche Satzlänge: maximal 18-22 Wörter
- Mehr Verben, weniger Nominalstil
- VERBOTEN: "fundamental", "exponentiell", "ganzheitlich", "holistisch"
- Jede Empfehlung braucht eine klare Handlungsaussage

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
    Für {{BRANCH_CONTEXT_LABEL}} mit Fokus auf <strong>{{OFFERING_LABEL}}</strong>
    gelten folgende priorisierte Empfehlungen.
  </p>

  <!-- ABSCHNITT 1: MUSS-MAßNAHMEN (genau 3) -->
  <h3>MUSS – Sofort umsetzen</h3>
  <ol class="recommendations-muss">
    <li>
      <strong>Minimal-Stack festlegen</strong> – Klarheit vor Komplexität schafft Handlungsfähigkeit.
      <p class="muss-detail">1 zentrales KI-Tool, 1 Ablageort, keine parallelen Experimente.</p>
    </li>
    <li>
      <strong>Ersten Standard-Workflow etablieren</strong> – Ohne Prozess keine messbare Verbesserung.
      <p class="muss-detail">Input → KI-Entwurf → Review → Freigabe für {{OFFERING_LABEL}}.</p>
    </li>
    <li>
      <strong>Review-Regel einführen</strong> – Qualität und Compliance von Anfang an sichern.
      <p class="muss-detail">Vier-Augen-Prinzip + Quellenpflicht für alle KI-Outputs.</p>
    </li>
  </ol>

  <!-- ABSCHNITT 2: OPTIONEN (für später) -->
  <h3>OPTIONEN – Phase 2/3</h3>
  <ul class="recommendations-optionen">
    <li>
      <strong>Wissensmanagement aufbauen</strong> – Zentrale Bibliothek für Vorlagen und Best Practices.
      <span class="option-timing">{% if COMPANY_SIZE == "solo" %}Ab Monat 3{% else %}Ab Monat 4-6{% endif %}</span>
    </li>
    <li>
      <strong>Branchenspezifischen Pilot ausweiten</strong> – Sichtbarer Erfolg für weitere Use Cases.
      <span class="option-timing">{% if COMPANY_SIZE == "solo" %}Ab Monat 6{% else %}Ab Monat 6-9{% endif %}</span>
    </li>
    <li>
      <strong>Governance formalisieren</strong> – {% if COMPANY_SIZE == "solo" %}Persönliche Checkliste{% elif COMPANY_SIZE == "team" %}Team-Leitfaden{% else %}Policy-Dokument{% endif %} für KI-Nutzung.
      <span class="option-timing">{% if COMPANY_SIZE == "solo" %}Ab Monat 3{% else %}Ab Monat 6{% endif %}</span>
    </li>
  </ul>

  <h3>Prioritäten-Überblick</h3>
  <table class="table">
    <thead>
      <tr><th>Typ</th><th>Empfehlung</th><th>Zeitrahmen</th><th>Hauptnutzen</th></tr>
    </thead>
    <tbody>
      <tr><td><strong>MUSS</strong></td><td>Minimal-Stack</td><td>Sofort</td><td>Handlungsfähigkeit</td></tr>
      <tr><td><strong>MUSS</strong></td><td>Standard-Workflow</td><td>Woche 1-2</td><td>Messbare Verbesserung</td></tr>
      <tr><td><strong>MUSS</strong></td><td>Review-Regel</td><td>Woche 1-2</td><td>Qualität & Compliance</td></tr>
      <tr><td>Option</td><td>Wissensmanagement</td><td>{% if COMPANY_SIZE == "solo" %}Monat 3+{% else %}Monat 4-6{% endif %}</td><td>Stabile Ergebnisse</td></tr>
      <tr><td>Option</td><td>Pilot ausweiten</td><td>{% if COMPANY_SIZE == "solo" %}Monat 6+{% else %}Monat 6-9{% endif %}</td><td>Sichtbarer Erfolg</td></tr>
      <tr><td>Option</td><td>Governance formalisieren</td><td>{% if COMPANY_SIZE == "solo" %}Monat 3+{% else %}Monat 6+{% endif %}</td><td>Rechtssicherheit</td></tr>
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
