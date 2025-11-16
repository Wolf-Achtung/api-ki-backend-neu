# Frontend-Briefing: Cookie-Authentifizierung aktivieren

**Datum:** 2025-11-16
**Betrifft:** E-Mail-Versand für KI-Status-Reports
**Priorität:** 🔴 HOCH
**Aufwand:** ~30 Minuten

---

## 🎯 Problem

User und Admins erhalten keine E-Mails nach dem Briefing-Submit, obwohl der Report erfolgreich generiert wird.

**Root Cause:**
Das Frontend sendet bei API-Calls keine Cookies mit → Backend kann User nicht identifizieren → `user_id=None` → keine User-E-Mail bekannt → keine E-Mail-Versand.

**Backend-Log (aktuell):**
```log
✅ Briefing saved to database: ID=72, user_id=None  ← PROBLEM!
```

**Backend-Log (gewünscht):**
```log
✅ Token validated successfully for user: wolf.hohl@web.de
✅ Found existing user: wolf.hohl@web.de (ID=5)
✅ Briefing saved to database: ID=72, user_id=5  ← LÖSUNG!
📧 Mail sent to user wolf.hohl@web.de via Resend
```

---

## 🔧 Was muss geändert werden?

### **1. Alle API-Calls müssen Cookies mitsenden**

Das Backend setzt nach Login ein httpOnly Cookie `auth_token`. Dieses Cookie muss bei **ALLEN** API-Requests mitgesendet werden.

**Betroffene Endpoints:**
- ✅ `POST /api/auth/request-code` (schon OK, kein Auth nötig)
- ✅ `POST /api/auth/login` (schon OK, setzt Cookie)
- 🔴 **`POST /api/briefings/submit`** ← HIER FEHLT ES
- 🔴 `GET /api/auth/me` (falls verwendet)
- 🔴 Alle anderen geschützten Endpoints

---

## 📝 Code-Änderungen

### **Variante A: fetch() API**

**❌ Aktuell (falsch):**
```javascript
const response = await fetch('https://api-ki-backend-neu-production.up.railway.app/api/briefings/submit', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(briefingData)
});
```

**✅ Neu (korrekt):**
```javascript
const response = await fetch('https://api-ki-backend-neu-production.up.railway.app/api/briefings/submit', {
  method: 'POST',
  credentials: 'include',  // ← NEU: Cookies mitsenden
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(briefingData)
});
```

---

### **Variante B: axios**

**❌ Aktuell (falsch):**
```javascript
const response = await axios.post(
  'https://api-ki-backend-neu-production.up.railway.app/api/briefings/submit',
  briefingData,
  {
    headers: {
      'Content-Type': 'application/json',
    }
  }
);
```

**✅ Neu (korrekt):**
```javascript
const response = await axios.post(
  'https://api-ki-backend-neu-production.up.railway.app/api/briefings/submit',
  briefingData,
  {
    withCredentials: true,  // ← NEU: Cookies mitsenden
    headers: {
      'Content-Type': 'application/json',
    }
  }
);
```

---

### **Variante C: axios global konfigurieren (empfohlen)**

Falls ihr axios global verwendet, könnt ihr `withCredentials` einmal zentral setzen:

```javascript
// In eurer API-Client-Konfiguration (z.B. api.js oder axios-config.js)
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'https://api-ki-backend-neu-production.up.railway.app',
  withCredentials: true,  // ← Gilt für alle Requests
  headers: {
    'Content-Type': 'application/json',
  }
});

export default apiClient;
```

Dann in Komponenten:
```javascript
import apiClient from './api';

// Alle Requests senden automatisch Cookies mit
const response = await apiClient.post('/api/briefings/submit', briefingData);
```

---

## 🔍 Betroffene Dateien (wahrscheinlich)

Sucht nach diesen Patterns in eurem Frontend-Code:

```bash
# Suche nach /api/briefings/submit ohne credentials
grep -r "briefings/submit" src/

# Suche nach fetch ohne credentials
grep -r "fetch.*api-ki-backend" src/

# Suche nach axios ohne withCredentials
grep -r "axios\." src/
```

**Typische Orte:**
- `src/services/api.js` oder `src/api/client.js`
- `src/components/BriefingForm.vue` / `.jsx` / `.tsx`
- `src/pages/Briefing.vue` / `.jsx` / `.tsx`
- `src/store/` (falls Vuex/Redux)

---

## ✅ Testing-Checklist

### **1. Login-Flow testen**

```javascript
// 1. Request Code
await fetch('https://api-ki-backend-neu-production.up.railway.app/api/auth/request-code', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'test@example.com' })
});

// 2. Login with Code
const loginResponse = await fetch('https://api-ki-backend-neu-production.up.railway.app/api/auth/login', {
  method: 'POST',
  credentials: 'include',  // ← WICHTIG
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'test@example.com', code: '123456' })
});

// 3. Check Cookie in DevTools
// Chrome: DevTools → Application → Cookies → api-ki-backend-neu-production.up.railway.app
// Sollte Cookie "auth_token" enthalten
```

### **2. Cookie im Browser verifizieren**

Nach erfolgreichem Login:

1. **Chrome/Edge:** F12 → Application → Cookies → `api-ki-backend-neu-production.up.railway.app`
2. **Firefox:** F12 → Storage → Cookies → `api-ki-backend-neu-production.up.railway.app`

**Erwartetes Cookie:**
- **Name:** `auth_token`
- **Value:** `eyJ...` (JWT Token)
- **HttpOnly:** ✅ true
- **Secure:** ✅ true
- **SameSite:** Lax
- **Path:** /
- **Expires:** ~1 Stunde ab Login

### **3. Briefing-Submit testen**

```javascript
// Nach Login (Cookie existiert)
const response = await fetch('https://api-ki-backend-neu-production.up.railway.app/api/briefings/submit', {
  method: 'POST',
  credentials: 'include',  // ← WICHTIG
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    lang: 'de',
    answers: { /* ... */ },
    queue_analysis: true
  })
});

// Response sollte 200 OK sein
console.log(response.status); // 200
```

### **4. Network-Tab prüfen**

In Chrome DevTools → Network → `briefings/submit` Request:

**Request Headers sollten enthalten:**
```
Cookie: auth_token=eyJ...
```

**Falls Cookie NICHT gesendet wird:**
- ❌ Frontend sendet `credentials: 'include'` nicht
- ❌ Cookie hat falsches Domain/Path-Attribut
- ❌ SameSite-Policy blockiert Cookie

---

## 🐛 Troubleshooting

### **Problem 1: Cookie wird nicht gesetzt nach Login**

**Check:**
```javascript
const response = await fetch('/api/auth/login', {
  credentials: 'include',  // ← Muss hier sein!
  // ...
});
```

**Lösung:** `credentials: 'include'` auch beim Login-Request setzen.

---

### **Problem 2: Cookie wird gesetzt, aber nicht mitgesendet**

**Check:**
- Frontend und Backend auf **verschiedenen Domains**?
  - Frontend: `ki-sicherheit.jetzt`
  - Backend: `api-ki-backend-neu-production.up.railway.app`

**Problem:** Cross-Domain-Cookies funktionieren nur mit korrekter CORS-Konfiguration.

**Lösung (Backend - bereits konfiguriert):**
```python
# main.py - BEREITS KORREKT
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ki-sicherheit.jetzt",
        "https://www.ki-sicherheit.jetzt",
        # ...
    ],
    allow_credentials=True,  # ← WICHTIG für Cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Lösung Frontend:**
```javascript
// MUSS credentials: 'include' setzen
fetch(url, { credentials: 'include' })
```

---

### **Problem 3: "CORS policy" Error**

**Error:**
```
Access to fetch at '...' has been blocked by CORS policy:
The value of the 'Access-Control-Allow-Credentials' header in the response is ''
which must be 'true' when the request's credentials mode is 'include'.
```

**Ursache:** Frontend-Domain ist nicht in Backend CORS `allow_origins` eingetragen.

**Lösung:** Backend-Team kontaktieren, Domain in Railway Environment Variable `CORS_ORIGINS` eintragen.

**Aktuell erlaubte Domains (Backend):**
- `https://ki-sicherheit.jetzt`
- `https://www.ki-sicherheit.jetzt`
- `https://ki-foerderung.jetzt`
- `https://make.ki-sicherheit.jetzt`
- `https://www.make.ki-sicherheit.jetzt`

Falls ihr von einer anderen Domain deployed: Backend muss angepasst werden!

---

### **Problem 4: Cookie existiert, aber Backend sagt "user_id=None"**

**Check Backend-Log:**
```log
# Sollte erscheinen (wenn Frontend korrekt):
[DEBUG] Found auth_token in cookie

# Fehlt diese Zeile?
→ Cookie wird nicht mitgesendet
→ credentials: 'include' fehlt
```

**Check im Browser Network-Tab:**
Request Headers sollten enthalten:
```
Cookie: auth_token=eyJ...
```

Falls nicht: `credentials: 'include'` fehlt!

---

## 📋 Deployment-Checkliste

- [ ] `credentials: 'include'` bei `/api/briefings/submit` hinzugefügt
- [ ] `credentials: 'include'` bei allen anderen geschützten Endpoints hinzugefügt
- [ ] Optional: axios global mit `withCredentials: true` konfiguriert
- [ ] Login-Flow getestet (Cookie wird gesetzt)
- [ ] Cookie im Browser DevTools verifiziert
- [ ] Briefing-Submit getestet (Cookie wird mitgesendet)
- [ ] Network-Tab geprüft (Cookie in Request Headers)
- [ ] E2E-Test: Briefing submitten → E-Mail beim User angekommen
- [ ] E2E-Test: Briefing submitten → E-Mail beim Admin angekommen (mit Briefing-Details)

---

## 📊 Erwartetes Ergebnis

### **Vorher (aktuell):**
```
User submittet Briefing
→ Frontend sendet Request OHNE Cookie
→ Backend: user_id=None
→ Report wird generiert
→ ❌ KEINE E-Mail an User (E-Mail unbekannt)
→ ✅ E-Mail an Admin (aber ohne User-Details)
```

### **Nachher (mit Fix):**
```
User submittet Briefing
→ Frontend sendet Request MIT Cookie (auth_token)
→ Backend liest Cookie, validiert Token
→ Backend findet User in DB: user_id=5, email=wolf.hohl@web.de
→ Report wird generiert
→ ✅ E-Mail an User (wolf.hohl@web.de)
→ ✅ E-Mail an Admin (mit Briefing-Details: Scores, Antworten)
```

---

## 🔗 Weitere Ressourcen

**MDN Dokumentation:**
- [fetch() credentials](https://developer.mozilla.org/en-US/docs/Web/API/fetch#credentials)
- [CORS credentials](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS#requests_with_credentials)

**axios Dokumentation:**
- [withCredentials](https://axios-http.com/docs/req_config)

**Backend-Dokumentation:**
- `DOWNLOAD_URLS.md` - Backend-Fixes
- `production-email-fixes/README.md` - Vollständige Backend-Dokumentation

---

## 📞 Support

**Bei Fragen:**
1. Backend-Logs aus Railway Dashboard kopieren
2. Frontend Network-Tab Screenshot (Request Headers)
3. Browser DevTools Cookie-Screenshot

**Backend-Team kontaktieren falls:**
- CORS-Fehler trotz `credentials: 'include'`
- Frontend-Domain nicht in `CORS_ORIGINS`
- Cookie wird gesetzt, aber Backend sagt "Invalid token"

---

**Geschätzter Aufwand:** 15-30 Minuten
**Priorität:** 🔴 Hoch (blockiert E-Mail-Versand)
**Testing-Zeit:** 10-15 Minuten
