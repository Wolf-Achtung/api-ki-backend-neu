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

## Offen (Handprüfung)

- Creative Europe MEDIA Games/XR (DEVVGIM): nächste Development-Runde ab
  Herbst 2026 — Cut-off-Datum auf eacea.ec.europa.eu prüfen.
- Drei Einträge ohne Prüfdatum, bewusst zurückgestellt (Sammel- und
  Rahmenprogramme): `digital_verwaltung_itsec`, `esf_plus_digital_skills`,
  `interreg`.
- Repo-Freigabe für die Routine-Umgebung, sonst scheitert auch der Lauf
  am 05.10.2026 am Push. Der neue Prompt schreibt in diesem Fall den
  vollständigen Diff in den Bericht.
