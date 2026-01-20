# Report 498 PDF Analysis Notes

## PDF Seitenreferenzen

### Seite 1 (Cover)
- **Amortisation: 3,5 Monate** (korrekt, Canonical)
- Quality Badge: "A" (inkorrekt - sollte C sein wegen Validator Warnings)

### Seite 14 (Business-Case Kennzahlen)
- **Payback: 9 Monate** (INKORREKT - woher?)
- Mögliche Quelle: LLM-generierter Text, nicht aus Canonical
- ROI-Rate: 165% nach 24 Monaten

### Seite 16 (Quick Wins)
- Überschrift "Quick Wins" vorhanden
- Inhalt: Nur 3 Bulletpoints (zu kurz laut Validator)
- **Problem:** Validator prüft `quick_wins` Text, nicht `QUICK_WINS_HTML`

### Seite 19 (ROI-Simulation)
- Realistisch: 3,5 Monate (korrekt)
- Konservativ: 6,6 Monate (korrekt)
- Monte Carlo P50: 6,1 Monate (korrekt - Simulation)

### Seite 31 (Risiko-Matrix)
- Tabelle mit 5 Risiken
- **Abgeschnittene Wörter:**
  - "Zeitblöc..." → Zeitblöcke
  - "Datennutzungsrichtlin..." → Datennutzungsrichtlinien
  - "sorgfältige Auswahl u..." → und...
  - "Strenge Faktenprüfun..." → Faktenprüfung
- **Ursache:** `table-layout: fixed` + WeasyPrint Word-Wrap Bug

### Seite 37 (Starter-Kit Quick Wins)
- Überschrift "Quick Wins" mit Budget/Meta
- **Inhalt: LEER**
- Wahrscheinlich ein zweiter Quick Wins Block, der nicht befüllt wird

---

## Inkonsistenzen-Matrix

| KPI | Cover (S1) | BC-Card (S14) | ROI-Sim (S19) | Canonical |
|-----|------------|---------------|---------------|-----------|
| Payback | 3,5 M | **9 M** | 3,5 M | 3,5 M |
| ROI | 165% | 165% | 165% | 165% |

**Fazit:** Seite 14 zeigt einen falschen Payback-Wert (9 Monate), der nicht aus den kanonischen Daten stammt.

---

## Beobachtungen Quick Wins

1. `QUICK_WINS_HTML` wird korrekt generiert (458 Zeichen, 3 Items)
2. Template rendert `QUICK_WINS_HTML` auf Seite 16
3. Validator prüft `quick_wins` (Text) statt `QUICK_WINS_HTML` (HTML)
4. Seite 37 ist leer - muss geprüft werden welche Variable dort gerendert wird

---

## Debug-HTML Pfad

```
/tmp/report_debug_R-20260119-KND.html
```

Dieser Pfad war im Log erwähnt - enthält die Pre-Render HTML für Debugging.
Falls noch verfügbar: Abschnitte "Schnelle Effekte / Quick Wins" und "Starter-Kit" extrahieren.
