Developer:
<!-- PLATIN++ PROMPT v5.5 - SPRINT G5 -->
<!-- SECTION: recommendations -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 600 (solo:0.8x=480, team:1.0x=600, kmu:1.15x=690) -->
<!--
###############################################################################
##                    🚨 KRITISCH: HAUPTLEISTUNG INTEGRATION 🚨              ##
###############################################################################

DIE VARIABLE {{hauptleistung}} ENTHÄLT DAS KERNGESCHÄFT DES USERS.
SIE MUSS MINDESTENS 5-8x IN DEN EMPFEHLUNGEN ERSCHEINEN!

PFLICHT-STELLEN FÜR {{hauptleistung}}:
1. ✅ Im Einleitungssatz: "Für Ihr Geschäftsmodell ({{hauptleistung}})..."
2. ✅ In MUSS-Maßnahme 1: Titel UND Detail mit {{hauptleistung}}
3. ✅ In MUSS-Maßnahme 2: Titel UND Detail mit {{hauptleistung}}
4. ✅ In MUSS-Maßnahme 3: Kontext zu {{hauptleistung}}
5. ✅ In der Prioritäten-Tabelle: {{hauptleistung}}-Bezug in Spalte "Hauptnutzen"

BEISPIEL {{hauptleistung}} WERTE:
- "KI-Beratung und Assessment-Tools"
- "Steuerberatung für KMU"
- "Content-Erstellung und Social Media Management"

⚠️ EMPFEHLUNGEN OHNE HAUPTLEISTUNG-BEZUG SIND WERTLOS!
⚠️ GENERISCHE PHRASEN OHNE GESCHÄFTSMODELL-KONTEXT WERDEN ABGELEHNT!

###############################################################################
-->
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

=============================================================================
ANTI-TEXTWÜSTEN REGELN v2.0 (AGGRESSIV - PFLICHT!)
=============================================================================
PROBLEM: Empfehlungs-Abschnitte werden zu langen Textwänden.
LÖSUNG: KOMPAKTE Struktur mit harten Wortlimits.

HARTE LIMITS PRO EMPFEHLUNG:
┌─────────────────────────────────────────────────────────┐
│ Feld                  │ Max Wörter │ Max Sätze        │
├─────────────────────────────────────────────────────────┤
│ Empfehlungs-Titel     │ 8 Wörter   │ -                │
│ Schwerpunkt           │ 20 Wörter  │ 1 Satz           │
│ Maßnahme              │ 20 Wörter  │ 1 Satz           │
│ Nutzen & Wirkung      │ 15 Wörter  │ 1 Satz           │
│ Aufwand & Budget      │ 12 Wörter  │ 1 Satz           │
│ Förderchance          │ 15 Wörter  │ 1 Satz           │
└─────────────────────────────────────────────────────────┘

FORMAT PRO EMPFEHLUNG (PFLICHT):
<strong>N. Empfehlung: [Titel max 8 Wörter]</strong>
<strong>Schwerpunkt:</strong> [1 Satz, max 20 Wörter]
<strong>Maßnahme:</strong> [1 Satz, max 20 Wörter]
<strong>Nutzen:</strong> [1 Satz, max 15 Wörter]
<strong>Aufwand:</strong> [Kategorie] – [kurze Beschreibung max 12 Wörter]
<strong>Förderchance:</strong> [1 Satz, max 15 Wörter]

VERBOTEN (STRIKT!):
❌ Mehr als 5 Empfehlungen
❌ Beschreibungen über 20 Wörter
❌ Mehrere Sätze pro Feld
❌ Erklärende Einleitungstexte zwischen Empfehlungen
❌ Schachtelsätze mit Nebensätzen

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
    Für Ihr Geschäftsmodell <strong>{{hauptleistung}}</strong> in der Branche {{BRANCH_CONTEXT_LABEL}}
    gelten folgende priorisierte Empfehlungen, die spezifisch auf {{hauptleistung}} abgestimmt sind.
  </p>

  <!-- ABSCHNITT 1: MUSS-MAßNAHMEN (genau 3) - PHASE 2b INDIVIDUALISIERT -->
  <!--
  🚨 KRITISCH: JEDE MUSS-MAßNAHME BRAUCHT {{hauptleistung}}! 🚨

  WICHTIG: Diese Maßnahmen werden vom LLM DYNAMISCH generiert basierend auf:
  - Maßnahme 1: {{ZEITERSPARNIS_PRIORITAET}} + KONTEXT zu {{hauptleistung}}
  - Maßnahme 2: {{hauptleistung}} EXPLIZIT im Titel UND Detail
  - Maßnahme 3: {{KI_GUARDRAILS}} + wie das {{hauptleistung}} schützt

  PFLICHT: {{hauptleistung}} muss in ALLEN 3 Maßnahmen erscheinen!
  -->
  <h3>MUSS – Sofort umsetzen für {{hauptleistung}}</h3>
  <ol class="recommendations-muss">
    <li>
      <!--
      MASCHINE GENERIERT: Basierend auf {{ZEITERSPARNIS_PRIORITAET}}
      PFLICHT: Titel MUSS {{hauptleistung}} enthalten!
      Beispiel: "Template-Bibliothek für {{hauptleistung}} aufbauen" statt "Minimal-Stack"
      -->
      <strong>[Maßnahme für {{hauptleistung}} die {{ZEITERSPARNIS_PRIORITAET}} löst]</strong> – [Warum das Zeit spart in {{hauptleistung}}].
      <p class="muss-detail">Für Ihr Kerngeschäft ({{hauptleistung}}): [Konkrete Umsetzungsschritte]</p>
    </li>
    <li>
      <!--
      MASCHINE GENERIERT: Basierend auf {{hauptleistung}}
      PFLICHT: {{hauptleistung}} muss 2x in diesem Punkt erscheinen!
      Beispiel: "Qualitätsstandard für {{hauptleistung}} definieren" statt "Standard-Workflow"
      -->
      <strong>[Optimierungsmaßnahme spezifisch für {{hauptleistung}}]</strong> – [Wie das {{hauptleistung}} verbessert].
      <p class="muss-detail">Bei {{hauptleistung}} konkret: [Prozessschritte mit Tools]</p>
    </li>
    <li>
      <!--
      MASCHINE GENERIERT: Basierend auf {{KI_GUARDRAILS}}
      PFLICHT: Erklären wie Qualitätssicherung {{hauptleistung}} schützt!
      Beispiel: "Review-Prozess für {{hauptleistung}}-Outputs" statt "Review-Regel"
      -->
      <strong>[Qualitätssicherung für {{hauptleistung}} passend zu {{KI_GUARDRAILS}}]</strong> – [Wie das Risiken in {{hauptleistung}} minimiert].
      <p class="muss-detail">Qualitätscheck für {{hauptleistung}}: [Konkrete Checkliste]</p>
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

  <h3>Prioritäten-Überblick für {{hauptleistung}}</h3>
  <table class="table">
    <thead>
      <tr><th>Typ</th><th>Empfehlung für {{hauptleistung}}</th><th>Zeitrahmen</th><th>Hauptnutzen</th></tr>
    </thead>
    <tbody>
      <!-- PHASE 2b: Tabelle wird DYNAMISCH generiert - JEDE Zeile mit {{hauptleistung}}-Bezug -->
      <tr><td><strong>MUSS</strong></td><td>[Maßnahme 1 für {{hauptleistung}}]</td><td>Sofort</td><td>Zeitersparnis bei {{hauptleistung}}</td></tr>
      <tr><td><strong>MUSS</strong></td><td>[Maßnahme 2 für {{hauptleistung}}]</td><td>Woche 1-2</td><td>Qualität in {{hauptleistung}}</td></tr>
      <tr><td><strong>MUSS</strong></td><td>[Maßnahme 3 für {{hauptleistung}}]</td><td>Woche 1-2</td><td>Sicherheit bei {{hauptleistung}}</td></tr>
      <tr><td>Option</td><td>Wissensmanagement für {{hauptleistung}}</td><td>{% if COMPANY_SIZE == "solo" %}Monat 3+{% else %}Monat 4-6{% endif %}</td><td>Skalierung von {{hauptleistung}}</td></tr>
      <tr><td>Option</td><td>{{hauptleistung}}-Pilot ausweiten</td><td>{% if COMPANY_SIZE == "solo" %}Monat 6+{% else %}Monat 6-9{% endif %}</td><td>Sichtbarer Erfolg</td></tr>
      <tr><td>Option</td><td>Governance für {{hauptleistung}}</td><td>{% if COMPANY_SIZE == "solo" %}Monat 3+{% else %}Monat 6+{% endif %}</td><td>Rechtssicherheit</td></tr>
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
