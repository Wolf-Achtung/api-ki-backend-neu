
Wichtig: In dieser Version kommen **keine** `{CONTEXT_…}`‑Platzhalter mehr vor.

---

## 3. `recommendations.md` – finale Version ohne `{CONTEXT_…}`

Bitte `prompts/de/recommendations.md` komplett durch Folgendes ersetzen:

```markdown
<!-- recommendations.md – v2.5 GOLD STANDARD+ BRANCHE, SIZE & FÖRDERUNG
     Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences. -->

<!-- KONTEXT-VARIABLEN (werden im System befüllt, NICHT im Output erwähnen)
     {{BRANCHE}} / {{BRANCHE_LABEL}}
     {{COMPANY_SIZE}} in {solo, team, kmu}
     {{UNTERNEHMENSGROESSE_LABEL}}
     {{HAUPTLEISTUNG}}
     {{BUNDESLAND_LABEL}}
     Score-Kontext: score_gesamt, score_governance, score_sicherheit,
                    score_befaehigung, score_nutzen
     Zusätzlich stehen Auswertungen aus Quick Wins, 90‑Tage‑Roadmap,
     Business Case und Förderpotenzial zur Verfügung. -->

<section class="section recommendations">
  <h2>Empfehlungen</h2>

  <p>
    Die folgenden Handlungsempfehlungen basieren auf den Analyse-Ergebnissen
    dieses Reports: Scores, identifizierte Quick Wins, 90‑Tage‑Roadmap,
    Business Case und – falls verfügbar – passenden Förderprogrammen
    für <strong>{{BUNDESLAND_LABEL}}</strong>.
    Sie sind speziell auf <strong>{{HAUPTLEISTUNG}}</strong> in der Branche
    <strong>{{BRANCHE_LABEL}}</strong> und die Unternehmensgröße
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> zugeschnitten.
  </p>

  <ol class="recommendations-list">
    <li>
      <h3>Empfehlung 1: [prägnanter Titel – max. 10 Wörter]</h3>
      <p>
        <strong>Problem im Kernprozess:</strong>
        [konkreter Engpass in {{HAUPTLEISTUNG}}, z. B. Medienbruch,
        manuelle Doppelarbeit, lange Durchlaufzeiten.]
      </p>
      <p>
        <strong>Empfohlene Maßnahme:</strong>
        [Zentrale Lösung in 1–2 Sätzen, gerne an vorhandene Quick Wins
        und Roadmap-Schritte anknüpfen.]
      </p>
      <p>
        <strong>Nutzen &amp; ROI:</strong>
        [messbare Wirkung: z. B. −X % Bearbeitungszeit, −Y % Fehler/
        Nachbesserungen, +Z € Umsatz/Monat. Auf Größe {{UNTERNEHMENSGROESSE_LABEL}}
        skaliert, keine Phantasiezahlen.]
      </p>
      <p>
        <strong>Aufwand &amp; Budget:</strong>
        [realistische Größenordnung – z. B. 3–5 Tage interner Aufwand
        + externes Budget in branchenüblichen Größen; bei Solo deutlich
        kleiner, bei KMU größer.]
      </p>
      <p>
        <strong>Verantwortlich:</strong>
        [Rollen passend zu {{COMPANY_SIZE}} – z. B. „Sie selbst“ (solo),
        „kleines Projektteam (2–3 Personen)“ oder „Fachbereich + IT“ (kmu).]
      </p>
      <p>
        <strong>Förderoption (falls sinnvoll):</strong>
        [kurzer Hinweis, ob und wie Förderprogramme aus dem Report genutzt
        werden können – z. B. Zuschuss für Beratung/Implementierung.]
      </p>
    </li>

    <!-- 3–5 weitere Empfehlungen im selben Muster, priorisiert nach Wirkung & Umsetzbarkeit -->
  </ol>

  <p class="small muted">
    Hinweis: Die genannten Budgets dienen der Orientierung und ersetzen
    keine individuelle Finanz- oder Rechtsberatung. Nutzen Sie die
    detaillierten Angaben aus Business Case und Förderkapitel für die
    konkrete Planung.
  </p>
</section>
