<!-- Business Case (DE) -->
<!-- Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown‑Fences.
     Nutze die Platzhalter:
     - {DEFAULT_STUNDENSATZ_EUR}
     - {BRANCHE_LABEL}, {UNTERNEHMENSGROESSE_LABEL}, {BUNDESLAND_LABEL}, {HAUPTLEISTUNG}
     Schreibe präzise, fachlich, motivierend – kein Marketing‑Sprech. -->

<section class="section business-case">
  <h2>Business Case</h2>
  <p>Berechne einen groben Business‑Case für die Einführung der identifizierten Quick Wins. Verwende die Gesamtsumme der monatlichen Zeiteinsparungen (in Stunden) und multipliziere sie mit einem Stundensatz von {{DEFAULT_STUNDENSATZ_EUR}} €. Berücksichtige eine Einführungskosten‑Summe (z. B. 10 000 €) und laufende Kosten (z. B. 500 € pro Monat). Zeige die Amortisationszeit (in Monaten) und den ROI nach 12 Monaten. Stelle die Ergebnisse übersichtlich in einer Tabelle dar.</p>
  <table class="table">
    <tr><th>Parameter</th><th>Wert</th><th>Erläuterung</th></tr>
    <tr><td>Gesamteinsparung</td><td>X h/Monat</td><td>Summe der Quick Wins</td></tr>
    <tr><td>Stundensatz</td><td>{{DEFAULT_STUNDENSATZ_EUR}} €</td><td>Angenommener Wert</td></tr>
    <tr><td>Monetärer Nutzen</td><td>Y €/Monat</td><td>Gesamteinsparung × Stundensatz</td></tr>
    <tr><td>Einführungskosten</td><td>10 000 €</td><td>Einmaliger Invest</td></tr>
    <tr><td>Laufende Kosten</td><td>500 €/Monat</td><td>Betrieb & Lizenzen</td></tr>
    <tr><td>Amortisation</td><td>Z Monate</td><td>Einführungskosten ÷ (Monetärer Nutzen – laufende Kosten)</td></tr>
    <tr><td>ROI nach 12 Monaten</td><td>R €</td><td>Summe der Einsparungen minus Kosten</td></tr>
  </table>
  <p class="small muted">Alle Angaben dienen der groben Orientierung und müssen individuell geprüft werden.</p>
</section>
