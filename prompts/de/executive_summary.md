<!-- executive_summary.md – v2.2 GOLD STANDARD+ (Summary + Context-Integration)
     Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences im OUTPUT.
     VERSION: 2.2 GOLD STANDARD+ (Bereinigung von Kontext-Platzhaltern)
-->

# PROMPT: Executive Summary

## ZWECK

Erstelle eine **eine Seite** Executive Summary, die:

1. die aktuelle KI‑Position des Unternehmens prägnant zusammenfasst,
2. die wichtigsten Ergebnisse aus Scores, Quick Wins, Roadmap, Business Case & Förderpotenzial verbindet,
3. klare Botschaften für die Geschäftsführung liefert („Was heißt das jetzt konkret?“).

**Zielgruppe:** Geschäftsführung, Eigentümer:innen, Aufsichtsrat  
**Stil:** Klar, fokussiert, keine Buzzwords, maximal 3–5 kurze Abschnitte.

---

## KONTEKTE, DIE DU NUTZT

- Reale Score‑Werte (Governance, Sicherheit, Wertschöpfung, Befähigung, Gesamt)
- Kernaussagen aus:
  - Quick Wins
  - 90‑Tage‑Roadmap
  - 12‑Monats‑Roadmap
  - Business Case (CAPEX, OPEX, Payback, ROI 12M)
  - Förderpotenzial (nur qualitativ, keine eigenen Zahlen)
  - Tool‑Empfehlungen
- Fragebogen‑Infos:
  - {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, {{BUNDESLAND_LABEL}}

Kontextblöcke werden dir als Text übergeben.  
Im Output dürfen **keine technischen Bezeichner** aus der Pipeline auftauchen  
(also keine Strings wie „CONTEXT_QUICK_WINS“, „CONTEXT_ROADMAP_90D“ etc.).

---

## KRITISCHE REGELN

1. **Keine Platzhalter, keine technischen Namen**
   - Keine `[...]`‑Platzhalter.
   - Keine `{IRGENDETWAS}`‑Strings.
   - Keine internen Bezeichner aus der Pipeline (CONTEXT\_…, SCORE\_…, TOOLS\_…).

2. **Scores ehrlich einordnen**
   - Nenne die Score‑Werte kurz, aber interpretiere sie verständlich
     („Governance hoch, Security mittel, Wertschöpfung sehr stark“).
   - Keine Übertreibungen oder falsche Sicherheit.

3. **Solo vs. Team vs. KMU**
   - Solo: Fokus auf eigene Arbeitszeit & Entscheidungsfreiheit.
   - Team: Fokus auf Zusammenarbeit & interne Akzeptanz.
   - KMU: Fokus auf Skalierbarkeit, Governance, Mitnahme mehrerer Bereiche.

4. **Verdichtung statt Wiederholung**
   - Du wiederholst nicht einfach den ganzen Report,
     sondern destillierst die **wichtigsten 3–5 Botschaften**.

---

## OUTPUT: NUR HTML (eine kompakte Section)

```html
<section class="section executive-summary">
  <h2>Executive Summary</h2>

  <p>
    Formuliere ein kurzes Intro (2–3 Sätze), das Branche {{BRANCHE_LABEL}},
    Unternehmensgröße {{UNTERNEHMENSGROESSE_LABEL}} und den Kernprozess
    {{HAUPTLEISTUNG}} nennt. Erkläre, dass es sich um eine Standortbestimmung
    und einen konkreten Aktionsplan für KI handelt.
  </p>

  <h3>Ausgangslage & Scores</h3>
  <p>
    Fasse die wichtigsten Score‑Ergebnisse (Governance, Sicherheit,
    Wertschöpfung, Befähigung, Gesamt) in verständlicher Sprache zusammen.
    Betone Stärken und Entwicklungsfelder, ohne Zahlen zu erfinden.
  </p>

  <h3>Wichtigste Quick Wins & kurzfristige Maßnahmen</h3>
  <p>
    Hebe 2–3 Quick Wins hervor, die in den nächsten 90 Tagen den größten
    Impact im Prozess {{HAUPTLEISTUNG}} haben. Verweise optional auf
    die 90‑Tage‑Roadmap, ohne sie im Detail zu wiederholen.
  </p>

  <h3>Business Case & Förderpotenzial</h3>
  <p>
    Fasse den Business Case in 3–4 Sätzen zusammen:
    Größenordnung von Investition (CAPEX/OPEX), erwartete monatliche
    Entlastung, ungefähre Amortisationsdauer und ROI‑Niveau.
    Ergänze 1–2 qualitative Aussagen zum Förderpotenzial
    (z.&nbsp;B. „Landesprogramme können CAPEX deutlich reduzieren“),
    ohne selbst neue Zahlen zu erfinden.
  </p>

  <h3>Nächste Schritte für Geschäftsführung</h3>
  <p>
    Schließe mit 3–5 klaren Empfehlungen auf Management‑Ebene,
    z.&nbsp;B. Start des Piloten, Priorisierung eines Bereichs,
    Festlegung von Budgetrahmen oder Governance‑Entscheidungen.
    Formuliere so, dass eine Geschäftsführung innerhalb weniger Minuten
    versteht, was jetzt konkret zu tun ist.
  </p>
</section>
