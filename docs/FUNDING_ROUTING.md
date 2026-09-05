# Funding Routing

Stand 2026-09-05 (KIS-1297).

## Routing Logic

| Language | Country | Route | Service | Data |
|----------|---------|-------|---------|------|
| de | * | DE | `services/funding_recommender.py` (Recommender, Strategiebericht) und `services/extra_sections.build_core_funding_table_html` (R1-Tabelle) | `data/funding_programmes_core_2025.json` |
| en | DE | EN-DE | `services/funding_service_en.get_funding_for_germany_en` | `data/funding/funding_de_en.json` |
| en | ≠DE | EN-EU | `services/funding_service_en.get_funding_eu_core_en` | `data/funding/funding_eu_core_en.json` |

Gelöscht am 05.09.2026, weil kein Report sie las: `services/funding_service.py`,
`data/funding/config.json`, `data/funding/funding_de.json`,
`data/funding/funding_eu.json`.

## Status Rule

Eine Regel für alle Pfade: `funding_recommender.ist_beantragbar`.
`status: paused` oder `expired` und eine verstrichene Datumsfrist schließen
ein Programm aus. Pausierte Programme tragen `recheck_after`; ab diesem Tag
erinnert `scripts/funding_radar.py`.

## Freshness

`scripts/check_funding_freshness.py --max-age-days 90` prüft alle drei
Dateien. Prüfdatum: `verified_at` (core_2025) bzw. `last_verified`
(EN-Dateien). Das Datum wird nur nach gelesener amtlicher Programmseite
gesetzt.

## Size Mapping

| Input | Normalized |
|-------|------------|
| solo, small, freiberufler | solo |
| team, small_team, klein | team |
| kmu, mittel, medium | kmu |

## Funding Scopes in Manifest

```json
{
  "foerderpotenzial": { "funding_scope": "DE" },
  "funding_potential": { "funding_scope": "EN-DE" },
  "funding_eu_core": { "funding_scope": "EN-EU" }
}
```
