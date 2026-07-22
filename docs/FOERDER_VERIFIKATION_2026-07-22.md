# Förderkonditionen-Verifikation Medien-Vertikale (2026-07-22)

Web-Recherche in drei parallelen Strängen (Bund / Länder / EU) gegen die
offiziellen Quellen (ffa.de, kulturstaatsminister.de, BMFTR, Länderförderer,
EU-Portale — teils via Suchindex, da Direktabruf durch die Egress-Policy
blockiert war). Alle als korrekt bestätigten oder korrigierten Einträge tragen
`last_verified: 2026-07-22` in den Datenquellen (`data/funding/*.json`,
`services/funding_engine_v2.py`).

## Wichtigste Korrekturen (waren in unserer Datenbank veraltet/falsch)

| Programm | Vorher (falsch) | Verifiziert (Stand 07/2026) |
|---|---|---|
| DFFF | 20–25 %, bis 4 Mio € | **30 %** seit 02/2025; DFFF I bis **5 Mio €**, DFFF II bis **25 Mio €**; Fusion DFFF/GMPF zu „Anreizförderung" für Mitte 2026 angekündigt |
| FFA Produktionsförderung | „Zuschuss/Darlehen" | Selektive Projektförderung (Darlehen) **seit 1.1.2025 abgeschafft** → Referenzfilmförderung (automatischer Zuschuss); Drehbuch/Treatment jetzt über **jurybasierte kulturelle Filmförderung** (BKM-Mittel, FFA-verwaltet; Drehbuch bis 40.000 €, Einzelautor:innen antragsberechtigt) |
| GMPF | „BMWK, bis 25 %" | **BKM** (seit 2018!), **30 %**, Serien bis **20 Mio €/Staffel**, Nicht-Kino-Filme bis 5 Mio € |
| Games-Förderung Bund | „BMWK, projektabhängig" | **BMFTR** (seit 05/2025), nach Antragsstopp **seit 08/2025 wieder offen**; bis 45 % (KMU) / 50 % (Start-ups), **bis 8 Mio €/Projekt** (min. 300 T€); Budget 2026: 125 Mio € — Mitte 2026 noch gute Antragschancen |
| Filmstiftung NRW (Games) | „Darlehen" | **Zuschuss** seit Leitlinie 01.09.2025, max. 300.000 € |
| FFF Bayern | pauschal | Kino bis **3 Mio €** (Darlehen, 150 %-Bayern-Effekt); XR bis 300 T€; Games-Zuschuss bis 70 % / 250 T€ (Richtlinie 01.07.2026) |
| MOIN | pauschal | Keine eigene Games-Linie — Games in HH über **Gamecity Hamburg** (Zuschuss bis 80 T€); Serien max. 500 T€ |
| MDM | pauschal | Eigene Games-/XR-Richtlinie, Produktion bis **600 T€**; regelhaft 250 T€ |
| Creative Europe MEDIA | „Ko-Finanzierung projektabhängig" | Call-spezifisch **60–80 %**; 2026er Development-Deadlines überwiegend vorbei, nächste Runde ab Herbst 2026; Programm endet 2027 → ab 2028 „MEDIA+" im geplanten AgoraEU |

## Neu aufgenommen

- **Jurybasierte kulturelle Filmförderung des Bundes** (Treatment 15 T€ / Drehbuch 40 T€ / Langfilm 1 Mio €; auch für Solo-Autor:innen)
- **Förderprogramm Filmerbe (FFE)** — Archiv-Digitalisierung, Stichtage 15.01./15.07., bis 70–80 T€ (passt zum Archiv-Monetarisierungs-Quick-Win)
- **nordmedia** (NI/HB, eigene Games-Förderung) und **Hessen Film & Medien** (inkl. Linie „Medien")
- EU: **DEVVGIM** (Games/XR, max. 200 T€, 60 %, jährlich ~Februar), **Horizon Europe Cluster 2 HERITAGE-03/-04** („KI in der Kreativwirtschaft", Deadline 23.09.2026 — bei Verifikation noch offen!), **Eurimages** (inkl. Serien-Pilotprogramm 2026)

## Offene Unsicherheiten (vor konkretem Kundenantrag prüfen)

1. Fusionierte DFFF/GMPF-Richtlinie („Anreizförderung", geplant Mitte 2026) — bei Verifikation nur Entwurfsstand belegt; ebenso Freigabestatus der gesperrten 120 Mio €.
2. Games-Förderquoten des Bundes (25/45/50 %) aus Sekundärquellen — gegen aktuelle BMFTR-Richtlinie prüfen.
3. Exakte Obergrenzen: Medienboard New-Media-Unterkategorien, NRW-Kinofilm-Maximum, MFG-DCF, MOIN-Kinofilm.
4. Eurimages-Förderobergrenze 2026; AI-Factories-Zugangskonditionen.
5. Fortbestand der FFA-„Übergangsförderung Produktion" in 2026.
6. Altbestand `funding_engine_v2`: „go-digital"/„Digital Jetzt" stehen dort noch als aktive Programme (2025) — vermutlich ausgelaufen (der b25-Enforcer blacklistet sie textseitig bereits); bei nächster Datenpflege verifizieren und ggf. entfernen.

Die vollständigen Recherche-Berichte mit allen Quellen-URLs liegen in den
Session-Transkripten; die wichtigsten Quellen: ffa.de (DFFF/GMPF/FFE/Referenz-
und kulturelle Förderung), kulturstaatsminister.de (30 %-PM 02/2025),
bmftr.bund.de + DLR Projektträger (Games), medienboard.de, filmstiftung.de,
fff-bayern.de, mfg.de, moin-filmfoerderung.de, mdm-online.de, nordmedia.de,
hessenfilm.de, EU Funding & Tenders Portal, coe.int/eurimages.
