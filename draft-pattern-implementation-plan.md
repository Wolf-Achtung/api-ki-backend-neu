# Implementierungsplan: Draft-State + Bestätigungs-Pattern

> Ziel: Extrahierte Werte werden nicht mehr sofort final in `collected_fields` geschrieben, sondern zuerst als Draft geführt und explizit bestätigt.

## A) Neuer Session-State

### Betroffene Dateien
- `models.py` (`ChatSession`)
- `migrations/*` (neue Migration, falls eigene Spalten)
- `schemas/chat.py` (`ChatSessionState` + ggf. neue Request-Schemas)
- `routes/chat.py` (`_build_session_state`)

### Konkrete Änderungen
1. Neue State-Felder:
   - `pending_field: str | null`
   - `pending_value: any | null`
   - `dialog_mode: bool`
2. **Empfehlung Speicherung:** zunächst in bestehendem JSON-State (`field_meta` oder neues JSON-Feld `runtime_state`) statt sofort neue DB-Spalten.
   - Vorteil: schnell, rückwärtskompatibel, einfache Migration.
   - Später bei Bedarf in dedizierte Spalten überführbar.
3. `ChatSessionState` API um diese drei Felder erweitern.

### Aufwand
- **klein–mittel**

### Abhängigkeiten
- Basis für alle weiteren Schritte (B–H).

### Risiken
- JSON-State kann uneinheitlich werden, wenn nicht zentral validiert.
- Alte Sessions enthalten die Felder nicht (muss default-sicher behandelt werden).

---

## B) Neuer Message-Flow

### Betroffene Dateien
- `routes/chat.py` (Hauptlogik `/chat/message`, SSE)
- `services/chat_extractor.py` (Signalerkennung)
- `services/chat_conversation.py` (zustandsabhängige Antwortführung)

### Konkrete Änderungen
1. **Rückfrage-Erkennung vor Extraktion**
   - Heuristik +/oder Extractor-Signal: `is_question`.
   - Bei Frage: kein Wert-Write, `dialog_mode=true`, current field bleibt.
2. **Extraktion → Draft statt Final**
   - Wenn inhaltliche Antwort: normalize, dann `pending_field/pending_value` setzen.
   - `collected_fields` unverändert bis Confirm.
   - SSE: `draft_value` senden.
3. **Conversation-Verhalten**
   - Bei offenem Draft: Sonnet soll nur bestätigen/korrigieren lassen, keine Progression.
4. **Confirm-Pfad**
   - Bei Confirm: pending → collected, pending leeren, `dialog_mode=false`, next field aktivieren.

### Aufwand
- **mittel–groß**

### Abhängigkeiten
- A zuerst; D/E parallel vorbereitbar.

### Risiken
- Edge Cases bei „Ja, aber ...“-Antworten.
- Doppel-Events oder inkonsistenter State bei SSE-Abbruch.

---

## C) Quick-Reply-Felder: Ausnahme oder auch Draft?

### Betroffene Dateien
- `services/chat_normalizer.py` (Feldtyp/Chat-Mode)
- `routes/chat.py` (`quick_reply_field`-Pfad, `_build_quick_replies`)

### Konkrete Änderungen (empfohlen)
- `QR` Single-Select: **kein Draft**, direkt final (explizite User-Aktion ist Bestätigung).
- `MS` Multi-Select: **Draft optional**, abhängig vom UI:
  - Wenn UI bereits „Auswahl bestätigen“ hat, kann final direkt beim Confirm-Click passieren.
  - Falls Auswahl in Freitext/semantisch extrahiert wird, dann Draft anwenden.
- `FT/SC` Freitext: **immer Draft**.

### Aufwand
- **mittel**

### Abhängigkeiten
- A/B und G (Frontend-Confirm-UX) abgestimmt.

### Risiken
- Inkonsistentes UX, wenn gleiche Feldart je nach Inputkanal anders behandelt wird.

---

## D) Conversation-Prompt-Änderungen

### Betroffene Dateien
- `services/chat_conversation.py` (`CONVERSATION_SYSTEM_PROMPT`, `STRATEGY_CONVERSATION_PROMPT`, `generate_response`)

### Konkrete Änderungen
1. Neuer Prompt-Block **DIALOG-MODUS**:
   - Wenn `dialog_mode=true` und kein `pending_value`: Rückfrage beantworten, nicht vorwärts springen.
2. Neuer Prompt-Block **DRAFT-BESTÄTIGUNG**:
   - Wenn `pending_value` gesetzt: kurze Zusammenfassung + konkrete Confirm-Frage.
3. Schärfere **FOKUS-REGEL**:
   - Kein Feldwechsel ohne Confirm des aktuellen Drafts.
4. Zustandsparameter in System-Prompt aufnehmen:
   - `pending_field`, `pending_value`, `dialog_mode`.

### Aufwand
- **mittel**

### Abhängigkeiten
- A/B umgesetzt.

### Risiken
- Prompt-only Enforcement kann gelegentlich verletzt werden → serverseitige Guardrails nötig.

---

## E) Extractor-Änderungen

### Betroffene Dateien
- `services/chat_extractor.py`
- ggf. `schemas/chat.py` (wenn strukturierter Extractor-Output typisiert werden soll)

### Konkrete Änderungen
Extractor-Output von reinem Feld-Dict auf signalfähiges Format erweitern, z. B.:
```json
{
  "mode": "extract" | "confirm" | "question" | "none",
  "fields": {"hauptleistung": "..."}
}
```
1. **Confirm-Erkennung** bei offenem Pending (`ja`, `stimmt`, `passt`, `weiter`).
2. **Rückfrage-Erkennung** (`?`, „was meinst du“, „warum“, ...).
3. **Bestehende Extraktion** unverändert weiter nutzbar.

### Aufwand
- **mittel**

### Abhängigkeiten
- A/B; D für harmonisierte Interpretation.

### Risiken
- False Positives bei Confirm-Wörtern in anderen Kontexten.

---

## F) Neue SSE-Event-Typen

### Betroffene Dateien
- `routes/chat.py` (`event_stream`)
- `schemas/chat.py` (optional Event-DTOs)
- Frontend-Client (extern)

### Konkrete Änderungen
Neue Events:
- `draft_value`: `{ field, value, label }`
- `field_confirmed`: `{ field, value }`
- `dialog_mode`: `{ active: true|false }`

Erweiterte Reihenfolge (Soll):
1. optional `dialog_mode`
2. optional `draft_value`
3. `token`-Stream
4. optional `field_confirmed`
5. `state_update`
6. optional `quick_replies`
7. `done`

### Aufwand
- **klein–mittel**

### Abhängigkeiten
- B und G.

### Risiken
- Event-Reihenfolge muss strikt dokumentiert werden, sonst Frontend-Rennen.

---

## G) Frontend-Änderungen (Überblick)

### Betroffene Dateien
- Frontend-Repo (in diesem Backend-Repo nicht vorhanden)

### Konkrete Änderungen (UI-Vertrag)
1. **Draft-Chip** unterhalb Chatverlauf mit Feldlabel + Wert.
2. Buttons am Chip:
   - `✓ Übernehmen` (confirm)
   - `✏️ Ändern` (zurück in Eingabe/Rewrite)
3. **Visual Feedback** nach Confirm (`field_confirmed`).
4. **Dialog-Modus UI**:
   - bei `dialog_mode.active=true` QR-Buttons ausblenden oder deaktivieren.
5. Multi-Select:
   - bestehendes „Auswahl bestätigen“ als Confirm-Hook verwenden.

### Aufwand
- **mittel** (abhängig von bestehender Widget-Architektur)

### Abhängigkeiten
- F (Event-Vertrag) + B/C (Flow-Entscheidung).

### Risiken
- Ohne saubere State-Machine im Client drohen inkonsistente Chips/Buttons.

---

## H) Migrationsstrategie

### Betroffene Dateien
- `routes/chat.py`
- `schemas/chat.py`
- `models.py` + ggf. neue Migration
- Config/Env-Layer (Feature-Flag)

### Konkrete Änderungen
1. Feature-Flag einführen: `DRAFT_MODE_ENABLED=true|false`.
2. Backward Compatibility:
   - Fehlende Pending-Felder defaulten auf `null/false`.
   - Alte Sessions laufen weiter im alten Verhalten, solange Flag aus.
3. Rollout:
   - Staging mit Flag an
   - schrittweise Aktivierung in Produktion
4. Rollback:
   - Flag aus => alter Sofort-Write-Pfad aktiv.

### Aufwand
- **klein–mittel**

### Abhängigkeiten
- A/B/F zuerst, dann schrittweise D/E/G.

### Risiken
- Gemischte Sessions (alt/neu) brauchen robuste Default-Initialisierung.

---

## Entscheidung Confirm-Mechanismus (B.4)

### Optionen
- **A: Neuer Endpoint `POST /api/chat/confirm`**
- B: Nur QR-Buttons „Übernehmen/Ändern“ als SSE-Signal
- C: Freitext-Confirm („ja/stimmt/passt“) via Heuristik/Extractor

### Empfehlung
**Option A als Primärpfad**, ergänzt um C als Komfort-Fallback.

**Begründung:**
- Sauberste Trennung von „inhaltlicher Antwort“ vs. „State-Transition confirm“.
- Bessere Wartbarkeit/Testbarkeit (idempotente Confirm-Operation).
- Reduziert Ambiguität bei natürlicher Sprache.
- Frontend kann weiterhin Buttons nutzen, aber technisch robust via explizitem Endpoint.

B und C bleiben sinnvoll als UX-Schicht, sollten serverseitig auf denselben Confirm-Servicepfad gemappt werden.
