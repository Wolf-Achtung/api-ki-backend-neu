# ENV-Audit Railway — 2026-09-03

**Grundlage:** Wolfs Railway-Export (374 Variablen, Schlüssel maskiert),
abgeglichen gegen den Code auf `main` (Stand nach PR #1159).
**Methode:** Jeder Name wurde im Python-Code gesucht (ohne `tests/`,
`docs/`). Namensfamilien mit dynamischem Suffix
(`OPENAI_MAX_TOKENS_<SEKTION>`, `ANTHROPIC_MODEL_<SEKTION>`,
`ANTHROPIC_MAX_TOKENS_<SEKTION>`, `USE_ANTHROPIC_FOR_<SEKTION>`) wurden
gegen die Suffix-Bildung im Code geprüft. Danach: Semantik der gelesenen
Variablen (wirkt der Wert tatsächlich?).

**Störgefahr:** Keine der Empfehlungen verlangt einen Code-Deploy.
Variablen, die der Code nie liest, können ohne Wirkung auf die Pipeline
entfernt werden. Änderungen an *gelesenen* Variablen sind einzeln
markiert.

---

## 1. Ergebnis in Zahlen

| | Anzahl |
|---|---|
| Variablen gesamt | 374 |
| vom Code gelesen und wirksam | 224 |
| gelesen, aber ohne Wirkung (Semantik) | 28 |
| nie gelesen (Karteileichen) | 94 |
| dynamische Familien, wirksam | 28 |

---

## 2. Die fünf Befunde, die zählen

### 2.1 `USE_INTERNAL_RESEARCH="0"` schaltet nichts ab

Der Code liest diesen Namen nicht. Der Schalter für die interne
Recherche ist `RESEARCH_PROVIDER` — und der steht auf `hybrid`. Die
Recherche läuft also, obwohl die Variable „aus" sagt. Gleiche Falle wie
seinerzeit `OPENAI_MODEL_DEFAULT`.

**Empfehlung:** Variable entfernen. `RESEARCH_PROVIDER=hybrid` stehen
lassen — das Grounding der Förderpotenzial-Prosa braucht es. Der doppelte
Recherche-Lauf verschwindet mit dem Pipeline-PR (KIS-1266), nicht per ENV.

### 2.2 `ENABLE_LIVE_FOERDERPROGRAMME="true"` — Entwarnung

Die Live-Fördersuche (`live_data_integration`, eigener Tavily-Pfad mit
Ratenbegrenzung) ist eingeschaltet, aber ihre Einstiegsfunktion
`get_foerderprogramme_for_report` hat **keinen Aufrufer**. Es gibt also
keinen dritten Tavily-Pfad pro Report. Mit ihr hängen sieben weitere
Variablen in der Luft: `TAVILY_MAX_RESULTS`, `TAVILY_TIMEOUT_MS`,
`TAVILY_RATE_LIMIT_PER_HOUR`, `ENABLE_LIVE_TOOL_PRICING` und die
`RESEARCH_DAYS_*`.

**Empfehlung:** Alle acht entfernen. Der wirksame Tavily-Timeout ist
`TAVILY_TIMEOUT` in Sekunden (Default 8), nicht `TAVILY_TIMEOUT_MS`.

### 2.3 Vier Modell-Overrides, die Opus überstimmt

`ANTHROPIC_MODEL_GAMECHANGER`, `ANTHROPIC_MODEL_BUSINESS_CASE`,
`ANTHROPIC_MODEL_STRATEGIE_GOVERNANCE` stehen auf `claude-sonnet-5`,
`ANTHROPIC_MODEL_RISKS` auf `claude-opus-4-8`. Alle vier Sektionen
stehen in `OPUS_SECTIONS`, und das Opus-Routing gewinnt **vor** jedem
Sektions-Override. Die vier Variablen sind wirkungslos; die Sektionen
laufen auf Opus, wie in CLAUDE.md dokumentiert.

**Empfehlung:** Entfernen — sie suggerieren eine Steuerung, die nicht
existiert. `ANTHROPIC_MODEL_RECOMMENDATIONS`, `_FOERDERPOTENZIAL`,
`_EXECUTIVE_SUMMARY` (alle `claude-sonnet-5`) sind wirksam, aber gleich
dem Default; können bleiben oder gehen.

### 2.4 Temperatur und Reasoning-Effort erreichen die Modelle nicht

- `ANTHROPIC_TEMPERATURE="0.3"`: Der Client entfernt `temperature` für
  die Claude-5-Familie und Opus 4.8 (400-Fehler). Wirkt nur beim
  Fallback auf Haiku 4.5.
- `OPENAI_REASONING_EFFORT="medium"`: wird nur an Reasoning-Modelle
  (`gpt-5*`, `o*`) gesendet. `OPENAI_MODEL=gpt-4.1-mini` ist keins.
  Wirkt also in keiner aktiven Pipeline.
- `OPENAI_MODEL_FALLBACK="gpt-5.4-mini-2026-03-17"`: wird beim Start
  **nur geloggt**. Keine Fallback-Kette im Code nutzt den Wert.

**Empfehlung:** Die drei können bleiben (harmlos) oder gehen. Wichtig
ist nur das Wissen: Sie steuern nichts.

### 2.5 Zwei Admin-Listen

`ADMIN_EMAILS` (ENV) enthält `bewertung@` und `wolf.hohl@web.de` und gilt
für `/admin/*`. `core.whitelist.ADMIN_EMAILS` (Code) enthält nur
`bewertung@` und gilt für den Admin-Pfad im Strategie-Modul.
`wolf.hohl@web.de` ist also halb Admin.

**Empfehlung:** Im nächsten Backend-PR die Code-Konstante die ENV lesen
lassen (Union). Kein ENV-Eingriff nötig.

---

## 3. Karteileichen — nie gelesen (94)

Entfernen ist ohne Risiko: Was nie gelesen wird, kann nichts verändern.
Empfohlen in zwei Tranchen mit einem Testlauf dazwischen — nicht weil
ein Risiko besteht, sondern damit ein späterer Fehler eindeutig
zuzuordnen bleibt.

**Tranche 1 — ganze Engine-Familien ohne Leser (61):**

- `TOOLS_*` (26 von 39): `TOOLS_DAYS`, `_AI_ACT_ALIGNMENT_REQUIRED`,
  `_ALIGNMENT_WEIGHT_AI_ACT/_CONFIDENCE/_FUNDING`, `_ANALYTICS_ENABLED`,
  `_CATEGORY_BALANCE_WARN_THRESHOLD`, `_CLUSTER_COUNT`,
  `_CONFIDENCE_LOW_THRESHOLD`, `_DIAGNOSTICS_ENABLED`,
  `_EMBEDDING_CACHE_ENABLED`, `_EMBEDDING_ENABLED`, `_EMBEDDING_MODEL`,
  `_EMBEDDING_PROVIDER`, `_FIT_THRESHOLD_HIGH/_MEDIUM`,
  `_FUNDING_MIN_CONFIDENCE`, `_GOVERNANCE_ENABLED`,
  `_HARMONIZATION_ENABLED`, `_KMU_GOVERNANCE_BOOST`,
  `_SEGMENT_MIN_COVERAGE`, `_SOLO_PERSONA_BIAS_PENALTY`, `_STACK_SIZE`,
  `_STARTER_KITS_ENABLED`, `_TREND_VOLATILITY_THRESHOLD`,
  `_WORKFLOW_ENABLED`
- `FUNDING_*` (17): `FUNDING_DAYS`, `_CONFIDENCE_STABILITY_REQUIRED`,
  `_DRIFT_THRESHOLD`, `_MAX_PROGRAMMES`, `_MIN_PREDICTIVE_OPPORTUNITY`,
  `_OPTIMIZER_*` (9), `_STRESS_ITERATIONS`, `_STRESS_TEST_ENABLED`,
  `_STRESS_TIMEOUT_SEC`
- `PROMPT_*` (5): `_AUTO_UNFREEZE_AFTER_DAYS`, `_LIFECYCLE_ENABLED`,
  `_LIFECYCLE_LOG_LEVEL`, `_RECOVERY_ENABLED`,
  `_RECOVERY_ON_CRITICAL_DRIFT`
- `AI_ACT_*` (7): `AI_ACT_DEBUG`, `_DEFAULT_RISK`,
  `_MIN_REASONING_LENGTH`, `_MODE`, `ENABLE_AI_ACT_ATTACH_CSV`,
  `ENABLE_AI_ACT_DEBUG`, `ENABLE_AI_ACT_INJECTION`
- `DASHBOARD_*` (3), `TELEMETRY_*` (2), `ZIM_*` (2), `LEARNING_*` (2)

**Tranche 2 — Einzelne (33):**

`ANTHROPIC_BASE_URL`, `ANTHROPIC_ENABLED`, `GUARDRAILS_V`,
`MAX_GUARDRAIL_HITS`, `MAX_PARALLEL_LLM_CALLS`, `MAX_PARALLEL_SECTIONS`,
`ENABLE_GUARDRAILS`, `ENABLE_METRICS`, `ENABLE_PROMPT_LABELS`,
`ENABLE_TAVILY`, `HARD_FAIL_ON_HTML_ERRORS`,
`HARD_FAIL_ON_VALIDATION_ERRORS`, `ENABLE_SENSITIVITY_TABLE`,
`USE_STOCK_IMAGES`, `TOKEN_LIMIT_HTML_REPAIR`, `MARKET_INSIGHTS_ENABLED`,
`STARTER_KITS_MAX_TOOLS`, `REPORT_ADMIN_EMAIL`, `DEBUG_LOG_HTML_SNAPSHOT`,
`DEBUG_LOG_PROMPTS`, `CORS_MAX_AGE`, `RATE_LIMIT_PER_MINUTE`,
`API_RATE_LIMIT_PER_MIN`, `AUTH_ALLOW_DEV_CONSOLE`, `AUTH_SEND_MAIL`,
`FEEDBACK_SECRET`, `PERPLEXITY_RATE_LIMIT_PER_HOUR`,
`RESEARCH_RSS_EXTRA_PATH`, `DISABLE_HIGH_RISK_AUTO_UPGRADE`,
`USE_INTERNAL_RESEARCH`, `ENABLE_LIVE_TOOL_PRICING`,
`MISE_PYTHON_GITHUB_ATTESTATIONS` (Railway-Build, kann bleiben),
`OPENAI_MAX_TOKENS_PROMPT_FRAMEWORK` (keine Sektion dieses Namens)

---

## 4. Gelesen, aber ohne Wirkung (28)

| Variable | Warum wirkungslos | Empfehlung |
|---|---|---|
| `USE_INTERNAL_RESEARCH` | siehe 2.1 | entfernen |
| `ENABLE_PERPLEXITY` | landet in `settings.research.enable_perplexity`, das niemand liest. Perplexity läuft, sobald `PERPLEXITY_API_KEY` gesetzt ist | entfernen |
| `ENABLE_LIVE_FOERDERPROGRAMME`, `TAVILY_MAX_RESULTS`, `TAVILY_TIMEOUT_MS`, `TAVILY_RATE_LIMIT_PER_HOUR`, `RESEARCH_DAYS_DEFAULT/_MAX/_MIN` | siehe 2.2 | entfernen |
| `RESEARCH_LANG`, `RESEARCH_COUNTRY`, `PERPLEXITY_TIMEOUT_MS`, `PERPLEXITY_MAX_TOKENS` | Settings-Felder ohne Verbraucher | entfernen |
| `RESEARCH_INCLUDE_FUNDING`, `RESEARCH_INCLUDE_TOOLS`, `RESEARCH_EXCLUDE` | nur `research_policy.py` liest sie, und das importiert nur ein totes Testmodul. Die Domänenlisten sind gut — sie werden nur nicht angewandt | behalten, im Pipeline-PR anschließen (siehe 6) |
| `RESEARCH_CACHE_PATH`, `RESEARCH_CACHE_TTL` | nur tote Module; Datei existiert nicht | entfernen |
| `ANTHROPIC_MODEL_GAMECHANGER/_BUSINESS_CASE/_STRATEGIE_GOVERNANCE/_RISKS` | siehe 2.3 | entfernen |
| `USE_ANTHROPIC_FOR_*` (5) | redundant: `ANTHROPIC_SECTIONS` listet alle, `LLM_PROVIDER_DEFAULT=anthropic` | entfernen |
| `ANTHROPIC_TEMPERATURE`, `OPENAI_REASONING_EFFORT`, `OPENAI_MODEL_FALLBACK` | siehe 2.4 | dürfen bleiben |
| `REPORT_TEMPLATE_PATH="pdf_template_v7.html"` | Legacy-Name; der Renderer nimmt ohnehin `templates/pdf_template_v7.html` als Default | entfernen |
| `SMTP_*` (7) | nur Fallback, `EMAIL_PROVIDER=resend` | behalten (Notnagel) |

---

## 5. Wirksam und in Ordnung — mit Anmerkungen

| Variable | Wert | Anmerkung |
|---|---|---|
| `ANTHROPIC_MODEL_DEFAULT` | `claude-sonnet-5` | wirksam; hat Vorrang vor `ANTHROPIC_MODEL`. CLAUDE.md nennt nur `ANTHROPIC_MODEL` — Doku anpassen |
| `ANTHROPIC_MODEL_FALLBACK` | `claude-haiku-4-5` | wirksam; Code-Default wäre Sonnet 4.5. Haiku ist billiger und schwächer — bewusste Wahl? |
| `ANTHROPIC_MODEL_OPUS`, `OPUS_SECTIONS` | Opus 4.8, 8 Sektionen | wirksam, konsistent mit CLAUDE.md |
| `ANTHROPIC_MAX_TOKENS_GAMECHANGER/_RECOMMENDATIONS/_RISKS` | 10k/15k/12k | wirksam (Token-Override gilt auch für Opus-Sektionen) |
| `OPENAI_MODEL` | `gpt-4.1-mini` | wirksam; OpenAI ist Fallback-Kette |
| `OPENAI_MAX_TOKENS_<SEKTION>` (27) | | wirksam, wenn die Sektion existiert; `PROMPT_FRAMEWORK` existiert nicht |
| `CHAT_CONVERSATION_MODEL` | `claude-sonnet-4-5-20250929` | gesetzt — der Nachfolger des deprecated Sonnet 4. CLAUDE.md-Tabelle ist damit veraltet |
| `EXTRA_WHITELIST` | `wolf@hohl.rocks` | bereits genutzt — gut |
| `CORS_ORIGINS` | 5 Ursprünge | `report.ki-sicherheit.jetzt` fügt der Code selbst hinzu. `ki-foerderung.jetzt` steht drin — gibt es diese Seite noch? |
| `RESEARCH_PROVIDER` | `hybrid` | wirksam; behalten |
| `TAVILY_API_KEY`, `PERPLEXITY_API_KEY` | gesetzt | Tavily: Tools/Förder-Grounding. Perplexity: Markt-Box, die im PDF nicht erscheint — Kosten ohne sichtbaren Nutzen, siehe 6 |
| `GPT_PARALLEL_WORKERS=4`, `LANG_SWEEP_PARALLELISM=6` | | wirksam |
| `STALE_BRIEFING_TIMEOUT=600` | | gleich dem Default |
| `CRON_SECRET` | gesetzt | schützt `/api/content/research-news` — der Endpunkt sollte nicht mehr benutzt werden (blockiert den Web-Container). Die Wächter laufen als CI-Jobs (PR #1160) |
| Pfad-Variablen (7) | | alle Dateien vorhanden außer `data/research_cache.json` (Cache ist ohnehin tot) |

---

## 6. Was der Pipeline-PR (KIS-1266) zusätzlich aufräumen sollte

Alles Backend-Änderungen, also nur mit Deploy und nur außerhalb eines
Testlaufs:

1. Zweiten `run_research`-Lauf entfernen (halbiert Tavily, spart ~8 s).
2. Tote Module löschen: `services/research.py`, `providers/tavily.py`,
   `research_fetcher.py`, `research_hybrid_addon.py`,
   `services/test_research_system.py`, `research_policy.py` — **oder**
   `research_policy.py` an `provider_tavily` anschließen, damit die
   guten Domänenlisten `RESEARCH_INCLUDE_*`/`RESEARCH_EXCLUDE` endlich
   wirken. Empfehlung: anschließen. Das verbessert die Trefferqualität
   der Fördersuche spürbar (nur Förderportale statt Blogs).
3. Perplexity-Aufrufe prüfen: Die Markt-Box wird im DE-Template nicht
   gerendert. Entweder rendern oder die beiden Perplexity-Aufrufe je
   Report abschalten.
4. `core.whitelist.ADMIN_EMAILS` aus der ENV `ADMIN_EMAILS` ergänzen.
5. CLAUDE.md: `ANTHROPIC_MODEL_DEFAULT`-Vorrang, Chat-Modell aktualisiert,
   OpenAI-Fallback-Variable dokumentieren.

---

## 7. Reihenfolge ohne Störgefahr

1. **Jetzt, in Railway, ohne Deploy:** Tranche 1 entfernen (61 nie
   gelesene Variablen). Railway startet den Dienst neu — das ist der
   einzige Effekt. Nicht während eines Testlaufs.
2. **Nach einem sauberen Testlauf:** Tranche 2 und die wirkungslosen
   gelesenen Variablen entfernen (Abschnitt 4, Spalte „entfernen").
3. **Als Backend-PR, wenn kein Testlauf aktiv ist:** Abschnitt 6.

Ergebnis: von 374 auf rund 240 Variablen, jede davon mit nachweisbarer
Wirkung.
