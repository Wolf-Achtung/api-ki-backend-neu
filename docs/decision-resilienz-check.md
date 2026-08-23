# Entscheidung: KI-Resilienz-Check — eigenständig oder integriert?

Stand: 2026-08-23 · Status: **Entwurf, wartet auf Wolfs Entscheidung** · Keine Implementierung vor Freigabe.
Fachliche Referenz: `resilienz-check-modul.md` (21 Fragen, 6 Blöcke, Min-/Deckelregel — wird nicht umgestaltet).

---

## 1. Diagnose-Zusammenfassung

**Fragebogen-Architektur.** Es gibt keine Fragebogen-Engine. Der r1-Fragebogen (53 Felder, 8 Blöcke) lebt als JS-Array im Frontend (`formbuilder_de_SINGLE_FULL.js:388-688`) mit Backend-Spiegel für den Chat (`services/chat_normalizer.py:137-272`). Strategy (14 Felder) ist ein eigener One-Pager (`strategy.html`) mit eigener Tabelle (`models.py:326`). Jede Typ-Unterscheidung ist ein hartes `if report_type == "strategy" … else r1` — an rund 40 Stellen, r1 ist überall der stille Default. Warnender Präzedenzfall: Der Typ `kpa` steht im Literal (`schemas/chat.py:122`), hat aber keine Registry — er degradiert still zu r1 statt zu scheitern.

**Scoring.** Durchgehend deterministisch und fest im Code. Der Readiness-Score ist ein **ungewichtetes** Mittel aus 4 Blöcken (`gpt_analyze.py:2038`). Die drei Mechaniken des Resilienz-Moduls existieren nirgends: keine Blockgewichtung, keine Min-Regel auf Antwortebene, keine Deckelregel „Gesamt ≤ schwächster Block". Strukturell nächster Verwandter: `services/appetizer_score.py` — kleines, isoliertes, deterministisches Modul mit Bändern und Caps. Genau so wird das Resilienz-Scoring gebaut, unabhängig von der Variante.

**Report-Pipeline.** Eine neue Sektion im r1-Report kostet 6 Pflicht- plus 7 Qualitäts-Integrationsstellen und zwei Templates (DE+EN). Ein neuer Report-Typ nach Strategy-Blaupause kostet ~4.900 Zeilen Python, 2 Tabellen, 2 Templates. Es gibt aber eine **billigere Blaupause: die Potenzialanalyse (KPA)** — vollwertiger dritter Report mit 1 Service (1.319 Zeilen), 4 Prompt-Dateien, 2 Templates, ohne eigene Tabelle, ohne eigenen Worker (läuft als Hintergrund-Thread nach r1, `gpt_analyze.py:24113`). PDF-Weg (`services/pdf_client.py` → pdfservice), Footer, Display-ID, Coverage-Audit, Branchen-Labels und Modell-Routing sind für alle Reports wiederverwendbar.

**Funnel & Daten.** Ein neuer Fragebogen braucht **keine Schema-Migration**, wenn die Antworten als JSON-Keys in `briefings.answers` landen (r1-Muster, `models.py:62`). Aber: `Briefing` hat kein Typ-Feld, und der Worker zieht **alle** offenen Briefings durch die r1-Pipeline (`workers/briefings_worker.py:186-226`) — ein neuer Typ braucht zwingend eine Typ-Spalte oder muss den Worker umgehen (In-Process wie Strategy/KPA). Neue Frontend-Seite = neue HTML-Datei, kein Routing nötig; neue Analytics-Events müssen in die Allowlist (`routes/metrics.py:36-45`). Der Login ist derzeit Whitelist-beschränkt (`routes/auth.py:180-185`, geschlossene Testphase).

**Alt-Bestände zum Thema.** Kein Resilienz-Fragebogen-Vorläufer im Code. NIS2 existiert nur als Kontextwissen (`services/research_agents/regulatory_agent.py:56`, `services/expert_agents/governance_advisor_agent.py:219`, `services/branch_profile_engine.py:273`). `services/governance_engine.py:235-372` enthält ein totes gewichtetes Reifegrad-Scoring (importiert, nie aufgerufen) — dessen Gewichte passen nicht zum Modul-Dokument; nicht wiederbeleben. Die `security-*`-Branches sind alte Audit-Sessions, kein Produktcode.

---

## 2. Variantenvergleich

| Kriterium | V1: Eigenständig | V2: Integration in r1 | V3: Hybrid (5 Signalfragen + Voll-Check) |
|---|---|---|---|
| **Aufwand** | **9–12 PT**: Scoring-Modul 1, Typ-Spalte + Submit 1–2, Report-Pipeline nach KPA-Blaupause 3–4, Frontend-One-Pager 2, Mail/Metrics/QA 1, Tests 1–2 | **15–20 PT**: 21 Felder in Formular DE+EN, Chat-Block-Struktur (`routes/chat.py:455-499`), Extractor-Tool, QR-Optionen, 2–3 neue r1-Sektionen à 6–13 Stellen, Template-Arbeit ×2 Sprachen | **V1 + 4–6 PT**: zusätzlich 5 Felder in Formular+Chat, 1 neue r1-Sektion „Resilienz-Schnellbild", Cross-Sell-Link im PDF |
| **Prompt-Risiko** | **Null.** Kein bestehender Prompt wird angefasst; nur neue Prompt-Dateien | **Hoch.** 21 neue Antwort-Keys fließen in `_build_prompt_vars` (`gpt_analyze.py:9331`) und damit in den Kontext aller 37 r1-Sektionen. Die in 4 Testzyklen (Läufe 1138–1141) stabilisierte Report-Qualität steht neu zur Prüfung; Regressionstest = kompletter Vorher/Nachher-Vergleichslauf | **Klein, aber real.** 5 neue Keys im r1-Kontext + 1 neue Sektion; Vergleichslauf nötig |
| **Fragebogen-Länge / UX** | 21 Fragen, 10–12 min, in sich geschlossen | r1: 53 → 74 Felder. Heute schon ~15–20 min; +40 % Länge = hohes Abbruchrisiko am längsten Punkt des Funnels | r1: 53 → 58 Felder (+9 %), vertretbar; Voll-Check separat |
| **Funnel-Logik** | **Zweiter, unabhängiger Einstiegspunkt** mit eigener Kernzahl („Reaktionslücke") — exakt die Stufe 0 aus dem Konzeptpapier | Kein neuer Einstiegspunkt. Ein längerer Gesamtcheck verwässert beide Produkte; Zielgruppen-Mismatch (r1: KI-Nutzung; Resilienz: Abwehrfähigkeit) | Zwei Einstiegspunkte + Cross-Sell im r1-PDF — stärkster Funnel, aber erst sinnvoll, wenn der Voll-Check existiert |
| **Wartbarkeit / Versionierung** | Isoliertes Modul; Änderungen am Resilienz-Katalog berühren r1 nie | Jede Katalog-Änderung ist eine r1-Änderung: Formular-Schema-Bump, Chat-Registry, Prompts — mit r1-Regressionstest | Voll-Check isoliert; die 5 Signalfragen hängen dauerhaft in r1 mit dessen Pflegezyklus |
| **Wiederverwendung** | pdf_client, Footer, Display-ID, Coverage-Guard, Labels, Mail-Versand, Status-Seite; Scoring neu (muss ohnehin neu) | dieselben Bausteine, zusätzlich r1-Template-Slots | wie V1, plus r1-Sektionsmechanik für das Schnellbild |

---

## 3. Empfehlung: Variante 1 — eigenständiger Resilienz-Check

Begründung in vier Punkten:

1. **Null Risiko fürs laufende Geschäft.** V2 legt 21 neue Antwort-Keys in den Kontext von 37 mühsam stabilisierten Report-Sektionen. Der einzige Weg, das abzusichern, sind vollständige Vergleichsläufe — wiederkehrend bei jeder Katalog-Pflege. V1 fasst keinen bestehenden Prompt an.
2. **Das Konzeptpapier verlangt einen eigenen Lead-Magneten.** Die „Reaktionslücke" ist als verkaufende Diagnose konzipiert (Stufe 0 der Produkttreppe) — als Block 9 eines langen Readiness-Fragebogens verliert sie genau diese Funktion. Zielgruppe (Geschäftsführung, Sicherheitslage) und Dramaturgie (eine Zahl auf Seite 1) sind ein eigenes Produkt.
3. **Die Codebase belohnt V1.** Die KPA-Blaupause zeigt: ein dritter Report ohne eigene Tabelle, ohne Worker-Umbau, mit 4–6 Prompt-Dateien ist der etablierte günstige Weg. Der Scoring-Kern (Gewichte, Min-Regel, Deckelregel) ist in jeder Variante ein Neubau — er kostet in V1 nichts extra.
4. **V3 ist kein Konkurrent, sondern der zweite Schritt.** Die 5 Signalfragen im r1 lohnen erst, wenn der Voll-Check existiert und erste echte Checks die Stufen-zu-Zeit-Kalibrierung bestätigt haben (Modul-Dokument, Teil 4.3). Empfehlung: V1 jetzt bauen, die Signalfragen-Erweiterung nach den ersten ~20 Checks als eigenes, kleines Vorhaben entscheiden.

**Architektur-Eckpunkte der Empfehlung** (nach KPA-Muster, aber mit eigenem Fragebogen):

- Antworten als JSON-Keys in `briefings.answers`, neue Spalte `briefings.report_type` (Default `'r1'`, Migration nach Muster `migrations/2026-03-09_*`), Worker-Claim filtert auf `r1` — der Resilienz-Report läuft in-process via `BackgroundTasks` (Strategy-Muster), weil er klein ist.
- Report überwiegend **deterministisch**: Score, Reaktionslücken-Band, Ampel, Quick Wins und Ausbaustufen kommen 1:1 aus dem Modul-Dokument als Daten (`data/resilienz/…`). Nur 2 LLM-Sektionen (individualisierte Kernaussage + Blockbefunde, claude-sonnet-5). Zeitstrahl und Spinnendiagramm als inline-SVG — **keine neuen Dependencies**.
- Frontend als One-Pager `resilienz.html` nach `strategy.html`-Muster (21 Fragen sind dafür die richtige Größe; der 74-Felder-Formbuilder ist das falsche Werkzeug).
- Kein Chat-Modus im MVP — spart die ~40 Chat-Touchpoints (`routes/chat.py`, Extractor, QR-Kataloge). Nachrüstbar.
- Sprachregelung hart im Prompt und Template verankert: „Entscheidungsfähigkeit, Vorbereitung, Selbstauskunft" — nie „Sicherheit/Schutz" zusichern; Pflichtformulierung „geschätzte Reaktionslücke auf Basis Ihrer Angaben" wörtlich; CI-Test darauf.

## 4. Umsetzungsplan (V1, ein Schritt = ein Commit)

**Migration**
1. `migrations/2026-08-XX_add_briefing_report_type_{postgres,sqlite}.sql` + `models.py`: Spalte `briefings.report_type` (String(20), Default `'r1'`); Worker-Claim (`workers/briefings_worker.py:204`) filtert `report_type='r1'`. Test: bestehende r1-Läufe unverändert (Worker-Testsuite), Resilienz-Briefing wird nicht vom Worker gezogen.

**Fachkern (ohne LLM)**
2. `data/resilienz/katalog_de.json`: 21 Fragen, 6 Blöcke, Gewichte, Stufen — wörtlich aus dem Modul-Dokument übernommen, inkl. `derived`-Regeln. Test: Struktur-Validierung.
3. `services/resilienz_score.py`: gewichteter Score, Reaktionslücke `min(B2,C1,C2,C3,C4)` → 4 Bänder, Deckelregel `ampel = min(block_means)`. Goldene Tests: alle-1, alle-4, Min-Regel schlägt Durchschnitt, Deckelregel (D=4/C=1 → Rot), Bandgrenzen.
4. `services/resilienz_recommender.py`: Quick Win + Ausbaustufe je schwächstem Block (Empfehlungs-Bibliothek als Daten). Test: pro Blockschwäche genau ein Quick Win.

**Backend-Route + Auslieferung**
5. `routes/resilienz.py`: `POST /resilienz/submit` (validiertes Pydantic-Modell — anders als r1: Enum-geprüfte Stufen 1–4), `GET /resilienz/status/{id}`, `GET /resilienz/pdf/{id}`; Generierung via `BackgroundTasks`. Kein Firmennamen-Feld (Invariante, Test wie `tests/test_wartung_2026_08_appetizer.py`).
6. `services/resilienz_pipeline.py` + `templates/resilienz_report.html`: deterministischer Renderer (Seite 1 Zeitstrahl-SVG, Seite 2 Score + Spinnendiagramm-SVG + Deckelregel-Erklärung, Blockbefunde, Pflichtenlage, Montags-Seite) + Mail-Versand über bestehenden Resend-Pfad. Test: Golden-HTML gegen fixe Antworten; Haftungs-Sprachregeln als Assertion (verbotene Wörter „garantiert sicher", „Schutz vor").

**Prompts (nur NEUE Dateien — kein bestehender Prompt wird verändert)**
7. `prompts/de/resilienz_kernaussage.md` + `prompts/de/resilienz_befunde.md` + Manifest-Einträge. Was ergänzt wird: 2 neue Dateien. Was unverändert bleibt: alle 59 bestehenden DE-Prompts, alle EN-Prompts, `prompt_map`, r1-Sektionsliste. Prüfung der Unverändertheit: `git diff --stat` des PR zeigt null Änderungen unter `prompts/` außer den 2 neuen Dateien + Manifest; zusätzlich ein r1-Vergleichslauf mit dem Medien-Testprofil vor/nach Merge (identische Testantworten, PDF-Diff der Sektionsstruktur).

**Frontend**
8. `make-ki-frontend/resilienz.html`: One-Pager nach `strategy.html`-Muster, 6 Blöcke, localStorage-Autosave, Submit auf `/resilienz/submit`, danach bestehende Status-Poll-Mechanik.
9. `routes/metrics.py:36-45`: Events `resilienz_started`, `resilienz_completed` in die Allowlist; CTA auf der Startseite (hinter Login wie alles in der Testphase).

**Abschluss**
10. End-to-End-Testlauf mit einem Medien-Profil, PDF-Review durch Wolf, dann erst Launch-Entscheidung.

Reihenfolge-Logik: Schritte 2–4 sind rein lokal testbar und ohne Deploy-Risiko; 1 und 5 berühren die Produktion und werden nur ohne aktiven Testlauf gemergt.

## 5. Offene Fragen an Wolf

1. **Sprache zum Start:** Nur Deutsch (Empfehlung — halbiert Formular-, Template- und Prompt-Arbeit; EN nachziehbar wie bei r1) oder direkt DE+EN?
2. **Zugang:** Bleibt der Resilienz-Check hinter der Login-Whitelist (wie alles in der Testphase), oder soll er als Lead-Magnet von Anfang an einen eigenen, offenen Zugang bekommen? (Offener Zugang = eigene Rate-Limits + Missbrauchsschutz, +1–2 PT.)
3. **Kernzahl-Beleg:** Die „15-Minuten"-Benchmark braucht vor Launch eine zitierfähige öffentliche Quelle (Modul-Dokument Teil 4.2). Soll ich das als eigenen Recherche-Task übernehmen?
4. **Extern zu klären (blockiert den Bau nicht, aber den Launch):** Markenprüfung „Reaktionslücke", anwaltliche Prüfung von Haftungsausschluss und NIS2-Aussagen (Modul-Dokument Teil 4.1/4.4).

---

## Anhang: Neben-Befunde der Diagnose (unabhängig von dieser Entscheidung)

Bei der Analyse gefunden, hier nur dokumentiert — keine Aktion ohne separates Go:

1. `README.md:19-20` und `docs/OPERATOR_GUIDE.md:47-50` beschreiben `alembic upgrade head`; Alembic existiert im Repo nicht (real: `core/migrate.py` + `migrations/*.sql`).
2. `core/migrate.py` und `models.py` beschreiben teils dieselben Tabellen unterschiedlich (`login_codes.code_hash` vs. `code`; `analyses.analysis_data` vs. `meta`); `appetizer_leads`, `login_audit` haben kein ORM-Modell.
3. `migrations/2026-03-09_add_strategy_tables_postgres.sql:4` sagt „DO NOT auto-apply", wird aber bei jedem App-Start automatisch angewandt (`core/migrate.py:245-255`).
4. `services/report_renderer.py:662` zeigt als DE-Template-Default auf eine nicht existierende Datei — Produktion hängt an der Railway-ENV `REPORT_TEMPLATE_PATH_DE`.
5. Chat-Weg Strategy: `s5_vision` fehlt im Upsert-Dict (`routes/chat.py:3918-3932`) — per Chat erhoben, wird es nicht gespeichert (Formular-Weg ist korrekt).
6. `formular/prefill.js:15-17` erwartet ein Response-Format, das `GET /briefings/{id}` nicht liefert — Prefill greift nie.
7. `templates/partials/` + `services/static_content.py`: kompletter Anhang-Mechanismus ohne Aufrufer (`APPENDIX_ENABLE` wirkungslos).
8. Prompt-Manifest deckt nur 43/53 DE- bzw. 53/63 EN-Prompts — 10 Engine-Prompts pro Sprache wären bei `RELEASE_STRICT_MODE=1` nicht ladbar.
9. Score-Berechnung dreifach dupliziert (`gpt_analyze.py`, `strategy_pipeline.py:113-165`, `strategy_renderer.py:213-260`) inkl. als „temporär" markierter Debug-Zeilen.
10. Die zwei r1-PDF-Render-Pfade (Worker `gpt_analyze.py:24420` vs. API `24564`) sind fast identisch dupliziert; nur der Worker-Pfad hat den Thin-Page-Check.
