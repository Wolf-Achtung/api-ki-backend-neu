Developer:
<!-- PLATIN++ PROMPT v5.2 -->
<!-- SECTION: ki_rechte_kennzeichnung -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{MEDIEN_SPARTE_LABEL}}, {{hauptleistung}}, {{ki_guardrails}}, {{COMPANY_SIZE}} -->
<!-- TOKEN-BUDGET: 900 (solo:0.8x=720, team:1.0x=900, kmu:1.15x=1035) -->
<!--
ZIEL: Das Differenzierungs-Kapitel für Medien-/Entertainment-Kunden — konkrete,
umsetzbare Leitplanken zu Rechten und Kennzeichnung beim KI-Einsatz in
Produktion und Verwertung. Kein Jura-Traktat, sondern Produktionsalltag.

PFLICHTSTRUKTUR (4 Blöcke):
1. Rechtekette bei KI-Material (2-3 Absätze oder Liste):
   - Verwertbarkeit von KI-Output (Schutzfähigkeit ungeklärt — was das für
     Buyouts, Lizenzierung und Stock-Verwertung bedeutet)
   - Training/Input: kein Kundenmaterial oder ungeklärtes Fremdmaterial in
     öffentliche Tools; TDM-Vorbehalte respektieren
   - Dokumentationspflicht: pro Projekt festhalten, welches Asset mit welchem
     Tool und welcher Lizenz entstanden ist
2. Stimme, Gesicht, Persönlichkeitsrechte (1-2 Absätze):
   - Klone/Digital Doubles/Synthese NUR mit ausdrücklicher, dokumentierter
     Einwilligung; Umfang (Projekte, Laufzeit, Medien) vertraglich festlegen
   - Bestandsverträge decken KI-Nutzung meist NICHT ab — Klauseln nachrüsten
3. Kennzeichnung nach EU AI Act Art. 50 (1-2 Absätze + Mini-Prozess):
   - Wann synthetische/KI-generierte Inhalte zu kennzeichnen sind
     (Deepfake-Regel; redaktionelle/künstlerische Einordnungen erwähnen)
   - Konkreter 3-Schritte-Prozess: erfassen → entscheiden → kennzeichnen
     (wer entscheidet, wo dokumentiert)
4. Checkliste "Vor jeder Auslieferung" (5-7 Punkte, als Liste):
   konkret ankreuzbar, auf {{hauptleistung}} bezogen

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: Selbst-Checkliste, einfache Vertrags-Bausteine, keine Prozesse-Bürokratie
- team: klare Zuständigkeit (wer prüft Rechte/Kennzeichnung vor Delivery)
- kmu: dokumentierter Freigabeprozess, Rechte-Register, Vertragsstandards

KONTEXTBEZUG:
- Wenn {{MEDIEN_SPARTE_LABEL}} vorhanden: Beispiele auf die Sparte zuschneiden
  (Produktion: Darsteller/Archiv; Post/VFX: Referenzmaterial/Upscaling-Quellen;
  Games: Assets/Store-Deklaration; Verlag: Text-/Bildrechte, Leser-Transparenz;
  Musik/Audio: Stimmen/Samples; Agentur: Kundenfreigaben/Werbekennzeichnung;
  Content Creation: Plattform-Kennzeichnungspflichten, Persönlichkeitsrechte
  bei Stimme/Gesicht, Sponsoring-Transparenz)
- Vorhandene Guardrails des Kunden ({{ki_guardrails}}) anerkennen und
  gezielt ergänzen statt wiederholen.

ANTI-REDUNDANZ / THEMEN-OWNERSHIP (verbindlich):
- Diese Section: OWNER für Rechtekette, Einwilligungen, Art.-50-Kennzeichnung
- NICHT hier: allgemeine AI-Act-Risikoklassen und Fristen (→ ai_act_summary)
- NICHT hier: allgemeine Nutzungsregeln (→ ai_policy_mini)
- NICHT hier: DSGVO-Basics (→ data_readiness)

STIL:
- Textumfang: 300-450 Wörter
- Konkret, produktionsnah, keine juristischen Floskeln
- Explizit: "keine Rechtsberatung — für Verträge Fachanwalt einbinden" (1 Satz)
- Keine erfundenen Paragraphen-Details über Art. 50 und § 44b UrhG hinaus

Nicht verwenden:
- Keine Platzhalter oder Template-Marker
- Keine Scheinpräzision zu ungeklärten Rechtsfragen
-->

<section class="section ki-rechte-kennzeichnung">
  <h2>KI-Rechte &amp; Kennzeichnung in der Produktion</h2>

  <p>
  [Block 1: Rechtekette bei KI-Material — konkret für {{hauptleistung}}]
  </p>

  <h3>Stimme, Gesicht, Persönlichkeitsrechte</h3>
  <p>
  [Block 2]
  </p>

  <h3>Kennzeichnung synthetischer Inhalte (EU AI Act Art. 50)</h3>
  <p>
  [Block 3 inkl. 3-Schritte-Prozess]
  </p>

  <h3>Checkliste: Vor jeder Auslieferung</h3>
  <ul>
    <li>[5-7 ankreuzbare Punkte]</li>
  </ul>
</section>

<!-- FIX-KIS-1246: Expliziter Kontext-Block — das Modell hat ALLE nötigen
     Angaben und darf NIE mit einer Rückfrage antworten. -->

VORLIEGENDER UNTERNEHMENSKONTEXT (vollständig — keine Rückfragen nötig):
- Branche: {{BRANCHE_LABEL}} · Sparte: {{MEDIEN_SPARTE_LABEL}}
- Unternehmensgröße: {{COMPANY_SIZE}} ({{UNTERNEHMENSGROESSE_LABEL}})
- Hauptleistung: {{hauptleistung}}
- Vorhandene KI-Leitplanken des Kunden: {{ki_guardrails}}

VERBINDLICH: Antworte ausschließlich mit dem fertigen HTML-Abschnitt gemäß
Pflichtstruktur. Stelle unter keinen Umständen Rückfragen, bitte nie um
weitere Angaben und erkläre nie, was dir fehlt — alle benötigten
Informationen stehen oben.
