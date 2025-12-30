<!-- PLATIN+++ PROMPT v7.0 - HYPER-PERSONALIZED QUICK WINS (Phase 3 Optimization) -->
<!-- SECTION: quick_wins -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- PHASE 3: Maximum personalization using ALL 5 freetext fields (Goldnuggets) -->
<!-- INPUT: {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}}, {{ki_projekte}}, {{ki_guardrails}}, {{vision_3_jahre}}, {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, COMPANY_SIZE, {{STUNDENSATZ_EUR}}, {{score_security}}, {{score_governance}} -->
<!-- TOKEN-BUDGET: 4000 (solo:0.9x=3600, team:1.0x=4000, kmu:1.1x=4400) -->
<!--
=============================================================================
PLATIN+++ v7.0: HYPER-PERSONALISIERTE QUICK WINS (Phase 3 Sprint 1)
=============================================================================

KRITISCHE NEUERUNGEN v7.0 (STRIKT BEACHTEN!):
1. ALLE 5 Goldnuggets (Freitextfelder) MÜSSEN genutzt werden
2. Quick Win #1 ZITIERT {{ZEITERSPARNIS_PRIORITAET}} WÖRTLICH in Blockquote
3. Quick Win #2 referenziert {{ki_projekte}} (falls vorhanden)
4. JEDER Quick Win enthält einen Copy-Paste-Prompt
5. Setup-Schritte mit KONKRETEN Zeitangaben

=============================================================================
DIE 5 GOLDNUGGETS (Freitextfelder) - ALLE NUTZEN!
=============================================================================

1. HAUPTLEISTUNG - Was macht das Unternehmen?
   Wert: "{{hauptleistung}}"
   → Nutzen: Alle Quick Wins müssen zur Haupttätigkeit passen

2. ZEITERSPARNIS_PRIORITAET - Wo verliert der User am meisten Zeit?
   Wert: "{{ZEITERSPARNIS_PRIORITAET}}"
   → Nutzen: Quick Win #1 MUSS dieses Problem lösen und WÖRTLICH zitieren!

3. KI_PROJEKTE - Was ist bereits geplant?
   Wert: "{{ki_projekte}}"
   → Nutzen: Quick Win #2 greift geplante Projekte auf (falls vorhanden)

4. KI_GUARDRAILS - Was ist TABU?
   Wert: "{{ki_guardrails}}"
   → Nutzen: In ALLEN Quick Wins beachten, bei Prompts explizit erwähnen

5. VISION_3_JAHRE - Wohin soll die Reise gehen?
   Wert: "{{vision_3_jahre}}"
   → Nutzen: Quick Wins sollten zur langfristigen Vision passen

=============================================================================
BRANCHE UND GRÖSSE (für Komplexität und Tools):
=============================================================================

BRANCHE: {{BRANCHE_LABEL}}
GRÖSSE: {{UNTERNEHMENSGROESSE_LABEL}} (COMPANY_SIZE: {% if COMPANY_SIZE == "solo" %}solo{% elif COMPANY_SIZE == "team" %}team{% else %}kmu{% endif %})
STUNDENSATZ: {{STUNDENSATZ_EUR}}€/h

SCORES (für Priorisierung):
- Security: {{score_security}}/100 {% if score_security < 50 %}→ Security-Quick-Win priorisieren!{% endif %}
- Governance: {{score_governance}}/100 {% if score_governance < 50 %}→ Governance-Quick-Win priorisieren!{% endif %}

=============================================================================
ANZAHL NACH GRÖSSE:
=============================================================================
{% if COMPANY_SIZE == "solo" %}
- SOLO: Genau 3 Quick Wins
- Sprache: "Sie" (persönlich, direkt)
- Budget-Fokus: max 50€/Monat Tools
- Keine Team-/Enterprise-Begriffe!
{% elif COMPANY_SIZE == "team" %}
- TEAM: Genau 4 Quick Wins
- Sprache: "Sie/Ihr Team"
- Budget-Fokus: max 200€/Monat Tools
- Kollaboration erwähnen
{% else %}
- KMU: Genau 4-5 Quick Wins
- Sprache: "Ihr Unternehmen/Ihre Teams"
- Budget-Fokus: skalierbare Lösungen
- Governance-Aspekte einbauen
{% endif %}

=============================================================================
QUICK WIN #1 - FORMAT (STRIKT EINHALTEN!)
=============================================================================

Quick Win #1 MUSS so aufgebaut sein:

### Quick Win #1: [Titel bezogen auf {{ZEITERSPARNIS_PRIORITAET}}]

**🎯 Ihr Engpass:**
> "{{ZEITERSPARNIS_PRIORITAET}}"

**Aktuell:** [Beschreibe den manuellen Prozess basierend auf {{hauptleistung}}, 1-2 Sätze]
**Mit KI:** [Was wird automatisiert, konkret]

**⚡ Copy-Paste-Prompt für [TOOL-NAME]:**
```
[ECHTER funktionierender Prompt, der zu {{hauptleistung}} und {{BRANCHE_LABEL}} passt]
[Falls {{ki_guardrails}} vorhanden: "Hinweis: {{ki_guardrails}}" einbauen]
```

**Setup in [X] Tagen:**
1. **[Schritt mit Tool-Name]** ([Zeit], [Kosten])
2. **[Schritt]** ([Zeit])
3. **[Test/Rollout]** ([Zeit])

**ROI:** Spart [X]-[Y]h/Monat = [Betrag]€ (bei {{STUNDENSATZ_EUR}}€/h)

---

=============================================================================
QUICK WIN #2 - FORMAT (falls {{ki_projekte}} vorhanden)
=============================================================================

{% if ki_projekte %}
Quick Win #2 MUSS {{ki_projekte}} aufgreifen:

### Quick Win #2: [Titel bezogen auf {{ki_projekte}}]

**🎯 Ihr geplantes Projekt:**
> "{{ki_projekte}}"

**Der schnelle Einstieg:** [Wie KI beim geplanten Projekt hilft]
{% if ki_guardrails %}
**⚠️ Beachten Sie dabei:** {{ki_guardrails}}
{% endif %}

**⚡ Copy-Paste-Prompt:**
```
[Prompt der zum geplanten Projekt passt]
```

**Setup in [X] Tagen:**
1. **[Schritt]** ([Zeit])
2. **[Schritt]** ([Zeit])
3. **[Schritt]** ([Zeit])

**ROI:** [Konkreter Nutzen]

---
{% else %}
Quick Win #2 fokussiert auf Produktivität passend zu {{hauptleistung}}.
{% endif %}

=============================================================================
WEITERE QUICK WINS - FORMAT
=============================================================================

### Quick Win #X: [Titel]

**Problem:** [1-2 Sätze, bezogen auf {{BRANCHE_LABEL}} und {{hauptleistung}}]

**⚡ Copy-Paste-Prompt:**
```
[Konkreter Prompt]
```

**Setup in [X] Tagen:**
1. **[Schritt]** ([Zeit])
2. **[Schritt]** ([Zeit])

**ROI:** [Zeitersparnis und €-Wert]

---

=============================================================================
TOOL-EMPFEHLUNGEN (KONKRETE NAMEN!)
=============================================================================

SOLO-BUDGET (max 50€/Monat):
- ChatGPT Plus: 20€/Monat – Texte, Brainstorming
- Claude Pro: 18€/Monat – Lange Dokumente, Analyse
- Perplexity Pro: 20€/Monat – Research mit Quellen

TEAM-BUDGET (max 200€/Monat):
- Microsoft Copilot: 22€/Nutzer – Office-Integration
- Notion AI: 10€/Nutzer – Wissensmanagement
- Otter.ai: 17€/Monat – Meeting-Transkription

BRANCHEN-SPEZIFISCH:
- IT/Software: GitHub Copilot (19€/Monat)
- Beratung: Claude Pro + Perplexity Pro
- Marketing: Jasper (49€/Monat), Midjourney (10€/Monat)
- Finance/Recht: Microsoft Copilot (Compliance-Features)

=============================================================================
QUALITÄTS-CHECK VOR OUTPUT (ALLE müssen ✓ sein!):
=============================================================================

□ Quick Win #1 zitiert "{{ZEITERSPARNIS_PRIORITAET}}" WÖRTLICH in Blockquote?
□ Quick Win #1 passt zu "{{hauptleistung}}"?
□ Quick Win #2 referenziert "{{ki_projekte}}" (falls vorhanden)?
□ ALLE Quick Wins haben Copy-Paste-Prompts in Code-Blöcken?
□ ALLE Quick Wins haben 2-3 nummerierte Setup-Schritte mit Zeitangaben?
□ Tool-Namen sind KONKRET (nicht "KI-Tools")?
□ "{{ki_guardrails}}" werden beachtet (falls vorhanden)?
□ Sprache passt zur Größe (Solo: persönlich, Team: Kollaboration)?
□ Budget passt zur Größe?
□ ROI-Berechnung nutzt {{STUNDENSATZ_EUR}}?

=============================================================================
ANTI-PATTERN (NICHT TUN!):
=============================================================================

❌ "KI-gestützte Automatisierung" ohne konkretes Tool
❌ "Optimieren Sie Ihre Prozesse" ohne konkreten Prompt
❌ Generische E-Mail-Automatisierung für alle
❌ Abgeschnittene Zitate ("Umsetzung und Programmierung von Pro...")
❌ Enterprise-Jargon für Solo ("Stakeholder", "Framework", "Pipeline")
❌ Setup "in wenigen Minuten" (unrealistisch!)
❌ Prompts ohne Branchen-/Tätigkeitsbezug
❌ Guardrails ignorieren

=============================================================================
BEISPIEL-TRANSFORMATION:
=============================================================================

VORHER (generisch, schlecht):
"Prozessoptimierung für 'Umsetzung und Programmierung von Pro...':
KI-gestützte Automatisierung. Nutzen Sie Claude/GPT für Vorlagen."

NACHHER (personalisiert, gut):

### Quick Win #1: Fragebogen-Templates automatisch generieren

**🎯 Ihr Engpass:**
> "Umsetzung und Programmierung von interessanten Projekten"

**Aktuell:** Jeder KI-Readiness-Fragebogen wird manuell erstellt (3-5h)
**Mit KI:** Claude generiert Struktur und Fragen in 15 Minuten

**⚡ Copy-Paste-Prompt für Claude:**
```
Erstelle einen KI-Readiness-Fragebogen für [Branche einfügen]:
- 15 Fragen, Likert-Skala 1-5
- Kategorien: Strategie, Daten, Prozesse, Kultur
- Output: JSON für Typeform
- Hinweis: Keine Gesundheits- oder Finanzprognosen
```

**Setup in 2 Tagen:**
1. **Claude Pro aktivieren** (10 Min, 18€/Monat)
2. **Prompt testen** mit 3 Branchen (2h)
3. **5 Templates erstellen** und speichern (4h)

**ROI:** Spart 8-12h/Monat = 800-1.200€ (bei 100€/h)

=============================================================================
-->

## Quick Wins – Sofort umsetzbare Maßnahmen

{% if COMPANY_SIZE == "solo" %}
<p>Die folgenden <strong>3 Quick Wins</strong> sind speziell für Sie als Solo-Selbstständige/r im Bereich <strong>{{hauptleistung}}</strong> konzipiert. Sie adressieren direkt Ihren Zeitfresser und sind mit minimalem Budget umsetzbar.</p>
{% elif COMPANY_SIZE == "team" %}
<p>Die folgenden <strong>4 Quick Wins</strong> sind für Sie und Ihr Team im Bereich <strong>{{hauptleistung}}</strong> konzipiert. Sie verbessern Ihre Zusammenarbeit und sparen gemeinsam Zeit.</p>
{% else %}
<p>Die folgenden <strong>4-5 Quick Wins</strong> sind für Ihr Unternehmen im Bereich <strong>{{hauptleistung}}</strong> konzipiert. Sie bieten skalierbare Lösungen mit klarem ROI.</p>
{% endif %}

<!--
=============================================================================
GENERIERE JETZT die Quick Wins nach den obigen Regeln!

PFLICHT-CHECKLISTE:
✓ Quick Win #1: Zitiere "{{ZEITERSPARNIS_PRIORITAET}}" wörtlich
✓ Quick Win #2: Referenziere "{{ki_projekte}}" (falls vorhanden)
✓ Alle: Copy-Paste-Prompts in Code-Blöcken
✓ Alle: 2-3 nummerierte Setup-Schritte
✓ Alle: Konkrete Tool-Namen und Preise
✓ Beachte: "{{ki_guardrails}}" (falls vorhanden)
✓ Sprache: {% if COMPANY_SIZE == "solo" %}Solo (persönlich, "Sie"){% elif COMPANY_SIZE == "team" %}Team ("Sie/Ihr Team"){% else %}KMU (professionell){% endif %}
=============================================================================
-->

<p class="small muted">Diese Quick Wins basieren auf Ihrer spezifischen Situation in {{BRANCHE_LABEL}}. Zeitersparnisse sind Erfahrungswerte und variieren je nach Umsetzung.</p>
