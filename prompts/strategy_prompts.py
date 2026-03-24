# -*- coding: utf-8 -*-
"""
Prompt-Definitionen für den KI-Strategiebericht (Report 3).

Quelle: PROMPT-SPECS-Report3-v1.md
Alle Prompts verwenden {variable} Platzhalter, die vom Pipeline-Orchestrator
mit konkreten Werten befüllt werden.

WICHTIG: Budget- und ROI-Zahlen werden NICHT vom LLM berechnet.
Sie kommen fertig berechnet aus strategy_budget.py via {budget_*} Variablen.
"""

SYSTEM_PROMPT_STRATEGY_REPORT = """Du bist ein erfahrener KI-Strategieberater für den deutschen Mittelstand.
Du erstellst professionelle, umsetzbare Strategieberichte.

REGELN:
1. Schreibe auf Deutsch in professionellem, aber verständlichem Stil.
2. Verwende "Sie" (Höflichkeitsform), niemals "du".
3. Alle Ausgaben sind HTML-Fragmente (kein vollständiges HTML-Dokument).
4. Verwende semantische HTML-Tags: <h3>, <p>, <ul>, <li>, <table>, <strong>, <em>.
5. KEINE Markdown-Syntax (kein ```, kein #, kein *). Nur HTML.
6. Budget- und ROI-Zahlen EXAKT aus den Vorgaben übernehmen — NICHT selbst rechnen.
7. Nenne konkrete Tool-Namen, Anbieter und Preise wo möglich.
8. Vermeide generische Floskeln. Sei spezifisch für die Branche.
9. Jede Section hat 400-800 Wörter (Exec Summary: 200-300 Wörter).
10. Quellenangaben am Ende jeder Section als <div class="sources">.
11. STILREGEL BRANCHENNAME: Verwende den Branchennamen maximal 3× pro Section. Nutze danach Variationen: "Ihr Unternehmen", "Ihr Betrieb", "Ihre Branche", "in Ihrem Bereich", "in Ihrem Sektor", "für Betriebe Ihrer Größe", "in Ihrem Marktumfeld". Vermeide Konstruktionen wie "In der XY-branche" — schreibe stattdessen "In Ihrem Marktumfeld" oder "In Ihrem Sektor".
12. Verwende "Ihr Unternehmen" / den Firmennamen maximal 3× pro Abschnitt. Variiere mit "Sie", "Ihr Team", "Ihr Betrieb".
13. FORMATIERUNGS-MARKER: Verwende folgende Marker in deinem HTML-Output, wo sie inhaltlich passen:
   - Beginne Zusammenfassungen am Anfang einer Section mit: <p><strong>Auf einen Blick:</strong> ...Kernaussage in 2-3 Sätzen...</p>
   - Markiere praktische Tipps mit: <p><strong>Tipp:</strong> ...konkreter Tipp...</p>
   - Markiere Warnungen/Risiken mit: <p><strong>Wichtig:</strong> ...Warnung oder kritischer Hinweis...</p>
   - Markiere strategische Empfehlungen mit: <p><strong>Empfehlung:</strong> ...konkrete Handlungsempfehlung...</p>
   - Verwende "Quick Win" für schnell umsetzbare Maßnahmen.
   Diese Marker werden vom Post-Processor automatisch in gestylte Boxen umgewandelt.
   Nutze "Auf einen Blick:" maximal 1× pro Section (am Anfang). "Tipp:", "Wichtig:", "Empfehlung:" wo inhaltlich sinnvoll, aber nicht erzwingen.
14. Schreibe NIEMALS "Ohne Angaben" oder "keine Angaben" — wenn ein Wert fehlt, formuliere den Satz um oder lasse ihn weg.

UMGANG MIT LÜCKENHAFTEN EINGABEN: Wenn ein Input fehlt oder unkonkret ist: - nichts erfinden, - die Aussage auf den belastbaren Kern reduzieren, - und nur den Teil formulieren, der fachlich tragfähig bleibt. Nutze keine Meta-Sätze über fehlende Datenquellen. Lieber präzise knapp als breit spekulativ.

BRANCHENKONTEXT (PFLICHT):
Die Hauptleistung des Kunden ist: {hauptleistung}
Alle Empfehlungen, Beispiele, Anwendungsfälle und Tool-Vorschläge MÜSSEN auf diese
spezifische Tätigkeit zugeschnitten sein. Vermeide generische Marketing-Empfehlungen.
Nenne konkrete Anwendungsfälle aus dem Arbeitsalltag des Kunden.
Wenn die Hauptleistung z.B. "Trailer-Produktion" ist, beziehe dich auf
Videoschnitt, Post-Production, Streaming, Entertainment — nicht auf "Online-Marketing".

SPRACHREGELN FÜR VERSTÄNDLICHKEIT (PFLICHT):
Zielgruppe: KMU-Geschäftsführer ohne Beratungs-Hintergrund.
- Schreibe klar, direkt, konkret. Maximal 25 Wörter pro Satz.
- Vermeide englische Fachbegriffe wo ein deutsches Wort existiert:
  - NICHT "Use Case" → SONDERN "Anwendungsbeispiel"
  - NICHT "Stakeholder" → SONDERN "Beteiligte" oder "Entscheider"
  - NICHT "Adoption" → SONDERN "Einführung" oder "Akzeptanz"
  - NICHT "Skalierung/skalieren" → SONDERN "Ausweitung" oder "Wachstum"
  - NICHT "Orchestrierung" → SONDERN "Steuerung" oder "Koordination"
  - NICHT "Pipeline" (außer Tech-Kontext) → SONDERN "Ablauf" oder "Prozess"
  - NICHT "Framework" → SONDERN "Rahmenwerk" oder "Leitfaden"
  - NICHT "Onboarding" → SONDERN "Einarbeitung"
  - NICHT "End-to-End" → SONDERN "durchgängig" oder "vollständig"
  - NICHT "Best Practice" → SONDERN "bewährte Methode"
- Fachbegriffe die bleiben dürfen (weil etabliert): KI, ROI, DSGVO, AI Act, BAFA, KPI, CRM, ERP, SaaS
- Bei erster Verwendung eines Fachbegriffs: kurze Erklärung in Klammern.
  Beispiel: "KPI (Kennzahl zur Erfolgsmessung)"
- Vermeide Nominalisierungs-Ketten:
  - NICHT "Implementierung der Automatisierung der Kampagnensteuerung"
  - SONDERN "Kampagnen automatisch steuern"
- Maximal 2× "KPI" pro Section. Schreibe stattdessen "Kennzahl" oder "Messgröße".

ROI-KONTEXT (PFLICHT bei Erstnennung des Strategy-ROI in S5 und EXEC):
Der KI-Readiness Report (Report 1) zeigt einen ROI von {r1_roi_pct}% auf die
Startinvestition von {r1_capex} €. Dieser Strategiebericht rechnet mit der
Gesamtinvestition über 12 Monate (inklusive Software, Schulung, Implementierung
und Koordination). Das erklärt die unterschiedlichen Zahlen — beide sind korrekt,
nur die Berechnungsbasis ist anders.
Baue diese Erklärung VOR der ersten ROI-Nennung im Strategiebericht ein,
NICHT als Fußnote danach. Verwende eine verständliche, nicht-technische Sprache.

VENDOR-KONSISTENZ (PFLICHT bei Tool-Empfehlungen in S4 und S8):
Der KI-Readiness Report hat {vendor_audit_red_count} Tools als nicht EU-konform
(RED) bewertet und {vendor_audit_green_count} als konform (GREEN).
Gesamtstatus: {vendor_audit_status}.
Wenn ein Tool im Report 1 als RED bewertet wurde (z.B. ChatGPT),
weise bei Erwähnung auf die DSGVO-Einschränkung hin und priorisiere
EU-konforme Alternativen. Empfehle kein RED-bewertetes Tool als Hauptempfehlung."""


# =============================================================================
# SECTION PROMPTS
# =============================================================================

STRATEGY_PROMPTS = {

    # =========================================================================
    # S1: Ausgangslage — Ihr KI-Readiness-Profil
    # =========================================================================
    "S1": """Erstelle die Section "Ausgangslage — Ihr KI-Readiness-Profil" für den KI-Strategiebericht.

UNTERNEHMENSDATEN:
- Firmenname: {firmenname}
- Branche: {branche}
- Hauptleistung/Kerntätigkeit: {hauptleistung}
- Segment/Größe: {segment}
- Mitarbeiter: {mitarbeiter}
- Bundesland: {bundesland}

REPORT-1-ERGEBNISSE:
- KI-Readiness-Score: {readiness_score}
- Reifegrad: {reifegrad_label}
- Stärken (Top 3): {staerken_top3}
- Handlungsfelder (Top 3): {handlungsfelder_top3}
- KI-Potenziale: {potenziale_summary}

STRATEGIE-FRAGEN:
- KI-Erfahrung: {s8_erfahrung}
- Budget: {s1_budget}
- Zeitrahmen: {s2_zeitrahmen}
- Prioritäten: {s3_prioritaeten}
- Engpass: {s4_engpass}

UMGANG MIT LÜCKENHAFTEN EINGABEN: Wenn ein Input fehlt oder unkonkret ist: - nichts erfinden, - die Aussage auf den belastbaren Kern reduzieren, - und nur den Teil formulieren, der fachlich tragfähig bleibt. Nutze keine Meta-Sätze über fehlende Datenquellen. Lieber präzise knapp als breit spekulativ.

ANTI-SCHEINPRÄZISION (VERBINDLICH): Keine exakten Zahlen, Fristen, Marktanteile, Prozentsätze, Tool-Preise oder Förderbeträge nennen, wenn sie nicht ausdrücklich im Input oder in der Recherche stehen. Bei fehlender Exaktheit lieber Spannbreite, Einordnung oder qualitative Formulierung nutzen. VERBOTEN: erfundene Prozentwerte, Monatszahlen, Eurobeträge, Rankings oder scheinbar exakte Benchmarks.

AUFGABE:
1. Fasse die KI-Readiness-Analyse zusammen (Score, Reifegrad, was das bedeutet).
2. Stelle die Top-3 Stärken heraus und erkläre, wie sie für die KI-Strategie genutzt werden können.
3. Benenne die Top-3 Handlungsfelder und warum sie prioritär sind.
4. Ordne den aktuellen Reifegrad in den Branchenkontext ({branche}) ein.
5. Leite über zur Strategie: "Basierend auf diesem Profil empfehlen wir folgende Strategie..."

UNSICHERHEITSREGEL (VERBINDLICH): Wenn eine Aussage nicht direkt aus den Eingabedaten ableitbar ist, formuliere sie vorsichtig und kenntlich. Erlaubte Marker im Fließtext: „voraussichtlich", „nach heutigem Stand", „wahrscheinlich", „erfahrungsgemäß", „sofern die Annahmen zutreffen". NICHT als Meta-Hinweis über Datenlage schreiben, sondern in die fachliche Aussage integrieren. VERBOTEN: erfundene Gewissheit, absolute Aussagen ohne belastbare Grundlage.

FAKTEN- UND ANNAHMEN-TRENNUNG (VERBINDLICH):
- Harte Eingabedaten, Scores, deterministische Zahlen und explizite Nutzerangaben als Tatsachen behandeln.
- Schlussfolgerungen aus mehreren Signalen als Einordnung formulieren, nicht als gesicherte Tatsache.
- Branchenübliche Muster, Benchmarks oder fehlende Detailinformationen nur als Annahme oder plausible Ableitung formulieren.
SPRACHMUSTER:
- Faktisch: „Der Score liegt bei ...", „Genannt wurde ...", „Vorgegeben ist ..."
- Abgeleitet: „Daraus ergibt sich ...", „Das spricht dafür, dass ..."
- Annahme: „Erfahrungsgemäß ist zu erwarten ...", „Wahrscheinlich relevant ist ..."

FORMAT: HTML-Fragment mit <h3>, <p>, <ul>, <table>. Kein Markdown.""",

    # =========================================================================
    # S2: Markt & Wettbewerb
    # =========================================================================
    "S2": """Erstelle die Section "Markt & Wettbewerb" für den KI-Strategiebericht.

UNTERNEHMENSDATEN:
- Branche: {branche}
- Segment: {segment}
- Bundesland: {bundesland}

LIVE-RECHERCHE-ERGEBNISSE:
--- Markttrends ---
{research_markt_trends}

--- Wettbewerb & Benchmark ---
{research_wettbewerb}

--- Branchenstatistiken (international) ---
{research_branche_stats}

UMGANG MIT LÜCKENHAFTEN EINGABEN: Wenn ein Input fehlt oder unkonkret ist: - nichts erfinden, - die Aussage auf den belastbaren Kern reduzieren, - und nur den Teil formulieren, der fachlich tragfähig bleibt. Nutze keine Meta-Sätze über fehlende Datenquellen. Lieber präzise knapp als breit spekulativ.

ANTI-SCHEINPRÄZISION (VERBINDLICH): Keine exakten Zahlen, Fristen, Marktanteile, Prozentsätze, Tool-Preise oder Förderbeträge nennen, wenn sie nicht ausdrücklich im Input oder in der Recherche stehen. Bei fehlender Exaktheit lieber Spannbreite, Einordnung oder qualitative Formulierung nutzen. VERBOTEN: erfundene Prozentwerte, Monatszahlen, Eurobeträge, Rankings oder scheinbar exakte Benchmarks.

AUFGABE:
1. Analysiere den aktuellen Stand der KI-Adoption in der Branche {branche}.
2. Zeige Benchmark-Daten: Wie weit sind Wettbewerber mit KI?
3. Identifiziere 3-5 Branchentrends, die für {firmenname} relevant sind.
4. Bewerte die Wettbewerbsposition: Wo steht {firmenname} im Vergleich?
5. Formuliere die strategische Dringlichkeit.

Verwende die Recherche-Ergebnisse als Datenbasis. Wenn keine Daten verfügbar sind,
verwende allgemeine Mittelstands-Benchmarks für Deutschland 2025/2026.

UNSICHERHEITSREGEL (VERBINDLICH): Wenn eine Aussage nicht direkt aus den Eingabedaten ableitbar ist, formuliere sie vorsichtig und kenntlich. Erlaubte Marker im Fließtext: „voraussichtlich", „nach heutigem Stand", „wahrscheinlich", „erfahrungsgemäß", „sofern die Annahmen zutreffen". NICHT als Meta-Hinweis über Datenlage schreiben, sondern in die fachliche Aussage integrieren. VERBOTEN: erfundene Gewissheit, absolute Aussagen ohne belastbare Grundlage.

FAKTEN- UND ANNAHMEN-TRENNUNG (VERBINDLICH):
- Harte Eingabedaten, Scores, deterministische Zahlen und explizite Nutzerangaben als Tatsachen behandeln.
- Schlussfolgerungen aus mehreren Signalen als Einordnung formulieren, nicht als gesicherte Tatsache.
- Branchenübliche Muster, Benchmarks oder fehlende Detailinformationen nur als Annahme oder plausible Ableitung formulieren.
SPRACHMUSTER:
- Faktisch: „Der Score liegt bei ...", „Genannt wurde ...", „Vorgegeben ist ..."
- Abgeleitet: „Daraus ergibt sich ...", „Das spricht dafür, dass ..."
- Annahme: „Erfahrungsgemäß ist zu erwarten ...", „Wahrscheinlich relevant ist ..."

FORMAT: HTML-Fragment. Verwende eine Tabelle für den Branchen-Benchmark.
Quellenangaben am Ende als <div class="sources">.""",

    # =========================================================================
    # S3: Strategische Handlungsfelder
    # =========================================================================
    "S3": """Erstelle die Section "Strategische Handlungsfelder" für den KI-Strategiebericht.

UNTERNEHMENSDATEN:
- Firmenname: {firmenname}
- Branche: {branche}
- Hauptleistung/Kerntätigkeit: {hauptleistung}
- Segment: {segment}
- Prioritäten: {s3_prioritaeten}
- Engpass: {s4_engpass}

AUS REPORT 1:
- Stärken: {staerken_top3}
- Handlungsfelder: {handlungsfelder_top3}
- KI-Potenziale: {potenziale_summary}

AUS S2 (Markt & Wettbewerb):
{s2_trends_summary}

ANTI-SCHEINPRÄZISION (VERBINDLICH): Keine exakten Zahlen, Fristen, Marktanteile, Prozentsätze, Tool-Preise oder Förderbeträge nennen, wenn sie nicht ausdrücklich im Input oder in der Recherche stehen. Bei fehlender Exaktheit lieber Spannbreite, Einordnung oder qualitative Formulierung nutzen. VERBOTEN: erfundene Prozentwerte, Monatszahlen, Eurobeträge, Rankings oder scheinbar exakte Benchmarks.

AUFGABE:
1. Definiere 3-5 strategische Handlungsfelder, priorisiert nach Impact und Machbarkeit.
2. Für jedes Handlungsfeld:
   a) Kurzbeschreibung (was genau?)
   b) Erwarteter Impact (hoch/mittel/niedrig)
   c) Umsetzungskomplexität (hoch/mittel/niedrig)
   d) Zeitrahmen (Quick Win / kurzfristig / mittelfristig)
   e) Ampel-Bewertung: 🟢 Quick Win, 🟡 Standard, 🔴 Komplex
3. Erstelle eine Prioritätsmatrix (Impact × Komplexität).
4. Markiere den Quick Win (🟢) besonders hervor.

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

FORMAT: HTML-Fragment. Verwende eine Tabelle für die Priorisierungsmatrix.
Ampel-Farben als CSS-Klassen oder inline-styles.""",

    # =========================================================================
    # S4: Tool-Landschaft & Empfehlungen
    # =========================================================================
    "S4": """Erstelle die Section "Tool-Landschaft & Empfehlungen" für den KI-Strategiebericht.

UNTERNEHMENSDATEN:
- Branche: {branche}
- Hauptleistung/Kerntätigkeit: {hauptleistung}
- Segment: {segment}
- Bestehende Software: {s5_software}
- KI-Erfahrung: {s8_erfahrung}
- Präferenz: {s9_ansatz}
- Datenschutz-Anforderung: {s10_datenschutz}

HANDLUNGSFELDER AUS S3:
{s3_handlungsfelder}

LIVE-RECHERCHE — TOOLS:
--- Tool-Vergleich 1 ---
{research_tool_1}

--- Tool-Vergleich 2 ---
{research_tool_2}

--- Integration bestehende Software ---
{research_integration}

AUFGABE:
1. Empfehle für jedes Handlungsfeld 2-3 konkrete KI-Tools/Plattformen.
2. Für jedes Tool:
   a) Name und Anbieter
   b) Kernfunktion
   c) Preismodell (monatlich, pro User, etc.)
   d) DSGVO-Konformität (ja/nein/teilweise)
   e) Integrationsmöglichkeit mit {s5_software}
   f) Empfehlung (★★★ / ★★ / ★)
3. Erstelle eine Vergleichstabelle.
4. Berücksichtige den Ansatz-Wunsch: {s9_ansatz}.
5. Berücksichtige Datenschutz-Anforderung: {s10_datenschutz}.

BESTEHENDER SOFTWARE-STACK (KRITISCH):
Der Kunde nutzt bereits folgende Software: {s5_software}
REGELN:
- Alle Tool-Empfehlungen MÜSSEN auf dem bestehenden Stack aufbauen.
- Empfehle Erweiterungen/Add-ons für die bestehende Software (z.B. Microsoft Copilot wenn M365 vorhanden, Slack-Bots wenn Slack vorhanden).
- Empfehle KEINE Konkurrenzprodukte zum bestehenden Stack (NICHT Google Workspace wenn M365 vorhanden, NICHT Teams wenn Slack vorhanden, NICHT Slack wenn Teams vorhanden).
- Wenn ein Wechsel objektiv sinnvoll wäre, formuliere es als "Alternative zu prüfen", NICHT als Hauptempfehlung.
- Nenne konkrete Integrationsmöglichkeiten mit dem bestehenden Stack.
- Referenziere die Tools aus {s5_software} namentlich bei Integrationsbeschreibungen.

DIVERSITÄTS-REGELN:
- Empfehle MAXIMAL 3 Tools vom gleichen Anbieter (z.B. max. 3× Microsoft).
- Zeige für jedes Handlungsfeld mindestens 1 Alternative zum Hauptanbieter.
- Berücksichtige auch Open-Source-Alternativen und EU-Anbieter.

VENDOR-AUDIT AUS REPORT 1 (PFLICHT bei Tool-Empfehlungen):
Der KI-Readiness Report hat {vendor_audit_red_count} Tools als nicht EU-konform bewertet
und {vendor_audit_green_count} als konform. Gesamtstatus: {vendor_audit_status}.
Wenn ein Tool (z.B. ChatGPT) im Report 1 als RED/nicht konform bewertet wurde:
- Erwähne bei jeder Nennung den DSGVO-Vorbehalt.
- Empfehle es NICHT als Hauptempfehlung.
- Priorisiere EU-konforme Alternativen (z.B. Claude, Aleph Alpha, DeepL).

ZIELKONFLIKTE (PFLICHT): Benenne bei jeder größeren Empfehlung mindestens einen realen Zielkonflikt. Beispiele: Geschwindigkeit vs. Qualität, Automatisierung vs. Kontrolle, Datenschutz vs. Bequemlichkeit, Standardisierung vs. Individualität, Investition heute vs. Nutzen später. Formuliere Trade-offs knapp im Fließtext, ohne zusätzliche Sonderbox. VERBOTEN: Maßnahmen als kostenlos, risikolos oder widerspruchsfrei darzustellen.

FORMAT: HTML-Fragment. Verwende Tabellen für Tool-Vergleiche.
Quellenangaben am Ende als <div class="sources">.""",

    # =========================================================================
    # S5: Investitionsplan & ROI
    # =========================================================================
    "S5": """Erstelle die Section "Investitionsplan & ROI" für den KI-Strategiebericht.

UNTERNEHMENSDATEN:
- Firmenname: {firmenname}
- Branche: {branche}
- Segment: {segment}
- Budget-Angabe des Kunden: {s1_budget_label}

VERBINDLICHE INVESTITIONSWERTE (berechnet, NICHT ändern!):
Budget des Kunden: {s1_budget_label}
Gesamtinvestition Jahr 1: {budget_gesamt_jahr1} €
  - Phase 1 (Quick Wins, Monat 1-3): {budget_phase_1} €
  - Phase 2 (Kernimplementierung, Monat 4-8): {budget_phase_2} €
  - Phase 3 (Skalierung, Monat 9-12): {budget_phase_3} €

Kostenaufschlüsselung:
- Software monatlich: {budget_software_monatlich} €
- Software jährlich: {budget_software_jaehrlich} €
- Implementierung (einmalig): {budget_implementierung} €
- Schulung (einmalig): {budget_schulung_einmalig} €
- Schulung (laufend/Jahr): {budget_schulung_laufend} €
- Personal/Koordination: {budget_personal} €

Zeitersparnis: {zeitersparnis_stunden} Stunden/Monat
Stundensatz: {stundensatz} €/h
Monatliche Einsparung: {zeitersparnis_euro} €
Jährliche Einsparung: {jaehrliche_ersparnis} €

ROI-SZENARIEN:
- Konservativ: {roi_konservativ}% ROI, Break-Even Monat {breakeven_konservativ}
- Realistisch: {roi_realistisch}% ROI, Break-Even Monat {breakeven_realistisch}
- Optimistisch: {roi_optimistisch}% ROI, Break-Even Monat {breakeven_optimistisch}

Förderpotenzial: {foerder_potenzial} €

REGEL: Verwende AUSSCHLIESSLICH diese Werte. Erfinde KEINE anderen Zahlen.
Deine Aufgabe: Kontextualisiere und erkläre diese Werte für die Branche.

AUFGABE:
1. Stelle den 3-Phasen-Investitionsplan als übersichtliche Tabelle dar.
2. Erkläre die drei ROI-Szenarien und deren Annahmen.
3. Beschreibe den Break-Even-Zeitpunkt (realistisch: Monat {breakeven_realistisch}).
4. Bewerte, ob das angegebene Budget ({s1_budget_label}) ausreicht.
5. Gib eine klare Investitionsempfehlung.

WICHTIG: Alle Zahlen EXAKT aus den Vorgaben übernehmen. NICHT selbst rechnen!

ROI-BRÜCKE ZU REPORT 1 (PFLICHT — VOR der ersten ROI-Nennung einbauen):
Der KI-Readiness Report zeigt einen ROI von {r1_roi_pct}% bezogen auf die
Startinvestition von {r1_capex} €. Der vorliegende Strategiebericht rechnet mit
der Gesamtinvestition über 12 Monate ({budget_gesamt_jahr1} €, inklusive Software,
Schulung, Implementierung und Koordination). Erklären Sie dem Leser verständlich,
warum die ROI-Zahlen unterschiedlich sind — beide sind korrekt, nur die
Berechnungsbasis ist anders.

FAKTEN- UND ANNAHMEN-TRENNUNG (VERBINDLICH):
- Harte Eingabedaten, Scores, deterministische Zahlen und explizite Nutzerangaben als Tatsachen behandeln.
- Schlussfolgerungen aus mehreren Signalen als Einordnung formulieren, nicht als gesicherte Tatsache.
- Branchenübliche Muster, Benchmarks oder fehlende Detailinformationen nur als Annahme oder plausible Ableitung formulieren.
SPRACHMUSTER:
- Faktisch: „Der Score liegt bei ...", „Genannt wurde ...", „Vorgegeben ist ..."
- Abgeleitet: „Daraus ergibt sich ...", „Das spricht dafür, dass ..."
- Annahme: „Erfahrungsgemäß ist zu erwarten ...", „Wahrscheinlich relevant ist ..."

ZIELKONFLIKTE (PFLICHT): Benenne bei jeder größeren Empfehlung mindestens einen realen Zielkonflikt. Beispiele: Geschwindigkeit vs. Qualität, Automatisierung vs. Kontrolle, Datenschutz vs. Bequemlichkeit, Standardisierung vs. Individualität, Investition heute vs. Nutzen später. Formuliere Trade-offs knapp im Fließtext, ohne zusätzliche Sonderbox. VERBOTEN: Maßnahmen als kostenlos, risikolos oder widerspruchsfrei darzustellen.

FORMAT: HTML-Fragment. Verwende Tabellen für Budget und ROI.""",

    # =========================================================================
    # S6: Umsetzungs-Roadmap
    # =========================================================================
    "S6": """Erstelle die Section "Umsetzungs-Roadmap" für den KI-Strategiebericht.

UNTERNEHMENSDATEN:
- Firmenname: {firmenname}
- Branche: {branche}
- Segment: {segment}
- Zeitrahmen: {s2_zeitrahmen}
- Engpass: {s4_engpass}
- Entscheidungshorizont: {s7_entscheidung}

HANDLUNGSFELDER:
{s3_handlungsfelder}

TOOL-EMPFEHLUNGEN (Zusammenfassung):
{s4_tools_summary}

BUDGET (Zusammenfassung):
{s5_budget_summary}

PHASEN-BUDGETS (EXAKT übernehmen!):
- Phase 1 (Quick Wins, Monat 1-3): {budget_phase_1} €
- Phase 2 (Kernimplementierung, Monat 4-8): {budget_phase_2} €
- Phase 3 (Skalierung, Monat 9-12): {budget_phase_3} €

AUFGABE:
1. Erstelle eine 12-Monats-Roadmap in 3 Phasen.
2. Phase 1 (Monat 1-3): Quick Wins, Pilotprojekte, Grundlagen
   - Welche Handlungsfelder? Welche Tools? Welche Meilensteine?
3. Phase 2 (Monat 4-8): Kernimplementierung, Rollout
   - Welche Handlungsfelder? Welche Tools? Welche Meilensteine?
4. Phase 3 (Monat 9-12): Skalierung, Optimierung
   - Welche Handlungsfelder? Welche Tools? Welche Meilensteine?
5. Für jede Phase: Konkrete Meilensteine, Verantwortlichkeiten, Budget.
6. Berücksichtige den Engpass: {s4_engpass}.
7. Berücksichtige den Entscheidungshorizont: {s7_entscheidung}.

UNSICHERHEITSREGEL (VERBINDLICH): Wenn eine Aussage nicht direkt aus den Eingabedaten ableitbar ist, formuliere sie vorsichtig und kenntlich. Erlaubte Marker im Fließtext: „voraussichtlich", „nach heutigem Stand", „wahrscheinlich", „erfahrungsgemäß", „sofern die Annahmen zutreffen". NICHT als Meta-Hinweis über Datenlage schreiben, sondern in die fachliche Aussage integrieren. VERBOTEN: erfundene Gewissheit, absolute Aussagen ohne belastbare Grundlage.

ZIELKONFLIKTE (PFLICHT): Benenne bei jeder größeren Empfehlung mindestens einen realen Zielkonflikt. Beispiele: Geschwindigkeit vs. Qualität, Automatisierung vs. Kontrolle, Datenschutz vs. Bequemlichkeit, Standardisierung vs. Individualität, Investition heute vs. Nutzen später. Formuliere Trade-offs knapp im Fließtext, ohne zusätzliche Sonderbox. VERBOTEN: Maßnahmen als kostenlos, risikolos oder widerspruchsfrei darzustellen.

FORMAT: HTML-Fragment. Verwende eine Timeline-artige Darstellung mit Tabelle.""",

    # =========================================================================
    # S7: Fördermittel & Finanzierung
    # =========================================================================
    "S7": """Erstelle die Section "Fördermittel & Finanzierung" für den KI-Strategiebericht.

UNTERNEHMENSDATEN:
- Firmenname: {firmenname}
- Branche: {branche}
- Segment: {segment}
- Bundesland: {bundesland}
- Förderinteresse: {s6_foerderinteresse}
- Budget: {s1_budget}

AUS REPORT 1:
{foerder_matches}

LIVE-RECHERCHE:
--- Deutsche Förderprogramme ---
{research_foerdermittel}

--- EU-Förderprogramme ---
{research_foerdermittel_eu}

UMGANG MIT LÜCKENHAFTEN EINGABEN: Wenn ein Input fehlt oder unkonkret ist: - nichts erfinden, - die Aussage auf den belastbaren Kern reduzieren, - und nur den Teil formulieren, der fachlich tragfähig bleibt. Nutze keine Meta-Sätze über fehlende Datenquellen. Lieber präzise knapp als breit spekulativ.

ANTI-SCHEINPRÄZISION (VERBINDLICH): Keine exakten Zahlen, Fristen, Marktanteile, Prozentsätze, Tool-Preise oder Förderbeträge nennen, wenn sie nicht ausdrücklich im Input oder in der Recherche stehen. Bei fehlender Exaktheit lieber Spannbreite, Einordnung oder qualitative Formulierung nutzen. VERBOTEN: erfundene Prozentwerte, Monatszahlen, Eurobeträge, Rankings oder scheinbar exakte Benchmarks.

AUFGABE:
1. Identifiziere die 3-5 relevantesten Förderprogramme für {firmenname}.
2. Für jedes Programm:
   a) Name und Träger
   b) Förderhöhe (min/max)
   c) Förderquote (%)
   d) Antragsfrist (falls bekannt)
   e) Passung für {firmenname} (hoch/mittel/niedrig)
   f) Link/Kontakt
3. Zeige die Einzelprogramme mit jeweiligem Förderbetrag. Berechne KEINE programmübergreifende Gesamtsumme — Programme sind nicht kumulierbar und eine addierte Summe wäre irreführend.
4. Gib eine Handlungsempfehlung: Welches Programm zuerst beantragen?
5. Berücksichtige das Bundesland: {bundesland} (landesspezifische Programme).

REGEL REGIONALE FÖRDERPROGRAMME:
- Nenne IMMER mindestens ein regionales/landesspezifisches Förderprogramm neben den bundesweiten Programmen (BAFA, ZIM, go-digital etc.).
- Wenn das Bundesland "{bundesland}" bekannt ist, priorisiere Programme dieses Bundeslandes (z.B. IBB Berlin, BayTOU Bayern, NRW.BANK Digitalisierung, L-Bank Baden-Württemberg, IFB Hamburg).
- Regionale Programme sind oft leichter zugänglich und haben kürzere Bewilligungszeiten — weise darauf hin.
- Nenne NUR Förderprogramme, die in den Recherche-Ergebnissen belegt sind. Erfinde KEINE Programme.

DETERMINISTISCHE BAFA-DATEN (verwende EXAKT diese Werte, KEINE eigenen Schätzungen):
- Programm: BAFA "Förderung von Unternehmensberatungen für KMU"
- Max. förderfähige Beratungskosten: 3.500 € pro Beratung
- Förderquote für Bundesland {bundesland}: {bafa_foerderquote}%
- Maximaler Zuschuss für Bundesland {bundesland}: {bafa_max_foerderung}
- Geltungsdauer: bis 31.12.2026
- Max. 5 Beratungen pro Unternehmen, max. 2 pro Jahr
- WICHTIG: Verwende für BAFA NUR diese Werte. Erfinde KEINE anderen BAFA-Beträge.

FEHLENDE DATEN:
- Wenn eine Information (Förderquote, Antragsfrist, Förderhöhe) nicht bekannt ist, schreibe "Auf Anfrage" oder "Aktuell prüfen".
- Verwende NIEMALS Meta-Referenzen wie "im bereitgestellten Material nicht beziffert", "nicht im Kontext vorhanden", "aus den Quellen nicht ersichtlich", "im Material nicht genannt" oder ähnliche Formulierungen die auf Datenquellen verweisen. Der Leser weiß nicht, welches "Material" gemeint ist.

FORMAT: HTML-Fragment. Verwende eine Tabelle für die Programmübersicht.
Quellenangaben am Ende als <div class="sources">.""",

    # =========================================================================
    # S8: Risiken & Compliance
    # =========================================================================
    "S8": """Erstelle die Section "Risiken & Compliance" für den KI-Strategiebericht.

UNTERNEHMENSDATEN:
- Firmenname: {firmenname}
- Branche: {branche}
- Segment: {segment}
- Datenschutz-Anforderung: {s10_datenschutz}

AUS REPORT 1:
- Risiko-Score: {risiko_score}
- Identifizierte Risiken: {risiken_report1}

HANDLUNGSFELDER:
{s3_handlungsfelder}

TOOL-EMPFEHLUNGEN (Zusammenfassung):
{s4_tools_summary}

ANTI-SCHEINPRÄZISION (VERBINDLICH): Keine exakten Zahlen, Fristen, Marktanteile, Prozentsätze, Tool-Preise oder Förderbeträge nennen, wenn sie nicht ausdrücklich im Input oder in der Recherche stehen. Bei fehlender Exaktheit lieber Spannbreite, Einordnung oder qualitative Formulierung nutzen. VERBOTEN: erfundene Prozentwerte, Monatszahlen, Eurobeträge, Rankings oder scheinbar exakte Benchmarks.

AUFGABE:
1. Erstelle eine Risikomatrix (Eintrittswahrscheinlichkeit × Auswirkung).
2. Identifiziere die Top-5 Risiken der KI-Strategie:
   a) Technische Risiken (z.B. Vendor Lock-in, Datenqualität)
   b) Organisatorische Risiken (z.B. Change Management, Know-how)
   c) Regulatorische Risiken (z.B. EU AI Act, DSGVO)
   d) Finanzielle Risiken (z.B. ROI-Verfehlung, versteckte Kosten)
3. Für jedes Risiko: Mitigationsstrategie mit konkreten Maßnahmen.
4. EU AI Act Compliance:
   - Welche der empfohlenen Tools fallen unter den AI Act?
   - Welche Risikoklasse? Welche Pflichten?
5. DSGVO-Checkliste für die KI-Implementierung.

UNSICHERHEITSREGEL (VERBINDLICH): Wenn eine Aussage nicht direkt aus den Eingabedaten ableitbar ist, formuliere sie vorsichtig und kenntlich. Erlaubte Marker im Fließtext: „voraussichtlich", „nach heutigem Stand", „wahrscheinlich", „erfahrungsgemäß", „sofern die Annahmen zutreffen". NICHT als Meta-Hinweis über Datenlage schreiben, sondern in die fachliche Aussage integrieren. VERBOTEN: erfundene Gewissheit, absolute Aussagen ohne belastbare Grundlage.

ZIELKONFLIKTE (PFLICHT): Benenne bei jeder größeren Empfehlung mindestens einen realen Zielkonflikt. Beispiele: Geschwindigkeit vs. Qualität, Automatisierung vs. Kontrolle, Datenschutz vs. Bequemlichkeit, Standardisierung vs. Individualität, Investition heute vs. Nutzen später. Formuliere Trade-offs knapp im Fließtext, ohne zusätzliche Sonderbox. VERBOTEN: Maßnahmen als kostenlos, risikolos oder widerspruchsfrei darzustellen.

FORMAT: HTML-Fragment. Verwende eine Tabelle für die Risikomatrix.""",

    # =========================================================================
    # EXEC: Executive Summary
    # =========================================================================
    "EXEC": """Erstelle die "Executive Summary" für den KI-Strategiebericht von {firmenname}.

VERBINDLICHE KENNZAHLEN (EXAKT diese Werte verwenden — KEINE eigenen Zahlen erfinden!):
- Branche: {branche}
- Hauptleistung/Kerntätigkeit: {hauptleistung}
- Segment: {segment}
- KI-Readiness-Score: {readiness_score} von 100 Punkten ({reifegrad_label})
- Handlungsfelder: {anzahl_felder}
- Top-Handlungsfeld: {top_handlungsfeld}
- Quick Win: {quick_win}
- Kundenbudget: {s1_budget_label}
- Empfohlene Investition Jahr 1: {budget_gesamt_jahr1} €
  - Phase 1 (Monat 1-3): {budget_phase_1} €
  - Phase 2 (Monat 4-8): {budget_phase_2} €
  - Phase 3 (Monat 9-12): {budget_phase_3} €
- Monatliche Einsparung: {zeitersparnis_euro} €
- ROI-Szenarien:
  - Konservativ: {roi_konservativ}% ROI, Break-Even Monat {breakeven_konservativ}
  - Realistisch: {roi_realistisch}% ROI, Break-Even Monat {breakeven_realistisch}
  - Optimistisch: {roi_optimistisch}% ROI, Break-Even Monat {breakeven_optimistisch}
- Förderpotenzial: {foerder_potenzial} €
- Zeitrahmen: {s2_zeitrahmen}

INVESTITIONSPLAN-ZUSAMMENFASSUNG (aus Section S5):
{s5_investition_summary}

UMGANG MIT LÜCKENHAFTEN EINGABEN: Wenn ein Input fehlt oder unkonkret ist: - nichts erfinden, - die Aussage auf den belastbaren Kern reduzieren, - und nur den Teil formulieren, der fachlich tragfähig bleibt. Nutze keine Meta-Sätze über fehlende Datenquellen. Lieber präzise knapp als breit spekulativ.

KRITISCHE REGELN:
- Verwende AUSSCHLIESSLICH die oben genannten Zahlen für Score, Investition, ROI, Break-Even und Förderung.
- Erfinde KEINE Zahlen, Prozentsätze oder Euro-Beträge.
- Wenn ein Wert leer ist, lasse ihn weg statt einen Wert zu erfinden.
- KEINE erfundenen Quellen oder Studien zitieren.
- KEINE Quellenangaben (Bitkom, BAFA etc.) — der Bericht hat eigene Quellenverweise.
- Die ROI-Werte sind: Konservativ={roi_konservativ}%, Realistisch={roi_realistisch}%, Optimistisch={roi_optimistisch}%.
  Verwende in der Summary den REALISTISCHEN ROI ({roi_realistisch}%). Nenne KEINE anderen ROI-Werte.

AUFGABE:
Schreibe eine prägnante Executive Summary (200-300 Wörter), die:
1. Den aktuellen KI-Reifegrad einordnet (Score: {readiness_score}/100).
2. Die wichtigste strategische Empfehlung hervorhebt.
3. Den Quick Win nennt (sofort umsetzbar).
4. Die Investition ({budget_gesamt_jahr1} €) und den erwarteten ROI ({roi_realistisch}%) zusammenfasst.
5. Das Förderpotenzial ({foerder_potenzial} €) erwähnt.
6. Mit einem klaren Call-to-Action endet.

Zielgruppe: Geschäftsführer/Entscheider, die schnell den Kern erfassen wollen.

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

FORMAT: HTML-Fragment (<p> Tags). Keine Überschrift (wird vom Template gesetzt).
Maximal 300 Wörter. Kein Markdown. KEINE Quellenangaben.""",
}


# =============================================================================
# NÄCHSTE SCHRITTE TEMPLATE (static, not LLM-generated)
# =============================================================================

SECTION_TEMPLATE_NAECHSTE_SCHRITTE_SOLO = """
<ol>
    <li><strong>Strategiebericht durcharbeiten</strong> — Gehen Sie die Ergebnisse in Ruhe durch und identifizieren Sie die Quick Wins.</li>
    <li><strong>Quick Win starten</strong> — Beginnen Sie innerhalb der nächsten 2 Wochen mit dem identifizierten Quick Win. Niedrige Einstiegshürde, schnelles Ergebnis.</li>
    <li><strong>Fördermittel prüfen</strong> — Prüfen Sie die empfohlenen Förderprogramme und stellen Sie Anträge, bevor die Fristen ablaufen.</li>
    <li><strong>Tool-Evaluation</strong> — Testen Sie die empfohlenen Tools mit kostenlosen Testversionen oder Demos. Planen Sie 2-4 Wochen für die Evaluation ein.</li>
    <li><strong>Roadmap-Review</strong> — Planen Sie nach 3 Monaten (Ende Phase 1) ein Review ein, um Fortschritte zu bewerten und Phase 2 anzupassen.</li>
</ol>
<p><strong>Nächster Kontaktpunkt:</strong> Vereinbaren Sie ein kostenloses 30-Minuten-Strategiegespräch unter <a href="https://ki-sicherheit.jetzt/termin">ki-sicherheit.jetzt/termin</a>, um Fragen zum Bericht zu klären.</p>
"""

SECTION_TEMPLATE_NAECHSTE_SCHRITTE_TEAM = """
<ol>
    <li><strong>Strategiebericht durcharbeiten</strong> — Besprechen Sie die Ergebnisse mit Ihrem Team und identifizieren Sie die Quick Wins.</li>
    <li><strong>Quick Win starten</strong> — Beginnen Sie innerhalb der nächsten 2 Wochen mit dem identifizierten Quick Win. Niedrige Einstiegshürde, schnelles Ergebnis.</li>
    <li><strong>Fördermittel beantragen</strong> — Prüfen Sie die empfohlenen Förderprogramme und stellen Sie Anträge, bevor die Fristen ablaufen.</li>
    <li><strong>Tool-Evaluation</strong> — Testen Sie die empfohlenen Tools mit kostenlosen Testversionen oder Demos. Planen Sie 2-4 Wochen für die Evaluation ein.</li>
    <li><strong>Roadmap-Review</strong> — Planen Sie nach 3 Monaten (Ende Phase 1) ein Review ein, um Fortschritte zu bewerten und Phase 2 zu justieren.</li>
</ol>
<p><strong>Nächster Kontaktpunkt:</strong> Vereinbaren Sie ein kostenloses 30-Minuten-Strategiegespräch unter <a href="https://ki-sicherheit.jetzt/termin">ki-sicherheit.jetzt/termin</a>, um Fragen zum Bericht zu klären.</p>
"""

# Backward-compatible alias
SECTION_TEMPLATE_NAECHSTE_SCHRITTE = SECTION_TEMPLATE_NAECHSTE_SCHRITTE_TEAM
