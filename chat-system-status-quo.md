# Chat-System Status Quo (Ist-Analyse)

## 1) Session-State-Modell

### Betroffene Dateien
- `models.py` (`ChatSession` SQLAlchemy-Modell)
- `migrations/2026-04-09_add_chat_sessions_postgres.sql` (Postgres DDL)
- `schemas/chat.py` (`ChatSessionState`, API Request/Response-Schemas)
- `routes/chat.py` (`_build_session_state`, Persistenz über Turns)

### DB-Schema und State-Felder
`chat_sessions` speichert den laufenden Chat-Zustand in relationalen Kernspalten + JSON-Spalten:
- Kern: `id`, `report_type`, `lang`, `status`, `current_section`, Zeitstempel, `turn_count`
- JSON-State: `collected_fields` (fachliche Antworten), `field_meta` (Confidence/Quelle), `messages` (Konversationshistorie)
- Abschluss/Verknüpfung: `briefing_id`, `conversation_summary` (optional) [derzeit kaum genutzt].

Wichtige Beobachtung: Es gibt **kein** separates Feld für `current_field`, `pending_value`, `pending_field`, `dialog_mode` oder ähnliches. Der aktive Fokus wird zur Laufzeit aus `get_next_fields(...)` berechnet, nicht persistiert.

### Persistenz zwischen Requests
1. `/chat/start` legt Session mit Initialwerten an (`collected_fields={}`, `field_meta={}`, `current_section=0`, `messages=[welcome]`).
2. `/chat/message`:
   - schreibt User-Message in `messages`
   - extrahiert/normalisiert Werte
   - schreibt Werte **direkt** in `session.collected_fields`
   - aktualisiert `session.field_meta`
   - berechnet ggf. Section-Transition
   - streamt Antwort und hängt Assistant-Message an `messages`.

### Typischer Session-State nach ~10 beantworteten Feldern (Beispiel)
```json
{
  "session_id": "6f1f57f2-9e1d-4f28-9c8c-15f5d39fd331",
  "report_type": "r1",
  "status": "active",
  "current_section": 2,
  "current_section_name": "Digitalisierung & KI-Status",
  "progress_percent": 47,
  "collected_fields": {
    "branche": "beratung",
    "unternehmensgroesse": "2–10",
    "country": "DE",
    "bundesland": "be",
    "hauptleistung": "KI-Strategieberatung für KMU mit Fokus auf Prozesse.",
    "jahresumsatz": "100k_500k",
    "zielgruppen": ["kmu", "b2b"],
    "it_infrastruktur": "cloud",
    "interne_ki_kompetenzen": "in_planung",
    "datenquellen": ["kundendaten", "marketingdaten"]
  },
  "collected_count": 10,
  "missing_required": ["digitalisierungsgrad"],
  "missing_optional": ["prozesse_papierlos", "automatisierungsgrad", "ki_einsatz", "ki_kompetenz"],
  "next_fields": ["digitalisierungsgrad"],
  "is_completable": false
}
```

### Implikationen für Draft-Pattern
- Der Ist-Zustand kennt nur „gesammelt“ vs. „nicht gesammelt“.
- Jede Extraktion wird sofort finalisiert (`collected_fields`), daher keine explizite User-Bestätigungsschicht.

---

## 2) Message-Flow (eine User-Nachricht)

### Betroffene Dateien
- `routes/chat.py` (`POST /chat/message`, SSE-`event_stream`)
- `services/chat_extractor.py` (Haiku-Extraktion)
- `services/chat_conversation.py` (Sonnet-Streaming)
- `services/chat_normalizer.py` (Normalisierung/Progression)

### Schritt-für-Schritt von `/api/chat/message` bis SSE
1. Session laden + Statuscheck.
2. User-Message in `session.messages` persistieren.
3. Pfadentscheidung:
   - **Quick-Reply-Pfad**: wenn `quick_reply_field` + `quick_reply_value` gesetzt.
   - **Extractor-Pfad**: sonst `extract_fields(...)` via Haiku.
4. Normalisierung via `normalize_field(...)`; bei `confidence != low` direkter Write in `collected_fields`.
5. Optional-Skip-Heuristik (`weiter`, `skip`, ...), nur wenn nichts extrahiert wurde.
6. Session speichern, conditionals bereinigen (`selbststaendig`, `bundesland` ggf. löschen).
7. Section-Transition prüfen (`_check_section_transition`): nur wenn required+optional leer.
8. Sonnet-Streaming starten (`generate_response(...)`) und `token`-Events senden.
9. Nach Streaming: Quick-Replies neu berechnen, Assistant-Message speichern.
10. SSE finalisieren: `state_update`, optional `quick_replies`, dann `done`.

### Reihenfolge (Ist)
**Extractor/QR-Norm → State-Update/DB-Commit → Conversation-LLM → QR-Generierung → SSE-Events**.

### Aktuelle SSE-Event-Typen
- `heartbeat`
- `token`
- `error`
- `state_update`
- `quick_replies`
- `done`

### Race-Conditions?
- Es gibt keinen parallelen Async-Write zwischen Extractor und QR-Generierung; Ablauf ist sequentiell.
- Potenzielles Risiko liegt eher in Session-Expiry nach Commit (im Code bewusst mitigiert durch `collected`-Closure + `collected_override`), nicht in echter Konkurrenz.

### Implikationen für Draft-Pattern
- Draft lässt sich sauber zwischen Schritt 4 und 7 einziehen (statt direkt final zu schreiben).
- Neue SSE-Events können am Ende des Streams ergänzt werden (z. B. `draft_value`).

---

## 3) Extractor (Haiku)

### Betroffene Dateien
- `services/chat_extractor.py` (`EXTRACTOR_SYSTEM_PROMPT`, `extract_fields`)
- Aufrufer: `routes/chat.py`

### System-Prompt (Quelle)
Vollständig in `EXTRACTOR_SYSTEM_PROMPT` in `services/chat_extractor.py`.
Kernregeln:
- nur genannte Felder setzen
- nichts erfinden
- Rückfragen → **kein** Tool-Call
- Skip/„keine Ahnung“ auf optionalen Feldern als `keine_angabe` fürs aktuelle Feld
- Fokus auf `current_field` + fehlende Felder + bereits erfasste Felder

### Input in den Extractor
`extract_fields(...)` bekommt:
- `user_message`
- `conversation_context` (letzte bis zu 6 Messages)
- `missing_fields`
- `collected_fields`
- `current_field` + `current_field_description`
- `report_type` (R1 vs Strategy Tool-Schema)

### Output-Format
- Erwartet Tool-Use `update_intake_fields` mit JSON-Objekt (Feldname → Rohwert).
- Kein Tool-Call => `{}`.

### Schreiben in `collected_fields`
- Extractor schreibt **nicht** in DB.
- `routes/chat.py` normalisiert Resultat und schreibt danach **sofort** in `collected_fields` (bei confidence high/medium).

### Quick-Reply-Bypass
- Bei explizitem Quick-Reply (`quick_reply_field/value`) wird Haiku übersprungen.
- Wert wird direkt normalisiert und bei Erfolg in `collected_fields` persistiert (`confirmed=True` in `field_meta`).

### Kritisch: Trennung „extrahiert“ vs „bestätigt“?
- **Nein, nicht wirklich.**
- Es gibt zwar `field_meta.confirmed`, aber für Freitext-Extraktion wird trotzdem sofort final gespeichert (nur Meta-Flag `confirmed=False`).
- Es existiert **kein** Workflow, der vor Persistierung eine explizite Bestätigung fordert.

### Implikationen für Draft-Pattern
- Technische Anschlussstelle ist klar: Nach Extractor/Normalizer zunächst in `pending_value` statt `collected_fields`.
- Zusätzlich braucht der Extractor einen Modus „confirm vs correction vs question“.

---

## 4) Conversation-LLM (Sonnet)

### Betroffene Dateien
- `services/chat_conversation.py` (`CONVERSATION_SYSTEM_PROMPT`, `STRATEGY_CONVERSATION_PROMPT`, `generate_response`)
- Aufrufer: `routes/chat.py`

### System-Prompt (Quelle)
- R1: `CONVERSATION_SYSTEM_PROMPT`
- Strategy: `STRATEGY_CONVERSATION_PROMPT`

### Input für Sonnet
`generate_response(...)` erhält:
- `session_messages` (kompakt: letzte 6 + optional Stub)
- `collected_fields`
- `missing_fields`
- `next_fields`
- `section`
- `report_type`

Prompt enthält u. a.:
- Abschnitt/Schritt
- bereits erfasste Felder (als Summary-String)
- fehlende Felder
- „als nächstes erfragen“ inkl. Feldbeschreibungen + Pflicht/Optional

### Entscheidungslogik „nächste Frage vs Kommentar“
- Der Code entscheidet es nicht deterministisch; Sonnet bekommt Instruktionen („genau eine Frage“, „kurz reagieren, dann nächste Frage“).
- Harte Logik „bleib im Feld bis bestätigt“ gibt es derzeit nicht.

### Rückfragen-Erkennung
- Prompt fordert Rückfragen zu beantworten.
- Zusätzlich im Extractor: kein Tool-Call bei Rückfrage.
- Aber es gibt keine persistente `dialog_mode`-State-Maschine, d. h. Verhalten bleibt promptgetrieben.

### Historienlänge
- `build_conversation_messages(...)`: effektiv letzte 6 Messages; bei mehr wird ein kurzer Stub vorangestellt.

### Implikationen für Draft-Pattern
- Sonnet-Prompt muss zustandsabhängig erweitert werden (Dialog-Modus / Draft-Bestätigung).
- Aktuell fehlt struktureller Guardrail, der Fortschritt vor Confirm blockiert.

---

## 5) Quick-Reply-Generierung

### Betroffene Dateien
- `routes/chat.py` (`_build_quick_replies`, `_QR_OPTIONS`, `FREETEXT_SUGGESTIONS`)

### Wann getriggert?
- Nach Abschluss des Sonnet-Streams im SSE-Callback (`event_stream`), basierend auf neu berechneten `next_fields`.
- Zusätzlich bei `/chat/start` (Welcome-QR) und `/chat/session/{id}` (Resume-State).

### Woher kommen Optionen?
- Statisch aus `_QR_OPTIONS` (feldspezifisch)
- Sonderfall dynamisch: `bundesland` aus `country` via `_build_bundesland_options`
- Freitextvorschläge aus `FREETEXT_SUGGESTIONS` für ausgewählte Textfelder

### Verhalten bei Freitext trotz QR-Feld
- User kann Freitext senden; dann läuft Extractor-Pfad.
- Wenn normalisierbar, wird Wert wie üblich in `collected_fields` geschrieben.
- QR ist also Hilfe, kein Zwang.

### Implikationen für Draft-Pattern
- QR-Single-Select kann weiter direkt final sein.
- Für FT/MS sollte QR-Ausgabe ggf. unterdrückt/angepasst werden, solange `pending_value` offen ist.

---

## 6) Field-Progression

### Betroffene Dateien
- `services/chat_normalizer.py` (`get_missing_fields`, `get_next_fields`, `is_section_complete`, `is_field_visible`)
- `routes/chat.py` (`_check_section_transition`)

### Logik der nächsten Felder
- `get_missing_fields`: pro Abschnitt fehlende required/optional, inklusive Conditional-Logik.
- `get_next_fields`: zuerst required, dann optional (Standard `max_fields=1`).

### Pflicht vs. Optional
- Unterscheidung aus Registry-Feld `required`.
- `skip_in_chat` blendet Felder im Chatfluss aus (z. B. `datenschutz`).

### Section-Transition
- `_check_section_transition(...)` wechselt Abschnitt erst, wenn **required und optional** leer sind.
- Dadurch bleiben optionale Felder Teil des Flows (außer Nutzer skippt sie).

### Wenn Extractor nichts extrahiert
- Feld bleibt offen.
- Optional kann über Skip-Wörter übersprungen werden (Sentinel `""` oder `None`).
- Sonnet antwortet dennoch weiter; keine harte Retry-/Clarification-State-Maschine.

### Implikationen für Draft-Pattern
- Progression muss um „pending blockiert next field“ erweitert werden.
- Section-Transition darf erst nach Confirm offener Drafts passieren.

---

## 7) Frontend-Chat-Widget (Überblick)

### Befund in diesem Backend-Repo
- Es gibt hier keinen konkreten Chat-Widget-Clientcode (kein EventSource-Handling, keine Button-Komponenten im gefundenen Codebestand).
- Vorhanden sind nur Backend-Schemas/Events und serverseitige QR-Datenstruktur.

### Ableitbarer Vertragsstatus (Backend-seitig)
- SSE liefert `token`, `state_update`, `quick_replies`, `done`, `error`, `heartbeat`.
- Quick-Replies enthalten:
  - `field`, `label`, `options[]`
  - `multi_select`, `max_select`
- Daraus folgt: Frontend muss Multi-Select + Confirm bereits clientseitig lösen, aber Implementierungsdetails liegen nicht in diesem Repository.

### Bestätigungs-UI vorhanden?
- In diesem Repo: **nein** (kein Draft-/Confirm-Event, kein dediziertes API-Pattern).

### Implikationen für Draft-Pattern
- API-Vertrag muss erweitert werden (neue Events und/oder Endpoint).
- Frontend-Umsetzung ist extern abzustimmen, da Quellcode im vorliegenden Repo nicht enthalten ist.
