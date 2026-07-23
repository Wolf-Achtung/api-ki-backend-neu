# Phase 1: Medien-Pilot — Umsetzung & Aktivierung

Stand 2026-07-22. Baut auf Phase 0 (PR #1110) auf. Ziel: Die Pipeline ist auf die
Vertikale Film/Medien/Entertainment ausgerichtet; die übrigen Branchen bleiben
vollständig erhalten, sind aber nicht mehr sichtbar (reversibel per Config).

## Was umgesetzt wurde

1. **Branchen-Sichtbarkeit (reversibel)**
   - Frontend: `js/config.js` → `VISIBLE_BRANCHES = ['medien']`. Der Formbuilder
     (DE/EN) filtert nur die Anzeige des `branche`-Selects; bei genau einer
     sichtbaren Option wird sie vorausgewählt. Leeres Array = alle 13 Branchen.
     Fail-open bei Konfigurationsfehlern.
   - Backend: `get_frontend_branch_options()` respektiert ENV
     `VISIBLE_BRANCHES` (kommagetrennt, z. B. `medien`). Ohne ENV: alle 13.
     Mapping, Profile und Alt-Daten sind nicht betroffen — bestehende Briefings
     anderer Branchen rendern unverändert.

2. **Medien-Branchenkontext vertieft**
   - `data/branch_contexts/medien.json` und `data/branch_contexts/en/creative_media.json`:
     Produktionskette (Development/Virtual Production/Lokalisierung), Rechte-
     und AI-Act-Painpoints, neue Quick Wins für Team (Post-Pipeline, Pre-Viz)
     und KMU (Archiv-/Rechte-Register, KI-Richtlinie mit Art.-50-Prozess),
     `regulatory_notes` (Art. 50, TDM/§ 44b UrhG, Persönlichkeitsrechte, DSGVO),
     erweiterte Erfolgs-KPIs und Tool-Ökosystem (generativ, VFX/Virtual Production).

3. **Medien-Förderdaten**
   - `data/funding/funding_de.json`: +10 Programme (DFFF, FFA, GMPF,
     Games-Förderung des Bundes, FFF Bayern, Medienboard BB, Filmstiftung NRW,
     MFG BW, MOIN, MDM) — alle mit `branchen: ["medien"]` markiert.
   - `data/funding/funding_eu.json`: +Creative Europe MEDIA.
   - `data/funding/funding_de_en.json`: 8 EN-Pendants.
   - Neuer optionaler **Branchen-Filter** in `funding_service.py` und
     `funding_service_en.py`: Programme mit `branchen`-Liste erscheinen nur für
     passende Branchen; Programme ohne Feld für alle (rückwärtskompatibel).
   - `funding_engine_v2.py` (G26-Matrix): Kategorie `medien` mit
     Alignment-Matrix + 5 Medien-Programme; `medien` in bestehende
     Kategorien-Alignments aufgenommen.
   - Hinweis Datenpflege: Beträge/Quoten sind bewusst qualitativ
     ("projektabhängig") gehalten, wo keine stabile Zahl existiert —
     vor Kundeneinsatz Details je Programm prüfen (Zahlen-Disziplin).

4. **Research-Queries**
   - `live_research.py`: `BRANCH_QUERY_OVERRIDES["medien"]` ersetzt die
     KMU-generischen Queries (Markt-Trends, Benchmark, Fördermittel DE/EU)
     durch medienspezifische; Queries nutzen jetzt das lesbare Branchenlabel
     statt des Rohwerts; `BRANCHE_MAP` um Medien-Einträge ergänzt.
   - `news_researcher.py`: neue Newsletter-Kategorie „MEDIEN & KI".

5. **Berater-Persona pro Vertikale**
   - `services/report_system_prompt.py`: Persona-Satz überschreibbar via
     ENV `REPORT_PERSONA_TEXT` (direkter Text) oder `REPORT_PERSONA_PATH`
     (Datei). Default unverändert (KMU/DACH). Fail-open.
   - Medien-Persona liegt bereit: `prompts/de/_persona_medien.md`.

## Aktivierung des Medien-Modus (Railway-ENV, Backend)

```
VISIBLE_BRANCHES=medien
REPORT_PERSONA_PATH=prompts/de/_persona_medien.md
```

Frontend ist nach Deploy dieses Branches automatisch im Medien-Modus
(`VISIBLE_BRANCHES` in `js/config.js`).

## Zurückdrehen

- Frontend: `VISIBLE_BRANCHES = []` in `js/config.js`.
- Backend: beide ENV-Variablen entfernen.

## Offene Punkte für den Pilot

- Detailprüfung der Förderprogramm-Konditionen vor erstem Kundenreport
  (Beträge, aktuelle Einreichfristen, Verfügbarkeit der Games-Förderrunden).
- Test-Profil „Produktionsfirma" (`data/test_profiles/`) anlegen und einen
  Gold-Report generieren, bevor der erste echte Pilot läuft.
- Optional: EN-Persona (`_persona_medien` EN-Pendant), falls der Pilot
  international koproduziert.

## Nachtrag 23.07.2026 — Internationalisierung & Daten-Aktualität (KIS-1248)

- **Branding**: „TÜV-zertifizierter KI-Manager" → „TÜV-zertifiziertes KI-Management"
  in allen Templates, Brand-Config und Prompts; „Live-Marktdaten"-Claim auch im
  Strategiebericht-Seitenfuß entschärft.
- **Quartals-Tool-Check**: `scripts/check_tools_freshness.py` prüft `verified_at`
  aller Einträge in `data/tools_seed.json` (Exit 1 bei >100 Tagen/nie verifiziert).
  Cloud-Routine `trig_014G1PCQxMLsryRB2BkNVXx4` läuft am 5. Jan/Apr/Jul/Okt
  (07:00 UTC, Fresh Session, Push+E-Mail): verifiziert Preise/AVV-Status gegen
  Herstellerquellen, aktualisiert tools_seed + Starter-Kit/Vendor-Basisdaten,
  öffnet Draft-PR. Spot-Check 23.07.: Amberscript/DeepL aktuell, Descript-Preis
  aktualisiert (0–35 $/Monat).
- **EU-Förderung**: Eurimages (Europarat, Koproduktionen, bis 500 T€, 3 Calls/Jahr)
  als medien-exklusives Programm ergänzt; EIC Accelerator, DIGITAL Europe,
  Horizon Europe Cluster 4 und Creative Europe MEDIA waren bereits im Datensatz
  (alle verified Juli 2026). Der monatliche Förder-Check überwacht auch diese.
- **Englische Report-Variante (Phase 1)**: `templates/pdf_template_en.html`
  (vollständige EN-Fassung von pdf_template_v7) — der Renderer wählt sie bei
  `lang=en` automatisch (Pfad existierte bereits, Datei fehlte). Prompts/en,
  i18n-ui_labels (191) und die Engine-Label-Sets (Business Case, Vendor-Audit,
  Risk) waren bereits zweisprachig. Noch offen für Voll-EN: strategy_report- und
  KPA-Template, E-Mail-Templates, EN-Fassung der Medien-Förderprofile.
- **Weitere Sprachen**: Architektur trägt das Muster prompts/<lang>/ +
  Template-je-Sprache + ui_labels; Renderer ist aktuell de/en-binär
  (`is_en`) — für FR/ES/IT müsste die Sprachweiche auf Lang-Codes
  verallgemeinert und je Sprache Template+Prompts übersetzt werden.
  DE-spezifische Pässe (Siezen-Guard, Dezimal-Komma-Lint) sind lang-gated
  zu halten.
