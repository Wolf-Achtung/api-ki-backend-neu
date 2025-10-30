# Lösung: Fehlende Dependencies beheben

## Problem
Die Warnung `gpt_analyze.run_async not available - analysis not queued` erscheint, weil die Python-Pakete aus `requirements.txt` nicht installiert sind.

**Auswirkung:**
- ✅ API läuft, Briefings werden gespeichert
- ❌ Keine KI-Analyse nach Briefing-Erstellung
- ❌ Keine Report-/PDF-Generierung
- ❌ Keine E-Mail-Benachrichtigungen

---

## Konkrete Lösung

### Option 1: Heroku/Render.com Deployment (EMPFOHLEN)

Wenn Sie auf Heroku oder Render.com deployen:

#### Schritt 1: Trigger einen neuen Build

```bash
# Im lokalen Repository
git commit --allow-empty -m "Trigger rebuild für dependency installation"
git push origin main
```

**Alternativ:** Im Heroku/Render.com Dashboard:
- Gehen Sie zu "Manual Deploy"
- Klicken Sie "Deploy Branch"
- Warten Sie bis der Build abgeschlossen ist

#### Schritt 2: Build-Logs prüfen

Prüfen Sie die Build-Logs auf Fehler bei der Installation:

```bash
# Heroku
heroku logs --tail --app IHR-APP-NAME

# Oder im Render.com Dashboard → Logs
```

**Achten Sie auf:**
- `Installing requirements.txt...`
- Fehlermeldungen wie `ERROR: Could not find a version...`
- Erfolgreiche Installation: `Successfully installed sqlalchemy-2.0.x fastapi-0.115.x ...`

#### Schritt 3: Wenn Build fehlschlägt

Falls Dependencies nicht installiert werden können, prüfen Sie:

1. **Python-Version kompatibel?**
   - `runtime.txt` zeigt: `python-3.11.9` ✅
   - Das sollte funktionieren

2. **requirements.txt korrekt?**
   - Ist bereits korrekt formatiert ✅
   - Alle Versionen sind spezifiziert ✅

3. **Build-Fehler beheben:**
   - Prüfen Sie Build-Logs auf spezifische Fehler
   - Eventuell müssen System-Dependencies hinzugefügt werden

---

### Option 2: Manuelles Deployment/VPS

Falls Sie auf einem eigenen Server/VPS deployen:

```bash
# 1. SSH in den Server
ssh user@ihr-server.de

# 2. Zum Projekt-Verzeichnis navigieren
cd /pfad/zu/api-ki-backend-neu

# 3. Git Pull (neueste Version)
git pull origin main

# 4. Virtual Environment aktivieren (falls vorhanden)
source venv/bin/activate

# 5. Dependencies installieren
pip install -r requirements.txt

# 6. Service neu starten
# Abhängig von Ihrem Setup:
sudo systemctl restart api-ki-backend
# ODER
pkill -f "uvicorn main:app"
uvicorn main:app --host 0.0.0.0 --port 8000 &
```

---

### Option 3: Docker (falls Sie zu Docker wechseln möchten)

Ich kann ein Dockerfile erstellen, wenn gewünscht. Docker würde sicherstellen, dass alle Dependencies korrekt installiert sind.

---

## Verification

Nach dem Fix sollten Sie folgendes sehen:

### 1. Logs prüfen

```bash
# Nach Briefing-Submit sollte erscheinen:
2025-10-30 10:21:32 [INFO] routes.briefings: Briefing created: id=17, user_id=6, email=wolf.hohl@web.de
2025-10-30 10:21:32 [INFO] routes.briefings: Async analysis queued for briefing_id=17
# ✅ KEINE WARNING mehr über "not available"

# Kurz danach:
2025-10-30 10:21:35 [INFO] gpt_analyze: [run-abc12345] analysis_created id=123 briefing_id=17
2025-10-30 10:21:50 [INFO] gpt_analyze: [run-abc12345] report_done id=456
```

### 2. Funktionalität testen

```bash
# Test-Briefing einreichen via API
curl -X POST https://IHR-APP-URL/api/briefing_async \
  -H "Content-Type: application/json" \
  -d '{
    "lang": "de",
    "email": "test@example.com",
    "answers": {
      "branche": "it",
      "hauptleistung": "Test"
    }
  }'

# Erwartete Response:
{
  "ok": true,
  "briefing_id": 18,
  "queued": true,  # ✅ sollte true sein!
  "message": "Briefing erstellt. Analyse läuft im Hintergrund."
}
```

---

## Häufige Probleme

### Problem: Build schlägt fehl mit "Could not find psycopg"

**Lösung:** System-Pakete fehlen (PostgreSQL-Dev-Headers)

**Heroku:** Fügen Sie ein `Aptfile` hinzu:
```
libpq-dev
```

**VPS:** Installieren Sie PostgreSQL-Dev:
```bash
# Ubuntu/Debian
sudo apt-get install libpq-dev python3-dev

# CentOS/RHEL
sudo yum install postgresql-devel python3-devel
```

### Problem: "No module named 'fastapi'" nach Installation

**Lösung:** Falsche Python-Umgebung aktiv

```bash
# Prüfen Sie, welches Python verwendet wird:
which python
which pip

# Stellen Sie sicher, dass Sie im venv sind:
source venv/bin/activate
pip install -r requirements.txt
```

---

## Nächste Schritte

1. **Welche Deployment-Plattform nutzen Sie?**
   - Heroku?
   - Render.com?
   - Eigener VPS?
   - Andere?

2. **Zugriff auf Logs?**
   - Können Sie Build-Logs einsehen?
   - Können Sie Runtime-Logs sehen?

→ Teilen Sie mir mit, welche Plattform Sie nutzen, dann kann ich spezifischere Anweisungen geben!
