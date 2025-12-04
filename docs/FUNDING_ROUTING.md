# PLATIN++ Funding Routing

## Routing Logic

| Language | Country | Route | Service |
|----------|---------|-------|---------|
| de | * | DE | funding_service.py |
| en | DE | EN-DE | funding_service_en.py |
| en | ≠DE | EN-EU | funding_eu_core |

## Data Sources

- `data/funding/funding_de.json` - German federal programs
- `data/funding/funding_de_en.json` - German programs in English
- `data/funding/funding_eu.json` - EU-wide programs
- `data/funding/funding_eu_core_en.json` - EU core programs in English

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
