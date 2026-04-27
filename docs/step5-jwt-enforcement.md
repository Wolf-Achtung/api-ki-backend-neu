# Step 5 — JWT-Enforcement in Report-Pipeline-Endpoints

**Status:** Plan (kein Code-Change in diesem PR — reine Doku zur Vorab-Review)
**Trigger:** PR #996 + #1000 — Audit-Daten zeigen 12/12 Briefings mit `source=anonymous` und `user_email=null`.
**Ziel:** Body-Email/-Override als spoofbarer Auth-Vektor wird gestrichen; Token-Email ist die einzige Wahrheit.

## TL;DR

Acht Endpoints werden auf eine zentrale Auth-Dependency umgestellt, die **JWT (Cookie oder Bearer)** ODER **`X-Service-Token`** akzeptiert. Body-Felder `email`, `email_override` werden entweder gestrichen oder müssen exakt gleich der Token-Email sein. Wenn keine valide Auth → 401.

`/api/appetizer/generate` (Lead-Magnet) bleibt explizit offen — Wolf E5 Stufe 2.

## Zentraler Auth-Helper (neu)

Vorschlag: `core/security.py` bekommt einen kombinierten Principal-Resolver.

```python
# core/security.py — neu

class AuthenticatedPrincipal(BaseModel):
    """Result of require_authenticated_principal — entweder User-JWT
    oder Service-Token, niemals beides leer."""
    email: Optional[str] = None              # User-JWT → email; Service → None
    service_principal: Optional[str] = None  # Service-Token → principal; User → None
    is_service: bool = False

    @property
    def identity(self) -> str:
        """Stable key for logs: 'user:foo@bar' oder 'service:golden_reports'."""
        if self.is_service:
            return f"service:{self.service_principal}"
        return f"user:{self.email}"


def require_authenticated_principal(
    auth_token: Optional[str] = Cookie(None, alias="auth_token"),
    authorization: Optional[str] = Header(None),
    x_service_token: Optional[str] = Header(None, alias="X-Service-Token"),
) -> AuthenticatedPrincipal:
    """Akzeptiert JWT (Cookie/Bearer) ODER Service-Token. 401 bei beiden leer.

    Service-Token hat Priorität (wie in routes/briefings.py:submit_briefing).
    """
    s = get_settings()

    # Priorität 1: Service-Token
    if x_service_token and s.security.service_token_enabled:
        # required_scope wird vom Endpoint via Closure gesetzt — siehe
        # require_authenticated_principal_with_scope() unten.
        payload = verify_service_token(x_service_token, required_scope="reports:write")
        return AuthenticatedPrincipal(
            service_principal=payload.principal,
            is_service=True,
        )

    # Priorität 2: User-JWT (Cookie ODER Bearer)
    token = auth_token
    if not token and authorization:
        scheme, _, header_token = authorization.partition(" ")
        if scheme.lower() == "bearer" and header_token:
            token = header_token
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required (JWT cookie/bearer or X-Service-Token).",
        )
    payload = verify_access_token(token)
    return AuthenticatedPrincipal(email=payload.email, is_service=False)
```

Bei Bedarf zusätzlich eine Whitelist-Check-Variante:

```python
def require_whitelisted_principal(
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
) -> AuthenticatedPrincipal:
    """JWT-User MUSS in EMAIL_WHITELIST sein. Service-Tokens kommen durch."""
    if principal.is_service:
        return principal
    from core.whitelist import require_whitelisted
    require_whitelisted(principal.email)
    return principal
```

So müssen Endpoints nur entscheiden: brauchen sie Whitelist (Standard) oder reicht JWT (Sonderfall)?

## Per-Endpoint-Diff-Liste

### 1. `POST /api/analyze/run` — `routes/analyze.py:24`

**Ist:** keine Auth, nur Rate-Limit `analyze:run 5/60`. Body hat `email_override: EmailStr | None` — wird unverändert an `gpt_analyze.run_async` durchgereicht.

**Soll:**
```python
@router.post("/run", status_code=202, dependencies=[Depends(rate_limiter("analyze:run", 5, 60))])
def run(
    body: RunAnalyze,
    request: Request,
    db = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(require_whitelisted_principal),
) -> dict:
    ...
    # email_override-Streichung: wenn gesetzt, MUSS = principal.email sein
    if body.email_override and not principal.is_service:
        if body.email_override.lower() != (principal.email or "").lower():
            raise HTTPException(403, "email_override must match token email")
    # Service-Tokens dürfen email_override frei setzen (Golden-Reports-Use-Case)
    final_email = body.email_override if principal.is_service else principal.email
    run_async(body.briefing_id, final_email)
```

**Risiko:** Niedrig. Endpoint hatte bereits Rate-Limit; legitime Aufrufer aus Frontend werden JWT haben.

---

### 2. `POST /api/report/generate` — `routes/report.py:183`

**Ist:** keine Auth. Body ist `Dict[str, Any]` mit beliebigem `email`-Feld → direkt an `run_async`.

**Soll:** Pydantic-Body-Schema einführen + JWT-Pflicht:

```python
class ReportGenerateRequest(BaseModel):
    briefing_id: int = Field(ge=0)
    variant: str = "auto"
    company_size: str | None = None
    email: EmailStr | None = None  # ignored unless service-principal

@router.post("/generate")
async def generate(
    payload: ReportGenerateRequest,
    principal: AuthenticatedPrincipal = Depends(require_whitelisted_principal),
) -> Dict[str, Any]:
    ...
    if payload.email and not principal.is_service:
        if payload.email.lower() != (principal.email or "").lower():
            raise HTTPException(403, "email must match token email")
    final_email = payload.email if principal.is_service else principal.email
    run_async(payload.briefing_id, email=final_email, report_variant=resolved_variant_str)
```

**Risiko:** Mittel. `routes/report.py:183` wird vom Frontend aufgerufen (genau wie `solo-compact`). Frontend muss JWT mitschicken — sollte schon jetzt der Fall sein, weil sonst der Login-Flow defekt wäre.

---

### 3. `POST /api/report/solo-compact` — `routes/report.py:86`

**Ist:** keine Auth. Body ist `ReportVariantRequest` (Pydantic) ohne email.

**Soll:**
```python
@router.post("/solo-compact")
async def generate_solo_compact(
    payload: ReportVariantRequest,
    principal: AuthenticatedPrincipal = Depends(require_whitelisted_principal),
) -> Dict[str, Any]:
    ...  # rest unverändert
```

**Risiko:** Niedrig. Kein email-Feld zu streichen.

---

### 4. `POST /api/report/gamechanger-deep-dive` — `routes/report.py:837`
### 4b. `POST /api/report/gamechanger-deep-dive/pdf/{briefing_id}` — `routes/report.py:1037`

**Ist:** keine Auth. Body ist `GamechangerDeepDiveRequest` mit nur `briefing_id`.

**Soll:** beide Endpoints bekommen `Depends(require_whitelisted_principal)`. Keine Body-Änderung nötig.

**Zusatz:** PDF-Endpoint sendet Email (siehe `_send_deep_dive_email` ab Zeile 951). Bisher wird die Empfänger-Email per `_determine_user_email(db, briefing, None)` aus dem Briefing-User aufgelöst — gut. Mit JWT-Pflicht kann die Funktion zusätzlich validieren, dass `principal.email == briefing.user.email`, sonst 403 (verhindert "PDF-Versand für fremdes Briefing erzwingen").

**Risiko:** Mittel-Hoch. Standalone-Produkt, möglicherweise eigener Frontend-Flow. Testen vor Merge in Staging.

---

### 5. `POST /api/strategy/generate/{briefing_id}` — `routes/strategy.py:319`

**Ist:** keine Auth, nur `payment_status`-Check (`beta | paid | free`).

**Soll:** `Depends(require_whitelisted_principal)` davor. Plus Owner-Check: nur der ursprüngliche Briefing-Eigentümer (oder Service-Token oder Admin) darf Strategy generieren — sonst kann jeder gegen LLM-Kosten den Pipeline triggern:

```python
@router.post("/generate/{briefing_id}")
async def generate_strategy_report_endpoint(
    briefing_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(require_whitelisted_principal),
):
    ...
    briefing = db.query(Briefing).filter(Briefing.id == briefing_id).first()
    if not briefing:
        raise HTTPException(404, "Briefing nicht gefunden")
    # Owner-Check
    if not principal.is_service:
        owner_email = getattr(briefing.user, "email", None) if briefing.user else None
        from core.whitelist import is_admin
        if owner_email != principal.email and not is_admin(principal.email):
            raise HTTPException(403, "Not your briefing")
    ...
```

**Risiko:** Mittel. Owner-Check ist neu — falls Wolf das nicht will, kann er rausgenommen werden. (Begründung pro Owner-Check: Strategy-Pipeline ist 5-10 € LLM-Kosten pro Aufruf.)

---

### 6. `POST /api/strategy/questions/{briefing_id}` — `routes/strategy.py:190`

**Ist:** keine Auth.

**Soll:** `Depends(require_whitelisted_principal)` + Owner-Check (gleich wie #5). Die Questions sind Pre-Conditions für `/generate/{id}` — wenn jemand Fremde Questions schreiben kann, kann er nachher nicht selbst generieren, aber er kann den Datensatz fälschen.

**Risiko:** Niedrig.

---

### 7. `POST /api/chat/start` — `routes/chat.py:516`
### 7b. `POST /api/chat/complete` — `routes/chat.py:2687`

**Ist:** Auth via `_resolve_user(request, db)` — non-throwing, gibt None zurück wenn kein Token → erzeugt anonyme Session.

**Soll:** non-throwing → throwing. `Depends(require_whitelisted_principal)` als Dependency. `_resolve_user` bleibt für `session.user_id`-Auflösung, aber der Endpoint selbst lehnt Anonymous mit 401 ab.

```python
@router.post("/start")
async def chat_start(
    req: ChatStartRequest,
    request: Request,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(require_whitelisted_principal),
):
    # principal garantiert vorhanden; weiterhin _resolve_user für user_id
    user_id, _ = _resolve_user(request, db)
    ...
```

**Risiko:** Hoch. Chat ist für End-User; falls das Frontend bisher anonyme Chat-Sessions erlaubt, müssen User dort jetzt erst einloggen. Verifikation per Audit-Daten: wenn `source=anonymous` Briefings über Chat reinkommen, müssen wir das Frontend-UX vorher anpassen.

---

## Was NICHT betroffen ist (Wolf E5 Stufe 2 — späterer PR)

- `POST /api/appetizer/generate` — Lead-Magnet, bleibt offen, bekommt aber später Per-IP-Rate-Limit + Email-Magic-Link-Verifikation + Audit-Log.
- `POST /api/strategy/admin/*` — schon hinter HMAC-`admin_key`, eigener Migration-Pfad zu JWT denkbar (nicht in Scope hier).
- `POST /api/admin-testrun/replay/{id}` — schon hinter `admin_key`, gleicher Status.

## Tests

Zwei Test-Klassen pro Endpoint:

1. **Auth-Gate**: Ohne Token / mit ungültigem Token → 401 (vorher 200).
2. **Body-Email-Streichung** (#1, #2, #4b): Token-Email ≠ Body-Email → 403; Token-Email == Body-Email → 200.
3. **Owner-Check** (#5, #6): Fremdes Briefing → 403; eigenes Briefing → 200; Admin → 200.
4. **Service-Token-Pfad**: gültiger `X-Service-Token` (Scope `reports:write`) → 200.

Plus zwei Helper-Tests für `require_authenticated_principal` (XFF + Cookie-Priorität, Service-Priorität).

## Rollout-Strategie

1. **PR vorbereiten** mit allen 8 Endpoints + neuem `core/security.py`-Helper + Tests.
2. **Auf Staging** mergen wenn vorhanden, oder mit Feature-Flag `STEP5_JWT_ENFORCEMENT=true` deployen.
3. **24 h Echt-Traffic beobachten** — `source`-Verteilung in `/api/admin/briefings/recent` zeigt, ob neue 401s auftauchen.
4. Wenn keine unbekannten Service-Caller reinflopen: Default flippen, Flag entfernen.

## Rollback

Per-Endpoint-Revert: jeder der acht Endpoints behält seine bisherige Implementierung im git-History, ein einzelner Revert bringt den Endpoint zurück. Plus Feature-Flag-Mechanik (3.) als zentraler Killswitch.

## Open Questions an Wolf

1. **Owner-Check bei Strategy** (#5, #6): drin lassen oder rausnehmen? Drin = strengere Sicherheit, kann Edge-Cases (Account-Wechsel) brechen.
2. **Chat-Anonymous-Flow** (#7): Frontend muss vorher Login-Wall einbauen. Hat das schon einer?
3. **Feature-Flag-Variante** vs. einfach hart deployen? Hart-Deployen wäre simpler, aber Rollback dauert.
4. **Service-Token-Scopes**: aktuell sind die in `core/security.py` granular (`briefings:submit`, `reports:read`). Brauchen wir `reports:write` für die generate-Endpoints? Oder existing Scope wiederverwenden?

Sobald die vier Punkte beantwortet sind, schreibe ich den Code-PR.
