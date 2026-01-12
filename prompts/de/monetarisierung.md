Developer:
<!-- PLATIN++ PROMPT v5.3 - SPRINT N -->
<!-- SECTION: monetarisierung -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, {{COMPANY_SIZE}} -->
<!-- TOKEN-BUDGET: 800 (solo:0.8x=640, team:1.0x=800, kmu:1.15x=920) -->
<!--
ZIEL: Kompakte Übersicht zu 3 Pricing-Modellen für KI-Services.

PFLICHTSTRUKTUR (3 Modelle):
1. Productized Service Light (Fixpreis) – Zielgruppe, Zeit, Preisband, Ergebnis
2. Retainer-Modell (monatlich) – Zielgruppe, Zeit, Preisband, Ergebnis
3. Workshop + Setup (Einmal + Follow-Up) – Zielgruppe, Zeit, Preisband, Ergebnis

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: Fokus auf Productized Services und Workshops (einfach erweiterbar)
- team: Retainer + Workshops
- kmu: Alle drei Modelle gleichwertig

ANTI-REDUNDANZ:
- Monetarisierung ergänzt Business Case, wiederholt ihn nicht
- Pricing-Logik HIER, nicht in anderen Sektionen

STIL:
- Textumfang: 120–180 Wörter
- Keine konkreten €-Beträge (nur Spannen)
- Keine Marketing-Floskeln

SPRINT N - SOLO PERSONA REGELN (STRIKT!):
{% if COMPANY_SIZE == "solo" %}
NICHT VERWENDEN für Solo:
- "Team aufbauen" → stattdessen: "Kapazität erweitern"
- "Mitarbeiter" → stattdessen: "Ressourcen"
- "Teams" → stattdessen: "Kapazitäten"
- "Fachbereich" → stattdessen: "Arbeitsfeld"
- "Abteilung" → stattdessen: "Arbeitsbereich"
Formulierungen ohne Team-/Abteilungsbegriff verwenden!
{% endif %}
-->

<section class="section monetization">
  <h2>Monetarisierung: 3 Pricing-Modelle für KI-Services</h2>

  <div class="pricing-models">
    <div class="model">
      <h4>1. Productized Service Light (Fixpreis)</h4>
      <ul>
        <li><strong>Zielgruppe:</strong> Kund:innen mit klar abgegrenztem Bedarf</li>
        <li><strong>Zeitaufwand:</strong> 2–8 Stunden pro Auftrag</li>
        <li><strong>Preisband:</strong> Niedriges bis mittleres Segment</li>
        <li><strong>Ergebnis:</strong> Standardisiertes Lieferergebnis (z.B. Prompt-Set, Mini-Audit)</li>
      </ul>
    </div>

    <div class="model">
      <h4>2. Retainer-Modell (monatlich)</h4>
      <ul>
        <li><strong>Zielgruppe:</strong> Stammkund:innen mit laufendem Bedarf</li>
        <li><strong>Zeitaufwand:</strong> 4–20 Stunden pro Monat</li>
        <li><strong>Preisband:</strong> Mittleres bis höheres Segment</li>
        <li><strong>Ergebnis:</strong> Kontinuierliche Betreuung, Updates, Optimierungen</li>
      </ul>
    </div>

    <div class="model">
      <h4>3. Workshop + Setup (Einmal + Follow-Up)</h4>
      <ul>
        <li><strong>Zielgruppe:</strong> Teams/KMU mit Einführungsbedarf</li>
        <li><strong>Zeitaufwand:</strong> 1 Tag Workshop + 2–4h Follow-Up</li>
        <li><strong>Preisband:</strong> Mittleres bis höheres Segment</li>
        <li><strong>Ergebnis:</strong> Befähigung des Teams + dokumentiertes Setup</li>
      </ul>
    </div>
  </div>

  <p class="small muted">
    Die Wahl des Modells hängt von Ihrer Kapazität und Zielgruppe ab.
    Kombinationen (z.B. Workshop → Retainer) erhöhen den Customer Lifetime Value.
  </p>
</section>
