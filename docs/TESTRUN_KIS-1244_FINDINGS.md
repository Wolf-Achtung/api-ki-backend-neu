# Testrun KIS-1244 (Briefing 1127): Befunde & Fix-Runden

Erster Medien-Vertikale-Testrun (Gold-Profil „Produktionsfirma Berlin", 22.07.2026).
Drei Reports auditiert (Status-Report 29 S., Strategiebericht 44 S., Potenzial-Analyse 9 S.).
Noten: R1 = 4, R2 = 3−, R3 = 3–4. Substanz durchweg gut medien-adaptiert (Quick Wins,
Roadmap, Vision-Aufgriff, Gamechanger-Wahl „Post-/Archiv-Erschließung"), Handwerk mangelhaft.

## Fix-Runde 1 (dieser PR) — P0

| Befund (Report/Seite) | Ursache | Fix |
|---|---|---|
| Kapitel „KI-Rechte & Kennzeichnung" leer, nur LLM-Rückfrage (R1 S.21) | Produktiv erreichte ein leerer/zu kurzer User-Prompt das LLM; Rückfrage ungefiltert gerendert | Guard: Prompt <300 Zeichen → kein LLM-Call, Fallback; Meta-Refusal-Gate (`_looks_like_meta_refusal`) verwirft Assistenten-Rückfragen; kuratierter statischer Fallback für das Rechte-Kapitel |
| Keine Medien-Förderprogramme in R1/R2 (R1 S.22, R2 S.30–33) | Gerenderte Fördertabelle speist sich aus DRITTER Quelle `data/funding_programmes_core_2025.json` (funding_recommender) — dort fehlten die Medien-Programme | 13 Medien-Programme (DFFF, Medienboard, GMPF, Games-Bund, kulturelle Filmförderung, FFE, Länderförderer, Creative Europe) mit `branches:["medien"]` + `branch_exclusive` ergänzt; harter Branchen-Filter + Match-Boost 1.3 im Recommender; KOMPASS auf `solo` korrigiert |
| „1 % ROI" als Cover-KPI (R1 S.1, R3 S.1) | Jahr-1-ROI mit voll verrechnetem CAPEX ist konstruktionsbedingt ~0 %; kein Sanity-Gate | KPI-Gate in beiden Templates: ROI <20 % → Cover zeigt Amortisation (R1) bzw. 3-Jahres-Nettonutzen (R3) |
| Cover-Slot „Reifegrad: Kleines Team" (R1 S.1) | Größen-Variable im Reifegrad-Slot gebunden | Slot auf `variant_label` (Builder/Starter/…) umgestellt |
| Rechte-Kapitel fehlt im Inhaltsverzeichnis (R1 S.2) | TOC-Generator kannte Sektion nicht | TOC-Eintrag ergänzt |
| Rechte-Kapitel ohne Branchen-/Größen-Kontextblock | Sektion fehlte in `PROMPTS_WITH_BRANCH_SIZE_CONTEXT` | in Whitelist aufgenommen |

Hinweis: Der Strategiebericht bezieht seine Förderliste ebenfalls über den
funding_recommender — die Medien-Programme fließen dort mit diesem Fix automatisch ein.

## Fix-Runde 2 (offen, priorisiert)

1. **Tabellen-Rendering (HIGH, R2 S.17–21/30–32, R3 S.3/4/7):** zerhackte Tool-Namen
   („DaV inci Res olve"), kollidierende Header („VERANTWORTUNGRESSOURCEN") —
   Print-CSS: `table-layout`, Mindestbreiten, `hyphens`-Kontrolle für Eigennamen,
   Spaltenzahl reduzieren; Rendering-Test mit langen deutschen Komposita.
2. **Budget-/Förder-Konsistenz R2 (HIGH):** Exec-Summary „70 % Förderquote /
   Break-Even Monat 4" muss aus den real gelisteten Programmen herleitbar sein;
   eine Budget-Quelle für alle Kapitel (R3: 5–15 T€ vs. 24 T€).
3. **Roadmap-Horizont R2 (MEDIUM):** Antwort „3–6 Monate" muss die Phasenstruktur
   steuern statt 12-Monats-Template + Entschuldigungssatz.
4. **Dedupe-Pass (MEDIUM):** ROI-Methodik-Box 2–3×, Vendor-Audit-Hinweis 4×,
   „kein Widerspruch"-Meta-Disclaimer kundensichtbar → auf je 1 Vorkommen reduzieren,
   Meta-Disclaimer intern halten; Report-Naming vereinheitlichen („KI-Status-Report (Report 1)").
5. **Medien-Tuning Restflächen (MEDIUM):** Starter-Kit (statt „CRM System": ElevenLabs/
   Runway/Firefly/Topaz/DaVinci), 30-Tage-Challenge mit Produktionsaufgaben,
   Fallstudien-Pool um Film/TV-Case, Vendor-Audit über die EMPFOHLENEN Tools
   (nicht nur Bestandstools), Deep-Dive-Tool-Katalog.
6. **Zahlen-Gate Benchmarks R2 (MEDIUM):** „19,95 %"-Scheinpräzision runden,
   Aggregator-Quellen (Gitnux, Mordor) blocklisten, Quelle je Tabellenzeile.
7. **Kleinkram (LOW):** Truncations (R1 S.5/S.7), Challenge-Tage 24–30 fehlen,
   AI-Act-Baustein nach Deployer-Rolle filtern (Anhang-III-Nennung bei „begrenzt"),
   Sparten-Label „Film-/TV-Produktion" auf Cover ausspielen, Kapitelnummer „3b",
   Leerseiten/Orphan-Control, Logo-Beschnitt R3-Cover, Badge-Leiste ohne Kontext prüfen
   (abmahnrelevant, falls Zertifikate nicht führbar), „Basierend auf Live-Marktdaten"-Claim.

## Verifikation Runde 1

- Recommender: `medien/team/BE` → DFFF, Medienboard, Games-Bund, GMPF in Top 8;
  `beratung` → keine Medien-Programme (hart gefiltert). Tests 120/120 grün.
- Meta-Refusal-Gate erkennt die produktive Rückfrage aus KIS-1244, lässt echte Inhalte durch.
- KPI-Gates: ROI 1 % → Amortisation/Nettonutzen; ROI 75 % → unverändert. Jinja-Parse beider Templates grün.
