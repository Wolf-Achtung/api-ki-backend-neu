# Steckbrief api-ki-backend-neu

Letzter Wartungs-Durchgang: **2026-08-19** (Skill `/wartung`).
Dieser Steckbrief listet die betriebskritischen Fakten. Details stehen in
`.env.example` und in den verlinkten Dateien.

## Laufzeit

| Was | Wert | Quelle |
|---|---|---|
| Python (Deploy-Pin) | 3.11.9 | `runtime.txt` |
| Python (Support-Ende) | Oktober 2027 | python.org-Release-Zyklus |
| Prozesse | `web` (uvicorn main:app), `worker` (workers.briefings_worker) | `Procfile` |
| Deploy-Plattform | Railway (Deploy bei Merge auf `main`) | — |

## Modelle (Stand 2026-08-19)

Alle Modell-IDs sind per ENV konfigurierbar. Die Tabelle zeigt den
**wirksamen Wert in Produktion** (Railway-ENV, sonst Code-Default).

| Zweck | ENV-Variable | Wirksam in Prod | Status |
|---|---|---|---|
| Report-Sektionen (Standard) | `ANTHROPIC_MODEL` | `claude-sonnet-5` | Aktiv; Denken läuft adaptiv mit (Voreinstellung) |
| 8 Premium-Sektionen | `ANTHROPIC_MODEL_OPUS` + `OPUS_SECTIONS` | `claude-opus-4-8` | Aktiv; Denken aus |
| Anthropic-Fallback | `ANTHROPIC_MODEL_FALLBACK` | Default `claude-sonnet-4-5-20250929` | Aktiv |
| Chat-Gespräch | `CHAT_CONVERSATION_MODEL` | Default `claude-sonnet-4-20250514` | ⚠️ **DEPRECATED** (Abschaltdatum offen; Quelle: Anthropic-Modellreferenz, Stand 2026-06-24) — Nachfolger festlegen |
| Chat-Extraktion | `CHAT_EXTRACTOR_MODEL` | Default `claude-haiku-4-5-20251001` | Aktiv |
| Coach | `ANTHROPIC_MODEL_COACH` → `ANTHROPIC_MODEL_OPUS` | `claude-opus-4-8` | Aktiv |
| Appetizer | `ANTHROPIC_MODEL_APPETIZER` → `ANTHROPIC_MODEL` | `claude-sonnet-5` | Aktiv |
| OpenAI-Fallback-Kette | `OPENAI_MODEL` | `gpt-4.1-mini` (Railway-ENV, seit 2026-08-19) | Aktiv; non-reasoning, kein Abschaltdatum angekündigt (Stand 08/2026) |

Merkregeln:

- `claude-sonnet-5` denkt ohne `thinking`-Parameter adaptiv mit; die
  Denk-Tokens zählen gegen `max_tokens`. Schutznetz: Truncation-Retry
  (KIS-1231 Textpfad, KIS-1288 Structured-Pfad).
- `claude-opus-4-8` denkt ohne Parameter NICHT.
- Kein aktuelles Modell akzeptiert `temperature` oder
  `thinking.budget_tokens` (400). `build_anthropic_create_kwargs` und
  `_maybe_add_thinking` behandeln das (services/anthropic_client.py).

## ENV-Vertrag

- Der Code liest ~730 Variablen (viele mit Defaults). Referenz: `.env.example`.
- Sektionsdynamische Namen: `USE_ANTHROPIC_FOR_<SECTION>`,
  `ANTHROPIC_MAX_TOKENS_<SECTION>`, `OPENAI_MAX_TOKENS_<SECTION>`,
  `OPENAI_MODEL_<SECTION>`, `OPENAI_TEMP_<SECTION>`, `BRAND_<KEY>`.
- Schreibweisen-Falle (2026-08 behoben): Der Code liest `OPENAI_MODEL` —
  nie `OPENAI_MODEL_DEFAULT`.
- Wichtige Schalter mit Default (nicht in Railway gesetzt = Default gilt):
  `ANTHROPIC_TRUNCATION_RETRY=1`, `LANG_SWEEP_MAX_LLM_CALLS=80`,
  `LANG_SWEEP_PARALLELISM=4`, `STALE_BRIEFING_TIMEOUT=600`,
  `ANTHROPIC_THINKING_BUDGET=0` (Denk-Opt-in aus).

## Bekannte Punkte (offen, Stand 2026-08-19)

- Chat-Modell deprecated (siehe Tabelle) — Wechsel ist eine
  Produktentscheidung, nicht automatisch ausgeführt.
- `routes/appetizer.py` hat keinen Aufrufer im eigenen Frontend und fragt
  als einziger Pfad einen Firmennamen ab (`firma`) — Produktentscheidung
  nötig: abschalten oder Feld entfernen.
- pdfservice: Docker-Image `puppeteer:22.10.0` (Mai 2024) gepinnt, kein
  Lockfile → `npm audit` nicht möglich.
- Monatlicher Förder-Freshness-Check: nächster Lauf Anfang September 2026
  (`scripts/check_funding_freshness.py --max-age-days 90`).

## Nicht verhandelbar

- Der Firmenname wird im Fragebogen/Chat nirgendwo erhoben
  (CI-Invariante: `tests/golden/`, `_NAME_KEY_RE`).
- Backend-Merges lösen einen Railway-Deploy aus und killen laufende
  Report-Generierungen — nie mergen, während ein Testlauf aktiv ist.
