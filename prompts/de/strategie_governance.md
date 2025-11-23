<!-- strategie_governance.md - v2.5 GOLD STANDARD+ -->
<!-- Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences im OUTPUT.
     VERSION: 2.5 GOLD STANDARD+ (Size-Awareness verschärft, Solo-Hinweise sauber getrennt) -->

# PROMPT: Strategie & Governance - KI-Governance-Strukturen

## ⚠️ SIZE-AWARENESS - ABSOLUT PFLICHT!

**Mögliche Unternehmensgrößen (NUR diese 3!):**
- `{{COMPANY_SIZE}}` = "solo" → Label: "1 (Solo-Selbstständig/Freiberuflich)"
- `{{COMPANY_SIZE}}` = "team" → Label: "2-10 (Kleines Team)"
- `{{COMPANY_SIZE}}` = "kmu"  → Label: "11-100 (KMU)"

### 📏 SIZE-APPROPRIATE LANGUAGE

**{{COMPANY_SIZE}} = "solo":**
- ✅ "Sie als Freiberufler", "Ihre Kund:innen", "Ihre Projekte"
- ✅ Externe Rollen: Anwalt, Steuerberater, IT-Dienstleister
- ✅ Einfache Checklisten statt komplexer Policies
- ❌ NIEMALS: "Team", "Führungskräfte", "Abteilung", "Steering Committee", "PMO"

**{{COMPANY_SIZE}} = "team" (2-10 MA):**
- ✅ "Geschäftsführung + Team", "eine verantwortliche Person für KI/Compliance"
- ✅ Einfache, leicht verständliche Richtlinien (1–2 Seiten)
- ✅ Pragmatistische Reviews (monatliches KI-Review-Meeting)
- ❌ NIEMALS: "PMO-Team", "Abteilungsleiter", "Change Manager", "Konzern-Governance"

**{{COMPANY_SIZE}} = "kmu" (11-100 MA):**
- ✅ "Projektleiter:in", "Führungskraft", "Compliance-Verantwortliche:r"
- ✅ "Projektteam (3–5 Personen)", "Fachbereich", "Abteilung"
- ✅ Optionale Gremien wie "Steering Committee", "PMO" (ab ~50 MA plausibel)

---

## 🔒 SIZE-CHECK & SOLO-HINWEISE

1. Lies `{{COMPANY_SIZE}}` bewusst.
2. Wenn `{{COMPANY_SIZE}} = "solo"`:
   - Du-Ansprache und Solo-Bezug sind OK.
   - Governance bleibt trotzdem schlank und pragmatisch.
3. Wenn `{{COMPANY_SIZE}} = "team"` oder `"kmu"`:
   - KEINE Formulierungen wie:
     - "als Solo-Beratung"
     - "wenn Sie später Mitarbeitende einstellen"
     - "Sie arbeiten aktuell noch allein"
   - Sprache immer auf Team/Unternehmen ausrichten.

---

## 🎯 ZWECK

Erstelle konkrete Governance-Empfehlungen, die:

1. Die Analyse-Scores sinnvoll interpretieren  
   (z. B. `{{score_governance}}`, `{{score_sicherheit}}`, `{{score_nutzen}}`).
2. Spezifisch für {{HAUPTLEISTUNG}} sind (keine generischen KI-Phrasen).
3. Rollen & Verantwortlichkeiten SIZE-AWARE definieren.
4. Konkrete Prozesse beschreiben (wer macht was, in welcher Frequenz?).

**Zielgruppe:** Geschäftsführung, Compliance-Verantwortliche, Risk-Owner.  
**Stil:** Strukturiert, compliance-fokussiert, pragmatisch, verständlich.

---

## ⛔ ABSOLUT VERBOTEN

### ❌ Generische Governance-Tipps ohne Kontext
- "KI-Beirat einrichten"
- "Regelmäßige Reviews durchführen"
- "Richtlinien erstellen" ohne Zweck & Inhalt
- "Governance-Strukturen aufbauen" als Leerformel

### ❌ Zahlen und Scores ignorieren
- `{{score_governance}}` < 60 und keine Maßnahmen zu DSGVO/EU AI Act
- `{{score_sicherheit}}` < 60 und keine Security/KI-Risiko-Maßnahmen

### ❌ Unpassende Größenlogik
- Konzernartige Strukturen bei Solo/Team
- Solo-Wording in Team/KMU-Reports
- Zusätzliche Vollzeitstellen empfehlen, wenn Business Case konservativ ist

---

## 🔧 STRUKTUR DER ANTWORT

Erzeuge eine HTML-Section mit:

1. Kurzer Einleitung (1 Absatz):
   - Einordnung der Governance- und Sicherheits-Scores.
   - Bezug zu {{HAUPTLEISTUNG}} und Unternehmensgröße.

2. 3–5 Themenblöcke, z. B.:
   - Rollen & Verantwortlichkeiten
   - Richtlinien & Nutzungsregeln
   - Risiko- und Compliance-Prozesse (DSGVO, EU AI Act)
   - Dokumentation & Nachvollziehbarkeit
   - Monitoring & kontinuierliche Verbesserung

Jeder Block:

- Überschrift `<h3>` oder `<h4>`.
- 1–2 Absätze mit klaren, umsetzbaren Maßnahmen.
- Nur dort Listen einsetzen, wo sie Struktur schaffen (max. 3–5 Punkte).

---

## 🧪 QUALITÄTS-CHECK

Vor Ausgabe prüfen:

1. **Size-Check:** Passt jede Rolle zur Unternehmensgröße?
2. **Score-Check:** Werden schwache Bereiche (Score < 60) sichtbar adressiert?
3. **Solo-Hinweise:** Keine Solo-Formulierungen bei `team`/`kmu`.
4. **Kohärenz mit Business Case & Roadmap:**  
   - Governance-Maßnahmen unterstützen die geplanten Projekte (z. B. Batch-Processing, Self-Service-Portal, White-Label).
5. **Klarheit:** Entscheider:innen können aus dem Text direkt Aufgaben ableiten.

**Output:** Valides HTML, keine Markdown-Fences, keine Platzhalter.
