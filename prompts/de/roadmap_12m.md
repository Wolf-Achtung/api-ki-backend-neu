
---

## `prompts/de/roadmap_12m.md`  :contentReference[oaicite:1]{index=1}  

```markdown
<!-- roadmap_12m.md – v3.0 GOLD STANDARD+ BRANCHENLOGIK
     Antworte ausschließlich mit **validem HTML**.
     Kein <html>, <head>, <body>. Keine Markdown-Fences. -->

# PROMPT: Roadmap 12 Monate – Langfrist-Planung

## ZWECK
Erstelle eine **12‑Monats-Roadmap (Monate 4–12)**, die:

1. nahtlos an die 90‑Tage‑Roadmap (Q1) anschließt  
2. pro Quartal (Q2, Q3, Q4) konkrete Meilensteine definiert  
3. die Entwicklung von Quick Wins → Skalierung → Gamechanger beschreibt  
4. messbare KPIs pro Quartal nennt  
5. zu {{BRANCHE_LABEL}}, {{HAUPTLEISTUNG}} und {{UNTERNEHMENSGROESSE_LABEL}} passt

---

## REGELN & VERBOTE

1. **Keine Wiederholung der 90‑Tage‑Roadmap**  
   – Q1 nur kurz einordnen, Roadmap beginnt bei Monat 4.

2. **Begriffswahl passend zur Branche**  
   - Nutze Begriffe aus {{HAUPTLEISTUNG}} und {{BRANCHE_LABEL}}  
     (z. B. „Kampagnen“, „Projekte“, „Kurse“, „Bauvorhaben“, „Mandate“).  
   - Begriffe wie „Assessment“, „KI‑Readiness“ nur, wenn sie wirklich zur Leistung passen.

3. **Realismus**  
   - max. ein Gamechanger‑MVP in 12 Monaten  
   - Q2: Skalierung Quick Wins & Professionalisierung  
   - Q3: Gamechanger-MVP + Governance/Compliance  
   - Q4: Ausbau, zweiter Revenue-Stream oder Tiefenintegration

---

## BRANCHEN-HEURISTIK

- **Beratung, Marketing, Medien, Kreativwirtschaft:**  
  Q2 = Standardisierung & Kapazität,  
  Q3 = Produktisierte Angebote / Portal / White‑Label,  
  Q4 = Partner-/Subscription-Modelle oder Plattform.

- **Finanzen, Gesundheit, Verwaltung:**  
  Q2 = kontrollierte Piloten + Richtlinien,  
  Q3 = Skalierung + formale Governance/Compliance,  
  Q4 = Tiefenintegration + Monitoring.

- **Bauwesen & Architektur, Industrie, Transport & Logistik:**  
  Q2 = Piloten an Projekten/Linien/Routen,  
  Q3 = Skalierung & Systemintegration,  
  Q4 = Standardisierung, KPI‑Tracking, Lessons Learned.

- **Bildung:**  
  Q2 = Pilotkurse/Module,  
  Q3 = Ausrollen auf Fachbereiche/Standorte,  
  Q4 = dauerhafte Programme & skalierbare digitale Angebote.

---

## STRUKTUR & OUTPUT-FORMAT

```html
<section class="section roadmap-12m">
  <h2>12-Monats-Roadmap (Monate 4–12)</h2>

  <p>[2–3 Sätze, wie diese Roadmap auf den Ergebnissen der ersten 90 Tage
     aufbaut – z. B. Quick Wins produktiv, erste Erfahrungen, validierte Piloten.]</p>

  <h3>Q2 (Monate 4–6): [Quartalsziel in 3–6 Wörtern]</h3>
  <ul>
    <li><strong>Monat 4:</strong> [konkrete Maßnahmen, z. B. Skalierung Pilot, Standardisierung, zusätzliche Automatisierung]</li>
    <li><strong>Monat 5:</strong> [Rollout auf weitere Kundensegmente/Standorte/Produkte]</li>
    <li><strong>Monat 6:</strong> [Stabilisierung, Monitoring, Lessons Learned]</li>
  </ul>
  <p><strong>KPIs Q2:</strong> [2–4 Kennzahlen mit Zielwerten]</p>

  <h3>Q3 (Monate 7–9): [Gamechanger-MVP & Governance]</h3>
  <ul>
    <li><strong>Monat 7:</strong> [Start/Weiterentwicklung Gamechanger-MVP, Governance/Compliance-Arbeit beginnen]</li>
    <li><strong>Monat 8:</strong> [Einsatz des MVP bei ausgewählten Kund:innen/Standorten, Feedback & Optimierung]</li>
    <li><strong>Monat 9:</strong> [Entscheidung zur Skalierung, ggf. Zertifizierungen/formale Freigaben]</li>
  </ul>
  <p><strong>KPIs Q3:</strong> [z. B. aktive Nutzer:innen, MRR, Compliance-Meilensteine]</p>

  <h3>Q4 (Monate 10–12): [Skalierung & neuer Revenue-Stream]</h3>
  <ul>
    <li><strong>Monat 10:</strong> [Skalierung auf breitere Basis, Integration in bestehende Systeme]</li>
    <li><strong>Monat 11:</strong> [Aufbau neuer Erlösmodelle, z. B. Abos, White-Label, Lizenzen]</li>
    <li><strong>Monat 12:</strong> [Konsolidierung, KPI-Review, Roadmap für Jahr 2 definieren]</li>
  </ul>
  <p><strong>KPIs Q4:</strong> [z. B. MRR, aktive Kund:innen/Partner, Einsparungen, Risiko-Reduktion]</p>

  <h3>Jahresziele (Monat 12)</h3>
  <ul>
    <li>[Ziel 1 mit Zahl, z. B. „X aktive Kund:innen/Partner“]</li>
    <li>[Ziel 2 mit Zahl, z. B. „Y € wiederkehrender Umsatz (MRR/ARR)“ – falls passend]</li>
    <li>[Ziel 3, z. B. „Z % weniger Durchlaufzeit/Nachbesserungen/Fehler“]</li>
    <li>[Governance-/Compliance‑Ziel, falls relevant]</li>
  </ul>
</section>
