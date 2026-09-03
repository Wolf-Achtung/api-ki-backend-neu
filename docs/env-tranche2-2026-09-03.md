# ENV-Tranche 2 — korrigiert am 03.09.2026

**Diese Datei ersetzt eine falsche Liste.** Die erste Fassung nannte 37
Variablen zum Löschen. In Railway existierte davon genau eine. Der Grund:
Die Liste war gegen den Code geprüft, aber nie gegen die tatsächlich
gesetzten Variablen. Die übrigen 36 Namen standen zwar in `.env.example`
und in einem älteren Audit — in Railway aber nicht.

Diese Fassung geht den umgekehrten Weg: Ausgangspunkt sind die **273
Shared Variables**, die am 03.09.2026 in Railway stehen. Jeder Name wurde
gegen den Laufzeit-Code geprüft.

Das Prüfverfahren steckt jetzt in `scripts/env_unused.py`:

```
python scripts/env_unused.py meine_variablen.txt
```

Die Datei enthält die Namen so, wie Railway sie anzeigt — durch
Leerzeichen oder Zeilen getrennt.

## Ergebnis: 4 löschen, 1 entscheiden

### Sicher löschen (4)

| Variable | Warum |
|---|---|
| `RATE_LIMIT_PER_MINUTE` | Der Code liest `REPORT_RATE_LIMIT_PER_MINUTE`. |
| `PROMPT_STABILITY_ENABLED` | Der Code liest `STABILITY_SCORING_ENABLED`. |
| `REPORT_ADMIN_EMAIL` | Kein Treffer im ganzen Repo. |
| `CORS_ALLOW_CREDENTIALS` | Nur `tools/validate_env.py` liest sie — ein Diagnosewerkzeug. Die CORS-Einstellung selbst steht fest in `main.py`. |

### Entscheiden (1)

`POLL_INTERVAL` — der Worker liest `WORKER_POLL_INTERVAL`
(`workers/briefings_worker.py:55`). Die gesetzte Variable wirkt nicht.
Zwei Wege: löschen, oder auf `WORKER_POLL_INTERVAL` umbenennen, wenn das
Poll-Intervall wirklich vom Standardwert (2 Sekunden) abweichen soll.

### Stehen lassen: die Smoke-Test-Variablen (5)

`SERVICE_TOKEN`, `SMOKE_AUTH_TOKEN`, `SMOKE_BASE_URL`, `API_BASE_URL`,
`POLL_TIMEOUT` gehören zu `scripts/submit_fixture.py` und den
GitHub-Workflows. Im Railway-Dienst wirken sie nicht. Sie kosten nichts
und dokumentieren die Gegenwerte des Smoke-Tests — `SERVICE_TOKEN` ist
der Client-Wert zu `SERVICE_TOKEN_SECRET`, das der Dienst prüft.

## Drei Schreibweisen-Fallen

Der wichtigere Befund als die Löschliste: Drei Einstellungen laufen auf
ihrem Standardwert, obwohl in Railway etwas anderes steht.

| Railway hat | Der Code liest | Folge |
|---|---|---|
| `RATE_LIMIT_PER_MINUTE` | `REPORT_RATE_LIMIT_PER_MINUTE` | Report-Limit läuft auf 5/Minute |
| `PROMPT_STABILITY_ENABLED` | `STABILITY_SCORING_ENABLED` | Stabilitäts-Scoring läuft auf „an" |
| `POLL_INTERVAL` | `WORKER_POLL_INTERVAL` | Worker pollt alle 2 Sekunden |

Alle drei Standardwerte sind brauchbar. Es besteht kein Handlungsdruck —
aber wer eine dieser Zahlen ändern will, muss den langen Namen setzen.

## Warum das Verfahren vorher danebengriff

Vier blinde Flecken, alle vier jetzt im Skript behandelt und in
`tests/test_kis1274_env_pruefung.py` festgehalten:

1. **Nur nach `os.getenv("NAME")` gesucht.** Namen, die über eine
   Konstante weitergereicht werden, galten als ungenutzt.
   → Nach dem nackten Namen suchen, nicht nach einem Zugriffsmuster.
2. **Zusammengesetzte Namen.** `f"OPENAI_MAX_TOKENS_{sektion}"` steht
   nirgends wörtlich im Code.
   → Die bekannten Präfixe kennen (`PRAEFIXE` im Skript).
3. **Teilzeichenketten.** `RATE_LIMIT_PER_MINUTE` fand sich in
   `REPORT_RATE_LIMIT_PER_MINUTE` — und wurde deshalb als „wird gelesen"
   eingestuft. Diese eine Verwechslung drehte die Antwort ins Gegenteil.
   → Wortgrenzen, die `_` als Wortzeichen behandeln. `\b` reicht nicht.
4. **Helfer statt `os.getenv`.** `_bool_env("X")`, `get_bool("X")`,
   `_truthy("X")`.
   → Löst sich mit Punkt 1.

Ein fünfter Fall kam beim Bauen dazu: Eine Datei, die ENV-Namen nennt,
um über sie zu reden — diese Datei hier, oder eine Testdatei — meldet
jeden Namen darauf als „benutzt". Das Skript überspringt `docs/`,
`tests/` und sich selbst.

## Grenzen des Skripts

Ein Treffer im Laufzeit-Code ist ein Hinweis, kein Beweis. Steht der Name
nirgends in Anführungszeichen, ist er wahrscheinlich nur eine
Python-Konstante gleichen Namens — so lag der Fall bei
`PROMPT_STABILITY_ENABLED`. Das Skript meldet diese Fälle getrennt unter
`NUR BEZEICHNER`. Jede Stelle dort gehört einzeln angesehen.

Umgekehrt gilt: `DATABASE_URL` und `MISE_PYTHON_GITHUB_ATTESTATIONS`
stehen nirgends im Code, weil Railway sie liest. Das Skript kennt sie
(`PLATTFORM_VARIABLEN`).

## Reihenfolge

1. Die vier oben in Railway löschen. Kein Deploy, nur ein Neustart.
   **Nicht während eines Testlaufs.**
2. `POLL_INTERVAL` entscheiden.
3. Danach einen Report erzeugen und mit `scripts/compare_reports.py`
   gegen den letzten Lauf halten. Bleiben die Kennzahlen gleich und
   meldet die Rückfall-Prüfung nichts, war das Löschen folgenlos.
