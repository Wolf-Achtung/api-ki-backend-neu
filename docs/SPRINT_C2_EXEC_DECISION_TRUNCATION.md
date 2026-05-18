# Sprint C2 — R1 Page 4 Executive-Decision Mid-Sentence Truncation

**Status:** H2/H3 Detect+Drop umgesetzt, Sprint-Constraint "H1 NICHT in diesem Sprint" eingehalten

**Auslöser:** R1-PDF KIS-1186 / Briefing 1069 zeigt auf Seite 4 ("Entscheidungsvorlage") einen Mid-Sentence-Cutoff:

> "Tun: Einen verbindlichen Standard-Arbeitsablauf einführen, bei dem jede Beratungsleistung den Ablauf Input"

Der "Tun"-Bullet endet ohne Punkt, ohne logischen Abschluss. Die nachfolgenden Bullets ("Lassen", "Risiko & Stop-Signal") enden korrekt mit "." — daher passt der Section-Last-Char-Check und der Bug rutschte durch die komplette Pipeline.

---

## Sektion 1: Diagnose-Befund

### 1.1 Production-Log-Signal

```
[FIX-C] Section 'executive_decision': removed 3 blocks, -801 chars
[PLATIN+++] Validation PASSED: 0 errors, 1 warnings
[PLATIN+++] WARNING: TRUNCATED: branch_deep_dive ends with '...'
```

Markant: **`branch_deep_dive`** wurde als TRUNCATED erkannt, **`executive_decision` NICHT** — obwohl beide mid-sentence enden. Keine `[FIX-G]`-, `[FIX-B38a]`- oder `[FIX-B39]`-Marker für `executive_decision`.

### 1.2 Root-Cause-Analyse: H2/H3 architektonische Lücke

Beide Mechanismen — `FIX-B38a`/`FIX-B39` Clean-Ending-Pass (`services/report_healer.py:3411 ff`) und PLATIN+++ `_check_sentence_completeness` (`services/report_validator.py:3486 ff`) — prüfen **nur das letzte Zeichen der gesamten Sektion**:

```python
# report_healer.py:3435
_b39_text = re.sub(r'</?\w+[^>]*>', '', _b39_content).rstrip()
if _b39_text[-1] not in _terminal_chars:  # checks SECTION terminus only
    ...
```

```python
# report_validator.py:3494
text = re.sub(r'<[^>]+>', '', html).strip()
if not text[-1] in '.!?:)"»”*':  # SECTION terminus only
    ...
```

Die Decision-Sektionen (`executive_decision`, `roadmap_90d_decision`, `gamechanger_decision`) folgen aber alle dem Output-Vertrag **"genau 3 `<li>`-Bullets, jeder ein vollständiger Satz"** (cf. `prompts/de/executive_decision.md` Z.93–98). Eine Truncation INNERHALB eines `<li>` wird vom Section-Level-Check NICHT erfasst, solange die nachfolgenden `<li>` mit `.` enden.

### 1.3 Wahrscheinliche Pipeline-Ursache (H1, Out-of-Scope dieses Sprints)

Token-Budget-Resolution für `executive_decision` (`gpt_analyze.py:1467 ff`):

| Kette | Wert |
|---|---|
| `_SECTION_MAX_TOKENS["executive_decision"]` | nicht definiert |
| Prompt-Kommentar `<!-- TOKEN-BUDGET: 400 -->` | nicht parser-genutzt |
| Fallback | `OPENAI_MAX_TOKENS_DEFAULT` = **3000** |

3000 Token reichen für 60–90 Wörter Prompt-Output. Beobachtet: LLM emittiert **>1500 Zeichen** (FIX-C entfernte 801 davon als Duplikate) — Hinweis darauf, dass das LLM den 60–90-Wort-Soft-Cap im Prompt regelmäßig verletzt und in Wiederholungen verfällt, bis `max_tokens` greift und mitten im Satz schneidet. **C2.2** wird über `[FIX-EXEC-DECISION-CLEAN]`-Marker-Daten priorisiert.

---

## Sektion 2: Patch (H2 + H3 kombiniert, Scope per Briefing)

### 2.1 Healer-Side (`services/report_healer.py`, +60 LOC nach FIX-B39-Block)

`[FIX-EXEC-DECISION-CLEAN]` iteriert über die drei Decision-Section-Keys (lower- + uppercase-Form), parst jedes `<li>` per Regex, prüft pro Bullet die letzte Zeichenposition. Truncierter Bullet wird ersetzt durch:

```html
<li><em>Weitere Punkte siehe Business Case und Roadmap.</em></li>
```

Marker emittiert pro Decision-Section auf Level `WARNING`:

```
[FIX-EXEC-DECISION-CLEAN] section=executive_decision total=3 truncated=1 dropped=1
```

Auf `DEBUG`-Level bei sauberer Sektion (für Sample-Bestätigung). Bewusst KEIN `briefing_id` im Marker — `run_id` ist im Healer-Scope nicht verfügbar; Korrelation läuft via Timestamp + sonstiger Run-Marker im selben Log-Block.

**Bullet-Drop ist intentional eine Vertragsverletzung:** Prompt fordert genau 3 Bullets mit fester Reihenfolge `Tun: / Lassen: / Risiko:`. Der Fallback-Bullet bricht diese Reihenfolge — sauberer als Anzeige eines abgehackten Satzes auf einer customer-facing Seite. Die Re-Gen-Logik in C2.2 wird das eleganter lösen.

**Schwellwert `len(bullet_text) < 25`:** Schützt vor False-Positives bei Mini-Labels wie `<li>Tun</li>` (Header-Pattern in einigen Templates). 25 Zeichen entspricht etwa 4–5 Worten — kürzere `<li>` sind statistisch keine vollständigen Sätze, sondern Labels.

### 2.2 Validator-Side (`services/report_validator.py`, +20 LOC in `_check_sentence_completeness`)

`PlatinValidator` führt vor dem Section-Level-Check einen Per-`<li>`-Check für die Decision-Sektionen durch und emittiert pro defektem Bullet:

```
TRUNCATED_LI: executive_decision bullet ends with '...jede Beratung den Ablauf Input'
```

`TRUNCATED_LI` ist absichtlich ein **eigener Warning-Code** (nicht `TRUNCATED`), damit Production-Log-Filter beide Failure-Modi separat zählen können.

### 2.3 Tests (`tests/test_exec_decision_clean.py`, 8 Tests)

| Test | Verifikation |
|---|---|
| `test_truncated_bullet_dropped_and_replaced` | KIS-1186-Reproduktion 1:1 |
| `test_clean_section_unchanged` | Keine Veränderung an sauberen Sektionen |
| `test_non_decision_section_ignored` | Nur die drei Decision-Sections werden bearbeitet |
| `test_short_bullet_below_threshold_preserved` | 25-Zeichen-Floor schützt Mini-Labels |
| `test_all_three_decision_sections_covered` | executive_decision + roadmap_90d_decision + gamechanger_decision |
| `test_truncated_li_emits_warning_despite_clean_section_end` | Validator-Hauptcase |
| `test_clean_section_no_truncated_li_warning` | Validator False-Positive-Schutz |
| `test_non_decision_section_not_checked_per_li` | Validator-Scope korrekt |

---

## Sektion 3: Empfehlung für Folge-Sprint C2.2

Nach Production-Smoke und Sammlung von `[FIX-EXEC-DECISION-CLEAN]`-Marker-Daten (mind. 48 h, ≥10 Briefings):

- **`truncated_rate > 5%`:** Sprint C2.2 anstoßen — Re-Gen-Logik analog `KI_STACK_SUMMARY` (`gpt_analyze.py:19630 ff`), wenn defekter Bullet erkannt → erneute LLM-Generierung mit niedrigerer Temperatur und tight `max_tokens` (z.B. 600).
- **`truncated_rate < 5%`:** Detect+Drop ist die finale Lösung. Marker bleibt für Monitoring.

Zusätzliche Folge-Themen (Out-of-Scope dieses Sprints):

- `executive_decision` in `_SECTION_MAX_TOKENS` aufnehmen mit explizitem Wert (z.B. 800) — verhindert über-generierung statt sie zu reparieren.
- `<!-- TOKEN-BUDGET: 400 -->` Prompt-Kommentar als Parser-honoriert implementieren oder entfernen (aktuell irreführend).

---

## Sektion 4: Validierungs-Plan nach Merge

1. Test-Briefing absenden (Solo + Beratung + `ki_kompetenz=hoch`, gleicher Profil-Schnitt wie 1069)
2. R1-PDF S.4 prüfen:
   - **Best Case:** Keine `[FIX-EXEC-DECISION-CLEAN]`-Marker → LLM lieferte sauber, Patch ungenutzt
   - **Healing Case:** Marker mit `truncated≥1`, S.4 zeigt Fallback-Bullet `"Weitere Punkte siehe Business Case und Roadmap"` an Position des defekten Bullets
3. Production-Logs nach beiden Markern filtern:
   - `[FIX-EXEC-DECISION-CLEAN]` (Healer)
   - `TRUNCATED_LI` (Validator-Warnings)
4. Nach 48 h: Rate berechnen und C2.2-Entscheidung treffen

---

## Sektion 5: Geänderte Dateien

| Datei | Δ |
|---|---|
| `services/report_healer.py` | +60 LOC (Per-`<li>`-Pass nach FIX-B39) |
| `services/report_validator.py` | +25 LOC (Per-`<li>`-Check in `_check_sentence_completeness`) |
| `tests/test_exec_decision_clean.py` | +144 LOC (8 Tests) |
| `docs/SPRINT_C2_EXEC_DECISION_TRUNCATION.md` | neu |

**Out-of-Scope:** H1 Re-Gen, S.5 "Fallstudie spart 15h"-Layout, S.11 Kosmetik (per Briefing).
