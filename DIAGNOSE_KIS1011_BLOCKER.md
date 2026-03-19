# Diagnose-Ergebnis: KIS-1011 — 3 Blocker aus Qualitätsprüfung

**Briefing:** 894 | **Profil:** KMU (11–100) · Marketing/AV-Produktion · Bayern · Score 91
**Validation:** PLATIN++ / G22 Grade A (100.0)
**Datum:** 2026-03-19

---

## B1 Diagnose-Ergebnis: „Ich haben" in R1 Fallstudie (Seite 7)

- **Fundort:** `services/sofort_start_generator.py:1923`
- **Typ:** Hardcodierter Python-String (Dictionary `FALLSTUDIEN`, Branche `"marketing"`, Key `"zitat"`)
- **Aktueller Text im Code:** `"Wir haben keinen Mitarbeiter eingestellt, sondern KI. Beste Entscheidung."`
- **Text im PDF (laut QA):** `"Ich haben keinen Mitarbeiter eingestellt, sondern KI."`

### Diskrepanz: Code hat "Wir haben" (korrekt), PDF zeigt "Ich haben" (falsch)

Der Quellcode enthält das grammatisch korrekte **"Wir haben"** (Zeile 1923). Im PDF erscheint jedoch **"Ich haben"** — d.h. "Wir" wurde zu "Ich" transformiert, **ohne** die Verbkonjugation anzupassen ("haben" → "habe").

### Root-Cause-Analyse

1. **Kein expliziter "Wir→Ich"-Replacer gefunden:** In der gesamten Codebase gibt es keinen Regex oder String-Replace, der "Wir" systematisch durch "Ich" ersetzt.

2. **Solo Language Normalizer** (`content_quality_enforcer.py:343`): Ersetzt Enterprise-Begriffe (Stakeholder, Rollout, etc.) durch Solo-freundliche Alternativen. SOFORT_START_HTML ist im Scope (Zeile 379). **Aber:** Der Normalizer greift nur bei `company_size == "solo"` (Zeile 417). Für KMU (11–100) wird er übersprungen.

3. **Wahrscheinlichster Root Cause:** Die LLM-basierte Postprocessing-Pipeline. Die SOFORT_START_HTML-Section durchläuft mehrere Nachbearbeitungsschritte:
   - Grammar-Sanitizer (`content_quality_enforcer.py`)
   - Text-Glitch-Fixer
   - Siezen-Guard
   - Global Truncation

   Keiner dieser Schritte sollte "Wir" → "Ich" ersetzen. **Mögliche Erklärungen:**
   - **Ältere Code-Version:** Briefing 894 wurde möglicherweise mit einer früheren Version generiert, die "Ich haben" im Dictionary hatte.
   - **LLM-Rewrite:** Ein nachgelagerter LLM-Aufruf (z.B. Executive Narrative Engine) könnte das Zitat paraphrasiert haben und dabei "Wir" → "Ich" geändert, ohne die Konjugation anzupassen.

- **Grammar-Sanitizer-Scope:** SOFORT_START_HTML wird durchlaufen (Zeile 379), aber der Sanitizer enthält keine Regel für "Ich haben" → "Ich habe". Die 6 gemeldeten Fixes betrafen andere Patterns.

### Offene Frage

Der aktuelle Code (Stand heute) enthält "Wir haben" (korrekt). Ob Briefing 894 mit einer älteren Version generiert wurde, lässt sich nur über die gespeicherte HTML in der Datenbank klären (API-Abfrage auf Production).

---

## B2 Diagnose-Ergebnis: „Vorhabe ichtschaftlich" in R1 Förderprogramme (Seite 20)

- **Fehler im HTML:** Ja (mit hoher Wahrscheinlichkeit — entsteht vor PDF-Rendering)
- **Fehler im PDF erst:** Nein
- **Fundort:** Section `FOERDERPOTENZIAL_HTML`, LLM-generierter Content
- **Typ:** LLM-Output (nicht Template)
- **Root Cause:** LLM-Token-Grenze ODER Python-seitige Zeichen-Trunkierung

### Analyse

1. **"Vorhaben wirtschaftlich" ist NICHT im Template hardcodiert.** Die Prompt-Datei `prompts/de/foerderpotenzial.md` enthält nur "Vorhaben" (Zeile 179, 206) ohne "wirtschaftlich". Die vollständige Phrase wird vom LLM frei generiert.

2. **Zwei mögliche Trunkierungspfade identifiziert:**

   **Pfad A — LLM-Token-Limit (wahrscheinlicher):**
   - `gpt_analyze.py:2318-2320`: Wenn `finish_reason == "length"`, wurde der LLM-Output am Token-Limit abgeschnitten.
   - Token-Grenzen stimmen nicht mit Zeichengrenzen überein → "Vorhaben wirtschaftlich" kann mitten im Token getrennt werden → "Vorhabe" + "[nächster Token]ichtschaftlich"
   - Die fehlenden Zeichen "n w" (2 Zeichen) passen zu einem Token-Grenzphänomen.

   **Pfad B — Python-seitige Character-Truncation:**
   - `gpt_analyze.py:13789-13905`: FOERDERPOTENZIAL_HTML ist in der `truncation_targets`-Liste.
   - Budget-basierte Trunkierung: `html[:_budget]` (Zeile 13865, 13890) schneidet am Zeichen-Index ab.
   - FIX-B4 (Zeile 13866-13877) versucht, an Satzgrenzen zu schneiden, aber fällt auf Raw-Cut zurück, wenn keine Grenze in den letzten 30% gefunden wird (Zeile 13883).
   - Prompt-Limits: Solo 4.500 / Team 7.500 / KMU 10.000 Zeichen (`prompts/de/foerderpotenzial.md:8-13`)

3. **Beteiligte Sanitizer:**
   - `services/html_sanitizer.py`: UTF-8 Mojibake-Fixing (Zeilen 36-109), doppelt-escapte Entities (1385-1415) — könnten Artefakte maskieren, aber verursachen sie nicht.
   - `cleanup_truncation_artifacts()` (`content_quality_enforcer.py`): Wird nach Trunkierung aufgerufen (Zeile 13858-13859), repariert aber nur bekannte Patterns.

### Fazit

Der Fehler entsteht **im HTML** (nicht erst im PDF). Root Cause ist mit >80% Wahrscheinlichkeit **LLM-Token-Limit-Truncation** (Pfad A), da:
- Die Phrase 2x auf derselben Seite vorkommt (systematisch, nicht zufällig)
- Der Fehlermodus (fehlende "n w") typisch für Token-Grenzen ist
- KMU-Profil hat 10.000 Zeichen Budget (großzügig), daher ist Python-seitige Trunkierung weniger wahrscheinlich

---

## B3 Diagnose-Ergebnis: Fehlender ROI-Wert in Realistisch-Szenario-Karte (Seite 12)

- **Template-Datei:** `services/business_case_engine_v2.py:2134-2173`
- **ROI-Daten vorhanden:** Ja (mit Sicherheit — die Engine berechnet ROI für alle 3 Szenarien identisch)
- **Realistisch-Karte HTML-Struktur:** **Identisch** mit Optimistisch und Konservativ
- **Root Cause:** CSS/PDF-Rendering-Bug (NICHT Template oder Daten)

### Analyse

1. **Template ist identisch für alle 3 Karten:**
   - `business_case_engine_v2.py:2134`: `for scenario in report.scenarios:` — eine einzige Schleife generiert alle 3 Karten.
   - ROI-Rendering: Zeile 2154-2155 — `{labels["roi_label"]}` + `{_display_roi:.0f}%` — KEIN bedingter Code, der ROI für "realistic" überspringt.
   - Die HTML-Struktur ist für alle Karten pixelgenau identisch:
     ```
     ROI (12M) Label → ROI Wert (24pt, fett)
     Amortisation Label → Amortisation Wert
     Monatl. Ersparnis Label → Ersparnis Wert
     Investition Label → Investition Wert
     ```

2. **ROI-Daten sind immer vorhanden:**
   - `ScenarioKPIs.__post_init__` (Zeile 915): `self.roi_12m = max(MIN_ROI, min(MAX_ROI, self.roi_12m))` — ROI wird immer auf [MIN_ROI, MAX_ROI] geclippt.
   - Validierung (Zeile 1192-1195): `if real.roi_12m <= 0.0: errors.append(...)` — ein fehlender/negativer ROI würde als CRITICAL Error geloggt.
   - Healing (Zeile 1246-1257): Wenn ROI ≤ 0 bei positiven Savings, wird er automatisch repariert.

3. **Kein Postprocessor modifiziert die Szenario-Karten:**
   - Die Section `BUSINESS_CASE_ENGINE_HTML` wird in `gpt_analyze.py:15903` gespeichert und danach nicht durch Truncation, Grammar-Sanitizer oder andere Postprocessoren verändert.
   - Die Section ist NICHT in `truncation_targets` (Zeile 13789-13794).

4. **Wahrscheinlichster Root Cause — CSS/PDF-Rendering:**
   - Die 3 Karten verwenden `display:flex;gap:12px;flex-wrap:wrap;` (Zeile 2131).
   - Jede Karte: `flex:1;min-width:180px;` (Zeile 2147).
   - Der ROI-Wert hat `font-size:24pt;font-weight:700;` (Zeile 2155) — die größte Schriftgröße in der Karte.
   - **Hypothese:** Bei der mittleren Karte (Realistisch) in der Flex-Reihe kommt es zu einem Layout-Overflow oder Page-Break, der das ROI-Element visuell abschneidet. Die anderen Karten (links/rechts) sind nicht betroffen, weil der Overflow nur die Mitte trifft.
   - **Alternative Hypothese:** `page-break-inside: avoid` fehlt für `.scenario-card` in `templates/pdf_template_v7.html`. Wenn ein Seitenumbruch mitten durch die Karte geht, fällt der ROI-Block (oberstes Element nach dem Label) auf die vorherige Seite, während der Rest auf der nächsten Seite erscheint.

### Empfohlene Verifikation

Zur endgültigen Bestätigung:
1. HTML von Briefing 894 abrufen und die 3 Karten vergleichen (alle sollten ROI enthalten)
2. PDF mit anderem Renderer erzeugen (z.B. Chrome Print statt wkhtmltopdf)
3. `page-break-inside: avoid` für `.scenario-card` in der PDF-CSS testen

---

## Zusammenfassung

| Blocker | Typ | Root Cause | Fix-Aufwand |
|---------|-----|-----------|-------------|
| B1 | Code-Diskrepanz | Code hat "Wir haben" (korrekt). PDF-Fehler "Ich haben" vermutlich aus älterer Version oder LLM-Rewrite. Defensiver Fix: "Ich habe" als Grammar-Regel hinzufügen | Klein (1 Zeile Regex) |
| B2 | LLM-Truncation | LLM-Token-Limit schneidet "Vorhaben wirtschaftlich" ab. Python-Truncation (Fallback) hat keine Wortgrenzen-Reparatur | Mittel (Token-Budget erhöhen + Wortgrenz-Truncation) |
| B3 | CSS/PDF-Rendering | Template ist identisch für alle 3 Karten. ROI-Daten sind vorhanden. Flex-Layout + fehlende `page-break-inside: avoid` | Klein (1 CSS-Regel) |
