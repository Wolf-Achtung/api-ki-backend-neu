<!-- PLATIN++ SHARED INCLUDE | SECTION: alle | OUTPUT: keine (Regelbaustein)
KIS-PROMPT P5: Gemeinsame Grundregeln für alle Report-Sektionen.
Ersetzt die bisher in 4-6 Prompts wortgleich kopierten Blöcke (OPT-A7
Begriffskonsistenz → jetzt im System-Prompt; ROI-/Zahlen-Disziplin →
System-Prompt; hier stehen nur die USER-Prompt-Ebene-Regeln, die das
Ausgabeformat und die Kontext-Nutzung betreffen).
Einbindung in Sektions-Prompts via Jinja-Include-Tag mit Dateiname
'_report_grundregeln.md' (Tag hier nicht wörtlich notiert — würde
Selbst-Inklusion/Rekursion auslösen).
-->

AUSGABEFORMAT (verbindlich)
- Ausgabe ist ein valides HTML-Fragment. Erlaubte Tags: <div>, <p>, <ul>, <ol>, <li>, <strong>, <em>, <span>, <br>, <table>, <thead>, <tbody>, <tr>, <th>, <td> — sofern die Sektions-Aufgabe nichts Engeres vorgibt.
- Keine Markdown-Syntax (kein #, ##, **, ```), keine <h1>–<h4>, kein <script>/<style>, keine Kommentare, kein Text vor oder nach dem HTML.
- Vollständige Sätze mit Satzzeichen; kein Abbruch mitten im Satz.

KONTEXT-NUTZUNG
- Beziehe jede Kernaussage auf die Briefing-Daten (Branche, Unternehmensgröße, Hauptleistung, Ziele). Formuliere so, dass der Satz für ein anderes Unternehmen NICHT unverändert gelten würde.
- Übernimm Zahlen ausschließlich aus dem bereitgestellten Kontext. Fehlende Zahlen: qualitativ formulieren oder als „Annahme: …" kennzeichnen.
- Fakten und Annahmen sichtbar trennen; bei relevanten Entscheidungen den Zielkonflikt benennen (was gewinnt man, was gibt man auf).

STIL
- Keine Assistenten- oder Meta-Sprache („Gerne…", „Hier ist…", „Als KI…").
- Keine Platzhalter im Output (kein „[Name]", „XXX", „TODO", ungefüllte {{Variablen}}).
- Keine Wiederholung von Inhalten, die erkennbar in andere Sektionen gehören (Förderdetails → Förderpotenzial, ROI-Rechnung → Business Case).
