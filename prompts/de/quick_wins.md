# Quick Wins - JSON Output v8.0
<!-- Problem #7 FIX: Hauptleistung als Analyse-Kern -->

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

## JSON-FORMAT (EXAKT SO VERWENDEN!)

```json
[
  {
    "title": "Kurzer prägnanter Titel (max 60 Zeichen)",
    "icon": "🎯",
    "time": "6-10 h/Monat",
    "engpass": "Ihr konkreter Zeitfresser/Pain Point aus ZEITERSPARNIS_PRIORITAET",
    "description": "Was ist das Problem? 2-3 Sätze, konkret auf Branche bezogen.",
    "mit_ki": "Wie hilft KI konkret? Welche Tools? 2-3 Sätze.",
    "steps": [
      "Konkreter Schritt 1 mit Zeitangabe (z.B. 30min)",
      "Konkreter Schritt 2 mit Tool-Namen",
      "Konkreter Schritt 3 mit messbarem Ergebnis"
    ],
    "zeitersparnis": "6-10 h/Monat = 600-1.000€ (bei {{STUNDENSATZ_EUR}}€/h)"
  }
]
```

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

## QUALITY-CHECKS (VOR OUTPUT PRÜFEN!)

- [ ] Valides JSON (keine trailing commas, escaped quotes)
- [ ] 3-5 Quick Wins im Array
- [ ] Jeder Quick Win hat alle 8 Felder: title, icon, time, engpass, description, mit_ki, steps, zeitersparnis
- [ ] Icons sind Emojis (nicht Text)
- [ ] steps ist Array mit 3-5 Strings
- [ ] Keine HTML-Tags im JSON
- [ ] Quick Win #1 zitiert ZEITERSPARNIS_PRIORITAET
- [ ] Tool-Namen sind KONKRET (nicht "KI-Tools")
- [ ] Guardrails werden beachtet (falls vorhanden)

## HAUPTLEISTUNG-BEZUG: BEISPIEL-TRANSFORMATION

**Hauptleistung des Kunden:** "Online-Shop für Büromöbel"

❌ **SCHLECHT (zu generisch):**
"E-Mail-Automatisierung einführen" – kein Bezug zu Büromöbeln

✅ **RICHTIG (hauptleistungsbezogen):**
"Produktbeschreibungen für neue Büromöbel mit KI generieren – spart 3h/Woche bei neuen Möbel-Listings"

---

## BEISPIEL (Beratungsbranche)

```json
[
  {
    "title": "Ablauf-Blueprint für Ihre KI-Beratungsprojekte",
    "icon": "🎯",
    "time": "6-10 h/Monat",
    "engpass": "Entwicklung und Optimierung von Abläufen",
    "description": "Aktuell strukturieren Sie jeden Beratungsablauf (Fragebogen, Auswertung, Report) neu und optimieren ad hoc – das kostet viel Denk- und Dokumentationszeit.",
    "mit_ki": "ChatGPT Plus erstellt mit Ihnen einen wiederverwendbaren Standard-Workflow inkl. Checklisten und Textbausteinen, den Sie nur noch leicht je Kunde anpassen.",
    "steps": [
      "ChatGPT Plus buchen (15 Min, 20€/Monat)",
      "Beste bisherige Projekte analysieren (2-3h)",
      "Standard-Workflow & Checklisten generieren (3-4h)"
    ],
    "zeitersparnis": "6-10 h/Monat = 600-1.000€ (bei 100€/h)"
  },
  {
    "title": "Testphase Ihres KI-Fragebogens in skalierbares MVP",
    "icon": "🚀",
    "time": "5-8 h/Monat",
    "engpass": "das Projekt mit der Beratung von Unternehmen zur Integration von KI",
    "description": "Sie testen das Angebot manuell, Auswertung und Reports entstehen jedes Mal neu und sind noch nicht als Produktpaket definiert.",
    "mit_ki": "Sie nutzen ChatGPT Plus, um feste Fragebogen-Varianten, Auswertungslogik und Report-Templates zu erstellen und als schlankes Online-MVP zu standardisieren.",
    "steps": [
      "Beste Testfälle clustern (2h, typische Kundentypen definieren)",
      "Fragebogen-Varianten mit GPT schärfen (3h)",
      "Standard-Reportstruktur bauen (3h)"
    ],
    "zeitersparnis": "5-8 h/Monat = 500-800€ (bei 100€/h)"
  },
  {
    "title": "KI-Sicherheitsrichtlinie erstellen",
    "icon": "🔒",
    "time": "2h Setup",
    "engpass": "Security-Score 45/100 (Handlungsbedarf)",
    "description": "Ohne klare Sicherheitsregeln riskieren Sie Datenschutzverletzungen bei der KI-Nutzung.",
    "mit_ki": "Claude Pro hilft Ihnen, eine kompakte Richtlinie zu erstellen: Welche Daten dürfen in KI-Tools? Welche Tools sind freigegeben?",
    "steps": [
      "Datenklassifikation erstellen (1h)",
      "Tool-Freigabeliste definieren (30min)",
      "Prüfregeln dokumentieren (30min)"
    ],
    "zeitersparnis": "Risikominimierung + Compliance"
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
