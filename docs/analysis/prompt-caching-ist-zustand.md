# Prompt-Caching — Ist-Zustand (Diagnose)

Stand: 2026-08-01. Reine Bestandsaufnahme, **keine Änderung an der Prompt-Logik**.
Ergänzt wurde ausschließlich Usage-Logging (siehe Abschnitt 4).

Modell-Minima für den kleinsten cachebaren Prefix (Quelle: Anthropic
Prompt-Caching-Doku). Unterhalb des Minimums wird **stillschweigend nicht**
gecacht — kein Fehler, `cache_creation_input_tokens` bleibt 0:

| Modell | Minimum |
|---|---:|
| Opus 5, Fable 5, Mythos 5 | 512 tok |
| Opus 4.8, Sonnet 5, Sonnet 4.6, **Sonnet 4.5**, **Sonnet 4**, Opus 4.1, Opus 4 | 1024 tok |
| Opus 4.7, Haiku 3.5 | 2048 tok |
| **Opus 4.6**, Opus 4.5, **Haiku 4.5** | 4096 tok |

Das Minimum ist **nicht monoton** über die Generationen — genau daran hängen
die beiden Hauptbefunde unten.

---

## 1. Call-Sites `api-ki-backend-neu`

| # | Call-Site | Modell (Default) | cache_control? | System-Prompt interpoliert? | Parallel? |
|---|---|---|---|---|---|
| A1 | `services/anthropic_client.py:712` `call_anthropic()` — Erst-Call | `_resolve_anthropic_model(section)`: OPUS_SECTIONS → `claude-opus-4-6`, sonst `ANTHROPIC_MODEL` → `claude-sonnet-4-5-20250929` | **ja** — `{"type":"ephemeral"}` auf Block 0 des **User**-Messages (`_build_user_content`, Z. 538–546), gated über `ANTHROPIC_PROMPT_CACHING` (Default an) | **nein** — `build_report_system_prompt()` ist deterministisch, keine Request-Daten, byte-identisch über alle Sektionen | **ja** — `ThreadPoolExecutor` (`gpt_analyze.py:14407`), alle Sektionen auf einmal |
| A2 | `anthropic_client.py:736` — Retry ohne `temperature` | wie A1 | wie A1 (gleiche `messages`) | nein | im Thread |
| A3 | `anthropic_client.py:765` — Fallback-Modell | `ANTHROPIC_MODEL_FALLBACK` → `claude-sonnet-4-5-20250929` | wie A1 | nein | im Thread |
| A4 | `anthropic_client.py:821/826` — Truncation-Retry (KIS-1231) | wie A1 | wie A1 | nein | im Thread |
| A5 | `anthropic_client.py:616/621` `call_anthropic_structured()` — quick_wins via Tool-Use | wie A1 | wie A1 (`_build_user_content`) | nein | im Thread |
| B | `routes/appetizer.py:111` | `ANTHROPIC_MODEL_APPETIZER` → `ANTHROPIC_MODEL` → `claude-sonnet-4-6` | **nein** | System kommt vom Caller als Parameter | nein |
| C1 | `services/chat_extractor.py:545` — Einzelfeld-Extraktion | `CHAT_EXTRACTOR_MODEL` → `claude-haiku-4-5-20251001` | **nein** | **ja** — `EXTRACTOR_SYSTEM_PROMPT.format(current_field, current_field_hint, missing_fields, collected_fields)` (Z. 522–527), zusätzlich `+= _DRAFT_SIGNAL_EXTENSION.format(pending_context=…)` (Z. 537) | nein |
| C2 | `chat_extractor.py:903` — Multi-Feld-Extraktion | wie C1 | **nein** | **ja** — `MULTI_FIELD_SYSTEM_PROMPT.format(fields_descriptions, collected_fields)` (Z. 894) | nein |
| D | `services/chat_conversation.py:1978` — Chat-Stream | `CHAT_CONVERSATION_MODEL` → `claude-sonnet-4-20250514` | **nein** | **ja, massiv** — `prompt_template.format(...)` (Z. 1833) plus ≥ 8 bedingte `system_prompt += …` Blöcke (Z. 1847–1964: Abschnitts-Hinweis, Draft-Kontext, Hilfe-Anfrage, Anti-Wiederholungs-Regeln, EN-Sprachdirektive) | nein |
| E | `services/coach_service.py:441` — Coach-Stream | `ANTHROPIC_MODEL_COACH` → `ANTHROPIC_MODEL_OPUS` → `claude-opus-4-6` | **nein** | **ja** — `_COACH_PROMPT_TEMPLATE.format(**context)` (Z. 370); 18 Platzhalter, erster bei Offset 2045 von 12 810 Zeichen | nein |

## 2. Call-Sites `creative-radar`

Alle Anthropic-Calls laufen über drei Wrapper in
`backend/app/services/anthropic_client.py`. **Nirgends** ist `cache_control`
gesetzt — bestätigt durch den Kommentar in `insight_engine.py:587`
(„once Anthropic prompt-caching is wired (Sprint-2 follow-up)").

| # | Call-Site | Modell (Default) | cache_control? | System-Prompt interpoliert? | Parallel? |
|---|---|---|---|---|---|
| F | `insight_engine.py:3714` `_run_brief_llm` → `messages_create_strict_json` (Pair-Brief, Title-Brief, Prompt-Eval) | `settings.anthropic_opus_model` → `claude-opus-4-8` | **nein** | **nein** — `SYSTEM_PROMPT` ist eine statische Modul-Konstante, 0 Platzhalter | **nein** — sequenziell + `MAX_RECALLS`-Retry-Loop |
| G | `segment_roundup.py:609` → `call_with_json_retry` → `messages_create_text` | `claude-opus-4-8` | **nein** | **nein** — `ROUNDUP_SYSTEM_PROMPT = BRIEF_VOICE + ROUNDUP_TASK`, statisch | nein |
| H | `title_brief.py:312` → `_run_brief_llm` | `claude-opus-4-8` | **nein** | **nein** — `TITLE_SYSTEM_PROMPT = BRIEF_VOICE + TITLE_BRIEF_TASK`, statisch | nein |
| I | `cutter_weekly.py:418` → `call_with_json_retry` | `claude-opus-4-8` | **nein** | **nein** — statische Konstante | nein |
| J | `designer_weekly.py:413` → `call_with_json_retry` | `claude-opus-4-8` | **nein** | **nein** — statische Konstante | nein |
| K | `forecast.py:289/300` → `messages_create_text` | `OPUS_MODEL_ALIAS` → `claude-opus-4-8` | **nein** | **nein** — `_EINORDNUNG_SYSTEM`, statisch | nein |
| L1 | `post_analyzer.py:187/213` `_classify_format_tone` (+Retry) | `settings.anthropic_haiku_model` → `claude-haiku-4-5-20251001` | **nein** | **nein** — `analyze_format_tone.SYSTEM_PROMPT`, statisch | nein — Schleife über Posts |
| L2 | `post_analyzer.py:242/268` `_classify_purpose_lifecycle` (+Retry) | `settings.anthropic_sonnet_model` → `claude-sonnet-5` | **nein** | **nein** — statisch | nein |
| L3 | `post_analyzer.py:302` `_describe_vision` | `claude-sonnet-5` | **nein** | **nein** — statisch | nein |

---

## 3. Ergebnis-Tabelle: statischer Prefix vs. Modell-Minimum

Token-Schätzungen aus Zeichenzahl bei 3,0–3,5 Zeichen/Token (Deutsch/JSON).
„Statischer Prefix" = der über wiederholte Calls **byte-identische** Anteil,
gerechnet in Render-Reihenfolge `tools → system → messages`.

| Call-Site | Modell | Token-Umfang statischer Prefix | Modell-Minimum | cacheable? | aktueller Breakpoint |
|---|---|---:|---:|---|---|
| A1–A5 **Sonnet-Sektionen** | `claude-sonnet-4-5` | system 606–707 + context_prefix 1 875–2 188 = **~2 500–2 900** | 1 024 | **ja** | User-Block 0 (`ephemeral`) |
| A1–A5 **Opus-Sektionen** (`OPUS_SECTIONS`) | `claude-opus-4-6` | **~2 500–2 900** | **4 096** | **NEIN — unter Minimum** | User-Block 0 (gesetzt, greift aber nie) |
| B Appetizer | `claude-sonnet-4-6` | System vom Caller, nicht vermessen | 1 024 | ungenutzt | **keiner** |
| C1/C2 Extractor | `claude-haiku-4-5` | **0** (System ist pro Request interpoliert) | **4 096** | **nein** | keiner |
| D Chat-Conversation | `claude-sonnet-4` | **0** (System pro Turn neu zusammengesetzt) | 1 024 | **nein** | keiner |
| E Coach | `claude-opus-4-6` | **0–584** (statischer Kopf bis Offset 2 045 = ~584–682 tok; danach Platzhalter) | **4 096** | **nein** | keiner |
| F Pair-/Title-Brief-Kernel | `claude-opus-4-8` | `SYSTEM_PROMPT` 46 306 Zeichen = **~13 200–15 400** | 1 024 | **ja — mit Abstand größter Hebel** | **keiner** |
| G Segment-Roundup | `claude-opus-4-8` | `BRIEF_VOICE` 4 879 + `ROUNDUP_TASK` 1 780 = **~6 700** | 1 024 | **ja** | keiner |
| H Title-Brief | `claude-opus-4-8` | `BRIEF_VOICE` 4 879 + `TITLE_BRIEF_TASK` 704 = **~5 600** | 1 024 | **ja** | keiner |
| I Cutter-Weekly | `claude-opus-4-8` | **~834–973** | 1 024 | **grenzwertig — knapp darunter** | keiner |
| J Designer-Weekly | `claude-opus-4-8` | **~880–1 027** | 1 024 | **grenzwertig — um das Minimum** | keiner |
| K Forecast-Einordnung | `claude-opus-4-8` | **~251–292** | 1 024 | **nein — zu kurz** | keiner |
| L1 Format/Tone | `claude-haiku-4-5` | **~140–163** | **4 096** | **nein — zu kurz** | keiner |
| L2 Purpose/Lifecycle | `claude-sonnet-5` | **~161–188** | 1 024 | **nein — zu kurz** | keiner |
| L3 Vision | `claude-sonnet-5` | **~121–141** | 1 024 | **nein — zu kurz** | keiner |

---

## 4. Befunde

**B1 — Opus-Sektionen cachen nie (api-ki-backend-neu).**
`OPUS_MODEL` ist per Default `claude-opus-4-6`, Minimum **4 096** Token. Der
gecachte Prefix (System ~600 + `_SHARED_CONTEXT_PREFIX` ~1 900–2 200) liegt bei
~2 500–2 900 Token und damit darunter. Der `cache_control`-Block wird gesetzt,
greift aber stillschweigend nicht — kein Fehler, `cache_creation_input_tokens`
bleibt 0. Die Sonnet-Sektionen (Minimum 1 024) sind davon nicht betroffen.

**B2 — Der Parallel-Fan-out entwertet den ersten Cache-Durchlauf (api-ki-backend-neu).**
Ein Cache-Eintrag ist erst lesbar, wenn die erste Antwort zu streamen beginnt.
`gpt_analyze.py:14407` submitted alle Sektionen gleichzeitig in den
`ThreadPoolExecutor`; die gesamte erste Welle (bis `max_workers`) läuft gegen
einen noch nicht existierenden Eintrag und zahlt vollen Preis — plus den
1,25×-Write-Aufschlag pro Worker. Erst spätere Wellen lesen.

**B3 — `creative-radar` hat 13 000+ Token statischen System-Prompt ohne jeden Breakpoint.**
`insight_engine.SYSTEM_PROMPT` ist mit ~13 200–15 400 Token vollständig statisch
(0 Platzhalter) und läuft auf `claude-opus-4-8` (Minimum 1 024) — also weit über
der Schwelle. Dasselbe gilt für Roundup (~6 700) und Title-Brief (~5 600), die
sich zusätzlich `BRIEF_VOICE` (~4 900) teilen. Es ist nirgends `cache_control`
gesetzt. Das ist der größte ungenutzte Hebel in beiden Repos.

**B4 — Drei `creative-radar`-Call-Sites sind zu kurz zum Cachen.**
Forecast (~250 tok), und die drei `post_analyzer`-Prompts (~120–190 tok) liegen
unter jedem Minimum. `post_analyzer` läuft zwar in einer Schleife über viele
Posts — aber auf Haiku 4.5 (Minimum 4 096) ist der Prompt um Faktor ~25 zu kurz.
Cutter-/Designer-Weekly (~830–1 030 tok) liegen genau **auf** der 1 024er-Kante,
d. h. ihr Cache-Verhalten wäre nicht verlässlich vorhersagbar.

**B5 — Vier Call-Sites haben strukturell keinen cachebaren Prefix.**
Bei C1/C2 (Extractor), D (Chat-Conversation) und E (Coach) steckt der
Request-Kontext **im System-Prompt** — also vor allem anderen in der
Render-Reihenfolge. Konkret:
- C1: `EXTRACTOR_SYSTEM_PROMPT.format(current_field, …, collected_fields)`
- C2: `MULTI_FIELD_SYSTEM_PROMPT.format(fields_descriptions, collected_fields)`
- D: `prompt_template.format(...)` + ≥ 8 bedingte `+=`-Blöcke pro Turn
- E: `_COACH_PROMPT_TEMPLATE.format(**context)`, erster Platzhalter bei
  Zeichen-Offset 2 045 von 12 810 → der statische Kopf davor sind nur
  ~584–682 Token, gegen ein Opus-4.6-Minimum von 4 096.

**B6 (Nebenbefund, nicht Caching) — `_SHARED_CONTEXT_PREFIX` ist ein Modul-Global.**
`gpt_analyze.py:14374` setzt das Global vor dem Thread-Pool. Innerhalb *eines*
Laufs ist das korrekt (gesetzt bevor Threads starten). Laufen zwei Reports
gleichzeitig im selben Prozess, überschreibt der zweite Lauf den Prefix des
ersten. Habe ich nicht angefasst — außerhalb des Diagnose-Auftrags.

---

## 5. Was in diesem Commit geändert wurde (nur Logging)

**`api-ki-backend-neu`** — neue Funktion `log_anthropic_usage(message, *, call_site, model)`
in `services/anthropic_client.py`. Sie ist exception-sicher gekapselt (Logging darf
nie einen Call brechen) und wird an allen 11 Call-Sites aufgerufen: A1–A5 inkl.
aller Retry-Pfade, B, C1, C2, D, E. Bei den beiden Streaming-Sites (D, E) wird
`stream.get_final_message()` genutzt — die vom SDK bereits akkumulierte Message,
**kein zusätzlicher API-Roundtrip**. Log-Format:

```
[CACHE-USAGE] call_site=call_anthropic:executive_summary model=claude-opus-4-6 \
  input_tokens=8123 cache_creation_input_tokens=0 cache_read_input_tokens=0 \
  prompt_tokens_total=8123 output_tokens=1450
```

**`creative-radar`** — eine Log-Zeile in `record_anthropic_call`
(`backend/app/services/cost_log.py`). Diese Funktion läuft bereits an *jeder*
Anthropic-Call-Site und bekommt `usage` + `operation` — deshalb keine
Signatur-Änderung und keine Caller-Edits nötig; `operation` ist das
Call-Site-Label. Gelesen wird über den vorhandenen `_get`-Helper, der sowohl
SDK-Objekte als auch Test-Dicts abdeckt.

**Auswertung der Logs:** `cache_read_input_tokens > 0` = Cache greift;
`cache_creation_input_tokens > 0` = dieser Call hat geschrieben; beide dauerhaft
0 = Prefix unter Modell-Minimum, kein `cache_control`, oder Prefix ändert sich
zwischen Calls. Erwartungswert vor jeder Änderung: in `creative-radar`
durchgängig 0, in `api-ki-backend-neu` 0 für alle Opus-Sektionen (B1) und für
die erste Thread-Welle (B2).
