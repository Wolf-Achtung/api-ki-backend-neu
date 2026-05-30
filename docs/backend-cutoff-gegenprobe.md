# Backend-Cutoff-Gegenprobe (Sprint 1027.5.2-DIAG-Backend)

**Scope:** reine Analyse, kein Code-Eingriff.
**Repo:** `api-ki-backend-neu` (Branch `main`, Stand 30.05.2026).
**Anlass:** Gegenstück zur make-ki-pdfservice-Diagnose (1027.5.2-DIAG) —
dort 0 Treffer auf die CSS-Fix-Marker. Frage: liegen die Fixes hier korrekt
und werden sie vom Downstream-Service nicht stillschweigend abgeräumt?

---

## A) Treffer-Tabelle (CSS-/Marker-Suche im Backend-Repo)

### A.1 `exec-decision-box`

| Datei | Zeile | Kontext |
|---|---|---|
| `templates/pdf_template_v7.html` | 706 | Kommentar: „`.exec-decision-box(break-inside:avoid)` clipte den Inhalt auf min-height (176px)" |
| `templates/pdf_template_v7.html` | 708 | Kommentar: „Container-Atomaritaet auf `.exec-decision-box` selbst, weil sie bei …" |
| `templates/pdf_template_v7.html` | **711** | **Aktive Regel:** `.exec-decision-box { … }` |
| `templates/pdf_template_v7.html` | **719** | **Aktive Regel:** `.exec-decision-box li { … }` |
| `templates/pdf_template_v7.html` | 1552 | Jinja-Kommentar: „inner `.exec-decision-box`) triggerten Chromium-Layout-Pass-Bug" |
| `templates/pdf_template_v7.html` | 1554 | Jinja-Kommentar: „`.exec-decision-box` trägt jetzt wieder allein die Atomarität." |
| `tests/test_decision_section_figure_wrapper.py` | 10/14/16/94/101/105/117/122/127/132/137/140/144/149/153/156/186 | Test-Assertions auf das o.g. Regelpaar |
| `tests/test_exec_decision_clean.py` | 35/113/326/356 | Fixture-HTML mit `<div class="exec-decision-box">` |
| `tests/test_fix_c_skip_decision.py` | 41 | Fixture-HTML |
| `tests/test_kis_1027_5_1_a_cutoff_trace.py` | 32 | Fixture-HTML |
| `tests/test_kis_1027_5_h1_render_cutoff.py` | 9/36/39/43/54/62/69/80/88 | Regression-Tests für 1027.5-H1 |

→ **Fazit:** der Selektor existiert genau einmal aktiv im Template
(`templates/pdf_template_v7.html:711`) plus einmal als `li`-Child
(`:719`). Alle übrigen Treffer sind Kommentare oder Tests.

### A.2 `decision > div`

| Datei | Zeile | Kontext |
|---|---|---|
| `templates/pdf_template_v7.html` | 699 | **Nur Kommentar:** „Die generische `#decision > div { break-inside: avoid }`-Regel re-introduzierte denselben Bug …" |
| `tests/test_decision_section_figure_wrapper.py` | 183/193/201 | Regression-Test: aktive Regel darf NICHT existieren |
| `tests/test_kis_1027_5_h1_render_cutoff.py` | 10/86 | Regression-Test (analog) |

→ **Fazit:** die Regel `#decision > div { break-inside: avoid }` ist
**aktiv entfernt**. Sie existiert nur noch als Audit-Trail-Kommentar
und als negativ-Assertion in zwei Tests.

### A.3 `break-inside`

Treffer-Hotspots (≥ 1 aktive Verwendung pro Datei):

| Bereich | Datei | Aktive Regelorte |
|---|---|---|
| Template-CSS | `templates/pdf_template_v7.html` | 691/692 (`#decision ul,ol,li,p,…`), 720/721 (`.exec-decision-box li`) |
| Template-CSS | `templates/gamechanger_deep_dive_v1.html` | 131/142/465/474/480/533 |
| Template-CSS | `templates/strategy_report.html` | (vorhanden, hier nicht im Fokus) |
| Inline-Styles | `gpt_analyze.py` | 4446/4970/6899/7221/14195 |
| Inline-Styles | `services/sofort_start_generator.py` | 1890/1920/1951/1972/2649/2990 |
| Inline-Styles | `services/quickwins_renderer.py` | 202/203/926 |
| Inline-Styles | `services/vendor_audit_engine.py` | 1554 |
| Inline-Styles | `services/business_case_engine_v2.py` | 2292 |
| Inline-Styles | `services/html_enhancer.py` | 236/600/607/614/621/663 |
| Inline-Styles | `services/layout_consistency_engine.py` | 365/367/385/388/469/630/649/656/666/920/1039/1043 |
| Postflight | `scripts/postflight_checker.py` | 96/98/99 |
| Release-Gate | `scripts/release_blocker_gate.py` | 29/314/320/322/415/418/420/426/429/431 |

→ Volltext-Treffer-Inhalte: siehe rohe Grep-Ausgabe oben im Run-Log.
Die Klasse hat hohe Verwendungs-Dichte; Refactoring-Risiko also
hoch. **Aber:** die für 1027.5-H1 relevanten Regeln liegen
ausschließlich in `templates/pdf_template_v7.html` Zeilen 685-724.

### A.4 `@page`

| Datei | Zeile | Inhalt |
|---|---|---|
| `templates/pdf_template_v7.html` | **22** | `@page { size: A4; margin: 12mm 12mm 15mm 12mm; @bottom-right {…} }` |
| `templates/strategy_report.html` | 21 | `@page { … }` (Strategy-Report, hier off-scope) |
| `templates/gamechanger_deep_dive_v1.html` | 20 | `@page { … }` |
| `services/email_templates.py` | 869 | inline: `"@page { size: A4; margin: 20mm 15mm; }"` |
| `services/layout_consistency_engine.py` | 620 | dynamisch generierter `@page`-Block |
| `tests/test_n37_regression_suite.py` | 581 | Test-Assertion |

→ Im Haupt-Template existiert **genau ein** `@page`-Block (Z. 22-31).

### A.5 `FIX-KIS-1027`-Marker (1027.2 / 1027.4 / 1027.5)

Über 60 aktive Treffer in Code, Tests, Template-Kommentaren. Für
den Cutoff direkt relevant:

| Datei | Zeile | Inhalt |
|---|---|---|
| `templates/pdf_template_v7.html` | 696-718 | `FIX-KIS-1027.5-H1` Audit-Trail + Active-CSS |
| `templates/pdf_template_v7.html` | 1550-1554 | `1027.2.3` Jinja-Kommentar (figure-Wrapper entfernt) |
| `templates/pdf_template_v7.html` | 1663 | `FIX-KIS-1027.5-A` (ROI-Sichten) |
| `services/report_renderer.py` | 74-80, 684, 871, 894, 899, 1147, 1154, 1576, 1581, 2180 | 1027.5.1-A Cutoff-Trace-Checkpoints 1-6 |
| `services/pdf_client.py` | 266-299 | 1027.5.1-A Cutoff-Trace-Checkpoint 7 (HTTP-Boundary) |

(Vollständige Liste der `1027.2`/`1027.4`/`1027.5`-Marker siehe
Run-Log. Hier nur Render-Pipeline-relevante Treffer.)

---

## B) PR #1042 — Files-Changed-Inspektion

**Status:** merged (2026-05-30 12:51 UTC) durch Wolf-Achtung.
**Head-SHA:** `d74a035d676b5c82a3b3bf97103f6dbe5b7a8430`.
**Diff:** +827 / −65, 16 files, 8 commits.

### B.1 Files-Changed-Liste

| # | Datei | Add | Del | Item |
|---|---|---|---|---|
| 1 | `core/audit.py` | 2 | 2 | mypy-cast |
| 2 | `docs/architecture-reference.md` | 24 | 0 | 5-D Doku |
| 3 | `gpt_analyze.py` | 14 | 8 | 5-B / 5-C |
| 4 | `mise.toml` | 15 | 0 | 5-D (neu) |
| 5 | `routes/chat.py` | 12 | 6 | 5-C |
| 6 | `services/email_templates.py` | 19 | 9 | 5-B / 5-C |
| 7 | `services/report_renderer.py` | 30 | 0 | 5-A |
| 8 | `services/vendor_audit_engine.py` | 29 | 5 | H2 |
| 9 | **`templates/pdf_template_v7.html`** | **48** | **10** | **H1 + 5-A** |
| 10 | `tests/test_decision_section_figure_wrapper.py` | 37 | 25 | H1-Regression |
| 11 | `tests/test_kis_1027_5_a_roi_methodik.py` | 125 | 0 | 5-A neu |
| 12 | `tests/test_kis_1027_5_b_admin_mail_deduplication.py` | 108 | 0 | 5-B neu |
| 13 | `tests/test_kis_1027_5_c_chat_blocks_naming.py` | 107 | 0 | 5-C neu |
| 14 | `tests/test_kis_1027_5_d_mise_toml.py` | 49 | 0 | 5-D neu |
| 15 | `tests/test_kis_1027_5_h1_render_cutoff.py` | 109 | 0 | H1 neu |
| 16 | `tests/test_kis_1027_5_h2_vendor_audit_strategy.py` | ~109 | 0 | H2 neu |

### B.2 Cross-Repo-Push nach `make-ki-pdfservice`?

**Nein.** Alle 16 geänderten Dateien liegen in
`Wolf-Achtung/api-ki-backend-neu`. Branch `claude/sprint-1027-5-combined`
mergt nach `main` desselben Repos. Es gibt keine Workflow- / Submodule- /
Deploy-Action in PR #1042, die nach `make-ki-pdfservice` propagiert.

Damit erklärt sich der Befund aus 1027.5.2-DIAG:
0 Treffer in `make-ki-pdfservice` für die `1027.5-H1`-Marker, weil
**die Markers strukturell nie dorthin gehörten**.

### B.3 Zeilen-Diff `templates/pdf_template_v7.html`

(zusammengefasst aus PR-Diff; Datei-Zeilen referenzieren den **Post-Merge-Stand**)

#### B.3.1 H1-Block (Zeilen 696-718, „Container-Atomarität entfernt")

```diff
-#decision > div,
-#decision .section-body > div {
-    break-inside: avoid;
-    page-break-inside: avoid;
-}
+/* FIX-KIS-1027.5-H1: KEIN break-inside:avoid auf generischen div-Kindern
+   von #decision. […]
+   Container darf jetzt ueber Seitengrenze hinweg flieЯen,
+   einzelne <li> bleiben atomar. */

 .exec-decision-box {
-    break-inside: avoid !important;
-    page-break-inside: avoid !important;
+    /* break-inside: avoid !important; -- FIX-KIS-1027.5-H1: entfernt */
+    /* page-break-inside: avoid !important; -- FIX-KIS-1027.5-H1: entfernt */
     break-before: auto;
     page-break-before: auto;
     break-after: auto;
     page-break-after: auto;
 }
```

Atomarität auf `<li>`-Ebene bleibt erhalten (Z. 719-724,
unverändert in PR):

```css
.exec-decision-box li {
    break-inside: avoid !important;
    page-break-inside: avoid !important;
    orphans: 3;
    widows: 3;
}
```

#### B.3.2 5-A-Block (Zeilen 1660-1696, ROI-Sichten-Tabelle)

`+48` Zeilen Jinja-Block für `roi-views-table` (CAPEX vs. 12-Mo-TCO);
nicht render-cutoff-relevant.

---

## C) `templates/pdf_template_v7.html` — Struktur-Inventar

### C.1 `@page`-Regel-Inventar

**Anzahl:** 1.
**Position:** Z. 22-31.
**Inhalt:**

```css
@page {
    size: A4;
    margin: 12mm 12mm 15mm 12mm;
    @bottom-right {
        content: "Seite " counter(page) " von " counter(pages);
        font-size: 7.5pt;
        color: #9CA3AF;
        font-family: 'Inter', system-ui, sans-serif;
    }
}
```

→ Definiert: Papierformat, äußere Ränder, Seitenzähler-Footer.
→ **Kein** explizites Verhalten für Page-Break-Inside; das wird
ausschließlich über `break-inside` / `page-break-inside` auf
Elementebene gesteuert.

### C.2 `<style>`-Block-Anzahl & Reihenfolge

**Anzahl:** **1** (single `<style>`-Block).
**Position:** Z. 10 (open) → Z. 1164 (close).
**Reihenfolge im Block (relevante Regionen):**

| Region | Z. | Funktion |
|---|---|---|
| `@import` Fonts | 19 | Inter-Font |
| `@page` | 22-31 | Papierformat |
| `:root` Tokens | 34-75 | CSS-Variablen |
| Base Reset / Body | 77-89 | inkl. globaler `orphans:4; widows:4` |
| Typography | 91-114 | |
| Page-Break-Rules v7.1.4 | 119-153 | `break-before: page` auf Major-Sections inkl. `#decision` (Z.138-140) |
| `.section` Basis | 154-176 | `break-inside: auto` (Default — kein implizites avoid) |
| … (Tokens, Komponenten) … | 177-630 | nicht atomic-relevant |
| Decision-Section Härtung | **678-724** | **1027.5-H1 Kernzone** |
| restliche Komponenten | 725-1163 | |

Da es nur einen Style-Block gibt, gibt es **keine** Reihenfolge-
Konflikte zwischen mehreren Style-Tags. Späterer Regel-Override
funktioniert ausschließlich über Source-Order innerhalb des Blocks
plus Specificity.

### C.3 Specificity-Übersicht — Decision-Section

| Selektor | Specificity (a,b,c) | break-inside | !important | aktiv? |
|---|---|---|---|---|
| `#decision` | (1,0,0) | — (`break-before:page`) | nein | ✅ Z.138 |
| `#decision ul, #decision ol, #decision li, #decision p, #decision .executive-decision-fallback, #decision .decision-card` | (1,0,1) bzw. (1,1,1) | `avoid` | nein | ✅ Z.685-694 |
| `.exec-decision-box` | (0,1,0) | (auskommentiert) | (war `!important`) | ❌ Z.711 |
| `.exec-decision-box li` | (0,1,1) | `avoid` | **`!important`** | ✅ Z.719-724 |
| `.decision-card` | (0,1,0) | `page-break-inside:avoid` | nein | ✅ Z.649-659 |
| `~~#decision > div, #decision .section-body > div~~` | ~~(1,0,1) / (1,1,1)~~ | ~~avoid~~ | — | ❌ entfernt |

**Wichtig:** keine konkurrierende Regel mit höherer Specificity
greift mehr auf `.exec-decision-box` ohne `li`-Suffix. Die einzige
Stelle, die `break-inside` für den Container setzen könnte, wäre
`#decision > div`/`#decision .section-body > div` (Specificity
1,0,1 bzw. 1,1,1) — beide sind gelöscht.

Andere im PR-Body erwähnte Container (`.qw-context-banner`) sind
**nicht** in der Decision-Section verbaut; volltextlich kommt
`qw-context-banner` im Template nicht vor (Grep: 0 Treffer in
`pdf_template_v7.html`). Damit konkurriert nichts mehr mit
`.exec-decision-box`.

---

## D) Bewertung CSS-Fix 1027.5-H1

### D.1 Ist „Container darf umbrechen, `<li>` bleibt atomar" korrekt?

**Ja.** Die Formulierung ist CSS-technisch sauber:

1. **Auf Container-Ebene** (`.exec-decision-box`, `#decision > div`)
   wurden `break-inside: avoid` und `page-break-inside: avoid`
   **vollständig** zurückgenommen — kein aktives Element setzt mehr
   eine Container-Atomarität, die Chromium dazu zwingen könnte, den
   gesamten Block auf einer Seite zu halten und bei `content > pageHeight`
   zu clippen.

2. **Auf `<li>`-Ebene** (`.exec-decision-box li`, `#decision li`)
   bleibt `break-inside: avoid` mit `!important` aktiv. Das verhindert
   Mid-Sentence-Cuts in einzelnen Bullets — exakt das gewünschte
   Verhalten (Bullet bleibt atomar, der umgebende Container darf
   umbrechen).

3. **`break-before/after: auto`** sind explizit gesetzt (Z. 714-717),
   um Erbschaft aus übergeordneten Regeln zu unterbinden — defensives,
   richtiges Pattern.

### D.2 Greift die Specificity über andere Regeln?

**Auf Container-Ebene:** Es gibt keine konkurrierende Regel mehr.
Die früher problematische `#decision > div`-Regel (Specificity
1,0,1) ist gelöscht; übrig bleibt nur `.exec-decision-box` selbst
(0,1,0), die ihre Atomarität-Properties auskommentiert hat.

**Auf `<li>`-Ebene:** `.exec-decision-box li` (0,1,1) **mit `!important`**
schlägt jeden generischen `#decision li`-Selektor (1,0,1) ohne
`!important`. Auch wenn `#decision li` (Z. 687) ohne `!important`
ebenfalls `break-inside: avoid` setzt, wäre das Resultat dasselbe —
beide Regeln zeigen in dieselbe Richtung. Kein Konflikt.

**`@page`-Konflikt:** der `@page`-Block (Z.22) definiert nur
Papierformat und Footer, kein Break-Verhalten. Damit greift er nicht
in Konkurrenz zu den Element-Regeln.

### D.3 Sind die `break-inside`-Werte konsistent?

**Ja, mit einer Mikro-Inkonsistenz, die unkritisch ist:**

| Ebene | break-inside | page-break-inside | Konsistenz |
|---|---|---|---|
| Container `.exec-decision-box` | (deaktiviert) | (deaktiviert) | ✅ |
| `<li>` `.exec-decision-box li` | `avoid !important` | `avoid !important` | ✅ |
| `<li>` `#decision li` | `avoid` (ohne `!important`) | `avoid` | ✅ |
| `<ul>/<ol>/<p>` `#decision ul, …` | `avoid` | `avoid` | ⚠️ (s.u.) |
| `.section` (Basis) | `auto` | — | ✅ |

⚠️ **Hinweis:** `#decision ul, #decision ol` haben weiterhin
`break-inside: avoid` (Z. 685-694). Das ist NICHT der Container
`.exec-decision-box`, sondern die innere Liste. **Wenn** das LLM
ein `<ul>` mit Inhalt > 1 Seite produziert, würde dieselbe
Clipping-Falle erneut zuschlagen — denselbe Mechanismus wie 1027.2.2-A
beim `<figure>`, nur diesmal auf `<ul>`. Das ist **noch nicht
expliziert behoben**. Für aktuellen R1-Content (3 Bullets ≈ 1-1.5
Seiten) reicht die `<li>`-Atomarität, aber bei breitem Content
(z. B. KMU-spezifisch mit längeren Bullets) bleibt Risiko.

→ **Empfehlung für Folge-Sprint:** prüfen, ob `#decision ul, #decision ol`
ebenfalls von `break-inside: avoid` auf `auto` umgestellt werden
sollte (Konsistenz mit der 1027.5-H1-Logik).

### D.4 Gesamturteil

Der 1027.5-H1-Fix ist **CSS-technisch korrekt** für den dokumentierten
Failure-Mode (Container-Atomarität bei 3-Bullet-Inhalt > 1 Seite).
Die Specificity-Hierarchie ist sauber, es greift keine versteckte
konkurrierende Regel mehr, und die Regression-Tests in
`test_decision_section_figure_wrapper.py` und
`test_kis_1027_5_h1_render_cutoff.py` decken sowohl positive
(`<li>` atomar) als auch negative (Container NICHT atomar) Aspekte ab.

**Restrisiko:** das `#decision ul, ol`-Atomicity-Pärchen (Z. 685-694)
ist nicht Teil des H1-Fixes und reproduziert dasselbe Pattern eine
DOM-Ebene tiefer. Falls Inhalt > 1 Seite **innerhalb eines einzelnen
`<ul>`** kommt, Clipping möglich.

---

## E) Aussage: was wäre nötig, wenn `make-ki-pdfservice` `stripAtRules` entfernen würde?

### E.1 Annahme & Hintergrund

Aus 1027.5.2-DIAG: der PDF-Service betreibt vermutlich eine
HTML-Sanitization-Stage (`stripAtRules`, `consolidateStyles`), die
`@page`-/`@import`-Regeln und ggf. komplette `<style>`-Blöcke
abräumen oder konsolidieren könnte, **bevor** Chromium das HTML
sieht. Wenn diese Stage entfernt würde (oder bereits jetzt
selektiv durchwirkt), würde das eingehende HTML
1:1 an Chromium gehen.

### E.2 Was bleibt im Backend zu tun?

**Wenn der Service `stripAtRules` entfernt: Backend muss aktiv NICHTS
zusätzlich tun**, weil:

1. Das Backend liefert bereits **gültigen** `@page`-Block
   (`pdf_template_v7.html:22-31`), den Chromium nativ versteht.
2. Das Backend liefert bereits **einen einzigen `<style>`-Block**
   ohne externe `<link rel="stylesheet">`-Referenzen — keine
   Konsolidierung nötig.
3. Die `1027.5-H1`-Regeln sind reines Standard-CSS3
   (`break-inside`, `page-break-inside`, `!important`,
   Specificity-Hierarchie) — keine Service-spezifischen
   Hilfsklassen, keine `@`-At-Rule-Abhängigkeit jenseits
   `@page`/`@import`.

**Was hingegen rückblickend nötig wäre, wenn `consolidateStyles`
weiter aktiv im pdfservice läuft:**

| Maßnahme | Backend-Eingriff |
|---|---|
| Inline-`!important`-Direkt-Attribute auf `<div class="exec-decision-box">` setzen | `gpt_analyze.py` / `services/report_renderer.py` müsste beim Inject von `EXECUTIVE_DECISION_HTML` den Container mit `style="break-inside:auto;page-break-inside:auto"` ausstatten — würde Spec-Override im Inline-Style umgehen |
| `<li>`-Inline-Style ergänzen | analog dazu pro `<li>` `style="break-inside:avoid;page-break-inside:avoid"` injizieren — robust gegen Style-Sheet-Stripping |
| `@import`-Font ersetzen | falls `consolidateStyles` `@import` entfernt: Font lokal einbetten oder `<link>` im `<head>` als Fallback |
| Cutoff-Trace Checkpoint 7 erweitern | `services/pdf_client.py:266` schon vorhanden (HTTP-Boundary-Trace); zusätzlich CSS-Marker-Hash transportieren, um End-to-End-Beweis zu führen, dass die Regel auch im Service ankommt |
| Smoke-Assertion gegen ausgehendes HTML | im `pdf_client._call` könnte ein Pre-Send-Check verifizieren, dass das gerenderte HTML die Marker `FIX-KIS-1027.5-H1` und die `<li>`-`break-inside`-Regel noch enthält |

**Faktisch nötig im aktuellen Zustand:** **keine** Backend-
Änderung, sofern die diagnostische Annahme stimmt, dass der
pdfservice nicht selektiv `.exec-decision-box`-Regeln entfernt.
Die Cutoff-Beobachtung in KIS-1199 lässt sich vollständig durch
den bereits gefixten Container-Atomarität-Bug erklären — und dieser
Fix ist hier korrekt eingespielt (Container offen, `<li>` atomar).

### E.3 Empfohlene Folge-Maßnahmen (nicht Teil dieser Diagnose)

- **`#decision ul, ol`** als nächste Specificity-Falle prüfen
  (Restrisiko aus D.3).
- **End-to-End-Hash-Diff**: post-Render-HTML vor und nach
  pdfservice vergleichen — wenn Hash stimmt, ist `consolidateStyles`
  bewiesenermaßen ein No-Op für die relevanten Selektoren.
- **`services/pdf_client.py:266` Checkpoint 7** um CSS-Klassen-Counter
  ergänzen: `<li class="…break-inside…">` count, damit Render-Layer
  einen objektiven Fingerprint vorzeigen kann.

---

## Anhang — Branch / SHA

- Backend-Repo: `Wolf-Achtung/api-ki-backend-neu`, Branch `main`.
- PR #1042 head: `d74a035d676b5c82a3b3bf97103f6dbe5b7a8430`, merged
  2026-05-30 12:51 UTC.
- Analyse-Branch: `claude/eloquent-mccarthy-FvAVq` (kein Code-Eingriff).
