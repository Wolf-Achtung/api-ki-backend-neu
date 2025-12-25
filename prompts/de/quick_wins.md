Developer:
<!-- PLATIN+++ PROMPT v5.4.3 - ENHANCED QUICK WINS -->
<!-- SECTION: quick_wins -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{HAUPTLEISTUNG}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{BRANCHE_LABEL}}, COMPANY_SIZE, {{STUNDENSATZ_EUR}} -->
<!-- TOKEN-BUDGET: 3500 (solo:0.9x=3150, team:1.0x=3500, kmu:1.1x=3850) -->
<!--
PLATIN+++ v5.4.3: ENHANCED QUICK WINS FORMAT

ZIEL: Konkrete, umsetzbare Quick Wins mit Tool-Namen, Schritt-für-Schritt-Anleitungen und ROI.

WICHTIG - JEDER QUICK WIN MUSS ENTHALTEN:
1. KONKRETER TOOL-NAME mit Preisangabe (z.B. "ChatGPT Plus (20€/Monat)")
2. SCHRITT-FÜR-SCHRITT Anleitung (3-4 nummerierte Schritte)
3. BEISPIEL-PROMPT zum Copy-Paste
4. ROI-BERECHNUNG mit Stundenersparnis und Euro-Wert
5. RISIKEN + LÖSUNGEN

FORMAT PRO QUICK WIN (STRIKT EINHALTEN!):
```
### QUICK WIN #X: [Titel] ([Zeitersparnis]/Monat)

**Problem:** [1-2 Sätze: Konkreter Zeitfresser]

**Lösung in 3 Schritten:**

1. **[Schritt-Titel]** (Setup: [Zeit])
   - Tool: [Konkreter Name] ([Preis/Monat]) – [Empfehlung für Zielgruppe]
   - [Konkrete Anweisung]

2. **[Schritt-Titel]** ([Zeit])
   - [Workflow-Beschreibung]
   - Beispiel-Prompt:
     > "[Konkreter Prompt zum Copy-Paste]"

3. **[Schritt-Titel]** ([Zeit])
   - [Test-/Rollout-Anweisung]

**Investment & ROI:**
| Aufwand | Wert |
|---------|------|
| Setup-Zeit | [X] Stunden |
| Laufende Kosten | [Y]€/Monat |
| Zeitersparnis | [Z] Std./Monat |
| Wert (bei [Stundensatz]€/h) | [Betrag]€/Monat |
| Payback | [Monate] |

**Risiken & Mitigationen:**
- [Risiko 1] → [Lösung]
- [Risiko 2] → [Lösung]
```

ANZAHL NACH GRÖSSE:
- solo: 3 Quick Wins (je 250-350 Wörter)
- team: 4 Quick Wins (je 250-350 Wörter)
- kmu: 4-5 Quick Wins (je 250-350 Wörter)

TOOL-EMPFEHLUNGEN (nutze diese konkreten Namen!):
- ChatGPT Plus: 20€/Monat – Allrounder, gut für Texte
- Claude Pro: 18€/Monat – Längere Dokumente, Analyse
- Microsoft Copilot: 22€/Monat – Office-Integration
- Notion AI: 10€/Monat – Wissensmanagement
- Otter.ai: 17€/Monat – Meeting-Transkription
- Descript: 12€/Monat – Audio/Video-Transkription
- Grammarly Business: 15€/Nutzer/Monat – Textqualität
- Jasper: 49€/Monat – Marketing-Content
- Copy.ai: 36€/Monat – Copywriting
- DeepL Pro: 25€/Monat – Übersetzungen

STUNDENSATZ für ROI:
- solo: 80-120€/h (nutze {{STUNDENSATZ_EUR}} falls vorhanden, sonst 100€)
- team: 70-90€/h (Durchschnitt)
- kmu: 60-80€/h (Durchschnitt)

BRANCHENSPEZIFIK BEACHTEN:
- {{BRANCHE_LABEL}}: Typische Aufgaben und Workflows dieser Branche
- {{HAUPTLEISTUNG}}: Beziehe Quick Wins auf diese Kernleistung
-->

## Quick Wins – Sofort umsetzbare Maßnahmen

{% if COMPANY_SIZE == "solo" %}
Die folgenden 3 Quick Wins sind speziell für Solo-Selbstständige im Bereich **{{HAUPTLEISTUNG}}** konzipiert. Jede Maßnahme können Sie diese Woche starten:

### QUICK WIN #1: E-Mail-Entwürfe automatisieren (5-8 Std./Monat)

**Problem:** Wiederkehrende E-Mails (Angebote, Terminbestätigungen, Nachfassschreiben) kosten täglich 20-30 Minuten, obwohl 80% der Struktur identisch ist.

**Lösung in 3 Schritten:**

1. **Tool einrichten** (Setup: 30 Min.)
   - Tool: ChatGPT Plus (20€/Monat) oder Claude Pro (18€/Monat)
   - Erstellen Sie einen Ordner "E-Mail-Vorlagen" mit Ihren 5 häufigsten E-Mail-Typen

2. **Basis-Prompt erstellen** (30 Min.)
   - Trainieren Sie das Tool mit Ihrem Schreibstil
   - Beispiel-Prompt:
     > "Du bist mein E-Mail-Assistent. Mein Stil ist professionell-freundlich, ich duze Kunden nach dem ersten Kontakt. Schreibe eine Angebotsbestätigung für [Projekt]. Kernpunkte: [Leistungen], [Preis], [Starttermin]. Halte dich kurz (max. 150 Wörter)."

3. **In Workflow integrieren** (1 Woche Test)
   - Nutzen Sie das Tool für jeden E-Mail-Entwurf > 3 Sätze
   - Prüfen und anpassen Sie jeden Entwurf vor dem Versand

**Investment & ROI:**
| Aufwand | Wert |
|---------|------|
| Setup-Zeit | 1 Stunde |
| Laufende Kosten | 20€/Monat |
| Zeitersparnis | 6 Std./Monat |
| Wert (bei {{STUNDENSATZ_EUR}}€/h) | {{STUNDENSATZ_EUR | default(100) | int * 6}}€/Monat |
| Payback | < 1 Woche |

**Risiken & Mitigationen:**
- Generische Formulierungen → Immer persönliche Anpassung vor Versand
- Datenschutz bei Kundennamen → Nur anonymisierte Anfragen stellen

---

### QUICK WIN #2: Dokument-Zusammenfassungen beschleunigen (4-6 Std./Monat)

**Problem:** Verträge, Briefings und Fachtexte durchzuarbeiten kostet viel Zeit. Oft suchen Sie nur 3-5 Kernpunkte.

**Lösung in 3 Schritten:**

1. **PDF-fähiges Tool wählen** (Setup: 15 Min.)
   - Tool: Claude Pro (18€/Monat) – beste Dokumentenanalyse
   - Alternative: ChatGPT Plus mit PDF-Upload (20€/Monat)

2. **Standard-Analyse-Prompts erstellen** (20 Min.)
   - Beispiel-Prompt für Verträge:
     > "Analysiere diesen Vertrag und gib mir: 1) Die 5 wichtigsten Verpflichtungen für mich, 2) Kündigungsfristen und -bedingungen, 3) Haftungsklauseln (vereinfacht erklärt), 4) Risiken, die ich beachten sollte. Format: Bullet Points, max. 300 Wörter."

3. **Bei jedem längeren Dokument anwenden** (laufend)
   - Dokument hochladen, Prompt nutzen, Zusammenfassung prüfen
   - Wichtig: Immer Originaldokument für finale Entscheidungen konsultieren

**Investment & ROI:**
| Aufwand | Wert |
|---------|------|
| Setup-Zeit | 30 Minuten |
| Laufende Kosten | 18€/Monat |
| Zeitersparnis | 5 Std./Monat |
| Wert (bei {{STUNDENSATZ_EUR}}€/h) | {{STUNDENSATZ_EUR | default(100) | int * 5}}€/Monat |
| Payback | < 1 Woche |

**Risiken & Mitigationen:**
- Wichtige Details übersehen → Zusammenfassung nur als Startpunkt, Original prüfen
- Vertrauliche Dokumente → Keine Kundendaten hochladen ohne Vereinbarung

---

### QUICK WIN #3: Angebots- und Präsentationserstellung (4-5 Std./Monat)

**Problem:** Jedes neue Angebot oder jede Präsentation startet bei null, obwohl 60% der Struktur wiederkehrend ist.

**Lösung in 3 Schritten:**

1. **Template-Bibliothek aufbauen** (Setup: 1 Std.)
   - Sammeln Sie Ihre 3 besten Angebote als Referenz
   - Tool: ChatGPT Plus oder Claude Pro (18-20€/Monat)

2. **Master-Prompt für Angebote erstellen**
   - Beispiel-Prompt:
     > "Erstelle ein Angebot für [Projekttyp] im Bereich {{HAUPTLEISTUNG}}. Kunde: [Branche/Größe]. Leistungsumfang: [Punkte]. Budget-Rahmen: [Betrag]. Struktur: 1) Ausgangssituation (2 Sätze), 2) Leistungen als Bullet Points, 3) Ihr Nutzen (3 Punkte), 4) Investment & Timeline, 5) Nächste Schritte. Tonalität: Professionell, lösungsorientiert. Max. 400 Wörter."

3. **Qualitätsprüfung etablieren** (laufend)
   - Jedes generierte Angebot mit Checkliste prüfen: Zahlen korrekt? Tonalität passend? USPs enthalten?

**Investment & ROI:**
| Aufwand | Wert |
|---------|------|
| Setup-Zeit | 1,5 Stunden |
| Laufende Kosten | 0€ (nutzt bestehendes Tool) |
| Zeitersparnis | 4,5 Std./Monat |
| Wert (bei {{STUNDENSATZ_EUR}}€/h) | {{STUNDENSATZ_EUR | default(100) | int * 4}}€/Monat |
| Payback | sofort |

**Risiken & Mitigationen:**
- Generische Angebote → Immer 15 Min. für kundenspezifische Anpassung einplanen
- Falsche Zahlen → Alle Preise und Termine manuell verifizieren

{% elif COMPANY_SIZE == "team" %}
Die folgenden 4 Quick Wins sind für Teams (2-10 Personen) im Bereich **{{HAUPTLEISTUNG}}** konzipiert. Start: Diese Woche.

### QUICK WIN #1: Meeting-Protokolle automatisieren (3-5 Std./Monat pro Person)

**Problem:** Nach jedem Meeting muss jemand 30-45 Minuten ein Protokoll schreiben. Oft verzögert sich dies und Details gehen verloren.

**Lösung in 3 Schritten:**

1. **Transkriptions-Tool einrichten** (Setup: 45 Min.)
   - Tool: Otter.ai Business (17€/Nutzer/Monat) oder Microsoft Copilot (22€/Monat)
   - Mit Kalender verbinden für automatische Meeting-Erkennung

2. **Protokoll-Template definieren** (30 Min.)
   - Standard-Struktur: Teilnehmer, Themen, Entscheidungen, Action Items, Nächster Termin
   - Beispiel-Prompt nach Transkription:
     > "Erstelle aus dieser Meeting-Transkription ein strukturiertes Protokoll: 1) Teilnehmer, 2) Besprochene Themen (Bullet Points), 3) Getroffene Entscheidungen, 4) Action Items mit Verantwortlichen und Deadline. Maximal 1 Seite."

3. **Team-Rollout** (1 Woche)
   - Pilotphase mit 2-3 Meetings pro Woche
   - Feedback sammeln, Protokoll-Qualität anpassen

**Investment & ROI:**
| Aufwand | Wert |
|---------|------|
| Setup-Zeit | 2 Stunden |
| Laufende Kosten | 17€/Nutzer/Monat |
| Zeitersparnis | 4 Std./Monat/Person |
| Wert (bei 75€/h Teamschnitt) | 300€/Monat/Person |
| Payback | < 1 Woche |

**Risiken & Mitigationen:**
- Vertrauliche Gespräche → Transkription nur bei internen Meetings aktivieren
- Akzeptanz im Team → Pilotphase mit Early Adopters starten

---

### QUICK WIN #2: Standardtexte & Vorlagen zentralisieren (5-8 Std./Monat Team)

**Problem:** Jedes Teammitglied schreibt E-Mails, Angebote und Reports unterschiedlich. Qualität schwankt, Onboarding dauert.

**Lösung in 3 Schritten:**

1. **Zentrale Prompt-Bibliothek einrichten** (Setup: 2 Std.)
   - Tool: Notion AI (10€/Nutzer/Monat) oder Team-ChatGPT (25€/Nutzer/Monat)
   - Ordner-Struktur: E-Mails, Angebote, Reports, Kundenanfragen

2. **Best-Practice-Prompts dokumentieren**
   - Top-Performer im Team identifizieren, deren Vorlagen als Basis nutzen
   - Beispiel-Prompt für Kundenanfragen:
     > "Beantworte diese Kundenanfrage zu [Thema]. Tonalität: Freundlich-professionell, [Du/Sie]. Struktur: 1) Danke für die Anfrage, 2) Direkte Antwort auf die Frage, 3) Zusätzlicher Mehrwert/Tipp, 4) Angebot für nächsten Schritt. Max. 200 Wörter."

3. **Qualitäts-Review einführen** (laufend)
   - Wöchentlicher 15-Min-Check: Welche Prompts funktionieren gut, welche müssen angepasst werden?

**Investment & ROI:**
| Aufwand | Wert |
|---------|------|
| Setup-Zeit | 4 Stunden |
| Laufende Kosten | 10€/Nutzer/Monat |
| Zeitersparnis | 6 Std./Monat Team |
| Wert (bei 75€/h) | 450€/Monat |
| Payback | 2-3 Wochen |

**Risiken & Mitigationen:**
- Veraltete Prompts → Monatliche Review-Routine einplanen
- Zu starre Vorgaben → 20% Anpassungsspielraum für individuelle Fälle lassen

---

### QUICK WIN #3: Recherche & Wissensaufbereitung (4-6 Std./Monat Team)

**Problem:** Marktrecherchen, Wettbewerbsanalysen und Fachthemen-Briefings kosten viel Zeit und werden oft nicht teamweit geteilt.

**Lösung in 3 Schritten:**

1. **KI-Recherche-Workflow definieren** (Setup: 1 Std.)
   - Tool: Claude Pro (18€/Monat) + Perplexity Pro (20€/Monat) für aktuelle Quellen
   - Recherche-Template erstellen

2. **Standard-Recherche-Prompts nutzen**
   - Beispiel-Prompt:
     > "Recherchiere zum Thema [X] im Kontext von {{BRANCHE_LABEL}}. Ich brauche: 1) 5 Key Facts (mit Quellenangabe falls möglich), 2) Aktuelle Trends (2024-2025), 3) 3 Handlungsempfehlungen für unser Team. Zielgruppe: [Intern/Kunde]. Format: Executive Summary (max. 400 Wörter)."

3. **Wissens-Sharing etablieren** (laufend)
   - Zentrale Ablage für Recherchen (Notion, Confluence)
   - Wöchentlicher "Learnings"-Slot im Team-Meeting (5 Min.)

**Investment & ROI:**
| Aufwand | Wert |
|---------|------|
| Setup-Zeit | 1,5 Stunden |
| Laufende Kosten | 38€/Monat (2 Tools) |
| Zeitersparnis | 5 Std./Monat Team |
| Wert (bei 75€/h) | 375€/Monat |
| Payback | 1-2 Wochen |

**Risiken & Mitigationen:**
- Veraltete Infos → Immer Datum der Recherche dokumentieren
- Halluzinationen → Wichtige Fakten mit Primärquellen verifizieren

---

### QUICK WIN #4: Qualitätssicherung vor Versand (2-3 Std./Monat Team)

**Problem:** Dokumente gehen an Kunden mit Tippfehlern, inkonsistenter Formatierung oder vergessenen Anpassungen.

**Lösung in 3 Schritten:**

1. **Qualitäts-Checkliste erstellen** (Setup: 30 Min.)
   - Tool: Grammarly Business (15€/Nutzer/Monat) oder LanguageTool (5€/Monat)
   - Checkliste: Rechtschreibung, Zahlen, Kundenname, Datum, Anhänge

2. **Automatisierte Prüfung einrichten**
   - Beispiel-Prompt für finale Prüfung:
     > "Prüfe dieses Dokument auf: 1) Rechtschreib- und Grammatikfehler, 2) Inkonsistenzen (z.B. Du/Sie-Mischung, unterschiedliche Schreibweisen), 3) Fehlende Informationen (Datum, Unterschrift, Kontaktdaten). Liste alle Findings als Bullet Points."

3. **Prüf-Routine etablieren** (laufend)
   - Regel: Kein Dokument > 1 Seite verlässt das Team ohne KI-Check
   - Review-Zeit: 2-3 Minuten pro Dokument

**Investment & ROI:**
| Aufwand | Wert |
|---------|------|
| Setup-Zeit | 1 Stunde |
| Laufende Kosten | 15€/Nutzer/Monat |
| Zeitersparnis | 2,5 Std./Monat Team |
| Qualitätsgewinn | Weniger Korrekturschleifen, besserer Eindruck |
| Payback | < 1 Monat |

**Risiken & Mitigationen:**
- Blindes Vertrauen → Immer menschliche Final-Prüfung bei wichtigen Dokumenten
- Tool-Abhängigkeit → Team weiterhin in manueller Prüfung schulen

{% else %}
Die folgenden 4-5 Quick Wins sind für Unternehmen ({{UNTERNEHMENSGROESSE_LABEL}}) im Bereich **{{HAUPTLEISTUNG}}** konzipiert:

### QUICK WIN #1: Standardisierte Report-Generierung (8-12 Std./Monat Fachbereich)

**Problem:** Wiederkehrende Reports (Wochenberichte, Statusupdates, Management-Summaries) binden Kapazitäten und verzögern sich oft.

**Lösung in 3 Schritten:**

1. **Report-Automation planen** (Setup: 3 Std.)
   - Tool: Microsoft Copilot für Microsoft 365 (22€/Nutzer/Monat) oder Power Automate + GPT
   - Report-Typen priorisieren: Welche 3 Reports kosten am meisten Zeit?

2. **Template-basierte Generierung einrichten**
   - Datenquellen definieren (Excel, CRM, Projektmanagement-Tool)
   - Beispiel-Prompt:
     > "Erstelle einen Wochenbericht für [Abteilung/Projekt]. Datengrundlage: [Quelle]. Struktur: 1) Highlights (3 Punkte), 2) Fortschritt vs. Plan (%), 3) Risiken/Blocker, 4) Nächste Woche (Prioritäten). Zielgruppe: Management. Max. 1 Seite."

3. **Pilot-Phase mit einem Report-Typ** (2 Wochen)
   - Mit unkritischem Report starten
   - Feedback-Schleife: Was muss manuell angepasst werden?

**Investment & ROI:**
| Aufwand | Wert |
|---------|------|
| Setup-Zeit | 6 Stunden |
| Laufende Kosten | 22€/Nutzer/Monat |
| Zeitersparnis | 10 Std./Monat/Bereich |
| Wert (bei 70€/h) | 700€/Monat/Bereich |
| Payback | 3-4 Wochen |

**Risiken & Mitigationen:**
- Datenqualität → Automatische Reports immer mit Datenstand-Datum versehen
- Akzeptanz → Stakeholder frühzeitig einbinden, Quick Win sichtbar machen

---

### QUICK WIN #2: Onboarding & Wissenstransfer beschleunigen (15-20% schnellere Einarbeitung)

**Problem:** Neue Mitarbeitende brauchen Wochen, um sich einzuarbeiten. Wissen ist in Köpfen, nicht in Systemen.

**Lösung in 3 Schritten:**

1. **Wissens-Hub aufbauen** (Setup: 4 Std.)
   - Tool: Notion AI (10€/Nutzer/Monat) oder Confluence + GPT-Integration
   - Struktur: Prozesse, FAQ, Ansprechpartner, Tools, Best Practices

2. **KI-gestütztes Q&A einrichten**
   - Wissensdatenbank als Kontext für KI-Antworten nutzen
   - Beispiel-Prompt für Onboarding-Bot:
     > "Du bist der Onboarding-Assistent für [Abteilung]. Beantworte Fragen neuer Mitarbeitender basierend auf unserer Wissensdatenbank. Bei Unsicherheit verweise auf den zuständigen Ansprechpartner. Tonalität: Hilfsbereit, ermutigend."

3. **Feedback-Loop mit neuen Mitarbeitenden** (laufend)
   - Nach 2 Wochen: Was fehlte? Welche Fragen blieben offen?
   - Wissensdatenbank kontinuierlich erweitern

**Investment & ROI:**
| Aufwand | Wert |
|---------|------|
| Setup-Zeit | 8 Stunden |
| Laufende Kosten | 10€/Nutzer/Monat |
| Zeitersparnis | 20% schnelleres Onboarding |
| Wert (bei 3 Neueinstellungen/Jahr) | 2.000-5.000€/Jahr |
| Payback | 2-3 Monate |

**Risiken & Mitigationen:**
- Veraltetes Wissen → Quartals-Review der Wissensdatenbank
- Zu viel Abhängigkeit von KI → Mentoring-Programm parallel beibehalten

---

### QUICK WIN #3: E-Mail-Triage & Standardantworten (5-8 Std./Monat pro Bereich)

**Problem:** Führungskräfte verbringen 1-2 Stunden täglich mit E-Mails. Viele davon sind Standardanfragen mit wiederkehrenden Antworten.

**Lösung in 3 Schritten:**

1. **E-Mail-Kategorisierung einrichten** (Setup: 2 Std.)
   - Tool: Microsoft Copilot (22€/Monat) oder Gmail + GPT-Integration
   - Kategorien definieren: Dringend, Standard-Anfrage, Info, Delegieren

2. **Antwort-Templates mit KI-Unterstützung**
   - Für jede Kategorie: Basis-Antwort + Personalisierungs-Prompt
   - Beispiel-Prompt:
     > "Kategorisiere diese E-Mail: [Dringend/Standard/Info/Delegieren]. Schlage eine passende Antwort vor basierend auf Kategorie. Bei 'Delegieren': Empfehle Ansprechpartner. Bei 'Standard': Nutze Template [X]. Bei 'Dringend': Markiere Action Items."

3. **Pilot mit Führungskraft starten** (2 Wochen)
   - Täglich 15 Min. gesparte Zeit messen
   - Anpassungen an Templates vornehmen

**Investment & ROI:**
| Aufwand | Wert |
|---------|------|
| Setup-Zeit | 4 Stunden |
| Laufende Kosten | 22€/Monat |
| Zeitersparnis | 7 Std./Monat/Person |
| Wert (bei 80€/h) | 560€/Monat/Person |
| Payback | < 2 Wochen |

**Risiken & Mitigationen:**
- Unpersönliche Antworten → Immer 1-2 persönliche Sätze ergänzen
- Wichtige E-Mails übersehen → Tägliche manuelle Prüfung des Posteingangs beibehalten

---

### QUICK WIN #4: Konsistente Kundenkommunikation (Qualitätsgewinn + 3-5 Std./Monat)

**Problem:** Unterschiedliche Mitarbeitende kommunizieren unterschiedlich. Markenstimme ist nicht konsistent.

**Lösung in 3 Schritten:**

1. **Brand Voice Guide erstellen** (Setup: 3 Std.)
   - Tool: Custom GPT (ChatGPT Team, 25€/Nutzer/Monat)
   - Definieren: Tonalität, Dos/Don'ts, Beispielformulierungen, verbotene Phrasen

2. **Brand-Check als Standard-Workflow**
   - Beispiel-Prompt:
     > "Prüfe diesen Text auf Brand Voice Konsistenz. Unsere Marke ist: [professionell-nahbar / innovativ / traditionell-vertrauensvoll]. Zeige Stellen, die angepasst werden sollten, und schlage Alternativen vor."

3. **Monatliches Brand Voice Audit** (laufend)
   - Stichprobe von 10 Kundenkommunikationen prüfen
   - Erkenntnisse ins Team-Training einfließen lassen

**Investment & ROI:**
| Aufwand | Wert |
|---------|------|
| Setup-Zeit | 4 Stunden |
| Laufende Kosten | 25€/Nutzer/Monat |
| Zeitersparnis | 4 Std./Monat |
| Qualitätsgewinn | Konsistentere Markenwahrnehmung |
| Payback | 1 Monat |

**Risiken & Mitigationen:**
- Zu rigide Vorgaben → Spielraum für Persönlichkeit lassen
- Tool-Überdruss → Nur bei externen Dokumenten anwenden

{% endif %}

---

*Diese Quick Wins basieren auf Erfahrungswerten aus vergleichbaren {{BRANCHE_LABEL}}-Unternehmen. Tatsächliche Einsparungen variieren je nach Ausgangslage und Umsetzungskonsequenz. Starten Sie mit dem Quick Win, der Ihren größten Zeitfresser adressiert.*
