# Steckbrief api-ki-backend-neu

Letzter Wartungs-Durchgang: **2026-09-05**.
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
- Tool-Daten: `data/tools_seed.json` hat 31 Einträge, 11 mit
  `verified_at` (8 davon aus dem Faktencheck vom 05.09.2026, KIS-1296:
  LanguageTool, DeepL Write Pro, Duden-Mentor, Auphonic, iZotope RX,
  Adobe Podcast Enhance, Crowdin, Canva Magic Studio). Abgelehnt, weil
  Verarbeitungsort oder DPA nicht belegt: Lokalise, Scenario, Inworld,
  Opus Clip (Begründung in `data/kandidaten_stufe4.json`). Der
  Tool-Radar läuft (Issue #1168). Die
  Domainbeschränkung (KIS-1273) wirkt: Der Lauf vom 03.09. 22:23 lieferte
  35 Kandidaten, alle auf der jeweiligen Herstellerdomain. Preise und
  DSGVO-Status muss trotzdem ein Mensch bestätigen — der Radar meldet
  nur. Alle zwölf toten Trust-URLs sind ersetzt (KIS-1277/1278);
  Adobe-Befunde sind Timeouts, keine toten Seiten.
- Zwei Tool-Listen: `data/tools_seed.json` (31 Einträge, der Radar prüft
  sie) und `DEFAULT_TOOLS` in `services/tools_recommender.py` (12
  Einträge, Notfall-Ausweichliste, ungeprüft). Wo sich beide
  überschneiden, hält `tests/test_kis1278_zweite_toolliste.py` sie
  gleich. Der Seed-Pfad ist seit KIS-1278 absolut — vorher konnte ein
  anderes Arbeitsverzeichnis still die Ausweichliste aktivieren.
- Der Werkzeug-Block im R1-Report (`VERIFIED_TOOLS_HTML`, KIS-1280)
  rendert `tools_seed.json` deterministisch. **Regel: Ein Preis
  erscheint nur mit `verified_at`.** Ohne Prüfdatum steht der Verweis
  auf die Anbieterseite. Stand 05.09.2026 haben 20 von 31 Einträgen kein
  Prüfdatum — die Lücke ist im Report sichtbar, mit Absicht. Nächster
  Prüflauf: `docs/perplexity-briefing-stufe4.md` als Vorlage, Ergebnis
  über `data/kandidaten_stufe4.json` und
  `scripts/kandidaten_uebernehmen.py`.
  Kill-Switch: `VERIFIED_TOOLS_BOX_ENABLED=0`.
- Zwei tote Tool-Pfade (nicht gelöscht, aber ohne Wirkung):
  `services/tools_html_output.py` hat keinen Aufrufer, und
  `TOOLS_FUNDING_ALIGNMENT_HTML` wird erzeugt, sitzt aber in Anhang A12
  — kein Anhang erscheint in den Berichten.
- Toter Code gelöscht: `services/funding_engine_v2.py` (1278 Zeilen,
  2026-09-03), `services/funding_parser.py` (101 Zeilen, 2026-09-04) und
  `services/funding_service.py` samt `data/funding/funding_de.json`,
  `funding_eu.json`, `config.json` (2026-09-05, KIS-1297 — kein Report
  las sie, die monatliche Routine pflegte sie trotzdem). Es bleiben drei
  Förderquellen: `data/funding_programmes_core_2025.json` (alle
  deutschen Reports), `data/funding/funding_de_en.json` und
  `funding_eu_core_en.json` (englische Reports), dazu
  `data/funding_programs.json` als Fallback in
  `services/research_pipeline.py`. Die Statusregel liegt in
  `funding_recommender.ist_beantragbar` und gilt seit KIS-1297 auch im
  EN-Pfad (`funding_service_en`).
- Ein Förderdaten-Punkt ohne Beleg (als Notiz im Datensatz vermerkt):
  „aws digi Invest" als eigenständiges Programm. Digitalbonus Bayern ist
  seit 05.09.2026 belegt wieder `active` (Laufzeit bis 31.12.2027,
  monatliches Kontingent); der Förder-Radar prüft nur noch die
  Basis-Blacklist, denn der Enforcer filtert Digitalbonus außerhalb
  Bayerns bedingt, nicht als totes Programm. Neu seit dem Faktencheck:
  Initiative Musik (Exportförderung, `musik_audio`) und Deutscher
  Verlagspreis (Preisgeld, `verlag_publishing`; bis zur Wiedervorlage am
  01.06.2027 auf `paused`, Bewerbung nur im Juli). Musikfonds abgelehnt:
  fördert Kunstprojekte, Antragsrecht von Unternehmen nicht belegt.
- ZIM steht bis zur Wiedervorlage am 15.01.2027 auf `paused` und fällt
  aus allen Empfehlungen. Der Förder-Radar erinnert ab diesem Datum.
- DFFF und GMPF stehen seit 05.09.2026 auf `paused` (Wiedervorlage
  01.11.2026): Die FFA nimmt seit 20.08.2026 keine Anträge für Drehbeginn
  2026 mehr an, das Einreichverfahren 2027 öffnet voraussichtlich im
  November (Beleg: `docs/FOERDER_VERIFIKATION_2026-09-05.md`). Keine
  Fusion — beide bleiben getrennte Programme mit eigener Richtlinie 2026.
  Film- und VFX-Kunden sehen bis dahin die regionalen Filmförderer,
  Filmerbe, kulturelle Filmförderung, Creative Europe MEDIA, Eurimages.
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

## Der Strategiebericht erfindet, was er nicht bekommt (KIS-1293)

Lauf KIS1272 (04.09.2026): Das Kapitel „Tool-Landschaft" (S4) empfahl
„Adobe Sensei", „Legiscope", „TrustArc", nannte Preismodelle und
DSGVO-Einstufungen im Fließtext und heftete den Vendor-Audit-Status aus
Report 1 („nicht bestanden") an Claude und Runway. Quelle laut Bericht:
„Vendor-Audit-Status Report 1 (Kundenunterlagen)". Das Risiko-Kapitel
(S8) stufte Copilot und Runway als „voraussichtlich hochriskant" ein und
nannte den 02.08.2026 „in wenigen Wochen erreicht" — vier Wochen danach.

- KIS-1281 galt nur für R1. Der Strategiebericht hatte **keinen**
  Faktenblock. Jetzt: `kuratierte_fakten.build_tool_fakten_strategie`
  (mit Anbieter-URL, sparten-sortiert über `recommend_tools`) als
  `{kuratierte_tools}` in S4 (DE/EN). Nie leer — ohne Daten steht die
  Rückfall-Regel im Prompt. Regel: nur Werkzeuge aus der Liste oder aus
  dem Stack des Kunden; Preis nur als Art; Hosting wörtlich; der
  Audit-Status gilt nie für ein empfohlenes Werkzeug.
- Der Prompt sagte „wenn das Reportdatum vor dem Stichtag liegt", gab
  dem Modell aber kein Datum. Jetzt rechnet `services/ai_act_stichtag.py`
  (`art50_prompt_text`, `art50_satz`) und liefert `{ai_act_stichtag}`
  in S8; die festen Hinweise (Pflichtenmatrix, KPA-Impressum,
  Feldhilfe) sagen „gelten seit". **Jede Frist gehört in Code, nie in
  einen Prompt-Satz mit Bedingung.**
- `{ai_act_risikoklasse}`: Text-, Bild-, Video- und Ton-Werkzeuge sind
  keine Hochrisiko-Systeme nach Anhang III. Hochrisiko nur über den
  Anwendungsfall, nie über das Werkzeug.
- Nachlauf KIS1273: S4 war sauber, aber das Umsatzkapitel (S3b) nannte
  „Adobe Sensei" als KI-Hebel — es bekam nur die Namensliste
  `{kuratierte_tools_namen}` nach. Die R1-Fördertabelle
  (`extra_sections.build_core_funding_table_html`) ist ein **eigener
  Pfad** und zeigte dem VFX-Studio weiter die Games-Förderung; der
  Sparten-Filter steht jetzt auch dort. Die Sofort-Start-Seite trug
  feste Preise aus dem Code („25–30 €/Nutzer/Monat") — jetzt
  `_sofort_preis`: Preis nur, wenn das Werkzeug mit `verified_at` im
  Seed steht, sonst „siehe Anbieterseite".
- Test: `tests/test_kis1293_strategie_fakten.py`. Wächter in
  `scripts/compare_reports.py`: „Stichtag als Zukunft",
  „Standard-Werkzeug als Hochrisiko", „erfundenes Werkzeug".

## Benchmarks sind Richtwerte (KIS-1294)

Vier Quellen, keine gemessen: `services/benchmarks.py` (tot, gelöscht —
der BDZV-Wert „96/100" maß den Anteil KI-Nutzer in Zeitungsverlagen, nicht
einen Reifegrad), `data/benchmarks.json` (interne Synthese), die
Größen-Schwellen `extra_sections.BENCHMARK_SCORES` (Deckblatt) und der
Prompt `wettbewerb_benchmark.md` samt EN-Alias `competition_benchmark.md`
(„Benchmark aus 30 Assessments", feste Ø- und Top-10-Zahlen).

- **Regel:** Eine Zahl ohne benannte Messung heißt im Report
  „Richtwert" / „guide value". Nie „Branchendurchschnitt", „Studie",
  „Assessments". Wer eine echte Quelle einträgt, darf die Zahl wieder
  als Messung nennen — mit Titel und URL im Datensatz.
- Die Zahlen selbst blieben unverändert; nur ihre Bezeichnung ist jetzt
  ehrlich. Test: `tests/test_kis1294_benchmarks_richtwert.py`.

## Sparten-Gate (KIS-1295)

Sieben Gold-Profile `data/test_profiles_gold/medien_<sparte>_sparte.json`
mit gesetztem `medien_sparte` laufen in `tests/golden/test_sparten_gate.py`
durch alles, was ohne Netz entscheidet: Label, Fallstudie, R1-Fördertabelle,
Förderempfehlung, Werkzeugliste und Faktenblock, System-Prompt,
Options-Labels, Platin-Kette. Wer Stufe 1 bis 4 anfasst, sieht es hier
zuerst. Die Profile nutzen das Vokabular aus `chat_normalizer.ENUM_VALUES`.

## Förder-Frischecheck (KIS-1297)

Die monatliche Routine „Förder-Aktualitäts-Check" (Claude Code Remote,
jeden 5. um 07:00 UTC) lief am 05.09.2026 an der falschen Datei und
konnte ihr Ergebnis nicht pushen. Befund und Regeln:

- `scripts/check_funding_freshness.py` prüft drei Dateien: core_2025
  (`verified_at`), `funding_de_en.json` und `funding_eu_core_en.json`
  (`last_verified`). Bis KIS-1297 fehlte core_2025 — die Datei, aus der
  jeder deutsche Report liest, wurde nie als veraltet gemeldet.
- **Belegregel der Routine:** Status, Frist, Fördersatz oder Obergrenze
  ändern sich nur nach tatsächlich gelesener amtlicher Seite, URL in
  `notes`. Eine fehlgeschlagene Suche ist kein Beleg — der Eintrag
  bleibt und landet im Bericht unter „unbelegt, Handprüfung". Die
  Routine vom 05.09. meldete „nächstes Fenster 09.10.2026"; die FFA
  nennt kein Datum.
- Die Routine pusht nur, wenn ihre Umgebung das Repo als Quelle trägt
  (Push 403 am 05.09.2026). Scheitert der Push, schreibt sie den
  vollständigen Diff in den Bericht. Nie mergen — ein Merge deployt.
- Externe Fakten kommen nur über Wolf (Perplexity-Briefing, nur
  Anbieter- oder Amtsseiten); der Egress-Proxy blockt jede Anbieterseite.
  Ergebnis als Tabelle mit Zitat, URL und Seitendatum, dann als
  `docs/FOERDER_VERIFIKATION_<Datum>.md` ins Repo.
- Tests: `tests/test_kis1297_foerder_frischecheck.py`. Das Sparten-Gate
  zieht den Film-Marker seither aus den Daten (`_exklusiv_passend`,
  `_exklusiv_fremd`), nicht aus einem festen Programmnamen.

## Filter löschen, was sie nicht kennen (KIS-1298)

Testlauf KIS1274 (05.09.2026): R1-Förderkapitel und KI-Rechte-Kapitel
kündigten Listen an, die nicht folgten („folgende Kategorien infrage:",
dann nichts). Ursache im Förderkapitel: Ein Filter gegen erfundene
Programme löschte jede HTML-Zeile mit „Digitalprämie" oder „Ihr
Bundesland" — seit Lauf KIS1269 in jedem Report. Die zweite Ursache
(beide Kapitel) fand erst Lauf KIS1275: der Healer-Budget-Trim, siehe
KIS-1302.

- `services/foerder_platzhalter.py` ersetzt Platzhalter (echtes Bundesland,
  „Landesprogramme zur Digitalisierung") und löscht nur noch Zeilen mit
  Fremdprogrammen (AT/CH/UK). **Regel: Ein Filter ersetzt, er löscht nie
  eine ganze Zeile wegen eines Wortes.**
- Wächter in `scripts/compare_reports.py`: „Ankündigung ohne Liste" und
  „US-Werkzeug als EU-konform" (Claude, ChatGPT, Perplexity, Runway,
  Gemini, Midjourney). Der zweite fand den Fehler rückwirkend in fünf
  Strategieberichten (KIS1264, 1267, 1269, 1270, 1274).
- Prompt-Anker statt Modellrechnung: Gesamtscore im 12-Monats-Ausblick
  (das Modell bildete den Mittelwert der Dimensionen: 77 statt 79),
  Zeitersparnis-Ziel in S6 (Stop-Regel „unter 100 Stunden" bei Ziel 25),
  Vergleichsregion und Werkzeugnamen in S2 („Wettbewerber in Bayern",
  „Adobe Sensei"), Umsatzmaßstab in S3b (Kleinstpakete bei über 10 Mio. €).
- Eine Budgetregel: Gate im Business Case nimmt das Budget aus
  Fragebogen 2, wenn es vorliegt, und nennt beide Angaben.
- Fördertabelle R1 nennt ausgesetzte Programme der eigenen Sparte in einer
  Hinweiszeile (`funding-paused-note`, Status und Wiedervorlage, kein
  Betrag). Tests, die „kein DFFF" prüfen, schneiden diese Zeile ab.
- Challenge-Banner nimmt die Tageszahl aus dem Inhalt (`CHALLENGE_DAYS`).
- Test: `tests/test_kis1298_testlauf_1274.py`.

## Der Healer kürzt, was er nicht kennt (KIS-1302)

Testlauf KIS1275 (05.09.2026, nach KIS-1298): Das R1-Förderkapitel verlor
weiter die Listen der Abschnitte 2, 3 und 5, die Überschriften 2 und 3
gleich mit, und endete mit einer Überschrift „5.". Das KI-Rechte-Kapitel
verlor 3-Schritte-Prozess und Checkliste. Lokal reproduziert mit
`report_healer.heal_report_html` (Segment `team`).

- `apply_segment_budget` (FIX-G) zählte die **deterministische
  Fördertabelle** (rund 5.000 Zeichen, vorn in `FOERDERPOTENZIAL_HTML`
  injiziert) gegen das Budget der LLM-Prosa (12.000). Strategie 2 behielt
  die ersten fünf `<li>` der **ganzen Sektion** — bei vier Listen blieb
  die erste, die anderen wurden leer. Der Clean-Ending-Check (B38a/B39)
  schnitt die verwaiste Überschrift an der ersten „Satzgrenze": „5.".
  Jetzt: Tabellen, `card-nobreak` und `funding-paused-note` werden vor
  der Messung maskiert und nie gekürzt; jede Liste behält ihre ersten
  fünf Punkte; eine Überschrift ohne Inhalt am Ende fällt ganz weg
  (`_strip_trailing_orphan_headings`).
- `KI_RECHTE_KENNZEICHNUNG_HTML` hatte kein Budget und fiel auf
  `_default` (team 5.000) — der Prompt erlaubt 450 Wörter plus zwei
  Listen. Jetzt 5.500/7.000/8.000. **Wer eine Sektion neu einhängt, trägt
  sie in `SEGMENT_BUDGETS` ein**, sonst kürzt der Default.
- Der h3-Filter in `gpt_analyze` (Reste der gestrippten LLM-Tabelle)
  traf „Fördermittel" und „Förderschwerpunkt" — die Pflicht-Überschriften
  2 und 3 aus `prompts/de/foerderpotenzial.md`. Jetzt nur noch
  Überblicks-Überschriften, nummerierte nie.
- Strategiebericht: S8 bekam keinen Faktenblock und nannte Runway
  „EU-konform"; der S4-Prompt selbst führte Claude als „EU-konforme
  Alternative". S8 hat jetzt `{kuratierte_tools}` mit Hosting-Regel; die
  Exec Summary bekommt Stärken und Handlungsfelder aus den
  Dimensions-Scores (`_r1_staerken_text`, `_r1_handlungsfelder_text`) —
  `Analysis.meta` hatte die Felder nie, und S1 schrieb „das einzige
  identifizierte Handlungsfeld: strategische Handlungsfelder". Die
  Förder-Box auf S. 4 verweist auf Kapitel 7 statt auf „regionale
  Digitalprämien" (Berlin hat keine).
- Quellenblock (`div.sources`) mit Liste wird im Enhancer zur Zeile —
  acht Werkzeugnamen untereinander füllten Strategie S. 21 allein.
- Wächter neu: „Satzabbruch vor Quartals-/Phasenblock" (R1 S. 28:
  „… Material zur Verfügung" → „Q1"). Ursache offen — der Text fehlt
  ohne Spur eines Filters; nächster Lauf zeigt, ob es wiederkommt.
  `us_werkzeug_als_eu` meldet alle Treffer (der erste verdeckte den
  echten in S8) und kennt EU-Werkzeuge sowie den Feldtrenner „·".
- Creative Europe MEDIA: Mini-Slate 2026 bis 17.09.2026, 2027-Calls am
  05.09.2026 nicht veröffentlicht (`recheck_after` 15.10.2026, Beleg in
  `docs/FOERDER_VERIFIKATION_2026-09-05.md`). Quick-Win-Prompt nennt
  Amberscript statt Otter.
- Test: `tests/test_kis1302_testlauf_1275.py`.

## Die Sparte schlägt die Branche (KIS-1313)

Testlauf KIS1282 (05.09.2026, Build 2201): erster Lauf mit dem
Verlag-Profil (KIS-1308), Score 84, Governance 87. Der Verlag-Pfad greift:
Fallstudie „Fachverlag halbiert die erste Korrekturschleife", Werkzeugblock
mit DeepL Pro, Trint, Aleph Alpha und LanguageTool, Hinweiszeile zum
pausierten Verlagspreis, Budget aus Fragebogen 2 in beiden Berichten,
Fachgebiet im Sofort-Start, Umsatzprojektionen rechnen (Preis × Menge). Was
noch die Branche statt der Sparte sah:

- **Sofort-Start:** Amberscript und DaVinci Resolve für einen Verlag (die
  Medien-Werkzeuge aus KIS-1312 waren Bewegtbild), dazu die Medien-Prompts
  Headline, Creative Brief, Skript-Outline. Jetzt `SPARTEN_TOOLS_MEDIEN`
  (Verlag: DeepL Write Pro, LanguageTool; Musik/Audio: Auphonic, iZotope RX;
  Agentur: Canva, Firefly) und `SPARTEN_PROMPTS_MEDIEN` (Verlag: erste
  Korrekturschleife, Kurzfassungen, Metadaten je Titel).
- **Starter-Kit:** Transkription, Frame.io, Media-Asset-Management. Jetzt
  `TOOL_TEMPLATES_MEDIA_SPARTE` (Verlag, Musik/Audio); die Sparte kommt aus
  `medien_sparte` im Briefing.
- **Prompt-Vorspann gekappt:** „Redaktion, Lektorat, Satz … im Haus.
  Generiere 10 Headline-Varianten" (R1 S. 7). Der Satz-Deduplizierer
  (KIS-1254) entfernt jeden Satz ab dem dritten Vorkommen — der
  Kontext-Vorspann steht mit Absicht in jedem Prompt-Kasten.
  `SOFORT_START_HTML` ist jetzt ausgenommen, der Vorspann nennt das kurze
  Fachgebiet. **Wer einen Text mit Absicht wiederholt, prüft den Cap.**
- **Recherche fragt nach Film:** Die Medien-Overrides in `live_research`
  suchten fest „KI Filmproduktion Postproduktion" — die Quellen des
  Verlag-Laufs waren Film-Artikel (Bertelsmann „Film- und TV-Produktion",
  OMR „Postproduktion"). Jetzt `{sparte}` in den drei Vorlagen, Rückfall
  „Film Postproduktion", wenn keine Sparte vorliegt.
- **Benchmark-Prozente ohne Beleg:** „ca. 35–45 % der Medienbetriebe … RTR
  2025, Bertelsmann 2025" (S2). Die Prompt-Regel (KIS-1305) hielt nicht.
  Jetzt `strategy_sanitizer.benchmark_prozent_richtwert`: Ein Prozentwert in
  S2, dessen Zahl nicht in der Recherche steht, bekommt „(Richtwert)". Dafür
  bekommt der Sanitizer die Recherche mit (`research_context`).
- **Genutzt oder empfohlen** gilt jetzt im System-Prompt für jede Section —
  S2 und S3 nannten Duden-Mentor als „im Einsatz".
- Quick Wins und KI-Systemlandschaft bekommen den Faktenblock (Claude, Notion
  und „Anthropic Claude-API" für einen Verlag mit DeepL Pro und ChatGPT).
- Kleinigkeiten: „-Entwurf" ohne „KI" (Glitch-Liste), „1 Anbieter sind
  EU-konform", S8-Risikomatrix auf vier Spalten begrenzt (sechs Spalten über
  drei Seiten), Wächter kennt die Verneinung („nicht EU-konform").
- Offen, nur beobachtet: Die 30-Tage-Challenge für Einsteiger bleibt
  generisch; Digitalbonus-Grenze und De-minimis-Schwelle kommen aus dem
  Modell; die Förder-Box auf Strategie S. 3/4 läuft auf eine dünne Seite.
- Test: `tests/test_kis1313_testlauf_1282.py`.

## Eine Siezen-Regel kennt kein Adverb (KIS-1312)

Testlauf KIS1281 (05.09.2026, Build 2126, Motion-Profil nach KIS-1311): Alles
aus KIS-1311 ist im PDF — Anwender-Pfad, Runway im Vendor-Audit, „Förderantrag
vorbereiten", Roadmap-Karten mit Trennern, EIC-Passung „niedrig", „0,5 und
2 Mio. €", kein falsches Jahr im Ausblick. Restbefunde:

- **„Prüfen Sie zueren, ob"** (R1 S. 27): Die Siezen-Regel `Sie (\w+)st` →
  `Sie \1en` hielt „zuerst" für eine Du-Form. Jetzt mit Ausnahmeliste
  (zuerst, erst, selbst, meist, fast, zunächst, Kunst, Text …). **Wer eine
  Endungsregel baut, listet die Wörter, die die Endung tragen, ohne Verb zu
  sein.**
- **„… sind als bei – siehe Roadmap für Details."** (R1 S. 29): Der
  Fragment-Reparateur ersetzt „Artikel + Adjektiv + Punkt", ließ aber die
  Präposition davor stehen. Jetzt fällt „als bei/bei/als/wie/mit" mit.
- **Sofort-Start:** „… Prozess in Medien & Kreativwirtschaft" statt des
  Fachgebiets, dazu „Microsoft Copilot + Azure OpenAI" und n8n für ein
  Motion-Studio. `_fachgebiet_kurz` (Doppelpunkt, Satz, Wortgrenze) gilt
  jetzt für alle Stufen; Medienbetriebe bekommen `TOOL_EMPFEHLUNGEN_MEDIEN`
  (Amberscript, DaVinci Resolve). Die 23-Tage-Challenge für Anwender bleibt
  generisch („E-Mail-zu-Zusammenfassung-Workflow") — eigene Medien-Fassung
  offen.
- **Kontext-Echo als Prosa** (R1 S. 23): „Typische Workflows umfassen …",
  „Ihr Unternehmen operiert als KMU mit 11–100 Mitarbeitenden, begrenztem
  CAPEX und OPEX" — der Kontextblock kam diesmal nicht als Liste, sondern als
  Vorspann. Zwei Absatzmuster in `pipeline_sanitizers`, Prompt-Regel dazu.
- **Szenario-Karten ohne Prozent** (Strategie S. 21): Das Modell schrieb
  „-18" ohne Zeichen, der Zahlen-Ersetzer greift nur mit `%`. Die Karte
  ergänzt es bei einer nackten Zahl. `.;` in den Roadmap-Karten: Punkt fällt
  vor dem Semikolon.
- **Adobe Firefly als „EU-konform"** (S3): Wächter und Prompt-Listen kannten
  nur sechs US-Namen. Jetzt auch Firefly, Descript, ElevenLabs.
- **Region der Quelle** (S2): „75 % der bayerischen Medienhäuser (RTR 2025)"
  — RTR ist die österreichische Regulierungsbehörde. Regel: Eine Quelle
  beschreibt die Region, die sie selbst nennt. Spalte „Ihr Unternehmen" nur
  aus dem Stack (dort stand Descript).
- **Umsatzprojektion** (S3b): „25.000 € im Monat bei 1–2 Jahreslizenzen zu
  20.000–40.000 €". Regel: Preis × Menge, Jahresbeträge durch zwölf.
- Offen, nur beobachtet: R1 S. 21 leer (53 Zeichen) — die Vendor-Prüfung
  mit vier Anbietern endet am Seitenende, die drei generischen
  Empfehlungs-Punkte („Zertifizierungsnachweise …") fehlen seit jeher im
  PDF, lokal sind sie im HTML. Ursache offen. Digitalbonus-Grenze „unter 50
  Mitarbeitende" kommt aus dem Modell, nicht aus den Daten.
- Test: `tests/test_kis1312_testlauf_1281.py`.

## Ein Teilwort ist kein Stichwort (KIS-1311)

Testlauf KIS1280 (05.09.2026, Build 2038): erster Lauf mit dem
Motion/Social-Profil München (KIS-1309), Score 84, Content Creation. Die
Sparten-Logik griff (Fallstudie Content Creation, Digitalbonus Bayern,
Vergleichsregion Bayern, Kennzeichnungspflicht in allen drei Reports). Die
Befunde lagen daneben:

- **Expertise-Stufe:** `expertise_detector` prüfte Stichwörter als
  Teilzeichenkette — `"rag" in "Hintergrund-Loops"` und
  `"api" in "Captions"` zählten je +3. Ein Studio mit „Erste Tools im
  Einsatz" bekam vier Seiten für Entwickler: Enterprise-LLM-Ops-Kit,
  Prompt-Engineering-Patterns, LiteLLM/Langfuse, 23-Tage-Challenge mit
  Semantic Caching. Fünf Gold-Profile waren über „rag" (Auftrag, Frage,
  Vertrag) ebenfalls „expert". Jetzt Wortgrenzen (`_enthaelt_stichwort`);
  Bindestrich und Schrägstrich bleiben Grenzen („RAG-System", „OpenAI API").
  **Wer eine Stichwortliste gegen Freitext prüft, prüft an Wortgrenzen.**
- **Starter-Kit:** Schritt 6 der KMU-Checkliste hieß fest „ZIM-Antrag
  vorbereiten" — in jedem KMU-Report, ZIM ist pausiert. Die
  KMU-Ausweichliste führte dazu „AI Act Compliance Support (BMWK,
  30.000 €)", ein Programm, das es nicht gibt. Beides ersetzt; das
  Programm kommt aus dem Förderkapitel.
- **Vendor-Audit:** `_KNOWN_VENDOR_META` kannte kein Medienwerkzeug. Der
  Kunde nutzte Runway produktiv, geprüft wurden ChatGPT und „Notion AI"
  (der Kunde hatte „Notion" genannt). Jetzt Runway, ElevenLabs, Descript,
  Firefly, Canva, Amberscript, DaVinci mit Hosting wie in `tools_seed.json`;
  Erkennung an Wortgrenzen. Der Strategiebericht bekommt die geprüften
  Namen als `{vendor_audit_tools}` — bis dahin heftete S4 den Status
  „nicht bestanden" an Runway, das nie geprüft war.
- **Genutzt oder empfohlen:** S1 schrieb dem Studio „erste Erfahrungen mit
  Canva Magic Studio" und „Nutzung von Amberscript oder DeepL Pro" zu —
  alles aus dem Faktenblock, nichts aus dem Stack. Regel in S1 (DE/EN):
  „im Einsatz" nur für `{s5_software}` und `{ki_projekte}`.
- **Roadmap-Karten:** `html_enhancer._TableParser` warf beim Umbau der
  Phasen-Tabelle (S5/S6) zu Karten jede `<li>`-Grenze weg — „… als Quick
  Win Einrichtung eines Steuerungskreises Kick-off-Kommunikation …" in
  allen Läufen seit KIS1275. Listenpunkte und `<br>` werden zu „; ".
- **Förder-Passung:** S7 gab EIC Accelerator und DIGITAL Europe für ein
  Motion-Design-Studio „hoch". Der Faktenblock trägt jetzt `notes`
  („Konsortial-Projekte", „für innovative Scale-ups"), die Prompt-Regel
  deckelt solche Programme auf „niedrig". Die R1-Tabelle zeigt beide für
  KMU weiter — Entscheidung über einen Filter offen.
- Kleinigkeiten mit Netz: „die Governance-Score" →
  `strategy_sanitizer.score_genus_korrigieren`; „zwischen 0.5 und 2 Mio. €"
  → Dezimalkomma in `GRAMMAR_FIX_PATTERNS`; Sofort-Start-Einschub endet an
  einer Satzgrenze statt bei 80 Zeichen (`_einschub_kuerzen`); der
  12-Monats-Ausblick bekommt `{{report_jahr}}` (er schrieb im September 2026
  „ob 2025 als Jahr des Einzelauftrags … in die Bücher eingeht"); S5 nennt
  keine Jahreszahl in der Quellenzeile („Investitionsplan 2024").
- Wächter `veraltete_jahreszahl` (Planungssatz mit Jahr vor dem
  Reportdatum). Offen, nur beobachtet: DeepL Pro als „Untertitel- und
  Schnittfassungs-Werkzeug" (R1 S. 13), DaVinci-Vorlagen für ein
  Premiere-Studio (Quick Win 1), Canva als „US-Anbieter" (S8; Liste sagt AU).
- Test: `tests/test_kis1311_testlauf_1280.py`.

## Testlauf KIS1279 (KIS-1307)

Build 1900 vom 05.09.2026, nach KIS-1306: Alle sieben Punkte aus KIS-1306
sind im PDF behoben, `compare_reports` meldet keinen Rückfall, keine dünnen
Seiten, Kennzahlen unverändert. Ein Restbefund ohne Ursache: R1 S. 11
„… vertraglich abgesicherte Datenhaltung ." — das Verb fehlt. Healer und
alle Enforcer lokal mit 30 Verb-Kandidaten geprüft, nichts löscht das Wort.
Wächter `wort_vor_punkt_fehlt` (Leerzeichen vor Satzpunkt) meldet das
Muster; in KIS1275 bis KIS1278 kommt es nicht vor. Beobachtung: S2 nennt
Benchmarks jetzt mit Quelle und übernimmt dabei die Region der Quelle
(„Medienhäuser in Bayern"), mit dem Zusatz „für Berlin vergleichbar" —
zulässig, aber die Vergleichsregion-Regel gilt weiter.

## Ein Abkürzungspunkt ist kein Satzende (KIS-1306)

Testlauf KIS1278 (05.09.2026, Build 1822, nach KIS-1305): Alle acht Punkte
aus KIS-1305 sind im PDF behoben. Restbefunde:

- **Fragment-Stripper:** `content_quality_enforcer.strip_trailing_sentence_fragments`
  teilte an `[.!?]\s+` — auch an „max. " und „ggf. ". Ergebnis in jedem
  Lauf seit KIS1275: „Format: Executive Summary (max." (R1 S. 8) und
  „… prüfen und ggf." im Vendor-Audit (R1 S. 21; der Rest „nachholen:
  Perplexity AI" war unter 30 Zeichen und galt als Fragment). KIS-1239
  hatte nur den FIX-G-Trim gegen Abkürzungen gesichert. Jetzt maskiert der
  Stripper Abkürzungen vor dem Split. **Wer an Satzgrenzen schneidet,
  prüft `_TRIM_ABBREVS`.**
- **Genus nach Ersetzung:** `Rollout → Einführung` (Anglizismus-Regel)
  hinterließ „Ein verfrühter Einführung", „ein verzögerter Einführung"
  (R1 S. 29). Vier Grammatik-Muster ziehen Artikel und Adjektiv nach
  (wie KIS-1230 für „Systemlandschaft").
- **S1 ohne Werkzeugregel:** „Adobe Sensei oder RunwayML" auf Strategie
  S. 5 — die Regel aus S2/S3b/S6/S8 fehlte in S1 und S3. Jetzt in beiden
  (DE/EN).
- **Abgelaufene Frist:** S7 nannte für das Medienboard „14.07.2026
  (Einreichfrist Filmförderung 2026)" und im Praxis-Tipp „Einreichfrist im
  Juli 2026" — aus der Recherche, nicht aus den Förderdaten („mehrere
  Termine/Jahr"). Prompt-Regel plus
  `strategy_sanitizer.abgelaufene_fristen_korrigieren` (nur S7, Datum vor
  Reportdatum → „Aktuell prüfen"). Wächter `abgelaufene_frist` liest das
  Reportdatum aus dem Seitenfuß.
- S8-Risikotabelle nannte Microsoft 365 Copilot „EU-konform" — Regel: kein
  Eintrag in der Liste heißt „laut Anbieter prüfen".
- Persönliche Einschätzung nannte das FB2-Budget jetzt korrekt, widmete der
  Differenz aber einen ganzen Absatz. Regel: alte Angabe gar nicht nennen,
  die Spannungs-Box hat sie schon.
- Wächter `satzabbruch_vor_block` hielt „… zwischen" / „Monat 8 und 17."
  für einen Phasenblock: Ein Blockanfang trägt Doppelpunkt, Gedankenstrich
  oder Klammer.
- Test: `tests/test_kis1306_testlauf_1278.py`.

## Eine Regel trifft auch den Produktnamen (KIS-1305)

Testlauf KIS1277 (05.09.2026, nach KIS-1304): R1 nannte „DaVinci Resolve
(Neural System)" (S. 15/16) — die Anglizismus-Regel `Engine → System` in
`content_quality_enforcer` (Grammatik- und Siezen-Fixer) kennt keine
Produktnamen. Jetzt schützt `PRODUKTNAME_ENGINE_SCHUTZ` (Lookbehind: Neural,
Unreal, Unity, Godot, Render) beide Stellen und den Solo-Blacklist-Pfad in
`report_healer`. **Wer eine Wort-Ersetzung einbaut, prüft sie gegen
`data/tools_seed.json`.**

- **Enhancer lief nie für den Strategiebericht:** `_transform_sources`
  brach ab, sobald „sources-footer" im Dokument stand — das Template trägt
  die CSS-Regel `.sources-footer`, also immer. Der `<div class="sources">`
  aus S4 blieb eine nackte Werkzeugliste (allein auf S. 21 in KIS1275,
  1276 und 1277), der `<p>Quellen: …</p>` aus S1 ein ungestylter Absatz.
  Jetzt wird nur übersprungen, was schon ein Footer ist. Der Faktenblock
  verlangt die Quellen zusätzlich als eine Zeile.
- **Budget:** Die Persönliche Einschätzung erklärte trotz Hinweis das
  FB1-Band für „maßgeblich" (R1 S. 33). Im geteilten Kontext trägt
  `investitionsbudget` jetzt selbst den FB2-Wert; die alte Angabe heißt
  `investitionsbudget_readiness_fragebogen_ueberholt`. Der Advisor-Prompt
  bekommt `{{INVESTITIONSBUDGET}}` mit Regel.
- **S1-Anker:** `_extract_top_handlungsfeld` nahm die erste `<h3>` aus S3 —
  den Sektionstitel „Strategische Handlungsfelder" („Genau hier setzt das
  Top-Handlungsfeld an: strategische Handlungsfelder", S. 3 in 1276 und
  1277). Etiketten werden übersprungen, Rückfall ist das erste abgeleitete
  Feld aus den Dimensions-Scores.
- **Verwaiste Einwort-Absätze:** Der 12-Monats-Ausblick endete mit
  „Jahresabschluss." (R1 S. 31); die Liste dazu fehlte, die Ursache blieb
  lokal nicht reproduzierbar. `_strip_trailing_orphan_headings` entfernt
  jetzt auch einen Absatz aus einem Wort am Sektionsende.
- **AI-Act-Nummer:** S8 zitierte „Verordnung 2021/0691". Die KI-Verordnung
  ist (EU) 2024/1689; `strategy_sanitizer.ai_act_verordnungsnummer_korrigieren`
  ersetzt jede andere Nummer neben „AI Act"/„KI-Verordnung".
- **Hosting `lokal` ≠ EU-gehostet:** S8 empfahl „EU-gehostete Tools wie
  Amberscript … und DaVinci Resolve". Regel in S4, S8 und Faktenblock:
  „lokal installiert". Wächter `lokal_als_eu_gehostet`.
- **Benchmarks in S2:** „Über 75 %", „Nahezu 96 %" (der BDZV-Wert aus
  KIS-1294) ohne Quelle, Spalte „Ihr Unternehmen 0 %" bei einem Kunden mit
  ChatGPT, Claude und Perplexity im Stack. S2 bekommt `{s5_software}` und
  `{s8_erfahrung}`; jeder Prozentwert nennt seine Quelle in der Zeile,
  sonst Einordnung in Worten als Richtwert.
- Wächter neu: `ai_act_verordnungsnummer`, `lokal_als_eu_gehostet`,
  `einwort_absatz_am_kapitelende`. Test: `tests/test_kis1305_testlauf_1277.py`.

## Der Replay kennt keine Fragebogen-2-Route (KIS-1304)

Testlauf KIS1276 (05.09.2026): Die [KIS-Admin]-Briefing-Mail (FB1+FB2)
kam trotz KIS-1303 nicht. Testläufe sind Replays
(`/api/admin/testrun/replay`): Der Replay kopiert Fragebogen 2 **vor**
Report 1, und `_auto_trigger_strategy_replay` startet den Strategiebericht
direkt — Fragebogen-2-Route (KIS-1299/1303) und Chat-Abschluss, die beide
die Mail schicken, laufen dabei nie. Jetzt schickt der Replay-Trigger die
Mail selbst, und die R1-Admin-Mail hängt das Briefing mit FB2 an, sobald
FB2 vorliegt. **Wer einen Weg baut, der Fragebogen 2 speichert, schickt
die Mail** — es gibt drei Wege, keinen gemeinsamen Haken.

- **Budget:** Fragebogen 2 hat Vorrang (`_budget_effektiv`). Prompts und
  geteilter Kontext sahen nur FB1, weil Underscore-Schlüssel ausgeblendet
  sind; der Business Case nannte deshalb „Budgetrahmen 2.000–10.000 €".
  Der Werkzeug-Filter (`tools_recommender`) nahm ebenfalls FB1 und warf
  Amberscript, Descript und Runway hinaus — übrig blieben Canva und Duden
  für ein VFX-Studio. Werkzeuge der eigenen Sparte fallen nie am Budget.
- **Kontextblock-Echo:** Der Prompt-Enhancer legt Branchen- und
  Größenkontext als HTML-Listen in den Prompt; das KI-Rechte-Kapitel gab
  sie aus. `strip_context_block_leaks` (FIX-C1) nahm nur die Labels, die
  Listen blieben (R1 S. 23 in KIS1275 und KIS1276). Jetzt fallen Label
  und Liste zusammen, und im KI-Rechte-Kapitel alles vor `<section>`.
- Quellenliste aus reinen Links wird im Enhancer zur Zeile (Strategie
  S. 19/20 und 34/35 waren fast leer). Kapitel-Etiketten
  („Strategische Handlungsfelder") sind keine Handlungsfelder für S1.
- Wächter: „nicht unter die Hochrisiko-Systeme" ist kein Befund; eine
  Liste nach dem Seitenfuß auch nicht.
- Seed: DaVinci Resolve (Neural Engine) mit Hosting `lokal`, ohne
  Prüfdatum — der Report empfahl es aus dem Branchenkontext, die
  Faktenliste kannte es nicht.
- Test: `tests/test_kis1304_testlauf_1276.py`.

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
  zehn behobenen Fehler. Exit-Code 1 bei einem Rückfall. Seit
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

- `POST /api/admin/testrun/profile` (KIS-1308) — legt aus einem Profil im
  Format der Gold-Profile (`answers` + `strategy_answers`) ein neues
  Briefing samt Fragebogen 2 an und stellt es in die Warteschlange; der
  Strategiebericht startet wie beim Replay automatisch
  (`source='admin_profile'`). Prüfung vorab: Pflichtfelder, Enum-Werte,
  Bundesland-Code, FB2-Regeln. Aufruf über das Skript:

  ```bash
  cd ~/api-ki-backend-neu && git pull
  export STRATEGY_ADMIN_KEY=…
  python3 scripts/testlauf_profil.py data/test_profiles_gold/medien_verlag_bayern_kmu_testlauf.json --email wolf@hohl.rocks
  ```

  `--check` prüft nur. Das Skript braucht nur die Standardbibliothek
  (KIS-1310): Die Prüfung liegt in `services/profil_pruefung.py`, ohne
  FastAPI und ohne App-Settings; der Endpunkt re-exportiert sie. Fehlt
  FastAPI lokal, prüft der Endpunkt Fragebogen 2 selbst — das Skript sagt
  das. Der erste Lauf auf dem Mac scheiterte an `routes.admin_testrun`
  (`No module named 'fastapi'`); Test:
  `tests/test_kis1310_skript_ohne_backend.py` startet das Skript mit
  `python3 -I -S`. Zwei Profile: `medien_verlag_bayern_kmu_testlauf`
  (Fachverlag, Bayern, 11–100 Mitarbeitende, FB2-Budget über FB1) und
  `medien_motion_social_muenchen_testlauf` (Motion-Design/Social-Media,
  München, Content Creation) — beide außerhalb des Post/VFX-Pfads der
  Läufe KIS1272–1279.
- `POST /api/strategy/admin/briefing-mail/{briefing_id}` (KIS-1299) —
  schickt das Briefing-PDF mit Fragebogen 1 und 2 an
  bewertung@ki-sicherheit.jetzt. Admin-Key per Header `X-Admin-Key`.
  Das ist der Weg zu den Rohantworten eines Laufs: Der
  Admin-JSON-Endpunkt ist in Produktion aus (`ENABLE_ADMIN_ROUTES=0`).
  Der Formular-Pfad schickt diese Mail seit KIS-1299 selbst nach Abgabe
  des Strategie-Fragebogens; der Betreff nennt „FB1+FB2" oder „nur FB1".
  **KIS-1303:** Als BackgroundTask kam sie in Lauf KIS1275 nie an (keine
  Spur im Postfach, Admin-Endpunkt lieferte). Jetzt synchron im Request
  über `asyncio.to_thread` — derselbe Weg wie Chat-Pfad und
  Admin-Endpunkt. Bleibt sie aus, in den Railway-Logs nach
  `ADMIN-BRIEFING-<id>` und `KIS-1303` suchen.

  ```bash
  curl -X POST -H 'X-Admin-Key: $STRATEGY_ADMIN_KEY' \
    'https://api-ki-backend-neu-production.up.railway.app/api/strategy/admin/briefing-mail/1157'
  ```

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
