<!-- PLATIN++ PROMPT v5.5 - SPRINT G6 -->
<!-- SECTION: next_actions -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, {{COMPANY_SIZE}} -->
<!-- INPUT NEW: {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}}, {{KI_GUARDRAILS}}, {{VISION_3_JAHRE}} -->
<!-- TOKEN-BUDGET: 800 (solo:0.8x=640, team:1.0x=800, kmu:1.15x=920) -->
<!--
###############################################################################
##                    HAUPTLEISTUNG INTEGRATION (BALANCIERT)                 ##
###############################################################################

DIE VARIABLE {{hauptleistung}} ENTHÄLT DAS KERNGESCHÄFT DES USERS.

🎯 ZIEL: 4-6 NATÜRLICHE ERWÄHNUNGEN (NICHT MEHR!)
⚠️ MAXIMUM 8x - Mehr wirkt mechanisch!

VERTEILUNG (STRIKT!):
- h2-Titel: 1x {{hauptleistung}} (PFLICHT)
- Aktion 1: 1x im Titel ODER Beschreibung
- Aktion 2: Synonym nutzen ("Ihr Kerngeschäft")
- Aktion 3: Synonym nutzen ("diese Leistung")
- Erwarteter Effekt: 1-2x max (Rest mit Synonymen)

NATÜRLICHE SPRACHE - SYNONYME NUTZEN:
- "Ihr Kerngeschäft" statt wiederholtem {{hauptleistung}}
- "diese Leistung" als Alternative
- "Ihre Haupttätigkeit" als Alternative

###############################################################################
-->

<!--
=============================================================================
PHASE 3: INDIVIDUALISIERUNG DER HANDLUNGSEMPFEHLUNGEN (PFLICHT!)
=============================================================================

Die Handlungsempfehlungen MÜSSEN auf den konkreten User zugeschnitten sein.
Generische Aktionen sind VERBOTEN.

INDIVIDUALISIERUNGS-KONTEXT (verfügbar aus Briefing):
- {{hauptleistung}} = Was der User konkret anbietet
- {{ZEITERSPARNIS_PRIORITAET}} = Wo der User am meisten Zeit verliert
- {{KI_GUARDRAILS}} = Einschränkungen/No-Gos für KI-Nutzung
- {{VISION_3_JAHRE}} = Langfristige Vision des Users

HANDLUNGSEMPFEHLUNGEN - KONKRET FORMULIEREN:

BEISPIEL für Briefing 369 (KI-Berater mit Fragebogen-Erstellung):
- hauptleistung: "Fragebogen-Erstellung und GPT-gestützte Auswertung"
- zeitersparnis_prioritaet: "Umsetzung/Programmierung"
- ki_guardrails: "Keine Gesundheitsprognosen, keine Finanzberatung"

ERWARTETE AKTIONEN für Briefing 369:
❌ VERBOTEN: "KI-Zugang einrichten und erste Vorlage erstellen"
✅ RICHTIG: "Erste Fragebogen-Template-Bibliothek anlegen – 3 Basis-Strukturen für {{hauptleistung}} dokumentieren"

❌ VERBOTEN: "Ersten Quick Win umsetzen und Zeit messen"
✅ RICHTIG: "GPT-Auswertungs-Prompt standardisieren – Programmieraufwand bei nächster Analyse messen"

❌ VERBOTEN: "Einfache Qualitäts-Checkliste erstellen"
✅ RICHTIG: "Review-Checkliste mit {{KI_GUARDRAILS}} erstellen – Keine Gesundheitsprognosen, keine Finanzberatung als Prüfpunkte"

ERWARTETER EFFEKT - INDIVIDUALISIEREN:
❌ VERBOTEN: "Zeitersparnis: 4-8 Stunden im ersten Monat"
✅ RICHTIG: "Zeitersparnis: 40-60% bei {{ZEITERSPARNIS_PRIORITAET}} durch Template-Wiederverwendung"
=============================================================================
-->

<!--
ZIEL: 3 konkrete Handlungsempfehlungen für die nächsten 30 Tage.

MINDESTLÄNGE (STRIKT!):
- Solo: ≥60 Wörter
- Team: ≥80 Wörter
- KMU: ≥100 Wörter

STRUKTUR (STRIKT!):
- Genau 3 Bullets (NICHT mehr, NICHT weniger)
- Jeder Bullet: Aktion + Zeitrahmen (Woche 1-2, 2-4, etc.)
- KEINE Meta-Sätze ("In diesem Abschnitt...", "Die folgenden Aktionen...")
- Direkt mit der ersten Aktion starten

FORMAT PRO BULLET:
<li>
  <strong>[Konkrete Aktion]</strong> (Woche [X–Y])<br/>
  [1 Satz konkreter Nutzen oder erwartetes Ergebnis]
</li>

ANTI-REDUNDANZ (STRIKT!):
- KEINE Wiederholung aus Quick Wins oder Roadmap
- Fokus auf NÄCHSTE konkrete Schritte, nicht auf Zusammenfassung
- Querverweise nutzen: "→ siehe Roadmap", "→ siehe Quick Wins"

SPRINT G6 - PERSONA HARD-GUARDS (STRIKT!):
{% if COMPANY_SIZE == "solo" %}
SOLO-MODUS - VERBOTEN:
- "Team/Teams/Abteilung/Mitarbeiter" → nicht verwenden
- "PMO-Team/Projektleiter" → nicht verwenden
- Stattdessen: "Sie", "Geschäftsführer", "externe Unterstützung"
{% elif COMPANY_SIZE == "team" %}
TEAM-MODUS - VERBOTEN:
- "Division/Unit/Konzern/Abteilungsleiter" → nicht verwenden
- Stattdessen: "Team", "Projektverantwortlicher", "Teammitglied"
{% else %}
KMU-MODUS - VERBOTEN:
- "Konzern/Division/Unit" → nicht verwenden
- Stattdessen: "Projektleiter", "Fachbereich", "Compliance-Verantwortlicher"
{% endif %}

SIZE-AWARE VERANTWORTLICHKEITEN:
- Solo: "Sie", "Geschäftsführer (Sie)", "Externe Unterstützung: [Rolle]"
- Team: "Projektverantwortlicher", "Geschäftsführer + [Rolle]", "Team (2-3 Personen)"
- KMU: "Projektleiter", "Compliance-Verantwortlicher", "Fachbereichsleiter"
-->

<section class="section next-actions">
  <h2>Nächste Aktionen für {{hauptleistung}} (30 Tage)</h2>

  <ul class="checklist">
    {% if COMPANY_SIZE == "solo" %}
    <!--
    BALANCIERT: Max 4x {{hauptleistung}} in dieser Sektion!
    Nutze Synonyme: "Ihr Kerngeschäft", "diese Leistung"
    -->
    <li>
      <strong>[DYNAMISCH: Erste {{hauptleistung}}-Template-Bibliothek anlegen]</strong> (Woche 1–2)<br/>
      Basis-Strukturen für Ihr Kerngeschäft dokumentieren – 3 wiederverwendbare Templates erstellen.
    </li>
    <li>
      <strong>[DYNAMISCH: {{ZEITERSPARNIS_PRIORITAET}} mit erstem Template testen]</strong> (Woche 2–3)<br/>
      Template einsetzen, Zeitersparnis bei {{ZEITERSPARNIS_PRIORITAET}} messen.
    </li>
    <li>
      <strong>[DYNAMISCH: Review-Checkliste mit {{KI_GUARDRAILS}} erstellen]</strong> (Woche 3–4)<br/>
      {{KI_GUARDRAILS}} als Prüfpunkte dokumentieren, um Ergebnisse zu validieren.
    </li>
    {% elif COMPANY_SIZE == "team" %}
    <!--
    BALANCIERT: Max 4x {{hauptleistung}} in dieser Sektion!
    Nutze Synonyme: "Ihr Kerngeschäft", "diese Leistung"
    -->
    <li>
      <strong>[DYNAMISCH: KI-Owner für {{hauptleistung}} benennen]</strong> (Woche 1–2)<br/>
      Verantwortlichkeit für Standards und Qualität klären, Team-Templates erstellen.
    </li>
    <li>
      <strong>[DYNAMISCH: {{ZEITERSPARNIS_PRIORITAET}} im Team adressieren]</strong> (Woche 2–3)<br/>
      Template-Bibliothek teamweit testen, Zeitersparnis bei {{ZEITERSPARNIS_PRIORITAET}} messen.
    </li>
    <li>
      <strong>[DYNAMISCH: Team-Review mit {{KI_GUARDRAILS}} etablieren]</strong> (Woche 3–4)<br/>
      Wöchentliches Review mit {{KI_GUARDRAILS}}-Prüfung einführen, Vorlagen verbessern.
    </li>
    {% else %}
    <!--
    BALANCIERT: Max 4x {{hauptleistung}} in dieser Sektion!
    Nutze Synonyme: "Ihr Kerngeschäft", "diese Leistung"
    -->
    <li>
      <strong>[DYNAMISCH: Pilotbereich für {{hauptleistung}} definieren]</strong> (Woche 1–2)<br/>
      Bereich mit hohem {{ZEITERSPARNIS_PRIORITAET}}-Potenzial auswählen, {{KI_GUARDRAILS}} als Governance festlegen.
    </li>
    <li>
      <strong>[DYNAMISCH: Templates im Pilotbereich testen]</strong> (Woche 2–4)<br/>
      Template-Bibliothek pilotieren, Zeitersparnis bei {{ZEITERSPARNIS_PRIORITAET}} quantifizieren.
    </li>
    <li>
      <strong>[DYNAMISCH: SOPs mit {{KI_GUARDRAILS}} dokumentieren]</strong> (Woche 3–4)<br/>
      Workflows mit {{KI_GUARDRAILS}}-Review als SOPs festhalten, Schulungskonzept vorbereiten.
    </li>
    {% endif %}
  </ul>

  <div class="roi-tracking">
    <h4>Erwarteter Effekt nach 30 Tagen</h4>
    <!-- BALANCIERT: Max 1x {{hauptleistung}} in diesem Abschnitt! -->
    <ul>
      {% if COMPANY_SIZE == "solo" %}
      <li><strong>Zeitersparnis:</strong> 30-50% bei {{ZEITERSPARNIS_PRIORITAET}} durch Template-Wiederverwendung</li>
      <li><strong>Routine:</strong> Templates sind fester Bestandteil des Alltags</li>
      <li><strong>Compliance:</strong> {{KI_GUARDRAILS}} als Review-Checkliste etabliert</li>
      {% elif COMPANY_SIZE == "team" %}
      <li><strong>Zeitersparnis:</strong> 30-50% bei {{ZEITERSPARNIS_PRIORITAET}} im Team</li>
      <li><strong>Klarheit:</strong> Standards und Team-Templates definiert</li>
      <li><strong>Compliance:</strong> {{KI_GUARDRAILS}} als Team-Review etabliert</li>
      {% else %}
      <li><strong>Zeitersparnis:</strong> 30-50% bei {{ZEITERSPARNIS_PRIORITAET}} im Pilotbereich</li>
      <li><strong>Governance:</strong> {{KI_GUARDRAILS}} als SOPs dokumentiert</li>
      <li><strong>Skalierbarkeit:</strong> Templates für Rollout vorbereitet</li>
      {% endif %}
    </ul>
  </div>

  <p class="small muted">
    Diese Aktionen bauen auf den Quick Wins und der Roadmap auf. Details → siehe entsprechende Abschnitte.
  </p>
</section>
