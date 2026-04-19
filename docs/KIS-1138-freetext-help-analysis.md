# KIS-1138 — Proaktive Hilfestellung bei R1-Freitextfeldern

**Status:** Diagnose / Design-Vorbereitung für Review am Mittwoch (KW 17).
**Scope:** Nur R1-Chat-Intake. Strategy- und Coach-Chat bewusst ausgeklammert.
**Erstellt:** 2026-04-19 nach Abschluss der Bug-Bundle-Fixes (KIS-1160…1163).

---

## Kontext

Heute beobachteter User-Schmerz: Bei Freitext-Feldern tippen User
`"siehe oben"` / `"das will ich doch von dir wissen"` — nicht aus Faulheit,
sondern weil die Fragen („Wie soll Ihr Unternehmen in 2–3 Jahren mit KI
arbeiten?") ohne Kontext schwer zu beantworten sind. Folge:
unvollständige Datenerfassung → schwächerer Report. Zwei parallele Fixes
sind heute eingelaufen: KIS-1161 blockt `"siehe oben"` mit konstruktiver
Re-Ask-Phrase, KIS-1163 erkennt natürliche Rückfragen
(`"welche gibt es denn?"`) und routet sie durch den bestehenden
`build_help_context`-Flow. **Damit ist reaktive Hilfe gelöst**: wer fragt,
kriegt eine branchenspezifische Erklärung mit konkreten Stichworten.

Die noch offene Lücke ist **proaktive Hilfe**: der User soll gar nicht erst
in den Frust-Modus geraten. Heute muss er aktiv einen Hilfe-Button
klicken oder eine natürliche Rückfrage formulieren — beides setzt voraus,
dass er erkennt, dass er Hilfe braucht, und die richtige Form findet.
KMU-Entscheider ohne Tech-Hintergrund tun das im Zweifel nicht; sie
tippen `"siehe oben"` und hoffen auf das Beste.

Dieses Dokument bereitet die Design-Entscheidung am Mittwoch vor.
**Kein Code-Write.** Ziel: Wolf hat in ~30 Min am Mittwoch genügend
Entscheidungsgrundlage, um eine Variante zu wählen und einen klaren
Implementations-Auftrag zu geben.

---

## 1. Inventar der Freitextfelder im R1-Chat-Intake

R1 hat **7 Freitext-Felder** (`type="text"`, `chat_mode="FT"`). Ermittelt
aus `services/chat_normalizer.py` (`FIELD_REGISTRY`) und
`services/field_templates.py` (`SONNET_REQUIRED_FIELDS`).

| # | Feldname | Block / Phase | User-facing Frage (Sonnet formuliert live, hier FIELD_DESCRIPTION als Proxy) | Pflicht | Klassifikation |
|---|---|---|---|---|---|
| 1 | `hauptleistung` | Phase 1b (offenes Kennenlerngespräch, Section 0) | „Hauptdienstleistung oder wichtigstes Produkt — 2–3 Sätze" | **Pflicht** | **Concrete-experiential** — User beschreibt, was er heute tut. Faktisch, nicht strategisch. |
| 2 | `ki_projekte` | Phase 2, Block C (Section 3) | „Bestehende KI-Tests, Tools oder Projekte — auch informell" | Optional | **Concrete-experiential** — Liste / Aufzählung. Einfach wenn vorhanden, schwierig bei „noch nichts" (→ User blockiert oft). |
| 3 | `zeitersparnis_prioritaet` | Phase 2, Block C (Section 3) | „Welche Aufgabe kostet im Arbeitsalltag am meisten Zeit oder Nerven?" | **Pflicht** | **Concrete-experiential, aber reflexiv** — User muss seinen Alltag introspektieren. Borderline; typische Antworten sind kurz („Angebote schreiben"). |
| 4 | `geschaeftsmodell_evolution` | Phase 2, Block B (Section 3) | „Ideen, wie KI das Geschäftsmodell verändern könnte" | Optional | **Strategic-imaginative** — verlangt Zukunftsvision + strategisches Framing. Primäre Frust-Zone. |
| 5 | `vision_3_jahre` | Phase 2, Block B (Section 4) | „Wie soll das Unternehmen in 2–3 Jahren mit KI arbeiten?" | **Pflicht** | **Strategic-imaginative** — abstrakte Zukunftsprojektion. Primäre Frust-Zone. |
| 6 | `strategische_ziele` | Phase 2, Block B (Section 4) | „Was soll KI in 6–12 Monaten konkret verbessern?" | **Pflicht** | **Strategic-imaginative** — Roadmap-Denken. Primäre Frust-Zone. |
| 7 | `ki_guardrails` | Phase 2, Block B (Section 4) | „No-Gos oder sensible Themen beim KI-Einsatz" | Optional | **Strategic-imaginative / abstrakt** — User muss erkennen, wo seine roten Linien liegen. Viele wissen nicht, was „Guardrail" heißt. |

### Verteilung

- **Concrete-experiential (3):** `hauptleistung`, `ki_projekte`,
  `zeitersparnis_prioritaet` — User kann aus gelebter Erfahrung schöpfen.
  Hier sind Beispiele „inspiration enough to start typing".
- **Strategic-imaginative (4):** `geschaeftsmodell_evolution`,
  `vision_3_jahre`, `strategische_ziele`, `ki_guardrails` — verlangen
  Zukunfts-Imagination und/oder abstraktes Framing. Hier entsteht der
  beobachtete Frust. **Drei der vier liegen in Block B.**

### Wiederkehrendes Muster in Block B

Drei Block-B-Felder stellen semantisch ähnliche Fragen in verschiedener
zeitlicher Aufhängung (`geschaeftsmodell_evolution` = Geschäftsmodell-
Wirkung, `vision_3_jahre` = 3-Jahres-Bild, `strategische_ziele` =
6–12-Monats-Ziele). User der den ersten Satz geschrieben hat, empfindet
die beiden nächsten als Doppelung — genau das Verhalten, das KIS-1159
(Block-B-Konsolidierung) adressieren soll. KIS-1138 und KIS-1159
interagieren: proaktive Beispiele helfen, *andere Aspekte* zu
artikulieren, was das Überlapp-Gefühl reduziert. Selbst wenn KIS-1159
das Datenmodell konsolidiert, bleibt mindestens ein strategisches
Freitextfeld, das Inspiration braucht.

---

## 2. Code-Eingriffspunkte

Inventur der Stellen, die bei jeder Implementations-Variante relevant
sind. Lesen, nicht anfassen — dieses Ticket ist Recherche.

### Backend — Konfigurations-/Daten-Ebene

| Datei | Was dort lebt | Eingriffs-Kandidaten |
|---|---|---|
| `services/chat_normalizer.py` | `FIELD_REGISTRY` (type, required, section, chat_mode pro Feld), `SECTIONS` | Ggf. neues Feld-Attribut `has_examples: bool` — rein deklarativ, kein Verhalten. |
| `services/field_templates.py` | `SONNET_REQUIRED_FIELDS` (frozenset der R1-FT-Felder), `FIELD_QUESTIONS` (nur QR), `get_confirmation` | Natürlicher Platz für ein neues `FIELD_EXAMPLES: dict[str, list[str]]` mit 2–5 Beispielen pro FT-Feld. |
| `services/chat_conversation.py` | `FIELD_DESCRIPTIONS` (interner Sonnet-Kontext), `HELP_REQUEST_PROMPT`, `build_help_context`, `BLOCK_A/B/C/D_PROMPT`, `SECTION_HINTS` | `build_help_context` könnte `FIELD_EXAMPLES` mitliefern. Oder es entsteht eine neue `build_field_inspiration(field_name, collected)`-Funktion. |

### Backend — Flow-Ebene

| Datei | Was dort lebt | Eingriffs-Kandidaten |
|---|---|---|
| `routes/chat.py` | `_HELP_REQUEST_HINTS` (14 Pattern seit KIS-1163), `is_natural_help_request`, `_is_help_request`-Zuweisung, Response-Assembly (`_build_session_state`) | Response-Schema um `field_examples: list[str] \| None` erweitern, damit Frontend sie pro Turn rendert ohne neuen Request. |
| `schemas/chat.py` | `ChatSessionState`, `QuickReply`, `QuickReplyOption` | Neues Feld `field_examples` auf State oder auf einem dedizierten `InspirationHint`-Objekt neben `quick_replies`. |

### Backend — Bestehende Help-Infrastruktur (reaktiv, seit heute funktional)

- **Trigger-Pfad:** `routes/chat.py:646` — `_is_help_request = ("__HELP_REQUEST__" in req.message) or (not _is_qr_click and is_natural_help_request(req.message))`.
- **Skip-Pfad:** Haiku-Extractor wird übersprungen; `_no_extraction = True`.
- **Prompt-Builder:** `chat_conversation.py::build_help_context(field_name, collected, rt)` → formatiert `HELP_REQUEST_PROMPT` mit Branche, Größe, Hauptleistung, KI-Erfahrungslevel.
- **Sonnet-Output:** Reflexionsfragen + 2–3 „Denkanstoß"-Stichworte, **explizit keine kopierbaren Beispiele** (Prompt-Regel auf `chat_conversation.py:1015-1017`).

### Wichtige Design-Spannung im Bestand

`HELP_REQUEST_PROMPT` enthält wörtlich:

> „Gib KEINE fertigen Antworten vor, die der Nutzer kopieren könnte.
> Gib KEINE Listen mit konkreten Beispielen ('Typische No-Gos sind: …').
> Stattdessen: Stelle Reflexionsfragen."

Das ist die ursprüngliche Design-Philosophie des Systems: **User soll
nachdenken, nicht kopieren**. Steht im **direkten Widerspruch** zum
beobachteten Schmerz („gib mir ein Beispiel, damit ich weiß, was gemeint
ist"). Jede Implementation von KIS-1138 impliziert eine Entscheidung zu
dieser Philosophie — siehe Abschnitt 5, Frage #1.

### Frontend (separates Repo `make-ki-frontend`)

Nicht in diesem Repo verfügbar, daher nur Referenz-Annahmen aus
Backend-Contract:

- **Help-Button:** injiziert aktuell die Sentinel-Message
  `__HELP_REQUEST__` in eine normale `/api/chat/message` POST. Backend
  seit KIS-1163 auch auf natürliche Formulierungen sensibel.
- **Input-Feld:** rendert pro Assistant-Turn mit Textarea + Send-Button,
  optional QR-Buttons.
- **Keine Telemetrie** im Backend über Help-Button-Nutzung — wie oft
  geklickt wird, ist heute blind. Das ist für die Variantenwahl
  relevant: wir wissen nicht, wie viele User den Button ignorieren.

### Keine Eingriffe in diesem Ticket

- R1-Report-Pipeline (konsumiert die Freitexte am Ende; welche Form
  ankommt, ändert sich nicht wenn wir die UX-Schicht verbessern).
- Strategy- und Coach-Chat (getrennte Flows, eigener Scope).
- Haiku-Extractor (transformiert nur, Inspiration ist Frontend-/
  State-Ebene).

---

*Commit 1 von 3 — nächste Abschnitte (Design-Varianten; Empfehlung +
offene Fragen + Nebenbefunde) folgen in separaten Commits.*

---

## 3. Design-Varianten

Drei Hauptvarianten, wobei **C die proaktive Haupt-Variante ist** und in
drei Sub-Ansätze zerfällt. A und B sind reaktive Baselines zum
Vergleich; A bleibt ohnehin als Fallback relevant, weil der bestehende
Help-Button-Flow aus KIS-1163 diese Form bereits nutzt.

### Variante A — Reaktiv, hardcoded (Minimal)

**Form:** Hilfe-Button neben Input; Klick zeigt 2–4 kurze Beispiel-Sätze
in einer zweiten Bubble. Beispiele sind pro Feld fest codiert, analog zu
`FIELD_QUESTIONS` in `field_templates.py`.

**Aufwand Backend (≈4 h):**
- Neues `FIELD_EXAMPLES: dict[str, list[str]]` in `services/field_templates.py` für die 7 FT-Felder (je 3–4 Beispiele).
- `build_help_context` in `chat_conversation.py` um optionales `examples=`-Argument erweitern.
- `HELP_REQUEST_PROMPT` um einen optionalen Abschnitt „BEISPIEL-ANTWORTEN (darfst du wörtlich zitieren)" ergänzen — **und die aktuelle Anti-Kopier-Regel entschärfen oder auf Strategic-Imaginative-Felder eingrenzen**.
- Unit-Tests: Pro Feld-Kategorie 1 Beispiel-Inhalt vorhanden + korrekte Länge.

**Aufwand Frontend (≈2 h):**
- Help-Button existiert schon und triggert `__HELP_REQUEST__`. Nur Rendering der Beispiele in der Antwort-Bubble (Sonnet liefert sie im Text, kein strukturelles Change am Response nötig).

**Risiken:**
- Beispiele altern — KMU-Sprache ändert sich über Monate, Pflegeaufwand muss jemand tragen.
- User klickt den Button nicht (heute schon Kernproblem) → Wirkung bleibt gering.
- Hardcoded Beispiele klingen potenziell generisch, wenn sie nicht branchenspezifisch sind.

**Design-Fragen an Wolf:**
- Branchen-agnostische Beispiele (einfacher, 1 Liste pro Feld) oder branchen-spezifisch (13 × 7 = 91 Listen, Maintenance-Problem)?
- Max-Länge pro Beispiel (1 Satz / 2 Sätze / Stichwort-Liste)?

**Technische Voraussetzungen:** keine, alle Bausteine existieren.

---

### Variante B — Reaktiv, LLM-generiert (Smart)

**Form:** Hilfe-Button → Backend ruft Sonnet mit Feldname + Branche +
Hauptleistung + KI-Erfahrungslevel + 3 letzte collected_fields auf, lässt
3 kontextuelle Beispiele generieren, die genau auf den User passen.

**Aufwand Backend (≈6 h):**
- Neuer Prompt `FIELD_EXAMPLES_PROMPT` in `chat_conversation.py`: Feld-Beschreibung + User-Kontext + Regeln (kurz, branchenspezifisch, keine Hallu bei Zahlen).
- Neuer Endpoint oder Seiten-Pfad: z. B. `POST /api/chat/examples/{field}?session_id=…` — oder Inline im `__HELP_REQUEST__`-Flow, dann bleibt die Oberfläche gleich.
- Caching pro `(field, branche)` im Session-Zustand, damit ein zweiter Klick nicht nochmal Latenz produziert.
- Unit-Tests: Prompt-Format-Regression + Mock-Sonnet-Antwort deserialisiert korrekt.

**Aufwand Frontend (≈2 h):** wie Variante A; bei separatem Endpoint
zusätzlich ein `fetch`-Handler + Loading-State.

**Risiken:**
- **Latenz:** Sonnet-Call = ~2–4 s; User wartet nach Button-Klick.
- **Kosten:** zusätzlicher Sonnet-Call pro Help-Klick (R1-typisch 7–10 FT-Turns → im Schnitt 1–2 Hilfe-Klicks = 1–2 Extra-Calls pro Session).
- **Halluzinationen:** Sonnet erfindet Zahlen/Namen; für DSGVO-Felder (nicht in FT-Liste, aber denkbar falls Scope wächst) besonders heikel.
- **Bruch mit TÜV-Seriosität:** KI-generierte „Beispiele von Ihrem Unternehmen" wirken bei einem TÜV-zertifizierten Tool befremdlich; User könnte das als „hat mir einer was vorgesagt?" interpretieren.

**Design-Fragen an Wolf:**
- Beispiele als Vorschlag (User modifiziert) oder reine Inspiration (User tippt frei)?
- Wie oft darf derselbe User bei demselben Feld Beispiele anfordern? (Cooldown ja/nein)

**Technische Voraussetzungen:** Sonnet-Client (existiert), zusätzliches
Prompt-Template, neues Feld in SessionState für Cache, ggf. separater
Endpoint mit eigenem Rate-Limit.

---

### Variante C — Proaktiv, inline (HAUPTVARIANTE)

**Gemeinsames Prinzip:** Inspiration ist bei Frage-Erscheinen bereits
sichtbar, User muss nichts anklicken. Drei Sub-Ansätze, deren Aufwand
und UX-Charakter sich deutlich unterscheiden.

#### C1 — Beispiel-Chips unter dem Input

**Form:** Direkt unter dem Eingabefeld erscheinen 3–5 graue Chips mit
Kurzbeispielen („Angebote automatisieren", „Reporting beschleunigen",
„Neukundengewinnung per Content"). Klick auf Chip = **Autofill in das
Input-Feld** (User kann dann weiter bearbeiten oder direkt absenden).

**Aufwand Backend (≈3 h):**
- `FIELD_EXAMPLES` wie Variante A.
- Response-Schema: neues Feld `field_examples: list[str] | None` auf
  `ChatSessionState` (oder dediziertes `InspirationHint`-Objekt neben
  `quick_replies`).
- `_build_session_state` in `routes/chat.py` befüllt es, wenn das
  nächste Feld FT ist und Examples vorhanden sind.
- Unit-Tests: Examples reichen bis zur Wire-Ebene; QR-Turns setzen sie
  auf `None`.

**Aufwand Frontend (≈4 h):**
- Neue UI-Komponente unterhalb Input; Klick-Handler = Textarea-Prefill.
- Chips dürfen nicht versehentlich als Send-Button wirken.
- Optional: Chip ausblenden sobald User zu tippen anfängt (Anti-Clutter).

**Risiken:**
- **Anchoring-Bias:** User kopiert das erste Chip statt eigene Antwort zu
  formulieren — Report-Qualität sinkt auf „Kopierbare-Beispiele"-Niveau.
- **UI-Clutter:** zusätzliche Fläche unter Input; auf Mobile knapp.
- **Erscheinen-Zeitpunkt:** wenn Chips gleichzeitig mit Sonnet-Token-
  Stream auftauchen, kann Layout-Sprung entstehen.

**Design-Fragen an Wolf:**
- Chip-Verhalten: Autofill (User kann bearbeiten) vs. reine Inspiration
  (nicht klickbar, nur grau zur Ansicht) vs. Direkt-Einsenden?
- Chip-Anzahl konstant (3) oder variabel (je nach Feld, 2–5)?
- Disclosure-Label: „Beispiele", „Inspiration", „So könnte eine Antwort
  aussehen", „Schreibhilfe"?

#### C2 — Smart Placeholder (rotierend)

**Form:** Der `placeholder`-Text im Input-Feld selbst zeigt ein
Beispiel, wechselt alle 3–4 Sekunden durch eine Liste. Sobald User
tippt, verschwindet er (Standard-HTML-Verhalten).

**Aufwand Backend (≈2 h):** wie C1, nur Liste statt einzelner Strings;
Frontend wählt selbst die Rotation.

**Aufwand Frontend (≈2 h):** `setInterval` für Placeholder-Rotation, Cleanup bei Input-Event.

**Risiken:**
- **Accessibility:** bewegter Placeholder ist für Screenreader und einige
  User mit kognitiven Einschränkungen ablenkend / unzugänglich; WCAG
  empfiehlt keine autorotating Texte ohne Pause-Option.
- **Lesbarkeit:** Placeholder in vielen Designs sehr hell (Kontrast ≥ 4.5:1
  nicht erfüllt) — bei beispielhaften Inhalten riskant.
- **Vergessen nach Fokus:** beim ersten Klick verschwindet der
  Placeholder, User hat keine Möglichkeit, die Beispiele nochmal zu
  sehen ohne das Feld zu leeren.

**Design-Fragen an Wolf:**
- Rotation überhaupt (a11y-Risiko) oder statischer Placeholder mit nur
  einem Beispiel?
- Fallback: Button „Beispiele anzeigen" neben Input als Escape-Hatch?

#### C3 — Inline-Graulauf in der Fragestellung

**Form:** Sonnet formuliert die Frage so, dass Beispielantworten als
grauer (CSS-styled) Nachsatz sichtbar sind. Beispiel:

> *„Was soll KI in den nächsten 6–12 Monaten konkret verbessern?"*
> *(z. B. Angebote automatisieren · Reporting-Zeit halbieren · Inbound-Qualität steigern)*

**Aufwand Backend (≈3 h):**
- Beispiele fließen in `FIELD_DESCRIPTIONS` oder ein neues
  `FIELD_EXAMPLES` ein.
- `BLOCK_B_PROMPT` (und für Block-C-Freitexte `BLOCK_C_PROMPT`) werden
  um eine Regel erweitert: „Wenn das nächste Feld ein Strategic-FT-Feld
  ist, hänge 3 kurze Beispiele an, getrennt durch `·`, in Klammern."
- Unit-Tests: Prompt enthält die Beispiel-Regel; Content-Assertion auf
  generierte Sonnet-Output-Form ist nicht stabil (Sonnet variiert).

**Aufwand Frontend (≈3 h):**
- CSS für die Grau-Formatierung — Sonnet könnte Markdown (`*…*`) oder
  einen dedizierten Marker-Tag (`<em class="hint">…</em>`) liefern. Das
  ist das kritische Design-Detail: wie bringt man das Frontend dazu, den
  Nachsatz anders zu formatieren als den eigentlichen Fragetext?
- Anti-Race: Beispiele dürfen nicht im Text-Replace-Schritt (KIS-1124
  `_post_process_response`) herausgefiltert werden.

**Risiken:**
- **Sonnet-Drift:** die LLM folgt Format-Anweisungen nicht konsistent,
  besonders nach mehreren hundert Turns im Gespräch. Beispiele kommen
  nicht immer oder nicht im richtigen Format.
- **Parsing-Fragilität:** Frontend muss zuverlässig erkennen, welcher
  Teil „grauer Hinweis" ist. Marker können vom Sonnet vergessen werden.
- **Token-Kosten:** mehr Prompt-Text + längere Sonnet-Antwort pro Turn.
- **Inkonsistenz:** bei manchen Turns kommen Beispiele, bei anderen
  nicht — User empfindet das als „mal gibt er mir Beispiele, mal
  nicht", fühlt sich weniger professionell.

**Design-Fragen an Wolf:**
- Marker-Convention: Markdown-`*kursiv*`, HTML-Tag, oder Unicode-
  Trenner (`·`, `—`)? Welches überlebt den Stream + Post-Processing
  zuverlässig?
- Nur bei FT-Feldern oder auch bei QR-Feldern (wo die QR-Optionen
  eigentlich selbst schon Beispiele darstellen)?

### Sub-Varianten-Vergleich (C1 vs C2 vs C3)

| Kriterium | C1 (Chips) | C2 (Placeholder) | C3 (Inline-Graulauf) |
|---|---|---|---|
| Sichtbarkeit ohne Klick | ✅ hoch | 〜 mittel (rotierend) | ✅ hoch |
| Autofill / Schnell-Start | ✅ ja | ❌ nein | ❌ nein |
| Mobile-tauglich | 〜 enge Chips | ✅ kein zusätzlicher Platz | ✅ im Text |
| Backend-Aufwand | 3 h | 2 h | 3 h |
| Frontend-Aufwand | 4 h | 2 h | 3 h |
| Anti-Clutter | 〜 | ✅ | ✅ |
| Accessibility | ✅ sauber | ❌ Rotation problematisch | ✅ sauber |
| Deterministik | ✅ (hardcoded) | ✅ (hardcoded) | 〜 LLM-abhängig |
| Anchoring-Bias | **hoch** (Klick = Kopie) | niedrig | niedrig (weniger aktiv) |
| Rollback-Trivialität | ✅ (Feld auf None) | ✅ | 〜 (Prompt-Rückbau) |

---

*Commit 2 von 3 — letzter Abschnitt (Empfehlung, offene Fragen,
Nebenbefunde) folgt separat.*
