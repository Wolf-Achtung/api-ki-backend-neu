<!-- business_case.md – v2.4 GOLD STANDARD+ ROI & SIZE
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences. -->

<!-- KONTEXT-VARIABLEN
     - {{BRANCHE_LABEL}}: Branche des Unternehmens.
     - {{COMPANY_SIZE}}: solo | team | kmu.
     - {{HAUPTLEISTUNG}}: zentrale Leistung / Wertschöpfungskern.
     - {{BUNDESLAND_LABEL}}: Standort (für qualitative Förder-Hinweise, keine eigenen Zahlen).
     - {{CAPEX_REALISTISCH_EUR}}: einmalige Investition in EUR.
     - {{OPEX_REALISTISCH_EUR}}: laufende monatliche Kosten in EUR.
     - {{EINSPARUNG_MONAT_EUR}}: realistische monatliche Einsparung in EUR.
     - {{PAYBACK_MONTHS}}: Amortisationsdauer in Monaten.
     - {{ROI_12M}}: erwarteter ROI nach 12 Monaten in Prozent.

     REGELN
     - Verwende exakt die übergebenen Zahlen. Keine eigenen Berechnungen oder zusätzlichen Beträge erfinden.
     - Verbal gern mit „rund / ca.“ arbeiten, aber die Werte nicht verändern.
     - Keine Förderquoten oder Zuschusshöhen nennen – dafür gibt es die Förderkapitel.
-->

<section class="section business-case">
  <h2>Business Case – Investition und erwarteter Nutzen</h2>

  <p>
    Für <strong>{{BRANCHE_LABEL}}</strong> in der Größe 
    <strong>{{COMPANY_SIZE}}</strong> ist {{HAUPTLEISTUNG}} ein zentraler Hebel der
    Wertschöpfung. Der folgende Business Case zeigt, wie sich eine systematische
    Nutzung von KI in diesem Kernprozess finanziell auswirkt.
  </p>

  <h3>Investition und laufende Kosten</h3>
  <p>
    Für Aufbau und Einführung der Lösung sind einmalige Investitionen von
    rund <strong>{{CAPEX_REALISTISCH_EUR}}&nbsp;€</strong> vorgesehen. 
    Hinzu kommen laufende Betriebskosten von etwa 
    <strong>{{OPEX_REALISTISCH_EUR}}&nbsp;€ pro Monat</strong> 
    (z.&nbsp;B. für KI‑Nutzung, Infrastruktur und ggf. Lizenzen).
  </p>

  <h3>Monatlicher Effekt im Kerngeschäft</h3>
  <p>
    Durch den Einsatz von KI im Prozess <strong>{{HAUPTLEISTUNG}}</strong> ist eine 
    realistische Entlastung von ungefähr 
    <strong>{{EINSPARUNG_MONAT_EUR}}&nbsp;€ pro Monat</strong> erreichbar – 
    kombiniert aus Zeitersparnis, weniger manuellen Schleifen und höherer Qualität.
    Die genaue Ausprägung hängt davon ab, wie konsequent der neue Workflow im Alltag
    genutzt wird.
  </p>

  <h3>Amortisation und ROI</h3>
  <p>
    Auf Basis dieser Relationen ergibt sich eine Amortisationsdauer von rund 
    <strong>{{PAYBACK_MONTHS}} Monaten</strong>. Über einen Zeitraum von zwölf
    Monaten liegt der erwartete Return on Investment bei etwa 
    <strong>{{ROI_12M}}&nbsp;%</strong>. 
    Dieser Wert beschreibt das Verhältnis zwischen Investition und erwarteter 
    Entlastung und dient als praxisnahe Orientierung – nicht als Garantie.
  </p>

  <h3>Einordnung nach Unternehmensgröße</h3>
  <p>
    Für <strong>{{COMPANY_SIZE}}</strong> gilt: Je stärker {{HAUPTLEISTUNG}} 
    auf wiederkehrende, standardisierbare Abläufe setzt, desto schneller macht sich 
    die Investition bemerkbar. Bei sehr geringer Auslastung des neuen Workflows
    verlängert sich die Amortisation, bei hoher Nutzung kann sie sich deutlich verkürzen.
  </p>

  <h3>Verbindung zu Fördermöglichkeiten (qualitativ)</h3>
  <p>
    In {{BUNDESLAND_LABEL}} gibt es Programme, die KI‑ und 
    Digitalisierungsprojekte unterstützen. Wird ein Teil der einmaligen Investition 
    über passende Förderprogramme refinanziert, verbessert sich der Business Case
    weiter – typischerweise durch eine kürzere Amortisationsdauer und einen höheren
    effektiven ROI. Konkrete Programme und Konditionen werden im Förderkapitel erläutert;
    hier werden bewusst keine zusätzlichen Zahlen erfunden.
  </p>

  <p class="small muted">
    Hinweis: Alle Zahlen dienen als realistische, aber vereinfachte Orientierung. 
    Vor größeren Investitionsentscheidungen sollten Szenario‑Rechnungen und 
    Sensitivitätsanalysen (z.&nbsp;B. konservativ / Basis / optimistisch) ergänzt werden.
  </p>
</section>
