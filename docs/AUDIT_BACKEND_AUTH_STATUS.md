# Backend-Auth-Status Audit Report

**Erstellt:** 2025-12-13
**Auditor:** Claude (Senior Backend Engineer)
**Scope:** Auth- und Security-Stand im Backend

---

## Architektur-Skizze (Request-Flow)

```
HTTP Request
    |
    v
+-------------------------------------------------------------+
|                    FastAPI App (main.py)                     |
|                                                              |
|  +------------------------------------------------------+   |
|  |            CORS Middleware (einzige Middleware)       |   |
|  |          - allow_credentials=True (wenn Origins fix)  |   |
|  |          - allow_origins aus ENV oder Defaults        |   |
|  +------------------------------------------------------+   |
|                            |                                 |
|                            v                                 |
|  +------------------------------------------------------+   |
|  |                 Route Dispatcher                      |   |
|  |    /api/auth/*     -> routes/auth.py                  |   |
|  |    /api/briefings/*-> routes/briefings.py             |   |
|  |    /api/analyze/*  -> routes/analyze.py               |   |
|  |    /api/report/*   -> routes/report.py                |   |
|  |    /api/feedback/* -> routes/feedback.py              |   |
|  |    /api/admin/*    -> routes/admin.py (wenn enabled)  |   |
|  +------------------------------------------------------+   |
|                            |                                 |
|                            v                                 |
|  +------------------------------------------------------+   |
|  |          Dependency Injection (pro Endpoint)          |   |
|  |    - Depends(get_db) -> DB Session                    |   |
|  |    - Depends(get_current_user) -> JWT Validation      |   |
|  |    - Depends(rate_limiter(...)) -> Rate Limiting      |   |
|  +------------------------------------------------------+   |
+-------------------------------------------------------------+
```

---

## 1) Auth-Entry-Points

### Zentrale Auth-Dependency: `core/security.py:51-87`

```python
def get_current_user(
    auth_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
) -> TokenPayload:
    # Priority 1: httpOnly Cookie (auth_token)
    # Priority 2: Authorization Header (Bearer token)
    # Wirft HTTPException 401 wenn kein Token
```

### Auth-Pruefung pro Endpoint-Kategorie:

| Route/Pfad | Auth-Dependency | Auth-Pflicht | Exceptions |
|------------|-----------------|--------------|------------|
| `/api/auth/me` | `Depends(get_current_user)` | Zwingend | 401 |
| `/api/briefings/submit` | **OPTIONAL** (manuelle Pruefung) | Optional | 401 nur bei ungueltigem Token |
| `/api/report/*` | **KEINE** | Keine | - |
| `/api/analyze/run` | **KEINE** | Keine | - |
| `/api/dashboard/*` | **KEINE** | Keine | - |
| `/api/reports/*` | **KEINE** | Keine | - |
| `/api/feedback` | **KEINE** | Keine | - |
| `/api/admin/*` | `Depends(get_current_user)` + `_require_admin()` | Admin erforderlich | 401 + 403 |

### Relevante Dateien:

| Datei | Rolle |
|-------|-------|
| `core/security.py` | JWT-Erstellung, Validierung, `get_current_user` Dependency |
| `routes/auth.py` | Login-Endpoints (request-code, login, logout, me) |
| `routes/_bootstrap.py` | `get_db`, `rate_limiter` Dependencies |
| `services/auth.py` | DB-basierte Code-Generierung & Validierung (Tabelle `login_codes`) |
| `settings.py` | JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_DAYS |

### Verwendete Exceptions:

- **401 UNAUTHORIZED**: `core/security.py:37,39,44,47,81-84` - Invalid/expired token, missing auth
- **403 FORBIDDEN**: `routes/auth.py:116-119` - Email nicht in Whitelist
- **409 CONFLICT**: `routes/auth.py:279` - Duplicate Request (Idempotency)
- **429 TOO_MANY_REQUESTS**: `services/rate_limit.py:71-75` - Rate limit exceeded

---

## 2) Session- & Cookie-Handling

### Cookie-Konfiguration: `routes/auth.py:291-300`

| Attribut | Wert | Quelle |
|----------|------|--------|
| Cookie-Name | `auth_token` | hardcoded |
| `httpOnly` | `True` | hardcoded |
| `Secure` | `True` | hardcoded |
| `SameSite` | `none` | hardcoded |
| `max_age` | `3600` (1 Stunde) | hardcoded |
| `path` | `/` | hardcoded |

### Session-Identifikation:

- **Kein Session-Store**: Stateless JWT-basierte Auth
- **Token-Lebensdauer**: `JWT_EXPIRE_DAYS` (default: 7 Tage) - aus `settings.py:19`
- **Refresh-Mechanismus**: Nicht vorhanden
- **Token-Speicher**:
  - Redis (wenn `REDIS_URL` gesetzt): `services/redis_utils.py` via `RedisBox`
  - Fallback: In-Memory Dict (`routes/auth.py:54`)

### Cookie-Validierung: `core/security.py:51-87`

```python
# Priority 1: Cookie "auth_token"
if auth_token:
    token = auth_token
# Priority 2: Authorization Header
elif authorization:
    ...
```

---

## 3) Report-Submission-Pfad (kritisch)

### Endpoint: `POST /api/briefings/submit` (`routes/briefings.py:38-167`)

**Auth-Verhalten:**
```python
# routes/briefings.py:71-122
# JWT optional - bei fehlendem Token wird NICHT blockiert
token = None

# Priority 1: Cookie
cookie_token = request.cookies.get("auth_token")
if cookie_token:
    token = cookie_token

# Fallback: Authorization Header
elif request.headers.get("authorization"):
    ...

if token:
    # Token validieren - BEI FEHLER WIRD ABGEBROCHEN (401)
    try:
        result = verify_access_token(token)
        authenticated_user = result.email
    except Exception:
        raise HTTPException(status_code=401, ...)
else:
    log.debug("No authentication found - proceeding without authentication")
```

**Ablauf:**
1. Idempotency-Check (`Idempotency-Key` Header)
2. Rate-Limiting (10 req / 300 sec pro IP)
3. Optional: JWT-Validierung (nur wenn Token vorhanden)
4. Briefing in DB speichern
5. GPT-Analyse triggern (wenn `queue_analysis=True`)

**Pfad-Isolation:** Der Submit-Pfad ist isoliert und kann unveraendert bleiben, da:
- Auth ist bereits optional implementiert
- Rate-Limiting ist unabhaengig von Auth
- DB-Operationen sind Auth-unabhaengig

---

## 4) Middleware-Reihenfolge

### Globale Middleware: **NUR CORS**

```python
# main.py:111-136
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Keine weiteren Middleware:**
- Keine globale Auth-Middleware (`@app.middleware("http")`)
- Keine Request-Logging-Middleware
- Keine Security-Header-Middleware

### Dependency-Reihenfolge (pro Request):

```
1. CORS Middleware (global)
2. Route Matching
3. Pydantic Request-Validation
4. Dependencies in Declaration-Order:
   a. rate_limiter (wenn deklariert)
   b. get_db
   c. get_current_user (wenn deklariert)
5. Endpoint Handler
6. Response Processing
```

---

## 5) Konfigurations- & ENV-Zugriff

### Zentrale Konfiguration: `settings.py`

| ENV-Variable | Zweck | Default |
|--------------|-------|---------|
| `JWT_SECRET` | Token-Signierung | PFLICHT |
| `JWT_ALGORITHM` | Signatur-Algo | `HS256` |
| `JWT_EXPIRE_DAYS` | Token-Gueltigkeit | `7` |
| `ADMIN_EMAILS` | Admin-Whitelist | - |
| `ENABLE_ADMIN_ROUTES` | Admin-Routen aktivieren | `0` |
| `ADMIN_ALLOW_RAW_SQL` | SQL-Hotfix aktivieren | `0` |

### Vorhandene Keys/Tokens:

| Key-Typ | Vorhanden | Verwendung |
|---------|-----------|------------|
| **Service-Keys** | NEIN | Nicht implementiert |
| **Admin-Keys** | Partial | `ADMIN_EMAILS` Whitelist, kein API-Key |
| **API-Keys** | Extern | `OPENAI_API_KEY`, `TAVILY_API_KEY`, etc. |
| **Feature-Flags** | Ja | 50+ Flags in `.env.example` |

---

## 6) Tests & CI-Abdeckung

### Auth-Tests: `tests/test_report_workflow.py`

| Test | Beschreibung | Auth-bezogen |
|------|--------------|--------------|
| `test_01_briefing_submission` | Briefing mit Auth-Headers | Ja |
| `test_04_rate_limiting` | Rate-Limit Test | Indirekt |
| `test_05_idempotency` | Idempotenz Test | Indirekt |

### CI-Pipeline: `.github/workflows/test.yml`

- **Unit Tests**: `pytest` mit Coverage fuer `services`, `routes`, `core`
- **Type-Check**: `mypy`
- **Security-Scan**: `bandit`, `safety`
- **E2E** (optional): Playwright

### Test-Abdeckung Auth:

| Aspekt | Getestet |
|--------|----------|
| JWT-Erstellung | Gemockt |
| JWT-Validierung | Gemockt |
| Cookie-Handling | Nicht explizit |
| Rate-Limiting | `test_04_rate_limiting` |
| Admin-Auth | Keine Tests |

---

## Antworten auf die 6 Kernfragen

### 1. Wo genau sitzt die aktuelle Auth-Logik? Ist sie zentral oder pro Endpoint?

**Antwort:** Die Auth-Logik ist **zentral** in `core/security.py`, aber **dezentral angewendet**:

- **Zentrale Definition**: `get_current_user()` in `core/security.py:51-87`
- **Dezentrale Anwendung**: Jeder Endpoint entscheidet selbst via `Depends(get_current_user)`
- **Kein globaler Auth-Guard**: Es gibt keine Middleware, die alle Requests filtert

---

### 2. Kann man vor der User-Auth einen optionalen Service-Token pruefen, ohne Nebenwirkungen?

**Antwort:** **JA, problemlos moeglich.**

**Begruendung:**
1. **Keine globale Middleware**: Es gibt keinen `@app.middleware("http")` der alle Requests filtert
2. **Dependency-basiert**: Auth wird pro Endpoint via `Depends()` injiziert
3. **Isolierter Token-Check**: `get_current_user()` prueft nur Cookie/Header, keine Seiteneffekte
4. **Reihenfolge steuerbar**: Dependencies werden in Deklarationsreihenfolge ausgefuehrt

---

### 3. Welche Datei(en) waeren die einzigen, die fuer einen Service-Token geaendert werden muessten?

**Antwort:** **1-2 Dateien** fuer minimale Integration:

| Datei | Aenderung | Risiko |
|-------|----------|--------|
| `core/security.py` | Neue Funktion `validate_service_token()` + kombinierte Dependency | Niedrig |
| `settings.py` | Neue ENV-Variable `SERVICE_TOKEN_SECRET` | Minimal |

---

### 4. Welche Regression-Risiken bestehen realistisch?

**Risiko-Bewertung: NIEDRIG**

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| User-Auth bricht | Sehr niedrig | Hoch | Service-Token als **Prioritaet vor** User-Auth, nicht Ersatz |
| Cookie-Handling Stoerung | Niedrig | Mittel | Neue Header (`X-Service-Token`) kollidiert nicht mit Cookie |
| Rate-Limiting Bypass | Niedrig | Mittel | Rate-Limiter ist Auth-unabhaengig (IP-basiert) |
| Test-Regression | Niedrig | Niedrig | Tests mocken Auth bereits; neue Tests hinzufuegen |

---

### 5. Gibt es Stellen, an denen ein Service-Header heute schon unabsichtlich geblockt wuerde?

**Antwort:** **NEIN**

**Analyse:**
1. **CORS-Headers**: `allow_headers=["*"]` erlaubt alle Header (`main.py:134`)
2. **Keine Header-Whitelist**: FastAPI/Starlette blockt keine unbekannten Header
3. **Rate-Limiter**: Verwendet IP, nicht Header (`routes/_bootstrap.py:99-101`)
4. **Keine WAF**: Keine Web Application Firewall konfiguriert

---

### 6. Empfehlung: Service-Token-Integration

## Empfehlung: **PROBLEMLOS MOEGLICH**

| Faktor | Bewertung | Details |
|--------|-----------|---------|
| Architektur | Guenstig | Dependency-basiert, keine globale Middleware |
| Isolation | Gegeben | Auth-Logik zentral in 1 Datei |
| Rueckwaertskompatibilitaet | Einfach | Service-Token als zusaetzliche Option, nicht Ersatz |
| Test-Abdeckung | Ausbaufaehig | Neue Tests erforderlich |
| Risiko | Niedrig | Keine Breaking Changes bei korrekter Implementierung |

### Empfohlene Implementierung:

```
1. settings.py:
   + SERVICE_TOKEN_SECRET: Optional[str] = None
   + SERVICE_TOKEN_ENABLED: bool = False

2. core/security.py:
   + def validate_service_token(token: str) -> ServicePayload
   + def get_service_or_user(...)  # Kombinierte Dependency

3. Beliebige Route:
   - Depends(get_current_user)
   + Depends(get_service_or_user)  # Oder parallel beide
```

### Nicht-Regression garantiert durch:

1. **Feature-Flag**: `SERVICE_TOKEN_ENABLED=0` als Default
2. **Additiv**: Service-Token ergaenzt User-Auth, ersetzt sie nicht
3. **Isoliert**: Neue Funktion, keine Aenderung an `get_current_user()`

---

## Zusammenfassung der relevanten Dateien

| Datei | Pfad | Rolle |
|-------|------|-------|
| Security Core | `core/security.py` | JWT-Logik, `get_current_user` |
| Auth Router | `routes/auth.py` | Login-Endpoints, Cookie-Handling |
| Briefings Router | `routes/briefings.py` | **Kritischer Pfad** - Report-Submission |
| Settings | `settings.py` | ENV-Konfiguration |
| Bootstrap | `routes/_bootstrap.py` | `get_db`, `rate_limiter` |
| Auth Service | `services/auth.py` | DB-Code-Handling |
| Rate Limiter | `services/rate_limit.py` | Token-Bucket, Global-Limits |
| Admin Router | `routes/admin.py` | Admin-Endpoints mit Auth |
