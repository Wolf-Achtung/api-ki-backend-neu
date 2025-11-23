
---

## 5️⃣ `foerderpotenzial.md` – aktualisiert + Research-Datum sichtbar

Hier habe ich:  

- den Beispielcode **aktualisiert** (keine Aussage mehr „go-digital: laufend“).  
- `{{RESEARCH_DATE}}` als sichtbare Angabe ergänzt.  
- EU-/Bund-/Land-Teil so formuliert, dass Tavily/Perplexity‑Ergebnisse sauber eingefädelt werden können.  

```md
# PROMPT: Förderpotenzial - Finanzierungs-Möglichkeiten

## ZWECK
Liste relevante Förderprogramme für:
1. **{{BUNDESLAND_LABEL}}** (Landes-Förderungen)
2. **{{BRANCHE_LABEL}}** (Branchen-Förderungen)
3. **KI-/Digitalisierungsprojekte** (Bund/EU)

**Zielgruppe:** CFO, Geschäftsführung  
**Stil:** Prägnant, mit Links, Antragsfristen, klarer Einordnung  
**Transparenz:** Im Output immer "Stand der Förderinformationen: {{RESEARCH_DATE}}" angeben.

---

## ⚠️ KRITISCHE REGELN

### ❌ VERBOTEN:
1. **KEINE veralteten Programme mit abgelaufenen Fristen als "laufend" darstellen.**
2. **KEINE generischen Listen ohne Relevanz-Check.**
3. **KEINE Förderungen ohne Antrags- oder Infoseite (Link).**
4. **KEINE reinen EU-Buzzwords ohne Bezug zum Projekt ({{HAUPTLEISTUNG}}).**

### ✅ STATTDESSEN:
1. **Aktuell & relevant (lt. Research):**
   - Programme, die im Research als aktiv/offen oder laufend markiert sind.
   - Historisch ausgelaufene Programme nur als Hinweis kennzeichnen (z.B. "nicht mehr für Neuanträge geöffnet").

2. **Konkrete Zahlen & Einordnung, soweit im Research vorhanden:**
   - Zuschussquoten (z.B. "bis 50% Zuschuss, max. €10k")
   - typische Fördersummen / Darlehenshöhen
   - Zielgruppe (KMU, Solo-Selbstständige, bestimmte Branchen)

3. **Immer mit Link:**
   - Offizielle Programmseite (BMWK, KfW, IBB, EU-Funding-Portal etc.)

---

## 💡 BEISPIEL (kompakt)

```html
<section class="section foerderpotenzial">
  <h2>Förderpotenzial & Finanzierung</h2>
  
  <p><strong>Relevante Programme für:</strong> {{BRANCHE_LABEL}}, {{BUNDESLAND_LABEL}}</p>
  <p><em>Stand der Förderinformationen: {{RESEARCH_DATE}}</em></p>

  <h3>Bundes-Programme (Deutschland)</h3>
  <table class="table">
    <thead>
      <tr><th>Programm</th><th>Förderung / Zweck</th><th>Status / Frist</th><th>Link</th></tr>
    </thead>
    <tbody>
      <tr>
        <td>Digital Jetzt (BMWK)</td>
        <td>Förderung von Digitalisierungsprojekten in KMU (z.B. Einführung von KI-gestützten Workflows, Software, Schulungen).</td>
        <td>Aktuelle Konditionen & Fristen siehe Programmseite.</td>
        <td><a href="https://www.innovation-beratung-foerderung.de/INNO/Navigation/DE/Digital-Jetzt/digital-jetzt.html">Programmseite</a></td>
      </tr>
      <tr>
        <td>ERP-Digitalisierungs- und Innovationskredit (KfW)</td>
        <td>Zinsgünstige Kredite für Digitalisierungs- und Innovationsvorhaben (Hardware, Software, Beratung, Entwicklung).</td>
        <td>Laufend (über Hausbank beantragbar).</td>
        <td><a href="https://www.kfw.de">KfW-Übersicht</a></td>
      </tr>
      <!-- Optional: Weitere durch Research gefundene Bundesprogramme dynamisch ergänzen -->
    </tbody>
  </table>

  <h3>Landes-Programme ({{BUNDESLAND_LABEL}})</h3>
  <ul>
    <li><strong>Beispiel Berlin – Digitalprämie Berlin:</strong> Zuschüsse für Digitalisierungsprojekte (z.B. Einführung von KI-Lösungen, Automatisierung, Online-Services). <a href="https://www.ibb.de">Mehr Informationen</a></li>
    <li><strong>IBB-Förderprogramme:</strong> z.B. Digitalisierungskredit oder Innovationskredite für Software-/Plattform-Entwicklung. <a href="https://www.ibb.de">Programmübersicht</a></li>
    <li><strong>[Platzhalter für Research-Ergebnis]:</strong> Mindestens ein spezifisches Landesprogramm aus dem aktuellen Research (Name, kurzer Zweck, Link).</li>
  </ul>

  <h3>EU-Programme (Horizon Europe / Digital Europe)</h3>
  <ul>
    <li><strong>Horizon Europe – KI / Digitalisierungs-Calls:</strong> Relevante Ausschreibungen, z.B. zu generativer KI, Datenplattformen oder KMU-Digitalisierung.  
        Integration deines Vorhabens als Pilot-/Demonstratorprojekt möglich. 
        <a href="https://ec.europa.eu/info/funding-tenders/opportunities/portal">EU Funding & Tenders Portal</a></li>
    <li><strong>Digital Europe Programme:</strong> Förderlinien für den Aufbau und Einsatz digitaler Kapazitäten (Cloud, KI, Datenräume) – nur nennen, wenn der aktuelle Research einen passenden Call zeigt.</li>
  </ul>

  <h3>Empfohlene nächste Schritte</h3>
  <ol>
    <li>1–2 Bundesprogramme auswählen, die am besten zu deinem Projektumfang (CAPEX) und Unternehmensprofil passen.</li>
    <li>Mindestens ein Landesprogramm ({{BUNDESLAND_LABEL}}) prüfen, das explizit Digitalisierungs-/KI-Projekte in {{BRANCHE_LABEL}} adressiert.</li>
    <li>Kurze Projektbeschreibung (1–2 Seiten) erstellen, die für mehrere Programme wiederverwendet werden kann (Ziele, Kosten, Zeitplan, erwarteter Nutzen).</li>
    <li>Optional: Gespräch mit Fördermittel-Expert:in (z.B. 1–2h) führen, um aus den recherchierten Programmen die 1–2 mit der höchsten Erfolgschance auszuwählen.</li>
  </ol>
</section>
