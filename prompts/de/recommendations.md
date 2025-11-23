
---

## 2) `prompts/de/recommendations.md` – Empfehlungen nach Branche & Größe

:contentReference[oaicite:8]{index=8}  

```markdown
<!-- recommendations.md – v2.3 GOLD STANDARD+ BRANCHENLOGIK -->
<!-- Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences. -->

# PROMPT: Recommendations – Konkrete Handlungsempfehlungen

## ZWECK

Erstelle **5–7 priorisierte Handlungsempfehlungen**, die:

1. auf den Analyse-Ergebnissen (Scores, Gaps, Quick Wins) aufbauen,  
2. **speziell für {{HAUPTLEISTUNG}} in {{BRANCHE_LABEL}}** formuliert sind,  
3. je Empfehlung **Priorität (H/M/N)**, **Zeitrahmen (30/60/90 Tage)**,  
   **Verantwortliche (size-aware)** und einen **klaren Nutzen/ROI** enthalten,  
4. in Summe eine **logische Umsetzungsstory** ergeben:
   Quick Wins → Skalierung → Governance/Compliance → Gamechanger.

---

## VARIABLEN

- {{BRANCHE_LABEL}}, {{BRANCHE}}  
- {{UNTERNEHMENSGROESSE_LABEL}}, {{COMPANY_SIZE}} (`solo`, `team`, `kmu`)  
- {{HAUPTLEISTUNG}}  
- {score_gesamt}, {score_governance}, {score_sicherheit}, {score_befaehigung}, {score_nutzen}  
- {CONTEXT_QUICK_WINS}, {CONTEXT_ROADMAP_90D}, {CONTEXT_GAMECHANGER} (optional)

---

## ⚠️ GLOBALE VERBOTE

1. **Keine generischen Standard-Empfehlungen**

   - ❌ „KI-Strategie entwickeln“ ohne konkreten Scope  
   - ❌ „Mitarbeitende schulen“ ohne Bezug zu einem Projekt  
   - ❌ „Change-Management aufsetzen“, „Pilotprojekte starten“, „Governance-Strukturen aufbauen“  
   → Diese Begriffe dürfen vorkommen, aber **nur als konkrete, messbare Maßnahmen**.

2. **Keine Empfehlungen ohne Nutzen-/ROI-Bezug**

   - Jede Empfehlung braucht einen **klaren Hebel** (Kapazität, Qualität, Risiko, Umsatz).

3. **Keine Wiederholung von Quick Wins (außer Top-Priorität)**

   - Quick Wins sind in der eigenen Section beschrieben.  
   - Höchstens 1–2 Quick Wins als Empfehlung mit [H], wenn sie **kritische Voraussetzung** sind.

4. **Keine unpassenden Preis-/Honorar-Empfehlungen**

   - ❌ In **Finanzen & Versicherungen, Bildung, Bauwesen, Industrie, Verwaltung**  
     keine Tipps wie „Stundensatz erhöhen“, „Honorare anpassen“, „Tagessätze verdoppeln“.  
   - ✅ Solche Hinweise sind nur erlaubt für Branchen mit typischen Agentur‑/Projektmodellen:
     **Beratung & Dienstleistungen**, **Marketing & Werbung**, **Medien & Kreativwirtschaft** usw.

---

## 🌍 BRANCHENLOGIK FÜR EMPFEHLUNGEN

Nutze die Branchencodes aus `mappings.json` als Orientierung (`beratung`, `marketing`, `medien`, `finanzen`, `bildung`, `bau`, `industrie`, `handel`, `logistik`, `gesundheit`, `verwaltung`). :contentReference[oaicite:9]{index=9}  

### A) Beratung & Dienstleistungen / Marketing / Medien (`beratung`, `marketing`, `medien`)

Fokus:

- Produktisierung (Pakete, Retainer, Abos) auf Basis von {{HAUPTLEISTUNG}}  
- Automatisierung von Angebot → Lieferung → Reporting  
- Aufbau von Self-Service-Angeboten (Portale, Assessments, KI-Assistants)  
- Qualitäts- und Review-Prozesse für KI-Ergebnisse

Hier dürfen **max. 1–2 Empfehlungen** Pricing-/Stundensatz-Aspekte enthalten – immer mit Begründung (z. B. „höherer Wert pro Projekt durch X“).

### B) Finanzen & Versicherungen (`finanzen`)

Fokus:

- Risiko- & Compliance-Reduktion (Regulatorik, Audit-Trails, Freigaben)  
- Standardisierte Prüfpfade, Vier-Augen-Prinzip, Logging  
- Entlastung hochpreisiger Fachkräfte durch Voranalyse, nicht durch vollautomatisierte Entscheidungen  
- Dokumentation (MaRisk/BAIT/etc.) mit klarem Ergebnis.

Keine kreativen Experimente ohne Kontrollmechanismus.

### C) Bildung (`bildung`)

Fokus:

- Konkrete Pilotkurse/Module mit KI-Unterstützung  
- Didaktisch sinnvolle Integration (z. B. Übungen, Feedback, Individualisierung)  
- Training der Lehrenden mit konkreten Unterrichtsszenarien  
- transparente Kommunikation gegenüber Lernenden (Fairness, Prüfungen).

Preis-/Sales-Themen nur am Rand.

### D) Bauwesen & Architektur (`bau`)

Fokus:

- Qualitativ bessere Planung & Dokumentation (BIM, Mängeldoku, Nachträge)  
- weniger Nachbesserung, weniger Streitigkeiten → messbare Kostenreduktion  
- Praxisnahe Baustellen-Workflows (mobile Apps, Foto-/Spracherfassung)  
- saubere Übergaben zwischen Planung, Ausführung, Abnahme.

Marketing/Content nur, wenn direkt auf Auftragslage wirkt und in 90–365 Tagen realistisch.

### E) Weitere Branchen (Industrie, Handel, Logistik, Gesundheit, Verwaltung)

Fokus:

- Kernprozess automatisieren (Fertigung, Fulfillment, Service, Vorgangsbearbeitung)  
- Qualitäts- und Sicherheitskennzahlen verbessern  
- Compliance-Anforderungen (ISO, DSGVO, branchenspezifische Vorgaben)  
- Daten- und Wissenszugriff für Fachbereiche (RAG, Assistenten).

---

## SIZE-AWARENESS

Verantwortlichkeiten und Aufwand müssen zur Größe passen:

- **Solo (`solo`)** – Empfehlungen so formulieren, dass sie von **1 Person + ggf. 1 Freelancer** umsetzbar sind.  
- **Team (`team`)** – kleine Projektteams (2–3 Personen), keine großen PMO-Strukturen.  
- **KMU (`kmu`)** – Projektteams 3–5 Personen, Stakeholder aus 2–3 Bereichen, realistische Budgets.

---

## 🎯 OUTPUT-FORMAT

Antworte mit **einer HTML-Sektion**:

```html
<section class="section recommendations">
  <h2>Empfehlungen</h2>

  <ol class="recommendations-list">
    <li>
      <h3>[H] Prägnanter Titel (max. 10 Wörter)</h3>
      <p><strong>Ziel:</strong> [Welches konkrete Problem im Kernprozess von {{HAUPTLEISTUNG}} wird gelöst?]</p>
      <p><strong>Nutzen / ROI:</strong> [Messbare Wirkung: z. B. −X % Durchlaufzeit,
         +Y € Umsatz/Monat, −Z % Reklamationen, Audit-/Compliance-Vorteile].</p>
      <p><strong>Zeitrahmen:</strong> [30 / 60 / 90 Tage] inkl. 1–2 Meilensteinen.</p>
      <p><strong>Verantwortlich:</strong> [Rollen, passend zu {{COMPANY_SIZE}}
         – z. B. „Sie selbst“, „kleines Projektteam“, „Fachbereich + IT“].</p>
      <p><strong>Abhängigkeiten:</strong> [z. B. Quick Win X, Tool Y].</p>
    </li>
    <!-- 4–6 weitere Empfehlungen -->
  </ol>

  <h3>Prioritäten-Überblick</h3>
  <table class="table">
    <thead>
      <tr>
        <th>Priorität</th>
        <th>Empfehlung</th>
        <th>Zeitrahmen</th>
        <th>Hauptnutzen</th>
      </tr>
    </thead>
    <tbody>
      <!-- 5–7 Zeilen, je Empfehlung -->
    </tbody>
  </table>
</section>
