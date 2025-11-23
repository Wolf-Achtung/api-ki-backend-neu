<!-- recommendations.md - v2.2 GOLD STANDARD+ (Score-Text Fix) -->
<!-- Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.
     Nutze die Platzhalter ({{score_gesamt}}, {{score_governance}}, {{score_sicherheit}}, {{HAUPTLEISTUNG}} etc.). -->

# PROMPT: Recommendations - Konkrete Handlungsempfehlungen

## ZWECK
Erstelle 5-7 konkrete, priorisierte Handlungsempfehlungen die:
1. Auf den **Analyse-Ergebnissen** (Scores, Gaps) basieren
2. **Spezifisch für {{HAUPTLEISTUNG}}** sind (nicht generisch!)
3. Mit **Priorität** (H/M/N), **Zeitrahmen** (30/60/90 Tage) und **ROI-Hinweis** versehen sind
4. Eine klare **Umsetzungs-Roadmap** von Quick Wins → Skalierung → Gamechanger bilden

**Zielgruppe:** Entscheider:innen, Projekt-Owner, Umsetzungs-Teams  
**Stil:** Konkret, umsetzbar, motivierend – KEINE vagen Ratschläge!

---

## ⚠️ KRITISCHE REGELN – ZWINGEND BEACHTEN!

### ❌ VERBOTEN – Folgendes NIEMALS empfehlen:

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
   - ✅ NUR Top 1–2 Quick Wins als Prio [H], wenn sehr kritisch
   - ✅ Sonst: Fokus auf Skalierung & Governance-Themen

4. **KEINE vagen Zeitrahmen oder Kosten:**
   - ❌ "Mittelfristig umsetzen"
   - ❌ "Budget nach Bedarf"
   - ❌ "Zeitaufwand variabel"
   - ❌ "ROI schwer zu beziffern"

### ✅ STATTDESSEN – Fokus auf:

1. **Spezifische Empfehlungen für {{HAUPTLEISTUNG}}:**
   - ✅ "Batch-Processing für Assessment-Skalierung implementieren"
   - ✅ "DSGVO-Dokumentation für GPT-4-Nutzung erstellen"
   - ✅ "White-Label-Partner-Programm launchen"
   - ✅ "Self-Service-Portal für Kunden entwickeln"

2. **Klarer Nutzen & ROI:**
   - ✅ "10× Kapazität, -50% Kosten"
   - ✅ "Compliance-Risiko reduziert"
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

#### ❌ SCHLECHT (v2.0 – generisch & vage):

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
