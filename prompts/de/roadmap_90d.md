Developer:
<!-- PLATIN+++ PROMPT v7.2 - SPRINT TRUNCATION-FIX -->
<!-- SECTION: roadmap_90d -->
<!-- PHASE 3: Maximum personalization using ALL 5 Goldnuggets -->

## ABSOLUTE LÄNGENREGEL (VOR ALLEM ANDEREN!)
{% if COMPANY_SIZE == "solo" %}
**SOLO-HARD-LIMIT: Maximal 400 Wörter / 2.500 Zeichen HTML gesamt. Bei Überschreitung wird 71% abgeschnitten!**
NUR die 4 Phasen mit je 3 kurzen Bullets + Erwartete Effekte. KEINE Booster-Sektionen (KPI-Tracking, Micro-Change etc.) — diese passen nicht ins Budget!
{% elif COMPANY_SIZE == "team" %}
**TEAM-HARD-LIMIT: Maximal 800 Wörter / 5.000 Zeichen HTML gesamt. Bei Überschreitung wird 41% abgeschnitten!**
4 Phasen + Erwartete Effekte + max. 1 kurze Booster-Sektion. Booster-Sektionen stark kürzen!
{% else %}
**KMU-HARD-LIMIT: Maximal 1000 Wörter / 7.000 Zeichen HTML gesamt.**
{% endif %}
JEDES WORT ÜBER DEM LIMIT WIRD BRUTAL ABGESCHNITTEN — der Report endet dann mitten im Satz!
<!--
###############################################################################
##   🚨🚨🚨 CRITICAL HAUPTLEISTUNG LIMIT - NON-NEGOTIABLE 🚨🚨🚨           ##
###############################################################################

**HARD RULE - MAXIMUM 3 OCCURRENCES IN ENTIRE ROADMAP SECTION**

DIE VARIABLE {{hauptleistung}} ENTHÄLT DAS KERNGESCHÄFT DES USERS.
Sie darf MAXIMAL 3x in der gesamten Roadmap erscheinen!

**ALLOWED LOCATIONS (choose ONLY 3):**
1. ✅ Im h2-Titel: "90-Tage-Fahrplan für {{hauptleistung}}" (1x)
2. ✅ Opening goal statement (1x)
3. ✅ ONE milestone OR Success metrics (1x)

**STRICTLY FORBIDDEN:**
❌ {{hauptleistung}} in JEDEM Phasennamen
❌ {{hauptleistung}} in JEDEM Bullet-Point
❌ {{hauptleistung}} mehr als 1x pro Absatz
❌ Mehr als 3x TOTAL in dieser Sektion

**SYNONYME NUTZEN (PFLICHT nach erster Erwähnung):**
- "diese Leistung" / "Ihre Dienstleistung"
- "Ihr Kerngeschäft" / "Ihr Hauptangebot"
- "dieser Service" / "diesen Bereich"
- "Ihre Arbeit" / "Ihre Tätigkeit"

**PRE-OUTPUT ENFORCEMENT:**
Nach dem Generieren: ZÄHLE alle {{hauptleistung}}-Vorkommen.
Wenn count > 3: UMSCHREIBEN mit Synonymen bis count ≤ 3.
NICHT AUSGEBEN bis count ≤ 3 erreicht ist.

⚠️ OVER-INTEGRATION (>5x) WIRKT MECHANISCH UND SEO-ARTIG!
⚠️ REPORT QUALITY VALIDATOR WIRD count > 5 ABLEHNEN!

###############################################################################
-->
<!--
=============================================================================
PLATIN+++ CONTENT DOD (verbindlich):
=============================================================================
- Transformationsbericht MIT Sicherheits- & Governance-Geländer
- Zentrale strategische Weichenstellung KLAR benennen
- Alte Logik EXPLIZIT ersetzen (Formel: "Nicht mehr X, sondern Y")
- Hauptleistung ({{HAUPTUMSATZTREIBER}}) als Bezugspunkt
- ENTSCHEIDUNGEN beschreiben, nicht Tools
- KEINE Beratungssprache, KEINE CTAs
- Kurze Absätze: ein Gedanke pro Absatz, 2-4 Sätze

MICRO-CONSISTENCY (verbindlich):
Die in der Executive Summary benannte Weichenstellung muss im Gamechanger
ausgearbeitet und in den Roadmaps sprachlich referenziert werden
(gleiche Begriffe, gleiche Logik).

HTML-VERTRAG (verbindlich):
ERLAUBT: <p>, <ul>, <ol>, <li>, <strong>, <em>
VERBOTEN: <h1>, <h2>, <h3>, <h4>, <section>, <article>
→ Überschriften werden vom Template gesetzt, nicht vom GPT-Output
=============================================================================
-->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, COMPANY_SIZE -->
<!-- INPUT NEW: {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}}, {{ki_projekte}}, {{KI_GUARDRAILS}}, {{VISION_3_JAHRE}} -->
<!-- TOKEN-BUDGET: 2800 (solo:0.8x=2240, team:1.0x=2800, kmu:1.15x=3220) -->
<!--
HÖCHSTLÄNGE (STRIKT! — Section wird bei Überschreitung automatisch getruncated!):
- Solo: max. 2.500 Zeichen (400 Wörter) | Team: max. 5.000 Zeichen (800 Wörter) | KMU: max. 7.000 Zeichen (1000 Wörter)
- WARNUNG: Solo-Budget ist NUR 3.000 Zeichen! Bei 9K+ Output = 71% Verlust!
- Solo: NUR 4 Phasen × 3 Bullets + Effekte. KEINE Booster-Sektionen!
- Team: 4 Phasen × 3-4 Bullets + Effekte + max. 1 kurze Booster-Sektion
- Jede Phase: max. 3 Bullets à 1 Satz (nicht mehr!)
- Lieber konkret und kurz als ausführlich und generisch
-->

<!--
=============================================================================
PHASE 3: INDIVIDUALISIERUNG DER ROADMAP (PFLICHT!)
=============================================================================

Die 90-Tage-Roadmap MUSS auf den konkreten User zugeschnitten sein.
Generische Phasennamen und Bullet-Points sind VERBOTEN.

INDIVIDUALISIERUNGS-KONTEXT (verfügbar aus Briefing):
- {{hauptleistung}} = Was der User konkret anbietet
- {{ZEITERSPARNIS_PRIORITAET}} = Wo der User am meisten Zeit verliert
- {{KI_GUARDRAILS}} = Einschränkungen/No-Gos für KI-Nutzung
- {{VISION_3_JAHRE}} = Langfristige Vision des Users

DYNAMISCHE PHASENNAMEN (PFLICHT - ABER OHNE {{hauptleistung}} ÜBERLAST!):
Statt generischer Namen, nutze spezifische Begriffe aus {{ZEITERSPARNIS_PRIORITAET}}.
⚠️ NICHT {{hauptleistung}} in jeden Phasennamen einfügen!

BEISPIEL für Briefing 369 (KI-Berater mit Fragebogen-Erstellung):
❌ VERBOTEN: "Phase 1: Entlastung"
❌ VERBOTEN: "Phase 1: {{hauptleistung}} optimieren" (zu repetitiv!)
✅ RICHTIG: "Phase 1: Fragebogen-Templates aufbauen"

❌ VERBOTEN: "Phase 2: Produktiver Einsatz"
✅ RICHTIG: "Phase 2: GPT-Auswertungs-Standard etablieren"

DYNAMISCHE BULLET-POINTS (PFLICHT - SYNONYME NUTZEN!):
Statt generischer Schritte, beziehe dich auf konkrete Arbeit des Users.
⚠️ NUTZE SYNONYME: "Ihr Kerngeschäft", "diese Leistung" statt wiederholtem {{hauptleistung}}!

BEISPIEL für Briefing 369:
❌ VERBOTEN: "Erste Prompt-Vorlage für eine Kernaufgabe erstellen"
✅ RICHTIG: "Erste Prompt-Vorlage für Fragebogen-Auswertung erstellen"

❌ VERBOTEN: "Template-Bibliothek für {{hauptleistung}} starten" (wenn schon 3x erwähnt!)
✅ RICHTIG: "Template-Bibliothek für Ihr Kerngeschäft mit 3 Basisvorlagen starten"

GUARDRAILS IN PHASE 0 (PFLICHT wenn {{KI_GUARDRAILS}} vorhanden):
Phase 0 MUSS die Guardrails erwähnen und als Review-Regel verankern.

BEISPIEL für Briefing 369:
"Qualitätskriterien: {{KI_GUARDRAILS}} als Checkliste dokumentieren"
→ "Qualitätskriterien: Keine Gesundheitsprognosen, keine Finanzberatung als Review-Checkliste"

VERBOTENE GENERISCHE PHRASEN in Bullets:
- "Erste Prompt-Vorlage für eine Kernaufgabe"
- "Quick Wins umsetzen"
- "Prompt-Bibliothek auf 5-10 Vorlagen erweitern"
- "Routine etablieren: täglich mindestens eine Aufgabe"
- "Standard-Workflow dokumentieren"

STATTDESSEN: Konkrete Bezüge zu {{ZEITERSPARNIS_PRIORITAET}} und Synonyme für {{hauptleistung}}.
⚠️ ERINNERUNG: MAX 3x {{hauptleistung}} TOTAL - nutze Synonyme für alle weiteren!

ERWARTETE EFFEKTE - INDIVIDUALISIEREN:
Statt generischer "15-25% Zeitersparnis" → Bezug zu {{ZEITERSPARNIS_PRIORITAET}}

BEISPIEL:
❌ "Zeitersparnis: 15-25% bei wiederkehrenden Aufgaben"
✅ "Zeitersparnis: 40-60% bei Umsetzung/Programmierung durch Template-Wiederverwendung"
=============================================================================
-->
<!--
ZIEL: 90-Tage-Roadmap als Abfolge von ENTSCHEIDUNGEN (nicht Tool-Einführungen).

=============================================================================
SPRACHSHIFT v6.0 — ENTSCHEIDUNGEN STATT IMPLEMENTIERUNGEN:
=============================================================================

Die Roadmap ist KEINE To-do-Liste für Tool-Auswahl und -Nutzung.
Die Roadmap ist eine Abfolge von bewussten Entscheidungen.

SPRACHSHIFT (verbindlich):
Roadmap als Entscheidungskette formulieren, nicht als Implementierungsplan.
Formulierungen beziehen sich auf Rahmen, Grenzen, Kriterien – nicht auf Produktnamen oder Rollout-Schritte.

TONALITÄT:
- Entscheidungsorientiert, nicht technisch
- Strategisch, nicht operativ
- Abgrenzend, nicht aufzählend

TONALITÄT KONSISTENZ (FORMELL - "SIE"):
⚠️ Der OUTPUT verwendet IMMER formelle Anrede "Sie" (nicht "du"!)
- Auch wenn diese Instruktionen "du" verwenden: OUTPUT ist FORMELL!
- NIEMALS informelles "du/dein/dir/dich" im Output verwenden!
- ERLAUBT: "Sie", "Ihr", "Ihnen", "Ihre"
- VERBOTEN: "du", "dein", "dir", "dich", "euer", "eure"

LESBARKEIT (v6.1 NEU):
- Maximal EIN abstrakter Gedanke pro Absatz
- 2–4 Sätze pro Absatz (nicht mehr)
- Keine Schachtelsätze – ein Hauptsatz, maximal ein Nebensatz
- Max. 3 Sätze pro Bullet-Punkt

=============================================================================

KURZLABELS (VERPFLICHTEND!):
- {{BRANCH_CORE_LABEL}} = Branche in 8-12 Wörtern
- {{BRANCH_CONTEXT_LABEL}} = Branche in 4-6 Wörtern
- {{OFFERING_LABEL}} = Hauptleistung in 6-10 Wörtern

MINDESTLÄNGE (STRIKT EINHALTEN - SPRINT G18!):
- Solo: Mindestens 180–230 Wörter, klar strukturiert.
- Team: Mindestens 220–280 Wörter, inklusive Change-Kommunikation.
- KMU: Mindestens 250–300 Wörter, inkl. Führung/Stakeholder-Hinweisen.

WICHTIG: Bei Unterschreitung wird Section abgelehnt!

BOOSTER-SEKTIONEN (NEU - SPRINT G17.R):
- Solo: KPI-Tracking & Mini-Dashboard Setup, Micro-Change-Management
- Team: Team-Kommunikation & Umsetzungsrituale, Dokumentation & Wissensspeicher
- KMU: Change-Kommunikation auf Führungsebene, KPI-Framework für Arbeitsbereiche

PHASEN-STRUKTUR (CONTENT QUALITY PACK v7.0 + PHASE 3 INDIVIDUALISIERUNG):
=============================================================================

PHASE 0 & PHASE 1 MÜSSEN BESONDERS SICHTBAR SEIN:
- DEUTLICHE ÜBERSCHRIFTEN für Phase 0 und Phase 1
- Genau 3 Bullets pro Phase (nicht mehr, nicht weniger)
- Phase 0 MUSS "Startpunkt 30 Minuten" referenzieren (aus Brutal Summary)

⚠️ PHASE 3 INDIVIDUALISIERUNG: Phasennamen und Bullets MÜSSEN
   {{hauptleistung}} und {{ZEITERSPARNIS_PRIORITAET}} konkret aufgreifen!

PHASE 0 (Woche 1–2): [INDIVIDUELL: Bezug zu {{hauptleistung}}]
→ Überschrift DYNAMISCH: "Phase 0: [Bezug zu {{hauptleistung}}] Setup"
→ Beispiel Briefing 369: "Phase 0: Fragebogen-Analyse Setup (Woche 1-2)"
→ Referenz: "Beginnen Sie mit dem 'Startpunkt in 30 Minuten' aus der Zusammenfassung."
→ 3 Bullets: MIT BEZUG zu {{hauptleistung}}, {{KI_GUARDRAILS}}
→ VERBOTEN: "Minimal-Setup" ohne Kontext!

PHASE 1 (Woche 3–5): [INDIVIDUELL: Bezug zu {{ZEITERSPARNIS_PRIORITAET}}]
→ Überschrift DYNAMISCH: "Phase 1: [Bezug zu {{ZEITERSPARNIS_PRIORITAET}}] Entlastung"
→ Beispiel Briefing 369: "Phase 1: Programmier-Aufwand reduzieren (Woche 3-5)"
→ 3 Bullets: MIT BEZUG zu {{ZEITERSPARNIS_PRIORITAET}}
→ VERBOTEN: "Quick Wins umsetzen" ohne Konkretisierung!

Phase 2 (Woche 6–10): [INDIVIDUELL: Workflow für {{hauptleistung}}]
→ Überschrift DYNAMISCH: "Phase 2: [{{hauptleistung}}]-Workflow stabilisieren"
→ Beispiel Briefing 369: "Phase 2: GPT-Auswertungs-Standard etablieren"
→ 3-4 Bullets: MIT BEZUG zu konkretem Workflow

Phase 3 (Woche 11–13): [INDIVIDUELL: Entscheidung mit {{VISION_3_JAHRE}}]
→ Überschrift DYNAMISCH: "Phase 3: Entscheidung [Richtung {{VISION_3_JAHRE}}]"
→ Beispiel Briefing 369: "Phase 3: Automatisierte Analyse-Pipelines evaluieren"
→ 3-4 Bullets: Messung, Lessons Learned, Entscheidung mit Bezug zur Vision

PFLICHT: "Erwartete Effekte nach 90 Tagen" (eigener Abschnitt am Ende)

=============================================================================
LEITENTSCHEIDUNGEN PRO PHASE (implizit verankern):
- Phase 0: "Transparenz vor Automatisierung" – erst verstehen, dann einsetzen
- Phase 1: "Regeln vor Erweiterung" – Qualitätskriterien definieren
- Phase 2: "Verantwortung vor Geschwindigkeit" – Prüfschleifen einbauen
- Phase 3: "Evidenz vor Expansion" – Entscheidungen auf Basis gemessener Ergebnisse

=============================================================================
FORMAT v7.0 (STRIKT):
- Jede Phase: Ziel (1 Satz) + GENAU 3 Bullets + Meilenstein (1 Satz)
- KEINE Absätze > 6 Zeilen
- KEINE langen Texte – nur Kernpunkte
- KEINE generischen Definitionen ("Eine Roadmap ist...")
- Durchschnittliche Satzlänge: maximal 18-22 Wörter

ANTI-REDUNDANZ (STRIKT!):
- Quick Wins wurden in quick_wins.md beschrieben → NICHT wiederholen
- Tools wurden in tools_empfehlungen.md beschrieben → nur referenzieren (→ siehe KI-Werkzeuge)
- Change-Management in org_change.md → Querverweis nutzen
- Hier: WIE und WANN, nicht WAS

THEMEN-OWNERSHIP (verbindlich):
- Diese Section: OWNER für konkrete 90-Tage-Maßnahmen und Phasenplanung
- NICHT hier: Datenlage-Bewertung (→ data_readiness)
- NICHT hier: Change-Perspektive/Widerstände (→ org_change)
- NICHT hier: Governance-Regeln (→ ai_policy_mini)
- NICHT hier: 12-Monats-Planung (→ roadmap_12m)

SPRINT G6 - PERSONA HARD-GUARDS (STRIKT!):
{% if COMPANY_SIZE == "solo" %}
SOLO-MODUS - VERBOTEN:
- "Team/Teams/Abteilung/Mitarbeiter" → nicht verwenden
- "Fachbereich" → "Arbeitsfeld"
- "HR" → nicht verwenden
{% elif COMPANY_SIZE == "team" %}
TEAM-MODUS - VERBOTEN:
- "Division/Unit/Konzern" → nicht verwenden
- "Abteilung" → "Bereich"
- Solo-Begriffe: "Einzelperson", "allein"
{% else %}
KMU-MODUS - VERBOTEN:
- "Konzern/Division/Unit" → nicht verwenden
- Solo-Begriffe: "Einzelperson", "allein"
{% endif %}

GUARDRAILS: Berücksichtige Leitplanken aus strategischem Kontext.
-->

<section class="section roadmap-90d">
  <h2>90-Tage-Fahrplan für {{hauptleistung}}</h2>
  <!-- PHASE 3: hauptleistung statt OFFERING_LABEL verwenden -->

  <p>
    Der folgende Plan zeigt die konkreten Schritte zur KI-Integration für
    <strong>{{hauptleistung}}</strong> in {{BRANCH_CONTEXT_LABEL}} – unterteilt in vier Phasen mit klaren Meilensteinen.
  </p>

  {% if COMPANY_SIZE == "solo" %}
  <!--
  =============================================================================
  SOLO-ROADMAP: MAX 2x {{hauptleistung}} in dieser Sektion!
  =============================================================================
  SYNONYME NUTZEN: "Ihr Kerngeschäft", "Ihre Leistung", "dieser Service"
  {{hauptleistung}} nur im Ziel-Statement, REST mit Synonymen!
  =============================================================================
  -->
  <h3>Phase 0: Setup (Woche 1–2)</h3>
  <p><strong>Ziel:</strong> Arbeitsfähigkeit mit KI für {{hauptleistung}} herstellen.</p>
  <ul>
    <li>Zugang zu einem KI-Assistenten einrichten und erste Testläufe durchführen</li>
    <li>Erste Prompt-Vorlage für Ihr Kerngeschäft erstellen</li>
    <li>Qualitätskriterien definieren: {{KI_GUARDRAILS}} als Review-Checkliste dokumentieren</li>
    <li>Einfachen Wissensspeicher für Vorlagen anlegen</li>
  </ul>
  <p><strong>Meilenstein:</strong> KI-Zugang funktioniert, erste Vorlage einsatzbereit.</p>

  <h3>Phase 1: Zeitersparnis (Woche 3–5)</h3>
  <p><strong>Ziel:</strong> Spürbare Zeitersparnis bei {{ZEITERSPARNIS_PRIORITAET}}.</p>
  <ul>
    <li>Template-Bibliothek mit 3 Basisvorlagen für Ihr Kerngeschäft starten</li>
    <li>Zeiteinsparung bei {{ZEITERSPARNIS_PRIORITAET}} messen (einfache Strichliste reicht)</li>
    <li>Prompt-Bibliothek auf 5–10 funktionierende Vorlagen erweitern</li>
    <li>Tägliche Routine: Eine Aufgabe mit KI-Unterstützung</li>
  </ul>
  <p><strong>Meilenstein:</strong> 3–5 Stunden pro Monat bei {{ZEITERSPARNIS_PRIORITAET}} eingespart.</p>

  <h3>Phase 2: Workflow (Woche 6–10)</h3>
  <p><strong>Ziel:</strong> Stabile Workflows für Ihr Kerngeschäft im Alltag.</p>
  <ul>
    <li>Workflow festigen: Input → KI-Entwurf → Prüfung gemäß {{KI_GUARDRAILS}} → Freigabe</li>
    <li>Qualitäts-Checkliste mit {{KI_GUARDRAILS}} als Prüfpunkte erstellen</li>
    <li>Self-Review zur Gewohnheit machen: jeden Output prüfen</li>
    <li>Prompt-Vorlagen verfeinern und dokumentieren</li>
    <li>Erste Automatisierung für wiederkehrende Aufgaben prüfen</li>
  </ul>
  <p><strong>Meilenstein:</strong> 70%+ der Entwürfe direkt nutzbar.</p>

  <h3>Phase 3: Richtung {{VISION_3_JAHRE}} (Woche 11–13)</h3>
  <p><strong>Ziel:</strong> Ergebnisse bewerten, nächste Schritte planen.</p>
  <ul>
    <li>Zeitersparnis bei {{ZEITERSPARNIS_PRIORITAET}} messen und mit Ziel abgleichen</li>
    <li>Qualität der Ergebnisse bewerten: Fehlerquote, Nacharbeitsaufwand</li>
    <li>Entscheidung: Ausweiten Richtung {{VISION_3_JAHRE}}, Vertiefen oder Stabilisieren?</li>
    {% if ki_projekte %}<li>Geplantes Projekt <em>{{ki_projekte}}</em> als nächsten Schritt evaluieren</li>{% endif %}
    <li>Nächste Use Cases für Weg zu {{VISION_3_JAHRE}} priorisieren</li>
  </ul>
  <p><strong>Meilenstein:</strong> Klare Entscheidung und priorisierte Liste Richtung {{VISION_3_JAHRE}}.</p>

  <h3>Erwartete Effekte nach 90 Tagen</h3>
  <ul>
    <li><strong>Zeitersparnis:</strong> 40-60% bei {{ZEITERSPARNIS_PRIORITAET}} durch Template-Wiederverwendung</li>
    <li><strong>Qualität:</strong> Konsistentere Outputs durch standardisierte Vorlagen</li>
    <li><strong>Compliance:</strong> {{KI_GUARDRAILS}} systematisch geprüft in jedem Output</li>
    <li><strong>Routine:</strong> KI ist Teil des Arbeitsalltags, keine Sonderaktion mehr</li>
    <li><strong>Klarheit:</strong> Fundierte Basis für nächste Schritte Richtung {{VISION_3_JAHRE}}</li>
  </ul>

  <h3>KPI-Tracking & Mini-Dashboard Setup</h3>
  <p>
    Als Einzelunternehmer:in benötigen Sie ein pragmatisches, zeitsparendes Reporting-System.
    Fokussieren Sie sich auf diese drei Kern-KPIs für Ihren KI-Einsatz:
  </p>
  <ul>
    <li><strong>Zeitersparnis pro Woche:</strong> Notieren Sie für jede KI-gestützte Aufgabe die
    eingesparte Zeit im Vergleich zur manuellen Bearbeitung. Eine einfache Strichliste oder
    Tabelle genügt – Ziel: 3–5 Stunden Ersparnis pro Monat.</li>
    <li><strong>Output-Menge:</strong> Wie viele Texte, E-Mails, Konzepte oder andere Deliverables
    haben Sie mit KI-Unterstützung erstellt? Tracken Sie die Produktivitätssteigerung
    quantitativ (z. B. „12 LinkedIn-Posts statt 4 ohne KI").</li>
    <li><strong>Qualitätsbewertung:</strong> Bewerten Sie Ihre KI-Outputs auf einer Skala von
    1–5 Sternen. Wie oft konnten Sie einen Entwurf direkt verwenden? Ziel: 70%+ Erstqualität.</li>
  </ul>
  <p>
    <strong>Mini-Dashboard einrichten:</strong> Nutzen Sie ein einfaches Tool wie Notion, Excel
    oder sogar ein Notizbuch. Legen Sie eine wöchentliche Tabelle an mit Spalten für Aufgabentyp,
    Zeitaufwand (mit/ohne KI), Qualitätssterne und kurze Learnings. Reservieren Sie jeden Freitag
    15–20 Minuten für die Dokumentation. Nach 90 Tagen haben Sie belastbare Daten für Ihre
    Investitionsentscheidung und können ROI konkret nachweisen.
  </p>

  <h3>Micro-Change-Management (1-Person-Betrieb)</h3>
  <p>
    Die Einführung neuer KI-Workflows erfordert bewusste Integration in Ihren Arbeitsalltag –
    auch wenn Sie allein arbeiten. Ohne strukturiertes Vorgehen besteht das Risiko, dass
    neue Tools nach anfänglicher Begeisterung wieder in Vergessenheit geraten.
  </p>
  <ul>
    <li><strong>Routine-Anker setzen:</strong> Verknüpfen Sie KI-Nutzung mit bestehenden
    Gewohnheiten. Beispiel: „Nach dem Morgenkaffee starte ich mit dem KI-gestützten
    E-Mail-Entwurf" oder „Vor jedem Kundengespräch lasse ich mir eine Gesprächsvorbereitung
    generieren". Feste Trigger erhöhen die Umsetzungswahrscheinlichkeit deutlich.</li>
    <li><strong>Selbstkontrolle ohne Druck:</strong> Führen Sie eine „Erfolgs-Checkliste" mit
    3–5 KI-Aufgaben pro Woche. Haken Sie ab, was Sie geschafft haben – ohne sich bei
    Auslassungen zu kritisieren. Der visuelle Fortschritt motiviert zur Kontinuität.</li>
    <li><strong>Wöchentliches Self-Review (30 Min.):</strong> Jeden Freitagmorgen oder
    Sonntagabend: Was hat gut funktioniert? Wo gab es Hürden? Welche Prompts brauchen
    Verfeinerung? Notieren Sie 2–3 konkrete Verbesserungsideen für die Folgewoche.</li>
    <li><strong>Iterative Anpassung:</strong> Ihr KI-Workflow ist ein lebendes System.
    Passen Sie Vorlagen und Routinen monatlich an veränderte Anforderungen in
    {{OFFERING_LABEL}} an. Was im ersten Monat funktioniert hat, muss im dritten
    Monat nicht mehr optimal sein.</li>
  </ul>
  <p>
    <strong>Erfolgsfaktor:</strong> Setzen Sie sich realistische Zwischenziele. Starten Sie
    mit einer KI-Aufgabe täglich, steigern Sie nach 2 Wochen auf 2–3. So vermeiden Sie
    Überforderung und bauen nachhaltige Kompetenz auf.
  </p>

  <h3>Content & Marketing-Systematik</h3>
  <p>
    Konzentrieren Sie sich auf 1–2 Kanäle, die zu {{OFFERING_LABEL}} passen (z. B. LinkedIn, Newsletter).
    Etablieren Sie eine feste Content-Routine: Einmal pro Woche einen kurzen Beitrag mit KI-Unterstützung
    erstellen. Nutzen Sie Ihre eigenen KI-Readiness-Reports als Marketing-Asset – sie zeigen Kompetenz
    und bieten echten Mehrwert für potenzielle Kunden. So verbinden Sie Ihre KI-Einführung direkt
    mit Ihrer Sichtbarkeit als Expert:in in {{BRANCH_CONTEXT_LABEL}}.
  </p>

  {% elif COMPANY_SIZE == "team" %}
  <!--
  =============================================================================
  TEAM-ROADMAP: MAX 2x {{hauptleistung}} in dieser Sektion!
  =============================================================================
  SYNONYME NUTZEN: "Ihr Kerngeschäft", "diese Leistung", "dieser Service"
  {{hauptleistung}} nur im Ziel-Statement, REST mit Synonymen!
  =============================================================================
  -->
  <h3>Phase 0: KI-Team-Setup (Woche 1–2)</h3>
  <p><strong>Ziel:</strong> Teamweite Arbeitsfähigkeit mit KI für {{hauptleistung}} herstellen.</p>
  <ul>
    <li>KI-Owner benennen (verantwortlich für Standards und Qualität)</li>
    <li>Gemeinsamen Zugang für alle Beteiligten einrichten</li>
    <li>Erste Vorlagen für Ihr Kerngeschäft erstellen</li>
    <li>{{KI_GUARDRAILS}} als Team-Review-Checkliste dokumentieren</li>
    <li>Gemeinsamen Wissensspeicher für Vorlagen anlegen</li>
  </ul>
  <p><strong>Meilenstein:</strong> Alle haben Zugang, erste Vorlagen verteilt.</p>

  <h3>Phase 1: Team-Entlastung bei {{ZEITERSPARNIS_PRIORITAET}} (Woche 3–5)</h3>
  <p><strong>Ziel:</strong> Zeitersparnis bei {{ZEITERSPARNIS_PRIORITAET}} im Team umsetzen.</p>
  <ul>
    <li>Template-Bibliothek für Ihr Kerngeschäft teamweit ausrollen</li>
    <li>Jede:r testet mindestens 2 Workflows für diese Leistung</li>
    <li>Erfahrungen zu {{ZEITERSPARNIS_PRIORITAET}} in Weekly-Check teilen</li>
    <li>Zeitersparnis dokumentieren</li>
    <li>Prompt-Vorlagen gemeinsam verbessern</li>
  </ul>
  <p><strong>Meilenstein:</strong> Alle nutzen KI für Ihr Kerngeschäft, Zeitersparnis dokumentiert.</p>

  <h3>Phase 2: Qualitätsstandards etablieren (Woche 6–10)</h3>
  <p><strong>Ziel:</strong> Einheitliche Qualitätsstandards für diese Leistung etablieren.</p>
  <ul>
    <li>Workflow dokumentieren: Input → KI → Review gemäß {{KI_GUARDRAILS}} → Freigabe</li>
    <li>Styleguide für KI-Outputs erstellen</li>
    <li>Review-Runden mit {{KI_GUARDRAILS}}-Prüfung etablieren</li>
    <li>Qualitätskennzahlen einführen</li>
    <li>Erste Automatisierungen prüfen</li>
  </ul>
  <p><strong>Meilenstein:</strong> Dokumentierter Workflow, Erstqualität > 70%.</p>

  <h3>Phase 3: Erweiterung Richtung {{VISION_3_JAHRE}} (Woche 11–13)</h3>
  <p><strong>Ziel:</strong> Ergebnisse messen, Erweiterung Richtung {{VISION_3_JAHRE}} vorbereiten.</p>
  <ul>
    <li>Wirkungsmessung bei {{ZEITERSPARNIS_PRIORITAET}}: Zeit, Qualität, Fehlerquote</li>
    <li>Lessons Learned für Ihre Workflows dokumentieren</li>
    <li>Entscheidung: Stabilisieren / Ausweiten Richtung {{VISION_3_JAHRE}} / Vertiefen</li>
    {% if ki_projekte %}<li>Geplantes Projekt <em>{{ki_projekte}}</em> als Team-Projekt evaluieren</li>{% endif %}
    <li>Backlog für nächste Use Cases priorisieren</li>
  </ul>
  <p><strong>Meilenstein:</strong> Klare Entscheidung Richtung {{VISION_3_JAHRE}}, priorisiertes Backlog.</p>

  <h3>Erwartete Effekte nach 90 Tagen</h3>
  <ul>
    <li><strong>Zeitersparnis:</strong> 30–50% bei {{ZEITERSPARNIS_PRIORITAET}} im Team</li>
    <li><strong>Qualität:</strong> Einheitliche Ergebnisse durch gemeinsame Standards</li>
    <li><strong>Compliance:</strong> {{KI_GUARDRAILS}} systematisch in Team-Reviews geprüft</li>
    <li><strong>Zusammenarbeit:</strong> Etablierte Review-Routinen</li>
    <li><strong>Übertragbarkeit:</strong> Dokumentierte Workflows für {{VISION_3_JAHRE}}</li>
  </ul>

  <h3>Team-Kommunikation & Umsetzungsrituale</h3>
  <p>
    Die erfolgreiche KI-Einführung im Bereich erfordert strukturierte Kommunikation und
    wiederkehrende Formate, die Akzeptanz und Kompetenzaufbau fördern. Etablieren Sie
    folgende Rituale:
  </p>
  <ul>
    <li><strong>KI-Standup (15 Min./Woche):</strong> Kurzer Austausch zu Beginn jeder
    Woche: Was habe ich mit KI ausprobiert? Was hat funktioniert? Welche Hürden gab es?
    Der KI-Owner moderiert und sammelt Themen für Vertiefung.</li>
    <li><strong>Feedback-Loop etablieren:</strong> Richten Sie einen dedizierten Kanal ein
    (Slack-Channel, Teams-Gruppe oder geteiltes Dokument), in dem Beteiligte Erfahrungen,
    Prompts und Tipps teilen. Niedrigschwelliger Austausch beschleunigt den Lernprozess.</li>
    <li><strong>Mini-Demos (30 Min. alle 2 Wochen):</strong> Ein Beteiligter zeigt einen
    erfolgreichen KI-Workflow live. Konkrete Anwendungsfälle motivieren mehr als
    theoretische Schulungen. Rotieren Sie die Präsentierenden.</li>
    <li><strong>Akzeptanz-Maßnahmen:</strong> Holen Sie Skeptiker:innen gezielt ab.
    Lassen Sie sie bei der Auswahl von Use Cases mitbestimmen. Zeigen Sie frühe Erfolge
    transparent – nichts überzeugt mehr als messbare Zeitersparnis bei Kolleg:innen.</li>
    <li><strong>Tool-Onboarding strukturieren:</strong> Erstellen Sie eine 1-Seiten-Anleitung
    für neue Beteiligte: Zugang, erste Schritte, wichtigste Prompts, Ansprechpartner.
    So wird niemand abgehängt, wenn er oder sie später einsteigt.</li>
  </ul>

  <h3>Dokumentation & Wissensspeicher</h3>
  <p>
    Wissen, das nur in einzelnen Köpfen existiert, geht verloren. Bauen Sie von Beginn an
    einen strukturierten KI-Wissensspeicher für Ihren Bereich auf:
  </p>
  <ul>
    <li><strong>KI-Handbuch anlegen:</strong> Ein lebendes Dokument mit Best Practices,
    bewährten Prompts, Qualitätskriterien und typischen Fehlern. Aktualisierung monatlich
    durch den KI-Owner, Input von allen Beteiligten.</li>
    <li><strong>Prompt-Bibliothek:</strong> Sammeln Sie alle funktionierenden Prompt-Vorlagen
    in einer gemeinsamen Ablage (Notion, Confluence, SharePoint). Kategorisieren Sie nach
    Anwendungsfall: Texterstellung, Recherche, Analyse, E-Mail etc.</li>
    <li><strong>Rollen & Verantwortlichkeiten klären:</strong>
      <ul>
        <li><em>KI-Owner:</em> Koordiniert Standards, pflegt Wissensspeicher, ist erster
        Ansprechpartner bei Fragen.</li>
        <li><em>Beteiligte:</em> Testen Workflows, geben Feedback, teilen Learnings.</li>
        <li><em>Qualitäts-Reviewer:</em> Prüft kritische KI-Outputs vor Freigabe.</li>
      </ul>
    </li>
    <li><strong>Lessons Learned dokumentieren:</strong> Nach jeder Phase (Setup, Entlastung,
    Produktiver Einsatz) kurz festhalten: Was haben wir gelernt? Was würden wir anders
    machen? Diese Erkenntnisse sind Gold wert für die Erweiterung.</li>
  </ul>
  <p>
    <strong>Tipp:</strong> Halten Sie die Dokumentation schlank. Lieber 10 funktionierende
    Prompts gut beschrieben als 50 ungeprüfte Vorlagen ohne Kontext.
  </p>

  {% else %}
  <!--
  =============================================================================
  KMU-ROADMAP: MAX 2x {{hauptleistung}} in dieser Sektion!
  =============================================================================
  SYNONYME NUTZEN: "Ihr Kerngeschäft", "diese Leistung", "dieser Service"
  {{hauptleistung}} nur im Ziel-Statement, REST mit Synonymen!
  =============================================================================
  -->
  <h3>Phase 0: KI-Pilot-Setup (Woche 1–2)</h3>
  <p><strong>Ziel:</strong> Pilotbereich für {{hauptleistung}} definieren und Grundlagen schaffen.</p>
  <ul>
    <li>Pilotbereich festlegen (hoher Entlastungspotenzial bei {{ZEITERSPARNIS_PRIORITAET}})</li>
    <li>KI-Verantwortliche:n benennen</li>
    <li>Governance-Grundregeln festlegen: {{KI_GUARDRAILS}} als Leitplanken</li>
    <li>Zugänge für Pilotbereich einrichten und dokumentieren</li>
    <li>Erste Vorlagen für Ihr Kerngeschäft erstellen</li>
  </ul>
  <p><strong>Meilenstein:</strong> Pilotbereich startklar, {{KI_GUARDRAILS}} definiert.</p>

  <h3>Phase 1: Pilot-Entlastung bei {{ZEITERSPARNIS_PRIORITAET}} (Woche 3–5)</h3>
  <p><strong>Ziel:</strong> Zeitersparnis bei {{ZEITERSPARNIS_PRIORITAET}} im Pilotbereich umsetzen.</p>
  <ul>
    <li>Template-Bibliothek für diese Leistung im Pilotbereich einsetzen</li>
    <li>Pilotbereich schult sich gegenseitig auf KI-Workflows</li>
    <li>Zeiteinsparung bei {{ZEITERSPARNIS_PRIORITAET}} dokumentieren und quantifizieren</li>
    <li>Wöchentliche Reviews im Pilotbereich etablieren</li>
    <li>Feedback-Kanal für Fragen einrichten</li>
  </ul>
  <p><strong>Meilenstein:</strong> Pilotbereich nutzt KI für Ihr Kerngeschäft, messbare Entlastung bei {{ZEITERSPARNIS_PRIORITAET}}.</p>

  <h3>Phase 2: Standardisierte SOPs etablieren (Woche 6–10)</h3>
  <p><strong>Ziel:</strong> Wiederholbare Prozesse für diese Leistung etablieren.</p>
  <ul>
    <li>SOPs für KI-Workflows dokumentieren</li>
    <li>QS-Prozess etablieren: Input → KI → Prüfung gemäß {{KI_GUARDRAILS}} → Freigabe</li>
    <li>Styleguide und Qualitätskriterien festlegen</li>
    <li>Schulungskonzept für Ausweitung auf weitere Bereiche entwickeln</li>
    <li>KPIs definieren: Zeitersparnis bei {{ZEITERSPARNIS_PRIORITAET}}, Qualität</li>
  </ul>
  <p><strong>Meilenstein:</strong> SOPs dokumentiert, Schulungskonzept fertig, KPIs definiert.</p>

  <h3>Phase 3: Ausweitungsentscheidung Richtung {{VISION_3_JAHRE}} (Woche 11–13)</h3>
  <p><strong>Ziel:</strong> Ausweitungsentscheidung und Erweiterungsplan Richtung {{VISION_3_JAHRE}}.</p>
  <ul>
    <li>Business-Case-Validierung anhand Pilotdaten</li>
    <li>Lessons Learned aus dem Pilot zusammenfassen</li>
    <li>Entscheidung: Ausweitung Richtung {{VISION_3_JAHRE}}? Ja/Nein/Anpassungen?</li>
    {% if ki_projekte %}<li>Geplantes Projekt <em>{{ki_projekte}}</em> für unternehmensweite Ausweitung evaluieren</li>{% endif %}
    <li>Priorisiertes Backlog für Erweiterung erstellen</li>
    <li>Ressourcenplanung für Weg zu {{VISION_3_JAHRE}} vorbereiten</li>
  </ul>
  <p><strong>Meilenstein:</strong> Management-Entscheidung Richtung {{VISION_3_JAHRE}} getroffen, Ausbauplan steht.</p>

  <h3>Erwartete Effekte nach 90 Tagen</h3>
  <ul>
    <li><strong>Zeitersparnis:</strong> 30–50% bei {{ZEITERSPARNIS_PRIORITAET}} im Pilotbereich</li>
    <li><strong>Qualität:</strong> Standardisierte Prozesse, dokumentierte Qualitätskriterien</li>
    <li><strong>Governance:</strong> {{KI_GUARDRAILS}} als klare Regeln, Verantwortlichkeiten dokumentiert</li>
    <li><strong>Übertragbarkeit:</strong> Erprobte SOPs für Ausweitung Richtung {{VISION_3_JAHRE}}</li>
    <li><strong>Business Case:</strong> Validierte ROI auf Basis echter Pilotdaten</li>
    <li><strong>Entscheidungsgrundlage:</strong> Fundierte Basis für {{VISION_3_JAHRE}}-Entscheidung</li>
  </ul>

  <h3>Change-Kommunikation auf Führungsebene</h3>
  <p>
    Die KI-Einführung in einem mittelständischen Unternehmen erfordert strategische
    Kommunikation auf Führungsebene. Ohne aktive Einbindung der Entscheidungsträger
    scheitern selbst erfolgreiche Pilotprojekte an fehlender Unterstützung für die Erweiterung.
  </p>
  <ul>
    <li><strong>Stakeholder-Mapping durchführen:</strong> Identifizieren Sie alle relevanten
    Entscheidungsträger und Einflusspersonen: Geschäftsführung, Bereichsleitungen,
    Betriebsrat (falls vorhanden), IT-Leitung. Verstehen Sie deren Perspektive: Wer sieht
    Chancen, wer hat Bedenken? Passen Sie Ihre Kommunikation entsprechend an.</li>
    <li><strong>Chancen & Risiken transparent kommunizieren:</strong> Präsentieren Sie
    eine ausgewogene Analyse: Welche konkreten Effizienzgewinne sind realistisch?
    Welche Risiken (Datenschutz, Qualität, Abhängigkeiten) bestehen und wie werden sie
    adressiert? Ehrliche Kommunikation schafft Vertrauen und vermeidet spätere Enttäuschungen.</li>
    <li><strong>Mitbestimmung einbinden:</strong> Falls ein Betriebsrat existiert, holen
    Sie ihn frühzeitig ins Boot. Klären Sie gemeinsam: Welche Daten werden verarbeitet?
    Gibt es Auswirkungen auf Arbeitsplätze oder -inhalte? Proaktive Einbindung verhindert
    Widerstände und Verzögerungen.</li>
    <li><strong>Regelmäßige Status-Updates:</strong> Etablieren Sie einen monatlichen
    Kurzbericht an die Geschäftsführung: Pilotfortschritt, erreichte Meilensteine,
    gemessene Effekte, nächste Schritte. Keine Überraschungen – kontinuierliche
    Transparenz ist der Schlüssel zu nachhaltigem Management-Support.</li>
    <li><strong>Erfolgsgeschichten nutzen:</strong> Dokumentieren Sie konkrete Erfolge
    aus dem Pilotbereich mit messbaren Zahlen. Diese „Proof Points" sind Ihre beste
    Argumentationsgrundlage für die Ausweitungsentscheidung.</li>
  </ul>

  <h3>KPI-Framework für Arbeitsbereiche</h3>
  <p>
    Ein strukturiertes KPI-Framework ermöglicht die objektive Bewertung des KI-Einsatzes
    über verschiedene Arbeitsbereiche hinweg. Definieren Sie Messgrößen, die ohne
    Interpretationsspielraum erfasst werden können:
  </p>
  <ul>
    <li><strong>Effizienz-KPIs:</strong>
      <ul>
        <li><em>Zeitersparnis pro Vorgang:</em> Vergleich der Bearbeitungszeit mit und ohne
        KI-Unterstützung (Ziel: 20–35% Reduktion)</li>
        <li><em>Durchsatz:</em> Anzahl bearbeiteter Vorgänge pro Zeiteinheit (Steigerung
        messbar machen)</li>
        <li><em>Automatisierungsgrad:</em> Anteil der Aufgaben, die vollständig oder
        teilautomatisiert ablaufen</li>
      </ul>
    </li>
    <li><strong>Qualitäts-KPIs:</strong>
      <ul>
        <li><em>Erstqualitätsrate:</em> Anteil der KI-Outputs, die ohne Nacharbeit
        verwendbar sind (Ziel: >70%)</li>
        <li><em>Fehlerquote:</em> Anzahl der Korrekturen oder Reklamationen pro 100
        KI-gestützte Vorgänge</li>
        <li><em>Kundenzufriedenheit:</em> Bewertung der Ergebnisqualität durch interne
        oder externe Empfänger</li>
      </ul>
    </li>
    <li><strong>Compliance-KPIs:</strong>
      <ul>
        <li><em>Governance-Einhaltung:</em> Anteil der Vorgänge, die nach definierten
        Standards geprüft wurden</li>
        <li><em>Datenschutz-Konformität:</em> Null-Toleranz bei Verstößen, regelmäßige
        Audits dokumentieren</li>
        <li><em>Dokumentationsgrad:</em> Vollständigkeit der Prozessdokumentation für
        regulatorische Anforderungen</li>
      </ul>
    </li>
    <li><strong>Akzeptanz-KPIs:</strong>
      <ul>
        <li><em>Nutzungsquote:</em> Anteil der Mitarbeitenden, die KI-Tools aktiv nutzen</li>
        <li><em>Schulungsabdeckung:</em> Prozent der geschulten Mitarbeitenden im Pilotbereich</li>
        <li><em>Feedback-Score:</em> Regelmäßige Zufriedenheitsbefragung (NPS oder 1–5 Skala)</li>
      </ul>
    </li>
  </ul>
  <p>
    <strong>Umsetzungshinweis:</strong> Starten Sie mit 3–5 Kern-KPIs, die Sie zuverlässig
    messen können. Erweitern Sie das Framework erst, wenn die Basismessung funktioniert.
    Vermeiden Sie KPI-Überflutung – weniger, aber aussagekräftige Kennzahlen sind wertvoller
    als umfangreiche Dashboards ohne Konsequenzen.
  </p>

  {% endif %}

  <h3>Risikominimierung während der Einführung</h3>
  <p>
    {% if COMPANY_SIZE == "solo" %}
    Beginnen Sie mit Aufgaben niedriger Kritikalität, um Erfahrung zu sammeln. Halten Sie bei wichtigen Outputs stets einen manuellen Prüfschritt ein. Dokumentieren Sie früh auftretende Fehlerquellen, um Ihre Prompts iterativ zu verbessern.
    {% elif COMPANY_SIZE == "team" %}
    Starten Sie mit klar abgegrenzten Pilotaufgaben im Bereich. Etablieren Sie Peer-Reviews als festen Bestandteil des Workflows. Sammeln Sie Feedback systematisch und passen Sie Vorlagen basierend auf konkreten Erfahrungen an.
    {% else %}
    Begrenzen Sie den initialen Pilotbereich auf unkritische Prozesse. Definieren Sie klare Eskalationswege bei unerwarteten Ergebnissen. Führen Sie regelmäßige Retrospektiven durch und weiten Sie erst nach validierter Qualität auf weitere Bereiche aus.
    {% endif %}
  </p>

  <!-- SPRINT G18: Narrative Verbindungen -->
  <p class="small muted">
    Nutzen Sie das <strong>Starter Kit</strong>, um Phase 1 technisch umzusetzen (→ siehe Starter Kit).
    Diese Roadmap verweist auf Quick Wins (→ siehe Sofortmaßnahmen) und
    Tools (→ siehe KI-Werkzeuge). Details zum Change-Management → siehe Veränderungsfähigkeit.
  </p>
</section>
