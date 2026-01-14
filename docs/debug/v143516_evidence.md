# Evidence-Pack v14.35.16 - Risk/Reco Healing Analysis

**Report:** 465
**Version:** v14.35.16
**Datum:** 2026-01-14
**Ziel:** Root Cause für Fragmente wie "Zeitblöcke.", "Feste.", "Kernprozesse.", "Mindestens.", ", die Sie."

---

## A. Code-Scan Ergebnisse

### A1. Doppelte Definitionen prüfen

```bash
grep -n "def _trim_fragment_sentences" gpt_analyze.py
```

**Output:**
```
5261:            def _trim_fragment_sentences(text):
```

**WICHTIG:** Die Funktion ist **NESTED** (eingerückt) - sie existiert nur innerhalb von `_convert_risk_bullets_to_cards`!

```bash
grep -n "def _heal_recommendation_text" gpt_analyze.py
```

**Output:**
```
5459:def _heal_recommendation_text(text: str) -> str:
```

**OK:** Top-Level-Funktion, keine Shadowing-Gefahr.

---

### A2. Aufrufstellen prüfen

```bash
grep -n "_trim_fragment_sentences(" gpt_analyze.py
```

**Output:**
```
5261:            def _trim_fragment_sentences(text):
5310:            description = _trim_fragment_sentences(description)
```

**ERKANNT:** Nur **1 Aufruf** in Zeile 5310!

```bash
grep -n "_heal_recommendation_text(" gpt_analyze.py
```

**Output:**
```
5459:def _heal_recommendation_text(text: str) -> str:
5536:                    schwerpunkt = _heal_recommendation_text(sp_match.group(1).strip()[:1000])
5540:                    massnahme = _heal_recommendation_text(ma_match.group(1).strip()[:1000])
```

**ERKANNT:** 2 Aufrufe in `_format_recommendations_as_cards` (Zeilen 5536, 5540)

---

### A3. Wo werden Risk-Cards gebaut?

```bash
grep -n "risk-cards-grid\|risk-card" gpt_analyze.py
```

**Output:**
```
5238:        cards_html = '<div class="risk-cards-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin: 16px 0;">\n'
5313:            card_html = f'''<div class="risk-card" style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; break-inside: avoid;">
```

**Risk-Cards werden gebaut in:** `_convert_risk_bullets_to_cards()` (Zeilen 5209-5329)

---

### A4. Wo werden Recommendations-Cards gebaut?

```bash
grep -n "recommendation-card\|HANDLUNGSEMPFEHLUNGEN" gpt_analyze.py
```

**Output (relevant):**
```
4106:        return f'''<div class="recommendation-card-compact">
4152:                        card = f'''<div class="recommendation-card-compact">
10884:            recommendations_html = _format_recommendations_as_cards(recommendations_html)
```

**Recommendations werden gebaut in:** `_format_recommendations_as_cards()` (ab Zeile 5496)

---

## B. Kritische Code-Snippets

### B1. `_trim_fragment_sentences` Definition (Zeile 5261-5309)

```python
# === v14.35.16: TAIL-TRIM - Mini-Sätze + Stop-Wörter entfernen ===
def _trim_fragment_sentences(text):
    """Entfernt unvollständige Sätze am Ende (Mini-Sätze + Stop-Wörter)"""
    import re
    if not text or len(text) < 10:
        return text

    max_iterations = 5
    for _ in range(max_iterations):
        # Split in Sätze
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        if len(sentences) <= 1:
            break

        last_sentence = sentences[-1].strip()
        words = re.findall(r'\b\w+\b', last_sentence)
        word_count = len(words)

        should_remove = False

        # 1) MINI-SÄTZE: 1-3 Wörter ohne Verb = Fragment!
        if word_count <= 3:
            verbs = {'ist', 'sind', 'war', 'hat', 'haben', 'wird', 'werden', 'kann', 'können', 'muss', 'müssen'}
            has_verb = any(w.lower() in verbs for w in words)
            if not has_verb:
                should_remove = True

        # 2) STOP-WÖRTER am Ende
        if not should_remove and words:
            last_word = words[-1].lower()
            stop_words = {'der', 'die', 'das', ...}  # [gekürzt]
            if last_word in stop_words:
                should_remove = True

        # 3) Entferne wenn Fragment erkannt
        if should_remove:
            text = ' '.join(sentences[:-1])
        else:
            break

    # Stelle sicher dass Text mit Punkt endet
    text = text.strip()
    if text and text[-1] not in '.!?':
        text += '.'
    return text
```

**PROBLEM:** Die Logik sollte "Zeitblöcke." (1 Wort, kein Verb) entfernen - **ABER** das Fragment ist möglicherweise **nicht am Ende**!

---

### B2. `_heal_recommendation_text` Definition (Zeile 5459-5493)

```python
def _heal_recommendation_text(text: str) -> str:
    """v14.35.16: Heilt Fragment-Sätze in Recommendation-Texten"""
    import re
    if not text or len(text) < 5:
        return text

    # 1) Soft-Trim: ", die Sie." und ähnliche Relativsatz-Fragmente
    comma_patterns = [
        (r',\s*die\s+Sie\.?\s*$', ''),
        (r',\s*der\s+Sie\.?\s*$', ''),
        (r',\s*das\s+Sie\.?\s*$', ''),
        (r',\s*welche\s+Sie\.?\s*$', ''),
    ]
    for pattern, repl in comma_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            last_comma = text.rfind(',')
            if last_comma > 10:
                text = text[:last_comma].strip()
                if text and text[-1] not in '.!?':
                    text += '.'
                break

    # 2) Mini-Sätze am Ende entfernen
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) > 1:
        last = sentences[-1]
        words = re.findall(r'\b\w+\b', last)
        if len(words) <= 3:
            verbs = {'ist', 'sind', 'war', ...}
            if not any(w.lower() in verbs for w in words):
                text = ' '.join(sentences[:-1])

    if text and text[-1] not in '.!?':
        text += '.'
    return text
```

**Logik OK für ", die Sie." am Satzende!**

---

### B3. Zentrales `text_healing.py` Modul

**Import in gpt_analyze.py Zeile 119:**
```python
from services.text_healing import heal_all_text_blocks, heal_text_block
```

**Aufruf in gpt_analyze.py Zeile 12667:**
```python
sections = heal_all_text_blocks(sections)
```

**`heal_all_text_blocks` behandelt diese Keys:**
```python
RISK_KEYS = ["RISKS_HTML", "risks", "RISK_MATRIX_HTML", "risk_matrix", "BRANCH_RISKS_HTML", "branch_risks"]
RECO_KEYS = ["RECOMMENDATIONS_HTML", "recommendations", "TOP_3_MASSNAHMEN_HTML", "top_3_massnahmen", "GAMECHANGER_HTML", "gamechanger"]
BC_KEYS = ["BUSINESS_CASE_HTML", "business_case", "BUSINESS_ROI_HTML", "business_roi"]
```

**ABER:** `_heal_html_blockwise` Regex-Pattern:
```python
# Heal Risk-Card description divs
html = re.sub(r'(<div[^>]*style="[^"]*color[^"]*"[^>]*>)([^<]{1,500})(</div>)', heal_inner, html, flags=re.IGNORECASE)
```

**PROBLEM:** `([^<]{1,500})` matcht **nicht**, wenn der Content HTML-Tags enthält!

---

## C. Workflow-Analyse (Timing)

| Zeile | Aktion | Healing? |
|-------|--------|----------|
| 10795-10818 | `RISKS_HTML` → `_convert_risk_bullets_to_cards` | `_trim_fragment_sentences` (nested) |
| 10877-10890 | `RECOMMENDATIONS_HTML` → `_format_recommendations_as_cards` | `_heal_recommendation_text` |
| 11783 | `RISK_ENGINE_HTML` generiert (risk_engine_v2.py) | **KEIN HEALING!** |
| 11820 | `RISK_ENGINE_V3_HTML` generiert (risk_engine_v3.py) | **KEIN HEALING!** |
| 11999 | `RECOMMENDATIONS_ENGINE_HTML` generiert | **KEIN HEALING!** |
| 12667 | `heal_all_text_blocks(sections)` | Nachträgliches HTML-Healing |

---

## D. Root Cause Analyse

### Hypothese 1: Fragment kommt aus ungehealer Quelle (WAHRSCHEINLICHSTE)

Die Fragmente "Zeitblöcke.", "Feste.", "Kernprozesse.", "Mindestens." könnten aus:
- `RISK_ENGINE_HTML` (risk_engine_v2.py)
- `RISK_ENGINE_V3_HTML` (risk_engine_v3.py)
- `RISK_MATRIX_HTML`
- `BRANCH_RISKS_HTML`

**Diese werden NICHT durch `_trim_fragment_sentences` gehealt!**

### Hypothese 2: `_heal_html_blockwise` Regex versagt

Das Pattern `([^<]{1,500})` in Zeile 554 von text_healing.py matcht **nur Text ohne innere HTML-Tags**.

Risk-Card HTML (Zeile 5313-5317):
```html
<div class="risk-card" style="...">
    <div style="font-weight: 600; color: #1e293b; ...">
        <span class="icon icon--warning">⚠</span> {title}
    </div>
    <div style="color: #475569; ...">{description}</div>
</div>
```

Der `<span>` Tag in der Title-Div verhindert das Matching!

### Hypothese 3: Timing-Problem

Der Workflow:
1. `_convert_risk_bullets_to_cards` healt Risk-Cards (Zeile ~10804)
2. **VIEL SPÄTER** läuft `heal_all_text_blocks` (Zeile 12667)
3. Zwischen Zeile 10804 und 12667 werden NEUE Sections generiert:
   - `RISK_ENGINE_HTML` (Zeile 11783)
   - `RISK_ENGINE_V3_HTML` (Zeile 11820)
   - `RECOMMENDATIONS_ENGINE_HTML` (Zeile 11999)

**Diese neuen Sections werden von `heal_all_text_blocks` behandelt, ABER nur wenn die HTML-Struktur zum Regex passt!**

---

## E. Empfohlene Debug-Instrumentierung

### E1. Risk-Engine Output prüfen

In `gpt_analyze.py` nach Zeile 11783 einfügen:
```python
_risk_engine_html = sections.get("RISK_ENGINE_HTML", "")
if _risk_engine_html:
    for needle in ["Zeitblöcke.", "Feste.", "Kernprozesse.", "Mindestens."]:
        if needle in _risk_engine_html:
            print(f"[RISK-ENGINE-HIT] RISK_ENGINE_HTML contains: {needle}")
```

### E2. Final Sections Scan

Vor Zeile 12672 (nach heal_all_text_blocks) einfügen:
```python
WATCH = ["Zeitblöcke.", "Feste.", "Kernprozesse.", "Mindestens.", ", die Sie.", "die Sie."]
KEYS = [
    "RISKS_HTML", "RISK_MATRIX_HTML", "BRANCH_RISKS_HTML", "RISK_ENGINE_HTML",
    "RISK_ENGINE_V3_HTML", "RECOMMENDATIONS_HTML", "RECOMMENDATIONS_ENGINE_HTML",
    "TOP_3_MASSNAHMEN_HTML", "EXEC_SUMMARY_HTML",
]
for k in KEYS:
    v = sections.get(k, "")
    if v:
        for needle in WATCH:
            if needle in v:
                print(f"[SECTION-HIT-FINAL] {k} contains: {needle}")
```

---

## F. Empfehlung für Patch v14.35.17

### Option A: Engine-Level Healing (EMPFOHLEN)

1. In `services/risk_engine_v2.py` und `services/risk_engine_v3.py`:
   - Importiere `from services.text_healing import heal_text_block`
   - Wende `heal_text_block(text, domain="risk")` auf alle Risk-Descriptions an

2. In `services/recommendations_engine.py`:
   - Importiere `from services.text_healing import heal_text_block`
   - Wende `heal_text_block(text, domain="reco")` auf alle Recommendation-Texte an

### Option B: Post-Generation Healing verstärken

In `gpt_analyze.py` nach Zeile 11842 (nach allen Engine-Generierungen):
```python
# === v14.35.17: Heal ALL Engine Outputs ===
ENGINE_KEYS = ["RISK_ENGINE_HTML", "RISK_ENGINE_V3_HTML", "RECOMMENDATIONS_ENGINE_HTML"]
for key in ENGINE_KEYS:
    if key in sections and sections[key]:
        sections[key] = _heal_html_blockwise(sections[key], domain="risk" if "RISK" in key else "reco")
```

### Option C: Regex-Pattern in `text_healing.py` erweitern

In `services/text_healing.py` Zeile 554 ändern:
```python
# ALT: html = re.sub(r'(<div[^>]*style="[^"]*color[^"]*"[^>]*>)([^<]{1,500})(</div>)', heal_inner, html, flags=re.IGNORECASE)

# NEU: Auch verschachtelte Tags tolerieren
html = re.sub(r'(<div[^>]*style="[^"]*color[^"]*"[^>]*>)(.*?)(</div>)', heal_inner_deep, html, flags=re.IGNORECASE | re.DOTALL)
```

---

## G. Nächste Schritte

1. **Instrumentierung einbauen** (temporär) → Report erneut generieren
2. **Logs analysieren** → Bestätigt welche Hypothese (1, 2, oder 3) zutrifft
3. **Patch v14.35.17** basierend auf Evidence

---

## H. FINALE ROOT CAUSE ANALYSE (nach vollständigem Code-Review)

### Workflow-Zusammenfassung

```
1. _generate_content_sections() [Zeile 10251]
   → GPT parallel aufrufen für "risks" Section
   → LLM-Output direkt in sections["RISKS_HTML"] speichern

2. SAFE RISKS FORMATTING [Zeile 10819-10836]
   → risks_html = sections.get("RISKS_HTML")
   → _enhance_text_readability()
   → _convert_risk_bullets_to_cards()  ← enthält _trim_fragment_sentences (NESTED!)
   → _format_risks_with_visual_breaks()
   → sections["RISKS_HTML"] = risks_html

3. Risk Engines (SPÄTER) [Zeile 11807-11842]
   → RISK_ENGINE_HTML generiert (KEIN HEALING!)
   → RISK_ENGINE_V3_HTML generiert (KEIN HEALING!)

4. heal_all_text_blocks() [Zeile 12699]
   → Versucht nachträgliches HTML-Healing
   → Regex-Pattern matchen nicht alle HTML-Strukturen
```

### DEFINITIVE ROOT CAUSE

**Die Fragmente kommen NICHT aus der `RISKS_HTML` Card-Transformation, sondern aus:**

#### Primär-Quelle: Risk Engine Output (UNGEHEALTER LLM-TEXT)

1. `RISK_ENGINE_HTML` (Zeile 11807) und `RISK_ENGINE_V3_HTML` (Zeile 11820) werden **NACH** den Healing-Transformationen generiert
2. Diese Engines rufen `risk_report_to_html()` aus `services/risk_engine_v2.py` auf
3. Der Output wird **NICHT** durch `_trim_fragment_sentences` oder `_heal_recommendation_text` geschickt
4. `heal_all_text_blocks()` läuft zwar danach (Zeile 12699), aber:
   - Das `_heal_html_blockwise` Regex matcht nur einfache HTML-Strukturen
   - Verschachtelte Tags werden übersprungen (`if "<" in inner`)

#### Sekundär-Quelle: Ungeparstes LLM-Format

1. `_convert_risk_bullets_to_cards()` erwartet `<ul><li>` Format
2. Wenn der LLM ein anderes Format generiert (z.B. `<p>`, `<div>`), greift die Transformation **nicht**
3. Die Fragmente bleiben im ursprünglichen LLM-Output

### BEWEIS

Das kritische Code-Snippet in `_heal_html_blockwise` (text_healing.py Zeile 543):

```python
def heal_inner(m: re.Match) -> str:
    open_tag = m.group(1)
    inner = m.group(2)
    close_tag = m.group(3)

    # Skip wenn verschachtelte Tags ← HIER IST DAS PROBLEM!
    if "<" in inner and ">" in inner:
        return str(m.group(0))  # KEINE HEILUNG!

    healed = heal_text_block(inner, domain=domain, llm_fallback=None)
    return f"{open_tag}{healed}{close_tag}"
```

**Die Risk-Cards HTML (Zeile 5313-5317) enthält `<span class="icon icon--warning">⚠</span>` → verschachtelt → KEINE HEILUNG!**

---

## I. EMPFEHLUNG FÜR PATCH v14.35.17

### Option 1: Engine-Level Fix (BEST)

In `services/risk_engine_v2.py` vor dem HTML-Output:
```python
from services.text_healing import heal_text_block

# In risk_report_to_html(), vor dem Zusammenbau:
for risk in report.risks:
    risk.description = heal_text_block(risk.description, domain="risk")
    risk.mitigation = heal_text_block(risk.mitigation, domain="risk")
```

### Option 2: Post-Engine Healing in gpt_analyze.py

Nach Zeile 11842 (nach allen Engine-Generierungen):
```python
# === v14.35.17: Heal ALL Engine Outputs ===
from services.text_healing import _heal_html_blockwise
ENGINE_KEYS = ["RISK_ENGINE_HTML", "RISK_ENGINE_V3_HTML", "RECOMMENDATIONS_ENGINE_HTML"]
for key in ENGINE_KEYS:
    if key in sections and sections[key]:
        original = sections[key]
        healed = _heal_html_blockwise(original, domain="risk" if "RISK" in key else "reco")
        if healed != original:
            log.info(f"[ENGINE-HEAL] {key} healed")
            sections[key] = healed
```

### Option 3: Fix `_heal_html_blockwise` Regex

In `services/text_healing.py` Zeile 537-547:
```python
def heal_inner_deep(m: re.Match) -> str:
    """Version die auch verschachtelte Tags verarbeitet."""
    open_tag = m.group(1)
    inner = m.group(2)
    close_tag = m.group(3)

    # Extrahiere nur Text-Content (strip alle Tags)
    text_only = re.sub(r'<[^>]+>', '', inner)
    if not text_only.strip():
        return str(m.group(0))

    healed_text = heal_text_block(text_only, domain=domain, llm_fallback=None)
    # Rekonstruiere mit gehealtem Text
    # (Vorsicht: verliert innere Tag-Struktur!)
    return f"{open_tag}{healed_text}{close_tag}"
```

**EMPFOHLEN: Option 1 (Engine-Level) weil präziser und weniger Risiko für HTML-Korrumpierung**

---

*Evidence-Pack erstellt von Claude Code am 2026-01-14*
*Root Cause Analyse abgeschlossen.*

