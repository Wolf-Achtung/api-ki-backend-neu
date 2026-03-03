Developer:
<!-- PLATIN++ PROMPT v7.1.1 -->
<!-- SECTION: score_interpretation -->
<!-- OUTPUT: PLAIN TEXT (kein HTML — Template wrappt in .score-interpretation) -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{score_int}}, {{variant_label}}, {{BRANCHE_LABEL}}, {{COMPANY_SIZE}}, {{hauptleistung}} -->
<!-- TOKEN-BUDGET: 600 -->
<!--
ZIEL: Kurze, konkrete Einordnung des KI-Readiness-Scores für das spezifische Unternehmen.

BRANCHENBEZEICHNUNG-REGEL:
Die Branchenbezeichnung "{{BRANCHE_LABEL}}" darf MAXIMAL 2x im gesamten Text vorkommen.
Ab der 3. Verwendung NUR noch Kurzformen: "Ihr Unternehmen", "Ihre Branche", "Ihr Geschäftsfeld".

REGELN (STRIKT):
- Ausgabe ist PLAIN TEXT — KEIN HTML, keine Tags, keine Markdown-Formatierung
- 2-3 Sätze, maximal 80 Wörter
- Score {{score_int}}/100 einordnen: Was bedeutet das konkret?
- Bezug zur Branche {{BRANCHE_LABEL}} und Hauptleistung {{hauptleistung}} herstellen
- Reifegrad {{variant_label}} erwähnen
- Konkret formulieren, keine Floskeln
- KEINE Emojis
- KEINE erfundenen Zahlen oder Benchmarks
- KEINE Handlungsempfehlungen (die kommen an anderer Stelle)
- KEIN Marketing-Deutsch

TONALITÄT:
- Sachlich, klar, auf den Punkt
- Wie ein Berater, der dem Geschäftsführer in einem Satz die Lage erklärt

BEISPIEL-STRUKTUR (nicht kopieren, nur als Orientierung):
"Mit [Score] Punkten liegt Ihr Unternehmen im [Reifegrad]-Bereich. Für [Branche] bedeutet das: [konkrete Einordnung]. [Ein Satz zur Perspektive]."
-->

Erstelle eine kurze Score-Einordnung (2-3 Sätze, Plain Text) für ein Unternehmen im Bereich {{hauptleistung}} ({{BRANCHE_LABEL}}) mit einem KI-Readiness-Score von {{score_int}}/100 (Reifegrad: {{variant_label}}).

Was bedeutet dieser Score konkret? Wie steht das Unternehmen da? Formuliere sachlich und ohne Floskeln.
