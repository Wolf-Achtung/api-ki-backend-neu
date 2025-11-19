<!-- unternehmensprofil_markt.md - v2.2 GOLD STANDARD+ -->
<!-- Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.
     Nutze die Platzhalter - KEINE erfundenen Beispiele!
     VERSION: 2.2 GOLD STANDARD+ (E-Commerce Bug Fix) -->

# PROMPT: Unternehmensprofil & Marktkontext

## ❗ KRITISCHE ANWEISUNG - VALIDATION REQUIRED

⚠️ **DU MUSST die folgenden Variablen verwenden - KEINE erfundenen Beispiele!**

**User-Spezifische Daten (VERWENDE DIESE!):**
- `{{BRANCHE_LABEL}}` = Echte Branche des Users
- `{{UNTERNEHMENSGROESSE_LABEL}}` = Echte Größe
- `{{BUNDESLAND_LABEL}}` = Echtes Bundesland  
- `{{HAUPTLEISTUNG}}` = Echte Hauptleistung
- `{{GESCHAEFTSMODELL_EVOLUTION}}` = Geschäftsmodell (falls vorhanden)

**Mögliche Branchen (KEINE anderen!):**
- Marketing & Werbung
- Beratung & Dienstleistungen
- IT & Software
- Finanzen & Versicherungen
- Handel & E-Commerce
- Bildung
- Verwaltung
- Gesundheit & Pflege
- Bauwesen & Architektur
- Medien & Kreativwirtschaft
- Industrie & Produktion
- Transport & Logistik

**Mögliche Größen (KEINE anderen!):**
- "1 (Solo-Selbstständig/Freiberuflich)"
- "2-10 (Kleines Team)"
- "11-100 (KMU)"

---

## ⛔ ABSOLUT VERBOTEN

**NIEMALS erfundene Beispiele verwenden:**
- ❌ "E-Commerce" wenn User "Beratung & Dienstleistungen" ist
- ❌ "Mittelständisch" wenn User "Solo" ist
- ❌ "München" wenn User "Berlin" ist
- ❌ "Verkauf von nachhaltigen Konsumgütern" wenn User etwas anderes macht

**Falls ein Platzhalter leer/fehlt:**
- ✅ Schreibe: "Nicht angegeben"
- ❌ NIEMALS einen Beispiel-Wert erfinden!

---

## 💡 CONTEXT-BLOCK NUTZUNG

Der `{CONTEXT_BLOCK}` enthält TYPISCHE Charakteristika der Branche (nicht des Users!):
- Typische Workflows in dieser Branche (generisch)
- Häufige Pain Points in dieser Branche (generisch)
- Typische Tools in dieser Branche (generisch)

**WICHTIG:**
- ✅ NUTZE Context für branchen-spezifische Trends & KI-Potenziale
- ❌ KOPIERE NICHT die User-Daten aus dem Context
- ❌ Context zeigt NICHT die Daten dieses Users!

---

## 🎯 DEINE AUFGABE

Erstelle das "Unternehmensprofil & Marktkontext"-Section mit:
1. **Unternehmensprofil:** Exakte Daten aus Variablen
2. **Marktkontext:** Branchen-Trends basierend auf Context
3. **KI-Potenzial:** Use Cases für diese Branche
4. **Wettbewerbsposition:** Größen-spezifische Einordnung

---

## 📝 OUTPUT-FORMAT

```html
<section class="section unternehmensprofil-markt">
  <h2>Unternehmensprofil & Marktkontext</h2>

  <div class="profil-box">
    <h3>Unternehmensprofil</h3>
    <ul>
      <li><strong>Branche:</strong> {{BRANCHE_LABEL}}</li>
      <li><strong>Größe:</strong> {{UNTERNEHMENSGROESSE_LABEL}}</li>
      <li><strong>Standort:</strong> {{BUNDESLAND_LABEL}}</li>
      <li><strong>Hauptleistung:</strong> {{HAUPTLEISTUNG}}</li>
      <li><strong>Geschäftsmodell:</strong> [Leite ab aus HAUPTLEISTUNG: B2B/B2C/B2G, Projektgeschäft/SaaS/Beratung/etc.]</li>
    </ul>
  </div>

  <div class="markt-context">
    <h3>Marktkontext & Trends ({{BRANCHE_LABEL}})</h3>
    <p>Die Branche {{BRANCHE_LABEL}} ist aktuell geprägt durch [beschreibe 2-3 relevante Trends basierend auf Context].</p>
    <ul>
      <li><strong>Marktwachstum:</strong> [Schätzung oder "Stabil" - KEINE erfundenen Zahlen wenn nicht sicher!]</li>
      <li><strong>KI-Adoption:</strong> [Branchen-spezifische Einschätzung basierend auf Context, z.B. "Wachsende Adoption in Kundenkommunikation und Prozessautomatisierung"]</li>
      <li><strong>Haupttreiber:</strong> [Leite ab aus Context: z.B. Fachkräftemangel, Kostendruck, Digitalisierungsdruck, Regulierung]</li>
      <li><strong>Herausforderungen:</strong> [Aus Context: Pain Points der Branche]</li>
    </ul>
  </div>

  <div class="ki-potenzial">
    <h3>KI-Potenzial für {{BRANCHE_LABEL}}</h3>
    <p>Spezifische Anwendungsfälle basierend auf Branchen-Charakteristika:</p>
    <ul>
      <li>[Use Case 1 - konkret für diese Branche, z.B. "Automatisierte Angebotserfassung" für Beratung]</li>
      <li>[Use Case 2 - konkret für diese Branche, z.B. "KI-gestützte Wissensmanagement-Systeme"]</li>
      <li>[Use Case 3 - konkret für diese Branche, z.B. "Intelligente Dokumentenanalyse"]</li>
    </ul>
  </div>

  <div class="wettbewerb">
    <h3>Wettbewerbsposition</h3>
    <p>Unternehmen der Größe {{UNTERNEHMENSGROESSE_LABEL}} in {{BRANCHE_LABEL}} haben typischerweise:</p>
    <ul>
      <li><strong>Vorteil:</strong> [Größen-spezifisch!
          Solo: Flexibilität, schnelle Entscheidungen, persönlicher Service
          2-10: Agilität, Teamwork, spezialisiertes Know-how
          11-100: Strukturierte Prozesse, dedizierte Rollen, Skalierbarkeit]</li>
      <li><strong>Nachteil:</strong> [Größen-spezifisch!
          Solo: Begrenzte Kapazität, keine Redundanz, Urlaubsvertretung schwierig
          2-10: Begrenzte Ressourcen, hohe Auslastung, wenig Spezialisierung
          11-100: Höhere Overhead-Kosten, langsamere Entscheidungen als Solo/Klein]</li>
      <li><strong>KI-Hebel:</strong> [Wie KI die Nachteile ausgleichen kann - größen-spezifisch!
          Solo: Automatisierung für mehr Kapazität, KI als "virtueller Mitarbeiter"
          2-10: Effizienzsteigerung, Wissensmanagement, Prozess-Standardisierung
          11-100: Skalierung ohne proportionalen Personalaufbau, Datengetriebene Entscheidungen]</li>
    </ul>
  </div>
</section>
```

---

## ✅ PRE-OUTPUT VALIDATION CHECKLIST

**PRÜFE JEDEN DIESER PUNKTE - BEI NEIN → STOPP & FIX!**

1. [ ] **Branche im Output = {{BRANCHE_LABEL}}?**
   - Output zeigt EXAKT die gleiche Branche wie die Variable
   - NICHT "E-Commerce" wenn User "Beratung & Dienstleistungen" hat!

2. [ ] **Größe im Output = {{UNTERNEHMENSGROESSE_LABEL}}?**
   - Output zeigt EXAKT die gleiche Größe wie die Variable
   - NICHT "Mittelständisch" wenn User "Solo" hat!

3. [ ] **Standort im Output = {{BUNDESLAND_LABEL}}?**
   - Output zeigt EXAKT das gleiche Bundesland wie die Variable
   - NICHT "München" wenn User "Berlin" hat!

4. [ ] **Hauptleistung im Output = {{HAUPTLEISTUNG}}?**
   - Output zeigt EXAKT die gleiche Hauptleistung wie die Variable
   - NICHT erfunden!

5. [ ] **KEINE erfundenen Beispiel-Daten?**
   - Keine Platzhalter wie "[Beispiel]" oder "[...]" im Output
   - Keine generischen Füll-Texte

6. [ ] **Wettbewerbsposition passt zur Größe?**
   - "Solo" → Vorteile: Flexibilität, Nachteile: Kapazität
   - "2-10" → Vorteile: Agilität, Nachteile: Ressourcen
   - "11-100" → Vorteile: Struktur, Nachteile: Overhead

7. [ ] **Context wurde NUR für Branchen-Trends genutzt?**
   - NICHT für User-Daten kopiert!

---

## 🎯 ERFOLGS-KRITERIEN

✅ **Wenn ALLE 7 Checkboxen ✅ sind → Output generieren!**
❌ **Wenn EINE Checkbox ❌ ist → STOPP & FIX!**

**Resultat:**
- Professionelles Unternehmensprofil mit exakten Daten
- Branchen-spezifischer Marktkontext
- Größen-angepasste Wettbewerbsanalyse
- Keine erfundenen Beispiele!

---

**VERSION:** v2.2 GOLD STANDARD+ (E-Commerce Bug Fixed)  
**AUSGABE:** Valides HTML (keine Markdown-Fences, kein ```html)
