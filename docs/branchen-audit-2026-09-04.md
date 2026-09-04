# Branchen-Audit: Hält der Report, was die Startseite verspricht?

Stand: 2026-09-04. Geprüft wurden Frontend (`make-ki-frontend`), Backend
(`api-ki-backend-neu`) und die Railway-Konfiguration vom 03.09.

## Das Versprechen

> „Der KI-Check-Report für die Medien- & Kreativbranche: eine strukturierte
> Einschätzung Ihres aktuellen und künftigen KI-Einsatzes – von
> Film-/TV-Produktion, Postproduktion und Tonstudio über Agenturen,
> Verlage und Games bis Content Creation."

Sieben Sparten. Die Frage ist nicht, ob der Report „Medien" kennt — das
tut er. Die Frage ist, ob ein Tonstudio einen anderen Report bekommt als
eine Filmproduktion.

## Kurzfassung

**Die Sparte wird erhoben und dann fast nirgends benutzt.**

Das Feld `medien_sparte` existiert mit genau den sieben versprochenen
Werten, sauber und deckungsgleich in Frontend, Backend, Chat und
Normalisierung. Es erreicht drei Stellen: ein einziger Prompt von 139
(`ki_rechte_kennzeichnung`), die Auswahl der Fallstudie, das Label auf
dem Deckblatt. Es erreicht **nicht**: die Werkzeugauswahl, die
Förderauswahl, die Starter-Kits, den Faktenblock, 47 weitere
R1-Prompts, alle 4 KPA-Prompts, alle 12 Strategie-Prompts.

Der Strategiebericht — das teuerste Produkt — läuft mit dem System-Prompt
„KI-Strategieberater für den deutschen Mittelstand" und bekommt als
Branchenkontext das Wort „Medien". Die Medien-Persona aus der
Railway-Konfiguration erreicht nur den Status-Report.

Was den Report heute medienspezifisch macht, ist der Freitext
`hauptleistung`. Er trägt die Last allein, und er trägt sie gut: Der
Lauf 1271 liest sich durchgehend nach Postproduktion. Aber er trägt sie
nur, weil der Kunde ihn gut ausgefüllt hat.

## Befund je Sparte

| Sparte | Werkzeuge | Förderung | Fallstudie | Persona | Prompt-Beispiele |
|---|---|---|---|---|---|
| Film-/TV-Produktion | dicht (7) | 14 Programme | eigene | genannt | nur `ki_rechte` |
| Postproduktion / VFX | am dichtesten | 14 (VFX in GMPF, MFG) | geteilt mit Film | genannt | nur `ki_rechte` |
| Tonstudio / Musik / Audio | **0** (ElevenLabs, Descript als Nachbarn) | **0** (Nebenerwähnung NRW) | Werbefilm-Studio | **nicht genannt** | nur `ki_rechte` |
| Agentur / Werbung / PR | nur über `marketing` | **0** | eigene | genannt | nur `ki_rechte` |
| Verlag / Publishing | **0** | **0** | Werbefilm-Studio | genannt | nur `ki_rechte` |
| Games / Interactive | **0** | 1 Bund + 7 Länder | eigene | genannt | nur `ki_rechte` |
| Content Creation | nur über `marketing` | **0** | Werbefilm-Studio | **nicht genannt** | **fehlt auch in `ki_rechte`** |

Drei Sparten haben eigenes Material: Film, Post, Games. Vier bekommen
Nachbarschaft. Ein Verlag und ein Tonstudio lesen dieselbe Fallstudie
über ein Werbefilm-Studio.

## Was hält

- **Die Taxonomie.** `field_registry.py:7–19` ist die Referenz; Chat
  (`routes/chat.py:4474`), Normalisierung (`answers_normalizer.py:117`),
  Formbuilder DE/EN — alle identisch.
- **Die Persona für R1.** Railway setzt `REPORT_PERSONA_PATH` auf
  `prompts/de/_persona_medien.md`; sie ist aktiv. (In `.env.example` steht
  sie nicht — wer lokal testet, bekommt die KMU-Persona.)
- **`CONTEXT_BLOCK`** aus `data/branch_contexts/medien.json` erreicht 30
  R1-Sektionen: vier Workflows, vier Schmerzpunkte, vier Werkzeuge.
  Branchen-, nicht Sparten-Ebene.
- **Werkzeugdaten.** 13 von 23 Einträgen in `tools_seed.json` sind
  medienspezifisch. Der Faktenblock (`kuratierte_fakten.py`) bringt sie in
  zwei Prompts.
- **Förderdaten.** 14 von 39 Programmen sind medienspezifisch und
  `branch_exclusive`.
- **`ki_rechte_kennzeichnung.md`** ist der eine Prompt, der die Sparte
  ernst nimmt: sechs von sieben Sparten mit eigenen Beispielen.
- **Firmenname.** Kein Feld erhebt ihn. Die Invariante hält.

## Was nicht hält

### 1. Die Sparte kommt nicht an

`grep medien_sparte` in den Auswahlpfaden:

```
services/tools_recommender.py       0
services/funding_recommender.py     0
services/tools_starter_kits.py      0
services/kuratierte_fakten.py       0
services/strategy_pipeline.py       0
services/gamechanger_deep_dive.py   0
services/prompt_enhancer.py         0
prompts/strategy_prompts.py         0
```

Die Förderauswahl filtert gegen `branche == "medien"`
(`funding_recommender.py:575–585`). Ein Tonstudio bekommt dieselben 14
Filmförderungen wie eine Filmproduktion. Werkzeuge ebenso.

### 2. Der Strategiebericht kennt die Branche nur dem Namen nach

`prompts/strategy_prompts.py:13`:

> „Du bist ein erfahrener KI-Strategieberater für den deutschen Mittelstand."

Kein `CONTEXT_BLOCK`, keine Persona, kein Sparten-Label. Der Kontext
enthält `branche = "Medien"` (`strategy_pipeline.py:300`) und den
Freitext. Zeile 249 desselben Prompts: „verwende allgemeine
Mittelstands-Benchmarks". Zeile 899 nennt als Beispiel für
Branchen-Compliance „Verschwiegenheitspflicht bei Steuerberatung".

Dasselbe gilt für die KPA: vier Prompts, null Medieninhalte, kein
`CONTEXT_BLOCK`.

### 3. Reste des Mehrbranchen-Systems in den Prompts

10 Prompt-Dateien enthalten Beispiele aus anderen Branchen:
Steuerberater (7 Stellen in `recommendations.md`, `top_3_massnahmen.md`,
`roadmap_90d.md`, `unternehmensprofil_markt.md`, `ai_act_summary.md`,
`strategy_prompts.py`), Handwerk/Sanitär (`branch_deep_dive.md:73`,
`kickoff_vorlage.md:62`, `gamechanger.md:295`), Industrie/E-Commerce
(`ai_act_summary.md:82–85, 198–205`, `costs_overview.md:191`).

Warum das zählt: Am 03.09. hat ein Prompt-Beispiel („rechnen wir mit")
den Report wörtlich geprägt, gegen eine ausdrückliche Regel. Ein
Beispiel schlägt jede Regel. Ein Steuerberater-Beispiel zieht den Text
vom Tonstudio weg.

### 4. Die Persona selbst lässt zwei Sparten aus

`prompts/de/_persona_medien.md` nennt „Produktionsfirmen über
Postproduktion/VFX bis zu Games, Verlagen und Agenturen". Tonstudio und
Content Creation fehlen — zwei der sieben versprochenen.

### 5. Der Fragebogen ist branchenneutral

52 von 53 Feldern lauten in jeder Branche gleich; nur `medien_sparte`
ist medienspezifisch. Im Strategie-Fragebogen: 13 von 13 neutral.
Konkret irreführend für Medienkunden:

- `pilot_bereich` und `ki_einsatz` bieten „Produktion / Logistik" —
  gemeint ist Fertigung. Kein Schnitt, keine Redaktion, kein Studio.
- `vorhandene_tools`: CRM, ERP, Projektmanagement, Buchhaltung. Kein
  Premiere, Avid, DaVinci, Pro Tools, Unreal, InDesign, Frame.io. Ein
  Postproduktionshaus kreuzt „Keine / andere" an.
- `datenquellen`: „Produktions-/Betriebsdaten". Kein Footage, kein
  Archiv, keine Rechte-Metadaten.
- `trainings_interessen`: keine Medienthemen — obwohl die Startseite
  „KI-Rechte & Kennzeichnung für Medieninhalte" verspricht.
- `s5_tools` im Strategie-Fragebogen: 15 Werkzeuge, kein Kreativ-Tool.
- Die Beispiel-Boxen lesen `branche`, nicht `medien_sparte`
  (`formbuilder_de:258`). Games-Studio und Tonstudio sehen dasselbe
  Beispiel.
- `branche` ist im Live-Betrieb ein Ein-Optionen-Dropdown
  (`js/config.js:31`). Die Frage steht trotzdem da.

### 6. Benchmarks: drei Quellen, zwei widersprechen sich

| Quelle | Medien-Wert | Herkunft | wirksam? |
|---|---|---|---|
| `data/benchmarks.json` | avg 44 / top25 62 | „interne Synthese" | **ja** |
| `services/benchmarks.py` DEFAULT | avg 96 / top25 100 | BDZV/Retresco 2025 | nur ohne Datei |
| `extra_sections.py:36` „Top 10 % ab 88" | größenbasiert | keine | ja |

Die einzige benannte Quelle (BDZV) misst den **Anteil KI-Nutzer in
Zeitungsverlagen** und wird als „KI-Reifegrad 96/100" der Medienbranche
gerendert — eine Kategorienverwechslung. Sie ist aber nicht die
wirksame. Die wirksame hat keine Quelle. Der Wert „Top 10 % ab 88" auf
dem Deckblatt hat keine Datenbasis.

### 7. Kleinere Fehler, gefunden nebenbei

| Wo | Was |
|---|---|
| `services/resilienz_pipeline.py:57–65` | 3 von 7 Sparten-Slugs falsch (`film_tv`, `verlag`, `agentur` statt `produktion`, `verlag_publishing`, `agentur_design`) — der Resilienz-Report druckt den Roh-Slug |
| `prompts/de/ki_rechte_kennzeichnung.md:39–42` | Content Creation fehlt in der Sparten-Liste (DE und EN) |
| `data/branch_contexts/medien.json:217` | `industry_specific_notes` mit Sparten-Hinweisen — von keiner Python-Datei gelesen; Schlüssel passen nicht zur Taxonomie |
| `services/tools_recommender.py:84` | `DEFAULT_TOOLS` (Notfallliste) enthält kein einziges Medien-Werkzeug |
| `services/strategy_pipeline.py:318` | `firmenname` wird aus `unternehmen_name` gelesen — ein Schlüssel, der nie existieren darf |
| `services/branch_mapping.py:224` | `"produktion" → industrie` kollidiert mit dem Sparten-Slug `produktion` |
| `formbuilder_de:480, 557` | `projekte_pro_monat`, `top_zeitfresser`: ohne Sternchen, blockieren aber „Weiter" |
| `formbuilder_en` | dieselben zwei Felder fehlen ganz |
| `tests/golden/` | kein Medien-Profil im Gate; kein einziges Testprofil setzt `medien_sparte` |
| `.env.example` | `REPORT_PERSONA_PATH`, `VISIBLE_BRANCHES` fehlen |

## Empfehlung

Die Bausteine sind da: Taxonomie, Persona, Daten, ein Prompt, der es
vormacht. Was fehlt, ist die Verdrahtung. Deshalb nicht das Versprechen
kürzen, sondern die Sparte durchreichen — in dieser Reihenfolge:

**Stufe 1 — Durchreichen (Backend, mechanisch).** Ein gemeinsamer
Baustein `services/medien_sparte.py` liefert das Label DE/EN. Die Sparte
kommt in den Strategie-Kontext, den KPA-Kontext und den
Resilienz-Report. Die Persona ersetzt „Mittelstand" im Strategiebericht,
sobald sie konfiguriert ist. Persona und `ki_rechte` nennen alle sieben.
`firmenname` wird strukturell fest. Kein neuer Inhalt, nur Leitungen.

**Stufe 2 — Prompt-Reste tilgen.** Die zehn Dateien mit
Steuerberater-, Handwerks- und Industrie-Beispielen bekommen
Medien-Beispiele, nach Sparte unterschieden. Das ist Textarbeit, kein
Code — und wegen „Beispiel schlägt Regel" die wirksamste Einzelmaßnahme.

**Stufe 3 — Fragebogen schärfen (Frontend).** Sechs Auswahlfelder
bekommen Medien-Optionen; die Beispiel-Boxen lesen die Sparte; der
Strategie-Fragebogen bekommt Kreativ-Werkzeuge. Das braucht Wolfs
Entscheidung über die Optionstexte.

**Stufe 4 — Daten füllen.** Werkzeuge für Games, Verlag, Tonstudio.
Förderung für Musik (Initiative Musik), Verlag (Deutscher Verlagspreis,
Länderprogramme) — jedes Programm von Hand geprüft, wie beim
Förder-Radar. Fallstudien für Verlag, Tonstudio, Content Creation.
Sparten-Feld in `tools_seed.json` und den Förderdaten, damit Stufe 1
etwas zu filtern hat.

**Stufe 5 — Benchmarks ehrlich machen.** Eine Quelle, benannt, oder
„Richtwert" statt Zahl. Der BDZV-Wert raus aus der Reifegrad-Rolle.

**Stufe 6 — Ein Golden-Profil je Sparte** mit gesetztem
`medien_sparte`. Der laute Prüfer, der Stufe 1 bis 4 gegen Rückfall
sichert.

Stufe 1 beginnt sofort. Stufe 2 folgt, sobald Wolf die Richtung
bestätigt. Stufe 3 braucht seine Optionstexte. Stufe 4 braucht die
Handprüfung je Programm und Werkzeug — dieselbe Regel wie beim
Preis-Prüfdatum: Ein Suchtreffer ist keine Tatsache.
