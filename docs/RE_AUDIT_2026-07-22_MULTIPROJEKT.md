# Re-Audit 2026-07-22: Multi-Projekt-Fähigkeit der Pipeline

**Fragestellung:** Wie kann die bestehende Pipeline (Fragebogen → GPT-Analyse → Report → PDF)
für andere Projekte nutzbar gemacht werden — für Privatpersonen ebenso wie für Unternehmen
aus Film-, Medien- und Entertainment-Sektoren?

**Umfang:** Frischer Audit über alle drei Repos auf aktuellem Stand (`main` vom 2026-07-22):
`api-ki-backend-neu`, `make-ki-frontend`, `make-ki-pdfservice`.

---

## 1. Executive Summary

Die Pipeline ist **näher an Multi-Projekt-Fähigkeit als erwartet** — aber die Distanz ist je
Schicht sehr unterschiedlich:

| Schicht | White-Label-Reife | Kernbefund |
|---|---|---|
| **PDF-Service** | ~90 % | Rein generischer HTML→PDF-Renderer, keinerlei Templates/Branding im Service. Sofort für zweites Projekt nutzbar. |
| **Backend-Infrastruktur** | ~70 % | Prompt-Loader (dateibasiert + Manifest + ENV), Modell-Routing, Feature-Flags, i18n, Worker-Queue, Research-Provider-Abstraktion sind domänenneutral. |
| **Backend-Inhalte/Logik** | ~40 % | Scoring-Modell, System-Prompt-Persona, Research-Queries, Förderdaten, Wissensbasen sind hart auf „KMU/DACH/KI-Governance" verdrahtet. |
| **Frontend** | ~30 % | Fragebogen als hardcodiertes JS-Array (2 Sprachdubletten), Branding über ~15 Dateien verstreut, Backend-URL an ~15 Stellen. |
| **Datenmodell** | 0 % | Kein Tenant-/Produkt-Konzept: `Briefing`/`Report`/`User` kennen keine Produktvariante. |

**Die zwei wichtigsten strategischen Erkenntnisse:**

1. **Film/Medien/Entertainment ist keine neue Welt, sondern eine fast fertige Vertikale.**
   Die Branche `medien` („Medien & Kreativwirtschaft", inkl. Film/TV-Produktion) existiert
   bereits vollständig als Branchenkontext (`data/branch_contexts/medien.json`,
   EN: `creative_media.json`), mit Mapping, Benchmark und Größenlogik. Es fehlen im
   Wesentlichen: Entkopplung des Brandings, medienspezifische Tool-Daten und eine
   inhaltliche Vertiefung (Produktion/Post/VFX/Rechte). **~70–80 % wiederverwendbar.**

2. **„Privatpersonen" ist keine neue Branche, sondern eine neue Produktlinie auf derselben
   Engine.** Die gesamte Größen-Ontologie (`solo`/`team`/`kmu` = Firmen mit Umsatz),
   Förder-Sektionen, Business-Case/ROI und das 4-Dimensionen-Governance-Scoring setzen
   ein Unternehmen voraus. Engine, Renderer, Qualitäts-Gates und i18n sind wiederverwendbar;
   Sektions-Inhalte und Datenmodelle der Zielgruppe müssen neu entstehen.

**Empfohlener Weg:** Kein Fork je Projekt, sondern Umbau zu einer **konfigurationsgetriebenen
Produkt-Plattform** („Vertical Packs"): ein Engine-Kern + pro Produkt ein Konfigurationspaket
(Fragebogen-Schema, Prompt-Ordner, Scoring-Schema, Branding, Content-Daten, Feature-Flags).

---

## 2. Ist-Stand im Detail (Befunde je Repo)

### 2.1 Backend `api-ki-backend-neu`

**Bereits generisch / wiederverwendbar:**

- **Prompt-System:** `services/prompt_loader.py` lädt Sektionen aus `prompts/<lang>/*.md`
  über `prompts/prompt_manifest.json`; Basis-Verzeichnis via ENV `PROMPTS_BASE_DIR`,
  Jinja2-Includes mit Allowlist. → Eine neue Domäne = eigener Prompt-Ordner + Manifest,
  ohne Code-Änderung.
- **Modell-Routing & Flags:** `OPENAI_MODEL_FAST/REASONING/FALLBACK`, Feature-Flags
  (`enable_ai_act_section`, `enable_perplexity`, `enable_quality_gates`, …) in `settings.py`.
- **Research-Provider abstrahiert** (`RESEARCH_PROVIDER` tavily/perplexity/hybrid).
- **Briefing-Antworten als loses JSON** (`models.py:62`) — kein starres Schema erzwungen.
- **PDF-Client** (`services/pdf_client.py`) — reiner HTTP-Adapter, domänenneutral.
- **i18n:** EN als Erstklasse-Sprache (paralleler Prompt-/Content-Baum), UI-Labels 5-sprachig.
- **Multi-Report-Ansatz vorhanden:** `ChatSession.report_type` (r1/…), Strategie-Report-Tabellen.

**Harte Kopplungspunkte (mit Aufwand):**

| # | Kopplungspunkt | Fundstelle | Aufwand |
|---|---|---|---|
| K1 | System-Prompt-Persona „Senior-Strategieberater für KI-Einführung bei KMU im DACH-Raum" — geht in *jeden* LLM-Call | `services/report_system_prompt.py:22` | S |
| K2 | Scoring-Modell: 4 fixe Dimensionen (Governance/Security/Value/Enablement) mit hartkodierten Feldnamen und Gewichten | `gpt_analyze.py:1956–2194` | XL |
| K3 | Freitext-Keyword-Bonus (deutsches KI-Governance-Vokabular) | `gpt_analyze.py:2198–2258` | M |
| K4 | Branchen-Mapping: 13 DACH-Branchen fest; „medien" wird teils auf „marketing"-Profil gemappt | `services/branch_mapping.py:53–210` | L |
| K5 | Branding in Templates: Logo, „Wolf Hohl · TÜV-zertifizierter KI-Manager", Kontakt/Impressum — ~33 Stellen in 3 Templates + `advisor_note.md` + `transparency_box.md` + `email_templates.py` | `templates/pdf_template_v7.html:1333,2097,2129ff` u. a. | M |
| K6 | Live-Research-Queries fix auf DACH/KMU/Förderung | `services/live_research.py:35–88`, `services/news_researcher.py:29–49` | M |
| K7 | Förderdaten DACH (Firmen-Zuschüsse) + Funding-Blacklist im Enforcer | `data/funding/*`, `b25_enforcer.py:322–398` | M |
| K8 | Wissensbasen KMU/KI-Governance, statisch injiziert (kein RAG), Sektion→KB-Map fix | `knowledge/*`, `services/kb_loader.py:127–164` | L |
| K9 | Größen-Ontologie nur solo/team/kmu (= Firmen); kein Adressat „Privatperson" | `data/size_contexts/*.json`, `prompts/de/_persona_guardrails.md` | M–L |
| K10 | Kein Tenant-/Produkt-Feld im Datenmodell (`Briefing`, `Report`, `User`) | `models.py` | L |

(Aufwand: S ≈ 1 PT · M ≈ 2–4 PT · L ≈ 1–2 PW · XL > 2 PW)

**Größtes strukturelles Risiko:** `gpt_analyze.py` (23.285 Zeilen). Scoring, Prompt-Var-Aufbau,
Fallbacks und Freitext-Bonus sind dort mit den KMU-Feldnamen verwoben. Solange dieses Modul
nicht in „domänen-agnostische Engine + austauschbare Domänen-Konfiguration" zerlegt ist,
bleibt jede neue Zielgruppe ein Fork statt eine Konfiguration.

### 2.2 Frontend `make-ki-frontend`

Statisches HTML/Vanilla-JS ohne Build-System, Netlify-Deployment; Auth- und Status-Flow
sind bereits projektneutral. Drei Hauptblocker:

1. **Fragebogen hardcodiert:** `formular/formbuilder_de_SINGLE_FULL.js` (~50 Felder, 8 Blöcke,
   inkl. `showIf`-Funktionen) + manuell synchron gehaltene EN-Dublette. Blöcke wie
   „Rechtliches & Compliance" und „Förderung & Investition" sind domänenspezifisch.
   Dazu 120 KB Branchen-Beispieltexte (`field_examples_de.js`).
2. **Branding verstreut:** Name, Domain, Logos (TÜV, KI-READY-Badge), Testimonials,
   Impressum in praktisch jeder HTML-Datei; keine zentrale Branding-Config.
   Lichtblick: `styles.css` hat CSS-Custom-Properties (`--mk-*`) als Theming-Grundlage —
   der Formbuilder injiziert allerdings eigene Styles mit festen Hex-Werten daran vorbei.
3. **Backend-URL an ~15 Stellen** hartkodiert (Meta-Tags, JS-Fallbacks, CSP in `netlify.toml`),
   obwohl der Mechanismus (`meta[api-base]` → `window.APP_CONFIG.API_BASE`) sauber ist.

### 2.3 PDF-Service `make-ki-pdfservice`

Bereits heute ein generischer, zustandsloser HTML→PDF-Renderer (Express + Puppeteer):
Input ist fertiges HTML inkl. Design; keine Templates/Fonts/Logos im Service. **Ein zweites
Projekt mit anderem Design ist ohne Code-Änderung möglich**, solange das aufrufende Backend
sein eigenes gebrandetes HTML schickt (Fonts als `@font-face`/Data-URI). Für sauberen
Parallelbetrieb fehlen nur Betriebsthemen: ein Key pro Mandant statt einem globalen
`PDF_SHARED_SECRET`, Rate-Limit/Metriken pro Mandant, Font-Strategie. Alternativ: pro Projekt
eine eigene Instanz (gleicher Code, eigene ENV) — dank Zustandslosigkeit trivial.

---

## 3. Zielbild: Konfigurationsgetriebene Produkt-Plattform („Vertical Packs")

Ein Produkt/Projekt = ein **Konfigurationspaket**, das die generische Engine bespielt:

```
products/
  ki-readiness-kmu/          ← heutiges Produkt, als erstes Pack extrahiert
    product.json             ← Metadaten, Feature-Flags (funding: on, ai_act: on, …)
    questionnaire.de.json    ← Fragebogen-Schema (Felder, Blöcke, showIf deklarativ)
    questionnaire.en.json
    scoring.json             ← Dimensionen, Feld-Gewichte, Kalibrierung, Badge-Schwellen
    prompts/de|en/*.md       ← Sektions-Prompts + Manifest (Loader existiert bereits!)
    persona.md               ← System-Prompt-Persona (statt report_system_prompt.py)
    brand.json               ← Name, Logo-Pfade, Berater-Signatur, Kontakt, Impressum, Farben
    content/                 ← Branchenkontexte, Benchmarks, Tools, Wissensbasen, (Förderdaten)
    research.json            ← Query-Templates für Live-Recherche je Sektion
  ki-kompass-privat/         ← neue Produktlinie Privatpersonen
  ki-check-film-medien/      ← Vertikale Film/Medien/Entertainment
```

**Technische Bausteine dafür (Backend):**

1. `product`-Spalte auf `Briefing`/`Report` (+ Migration) und ein `ProductConfig`-Resolver,
   der pro Request das Pack lädt (K10).
2. `build_report_system_prompt(product)` statt fixer Konstante (K1).
3. Scoring-Engine datengetrieben: Dimensionen/Felder/Gewichte/Caps aus `scoring.json` (K2) —
   der größte Einzelposten, aber der Schlüssel, damit neue Produkte kein Fork sind.
4. Branding-Variablen in den Jinja2-Templates (Logo, Signatur, Kontakt, Farben aus
   `brand.json`) statt hardcodierter Blöcke (K5).
5. Research-Query-Templates und Sektion→KB-Zuordnung aus dem Pack (K6, K8).
6. Förder-/AI-Act-/Business-Case-Sektionen per Pack-Flag zu- und abschaltbar (K7).

**Frontend:** Generischer Kern (Form-Renderer + Auth + Status-Polling) + pro Produkt ein
Config-Ordner (`questionnaire.json`, `brand.json`, `theme.css`, Content, API-Base). Der
Fragebogen wandert von JS-Code in Schema-JSON; `showIf` wird deklarativ (`{field, op, value}`);
Labels bekommen Sprach-Keys statt Dateidubletten.

**PDF-Service:** unverändert nutzen; bei mehreren Marken Keys→Tenant-Map + per-Tenant-Limits,
oder je Projekt eine eigene Instanz.

---

## 4. Produktideen für die neuen Zielgruppen

### 4.1 Vertikale „Film / Medien / Entertainment" (B2B — der schnellste Markt)

Die Branche existiert im System bereits; hier geht es um Vertiefung und Positionierung.
Konkrete Produktideen auf der bestehenden Pipeline:

1. **KI-Readiness-Check für Produktionsfirmen & Studios** (Film/TV, Post, VFX, Animation,
   Games, Musik, Verlage, Agenturen): gleiche Dramaturgie wie heute (Score, Quick Wins,
   Roadmap, Business Case), aber mit branchenspezifischen Blöcken:
   - KI in der Produktionskette (Development/Drehbuch, Pre-Viz, Dreh, Post/VFX, Verwertung),
   - **Rechte & Urheberrecht bei generativer KI** (Training/Output, Verwertungsketten,
     Darsteller-Einwilligungen, Stimm-/Gesichts-Klone),
   - **EU-AI-Act-Transparenzpflichten für synthetische Inhalte** (Kennzeichnung von
     KI-generiertem Material — Art. 50) statt reiner DSGVO-Compliance,
   - Tarif-/Verbandskontext (Pensionskassen-Debatten, KI-Klauseln in Verträgen),
   - Tool-Stack Medien (Runway, ElevenLabs, DaVinci/Resolve-KI, Firefly, Topaz, …).
   Aufwand: primär Content (Branchenkontext vertiefen, `tools_seed.json` um `medien`-Tools
   ergänzen, 5–10 Prompt-Sektionen schärfen) + Branding-Entkopplung.
2. **Förder-Modul Medien:** Statt BAFA/KfW die medienspezifische Förderlandschaft
   (FFA, Länder-Filmförderungen wie FFF Bayern/MBB/MFG, Creative Europe MEDIA,
   Games-Förderung) — die Funding-Engine-Struktur (`data/funding/*.json` mit
   `suitable_for`/`region`) passt dafür unverändert; nur die Daten sind auszutauschen.
3. **White-Label für Multiplikatoren:** Verbände, Filmförderanstalten, Berufsverbände oder
   Medienakademien bieten den Check unter eigener Marke ihren Mitgliedern an
   (Brand-Pack + eigene Domain + eigener Prompt-Ton). Das ist das erste echte
   Mehr-Mandanten-Szenario und der Grund, K5/K10 sauber zu lösen.
4. **Team-/Produktions-Check:** Mehrere Personen einer Produktion füllen den Bogen aus,
   der Report aggregiert (die Delta-/Versions-Engine aus G11 liefert Bausteine dafür).

### 4.2 Produktlinie „Privatpersonen" (B2C)

Neue Produktlinie auf derselben Engine — kürzer, günstiger, ohne Firmen-Annahmen:

1. **„Persönlicher KI-Kompass":** 15–20 Fragen (Beruf/Alltag, bisherige KI-Nutzung,
   Lernziele, Datenschutz-Sorgen) → Report mit persönlichem KI-Fitness-Score,
   Tool-Empfehlungen für den Alltag, Lernpfad (statt Roadmap), Sicherheits-/Privacy-Basics
   (statt Governance), „KI im Beruf"-Kapitel je Berufsfeld (statt Branche).
   Entfällt: Förderung, Business Case/ROI, Wettbewerb, Compliance-Kapitel.
2. **Karriere-Variante:** „Wie KI-fest ist mein Job/Skill-Profil?" — Score + konkrete
   Weiterbildungs-Empfehlungen; anschlussfähig an den bestehenden Coach-/Chat-Flow.
3. **Einstieg über Freemium:** Kurz-Check kostenlos (Appetizer-Mechanik existiert bereits
   als `appetizer_prompts.py`), Voll-Report kostenpflichtig.

Technisch erfordert das: neuen `size_context` „privat", Pack-Flags zum Abschalten der
Firmen-Sektionen, neue Sektions-Prompts (ca. 10–15 statt 57), eigenes Fragebogen-Schema.
Das 4-Dimensionen-Scoring wird durch ein einfacheres, persönliches Schema ersetzt —
ein weiterer Grund für die datengetriebene Scoring-Engine (K2).

### 4.3 Generelles Geschäftsmodell

- **Ein Engine-Kern, viele Produkte:** Jedes neue Produkt ist nach dem Plattform-Umbau
  primär Content-Arbeit (Fragebogen + Prompts + Daten + Branding), Größenordnung
  ~1–2 Wochen statt Monate.
- **White-Label/Partner-Modell:** Packs + Brand-Configs machen die Pipeline für Partner
  (Berater, Verbände, Agenturen) lizenzierbar — wiederkehrende Erlöse statt Einzelverkauf.
- **Mehrsprachigkeit als Verkaufsargument:** Der EN-Zweig ist erstklassig ausgebaut;
  FR/ES/IT sind im Code vorgesehen und nur Content-Arbeit entfernt.

---

## 5. Empfohlene Roadmap

**Phase 0 — Quick Wins (~1 Woche), sofort sinnvoll, auch ohne Plattform-Entscheidung:**
- Branding zentralisieren: Berater-Signatur, Logos, Kontakt, Impressum als Template-Variablen
  aus einer `brand.json`/ENV (Backend K5 + Frontend-Streuung); `advisor_note.md` und
  `transparency_box.md` parametrisieren.
- Frontend: Backend-URL auf eine Config-Quelle reduzieren; Formbuilder-`injectCSS` auf
  `var(--mk-*)` umstellen.
- `tools_seed.json` um `medien` + Medien-Tools ergänzen; `branch_mapping.py`: `medien`
  auf ein echtes Medien-Profil statt „marketing" mappen.

**Phase 1 — Pilot „Film/Medien" auf Minimalpfad (~2–3 Wochen):**
- Eigener Prompt-Ordner + Manifest für die Medien-Variante (Loader kann das heute schon
  via `PROMPTS_BASE_DIR`); Persona-Prompt je Produkt (K1).
- `medien.json` zur Entertainment-Tiefe ausbauen (Produktion/Post/VFX/Rechte/AI-Act-Art.-50);
  Medien-Förderdaten als eigenes Funding-Set.
- Research-Query-Templates konfigurierbar machen (K6).
- Damit einen realen Pilot-Report für eine Produktionsfirma erzeugen und validieren.

**Phase 2 — Plattform-Fundament (~4–6 Wochen):**
- `product`-Spalte + `ProductConfig`-Resolver (K10); Pack-Struktur einführen und das
  heutige Produkt als erstes Pack extrahieren.
- Scoring datengetrieben aus `scoring.json` (K2) — schrittweise aus `gpt_analyze.py`
  herauslösen; Freitext-Keyword-Maps in Config (K3).
- Frontend: Fragebogen-as-Data (Schema-JSON, deklaratives `showIf`, Sprach-Keys),
  Branding-/Theme-Config, minimaler Build-Schritt.
- PDF-Service: Keys→Tenant-Map + per-Tenant-Rate-Limit/Metriken (oder Instanz je Projekt).

**Phase 3 — Produktlinie „Privatpersonen" (~3–4 Wochen auf fertiger Plattform):**
- Pack `ki-kompass-privat`: neues Fragebogen-Schema, `size_context` „privat",
  10–15 neue Sektions-Prompts, persönliches Scoring, Firmen-Sektionen per Flag aus.

**Reihenfolge-Begründung:** Film/Medien zuerst, weil ~70–80 % vorhanden sind und der Pilot
ohne Plattform-Umbau möglich ist (Minimalpfad); die Plattform-Investition (Phase 2) wird
durch den zweiten zahlenden Anwendungsfall gerechtfertigt; Privatpersonen als drittes,
weil dort der Content-Neuanteil am höchsten ist.

---

## 6. Risiken & Leitplanken

- **`gpt_analyze.py` nicht „nebenbei" refactoren:** Das Scoring-Herauslösen (K2) nur mit
  Golden-Master-Tests (bestehende Gold-Profile/E2E-Checks nutzen), damit das heutige
  Produkt bit-identisch bleibt.
- **Kein Fork pro Projekt:** Jede Abzweigung ohne Pack-Struktur erzeugt doppelte
  Wartung (die DE/EN-Formbuilder-Dublette im Frontend zeigt das Muster bereits).
- **Qualitäts-Gates mitziehen:** `prompt_manifest.json` (`min_words`, `persona_rules`) und
  `b25_enforcer` sind größen-/KPI-, kaum branchenspezifisch — wiederverwenden, aber die
  Funding-Blacklist und ROI-Regeln pro Pack konfigurierbar machen.
- **Rechtliches je Produkt:** Impressum/Datenschutz/AVV sind heute Teil des Brandings —
  bei White-Label-Partnern pro Mandant pflegen (gehört in `brand.json`).
