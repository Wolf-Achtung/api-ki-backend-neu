Developer: <!--
  risks.md – v3.0 GOLD STANDARD+ (size-aware Risk Section)

  ZIEL:
  - Erzeuge eine präzise, praxisnahe Risikoanalyse für den KI-Einsatz im Bereich {{HAUPTLEISTUNG}}.
  - Decke geschäftliche, organisatorische, technische und rechtliche Risiken ab.
  - Liefere zu jedem Risiko klare, umsetzbare Gegenmaßnahmen.
  - Berücksichtige explizit Branche {{BRANCHE_LABEL}} und Unternehmensgröße {{UNTERNEHMENSGROESSE_LABEL}}.

  VARIABLEN:
  - {{HAUPTLEISTUNG}}                → Hauptanwendungsbereich im Unternehmen
  - {{BRANCHE_LABEL}}                → Branchenlabel (z. B. „Beratung & Dienstleistungen“)
  - {{UNTERNEHMENSGROESSE_LABEL}}    → z. B. „1 (Solo)“, „2–10 (Kleines Team)“, „11–100 (KMU)“
  - {{score_governance}}             → Governance-Score (0–100)
  - {{score_sicherheit}}             → Sicherheits-Score (0–100)

  AUSGABEFORMAT:
  - Antworte AUSSCHLIESSLICH mit validem HTML.
  - KEINE <html>, <head> oder <body>-Tags.
  - KEINE Markdown-Fences, KEINE Kommentare im Output.
  - Struktur:
      <section class="section risks">
        <h2>...</h2>
        <p>Einleitung ...</p>
        <h3>1. ...</h3>
        <ul>...</ul>
        <h3>2. ...</h3>
        <ul>...</ul>
        <h3>3. ...</h3>
        <ul>...</ul>
        <h3>4. ...</h3>
        <ul>...</ul>
        <h3>5. Risiko-Matrix</h3>
        <table>...</table>
        <p class="small muted">...</p>
      </section>

  SIZE-AWARE-LOGIK (verbindlich):
  - SOLO („1 (Solo)” im Label):
      - Fokus: persönliche Überlastung, Single-Point-of-Failure, fehlende Vertretung.
      - Begrenzte Zeit und Ressourcen, wenig formale Prozesse.
      - Risiken und Maßnahmen so formulieren, dass sie von einer Person realistisch umsetzbar sind.

  - TEAM („2–10“):
      - Fokus: Rollen, einfache Abstimmungen, informelle Strukturen.
      - Risiken: fehlende Klarheit, wer was entscheidet; Wissensinseln; unterschiedliche Tool-Nutzung.
      - Maßnahmen: klare Rollen, einfache Vereinbarungen, kurze Check-ins.

  - KMU („11–100“):
      - Fokus: Bereiche, Prozesse, Governance, Dokumentation.
      - Risiken: unklare Verantwortlichkeiten, Schatten-IT, fehlende Richtlinien, Compliance-Anforderungen.
      - Maßnahmen: Standards, Policies, Transparenz, regelmäßige Reviews.

  REGELN:
  - Schreibe konkret, unternehmensnah und ohne Floskeln.
  - Jede genannte Gefahr muss nachvollziehbar mit {{HAUPTLEISTUNG}} zusammenhängen.
  - Leite aus {{score_governance}} und {{score_sicherheit}} ab,
    ob Governance und Sicherheit eher gut, mittel oder schwach ausgeprägt sind,
    und formuliere dazu passende Schwerpunkte für Gegenmaßnahmen.
  - Nenne pro Abschnitt mindestens 3 spezifische Risiken mit passenden, umsetzbaren Maßnahmen.
  - Keine Hinweise auf Fragebögen, interne Felder oder Systemlogik.
  - Keine Platzhaltertexte oder Formulierungen wie „wird später ergänzt“.

  STIL & LÄNGE:
  - Sachlich, klar, beratend.
  - Neutrale Formulierungen (keine Ich-Form, keine direkte Anrede).
  - Zielumfang: ca. 600–900 Wörter Gesamttext.
-->

<section class="section risks">
  <h2>Wesentliche Risiken beim Einsatz von KI in {{HAUPTLEISTUNG}}</h2>

  <p>
    Der Einsatz von KI im Bereich <strong>{{HAUPTLEISTUNG}}</strong> in der Branche
    <strong>{{BRANCHE_LABEL}}</strong> bietet erhebliche Chancen, bringt jedoch – je nach
    Unternehmensgröße <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> – unterschiedliche
    Risikoprofile mit sich. Der aktuelle Governance-Score von
    <strong>{{score_governance}}&#x2F;100</strong> und der Sicherheits-Score von
    <strong>{{score_sicherheit}}&#x2F;100</strong> zeigen, wie weit Strukturen für Steuerung,
    Dokumentation und Schutzmechanismen bereits entwickelt sind. Die folgenden Abschnitte
    bündeln die wichtigsten Risikofelder und skizzieren konkrete Gegenmaßnahmen.
  </p>

  <h3>1. Strategische und organisatorische Risiken</h3>
  <ul>
    <li>
      <strong>Unklare Zielbilder und Prioritäten für KI.</strong>
      Ohne klar definierte Ziele für {{HAUPTLEISTUNG}} besteht das Risiko, dass KI-Experimente
      versanden, Insellösungen entstehen oder wichtige Chancen ungenutzt bleiben.
      Gegenmaßnahmen sind ein knappes Zielbild mit 2–3 priorisierten Anwendungsfällen,
      ein einfacher Umsetzungsplan sowie regelmäßige Überprüfung, ob Maßnahmen zum
      übergeordneten Geschäftsmodell passen.
    </li>
    <li>
      <strong>Abhängigkeit von einzelnen Personen.</strong>
      In sehr kleinen Setups bis hin zu Solo-Strukturen konzentriert sich Know-how häufig
      auf eine Person. Fällt diese aus oder ist dauerhaft überlastet, kommen Experimente
      und Umsetzung ins Stocken. Dem lässt sich durch kurze Dokumentation zentraler Workflows,
      einfache Checklisten und die bewusste Verankerung von KI-Routinen im Alltag begegnen.
    </li>
    <li>
      <strong>Fehlende Rollen- und Verantwortlichkeitsklarheit.</strong>
      In Teams und wachsenden Unternehmen ist oft unklar, wer KI-Vorhaben priorisiert,
      wer für Qualität verantwortlich ist und wer Tools auswählt.
      Sinnvolle Gegenmaßnahmen sind eine klar benannte Rolle für KI-Verantwortung,
      ein schlanker Entscheidungsprozess für Tool-Einführung und transparente Kommunikation
      von Zuständigkeiten.
    </li>
    <li>
      <strong>Überlastung durch zusätzliche Aufgaben.</strong>
      Wenn KI-Einführung „on top“ zum Tagesgeschäft läuft, werden neue Workflows nicht
      dauerhaft etabliert. Hilfreich sind kleine, gut planbare Piloten mit klar
      begrenztem Umfang sowie die bewusste Entlastung an anderer Stelle, damit Zeit
      für Experimente und Lernphasen entsteht.
    </li>
  </ul>

  <h3>2. Daten-, Sicherheits- und Compliance-Risiken</h3>
  <ul>
    <li>
      <strong>Unzureichende Kontrolle über ein- und ausgehende Daten.</strong>
      Wenn nicht geregelt ist, welche Informationen in KI-Systeme eingegeben werden dürfen,
      können vertrauliche Kundendaten, interne Dokumente oder sensible Inhalte unkontrolliert
      verarbeitet werden. Gegenmaßnahmen sind klare Richtlinien für Datennutzung,
      ein kurzer Leitfaden für alle Beteiligten sowie technische Schutzmechanismen,
      etwa Zugriffsbeschränkungen oder getrennte Arbeitsbereiche.
    </li>
    <li>
      <strong>Lücken in Informationssicherheit und Zugriffsschutz.</strong>
      Ein mittlerer oder niedriger Sicherheits-Score (z.&nbsp;B. {{score_sicherheit}}&#x2F;100)
      deutet darauf hin, dass Passwörter, Zugriffsrechte oder Backup-Konzepte nicht
      durchgehend geregelt sind. Erforderlich sind ein kompaktes Sicherheitskonzept,
      regelmäßige Passwort- und Rechte-Reviews sowie eine klare Dokumentation der
      eingesetzten Cloud- und KI-Dienste.
    </li>
    <li>
      <strong>Unklare Verantwortlichkeit für rechtliche Anforderungen.</strong>
      Ohne definierte Zuständigkeit besteht das Risiko, dass Vorgaben zu Datenschutz,
      Urheberrecht oder branchenspezifischer Regulierung nur punktuell beachtet werden.
      Sinnvoll ist eine benannte Stelle, die Mindestanforderungen bündelt, praxisnahe
      Leitlinien formuliert und bei Unsicherheiten externe fachliche Beratung einholt.
    </li>
    <li>
      <strong>Fehlende Transparenz gegenüber Kund:innen und Partnern.</strong>
      Wenn unklar bleibt, an welchen Stellen KI Beiträge leistet, kann dies zu
      Vertrauensverlust führen. Gegenmaßnahmen sind kurze, verständliche Hinweise
      zur Nutzung von KI sowie nachvollziehbare Dokumentation im Hintergrund.
    </li>
  </ul>

  <h3>3. Qualitäts-, Transparenz- und Akzeptanzrisiken</h3>
  <ul>
    <li>
      <strong>Inkonsistente Ergebnisse und Qualitätsstreuung.</strong>
      Werden Prompts, Vorlagen und Workflows nicht dokumentiert, hängen Qualität und
      Stil stark von der jeweiligen Person ab. Dies erschwert reproduzierbare Ergebnisse.
      Abhilfe schaffen einheitliche Templates, kurze Leitfäden und regelmäßige Reviews
      von Beispielausgaben.
    </li>
    <li>
      <strong>Übervertrauen in KI-Ergebnisse.</strong>
      Wenn Texte, Analysen oder Bewertungen ungeprüft übernommen werden, können
      Fehler oder Halluzinationen direkt in Kundendokumente und Entscheidungen
      einfließen. Notwendig sind klare Regeln für manuelle Prüfung, Vier-Augen-Prinzip
      bei kritischen Inhalten sowie einfache Checklisten für Qualitätskontrolle.
    </li>
    <li>
      <strong>Akzeptanzprobleme im Alltag.</strong>
      In Teams und größeren Organisationen entsteht Widerstand, wenn der Nutzen von KI
      nicht nachvollziehbar ist oder Workflows als zu komplex empfunden werden.
      Gegenmaßnahmen sind verständliche Kommunikation der Ziele, kleine Pilotprojekte
      mit sichtbarem Nutzen und das aktive Einholen von Feedback, um Routinen anzupassen.
    </li>
    <li>
      <strong>Unklare Nachvollziehbarkeit von Entscheidungen.</strong>
      Wenn nicht dokumentiert ist, welche Rolle KI in der Vorbereitung von Angeboten,
      Reports oder Entscheidungen spielt, wird es im Streitfall schwierig, Entscheidungswege
      zu rekonstruieren. Eine kurze interne Dokumentation zu „Wo unterstützt KI?“ senkt
      dieses Risiko deutlich.
    </li>
  </ul>

  <h3>4. Abhängigkeiten, Betriebs- und Lieferantenrisiken</h3>
  <ul>
    <li>
      <strong>Starke Abhängigkeit von einzelnen Tools oder Plattformen.</strong>
      Wenn zentrale Workflows ausschließlich auf einem Dienst oder einem Modell basieren,
      führen Preisänderungen, Ausfälle oder geänderte Nutzungsbedingungen schnell zu
      Unterbrechungen. Gegenmaßnahmen sind einfache Fallback-Szenarien, Exportmöglichkeiten
      für Daten sowie die Beobachtung von Alternativen.
    </li>
    <li>
      <strong>Unklare Regelungen mit Dienstleistern.</strong>
      Werden Auftragsverhältnisse, Datenverarbeitung oder Service-Level nicht explizit
      vereinbart, können Lücken in Haftung und Verfügbarkeit entstehen.
      Sinnvoll sind klare Verträge, vereinbarte Reaktionszeiten und transparente
      Angaben zur Datenhaltung.
    </li>
    <li>
      <strong>Fehlende Notfall- und Wiederanlaufplanung.</strong>
      Wenn nicht vorab geklärt ist, wie im Fall von Systemausfällen, Datenverlust oder
      Fehlkonfigurationen reagiert wird, verzögert sich der Wiederanlauf.
      Empfohlen sind einfache Notfallpläne, regelmäßige Backups sowie definierte
      Kontaktwege für kritische Vorfälle.
    </li>
    <li>
      <strong>Überkomplexe Tool-Landschaft.</strong>
      Werden zu viele spezialisierte KI-Tools parallel eingeführt, steigt der Aufwand
      für Pflege, Schulung und Koordination. Gegenmaßnahmen sind Konsolidierung auf
      wenige Kernlösungen und eine bewusst schlanke Tool-Strategie.
    </li>
  </ul>

  <h3>5. Risiko-Matrix – Überblick über zentrale Risiken</h3>
  <table class="table">
    <thead>
      <tr>
        <th>Risikobereich</th>
        <th>Typische Auswirkung</th>
        <th>Eintrittswahrscheinlichkeit</th>
        <th>Auswirkungsstärke</th>
        <th>Empfohlene Schwerpunkt-Maßnahmen</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Strategie & Organisation</td>
        <td>Verzettelung, ausbleibende Wirkung, Frust im Alltag</td>
        <td>mittel</td>
        <td>hoch</td>
        <td>Klares Zielbild, priorisierte Use Cases, benannte Verantwortung für KI.</td>
      </tr>
      <tr>
        <td>Daten & Sicherheit</td>
        <td>Fehlende Transparenz, potenzielle Datenschutz-Verstöße</td>
        <td>mittel bis hoch</td>
        <td>hoch</td>
        <td>Kurzleitlinie für Datennutzung, Zugriffs- und Passwortkonzept, Dokumentation der Dienste.</td>
      </tr>
      <tr>
        <td>Qualität & Akzeptanz</td>
        <td>Uneinheitliche Ergebnisse, Misstrauen oder Blindvertrauen in KI</td>
        <td>mittel</td>
        <td>mittel bis hoch</td>
        <td>Standards für Templates, Review-Loops, verständliche Kommunikation von Nutzen und Grenzen.</td>
      </tr>
      <tr>
        <td>Abhängigkeiten & Betrieb</td>
        <td>Unterbrechungen im Betrieb, Mehrkosten, Lock-in-Effekte</td>
        <td>niedrig bis mittel</td>
        <td>mittel</td>
        <td>Fallback-Szenarien, Konsolidierung der Tool-Landschaft, klare Vereinbarungen mit Dienstleistern.</td>
      </tr>
    </tbody>
  </table>

  <p class="small muted">
    Diese Risikoanalyse zeigt die wichtigsten Handlungsfelder für KI in
    <strong>{{HAUPTLEISTUNG}}</strong> in einem Unternehmen der Größe
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>. Im nächsten Schritt sollten die Risiken
    nach Eintrittswahrscheinlichkeit und Auswirkung priorisiert und in eine konkrete
    Maßnahmenplanung für die kommenden 3–6&nbsp;Monate überführt werden.
  </p>
</section>
