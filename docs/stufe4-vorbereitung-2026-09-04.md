# Stufe 4 — Daten je Sparte (Vorbereitung, 04.09.2026)

Stufe 4 des Branchen-Audits (`docs/branchen-audit-2026-09-04.md`) hat
zwei Hälften. Die erste ist Code und läuft ohne Netz: ein Sparten-Feld
in den Daten und die Auswahl, die es liest. Die zweite ist Handprüfung:
neue Werkzeuge und Programme für die Sparten, die heute leer ausgehen.
Dieses Dokument liefert die erste Hälfte fertig und die zweite als
Kandidatenliste. Regel wie beim Preis-Prüfdatum: **Ein Suchtreffer ist
keine Tatsache.** Kein Kandidat steht in den Daten, bevor ein Mensch die
Anbieterseite gesehen hat.

## 1. Befund vor Stufe 4

| Baustein | Kannte die Sparte? | Folge |
|---|---|---|
| Werkzeugauswahl (`tools_recommender`) | nein, nur `branche` | Tonstudio und Games-Studio bekamen dieselbe Liste |
| Faktenblock (`kuratierte_fakten`) | nein (läuft über `recommend_tools`) | dito im Prompt |
| Förderauswahl (`funding_recommender`) | nein | Tonstudio sah DFFF und GMPF (Kinofilm, High-End-Serie) |
| Fallstudie (`sofort_start_generator`) | teilweise (3 Fälle) | Verlag, Tonstudio, Content Creation bekamen das Werbefilm-Studio |
| Starter-Stacks (`extra_sections`) | — | Baustein ist tot (siehe Abschnitt 5) |

## 2. Was jetzt eingebaut ist (KIS-1292)

**Sparten-Feld.** `sparten` ist eine optionale Liste von Slugs aus
`services/medien_sparte.py`. Ein Eintrag ohne Feld bleibt, wie er war.
`medien_sparte.passt_zur_sparte(eintrag, sparte)` liefert `None`, wenn
es nichts zu sagen gibt (kein Feld, keine Kunden-Sparte, leeres Feld),
sonst `True` oder `False`. Ein vergessenes Feld kann so nie stillschweigend
alles ausfiltern.

**Werkzeuge.** 13 der 23 Einträge in `data/tools_seed.json` tragen
Sparten. Treffer: +2 im Basis-Score und +0,15 im Segmentgewicht. Kein
Treffer: kein Abzug, nichts fällt heraus. Die zehn generischen Werkzeuge
(Make, Notion, OpenAI, Mistral …) bleiben ohne Feld.

**Förderung.** Alle 14 exklusiven Medienprogramme in
`data/funding_programmes_core_2025.json` tragen Sparten, abgeleitet aus
ihrem `focus`-Text. Treffer ×1,2. Kein Treffer bei `branch_exclusive`
→ Programm fällt weg; bei einem generischen Programm ×0,8. Ohne
Kunden-Sparte bleibt die Tabelle byte-gleich. Beispiele:

| Kunde | bleibt | fällt weg |
|---|---|---|
| Tonstudio (NRW) | Film- und Medienstiftung NRW (nennt Audio/Podcast) | DFFF, GMPF, Games-Förderung |
| Games-Studio (Bayern) | Games-Förderung des Bundes, FFF Bayern | DFFF, Eurimages |
| Verlag | nur die generischen Programme (KfW, BAFA, Länder-Digital) | alle Filmprogramme |

Die Zuordnung steht als Tabelle in Abschnitt 3 — sie ist eine
Einordnung aus dem Programmtext, keine geprüfte Antragsberechtigung.
Wer eine Zeile anders liest, ändert die Liste im JSON, nicht den Code.

**Fallstudien.** Drei neue Fälle in DE und EN: Fachverlag
(Vorlektorat, Metadaten), Tonstudio (Take-Suche, Vorreinigung,
Einwilligung für synthetische Stimmen), Content-Team (ein Dreh, zehn
Formate, Kennzeichnung). Die Auswahl geht jetzt über den Slug; vorher
traf das Label „Film-/TV-Produktion" über die Teilzeichenkette „pr"
auch die Agentur.

**Durchgereicht** an beiden Stellen, die die Förderliste ziehen
(`gpt_analyze` für R1, `strategy_pipeline` für S7), und an
`get_recommendations_for_report`.

Test: `tests/test_kis1292_sparte_daten.py` (53).

## 3. Sparten-Zuordnung der Förderprogramme

| Programm | Sparten | Grund (aus `focus`) |
|---|---|---|
| DFFF | produktion, post_vfx | Kinofilmproduktion |
| GMPF | produktion, post_vfx | High-End-Serien, VFX-Anteil |
| Kulturelle Filmförderung des Bundes | produktion | Treatment bis Verleih |
| Games-Förderung des Bundes | games | Entwicklung, Prototyping |
| Filmerbe (FFE) | produktion, post_vfx | Archiv-Digitalisierung |
| Medienboard Berlin-Brandenburg | produktion, post_vfx, games | Film, Serie, Games, XR |
| FFF Bayern | produktion, post_vfx, games | Film, Games, XR |
| Film- und Medienstiftung NRW | produktion, post_vfx, games, musik_audio | nennt Audio/Podcast |
| MFG Baden-Württemberg | produktion, post_vfx, games, content_creation | Digital Content (DCF) |
| MDM | produktion, post_vfx, games | Film, Serie, Games/XR |
| MOIN | produktion, post_vfx | Film, Serie, XR |
| nordmedia | produktion, post_vfx, games | eigene Games-Förderung |
| Creative Europe MEDIA | produktion, post_vfx, games | AV-Sektor, Games-Call |
| Eurimages | produktion | Koproduktion ab 70 Min. |

Offen: `agentur_design` und `verlag_publishing` haben kein einziges
Programm. Das ist richtig so, solange die Daten keines kennen — der
Report zeigt dann die generischen Programme, keine Filmförderung.

## 4. Kandidaten zur Handprüfung

Je Kandidat prüfen: Anbieterseite erreichbar, Sitz des Anbieters,
AVV/DSGVO-Aussage, Preis. Nur was geprüft ist, kommt mit `verified_at`
in die Daten; ohne Prüfdatum zeigt der Report keinen Preis.

### 4.1 Werkzeuge

| Sparte | heute im Seed | Kandidat | Wofür | Prüfen |
|---|---|---|---|---|
| verlag_publishing | Firefly, DeepL, Trint, Aleph Alpha | LanguageTool | Korrektur, Stil (Anbieter in Potsdam) | Sitz, AVV, Team-Preis |
| verlag_publishing | | DeepL Write | Umformulierung, Stil | ob eigenständig oder Teil von DeepL Pro |
| verlag_publishing | | Duden-Mentor | Korrektur nach Duden | Anbieter (Cornelsen), Unternehmenslizenz |
| musik_audio | ElevenLabs, Descript, Amberscript | Auphonic | Podcast-Nachbearbeitung, Pegel, Rauschen (Anbieter in Wien) | Sitz, AVV, Preisstufen |
| musik_audio | | iZotope RX | Restauration, Rauschentfernung | US-Anbieter, Desktop, kein Cloud-Datenfluss? |
| musik_audio | | Adobe Podcast Enhance | Sprachverbesserung | Adobe-AVV, ob im CC-Abo |
| games | ElevenLabs, DeepL, Firefly | Lokalise oder Crowdin | Lokalisierungs-Pipeline | Sitz, AVV, ab welcher Stufe KI-Übersetzung |
| games | | Scenario | Asset-Varianten aus eigenem Stil | Sitz, Rechte an Trainingsdaten |
| games | | Inworld AI | NPC-Dialoge | US, Datenfluss, Store-Deklaration |
| content_creation | Descript, Runway, Firefly, Amberscript, Trint | Opus Clip | Kurzformate aus Langvideo | US, AVV, Preis |
| content_creation | | Canva Magic Studio | Grafik, Varianten | Sitz (AU), AVV, Team-Preis |
| content_creation | | CapCut | Schnitt | **nur als Warnung**: ByteDance, Datenschutz-Lage unklar |
| agentur_design | Firefly, Runway, Frame.io, DeepL, Aleph Alpha | Midjourney | Moodboards | kein AVV bekannt — eher als Hinweis, nicht als Empfehlung |

### 4.2 Förderprogramme

| Sparte | Kandidat | Träger | Prüfen |
|---|---|---|---|
| musik_audio | Initiative Musik (Infrastrukturförderung, Musikexport) | Bund (BKM) | ob Studios als Unternehmen der Musikwirtschaft antragsberechtigt; Fristen |
| musik_audio | Musikfonds | Bund (BKM) | Zielgruppe (Künstler:innen vs. Unternehmen) |
| verlag_publishing | Deutscher Verlagspreis | Bund (BKM) | ist ein Preis, keine Projektförderung — Bewerbung möglich, Kriterien |
| verlag_publishing | Landes-Verlagspreise (Berlin, Bayern) | Länder | dito |
| verlag_publishing | Deutscher Übersetzerfonds | Bund | nur Übersetzungen, Antrag durch Übersetzer:innen |
| content_creation | Länderprogramme Kultur- und Kreativwirtschaft | Länder | ob Content-Produktion förderfähig; meist Beratung/Coaching |

Für `agentur_design` und `content_creation` bleibt vorerst die
generische Liste. Das ist ehrlicher als ein Programm, das nicht passt.

### 4.3 Fallstudien

Erledigt (Abschnitt 2). Offen bleibt eine zweite Variante je Sparte für
`kmu`, sobald die Rückmeldungen aus `tools_adopted` und
`funding_applied` zeigen, was Kunden wirklich einsetzen.

## 5. Toter Baustein: Starter-Stacks

`extra_sections.build_starter_stacks` liest `data/starter_stacks.json`
und iteriert wie über eine Liste. Die Datei ist ein Dict mit Schlüsseln
wie `common`, `marketing & werbung`. Jeder Schleifendurchlauf wirft
`AttributeError`, die Schleife fängt das und macht weiter; das Ergebnis
ist immer „Keine Starter-Stacks konfiguriert". Kein Template rendert
`STARTER_STACKS_HTML`. Der Baustein steht nicht auf der Stufe-4-Liste.
Entscheidung offen: beleben (dann mit Sparten-Schlüsseln) oder löschen.

## 6. Nächste Schritte

1. Wolf prüft die Kandidaten in 4.1 und 4.2 und streicht, was nicht
   passt.
2. Geprüfte Einträge kommen mit `verified_at`, `sparten` und den
   bestätigten Feldern in die Daten. Der Tool-Radar und der Förder-Radar
   nehmen sie dann in die Wiedervorlage.
3. Stufe 5: Benchmarks — eine Quelle oder „Richtwert".
4. Stufe 6: ein Golden-Profil je Sparte mit gesetztem `medien_sparte`,
   damit ein Rückfall in Stufe 1 bis 4 laut wird.
