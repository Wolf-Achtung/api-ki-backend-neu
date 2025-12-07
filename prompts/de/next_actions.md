<!-- PLATIN++ PROMPT v5.4 - SPRINT G6 -->
<!-- SECTION: next_actions -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, {{COMPANY_SIZE}} -->
<!-- TOKEN-BUDGET: 800 (solo:0.8x=640, team:1.0x=800, kmu:1.15x=920) -->
<!--
ZIEL: 3 konkrete Handlungsempfehlungen für die nächsten 30 Tage.

MINDESTLÄNGE (STRIKT!):
- Solo: ≥60 Wörter
- Team: ≥80 Wörter
- KMU: ≥100 Wörter

STRUKTUR (STRIKT!):
- Genau 3 Bullets (NICHT mehr, NICHT weniger)
- Jeder Bullet: Aktion + Zeitrahmen (Woche 1-2, 2-4, etc.)
- KEINE Meta-Sätze ("In diesem Abschnitt...", "Die folgenden Aktionen...")
- Direkt mit der ersten Aktion starten

FORMAT PRO BULLET:
<li>
  <strong>[Konkrete Aktion]</strong> (Woche [X–Y])<br/>
  [1 Satz konkreter Nutzen oder erwartetes Ergebnis]
</li>

ANTI-REDUNDANZ (STRIKT!):
- KEINE Wiederholung aus Quick Wins oder Roadmap
- Fokus auf NÄCHSTE konkrete Schritte, nicht auf Zusammenfassung
- Querverweise nutzen: "→ siehe Roadmap", "→ siehe Quick Wins"

SPRINT G6 - PERSONA HARD-GUARDS (STRIKT!):
{% if COMPANY_SIZE == "solo" %}
SOLO-MODUS - VERBOTEN:
- "Team/Teams/Abteilung/Mitarbeiter" → nicht verwenden
- "PMO-Team/Projektleiter" → nicht verwenden
- Stattdessen: "Sie", "Geschäftsführer", "externe Unterstützung"
{% elif COMPANY_SIZE == "team" %}
TEAM-MODUS - VERBOTEN:
- "Division/Unit/Konzern/Abteilungsleiter" → nicht verwenden
- Stattdessen: "Team", "Projektverantwortlicher", "Teammitglied"
{% else %}
KMU-MODUS - VERBOTEN:
- "Konzern/Division/Unit" → nicht verwenden
- Stattdessen: "Projektleiter", "Fachbereich", "Compliance-Verantwortlicher"
{% endif %}

SIZE-AWARE VERANTWORTLICHKEITEN:
- Solo: "Sie", "Geschäftsführer (Sie)", "Externe Unterstützung: [Rolle]"
- Team: "Projektverantwortlicher", "Geschäftsführer + [Rolle]", "Team (2-3 Personen)"
- KMU: "Projektleiter", "Compliance-Verantwortlicher", "Fachbereichsleiter"
-->

<section class="section next-actions">
  <h2>Nächste Aktionen (30 Tage)</h2>

  <ul class="checklist">
    {% if COMPANY_SIZE == "solo" %}
    <li>
      <strong>KI-Zugang einrichten und erste Vorlage erstellen</strong> (Woche 1–2)<br/>
      Basis für {{OFFERING_LABEL}} schaffen – Zugang testen, erste Prompt-Vorlage für Kernaufgabe anlegen.
    </li>
    <li>
      <strong>Ersten Quick Win umsetzen und Zeit messen</strong> (Woche 2–3)<br/>
      Wiederkehrende Aufgabe mit KI-Unterstützung durchführen, Zeitersparnis dokumentieren (→ siehe Quick Wins).
    </li>
    <li>
      <strong>Einfache Qualitäts-Checkliste erstellen</strong> (Woche 3–4)<br/>
      3-5 Prüfpunkte definieren, um KI-Ergebnisse vor Verwendung zu validieren.
    </li>
    {% elif COMPANY_SIZE == "team" %}
    <li>
      <strong>KI-Owner benennen und gemeinsamen Zugang einrichten</strong> (Woche 1–2)<br/>
      Verantwortlichkeit für Standards und Qualität klären, alle Beteiligten mit Zugang ausstatten.
    </li>
    <li>
      <strong>Ersten teamweiten Quick Win umsetzen</strong> (Woche 2–3)<br/>
      Ausgewählte Aufgabe aus {{OFFERING_LABEL}} mit KI testen, Erfahrungen im Team teilen (→ siehe Quick Wins).
    </li>
    <li>
      <strong>Kurzen Review-Prozess etablieren</strong> (Woche 3–4)<br/>
      Wöchentliches 15-Minuten-Review einführen: Was funktioniert, was nicht? Vorlagen bei Bedarf anpassen.
    </li>
    {% else %}
    <li>
      <strong>Pilotbereich definieren und KI-Verantwortliche:n benennen</strong> (Woche 1–2)<br/>
      Fachbereich mit hohem Potenzial auswählen, Governance-Grundregeln festlegen, Zugänge einrichten.
    </li>
    <li>
      <strong>Quick Wins im Pilotbereich starten und dokumentieren</strong> (Woche 2–4)<br/>
      2-3 priorisierte Anwendungsfälle aus {{OFFERING_LABEL}} testen, erste Zeitersparnis quantifizieren (→ siehe Quick Wins).
    </li>
    <li>
      <strong>Wöchentliche Kurz-Reviews etablieren und Learnings sammeln</strong> (Woche 3–4)<br/>
      Feedback-Schleifen im Pilotbereich einführen, Basis für SOPs und Schulungskonzept schaffen.
    </li>
    {% endif %}
  </ul>

  <div class="roi-tracking">
    <h4>Erwarteter Effekt nach 30 Tagen</h4>
    <ul>
      {% if COMPANY_SIZE == "solo" %}
      <li><strong>Zeitersparnis:</strong> 4–8 Stunden im ersten Monat</li>
      <li><strong>Routine:</strong> KI ist fester Bestandteil des Alltags</li>
      {% elif COMPANY_SIZE == "team" %}
      <li><strong>Zeitersparnis:</strong> 10–20 Stunden im Team gesamt</li>
      <li><strong>Klarheit:</strong> Rollen, Zuständigkeiten und erste Standards definiert</li>
      {% else %}
      <li><strong>Zeitersparnis:</strong> 15–30 Stunden im Pilotbereich</li>
      <li><strong>Governance:</strong> Klare Regeln, erste Dokumentation, messbare Basis</li>
      {% endif %}
    </ul>
  </div>

  <p class="small muted">
    Diese Aktionen bauen auf den Quick Wins und der Roadmap auf. Details → siehe entsprechende Abschnitte.
  </p>
</section>
