# Phase 2: Frontend-Migration zu httpOnly Cookies

## Übersicht

Dieses Dokument beschreibt die notwendigen Änderungen im Frontend, um von localStorage JWT-Tokens auf httpOnly Cookie-basierte Authentifizierung umzustellen.

**Status:** Phase 1 (Backend Hybrid-Modus) ist abgeschlossen ✅
**Ziel:** Frontend nutzt sichere httpOnly Cookies statt localStorage

---

## Warum diese Migration?

### Sicherheitsprobleme mit localStorage:
- ❌ **XSS-Anfällig:** Jedes JavaScript kann auf localStorage zugreifen
- ❌ **Token-Diebstahl:** Angreifer können Tokens bei XSS-Angriffen auslesen
- ❌ **Keine HTTP-Only Option:** Schutz vor JavaScript-Zugriff nicht möglich

### Vorteile von httpOnly Cookies:
- ✅ **XSS-Schutz:** JavaScript hat keinen Zugriff auf httpOnly Cookies
- ✅ **Automatisch:** Browser sendet Cookies automatisch mit jeder Anfrage
- ✅ **Secure Flag:** Nur über HTTPS übertragen
- ✅ **SameSite Protection:** CSRF-Schutz eingebaut

---

## Migration-Checkliste

### 🔍 Schritt 1: Frontend-Code analysieren
Finden Sie alle Stellen, die auf Authentifizierung zugreifen:

```bash
# Suchen Sie nach localStorage-Zugriffen
grep -r "localStorage.getItem.*token" src/
grep -r "localStorage.setItem.*token" src/
grep -r "localStorage.removeItem.*token" src/

# Suchen Sie nach Authorization Header Konstruktion
grep -r "Authorization.*Bearer" src/
grep -r "headers.*authorization" src/
```

### 📝 Schritt 2: Typische Code-Stellen identifizieren

Die folgenden Code-Bereiche müssen normalerweise angepasst werden:

1. **Login-Flow** (Token-Speicherung)
2. **API-Client-Konfiguration** (Header-Konstruktion)
3. **Auth-Context/Store** (Token-Verwaltung)
4. **Protected Routes** (Authentifizierungs-Prüfung)
5. **Logout-Flow** (Token-Löschung)

---

## Detaillierte Änderungen

### 1. Login-Flow anpassen

#### ❌ **VORHER** (localStorage):
```javascript
// Login-Funktion (z.B. in auth.js, authService.js oder useAuth.js)
async function login(email, code) {
  const response = await fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, code }),
  });

  const data = await response.json();

  // ❌ ENTFERNEN: Token in localStorage speichern
  localStorage.setItem('auth_token', data.access_token);
  localStorage.setItem('user_email', email);

  return data;
}
```

#### ✅ **NACHHER** (Cookie-basiert):
```javascript
// Login-Funktion - Cookie wird automatisch vom Backend gesetzt
async function login(email, code) {
  const response = await fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include', // ✅ NEU: Wichtig für Cookies!
    body: JSON.stringify({ email, code }),
  });

  const data = await response.json();

  // ✅ KEIN localStorage mehr - Cookie wird automatisch gesetzt
  // Optional: User-Email trotzdem speichern (keine sensiblen Daten)
  localStorage.setItem('user_email', email);

  return data;
}
```

**Wichtige Änderungen:**
- ✅ `credentials: 'include'` hinzufügen (ermöglicht Cookie-Übertragung)
- ❌ `localStorage.setItem('auth_token', ...)` entfernen
- ✅ Cookie wird automatisch vom Backend gesetzt

---

### 2. API-Client konfigurieren

#### ❌ **VORHER** (manueller Authorization Header):
```javascript
// API Client (z.B. api.js, apiClient.js, oder axios-Konfiguration)
async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem('auth_token'); // ❌ ENTFERNEN

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // ❌ ENTFERNEN: Manueller Authorization Header
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  return response;
}
```

#### ✅ **NACHHER** (automatische Cookies):
```javascript
// API Client - vereinfacht, da Cookies automatisch gesendet werden
async function apiRequest(endpoint, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include', // ✅ NEU: Cookies automatisch senden
  });

  return response;
}
```

**Für Axios-Nutzer:**
```javascript
// axios-Konfiguration (z.B. in api/client.js)
import axios from 'axios';

const apiClient = axios.create({
  baseURL: API_URL,
  withCredentials: true, // ✅ NEU: Entspricht credentials: 'include' bei fetch
  headers: {
    'Content-Type': 'application/json',
  },
});

// ❌ ENTFERNEN: Request Interceptor für Authorization Header
// apiClient.interceptors.request.use((config) => {
//   const token = localStorage.getItem('auth_token');
//   if (token) {
//     config.headers.Authorization = `Bearer ${token}`;
//   }
//   return config;
// });

export default apiClient;
```

---

### 3. Authentifizierungs-Status prüfen

#### ✅ **NEU:** `/api/auth/me` Endpoint nutzen

Statt den Token aus localStorage zu lesen, nutzen Sie den neuen `/api/auth/me` Endpoint:

```javascript
// Auth-Status prüfen (z.B. in useAuth.js, authContext.js)
async function checkAuthStatus() {
  try {
    const response = await fetch(`${API_URL}/api/auth/me`, {
      credentials: 'include', // ✅ Cookie wird automatisch gesendet
    });

    if (response.ok) {
      const userData = await response.json();
      // userData enthält: { email, sub, exp, iat }
      return {
        isAuthenticated: true,
        user: userData,
      };
    } else if (response.status === 401) {
      return {
        isAuthenticated: false,
        user: null,
      };
    }
  } catch (error) {
    console.error('Auth check failed:', error);
    return {
      isAuthenticated: false,
      user: null,
    };
  }
}
```

#### **React Context Beispiel:**
```javascript
// AuthContext.js oder useAuth.js
import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Bei App-Start: Auth-Status prüfen
  useEffect(() => {
    checkAuthStatus();
  }, []);

  async function checkAuthStatus() {
    try {
      const response = await fetch(`${API_URL}/api/auth/me`, {
        credentials: 'include',
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        setIsAuthenticated(true);
      } else {
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  }

  async function login(email, code) {
    const response = await fetch(`${API_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, code }),
    });

    if (response.ok) {
      // Nach erfolgreichem Login: Auth-Status neu laden
      await checkAuthStatus();
      return true;
    }
    return false;
  }

  async function logout() {
    await fetch(`${API_URL}/api/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    });

    setUser(null);
    setIsAuthenticated(false);
  }

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated,
      isLoading,
      login,
      logout,
      checkAuthStatus
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
```

---

### 4. Logout-Flow anpassen

#### ❌ **VORHER** (localStorage löschen):
```javascript
function logout() {
  // ❌ ENTFERNEN: localStorage-Zugriff
  localStorage.removeItem('auth_token');
  localStorage.removeItem('user_email');

  // Redirect zur Login-Seite
  window.location.href = '/login';
}
```

#### ✅ **NACHHER** (Backend-Endpoint aufrufen):
```javascript
async function logout() {
  try {
    // ✅ NEU: Backend-Endpoint aufrufen zum Cookie löschen
    await fetch(`${API_URL}/api/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    });
  } catch (error) {
    console.error('Logout failed:', error);
  } finally {
    // Optional: localStorage aufräumen (nur nicht-sensitive Daten)
    localStorage.removeItem('user_email');

    // Redirect zur Login-Seite
    window.location.href = '/login';
  }
}
```

---

### 5. Protected Routes / Route Guards

#### ✅ **NEU:** Auth-Prüfung ohne localStorage

```javascript
// ProtectedRoute.jsx (React Router v6 Beispiel)
import { Navigate } from 'react-router-dom';
import { useAuth } from './useAuth';

export function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>; // Oder Spinner-Komponente
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}
```

**Verwendung:**
```javascript
// App.jsx oder Router-Konfiguration
<Route
  path="/dashboard"
  element={
    <ProtectedRoute>
      <Dashboard />
    </ProtectedRoute>
  }
/>
```

---

### 6. Token-Expiry Validierung

Da der Token jetzt im httpOnly Cookie ist und nicht mehr ausgelesen werden kann, nutzen Sie den `/api/auth/me` Endpoint:

```javascript
// Token-Expiry prüfen
async function validateTokenExpiry() {
  try {
    const response = await fetch(`${API_URL}/api/auth/me`, {
      credentials: 'include',
    });

    if (response.ok) {
      const data = await response.json();
      const expiresAt = data.exp * 1000; // Unix timestamp zu Millisekunden
      const now = Date.now();

      if (expiresAt < now) {
        console.warn('Token expired');
        await logout();
        return false;
      }

      return true;
    } else {
      // Token ungültig oder abgelaufen
      await logout();
      return false;
    }
  } catch (error) {
    console.error('Token validation failed:', error);
    return false;
  }
}

// Optional: Periodische Prüfung (z.B. alle 5 Minuten)
setInterval(validateTokenExpiry, 5 * 60 * 1000);
```

---

## Fetch vs. Axios

### **Fetch API:**
```javascript
fetch(url, {
  credentials: 'include', // ✅ Cookies senden/empfangen
})
```

### **Axios:**
```javascript
axios.create({
  withCredentials: true, // ✅ Cookies senden/empfangen
})
```

Beide sind gleichwertig - wählen Sie basierend auf Ihrer bisherigen Implementierung.

---

## CORS-Konfiguration prüfen

### Backend (bereits erledigt ✅):
```python
# main.py - CORS mit credentials
CORSMiddleware(
    allow_origins=allowed_origins,
    allow_credentials=True,  # ✅ Bereits konfiguriert
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Frontend-Umgebungsvariablen:
Stellen Sie sicher, dass die API-URL korrekt konfiguriert ist:

```bash
# .env oder .env.local
VITE_API_URL=https://api.ki-sicherheit.jetzt
# oder
REACT_APP_API_URL=https://api.ki-sicherheit.jetzt
# oder
NEXT_PUBLIC_API_URL=https://api.ki-sicherheit.jetzt
```

**Wichtig:** Cookie-basierte Auth funktioniert **NUR** wenn:
- Frontend und Backend auf derselben Domain (oder Subdomain) sind
- ODER Backend CORS korrekt für Frontend-Origin konfiguriert ist
- `credentials: 'include'` / `withCredentials: true` gesetzt ist

---

## Migrations-Strategie

### Option A: Inkrementelle Migration (empfohlen)
1. ✅ Backend Hybrid-Modus aktiviert (Phase 1 - bereits erledigt)
2. 🔄 Frontend Schritt für Schritt anpassen:
   - Erst Login-Flow
   - Dann API-Client
   - Dann Auth-Checks
   - Zuletzt Logout
3. ✅ Testen in Entwicklung
4. ✅ Testen in Staging
5. ✅ Produktions-Deployment

### Option B: Big Bang Migration
- Alle Änderungen auf einmal in einem Feature-Branch
- Umfassende Tests vor Merge
- Risiko: Mehr potenzielle Fehlerquellen

**Empfehlung:** Option A - inkrementelle Migration

---

## Testing-Checkliste

### ✅ Funktionale Tests:

- [ ] **Login funktioniert**
  - Set-Cookie Header wird vom Backend gesendet
  - Cookie wird im Browser gespeichert
  - Keine Fehler in der Browser-Konsole

- [ ] **API-Requests funktionieren**
  - Cookie wird automatisch mit jeder Anfrage gesendet
  - Geschützte Endpoints liefern korrekte Daten
  - Keine 401-Fehler bei authentifizierten Requests

- [ ] **Auth-Status wird korrekt ermittelt**
  - `/api/auth/me` liefert Benutzer-Daten
  - Protected Routes funktionieren
  - Unauthentifizierte Nutzer werden zur Login-Seite geleitet

- [ ] **Logout funktioniert**
  - `/api/auth/logout` wird aufgerufen
  - Cookie wird gelöscht
  - Nach Logout keine Zugriff mehr auf geschützte Bereiche

- [ ] **Token-Expiry funktioniert**
  - Nach Ablauf des Cookies (1 Stunde) erfolgt Auto-Logout
  - Oder Redirect zur Login-Seite

### 🔍 Browser DevTools Checks:

**Chrome/Firefox DevTools:**
1. **Application/Storage Tab → Cookies:**
   - Nach Login: `auth_token` Cookie sollte sichtbar sein
   - Flags: `HttpOnly`, `Secure`, `SameSite=Lax`
   - Nach Logout: Cookie sollte verschwunden sein

2. **Network Tab:**
   - Login-Request: Response Headers sollten `Set-Cookie: auth_token=...` enthalten
   - API-Requests: Request Headers sollten `Cookie: auth_token=...` enthalten
   - Keine `Authorization: Bearer ...` Headers mehr

3. **Console:**
   - Keine Fehler bezüglich CORS
   - Keine `localStorage.getItem` Aufrufe für Tokens

---

## Häufige Probleme & Lösungen

### Problem 1: "Cookie wird nicht gesetzt"

**Symptom:** Nach Login ist kein Cookie im Browser sichtbar.

**Lösungen:**
- ✅ Prüfen: `credentials: 'include'` bei fetch / `withCredentials: true` bei axios
- ✅ Prüfen: CORS-Origin ist korrekt konfiguriert (Backend)
- ✅ Prüfen: `allow_credentials=True` im Backend (bereits erledigt)
- ✅ Prüfen: HTTPS wird verwendet (Secure-Flag erfordert HTTPS)
- ✅ Lokale Entwicklung: `Secure=False` temporär setzen (nur für localhost)

### Problem 2: "Cookie wird nicht mit Requests gesendet"

**Symptom:** API-Requests bekommen 401-Fehler trotz vorhandenem Cookie.

**Lösungen:**
- ✅ Prüfen: `credentials: 'include'` bei JEDEM fetch-Call
- ✅ Prüfen: Cookie-Domain passt zur Request-Domain
- ✅ Prüfen: Cookie ist nicht abgelaufen (DevTools → Application → Cookies)
- ✅ Prüfen: Cookie-Path ist `/` (nicht `/api` oder spezifischer)

### Problem 3: "CORS-Fehler"

**Symptom:** Browser blockiert Requests mit CORS-Fehlern.

**Lösungen:**
- ✅ Prüfen: Frontend-Origin ist in Backend CORS-Config erlaubt
- ✅ Prüfen: `allow_credentials=True` im Backend
- ✅ Prüfen: Keine Wildcards (`*`) bei Origins wenn credentials=True
- ✅ Prüfen: Preflight OPTIONS-Requests werden korrekt beantwortet

### Problem 4: "Cookie funktioniert nicht auf localhost"

**Symptom:** In lokaler Entwicklung wird Cookie nicht gesetzt/gesendet.

**Lösungen:**

**Option A:** Backend temporär mit `Secure=False` (nur für Entwicklung):
```python
# routes/auth.py - NUR für Entwicklung!
response.set_cookie(
    key="auth_token",
    value=token,
    httponly=True,
    secure=False,  # ⚠️ NUR für localhost ohne HTTPS!
    samesite="lax",
    max_age=3600,
)
```

**Option B:** Lokales HTTPS mit mkcert:
```bash
# mkcert installieren und lokales HTTPS einrichten
mkcert -install
mkcert localhost 127.0.0.1 ::1
```

**Option C:** Frontend und Backend auf demselben Port (Proxy):
```javascript
// vite.config.js oder vue.config.js
export default {
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      }
    }
  }
}
```

---

## Code-Beispiele für verschiedene Frameworks

### React (mit Hooks):
Siehe oben unter "Authentifizierungs-Status prüfen" → React Context Beispiel

### Vue.js 3 (Composition API):
```javascript
// useAuth.js
import { ref, computed, onMounted } from 'vue';

const user = ref(null);
const isAuthenticated = computed(() => !!user.value);
const isLoading = ref(true);

export function useAuth() {
  async function checkAuthStatus() {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/auth/me`, {
        credentials: 'include',
      });

      if (response.ok) {
        user.value = await response.json();
      } else {
        user.value = null;
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      user.value = null;
    } finally {
      isLoading.value = false;
    }
  }

  async function login(email, code) {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, code }),
    });

    if (response.ok) {
      await checkAuthStatus();
      return true;
    }
    return false;
  }

  async function logout() {
    await fetch(`${import.meta.env.VITE_API_URL}/api/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    });
    user.value = null;
  }

  onMounted(() => {
    checkAuthStatus();
  });

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    checkAuthStatus,
  };
}
```

### Svelte:
```javascript
// stores/auth.js
import { writable } from 'svelte/store';

function createAuthStore() {
  const { subscribe, set, update } = writable({
    user: null,
    isAuthenticated: false,
    isLoading: true,
  });

  return {
    subscribe,
    async checkAuth() {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/api/auth/me`, {
          credentials: 'include',
        });

        if (response.ok) {
          const userData = await response.json();
          set({ user: userData, isAuthenticated: true, isLoading: false });
        } else {
          set({ user: null, isAuthenticated: false, isLoading: false });
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        set({ user: null, isAuthenticated: false, isLoading: false });
      }
    },
    async login(email, code) {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email, code }),
      });

      if (response.ok) {
        await this.checkAuth();
        return true;
      }
      return false;
    },
    async logout() {
      await fetch(`${import.meta.env.VITE_API_URL}/api/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
      set({ user: null, isAuthenticated: false, isLoading: false });
    },
  };
}

export const auth = createAuthStore();
```

---

## Deployment-Hinweise

### Umgebungsvariablen aktualisieren:
```bash
# Production
CORS_ORIGINS=https://ki-sicherheit.jetzt,https://make.ki-sicherheit.jetzt

# Staging
CORS_ORIGINS=https://staging.ki-sicherheit.jetzt
```

### Cookie-Konfiguration für Production:
- ✅ `Secure=True` (nur HTTPS)
- ✅ `SameSite=Lax` (CSRF-Schutz)
- ✅ `HttpOnly=True` (XSS-Schutz)
- ✅ `max_age=3600` (1 Stunde, anpassbar)

### Monitoring:
- Fehlerrate bei Login-Requests überwachen
- Cookie-Setzung in Logs verfolgen
- CORS-Fehler im Browser-Monitoring erfassen

---

## Rollback-Plan

Falls Probleme auftreten, können Sie temporär zurückrollen:

1. **Frontend:** Alte localStorage-Version deployen
2. **Backend:** Bleibt im Hybrid-Modus (unterstützt beide Methoden)
3. **Problem analysieren und beheben**
4. **Erneut deployen**

Der Hybrid-Modus (Phase 1) ermöglicht diese Flexibilität!

---

## Nächste Schritte nach erfolgreicher Migration

Nach erfolgreicher Phase 2-Migration:

1. ✅ **Monitoring:** 1-2 Wochen in Production beobachten
2. ✅ **User-Feedback:** Probleme sammeln und beheben
3. ✅ **Performance:** Token-Validierungs-Performance messen
4. 🔮 **Phase 3 (optional):** Backend auf Cookie-Only umstellen

**Phase 3 ist OPTIONAL** und sollte erst nach erfolgreicher Phase 2 in Betracht gezogen werden!

---

## Zusammenfassung

### Kern-Änderungen:
1. ❌ **Entfernen:** `localStorage.getItem/setItem('auth_token')`
2. ❌ **Entfernen:** Manuelle `Authorization: Bearer` Header
3. ✅ **Hinzufügen:** `credentials: 'include'` bei ALLEN API-Requests
4. ✅ **Nutzen:** `/api/auth/me` für Auth-Status
5. ✅ **Nutzen:** `/api/auth/logout` für Logout

### Vorteile nach Migration:
- 🔒 **Sicherer:** XSS-Angriffe können Tokens nicht mehr stehlen
- 🚀 **Einfacher:** Keine manuelle Token-Verwaltung nötig
- ✅ **Modern:** Industry Best Practice für Web-Authentifizierung

---

## Support & Fragen

Bei Fragen oder Problemen während der Migration:
1. Prüfen Sie die "Häufige Probleme & Lösungen" Sektion
2. Überprüfen Sie Browser DevTools (Network + Application Tabs)
3. Kontaktieren Sie das Backend-Team

**Viel Erfolg bei der Migration!** 🚀
