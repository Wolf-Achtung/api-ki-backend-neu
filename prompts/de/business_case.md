<!-- Business Case (DE) -->
<!-- Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown‑Fences.
     Nutze die Platzhalter:
     - {DEFAULT_STUNDENSATZ_EUR}
     - {BRANCHE_LABEL}, {UNTERNEHMENSGROESSE_LABEL}, {BUNDESLAND_LABEL}, {HAUPTLEISTUNG}
     Schreibe präzise, fachlich, motivierend – kein Marketing‑Sprech. -->

<section class="section business-case">
  <h2>Business Case</h2>
  <p>Die folgende Tabelle stellt den groben Business‑Case für die Umsetzung der identifizierten Quick Wins dar. Sie basiert auf den monatlichen Zeiteinsparungen, dem Beratungsstundensatz von {{DEFAULT_STUNDENSATZ_EUR}} € sowie einer realistischen Einschätzung der einmaligen Einführungskosten und der laufenden Kosten.</p>
  <table class="table">
    <tr><th>Parameter</th><th>Wert</th><th>Erläuterung</th></tr>
    <tr><td>Gesamteinsparung</td><td><!-- Hier soll der LLM die Summe der monatlichen Zeiteinsparungen aus den Quick Wins eintragen (in Stunden). --></td><td>Summe der monatlichen Zeiteinsparungen aus den Quick Wins</td></tr>
    <tr><td>Stundensatz</td><td>{{DEFAULT_STUNDENSATZ_EUR}} €</td><td>Angenommener Beratungsstundensatz</td></tr>
    <tr><td>Monetärer Nutzen</td><td><!-- Hier soll der LLM den monetären Nutzen (Gesamteinsparung × Stundensatz) eintragen. --></td><td>Gesamteinsparung × Stundensatz</td></tr>
    <tr><td>Einführungskosten</td><td><!-- Hier soll der LLM realistische einmalige Einführungskosten eintragen (z. B. 2 000–5 000 €). --></td><td>Einmaliger Invest für Software & Setup</td></tr>
    <tr><td>Laufende Kosten</td><td><!-- Hier soll der LLM realistische laufende Kosten pro Monat eintragen (z. B. 100–300 €). --></td><td>Abos, Lizenzen & Betrieb</td></tr>
    <tr><td>Amortisation</td><td><!-- Hier soll der LLM die Amortisationszeit berechnen (Einführungskosten ÷ (Monetärer Nutzen – laufende Kosten)). --></td><td>Einführungskosten ÷ (Monetärer Nutzen – laufende Kosten)</td></tr>
    <tr><td>ROI nach 12 Monaten</td><td><!-- Hier soll der LLM den ROI nach 12 Monaten eintragen (Monetäre Einsparungen nach 12 Monaten minus aller Kosten). --></td><td>Monetäre Einsparungen nach 12 Monaten abzüglich aller Kosten</td></tr>
  </table>
  <p class="small muted">Diese Berechnung dient als grobe Orientierung und muss individuell geprüft werden.</p>
</section>
