# Login-Problem Debugging Guide

## Problem
Nach Eingabe des Login-Codes wird der Benutzer zurück zur Login-Seite geleitet.

## Mögliche Ursachen

### 1. Token wird nicht korrekt gespeichert
Das Frontend speichert den Token in `localStorage` unter dem Key `jwt`.

### 2. Token-Validierung schlägt fehl
Der Token wird gespeichert, aber die Validierung schlägt fehl.

### 3. CORS-Problem
CORS verhindert das Speichern des Tokens.

---

## Debugging-Schritte im Browser

### Schritt 1: Browser DevTools öffnen
- Chrome/Edge: `F12` oder `Strg+Shift+I`
- Firefox: `F12` oder `Strg+Shift+K`

### Schritt 2: Console-Tab öffnen
Wechsle zum "Console"-Tab.

### Schritt 3: Login-Prozess überwachen

Füge diesen Code in die Console ein **BEVOR** du den Login-Code eingibst:

```javascript
// Überwache localStorage-Änderungen
const originalSetItem = localStorage.setItem;
localStorage.setItem = function(key, value) {
  console.log('✅ localStorage.setItem:', key, '=', value);
  originalSetItem.apply(this, arguments);
};

// Überwache fetch-Requests
const originalFetch = window.fetch;
window.fetch = function(...args) {
  console.log('🌐 FETCH:', args[0]);
  return originalFetch.apply(this, arguments).then(response => {
    console.log('✅ RESPONSE:', args[0], 'Status:', response.status);
    return response;
  }).catch(error => {
    console.error('❌ FETCH ERROR:', args[0], error);
    throw error;
  });
};

console.log('🔍 Debugging aktiviert! Jetzt Login-Code eingeben.');
```

### Schritt 4: Login durchführen
Gib jetzt deinen Login-Code ein und beobachte die Console.

**Was du sehen solltest:**
1. `FETCH: /api/auth/login` (POST-Request)
2. `RESPONSE: /api/auth/login Status: 200`
3. `localStorage.setItem: jwt = <token>`

**Wenn du das NICHT siehst:**
- ❌ Wenn `localStorage.setItem` nicht aufgerufen wird → Frontend speichert Token nicht
- ❌ Wenn Status nicht 200 ist → Backend-Problem
- ❌ Wenn FETCH ERROR → Netzwerk- oder CORS-Problem

---

### Schritt 5: Token im localStorage überprüfen

```javascript
// Prüfe, ob Token gespeichert wurde
const token = localStorage.getItem('jwt');
console.log('Token im localStorage:', token);
console.log('Token-Länge:', token ? token.length : 'KEIN TOKEN!');
```

**Erwartetes Ergebnis:**
- Token sollte ca. 180-200 Zeichen lang sein
- Format: `eyJhbGciOiJIUzI1NiIs...` (JWT-Format)

---

### Schritt 6: Token-Validierung testen

```javascript
// Teste Token-Validierung gegen Debug-Endpoint
const token = localStorage.getItem('jwt');
if (!token) {
  console.error('❌ Kein Token gefunden!');
} else {
  fetch('/api/auth/debug', {
    headers: {
      'Authorization': 'Bearer ' + token,
      'Content-Type': 'application/json'
    }
  })
  .then(res => res.json())
  .then(data => {
    console.log('🔍 Debug-Response:', data);
    if (data.token_info.verified) {
      console.log('✅ Token ist GÜLTIG!');
      console.log('User:', data.token_info.verified_email);
    } else {
      console.error('❌ Token ist UNGÜLTIG!');
      console.error('Fehler:', data.token_info.verify_error);
    }
  })
  .catch(err => console.error('❌ Fehler:', err));
}
```

---

### Schritt 7: CORS-Probleme überprüfen

Schaue in der Console nach CORS-Fehlern wie:
```
Access to fetch at '...' from origin '...' has been blocked by CORS policy
```

**Wenn CORS-Fehler vorhanden:**
1. Überprüfe die `CORS_ORIGINS` Umgebungsvariable im Backend
2. Stelle sicher, dass die Frontend-URL in der Liste ist

**Aktuelle CORS-Konfiguration:**
```
https://ki-sicherheit.jetzt
https://www.ki-sicherheit.jetzt
https://ki-foerderung.jetzt
https://make.ki-sicherheit.jetzt
https://www.make.ki-sicherheit.jetzt
```

---

## Test mit Python-Script

Alternativ kannst du den Login-Flow mit dem Python-Script testen:

```bash
python test_login_flow.py
```

Dies testet:
1. Code-Anforderung
2. Login mit Code
3. Token-Validierung
4. Zugriff auf geschützte Endpoints

---

## Häufige Probleme & Lösungen

### Problem 1: Token wird nicht gespeichert

**Symptom:** `localStorage.setItem` wird nicht aufgerufen

**Ursache:** Frontend-Code speichert Token nicht nach erfolgreichem Login

**Lösung:** Überprüfe den Login-Handler im Frontend:
```javascript
// RICHTIG:
fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, code })
})
.then(res => res.json())
.then(data => {
  if (data.access_token) {
    localStorage.setItem('jwt', data.access_token);  // <-- WICHTIG!
    window.location.href = '/admin/';
  }
});
```

### Problem 2: Token ist ungültig

**Symptom:** `verified: false` im Debug-Endpoint

**Mögliche Ursachen:**
- JWT_SECRET im Backend hat sich geändert
- Token ist abgelaufen
- Token-Format ist falsch

**Lösung:**
1. Prüfe JWT_SECRET: `/api/debug/env`
2. Generiere neuen Token durch erneuten Login

### Problem 3: CORS blockiert Requests

**Symptom:** Console zeigt CORS-Fehler

**Lösung:**
1. Füge Frontend-URL zu `CORS_ORIGINS` hinzu
2. Oder setze `CORS_ALLOW_ANY=1` (nur für Development!)

### Problem 4: Token-Format falsch

**Symptom:** Backend-Logs zeigen "Invalid Authorization header format"

**Lösung:** Authorization-Header muss Format haben:
```
Authorization: Bearer <token>
```

NICHT:
```
Authorization: <token>
```

---

## Debug-Endpoints

Das Backend bietet folgende Debug-Endpoints:

### `/api/auth/debug`
Zeigt:
- JWT-Konfiguration
- Token-Validierung
- Redis-Status
- Mail-Provider
- Rate-Limits

### `/api/briefings/debug`
Zeigt:
- Authentifizierungsstatus
- Token-Verifizierung
- Client-Informationen
- Request-Headers

### `/api/debug/config`
Zeigt:
- App-Konfiguration
- Feature-Flags
- Security-Einstellungen (ohne Secrets)

### `/api/debug/env`
Zeigt:
- Umgebungsvariablen
- Secret-Status

### `/api/debug/system`
Zeigt:
- Python-Version
- Platform-Informationen
- Gemountete Router

---

## Kontakt & Support

Bei weiteren Problemen:
1. Überprüfe die Browser-Console
2. Führe das Python-Test-Script aus
3. Nutze die Debug-Endpoints
4. Erstelle ein GitHub-Issue mit den Console-Logs
