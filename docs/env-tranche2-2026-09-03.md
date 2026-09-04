# ENV-Prüfung Railway — Stand 04.09.2026

Geprüft wurden die **309 Shared Variables**, die am 04.09.2026 in Railway
stehen, gegen den Laufzeit-Code. Werkzeug:

```
python scripts/env_unused.py meine_variablen.txt
```

Die Datei enthält die Namen so, wie Railway sie anzeigt — als
`NAME="wert"`-Zeilen oder durch Leerzeichen getrennt.

## Zur Vorgeschichte

Am 03.09. stand hier eine Liste mit 37 Variablen. Ein Abzug aus Railway
enthielt davon nur eine, worauf diese Datei auf 4 Variablen gekürzt
wurde. Der Abzug vom 04.09. enthält alle 37 wieder. Der Vergleich beider
Abzüge zeigt: **36 Namen kamen hinzu, keiner verschwand.** Der Abzug vom
03.09. war unvollständig, die ursprüngliche Liste im Kern richtig.

Lehre daraus, nicht für die Liste, sondern für das Verfahren: Ein
Variablen-Abzug ist eine Momentaufnahme aus einer Oberfläche. Wer daraus
löscht, prüft vorher, ob er vollständig ist — `wc -l` gegen die
Stückzahl, die Railway anzeigt.

## Ergebnis

### Stufe 1 — löschen, kein Treffer im Repo (29)

Diese Namen kommen in `services/`, `routes/`, `core/`, `workers/`,
`utils/`, `main.py`, `settings.py`, `gpt_analyze.py`, in den Skripten
und in den Workflows **nirgends** vor.

```
ANTHROPIC_BASE_URL              HARD_FAIL_ON_VALIDATION_ERRORS
ANTHROPIC_ENABLED               MARKET_INSIGHTS_ENABLED
API_RATE_LIMIT_PER_MIN          MAX_GUARDRAIL_HITS
AUTH_ALLOW_DEV_CONSOLE          MAX_PARALLEL_LLM_CALLS
AUTH_SEND_MAIL                  MAX_PARALLEL_SECTIONS
CORS_MAX_AGE                    PERPLEXITY_RATE_LIMIT_PER_HOUR
DEBUG_LOG_HTML_SNAPSHOT         RATE_LIMIT_PER_MINUTE
DEBUG_LOG_PROMPTS               REPORT_ADMIN_EMAIL
DISABLE_HIGH_RISK_AUTO_UPGRADE  RESEARCH_RSS_EXTRA_PATH
ENABLE_GUARDRAILS               STARTER_KITS_MAX_TOOLS
ENABLE_METRICS                  TOKEN_LIMIT_HTML_REPAIR
ENABLE_PROMPT_LABELS            USE_STOCK_IMAGES
ENABLE_SENSITIVITY_TABLE
ENABLE_TAVILY
FEEDBACK_SECRET
GUARDRAILS_V
HARD_FAIL_ON_HTML_ERRORS
```

### Stufe 2 — löschen, per Hand geprüft (13)

`settings.py` liest diese Werte in ein Feld ein. **Niemand liest dieses
Feld.** Der Wert wandert in ein Objekt und bleibt dort liegen.

| Variable | Feld in settings.py | Verbraucher |
|---|---|---|
| `ENABLE_PERPLEXITY` | `enable_perplexity` | keiner |
| `ENABLE_LLM_CACHE` | `enable_llm_cache` | keiner |
| `ENABLE_QUALITY_GATES` | `enable_quality_gates` | keiner |
| `ENABLE_AI_ACT_TABLE` | `enable_ai_act_table` | keiner |
| `PERPLEXITY_MAX_TOKENS` | `perplexity.max_tokens` | keiner |
| `PERPLEXITY_TIMEOUT_MS` | `perplexity.timeout_ms` | keiner |
| `RESEARCH_LANG` | `research.lang` | keiner |
| `RESEARCH_COUNTRY` | `research.country` | keiner |
| `RESEARCH_DAYS_DEFAULT` | `research.days_default` | keiner |
| `RESEARCH_DAYS_MIN` | `research.days_min` | keiner |
| `RESEARCH_DAYS_MAX` | `research.days_max` | keiner |
| `RESEARCH_CACHE_TTL` | `research.cache_ttl` | keiner |
| `REPORT_DATE` | `report_date` | keiner |

`ENABLE_AI_ACT_SECTION` dagegen **wirkt** — `gpt_analyze.py` liest den
Namen direkt. Der Abschnitt lässt sich also schalten, die Tabelle darin
nicht.

### Stufe 3 — stehen lassen (6)

`SERVICE_TOKEN`, `SMOKE_AUTH_TOKEN`, `SMOKE_BASE_URL`, `API_BASE_URL`,
`POLL_TIMEOUT`, `BACKEND_BASE` gehören zum Smoke-Test und den
GitHub-Workflows. Im Railway-Dienst wirken sie nicht, sie kosten nichts
und dokumentieren die Gegenwerte.

### Stufe 4 — aus den Shared Variables entfernen (2)

`DATABASE_URL` und `MISE_PYTHON_GITHUB_ATTESTATIONS` sind laut Railway
**mit keinem Dienst verbunden**. Sie wirken nirgends.

- Die echte Datenbankverbindung steht im Dienst selbst — das Backend
  läuft, also kann die Shared-Kopie nicht die Quelle sein.
- Die mise-Einstellung war ein Notbehelf aus Sprint 1027.4. Der
  dauerhafte Fix liegt seit damals versioniert in `mise.toml`
  (Test: `tests/test_kis_1027_5_d_mise_toml.py`).

## Vier Schreibweisen-Fallen

Wichtiger als die Löschliste: Vier Einstellungen laufen auf ihrem
Standardwert, obwohl in Railway etwas anderes steht.

| Railway hat | Der Code liest | Wirksam |
|---|---|---|
| `RATE_LIMIT_PER_MINUTE=60` | `REPORT_RATE_LIMIT_PER_MINUTE` | 5 je Nutzer/Minute (dazu 20 systemweit) |
| `PROMPT_STABILITY_ENABLED=1` | `STABILITY_SCORING_ENABLED` | an (Standard) |
| `POLL_INTERVAL=2` | `WORKER_POLL_INTERVAL` | 2 Sekunden (Standard) |
| `RESEARCH_CACHE_TTL=604800` | `RESEARCH_CACHE_TTL_DAYS` | 14 Tage statt der gemeinten 7 |

Alle vier Standardwerte sind brauchbar. Wer eine dieser Zahlen ändern
will, muss den langen Namen setzen.

## Was Tavily und Perplexity wirklich schaltet

`ENABLE_TAVILY` und `ENABLE_PERPLEXITY` sind wirkungslos. Beide Dienste
schalten über die **Anwesenheit des API-Schlüssels**:

- `services/provider_tavily.py:50` — ohne `TAVILY_API_KEY` keine Suche
- Perplexity ebenso über `PERPLEXITY_API_KEY`

Wer einen der beiden abschalten will, entfernt den Schlüssel.

## Fünf blinde Flecken des Prüfverfahrens

Alle fünf sind in `scripts/env_unused.py` behandelt und in
`tests/test_kis1274_env_pruefung.py` festgehalten:

1. **Nur nach `os.getenv("NAME")` gesucht.** Namen, die über eine
   Konstante weitergereicht werden, galten als ungenutzt.
   → Nach dem nackten Namen suchen, nicht nach einem Zugriffsmuster.
2. **Zusammengesetzte Namen.** `f"OPENAI_MAX_TOKENS_{sektion}"` steht
   nirgends wörtlich im Code. → Die bekannten Präfixe kennen.
3. **Teilzeichenketten.** `RATE_LIMIT_PER_MINUTE` fand sich in
   `REPORT_RATE_LIMIT_PER_MINUTE` und galt deshalb als benutzt. Diese
   eine Verwechslung drehte die Antwort ins Gegenteil. → Wortgrenzen,
   die `_` als Wortzeichen behandeln; `\b` reicht nicht.
4. **Helfer statt `os.getenv`.** `_bool_env("X")`, `get_bool("X")`,
   `_truthy("X")`. → Löst sich mit Punkt 1.
5. **Eingelesen, aber nie verbraucht.** `settings.py` liest den Wert in
   ein Feld. Liest niemand das Feld, ist die Variable wirkungslos —
   trotz Treffer im Code. → Eigene Gruppe `NUR SETTINGS`; das Urteil
   fällt ein Mensch.

Ein sechster Fall betrifft die Prüfung selbst: Eine Datei, die
ENV-Namen nennt, um über sie zu reden — diese hier oder eine Testdatei —
meldet jeden Namen darauf als „benutzt". Das Skript überspringt `docs/`,
`tests/` und sich selbst.

## Grenzen

Ein Treffer im Laufzeit-Code ist ein Hinweis, kein Beweis. Steht der
Name nirgends in Anführungszeichen, ist er wahrscheinlich nur eine
Python-Konstante gleichen Namens — so lag der Fall bei
`PROMPT_STABILITY_ENABLED`. Das Skript meldet solche Fälle getrennt
unter `NUR BEZEICHNER`.

Umgekehrt liest Railway `DATABASE_URL` und
`MISE_PYTHON_GITHUB_ATTESTATIONS` selbst; sie stehen deshalb nirgends im
Code. Das Skript kennt sie (`PLATTFORM_VARIABLEN`).

## Reihenfolge

1. Stufe 1 und 2 löschen (42 Variablen), dazu die zwei aus Stufe 4.
   Kein Deploy, nur ein Neustart. **Nicht während eines Testlaufs.**
2. `ki-foerderung.jetzt` aus `CORS_ORIGINS` streichen — die Domain gibt
   es nicht mehr.
3. Danach einen Report erzeugen und mit `scripts/compare_reports.py`
   gegen den letzten Lauf halten. Bleiben die Kennzahlen gleich und
   meldet die Rückfall-Prüfung nichts, war das Löschen folgenlos.
