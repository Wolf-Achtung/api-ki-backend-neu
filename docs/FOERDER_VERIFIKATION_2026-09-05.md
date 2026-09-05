# Förderkonditionen-Verifikation (2026-09-05) — Routine-Lauf und Nachprüfung

Die monatliche Routine lief am 05.09.2026 um 07:07 UTC. Ihr Commit
(`6b36c3f`, Branch `claude/funding-freshness-2026-09`) kam nie an: Der Push
scheiterte mit 403, weil die Umgebung der Routine das Repo nicht mehr in
den freigegebenen Quellen hatte. Dieses Dokument ersetzt den verlorenen
Bericht und hält fest, was davon belegt ist.

## Befund am Verfahren (KIS-1297)

| Befund | Folge | Behoben |
|---|---|---|
| Die Routine pflegte `data/funding/funding_de.json`. Kein Report las die Datei; der einzige Leser war `services/funding_service.py`, den nur ein Stresstest aufrief. | Zwei Datenwelten liefen auseinander: DFFF/GMPF in der wirksamen Datei auf „laufend", in der gepflegten Datei mit Serviceportal-Notiz. | Beide Dateien, `funding_eu.json` und `config.json` gelöscht; Stresstest hängt am Produktionspfad. |
| `scripts/check_funding_freshness.py` kannte `data/funding_programmes_core_2025.json` nicht — die Datei, aus der die deutschen Reports lesen. | Die wirksamen Einträge wurden nie als veraltet gemeldet. | Skript prüft core_2025 (`verified_at`) und die beiden EN-Dateien (`last_verified`). |
| Der EN-Pfad (`funding_service_en.py`) kannte kein Statusfeld. | ZIM stand trotz Antragsstopp in der englischen Förderbox (priority 3). | `ist_beantragbar` gilt jetzt in allen Pfaden; die EN-Datei trägt `status`/`recheck_after`. |
| Routine-Prompt verwies auf `services/funding_engine_v2.py` (gelöscht 03.09.). | Kein Schaden, aber ein toter Befehl. | Prompt am 05.09. aktualisiert (Belegregel, Dateien, Tests, Diff-Ausgabe bei Push-Fehler). |

## Belege (Wolf, Perplexity, nur ffa.de, 05.09.2026)

| Nr | Frage | Antwort (Zitat von ffa.de) | URL | Datum auf der Seite |
|---|---|---|---|---|
| 1a | DFFF – Mittel 2026 ausgeschöpft? | „Das für 2026 verfügbare Antragsvolumen von DFFF und GMPF ist nun ausgeschöpft. Damit wird die historische Höchstsumme an Fördermitteln für die Anreizförderung von der Filmbranche in Anspruch genommen." | ffa.de/dfff-aktuelles.html, Pressemitteilung | 20.08.2026 |
| 1b | DFFF – Antragsstopp? | „Update: 20. August 2026 — Ab sofort ist eine Antragsannahme für Projekte mit Drehbeginn im Jahr 2026 nicht mehr möglich. Das vorgesehene Antragsvolumen von 30 Mio. Euro wurde erreicht." (identisch auf DFFF I und DFFF II) | ffa.de/dfff-i.html, ffa.de/dfff-ii.html | Update 20.08.2026 |
| 1c | DFFF – nächstes Antragsfenster | „Anträge für Projekte mit Drehbeginn im Jahr 2027 können voraussichtlich ab November über das FFA-Serviceportal gestellt werden. Über das Einreichverfahren 2027 wird die FFA schnellstmöglich informieren." Kein Kalenderdatum. | ffa.de/dfff-i.html | Update 20.08.2026 |
| 2a–c | GMPF | Identischer Text wie DFFF (Volumen ausgeschöpft, kein Drehbeginn 2026, 2027 voraussichtlich ab November). | ffa.de/german-motion-picture-fund-gmpf.html | Update 20.08.2026 |
| 3 | Fusion DFFF/GMPF? | Nein. Zwei getrennte Programme unter dem Oberbegriff „Anreizförderung". DFFF-Richtlinie 2026 gilt 01.01.–31.12.2026 (löst Fassung vom 05.07.2024 ab); GMPF-Richtlinie 2026 gilt 01.01.–31.12.2026 (löst Richtlinie vom 28.03.2025 ab). | ffa.de/, ffa.de/dfff-home.html, ffa.de/dfff-richtlinie.html, beide Richtlinien-PDFs | Stand 01.01.2026; Startseite 02.09.2026 |

Die Routine hatte „nächstes Fenster 09.10.2026" gemeldet. Die FFA nennt
kein Datum, nur „voraussichtlich ab November". Das Routine-Datum stammte
aus fehlgeschlagenen Web-Suchen und ist nicht übernommen.

## Änderungen in den Daten

| Programm | Vorher | Jetzt |
|---|---|---|
| **DFFF** (core_2025, funding_de_en) | `active`, „laufend", Fusion angekündigt | `paused`, `recheck_after` 01.11.2026, Notiz mit Beleg; keine Fusion; `verified_at`/`last_verified` 2026-09-05 |
| **GMPF** (core_2025, funding_de_en) | wie DFFF; EN-URL zeigte auf bmwk.de | wie DFFF; URL ffa.de/german-motion-picture-fund-gmpf.html |
| **ZIM** (funding_de_en) | ohne Statusfeld | `paused`, `recheck_after` 2027-01-15 (wie core_2025) |
| Transfer BONUS Berlin, Innovationsgutschein Bayern (funding_de_en) | tote URLs aus der Radar-Mail vom 03.09. | Programmseiten von ibb.de bzw. bayern-innovativ.de (Stand 05.08.2026) |

Nicht übernommen, weil unbelegt: die Korrekturen der Routine an
`digital_verwaltung_itsec` und `esf_plus_digital_skills` (kein Beleg im
Bericht, Commit verloren) sowie Interreg „bis 80 %" — „70–85 %" bleibt, denn
85 % gilt für Sonderregionen.

## Was Kunden jetzt sehen

- Film- und VFX-Sparten: DFFF und GMPF fallen aus allen Empfehlungen
  (R1-Tabelle, Recommender, Strategiebericht, EN-Förderbox). Regionale
  Filmförderer (Medienboard, FFF Bayern, Filmstiftung NRW, MFG, MDM,
  nordmedia, MOIN), Filmerbe, kulturelle Filmförderung des Bundes,
  Creative Europe MEDIA und Eurimages bleiben.
- Ab 01.11.2026 erinnert der Förder-Radar: Prüfen, ob die FFA das
  Einreichverfahren 2027 geöffnet hat, dann `status: active` und
  `deadline` neu setzen.

## Nachtrag: ProFIT (Wolf, Perplexity, nur ibb.de, 05.09.2026)

Anlass: Die deutsche Datei sagte „bis 80 % Zuschuss, Rest Darlehen", die
englische „bis 50 % Zuschuss". Beide waren falsch. Der Strategiebericht
KIS1274 versprach daraus „Förderquoten bis 80 %" für die Einführung von
KI-Werkzeugen.

| Frage | Antwort (Zitat Richtlinie ProFIT, Stand 01.01.2026) | Fundstelle |
|---|---|---|
| Zuschuss industrielle Forschung | Kleine Unternehmen 70 %, mittlere 60 % (Einzelprojekt); im Verbund „KMU und Forschungseinrichtung": „80 % (Zuschussquote)" kleine, „75 %" mittlere | Anhang 1, S. 13 ff. |
| Zuschuss experimentelle Entwicklung | Regulär Darlehen: „als Darlehen vorrangig für KMU in den Phasen der experimentellen Entwicklung …"; Zuschuss nur „im Rahmen von thematischen Aufrufen (Calls)". Produktseite: „nur bei KMU max. 80 % als Darlehen" | Ziffer 5.2, Produktseite |
| Höchstbeträge | „Zuschüsse … auf insgesamt 500.000 EUR je Projekt bzw. Projektpartner begrenzt", „Darlehen beträgt maximal 1.000.000 EUR je Projekt" | Ziffer 5.2.1, S. 6 |
| Geltung | „treten am 01.01.2026 in Kraft", „mit Ablauf des 31. Dezember 2027 außer Kraft" (Anträge bis dahin) | Ziffer 8, S. 12 |
| KI-Werkzeuge einführen ohne Forschungsanteil | Nicht belegt. „Nicht erfasst sind routinemäßige Änderungen an bestehenden Produkten, Prozessen oder Dienstleistungen." Projekte „müssen erkennbare technische Risiken beinhalten … und zu technisch innovativen Lösungen mit Alleinstellungsmerkmale führen." | Ziffer 2.1.2, S. 2–3; Ziffer 4.1/4.2, S. 4 |

Quelle: https://www.ibb.de/media/dokumente/foerderprogramme/wirtschaftsfoerderung/profit/profit-projektfoerderung/profit_richtlinie.pdf
und https://www.ibb.de/de/foerderprogramme/pro-fit-projektfinanzierung.html

Folge in den Daten (beide Dateien): Fördersatz differenziert, Höchstbeträge,
Fokus „F&E mit technischem Risiko — Einführung vorhandener Werkzeuge nicht
förderfähig", KI-Relevanz von „Sehr hoch" auf „Mittel", Priorität 1 → 2,
Frist 31.12.2027, Prüfdatum 05.09.2026. Für die meisten Medienkunden ist
ProFIT damit kein Weg, die Einführung von KI-Werkzeugen zu finanzieren —
nur eigene Entwicklungsprojekte.

## Nachtrag: Creative Europe MEDIA (Wolf, Perplexity, nur ec.europa.eu und eacea.ec.europa.eu, 05.09.2026)

Anlass: Der Datensatz sagte „Calls ab Herbst 2026" ohne Datum; Report 1
zeigte dem VFX-Studio „Games/XR Call jährlich" ohne Frist.

| Call | Kennung | Status | Beleg (Zitat) | URL |
|---|---|---|---|---|
| Video Games and Immersive Content Development 2026 | CREA-MEDIA-2026-DEVVGIM | Closed | „Opening date: 30 September 2025 … Deadline date: 11 February 2026, 17:00:00 Brussels time … EUR 200 000 per project" | ec.europa.eu/info/funding-tenders/…/topic-details/CREA-MEDIA-2026-DEVVGIM; Call-Fiche PDF |
| European Slate Development 2026 | CREA-MEDIA-2026-DEVSLATE | Closed | „Opening date: 30 September 2025 … Deadline date: 03 December 2025" | …/topic-details/CREA-MEDIA-2026-DEVSLATE |
| European Mini-Slate Development 2026 | CREA-MEDIA-2026-DEVMINISLATE | Offen | „the Call opened on 28/04/2026 … Deadline date: 17 September 2026, 17:00:00 Brussels time" | …/topic-details/CREA-MEDIA-2026-DEVMINISLATE |
| Alle 2027-Calls | CREA-MEDIA-2027-* | Nicht belegt | Portal-Suche: „No results found"; Themenseiten laden keinen Inhalt; culture.ec.europa.eu/funding/calls filtert nur bis 2026 | Funding & Tenders Portal, Calls-for-proposals-Suche |

Folge in `data/funding_programmes_core_2025.json` (`creative_europe_media`):
`deadline` nennt die Mini-Slate-Frist 17.09.2026, `deadline_notes` die
geschlossenen 2026er Calls und die offene 2027-Runde, `verified_at`
05.09.2026, `recheck_after` 15.10.2026 — die Routine vom 05.11. prüft
dann, ob die 2027-Calls offen sind (Muster: Öffnung Ende September).
Nicht eingetragen: ein Datum für 2027, denn es gibt keins.

## Offen (Handprüfung)

- Creative Europe MEDIA 2027-Calls: ab Mitte Oktober auf dem Funding &
  Tenders Portal prüfen (siehe Nachtrag).
- Drei Einträge ohne Prüfdatum, bewusst zurückgestellt (Sammel- und
  Rahmenprogramme): `digital_verwaltung_itsec`, `esf_plus_digital_skills`,
  `interreg`.
- Repo-Freigabe für die Routine-Umgebung, sonst scheitert auch der Lauf
  am 05.10.2026 am Push. Der neue Prompt schreibt in diesem Fall den
  vollständigen Diff in den Bericht.
