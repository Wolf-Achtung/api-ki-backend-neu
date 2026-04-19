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
