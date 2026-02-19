**WICHTIG – Längenlimit: Deine Antwort darf maximal 400 Wörter umfassen. Kürze lieber als zu überziehen.**

Developer:
<!-- ki_aktivitaeten_ziele.md – v3.0 GOLD STANDARD+
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     ZWECK:
       - Dokumentation der aktuellen KI-Aktivitäten (IST)
       - Ableitung realer SOLL-Ziele (nächste 12 Monate)
       - Strategische KI-Vision (2–3 Jahre)

     PFLICHTVARIABLEN:
       {{KI_PROJEKTE}}         // Liste oder leer
       {{HAUPTLEISTUNG}}       // Text oder leer
       {{TOOLS_AKTUELL}}       // Liste oder leer

     Nicht verwenden:
       - Keine erfundenen KI-Projekte, keine Fantasie-Tools.
       - Keine generischen, nicht belegten IST-Aussagen.
       - Keine unrealistischen Ziele.
       - Keine Projekte nennen, die nicht in {{KI_PROJEKTE}} oder {{TOOLS_AKTUELL}} stehen.
       - Keine Platzhaltertexte („Platzhalter", „TODO" oder andere Template-Marker).

     IST-REGEL:
       - Wenn ALLE drei Variablen leer sind → statt Tabelle: Text "Noch keine KI-Projekte im Einsatz."
       - Wenn eine Pflichtvariable fehlerhaft oder nicht lesbar ist → „Fehler: Datenquelle nicht verfügbar.“

     SOLL-REGEL:
       - Ziele ausschließlich aus Quick Wins + Gamechanger + Hauptleistung ableiten.
       - Max. 6 Ziele, chronologisch (Q2 → Q3 → Q4 → Q1 Folgejahr).

     VISION:
       - Max. 4 strategische Aussagen.
       - Keine Zahlen erfinden (MRR, ARR nur wenn im Briefing vorhanden).

     OUTPUT:
       - Exakt ein <section>-Block mit:
         * <h2>KI-Aktivitäten & Ziele</h2>
         * IST-Stand (Tabelle oder Hinweis)
         * SOLL-Ziele (UL)
         * Strategische KI-Vision (UL)
-->

<section class="section ki-aktivitaeten">
  <h2>KI-Aktivitäten &amp; Ziele</h2>

  <!-- IST-STAND -->
  <h3>IST-Stand (Aktuelle KI-Nutzung)</h3>

  <!-- Dynamische Fehlerbehandlung -->
  <!-- Wenn Variablen beschädigt/fehlend sind: -->
  <!-- <div class="error">Fehler: Datenquelle nicht verfügbar.</div> -->

  <!-- Wenn KEINE KI-Projekte, KEINE Tools & KEINE Hauptleistung -->
  <!-- <p>Noch keine KI-Projekte im Einsatz.</p> -->

  <!-- Standardfall: Tabelle -->
  <table class="table">
    <thead>
      <tr>
        <th>Bereich</th>
        <th>Tool/System</th>
        <th>Nutzung</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      <!-- AUS {{KI_PROJEKTE}}, {{HAUPTLEISTUNG}}, {{TOOLS_AKTUELL}} generierte Zeilen -->
      <!-- Beispiel für GPT:
           <tr>
             <td>Bereich A</td>
             <td>Tool X</td>
             <td>Kurzbeschreibung</td>
             <td>Produktiv / In Planung / Explorativ</td>
           </tr>
      -->
    </tbody>
  </table>

  <!-- SOLL-ZIELE -->
  <h3>SOLL-Ziele (Nächste 12 Monate)</h3>
  <ul>
    <!-- GPT generiert 3–6 Ziele, geordnet nach Quartal.
         Beispiele:
         <li><strong>Q2:</strong> Quick-Win A integrieren.</li>
         <li><strong>Q3:</strong> Gamechanger-MVP starten.</li>
         <li><strong>Q4:</strong> Standardisierung & Reporting-Zyklus.</li>
    -->
  </ul>

  <!-- VISIONS-KAPITEL -->
  <h3>Strategische KI-Vision (2–3 Jahre)</h3>
  <ul>
    <!-- GPT generiert 2–4 langfristige strategische Visionen.
         Beispiele:
         <li>KI-gestützte, standardisierte End-to-End-Prozesse im Bereich {{HAUPTLEISTUNG}}.</li>
         <li>Wissensmodule & wiederverwendbare Workflows.</li>
         <li>Skalierbare, auditierbare KI-Architektur.</li>
    -->
  </ul>
</section>
