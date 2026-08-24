# Briefing: Cyberangriffs-Check auf ki-sicherheit.jetzt einbinden

**Für:** eine neue Claude-Code-Sitzung im Repository der Website
ki-sicherheit.jetzt (Marketing-Seite, nicht das App-Frontend).
**Stand:** 24.08.2026. Backend und App-Frontend sind fertig und live.
**Auftraggeber:** Wolf Hohl.

---

## 1. Worum es geht

Auf der Startseite steht heute der Button **„Zum KI-Schnell-Check"**. Er
führt zu einem anonymen Fragebogen („Kostenfreier KI-Risiko-Check &
Empfehlung", Thema EU AI Act und DSGVO).

Dieser Einstieg soll durch den **Cyberangriffs-Check** ersetzt werden.
Der neue Check beantwortet eine konkretere Frage: *Wie schnell könnte
Ihr Betrieb einen automatisierten Cyber-Angriff stoppen?*

Das Ergebnis heißt **Reaktionslücke** — die geschätzte Zeit von einem
Alarm bis zur ersten wirksamen Entscheidung. Verglichen wird sie mit
einem Benchmark: Ein automatisierter Angriff ist in rund **15 Minuten**
abgeschlossen.

Der Check ist offen für alle Branchen. Er verlangt keine Anmeldung.

---

## 2. Was bereits fertig ist

**Backend** (`api-ki-backend-neu`, Railway, live):
fünf öffentliche Endpunkte unter `/api/cyber/`, Scoring, LLM-Texte,
PDF-Erzeugung, Mailversand, Bot- und Missbrauchsschutz.

**App-Frontend** (`make-ki-frontend`, Netlify, live):
eine fertige öffentliche Seite `cyber-check.html` mit dem kompletten
Ablauf. Sie ist eigenständig lauffähig.

**Nicht fertig — das ist Ihre Aufgabe:** die Einbindung auf der
Marketing-Seite ki-sicherheit.jetzt.

---

## 3. Zwei Wege — bitte Weg A, sofern nichts dagegen spricht

### Weg A: Verlinken (empfohlen, klein)

Der Button auf der Startseite zeigt auf die fertige Seite. Der
KI-Schnell-Check verschwindet aus der Navigation oder wird zur
Zweitwahl.

**Aufwand:** Button-Ziel und Beschriftung ändern, Texte auf der
Startseite anpassen.
**Kein CORS nötig, kein API-Code auf der Marketing-Seite.**

Prüfen Sie zuerst, unter welcher Adresse `cyber-check.html` ausgeliefert
wird. Das App-Frontend läuft auf einer eigenen Subdomain — im Backend
sind als erlaubte Ursprünge hinterlegt:

```
https://ki-sicherheit.jetzt
https://www.ki-sicherheit.jetzt
https://make.ki-sicherheit.jetzt
https://www.make.ki-sicherheit.jetzt
https://report.ki-sicherheit.jetzt
```

Fragen Sie Wolf, welche davon das App-Frontend ausliefert, oder prüfen
Sie, wohin der bestehende Button „KI-Report" in der Navigation zeigt —
dieselbe Domain, Pfad `/cyber-check.html`.

### Weg B: Nativ nachbauen (größer)

Der Check läuft direkt auf ki-sicherheit.jetzt, im Design der Seite.
Nötig, wenn der Besucher die Domain nicht verlassen soll.

CORS ist dafür bereits vorbereitet: `https://ki-sicherheit.jetzt` und
`https://www.ki-sicherheit.jetzt` stehen in den konservativen Defaults.
**Aber:** Sobald in Railway die Variable `CORS_ORIGINS` gesetzt ist,
gelten die Defaults nicht mehr — dann muss die Domain dort eingetragen
sein. Bitte mit Wolf abklären, bevor Sie Weg B beginnen.

Der komplette Ablauf ist in `make-ki-frontend/cyber-check.html`
implementiert. Nehmen Sie die Datei als Vorlage; das API-Protokoll steht
unten vollständig.

---

## 4. Der Ablauf, den der Nutzer sieht

Der Check ist **zweistufig**. Das ist wichtig und kein Kompromiss:

**Stufe 1 — fünf Fragen, eine pro Bildschirm, große Knöpfe.**
Genau das Muster des heutigen KI-Schnell-Checks. Danach steht das
Ergebnis sofort da: die Reaktionslücke, der Zeitvergleich zum
15-Minuten-Benchmark und die Antworten, die das Ergebnis bestimmt haben.
Keine E-Mail nötig, kein Warten.

**Stufe 2 — der vollständige Report.**
17 weitere Fragen, E-Mail, Einwilligung. Danach kommt eine
Bestätigungsmail. Erst der Klick darauf löst den PDF-Report aus.

### Warum fünf Fragen ein echtes Ergebnis liefern

Die Reaktionslücke wird nach der **Min-Regel** berechnet: aus genau fünf
Feldern (B2, C1, C2, C3, C4) zählt die *schlechteste* Antwort. Der
langsamste Faktor bestimmt das System, nicht der Durchschnitt.

Diese fünf Fragen sind der Kurz-Check. Das Ergebnis ist damit **dieselbe
Zahl** wie im großen Check — keine geschönte Vorschau. Die restlichen 17
Fragen liefern das Blockprofil, die Befunde und die Empfehlungen, also
den Inhalt des PDF-Reports.

Sie dürfen das Kurzergebnis deshalb als vollwertig bewerben. Bitte aber
nie als Messung: Es ist eine Selbstauskunft (siehe Abschnitt 8).

---

## 5. Die fünf Fragen im Wortlaut

Ziehen Sie sie zur Laufzeit von `GET /api/cyber/kurzfragen` — dann
bleibt eine Textänderung im Katalog automatisch wirksam. Zum Entwerfen
des Layouts hier der aktuelle Stand:

**B2 — Ein Alarm schlägt Samstagnacht um 2 Uhr an. Wann erfährt ein
handlungsfähiger Mensch davon?**
1. Montagmorgen
2. Im Lauf des Wochenendes, mit Glück
3. Rufbereitschaft (intern oder Dienstleister) reagiert innerhalb von Stunden
4. Automatische Sofortmaßnahme plus Benachrichtigung innerhalb von Minuten

**C1 — Ein System ist mutmaßlich kompromittiert. Wer darf es sofort vom
Netz nehmen?**
1. Nur die Geschäftsführung nach Rücksprache
2. IT/Dienstleister nach eingeholter Freigabe
3. Benannte Personen nach vorab definierten Kriterien, Info danach
4. Automatische Trennung bei definierten Signalen, menschliche Prüfung danach

**C2 — Gibt es schriftlich festgelegte Wenn-dann-Entscheidungen für den
Ernstfall („Wenn X passiert, wird sofort Y getan — ohne Rückfrage")?**
1. Nein
2. Sinngemäß im Kopf einzelner Personen
3. Für die wichtigsten Szenarien dokumentiert
4. Dokumentiert, freigegeben und mindestens einmal geübt

**C3 — Der Hauptentscheider ist im Flugzeug, im Urlaub oder krank. Was
passiert?**
1. Es wird gewartet
2. Improvisation
3. Benannte Stellvertretung mit klarer Befugnis
4. Entscheidungen hängen nicht an Einzelpersonen (Playbooks + Stellvertreterkette)

**C4 — Dürfen Schutzmaßnahmen zuerst ausgeführt und danach gemeldet
werden — oder braucht jede Maßnahme vorher eine Genehmigung?**
1. Immer erst Genehmigung
2. Genehmigung mit 1–2 Unterschriften
3. Vorab genehmigte Maßnahmen für bekannte Fälle
4. Handeln vor Melden ist für definierte Fälle ausdrücklich erlaubt

### Die vier möglichen Ergebnisse

| schlechteste Antwort | Reaktionslücke | Ampel | Kernaussage |
|---|---|---|---|
| Stufe 1 | mehr als 8 Stunden | rot | Ein automatisierter Angriff ist ~30-mal schneller abgeschlossen, als Ihre Organisation entscheiden kann. |
| Stufe 2 | 2–8 Stunden | rot | Ihre Abläufe stammen aus einer Zeit, in der Angriffe Tage dauerten. |
| Stufe 3 | 15 Minuten – 2 Stunden | gelb | Sie können reagieren — aber nicht in jedem Fall schnell genug. |
| Stufe 4 | unter 15 Minuten | grün | Ihre Entscheidungswege sind auf Maschinengeschwindigkeit vorbereitet. |

---

## 6. Das API-Protokoll (nur für Weg B)

Basis-URL: `https://api-ki-backend-neu-production.up.railway.app/api`

Alle Endpunkte sind öffentlich, ohne Token. Keiner braucht Cookies —
setzen Sie **kein** `credentials: "include"`.

### `GET /cyber/kurzfragen`

Liefert die fünf Fragen. Antwort:

```json
{
  "benchmark_minuten": 15,
  "ehrlichkeitsregel": "geschätzte Reaktionslücke auf Basis Ihrer Angaben",
  "questions": [
    { "id": "B2", "text": "…", "stufen": ["…", "…", "…", "…"] }
  ]
}
```

### `POST /cyber/kurzcheck`

```json
{
  "answers": { "B2": 1, "C1": 2, "C2": 1, "C3": 1, "C4": 2 },
  "hp": "",
  "ms": 45000
}
```

`answers` muss **genau** diese fünf Schlüssel enthalten, Werte 1–4.
`hp` ist das Honigtopf-Feld (siehe Abschnitt 7), `ms` die verstrichene
Zeit seit Seitenaufruf in Millisekunden.

Antwort:

```json
{
  "label": "mehr als 8 Stunden",
  "aussage": "Ein automatisierter Angriff ist ~30-mal schneller …",
  "ampel": "rot",
  "min_stufe": 1,
  "benchmark_minuten": 15,
  "ehrlichkeitsregel": "geschätzte Reaktionslücke auf Basis Ihrer Angaben",
  "treiber": [ { "id": "B2", "text": "…", "antwort": "Montagmorgen" } ]
}
```

`treiber` sind die Antworten, die das Ergebnis bestimmt haben — zeigen
Sie sie. Sie machen die Zahl nachvollziehbar.

Nichts wird gespeichert. Kein LLM, keine Kosten.

### `GET /cyber/fragen`

Der komplette Katalog: sechs Blöcke, 22 Fragen, ohne die internen
Gewichte.

```json
{
  "version": "…",
  "benchmark_minuten": 15,
  "blocks": [
    { "id": "A", "titel": "Kernsysteme",
      "questions": [ { "id": "A1", "text": "…", "stufen": ["…"] } ] }
  ]
}
```

Die fünf bereits beantworteten Fragen stecken darin. Filtern Sie sie
heraus und übernehmen Sie die Antworten aus Stufe 1.

### `POST /cyber/anfordern`

```json
{
  "answers": { "A1": 2, "…": 3 },
  "email": "name@firma.de",
  "einwilligung": true,
  "hp": "",
  "ms": 400000
}
```

`answers` muss **alle 22** Fragen enthalten, Werte 1–4. `einwilligung`
muss `true` sein. Antwort: `202` mit
`{"status": "bestaetigung_gesendet"}`.

Der Report entsteht hier **noch nicht**. Der Nutzer bekommt eine Mail
mit einem Bestätigungslink; erst dessen Klick löst die Erzeugung aus.
Zeigen Sie danach einen Hinweis aufs Postfach, inklusive Spam-Ordner.

### `GET /cyber/bestaetigen`

Wird nur aus der E-Mail heraus aufgerufen und liefert eine fertige
HTML-Seite. **Nicht einbinden, nicht nachbauen.**

### Fehlerfälle, die Sie behandeln müssen

| Code | Bedeutung | Was anzeigen |
|---|---|---|
| 422 | Antworten unvollständig, Einwilligung fehlt, **oder Bot-Verdacht** | Freundlicher Hinweis, Formular offen lassen |
| 429 | IP-Limit erreicht | „Zu viele Anfragen von diesem Anschluss. Bitte später erneut." |
| 5xx / Netzfehler | Backend nicht erreichbar | „Gerade nicht erreichbar", Formular offen lassen |

Der Bot-Verdacht antwortet bewusst mit derselben nichtssagenden Meldung
wie eine fehlende Antwort. **Verraten Sie im Frontend nicht, woran es
lag** — sonst ist der Schutz wertlos.

---

## 7. Missbrauchsschutz — was Sie beitragen müssen

Der Endpunkt löst LLM-Kosten und Mailversand aus. Das Backend schützt
sich selbst (IP-Limits, Bestätigungslink, Ablauffrist, kein zweiter
Report bei Doppelklick). Zwei Dinge kommen aber aus dem Frontend:

**Honigtopf-Feld.** Ein Textfeld, das für Menschen unsichtbar ist und
von Skripten trotzdem ausgefüllt wird. Bitte per Positionierung
verstecken, **nicht** per `display:none` — manche Bots ignorieren
sichtbare Felder nicht, aber erkennen `display:none`:

```html
<div style="position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden">
  <label>Bitte frei lassen
    <input type="text" id="hp" tabindex="-1" autocomplete="off">
  </label>
</div>
```

Den Wert unverändert als `hp` mitschicken.

**Ausfüllzeit.** Merken Sie sich `Date.now()` beim Seitenaufruf und
schicken Sie die Differenz als `ms` mit. Das Backend verlangt mindestens
3 Sekunden für den Kurz-Check und 20 Sekunden für den Vollreport.

> Beim Testen: Wenn Sie sehr schnell durchklicken, weist der Server ab.
> Das ist der Schutz, kein Fehler.

**Was Sie nicht tun sollen:** kein Captcha, kein Tracking-Skript, keine
Fingerprinting-Bibliothek. Die Kombination oben reicht für den Anfang,
und Wolf will die Seite schlank halten.

---

## 8. Sprachregeln — bitte streng einhalten

Diese Regeln sind haftungsrelevant und im Backend per Test abgesichert.
Sie gelten auch für jeden Werbetext auf der Seite.

**Verboten** ist jede Zusicherung von Sicherheit oder Schutz:
„geschützt", „sicher vor", „garantiert", „100 % Schutz",
„Sicherheitsgarantie".

**Richtig** ist das Vokabular von Entscheidungsfähigkeit, Vorbereitung
und Selbstauskunft. Der Check bewertet **Angaben**, nicht **Systeme**.

Diese Einordnung gehört sichtbar auf die Seite:

> Selbstauskunft, keine Sicherheitsprüfung: Der Check bewertet Ihre
> Angaben, nicht Ihre Systeme. Er ist kein Penetrationstest und keine
> Rechtsberatung.

Die Reaktionslücke ist immer eine **geschätzte** Größe. Der offizielle
Wortlaut steht im Feld `ehrlichkeitsregel` der API-Antwort — benutzen
Sie ihn statt eigener Formulierungen.

**Zwei Wörter, die nicht vorkommen dürfen:**

- **„Resilienz"** — Wolf mag den Begriff nicht. Interne Bezeichner
  (Routen, Dateinamen) tragen ihn noch, sichtbarer Text nie.
- **„Kronjuwelen"** — im Deutschen doppeldeutig. Der Block heißt
  „Kernsysteme".

Das Produkt heißt **„Cyberangriffs-Check"**, in dieser Schreibweise.
Nicht „Cyber-Angriff-Check", nicht „Cyberangriff-Check".

---

## 9. Eine harte Regel des Projekts

**Ein Firmenname wird nirgends erhoben.** Nicht im Fragebogen, nicht im
Chat, nicht als optionales Feld. Das ist eine Sicherheitsentscheidung
von Wolf und im Backend durch CI-Tests abgesichert.

Erhoben werden: 22 Stufenwerte und eine E-Mail-Adresse. Sonst nichts.
Bauen Sie kein Feld für Firma, Name, Telefon oder Position ein — auch
nicht freiwillig, auch nicht „für die persönliche Ansprache".

---

## 10. Datenschutz

Bei der E-Mail-Eingabe brauchen Sie:

- eine **Checkbox** (nicht vorausgewählt) mit klarer Zweckangabe,
- einen **Link zur Datenschutzerklärung**,
- den Hinweis, dass zuerst eine Bestätigungsmail kommt.

Formulierungsvorschlag, im App-Frontend bereits im Einsatz:

> Ich bin damit einverstanden, dass meine Angaben zur Erstellung des
> Reports verarbeitet werden und der Report an diese Adresse geht.
> Details in der Datenschutzerklärung.

Für Werbung nach dem Report bräuchte es eine **getrennte** Einwilligung.
Bauen Sie die nicht ohne Rücksprache mit Wolf ein.

---

## 11. Textbausteine für die Startseite

Als Ausgangspunkt, gern anpassen — aber im Rahmen von Abschnitt 8.

**Überschrift:**
> Wie schnell könnte Ihr Betrieb einen Cyber-Angriff stoppen?

**Vorspann:**
> Ein automatisierter Angriff ist in rund 15 Minuten durch. Fünf Fragen
> zeigen Ihnen, wie lange Ihre Organisation bis zur ersten Entscheidung
> braucht. Keine Anmeldung, kein Firmenname.

**Button:**
> Reaktionslücke ermitteln →

**Kleingedrucktes unter dem Button:**
> Fünf Fragen, unter einer Minute. Der ausführliche PDF-Report ist
> kostenfrei und optional.

---

## 12. Was Wolf entscheiden muss — nicht selbst festlegen

1. **Bleibt der KI-Schnell-Check bestehen?** Er läuft technisch weiter
   (Backend-Route `/api/appetizer/generate`) und schickt Wolf
   Lead-Mails. Erst fragen, dann entfernen.
2. **Welche Domain liefert `cyber-check.html` aus?** Siehe Abschnitt 3.
3. **Weg A oder Weg B**, falls Weg A aus Gründen ausscheidet, die Sie im
   Repository sehen und ich nicht.
4. **Steht `CORS_ORIGINS` in Railway?** Nur relevant für Weg B.

---

## 13. Abnahmekriterien

- Die Startseite führt sichtbar zum Cyberangriffs-Check.
- Fünf Fragen, ein Ergebnis, keine Anmeldung, keine E-Mail-Pflicht für
  das Kurzergebnis.
- Das Ergebnis nennt die Reaktionslücke, den 15-Minuten-Benchmark und
  die bestimmenden Antworten.
- Der Selbstauskunfts-Hinweis steht sichtbar auf der Seite.
- Kein Feld fragt nach einem Firmennamen.
- Die Wörter „Resilienz", „Kronjuwelen", „geschützt", „sicher vor",
  „garantiert" kommen im sichtbaren Text nicht vor.
- Bei Weg B: Honigtopf und Ausfüllzeit werden mitgeschickt; 422 und 429
  werden unterschieden und freundlich angezeigt.
- Die Seite funktioniert auf dem Telefon.

---

## 14. Wenn etwas nicht funktioniert

**Alle API-Aufrufe scheitern mit einem CORS-Fehler:** Die Domain steht
nicht in den erlaubten Ursprüngen. Wolf muss `CORS_ORIGINS` in Railway
ergänzen — im Website-Repository lässt sich das nicht lösen.

**422 obwohl alles ausgefüllt ist:** Vermutlich die Ausfüllzeit. Prüfen
Sie, ob `ms` wirklich gesetzt und groß genug ist.

**Die Bestätigungsmail kommt nicht an:** Zuerst im Spam-Ordner sehen.
Kommt sie gar nicht, liegt es am Backend (Resend) — nicht an der Seite.

**Der Link in der Mail zeigt auf die falsche Domain:** Das steuert die
Backend-Variable `API_PUBLIC_URL`. Fall für Wolf.

---

## 15. Zum Nachlesen

Im Repository `api-ki-backend-neu`:

- `routes/cyber_public.py` — die öffentlichen Endpunkte
- `services/resilienz_score.py` — Min-Regel, Deckelregel, Score
- `data/resilienz/katalog_de.json` — alle Fragen und Texte
- `docs/decision-resilienz-check.md` — warum der Check so gebaut ist
- `docs/resilienz-benchmark-quellen.md` — Quelle für die 15 Minuten
- `tests/test_cyber_public.py` — das erwartete Verhalten, auch bei
  Missbrauch

Im Repository `make-ki-frontend`:

- `cyber-check.html` — die fertige Referenz-Umsetzung
