Developer:
<!-- PLATIN+++ PROMPT v6.0 - DYNAMIC QUICK WINS (Phase 2 Fix) -->
<!-- SECTION: quick_wins -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- PHASE 2: Completely dynamic - NO static templates! -->
<!-- INPUT: {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}}, {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, COMPANY_SIZE, {{STUNDENSATZ_EUR}}, {{score_security}}, {{score_governance}}, {{KI_GUARDRAILS}} -->
<!-- TOKEN-BUDGET: 3500 (solo:0.9x=3150, team:1.0x=3500, kmu:1.1x=3850) -->
<!--
=============================================================================
PLATIN+++ v6.0: DYNAMISCHE QUICK WINS (Phase 2 Individualisierung)
=============================================================================

KRITISCHE ÄNDERUNG v6.0:
Die Quick Wins sind NICHT mehr statisch! Sie werden individuell generiert
basierend auf den echten Briefing-Daten des Users.

=============================================================================
INDIVIDUALISIERUNGS-KONTEXT (PFLICHT - DIESE DATEN NUTZEN!)
=============================================================================

KERNGESCHÄFT DES USERS (Quick Wins müssen hierzu passen):
{{hauptleistung}}

WO VERLIERT DER USER ZEIT (Hauptfokus für Quick Win #1):
{{ZEITERSPARNIS_PRIORITAET}}

BRANCHE (für branchenspezifische Tool-Empfehlungen):
{{BRANCHE_LABEL}}

UNTERNEHMENSGRÖSSE (für Komplexität und Budget):
{{UNTERNEHMENSGROESSE_LABEL}} (COMPANY_SIZE: {% if COMPANY_SIZE == "solo" %}solo{% elif COMPANY_SIZE == "team" %}team{% else %}kmu{% endif %})

STUNDENSATZ FÜR ROI-BERECHNUNG:
{{STUNDENSATZ_EUR}}€/h (Fallback: solo=100€, team=75€, kmu=70€)

SCORES (für Priorisierung):
- Security: {{score_security}}/100 {% if score_security < 50 %}→ Security-Quick-Win priorisieren!{% endif %}
- Governance: {{score_governance}}/100 {% if score_governance < 50 %}→ Governance-Quick-Win priorisieren!{% endif %}

EINSCHRÄNKUNGEN (in Empfehlungen beachten):
{{KI_GUARDRAILS}}

=============================================================================
GENERIERUNGSREGELN (STRIKT EINHALTEN!)
=============================================================================

REGEL 1: QUICK WIN #1 MUSS sich auf {{ZEITERSPARNIS_PRIORITAET}} beziehen
- Der User hat explizit angegeben, wo er Zeit verliert
- Quick Win #1 adressiert GENAU dieses Problem
- KEINE generische "E-Mail-Automatisierung" wenn der User "Programmierung" sagt!

REGEL 2: Alle Quick Wins müssen zu {{hauptleistung}} passen
- Ein KI-Berater bekommt andere Quick Wins als ein Fotograf
- Beziehe die Tool-Nutzung auf die tatsächliche Arbeit des Users
- Beispiel-Prompts müssen zur Branche passen

REGEL 3: Score-basierte Priorisierung
- Wenn {{score_security}} < 50: Ein Quick Win muss Security adressieren
- Wenn {{score_governance}} < 50: Ein Quick Win muss Governance adressieren
- Höhere Scores = weniger Fokus auf dieses Thema

REGEL 4: Branchen-spezifische Tools
- {{BRANCHE_LABEL}} bestimmt welche Tools sinnvoll sind
- Finance/Recht: Compliance-Tools priorisieren
- Kreativ/Marketing: Content-Tools priorisieren
- IT/Software: Developer-Tools priorisieren
- Beratung: Analyse/Research-Tools priorisieren

REGEL 5: Guardrails beachten
- {{KI_GUARDRAILS}} enthält Einschränkungen des Users
- NIEMALS Tools empfehlen, die gegen Guardrails verstoßen
- Beispiel: "keine Gesundheitsprognosen" → keine Diagnose-Tools

=============================================================================
ANZAHL NACH GRÖSSE:
=============================================================================
{% if COMPANY_SIZE == "solo" %}
- SOLO: Genau 3 Quick Wins (je 250-350 Wörter)
- Fokus: Persönliche Produktivität, niedrige Kosten, schneller ROI
{% elif COMPANY_SIZE == "team" %}
- TEAM: Genau 4 Quick Wins (je 250-350 Wörter)
- Fokus: Team-Workflows, Wissensteilung, moderate Investition
{% else %}
- KMU: Genau 4-5 Quick Wins (je 250-350 Wörter)
- Fokus: Skalierbare Prozesse, Governance, Enterprise-Tools
{% endif %}

=============================================================================
FORMAT PRO QUICK WIN (STRIKT EINHALTEN!):
=============================================================================

### QUICK WIN #X: [Titel bezogen auf {{hauptleistung}}] ([Zeitersparnis]/Monat)

**Problem:** [1-2 Sätze: Konkreter Zeitfresser aus {{ZEITERSPARNIS_PRIORITAET}} oder Branche]

**Lösung in 3 Schritten:**

1. **[Schritt-Titel]** (Setup: [Zeit])
   - Tool: [Konkreter Name] ([Preis/Monat]) – [Empfehlung für {{BRANCHE_LABEL}}]
   - [Konkrete Anweisung passend zu {{hauptleistung}}]

2. **[Schritt-Titel]** ([Zeit])
   - [Workflow-Beschreibung]
   - Beispiel-Prompt für {{BRANCHE_LABEL}}:
     > "[Konkreter Prompt passend zu {{hauptleistung}} - zum Copy-Paste]"

3. **[Schritt-Titel]** ([Zeit])
   - [Test-/Rollout-Anweisung]
   - {% if KI_GUARDRAILS %}Beachte: {{KI_GUARDRAILS}}{% endif %}

**Investment & ROI:**
| Aufwand | Wert |
|---------|------|
| Setup-Zeit | [X] Stunden |
| Laufende Kosten | [Y]€/Monat |
| Zeitersparnis | [Z] Std./Monat |
| Wert (bei {{STUNDENSATZ_EUR}}€/h) | [Betrag]€/Monat |
| Payback | [Wochen/Monate] |

**Risiken & Mitigationen:**
- [Risiko 1] → [Lösung]
- [Risiko 2] → [Lösung]

---

=============================================================================
TOOL-EMPFEHLUNGEN (nutze diese konkreten Namen!):
=============================================================================
ALLGEMEIN:
- ChatGPT Plus: 20€/Monat – Allrounder, gut für Texte
- Claude Pro: 18€/Monat – Längere Dokumente, Analyse
- Microsoft Copilot: 22€/Monat – Office-Integration
- Perplexity Pro: 20€/Monat – Research mit Quellen

BRANCHEN-SPEZIFISCH:
- Beratung/Consulting: Claude Pro, Perplexity Pro, Notion AI
- Finance/Recht: Microsoft Copilot (Compliance), Claude Pro (Analyse)
- IT/Software: GitHub Copilot (19€/Monat), Claude Pro (Code-Review)
- Marketing/Kreativ: Jasper (49€/Monat), Midjourney (10€/Monat)
- Gesundheit: VORSICHT - nur mit Arzt-Review, keine Diagnosen!

PRODUKTIVITÄT:
- Notion AI: 10€/Monat – Wissensmanagement
- Otter.ai: 17€/Monat – Meeting-Transkription
- Grammarly Business: 15€/Nutzer/Monat – Textqualität
- DeepL Pro: 25€/Monat – Übersetzungen

=============================================================================
BEISPIEL-TRANSFORMATION (vorher → nachher):
=============================================================================

VORHER (statisch, generisch):
Quick Win #1: E-Mail-Entwürfe automatisieren
→ Identisch für KI-Berater UND Fotografen

NACHHER (dynamisch, individuell):

Für KI-Berater (hauptleistung="Beratung mittels Fragebogen und GPT"):
Quick Win #1: Report-Templates standardisieren
- Basierend auf ZEITERSPARNIS_PRIORITAET="Umsetzung und Programmierung"
- Tool: Claude Pro für Analyse-Workflows
- Prompt: "Analysiere diesen Fragebogen und erstelle ein Executive Summary..."

Für Fotografen (hauptleistung="Hochzeitsfotografie"):
Quick Win #1: Bildauswahl mit KI beschleunigen
- Basierend auf ZEITERSPARNIS_PRIORITAET="Bildbearbeitung"
- Tool: Adobe Lightroom + AI-Culling
- Prompt: "Sortiere diese 500 Bilder nach Qualität und Emotion..."

=============================================================================
QUALITÄTS-SELBSTCHECK VOR OUTPUT:
=============================================================================
□ Quick Win #1 adressiert {{ZEITERSPARNIS_PRIORITAET}}?
□ Alle Quick Wins passen zu {{hauptleistung}}?
□ Tool-Empfehlungen passen zu {{BRANCHE_LABEL}}?
□ ROI-Berechnung nutzt {{STUNDENSATZ_EUR}}?
□ Bei niedrigen Scores: Security/Governance-Quick-Win enthalten?
□ {{KI_GUARDRAILS}} werden beachtet (falls vorhanden)?
□ Keine generischen "E-Mail-Automatisierung" für alle?
□ Beispiel-Prompts sind branchenspezifisch?
=============================================================================
-->

## Quick Wins – Sofort umsetzbare Maßnahmen

{% if COMPANY_SIZE == "solo" %}
Die folgenden 3 Quick Wins sind speziell für Solo-Selbstständige mit Fokus auf **{{hauptleistung}}** konzipiert und adressieren direkt das Thema **{{ZEITERSPARNIS_PRIORITAET}}**:
{% elif COMPANY_SIZE == "team" %}
Die folgenden 4 Quick Wins sind für Teams im Bereich **{{hauptleistung}}** konzipiert und adressieren direkt das Thema **{{ZEITERSPARNIS_PRIORITAET}}**:
{% else %}
Die folgenden 4-5 Quick Wins sind für KMU im Bereich **{{hauptleistung}}** konzipiert und adressieren direkt das Thema **{{ZEITERSPARNIS_PRIORITAET}}**:
{% endif %}

<!--
=============================================================================
JETZT GENERIEREN: Individuelle Quick Wins basierend auf dem Kontext oben
=============================================================================

ERINNERUNG:
- Quick Win #1 MUSS {{ZEITERSPARNIS_PRIORITAET}} adressieren
- Alle Quick Wins müssen zu {{hauptleistung}} passen
- Tool-Empfehlungen müssen zu {{BRANCHE_LABEL}} passen
- Bei score_security < 50 oder score_governance < 50: Entsprechenden Quick Win einbauen
- {{KI_GUARDRAILS}} beachten!

GENERIERE JETZT die Quick Wins im Format oben.
KEINE STATISCHEN TEMPLATES - INDIVIDUELLE INHALTE!
=============================================================================
-->

*Diese Quick Wins basieren auf der spezifischen Analyse für {{BRANCHE_LABEL}} im Bereich {{hauptleistung}}. Priorisiert nach dem angegebenen Zeitfresser: {{ZEITERSPARNIS_PRIORITAET}}. Tatsächliche Einsparungen variieren je nach Umsetzungskonsequenz.*
