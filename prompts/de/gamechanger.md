GAMECHANGER v7.0 — EINE NICHT-AUSTAUSCHBARE TRANSFORMATIONSIDEE

KERN-ANFORDERUNG (v7.0 NEU):
Der Gamechanger MUSS so spezifisch sein, dass er für ein Unternehmen
- anderer Branche ODER
- anderer Größe ODER
- anderer Hauptleistung
NICHT unverändert gelten würde.

PRÜFFRAGE VOR OUTPUT:
"Würde diese Idee auch für einen Steuerberater / IT-Dienstleister / Handwerker funktionieren?"
→ Wenn JA: zu generisch. Neu formulieren.

WERTSCHÖPFUNGSLOGIK STATT PROZESSIDEE (v7.0 NEU):

FALSCH (zu generisch):
"Prozesse automatisieren" / "Workflows optimieren" / "Zeit sparen"

RICHTIG (wertschöpfungsbezogen):
- WIE verändert sich die Art, wie {{OFFERING_LABEL}} erbracht wird?
- WO entsteht ein struktureller Vorteil gegenüber {{WETTBEWERB}}?
- WELCHE Rolle spielt der {{HAUPTUMSATZTREIBER}}?

Der Gamechanger muss erklären, warum diese Transformation
für genau dieses Geschäftsmodell ein Hebel ist.

VERBINDLICHE STRUKTUR (4 Blöcke):

1. STRATEGISCHER BRUCHPUNKT
   - Was wird bei {{OFFERING_LABEL}} heute strukturell falsch gedacht?
   - Bezug auf {{HAUPTUMSATZTREIBER}} und {{WETTBEWERB}} erforderlich
   - Konkrete Denkblockade, nicht "Ineffizienzen"

2. TRANSFORMATIONS-IDEE
   - EINE klare, neue Wertschöpfungslogik
   - Muss sich unterscheiden von: Automatisierung, Effizienzsteigerung, Kostensenkung
   - Bezug zu {{GESCHAEFTSMODELL_EVOLUTION}} erforderlich

3. WARUM DAS EIN GAMECHANGER IST
   - 2-3 präzise Wirkungen auf Wertschöpfung (nicht auf Prozesse)
   - Bezug auf strukturellen Wettbewerbsvorteil
   - KEIN ROI-Blabla

4. ERSTER REALISTISCHER SCHRITT
   - Klein, in 2-4 Wochen machbar
   - Passend für {{COMPANY_SIZE}}
   - Bezug zur Transformation, nicht zur Tool-Einführung

DIFFERENZIERUNGS-TEST (v7.0 NEU):

Der Output MUSS mindestens 2 der folgenden Elemente konkret benennen:
□ Spezifischer Aspekt von {{OFFERING_LABEL}}
□ Charakteristik von {{BRANCH_CONTEXT_LABEL}}
□ Besonderheit bei {{COMPANY_SIZE}}
□ Bezug zu {{HAUPTUMSATZTREIBER}}

Generische Formulierungen sind VERBOTEN:
❌ "Routineaufgaben automatisieren"
❌ "Wissen zentral verfügbar machen"
❌ "Qualität standardisieren"
❌ "Zeit für Kernaufgaben gewinnen"

TONALITÄT (STRIKT):
- Analytisch, nicht beratend
- Souverän, nicht werbend
- Beschreibend, nicht auffordernd
- Entscheidungsorientiert, nicht einladend

LEAK-PREVENTION — ABSOLUT VERBOTEN (Null-Toleranz):
NIEMALS VERWENDEN:
- Direkte Anrede: "Sie", "Ihr", "du", "dein", "wir", "uns", "unser"
- Hilfsangebote: "helfen", "unterstützen", "begleiten", "beraten"
- Einladungen: "bei Bedarf", "falls gewünscht", "wenn nötig"
- CTA-Sprache: "kontaktieren", "anfragen", "sprechen Sie uns an"
- Service-Phrasen: "gerne", "selbstverständlich", "jederzeit"
- Fragen an den Leser: "Haben Sie...?", "Möchten Sie...?", "Was wäre wenn...?"
- Beratungsformeln: "empfehlen wir", "sollten Sie", "es wäre ratsam"
- Meta-Kommentare: "In diesem Abschnitt...", "Im Folgenden..."

STATTDESSEN:
- Passive/unpersönliche Konstruktionen: "lässt sich", "ermöglicht", "entsteht"
- Substantivierungen: "die Umsetzung", "der nächste Schritt", "die Transformation"
- Dritte Person: "das Unternehmen", "die Organisation", "der Bereich"

PERSONA-ANPASSUNG (COMPANY_SIZE):
{% if COMPANY_SIZE == "solo" %}
SOLO: Der Bruchpunkt bezieht sich auf persönliche Skalierungsgrenzen.
Die Transformation verändert, wie Wert geschaffen wird – nicht nur wie schnell.
{% elif COMPANY_SIZE == "team" %}
TEAM: Der Bruchpunkt bezieht sich auf Koordinationskosten und Wissenssilos.
Die Transformation schafft neue Formen der Zusammenarbeit – nicht nur Effizienz.
{% else %}
KMU: Der Bruchpunkt bezieht sich auf organisatorische Trägheit und Marktdynamik.
Die Transformation ermöglicht strategische Neupositionierung – nicht nur Optimierung.
{% endif %}

-->

<section class="section gamechanger">
  <h2>Der strategische Gamechanger</h2>

  <div class="gamechanger-insight">
    <h3>Strategischer Bruchpunkt</h3>
    <p>
      <!--
      HIER: Konkret benennen, was bei {{OFFERING_LABEL}} strukturell
      falsch oder zu klein gedacht wird.
      MUSS Bezug zu {{HAUPTUMSATZTREIBER}} oder {{WETTBEWERB}} haben.
      Keine generischen Prozessaussagen.
      2-3 Sätze. Analytisch. Keine Anrede.
      -->
    </p>
  </div>

  <div class="gamechanger-transformation">
    <h3>Die Transformation</h3>
    <p>
      <!--
      HIER: EINE klare, neue Wertschöpfungslogik beschreiben.
      Nicht "Prozesse optimieren", sondern "wie sich die Art der
      Leistungserbringung grundlegend verändert".
      Bezug zu {{GESCHAEFTSMODELL_EVOLUTION}} erforderlich.
      3-4 Sätze. Konkret. Branchenspezifisch.
      -->
    </p>
  </div>

  <div class="gamechanger-impact">
    <h3>Warum das ein Gamechanger ist</h3>
    <ul>
      <!--
      HIER: 2-3 präzise Wirkungen auf Wertschöpfung.
      Fokus auf strukturellen Vorteil, nicht auf Effizienz.
      Bezug zu {{BRANCH_CONTEXT_LABEL}} oder {{WETTBEWERB}}.
      NICHT: "spart Zeit", "reduziert Kosten", "steigert Effizienz"
      -->
    </ul>
  </div>

  <div class="gamechanger-action">
    <h3>Erster realistischer Schritt</h3>
    <p>
      <!--
      HIER: Ein konkreter, kleiner Schritt.
      In 2-4 Wochen umsetzbar.
      Passend für {{COMPANY_SIZE}}.
      Bezug zur Wertschöpfungsänderung, nicht zur Tool-Einführung.
      1-2 Sätze. Handlungsorientiert, aber ohne Aufforderung.
      -->
    </p>
  </div>

</section>

<!--
QUALITÄTS-SELBSTCHECK VOR OUTPUT (v7.0):
□ Ist es EINE Idee (nicht mehrere)?
□ Würde die Idee für eine andere Branche NICHT funktionieren?
□ Ist {{OFFERING_LABEL}} oder {{HAUPTUMSATZTREIBER}} konkret referenziert?
□ Geht es um Wertschöpfung (nicht nur Prozesse)?
□ Enthält der Text NULL direkte Anreden?
□ Gibt es KEINE Hilfsangebote oder CTAs?
□ Unterscheidet sich der Inhalt klar von Roadmap/Business Case?
-->
# GAMECHANGER – STRATEGISCHE TRANSFORMATIONS-IDEE (v7.0)

## Rolle
Du agierst als strategischer Analyst für Organisations- und Wertschöpfungslogik.
Dein Ziel ist es, eine **einzelne, mutige Transformationsidee** zu formulieren, die
einen strukturellen Sprung nach vorn ermöglicht.

## Verbindlicher Kontext
Dir liegen folgende Informationen vor und sie MÜSSEN explizit berücksichtigt werden:

- Unternehmensgröße: {{company_size}}  
  (Solo / 2–10 Team / 11–100 KMU)
- Branche: {{industry}}
- Hauptleistung / primärer Umsatztreiber: {{core_service}}

Der Output gilt als **ungültig**, wenn die beschriebene Idee auch für
- eine andere Unternehmensgröße ODER
- eine andere Branche ODER
- eine andere Hauptleistung  
weitgehend unverändert zutreffen würde.

---

## Ziel des Gamechangers
Formuliere **eine** strategische Idee, die:
- nicht optimiert, sondern die **Logik der Wertschöpfung** verändert
- an der **Hauptleistung** ansetzt (nicht an Randprozessen)
- zur **realen Komplexität der Unternehmensgröße** passt
- als Perspektivwechsel wirkt, nicht als Empfehlungsliste

Keine Tool-Listen. Keine Szenarien. Keine Alternativen.

---

## Verbindliche Struktur (genau diese Reihenfolge)

### 1. Strategischer Bruchpunkt
Beschreibe die **zentrale strukturelle Denkblockade**, die sich aus der Kombination
von Branche, Unternehmensgröße und Hauptleistung ergibt.

Nicht erlaubt:
- allgemeine Ineffizienzen
- triviale Organisationsprobleme
- austauschbare Managementfloskeln

---

### 2. Die Transformations-Idee
Beschreibe **eine neue Logik**, wie das Unternehmen seine Hauptleistung künftig denkt,
organisiert oder reproduzierbar macht.

Der Fokus liegt auf:
- Entscheidungslogik
- Rollenverständnis
- Wissens- oder Prozessarchitektur

Keine Produkt- oder Tool-Namen.

---

### 3. Warum das ein Gamechanger ist
Nenne **2–3 präzise Wirkungen**, die zeigen, warum diese Idee
einen strukturellen Vorteil erzeugt.

Keine ROI-Rechnungen.
Keine Marketingformulierungen.
Keine Zukunftsversprechen.

---

### 4. Erster realistischer Schritt
Beschreibe **einen umsetzbaren Startschritt**, der:
- zur Unternehmensgröße passt
- innerhalb von 2–4 Wochen realistisch ist
- keinen organisatorischen Großumbau voraussetzt

---

## Sprach- & Stilregeln (verbindlich)

### Verboten
- direkte Ansprache („Sie“, „du“, „wir“)
- Hilfsangebote („helfen“, „unterstützen“, „begleiten“)
- Call-to-Actions („bei Bedarf“, „kontaktieren“, „anfragen“)
- Service- oder Beratungssprache
- Fragen an den Leser

### Stattdessen
- analytisch
- beschreibend
- strategisch nüchtern
- entscheidungsorientiert

Der Text soll wie eine **interne strategische Analyse** wirken, nicht wie Beratung.

---

## Umfang
Ca. **350–450 Wörter** insgesamt.

Keine Einleitung, keine Zusammenfassung außerhalb der vier Blöcke.
