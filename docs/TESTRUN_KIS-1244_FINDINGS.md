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

## Testrun KIS-1246 (Briefing 1129, 23.07.2026) — Validierung Runde 1 + Fix-Runde 2

Noten: R1 = 2, R2 = 2, R3 = 2+/1−. Runde-1-Fixes im Ergebnis bestätigt:
Cover zeigt „11,9 Mon. Amortisation" statt „1 % ROI", „Reifegrad: Builder",
Rechte-Kapitel im TOC, 8 Medien-Programme in der Fördertabelle (mit Links),
Hero der KPA zeigt „+48.900 € Nettonutzen (3 Jahre)", Fallstudie medien-adaptiert,
R2-Exec-Summary erklärt ROI-Methodik (19 % brutto vs. 1 % netto) und deckelt
die 70-%-Förderquote als Plausibilitäts-Cap.

### Fix-Runde 2 (dieser PR)

| Befund (Report/Seite) | Ursache | Fix |
|---|---|---|
| Rechte-Kapitel WIEDER LLM-Rückfrage (R1 S.22): „Bitte senden Sie den Unternehmenskontext und die gewünschte Report-Sektion…" | Enhanced-Prompt-Pfad warf Exception → Legacy-Pfad rief LLM mit `prompts.get(section, "")` = LEEREM Prompt auf; Refusal-Gate (feste Phrasenliste) kannte die neue Formulierung nicht; min_words-Default 10 ließ die 35-Wörter-Rückfrage durch | (1) Legacy-Pfad: Prompt <200 Zeichen → kein LLM-Call, kuratierter Fallback; (2) Refusal-Gate auf Struktur-Regex umgestellt + auch im Legacy-Pfad aktiv; (3) `ki_rechte_kennzeichnung` min_words=200 in beiden Gates; (4) expliziter Kontext-Block + „nie Rückfragen"-Direktive in beiden Prompt-Dateien |
| Tool-/Fördertabellen zerhackt (R2 S.18–20/29–30): „Micr osoft Copilot", Header-Kollision „DSGVO-KONFOR MITÄT"/„PASSUNGLINK" ; Risiko-Matrix-Header-Kollision (R3 S.7) | `table-layout:fixed` = GLEICHE Spaltenbreiten für 7-Spalten-Tabellen; lange Header ohne Trennstellen | `style_lint.harden_wide_tables()`: injiziert `<colgroup>` mit inhaltsbasierten Gewichten (schmal für Ampeln/Kürzel, breit für Fließtext) + kürzt Lang-Header (EINTRITTSWAHRSCHEINLICHKEIT→Eintritt, DSGVO-KONFORMITÄT→DSGVO, …); verdrahtet in strategy_renderer, report_renderer (Final-Pass) und gamechanger_deep_dive |
| Starter-Kit generisch (R1 S.15/16): „CRM-System", „Team-KI-Plattform" für eine Filmproduktion | Kits nur nach Größe, nicht nach Branche | `TOOL_TEMPLATES_MEDIA` (solo/team/kmu): Transkription/Untertitelung, Frame.io-Review, Schnitt-KI im Bestand, Footage-Archiv/MAM, Rechte-Register |
| Fast leere Seite 3 (R1): eine TOC-Zeile + Weißraum | Neues Rechte-Kapitel = 1 TOC-Zeile mehr als auf S. 2 passt | Selbstreferenzielle TOC-Einträge (Cover, Inhaltsverzeichnis) entfernt = 2 Zeilen frei |
| Doppelte Überschrift „Kernprogramme für Ihr Profil" + hängender „4."-Torso (R1 S.23–25) | Duplikat überlebte als Nicht-h3-Variante den h3-Strip; Healer-Trim ließ Aufzählungs-Torso zurück | Heading-Strip auf h2–h4 + `<p><strong>`-Pseudo-Überschriften + nackten Text erweitert; Regex tilgt einsame Zähler-Absätze am Prose-Ende |
| „30-Tage Challenge" endet bei Tag 23 (R1 S.17) | Woche-1-Drop für Intermediate renummeriert auf 1–23, Titel blieb „30 Tage" | Titel dynamisch („Ihre 23-Tage KI-Challenge") + Subtitle-Hinweis „Grundlagen-Woche übersprungen" |
| Gemischte Sprache „KI-Relevanz: medium/high" (R1 S.23) | 13 Medien-Programme trugen englische `relevance_ki`-Werte | auf Sehr hoch/Hoch/Mittel/Niedrig eingedeutscht |

### Runde 3 (KIS-1247, dieser PR) — LOW-Punkte + Feinschliff

| Punkt | Fix |
|---|---|
| Quick-Wins-Überschrift verwaist (R1 S.9) | `#quick-wins-section { break-before: page }` — deterministischer Kapitelanfang (Muster wie #aiact-compact) |
| Quellen-Spill-Seiten (R2 S.32/36) | `.sources-footer`: intern umbrechbar + klebt am vorigen Inhalt (`break-inside:auto`, `break-before:avoid-page`) |
| Roadmap ignorierte Zeitrahmen „3–6 Monate" (R2 Kap. 5/6) | `phase_windows()` leitet Phasen-Fenster aus s2_zeitrahmen ab (3/6/12/18-Monats-Raster); 12 Hardcodes in strategy_prompts ersetzt + verbindliche Horizont-Direktive |
| Konservativ −48 % ohne Einordnung (R1 S.13) | Bedingte Einordnungs-Box unter den Szenario-Karten (negativer Jahr-1-ROI = Amortisation im 2. Jahr, kein Verlustgeschäft) |
| Deploy killt laufende Läufe (600 s tote Statusseite) | Graceful Drain: SIGTERM-Handler gibt das laufende Briefing sofort wieder frei (status=accepted), neuer Container übernimmt ohne Stale-Timeout; Doppel-Lauf durch done-Race-Guard abgesichert |
| Sparten-Label fehlte auf dem Cover | Cover-Meta zeigt MEDIEN_SPARTE_LABEL („Film-/TV-Produktion") zwischen Branche und Größe |
| Nur 1 generischer Medien-Case | `FALLSTUDIEN_MEDIEN`-Pool: Doku-Produktion (Archiv), Werbefilm-Studio (Pitch-Sprint), Games-Studio (Lokalisierung) — sparten- und größen-aware, klar als fiktive Branchen-Beispiele gekennzeichnet |
| Badge-Leiste abmahnrelevant (KI-READY/DSGVO/AI-Act-Siegel selbst verliehen) | In allen 3 Templates entfernt; nur der reale TÜV-Personennachweis bleibt, mit Einordnung „Erstellt von Wolf Hohl · TÜV-zertifizierter KI-Manager"; „Live-Marktdaten"-Claim → „Marktdaten-Recherche vom …" |
| Vendor-Audit „0 % Compliance" wirkt wie K.-o. | Score-Kachel zeigt zusätzlich „mit AVV + Leitplanken erreichbar: X %"; rote Vendor-Karten mit verfügbarem AVV bekommen grünen „regelkonform einsetzbar"-Hinweis |

## Verifikation Runde 1

- Recommender: `medien/team/BE` → DFFF, Medienboard, Games-Bund, GMPF in Top 8;
  `beratung` → keine Medien-Programme (hart gefiltert). Tests 120/120 grün.
- Meta-Refusal-Gate erkennt die produktive Rückfrage aus KIS-1244, lässt echte Inhalte durch.
- KPI-Gates: ROI 1 % → Amortisation/Nettonutzen; ROI 75 % → unverändert. Jinja-Parse beider Templates grün.
