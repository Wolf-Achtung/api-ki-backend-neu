
---

### `strategie_governance.md` – neue Version

```markdown
Developer:
# strategie_governance.md – v4.1 GOLD STANDARD+ (size-aware, validator-safe)

ZIEL DES PROMPTS
- Erzeuge eine kompakte, strategische Einordnung von KI-Strategie & Governance für das Unternehmen.
- Verbinde bestehende Rahmenbedingungen (Richtlinien, Datenschutz, Meldewege) mit klaren Leitlinien für die nächsten 12–24 Monate.
- Der Abschnitt soll für Geschäftsführung / Inhaber als Grundlage für Entscheidungen dienen und zu Risiken, Roadmap und AI-Act-Teil passen.

EINGABE-VARIABLEN (werden im Kontext bereitgestellt)
- {{BRANCHE_LABEL}}
- {{UNTERNEHMENSGROESSE_LABEL}}
- {{COMPANY_SIZE}} – "solo", "small_team", "kmu"
- {{GOVERNANCE_RICHTLINIEN_LABEL}}
- {{CHANGE_MANAGEMENT_LABEL}}
- {{MELDEWEGE_LABEL}}
- {{DATENSCHUTZ_LABEL}}
- {{LOESCHREGELN_LABEL}}
- {{DATENSCHUTZBEAUFTRAGTER_LABEL}}
- {{FOLGENABSCHAETZUNG_LABEL}}
- {{INTERNE_KI_KOMPETENZEN_LABEL}}

GRÖSSENLOGIK
- Solo („{{COMPANY_SIZE}} = 'solo'“):
  - Governance schlank und pragmatisch beschreiben (klare Regeln, Checklisten, feste Routinen).
  - Direkte Verantwortung beim Inhaber; keine Begriffe wie „Abteilung“ oder „Bereich“ verwenden.
- Kleines Team („small_team“):
  - Fokus auf wenige Kernrollen (z. B. Geschäftsführung + eine verantwortliche Person).
  - Governance als leichtgewichtige, gut kommunizierte Struktur.
- KMU („kmu“):
  - Mehrere Funktionen/Teams einbeziehen, aber trotzdem auf das Wesentliche fokussieren.
  - Verantwortlichkeiten klar, ohne Konzernsprache.

VERBOTEN IM OUTPUT
- Keine Wörter: „Platzhalter“, „Content wird erstellt“, „Freitextfeld“, „TODO“.
- Keine Hinweise auf Prompt, Variablen oder interne Bewertungslogik.
- Keine leeren Floskeln wie „es sollten noch Richtlinien erstellt werden, wenn Zeit ist“.

STIL & UMFANG
- Ton: klar, sachlich, vertrauensbildend.
- Umfang: ca. 8–12 Sätze Gesamttext, ergänzt um 1–2 Listen mit je 3–6 Punkten.
- Klare Verbindung zwischen aktuellem Status und konkreten nächsten Schritten herstellen.

HTML-STRUKTUR (Beispiel – in der Antwort vollständig befüllen)

```html
<section class="section governance-strategy">
  <h2>KI-Strategie &amp; Governance</h2>

  <p>
    Einleitender Überblick in 2–3 Sätzen, wie ein Unternehmen aus der Branche {{BRANCHE_LABEL}}
    mit der Größe {{UNTERNEHMENSGROESSE_LABEL}} beim Thema KI-Strategie und Governance aktuell aufgestellt ist.
    Hebe Stärken hervor und benenne klar 1–2 zentrale Lücken, ohne dramatisierend zu formulieren.
  </p>

  <h3>Rahmenbedingungen &amp; Regelwerk</h3>
  <ul>
    <li><strong>Richtlinien &amp; Policy:</strong> Kurzbewertung basierend auf {{GOVERNANCE_RICHTLINIEN_LABEL}} (z. B. vorhandene Regeln, Entwürfe, noch offene Lücken).</li>
    <li><strong>Change-Management &amp; Kommunikation:</strong> Einordnung auf Basis von {{CHANGE_MANAGEMENT_LABEL}} – wie gut Veränderungen erklärt und begleitet werden.</li>
    <li><strong>Meldewege &amp; Vorfälle:</strong> Einschätzung anhand von {{MELDEWEGE_LABEL}} – gibt es klare Ansprechpersonen und Prozesse bei Problemen mit KI?</li>
    <li><strong>Datenschutz &amp; Löschregeln:</strong> Bewertung von {{DATENSCHUTZ_LABEL}} und {{LOESCHREGELN_LABEL}} – wie gut sind personenbezogene Daten geschützt und Löschfristen geregelt?</li>
    <li><strong>Verantwortlichkeiten &amp; Kompetenzen:</strong> Hinweis auf {{DATENSCHUTZBEAUFTRAGTER_LABEL}}, {{INTERNE_KI_KOMPETENZEN_LABEL}} und {{FOLGENABSCHAETZUNG_LABEL}} – wer trägt Verantwortung und wie gut ist das Know-how verteilt?</li>
  </ul>

  <h3>Strategische Leitlinien für die nächsten 12–24 Monate</h3>
  <ol>
    <li>
      <strong>Leitlinie&nbsp;1:</strong> Konkreter Schwerpunkt, der Governance und Geschäftsziel verbindet
      (z. B. „klare Spielregeln für den Einsatz von KI in Kundenprojekten“).
    </li>
    <li>
      <strong>Leitlinie&nbsp;2:</strong> Maßnahme zur systematischen Einführung oder Überarbeitung von Richtlinien und Prozessen.
    </li>
    <li>
      <strong>Leitlinie&nbsp;3:</strong> Vorgehen zur Qualifizierung der beteiligten Personen (z. B. Schulungen, Leitfäden, Sprechstunden).
    </li>
    <!-- Optional 1–2 weitere Leitlinien mit klarer Verbindung zu Risiko, Compliance oder Wertschöpfung -->
  </ol>

  <h3>Verantwortung &amp; Steuerung</h3>
  <p>
    Erläutere in 2–3 Sätzen, wie die Steuerung von KI-Strategie und Governance in einem Unternehmen der Größe
    {{UNTERNEHMENSGROESSE_LABEL}} pragmatisch organisiert werden kann:
    bei Solo mit einer klar definierten Owner-Rolle, bei kleinen Teams mit einem kompakten Steuerungskreis,
    bei KMU mit klar benannten Verantwortlichen in mehreren Funktionen.
  </p>

  <p class="small muted">
    Formuliere die Aussagen so, dass sie anschlussfähig an die Roadmap, den AI-Act-Status
    und die Risikobetrachtung im Report sind und unmittelbar als Grundlage für nächste Entscheidungen dienen können.
  </p>
</section>
