# Förderkonditionen-Verifikation (2026-08-05) — monatlicher Freshness-Check

`scripts/check_funding_freshness.py --max-age-days 90` meldete 30 Einträge
(alle „nie verifiziert", 19 distinkte Programme über 4 Dateien). Die
Medien-Vertikale war mit `last_verified: 2026-07-22` durchgehend aktuell;
zusätzlich wurden die offenen Punkte aus `FOERDER_VERIFIKATION_2026-07-22.md`
nachrecherchiert. Alle bestätigten/korrigierten Einträge tragen jetzt
`last_verified: 2026-08-05`.

## Wichtigste Änderungen

| Programm | Vorher | Verifiziert (Stand 08/2026) |
|---|---|---|
| **ZIM** | „laufend offen", 550 T€ | ⚠️ **Befristeter Antragsstopp seit 07.07.2026** (alle Projektformen, Bundesmittel erschöpft); Wiederaufnahme angestrebt Anfang 2027. Priority 1→3, Engine-Eintrag aktualisiert (war dort noch 380 T€/BMWK) |
| **Invest BW** | pauschal „30–50%, bis 200 T€" | Aufruf-gebunden (zweistufig); Einzelvorhaben bis **650 T€**, Verbund bis **1,3 Mio €** |
| **ProFIT Berlin** | „bis 80%", 500 T€ | Neue Richtlinie seit 01.01.2026: **Zuschuss bis 500 T€** (vorher 400 T€), Darlehen bis 1 Mio €, Zuschussquote bis 50%, Frühphasen-Darlehen bis 10 Jahre |
| **Coaching BONUS Berlin** | „bis 50%, ~4 T€" | **50/80% des Tagessatzes** (Bestand/Gründung), max. 20 Tage à 1.000 € → bis **16 T€** |
| **Transfer BONUS Berlin** | ohne Enddatum | Konditionen bestätigt (70%, 45 T€); **Programmlaufzeit endet 31.12.2026** |
| **Innovationsgutschein Bayern** | „bis 50%, 30 T€" | standard 40% (bis ~15,2 T€), spezial 50% (bis ~49,75 T€); **reine Softwareentwicklung nicht förderfähig** |
| **KfW ERP-Förderkredit 511–513** | generisch | 2026: **kein Mindestkreditbetrag mehr** (ab 25 T€), bis 25 Mio €, Zins ~3,5–5,2% gestaffelt |
| **EXIST** | generisch | Aktiv, Richtlinie bis Ende 2029; laufende Antragstellung, quartalsweise Bewertung |
| **EU-KMU-Fonds (EUIPO)** | „Marken-Voucher 75%" | ⚠️ **Voucher 1 (IP-Scan) und 2 (Marken/Designs) 2026 bereits erschöpft** — nur noch Patente (V3) und Sortenschutz (V4); Priority → 3 |
| **EIC Accelerator** | ohne Termine | 2026: sechs Cut-offs, verbleibend **02.09.** und **04.11.2026**; Zuschuss 2,5 Mio € als Pauschale + Equity 0,5–10 Mio € |
| **EIC Pathfinder** | generisch | Open-Deadline 12.05.2026 vorbei; **Challenges bis 28.10.2026** (u. a. „DeepRAP" vertrauenswürdige kognitive KI, bis 4 Mio €) |
| **Eurostars** | ohne Termine | **Call 11: Einreichung 09.07.–10.09.2026** (14:00 CET) |
| **InnovFin/EIB** | als aktiv geführt | Legacy (Horizon 2020, 2014–2020) — Neuvergaben über **InvestEU**/EIB-Gruppe; Priority → 3 |
| **go-digital** (Engine-Altbestand) | „läuft evtl. 2025 aus" | **Zum 31.12.2024 eingestellt** (Digital Jetzt ebenfalls; Portal 03/2026 abgeschaltet). Engine-Eintrag als eingestellt markiert, fit-Werte 0 |

## Medien-Vertikale (Nachverifikation der offenen Punkte vom 22.07.)

- **DFFF/GMPF**: FFA-Serviceportal seit **22.07.2026** offen; E-Mail-Anträge nur
  noch bis **31.08.2026**, ab 01.09. Portal-Pflicht (portal.ffa.de).
  Anreizförderung auf **~250 Mio €/Jahr verdoppelt**, Haushaltssperre aufgehoben.
- **Games-Förderung Bund (BMFTR)**: Budget 2026 = 125 Mio €; Mitte 2026 erst
  ~35–40 Mio € gebunden → **über 80 Mio € verfügbar**, Bearbeitung nach
  Eingangsreihenfolge — sehr gute Antragslage im 2. Halbjahr.
- **Creative Europe MEDIA**: DEVVGIM 2026 (Games/XR, bis 200 T€) war zum
  11.02.2026 geschlossen; nächste Development-Runden ab **Herbst 2026** beobachten.

## Einreichfristen in den nächsten 8 Wochen (Kundenberatung!)

| Frist | Programm |
|---|---|
| **31.08.2026** | DFFF/GMPF: letzter Tag für E-Mail-Anträge (danach nur FFA-Portal — Registrierung rechtzeitig anlegen) |
| **02.09.2026** | EIC Accelerator Cut-off (Vollantrag) |
| **10.09.2026** | Eurostars Call 11 (14:00 CET) |
| laufend | Games-Förderung Bund: Eingangsreihenfolge bei >80 Mio € Restbudget — früh einreichen |
| bis 31.12.2026 | Transfer BONUS Berlin: letztes Programmjahr |

## Bewusst zurückgestellt (weiter ohne last_verified)

- `digital_verwaltung_itsec` (Sammel-Eintrag Länderprogramme — keine
  Einzelquelle sinnvoll verifizierbar)
- `esf_plus_digital_skills`, `interreg` (nur Programmperioden-Rahmen 2021–2027;
  keine programmspezifische Recherche in diesem Lauf)

## Quellen (Auswahl)

zim.de (Antragsstopp-Meldung 07.07.2026), ffa.de (Serviceportal-PM 22.07.2026,
DFFF/GMPF), bundesregierung.de (250-Mio-Verdopplung), gameswirtschaft.de +
bmftr.bund.de (Games-Budget/Bindungsstand), invest-bw.de + wm.baden-wuerttemberg.de,
ibb.de (ProFIT-Richtlinie 2026), ibb-business-team.de (Coaching/Transfer BONUS),
stmwi.bayern.de + foerderdatenbank.de (Innovationsgutschein), kfw.de (ERP 511–513),
ptj.de (EXIST), euipo.europa.eu (SME Fund 2026 inkl. Voucher-Erschöpfung),
eic.ec.europa.eu-Ökosystem (Accelerator/Pathfinder 2026), eurekanetwork.org
(Eurostars Call 11), hadea.ec.europa.eu (Digital Europe 2026), ideal-ist.eu
(Cluster-4-WP 2026–27), eacea.ec.europa.eu (DEVVGIM),
innovation-beratung-foerderung.de (go-digital-Ende).
