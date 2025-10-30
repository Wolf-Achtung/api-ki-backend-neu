# Railway Deployment - Dependencies Fix

## Problem
Die Warnung `gpt_analyze.run_async not available` erscheint, weil Python-Dependencies nicht installiert sind.

---

## ✅ Lösung für Railway

### Schritt 1: Build-Logs prüfen (JETZT)

1. Gehen Sie zu: https://railway.app
2. Öffnen Sie Ihr Projekt
3. Klicken Sie auf Ihren Service (vermutlich "api-ki-backend-neu")
4. Gehen Sie zu **"Deployments"** Tab
5. Klicken Sie auf das neueste Deployment
6. Schauen Sie in die **Build Logs**

**Suchen Sie nach diesen Zeilen:**

```
✅ GUTES ZEICHEN:
#10 [python-packages] RUN pip install -r requirements.txt
#10 [python-packages] Collecting fastapi>=0.115
#10 [python-packages] Collecting SQLAlchemy>=2.0
#10 [python-packages] Successfully installed fastapi-0.115.x sqlalchemy-2.0.x ...

❌ SCHLECHTES ZEICHEN:
ERROR: Could not find a version that satisfies...
ERROR: No matching distribution found...
WARNING: pip is being invoked by an old script wrapper...
```

---

### Schritt 2: Neues Deployment triggern

#### Option A: Via Git Push (EMPFOHLEN)

```bash
# In Ihrem lokalen Repository:
git pull origin claude/analyze-log-entry-011CUdEXLBbpaZb2Kq2MdoGF

# Trigger einen Redeploy:
git commit --allow-empty -m "Railway: Trigger rebuild für dependency installation"
git push origin main
```

Railway wird automatisch ein neues Deployment starten.

#### Option B: Via Railway Dashboard

1. Gehen Sie zu Railway Dashboard
2. Wählen Sie Ihr Projekt
3. Klicken Sie auf **Settings**
4. Unter **Deployment** → Klicken Sie **"Redeploy"**

---

### Schritt 3: Build-Logs während des Builds beobachten

Während Railway neu deployed:

1. Gehen Sie zu **"Deployments"** Tab
2. Das neue Deployment sollte als "Building" angezeigt werden
3. Klicken Sie darauf
4. Beobachten Sie die Build-Logs in Echtzeit

**Achten Sie auf:**

```bash
# Phase 1: Dependencies installieren
=> [python-packages] RUN pip install -r requirements.txt
=> [python-packages] Collecting fastapi>=0.115,<0.116
=> [python-packages] Collecting SQLAlchemy>=2.0,<2.1
=> [python-packages] Collecting psycopg[binary]>=3.1.18
...
=> [python-packages] Successfully installed [LANGE LISTE VON PAKETEN]

# Phase 2: Application starten
=> Starting service with: uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

### Schritt 4: Deployment Logs prüfen (nach Build)

Nach erfolgreichem Build:

1. Gehen Sie zu **"Logs"** Tab (nicht Deployments!)
2. Sehen Sie sich die Runtime-Logs an
3. Erstellen Sie ein Test-Briefing über Ihr Frontend

**Erwartete Logs nach dem Fix:**

```
✅ VORHER (FALSCH):
[INFO] routes.briefings: Briefing created: id=17
[WARNING] routes.briefings: gpt_analyze.run_async not available

✅ NACHHER (RICHTIG):
[INFO] routes.briefings: Briefing created: id=18
[INFO] routes.briefings: Async analysis queued for briefing_id=18
[INFO] gpt_analyze: [run-abc12345] analysis_created id=123 briefing_id=18
[INFO] gpt_analyze: [run-abc12345] report_pending id=456
[INFO] gpt_analyze: [run-abc12345] pdf_render start
[INFO] gpt_analyze: [run-abc12345] report_done id=456
```

---

## 🔧 Falls der Build fehlschlägt

### Problem: "Could not find psycopg"

Railway braucht möglicherweise System-Dependencies für PostgreSQL.

**Lösung:** Nixpacks-Konfiguration hinzufügen

Erstellen Sie eine Datei `nixpacks.toml` im Root-Verzeichnis:

```toml
[phases.setup]
aptPkgs = ["postgresql-dev", "gcc", "musl-dev"]
```

Dann erneut pushen:
```bash
git add nixpacks.toml
git commit -m "Add PostgreSQL build dependencies for Railway"
git push origin main
```

---

### Problem: "Module not found" trotz erfolgreicher Installation

**Ursache:** Railway verwendet möglicherweise falsche Python-Version

**Lösung:** Prüfen Sie `runtime.txt`:

```
python-3.11.9
```

Falls das nicht hilft, setzen Sie explizit in Railway:
1. Settings → Environment → Variables
2. Fügen Sie hinzu: `PYTHON_VERSION=3.11.9`

---

### Problem: Build erfolgreich, aber WARNING erscheint weiterhin

**Ursache:** App läuft noch mit altem Container

**Lösung:** Hard Restart:

1. Railway Dashboard → Ihr Service
2. Settings → Danger Zone
3. **"Restart"** klicken
4. Warten bis Service neu startet

---

## 📊 Verification Checklist

Nach dem Redeploy:

- [ ] Build-Logs zeigen: `Successfully installed sqlalchemy-2.0.x fastapi-0.115.x`
- [ ] Runtime-Logs zeigen: Keine WARNING "not available"
- [ ] Runtime-Logs zeigen: `Async analysis queued for briefing_id=X`
- [ ] Test-Briefing erstellen über Frontend
- [ ] Prüfen ob Report-Email ankommt

---

## 🚀 Nächste Schritte - GENAU SO:

1. **JETZT:** Prüfen Sie Build-Logs vom letzten Deploy
   - Railway Dashboard → Deployments → Letztes Deployment → Build Logs
   - Screenshot machen falls unklar

2. **DANACH:** Trigger Redeploy
   ```bash
   git commit --allow-empty -m "Railway: Rebuild"
   git push origin main
   ```

3. **BEOBACHTEN:** Neue Build-Logs während des Deployments

4. **TESTEN:** Nach erfolgreichem Deploy ein Briefing erstellen

5. **MELDEN:** Was zeigen die Logs? Erfolg oder Fehler?

---

## 💡 Railway-Spezifische Tipps

- **Auto-Deploy:** Railway deployed automatisch bei jedem Push zu `main`
- **Live Logs:** Logs in Echtzeit verfügbar im Dashboard
- **Environment Variables:** Prüfen Sie ob alle ENV-Vars gesetzt sind (OPENAI_API_KEY, DATABASE_URL, etc.)
- **Health Checks:** Railway prüft automatisch ob Ihre App startet

---

## ❓ Falls Probleme auftreten

Teilen Sie mir:
1. Screenshot der Build-Logs (oder kopieren Sie relevante Zeilen)
2. Screenshot der Runtime-Logs nach dem Redeploy
3. Railway zeigt Status als "Active" oder "Failed"?

→ Dann kann ich das konkrete Problem identifizieren!
