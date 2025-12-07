Developer:
<!-- PLATIN++ PROMPT v5.2 -->
<!-- SECTION: executive_summary -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}} -->
<!-- TOKEN-BUDGET: 600 (solo:0.8x=480, team:1.0x=600, kmu:1.15x=690) -->
<!--
ZIEL: CEO-taugliche Executive Summary in 2-4 Sätzen.

PLOT-STRUKTUR (STRIKT – ein Absatz):
1. Ausgangslage: Wo steht das Unternehmen heute? (Branche, Größe, KI-Reife)
2. Fokus & Ziele: Was ist das zentrale Ziel mit KI?
3. Wichtigste Hebel: Welcher eine Ansatzpunkt bringt den größten Effekt?
4. Sofortige Chance: Was ist der konkrete nächste Schritt?

STIL (CEO-TAUGLICH):
- Prägnant, keine Buzzwords ("Synergien", "Transformation", "Next-Level")
- Faktenbasiert, nüchtern, ergebnisorientiert
- KEINE Wiederholung von Roadmap-Details oder Quick-Win-Listen
- KEINE Aufzählungen – nur Fließtext
- Maximal 80 Wörter

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: "Sie", persönliche Perspektive, Entlastung als Ziel
- team: "Ihr Team", gemeinsame Effizienz
- kmu: "Ihr Unternehmen", strukturelle Hebel

ANTI-REDUNDANZ:
- Details zu Quick Wins → siehe quick_wins.md
- Details zu Roadmap → siehe roadmap_90d.md / roadmap_12m.md
- Hier NUR die Essenz, KEINE Vorwegnahme

GUARDRAILS: Respektiere angegebene Leitplanken aus strategischem Kontext.

WICHTIG:
- Gib KEINE eigenen h1/h2/h3-Überschriften aus.
- Der Template-Rahmen stellt bereits die Überschriften.
- Erzeuge NUR <p>-Elemente, ohne "Executive Summary"-Headline.
-->

<section class="section executive-summary">
  <!-- KEINE h2 hier - Template stellt Überschrift bereit -->

  <p>
    {% if COMPANY_SIZE == "solo" %}
    Als Einzelunternehmer:in in der Branche <strong>{{BRANCHE_LABEL}}</strong> mit dem Schwerpunkt
    <strong>{{HAUPTLEISTUNG}}</strong> liegt Ihr größter Hebel in der Automatisierung
    wiederkehrender Aufgaben – hier lassen sich pro Woche mehrere Stunden zurückgewinnen.
    Der erste Schritt: ein strukturierter KI-Workflow für Ihre zeitintensivste Routineaufgabe.
    {% elif COMPANY_SIZE == "team" %}
    Ihr Team in der Branche <strong>{{BRANCHE_LABEL}}</strong> ({{UNTERNEHMENSGROESSE_LABEL}})
    kann durch gezielte KI-Unterstützung im Bereich <strong>{{HAUPTLEISTUNG}}</strong>
    signifikante Effizienzgewinne erzielen. Der zentrale Ansatzpunkt: gemeinsame Standards
    für KI-gestützte Routinen, die sofort Entlastung bringen und Qualität sichern.
    {% else %}
    Für ein Unternehmen Ihrer Größe ({{UNTERNEHMENSGROESSE_LABEL}}) in der Branche
    <strong>{{BRANCHE_LABEL}}</strong> bietet der Bereich <strong>{{HAUPTLEISTUNG}}</strong>
    den größten Hebel für KI-gestützte Produktivitätsgewinne. Der strategische Fokus liegt
    auf skalierbaren Prozessen, die in Pilotbereichen erprobt und dann ausgerollt werden.
    {% endif %}
  </p>
</section>
