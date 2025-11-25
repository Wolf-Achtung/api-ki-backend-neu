Developer: ## 2️⃣ `unternehmensprofil_markt.md`

<!-- unternehmensprofil_markt.md - v2.2 GOLD STANDARD+ -->
<!-- Antworte ausschließlich mit **validem HTML**. KEIN <html>, <head> oder <body>. KEINE Markdown-Fences. Nutze die Platzhalter - KEINE erfundenen Beispiele! VERSION: 2.2 GOLD STANDARD+ (E-Commerce Bug Fix) -->

# PROMPT: Unternehmensprofil & Marktkontext

### Beginne mit einer kurzen Checkliste (3-7 Punkte):
- Eingabevariablen auf vollständige Werte prüfen und „Nicht angegeben“ setzen, falls Werte fehlen.
- Unternehmensprofil-Daten exakt den angegebenen Platzhaltern entnehmen.
- Marktkontext ausschließlich anhand des gegebenen Context-Blocks ausfüllen, keine Userdaten für Kontext oder umgekehrt verwenden.
- Branchen- und größenbezogene Abschnitte gemäß Template und nur mit erlaubten Werten ausfüllen.
- Ausgabe strikt im vorgegebenen HTML-Struktur und Reihenfolge.
- Keine fiktiven Beispiele oder Annahmen treffen.
- Nach Ausgabe überprüfen, ob keine Werte erfunden wurden und alle Abschnitte ausgefüllt sind.

## ‼️ KRITISCHE ANWEISUNG - VALIDIERUNG ERFORDERLICH

⚠️ **DU MUSST die folgenden Variablen verwenden – KEINE erfundenen Beispiele!**

**User-spezifische Daten (VERWENDEN!):**
- `{{BRANCHE_LABEL}}` = Echte Branche des Users
- `{{UNTERNEHMENSGROESSE_LABEL}}` = Echte Größe des Unternehmens
- `{{BUNDESLAND_LABEL}}` = Echtes Bundesland
- `{{HAUPTLEISTUNG}}` = Echte Hauptleistung
- `{{GESCHAEFTSMODELL_EVOLUTION}}` = Geschäftsmodel (falls vorhanden)

**Zulässige Branchen (nur diese verwenden!):**
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

**Zulässige Größen (nur diese verwenden!):**
- "1 (Solo-Selbstständig/Freiberuflich)"
- "2-10 (Kleines Team)"
- "11-100 (KMU)"

---

## ⛔ ABSOLUT VERBOTEN

**NIEMALS fiktive Beispiele verwenden:**
- ❌ „E-Commerce“ wenn User „Beratung & Dienstleistungen“ ist
- ❌ „Mittelständisch“ wenn User „Solo“ ist
- ❌ „München“ wenn User „Berlin“ ist
- ❌ „Verkauf von nachhaltigen Konsumgütern“ wenn User etwas anderes macht

**Falls Wert eines Platzhalters leer oder nicht angegeben:**
- ✅ Schreibe: "Nicht angegeben"
- ❌ NIEMALS einen Beispiel-Wert erfinden!

---

## 💡 CONTEXT-BLOCK-VERWENDUNG

`{CONTEXT_BLOCK}` liefert generische Charakteristika der Branche (nicht user-spezifisch!):
- Typische Workflows (generisch)
- Häufige Pain Points (generisch)
- Typische Tools (generisch)

**WICHTIG:**
- ✅ Kontext für branchenspezifische Trends & KI-Potenziale verwenden
- ❌ KEINE Userdaten aus Kontext übernehmen
- ❌ Kontext ist NICHT user-spezifisch!
- Ist Context leer oder fehlt die Information, schreibe "Nicht angegeben" an entsprechender Stelle.

---

## 🎯 DEINE AUFGABE

Erstelle den Abschnitt "Unternehmensprofil & Marktkontext" wie folgt:
1. **Unternehmensprofil:** Exakte Daten aus Variablen
2. **Marktkontext:** Branchen-Trends anhand des Context
3. **KI-Potenzial:** Use Cases dieser Branche
4. **Wettbewerbsposition:** Größenspezifische Einordnung

---

## 📝 OUTPUT-FORMAT

<section class="section unternehmensprofil-markt">
  <h2>Unternehmensprofil & Marktkontext</h2>
  <div class="profil-box">
    <h3>Unternehmensprofil</h3>
    <ul>
      <li><strong>Branche:</strong> {{BRANCHE_LABEL}}<span aria-hidden="true"></span></li>
      <li><strong>Größe:</strong> {{UNTERNEHMENSGROESSE_LABEL}}</li>
      <li><strong>Standort:</strong> {{BUNDESLAND_LABEL}}</li>
      <li><strong>Hauptleistung:</strong> {{HAUPTLEISTUNG}}</li>
      <li><strong>Geschäftsmodell:</strong> {{GESCHAEFTSMODELL_EVOLUTION}}<br><em>Falls nicht vorhanden: Schreibe "Nicht angegeben".<br>Falls Logik zur Ableitung aus Hauptleistung nicht eindeutig möglich, schreibe "Nicht angegeben".</em></li>
    </ul>
  </div>
  <div class="markt-context">
    <h3>Marktkontext & Trends ({{BRANCHE_LABEL}})</h3>
    <p>Die Branche {{BRANCHE_LABEL}} ist aktuell geprägt durch <span class="trends">[2-3 relevante Trends aus Context, sonst "Nicht angegeben"]</span>.</p>
    <ul>
      <li><strong>Marktwachstum:</strong> <span class="marktwachstum">[Schätzung aus Context oder "Stabil"; falls Information nicht vorhanden: "Nicht angegeben"]</span></li>
      <li><strong>KI-Adoption:</strong> <span class="ki-adoption">[Branchenspezifische Einschätzung aus Context, falls nicht vorhanden: "Nicht angegeben"]</span></li>
      <li><strong>Haupttreiber:</strong> <span class="haupttreiber">[Abgeleitet aus Context: z.B. Fachkräftemangel, Regulierung o.ä., sonst "Nicht angegeben"]</span></li>
      <li><strong>Herausforderungen:</strong> <span class="herausforderungen">[Aus Context: Branchen-Pain Points, sonst "Nicht angegeben"]</span></li>
    </ul>
  </div>
  <div class="ki-potenzial">
    <h3>KI-Potenzial für {{BRANCHE_LABEL}}</h3>
    <p>Spezifische Anwendungsfälle basierend auf Branchen-Charakteristika:</p>
    <ul>
      <li>[Use Case 1 – branchenspezifisch, z. B. "Automatisierte Angebotserfassung" für Beratung; falls Context fehlt: "Nicht angegeben"]</li>
      <li>[Use Case 2 – branchenspezifisch, z. B. "KI-gestützte Wissensmanagement-Systeme"; falls Context fehlt: "Nicht angegeben"]</li>
      <li>[Use Case 3 – branchenspezifisch, z. B. "Intelligente Dokumentenanalyse"; falls Context fehlt: "Nicht angegeben"]</li>
    </ul>
  </div>
  <div class="wettbewerb">
    <h3>Wettbewerbsposition</h3>
    <p>Unternehmen der Größe {{UNTERNEHMENSGROESSE_LABEL}} in {{BRANCHE_LABEL}} haben typischerweise:</p>
    <ul>
      <li><strong>Vorteil:</strong> <span class="vorteil">[Größenspezifisch! Solo: Flexibilität, schnelle Entscheidungen, persönlicher Service. 2-10: Agilität, Teamwork, spezialisiertes Know-how. 11-100: Strukturierte Prozesse, dedizierte Rollen, Skalierbarkeit. Falls nicht ableitbar: "Nicht angegeben"]</span></li>
      <li><strong>Nachteil:</strong> <span class="nachteil">[Größenspezifisch! Solo: Begrenzte Kapazität, keine Redundanz. 2-10: Begrenzte Ressourcen. 11-100: Höhere Overhead-Kosten. Falls nicht ableitbar: "Nicht angegeben"]</span></li>
      <li><strong>KI-Hebel:</strong> <span class="ki-hebel">[Wie KI Nachteile ausgleichen kann – größenspezifisch! Solo: Automatisierung, KI als "virtueller Mitarbeiter". 2-10: Effizienzsteigerung, Wissensmanagement. 11-100: Skalierung, datengetriebene Entscheidungen. Falls nicht ableitbar: "Nicht angegeben"]</span></li>
    </ul>
  </div>
</section>

---

## Ausgabeformat

- **Nur gültiges HTML** ausgeben, kein <html>, <head> oder <body>, keine Markdown, keine Code-Fences.
- Reihenfolge und Struktur der Abschnitte **genau** wie oben beibehalten.
- Alle Platzhalter (`{{...}}`) sind mit echten Userdaten oder Context zu füllen, falls leer/nicht angegeben: "Nicht angegeben".
- NIEMALS Werte erfinden oder umformulieren, was nicht geliefert wurde.
- Bei Feldern, die auf Hauptleistung basieren (z. B. Geschäftsmodell) und ohne klare Herleitung: "Nicht angegeben" verwenden.
- Für alle Bullets in Marktkontext, KI-Potenzial und Wettbewerb gilt: Inhalt aus Context, Uservariablen oder laut Template – andernfalls "Nicht angegeben" schreiben.
- Niemals Reihenfolge oder Struktur ändern.
- Nach der Ausgabe überprüfe die Einhaltung aller Anforderungen. Wenn ein Wert nicht ableitbar ist oder fehlt, muss eindeutig „Nicht angegeben“ erscheinen.
- Siehe folgendes Beispiel:

<section class="section unternehmensprofil-markt">
  <h2>Unternehmensprofil & Marktkontext</h2>
  <div class="profil-box">
    <h3>Unternehmensprofil</h3>
    <ul>
      <li><strong>Branche:</strong> Beratung & Dienstleistungen</li>
      <li><strong>Größe:</strong> Nicht angegeben</li>
      <li><strong>Standort:</strong> Berlin</li>
      <li><strong>Hauptleistung:</strong> Strategieberatung</li>
      <li><strong>Geschäftsmodell:</strong> Nicht angegeben</li>
    </ul>
  </div>
  <div class="markt-context">
    <h3>Marktkontext & Trends (Beratung & Dienstleistungen)</h3>
    <p>Die Branche Beratung & Dienstleistungen ist aktuell geprägt durch <span class="trends">Nicht angegeben</span>.</p>
    <ul>
      <li><strong>Marktwachstum:</strong> <span class="marktwachstum">Nicht angegeben</span></li>
      <li><strong>KI-Adoption:</strong> <span class="ki-adoption">Nicht angegeben</span></li>
      <li><strong>Haupttreiber:</strong> <span class="haupttreiber">Nicht angegeben</span></li>
      <li><strong>Herausforderungen:</strong> <span class="herausforderungen">Nicht angegeben</span></li>
    </ul>
  </div>
  <div class="ki-potenzial">
    <h3>KI-Potenzial für Beratung & Dienstleistungen</h3>
    <p>Spezifische Anwendungsfälle basierend auf Branchen-Charakteristika:</p>
    <ul>
      <li>Nicht angegeben</li>
      <li>Nicht angegeben</li>
      <li>Nicht angegeben</li>
    </ul>
  </div>
  <div class="wettbewerb">
    <h3>Wettbewerbsposition</h3>
    <p>Unternehmen der Größe Nicht angegeben in Beratung & Dienstleistungen haben typischerweise:</p>
    <ul>
      <li><strong>Vorteil:</strong> <span class="vorteil">Nicht angegeben</span></li>
      <li><strong>Nachteil:</strong> <span class="nachteil">Nicht angegeben</span></li>
      <li><strong>KI-Hebel:</strong> <span class="ki-hebel">Nicht angegeben</span></li>
    </ul>
  </div>
</section>