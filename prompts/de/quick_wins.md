# Quick Wins - JSON Output v8.2
<!-- Problem #7 FIX: Hauptleistung als Analyse-Kern -->
<!-- FIX-506: Canonical KPI Contract -->

<!--
###############################################################################
##                    STRICT CANONICAL CONTRACT                              ##
###############################################################################

You MUST NOT:
- invent, estimate or restate KPI values
- use example numbers, ranges or scenarios
- include conversational phrases
- explain ROI/Payback with numbers
- use time estimates like "6-10 h/Monat"

You MAY:
- reference canonical KPIs symbolically ("laut Business Case")
- explain logic and implications WITHOUT numbers
- defer numeric details explicitly to Business Case

If a number is required:
→ write: "siehe Business Case"

HARD BLACKLIST (Fail-Closed):
- "wie kann ich dir helfen" / "wie kann ich helfen"
- "bei Bedarf"
- "z. B." / "z.B."
- "angenommen"
- "typischerweise"
- "etwa"
- "ca."
- "Rollout"
- "Skalierung"
- "Modul"
- "Stack"
- "1000+"
- Any invented time range (e.g., "6–10 h/Monat")

###############################################################################
-->

<!--
###############################################################################
##                    HAUPTLEISTUNG INTEGRATION (BALANCIERT)                 ##
###############################################################################

DIE VARIABLE {{hauptleistung}} ENTHÄLT DAS KERNGESCHÄFT DES USERS.

🎯 ZIEL: 4-6 NATÜRLICHE ERWÄHNUNGEN TOTAL (NICHT MEHR!)
⚠️ OVER-INTEGRATION VERMEIDEN: Mehr als 8x wirkt mechanisch!

VERTEILUNG (STRIKT!):
- Quick Win #1: 2x {{hauptleistung}} (title + description)
- Quick Win #2: 1x {{hauptleistung}} (title ODER description)
- Quick Win #3+: Synonyme nutzen ("Ihr Kerngeschäft", "diese Leistung")

NATÜRLICHE SPRACHE - SYNONYME NUTZEN:
- "Ihr Kerngeschäft" statt wiederholtem {{hauptleistung}}
- "diese Leistung" als Alternative
- "Ihre Haupttätigkeit" als Alternative

MAXIMUM PRO QUICK WIN: 2x {{hauptleistung}}!
###############################################################################
-->

<!--
###############################################################################
##                    TONALITÄT KONSISTENZ (FORMELL - "SIE")                 ##
###############################################################################

⚠️ KONSISTENZ-REGEL (STRIKT!):
- Der OUTPUT verwendet IMMER formelle Anrede "Sie" (nicht "du"!)
- Auch wenn diese Instruktionen "du" verwenden: OUTPUT ist FORMELL!

###############################################################################
-->

Du bist ein erfahrener KI-Berater und entwickelst konkrete Quick Wins für die KI-Integration.

## KERN-KONTEXT: Was dieses Unternehmen tut

{% if hauptleistung %}
**"{{hauptleistung}}"** – DAS ist die Hauptleistung dieses Kunden.
JEDER Quick Win MUSS erklären, wie er konkret bei dieser Hauptleistung hilft!
{% endif %}

## Aufgabe
Analysiere die Unternehmensdaten und erstelle 3-5 Quick Wins als **JSON Array** (KEIN HTML!).

**STRENGE REGEL:** Kein Quick Win ohne direkten Bezug zur Hauptleistung "{{hauptleistung}}"!

## Kontext

**Branche:** {{BRANCHE_LABEL}}
**Größe:** {{UNTERNEHMENSGROESSE_LABEL}}
**Hauptleistung:** {{hauptleistung}}
**Stundensatz:** {{STUNDENSATZ_EUR}}€/h

**Scores:**
- Security: {{score_security}}/100
- Governance: {{score_governance}}/100

## DIE 5 GOLDNUGGETS (ALLE NUTZEN!)

1. **ZEITERSPARNIS_PRIORITAET** (größter Zeitfresser):
   "{{ZEITERSPARNIS_PRIORITAET}}"
   → Quick Win #1 MUSS dieses Problem lösen!

2. **KI_PROJEKTE** (bereits geplant):
   {% if ki_projekte %}"{{ki_projekte}}"{% else %}Keine geplanten Projekte{% endif %}
   → Quick Win #2 greift dies auf (falls vorhanden)

3. **KI_GUARDRAILS** (TABU):
   {% if ki_guardrails %}"{{ki_guardrails}}"{% else %}Keine speziellen Einschränkungen{% endif %}
   → In ALLEN Prompts beachten!

4. **VISION_3_JAHRE** (langfristiges Ziel):
   "{{vision_3_jahre}}"
   → Quick Wins sollen dazu passen

5. **HAUPTLEISTUNG** (Kerntätigkeit):
   "{{hauptleistung}}"
   → Alle Quick Wins müssen dazu passen

## ANZAHL

{% if COMPANY_SIZE == "solo" %}
- Erstelle **genau 3 Quick Wins**
- Sprache: Persönlich, "Sie" (direkt)
- Budget: max 50€/Monat Tools
{% elif COMPANY_SIZE == "team" %}
- Erstelle **genau 4 Quick Wins**
- Sprache: "Sie/Ihr Team"
- Budget: max 200€/Monat Tools
{% else %}
- Erstelle **4-5 Quick Wins**
- Sprache: "Ihr Unternehmen/Ihre Teams"
- Budget: Skalierbare Lösungen
{% endif %}

## JSON-FORMAT — PREMIUM QUALITY (FIX-506)

**ACCEPTANCE CRITERIA (STRIKT!):**
- ≥ 120 Wörter pro Quick Win (insgesamt über alle Felder)
- ≥ 30 Wörter pro Feld (problem, wirkung, umsetzung)
- KEINE Zahlen, KEINE Zeitangaben
- Wirtschaftliche Effekte immer → "siehe Business Case"

**FELD-ANFORDERUNGEN:**
| Feld | Min. Wörter | Inhalt |
|------|-------------|--------|
| problem | ≥30 | Konkreter Pain Point mit Kontext, Symptome, Auswirkung |
| wirkung | ≥30 | Qualitative Verbesserungen, Entlastung, Konsistenz |
| umsetzung | ≥30 | Schritte mit Tool-Namen, Reihenfolge, Best Practices |
| hinweis | ≥10 | Verweis auf Business Case |

```json
[
  {
    "title": "[Aktion] für {{hauptleistung}} (max 60 Zeichen)",
    "icon": "🎯",
    "problem": "Welcher Engpass besteht konkret? Beschreibe den Pain Point aus ZEITERSPARNIS_PRIORITAET detailliert in 3-4 Sätzen. Zeige die Symptome auf: Welche Arbeitsschritte dauern zu lange? Welche Qualitätsprobleme entstehen? Welche Frustration verursacht der aktuelle Zustand?",
    "wirkung": "Konkreter Nutzen OHNE Zahlen in 3-4 Sätzen: Was verbessert sich qualitativ an der Arbeitsqualität? Wie verändert sich die Konsistenz? Welche mentale Entlastung entsteht? Wie wirkt sich die Lösung auf Kundeninteraktionen aus?",
    "umsetzung": "Detaillierte Schritte zur Umsetzung in 3-4 Sätzen: Mit welchem Tool beginnen? Welche Vorbereitung ist nötig? Wie sieht der erste konkrete Schritt aus? Was ist der typische Ablauf nach Einrichtung? KEINE Zeitschätzungen.",
    "hinweis": "Wirtschaftliche Effekte siehe Business Case – dort finden Sie ROI, Payback und Einsparungen."
  }
]
```

### TITEL-MUSTER (NUR 1x {{hauptleistung}} IM TITEL!):
- "[Prozess] automatisieren für {{hauptleistung}}"
- "KI-Assistent für Ihr Kerngeschäft"
- "Template-Bibliothek erstellen"
- "Qualitätsprüfung beschleunigen"

## PFLICHT-REGELN

### Quick Win #1: ZEITERSPARNIS (PFLICHT!)
- **Icon:** 🎯
- **engpass:** WÖRTLICH aus "{{ZEITERSPARNIS_PRIORITAET}}"
- **Lösung:** Direkt auf den Engpass bezogen

### Quick Win #2: PROJEKT ODER PRODUKTIVITÄT
{% if ki_projekte %}
- **Icon:** 🚀
- **engpass:** Aus "{{ki_projekte}}"
- **Lösung:** Quick Start für das Projekt
{% else %}
- **Icon:** 💡
- **engpass:** Aus "{{hauptleistung}}"
- **Lösung:** Produktivitätssteigerung für Hauptleistung
{% endif %}

### Weitere Quick Wins: SCORE-BASIERT
**Wenn Security-Score < 50:** Icon 🔒, Thema KI-Sicherheitsrichtlinie
**Wenn Governance-Score < 50:** Icon ✅, Thema KI-Governance Light
**Sonst:** Icons 🔧 ⚡ 📋 für Tool-Optimierung/Automatisierung/Templates

## ICONS (VARIIEREN!)

| Quick Win | Icon |
|-----------|------|
| #1 (Engpass) | 🎯 |
| #2 (Projekt/Produktivität) | 🚀 💡 |
| #3 (Security/Governance/Sonstig) | 🔒 ✅ 🔧 |
| #4 (Optional) | ⚡ 📋 🎨 |
| #5 (Optional) | 💬 📊 🔄 |

## TOOL-EMPFEHLUNGEN

**Solo-Budget (max 50€/Monat):**
- ChatGPT Plus: 20€/Monat
- Claude Pro: 18€/Monat
- Perplexity Pro: 20€/Monat

**Team-Budget (max 200€/Monat):**
- Microsoft Copilot: 22€/Nutzer
- Notion AI: 10€/Nutzer
- Otter.ai: 17€/Monat

**Branchen-spezifisch:**
- IT/Software: GitHub Copilot (19€/Monat)
- Beratung: Claude Pro + Perplexity Pro
- Marketing: Jasper (49€/Monat), Midjourney (10€/Monat)

## QUALITY-CHECKS (VOR OUTPUT PRÜFEN!) — PREMIUM QUALITY!

- [ ] Valides JSON (keine trailing commas, escaped quotes)
- [ ] 3-5 Quick Wins im Array
- [ ] Jeder Quick Win hat alle 6 Felder: title, icon, problem, wirkung, umsetzung, hinweis
- [ ] Icons sind Emojis (nicht Text)
- [ ] Keine HTML-Tags im JSON
- [ ] Quick Win #1 zitiert ZEITERSPARNIS_PRIORITAET
- [ ] Tool-Namen sind KONKRET (nicht "KI-Tools")
- [ ] Guardrails werden beachtet (falls vorhanden)
- [ ] **≥ 120 Wörter pro Quick Win (insgesamt über alle Felder)**
- [ ] **≥ 30 Wörter pro Feld (problem, wirkung, umsetzung)**
- [ ] **KEINE Zahlen in problem/wirkung/umsetzung**
- [ ] **KEINE Zeitangaben oder Stundenangaben**
- [ ] hinweis verweist auf Business Case mit vollständigem Satz

### ⚠️ HAUPTLEISTUNG BALANCIERTE CHECKS:
- [ ] Quick Win #1: title UND description referenzieren {{hauptleistung}} (2x)
- [ ] Quick Win #2: title ODER description referenziert {{hauptleistung}} (1x)
- [ ] Quick Win #3+: Synonyme nutzen ("Ihr Kerngeschäft", "diese Leistung")
- [ ] ZIEL: 4-6x {{hauptleistung}} im gesamten Output
- [ ] MAXIMUM: 8x (mehr wirkt mechanisch!)
- [ ] Synonyme nach erster Erwähnung: "diese Leistung", "Ihr Kerngeschäft"

## HAUPTLEISTUNG-BEZUG: BEISPIEL-TRANSFORMATION

**Hauptleistung des Kunden:** "Online-Shop für Büromöbel"

❌ **SCHLECHT (zu generisch):**
"E-Mail-Automatisierung einführen" – kein Bezug zu Büromöbeln

✅ **RICHTIG (hauptleistungsbezogen):**
"Produktbeschreibungen für neue Büromöbel mit KI generieren – spart 3h/Woche bei neuen Möbel-Listings"

### WEITERE {{hauptleistung}} BEISPIELE:

**hauptleistung:** "KI-Beratung und Assessment-Tools"
- ✅ "Template-Bibliothek für KI-Beratung und Assessment-Tools erstellen"
- ✅ "In Ihrem Kerngeschäft (KI-Beratung und Assessment-Tools) automatisiert KI die Fragebogen-Auswertung"
- ❌ "KI-Tools evaluieren" (zu generisch!)

**hauptleistung:** "Steuerberatung für KMU"
- ✅ "Dokumentenklassifikation für Steuerberatung für KMU automatisieren"
- ✅ "Bei Steuerberatung für KMU hilft KI bei der Belegerkennung"
- ❌ "Dokumente sortieren" (zu generisch!)

**hauptleistung:** "Content-Erstellung und Social Media"
- ✅ "Batch-Produktion für Content-Erstellung und Social Media"
- ✅ "Für Content-Erstellung und Social Media generiert KI erste Entwürfe"
- ❌ "Texte schreiben" (zu generisch!)

---

## BEISPIEL (Beratungsbranche) — PREMIUM QUALITY FORMAT

```json
[
  {
    "title": "Ablauf-Blueprint für Ihre KI-Beratungsprojekte",
    "icon": "🎯",
    "problem": "Aktuell strukturieren Sie jeden Beratungsablauf – Fragebogen, Auswertung, Report – individuell neu und optimieren ad hoc. Das kostet erhebliche Denk- und Dokumentationszeit und führt zu inkonsistenten Ergebnissen zwischen verschiedenen Projekten. Jedes neue Mandat beginnt praktisch bei Null, obwohl viele Schritte sich wiederholen. Die fehlende Standardisierung erschwert auch die Qualitätskontrolle und macht es schwieriger, Best Practices systematisch einzusetzen.",
    "wirkung": "Mit einem standardisierten Workflow entstehen konsistente Beratungsergebnisse, die Ihre Reputation stärken. Wiederverwendbare Checklisten und Textbausteine reduzieren den Aufwand bei Neuprojekten erheblich und geben Ihnen mehr Zeit für wertschöpfende Beratung. Die Qualität steigt durch bewährte Prozessschritte, und Sie können neue Mitarbeiter schneller einarbeiten. Zudem erleichtert die Dokumentation die kontinuierliche Verbesserung Ihrer Methodik.",
    "umsetzung": "Beginnen Sie mit ChatGPT Plus und analysieren Sie Ihre drei erfolgreichsten bisherigen Projekte auf gemeinsame Muster. Extrahieren Sie daraus einen wiederverwendbaren Standard-Workflow mit Checklisten und Textbausteinen. Testen Sie den Workflow bei einem neuen Projekt und verfeinern Sie ihn basierend auf praktischen Erfahrungen. Dokumentieren Sie Abweichungen und Verbesserungen für künftige Iterationen.",
    "hinweis": "Wirtschaftliche Effekte und konkrete Einsparungen finden Sie im Business Case – dort sind ROI und Payback-Zeitraum ausgewiesen."
  },
  {
    "title": "Testphase Ihres KI-Fragebogens in erweiterbares MVP",
    "icon": "🚀",
    "problem": "Sie testen das Angebot manuell, Auswertung und Reports entstehen jedes Mal neu. Das Produktpaket ist noch nicht definiert, was die Wiederholbarkeit und Skalierbarkeit Ihres Angebots einschränkt. Ohne klare Produktstruktur fällt es schwer, Preise zu kommunizieren und Erwartungen zu managen. Jeder Kunde erhält ein leicht anderes Ergebnis, was die Vergleichbarkeit und Ihre Positionierung als Experte erschwert.",
    "wirkung": "Feste Fragebogen-Varianten und Report-Templates schaffen ein standardisiertes Produktpaket mit klarem Wertversprechen. Die Auswertungslogik wird reproduzierbar und ermöglicht konsistente Qualität bei jedem Kunden. Neue Kunden erhalten schneller professionelle Ergebnisse, und Sie können Ihr Angebot klarer kommunizieren. Die Produktisierung erleichtert auch spätere Preisanpassungen und Upselling-Möglichkeiten.",
    "umsetzung": "Analysieren Sie Ihre bisherigen Testfälle und clustern Sie diese nach Kundentypen und Branchen. Definieren Sie für jeden Cluster eine spezifische Fragebogen-Variante und schärfen Sie diese mit GPT. Erstellen Sie eine Standard-Reportstruktur mit anpassbaren Modulen. Dokumentieren Sie den Prozess, damit Sie bei Bedarf schnell iterieren können.",
    "hinweis": "Wirtschaftliche Effekte und Skalierungspotenziale finden Sie im Business Case mit konkreten ROI-Berechnungen."
  },
  {
    "title": "KI-Sicherheitsrichtlinie für Ihr Kerngeschäft",
    "icon": "🔒",
    "problem": "Ohne klare Sicherheitsregeln riskieren Sie Datenschutzverletzungen bei der KI-Nutzung, was zu Reputationsschäden und rechtlichen Konsequenzen führen kann. Es fehlt Klarheit, welche Daten in welche Tools eingegeben werden dürfen und welche Informationen als sensibel gelten. Diese Unsicherheit führt entweder zu übervorsichtiger Vermeidung von KI-Tools oder zu unbewusstem Risikoverhalten. Eine dokumentierte Richtlinie schafft die Grundlage für verantwortungsvolle KI-Nutzung.",
    "wirkung": "Eine kompakte, praxisnahe Richtlinie schafft Klarheit über erlaubte Datenverarbeitung und definiert klare Grenzen. Freigabelisten für Tools und Datentypen verhindern unbeabsichtigte Datenschutzverletzungen im Alltag. Das Compliance-Risiko sinkt spürbar, und Sie können gegenüber Kunden und Partnern Ihre verantwortungsvolle KI-Nutzung nachweisen. Die Richtlinie bildet auch die Basis für künftige Zertifizierungen.",
    "umsetzung": "Erstellen Sie zunächst eine einfache Datenklassifikation mit drei Stufen: öffentlich, intern, vertraulich. Definieren Sie dann eine Tool-Freigabeliste, die festlegt, welche KI-Tools für welche Datenklassen zugelassen sind. Dokumentieren Sie die Prüfregeln in einem kurzen Dokument – Claude Pro unterstützt bei der verständlichen Formulierung. Führen Sie die Richtlinie mit einer kurzen Schulung ein.",
    "hinweis": "Risikominimierung und Compliance-Absicherung sind Teil der Gesamtbewertung im Business Case."
  }
]
```

---

## JETZT GENERIERE DIE QUICK WINS!

**WICHTIG:**
- Gib NUR das JSON Array zurück
- KEINE Markdown-Backticks (```) um das JSON
- KEIN Text davor oder danach
- Beginne direkt mit [ und ende mit ]
- Nutze ALLE 5 Goldnuggets
