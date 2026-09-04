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
- Der Werkzeug-Block im R1-Report (`VERIFIED_TOOLS_HTML`, KIS-1280)
  rendert `tools_seed.json` deterministisch. **Regel: Ein Preis
  erscheint nur mit `verified_at`.** Ohne Prüfdatum steht der Verweis
  auf die Anbieterseite. Stand 04.09.2026 haben 20 von 23 Einträgen kein
  Prüfdatum — die Lücke ist im Report sichtbar, mit Absicht.
  Kill-Switch: `VERIFIED_TOOLS_BOX_ENABLED=0`.
- Zwei tote Tool-Pfade (nicht gelöscht, aber ohne Wirkung):
  `services/tools_html_output.py` hat keinen Aufrufer, und
  `TOOLS_FUNDING_ALIGNMENT_HTML` wird erzeugt, sitzt aber in Anhang A12
  — kein Anhang erscheint in den Berichten.
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

## Trennung von Tatsache und Einordnung (KIS-1281)

Im Report stehen zwei Sorten Aussagen, und sie haben verschiedene
Quellen. Wer das vermischt, bekommt ZIM trotz Antragsstopp und
Werkzeuge ohne belegte Datenschutzlage.

| Sorte | Quelle | Beispiel |
|---|---|---|
| Prüfbare Tatsache | gepflegte Daten | Preis, DSGVO-Status, Förderquote, Frist |
| Beratende Einordnung | Sprachmodell | „Für Ihre Postproduktion zuerst der Schnitt" |

- **Stufe 1** — `services/kuratierte_fakten.py` reicht die gepflegten
  Daten als Faktenblock in die Prompts `tools_empfehlungen` und
  `foerderpotenzial`. Regel im Block: nur diese Namen, keine Preise in
  den Fließtext. Braucht kein Netz (anders als `research_grounding`);
  beide Blöcke werden mit `verbinde_grounding` zusammengeführt, die
  kuratierten zuerst. Schalter: `KURATIERTE_FAKTEN_ENABLED=0`.
- **Stufe 2** — `scripts/tools_radar.py --apply-fixes` ersetzt tote
  Adressen durch erreichbare auf derselben Herstellerdomain und öffnet
  einen Entwurfs-PR. Dreifach geprüft: gleiche Domain, neu erreichbar,
  alt nachweislich tot (`unpruefbar` zählt nicht). **Preise nie
  automatisch** — ein Suchtreffer ist eine Seite, kein geprüfter Preis.
- **Stufe 3** — `funding_recommender.ist_beantragbar` prüft jetzt auch
  die Frist. Textangaben („laufend", „4 Termine/Jahr") gelten als offen.
  Entfernt heute kein Programm; das Netz spannt für später.
- **Stufe 4** — Feedback-Felder `tools_adopted` und `funding_applied`
  (Freitext, freiwillig), ausgewertet mit
  `scripts/empfehlungs_resonanz.py`. Der wertvollste Wert steht unter
  „Genannt, aber nicht von uns empfohlen": die einzige Stelle, an der
  Neues von aussen hereinkommt, ohne dass ein Modell es erfindet.
  Belastbar ab etwa 30 Rückmeldungen.

- Beraterstimme: Hinter der Marke steht eine Person. Der Status-Report
  setzt `wir` seit jeher in `ich` (Ersetzungsliste in `gpt_analyze.py`,
  tauscht aber nur Wörter — „weisen wir" wurde zu „weisen ich"). Der
  Strategiebericht nutzt seit KIS-1283 `services/beraterstimme.py`, das
  die Verbform mitzieht („empfehlen wir" → „empfehle ich"). Fester Text
  in deterministischen Bausteinen vermeidet die erste Person Plural
  ganz. Schalter: `BERATERSTIMME_ENABLED=0`.

## Tabellen im PDF (KIS-1284)

Breite Tabellen sind die empfindlichste Stelle im Layout. Headless-Chromium
hat kein deutsches Trennwörterbuch; zu schmale Spalten brechen deshalb ohne
Trennstrich mitten im Wort.

- Ab **5 Spalten** läuft die inhaltsbasierte Härtung
  (`style_lint.harden_wide_tables`): Spaltenbreiten aus dem längsten
  unteilbaren Inhalt, Daten und Beträge non-breaking, `table-layout:fixed`,
  Kompaktschrift, Marker `data-ksj-hardened="1"`. Darunter bleibt es beim
  alten Pfad.
- Der Marker ist Pflicht: Ohne ihn setzt `html_enhancer` Schrift und
  Padding zurück — genau die Werte, auf die die Spalten-Minima kalibriert
  sind.
- **Deutsch trennt nur an gesetzten Stellen** (`hyphens:manual`).
  `hyphens:auto` erzeugt „Selbs-tbetrieb" (KIS-1244). Die Trennstellen
  setzt `soften_table_long_words` direkt danach als `&shy;`.
- Die Trennheuristik folgt der **Silbenregel**, nicht der Wortbildung.
  Komposita brechen deshalb manchmal eine Stelle zu spät
  („projek-tabhängig", „Startin-vestition"). Ohne Wörterbuch ist das
  nicht zu beheben — eine Regel, die „sch" pauschal in die Folgesilbe
  schiebt, macht aus dem korrekten „Deutsch-land" ein „Deut-schland"
  (geprüft am Lauf 1271, als Kommentar im Code festgehalten).
  Unteilbare Paare (`ck`, `ch`, `ß` …) sind dagegen hart geschützt —
  auch gegen die Onset-Regel, die die Trennstelle verschiebt (KIS-1287).
- Reichen die Mindestbreiten nicht auf 100 %, greift die Staffel:
  Wort-Minimum auf 12 Zeichen deckeln → nur noch die harten Minima →
  gleichmäßig skalieren (mit Warnung im Log).
- Bis KIS-1284 galt das alles **nur für Englisch**. Die drei EN-Läufe
  (KIS-1272/1273/1275) hielten den DE-Pfad ausdrücklich byte-identisch —
  und damit kaputt.
- In gehärteten Tabellen gilt die Kopfzeilen-Schwelle für Trennstellen
  (ab 10 Zeichen) auch für Datenzellen — bei 12,5 % Spaltenbreite bricht
  sonst schon „Abonnement" strichlos (KIS-1285).
- **Reihenfolge entscheidet.** `harden_wide_tables` überspringt Tabellen,
  die schon ein `<colgroup>` tragen. `html_enhancer._balance_column_widths`
  setzt eines — aber nur bei „echter Schieflage" (breiteste Spalte ≥ 3×
  schmalste), also genau bei der Fördertabelle mit ihrer 70-Zeichen-URL
  neben „Hoch". Deshalb läuft die Härtung im Strategiebericht **vor** dem
  Enhancer (KIS-1286). Wer eine neue Tabellenstufe einhängt, prüft diese
  Reihenfolge zuerst.
- Schrägstrich-Fügungen („GitHub/GitLab") bekommen in gehärteten Tabellen
  ein Nullbreiten-Leerzeichen nach dem Schrägstrich — nie einen
  Trennstrich. Beide Seiten brauchen vier Buchstaben, sonst träfe die
  Regel Einheiten wie `h/mo.`.

## Die Sparte (KIS-1288)

Der Fragebogen erhebt `medien_sparte` mit sieben Werten
(`field_registry.py`). Befund vom 04.09.2026
(`docs/branchen-audit-2026-09-04.md`): Sie erreichte einen Prompt von
139, die Fallstudie und das Deckblatt — Strategiebericht, KPA und
Resilienz-Check kannten sie nicht.

- Label immer aus `services/medien_sparte.py` (`label`, `aus_antworten`).
  Ein unbekannter Wert ergibt ein leeres Label, nie den Roh-Slug.
- Strategiebericht: `medien_sparte` im Kontext; `persona_und_sparte`
  ersetzt die „Mittelstand"-Zeile des System-Prompts durch die
  konfigurierte Persona (`REPORT_PERSONA_PATH`). Ohne Konfiguration
  ändert sich nichts.
- KPA: `MEDIEN_SPARTE_LABEL` im Kontext; die vier `gc_*`-Prompts nennen
  sie bedingt (`{% if MEDIEN_SPARTE_LABEL %}`).
- **Sparten-Feld in den Daten** (KIS-1292, Stufe 4): `sparten` ist eine
  optionale Liste von Slugs an Werkzeugen (`tools_seed.json`, 13 von 23)
  und Förderprogrammen (`funding_programmes_core_2025.json`, alle 14
  exklusiven Medienprogramme). `medien_sparte.passt_zur_sparte` liefert
  `None` (kein Feld oder keine Kunden-Sparte: nichts ändert sich),
  `True` oder `False`. Werkzeuge: Treffer steigt auf, nichts fällt heraus.
  Förderung: Treffer ×1.2; kein Treffer bei `branch_exclusive` → raus
  (ein Tonstudio sieht keinen DFFF mehr), sonst ×0.8. Der Faktenblock
  (`kuratierte_fakten`) läuft über `recommend_tools` mit. Fallstudien:
  Verlag, Tonstudio und Content Creation haben eigene Fälle
  (`sofort_start_generator.FALLSTUDIEN_MEDIEN`, DE und EN); die Auswahl
  geht über den Slug, nicht mehr über Teilstrings im Label.
  Test: `tests/test_kis1292_sparte_daten.py`.
- **Tot:** `extra_sections.build_starter_stacks` iteriert über
  `data/starter_stacks.json` wie über eine Liste; die Datei ist ein Dict.
  Jeder Eintrag wirft, die Schleife fängt das still, das Ergebnis ist
  immer „Keine Starter-Stacks konfiguriert". Kein Template rendert
  `STARTER_STACKS_HTML`. Kein Sparten-Ziel — erst Entscheidung, ob der
  Baustein leben soll.
- In Produktion setzt Railway `VISIBLE_BRANCHES=medien` und
  `REPORT_PERSONA_PATH`; lokal stehen beide in `.env.example` als
  Kommentar.
- **Kein Beispiel aus einer fremden Branche** (KIS-1289). Ein Beispiel
  schlägt jede Regel — ein Steuerberater-Beispiel zieht den Text vom
  Tonstudio weg. Ersatz-Beispiele verteilen sich über die Sparten.
  `tests/test_kis1289_prompt_beispiele.py` prüft jede Prompt-Datei; der
  Test findet auch den geschützten Bindestrich in `go‑digital`, den
  `grep` übersieht.
- **Ausgesetzte Programme nie als Empfehlung im Prompt**: ZIM
  (`paused` bis 15.01.2027) und go-digital (`expired`) standen bis
  KIS-1289 in acht Prompts als Beispiel oder Whitelist — auch im
  deutschen Förder-Prompt für KMU. Der PDF-Wächter hätte das erst
  hinterher gefunden.
- **Eine Option lebt an fünf Stellen** (KIS-1291): `field_registry.py`
  (Label-Fallback `_flat_option_label`), `routes/chat.py` (`_QR_OPTIONS`
  DE, EN-Anzeige-Map, `_ANWENDUNG_TO_PILOT`),
  `services/chat_conversation.py` (DE-Anzeige),
  `services/chat_normalizer.py` (`ENUM_VALUES`) — plus beide Formbuilder
  im Frontend. `tests/test_kis1291_optionen.py` hält die fünf gleich;
  wer eine Option ergänzt, ergänzt alle. Der Wert `produktion` bleibt
  (Smart-Skip hängt daran), das Label heißt jetzt „Produktion /
  Postproduktion". Achtung: `produktion` ist auch ein Sparten-Wert
  („Film-/TV-Produktion") — Ersetzungen am Label verankern, nie am Wert.

## Textknoten sind nicht nur Text (KIS-1285)

`_TAG_SPLIT_RE` teilt HTML an Tags. Was dazwischen liegt, gilt als Text —
auch der Inhalt von `<style>` und `<script>`. Die Prozent-Normalisierung
machte daraus `top: 50 %`; Chromium verwarf die Regel still, und das
Deckblatt des Strategieberichts verlor seinen Score (Lauf 1269).
**Jede Funktion, die auf Textknoten arbeitet, muss diese beiden Elemente
überspringen.** Betroffen sind alle `_TAG_SPLIT_RE`-Nutzer in
`style_lint.py` und `solo_final_pass.py`.

## Werkzeuge

- `scripts/compare_reports.py alt.pdf neu.pdf` — vergleicht zwei
  Report-Läufe: Kennzahlen, dünne Seiten, Rückfall-Prüfung gegen die
  sieben behobenen Fehler. Exit-Code 1 bei einem Rückfall. Seit
  KIS-1284 prüft es auch auf zerhackte Tabellenzellen; „€/Monat" zählt
  nur mit Kontext („laufende Tool-Kosten"), sonst schlug der Preis des
  ersten Werkzeugs als OPEX-Abweichung durch.
- `scripts/env_unused.py liste.txt` — prüft eine Liste von ENV-Namen
  gegen den Laufzeit-Code. Kennt die vier Fallen, an denen die
  Handprüfung scheitert (Konstanten, dynamische Namen,
  Teilzeichenketten, `_bool_env`-Helfer).
- `POST /api/admin/testrun/replay/{briefing_id}` — erzeugt einen Lauf
  mit identischen Antworten (kopiert auch FB2). Admin-Key per Header
  `X-Admin-Key`; der Query-Parameter bleibt gültig, verträgt aber kein
  `+` im Schlüssel. **Ohne `email_override` setzt der Endpunkt eine
  Wegwerf-Adresse** (`test-replay-<zeit>@ki-sicherheit.jetzt`) — sonst
  ginge bei jedem Testlauf eine Mail an den echten Kunden.

  ```bash
  curl -X POST \
    -H 'X-Admin-Key: $STRATEGY_ADMIN_KEY' \
    -H 'Content-Type: application/json' \
    -d '{"email_override":"wolf@hohl.rocks"}' \
    'https://api-ki-backend-neu-production.up.railway.app/api/admin/testrun/replay/<id>?force=true'
  ```

  Vorher `…/api/healthz` abfragen: Ein Deploy mitten in der Generierung
  bricht sie ab. `?force=true` hebt die 30-Minuten-Sperre auf.

  **Zwei Nummern, eine Falle:** Die `<id>` ist die Briefing-ID aus der
  Datenbank. Die Nummer im PDF-Dateinamen (`KIS1272`) ist die Briefing-ID
  **plus 117** (`REPORT_DISPLAY_OFFSET`, `utils/report_display_id.py`).
  Wer „Replay von 1272" liest, muss `replay/1155` aufrufen; das Ergebnis
  ist Briefing 1156 und heißt im PDF KIS1273. Am 04.09.2026 stand
  `replay/1272` als Befehl in einer Antwort — die ID gibt es nicht.

## Nicht verhandelbar

- Der Firmenname wird im Fragebogen/Chat nirgendwo erhoben
  (CI-Invariante: `tests/golden/`, `_NAME_KEY_RE`).
- Backend-Merges lösen einen Railway-Deploy aus und killen laufende
  Report-Generierungen — nie mergen, während ein Testlauf aktiv ist.
