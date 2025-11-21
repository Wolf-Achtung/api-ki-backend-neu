# PROMPT: Recommendations - Konkrete Handlungsempfehlungen

## ZWECK
Erstelle 5-7 konkrete, priorisierte Handlungsempfehlungen die:
1. Auf den **Analyse-Ergebnissen** (Scores, Gaps) basieren
2. **Spezifisch für {{HAUPTLEISTUNG}}** sind (nicht generisch!)
3. Mit **Priorität** (H/M/N), **Zeitrahmen** (30/60/90 Tage) und **ROI-Hinweis** versehen sind
4. Eine klare **Umsetzungs-Roadmap** von Quick Wins → Skalierung → Gamechanger bilden

**Zielgruppe:** Entscheider:innen, Projekt-Owner, Umsetzungs-Teams
**Stil:** Konkret, umsetzbar, motivierend - KEINE vagen Ratschläge!

---

## ⚠️ KRITISCHE REGELN - ZWINGEND BEACHTEN!

### ❌ VERBOTEN - Folgendes NIEMALS empfehlen:

1. **KEINE generischen Standard-Empfehlungen:**
   - ❌ "KI-Schulungen für Mitarbeiter durchführen"
   - ❌ "KI-Strategie entwickeln und dokumentieren"
   - ❌ "Change-Management-Prozess initiieren"
   - ❌ "Pilot-Projekte starten und evaluieren"
   - ❌ "Governance-Strukturen aufbauen"

2. **KEINE Empfehlungen ohne ROI/Nutzen-Bezug:**
   - ❌ "Einführung eines KI-Beirats" (Warum? Was bringt's?)
   - ❌ "Regelmäßige KI-Updates" (Welcher Nutzen konkret?)
   - ❌ "Dokumentation erstellen" (Für was? Welcher Impact?)
   - ❌ "Compliance prüfen" (Was genau? Mit welchem Ergebnis?)

3. **KEINE Wiederholung von Quick Wins (außer Prio H):**
   - ❌ Quick Wins sind bereits in eigener Section!
   - ✅ NUR Top 1-2 Quick Wins als Prio [H] wenn sehr kritisch
   - ✅ Sonst: Fokus auf Skalierung & Governance-Themen

4. **KEINE vagen Zeitrahmen oder Kosten:**
   - ❌ "Mittelfristig umsetzen"
   - ❌ "Budget nach Bedarf"
   - ❌ "Zeitaufwand variabel"
   - ❌ "ROI schwer zu beziffern"

### ✅ STATTDESSEN - Fokus auf:

1. **Spezifische Empfehlungen für {{HAUPTLEISTUNG}}:**
   - ✅ "Batch-Processing für Assessment-Skalierung implementieren"
   - ✅ "DSGVO-Dokumentation für GPT-4-Nutzung erstellen"
   - ✅ "White-Label-Partner-Programm launchen"
   - ✅ "Self-Service-Portal für Kunden entwickeln"

2. **Klarer Nutzen & ROI:**
   - ✅ "10× Kapazität, -50% Kosten"
   - ✅ "Compliance-Risiko eliminiert"
   - ✅ "€10k MRR nach 6 Monaten"
   - ✅ "-70% Support-Anfragen"

3. **Konkrete nächste Aktionen:**
   - ✅ "Backend-Dev beauftragen (20h)"
   - ✅ "DSGVO-Anwalt Audit durchführen lassen (€1.500)"
   - ✅ "5 Partner onboarden (MVP-Phase)"
   - ✅ "Supabase Auth + Storage integrieren"

4. **Realistische Zeitrahmen mit Meilensteinen:**
   - ✅ "30 Tage: MVP ready, 60 Tage: 10 Beta-User"
   - ✅ "90 Tage: Audit abgeschlossen, Zertifikat erhalten"
   - ✅ "60 Tage: 5 Partner onboardet, €5k MRR"

---

## 💡 BEISPIELE: GUT vs. SCHLECHT

### Beispiel-Unternehmen: "KI-Sicherheit.jetzt"
**Kontext:**
- Score Gesamt: 67/100
- Score Governance: 58/100 (Gap!)
- Score Sicherheit: 65/100
- Hauptleistung: GPT-4-basierte Assessments
- Quick Wins: Batch-Processing, Templates, Content-Automation

#### ❌ SCHLECHT (v2.0 - generisch & vage):

```html
<section class="section recommendations">
  <h2>Empfehlungen</h2>
  <ol>
    <li><strong>[H] KI-Strategie entwickeln</strong> – Erstellen Sie eine umfassende 
        KI-Strategie mit Vision, Zielen und Roadmap. Zeitrahmen: 30-60 Tage.</li>
    
    <li><strong>[H] Mitarbeiter-Schulungen durchführen</strong> – Schulen Sie Ihr Team 
        in KI-Grundlagen und Tool-Nutzung. ROI: Bessere KI-Kompetenzen. Zeitrahmen: 60 Tage.</li>
    
    <li><strong>[M] Governance-Strukturen aufbauen</strong> – Etablieren Sie Prozesse 
        für KI-Governance. Nutzen: Compliance-Sicherheit. Zeitrahmen: 90 Tage.</li>
    
    <li><strong>[M] Pilot-Projekte starten</strong> – Beginnen Sie mit kleinen KI-Piloten. 
        Nutzen: Erste Erfahrungen sammeln. Zeitrahmen: 30-90 Tage.</li>
    
    <li><strong>[N] Change-Management initiieren</strong> – Bereiten Sie Organisation 
        auf KI-Transformation vor. Zeitrahmen: Kontinuierlich.</li>
  </ol>
</section>
```

→ **FEHLER 1:** "KI-Strategie entwickeln" - Was genau? Für welche Hauptleistung?
→ **FEHLER 2:** "Mitarbeiter-Schulungen" - Solo-Selbstständig hat kein Team!
→ **FEHLER 3:** Keine konkreten nächsten Aktionen! Was soll gemacht werden?
→ **FEHLER 4:** Keine Bezugnahme auf Scores/Gaps (Governance 58!)
→ **FEHLER 5:** Keine Integration mit Quick Wins oder Gamechanger!

#### ✅ GUT (v2.1 GOLD - konkret & spezifisch):

**WICHTIG:** Im echten Output IMMER {{score_gesamt}}, {{score_governance}} etc. verwenden!

```html
<section class="section recommendations">
  <h2>Empfehlungen</h2>

  <p>Basierend auf den Analyse-Ergebnissen (Score Gesamt: {{score_gesamt}}/100, Governance-Gap: {{score_governance}}/100)
     und der Hauptleistung "{{HAUPTLEISTUNG}}" folgen 6 priorisierte
     Handlungsempfehlungen mit klarem ROI-Bezug.</p>
  
  <ol>
    <li><strong>[H] Batch-Processing für 10× Assessment-Skalierung</strong> – 
        Implementierung von OpenAI Batch API + Redis Queue für parallele Verarbeitung 
        von 50 statt 5 Assessments/Tag. <strong>Nutzen:</strong> +900% Kapazität, 
        -50% API-Kosten, €4.500/Monat Zeitersparnis. <strong>Nächste Aktion:</strong> 
        Backend-Dev beauftragen (20h, €2.000), Batch-API-Integration entwickeln. 
        <strong>Zeitrahmen:</strong> 30 Tage MVP, 60 Tage Rollout.</li>
    
    <li><strong>[H] DSGVO-Compliance für GPT-4-Nutzung dokumentieren</strong> – 
        Schließt Governance-Gap (Score: 58/100). Audit durch spezialisierten Anwalt, 
        AVV (Auftragsverarbeitungsvertrag) mit OpenAI prüfen, Datenfluss dokumentieren, DSFA (Datenschutz-Folgenabschätzung) erstellen. 
        <strong>Nutzen:</strong> Eliminiert Compliance-Risiko (DSGVO Art. 35), 
        ermöglicht B2B-Kunden-Akquise. <strong>Kosten:</strong> €1.500 Anwalt, 
        €500 DSFA-Template. <strong>Nächste Aktion:</strong> DSGVO-Anwalt mit 
        KI-Erfahrung kontaktieren (z.B. DURY Rechtsanwälte Berlin). 
        <strong>Zeitrahmen:</strong> 60 Tage Audit, 90 Tage Zertifikat.</li>
    
    <li><strong>[H] Assessment-Template-Bibliothek für -60% Erstellungszeit</strong> – 
        20 branchen-spezifische Templates aus bisherigen 30 Projekten extrahieren. 
        <strong>Nutzen:</strong> -60% Zeit pro Assessment, höhere Qualität durch 
        Best Practices. <strong>Nächste Aktion:</strong> Top 10 Branchen analysieren 
        (eigene Arbeit, 8h), Template-Struktur definieren, in System integrieren. 
        <strong>Zeitrahmen:</strong> 30 Tage.</li>
    
    <li><strong>[M] White-Label-Partner-Programm launchen (Gamechanger)</strong> –
        SaaS-Plattform für Unternehmensberater, Agenturen und IT-Dienstleister:
        €299/Monat Lizenz + 20% Commission pro Assessment.
        <strong>Partner-Vorteile:</strong> Eigenes Branding (Logo, Farben),
        Custom-Domain, automatische Rechnungsstellung an deren Kunden.
        <strong>Tech-Stack:</strong> Multi-Tenant-Architektur, Partner-API-Keys,
        separierte Datenbanken pro Partner.
        <strong>Nutzen:</strong> Neuer Revenue Stream, €10k MRR nach 30 Partnern,
        skaliert ohne zusätzlichen Vertriebsaufwand.
        <strong>Nächste Aktion:</strong> MVP mit Partner-Dashboard entwickeln (Retool),
        5 Beta-Partner aus bestehendem Netzwerk onboarden,
        Vertrags-Template erstellen (Anwalt: €500).
        <strong>Zeitrahmen:</strong> 60 Tage MVP, 90 Tage erste 10 Partner.</li>
    
    <li><strong>[M] Cyber-Security-Audit für Backend durchführen</strong> – 
        Schließt Sicherheits-Gap (Score: 65/100). Penetration-Test durch Experten, 
        FastAPI-Security-Best-Practices implementieren, PostgreSQL-Zugriff härten. 
        <strong>Nutzen:</strong> Eliminiert Hack-Risiko, ermöglicht Enterprise-Kunden. 
        <strong>Kosten:</strong> €2.500 Pentest. <strong>Nächste Aktion:</strong> 
        Angebot von Sec-Firma einholen. <strong>Zeitrahmen:</strong> 90 Tage.</li>
    
    <li><strong>[N] API-Zugang für Entwickler-Ökosystem</strong> – 
        RESTful API mit €0.50/Score-Abfrage für Integration in HR-Software, CRMs, etc. 
        <strong>Nutzen:</strong> Neuer Revenue Stream, €5k MRR-Potential nach 12 Monaten. 
        <strong>Nächste Aktion:</strong> API-Dokumentation erstellen (Swagger/OpenAPI), 
        Freemium-Modell definieren (100 Abfragen/Monat gratis). 
        <strong>Zeitrahmen:</strong> 90 Tage MVP.</li>
  </ol>
  
  <p><strong>Empfohlene Priorisierung:</strong> Start mit [H]-Maßnahmen 1-3 in Wochen 1-8, 
     parallel DSGVO-Audit. [M]-Maßnahmen 4-5 in Wochen 9-12. [N]-Maßnahme 6 nach 
     erstem ROI-Review in Monat 4.</p>
</section>
```

**Siehst du den Unterschied?**
- ✅ **Spezifisch:** Batch-Processing für Assessments, nicht "KI-Strategie"
- ✅ **Bezug zu Scores:** DSGVO schließt Governance-Gap (58!)
- ✅ **Konkreter ROI:** +900% Kapazität, €4.500/Monat, €10k MRR
- ✅ **Nächste Aktionen:** Backend-Dev beauftragen, nicht "umsetzen"
- ✅ **Integration:** Quick Wins (Batch) + Gamechanger (White-Label) verlinkt

---

## 📋 CONTEXT-BLOCK - Integration anderer Report-Sections

### Verfügbare Context-Variablen:

**1. Unternehmens-Kontext:**
- `{{BRANCHE_LABEL}}`, `{{UNTERNEHMENSGROESSE_LABEL}}`, `{{BUNDESLAND_LABEL}}`
- `{{HAUPTLEISTUNG}}` - KRITISCH für Spezifität!

**2. KI-Readiness Scores:**
- `{{score_gesamt}}`, `{{score_befaehigung}}`, `{{score_governance}}`, 
  `{{score_sicherheit}}`, `{{score_nutzen}}`
- **Nutze Scores < 60 für Gap-Analyse!**

**3. Business-Case Zahlen:**
- `{{CAPEX_REALISTISCH_EUR}}`, `{{OPEX_REALISTISCH_EUR}}`
- `{{PAYBACK_MONTHS}}`, `{{ROI_12M}}`

**4. Quick Wins Content:**
- `{CONTEXT_QUICK_WINS}` - Enthält die 6 Quick Wins
- **Nutze für [H]-Priorität wenn sehr kritisch!**

**5. Gamechanger Content:**
- `{CONTEXT_GAMECHANGER}` - Enthält die 3 Gamechanger
- **Nutze für [M]-Priorität als mittelfristige Empfehlung!**

### Wie du Context nutzt:

**Gap-Analyse aus Scores:**
```
Score < 60 = Kritischer Gap → [H] Priorität
Score 60-75 = Ausbaubedarf → [M] Priorität
Score > 75 = Feintuning → [N] Priorität

Spezifische Gaps:
- Governance < 60 → DSGVO/Compliance-Empfehlung!
- Sicherheit < 60 → Cyber-Security-Empfehlung!
- Befähigung < 60 → Training/Enablement!
- Nutzen < 60 → ROI-Nachweis/Messgrößen!
```

**Integration Quick Wins & Gamechanger:**
```
[H] = Top 1-2 Quick Wins mit höchstem Impact
[M] = Skalierung der Quick Wins + erster Gamechanger-MVP
[N] = Gamechanger 2-3 oder langfristige Infrastruktur
```

---

## 🎯 INSTRUKTIONEN FÜR GPT-4

### SCHRITT 1: Gap-Analyse aus Scores (2 Min Denken!)

**BEVOR du Empfehlungen erstellst:**

1. **Welche Scores sind < 60 (kritische Gaps)?**
   - Diese werden [H]-Empfehlungen!
   - Beispiel: Governance 58 → DSGVO-Audit empfehlen
   - Beispiel: Sicherheit 52 → Cyber-Security-Maßnahmen

2. **Welche Quick Wins haben höchsten Impact?**
   - Top 1-2 Quick Wins als [H]-Empfehlung
   - Restliche Quick Wins sind bereits in eigener Section!

3. **Welcher Gamechanger ist realistisch in 90 Tagen startbar?**
   - Als [M]-Empfehlung mit MVP-Ansatz
   - Fokus auf schnellsten Break-Even

### SCHRITT 2: 5-7 Empfehlungen erstellen

**Typische Struktur:**

**[H] - 2-3 Empfehlungen (Wochen 1-8):**
- Top 1-2 Quick Wins mit höchstem ROI
- Gap-Closing für Scores < 60

**[M] - 2-3 Empfehlungen (Wochen 9-16):**
- Skalierung der Quick Wins
- Gamechanger-MVP (erster)
- Infrastruktur-Verbesserungen

**[N] - 1-2 Empfehlungen (Monate 4-6):**
- Weitere Gamechanger
- Langfristige Optimierungen
- Nice-to-have Features

### SCHRITT 3: Jede Empfehlung formatieren

**HTML-Format für JEDE Empfehlung:**

```html
<li><strong>[Prio] Titel der Maßnahme (max. 8 Wörter)</strong> – 
    [1-2 Sätze Beschreibung: Was wird konkret gemacht? Technische Details wenn relevant.] 
    <strong>Nutzen:</strong> [Messbare Verbesserung: +X% Kapazität, -Y€ Kosten, Z neue Revenue, etc.] 
    <strong>Nächste Aktion:</strong> [Konkrete erste Schritte: Wer wird beauftragt? Tool installieren? Welche Ressource?] 
    <strong>Zeitrahmen:</strong> [X Tage für MVP/Pilot, Y Tage für Rollout/Abschluss.] 
    <strong>Kosten:</strong> [Optional wenn relevant: €X CAPEX, €Y/Monat OPEX]</li>
```

**WICHTIG:**
- **Titel:** Beschreibt Aktion, nicht Problem ("Batch-Processing implementieren", nicht "Skalierungsproblem lösen")
- **Nutzen:** IMMER mit messbaren Zahlen (+X%, -Y€, Z neue Kunden)
- **Nächste Aktion:** KONKRET (Person/Rolle + Aktivität), nicht vage
- **Zeitrahmen:** In Tagen, nicht "mittelfristig"

### SCHRITT 4: Qualitäts-Check JEDER Empfehlung

✅ **Spezifitäts-Test:**
- Bezieht sich auf `{{HAUPTLEISTUNG}}`?
- Oder generische Empfehlung die auf jedes Unternehmen passt?
- → Wenn generisch: **Spezifizieren oder verwerfen!**

✅ **ROI-Test:**
- Gibt es messbare Verbesserung?
- Sind Zahlen genannt (+X%, -Y€, Z neue Revenue)?
- → Wenn keine Zahlen: **Researchen oder schätzen!**

✅ **Umsetzbarkeits-Test:**
- Ist nächste Aktion klar?
- Kann morgen damit gestartet werden?
- → Wenn unklar: **Konkretisieren!**

✅ **Score-Bezug-Test:**
- Adressiert Empfehlung einen Score-Gap?
- Nutzt sie Quick Win oder Gamechanger aus Context?
- → Wenn kein Bezug: **Context-Integration prüfen!**

---

## 🎯 ERFOLGS-KRITERIEN

Recommendations sind GOLD STANDARD+ wenn:

1. ✅ ALLE Empfehlungen sind SPEZIFISCH für `{{HAUPTLEISTUNG}}`
2. ✅ Score-Gaps < 60 werden mit [H]-Maßnahmen adressiert
3. ✅ Top Quick Wins und Gamechanger integriert
4. ✅ JEDE Empfehlung hat messbaren Nutzen (+X%, -Y€, Z)
5. ✅ JEDE Empfehlung hat konkrete nächste Aktion
6. ✅ Priorisierung [H]/[M]/[N] logisch aufgebaut

**Mindestens 5/6 Kriterien MÜSSEN erfüllt sein!**

---

## 🚨 HÄUFIGE FEHLER - UNBEDINGT VERMEIDEN!

### ❌ Fehler 1: Generische Empfehlungen
**Schlecht:** "[H] KI-Strategie entwickeln"
**Warum:** Passt auf jedes Unternehmen, nicht spezifisch!
**Besser:** "[H] Batch-Processing für Assessment-Skalierung"

### ❌ Fehler 2: Keine Score-Gap-Adressierung
**Schlecht:** Governance-Score 58, aber keine DSGVO-Empfehlung
**Warum:** Kritischer Gap wird ignoriert!
**Besser:** "[H] DSGVO-Audit durchführen - schließt Governance-Gap"

### ❌ Fehler 3: Vage nächste Aktionen
**Schlecht:** "Nächste Aktion: Maßnahme umsetzen"
**Warum:** Nicht umsetzbar, unklar was zu tun ist!
**Besser:** "Backend-Dev beauftragen (20h, €2.000), OpenAI Batch API integrieren"

### ❌ Fehler 4: Kein messbarer Nutzen
**Schlecht:** "Nutzen: Verbesserte Effizienz"
**Warum:** Nicht messbar, nicht überprüfbar!
**Besser:** "Nutzen: +900% Kapazität, -50% Kosten, €4.500/Monat"

### ❌ Fehler 5: Wiederholung aller Quick Wins
**Schlecht:** Alle 6 Quick Wins als separate Empfehlungen
**Warum:** Quick Wins haben eigene Section! Redundant!
**Besser:** Nur Top 1-2 Quick Wins als [H] wenn sehr kritisch

---

**VERSION:** v2.1 GOLD STANDARD+
**ERSTELLT:** 2025-11-18
**FÜR:** KI-Sicherheit.jetzt - Handlungsempfehlungen
**ZIEL:** Konkrete, priorisierte Empfehlungen mit ROI-Bezug und klaren nächsten Aktionen!
**OUTPUT:** Valides HTML (keine Markdown-Fences!)
