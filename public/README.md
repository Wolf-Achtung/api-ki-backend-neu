# 🧪 Interaktives Test-Dashboard

## Schnellstart

### Option 1: Direkt im Browser öffnen

```bash
# 1. Backend starten
uvicorn main:app --reload --port 8000

# 2. Dashboard öffnen
open public/test-dashboard.html
# oder
firefox public/test-dashboard.html
```

### Option 2: Über Backend servieren

```bash
# 1. Backend starten
uvicorn main:app --reload --port 8000

# 2. Im Browser öffnen
open http://localhost:8000/test-dashboard.html
```

Fügen Sie in `main.py` hinzu:

```python
from fastapi.staticfiles import StaticFiles

# Nach app-Initialisierung:
app.mount("/", StaticFiles(directory="public", html=True), name="public")
```

### Option 3: In Frontend integrieren

```jsx
// In Next.js / React
export default function TestPage() {
  return (
    <div style={{ width: '100%', height: '100vh' }}>
      <iframe
        src="/test-dashboard.html"
        width="100%"
        height="100%"
        frameBorder="0"
      />
    </div>
  );
}
```

---

## Features

### ✅ Automatisierte Tests

Das Dashboard führt 8 wichtige Tests aus:

1. **Health Check** - Backend-Erreichbarkeit
2. **Login-Code anfordern** - Auth-Endpoint `/api/auth/request-code`
3. **Briefing einreichen** - Formular-Submit `/api/briefings/submit`
4. **Analyze Dry-Run** - LLM-Trigger ohne echte API-Calls
5. **Rate-Limiting** - Prüft HTTP 429 nach zu vielen Requests
6. **Idempotenz** - Doppelte Requests werden ignoriert
7. **XSS-Schutz** - HTML-Escaping funktioniert
8. **CORS-Konfiguration** - Header-Validierung

### 📊 Live-Statistiken

- ✅ Anzahl erfolgreicher Tests
- ❌ Anzahl fehlgeschlagener Tests
- ⏸️ Anzahl ausstehender Tests
- 📈 Fortschrittsbalken

### 📋 Echtzeit-Logs

Alle Test-Aktivitäten werden live protokolliert:
- Timestamps
- Log-Level (INFO, SUCCESS, ERROR, WARNING)
- Detaillierte Fehlermeldungen
- JSON-Response-Daten

### ⚙️ Konfigurierbar

- API-URL anpassen (z.B. für Staging/Production)
- Test-E-Mail ändern
- Tests einzeln oder alle zusammen ausführen

---

## Verwendung

### Alle Tests ausführen

1. Geben Sie die Backend-URL ein (Standard: `http://localhost:8000`)
2. Klicken Sie auf **"▶️ Alle Tests starten"**
3. Beobachten Sie die Ergebnisse in Echtzeit

### Einzelne Tests ausführen

Tests werden automatisch sequenziell ausgeführt. In der aktuellen Version gibt es keine einzelne Test-Ausführung (kann leicht erweitert werden).

### Ergebnisse interpretieren

**Grüne Karte (✅)** - Test erfolgreich
- Response wird als formatiertes JSON angezeigt
- Log-Eintrag zeigt Details

**Rote Karte (❌)** - Test fehlgeschlagen
- Fehlermeldung wird angezeigt
- Prüfen Sie die Logs für Details
- Häufige Ursachen:
  - Backend nicht erreichbar
  - Falsche API-URL
  - Validierungs-Fehler

**Gelbe Karte (⏳)** - Test läuft gerade
- Animierte Anzeige
- Warten Sie auf Ergebnis

---

## Troubleshooting

### Problem: "Failed to fetch" Fehler

**Ursache**: CORS-Probleme oder Backend nicht erreichbar

**Lösung**:
```bash
# 1. Prüfen Sie ob Backend läuft
curl http://localhost:8000/health

# 2. Prüfen Sie CORS-Konfiguration in main.py
# allow_origins sollte ["*"] oder spezifische Origins enthalten
```

### Problem: Alle Tests schlagen fehl

**Ursache**: Falsche API-URL

**Lösung**:
- Prüfen Sie die URL im Konfigurationsfeld
- Entfernen Sie trailing slash: `http://localhost:8000` (nicht `/`)
- Bei Docker: Verwenden Sie `http://host.docker.internal:8000`

### Problem: Rate-Limiting Test zeigt Warnung

**Ursache**: Rate-Limit ist zu hoch konfiguriert

**Lösung**:
- Das ist normal in Entwicklungsumgebungen
- In Production sollte das Limit niedriger sein
- Anpassen in `settings.py` oder `.env`:
  ```
  RATE_LIMIT_MAX=10
  RATE_LIMIT_WINDOW=300
  ```

### Problem: Login-Code Test schlägt fehl

**Ursache**: Email-Versand nicht konfiguriert

**Lösung**:
- Das ist normal - der Endpoint gibt HTTP 204 zurück
- Für echten Email-Versand: SMTP-Konfiguration in `.env`
- Für Tests: Mock-Mailer verwenden

---

## Erweiterungen

### Neue Tests hinzufügen

Bearbeiten Sie `test-dashboard.html` und fügen Sie im `tests`-Array hinzu:

```javascript
{
  id: 'my-custom-test',
  title: 'Mein Custom Test',
  description: 'Beschreibung des Tests',
  async run(config) {
    const res = await fetch(`${config.apiUrl}/api/my-endpoint`);
    const data = await res.json();

    if (!res.ok) {
      throw new Error('Test fehlgeschlagen');
    }

    return { success: true, data };
  }
}
```

### Einzelne Test-Buttons

Fügen Sie jedem Test einen Button hinzu:

```javascript
// In renderTests() Funktion
<button onclick="runTest(tests.find(t => t.id === '${test.id}'))">
  Test ausführen
</button>
```

### Export-Funktion

Fügen Sie einen Export-Button hinzu:

```javascript
function exportResults() {
  const results = {
    timestamp: new Date().toISOString(),
    tests: testStates,
    logs: logs
  };

  const blob = new Blob([JSON.stringify(results, null, 2)], {
    type: 'application/json'
  });

  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `test-results-${Date.now()}.json`;
  a.click();
}
```

---

## Integration in CI/CD

Das Dashboard kann auch für automatisierte Tests verwendet werden:

### Mit Puppeteer/Playwright

```javascript
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  await page.goto('http://localhost:8000/test-dashboard.html');
  await page.click('#runAllBtn');

  // Warte auf Abschluss
  await page.waitForSelector('#statPending:has-text("0")', { timeout: 60000 });

  // Lese Ergebnisse
  const success = await page.textContent('#statSuccess');
  const errors = await page.textContent('#statError');

  console.log(`Tests: ${success} erfolg, ${errors} fehler`);

  if (errors !== '0') {
    process.exit(1); // CI-Fail
  }

  await browser.close();
})();
```

---

## Best Practices

1. **Regelmäßig testen**: Führen Sie Tests nach jeder größeren Änderung aus
2. **Vor Deployment**: Immer alle Tests grün vor Production-Deploy
3. **Staging testen**: Verwenden Sie das Dashboard auch gegen Staging-Umgebung
4. **Logs speichern**: Exportieren Sie Logs bei Fehlern für Debugging
5. **Browser-DevTools**: Öffnen Sie Network-Tab für detaillierte Request-Analyse

---

## Screenshots

### Alle Tests erfolgreich
```
Stats: 8 Erfolgreich | 0 Fehlgeschlagen | 0 Ausstehend
Fortschritt: 100%
```

### Einzelner Test
```
✅ Briefing einreichen
Status: Erfolg
Response: {
  "status": "queued",
  "lang": "de"
}
```

### Live-Logs
```
[14:23:45] [INFO] Dashboard initialisiert
[14:23:50] [INFO] Starte Test: Health Check
[14:23:51] [SUCCESS] ✅ Health Check erfolgreich
[14:23:52] [INFO] Starte Test: Login-Code anfordern
...
```

---

## Support

Bei Problemen:
1. Öffnen Sie Browser-DevTools (F12)
2. Prüfen Sie Console auf JavaScript-Fehler
3. Prüfen Sie Network-Tab für fehlgeschlagene Requests
4. Exportieren Sie Logs und senden Sie an Support

## Lizenz

Teil des KI-Backend-Projekts. Siehe Haupt-README für Details.
