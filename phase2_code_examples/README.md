# Phase 2 Code-Beispiele

Dieses Verzeichnis enthält Copy-Paste-fähige Code-Beispiele für die Frontend-Migration zu httpOnly Cookies.

## 📁 Enthaltene Dateien

### 1. `01_fetch_api_client.js`
Einfacher API-Client mit der nativen Fetch API.

**Verwendung:**
- Vanilla JavaScript
- React ohne zusätzliche Libraries
- Next.js

**Key Features:**
- ✅ `credentials: 'include'` für Cookie-Support
- ✅ Helper-Funktionen für GET, POST, DELETE
- ✅ Automatische JSON-Verarbeitung

---

### 2. `02_axios_api_client.js`
API-Client mit Axios Library.

**Verwendung:**
- React mit Axios
- Vue.js mit Axios
- Jedes Framework mit Axios

**Key Features:**
- ✅ `withCredentials: true` für Cookie-Support
- ✅ Response Interceptor für Auto-Logout bei 401
- ✅ Vorkonfigurierte Axios-Instanz

---

### 3. `03_react_useAuth_hook.jsx`
Vollständiger React Auth Hook mit Context API.

**Verwendung:**
- React 16.8+
- React mit Hooks

**Key Features:**
- ✅ AuthProvider Component
- ✅ useAuth Hook
- ✅ Login, Logout, checkAuthStatus Funktionen
- ✅ User-State-Management
- ✅ Loading-State-Handling

---

### 4. `04_react_protected_route.jsx`
Protected Route Component für React Router v6.

**Verwendung:**
- React mit React Router v6

**Key Features:**
- ✅ Automatische Weiterleitung zur Login-Seite
- ✅ Loading-State während Auth-Check
- ✅ Optional: Redirect-URL nach Login speichern

---

### 5. `05_vue_composable_useAuth.js`
Vue 3 Composable für Authentifizierung.

**Verwendung:**
- Vue 3 mit Composition API

**Key Features:**
- ✅ Reactive State (ref, computed)
- ✅ Login, Logout, checkAuthStatus Funktionen
- ✅ Vue Router Navigation Guard Beispiel
- ✅ Shared State über Komponenten hinweg

---

## 🚀 Schnellstart

### Schritt 1: Datei kopieren
Kopieren Sie die passende Datei in Ihr Projekt:

```bash
# React Projekt
cp phase2_code_examples/03_react_useAuth_hook.jsx src/hooks/useAuth.jsx

# Vue Projekt
cp phase2_code_examples/05_vue_composable_useAuth.js src/composables/useAuth.js

# API Client
cp phase2_code_examples/01_fetch_api_client.js src/api/client.js
```

### Schritt 2: Anpassen
Passen Sie die API-URL an Ihre Umgebung an:

```javascript
// React
const API_URL = process.env.REACT_APP_API_URL;

// Vue/Vite
const API_URL = import.meta.env.VITE_API_URL;

// Next.js
const API_URL = process.env.NEXT_PUBLIC_API_URL;
```

### Schritt 3: Integrieren
Integrieren Sie den Code in Ihre App (siehe Verwendungsbeispiele in den Dateien).

---

## 📋 Wichtige Änderungen gegenüber localStorage

### ❌ VORHER (localStorage):
```javascript
// Token in localStorage speichern
localStorage.setItem('auth_token', token);

// Token aus localStorage lesen
const token = localStorage.getItem('auth_token');

// Authorization Header manuell setzen
headers: {
  'Authorization': `Bearer ${token}`
}
```

### ✅ NACHHER (httpOnly Cookies):
```javascript
// KEIN localStorage mehr - Cookie wird automatisch gesetzt

// KEINE Token-Verwaltung im Frontend

// credentials: 'include' bei fetch
fetch(url, { credentials: 'include' })

// withCredentials: true bei axios
axios.create({ withCredentials: true })
```

---

## 🧪 Testing

Alle Beispiele sollten folgende Funktionalität unterstützen:

1. **Login:**
   - Cookie wird vom Backend gesetzt
   - User-State wird aktualisiert
   - Redirect zum Dashboard

2. **API-Requests:**
   - Cookie wird automatisch gesendet
   - Keine manuellen Authorization Header

3. **Auth-Check:**
   - `/api/auth/me` wird bei App-Start aufgerufen
   - User-State wird basierend auf Cookie-Validität gesetzt

4. **Logout:**
   - `/api/auth/logout` wird aufgerufen
   - Cookie wird gelöscht
   - User-State wird zurückgesetzt

---

## 🔧 Anpassung an Ihr Projekt

Diese Beispiele sind als Startpunkt gedacht. Sie müssen möglicherweise angepasst werden:

- **Error Handling:** Erweitern Sie die Error-Handling-Logik
- **Loading States:** Fügen Sie eigene Loading-Komponenten hinzu
- **Routing:** Passen Sie Redirect-Logik an Ihre Router-Konfiguration an
- **State Management:** Integrieren Sie mit Redux, Pinia, etc. falls gewünscht

---

## 📚 Weitere Ressourcen

- **Vollständige Dokumentation:** `../FRONTEND_MIGRATION_PHASE2.md`
- **Quick-Start Guide:** `../PHASE2_QUICK_START.md`
- **Backend-Änderungen:** `../routes/auth.py`, `../core/security.py`

---

## 💡 Tipps

1. **Starten Sie klein:** Implementieren Sie erst Login, dann API-Client, dann den Rest
2. **Testen Sie lokal:** Nutzen Sie Browser DevTools um Cookies zu inspizieren
3. **CORS beachten:** `credentials: 'include'` funktioniert nur mit korrekter CORS-Konfiguration
4. **HTTPS in Production:** Secure-Flag erfordert HTTPS (außer localhost)

---

## ✅ Checkliste nach Implementierung

Nach Integration dieser Beispiele:

- [ ] Login funktioniert und setzt Cookie
- [ ] API-Requests senden Cookie automatisch
- [ ] Logout löscht Cookie
- [ ] Protected Routes funktionieren
- [ ] Keine localStorage-Zugriffe für Tokens mehr
- [ ] Keine manuellen Authorization Header mehr

**Viel Erfolg bei der Migration!** 🚀
