# Steckbrief api-ki-backend-neu

Letzter Wartungs-Durchgang: **2026-09-03**.
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
| Report-Sektionen (Standard) | `ANTHROPIC_MODEL_DEFAULT` (Vorrang) → `ANTHROPIC_MODEL` | `claude-sonnet-5` (Railway setzt `ANTHROPIC_MODEL_DEFAULT`) | Aktiv; Denken läuft adaptiv mit (Voreinstellung) |
| 8 Premium-Sektionen | `ANTHROPIC_MODEL_OPUS` + `OPUS_SECTIONS` | `claude-opus-4-8` | Aktiv; Denken aus |
| Anthropic-Fallback | `ANTHROPIC_MODEL_FALLBACK` | `claude-haiku-4-5-20251001` (Railway-ENV; Code-Default ist Sonnet 4.5) | Greift NUR bei `NotFoundError`, also praktisch nie — dann aber für JEDE Sektion. Haiku senkt dort die Qualität ohne nennenswerte Ersparnis. **Empfehlung: Railway-Override entfernen** (Test: tests/test_kis1272_fallback_modell.py) |
| Chat-Gespräch | `CHAT_CONVERSATION_MODEL` | `claude-sonnet-4-5-20250929` (Railway-ENV, seit 2026-09) | Aktiv; Deprecation von Sonnet 4 damit erledigt |
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

## Bekannte Punkte (offen, Stand 2026-09-03)

- ENV-Prüfung: `docs/env-tranche2-2026-09-03.md` — 309 Railway-Variablen
  gegen den Code geprüft. 42 löschbar, dazu `DATABASE_URL` und
  `MISE_PYTHON_GITHUB_ATTESTATIONS` (mit keinem Dienst verbunden).
  Vier Schreibweisen-Fallen: Railway hat `RATE_LIMIT_PER_MINUTE`,
  `PROMPT_STABILITY_ENABLED`, `POLL_INTERVAL`, `RESEARCH_CACHE_TTL` —
  der Code liest `REPORT_RATE_LIMIT_PER_MINUTE`,
  `STABILITY_SCORING_ENABLED`, `WORKER_POLL_INTERVAL`,
  `RESEARCH_CACHE_TTL_DAYS`. Alle vier laufen auf ihrem Standardwert.
  `ENABLE_TAVILY`/`ENABLE_PERPLEXITY` sind wirkungslos — beide Dienste
  schalten über die Anwesenheit ihres API-Schlüssels. Werkzeug:
  `scripts/env_unused.py`. Löschen muss Wolf in Railway.
- Tool-Daten: `data/tools_seed.json` hat 20 von 23 Einträgen ohne
  `verified_at`. Der Tool-Radar läuft (Issue #1168). Die
  Domainbeschränkung (KIS-1273) wirkt: Der Lauf vom 03.09. 22:23 lieferte
  35 Kandidaten, alle auf der jeweiligen Herstellerdomain. Preise und
  DSGVO-Status muss trotzdem ein Mensch bestätigen — der Radar meldet
  nur. Alle zwölf toten Trust-URLs sind ersetzt (KIS-1277/1278);
  Adobe-Befunde sind Timeouts, keine toten Seiten.
- Zwei Tool-Listen: `data/tools_seed.json` (23 Einträge, der Radar prüft
  sie) und `DEFAULT_TOOLS` in `services/tools_recommender.py` (12
  Einträge, Notfall-Ausweichliste, ungeprüft). Wo sich beide
  überschneiden, hält `tests/test_kis1278_zweite_toolliste.py` sie
  gleich. Der Seed-Pfad ist seit KIS-1278 absolut — vorher konnte ein
  anderes Arbeitsverzeichnis still die Ausweichliste aktivieren.
- Toter Code gelöscht: `services/funding_engine_v2.py` (1278 Zeilen,
  2026-09-03) und `services/funding_parser.py` (101 Zeilen, 2026-09-04,
  kein Aufrufer). Es bleiben zwei Förderquellen:
  `funding_programmes_core_2025` (Kern) und `data/funding/funding_de.json`,
  dazu `data/funding_programs.json` als Fallback in
  `services/research_pipeline.py`. Die Statusregel liegt in
  `funding_recommender.ist_beantragbar`.
- Zwei Förderdaten-Punkte ohne Beleg (als Notiz im Datensatz vermerkt):
  „aws digi Invest" als eigenständiges Programm, und der Status von
  Digitalbonus Bayern (steht als `expired`, Seite wieder erreichbar).
- ZIM steht bis zur Wiedervorlage am 15.01.2027 auf `paused` und fällt
  aus allen Empfehlungen. Der Förder-Radar erinnert ab diesem Datum.
- Perplexity liefert die Markt-Box, die das DE-Template nicht rendert:
  zwei Aufrufe je Report ohne sichtbaren Nutzen. Entscheidung offen.
- `routes/appetizer.py` bleibt aktiv (Wolf plant eine Einbindung), hat
  aber noch keinen Aufrufer im eigenen Frontend.
- pdfservice: Docker-Image `puppeteer:22.10.0` (Mai 2024) gepinnt, kein
  Lockfile → `npm audit` nicht möglich.
- GitHub-Label `datenpflege` existiert nicht — die Wächter legen ihre
  Issues deshalb ohne Label an.

## Werkzeuge

- `scripts/compare_reports.py alt.pdf neu.pdf` — vergleicht zwei
  Report-Läufe: Kennzahlen, dünne Seiten, Rückfall-Prüfung gegen die
  behobenen Fehler. Exit-Code 1 bei einem Rückfall.
- `scripts/env_unused.py liste.txt` — prüft eine Liste von ENV-Namen
  gegen den Laufzeit-Code. Kennt die vier Fallen, an denen die
  Handprüfung scheitert (Konstanten, dynamische Namen,
  Teilzeichenketten, `_bool_env`-Helfer).
- `POST /api/admin/testrun/replay/{briefing_id}` — erzeugt einen Lauf
  mit identischen Antworten (kopiert auch FB2). Admin-Key jetzt per
  Header `X-Admin-Key`; der Query-Parameter bleibt gültig, verträgt aber
  kein `+` im Schlüssel.

## Nicht verhandelbar

- Der Firmenname wird im Fragebogen/Chat nirgendwo erhoben
  (CI-Invariante: `tests/golden/`, `_NAME_KEY_RE`).
- Backend-Merges lösen einen Railway-Deploy aus und killen laufende
  Report-Generierungen — nie mergen, während ein Testlauf aktiv ist.
