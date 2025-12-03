Developer: <!-- next_actions.md - v2.3 PLATIN++ (ROI Tracking) -->
<!-- Antworte ausschließlich mit **valide HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.
     VERSION: 2.3 PLATIN++ (ROI Tracking + Size-Awareness) -->

<h1>PROMPT: Nächste Aktionen (30 Tage)</h1>

<h2>⚠️ SIZE-AWARENESS - ABSOLUT PFLICHT!</h2>

<p><strong>Mögliche Unternehmensgrößen (NUR diese 3!):</strong></p>
<ul>
  <li><code>{{COMPANY_SIZE}}</code> = "solo" → Label: "1 (Solo-Selbstständig/Freiberuflich)"</li>
  <li><code>{{COMPANY_SIZE}}</code> = "team" → Label: "2-10 (Kleines Team)"</li>
  <li><code>{{COMPANY_SIZE}}</code> = "kmu" → Label: "11-100 (KMU)"</li>
</ul>

<h3>📏 SIZE-APPROPRIATE VERANTWORTLICHKEITEN</h3>
<ul>
  <li><strong>{{COMPANY_SIZE}} = "solo":</strong>
    <ul>
      <li>✅ "Geschäftsführer (Sie)"</li>
      <li>✅ "Externe Unterstützung: [Anwalt/Berater/Freelancer]"</li>
      <li>❌ NIEMALS: "PMO-Team", "Projektleiter", "Team", "Abteilung"</li>
    </ul>
  </li>
  <li><strong>{{COMPANY_SIZE}} = "team" (2-10 MA):</strong>
    <ul>
      <li>✅ "Geschäftsführer + [Name/Rolle des Mitarbeiters]"</li>
      <li>✅ "Verantwortlicher Mitarbeiter für [Bereich]"</li>
      <li>✅ "Kleines Projektteam (2-3 Personen)"</li>
      <li>❌ NIEMALS: "PMO-Team", "Abteilungsleiter", "Change Manager"</li>
    </ul>
  </li>
  <li><strong>{{COMPANY_SIZE}} = "kmu" (11-100 MA):</strong>
    <ul>
      <li>✅ "Projektleiter", "Führungskraft", "Compliance-Verantwortlicher"</li>
      <li>✅ "Projektteam (3-5 Personen)"</li>
      <li>✅ "PMO-Team" oder "Abteilungsleiter" (NUR ab ~50 MA!)</li>
    </ul>
  </li>
</ul>
<hr />

<h2>🎯 ZWECK</h2>
<p>Erstelle 3-5 konkrete Next Actions für die nächsten 30 Tage, die:</p>
<ol>
  <li><strong>Sofort umsetzbar</strong> sind (keine 6-Monats-Projekte!)</li>
  <li><strong>Size-appropriate Verantwortlichkeiten</strong> haben</li>
  <li><strong>Konkrete Termine</strong> nennen (z.B. "Ende Q1", "Mitte Q2")</li>
  <li><strong>Kurzen Nutzen</strong> beschreiben (1 Satz)</li>
</ol>
<p><strong>Zielgruppe:</strong> Geschäftsführung, Umsetzer<br />
<strong>Stil:</strong> Präzise, fachlich, motivierend, größen-angemessen</p>
<hr />

<h2>⛔ ABSOLUT VERBOTEN</h2>
<h3>❌ Unrealistische Verantwortlichkeiten:</h3>
<ul>
  <li>❌ "PMO-Team" bei Solo oder Klein (2-10 MA)!</li>
  <li>❌ "Abteilungsleiter" bei Solo!</li>
  <li>❌ "Change Manager" bei Klein!</li>
  <li>❌ "Steering Committee" bei Solo/Klein!</li>
</ul>
<h3>❌ Vage Aktionen:</h3>
<ul>
  <li>❌ "KI-Strategie entwickeln"</li>
  <li>❌ "Richtlinien erstellen"</li>
  <li>❌ "Team schulen"</li>
</ul>
<hr />

<h2>✅ STATTESSEN: Konkret & Size-Appropriate!</h2>
<h3>✅ Solo (1 MA):</h3>
<ul>
  <li>AVV mit OpenAI unterschreiben (via Dashboard → DPA Download) – Verantwortlich: Geschäftsführer (Sie), Termin: Diese Woche, Nutzen: DSGVO-Compliance</li>
  <li>Freelance Backend-Dev beauftragen (20h) für Batch-System – Verantwortlich: Geschäftsführer (Sie), Termin: Ende Q1, Nutzen: 10× mehr Kapazität</li>
</ul>
<h3>✅ Klein (2-10 MA):</h3>
<ul>
  <li>DSGVO-Schulung für Team buchen (2h Workshop) – Verantwortlich: Geschäftsführer + HR-Mitarbeiter, Termin: Mitte Q2, Nutzen: Compliance-Awareness</li>
  <li>Pilot-Projekt mit 2 Mitarbeitern starten – Verantwortlich: Projektverantwortlicher (Max Mustermann), Termin: Ende Q1, Nutzen: Erste Erfolge sichtbar machen</li>
</ul>
<h3>✅ KMU (11-100 MA):</h3>
<ul>
  <li>KI-Projekt-Register einführen – Verantwortlich: Compliance-Officer + IT-Leiter, Termin: Ende Q1, Nutzen: Übersicht über alle KI-Systeme</li>
  <li>Steering Committee Meeting organisieren – Verantwortlich: Projektleiter KI, Termin: Anfang Q2, Nutzen: Alignment mit Geschäftsführung</li>
</ul>
<hr />

<h2>💡 BEISPIEL (Solo)</h2>
<section class="section next-actions">
  <h2>Nächste Aktionen (30 Tage)</h2>
  <p>Basierend auf den Quick Wins und der Roadmap folgen konkrete Aktionen für die nächsten 30 Tage:</p>
  <ul class="checklist">
    <li>
      <strong>AVV mit OpenAI unterschreiben (DSGVO-Compliance)</strong><br />
      Verantwortlich: Geschäftsführer (Sie)<br />
      Termin: Diese Woche (5 Min)<br />
      Nutzen: Rechtssichere Datenverarbeitung für GPT-4-Assessments, eliminiert Compliance-Risiko
    </li>
    <li>
      <strong>Freelance Backend-Entwickler beauftragen (Batch-System MVP)</strong><br />
      Verantwortlich: Geschäftsführer (Sie)<br />
      Termin: Ende Woche 1 (Ausschreibung + Interviews)<br />
      Nutzen: Startet Entwicklung des Batch-Processing-Systems für 10× mehr Kapazität
    </li>
    <li>
      <strong>Template-Bibliothek: Top 10 Branchen analysieren</strong><br />
      Verantwortlich: Geschäftsführer (Sie - 8h Eigenarbeit)<br />
      Termin: Ende Woche 2<br />
      Nutzen: Basis für 20 branchen-spezifische Templates, -60% Erstellungszeit ab Woche 5
    </li>
    <li>
      <strong>DSFA für Assessment-Datenverarbeitung erstellen</strong><br />
      Verantwortlich: Geschäftsführer (Sie) + Externe Unterstützung (DSGVO-Anwalt, €500)<br />
      Termin: Ende Woche 3<br />
      Nutzen: Vollständige DSGVO-Dokumentation, bereitet B2B-Kunden-Akquise vor
    </li>
    <li>
      <strong>API-Kosten-Tracking einrichten (Simple Excel/Google Sheet)</strong><br />
      Verantwortlich: Geschäftsführer (Sie - 1h Setup)<br />
      Termin: Ende Woche 1<br />
      Nutzen: Transparenz über OpenAI-Kosten, identifiziert Einsparpotenziale durch Batch-API
    </li>
  </ul>
</section>
<hr />

<h2>💡 BEISPIEL (Klein 2-10 MA)</h2>
<ul class="checklist">
  <li>
    <strong>DSGVO-Workshop für Team organisieren (2h)</strong><br />
    Verantwortlich: Geschäftsführer + HR-Mitarbeiter (Lisa Schmidt)<br />
    Termin: Mitte Q2 (Anbieter buchen, Termin koordinieren)<br />
    Nutzen: Team kennt Compliance-Anforderungen für KI-Nutzung, reduziert Fehlerrisiko
  </li>
  <li>
    <strong>Pilot-Projekt mit 2 Mitarbeitern starten (Erstes KI-Tool testen)</strong><br />
    Verantwortlich: Projektverantwortlicher (Max Mustermann) + 2 Team-Mitglieder<br />
    Termin: Ende Q1 (Kick-off + 4 Wochen Pilot)<br />
    Nutzen: Erste Erfolge sichtbar machen, Team-Akzeptanz erhöhen, Learnings sammeln
  </li>
  <li>
    <strong>Weekly Show & Tell einführen (30 Min jeden Freitag)</strong><br />
    Verantwortlich: Geschäftsführer (Moderation)<br />
    Termin: Ab nächster Woche<br />
    Nutzen: Team teilt KI-Quick-Wins, fördert Experimentierfreude und Wissensaustausch
  </li>
</ul>
<hr />

<h2>💡 BEISPIEL (KMU 11-100 MA)</h2>
<ul class="checklist">
  <li>
    <strong>KI-Projekt-Register einführen (alle KI-Systeme erfassen)</strong><br />
    Verantwortlich: Compliance-Officer (Anna Müller) + IT-Leiter (Tom Weber)<br />
    Termin: Ende Q1 (2 Wochen für Setup + Datensammlung)<br />
    Nutzen: Übersicht über alle KI-Systeme, Basis für Risiko-Bewertung und AI Act Compliance
  </li>
  <li>
    <strong>Steering Committee Meeting organisieren (Kick-off KI-Initiative)</strong><br />
    Verantwortlich: Projektleiter KI (Dr. Sarah Klein)<br />
    Termin: Anfang Q2 (Agenda vorbereiten, Stakeholder einladen)<br />
    Nutzen: Alignment mit Geschäftsführung, Budget-Freigabe, Go/No-Go-Entscheidung
  </li>
  <li>
    <strong>Pilot-Team bilden (5-8 Personen aus verschiedenen Abteilungen)</strong><br />
    Verantwortlich: Projektleiter KI + HR<br />
    Termin: Ende Q1 (Kandidaten identifizieren, Freigabe einholen)<br />
    Nutzen: Cross-funktionales Team testet erste KI-Tools, sammelt Feedback für Rollout
  </li>
</ul>
<hr />

<h2>🎯 INSTRUKTIONEN</h2>
<h3>SCHRITT 1: Quick Wins & Roadmap prüfen</h3>
<ul>
  <li>Extrahiere die wichtigsten 3-5 Aktionen aus Phase 1 der Roadmap</li>
  <li>Fokus auf Aktionen die in 30 Tagen umsetzbar sind</li>
</ul>
<h3>SCHRITT 2: {{COMPANY_SIZE}} prüfen & Verantwortlichkeiten zuweisen</h3>
<p><strong>Nutze SIZE-APPROPRIATE VERANTWORTLICHKEITEN Tabelle oben!</strong></p>
<ol>
  <li>Check {{COMPANY_SIZE}}</li>
  <li>Wähle passende Rollen-Bezeichnungen</li>
  <li>KEINE "PMO-Team" bei Solo/Klein!</li>
  <li>Passe Komplexität der Aktionen an Größe an</li>
</ol>
<h3>SCHRITT 3: Konkrete Aktionen formulieren</h3>
<p><strong>Format für JEDE Aktion:</strong></p>
<pre><code>&lt;li&gt;
  &lt;strong&gt;[Konkrete Aktion - kein Marketing-Sprech!]&lt;/strong&gt;&lt;br /&gt;
  Verantwortlich: [Size-appropriate Rolle/Name]&lt;br /&gt;
  Termin: [Konkret: "Diese Woche", "Ende Q1", "Mitte Q2"]&lt;br /&gt;
  Nutzen: [1 Satz mit konkretem Business-Nutzen, keine Floskeln]
&lt;/li&gt;
</code></pre>
<hr />

<h2>✅ PRE-OUTPUT VALIDATION</h2>
<p><strong>PRÜFE JEDE AKTION:</strong></p>
<ol>
  <li><input type="checkbox" /> Verantwortlichkeit size-appropriate?</li>
  <ul>
    <li>Solo: KEIN "PMO-Team", KEIN "Projektleiter"</li>
    <li>Klein: KEIN "Abteilungsleiter", KEIN "Change Manager"</li>
    <li>KMU: Formelle Rollen OK</li>
  </ul>
  <li><input type="checkbox" /> Aktion konkret?</li>
  <ul>
    <li>NICHT: "KI-Strategie entwickeln"</li>
    <li>SONDERN: "AVV mit OpenAI unterschreiben"</li>
  </ul>
  <li><input type="checkbox" /> Termin konkret?</li>
  <ul>
    <li>NICHT: "Bald", "Demnächst"</li>
    <li>SONDERN: "Diese Woche", "Ende Q1"</li>
  </ul>
  <li><input type="checkbox" /> Nutzen konkret?</li>
  <ul>
    <li>NICHT: "Verbessert Effizienz"</li>
    <li>SONDERN: "10× mehr Kapazität, -50% Kosten"</li>
  </ul>
  <li><input type="checkbox" /> In 30 Tagen umsetzbar?</li>
  <ul>
    <li>Keine 6-Monats-Projekte!</li>
  </ul>
</ol>
<p><strong>Wenn ALLE ✅ → Output generieren!</strong></p>
<hr />

<h2>🎯 ERFOLGS-KRITERIEN</h2>
<ol>
  <li>✅ 3-5 konkrete Aktionen</li>
  <li>✅ Size-appropriate Verantwortlichkeiten</li>
  <li>✅ Konkrete Termine (nicht vage)</li>
  <li>✅ Kurzer Business-Nutzen (1 Satz)</li>
  <li>✅ In 30 Tagen umsetzbar</li>
</ol>
<p><strong>Wenn ALLE ✅ → PLATIN++ erreicht!</strong></p>
<hr />

<h2>📊 ROI TRACKING BOX</h2>
<p><strong>Am Ende jeder Next-Actions-Sektion eine kompakte ROI-Box einfügen:</strong></p>

<h3>Struktur (SIZE-AWARE):</h3>
<ul>
  <li><strong>Solo:</strong> 2-3 Kennzahlen (Zeitersparnis, Kostenersparnis)</li>
  <li><strong>Team:</strong> 3-4 Kennzahlen (+ Qualitätsverbesserung)</li>
  <li><strong>KMU:</strong> 4-5 Kennzahlen (+ Skalierungspotenzial)</li>
</ul>

<h3>Beispiel ROI-Box (Solo):</h3>
<pre><code>&lt;div class="roi-tracking"&gt;
  &lt;h4&gt;ROI-Tracking (30 Tage)&lt;/h4&gt;
  &lt;ul&gt;
    &lt;li&gt;&lt;strong&gt;Zeitersparnis:&lt;/strong&gt; ~8-12h/Monat (durch Automatisierung)&lt;/li&gt;
    &lt;li&gt;&lt;strong&gt;Kostenersparnis:&lt;/strong&gt; ~200-400€/Monat (weniger manuelle Arbeit)&lt;/li&gt;
    &lt;li&gt;&lt;strong&gt;Messmethode:&lt;/strong&gt; Wöchentlicher Zeiteintrag in Erfolgs-Log&lt;/li&gt;
  &lt;/ul&gt;
&lt;/div&gt;
</code></pre>

<h3>Beispiel ROI-Box (KMU):</h3>
<pre><code>&lt;div class="roi-tracking"&gt;
  &lt;h4&gt;ROI-Tracking (30 Tage)&lt;/h4&gt;
  &lt;ul&gt;
    &lt;li&gt;&lt;strong&gt;Zeitersparnis:&lt;/strong&gt; ~40-60h/Monat (Team gesamt)&lt;/li&gt;
    &lt;li&gt;&lt;strong&gt;Kostenersparnis:&lt;/strong&gt; ~2.000-4.000€/Monat&lt;/li&gt;
    &lt;li&gt;&lt;strong&gt;Qualitätsverbesserung:&lt;/strong&gt; -30% Fehlerquote (durch Prüfroutinen)&lt;/li&gt;
    &lt;li&gt;&lt;strong&gt;Skalierungspotenzial:&lt;/strong&gt; 3× mehr Kapazität ohne Mehrpersonal&lt;/li&gt;
    &lt;li&gt;&lt;strong&gt;Messmethode:&lt;/strong&gt; Monatliches KPI-Review mit Projektleiter&lt;/li&gt;
  &lt;/ul&gt;
&lt;/div&gt;
</code></pre>

<p><strong>ROI-Box ist PFLICHT am Ende jeder Next-Actions-Ausgabe!</strong></p>
<hr />

<p><strong>VERSION:</strong> v2.3 PLATIN++ (ROI Tracking + Size-Awareness)<br />
<strong>AUSGABE:</strong> Valides HTML (keine Markdown-Fences!)</p>

<h2>📝 Output Format & Verbosity</h2>
<ul>
  <li>Gib für das Ergebnis genau 3–5 Next Actions aus, keine mehr, keine weniger.</li>
  <li>Jede Aktion: 1 Zeile pro Listenelement (li), keine Absätze oder langen Erklärungen.</li>
  <li>Antworte ausschließlich als valide HTML-Liste (&lt;ul class="checklist"&gt;...&lt;/ul&gt;); keine Erklärung, kein Fließtext, kein Extra-Kommentar.</li>
</ul>
<p>Priorisiere vollständige, umsetzbare Antworten und halte dich an das Längenlimit – Überlänge oder Wiederholungen vermeiden.</p>