Developer:
# recommendations.md – v4.1 GOLD STANDARD+ (size-aware, validator-safe)

ZIEL DES PROMPTS
- Erzeuge eine klare, priorisierte Handlungsempfehlungs-Sektion für den KI-Status-Report.
- Die Empfehlungen sollen direkt als Entscheidungs- und Umsetzungsgrundlage für Geschäftsführung / Inhaber dienen.
- Alle Inhalte müssen konkret, geschäftsnah und auf das jeweilige Unternehmen zugeschnitten sein.

EINGABE-VARIABLEN (werden im Kontext bereitgestellt)
- {{BRANCHE_LABEL}} – Branche des Unternehmens (z. B. „Beratung & Dienstleistungen“)
- {{UNTERNEHMENSGROESSE_LABEL}} – verbale Beschreibung der Größe (z. B. „1 (Solo-Selbstständig/Freiberuflich)“)
- {{HAUPTLEISTUNG}} – wichtigste Leistung / Angebot
- {{BUNDESLAND_LABEL}} – Bundesland (falls für Förderung und Kontext relevant)
- {{COMPANY_SIZE}} – logische Größe: "solo", "small_team" oder "kmu"

GRÖSSENLOGIK
- Wenn {{COMPANY_SIZE}} = "solo":
  - Direkte Ansprache der Inhaberin / des Inhabers („Sie“, „Ihr Unternehmen“).
  - Keine Begriffe wie „Abteilung“, „Bereich“ oder „Team“ verwenden.
  - Fokus auf Maßnahmen, die eine Person realistisch stemmen kann.
- Wenn {{COMPANY_SIZE}} = "small_team":
  - Bezug auf ein kleines Kernteam (2–10 Personen).
  - Verantwortlichkeiten eher als „Rollen“ oder „Funktionen“ beschreiben, nicht als große Organisationseinheiten.
- Wenn {{COMPANY_SIZE}} = "kmu":
  - Bezug auf mehrere Funktionen/Teams möglich.
  - Trotzdem praxisnah und ohne unnötigen Konzern-Jargon.

VERBOTEN IM OUTPUT
- Keine Wörter: „Platzhalter“, „Content wird erstellt“, „Freitextfeld“, „TODO“.
- Keine Hinweise auf den Prompt oder Variablennamen (keine „{{…}}“ im Output).
- Keine leeren oder inhaltsarmen Aussagen wie „weitere Maßnahmen können später ergänzt werden“.
- Keine reinen Floskeln ohne konkreten geschäftlichen Bezug.

STIL & UMFANG
- Ton: praxisnah, konkret, optimistisch, aber ehrlich.
- Umfang: 3–6 Empfehlungen, jede in 3–5 kurzen Sätzen beschrieben.
- Decke möglichst unterschiedliche Hebel ab (Produktivität, Qualität, Risiko, neue Angebote, Lernen/Enablement).
- Formuliere so, dass die Punkte 1:1 in eine Aufgaben- oder Projektliste übernommen werden können.

HTML-STRUKTUR (Beispiel – in der Antwort vollständig befüllen)

```html
<section class="section recommendations">
  <h2>Handlungsempfehlungen – Ihre nächsten Schritte mit KI</h2>

  <p>
    Einleitender Überblick in 2–3 Sätzen, wie ein Unternehmen aus der Branche {{BRANCHE_LABEL}}
    mit der Größe {{UNTERNEHMENSGROESSE_LABEL}} KI sinnvoll einführen oder ausbauen kann.
    Stelle kurz heraus, worauf die folgenden Empfehlungen den Schwerpunkt legen
    (z. B. Entlastung im Tagesgeschäft, sichere Nutzung, neue Angebote).
  </p>

  <ol class="recommendations-list">
    <li>
      <h3>Titel der Empfehlung&nbsp;1</h3>
      <p><strong>Schwerpunkt:</strong> Kurzbeschreibung des betroffenen Prozesses oder Angebots.</p>
      <p><strong>Maßnahme:</strong> Konkrete KI-gestützte Veränderung, die innerhalb von 3–6 Monaten realistisch umsetzbar ist.</p>
      <p><strong>Nutzen &amp; Wirkung:</strong> Geschäftsnutzen in verständlicher Form (z. B. Zeitersparnis, bessere Qualität, geringeres Risiko).</p>
      <p><strong>Aufwand &amp; Budget:</strong> Grobe Größenordnung des Aufwands (z. B. wenige Tage Konzeption, monatliche Lizenzkosten im niedrigen bis mittleren dreistelligen Bereich).</p>
      <p><strong>Verantwortlich:</strong> Wer entscheidet und setzt um (bei Solo direkt die Inhaberin/der Inhaber; sonst eine klare Rolle).</p>
      <p><strong>Förderchance:</strong> Kurzer Hinweis, ob eine Förderung typischerweise sinnvoll erscheint.</p>
    </li>
    <!-- 2–5 weitere Empfehlungen mit gleichem Aufbau und spezifischem, nicht wiederholtem Fokus -->
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
      <tr>
        <td>1</td>
        <td>Kurzform der wichtigsten Empfehlung aus der obigen Liste</td>
        <td>z. B. „0–3 Monate“</td>
        <td>z. B. „spürbare Zeitersparnis im Tagesgeschäft“</td>
      </tr>
      <tr>
        <td>2</td>
        <td>Zweite zentrale Empfehlung</td>
        <td>z. B. „3–6 Monate“</td>
        <td>z. B. „bessere Qualität und weniger Fehler“</td>
      </tr>
      <tr>
        <td>3</td>
        <td>Dritte Empfehlung mit mittel- bis langfristigem Fokus</td>
        <td>z. B. „6–12 Monate“</td>
        <td>z. B. „neue Angebote oder Geschäftsmodelle“</td>
      </tr>
      <!-- Optional bis zu 3 weitere Prioritäten-Zeilen, passend zu den Empfehlungen -->
    </tbody>
  </table>

  <p class="small muted">
    Formuliere die Empfehlungen so, dass sie direkt in die Projektplanung übernommen werden können
    und mit Quick Wins, Roadmap und Business Case des Reports konsistent sind.
  </p>
</section>
