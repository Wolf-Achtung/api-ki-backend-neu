<!--
Business‑Case (DE) — Steuerung & Regeln
Eingaben (numerisch, bereits berechnet und im Template-Kontext verfügbar):
  - CAPEX_REALISTISCH_EUR (€, einmalig)
  - OPEX_REALISTISCH_EUR (€/Monat)
  - EINSPARUNG_MONAT_EUR (€/Monat, Quick‑Wins)
  - PAYBACK_MONTHS (Monate)
  - ROI_12M (0..1, als Anteil)

WICHTIG:
  - Keine Zahlen erfinden. Ausschließlich die oben genannten Variablen verwenden.
  - Kurz, sachlich und zuversichtlich – kein Marketing‑Wording.
  - Zielgruppe: Entscheider:innen. Nutzen, Amortisation und Risiken klar benennen.
-->

### Business‑Case (Ergebnis)

**Monatliche Einsparung:** {{EINSPARUNG_MONAT_EUR}} €  
**CAPEX:** {{CAPEX_REALISTISCH_EUR}} € · **OPEX:** {{OPEX_REALISTISCH_EUR}} €/Monat  
**Amortisation:** {{PAYBACK_MONTHS}} Monate · **ROI (12 Monate):** {{ (ROI_12M*100)|round(1) }} %

#### Interpretation
Die Quick‑Win‑Einsparungen von {{EINSPARUNG_MONAT_EUR}} €/Monat tragen die laufenden Kosten (OPEX) und führen zu einer Amortisation nach {{PAYBACK_MONTHS}} Monaten.
Der ROI nach 12 Monaten von {{ (ROI_12M*100)|round(1) }} % ergibt sich ausschließlich aus den bereitgestellten Zahlen — ohne zusätzliche Annahmen.

#### Sensitivität (±20 %)
- **Einsparung −20 %:** Längere Amortisationszeit, ROI verringert sich entsprechend.  
- **Einsparung +20 %:** Schnellere Amortisation, höherer ROI.  
- **Kosten +/−20 %:** Payback verschiebt sich proportional, Aussage bleibt robust, wenn Prozesse und Nutzung stabil sind.

#### Empfehlungen zur ROI‑Hebelung (konkret)
1) **Stufenweise Einführung (MVP → Skalierung):** Erst Pilot, dann Ausrollen; verhindert Überinvestitionen.  
2) **Tooling optimieren:** Vorhandene Lizenzen nutzen, Verträge bündeln, Automationsgrad erhöhen.  
3) **Enablement & Standards:** Rollen schulen, klare Messgrößen (Zeit, Qualität, Risiko) definieren, regelmäßiges Review.

*Hinweis:* Für Solo‑Beratung gelten konservative Annahmen; Anpassungen (z. B. Stundensatz, Tool‑Mix) ändern die Kennzahlen entsprechend.
