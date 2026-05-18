# Sprint C1 — Quick-Wins-Bug: Diagnose + Schema-Fix

**Status:** Diagnose abgeschlossen, trivialer Fix umgesetzt, Diagnose-Marker installiert für Folge-Sprint C1.2

**Auslöser:** R1-PDF zu Briefing 1068 (KIS-1185) zeigt auf Seite 7–8 Quick-Wins mit "Schritt 1./2./3.", leerem "IHR ENGPASS", leerem "Aktuell:", leerem "Mit KI:" und "Zeitersparnis: auf Anfrage" — obwohl der LLM-Output strukturierte JSON liefert.

**Hypothese vor Sprint:** Pipeline-Nullung oder unvollständige LLM-JSON. → **Beides falsch.**

---

## Sektion 1: Diagnose-Befund

### 1.1 Root Cause: Schema-Bruch zwischen Prompt und Legacy-Renderer

Der Quick-Wins-Codepfad hat zwei Renderer:

| Renderer | Position | Erwartetes Schema | Status |
|---|---|---|---|
| Premium (Primary) | `services/quickwins_renderer.py:795 render_quickwins_premium_json` | `title, icon, problem, wirkung, umsetzung, hinweis` | **stimmt mit Prompt überein** |
| Legacy (Fallback) | `gpt_analyze.py:4208 _parse_quick_wins_json` + `gpt_analyze.py:4314 _build_quick_wins_html` | `title, icon, time, engpass, description, mit_ki, steps, zeitersparnis` | **stimmt NICHT mit Prompt überein** |

Der Prompt (`prompts/de/quick_wins.md` Z.12–19, Output-Vertrag v8.3) fordert:
```
title, icon, problem, wirkung, umsetzung, hinweis
```

Der Legacy-Parser (vor Fix) erwartete:
```python
required_fields = ['title', 'icon', 'time', 'engpass', 'description', 'mit_ki', 'steps', 'zeitersparnis']
```

→ 6 von 8 Legacy-Feldern fehlen in **jeder** vom Prompt gelieferten JSON. Der Parser deklariert sie als "fehlend" und füllt mit hardcoded Defaults (`gpt_analyze.py:4291`):

```python
if field == 'steps':
    qw[field] = ["Schritt 1", "Schritt 2", "Schritt 3"]
elif field == 'icon':
    qw[field] = "◎"
else:
    qw[field] = ""
```

Der Legacy-Builder rendert dann eine Card mit leeren Blöcken plus den Hardcoded-Schritten — exakt das Briefing-1068-Symptom.

### 1.2 Wie die Pipeline tatsächlich Briefing 1068 produziert

1. LLM erzeugt JSON nach Output-Vertrag (`title/icon/problem/wirkung/umsetzung/hinweis`)
2. `_generate_content_sections` ruft `render_quickwins_premium_json` zuerst (`gpt_analyze.py:13135`) — der Primary-Pfad
3. Premium-Renderer schlägt aus noch unbekanntem Grund fehl (`return None`) → siehe Sektion 4
4. Codepfad fällt durch zu `_parse_quick_wins_json` (`gpt_analyze.py:13158`) — der Legacy-Fallback
5. Legacy-Parser sieht 6/8 erwartete Felder als "missing" → Hardcoded-Defaults greifen
6. `_build_quick_wins_html` rendert das User-sichtbare Bild aus Briefing 1068

Pristine-HTML enthält damit bereits Platzhalter, kein nachgelagerter Renderer-Bug.

### 1.3 Beobachtbare Lücken im Codepfad

| Code-Stelle | Lücke | Behoben in diesem Sprint |
|---|---|---|
| `gpt_analyze.py:4283` | `required_fields` = Legacy-Schema (8 Felder) statt Prompt-Schema (6 Felder) | ✅ Schema angeglichen |
| `gpt_analyze.py:4291` | Hardcoded `["Schritt 1", "Schritt 2", "Schritt 3"]`-Default | ✅ Entfernt (steps existiert im neuen Schema nicht) |
| `gpt_analyze.py:4314 ff` | Builder rendert nur Legacy-Felder, ignoriert `problem/wirkung/umsetzung/hinweis` | ✅ Conditional-Blocks für `problem/wirkung/umsetzung/hinweis` (analog Premium-Renderer) |
| `gpt_analyze.py:4759` | Minimal-QW-Build mit Legacy-Feldern bei Title-Extraction-Fallback | ✅ Auf Prompt-Schema umgestellt |
| `services/quickwins_renderer.py:795 ff` | Drei `return None`-Punkte ohne Diagnose-Log, kein Insight WARUM Primary fehlschlägt | ✅ `[QW-JSON-DEBUG]`-Marker an allen Failure- und Success-Pfaden |

---

## Sektion 2: Hypothesen für die Premium-Fehler-Ursache (offen für C1.2)

Mit dem Schema-Fix in diesem Sprint wird der Fallback-Pfad gesund. Aber: **warum greift der Fallback überhaupt für Briefing 1068, wenn der Premium-Renderer das richtige Schema versteht?** Diese Frage bleibt offen — der Diagnose-Marker in `render_quickwins_premium_json` wird sie nach Merge mit Production-Daten beantworten.

### H1 — JSON-Truncation durch max_tokens-Limit

Der Prompt setzt eine Höchstlänge von 6500 Zeichen pro JSON-Array. `gpt_analyze.py:1385` setzt `"quick_wins": 5000` als Token-Budget. Bei verbose Branchen-Spezial mit 4–5 Quick Wins à 1200 Zeichen kann der Output am Token-Limit abgeschnitten werden → `json.loads` schlägt fehl → Premium-Renderer returnt `None`.

- **Wahrscheinlichkeit:** hoch
- **Validierung:** Marker zeigt `status=fail reason=json_decode_error json_raw_chars=...` — wenn raw_chars nahe am 5000-Token-Output-Cap liegt, ist Truncation der Treffer.
- **Patch-Pfad (Folge-Sprint C1.2):** max_tokens für QW erhöhen, **oder** Streaming-Parse mit Recovery für truncated arrays, **oder** Re-Gen-Logik analog `KI_STACK_SUMMARY` (`gpt_analyze.py:19630ff`).

### H2 — Leeres oder list-loses JSON-Objekt

Wenn das LLM trotz Prompt-Vertrag mit einem Object-Wrapper antwortet (`{"quick_wins": [...]}`), greift der Premium-Renderer's Array-Extract-Regex (`r'(\[[\s\S]*\])'`, Z.829) zwar — aber wenn das LLM komplett aus dem Output-Vertrag fällt (z.B. Markdown-Erklärung statt JSON), returnt der Renderer mit `data isinstance check` failure.

- **Wahrscheinlichkeit:** mittel
- **Validierung:** Marker zeigt `status=fail reason=not_a_list` oder `empty_array`.
- **Patch-Pfad:** Prompt-Hardening (Output-Vertrag steht bereits klar in Z.5–10 von `prompts/de/quick_wins.md`, mehr ist schwierig); alternativ Object-Wrapper-Detection wie in `_parse_quick_wins_json:4272`.

### H3 — Validation-Gate `enforce_quickwins_complete` produziert leere cards_html

`enforce_quickwins_complete` (`services/quickwins_renderer.py:611`) füllt leere Felder mit deterministischen Fallbacks. Wenn aber **alle** QWs als `not isinstance(qw, dict)` durchfallen (z.B. wenn LLM ein verschachteltes JSON liefert), endet `cards_html` leer → `return None` (Z.904).

- **Wahrscheinlichkeit:** niedrig
- **Validierung:** Marker zeigt `status=fail reason=no_valid_cards` und im vorgelagerten Log `status=parsed item_count=N` mit hohem N.
- **Patch-Pfad:** Defensive Type-Coercion in `enforce_quickwins_complete`.

---

## Sektion 3: Empfehlung

**Diesen Sprint mergen** — er fixt die User-sichtbaren Symptome aus Briefing 1068 sofort (Schema-Angleichung), und der Diagnose-Marker sammelt parallel WHY-Daten für den Folge-Sprint.

**Folge-Sprint C1.2:** Nach 24–48 h Production-Marker-Daten den häufigsten `fail reason` identifizieren und gezielt patchen. Wahrscheinlichkeitsreihenfolge:

1. **H1 (Truncation)** zuerst prüfen — höchste Vermutung, einfacher Patch (max_tokens hoch).
2. **H3 (Validation-Gate)** zweite Prüfung — Defensive-Coercion ist trivial.
3. **H2 (LLM-Vertragsbruch)** dritte Prüfung — wenn 1+3 nicht erklären, Prompt-Iteration.

**Optionaler Folge-Sprint C1.3 (Tech-Debt):** Legacy-Parser+Builder komplett entfernen, Premium-Renderer wird Primary und einziger Pfad. Bedingt durch C1.2 (erst wenn Premium-Failover-Rate gegen 0 geht). Tests `tests/test_finalD_quickwins_no_raw_json.py`, `tests/test_finalG_quickwins_hardcorrect.py`, `tests/test_p07_quickwins_canonical.py` müssen dann mitwandern oder gelöscht werden (sie referenzieren `_calculate_quickwin_savings_display` und `_sanitize_quickwin_step`, die nach dem Aufräumen verschwinden).

---

## Sektion 4: Validierung der Diagnose-Marker

### Marker-Format

`render_quickwins_premium_json` loggt auf Level `INFO` mit folgenden Status-Werten:

| `status` | Bedeutung | Felder |
|---|---|---|
| `ok` | HTML-Rendering erfolgreich | `json_raw_chars`, `item_count`, `total_words`, `mode` |
| `parsed` | JSON geparst, Schema-Check abgeschlossen, vor Completeness-Gate | `json_raw_chars`, `item_count`, `fields_missing_per_qw` |
| `fail reason=empty_input` | `raw_json` war leer oder nur Whitespace | `json_raw_chars` |
| `fail reason=not_a_list` | Geparstes JSON war kein Array | `json_raw_chars`, `item_count` |
| `fail reason=empty_array` | Geparstes JSON war leeres Array | `json_raw_chars`, `item_count` |
| `fail reason=no_valid_cards` | Alle Items waren keine Dicts oder durchgefallen | `json_raw_chars`, `item_count` |
| `fail reason=json_decode_error` | `json.loads` warf JSONDecodeError | `json_raw_chars`, `err` |
| `fail reason=exception` | Anderer Fehler im Render-Pfad | `json_raw_chars`, `err_type`, `err` |

`_parse_quick_wins_json` loggt parallel auf Level `INFO`:
```
[QW-JSON-DEBUG] parser=legacy qw_count=N json_raw_chars=M fields_missing_per_qw=[...]
```
→ Zeigt, ob nach Schema-Fix der Legacy-Pfad noch Felder fehlen sieht. Wenn `fields_missing_per_qw` durchgehend leere Listen sind, deckt der Prompt das neue Schema vollständig ab.

### Keine Roh-JSON-Inhalte

Bewusst KEIN Roh-JSON, KEINE Textfeld-Inhalte gelogged. Nur Counts, Feldnamen, Fehlertypen — datenschutz-tauglich für Production-Logs.

### Validierungs-Plan nach Merge

1. Test-Briefing (Solo + Beratung + `ki_kompetenz=hoch`) absenden, der für Briefing 1068 reproduziert wurde
2. Production-Logs nach `[QW-JSON-DEBUG]` filtern
3. Erwartung nach Schema-Fix:
   - **Best case (Premium greift):** `status=ok` Marker erscheint, R1-PDF S.7–8 zeigt echte QW-Inhalte
   - **Failover-Fall (Legacy greift):** `status=fail reason=X` Marker zeigt konkreten Premium-Fehler; daraufhin loggt `parser=legacy` den Fall — und R1-PDF S.7–8 zeigt die echten Prompt-Felder (problem als Engpass-Box, wirkung+umsetzung als Body, hinweis als Tipp), weil der Legacy-Pfad jetzt schema-konsistent ist
4. Häufigsten `fail reason=X` als Treiber für C1.2 identifizieren

---

## Sektion 5: Geänderte Zeilen (für Reviewer)

| Datei | Zeilen | Δ | Beschreibung |
|---|---:|---:|---|
| `gpt_analyze.py` | 4283–4316 | +18 / −13 | `required_fields` angeglichen; Hardcoded-Defaults entfernt; `[QW-JSON-DEBUG]` Legacy-Marker |
| `gpt_analyze.py` | 4361–4438 | +43 / −62 | `_build_quick_wins_html` Render-Body komplett auf Prompt-Schema (Conditional-Blocks für `problem/wirkung/umsetzung/hinweis`) |
| `gpt_analyze.py` | 4762–4768 | +6 / −2 | Title-Extraction-Fallback nutzt jetzt Prompt-Schema |
| `services/quickwins_renderer.py` | 795–812 | +1 | `run_id`-Parameter, optional |
| `services/quickwins_renderer.py` | 812–820 | +7 | Marker für `empty_input` |
| `services/quickwins_renderer.py` | 835–845 | +9 | Marker für `not_a_list` / `empty_array` |
| `services/quickwins_renderer.py` | 850–862 | +14 | `[QW-JSON-DEBUG] status=parsed` mit `fields_missing_per_qw` vor Completeness-Gate |
| `services/quickwins_renderer.py` | 920–925 | +5 | Marker für `no_valid_cards` |
| `services/quickwins_renderer.py` | 957–975 | +14 | Marker für `ok` und Exception-Branches |

**Helper-Funktionen `_calculate_quickwin_savings_display` und `_sanitize_quickwin_step`** bleiben **unverändert** in `gpt_analyze.py`, obwohl der neue Render-Code sie nicht mehr aufruft. Grund: `tests/test_finalD_quickwins_no_raw_json.py`, `tests/test_finalG_quickwins_hardcorrect.py`, `tests/test_p07_quickwins_canonical.py` importieren sie. Aufräumen erfolgt im optionalen Sprint C1.3 zusammen mit den Tests.

---

## Sektion 6: Out of Scope für diesen Sprint

- **WHY-Diagnose des Premium-Fehlers** — passiert nach Merge via Marker in Production
- **Re-Gen-Logik bei truncated JSON** — Folge-Sprint C1.2, abhängig von Marker-Befund
- **Legacy-Code-Entfernung** — Folge-Sprint C1.3 nach Premium-Stabilisierung
- **Prompt-Iteration** — Output-Vertrag steht bereits klar; Änderungen nur bei H2-Befund
