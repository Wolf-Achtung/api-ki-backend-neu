# Phase 2 Quick-Start Checkliste

## ⚡ Schnellstart für Entwickler

Diese Checkliste führt Sie durch die wichtigsten Schritte der Frontend-Migration.

---

## 🔍 Schritt 1: Analyse (10-15 Min)

### A. Finden Sie alle relevanten Dateien:

```bash
# Im Frontend-Repository ausführen:

# 1. localStorage Token-Zugriffe finden
grep -rn "localStorage.*token" src/ --include="*.js" --include="*.ts" --include="*.jsx" --include="*.tsx"

# 2. Authorization Header finden
grep -rn "Authorization.*Bearer" src/ --include="*.js" --include="*.ts" --include="*.jsx" --include="*.tsx"

# 3. Auth-Services/Hooks finden
find src/ -name "*auth*" -o -name "*login*"
```

### B. Notieren Sie die gefundenen Dateien:

- [ ] Auth-Service/Hook: `_________________`
- [ ] API-Client: `_________________`
- [ ] Login-Komponente: `_________________`
- [ ] Protected Route: `_________________`
- [ ] Logout-Funktion: `_________________`

---

## ✏️ Schritt 2: Code-Änderungen (30-60 Min)

### 1. API-Client anpassen

**Datei:** (Ihr API-Client, z.B. `src/api/client.js`)

**Änderung:**
```diff
+ // Für fetch:
+ credentials: 'include'

+ // Für axios:
+ withCredentials: true

- // ENTFERNEN: Authorization Header Interceptor
- axios.interceptors.request.use(config => {
-   const token = localStorage.getItem('auth_token');
-   if (token) config.headers.Authorization = `Bearer ${token}`;
-   return config;
- });
```

---

### 2. Login-Funktion anpassen

**Datei:** (Ihr Auth-Service, z.B. `src/services/auth.js` oder `src/hooks/useAuth.js`)

**Änderung:**
```diff
  async function login(email, code) {
    const response = await fetch(`${API_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
+     credentials: 'include', // ✅ HINZUFÜGEN
      body: JSON.stringify({ email, code }),
    });

    const data = await response.json();
-   localStorage.setItem('auth_token', data.access_token); // ❌ ENTFERNEN
    return data;
  }
```

---

### 3. Auth-Status-Prüfung implementieren

**Datei:** (Ihr Auth-Service/Hook)

**NEU hinzufügen:**
```javascript
async function checkAuthStatus() {
  try {
    const response = await fetch(`${API_URL}/api/auth/me`, {
      credentials: 'include',
    });

    if (response.ok) {
      const userData = await response.json();
      return { isAuthenticated: true, user: userData };
    }
    return { isAuthenticated: false, user: null };
  } catch (error) {
    console.error('Auth check failed:', error);
    return { isAuthenticated: false, user: null };
  }
}
```

---

### 4. Logout-Funktion anpassen

**Datei:** (Ihr Auth-Service/Hook)

**Änderung:**
```diff
  async function logout() {
+   // ✅ Backend-Endpoint aufrufen
+   await fetch(`${API_URL}/api/auth/logout`, {
+     method: 'POST',
+     credentials: 'include',
+   });

-   localStorage.removeItem('auth_token'); // ❌ ENTFERNEN
    window.location.href = '/login';
  }
```

---

### 5. Protected Routes anpassen

**Datei:** (Ihre Route-Guard-Komponente)

**Änderung:**
```diff
  function ProtectedRoute({ children }) {
-   const token = localStorage.getItem('auth_token'); // ❌ ENTFERNEN
-   if (!token) return <Navigate to="/login" />;

+   const { isAuthenticated, isLoading } = useAuth(); // ✅ Hook nutzen
+   if (isLoading) return <div>Loading...</div>;
+   if (!isAuthenticated) return <Navigate to="/login" />;

    return children;
  }
```

---

## 🧪 Schritt 3: Testing (15-30 Min)

### Manuelle Tests:

- [ ] **Login-Flow:**
  - [ ] Login-Formular ausfüllen und absenden
  - [ ] Prüfen: Cookie `auth_token` in DevTools (Application → Cookies)
  - [ ] Prüfen: Set-Cookie Header in Network Tab
  - [ ] Prüfen: Redirect zum Dashboard funktioniert

- [ ] **API-Requests:**
  - [ ] Geschützte Seite öffnen (z.B. Dashboard)
  - [ ] Prüfen: API-Requests enthalten Cookie (Network Tab → Request Headers)
  - [ ] Prüfen: Keine 401-Fehler
  - [ ] Prüfen: Daten werden korrekt geladen

- [ ] **Logout-Flow:**
  - [ ] Logout-Button klicken
  - [ ] Prüfen: Cookie wird gelöscht (Application → Cookies)
  - [ ] Prüfen: Redirect zur Login-Seite
  - [ ] Prüfen: Geschützte Seiten nicht mehr zugänglich

### Browser DevTools Checks:

**Chrome/Firefox DevTools:**

1. **Application Tab → Cookies:**
   ```
   ✅ Name: auth_token
   ✅ HttpOnly: ✓
   ✅ Secure: ✓
   ✅ SameSite: Lax
   ```

2. **Network Tab:**
   - Login-Request Response Headers:
     ```
     ✅ Set-Cookie: auth_token=eyJ...
     ```
   - API-Request Headers:
     ```
     ✅ Cookie: auth_token=eyJ...
     ❌ NICHT: Authorization: Bearer ...
     ```

3. **Console:**
   ```
   ❌ Keine CORS-Fehler
   ❌ Keine localStorage warnings
   ```

---

## 🚀 Schritt 4: Deployment

### Development:

```bash
# .env.development
VITE_API_URL=http://localhost:8080
# oder
REACT_APP_API_URL=http://localhost:8080
```

### Production:

```bash
# .env.production
VITE_API_URL=https://api.ki-sicherheit.jetzt
# oder
REACT_APP_API_URL=https://api.ki-sicherheit.jetzt
```

### Deploy-Checkliste:

- [ ] Umgebungsvariablen aktualisiert
- [ ] Build erfolgreich
- [ ] Smoke-Tests nach Deployment
- [ ] CORS-Konfiguration im Backend prüfen

---

## 🐛 Häufige Probleme

### Problem: "Cookie wird nicht gesetzt"

**Lösung:**
```javascript
// Prüfen Sie ALLE fetch/axios Calls:
fetch(url, {
  credentials: 'include' // ✅ Muss gesetzt sein!
})
```

### Problem: "401 Unauthorized"

**Ursachen:**
1. `credentials: 'include'` fehlt
2. Cookie ist abgelaufen
3. CORS-Konfiguration falsch

**Prüfen:**
```javascript
// Browser Console:
document.cookie // Sollte auth_token enthalten
```

### Problem: "CORS Error"

**Backend prüfen:**
```python
# main.py - CORS-Konfiguration
CORSMiddleware(
    allow_origins=["https://make.ki-sicherheit.jetzt"],  # ✅ Korrekte Origin
    allow_credentials=True,  # ✅ Muss True sein
)
```

---

## 📊 Erfolgs-Kriterien

Nach erfolgreicher Migration sollten Sie:

- ✅ **KEINE** `localStorage.getItem('auth_token')` Aufrufe mehr haben
- ✅ **KEINE** manuellen `Authorization: Bearer` Header mehr setzen
- ✅ `credentials: 'include'` bei ALLEN API-Requests haben
- ✅ Login/Logout funktionieren einwandfrei
- ✅ Cookies in Browser DevTools sichtbar sein

---

## 📚 Weitere Ressourcen

- **Vollständige Dokumentation:** `FRONTEND_MIGRATION_PHASE2.md`
- **Backend-Code:** `routes/auth.py`, `core/security.py`
- **API-Dokumentation:** `/docs` auf Ihrem Backend

---

## ⏱️ Geschätzte Zeit

- **Analyse:** 10-15 Min
- **Code-Änderungen:** 30-60 Min
- **Testing:** 15-30 Min
- **Deployment:** 10-20 Min

**Gesamt:** ~1-2 Stunden (abhängig von der Komplexität Ihres Frontends)

---

## ✅ Abschluss-Checkliste

Nach Abschluss der Migration:

- [ ] Alle localStorage Token-Zugriffe entfernt
- [ ] credentials: 'include' überall gesetzt
- [ ] Login funktioniert mit Cookie
- [ ] API-Requests verwenden Cookie
- [ ] Logout löscht Cookie
- [ ] Protected Routes funktionieren
- [ ] Tests in Development erfolgreich
- [ ] Tests in Production erfolgreich
- [ ] Team informiert über Änderungen
- [ ] Dokumentation aktualisiert

**🎉 Glückwunsch! Phase 2 abgeschlossen!**
