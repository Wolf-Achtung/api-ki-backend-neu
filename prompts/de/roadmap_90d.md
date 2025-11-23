<!-- roadmap_90d.md - v3.0 GOLD STANDARD+ SIZE & BRANCHENLOGIK
     Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences. -->

# PROMPT: 90-Tage Roadmap - Konkrete Umsetzungsplanung

## ⚠️ SIZE-AWARENESS - ABSOLUT PFLICHT!

**Mögliche Unternehmensgrößen (NUR diese 3!):**
- `{{COMPANY_SIZE}}` = "solo" → Label: "1 (Solo-Selbstständig/Freiberuflich)"
- `{{COMPANY_SIZE}}` = "team" → Label: "2–10 (Kleines Team)"  
- `{{COMPANY_SIZE}}` = "kmu" → Label: "11–100 (KMU)"

### 📏 SIZE-APPROPRIATE TEAMS & BUDGETS

**{{COMPANY_SIZE}} = "solo":**
- ✅ Team: "Geschäftsführer (Sie)" + "Freelancer oder Partner (bei Bedarf)"
- ✅ Budget: max. 10.000 € CAPEX, 500 €/Monat OPEX
- ✅ Timeline: eher +50 % Zeit (da eine Person vieles selbst macht)
- ❌ NIEMALS: "PMO-Team", "Projektleiter", "Entwicklerteam", "Abteilung"

**{{COMPANY_SIZE}} = "team" (2–10 MA):**
- ✅ Team: "Geschäftsführer + 1–2 Mitarbeitende" oder "kleines Projektteam (2–3 Personen)"
- ✅ Budget: max. 50.000 € CAPEX, 2.000 €/Monat OPEX
- ✅ Timeline: normal
- ❌ NIEMALS: "PMO-Team", "Abteilungsleiter", "dediziertes Entwicklerteam"

**{{COMPANY_SIZE}} = "kmu" (11–100 MA):**
- ✅ Team: "Projektteam (3–5 Personen)", "Projektleiter + Entwickler"
- ✅ „PMO-Team“ nur ab ca. 50 MA
- ✅ Budget: max. 200.000 € CAPEX, 10.000 €/Monat OPEX
- ✅ Timeline: normal bis −20 % (dedizierte Ressourcen möglich)

---

## 🧭 BRANCHEN-AWARENESS – BEGRIFFE & PILOTTYPEN

Nutze {{BRANCHE_LABEL}} und {{HAUPTLEISTUNG}}, um passende Begriffe für Phasen, Deliverables und KPIs zu wählen:

- **Beratung & Dienstleistungen / Agenturen:**  
  „Mandate“, „Projekte“, „Workshops“, „Retainer‑Kunden“, „Pakete“

- **Marketing & Werbung / Medien & Kreativwirtschaft:**  
  „Kampagnen“, „Formate“, „Spots“, „Videos“, „Content-Pakete“  
  → Begriffe wie „Assessment“ nur, wenn {{HAUPTLEISTUNG}} wirklich eine Analyse/Assessment-Leistung ist.

- **Finanzen & Versicherungen:**  
  „Fälle“, „Mandate“, „Prüfvorgänge“, „Anträge“, „Portfolios“  
  → starker Fokus auf Compliance, Freigaben, Vier-Augen-Prinzip.

- **Bauwesen & Architektur:**  
  „Bauvorhaben“, „Projekte“, „Baustellen“, „Planungsphasen“  
  → Fokus auf Dokumentation, Planprüfung, Nachbesserungsquote.

- **Bildung:**  
  „Kurse“, „Module“, „Klassen“, „Lernpfade“, „Prüfungen“  
  → Fokus auf Lernqualität, Korrekturaufwand, Teilnehmendenzahl.

- **Industrie, Produktion, Transport & Logistik:**  
  „Produktionslinien“, „Chargen“, „Routen“, „Touren“, „Schichten“.

**Regel:** Verwende Begriffe wie „Assessment“, „KI-Readiness“, „Fragebogen“ nur, wenn sie zu {{HAUPTLEISTUNG}} passen; sonst fachlich passende Begriffe aus der Branche verwenden.

---

## 🚨 KRITISCHER FIX: KEINE TEMPLATE-ÜBERSCHRIFTEN!

### ❌ DIESE WÖRTER/PHRASEN DÜRFEN NIEMALS ALS ÜBERSCHRIFT ERSCHEINEN:

- ❌ **"Risiken & Mitigation:"** oder **"Risiken:"** als Heading  
- ❌ **"Was wird gebaut:"** als Heading  
- ❌ **"Messbarer Erfolg:"** als Heading  
- ❌ **"Team & Ressourcen:"** als Heading  
- ❌ **"Abhängigkeiten:"** als Heading  

### ✅ RICHTIG – ALLES IM FLIEßTEXT

FALSCH:
```html
<h5>Risiken & Mitigation:</h5> <!-- ❌ FEHLER -->
<ul>
  <li>API-Ausfall → Fallback nutzen</li>
</ul>
