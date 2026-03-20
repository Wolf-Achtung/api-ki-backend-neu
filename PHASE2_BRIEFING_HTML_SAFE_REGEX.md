# Phase 2 Briefing: GLOBAL FINAL ENFORCER HTML-Safe machen

**Datum:** 2026-03-20
**Vorgänger:** DIAGNOSE_KIS1019_CHUNK_BOUNDARY.md
**Scope:** `gpt_analyze.py:20417-20561` — GLOBAL FINAL ENFORCER
**Ziel:** Root-Cause-Fix statt str.replace-Pflaster

---

## Problem

Der GLOBAL FINAL ENFORCER wendet `re.sub(r'\bwir\b', 'ich', final_html)` auf **rohen HTML-String** an. `\b` (Word Boundary) behandelt `<`, `>`, `/` als Non-Word-Characters. Dadurch matcht `\bwir\b` auch innerhalb von HTML-Tags gesplitteten Wörtern:

```python
# IST-Zustand (Zeile 20534):
re.sub(r'\bwir\b', 'ich', '<strong>wir</strong>tschaftlich')
# → '<strong>ich</strong>tschaftlich'  → rendert als "ichtschaftlich"

re.sub(r'\buns\b', 'mir', '<em>uns</em>erer Kalkulation')
# → '<em>mir</em>erer Kalkulation'  → rendert als "mirerer Kalkulation"
```

**Betroffen sind ALLE 130+ Patterns** in `global_replacements` (Zeile 20423-20552), die `\b` verwenden und auf `final_html` operieren — nicht nur `wir`/`uns`.

---

## Warum str.replace-Pflaster nicht reichen

1. **Kombinatorische Explosion:** Jedes der ~20 Wörter (`wir`, `uns`, `unser`, `unsere`, `unseren`, `unserem`, `unserer`, `unseres`, `Wir`, `Uns`, ...) kann in jedem deutschen Kompositum vorkommen, das zufällig mit diesen Silben beginnt/endet. Nicht aufzählbar.
2. **Nicht deterministisch:** Welche Wörter der LLM in HTML-Tags splittet, ist nicht vorhersagbar. Heute `<strong>wir</strong>tschaftlich`, morgen `<em>uns</em>icher`.
3. **Jedes neue Pattern** in `global_replacements` erzeugt das gleiche Risiko.

---

## Lösung: Text-Only Regex auf HTML

### Kernidee

Statt `re.sub()` direkt auf HTML anzuwenden, eine Hilfsfunktion nutzen, die **nur auf sichtbaren Text** matcht und Tags überspringt.

### Implementierung

**Neue Hilfsfunktion** (inline in `gpt_analyze.py` oder als Utility):

```python
import re

# Pattern das HTML-Tags matcht (inkl. Kommentare und Processing Instructions)
_HTML_TAG_RE = re.compile(r'<[^>]+>')

def _html_safe_sub(pattern: str, replacement: str, html: str, flags: int = 0) -> str:
    """
    Führt re.sub() nur auf sichtbaren Text-Segmenten aus,
    lässt HTML-Tags unverändert.

    Strategie: HTML in Text- und Tag-Segmente splitten,
    Regex nur auf Text-Segmente anwenden, wieder zusammensetzen.
    """
    compiled = re.compile(pattern, flags)

    # HTML in Segmente aufteilen: abwechselnd Text und Tags
    parts = _HTML_TAG_RE.split(html)     # Text-Segmente
    tags = _HTML_TAG_RE.findall(html)     # Tag-Segmente

    # Regex nur auf Text-Segmente anwenden
    replaced_parts = [compiled.sub(replacement, part) for part in parts]

    # Wieder zusammensetzen: Text, Tag, Text, Tag, ...
    result = []
    for i, text_part in enumerate(replaced_parts):
        result.append(text_part)
        if i < len(tags):
            result.append(tags[i])

    return ''.join(result)
```

### Was sich ändert

**Eine Zeile** in der Hauptschleife (Zeile 20555-20559):

```python
# ALT (Zeile 20556):
new_html = re.sub(pattern, replacement, final_html,
                  flags=re.IGNORECASE if 'skalier' in pattern.lower() ... else 0)

# NEU:
new_html = _html_safe_sub(pattern, replacement, final_html,
                           flags=re.IGNORECASE if 'skalier' in pattern.lower() ... else 0)
```

### Warum das funktioniert

| Fall | Vorher | Nachher |
|------|--------|---------|
| `\bwir\b` auf `"...wir haben..."` | ✅ `"...ich habe..."` | ✅ `"...ich habe..."` |
| `\bwir\b` auf `"<b>wir</b>tschaftlich"` | ❌ `"<b>ich</b>tschaftlich"` | ✅ `"<b>wir</b>tschaftlich"` (kein Match — "wir" ist Textsegment, aber im Kontext von `_HTML_TAG_RE.split()` wird es als eigenständiges Segment gesehen wo `\bwir\b` matcht!) |

**ACHTUNG — Grenzfall:** Wenn der LLM `<b>wir</b>tschaftlich` generiert, ist "wir" ein eigenständiges Text-Segment. `\bwir\b` matcht darauf trotzdem, weil "wir" am Anfang und Ende des Segments steht und `\b` dort matcht.

### Erweiterte Lösung: Kontextprüfung

Für den Grenzfall brauchen wir eine erweiterte Variante, die prüft ob das nächste/vorherige Text-Segment nahtlos anschließt:

```python
def _html_safe_sub(pattern: str, replacement: str, html: str, flags: int = 0) -> str:
    """
    Führt re.sub() nur auf den zusammengesetzten Klartext aus,
    mappt Matches zurück auf die Originalposition und ersetzt dort.

    Verhindert Matches, die über Tag-Grenzen hinweg Wörter splitten.
    """
    compiled = re.compile(pattern, flags)

    # Schritt 1: Text-Segmente und ihre Positionen extrahieren
    segments = []  # (start_in_html, end_in_html, text)
    last_end = 0
    for tag_match in _HTML_TAG_RE.finditer(html):
        if tag_match.start() > last_end:
            segments.append((last_end, tag_match.start(), html[last_end:tag_match.start()]))
        last_end = tag_match.end()
    if last_end < len(html):
        segments.append((last_end, len(html), html[last_end:]))

    # Schritt 2: Klartext zusammensetzen + Offset-Map
    plain_text = ''
    offset_map = []  # (plain_start, plain_end, html_start, html_end)
    for html_start, html_end, text in segments:
        plain_start = len(plain_text)
        plain_text += text
        plain_end = len(plain_text)
        offset_map.append((plain_start, plain_end, html_start, html_end))

    # Schritt 3: Regex auf Klartext anwenden
    matches = list(compiled.finditer(plain_text))
    if not matches:
        return html

    # Schritt 4: Matches zurück auf HTML-Positionen mappen und ersetzen
    # (Rückwärts ersetzen um Positionen nicht zu verschieben)
    result = html
    for m in reversed(matches):
        match_start_plain = m.start()
        match_end_plain = m.end()

        # HTML-Positionen für Start und Ende finden
        html_start = _plain_to_html_pos(match_start_plain, offset_map)
        html_end = _plain_to_html_pos(match_end_plain, offset_map)

        if html_start is not None and html_end is not None:
            # Replacement mit Gruppen-Referenzen auflösen
            expanded = m.expand(replacement)
            # Ersetze im HTML (inkl. dazwischenliegender Tags)
            result = result[:html_start] + expanded + result[html_end:]

    return result


def _plain_to_html_pos(plain_pos: int, offset_map: list) -> int:
    """Mappt eine Position im Klartext zurück auf die HTML-Position."""
    for plain_start, plain_end, html_start, html_end in offset_map:
        if plain_start <= plain_pos <= plain_end:
            offset_within = plain_pos - plain_start
            return html_start + offset_within
    return None
```

### Was diese Lösung bewirkt

| Fall | HTML Input | Klartext | Match? | Ergebnis |
|------|-----------|----------|--------|----------|
| Normal | `wir haben` | `wir haben` | ✅ `\bwir\b` | `ich haben` |
| Tag-Split | `<b>wir</b>tschaftlich` | `wirtschaftlich` | ❌ `\bwir\b` kein Match in "wirtschaftlich" | unverändert ✅ |
| Tag-Wrap | `<b>wir</b> haben` | `wir haben` | ✅ `\bwir\b` | `<b>ich</b> haben` |
| Nested | `<p>Wir <b>können</b></p>` | `Wir können` | ✅ `\bWir\b` | `<p>Ich <b>können</b></p>` |

---

## Aufwand und Risiko

### Aufwand
- **~60 Zeilen** neue Hilfsfunktion
- **1 Zeile** Änderung in der Hauptschleife
- **0 Pattern-Änderungen** — alle 130+ Patterns bleiben identisch

### Risiko
- **Niedrig:** Die Hilfsfunktion ist ein reiner Wrapper. Wenn sie fehlschlägt, Fallback auf `re.sub()` direkt.
- **Edge Case:** Patterns mit `$` (Zeile 20467-20480, "ca. am Ende") — diese müssen auf Segment-Ende matchen. Die erweiterte Lösung handelt das korrekt, weil `$` auf das Ende des zusammengesetzten Klartexts matcht.

### Testing
1. Unit-Test: `_html_safe_sub(r'\bwir\b', 'ich', '<b>wir</b>tschaftlich')` → unverändert
2. Unit-Test: `_html_safe_sub(r'\bwir\b', 'ich', 'wir haben')` → `'ich haben'`
3. Unit-Test: `_html_safe_sub(r'\bwir\b', 'ich', '<b>wir</b> haben')` → `'<b>ich</b> haben'`
4. Regressionstest: Briefings 897, 901, 902 erneut generieren, auf "ichtschaftlich" prüfen
5. Regressionstest: Alle bestehenden str.replace-Pflaster in `_post_grammar` sollten NICHT mehr triggern

---

## Aufräumen nach Phase 2

Nach erfolgreichem Deploy der HTML-safe Lösung können diese Pflaster entfernt werden:

1. **`_post_grammar`-Block** (Zeile 20561-20609): Die meisten Einträge werden obsolet. Nur die reinen Verb-Agreement-Fixes (`Ich haben → Ich habe` etc.) bleiben nötig, da sie ein separates Problem lösen (Pattern-Reihenfolge, nicht HTML-Safety).

2. **`KNOWN_TRUNCATION_FIXES`** in `content_quality_enforcer.py:4536`: Die Einträge für `Vorhabe ichtschaftlich` können entfernt werden, sobald bestätigt ist dass der Root Cause (LLM-Artefakt oder Tag-Split) nicht mehr durchkommt.

---

## Zusammenfassung

| Was | Detail |
|-----|--------|
| **Root Cause** | `\b` in Regex matcht an HTML-Tag-Grenzen (`<`, `>` sind Non-Word) |
| **Fix** | `_html_safe_sub()` — Regex auf zusammengesetztem Klartext, Matches auf HTML zurückmappen |
| **Scope** | 1 neue Funktion + 1 Zeile Änderung in Hauptschleife |
| **Patterns** | Alle 130+ bleiben unverändert |
| **Risiko** | Niedrig — reiner Wrapper, Fallback möglich |
| **Eliminiert** | Alle aktuellen UND zukünftigen Tag-Split-Bugs für alle Patterns |
