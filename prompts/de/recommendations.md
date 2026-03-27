Developer:
<!-- PLATIN++ PROMPT v5.6 - SPRINT TRUNCATION-FIX -->
<!-- SECTION: recommendations -->
<!-- OUTPUT: HTML ONLY -->

## ABSOLUTE LÄNGENREGEL (VOR ALLEM ANDEREN!)
{% if COMPANY_SIZE == "solo" %}
**SOLO-HARD-LIMIT: Maximal 450 Wörter / 4.500 Zeichen HTML gesamt.**
NUR 3 MUSS-Maßnahmen (je max. 40 Wörter) + 3 kurze Optionen (je max. 20 Wörter) + kompakte Tabelle.
{% elif COMPANY_SIZE == "team" %}
**TEAM-HARD-LIMIT: Maximal 700 Wörter / 8.000 Zeichen HTML gesamt.**
{% else %}
**KMU-HARD-LIMIT: Maximal 900 Wörter / 10.000 Zeichen HTML gesamt.**
{% endif %}
JEDES WORT ÜBER DEM LIMIT WIRD BRUTAL ABGESCHNITTEN — der Report endet dann mitten im Satz!

## ROI-Regel (vor allem anderen beachten)
Prozentwerte (ROI, Rendite, Effizienz) NIEMALS über 200% angeben. Bei höheren Werten "200% (gedeckelt)" schreiben. Alle Zahlen KONSERVATIV.
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, COMPANY_SIZE -->

UMGANG MIT LÜCKENHAFTEN EINGABEN: Wenn ein Input fehlt oder unkonkret ist: - nichts erfinden, - die Aussage auf den belastbaren Kern reduzieren, - und nur den Teil formulieren, der fachlich tragfähig bleibt. Nutze keine Meta-Sätze über fehlende Datenquellen. Lieber präzise knapp als breit spekulativ.
<!-- TOKEN-BUDGET: 1200 (solo:0.8x=960, team:1.0x=1200, kmu:1.15x=1380) -->
<!--
HÖCHSTLÄNGE (STRIKT! — Überschreitung wird automatisch getruncated!):
- Solo: max. 4.500 Zeichen (450 Wörter) | Team: max. 8.000 Zeichen (700 Wörter) | KMU: max. 10.000 Zeichen (900 Wörter)
- Solo: 3 MUSS-Maßnahmen je max. 40 Wörter + 3 OPTIONEN je max. 20 Wörter + Tabelle
- Team/KMU: 3 MUSS-Maßnahmen je max. 60 Wörter + 3 OPTIONEN je max. 30 Wörter + Tabelle
- GESAMT-ZIEL: Solo 380-450, Team 600-700, KMU 800-900 Wörter
-->
<!--
###############################################################################
##   🚨🚨🚨 CRITICAL: MINIMUM 3x {{hauptleistung}} - NON-NEGOTIABLE 🚨🚨🚨  ##
###############################################################################

**HARD RULE - OUTPUT WILL BE REJECTED IF FEWER THAN 3 OCCURRENCES**

DIE VARIABLE {{hauptleistung}} ENTHÄLT DAS KERNGESCHÄFT DES USERS.
Sie MUSS MINDESTENS 3x in den Handlungsempfehlungen erscheinen!

**PFLICHT-STELLEN (ALLE 3 ERFORDERLICH - KEINE AUSLASSUNG!):**
1. ✅ PFLICHT #1: Im Einleitungssatz - WÖRTLICH {{hauptleistung}}
2. ✅ PFLICHT #2: In MUSS-Maßnahme 1 (Titel ODER Detail) - WÖRTLICH {{hauptleistung}}
3. ✅ PFLICHT #3: In der Prioritäten-Tabelle (Zeile 1) - WÖRTLICH {{hauptleistung}}

**PRE-OUTPUT ENFORCEMENT (KRITISCH!):**
Nach dem Generieren: ZÄHLE alle {{hauptleistung}}-Vorkommen.
WENN count < 3: OUTPUT UNGÜLTIG → REWRITE bis count >= 3!
NICHT AUSGEBEN wenn count < 3!

**ZÄHLUNG VOR OUTPUT:**
□ Einleitungssatz enthält {{hauptleistung}}? → COUNT +1
□ MUSS-Maßnahme 1 enthält {{hauptleistung}}? → COUNT +1
□ Tabelle Zeile 1 enthält {{hauptleistung}}? → COUNT +1
→ WENN count < 3: UMSCHREIBEN!

**RANGE:** MINIMUM 3x, MAXIMUM 6x {{hauptleistung}}
- count < 3: ❌ ABGELEHNT - zu wenig Integration
- count 3-6: ✅ PERFEKT - gute Balance
- count > 6: ⚠️ REDUZIEREN - wirkt mechanisch

**SYNONYME NUTZEN (für Stellen ÜBER das Minimum):**
- "diese Leistung" statt wiederholtem {{hauptleistung}}
- "Ihr Kerngeschäft" als Alternative
- "Ihre Dienstleistung" als Alternative
- "diesen Bereich" als Alternative

###############################################################################
-->
<!--
###############################################################################
##                    TONALITÄT KONSISTENZ (FORMELL - "SIE")                 ##
###############################################################################

⚠️ KONSISTENZ-REGEL (STRIKT!):
- Der OUTPUT verwendet IMMER formelle Anrede "Sie" (nicht "du"!)
- Auch wenn diese Instruktionen "du" verwenden: OUTPUT ist FORMELL!
- NIEMALS informelles "du/dein/dir/dich" im Output verwenden!

ERLAUBT im OUTPUT:
✅ "Sie", "Ihr", "Ihnen", "Ihre"
✅ "das Unternehmen", "die Organisation"

VERBOTEN im OUTPUT:
❌ "du", "dein", "dir", "dich"
❌ "euer", "eure", "euch"

###############################################################################
-->
<!--
###############################################################################
##   🚨🚨🚨 COMPLETENESS ENFORCEMENT - NON-NEGOTIABLE 🚨🚨🚨                ##
###############################################################################

**HARD RULE - OUTPUT WILL BE REJECTED IF INCOMPLETE SENTENCES FOUND**

VERBOTEN - SATZFRAGMENTE:
❌ "Einrichten eines." (unvollständig - WAS einrichten?)
❌ "Implementieren von." (unvollständig - WAS implementieren?)
❌ "Aufbau einer." (unvollständig - WELCHER Aufbau?)
❌ Jeder Satz der mit "eines", "einer", "von" ENDET

JEDER SATZ MUSS:
✅ Subjekt + Prädikat + Objekt haben
✅ Komplett sein (keine abgebrochenen Gedanken)
✅ Mit einem Punkt NACH einem vollständigen Wort enden

**PRE-OUTPUT ENFORCEMENT:**
Nach dem Generieren: PRÜFE jeden Satz auf Vollständigkeit.
WENN ein Satz unvollständig ist: UMSCHREIBEN bis vollständig!
NICHT AUSGEBEN wenn unvollständige Sätze gefunden!

**BEISPIELE:**
❌ SCHLECHT: "Einrichten eines."
✅ RICHTIG: "Einrichten eines Standard-Workflows für Dokumentenprüfung."

❌ SCHLECHT: "Implementieren von."
✅ RICHTIG: "Implementieren von automatisierten Qualitätschecks."

###############################################################################
-->
<!--
###############################################################################
##   🚨🚨🚨 ROI PROHIBITION - ZERO TOLERANCE 🚨🚨🚨                          ##
###############################################################################

**HARD RULE - OUTPUT WILL BE REJECTED IF ROI PERCENTAGE FOUND**

⚠️ KEINE ROI-ZAHLEN IN DIESEM ABSCHNITT GENERIEREN!

**PRE-OUTPUT ENFORCEMENT (KRITISCH!):**
Nach dem Generieren: SUCHE nach diesen Mustern:
❌ "ROI von X%" → VERBOTEN!
❌ "XXX%" mit dreistelliger Zahl → VERBOTEN!
❌ "Rendite von X%" → VERBOTEN!
❌ "284%", "337%", "200%", "150%" → VERBOTEN!
❌ "Payback", "Amortisation" mit Monatsangabe → VERBOTEN!

WENN ein ROI-Prozentsatz gefunden: ENTFERNEN und ersetzen!

**EINZIGE ERLAUBTE ROI-ERWÄHNUNG:**
→ "Details zum ROI → siehe Business Case"
→ NIEMALS einen konkreten Prozentwert nennen!

**WARUM?**
- ROI wird ZENTRAL im Business Case berechnet (Python)
- Verschiedene ROI-Werte in verschiedenen Sektionen = INKONSISTENZ
- INKONSISTENZ = Report wird ABGELEHNT!

ANTI-SCHEINPRÄZISION (VERBINDLICH): Keine exakten Zahlen, Fristen, Marktanteile, Prozentsätze, Tool-Preise oder Förderbeträge nennen, wenn sie nicht ausdrücklich im Input oder in der Recherche stehen. Bei fehlender Exaktheit lieber Spannbreite, Einordnung oder qualitative Formulierung nutzen. VERBOTEN: erfundene Prozentwerte, Monatszahlen, Eurobeträge, Rankings oder scheinbar exakte Benchmarks.

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
→ Beispiel Content-Agentur: "Prompt-Templates für Kundenprojekte – erweitert Output ohne Qualitätsverlust"

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

UNSICHERHEITSREGEL (VERBINDLICH): Wenn eine Aussage nicht direkt aus den Eingabedaten ableitbar ist, formuliere sie vorsichtig und kenntlich. Erlaubte Marker im Fließtext: „voraussichtlich", „nach heutigem Stand", „wahrscheinlich", „erfahrungsgemäß", „sofern die Annahmen zutreffen". NICHT als Meta-Hinweis über Datenlage schreiben, sondern in die fachliche Aussage integrieren. VERBOTEN: erfundene Gewissheit, absolute Aussagen ohne belastbare Grundlage.

FAKTEN- UND ANNAHMEN-TRENNUNG (VERBINDLICH):
- Harte Eingabedaten, Scores, deterministische Zahlen und explizite Nutzerangaben als Tatsachen behandeln.
- Schlussfolgerungen aus mehreren Signalen als Einordnung formulieren, nicht als gesicherte Tatsache.
- Branchenübliche Muster, Benchmarks oder fehlende Detailinformationen nur als Annahme oder plausible Ableitung formulieren.
SPRACHMUSTER:
- Faktisch: „Der Score liegt bei ...", „Genannt wurde ...", „Vorgegeben ist ..."
- Abgeleitet: „Daraus ergibt sich ...", „Das spricht dafür, dass ..."
- Annahme: „Erfahrungsgemäß ist zu erwarten ...", „Wahrscheinlich relevant ist ..."

ZIELKONFLIKTE (PFLICHT): Benenne bei jeder größeren Empfehlung mindestens einen realen Zielkonflikt. Beispiele: Geschwindigkeit vs. Qualität, Automatisierung vs. Kontrolle, Datenschutz vs. Bequemlichkeit, Standardisierung vs. Individualität, Investition heute vs. Nutzen später. Formuliere Trade-offs knapp im Fließtext, ohne zusätzliche Sonderbox. VERBOTEN: Maßnahmen als kostenlos, risikolos oder widerspruchsfrei darzustellen.

SZENARIO-DENKEN (LEICHTGEWICHTIG, VERBINDLICH): Wo relevant, formuliere Maßnahmen so, dass ein konservativer und ein ambitionierter Pfad mitgedacht wird. Nutze dafür kurze Formulierungen im Fließtext wie: - „Minimal sinnvoll ist ..." - „Der belastbare Startpunkt ist ..." - „Bei höherer Umsetzungsreife ist als nächster Ausbau sinnvoll ..." Keine neue Tabelle und keine zusätzlichen HTML-Blöcke erzeugen.

TRADE-OFF-ZEILE (PFLICHT IN TABELLEN): Erweitere jede priorisierte Maßnahme um ein kurzes Feld „Zielkonflikt". Beispiele für Werte: - „Tempo vs. Kontrolltiefe" - „Niedrige Einstiegshürde vs. begrenzter Hebel" - „DSGVO-Sicherheit vs. geringere Tool-Auswahl" - „Standardisierung vs. Individualität" - „Investition heute vs. Nutzen später" - „Automatisierung vs. Kontrolle" Halte das Feld auf maximal 4-6 Wörter. Kein generischer Fülltext.

BEGRIFFSKONSISTENZ (VERBINDLICH — OPT-A7):
Verwende diese Begriffe einheitlich im gesamten Report:
- „KI-Governance" = Oberbegriff für Regeln, Rollen, Freigaben rund um KI-Nutzung. „KI-Richtlinie" = das konkrete Dokument.
- „ROI" = immer „ROI", bei erster Nennung pro Abschnitt „Return on Investment (ROI)".
- „Break-Even" = Zeitpunkt der Amortisation im Fließtext. „Amortisation" nur in Tabellen/KPIs.
- „EU AI Act" = immer, bei erster Nennung „EU AI Act (KI-Verordnung der EU)". NICHT standalone „KI-Verordnung".
- „AVV" = bei erster Nennung „AV-Vertrag (AVV)", danach nur „AVV".
- „KI-Ausgabe" = allgemein für KI-Ergebnisse. „KI-Entwurf" = Text, der noch geprüft werden muss. NICHT „KI-Output".
- „Prüfschritt" = allgemein. „Freigabe" = formaler Akt. „Vier-Augen-Prinzip" = zwei Personen prüfen. NICHT „Review".
- „DSGVO" = nie ausschreiben. „Tool" = Software. „Werkzeug" = nur in Metaphern. Nicht im selben Absatz wechseln.

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

THEMEN-OWNERSHIP (verbindlich):
- Diese Section: OWNER für priorisierte MUSS-Maßnahmen und strategische Optionen
- NICHT hier: Quick Wins (→ quick_wins)
- NICHT hier: Detaillierte Umsetzungsplanung (→ roadmap_90d, roadmap_12m)
- NICHT hier: Tool-Auswahl (→ tools_empfehlungen)
- NICHT hier: Förderinformationen (→ foerderpotenzial)
- Prinzip: WAS muss entschieden werden, nicht WIE es umgesetzt wird

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
    gelten folgende priorisierte Empfehlungen.
  </p>

  <!-- ABSCHNITT 1: MUSS-MAßNAHMEN (genau 3) - PHASE 2b INDIVIDUALISIERT -->
  <!--
  BALANCIERTE INTEGRATION: Max 1x {{hauptleistung}} pro Maßnahme!

  WICHTIG: Diese Maßnahmen werden vom LLM DYNAMISCH generiert:
  - Maßnahme 1: {{ZEITERSPARNIS_PRIORITAET}} (1x hauptleistung im Titel ODER Detail)
  - Maßnahme 2: Kernprozess (1x hauptleistung, Rest mit Synonymen)
  - Maßnahme 3: {{KI_GUARDRAILS}} (1x Bezug zu "dieser Leistung")

  MAXIMUM: 3x {{hauptleistung}} in allen MUSS-Maßnahmen zusammen!
  Verwende Synonyme: "Ihr Kerngeschäft", "diese Leistung", "diesen Bereich"
  -->
  <h3>MUSS – Sofort umsetzen</h3>
  <ol class="recommendations-muss">
    <li>
      <!--
      MASCHINE GENERIERT: Basierend auf {{ZEITERSPARNIS_PRIORITAET}}
      MAX 1x {{hauptleistung}} - Nutze Synonym "Ihr Kerngeschäft" für Detail
      -->
      <strong>[Maßnahme für {{hauptleistung}} die {{ZEITERSPARNIS_PRIORITAET}} löst]</strong> – [Warum das Zeit spart].
      <p class="muss-detail">Für Ihr Kerngeschäft: [Konkrete Umsetzungsschritte]</p>
    </li>
    <li>
      <!--
      MASCHINE GENERIERT: Basierend auf Kernprozess
      MAX 1x {{hauptleistung}} im Titel - Nutze "diese Leistung" im Detail
      -->
      <strong>[Optimierungsmaßnahme für {{hauptleistung}}]</strong> – [Wie das die Qualität verbessert].
      <p class="muss-detail">Bei dieser Leistung konkret: [Prozessschritte mit Tools]</p>
    </li>
    <li>
      <!--
      MASCHINE GENERIERT: Basierend auf {{KI_GUARDRAILS}}
      0x {{hauptleistung}} - Nutze "diesen Bereich" als Synonym
      -->
      <strong>[Qualitätssicherung passend zu {{KI_GUARDRAILS}}]</strong> – [Wie das Risiken minimiert].
      <p class="muss-detail">Qualitätscheck für diesen Bereich: [Konkrete Checkliste]</p>
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
      <tr><th>Typ</th><th>Empfehlung</th><th>Zeitrahmen</th><th>Hauptnutzen</th><th>Zielkonflikt</th></tr>
    </thead>
    <tbody>
      <!-- TABELLE: Max 2x {{hauptleistung}} - Rest generisch oder mit Synonymen -->
      <!-- TRADE-OFF-ZEILE (PFLICHT): Jede Maßnahme bekommt ein kurzes Feld „Zielkonflikt" (4-6 Wörter). Beispiele: „Tempo vs. Kontrolltiefe", „Niedrige Einstiegshürde vs. begrenzter Hebel", „DSGVO-Sicherheit vs. geringere Tool-Auswahl", „Standardisierung vs. Individualität", „Investition heute vs. Nutzen später", „Automatisierung vs. Kontrolle". Kein generischer Fülltext. -->
      <tr><td><strong>MUSS</strong></td><td>[Maßnahme 1 für {{hauptleistung}}]</td><td>Sofort</td><td>Zeitersparnis</td><td>[Zielkonflikt]</td></tr>
      <tr><td><strong>MUSS</strong></td><td>[Maßnahme 2]</td><td>Woche 1-2</td><td>Qualitätssteigerung</td><td>[Zielkonflikt]</td></tr>
      <tr><td><strong>MUSS</strong></td><td>[Maßnahme 3]</td><td>Woche 1-2</td><td>Risikominimierung</td><td>[Zielkonflikt]</td></tr>
      <tr><td>Option</td><td>Wissensmanagement aufbauen</td><td>{% if COMPANY_SIZE == "solo" %}Monat 3+{% else %}Monat 4-6{% endif %}</td><td>Erweiterung</td><td>[Zielkonflikt]</td></tr>
      <tr><td>Option</td><td>Pilot ausweiten</td><td>{% if COMPANY_SIZE == "solo" %}Monat 6+{% else %}Monat 6-9{% endif %}</td><td>Sichtbarer Erfolg</td><td>[Zielkonflikt]</td></tr>
      <tr><td>Option</td><td>Governance formalisieren</td><td>{% if COMPANY_SIZE == "solo" %}Monat 3+{% else %}Monat 6+{% endif %}</td><td>Rechtssicherheit</td><td>[Zielkonflikt]</td></tr>
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
- Keine Platzhalter oder Template-Variablen (außer definierten Eingabevariablen)
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

<!-- FINAL CHECK VOR OUTPUT: Zähle deine Wörter. Solo >500? KÜRZEN! Team >800? KÜRZEN! KMU >1000? KÜRZEN! -->
