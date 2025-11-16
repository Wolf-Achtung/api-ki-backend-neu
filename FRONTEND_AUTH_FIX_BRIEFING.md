# Frontend Auth-Fix: Briefing für Entwicklung

## 🎯 Problem-Beschreibung

**Symptom:** Nach erfolgreichem Login wird der User zur Startseite zurückgeleitet, anstatt zum Fragebogen weitergeleitet zu werden.

**Root Cause:** Frontend speichert das Auth-Token nach dem Login nicht und sendet es bei nachfolgenden Requests nicht mit. Das Backend erkennt den User daher als "nicht eingeloggt" und schickt ihn zurück.

**Diagnose-Ergebnis (aus Backend-Tests):**
```
✅ Login erfolgreich! (Backend gibt Token zurück)
✅ /me mit Authorization Header funktioniert!
❌ Cookie "auth_token" NICHT gefunden! (Cross-Domain Problem)
❌ /me mit Cookie fehlgeschlagen: HTTP 401
```

---

## 🔍 Technische Details

### **Warum funktionieren Cookies nicht?**

**Frontend:** `https://make.ki-sicherheit.jetzt`
**Backend:** `https://api-ki-backend-neu-production.up.railway.app`

→ **Verschiedene Domains** → Browser blockiert Cross-Domain Cookies aus Sicherheitsgründen

### **Backend-Verhalten (korrekt)**

Das Backend gibt beim Login **zwei Auth-Mechanismen** zurück:

1. **httpOnly Cookie** `auth_token` (funktioniert nur bei gleicher Domain)
2. **Access Token** im Response-Body (funktioniert immer, muss manuell verwaltet werden)

**Login-Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## ✅ Erforderliche Änderungen im Frontend

### **1. Token nach Login speichern**

**Datei:** Login-Komponente (z.B. `pages/login.tsx` oder `components/Login.jsx`)

**Änderung:**
```typescript
// VORHER (funktioniert nicht):
async function handleLogin(email: string, code: string) {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, code })
  });

  if (response.ok) {
    // ❌ Token wird nicht gespeichert!
    router.push('/fragebogen');
  }
}

// NACHHER (funktioniert):
async function handleLogin(email: string, code: string) {
  const response = await fetch('https://api-ki-backend-neu-production.up.railway.app/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, code })
  });

  if (response.ok) {
    const data = await response.json();

    // ✅ TOKEN SPEICHERN
    localStorage.setItem('access_token', data.access_token);

    // Jetzt zur nächsten Seite
    router.push('/fragebogen');
  }
}
```

---

### **2. API-Helper erstellen**

**Neue Datei:** `lib/api.ts` oder `utils/api.ts`

```typescript
const API_BASE_URL = 'https://api-ki-backend-neu-production.up.railway.app';

export async function apiCall(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = localStorage.getItem('access_token');

  const config: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
      // ✅ Token als Authorization Header hinzufügen
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

  // Bei 401 Unauthorized: Token ungültig → zurück zum Login
  if (response.status === 401) {
    localStorage.removeItem('access_token');
    window.location.href = '/';
    throw new Error('Unauthorized - Bitte neu einloggen');
  }

  return response;
}

// Convenience-Funktionen:
export async function apiGet(endpoint: string) {
  return apiCall(endpoint, { method: 'GET' });
}

export async function apiPost(endpoint: string, data: any) {
  return apiCall(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
```

---

### **3. Auth-Check auf Fragebogen-Seite**

**Datei:** `pages/fragebogen.tsx` oder entsprechende Komponente

```typescript
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { apiGet } from '@/lib/api';

export default function FragebogenPage() {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [userEmail, setUserEmail] = useState('');

  useEffect(() => {
    checkAuth();
  }, []);

  async function checkAuth() {
    try {
      const response = await apiGet('/api/auth/me');

      if (response.ok) {
        const userData = await response.json();
        setUserEmail(userData.email);
        setIsAuthenticated(true);
      } else {
        // Nicht eingeloggt → zurück zum Login
        router.push('/');
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      router.push('/');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <div>Laden...</div>;
  }

  if (!isAuthenticated) {
    return null; // Wird schon umgeleitet
  }

  return (
    <div>
      <h1>Fragebogen für {userEmail}</h1>
      {/* Ihr Fragebogen */}
    </div>
  );
}
```

---

### **4. Briefing-Submit mit Auth**

**Datei:** Fragebogen-Submit-Handler

```typescript
import { apiPost } from '@/lib/api';

async function submitBriefing(formData: any) {
  try {
    const response = await apiPost('/api/briefings/submit', {
      lang: 'de',
      answers: formData,  // Ihre Formulardaten
      queue_analysis: true,
    });

    if (response.ok) {
      const data = await response.json();
      console.log('Briefing eingereicht:', data);

      // Weiterleitung zur Erfolgsseite
      router.push('/success');
    } else {
      const error = await response.json();
      alert('Fehler beim Einreichen: ' + (error.detail || 'Unbekannter Fehler'));
    }
  } catch (error) {
    console.error('Submit error:', error);
    alert('Fehler beim Einreichen des Briefings');
  }
}
```

---

## 📝 API-Dokumentation

### **Backend-Endpoints**

**Base URL:** `https://api-ki-backend-neu-production.up.railway.app`

#### **1. Code anfordern**

```
POST /api/auth/request-code
Content-Type: application/json

Body:
{
  "email": "user@example.com"
}

Response: 204 No Content
```

#### **2. Login mit Code**

```
POST /api/auth/login
Content-Type: application/json

Body:
{
  "email": "user@example.com",
  "code": "123456"
}

Response: 200 OK
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

#### **3. Auth-Status prüfen**

```
GET /api/auth/me
Authorization: Bearer <access_token>

Response: 200 OK
{
  "email": "user@example.com",
  "sub": "user@example.com",
  "exp": 1234567890,
  "iat": 1234567890
}

Response bei fehlendem/ungültigem Token: 401 Unauthorized
```

#### **4. Briefing einreichen**

```
POST /api/briefings/submit
Authorization: Bearer <access_token>
Content-Type: application/json
Idempotency-Key: unique-key-123

Body:
{
  "lang": "de",
  "answers": {
    "branche": "IT",
    "bundesland": "Bayern",
    "jahresumsatz": "1-5M",
    "unternehmensgroesse": "10-50",
    "ki_kompetenz": "Anfänger",
    "hauptleistung": "Software-Entwicklung"
  },
  "queue_analysis": true
}

Response: 202 Accepted
{
  "status": "queued",
  "lang": "de"
}
```

---

## 🧪 Testing-Anleitung

### **Lokales Testen**

1. **Login-Flow testen:**
   ```typescript
   // Browser Console:
   localStorage.clear(); // Reset

   // Nach Login prüfen:
   console.log('Token:', localStorage.getItem('access_token'));
   // Sollte: "eyJhbGci..." anzeigen
   ```

2. **Auth-Status prüfen:**
   ```typescript
   // Browser Console:
   fetch('https://api-ki-backend-neu-production.up.railway.app/api/auth/me', {
     headers: {
       'Authorization': 'Bearer ' + localStorage.getItem('access_token')
     }
   })
   .then(r => r.json())
   .then(d => console.log('User:', d));
   // Sollte: { email: "...", ... } anzeigen
   ```

3. **Kompletter Flow:**
   - Login mit echtem Account: `wolf.hohl@web.de`
   - Code aus Email eingeben
   - Prüfen ob Weiterleitung zum Fragebogen erfolgt
   - Browser DevTools Network-Tab: Alle Requests sollten `Authorization: Bearer ...` Header haben

### **Backend Test-Dashboard**

Es gibt ein Test-Dashboard zum Debuggen:
```
https://make.ki-sicherheit.jetzt/formular/test-dashboard-minimal.html
```

**Features:**
- ✅ 5 automatische API-Tests
- 🔐 Interaktiver Login-Flow-Test
- 📋 Live-Logs mit detaillierten Fehlermeldungen

**Verwendung:**
1. Dashboard öffnen
2. API-URL: `https://api-ki-backend-neu-production.up.railway.app`
3. Email: `wolf.hohl@web.de`
4. Klick auf "🔐 Login-Flow testen"
5. Code aus Email eingeben
6. Ergebnisse analysieren

---

## ✅ Checkliste

### **Code-Änderungen:**
- [ ] Login-Komponente speichert `access_token` nach erfolgreichem Login
- [ ] API-Helper (`lib/api.ts`) erstellt mit Authorization Header
- [ ] Fragebogen-Seite prüft Auth-Status beim Laden
- [ ] Briefing-Submit verwendet API-Helper mit Auth
- [ ] Logout-Funktion löscht Token aus localStorage

### **Testing:**
- [ ] Login funktioniert (Token wird gespeichert)
- [ ] Nach Login Weiterleitung zum Fragebogen
- [ ] Fragebogen lädt ohne Redirect zurück zum Login
- [ ] Briefing kann eingereicht werden
- [ ] Bei ungültigem Token: Redirect zum Login
- [ ] Logout funktioniert

### **Edge Cases:**
- [ ] Was passiert wenn Token abgelaufen ist? → Redirect zum Login
- [ ] Was passiert bei Seiten-Reload? → Auth-Check läuft, User bleibt eingeloggt
- [ ] Was passiert wenn Backend offline ist? → Sinnvolle Fehlermeldung

---

## 🔧 Optional: Auth Context (für größere Apps)

Für eine saubere Architektur kann ein Auth Context erstellt werden:

**Datei:** `contexts/AuthContext.tsx`

```typescript
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiGet } from '@/lib/api';

interface User {
  email: string;
  sub: string;
  exp: number;
  iat: number;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, code: string) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  async function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const res = await apiGet('/api/auth/me');
      if (res.ok) {
        const userData = await res.json();
        setUser(userData);
      } else {
        localStorage.removeItem('access_token');
      }
    } catch (error) {
      console.error('Auth check failed:', error);
    } finally {
      setLoading(false);
    }
  }

  async function login(email: string, code: string): Promise<boolean> {
    const res = await fetch('https://api-ki-backend-neu-production.up.railway.app/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, code }),
    });

    if (res.ok) {
      const data = await res.json();
      localStorage.setItem('access_token', data.access_token);
      await checkAuth();
      return true;
    }
    return false;
  }

  function logout() {
    localStorage.removeItem('access_token');
    setUser(null);
    window.location.href = '/';
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

**Verwendung:**

```typescript
// _app.tsx
import { AuthProvider } from '@/contexts/AuthContext';

export default function App({ Component, pageProps }) {
  return (
    <AuthProvider>
      <Component {...pageProps} />
    </AuthProvider>
  );
}

// In Komponenten:
import { useAuth } from '@/contexts/AuthContext';

function FragebogenPage() {
  const { user, loading, logout } = useAuth();

  if (loading) return <div>Laden...</div>;
  if (!user) {
    router.push('/');
    return null;
  }

  return (
    <div>
      <p>Eingeloggt als: {user.email}</p>
      <button onClick={logout}>Logout</button>
      {/* ... */}
    </div>
  );
}
```

---

## 📞 Support

**Backend-Status prüfen:**
```
https://api-ki-backend-neu-production.up.railway.app/health
```

**Test-Dashboard:**
```
https://make.ki-sicherheit.jetzt/formular/test-dashboard-minimal.html
```

**Typische Fehler:**

| Fehler | Ursache | Lösung |
|--------|---------|---------|
| HTTP 401 Unauthorized | Token fehlt oder ungültig | Token prüfen, ggf. neu einloggen |
| HTTP 422 Validation Error | Falsches Request-Format | Body-Format prüfen (siehe API-Doku) |
| Zurück zum Login nach Submit | Token wird nicht mitgeschickt | Authorization Header prüfen |
| CORS Error | Falsche Origin | Sollte nicht passieren, CORS ist konfiguriert |

---

## 🎯 Zusammenfassung

**Problem:** Token wird nach Login nicht gespeichert und bei Requests nicht mitgeschickt.

**Lösung:**
1. Nach Login: Token in `localStorage` speichern
2. Bei jedem Request: Token als `Authorization: Bearer <token>` Header mitschicken
3. Bei 401: Zurück zum Login

**Aufwand:** ~2-3 Stunden (je nach Code-Struktur)

**Priorität:** 🔴 Hoch (blockiert Login-Flow)
