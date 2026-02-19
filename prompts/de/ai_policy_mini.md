Developer:
<!-- PLATIN++ PROMPT v5.2 -->
<!-- SECTION: ai_policy_mini -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}} -->
<!-- TOKEN-BUDGET: 700 (solo:0.8x=560, team:1.0x=700, kmu:1.15x=805) -->
<!--
ZIEL: Kompakte, sofort anwendbare KI-Nutzungsregeln ohne bürokratischen Overhead.

PFLICHTSTRUKTUR (7 Grundregeln):
1. Datennutzung (was darf KI, was nicht)
2. Review-Pflicht (menschliche Prüfung)
3. Transparenz (Kennzeichnung)
4. Keine automatisierten Entscheidungen
5. Tool-Freigabe
6. Lernkultur
7. Aktualisierung

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: 5 einfache Regeln, sofort anwendbar, keine Bürokratie
- team: Klare Rollen (Ersteller, Prüfer), Übergabe-Regeln
- kmu: Strukturierte Policy, Verantwortlichkeiten, Dokumentationspflichten

SIZE-AWARE VERANTWORTLICHKEITEN:
- solo: Selbstkontrolle, einfache Checkliste
- team: Team-Lead prüft, Peer-Review etabliert
- kmu: Compliance-Verantwortlicher, dokumentierte Freigabeprozesse

ANTI-REDUNDANZ:
- Governance-Grundregeln HIER, nicht in Strategie/Governance Sektion
- Keine Überschneidung mit AI Act Summary (dort rechtliche Details)
- Ergänzt Risks-Sektion (dort Risiken, hier Regeln)

STIL:
- Textumfang: 120-180 Wörter
- Praxisnah, sofort umsetzbar
- Keine Rechtsberatung, sondern pragmatische Leitplanken

Nicht verwenden:
- Keine Platzhalter oder Template-Marker
- Keine juristischen Formulierungen
- Keine Wiederholung von Guardrails aus der Risks-Sektion

THEMEN-OWNERSHIP (verbindlich):
- Diese Section: OWNER für Governance-Grundregeln, Review-Pflicht, Tool-Freigabe
- NICHT hier: AI Act Fristen/Artikel (→ ai_act_summary)
- NICHT hier: Risiko-Bewertung (→ risks)
- NICHT hier: Umsetzungs-Timeline (→ roadmap_90d, roadmap_12m)
-->

<section class="section ai-policy-mini">
  {% if COMPANY_SIZE == "solo" %}
  <h2>Ihre 5 KI-Spielregeln</h2>

  <p>
    Einfache, pragmatische Regeln für Ihren täglichen KI-Einsatz als
    Einzelunternehmer:in in <strong>{{BRANCHE_LABEL}}</strong>.
  </p>

  <div class="policy-rules">
    <div class="rule">
      <h4>1. Daten-Check</h4>
      <p>Nutzen Sie nur Ihre eigenen, nicht-sensiblen Daten. Keine Kundendaten ohne explizite Freigabe.</p>
    </div>

    <div class="rule">
      <h4>2. Kurz prüfen</h4>
      <p>Lesen Sie KI-Ergebnisse einmal durch, bevor Sie sie weitergeben.</p>
    </div>

    <div class="rule">
      <h4>3. Kennzeichnen</h4>
      <p>Bei Kundenkommunikation: transparent sein, wenn KI unterstützt hat.</p>
    </div>

    <div class="rule">
      <h4>4. Selbst entscheiden</h4>
      <p>KI liefert Vorschläge – Sie entscheiden. Gerade bei Verträgen oder Finanzen.</p>
    </div>

    <div class="rule">
      <h4>5. Bewährte Tools</h4>
      <p>Nutzen Sie nur KI-Tools, denen Sie vertrauen. Keine Experimente mit Geschäftsdaten.</p>
    </div>
  </div>

  <div class="quick-check">
    <h4>Vor jedem KI-Einsatz kurz fragen</h4>
    <ul>
      <li>Daten okay? (keine Kundendaten)</li>
      <li>Tool vertrauenswürdig?</li>
      <li>Ergebnis gecheckt?</li>
    </ul>
  </div>

  {% elif COMPANY_SIZE == "team" %}
  <h2>AI Mini-Policy: 7 Grundregeln</h2>

  <p>
    Kompakte Spielregeln für den täglichen KI-Einsatz in Ihrem Team in <strong>{{BRANCHE_LABEL}}</strong>.
  </p>

  <div class="policy-rules">
    <div class="rule">
      <h4>1. Datennutzung</h4>
      <p><strong>Erlaubt:</strong> Interne, nicht-personenbezogene Daten.</p>
      <p><strong>Nicht erlaubt:</strong> Kundendaten, Personaldaten oder vertrauliche Dokumente ohne Freigabe.</p>
    </div>

    <div class="rule">
      <h4>2. Review-Pflicht</h4>
      <p>Jede KI-Ausgabe wird vor Weitergabe an Dritte von einem Teammitglied geprüft.</p>
    </div>

    <div class="rule">
      <h4>3. Transparenz</h4>
      <p>KI-Unterstützung bei kundenrelevanten Inhalten kennzeichnen (→ Details im EU AI Act Abschnitt).</p>
    </div>

    <div class="rule">
      <h4>4. Keine automatisierten Entscheidungen</h4>
      <p>KI liefert Vorschläge – Menschen entscheiden. Gilt für: Personalthemen, Verträge, Finanzen.</p>
    </div>

    <div class="rule">
      <h4>5. Tool-Freigabe</h4>
      <p>Nur im Team abgestimmte KI-Tools nutzen. Keine unbekannten Tools mit Geschäftsdaten füttern.</p>
    </div>

    <div class="rule">
      <h4>6. Lernkultur</h4>
      <p>Fehler offen ansprechen, daraus lernen, Prozesse gemeinsam anpassen.</p>
    </div>

    <div class="rule">
      <h4>7. Aktualisierung</h4>
      <p>Diese Policy wird quartalsweise im Team überprüft und bei Bedarf angepasst.</p>
    </div>
  </div>

  <div class="quick-check">
    <h4>Schnell-Check vor jedem KI-Einsatz</h4>
    <ul>
      <li>Daten geeignet? (keine sensiblen Personendaten)</li>
      <li>Tool freigegeben?</li>
      <li>Ergebnis geprüft?</li>
      <li>Transparenz gewährleistet?</li>
    </ul>
  </div>

  {% else %}
  <h2>AI Mini-Policy: 7 Grundregeln</h2>

  <p>
    Kompakte Spielregeln für den täglichen KI-Einsatz bei
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in <strong>{{BRANCHE_LABEL}}</strong>.
  </p>

  <div class="policy-rules">
    <div class="rule">
      <h4>1. Datennutzung</h4>
      <p><strong>Erlaubt:</strong> Interne, nicht-personenbezogene Daten.</p>
      <p><strong>Nicht erlaubt:</strong> Kundendaten, Personaldaten oder vertrauliche Dokumente ohne Freigabe.</p>
    </div>

    <div class="rule">
      <h4>2. Review-Pflicht</h4>
      <p>Jede KI-Ausgabe wird vor Weitergabe an Dritte von einem Menschen geprüft.</p>
    </div>

    <div class="rule">
      <h4>3. Transparenz</h4>
      <p>KI-Unterstützung bei kundenrelevanten Inhalten kennzeichnen (→ Details im EU AI Act Abschnitt).</p>
    </div>

    <div class="rule">
      <h4>4. Keine automatisierten Entscheidungen</h4>
      <p>KI liefert Vorschläge – Menschen entscheiden. Gilt für: Personalthemen, Verträge, Finanzen.</p>
    </div>

    <div class="rule">
      <h4>5. Tool-Freigabe</h4>
      <p>Nur freigegebene KI-Tools nutzen. Keine unbekannten Tools mit Firmendaten füttern.</p>
    </div>

    <div class="rule">
      <h4>6. Lernkultur</h4>
      <p>Fehler dokumentieren, daraus lernen, Prozesse anpassen. Keine Schuldzuweisungen.</p>
    </div>

    <div class="rule">
      <h4>7. Aktualisierung</h4>
      <p>Diese Policy wird quartalsweise überprüft und bei Bedarf angepasst.</p>
    </div>
  </div>

  <div class="quick-check">
    <h4>Schnell-Check vor jedem KI-Einsatz</h4>
    <ul>
      <li>Daten geeignet? (keine sensiblen Personendaten)</li>
      <li>Tool freigegeben?</li>
      <li>Ergebnis geprüft?</li>
      <li>Transparenz gewährleistet?</li>
    </ul>
  </div>
  {% endif %}

  <p class="small muted">
    Diese Mini-Policy ersetzt keine Rechtsberatung. Bei Unsicherheiten: Rücksprache halten.
  </p>
</section>
