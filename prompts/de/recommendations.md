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
- KEINE Detailerklärungen in diesem Abschnitt
- PHASE 2b: INDIVIDUALISIERUNG STATT GENERIK (PFLICHT!)

INDIVIDUALISIERUNGS-KONTEXT (verfügbar aus Briefing):
- {{hauptleistung}} = Was der User konkret anbietet
- {{ZEITERSPARNIS_PRIORITAET}} = Wo der User am meisten Zeit verliert
- {{KI_GUARDRAILS}} = Einschränkungen/No-Gos für KI-Nutzung
- {{VISION_3_JAHRE}} = Wohin will der User langfristig

MAßNAHME 1: MUSS {{ZEITERSPARNIS_PRIORITAET}} direkt adressieren
→ Frage: Wie kann KI/Automatisierung DIESEN spezifischen Zeitfresser reduzieren?
→ VERBOTEN: "Minimal-Stack definieren" (zu generisch!)
→ Beispiel KI-Berater: "Fragebogen-Template-Bibliothek aufbauen – reduziert Umsetzungsaufwand pro Projekt"
→ Beispiel Steuerberater: "Mandanten-Dokumente automatisch klassifizieren – eliminiert manuelle Vorsortierung"

MAßNAHME 2: MUSS zu {{hauptleistung}} passen
→ Frage: Was ist DER kritische Erfolgsfaktor für diese spezielle Leistung?
→ VERBOTEN: "Standard-Workflow etablieren" (zu allgemein!)
→ Beispiel Fragebogen+GPT: "GPT-Auswertungs-Standard definieren – konsistente Qualität bei jeder Analyse"
→ Beispiel Content-Agentur: "Prompt-Templates für Kundenprojekte – skaliert Output ohne Qualitätsverlust"

MAßNAHME 3: MUSS Risiken/Guardrails adressieren
→ Beachte {{KI_GUARDRAILS}} explizit wenn vorhanden
→ VERBOTEN: "Review-Regel einführen" (zu vage!)
→ Beispiel mit Guardrails: "Review-Checkliste gegen unerlaubte Prognosen – verhindert Compliance-Verstöße"
→ Beispiel ohne Guardrails: "Qualitätssicherung für KI-Outputs – schützt vor Fehlinformationen"

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

  <!-- ABSCHNITT 1: MUSS-MAßNAHMEN (genau 3) - PHASE 2b INDIVIDUALISIERT -->
  <!--
  WICHTIG: Diese Maßnahmen werden vom LLM DYNAMISCH generiert basierend auf:
  - Maßnahme 1: {{ZEITERSPARNIS_PRIORITAET}} (größter Zeitfresser des Users)
  - Maßnahme 2: {{hauptleistung}} (konkrete Kernleistung des Users)
  - Maßnahme 3: {{KI_GUARDRAILS}} (Einschränkungen/No-Gos)

  NICHT die statischen Beispiele unten verwenden!
  -->
  <h3>MUSS – Sofort umsetzen</h3>
  <ol class="recommendations-muss">
    <li>
      <!--
      MASCHINE GENERIERT: Basierend auf {{ZEITERSPARNIS_PRIORITAET}}
      Beispiel: "Fragebogen-Template-Bibliothek aufbauen" statt "Minimal-Stack"
      -->
      <strong>[Maßnahme die {{ZEITERSPARNIS_PRIORITAET}} direkt adressiert]</strong> – [Warum diese Maßnahme Zeit spart].
      <p class="muss-detail">[Konkrete Umsetzung für {{hauptleistung}}]</p>
    </li>
    <li>
      <!--
      MASCHINE GENERIERT: Basierend auf {{hauptleistung}}
      Beispiel: "GPT-Auswertungs-Standard definieren" statt "Standard-Workflow"
      -->
      <strong>[Maßnahme die {{hauptleistung}} optimiert]</strong> – [Warum das die Kernleistung verbessert].
      <p class="muss-detail">[Konkrete Prozessschritte für {{OFFERING_LABEL}}]</p>
    </li>
    <li>
      <!--
      MASCHINE GENERIERT: Basierend auf {{KI_GUARDRAILS}} oder allgemeine Qualitätssicherung
      Beispiel: "Review-Checkliste gegen unerlaubte Prognosen" statt "Review-Regel"
      -->
      <strong>[Qualitäts-/Risiko-Maßnahme passend zu {{KI_GUARDRAILS}}]</strong> – [Warum das Risiken minimiert].
      <p class="muss-detail">[Konkrete Checkliste oder Freigabeprozess]</p>
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
      <!-- PHASE 2b: Tabelle wird DYNAMISCH generiert basierend auf den 3 MUSS-Maßnahmen oben -->
      <tr><td><strong>MUSS</strong></td><td>[Kurzform Maßnahme 1 - zu {{ZEITERSPARNIS_PRIORITAET}}]</td><td>Sofort</td><td>Zeitersparnis</td></tr>
      <tr><td><strong>MUSS</strong></td><td>[Kurzform Maßnahme 2 - zu {{hauptleistung}}]</td><td>Woche 1-2</td><td>Qualitätssteigerung</td></tr>
      <tr><td><strong>MUSS</strong></td><td>[Kurzform Maßnahme 3 - zu {{KI_GUARDRAILS}}]</td><td>Woche 1-2</td><td>Risikominimierung</td></tr>
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

<!-- PHASE 2b: GENERISCHE PHRASEN VERBOTEN -->
<!--
=============================================================================
VERBOTEN FÜR MUSS-MAßNAHMEN (STRIKT!):
=============================================================================
Die folgenden Phrasen sind ZU GENERISCH und VERBOTEN:
- "Minimal-Stack festlegen/definieren"
- "Standard-Workflow etablieren"
- "Review-Regel einführen"
- "Klarheit vor Komplexität"
- "Ein zentrales Tool"
- "Input → KI-Entwurf → Review"
- Jede Phrase die zu JEDEM User passen würde

STATTDESSEN NUTZEN:
- Konkrete Bezüge zu {{hauptleistung}}
- Konkrete Bezüge zu {{ZEITERSPARNIS_PRIORITAET}}
- Konkrete Bezüge zu {{KI_GUARDRAILS}}
- Branchenspezifische Begriffe aus {{BRANCH_CONTEXT_LABEL}}

BEISPIEL-TRANSFORMATIONEN:
❌ "Minimal-Stack festlegen"
✅ "Fragebogen-Template-Bibliothek aufbauen" (für KI-Berater)
✅ "Mandanten-Dokument-Klassifizierung automatisieren" (für Steuerberater)
✅ "Content-Batch-Prozess etablieren" (für Content-Agentur)

❌ "Standard-Workflow etablieren"
✅ "GPT-Auswertungs-Standard definieren" (für Fragebogen-Business)
✅ "Steuererklärungsentwurf-Pipeline aufbauen" (für Steuerberater)
✅ "Editorial-Freigabe-Workflow implementieren" (für Content-Agentur)

❌ "Review-Regel einführen"
✅ "Review-Checkliste gegen unerlaubte Prognosen" (bei Gesundheits-Guardrails)
✅ "Vier-Augen-Prinzip für Steuerbescheide" (bei Finanz-Compliance)
✅ "Fakten-Check vor Veröffentlichung" (bei Content-Risiken)
=============================================================================
-->
