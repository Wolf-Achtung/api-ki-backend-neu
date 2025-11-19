<!-- next_actions.md - v2.2 GOLD STANDARD+ -->
<!-- Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.
     VERSION: 2.2 GOLD STANDARD+ (Size-Awareness Fix) -->

# PROMPT: Nächste Aktionen (30 Tage)

## ⚠️ SIZE-AWARENESS - ABSOLUT PFLICHT!

**Mögliche Unternehmensgrößen (NUR diese 3!):**
- `{{COMPANY_SIZE}}` = "solo" → Label: "1 (Solo-Selbstständig/Freiberuflich)"
- `{{COMPANY_SIZE}}` = "team" → Label: "2-10 (Kleines Team)"  
- `{{COMPANY_SIZE}}` = "kmu" → Label: "11-100 (KMU)"

### 📏 SIZE-APPROPRIATE VERANTWORTLICHKEITEN

**{{COMPANY_SIZE}} = "solo":**
- ✅ "Geschäftsführer (Sie)"
- ✅ "Externe Unterstützung: [Anwalt/Berater/Freelancer]"
- ❌ NIEMALS: "PMO-Team", "Projektleiter", "Team", "Abteilung"

**{{COMPANY_SIZE}} = "team" (2-10 MA):**
- ✅ "Geschäftsführer + [Name/Rolle des Mitarbeiters]"
- ✅ "Verantwortlicher Mitarbeiter für [Bereich]"
- ✅ "Kleines Projektteam (2-3 Personen)"
- ❌ NIEMALS: "PMO-Team", "Abteilungsleiter", "Change Manager"

**{{COMPANY_SIZE}} = "kmu" (11-100 MA):**
- ✅ "Projektleiter", "Führungskraft", "Compliance-Verantwortlicher"
- ✅ "Projektteam (3-5 Personen)"
- ✅ "PMO-Team" oder "Abteilungsleiter" (NUR ab ~50 MA!)

---

## 🎯 ZWECK

Erstelle 3-5 konkrete Next Actions für die nächsten 30 Tage die:
1. **Sofort umsetzbar** sind (keine 6-Monats-Projekte!)
2. **Size-appropriate Verantwortlichkeiten** haben
3. **Konkrete Termine** nennen (z.B. "Ende Q1", "Mitte Q2")
4. **Kurzen Nutzen** beschreiben (1 Satz)

**Zielgruppe:** Geschäftsführung, Umsetzer  
**Stil:** Präzise, fachlich, motivierend, größen-angemessen

---

## ⛔ ABSOLUT VERBOTEN

### ❌ Unrealistische Verantwortlichkeiten:
- ❌ "PMO-Team" bei Solo oder Klein (2-10 MA)!
- ❌ "Abteilungsleiter" bei Solo!
- ❌ "Change Manager" bei Klein!
- ❌ "Steering Committee" bei Solo/Klein!

### ❌ Vage Aktionen:
- ❌ "KI-Strategie entwickeln"
- ❌ "Richtlinien erstellen"
- ❌ "Team schulen"

---

## ✅ STATTDESSEN: Konkret & Size-Appropriate!

### ✅ Solo (1 MA):
- "AVV mit OpenAI unterschreiben (via Dashboard → DPA Download) – Verantwortlich: Geschäftsführer (Sie), Termin: Diese Woche, Nutzen: DSGVO-Compliance"
- "Freelance Backend-Dev beauftragen (20h) für Batch-System – Verantwortlich: Geschäftsführer (Sie), Termin: Ende Q1, Nutzen: 10× mehr Kapazität"

### ✅ Klein (2-10 MA):
- "DSGVO-Schulung für Team buchen (2h Workshop) – Verantwortlich: Geschäftsführer + HR-Mitarbeiter, Termin: Mitte Q2, Nutzen: Compliance-Awareness"
- "Pilot-Projekt mit 2 Mitarbeitern starten – Verantwortlich: Projektverantwortlicher (Max Mustermann), Termin: Ende Q1, Nutzen: Erste Erfolge sichtbar machen"

### ✅ KMU (11-100 MA):
- "KI-Projekt-Register einführen – Verantwortlich: Compliance-Officer + IT-Leiter, Termin: Ende Q1, Nutzen: Übersicht über alle KI-Systeme"
- "Steering Committee Meeting organisieren – Verantwortlich: Projektleiter KI, Termin: Anfang Q2, Nutzen: Alignment mit Geschäftsführung"

---

## 💡 BEISPIEL (Solo)

```html
<section class="section next-actions">
  <h2>Nächste Aktionen (30 Tage)</h2>
  
  <p>Basierend auf den Quick Wins und der Roadmap folgen konkrete Aktionen für die nächsten 30 Tage:</p>
  
  <ul class="checklist">
    <li>
      <strong>AVV mit OpenAI unterschreiben (DSGVO-Compliance)</strong><br>
      Verantwortlich: Geschäftsführer (Sie)<br>
      Termin: Diese Woche (5 Min)<br>
      Nutzen: Rechtssichere Datenverarbeitung für GPT-4-Assessments, eliminiert Compliance-Risiko
    </li>
    
    <li>
      <strong>Freelance Backend-Entwickler beauftragen (Batch-System MVP)</strong><br>
      Verantwortlich: Geschäftsführer (Sie)<br>
      Termin: Ende Woche 1 (Ausschreibung + Interviews)<br>
      Nutzen: Startet Entwicklung des Batch-Processing-Systems für 10× mehr Kapazität
    </li>
    
    <li>
      <strong>Template-Bibliothek: Top 10 Branchen analysieren</strong><br>
      Verantwortlich: Geschäftsführer (Sie - 8h Eigenarbeit)<br>
      Termin: Ende Woche 2<br>
      Nutzen: Basis für 20 branchen-spezifische Templates, -60% Erstellungszeit ab Woche 5
    </li>
    
    <li>
      <strong>DSFA für Assessment-Datenverarbeitung erstellen</strong><br>
      Verantwortlich: Geschäftsführer (Sie) + Externe Unterstützung (DSGVO-Anwalt, €500)<br>
      Termin: Ende Woche 3<br>
      Nutzen: Vollständige DSGVO-Dokumentation, bereitet B2B-Kunden-Akquise vor
    </li>
    
    <li>
      <strong>API-Kosten-Tracking einrichten (Simple Excel/Google Sheet)</strong><br>
      Verantwortlich: Geschäftsführer (Sie - 1h Setup)<br>
      Termin: Ende Woche 1<br>
      Nutzen: Transparenz über OpenAI-Kosten, identifiziert Einsparpotenziale durch Batch-API
    </li>
  </ul>
</section>
```

---

## 💡 BEISPIEL (Klein 2-10 MA)

```html
<ul class="checklist">
  <li>
    <strong>DSGVO-Workshop für Team organisieren (2h)</strong><br>
    Verantwortlich: Geschäftsführer + HR-Mitarbeiter (Lisa Schmidt)<br>
    Termin: Mitte Q2 (Anbieter buchen, Termin koordinieren)<br>
    Nutzen: Team kennt Compliance-Anforderungen für KI-Nutzung, reduziert Fehlerrisiko
  </li>
  
  <li>
    <strong>Pilot-Projekt mit 2 Mitarbeitern starten (Erstes KI-Tool testen)</strong><br>
    Verantwortlich: Projektverantwortlicher (Max Mustermann) + 2 Team-Mitglieder<br>
    Termin: Ende Q1 (Kick-off + 4 Wochen Pilot)<br>
    Nutzen: Erste Erfolge sichtbar machen, Team-Akzeptanz erhöhen, Learnings sammeln
  </li>
  
  <li>
    <strong>Weekly Show & Tell einführen (30 Min jeden Freitag)</strong><br>
    Verantwortlich: Geschäftsführer (Moderation)<br>
    Termin: Ab nächster Woche<br>
    Nutzen: Team teilt KI-Quick-Wins, fördert Experimentierfreude und Wissensaustausch
  </li>
</ul>
```

---

## 💡 BEISPIEL (KMU 11-100 MA)

```html
<ul class="checklist">
  <li>
    <strong>KI-Projekt-Register einführen (alle KI-Systeme erfassen)</strong><br>
    Verantwortlich: Compliance-Officer (Anna Müller) + IT-Leiter (Tom Weber)<br>
    Termin: Ende Q1 (2 Wochen für Setup + Datensammlung)<br>
    Nutzen: Übersicht über alle KI-Systeme, Basis für Risiko-Bewertung und AI Act Compliance
  </li>
  
  <li>
    <strong>Steering Committee Meeting organisieren (Kick-off KI-Initiative)</strong><br>
    Verantwortlich: Projektleiter KI (Dr. Sarah Klein)<br>
    Termin: Anfang Q2 (Agenda vorbereiten, Stakeholder einladen)<br>
    Nutzen: Alignment mit Geschäftsführung, Budget-Freigabe, Go/No-Go-Entscheidung
  </li>
  
  <li>
    <strong>Pilot-Team bilden (5-8 Personen aus verschiedenen Abteilungen)</strong><br>
    Verantwortlich: Projektleiter KI + HR<br>
    Termin: Ende Q1 (Kandidaten identifizieren, Freigabe einholen)<br>
    Nutzen: Cross-funktionales Team testet erste KI-Tools, sammelt Feedback für Rollout
  </li>
</ul>
```

---

## 🎯 INSTRUKTIONEN

### SCHRITT 1: Quick Wins & Roadmap prüfen

- Extrahiere die wichtigsten 3-5 Aktionen aus Phase 1 der Roadmap
- Fokus auf Aktionen die in 30 Tagen umsetzbar sind

### SCHRITT 2: {{COMPANY_SIZE}} prüfen & Verantwortlichkeiten zuweisen

**Nutze SIZE-APPROPRIATE VERANTWORTLICHKEITEN Tabelle oben!**

1. Check {{COMPANY_SIZE}}
2. Wähle passende Rollen-Bezeichnungen
3. KEINE "PMO-Team" bei Solo/Klein!
4. Passe Komplexität der Aktionen an Größe an

### SCHRITT 3: Konkrete Aktionen formulieren

**Format für JEDE Aktion:**

```
<li>
  <strong>[Konkrete Aktion - kein Marketing-Sprech!]</strong><br>
  Verantwortlich: [Size-appropriate Rolle/Name]<br>
  Termin: [Konkret: "Diese Woche", "Ende Q1", "Mitte Q2"]<br>
  Nutzen: [1 Satz mit konkretem Business-Nutzen, keine Floskeln]
</li>
```

---

## ✅ PRE-OUTPUT VALIDATION

**PRÜFE JEDE AKTION:**

1. [ ] **Verantwortlichkeit size-appropriate?**
   - Solo: KEIN "PMO-Team", KEIN "Projektleiter"
   - Klein: KEIN "Abteilungsleiter", KEIN "Change Manager"
   - KMU: Formelle Rollen OK

2. [ ] **Aktion konkret?**
   - NICHT: "KI-Strategie entwickeln"
   - SONDERN: "AVV mit OpenAI unterschreiben"

3. [ ] **Termin konkret?**
   - NICHT: "Bald", "Demnächst"
   - SONDERN: "Diese Woche", "Ende Q1"

4. [ ] **Nutzen konkret?**
   - NICHT: "Verbessert Effizienz"
   - SONDERN: "10× mehr Kapazität, -50% Kosten"

5. [ ] **In 30 Tagen umsetzbar?**
   - Keine 6-Monats-Projekte!

**Wenn ALLE ✅ → Output generieren!**

---

## 🎯 ERFOLGS-KRITERIEN

1. ✅ 3-5 konkrete Aktionen
2. ✅ Size-appropriate Verantwortlichkeiten
3. ✅ Konkrete Termine (nicht vage)
4. ✅ Kurzer Business-Nutzen (1 Satz)
5. ✅ In 30 Tagen umsetzbar

**Wenn ALLE ✅ → GOLD STANDARD+ erreicht!**

---

**VERSION:** v2.2 GOLD STANDARD+ (Size-Awareness Fixed)  
**AUSGABE:** Valides HTML (keine Markdown-Fences!)
