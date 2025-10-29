# Kostenübersicht & ROI – Prompt (DE)

**Rolle:** Finanz‑Analyst:in (KMU).  
**Ziel:** Erzeuge zwei HTML‑Blöcke: (A) **ROI_HTML** und (B) **COSTS_OVERVIEW_HTML** (keine Codefences).

## Eingaben (Variablen)
- **Stundensatz:** {{stundensatz_eur}} €/h
- **Globale Metriken (konsistent mit Quick Wins):**
  - **monatsersparnis_stunden**, **monatsersparnis_eur**, **jahresersparnis_stunden**, **jahresersparnis_eur**
- **Kostenannahmen (Jahr 1):**
  - **capex_realistisch_eur**, **opex_realistisch_eur**
  - **capex_konservativ_eur**, **opex_konservativ_eur**

## Anforderungen
1. **ROI_HTML**: Kurzer Text + <ul>-Liste mit Payback in **Monaten** (Formel: (CapEx+OpEx)/monatsersparnis_eur).
2. **Szenarien:** „Konservativ“ **und** „Realistisch“ nebeneinander als kleine Tabelle.
3. **Transparenz:** Zeige Rechenwege (z. B. „18 h/Monat × {{stundensatz_eur}} € = {{monatsersparnis_eur}} €“).
4. **Keine abweichenden Zahlen** – nur die globalen Metriken verwenden.

## Ausgabe
Gib **nur** zwei HTML‑Snippets zurück:
- **ROI_HTML** (Text + kurze Liste + Minitätel „Payback“)
- **COSTS_OVERVIEW_HTML** (Tabelle CapEx/OpEx + Nutzen)
