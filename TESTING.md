# 🧪 Test-Strategie: Frontend ↔ Backend ↔ Report-Generierung

Umfassende Test-Anleitung für das KI-Status-Report-System.

## 📋 Inhaltsverzeichnis

1. [Schnellstart](#schnellstart)
2. [Test-Ebenen](#test-ebenen)
3. [Lokale Entwicklung](#lokale-entwicklung)
4. [CI/CD Integration](#cicd-integration)
5. [Troubleshooting](#troubleshooting)

---

## 🚀 Schnellstart

```bash
# 1. Test-Dependencies installieren
pip install -r requirements-test.txt

# 2. Unit-Tests ausführen
pytest tests/ -v

# 3. Mit Coverage
pytest --cov=. --cov-report=html tests/

# 4. Manueller Workflow-Test
chmod +x scripts/test_workflow.sh
./scripts/test_workflow.sh

# 5. E2E-Tests (benötigt laufendes Frontend)
pytest tests/test_e2e_playwright.py -m e2e
```

---

## 🎯 Test-Ebenen

### Level 1: Unit-Tests ⚡ (Schnell)

**Zweck**: Einzelne Funktionen und Module isoliert testen

**Beispiele**:
```python
# Test: Template-Engine
from services.template_engine import render_template

def test_xss_protection():
    result = render_template(
        "Hello {{name}}",
        {"name": "<script>alert('xss')</script>"},
        escape_html=True
    )
    assert "&lt;script&gt;" in result
    assert "<script>" not in result

# Test: URL-Sanitizer
from gpt_analyze import _sanitize_url

def test_ssrf_protection():
    # Localhost sollte blockiert werden
    assert _sanitize_url("http://localhost/api") is None
    assert _sanitize_url("http://169.254.169.254/metadata") is None

    # Valide URLs sollten durchgehen
    assert _sanitize_url("https://example.com") is not None
```

**Ausführung**:
```bash
pytest tests/test_unit_*.py -v
```

---

### Level 2: Integration-Tests 🔗 (Mittel)

**Zweck**: API-Endpoints und Zusammenspiel mehrerer Komponenten testen

**Test-Szenarien**:

#### ✅ Szenario 1: Kompletter Briefing-Workflow

```bash
# 1. Backend starten
uvicorn main:app --reload --port 8000

# 2. Integration-Tests ausführen
pytest tests/test_report_workflow.py::TestReportWorkflow -v
```

**Was wird getestet**:
- ✓ Briefing-Submission mit Validierung
- ✓ Idempotenz (doppelte Requests werden ignoriert)
- ✓ Rate-Limiting funktioniert
- ✓ Auth-Flow (Code-Request → Login → Token)
- ✓ Analyze-Trigger ohne echtes LLM (Dry-Run)

#### ✅ Szenario 2: Report-Generierung mit Mock

```python
@patch("gpt_analyze._call_openai")
def test_report_with_mocked_llm(mock_openai):
    # Mock LLM-Antwort
    mock_openai.return_value = '{"executive_summary": "Test"}'

    # Trigger Analyse
    result = analyze_briefing(db, briefing_id=1, run_id="test")

    # Validiere Ergebnis
    assert result["executive_summary"] == "Test"
```

**Ausführung**:
```bash
pytest tests/test_report_workflow.py::TestReportGeneration -v
```

---

### Level 3: End-to-End Tests 🌐 (Langsam)

**Zweck**: Kompletter Workflow mit echtem Frontend testen

**Voraussetzungen**:
```bash
# Frontend starten (z.B. Next.js)
cd ../frontend
npm run dev

# Backend starten
cd ../backend
uvicorn main:app --reload
```

**E2E-Test ausführen**:
```bash
# Mit Playwright
pytest tests/test_e2e_playwright.py -v -s

# Nur bestimmte Tests
pytest tests/test_e2e_playwright.py::TestE2EReportGeneration::test_complete_workflow -v
```

**Was wird getestet**:
- ✓ Formular-Ausfüllung im Browser
- ✓ API-Calls während Frontend-Interaktion
- ✓ Erfolgs-/Fehler-Meldungen
- ✓ Report-Download
- ✓ Network-Traffic-Monitoring

---

## 🛠️ Lokale Entwicklung

### Manuelles Testen mit cURL

**1. Health Check**
```bash
curl http://localhost:8000/health
# Erwartung: {"status":"ok"}
```

**2. Login-Code anfordern**
```bash
curl -X POST http://localhost:8000/api/auth/request-code \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{"email": "test@example.com"}'
# Erwartung: HTTP 204
```

**3. Briefing einreichen**
```bash
curl -X POST http://localhost:8000/api/briefings/submit \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "lang": "de",
    "branche": "IT",
    "bundesland": "Bayern",
    "jahresumsatz": "1-5M",
    "unternehmensgroesse": "10-50",
    "ki_kompetenz": "Anfänger",
    "hauptleistung": "Software-Entwicklung",
    "antworten": []
  }'
# Erwartung: {"status":"queued","lang":"de"}
```

**4. Analyze Dry-Run (ohne echtes LLM)**
```bash
curl -X POST http://localhost:8000/api/analyze/run \
  -H "Content-Type: application/json" \
  -H "x-dry-run: true" \
  -d '{"briefing_id": 1}'
# Erwartung: {"accepted":true,"dry_run":true,"analyzer_import_ok":true}
```

---

### Automatisches Test-Script

```bash
# Macht den Test-Script ausführbar
chmod +x scripts/test_workflow.sh

# Führt alle 6 Workflow-Tests aus
./scripts/test_workflow.sh

# Mit custom API-URL
API_BASE_URL=http://localhost:8080 ./scripts/test_workflow.sh
```

**Output-Beispiel**:
```
🧪 KI-Backend Workflow-Test
================================
[1/6] Health Check...
✓ Backend läuft

[2/6] Login-Code anfordern...
✓ Login-Code angefordert für: test-1699999999@example.com

[3/6] Briefing einreichen...
✓ Briefing erfolgreich eingereicht

[4/6] Analyze Dry-Run...
✓ Analyzer-Import erfolgreich

[5/6] Rate-Limiting testen...
✓ Rate-Limit funktioniert (Request #11 blockiert)

[6/6] Template XSS-Schutz testen...
✓ XSS-Schutz aktiv (HTML wird escaped)

✅ Workflow-Tests abgeschlossen
```

---

## 🔄 CI/CD Integration

### GitHub Actions Workflow

Erstelle `.github/workflows/test.yml`:

```yaml
name: Test Backend

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt

    - name: Run Unit Tests
      run: pytest tests/ -v --tb=short -m "not slow and not e2e"

    - name: Run Integration Tests (Dry-Run)
      env:
        DATABASE_URL: sqlite:///:memory:
        JWT_SECRET: test-secret-key
        OPENAI_API_KEY: sk-test-mock
      run: |
        # Backend im Hintergrund starten
        uvicorn main:app --host 0.0.0.0 --port 8000 &
        sleep 5

        # Workflow-Test ausführen
        ./scripts/test_workflow.sh

    - name: Coverage Report
      run: |
        pytest --cov=. --cov-report=xml --cov-report=html tests/

    - name: Upload Coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

---

## 🐛 Troubleshooting

### Problem: Tests schlagen fehl mit "Database connection error"

**Lösung**:
```bash
# Setze In-Memory-Datenbank für Tests
export DATABASE_URL="sqlite:///:memory:"
pytest tests/
```

### Problem: "OpenAI API Key not found"

**Lösung 1 - Dry-Run verwenden**:
```bash
# Tests ohne echtes LLM
pytest tests/ -k "not slow"
```

**Lösung 2 - Mock-Key setzen**:
```bash
export OPENAI_API_KEY="sk-test-mock-key"
pytest tests/
```

### Problem: Rate-Limiting schlägt in Tests fehl

**Lösung**:
```bash
# Rate-Limits für Tests erhöhen
export RATE_LIMIT_MAX=1000
export RATE_LIMIT_WINDOW=3600
pytest tests/
```

### Problem: E2E-Tests finden Frontend nicht

**Lösung**:
```bash
# 1. Frontend starten
cd ../frontend && npm run dev &

# 2. Warte auf Start
sleep 10

# 3. Tests mit korrekter URL
FRONTEND_URL=http://localhost:3000 pytest tests/test_e2e_playwright.py
```

---

## 📊 Test-Coverage Ziele

| Komponente | Ziel-Coverage | Aktuell |
|------------|---------------|---------|
| routes/* | 80% | - |
| services/* | 85% | - |
| gpt_analyze.py | 70% | - |
| utils/* | 90% | - |

**Coverage prüfen**:
```bash
pytest --cov=. --cov-report=term-missing tests/
```

**HTML-Report generieren**:
```bash
pytest --cov=. --cov-report=html tests/
open htmlcov/index.html
```

---

## 🎯 Best Practices

### 1. **Immer mit Dry-Run starten**

Teste erst ohne echtes LLM, dann mit Mock, dann (optional) mit echtem API:

```python
# Level 1: Dry-Run
@pytest.mark.fast
def test_analyzer_import():
    # Nur Import-Test, kein LLM-Call

# Level 2: Mit Mock
@patch("gpt_analyze._call_openai")
def test_with_mock(mock_llm):
    # Gemockte LLM-Antwort

# Level 3: Echtes LLM (slow)
@pytest.mark.slow
def test_with_real_llm():
    # Nur in Staging/Pre-Prod
    pytest.skip("Nur manuell ausführen")
```

### 2. **Idempotenz-Keys verwenden**

```python
headers = {
    "Idempotency-Key": f"test-{uuid.uuid4()}"
}
```

### 3. **Timeouts setzen**

```python
# Für lange API-Calls
response = client.post("/analyze/run", timeout=60)
```

### 4. **Cleanup nach Tests**

```python
@pytest.fixture(autouse=True)
def cleanup():
    yield
    # Räume Testdaten auf
    db.query(Briefing).filter(Briefing.id.like("test-%")).delete()
```

---

## 📞 Support

Bei Problemen:
1. Prüfe Logs: `tail -f logs/app.log`
2. Erhöhe Verbosity: `pytest -vvv tests/`
3. Debug einzelnen Test: `pytest tests/test_file.py::test_name -vvs --pdb`

**Hilfreiche Kommandos**:
```bash
# Nur fehlgeschlagene Tests
pytest --lf

# Stoppe bei erstem Fehler
pytest -x

# Zeige lokale Variablen bei Fehler
pytest -l

# Detaillierter Traceback
pytest --tb=long
```
