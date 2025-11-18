# PROMPT: Technologie & Prozesse

## ZWECK
Dokumentiere:
1. **Tech-Stack:** Alle genutzten Tools/Systeme
2. **Prozesse:** Wie fließen Daten durch System
3. **Integration:** Wie sind Tools verbunden

**Zielgruppe:** CTO, IT, Entwickler
**Stil:** Technisch, präzise, architektur-fokussiert

---

## ⚠️ KRITISCHE REGELN

### ❌ VERBOTEN:
1. **KEINE theoretischen Architekturen**
2. **NUR tatsächlich genutzte Tools**

### ✅ STATTDESSEN:
1. **Real Stack:** GPT-4, PostgreSQL, FastAPI, React
2. **Datenfluss:** Typeform → Backend → OpenAI → PDF

---

## 💡 BEISPIEL

```html
<section class="section technologie-prozesse">
  <h2>Technologie & Prozesse</h2>

  <h3>Tech-Stack (IST)</h3>
  <table class="table">
    <thead><tr><th>Layer</th><th>Technologie</th><th>Zweck</th><th>Hosting</th></tr></thead>
    <tbody>
      <tr><td>Frontend</td><td>React, Tailwind</td><td>User Interface</td><td>Netlify</td></tr>
      <tr><td>Backend</td><td>FastAPI, Python</td><td>API, Business Logic</td><td>Railway</td></tr>
      <tr><td>Database</td><td>PostgreSQL</td><td>Assessments, Reports</td><td>Railway</td></tr>
      <tr><td>KI</td><td>GPT-4 API</td><td>Report-Generierung</td><td>OpenAI</td></tr>
      <tr><td>Forms</td><td>Typeform</td><td>Fragebogen</td><td>Typeform</td></tr>
      <tr><td>PDF</td><td>WeasyPrint</td><td>Report-Export</td><td>Railway</td></tr>
    </tbody>
  </table>

  <h3>Datenfluss (Haupt-Prozess)</h3>
  <ol>
    <li>Kunde füllt Typeform-Fragebogen aus (15 Min)</li>
    <li>Webhook → FastAPI Backend</li>
    <li>Backend validiert Daten, speichert in PostgreSQL</li>
    <li>GPT-4 API Call (6 Prompts für 6 Report-Sections)</li>
    <li>Responses werden kombiniert & in PostgreSQL gespeichert</li>
    <li>WeasyPrint generiert PDF aus HTML-Template</li>
    <li>PDF-Link per E-Mail an Kunden (SendGrid)</li>
  </ol>

  <h3>Geplante Tech-Änderungen (Q2-Q4 2025)</h3>
  <ul>
    <li><strong>Q2:</strong> Redis für Queue-Management (Batch-Processing)</li>
    <li><strong>Q3:</strong> Supabase für Auth + Partner-Management</li>
    <li><strong>Q4:</strong> Retool für Admin-Dashboard</li>
  </ul>
</section>
```

---

## 🎯 ERFOLGS-KRITERIEN

1. ✅ Vollständiger Tech-Stack
2. ✅ Datenfluss dokumentiert
3. ✅ Geplante Änderungen genannt

---

**VERSION:** v2.1 GOLD STANDARD+
**OUTPUT:** Valides HTML
